import json
import sys
import tomllib

import pytest

from awb_core.adapters.codex import argv
from awb_core.contracts import AWBError
from test_system_contracts import profile


def test_nested_resource_overrides_are_valid_toml_for_both_codex_modes(tmp_path):
    from awb_core.intelligence import app_server_command
    config = {"executable": sys.executable, "model": "gpt-6-sol",
              "config_overrides": {"skills.config": [{"path": "C:/a/SKILL.md", "enabled": False}]}}
    for args in (argv(config, tmp_path, tmp_path / "s", tmp_path / "f"), app_server_command(config)):
        setting = args[args.index("-c") + 1]
        assert tomllib.loads(setting)["skills"]["config"][0]["enabled"] is False


def test_exec_inherits_working_provider_and_rules_and_can_write_when_authorized(tmp_path):
    config = {"executable": sys.executable, "model": "gpt-6.1-sol", "reasoning_effort": "max"}
    args = argv(config, tmp_path, tmp_path / "schema.json", tmp_path / "final.json")
    assert "--ignore-user-config" not in args and "--ignore-rules" not in args
    assert args[args.index("--sandbox") + 1] == "read-only"
    with pytest.raises(AWBError, match="authorized"):
        argv(config | {"sandbox": "workspace-write"}, tmp_path, tmp_path / "s", tmp_path / "f")
    args = argv(config | {"sandbox": "workspace-write", "workspace_write_authorized": True}, tmp_path, tmp_path / "s", tmp_path / "f")
    assert args[args.index("--sandbox") + 1] == "workspace-write"
    assert args[args.index("-C") + 1] == str(tmp_path)


def test_profile_compiler_preserves_host_and_refuses_unverified_resources(tmp_path):
    from awb_core.intelligence import compile_profile
    p = profile() | {"mode": "mixed", "model": "gpt-6.1-sol", "codex_home": str(tmp_path), "reasoning_effort": "max"}
    cfg = compile_profile(p)
    assert cfg["codex_home"] == str(tmp_path.resolve())
    assert cfg["inherit_user_config"] and cfg["inherit_rules"]
    assert cfg["model"] == "gpt-6.1-sol"
    resource = {"id": "x", "kind": "mcp", "source": "https://example.test", "version": None, "license": None,
                "compatibility": "unknown", "operation": "use"}
    with pytest.raises(AWBError, match="compatibility"):
        compile_profile(p | {"resources": [resource]})


def test_app_server_handles_events_sessions_and_explicit_approval(tmp_path):
    from awb_core.adapters.app_server import AppServerClient
    # Actual stdio peer validates messages; no model call. Real transport and owned process.
    peer = tmp_path / "peer.py"
    peer.write_text('''import json,sys
thread="thread-1"
for line in sys.stdin:
 msg=json.loads(line)
 if "method" not in msg: continue
 method=msg["method"]
 if method=="initialized": continue
 result={}
 if method=="thread/start":
  assert msg["params"]["model"]=="gpt-6.1-sol"
  assert msg["params"]["sandbox"]=="read-only"
  result={"thread":{"id":thread}}
 if method=="thread/resume":
  assert msg["params"]["threadId"]==thread
  result={"thread":{"id":thread}}
 if method=="turn/start":
  assert msg["params"]["threadId"]==thread
  result={"turn":{"id":"turn-1","status":"inProgress"}}
 print(json.dumps({"id":msg["id"],"result":result}),flush=True)
 if method=="turn/start":
  print(json.dumps({"id":900,"method":"item/commandExecution/requestApproval","params":{"threadId":thread,"turnId":"turn-1"}}),flush=True)
  reply=json.loads(next(sys.stdin)); assert reply=={"id":900,"result":{"decision":"decline"}}
  print(json.dumps({"method":"turn/completed","params":{"threadId":thread,"turn":{"id":"turn-1","status":"completed"}}}),flush=True)
''', encoding="utf-8")
    cfg = {"model": "gpt-6.1-sol", "sandbox": "read-only", "approval_policy": "on-request"}
    with AppServerClient([sys.executable, "-u", str(peer)], tmp_path, tmp_path / "logs", cfg, timeout=3) as client:
        thread = client.start_thread()
        assert thread == "thread-1"
        assert client.resume_thread(thread) == thread
        assert client.start_turn(thread, "Discuss a task")["id"] == "turn-1"
        approval = client.next_event()
        assert approval["id"] == 900
        client.respond_approval(900, {"decision": "decline"})
        assert client.next_event()["params"]["turn"]["status"] == "completed"
        with pytest.raises(AWBError, match="pending"):
            client.respond_approval(900, {"decision": "accept"})
    assert (tmp_path / "logs/events.jsonl").is_file()


def test_app_server_dead_peer_is_a_bounded_failure(tmp_path):
    from awb_core.adapters.app_server import AppServerClient
    with pytest.raises(AWBError, match="closed|exited"):
        with AppServerClient([sys.executable, "-c", "pass"], tmp_path, tmp_path / "logs", {}, timeout=1):
            pass


def test_codex_actual_error_event_preserves_quota_for_checkpointing(tmp_path):
    from awb_core.adapters.codex import failure_error
    events = tmp_path / "events.jsonl"
    events.write_text(json.dumps({"type": "error", "message": "You have hit your usage limit. Try again later."}) + "\n", encoding="utf-8")
    assert failure_error(events).code == "quota"
