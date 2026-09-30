import json
from pathlib import Path

import pytest


def api():
    try:
        from awb_core.state import Store
        from awb_core.contracts import AWBError, validate_record
    except ImportError:
        pytest.fail("Persistent contracts and state are not implemented")
    return Store, AWBError, validate_record


def goal():
    return {"schema_version": 1, "id": "goal-1", "revision": 1,
            "text": "Classify materials without changing sources", "requirements": [
                {"id": "R1", "text": "Keep sources unchanged", "source": "user",
                 "kind": "hard", "status": "confirmed"}], "offline": True}


def test_rejects_unsupported_schema_and_inferred_hard_constraint():
    _, error, validate = api()
    bad = goal() | {"schema_version": 9}
    with pytest.raises(error, match="schema"):
        validate("goal", bad)
    bad = goal()
    bad["requirements"][0]["source"] = "inference"
    with pytest.raises(error, match="confirmed"):
        validate("goal", bad)


def test_stale_revision_and_restart_preserve_history(tmp_path):
    Store, error, _ = api()
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Validate quoted sources", "goal_revision": 1})
    db.record_transition(cycle["id"], 1, "implementing", [])
    with pytest.raises(error, match="revision"):
        db.record_transition(cycle["id"], 1, "cancelled", [])
    restored = Store(tmp_path)
    assert restored.get(cycle["id"])["status"] == "implementing"
    assert len(restored.history(cycle["id"])) == 2


def test_acceptance_requires_valid_bound_evidence(tmp_path):
    Store, error, _ = api()
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Check result", "goal_revision": 1})
    db.record_transition(cycle["id"], 1, "implementing", [])
    db.record_transition(cycle["id"], 2, "verifying", [])
    db.record_transition(cycle["id"], 3, "deciding", [])
    with pytest.raises(error, match="evidence"):
        db.record_transition(cycle["id"], 4, "accepted", [])
    item = tmp_path / "result.txt"
    item.write_text("verified", encoding="utf-8")
    ev = db.add_evidence(cycle["id"], [item], {"correct": True}, {"goal_revision": 1})
    item.write_text("changed", encoding="utf-8")
    with pytest.raises(error, match="(?i)evidence"):
        db.record_transition(cycle["id"], 4, "accepted", [ev["id"]])


def test_goal_change_retains_history_and_invalidates_approval(tmp_path):
    Store, error, _ = api()
    db = Store.initialize(tmp_path, goal())
    request = db.request_review("run-1", "abc", ["classify"], {"item": "a"})
    db.approve(request["id"], {"category": "research"}, "user")
    assert db.review_answer(request["id"], "abc", 1)["category"] == "research"
    db.update_goal(goal() | {"revision": 2, "text": "Changed goal"}, 1)
    with pytest.raises(error, match="stale"):
        db.review_answer(request["id"], "abc", 2)
    assert db.goal()["revision"] == 2
    assert json.loads((db.root / "goals" / "000001.json").read_text(encoding="utf-8"))["text"].startswith("Classify")


def test_goal_mirror_drift_is_detected(tmp_path):
    Store, error, _ = api()
    db = Store.initialize(tmp_path, goal())
    (db.root / "goal.json").write_text('{"manually":"changed"}', encoding="utf-8")
    with pytest.raises(error, match="drift"):
        db.goal()


def test_path_escape_is_rejected(tmp_path):
    Store, error, _ = api()
    db = Store.initialize(tmp_path, goal())
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    with pytest.raises(error, match="outside"):
        db.add_evidence("cycle-1", [outside], {"ok": True}, {})
