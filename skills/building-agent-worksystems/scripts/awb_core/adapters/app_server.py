"""Owned local stdio JSON-RPC client. The target app owns UI, state and user approvals."""
import json
import os
import queue
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

from ..contracts import AWBError
from ..process import WindowsJob, resume_owned_process
from ..intelligence import host_environment


class AppServerClient:
    def __init__(self, argv, cwd, evidence_dir, config, timeout=30, max_bytes=4 * 1024 * 1024, experimental=False):
        self.argv, self.cwd, self.config = argv, Path(cwd).resolve(), config
        self.directory = Path(evidence_dir)
        self.timeout, self.max_bytes = timeout, max_bytes
        self.experimental = experimental
        self.messages, self.events, self.pending = queue.Queue(maxsize=1024), deque(), {}
        self.sequence, self.process, self.job = 0, None, None
        self.lock, self.write_lock = threading.RLock(), threading.Lock()

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.stderr = (self.directory / "stderr.log").open("wb")
        try:
            self.process = subprocess.Popen(self.argv, cwd=self.cwd, env=host_environment(self.config),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
                text=True, encoding="utf-8", creationflags=4 if os.name == "nt" else 0,
                start_new_session=os.name != "nt", bufsize=1)
            if os.name == "nt":
                self.job = WindowsJob(self.process)
                resume_owned_process(self.process)
            self.reader = threading.Thread(target=self._read, daemon=True)
            self.reader.start()
            params = {"clientInfo": {"name": "awb-local-target", "version": "0.2.0"}}
            if self.experimental:
                params["capabilities"] = {"experimentalApi": True}
            self.request("initialize", params)
            self._send({"method": "initialized", "params": {}})
            return self
        except BaseException:
            self.close()
            raise

    def _read(self):
        size = 0
        try:
            with (self.directory / "events.jsonl").open("w", encoding="utf-8") as log:
                while True:
                    line = self.process.stdout.readline(self.max_bytes + 1)
                    if not line:
                        break
                    size += len(line.encode("utf-8"))
                    if size > self.max_bytes:
                        raise AWBError("output_limit", "App-server event log limit reached")
                    value = json.loads(line)
                    log.write(line)
                    log.flush()
                    self.messages.put(value, timeout=1)
        except (ValueError, OSError, queue.Full, AWBError) as exc:
            self.messages.put_nowait({"_transport_error": str(exc)}) if not self.messages.full() else None
        finally:
            if not self.messages.full():
                self.messages.put_nowait({"_closed": True})

    def _send(self, value):
        with self.write_lock:
            if self.process is None or self.process.poll() is not None:
                raise AWBError("transport", "App-server exited or connection closed")
            try:
                self.process.stdin.write(json.dumps(value, ensure_ascii=False) + "\n")
                self.process.stdin.flush()
            except (OSError, ValueError) as exc:
                raise AWBError("transport", "App-server connection closed") from exc

    def _receive(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AWBError("timed_out", "App-server request timed out; retain session checkpoint")
        try:
            value = self.messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise AWBError("timed_out", "App-server request timed out; retain session checkpoint") from exc
        if value.get("_closed"):
            raise AWBError("transport", "App-server connection closed")
        if value.get("_transport_error"):
            raise AWBError("transport", value["_transport_error"])
        return value

    def _event(self, message):
        if "method" in message:
            if "id" in message:
                self.pending[message["id"]] = message
            self.events.append(message)

    def request(self, method, params):
        with self.lock:
            self.sequence += 1
            number = self.sequence
            self._send({"id": number, "method": method, "params": params})
            deadline = time.monotonic() + self.timeout
            while True:
                message = self._receive(deadline)
                if message.get("id") == number and "method" not in message:
                    if message.get("error"):
                        raise AWBError("rpc", "App-server rejected request", response=message["error"])
                    return message["result"]
                self._event(message)

    def next_event(self, timeout=None):
        with self.lock:
            deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
            while not self.events:
                self._event(self._receive(deadline))
            return self.events.popleft()

    def respond_approval(self, request_id, result):
        with self.lock:
            request = self.pending.get(request_id)
            if request is None:
                raise AWBError("approval", "No pending app-server request with this ID")
            if request["method"] in {"item/commandExecution/requestApproval", "item/fileChange/requestApproval"}:
                if result.get("decision") not in {"accept", "acceptForSession", "decline", "cancel"}:
                    raise AWBError("approval", "Invalid explicit approval decision")
            elif request["method"] not in {"item/tool/requestUserInput", "mcpServer/elicitation/request", "item/permissions/requestApproval"}:
                raise AWBError("approval", "Unsupported server request; cannot approve implicitly")
            self._send({"id": request_id, "result": result})
            del self.pending[request_id]

    def _thread_params(self):
        cfg = dict(self.config.get("config_overrides", {}))
        if self.config.get("reasoning_effort"):
            cfg["model_reasoning_effort"] = self.config["reasoning_effort"]
        return {"cwd": str(self.cwd), "model": self.config.get("model"), "sandbox": self.config.get("sandbox", "read-only"),
                "approvalPolicy": self.config.get("approval_policy", "on-request"), "config": cfg}

    def start_thread(self):
        return self.request("thread/start", self._thread_params())["thread"]["id"]

    def resume_thread(self, thread_id):
        return self.request("thread/resume", self._thread_params() | {"threadId": thread_id})["thread"]["id"]

    def start_turn(self, thread_id, text, output_schema=None):
        params = {"threadId": thread_id, "input": [{"type": "text", "text": text}]}
        if output_schema is not None:
            params["outputSchema"] = output_schema
        return self.request("turn/start", params)["turn"]

    def interrupt(self, thread_id, turn_id):
        return self.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})

    def close(self):
        if getattr(self, "closed", False):
            return
        self.closed = True
        if self.job:
            self.job.close()
            self.job = None
        if self.process is not None:
            if os.name != "nt":
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait(timeout=5)
            self.process.stdin.close()
            if hasattr(self, "reader"):
                self.reader.join(timeout=2)
            self.process.stdout.close()
        if hasattr(self, "stderr"):
            self.stderr.close()

    def __exit__(self, *exc):
        self.close()
