"""Local, synthetic construction trial with a real failing candidate and correction."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "building-agent-worksystems" / "scripts"))

from awb_core.contracts import write_json
from awb_core.cycle import apply_decision
from awb_core.generation import apply_change, prepare_change
from awb_core.materials import run_materials
from awb_core.state import Store
from awb_core.verification import verify_candidate


SOURCE = '''import json, sys
task = json.load(sys.stdin)
text = task["document"]
research = "research" in text.lower()
procedure = "steps" in text.lower()
category = "research" if research else "procedure" if procedure else "other"
review = REVIEW_EXPRESSION
print(json.dumps({"category": category, "evidence": text[:200], "review_required": review}))
'''


def demo(project):
    project = Path(project).resolve()
    project.mkdir(parents=True, exist_ok=False)
    goal = {"schema_version": 1, "id": "demo-goal", "revision": 1, "text": "Classify source material and refer mixed content for review",
            "offline": False, "requirements": [{"id": "R1", "text": "Preserve source files and review mixed material", "source": "user", "kind": "acceptance", "status": "confirmed"}]}
    store = Store.initialize(project, goal)
    inputs = project / "input"
    inputs.mkdir()
    for name, content in {"research.txt": "Research results: the measurement is provisional.", "procedure.txt": "Steps: open the folder and check the output.",
                          "mixed.txt": "Research notes. Steps for rerunning the experiment."}.items():
        (inputs / name).write_text(content, encoding="utf-8")
    reference = {"research.txt": "research", "procedure.txt": "procedure", "mixed.txt": "procedure"}
    write_json(project / "reference.json", reference)
    reports = []
    for corrected in (False, True):
        cycle = store.create("cycle", {"hypothesis": "Route mixed material to review" if corrected else "The first matching keyword is sufficient",
                              "requirement_ids": ["R1"], "baseline": "original fixture", "verification_plan": "Compare every label with independent reference.json",
                              "limits": {"calls": 3, "seconds": 20}})
        cycle = store.record_transition(cycle["id"], cycle["revision"], "implementing", [])
        source = SOURCE.replace("REVIEW_EXPRESSION", "research == procedure" if corrected else "False")
        change = prepare_change({"files": {}}, {"files": {"classifier.py": source}}, store)
        store.update(cycle["id"], cycle["revision"], {"change_id": change["id"]})
        apply_change(store, change)
        backend = {"backend": "command", "argv": [sys.executable, str(project / "classifier.py")],
                   "allowed_executables": [sys.executable], "trusted": True, "timeout": 5, "side_effect": "none"}
        result = run_materials(store, inputs, backend, max_calls=3, max_seconds=20)
        if result["status"] == "needs_human":
            for review in store.list("review"):
                if review["entity_id"] == result["id"] and review["status"] == "needs_human":
                    store.approve(review["id"], {"category": reference[review["question"]["source_id"]]}, "simulated-demo-reviewer")
            process = subprocess.run([sys.executable, str(ROOT / "skills" / "building-agent-worksystems" / "scripts" / "awb.py"), "resume", "--id", result["id"], "--project", str(project)],
                                     capture_output=True, text=True, encoding="utf-8", timeout=15)
            if process.returncode:
                raise RuntimeError(process.stdout + process.stderr)
            result = json.loads(process.stdout)
        cycle = store.get(cycle["id"])
        cycle = store.record_transition(cycle["id"], cycle["revision"], "verifying", [])
        evidence = verify_candidate({"store": store, "cycle_id": cycle["id"], "change_id": change["id"]},
                                    {"kind": "materials", "run_id": result["id"], "reference": reference})
        cycle = store.record_transition(cycle["id"], cycle["revision"], "deciding", [])
        cycle = store.update(cycle["id"], cycle["revision"], {"refuted": not evidence["passed"], "progress": corrected, "uncertainty_reduced": True})
        decision = apply_decision(store, cycle["id"], {"action": "accept" if evidence["passed"] else "rollback",
                                  "reason": "Independent labels agree after mixed-content review" if corrected else "First-keyword rule misclassifies mixed material; revise routing",
                                  "evidence_refs": [evidence["id"]]})
        reports.append({"cycle_id": cycle["id"], "run_id": result["id"], "evidence_id": evidence["id"], "passed": evidence["passed"], "decision": decision["status"]})
    report = {"synthetic_fixture": True, "real_model_used": False, "human_review": "simulated-demo-reviewer",
              "baseline_passed": reports[0]["passed"], "candidate_passed": reports[1]["passed"],
              "accepted": reports[1]["decision"] == "accepted", "cycles": reports, "project": str(project)}
    write_json(project / "demo-report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    print(json.dumps(demo(args.project), ensure_ascii=False))
