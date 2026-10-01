"""Actual representative target integration trial; human use is a separate gate."""
import importlib.util
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
from awb_core.contracts import AWBError, file_digest, read_json, write_json
from awb_core.adapters.codex import executable


def run(output, receipt):
    output = Path(output).resolve()
    if output.exists():
        raise AWBError("trial", "Preserve old trials; choose a fresh output directory")
    if not receipt.get("passed") or receipt["model"] != "gpt-6-sol":
        raise AWBError("trial", "Actual approved host preflight is required")
    if file_digest(executable({})) != receipt["binary_sha256"] or file_digest(Path(receipt["codex_home"]) / "config.toml") != receipt["config_sha256"]:
        raise AWBError("drift", "Host changed since preflight")
    output.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location("awb_target_workbench", ROOT / "examples/task-workbench/workbench.py")
    wb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wb)
    p = read_json(ROOT / "examples/task-workbench/profile.json")
    app = wb.Workbench(output / "business-data", p)
    server = wb.make_server(app, 0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    report = {"schema_version": 1, "model": receipt["model"], "host": receipt["host_version"],
              "simulated_user": True, "actual_model": True, "human_trial": "pending", "qualification": "not_established",
              "source_hashes": {path.relative_to(ROOT).as_posix(): file_digest(path) for folder in
                  ("examples/task-workbench", "examples/existing-project", "examples/pure-program")
                  for path in (ROOT / folder).rglob("*") if path.is_file() and "__pycache__" not in path.parts},
              "checks": {}}
    try:
        with urllib.request.urlopen("http://127.0.0.1:" + str(server.server_port)) as response:
            report["checks"]["ui_served"] = b"Task workbench" in response.read()
        task = app.create_task("Count nonempty lines in input.txt and create result.json with the count. Preserve the input.",
                               {"count": 3}, "alpha\nbeta\ngamma\n")
        app.discuss(task["id"], "Explain the intended acceptance briefly. Do not use tools.")
        deadline = time.monotonic() + 130
        while task["id"] in app.clients and time.monotonic() < deadline:
            time.sleep(0.2)
        events = app.events(task["id"])
        completed = [e for e in events if e.get("method") == "turn/completed"]
        report["checks"]["interactive"] = bool(completed and completed[-1]["params"]["turn"]["status"] == "completed")
        write_json(output / "discussion.json", events)
        app.approve(task["id"], 1, "simulated-trial-user")
        attempt = app.execute(task["id"])
        report["checks"]["noninteractive_actual_output"] = attempt["status"] == "verified" and not attempt["simulated_executor"]
        restored = wb.Workbench(output / "business-data", p)
        report["checks"]["restart_business_state"] = restored.task(task["id"])["status"] == attempt["status"]
        report["checks"]["separate_business_state"] = not (output / "business-data/.worksystem-build").exists()
        profile_path = output / "profile.json"
        write_json(profile_path, p)
        input_path = output / "existing-input.txt"
        input_path.write_text("existing parser\nintelligence annotation\n", encoding="utf-8")
        proc = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "examples/existing-project/enhance.py"),
            "--input", str(input_path), "--output", str(output / "enhanced.json"), "--profile", str(profile_path)],
            capture_output=True, text=True, encoding="utf-8", timeout=150)
        (output / "enhance.stdout").write_text(proc.stdout, encoding="utf-8")
        (output / "enhance.stderr").write_text(proc.stderr, encoding="utf-8")
        enhanced = read_json(output / "enhanced.json") if (output / "enhanced.json").exists() else {}
        report["checks"]["existing_intelligence"] = proc.returncode == 0 and enhanced.get("intelligence", {}).get("execution_status") == "completed"
        report["checks"]["existing_api"] = enhanced.get("parsed") == {"count": 2, "items": ["existing parser", "intelligence annotation"]}
        report["checks"]["existing_source_preserved"] = file_digest(ROOT / "examples/existing-project/parser.py") == report["source_hashes"]["examples/existing-project/parser.py"]
        csv = output / "pure-input.csv"
        csv.write_text("name,value\na,2\na,3\nb,-1\n", encoding="utf-8")
        original = file_digest(csv)
        pure = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "examples/pure-program/summarize.py"),
            str(csv), str(output / "pure-result.json")], capture_output=True, timeout=10)
        report["checks"]["pure_program"] = pure.returncode == 0 and read_json(output / "pure-result.json") == {"a": 5, "b": -1} and file_digest(csv) == original
        report["passed"] = all(report["checks"].values())
    except Exception as exc:
        report.update(passed=False, error=str(exc))
    finally:
        server.shutdown()
        server.server_close()
        app.close()
        worker.join(timeout=2)
        write_json(output / "receipt.json", report)
    return report


def finish_checks(output):
    """Complete deterministic postchecks after a harness error; preserve failed receipt."""
    output = Path(output).resolve()
    original = read_json(output / "receipt.json")
    if not all(original["checks"].get(key) for key in ("interactive", "noninteractive_actual_output", "existing_intelligence", "existing_api")):
        raise AWBError("trial", "No successful real-mode evidence to finalize")
    report = original | {"prior_receipt_sha256": file_digest(output / "receipt.json"), "completion_has_new_model_calls": False}
    report.pop("error", None)
    report["checks"]["existing_source_preserved"] = all(file_digest(ROOT / Path(name)) == sha for name, sha in original["source_hashes"].items())
    from awb_core.state import identifier
    completion = output / identifier("deterministic-postcheck")
    completion.mkdir()
    csv = completion / "pure-input.csv"
    csv.write_text("name,value\na,2\na,3\nb,-1\n", encoding="utf-8")
    original_hash = file_digest(csv)
    pure = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "examples/pure-program/summarize.py"),
        str(csv), str(completion / "pure-result.json")], capture_output=True, timeout=10)
    report["checks"]["pure_program"] = pure.returncode == 0 and read_json(completion / "pure-result.json") == {"a": 5, "b": -1} and file_digest(csv) == original_hash
    report["passed"] = all(report["checks"].values())
    write_json(completion / "completion.json", report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--finish", action="store_true", help="Only finish deterministic checks; preserve prior failure, no new model calls")
    args = parser.parse_args()
    if not args.finish and not args.preflight:
        parser.error("--preflight is required for a new trial")
    result = finish_checks(args.output) if args.finish else run(args.output, read_json(args.preflight))
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)
