import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest

from awb_core.contracts import AWBError, read_json

ROOT = Path(__file__).resolve().parents[1]


def evaluator():
    spec = importlib.util.spec_from_file_location("awb_system_evaluate", ROOT / "tools/evaluate_systems.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_full_matrix_has_six_cases_four_conditions_and_120_jobs(tmp_path):
    module = evaluator()
    plan = module.prepare_matrix(read_json(ROOT / "evals/systems.json"), {"passed": False, "model": "gpt-6-sol"}, tmp_path / "matrix")
    assert plan["planned_attempts"] == 120
    assert len(plan["order"]) == 120
    assert {job["condition"] for job in plan["order"]} == {"baseline", "generic", "previous", "builder"}
    summary = read_json(tmp_path / "matrix/summary.json")
    assert summary["complete"] is False and summary["attempts"] == []
    assert summary["checkpoint"]["reason"] == "real_access_preflight_failed"


def test_matrix_budget_refuses_hidden_extra_attempts_before_output_creation(tmp_path):
    with pytest.raises(AWBError, match="budget"):
        evaluator().prepare_matrix(read_json(ROOT / "evals/systems.json"), {"passed": False}, tmp_path / "matrix", max_attempts=119)
    assert not (tmp_path / "matrix").exists()


def test_full_build_attempt_uses_actual_program_and_keeps_multiturn_script_and_limits(tmp_path):
    module = evaluator()
    class Session:
        def __init__(self, workspace, **kwargs):
            self.workspace = workspace
            self.count = 0
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def turn(self, text, timeout, event_callback):
            self.count += 1
            if self.count == 1:
                return {"state": "need_input", "question": "Should input remain intact?", "reason": "Confirm the limit"}
            (self.workspace / "app.py").write_text("print('actual verified result')\n", encoding="utf-8")
            event_callback({"method": "item/completed", "params": {"item": {"type": "fileChange"}}})
            return {"state": "done", "reason": "I passed every check"}
    case = {"id": "fixture", "family": "pure", "split": "development", "prompt": "Build a script",
            "files": {"input.txt": "preserve"}, "unchanged": ["input.txt"],
            "user_script": [{"match": ["input", "intact"], "answer": "Preserve the input."}],
            "validator": {"argv": [sys.executable, "app.py"], "stdout_contains": "actual verified result"}}
    result = module.run_attempt(case, "baseline", {"model": "fixture", "codex_home": "C:/codex"}, tmp_path / "attempt", session_factory=Session)
    assert result["artifact_checks_passed"]
    assert result["host_turns"] == 2 and result["construction_cycles"] == 1
    assert result["simulated_user"] and result["synthetic_fixture"]
    assert result["qualification"] == "not_established"
    assert len(read_json(tmp_path / "attempt/conversation.json")) == 4


def test_self_report_without_program_is_failure_and_budget_limit_is_not_retried(tmp_path):
    module = evaluator()
    class Session:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def turn(self, *args, **kwargs):
            return {"state": "continue", "reason": "All checks pass"}
    case = {"id": "fixture", "family": "pure", "split": "development", "prompt": "Build a script",
            "files": {"input.txt": "preserve"}, "unchanged": ["input.txt"], "user_script": [],
            "validator": {"argv": [sys.executable, "app.py"]}}
    result = module.run_attempt(case, "baseline", {"model": "fixture"}, tmp_path / "attempt", session_factory=Session,
                                limits={"host_turns": 3, "construction_cycles": 2, "seconds": 10})
    assert result["status"] == "budget_exhausted"
    assert result["host_turns"] == 3
    assert result["artifact_checks_passed"] is False
    assert result["hidden_retries"] == 0


def test_streaming_events_do_not_extend_the_wall_clock_deadline(tmp_path):
    module = evaluator()
    class Peer:
        def __init__(self):
            self.interrupted = False
        def start_turn(self, *args):
            return {"id": "turn"}
        def next_event(self, *args):
            time.sleep(0.01)
            return {"method": "item/agentMessage/delta", "params": {"delta": "still streaming"}}
        def interrupt(self, *args):
            self.interrupted = True
    session = module.HostSession(tmp_path, {}, tmp_path)
    session.client, session.thread_id = Peer(), "thread"
    # A callback caps the reproduction rather than hanging forever in the broken loop.
    started = time.monotonic()
    def observe(event):
        if time.monotonic() - started > 0.1:
            raise RuntimeError("deadline bypassed")
    with pytest.raises(AWBError, match="budget|deadline"):
        session.turn("build", 0.02, observe)
    assert session.client.interrupted


def test_resume_skips_old_quota_checkpoint_and_only_launches_unattempted_jobs(tmp_path, monkeypatch):
    module = evaluator()
    corpus = {"cases": [{"id": "case", "family": "pure", "split": "development"}]}
    plan = {"preflight": {"passed": True}, "limits": module.LIMITS,
            "order": [{"scenario": "case", "condition": "baseline", "repetition": 0}, {"scenario": "case", "condition": "generic", "repetition": 0}]}
    from awb_core.contracts import write_json
    for name, value in (("plan", plan), ("corpus", corpus), ("context", {}), ("host-config", {}), ("summary", {"complete": False, "qualified": False, "attempts": []})):
        write_json(tmp_path / (name + ".json"), value)
    old = {"scenario": "case", "condition": "baseline", "status": "failed", "error": {"message": "quota"}, "question_count": 0, "artifact_checks_passed": False}
    write_json(tmp_path / "attempt-001/attempt.json", old)
    monkeypatch.setattr(module, "validate_frozen", lambda *args: None)
    launched = []
    def attempt(case, condition, config, directory, **kwargs):
        launched.append(condition)
        return {"scenario": "case", "condition": condition, "status": "completed", "question_count": 0, "artifact_checks_passed": True}
    monkeypatch.setattr(module, "run_attempt", attempt)
    summary = module.evaluate(tmp_path)
    assert launched == ["generic"]
    assert len(summary["attempts"]) == 2 and summary["attempts"][0] == old


def test_external_grader_model_quota_is_an_environment_checkpoint(tmp_path):
    module = evaluator()
    checker = tmp_path / "checker.py"
    checker.write_text("import sys,json\nfrom pathlib import Path\np=Path(sys.argv[sys.argv.index('--evidence')+1]); p.mkdir(); (p/'receipt.json').write_text(json.dumps({'passed':False,'environment_error':{'code':'quota','message':'Usage limit'}})); sys.exit(1)\n")
    class Session:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def turn(self, *args, **kwargs): return {"state": "done", "reason": "ready"}
    case = {"id": "fixture", "family": "existing", "split": "development", "prompt": "Build", "files": {}, "unchanged": [], "user_script": [], "validator": {}}
    result = module.run_attempt(case, "baseline", {}, tmp_path / "attempt", session_factory=Session, checker=checker)
    assert result["status"] == "environment_error"
    assert result["environment_error"]["code"] == "quota"


def test_effective_host_configuration_changes_invalidate_frozen_matrix(tmp_path):
    module = evaluator()
    from awb_core.contracts import digest, file_digest, write_json
    matrix = tmp_path / "matrix"
    plan = module.prepare_matrix(read_json(ROOT / "evals/systems.json"), {"passed": False}, matrix)
    home = tmp_path / "fixture-home"
    home.mkdir()
    (home / "config.toml").write_text('model="gpt-6-sol"')
    config = {"model": "gpt-6-sol", "reasoning_effort": "max", "codex_home": str(home), "executable": sys.executable, "sandbox": "workspace-write"}
    plan["preflight"] = {"passed": True, "model": "gpt-6-sol", "codex_home": str(home), "config_sha256": file_digest(home / "config.toml"), "binary_sha256": file_digest(sys.executable)}
    module.freeze_context(matrix)
    context = read_json(matrix / "context.json") | {"host_config_sha256": digest(config)}
    plan["frozen_context_sha256"] = digest(context)
    module.validate_frozen(matrix, plan, config, context)
    for changed in (config | {"sandbox": "read-only"}, config | {"model": "other"}, config | {"config_overrides": {"skills.config": []}}):
        with pytest.raises(AWBError, match="Frozen"):
            module.validate_frozen(matrix, plan, changed, context)


def test_skill_disable_overlay_uses_native_reported_entrypoint_paths(tmp_path):
    module = evaluator()
    path = tmp_path / "skill/SKILL.md"
    overlay = module.disabled_skill_overlay({"data": [{"skills": [{"path": str(path)}]}]})
    assert overlay == [{"path": str(path.resolve()), "enabled": False}]


def test_native_cli_integration_overlay_does_not_create_quoted_server_names():
    module = evaluator()
    assert module.disabled_integrations({"mcp_servers": {"node_repl": {}}, "plugins": {"awb@personal": {}}}) == {
        "mcp_servers.node_repl.enabled": False, "plugins.awb@personal.enabled": False}
