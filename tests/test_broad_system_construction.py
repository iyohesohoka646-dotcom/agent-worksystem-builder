"""Multi-component runtime regression, not a model/human qualification trial."""
import json
import sys

from awb_core.cycle import apply_decision
from awb_core.delivery import check_delivery, coverage
from awb_core.generation import apply_change, prepare_change
from awb_core.state import Store
from awb_core.verification import verify_candidate


def accept(db, architecture_id, acceptance):
    cycle = db.create("cycle", {"hypothesis": "Verify one component of the whole system",
        "architecture_id": architecture_id, "requirement_ids": acceptance["requirement_ids"]})
    evidence = verify_candidate({"store": db, "cycle_id": cycle["id"]}, acceptance)
    assert evidence["passed"]
    for status in ("implementing", "verifying", "deciding"):
        cycle = db.record_transition(cycle["id"], cycle["revision"], status, [])
    apply_decision(db, cycle["id"], {"action": "accept", "reason": "Actual component execution passed",
        "evidence_refs": [evidence["id"]]})
    return evidence


def test_multiple_components_tasks_and_launches_need_whole_goal_coverage(tmp_path):
    goal = {"schema_version": 1, "id": "system-goal", "revision": 1,
        "text": "Deliver project/task persistence and a separate report program; no intelligence is needed.",
        "offline": True, "requirements": [
            {"id": "projects", "text": "Persist multiple projects with multiple tasks", "source": "user", "kind": "acceptance", "status": "confirmed"},
            {"id": "reports", "text": "Another component consumes stored tasks and creates a report", "source": "user", "kind": "acceptance", "status": "confirmed"}]}
    db = Store.initialize(tmp_path, goal)
    files = {
        "projects.py": "import json\nfrom pathlib import Path\np={'projects':[{'id':'A','tasks':['design','build']},{'id':'B','tasks':['verify','deliver']}]}\nPath('business.json').write_text(json.dumps(p))\nprint('projects persisted')\n",
        "reports.py": "import json\nfrom pathlib import Path\np=json.loads(Path('business.json').read_text())\nhtml='<html>'+''.join('<section>'+x['id']+': '+','.join(x['tasks'])+'</section>' for x in p['projects'])+'</html>'\nPath('report.html').write_text(html)\nprint('report generated')\n",
    }
    change = prepare_change(db.accepted_spec(), {"files": files}, db)
    apply_change(db, change)
    configs = {
        "projects": {"entrypoint_id": "projects", "argv": [sys.executable, "projects.py"], "allowed_executables": [sys.executable],
            "trusted": True, "timeout": 5, "stdout_contains": "projects persisted", "input_files": ["projects.py"]},
        "reports": {"entrypoint_id": "reports", "argv": [sys.executable, "reports.py"], "allowed_executables": [sys.executable],
            "trusted": True, "timeout": 5, "stdout_contains": "report generated", "input_files": ["reports.py", "business.json"]},
    }
    architecture = db.record_contract("architecture", {
        "schema_version": 1, "goal_revision": 1, "title": "Independent multi-component project tools",
        "components": [{"id": "projects", "kind": "domain-program"}, {"id": "store", "kind": "business-data"}, {"id": "reports", "kind": "report-program"}],
        "interfaces": [{"id": "save", "from": "projects", "to": "store"}, {"id": "read", "from": "store", "to": "reports"}],
        "dependencies": [{"from": "reports", "to": "store"}],
        "entrypoints": [{"id": key, "component_id": key, "argv": config["argv"]} for key, config in configs.items()],
        "acceptance": [{"id": key, "requirement_ids": [key], "verifier": "program", "config": config} for key, config in configs.items()],
        "intelligence_profile_id": None, "decisions": []})
    launch = {}
    for key, config in configs.items():
        evidence = accept(db, architecture["id"], config | {"kind": "program", "acceptance_id": key, "requirement_ids": [key]})
        launch[key] = evidence["id"]
        if key == "projects":
            assert coverage(Store(tmp_path))["missing"] == ["reports"]
            assert not coverage(Store(tmp_path))["complete"]
    assert json.loads((tmp_path / "business.json").read_text())["projects"][1]["tasks"] == ["verify", "deliver"]
    assert "A: design,build" in (tmp_path / "report.html").read_text()
    manifest = {"architecture_id": architecture["id"], "launch_evidence": launch}
    for name in ("architecture", "dependencies", "configuration", "recovery", "extensions"):
        (tmp_path / (name + ".md")).write_text("Fixture documentation; not human acceptance.")
        manifest[name] = name + ".md"
    result = check_delivery(Store(tmp_path), manifest)
    assert result["passed"] and result["human_acceptance"] == "not_inferred"
    # Construction and business persistence have independent files/lifecycles.
    assert (tmp_path / "business.json").is_file() and db.root != tmp_path
    (tmp_path / "reports.py").write_text("raise SystemExit(2)")
    assert not check_delivery(Store(tmp_path), manifest)["passed"]
