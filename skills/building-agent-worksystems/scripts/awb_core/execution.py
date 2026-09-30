from __future__ import annotations

import json
import shutil
import sys
import threading
import time
from pathlib import Path

from .adapters import codex, ollama
from .adapters.command import command_argv
from .contracts import AWBError, canonical, digest, inside, validate_schema, validate_record, write_json
from .process import run_process
from .state import identifier, now


def can_replay(node):
    return node.get("side_effect") == "none" or (node.get("side_effect") == "idempotent" and bool(node.get("idempotency_key")))


def dependency_hashes(node, project):
    from .contracts import file_digest
    paths = [inside(project, path) for path in node.get("input_files", [])]
    if node.get("backend") == "command":
        args = command_argv(node)
        for index, part in enumerate(args):
            path = Path(part)
            if path.is_file():
                if index == 0 and str(path).casefold() == str(Path(sys.executable)).casefold():
                    path = Path(sys.base_prefix) / Path(sys.executable).name
                paths.append(path.resolve())
    elif node.get("backend") == "codex":
        paths.append(Path(codex.executable(node)))
    return {str(path): file_digest(path) for path in paths}


class Budget:
    def __init__(self, max_calls, max_seconds, used_calls=0):
        if type(max_calls) is not int or max_calls < 0 or max_seconds <= 0:
            raise AWBError("budget", "A nonnegative call budget and positive time budget are required")
        self.max_calls, self.max_seconds, self.calls = max_calls, max_seconds, used_calls
        self.started, self.lock = time.monotonic(), threading.Lock()

    def remaining(self):
        return max(0.0, self.max_seconds - (time.monotonic() - self.started))

    def reserve(self):
        with self.lock:
            if self.calls >= self.max_calls or self.remaining() <= 0:
                raise AWBError("budget", "Execution budget exhausted; save checkpoint")
            self.calls += 1


CAPABILITIES = {
    "command": {"noninteractive", "structured_output", "cancel"},
    "codex": {"noninteractive", "structured_output", "cancel", "events"},
    "ollama": {"noninteractive", "structured_output"},
}


def preflight(node, context):
    validate_record("node", node)
    backend = node.get("backend")
    if backend not in CAPABILITIES:
        raise AWBError("backend", "Unsupported backend")
    if node.get("require_isolation"):
        raise AWBError("policy", "This runtime cannot attest an OS isolation boundary")
    if context.get("offline") and backend == "codex":
        raise AWBError("policy", "Offline runs cannot use the cloud CLI backend")
    if context.get("offline") and backend == "command":
        raise AWBError("policy", "Generic commands cannot enforce an offline boundary; use the built-in material processor")
    if not set(node.get("required_capabilities", [])) <= CAPABILITIES[backend]:
        raise AWBError("capability", "Backend lacks a required capability")
    if not node.get("timeout", 0) > 0 or "output_schema" not in node:
        raise AWBError("configuration", "Each node needs a timeout and output schema")
    if backend == "command":
        command_argv(node)
    elif backend == "codex":
        codex.executable(node)
        if not node.get("model"):
            raise AWBError("configuration", "An explicit model is required")
    else:
        ollama.validate_endpoint(node.get("endpoint", "http://127.0.0.1:11434"), context.get("offline", False))
        model = node.get("model")
        if not isinstance(model, str) or not model or (context.get("offline") and model.endswith((":cloud", "-cloud"))):
            raise AWBError("policy", "An explicit permitted local model is required")


def execute_node(node_spec, task, context, limits):
    preflight(node_spec, context)
    workspace = Path(context["workspace"]).resolve()
    attempts = []
    retries = node_spec.get("retries", 0)
    if type(retries) is not int or not 0 <= retries <= 2:
        raise AWBError("configuration", "Retries must be between zero and two")
    for _ in range(retries + 1):
        try:
            limits.reserve()
        except AWBError as exc:
            if not attempts:
                raise
            return attempt | {"status": "budget_exhausted", "error": exc.as_dict(), "attempts": attempts}
        attempt = _execute_once(node_spec, task, context, limits, workspace)
        attempts.append(attempt["attempt_id"])
        if not can_replay(node_spec):
            break
        if attempt["status"] in {"completed", "cancelled"} or attempt.get("error", {}).get("code") not in {"timed_out", "http_429", "http_503"}:
            break
    return attempt | {"attempts": attempts}


def _execute_once(node, task, context, budget, workspace):
    attempt_id = identifier("attempt")
    directory = inside(workspace, Path("attempts") / attempt_id)
    directory.mkdir(parents=True)
    write_json(directory / "intent.json", {"node_digest": digest(node), "task_digest": digest(task), "started_at": now(), "side_effect": node.get("side_effect", "unknown")})
    write_json(directory / "input.json", task)
    write_json(directory / "schema.json", node["output_schema"])
    output, stderr = directory / "stdout.log", directory / "stderr.log"
    started = time.monotonic()
    record = {"schema_version": 1, "attempt_id": attempt_id, "node_id": node["id"], "backend": node["backend"],
              "status": "failed", "verification": "unverified", "result": None, "usage": {"cost": None},
              "logs": {"stdout": output.relative_to(workspace).as_posix(), "stderr": stderr.relative_to(workspace).as_posix()}}
    try:
        timeout = min(node["timeout"], budget.remaining())
        if node["backend"] == "ollama":
            request = directory / "http-request.json"
            write_json(request, {"config": node, "task": task, "timeout": timeout, "offline": context.get("offline", False)})
            worker = Path(ollama.__file__).with_name("ollama_worker.py")
            proc = run_process([sys.executable, "-X", "utf8", str(worker)], directory, request, output, stderr, timeout, context.get("cancel"))
            record["returncode"] = proc["returncode"]
            if proc["reason"]:
                raise AWBError(proc["reason"], "HTTP execution stopped")
            if proc["returncode"] != 0:
                raise AWBError("process_exit", "HTTP worker exited unsuccessfully")
            response = json.loads(output.read_text(encoding="utf-8"))
            if response.get("error"):
                error = response["error"]
                raise AWBError(error["code"], error["message"])
            result = response["result"]
        else:
            args = command_argv(node) if node["backend"] == "command" else codex.argv(node, directory, directory / "schema.json", directory / "final.json")
            proc = run_process(args, directory, directory / "input.json", output, stderr, timeout, context.get("cancel"))
            record["returncode"] = proc["returncode"]
            if proc["reason"]:
                raise AWBError(proc["reason"], "Node execution stopped")
            if proc["returncode"] != 0:
                raise AWBError("process_exit", "Node exited unsuccessfully", returncode=proc["returncode"])
            if node["backend"] == "codex":
                result = codex.normalize(directory / "final.json", output)
            else:
                try:
                    result = json.loads(output.read_text(encoding="utf-8"))
                except (ValueError, UnicodeError) as exc:
                    raise AWBError("invalid_output", "Node did not emit one JSON object") from exc
        validate_schema(node["output_schema"], result)
        record.update(status="completed", result=result)
    except AWBError as exc:
        record.update(status=exc.code if exc.code in {"timed_out", "cancelled"} else "failed", error=exc.as_dict())
    except OSError as exc:
        record["error"] = {"code": "process", "message": str(exc)}
    except (ValueError, TypeError, KeyError) as exc:
        record["error"] = {"code": "invalid_output", "message": str(exc)}
    record["elapsed_seconds"] = time.monotonic() - started
    validate_record("result", record)
    write_json(directory / "result.json", record)
    return record


def probe_backend(config, workspace=None, live=False):
    backend = config.get("backend")
    available, version, error = False, None, None
    try:
        if backend == "codex":
            import subprocess
            version = subprocess.run([codex.executable(config), "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10).stdout.strip()
            available = bool(version)
        elif backend == "command":
            command_argv(config)
            available = True
        elif backend == "ollama":
            import httpx
            endpoint = ollama.validate_endpoint(config.get("endpoint", "http://127.0.0.1:11434"), True)
            with httpx.Client(timeout=3, follow_redirects=False, trust_env=False) as client:
                response = client.get(endpoint + "/api/version")
                response.raise_for_status()
                version = response.json()["version"]
                available = True
        else:
            raise AWBError("backend", "Unknown backend")
    except Exception as exc:
        error = str(exc)
    capabilities = {name: "documented" if available else "unknown" for name in CAPABILITIES.get(backend, set())}
    report = {"schema_version": 1, "backend": backend, "available": available, "version": version,
              "config_digest": digest(config), "capabilities": capabilities, "error": error, "checked_at": now()}
    if live:
        if workspace is None:
            raise AWBError("configuration", "Live probes need an evidence workspace")
        probe = config | {"id": "probe", "side_effect": "none", "output_schema": {"type": "object", "properties": {"ok": {"type": "boolean", "enum": [True]}}, "required": ["ok"], "additionalProperties": False}}
        result = execute_node(probe, {"instruction": "Return the JSON object {\"ok\":true}. No tools are needed."}, {"workspace": workspace}, Budget(1, config["timeout"]))
        report["live_result"] = result
        if result["status"] == "completed":
            for capability in ("noninteractive", "structured_output"):
                capabilities[capability] = "tested"
    return report
