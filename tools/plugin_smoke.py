"""Install the packaged plugin with native Codex in an isolated, credential-free home."""
import json
import argparse
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
from awb_core.adapters.codex import executable
from awb_core.contracts import read_json, write_json
from package_plugin import package
from awb_core.process import WindowsJob, resume_owned_process


def discover(binary, root, env):
    messages = queue.Queue()
    job = None
    with (root / "app-server.stderr.log").open("wb") as stderr:
        process = subprocess.Popen([binary, "app-server", "--stdio"], cwd=root, env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                   text=True, encoding="utf-8", creationflags=4 if os.name == "nt" else 0)
        try:
            if os.name == "nt":
                job = WindowsJob(process)
                resume_owned_process(process)
            def read_messages():
                for line in process.stdout:
                    try:
                        messages.put(json.loads(line))
                    except ValueError:
                        pass
            reader = threading.Thread(target=read_messages, daemon=True)
            reader.start()
            def send(value):
                process.stdin.write(json.dumps(value) + "\n")
                process.stdin.flush()
            def receive(identifier):
                deadline = time.monotonic() + 20
                while True:
                    response = messages.get(timeout=max(0.01, deadline - time.monotonic()))
                    if response.get("id") == identifier:
                        return response
            send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "awb-package-check", "version": "1"}, "capabilities": {"experimentalApi": True}}})
            initialized = receive(1)
            if initialized.get("error"):
                return {"passed": False, "response": initialized}
            send({"method": "initialized"})
            send({"id": 2, "method": "skills/list", "params": {"cwds": [str(root)], "forceReload": True}})
            response = receive(2)
            skills = [s for entry in response.get("result", {}).get("data", []) for s in entry["skills"]
                      if s.get("pluginId") == "agent-worksystem-builder@agent-worksystem-builder-plugins"]
            return {"passed": any(s["enabled"] and s["name"].endswith("building-agent-worksystems") for s in skills), "skills": skills}
        except (queue.Empty, OSError) as exc:
            return {"passed": False, "error": str(exc)}
        finally:
            if job:
                job.close()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            process.stdin.close()
            reader.join(timeout=2) if 'reader' in locals() else None
            process.stdout.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--marketplace-source", help="Also validate a published Git marketplace instead of the local archive")
    parser.add_argument("--ref", help="Pin the published marketplace revision")
    parser.add_argument("--archive", type=Path, help="Validate a downloaded release archive")
    options = parser.parse_args()
    receipt = package()
    if options.archive:
        from awb_core.contracts import file_digest
        if file_digest(options.archive) != receipt["sha256"]:
            raise ValueError("Downloaded release archive does not match the local receipt")
    binary = executable({})
    report = {"version": receipt["version"], "archive_sha256": receipt["sha256"], "checks": []}
    with tempfile.TemporaryDirectory(prefix="awb-plugin-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(options.archive or ROOT / "dist" / receipt["archive"]) as archive:
            archive.extractall(root)
        catalog = read_json(ROOT / ".agents/plugins/marketplace.json")
        catalog["plugins"][0]["source"]["path"] = "./agent-worksystem-builder"
        write_json(root / ".agents/plugins/marketplace.json", catalog)
        (root / "host-state").mkdir()
        env = dict(os.environ, CODEX_HOME=str(root / "host-state"))
        commands = [
            [binary, "plugin", "marketplace", "add", options.marketplace_source or str(root), "--json"] + (["--ref", options.ref] if options.ref else []),
            [binary, "plugin", "add", "agent-worksystem-builder@agent-worksystem-builder-plugins", "--json"],
            [binary, "plugin", "list", "--json"],
        ]
        for args in commands:
            try:
                result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            except subprocess.TimeoutExpired as exc:
                report["checks"].append({"command": args[1:4], "returncode": 124, "stderr": "Native marketplace command exceeded 60 seconds"})
                break
            report["checks"].append({"command": args[1:4], "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
            if result.returncode:
                break
        cached = list((root / "host-state" / "plugins" / "cache").rglob("awb.py"))
        report["runtime_in_installed_cache"] = bool(cached)
        if cached:
            result = subprocess.run([sys.executable, str(cached[0]), "--help"], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=20)
            report["checks"].append({"command": ["installed awb.py", "--help"], "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        report["skill_discovery"] = discover(binary, root, env) if cached else {"passed": False}
        report["passed"] = bool(cached) and all(c["returncode"] == 0 for c in report["checks"]) and report["skill_discovery"]["passed"]
    report["marketplace_source"] = options.marketplace_source or "local archive"
    write_json(ROOT / "reports" / ("plugin-remote-install.json" if options.marketplace_source else "plugin-install.json"), report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
