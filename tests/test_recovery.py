import json
import sys
import pytest

from test_state import goal
from test_scheduler import node


def test_unordered_graph_reuses_topological_results(tmp_path):
    from awb_core.scheduler import run_graph
    from awb_core.state import Store
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    graph = {"nodes": [node("c", ["a", "b"]), node("a"), node("b")]}
    first = run_graph(db, graph, {}, 3, 10, 2)
    again = run_graph(db, graph, {}, 3, 10, 2, first["id"])
    assert again["status"] == "completed"
    assert again["reused_nodes"] == 3


def test_candidate_acceptance_needs_semantic_reference(tmp_path):
    from awb_core.state import Store
    from awb_core.materials import run_materials
    from awb_core.verification import verify_candidate
    from awb_core.contracts import AWBError
    db = Store.initialize(tmp_path, goal())
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "a.txt").write_text("Research results", encoding="utf-8")
    result = run_materials(db, folder)
    cycle = db.create("cycle", {"hypothesis": "Classify correctly"})
    with pytest.raises(AWBError, match="reference"):
        verify_candidate({"store": db, "cycle_id": cycle["id"]}, {"kind": "materials", "run_id": result["id"]})


def test_cancel_request_is_applied_when_resuming_waiting_run(tmp_path):
    from awb_core.state import Store
    from awb_core.materials import run_materials, resume_materials
    from awb_core.contracts import write_json
    db = Store.initialize(tmp_path, goal())
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "a.txt").write_text("uncertain", encoding="utf-8")
    run = run_materials(db, folder)
    write_json(db.root / "cancellations" / (run["id"] + ".json"), {"requested": True})
    assert resume_materials(db, run["id"])["status"] == "cancelled"


def test_completed_parent_corruption_invalidates_dependent_result(tmp_path):
    from awb_core.scheduler import run_graph
    from awb_core.state import Store
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    graph = {"nodes": [node("a") | {"side_effect": "none"}, node("b", ["a"]) | {"side_effect": "none"}]}
    result = run_graph(db, graph, {}, 4, 10)
    (tmp_path / result["nodes"]["a"]["output_path"]).write_text("tampered")
    again = run_graph(db, graph, {}, 4, 10, run_id=result["id"])
    assert again["status"] == "completed"
    assert again["calls_reserved"] >= 3


def test_candidate_verification_captures_deleted_targets(tmp_path):
    from awb_core.state import Store
    from awb_core.generation import prepare_change, apply_change
    from awb_core.materials import run_materials
    from awb_core.verification import verify_candidate
    from awb_core.contracts import file_digest, AWBError
    db = Store.initialize(tmp_path, goal())
    old = tmp_path / "old.txt"
    old.write_text("old")
    change = prepare_change({"files": {"old.txt": file_digest(old)}}, {"files": {"old.txt": None}}, db)
    apply_change(db, change)
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "a.txt").write_text("Research", encoding="utf-8")
    run = run_materials(db, folder)
    cycle = db.create("cycle", {"hypothesis": "Remove obsolete file"})
    ev = verify_candidate({"store": db, "cycle_id": cycle["id"], "change_id": change["id"]},
                          {"kind": "materials", "run_id": run["id"], "reference": {"a.txt": "research"}})
    old.write_text("returned")
    with pytest.raises(AWBError):
        db.check_evidence(ev["id"])


def test_goal_drift_cannot_forge_known_historical_revision(tmp_path):
    from awb_core.state import Store
    from awb_core.contracts import AWBError
    db = Store.initialize(tmp_path, goal())
    malicious = goal() | {"revision": 2, "text": "manual"}
    (db.root / "goals" / "000002.json").write_text(json.dumps(malicious))
    (db.root / "goal.json").write_text(json.dumps(malicious))
    with pytest.raises(AWBError, match="drift"):
        db.goal()
