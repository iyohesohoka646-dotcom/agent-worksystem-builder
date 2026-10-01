import json

import pytest

from awb_core.contracts import AWBError, validate_record
from awb_core.state import Store
from test_state import goal
from test_cli import invoke


def architecture():
    return {"schema_version": 1, "goal_revision": 1, "title": "Standalone program",
            "components": [{"id": "cli", "kind": "program", "technology": "Python"}],
            "interfaces": [], "dependencies": [],
            "entrypoints": [{"id": "main", "component_id": "cli", "argv": ["python", "main.py"]}],
            "acceptance": [{"id": "keep", "requirement_ids": ["R1"], "verifier": "artifact", "config": {}}],
            "intelligence_profile_id": None, "decisions": []}


def profile():
    return {"schema_version": 1, "goal_revision": 1, "mode": "none", "model": None,
            "resources": [], "context": {"inherit_user_config": True, "inherit_rules": True},
            "permissions": {"sandbox": "read-only", "approval_policy": "untrusted"},
            "budget": {"max_calls": 0, "max_seconds": 60}, "decisions": []}


def exploration():
    return {"schema_version": 1, "goal_revision": 1,
            "question": {"id": "storage", "text": "Choose storage", "impact": 8, "uncertainty": 0.8,
                         "discoverable": True, "consequential": False},
            "strategy": {"method": "environment", "reason": "Inspect existing persistence before proposing changes"},
            "candidates": [{"id": "existing", "description": "Reuse existing store", "status": "open", "evidence_refs": []}],
            "evidence": [], "decision": None}


def test_contracts_allow_pure_program_and_reject_broken_component_references():
    assert validate_record("architecture", architecture())["intelligence_profile_id"] is None
    assert validate_record("profile", profile())["mode"] == "none"
    assert validate_record("exploration", exploration())["decision"] is None
    bad = architecture()
    bad["entrypoints"][0]["component_id"] = "missing"
    with pytest.raises(AWBError, match="component"):
        validate_record("architecture", bad)


def test_contracts_version_and_duplicate_ids_are_not_silently_accepted():
    with pytest.raises(AWBError, match="schema"):
        validate_record("profile", profile() | {"schema_version": 2})
    bad = architecture()
    bad["components"] *= 2
    with pytest.raises(AWBError, match="unique"):
        validate_record("architecture", bad)


def test_goal_change_reopens_decisions_and_preserves_original_request(tmp_path):
    db = Store.initialize(tmp_path, goal())
    e = db.record_contract("exploration", exploration() | {"decision": {"choice": "existing", "reason": "Already available", "reopen_when": ["Goal changes"]}})
    a = db.record_contract("architecture", architecture())
    db.update_goal(goal() | {"revision": 2, "text": "Now build a service"}, 1)
    restored = Store(tmp_path)
    assert restored.original_goal()["text"] == "Classify materials without changing sources"
    assert restored.get(e["id"])["status"] == "reopened"
    assert restored.get(a["id"])["status"] == "stale"
    assert len(restored.history(e["id"])) == 2
    assert restored.list("profile") == []  # Do not invent historical profiles.


def test_contract_update_requires_revision_and_uses_existing_state_database(tmp_path):
    db = Store.initialize(tmp_path, goal())
    a = db.record_contract("architecture", architecture())
    changed = architecture() | {"title": "Version two"}
    with pytest.raises(AWBError, match="revision"):
        db.record_contract("architecture", changed, a["id"], 0)
    db.record_contract("architecture", changed, a["id"], 1)
    assert Store(tmp_path).get(a["id"])["title"] == "Version two"
    assert len(db.history(a["id"])) == 2


def test_consequential_resource_decision_pauses_execution_not_recording(tmp_path):
    db = Store.initialize(tmp_path, goal())
    p = db.record_contract("profile", profile() | {"decisions": [{"id": "data", "question": "May data leave this machine?", "consequential": True}]})
    assert p["status"] == "needs_human"
    with pytest.raises(AWBError, match="decision"):
        db.require_contract(p["id"], "profile")
    review = db.list("review")[0]
    db.approve(review["id"], {"approved": True}, "simulated-user")
    assert db.require_contract(p["id"], "profile")["mode"] == "none"
    db.record_contract("profile", profile() | {"model": "different"}, p["id"], p["revision"])
    with pytest.raises(AWBError, match="stale"):
        db.review_answer(review["id"], "changed", 1)


def test_cli_records_and_queries_all_three_contracts(tmp_path):
    Store.initialize(tmp_path, goal())
    for command, data in [("architecture", architecture()), ("profile", profile()), ("explore", exploration())]:
        source = tmp_path / (command + ".json")
        source.write_text(json.dumps(data), encoding="utf-8")
        result = invoke(tmp_path, command, "--file", str(source))
        assert result.returncode == 0, result.stderr + result.stdout
        saved = json.loads(result.stdout)
        queried = invoke(tmp_path, command, "--id", saved["id"])
        assert json.loads(queried.stdout)["id"] == saved["id"]
        assert len(json.loads(invoke(tmp_path, command).stdout)) == 1


def test_exploration_uses_saved_answers_and_reopens_on_new_evidence(tmp_path):
    from awb_core.exploration import next_action, answer_question, reopen_question
    db = Store.initialize(tmp_path, goal())
    issue = db.record_contract("exploration", exploration())
    assert next_action(db)["action"] == "probe"
    answer_question(db, issue["id"], {"choice": "existing", "reason": "Discovered an installed store"}, "environment")
    assert next_action(Store(tmp_path))["action"] == "propose_change"
    reopen_question(db, issue["id"], "The persistence interface failed a trial")
    assert next_action(db)["uncertainty_id"] == "storage"


def test_exploration_budget_exhaustion_keeps_checkpoint(tmp_path):
    from awb_core.exploration import next_action
    db = Store.initialize(tmp_path, goal() | {"budget": {"max_calls": 2, "used_calls": 2}})
    db.record_contract("exploration", exploration())
    assert next_action(db)["action"] == "budget_exhausted"
    assert Store(tmp_path).list("exploration")[0]["status"] == "open"


def test_reopened_question_overrides_a_previous_goal_answer(tmp_path):
    from awb_core.exploration import next_action, reopen_question
    db = Store.initialize(tmp_path, goal() | {"answers": {"storage": "reuse"}})
    e = db.record_contract("exploration", exploration())
    reopen_question(db, e["id"], "Observed backend failure invalidates the old answer")
    assert next_action(db)["uncertainty_id"] == "storage"


def test_architecture_cannot_bypass_its_embedded_pending_intelligence_profile(tmp_path):
    db = Store.initialize(tmp_path, goal())
    p = db.record_contract("profile", profile() | {"decisions": [{"id": "privacy", "question": "Approve data destination?", "consequential": True}]})
    a = db.record_contract("architecture", architecture() | {"intelligence_profile_id": p["id"]})
    cycle = db.create("cycle", {"hypothesis": "Cannot bypass selected privacy profile", "architecture_id": a["id"]})
    with pytest.raises(AWBError, match="decision"):
        db.require_contract(a["id"], "architecture")
    with pytest.raises(AWBError, match="decision"):
        db.record_transition(cycle["id"], cycle["revision"], "implementing", [])
