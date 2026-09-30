import json
import sys
import threading
import time

import pytest


def runtime():
    try:
        from awb_core.execution import execute_node, Budget
        from awb_core.contracts import AWBError
    except ImportError:
        pytest.fail("Bounded execution is not implemented")
    return execute_node, Budget, AWBError


def node(code):
    return {"id": "n1", "backend": "command", "argv": [sys.executable, "-c", code],
            "allowed_executables": [sys.executable], "trusted": True, "timeout": 5,
            "output_schema": {"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}}


def test_stderr_is_separate_and_result_is_validated(tmp_path):
    run, Budget, _ = runtime()
    spec = node("import sys; print('diagnostic', file=sys.stderr); print('{\"ok\":true}')")
    result = run(spec, {}, {"workspace": tmp_path, "offline": False}, Budget(1, 10))
    assert result["status"] == "completed"
    assert result["result"] == {"ok": True}
    assert "diagnostic" in (tmp_path / result["logs"]["stderr"]).read_text()
    assert result["verification"] == "unverified"


@pytest.mark.parametrize("code,error", [
    ("import sys; print('{\"ok\":true}'); sys.exit(2)", "process_exit"),
    ("print('not json')", "invalid_output"),
    ("print('{}')", "schema"),
])
def test_failed_output_never_becomes_success(tmp_path, code, error):
    run, Budget, _ = runtime()
    result = run(node(code), {}, {"workspace": tmp_path}, Budget(1, 10))
    assert result["status"] == "failed"
    assert result["error"]["code"] == error


def test_timeout_and_budget_are_bounded(tmp_path):
    run, Budget, error = runtime()
    spec = node("import time; time.sleep(20)") | {"timeout": 0.1}
    budget = Budget(1, 3)
    result = run(spec, {}, {"workspace": tmp_path}, budget)
    assert result["status"] == "timed_out"
    assert result["elapsed_seconds"] < 3
    with pytest.raises(error, match="budget"):
        run(spec, {}, {"workspace": tmp_path}, budget)


def test_cancel_stops_owned_processes(tmp_path):
    run, Budget, _ = runtime()
    cancel = threading.Event()
    timer = threading.Timer(0.3, cancel.set)
    timer.start()
    try:
        result = run(node("import time; time.sleep(20)"), {}, {"workspace": tmp_path, "cancel": cancel}, Budget(1, 10))
    finally:
        timer.cancel()
    assert result["status"] == "cancelled"


def test_noninteractive_closes_stdin(tmp_path):
    run, Budget, _ = runtime()
    result = run(node("import sys,json; data=sys.stdin.read(); print(json.dumps({'ok':bool(data)}))"),
                 {"input": "材料"}, {"workspace": tmp_path}, Budget(1, 10))
    assert result["result"] == {"ok": True}


def test_policy_blocks_untrusted_commands_cloud_and_unknown_isolation(tmp_path):
    run, Budget, error = runtime()
    cases = [node("pass") | {"trusted": False},
             {"id": "c", "backend": "codex", "model": "test", "timeout": 1},
             node("pass") | {"require_isolation": True}]
    for spec in cases:
        with pytest.raises(error):
            run(spec, {}, {"workspace": tmp_path, "offline": True}, Budget(1, 3))


def test_missing_capability_blocks_before_start(tmp_path):
    run, Budget, error = runtime()
    spec = node("pass") | {"required_capabilities": ["filesystem_sandbox"]}
    with pytest.raises(error, match="capability"):
        run(spec, {}, {"workspace": tmp_path}, Budget(1, 3))


def test_ollama_http_normalization_and_no_redirect(tmp_path):
    try:
        from awb_core.adapters.ollama import parse_response, validate_endpoint
        from awb_core.contracts import AWBError
    except ImportError:
        pytest.fail("Ollama adapter not implemented")
    assert parse_response({"message": {"content": '{"ok":true}'}, "done": True}) == {"ok": True}
    with pytest.raises(AWBError):
        validate_endpoint("https://cloud.example.com", offline=True)
    with pytest.raises(AWBError):
        parse_response({"message": {"content": "{bad"}, "done": True})
