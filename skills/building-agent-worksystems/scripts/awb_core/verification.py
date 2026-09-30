import json
import hashlib
from pathlib import Path

from .contracts import AWBError, digest, file_digest, inside, read_json, write_json
from .materials import CATEGORIES
from .state import identifier
from .locking import mutation, project_lock


@mutation
def verify_materials(store, run_id, reference=None):
    run = store.get(run_id)
    checks = {"run_completed": run["status"] == "completed", "current_goal": run["goal_revision"] == store.goal()["revision"],
              "export_hashes": True, "source_hashes": True, "source_quotes": True,
              "complete_inventory": True, "valid_categories": True, "human_decisions": True}
    rows, observed_hashes, contents = [], {}, {}
    outputs = run.get("outputs", {})
    try:
        for key in ("jsonl", "csv"):
            path = inside(store.project, outputs[key])
            content = path.read_bytes()
            observed_hashes[path.relative_to(store.project).as_posix()] = hashlib.sha256(content).hexdigest()
            contents[key] = content
            checks["export_hashes"] &= hashlib.sha256(content).hexdigest() == outputs["sha256"][key]
        rows = [json.loads(line) for line in contents["jsonl"].decode("utf-8").splitlines()]
    except (AWBError, OSError, ValueError, KeyError):
        checks["export_hashes"] = False
    sources = {s["source_id"]: s for s in run["sources"]}
    checks["complete_inventory"] = len(rows) == len(sources) and {r.get("source_id") for r in rows} == set(sources)
    items = {i["source_id"]: i for i in run["items"]}
    for row in rows:
        source = sources.get(row.get("source_id"))
        if source is None:
            checks["complete_inventory"] = False
            continue
        try:
            path = inside(store.project, source["path"])
            content = path.read_bytes()
            observed_hashes[path.relative_to(store.project).as_posix()] = hashlib.sha256(content).hexdigest()
            checks["source_hashes"] &= hashlib.sha256(content).hexdigest() == source["source_sha256"] == row.get("source_sha256")
            text = content.decode("utf-8-sig")
            checks["source_quotes"] &= isinstance(row.get("evidence"), str) and row["evidence"] in text and (bool(row["evidence"]) or not text)
        except (OSError, AWBError, UnicodeError):
            checks["source_hashes"] = False
        checks["valid_categories"] &= row.get("category") in CATEGORIES
        item = items[source["source_id"]]
        if item.get("review_id"):
            answer = store.review_answer(item["review_id"], item["review_binding"], run["goal_revision"], ["classify"])
            checks["human_decisions"] &= answer is not None and answer.get("category") == row.get("category") and row.get("review_required") is False
        else:
            checks["human_decisions"] &= row.get("review_required") is False
    if reference is not None:
        checks["reference_categories"] = {r.get("source_id"): r.get("category") for r in rows} == reference
    checks["execution_dependencies"] = all(Path(p).is_file() and file_digest(Path(p)) == h for p, h in run.get("dependency_hashes", {}).items())
    report = {"schema_version": 1, "run_id": run_id, "checks": checks, "passed": all(checks.values()),
              "semantic_reference_used": reference is not None, "verifier_sha256": file_digest(Path(__file__)),
              "observed_hashes": observed_hashes,
              "limitation": "Category correctness needs a reference or human task acceptance; structural checks alone do not establish it."}
    path = store.root / "runs" / run_id / "verifications" / (identifier("verification") + ".json")
    report["report_path"] = path.relative_to(store.project).as_posix()
    write_json(path, report)
    return report


def verify_candidate(candidate_ref, acceptance_ref):
    with project_lock(candidate_ref["store"], "mutation"):
        return _verify_candidate(candidate_ref, acceptance_ref)


def _verify_candidate(candidate_ref, acceptance_ref):
    """Run a declared deterministic verifier; no model-authored pass flag is trusted."""
    store = candidate_ref["store"]
    if acceptance_ref["kind"] != "materials":
        raise AWBError("verification", "Register a domain verifier for this acceptance kind")
    if acceptance_ref.get("reference") is None:
        raise AWBError("verification", "Candidate acceptance requires an independent reference")
    report = verify_materials(store, acceptance_ref["run_id"], acceptance_ref.get("reference"))
    run = store.get(acceptance_ref["run_id"])
    observed = dict(report["observed_hashes"])
    artifacts = [inside(store.project, report["report_path"])]
    artifacts += [inside(store.project, run["outputs"][key]) for key in ("jsonl", "csv") if key in run["outputs"]]
    artifacts += [inside(store.project, s["path"]) for s in run["sources"]]
    bindings = {"goal_revision": store.goal()["revision"], "acceptance_digest": digest(acceptance_ref),
                "verifier_sha256": report["verifier_sha256"]}
    if candidate_ref.get("change_id"):
        change = store.get(candidate_ref["change_id"])
        bindings["candidate_digest"] = change["candidate_digest"]
        bindings["absent_paths"] = [e["path"] for e in change["entries"] if e["after"] is None]
        report["checks"]["candidate_files"] = all(
            (not inside(store.project, e["path"]).exists()) if e["after"] is None
            else (inside(store.project, e["path"]).is_file() and file_digest(inside(store.project, e["path"])) == e["after_hash"])
            for e in change["entries"])
        report["passed"] = all(report["checks"].values())
        for entry in change["entries"]:
            if entry["after"] is not None:
                observed[entry["path"]] = entry["after_hash"]
        report["checks"]["candidate_execution_binding"] = all(
            run.get("dependency_hashes", {}).get(str(inside(store.project, e["path"]))) == e["after_hash"]
            for e in change["entries"] if e["after"] is not None and e["path"].endswith(".py"))
        report["passed"] = all(report["checks"].values())
        write_json(inside(store.project, report["report_path"]), report)
        artifacts += [inside(store.project, e["path"]) for e in change["entries"] if e["after"] is not None]
    observed[report["report_path"]] = file_digest(inside(store.project, report["report_path"]))
    return store.add_evidence(candidate_ref["cycle_id"], artifacts, report["checks"], bindings, expected_hashes=observed)
