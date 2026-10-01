"""Trusted evaluation resource. Same real Codex gateway is available to all conditions."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from awb_core.adapters.app_server import AppServerClient
from awb_core.contracts import AWBError, inside, write_json
from awb_core.execution import Budget, execute_node
from awb_core.intelligence import app_server_command

TEXT_SCHEMA = {"type": "object", "properties": {"text": {"type": "string"}},
               "required": ["text"], "additionalProperties": False}


class Gateway:
    def __init__(self, workspace, config, evidence, max_calls=2):
        self.workspace, self.config, self.evidence = Path(workspace), config, Path(evidence)
        self.calls, self.max_calls = [], max_calls
        self.lock = threading.Lock()
        gateway = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                status = 200
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 1024 * 1024:
                        raise ValueError("Invalid request size")
                    body = json.loads(self.rfile.read(length))
                    result = gateway.call(self.path.strip("/"), body["prompt"], body["cwd"])
                except Exception as exc:
                    status, result = 503, {"error": str(exc)}
                data = json.dumps(result, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)

    def call(self, mode, prompt, cwd):
        if mode not in {"interactive", "noninteractive"} or not isinstance(prompt, str):
            raise ValueError("Unsupported mode or prompt")
        cwd = inside(self.workspace, cwd)
        cwd.mkdir(parents=True, exist_ok=True)
        with self.lock:
            if len(self.calls) >= self.max_calls:
                raise AWBError("budget", "Gateway actual-call budget exhausted; no retries")
            record = {"mode": mode, "status": "running", "prompt": prompt}
            self.calls.append(record)
            number = len(self.calls)
        directory = self.evidence / str(number)
        cfg = self.config | {"sandbox": "read-only", "workspace_write_authorized": False,
                            "approval_policy": "never", "timeout": 120, "retries": 0}
        instruction = "Do not use tools or alter files. Answer the request. Return a JSON object with a text string containing your actual answer. If a JSON result is requested, put that JSON as the text string.\nRequest: " + prompt
        try:
            if mode == "noninteractive":
                cfg.update(id="gateway", backend="codex", cwd=str(cwd), output_schema=TEXT_SCHEMA)
                result = execute_node(cfg, {"instruction": instruction},
                    {"workspace": directory, "project": self.workspace}, Budget(1, 120))
                if result["status"] != "completed":
                    record["environment_error"] = result.get("error")
                    raise AWBError("backend", "Gateway exec failed", result=result)
                text = result["result"]["text"]
                record["attempt_id"] = result["attempt_id"]
            else:
                started = time.monotonic()
                with AppServerClient(app_server_command(cfg), cwd, directory, cfg, timeout=20) as client:
                    thread = client.start_thread()
                    turn = client.start_turn(thread, instruction, TEXT_SCHEMA)
                    text = None
                    while True:
                        remaining = 120 - (time.monotonic() - started)
                        if remaining <= 0:
                            client.interrupt(thread, turn["id"])
                            raise AWBError("budget", "Gateway wall-clock deadline exhausted")
                        event = client.next_event(remaining)
                        if event.get("id") is not None:
                            raise AWBError("approval", "No-tools gateway unexpectedly requested approval")
                        params = event.get("params", {})
                        if event.get("method") == "item/completed" and params.get("item", {}).get("type") == "agentMessage":
                            text = json.loads(params["item"]["text"])["text"]
                        if event.get("method") == "turn/completed" and params["turn"]["id"] == turn["id"]:
                            if params["turn"]["status"] != "completed" or not text:
                                record["environment_error"] = params["turn"].get("error")
                                raise AWBError("backend", "Gateway discussion failed")
                            break
                    record.update(thread_id=thread, turn_id=turn["id"])
            record.update(status="completed", text=text)
            return {"text": text}
        except Exception as exc:
            record.update(status="failed", error=str(exc))
            if isinstance(exc, AWBError) and exc.code == "rpc":
                record["environment_error"] = exc.as_dict()
            raise
        finally:
            write_json(self.evidence / "calls.json", self.calls)

    def __enter__(self):
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.url = "http://127.0.0.1:" + str(self.server.server_port)
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)
