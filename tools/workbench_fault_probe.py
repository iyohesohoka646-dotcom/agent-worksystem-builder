"""Separate deterministic fault probes of copied build artifacts; zero model calls.

This does not change matrix grades, add construction attempts or grant release approval.
"""
import argparse
import json
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
sys.path.insert(0, str(ROOT / "evals"))
from awb_core.contracts import AWBError, digest, file_digest, read_json, write_json
from system_checks import TargetServer


def different(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, str):
        return value + "-injected-wrong-result"
    if isinstance(value, list):
        return [different(value[0]), *value[1:]] if value else ["injected"]
    if isinstance(value, dict):
        key = next(iter(value), None)
        return value | {key: different(value[key])} if key is not None else {"injected": True}
    return {"injected": True}


def request(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return {"status": response.status, "body": json.loads(response.read(1024 * 1024))}
    except urllib.error.HTTPError as exc:
        raw = exc.read(1024 * 1024)
        try:
            value = json.loads(raw)
        except ValueError:
            value = {"error": raw.decode("utf-8", errors="replace")}
        return {"status": exc.code, "body": value}


class FaultGateway:
    def __init__(self, result, fail):
        self.calls = []
        gateway = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 * 1024:
                    self.send_error(400)
                    return
                body = json.loads(self.rfile.read(length))
                gateway.calls.append({"path": self.path, "body": body})
                value = {"error": "Injected deterministic backend failure"} if fail else {"text": json.dumps(result)}
                data = json.dumps(value).encode()
                self.send_response(503 if fail else 200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True

    def __enter__(self):
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.url = "http://127.0.0.1:" + str(self.server.server_port)
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)


def run(workspace, task, output):
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(workspace):
        raise AWBError("probe", "Choose a fresh probe directory outside original target sources")
    output.mkdir(parents=True)
    started = time.monotonic()
    hashes = {p.relative_to(workspace).as_posix(): file_digest(p) for p in workspace.rglob("*")
        if p.is_file() and not any(s in {"__pycache__", ".git", ".venv", ".worksystem-build"} for s in p.parts)}
    checks, phases = {}, {}
    wrong = different(task["expected"])
    for phase in ("wrong-result", "backend-failure"):
        directory = output / phase
        copied = directory / "workspace"
        shutil.copytree(workspace, copied, ignore=shutil.ignore_patterns(".git", ".venv", ".worksystem-build", "__pycache__"))
        evidence = {"simulated_node": True, "actual_model_calls": 0, "injected_result": wrong if phase == "wrong-result" else None}
        try:
            with FaultGateway(wrong, fail=phase == "backend-failure") as gateway:
                profile = directory / "profile.json"
                write_json(profile, {"gateway": gateway.url, "model": "deterministic-fault-node"})
                with TargetServer(copied, profile, directory / "business-data", directory / "server") as server:
                    created = request(server.url + "/api/tasks", task)
                    if not 200 <= created["status"] < 300:
                        raise AWBError("probe", "Target task creation failed", response=created)
                    task_id = str(created["body"]["id"])
                    approved = request(server.url + "/api/tasks/" + task_id + "/approve", {})
                    if not 200 <= approved["status"] < 300:
                        raise AWBError("probe", "Target approval failed", response=approved)
                    response = request(server.url + "/api/tasks/" + task_id + "/execute", {})
                    evidence["execution_response"] = response
                    body = response["body"]
                    explicit_error = response["status"] >= 400 or (isinstance(body, dict) and bool(body.get("error")))
                    rejected = explicit_error or (isinstance(body, dict) and body.get("verified") is False)
                    calls = [c for c in gateway.calls if c["path"] == "/noninteractive"]
                    if phase == "wrong-result":
                        bound = explicit_error or (isinstance(body, dict) and digest(body.get("output")) == digest(wrong))
                        checks["wrong_result_rejected"] = len(calls) == 1 and rejected
                        checks["wrong_output_bound_or_explicitly_rejected"] = len(calls) == 1 and bound
                    else:
                        checks["backend_failure_explicit"] = len(calls) == 1 and explicit_error
                    checks[phase + ":no_retry"] = len(calls) == 1
                    evidence["task_state_after_failure"] = request(server.url + "/api/tasks/" + task_id)
                evidence["gateway_calls"] = gateway.calls
        except Exception as exc:
            checks[phase + ":completed_probe"] = False
            evidence["error"] = str(exc)
        phases[phase] = evidence
        write_json(directory / "receipt.json", evidence)
    checks["original_sources_preserved"] = all((workspace / name).is_file()
        and file_digest(workspace / name) == sha for name, sha in hashes.items())
    report = {"schema_version": 1, "source_hashes": hashes, "checks": checks, "phases": phases,
        "passed": all(checks.values()), "elapsed_seconds": time.monotonic() - started,
        "actual_model_calls": 0, "simulated_node": True, "construction_retry": False,
        "release_qualified": False, "human_trial": "pending",
        "scope": "Separate artifact fault probe; original frozen matrix grades and budgets are unchanged.",
        "pending_checks": ["semantic goal coverage", "persistence and recovery semantics review", "actual system-level human use"]}
    write_json(output / "receipt.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    case_path = args.attempt / "case.json"
    if case_path.is_file():
        case = read_json(case_path)
    else:
        record = read_json(args.attempt / "attempt.json")
        case = next((c for c in read_json(args.attempt.parent / "corpus.json")["cases"]
            if c["id"] == record["scenario"]), None)
        if case is None:
            parser.error("No matching frozen case for this attempted cell")
    if case["family"] != "workbench":
        parser.error("The selected artifact must be a workbench-family attempt")
    result = run(args.attempt / "workspace", case["task"], args.output)
    print(json.dumps({"passed": result["passed"], "checks": result["checks"], "actual_model_calls": 0,
        "release_qualified": False}, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)
