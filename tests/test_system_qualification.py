import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def qualifier():
    spec = importlib.util.spec_from_file_location("awb_qualification", ROOT / "tools/qualify_systems.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_qualification_never_treats_self_report_or_partial_matrix_as_release(tmp_path):
    report = qualifier().audit_attempt({"status": "completed", "artifact_checks_passed": True,
        "host_turns": 1, "construction_cycles": 1, "elapsed_seconds": 2,
        "hidden_retries": 0, "synthetic_fixture": False, "simulated_user": True,
        "artifact_checks": {"actual_program": False}, "family": "pure"}, tmp_path)
    assert not report["actual_artifact_pass"]
    assert report["human_trial"] == "pending"
    assert report["release_qualified"] is False


def test_budgets_and_preservation_are_observed_hard_constraints(tmp_path):
    report = qualifier().audit_attempt({"status": "budget_exhausted", "artifact_checks_passed": False,
        "host_turns": 31, "construction_cycles": 9, "elapsed_seconds": 901,
        "hidden_retries": 1, "synthetic_fixture": False, "simulated_user": True,
        "artifact_checks": {"preserved:input.csv": False}, "family": "pure"}, tmp_path)
    assert set(report["hard_constraint_violations"]) == {
        "host_turns", "construction_cycles", "seconds", "hidden_retries", "preserved:input.csv"}


def test_workbench_gate_requires_node_result_binding_not_only_a_call(tmp_path):
    evidence = tmp_path / "validation"
    (evidence / "gateway").mkdir(parents=True)
    (evidence / "gateway/calls.json").write_text(json.dumps([
        {"mode": "interactive", "status": "completed", "text": "discussion"},
        {"mode": "noninteractive", "status": "completed", "text": '{"sum":5}'}]), encoding="utf-8")
    (tmp_path / "case.json").write_text(json.dumps({"task": {"expected": {"sum": 5}}}), encoding="utf-8")
    report = qualifier().audit_attempt({"status": "completed", "artifact_checks_passed": True,
        "host_turns": 1, "construction_cycles": 1, "elapsed_seconds": 2,
        "hidden_retries": 0, "synthetic_fixture": False, "simulated_user": True,
        "artifact_checks": {"actual_program": True}, "family": "workbench"}, tmp_path)
    assert report["node_answer_matches_expected"] is True
    # Even a correct actual node answer does not prove the target used it.
    assert "target_output_bound_to_node" in report["pending_checks"]
    assert "reject_wrong_node_result" in report["pending_checks"]
    assert not report["release_qualified"]
