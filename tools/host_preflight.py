"""Explicit, bounded access preflight of the approved Codex host. No key provisioning."""
import argparse
import json
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
from awb_core.adapters.codex import executable
from awb_core.adapters.app_server import AppServerClient
from awb_core.intelligence import app_server_command
from awb_core.contracts import AWBError, file_digest, write_json
from awb_core.execution import execute_node, Budget


def preflight(output, timeout=60, model="gpt-6.1-sol"):
    if not 0 < timeout <= 120:
        raise AWBError("budget", "Preflight timeout must be between zero and 120 seconds")
    output = Path(output).resolve()
    if output.exists():
        raise AWBError("evaluation", "Use a fresh preflight directory; preserve previous attempts")
    home = Path("C:/codex")
    # Read only nonsecret selected fields into the public receipt. No credential contents or provider headers.
    config_path = home / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    binary = executable({})
    version = subprocess.run([binary, "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10).stdout.strip()
    report = {"schema_version": 1, "codex_home": str(home), "host_version": version,
              "model": model, "base_config_model": config.get("model"), "reasoning_effort": config.get("model_reasoning_effort"),
              "binary_sha256": file_digest(binary), "config_sha256": file_digest(config_path),
              "auth_present": (home / "auth.json").is_file(), "cost": None, "tokens": None, "checks": {}}
    output.mkdir(parents=True)
    write_json(output / "receipt.json", report)
    if (version, report["base_config_model"], report["reasoning_effort"]) != ("codex-cli 0.158.0", "gpt-6.1-sol", "max"):
        report.update(passed=False, blocker="Approved host/model/config do not match; no inference attempted")
        write_json(output / "receipt.json", report)
        return report
    cfg = {"backend": "codex", "id": "access", "executable": binary, "model": model,
           "reasoning_effort": "max", "codex_home": str(home), "timeout": timeout, "retries": 0,
           "sandbox": "read-only", "approval_policy": "never", "inherit_user_config": True, "inherit_rules": True}
    schema = {"type": "object", "properties": {"ok": {"type": "boolean", "enum": [True]}},
              "required": ["ok"], "additionalProperties": False}
    workspace = output / "workspace"
    workspace.mkdir()
    cfg.update(output_schema=schema, cwd=str(workspace))
    result = execute_node(cfg, {"instruction": "Return only {\"ok\":true}. Do not use tools, access files or make other requests."},
                          {"workspace": output / "exec", "project": workspace}, Budget(1, timeout))
    report["checks"]["noninteractive"] = {"passed": result["status"] == "completed" and result["result"] == {"ok": True},
        "status": result["status"], "attempt_id": result["attempt_id"], "elapsed_seconds": result["elapsed_seconds"],
        "error_code": result.get("error", {}).get("code")}
    write_json(output / "receipt.json", report)
    started = time.monotonic()
    try:
        with AppServerClient(app_server_command(cfg), workspace, output / "interactive", cfg, timeout=min(timeout, 20)) as client:
            thread_id = client.start_thread()
            turn = client.start_turn(thread_id, 'Return only {"ok":true}. No tools or file access.', schema)
            messages = []
            deadline = started + timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    client.interrupt(thread_id, turn["id"])
                    raise AWBError("budget", "Preflight wall-clock deadline exhausted")
                event = client.next_event(timeout=remaining)
                if event.get("id") is not None:
                    raise AWBError("approval", "No-tools preflight unexpectedly requested user approval")
                if event.get("method") == "item/completed" and event.get("params", {}).get("item", {}).get("type") == "agentMessage":
                    messages.append(event["params"]["item"].get("text", ""))
                if event.get("method") == "turn/completed" and event["params"]["turn"]["id"] == turn["id"]:
                    status = event["params"]["turn"]["status"]
                    break
            passed = status == "completed" and any(json.loads(message) == {"ok": True} for message in messages)
            report["checks"]["interactive"] = {"passed": passed, "status": status, "thread_id": thread_id, "turn_id": turn["id"]}
    except (AWBError, OSError, ValueError) as exc:
        report["checks"]["interactive"] = {"passed": False, "status": "failed", "error_code": getattr(exc, "code", "transport")}
    report["checks"]["interactive"]["elapsed_seconds"] = time.monotonic() - started
    report["passed"] = all(c["passed"] for c in report["checks"].values())
    report["matrix_authorized_to_start"] = report["passed"]
    write_json(output / "receipt.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--model", default="gpt-6.1-sol", help="Explicit user-approved model override; does not edit the host configuration")
    args = parser.parse_args()
    receipt = preflight(args.output, args.timeout, args.model)
    print(json.dumps(receipt, ensure_ascii=False))
    raise SystemExit(0 if receipt["passed"] else 1)
