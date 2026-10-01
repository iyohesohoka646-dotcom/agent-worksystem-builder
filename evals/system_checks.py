"""Frozen external artifact grader; actual processes/HTTP/data, never completion claims."""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# The shared gateway runtime is frozen identically for all four conditions.
sys.path.insert(0, str(Path(__file__).resolve().parent / "builder/building-agent-worksystems/scripts"))
from awb_core.contracts import file_digest, read_json, write_json
from awb_core.process import WindowsJob, resume_owned_process
from system_gateway import Gateway


def command(args, workspace, timeout=120):
    result = subprocess.run([sys.executable, "-X", "utf8", *args], cwd=workspace,
        capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if result.returncode:
        raise AssertionError("Program failed: " + result.stderr[-2000:])
    return result.stdout


def request(url, body=None):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=150) as response:
        return json.load(response)


class TargetServer:
    def __init__(self, workspace, profile, data, evidence):
        self.workspace, self.profile, self.data, self.evidence = workspace, profile, data, evidence
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.url = "http://127.0.0.1:" + str(self.port)

    def __enter__(self):
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.out = (self.evidence / "stdout.log").open("wb")
        self.err = (self.evidence / "stderr.log").open("wb")
        self.process = subprocess.Popen([sys.executable, "-X", "utf8", "app.py", "--data", str(self.data),
            "--profile", str(self.profile), "--port", str(self.port)], cwd=self.workspace,
            stdout=self.out, stderr=self.err, creationflags=4 if os.name == "nt" else 0,
            start_new_session=os.name != "nt")
        self.job = WindowsJob(self.process) if os.name == "nt" else None
        if self.job:
            resume_owned_process(self.process)
        deadline = time.monotonic() + 15
        try:
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise AssertionError("Target server exited at startup")
                try:
                    with urllib.request.urlopen(self.url, timeout=1) as response:
                        self.html = response.read()
                    return self
                except (OSError, urllib.error.HTTPError):
                    time.sleep(0.1)
            raise AssertionError("Target server did not start")
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *args):
        if self.job:
            self.job.close()
        elif self.process.poll() is None:
            import signal
            os.killpg(self.process.pid, signal.SIGKILL)
        self.process.wait(timeout=5)
        self.out.close()
        self.err.close()


def check(case, workspace, config, evidence):
    evidence.mkdir(parents=True, exist_ok=True)
    checks = {}
    hashes = {name: file_digest(workspace / name) for name in case["unchanged"]}
    checks["launch"] = any(p.is_file() for p in (workspace / "README.md", workspace / "README.zh-CN.md"))
    family = case["family"]
    if family == "pure":
        command(["app.py", "--input", "input.csv", "--output", "output.json"], workspace)
        checks["deterministic_result"] = read_json(workspace / "output.json") == case["expected"]
        # Output must be independent of model credentials or services.
        source = "\n".join(p.read_text(encoding="utf-8") for p in workspace.glob("*.py")).lower()
        checks["no_intelligence_or_service"] = not any(s in source for s in ("openai", "codex", "httpserver", "requests.", "agent", "awb_core"))
    else:
        with Gateway(workspace, config, evidence / "gateway", max_calls=2 if family == "workbench" else 1) as gateway:
            profile_path = evidence / "runtime-profile.json"
            write_json(profile_path, {"gateway": gateway.url, "model": config["model"], "codex_home": config["codex_home"]})
            if family == "existing":
                command(["enhance.py", "--input", "input.txt", "--output", "plain.json", "--no-intelligence"], workspace)
                checks["regression"] = all(read_json(workspace / "plain.json").get(k) == v for k, v in case["expected"].items())
                command(["enhance.py", "--input", "input.txt", "--output", "annotated.json", "--profile", str(profile_path)], workspace, timeout=150)
                output = read_json(workspace / "annotated.json")
                checks["existing_api"] = all(output.get(k) == v for k, v in case["expected"].items())
                checks["actual_annotation"] = len(gateway.calls) == 1 and gateway.calls[0]["status"] == "completed" and output.get("annotation") == gateway.calls[0]["text"]
                # Replacement with an unreachable resource must produce explicit failure without another model call.
                write_json(profile_path, {"gateway": "http://127.0.0.1:1", "model": config["model"]})
                failure = subprocess.run([sys.executable, "-X", "utf8", "enhance.py", "--input", "input.txt", "--output", "failed.json",
                    "--profile", str(profile_path)], cwd=workspace, capture_output=True, timeout=15)
                checks["configuration_replacement_failure"] = failure.returncode != 0 and len(gateway.calls) == 1
            else:
                data = evidence / "business-data"
                with TargetServer(workspace, profile_path, data, evidence / "server-1") as server:
                    checks["ui_html_served"] = b"<" in server.html and (b"form" in server.html.lower() or b"button" in server.html.lower())
                    task = request(server.url + "/api/tasks", case["task"])
                    task_id = str(task["id"])
                    discussion = request(server.url + "/api/tasks/" + task_id + "/discuss",
                        {"message": "Discuss this task briefly. Return a short nonempty task explanation."})
                    checks["interactive"] = any(c["mode"] == "interactive" and c["status"] == "completed" and discussion.get("text") == c["text"] for c in gateway.calls)
                    try:
                        request(server.url + "/api/tasks/" + task_id + "/execute", {})
                        checks["approval_required"] = False
                    except urllib.error.HTTPError:
                        checks["approval_required"] = not any(c["mode"] == "noninteractive" for c in gateway.calls)
                    request(server.url + "/api/tasks/" + task_id + "/approve", {})
                    output = request(server.url + "/api/tasks/" + task_id + "/execute", {})
                    checks["actual_execution_result"] = output.get("output") == case["task"]["expected"]
                    checks["ordinary_verification"] = output.get("verified") is True and checks["actual_execution_result"]
                    checks["noninteractive"] = any(c["mode"] == "noninteractive" and c["status"] == "completed" for c in gateway.calls)
                    checks["business_data"] = any(p.is_file() for p in data.rglob("*"))
                # Builder is no longer running during this check; own service restarts on persistent state.
                with TargetServer(workspace, profile_path, data, evidence / "server-2") as server:
                    tasks = request(server.url + "/api/tasks")
                    checks["restart"] = isinstance(tasks, list) and any(str(t.get("id")) == task_id for t in tasks)
    for name, expected in hashes.items():
        checks["preserved:" + name] = file_digest(workspace / name) == expected
    write_json(evidence / "receipt.json", {"checks": checks, "passed": all(checks.values()), "simulated_user": True,
                                         "human_trial": "pending", "qualification": "not_established"})
    return all(checks.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("case", "workspace", "config", "evidence"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    try:
        passed = check(read_json(args.case), args.workspace, read_json(args.config), args.evidence)
    except Exception as exc:
        args.evidence.mkdir(parents=True, exist_ok=True)
        environment_error = None
        calls_path = args.evidence / "gateway/calls.json"
        if calls_path.is_file():
            environment_error = next((c["environment_error"] for c in read_json(calls_path) if c.get("environment_error")), None)
        write_json(args.evidence / "receipt.json", {"passed": False, "error": str(exc), "environment_error": environment_error, "simulated_user": True})
        print(str(exc), file=sys.stderr)
        passed = False
    raise SystemExit(0 if passed else 1)
