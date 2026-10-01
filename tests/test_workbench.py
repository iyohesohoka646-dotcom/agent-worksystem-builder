import importlib.util
import json
import threading
import urllib.request
from pathlib import Path

import pytest

from awb_core.contracts import AWBError
from test_system_contracts import profile

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location("awb_example_workbench", ROOT / "examples/task-workbench/workbench.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_task_versions_approval_and_restart_keep_business_state_separate(tmp_path):
    app = module().Workbench(tmp_path, profile())
    task = app.create_task("Count three items", {"count": 3}, "a\nb\nc")
    app.approve(task["id"], 1)
    app.update_task(task["id"], 1, "Count four items", {"count": 4}, "a\nb\nc\nd")
    with pytest.raises(AWBError, match="approval|version"):
        app.execute(task["id"])
    restarted = module().Workbench(tmp_path, profile())
    assert restarted.task(task["id"])["version"] == 2
    assert restarted.task(task["id"])["status"] == "draft"
    assert (tmp_path / "workbench.sqlite").is_file()
    assert not (tmp_path / ".worksystem-build").exists()


def test_execution_uses_real_artifacts_not_executor_claims_and_keeps_failures(tmp_path):
    app = module().Workbench(tmp_path, profile())
    task = app.create_task("Count three items", {"count": 3}, "a\nb\nc")
    app.approve(task["id"], 1)
    def bad_executor(task, workspace, logs):
        (workspace / "result.json").write_text('{"count":2}', encoding="utf-8")
        return {"status": "completed", "result": {"all_tests_passed": True}}
    result = app.execute(task["id"], executor=bad_executor)
    assert result["status"] == "failed"
    assert result["verification"]["output_matches"] is False
    assert module().Workbench(tmp_path, profile()).attempts(task["id"])[0]["status"] == "failed"
    with pytest.raises(AWBError, match="attempt|version"):
        app.execute(task["id"], executor=bad_executor)


def test_user_changed_inputs_invalidate_approval_before_executor_starts(tmp_path):
    app = module().Workbench(tmp_path, profile())
    task = app.create_task("Count items", {"count": 1}, "one")
    app.approve(task["id"], 1)
    (app.workspace(task["id"]) / "input.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(AWBError, match="drift|approval"):
        app.execute(task["id"], executor=lambda *args: pytest.fail("Stale approval executed"))


def test_local_http_service_serves_ui_and_persistent_task_api(tmp_path):
    wb = module()
    app = wb.Workbench(tmp_path, profile())
    server = wb.make_server(app, port=0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert b"Task workbench" in urllib.request.urlopen(base).read()
        body = json.dumps({"goal": "Count", "expected": {"count": 2}, "input": "a\nb"}).encode()
        request = urllib.request.Request(base + "/api/tasks", data=body, headers={"Content-Type": "application/json", "Origin": base})
        created = json.load(urllib.request.urlopen(request))
        assert created["status"] == "draft"
        unapproved = urllib.request.Request(base + "/api/execute", data=json.dumps({"id": created["id"]}).encode(), headers={"Content-Type": "application/json"})
        with pytest.raises(urllib.error.HTTPError) as unapproved_error:
            urllib.request.urlopen(unapproved)
        assert unapproved_error.value.code == 400
        assert json.load(urllib.request.urlopen(base + "/api/tasks"))[0]["goal"] == "Count"
        denied = urllib.request.Request(base + "/api/tasks", data=body,
                    headers={"Content-Type": "application/json", "Origin": "https://unrelated.example"})
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(denied)
        assert exc.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
        app.close()


def test_process_restart_retains_interrupted_attempt_not_running_forever(tmp_path):
    app = module().Workbench(tmp_path, profile())
    task = app.create_task("Count", {"count": 1}, "a")
    with app.db() as db:
        task["status"] = "running"
        app._save(db, task)
        db.execute("INSERT INTO attempts VALUES (?,?,?,?)", ("interrupted", task["id"], 1, json.dumps({"id": "interrupted", "status": "running"})))
    restored = module().Workbench(tmp_path, profile())
    assert restored.attempts(task["id"])[0]["status"] == "interrupted"
    assert restored.task(task["id"])["status"] == "needs_human"


def test_interactive_zero_call_budget_stops_before_transport_start(tmp_path, monkeypatch):
    wb = module()
    p = profile() | {"mode": "interactive", "model": "gpt-6-sol", "budget": {"max_calls": 0, "max_seconds": 30}}
    app = wb.Workbench(tmp_path, p)
    task = app.create_task("Count", {"count": 1}, "a")
    monkeypatch.setattr(wb, "AppServerClient", lambda *args, **kwargs: pytest.fail("Zero budget started transport"))
    with pytest.raises(AWBError, match="budget"):
        app.discuss(task["id"], "Discuss")
