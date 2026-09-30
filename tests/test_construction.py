import pytest
from test_state import goal


def modules():
    try:
        from awb_core.generation import prepare_change, apply_change, rollback_change
        from awb_core.cycle import apply_decision, stagnation
        from awb_core.intent import propose_next_action
        from awb_core.state import Store
        from awb_core.contracts import AWBError
    except ImportError:
        pytest.fail("Construction loop is not implemented")
    return prepare_change, apply_change, rollback_change, apply_decision, stagnation, propose_next_action, Store, AWBError


def test_user_edits_are_preserved_during_apply_and_rollback(tmp_path):
    prepare, apply, rollback, _, _, _, Store, error = modules()
    db = Store.initialize(tmp_path, goal())
    plan = prepare({"files": {}}, {"files": {"pipeline.py": "first"}}, db)
    apply(db, plan)
    assert (tmp_path / "pipeline.py").read_text() == "first"
    (tmp_path / "pipeline.py").write_text("user edit")
    with pytest.raises(error, match="drift"):
        rollback(db, plan["id"])
    assert (tmp_path / "pipeline.py").read_text() == "user edit"


def test_change_rollback_preserves_original_and_unrelated_files(tmp_path):
    prepare, apply, rollback, _, _, _, Store, _ = modules()
    from awb_core.contracts import file_digest
    db = Store.initialize(tmp_path, goal())
    existing = tmp_path / "pipeline.py"
    existing.write_text("baseline")
    other = tmp_path / "user.txt"
    other.write_text("untouched")
    plan = prepare({"files": {"pipeline.py": file_digest(existing)}}, {"files": {"pipeline.py": "candidate", "new.txt": "added"}}, db)
    apply(db, plan)
    rollback(db, plan["id"])
    assert existing.read_text() == "baseline"
    assert not (tmp_path / "new.txt").exists()
    assert other.read_text() == "untouched"


def test_unowned_existing_file_and_state_paths_cannot_be_generated(tmp_path):
    prepare, _, _, _, _, _, Store, error = modules()
    db = Store.initialize(tmp_path, goal())
    (tmp_path / "user.txt").write_text("mine")
    for path in ["user.txt", "../escape", ".worksystem-build/goal.json", ".git/config"]:
        with pytest.raises(error):
            prepare({"files": {}}, {"files": {path: "new"}}, db)


def test_failed_evidence_cannot_accept_candidate(tmp_path):
    _, _, _, decide, _, _, Store, error = modules()
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Classify ambiguities"})
    for status in ["implementing", "verifying", "deciding"]:
        cycle = db.record_transition(cycle["id"], cycle["revision"], status, [])
    result = tmp_path / "result.json"
    result.write_text('{}')
    ev = db.add_evidence(cycle["id"], [result], {"task_correct": False}, {"goal_revision": 1})
    with pytest.raises(error):
        decide(db, cycle["id"], {"action": "accept", "reason": "Looks fine", "evidence_refs": [ev["id"]]})
    assert db.get(cycle["id"])["status"] == "deciding"


def test_stagnation_changes_next_action():
    _, _, _, _, check, _, _, _ = modules()
    assert check([{"hypothesis": "x", "refuted": True}] * 2) == "reassess"
    assert check([{"hypothesis": str(i), "progress": False, "uncertainty_reduced": False} for i in range(3)]) == "needs_human"


def test_interview_uses_answers_and_prefers_environment_probe():
    _, _, _, _, _, propose, _, _ = modules()
    g = goal() | {"answers": {"purpose": "classify"}, "existing_pipeline": True}
    result = propose(g, {}, [{"id": "purpose", "impact": 10}, {"id": "backend", "impact": 5, "probe": "backend"}])
    assert result["action"] == "probe"
    assert result["uncertainty_id"] == "backend"
    assert result["constraints"]["offline"] is True
    assert propose(g, {}, [])['strategy'] == "incremental"
