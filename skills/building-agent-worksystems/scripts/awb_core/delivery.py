"""Whole-goal coverage and inspectable independent delivery; a cycle is not the whole goal."""
from .contracts import AWBError, inside, file_digest


def coverage(store):
    goal = store.goal()
    covered, invalid = set(), []
    required = {r["id"] for r in goal["requirements"] if r["status"] != "replaced"}
    unresolved = [r["id"] for r in goal["requirements"] if r["status"] == "unconfirmed"]
    for cycle in store.list("cycle"):
        if cycle["status"] != "accepted" or cycle["goal_revision"] != goal["revision"]:
            continue
        for ref in cycle.get("evidence_refs", []):
            try:
                report = store.check_evidence(ref)
                if report["passed"] and report["bindings"].get("goal_revision") == goal["revision"]:
                    covered.update(report["bindings"].get("requirement_ids", []))
            except AWBError:
                invalid.append(ref)
    return {"goal_revision": goal["revision"], "covered": sorted(covered & required), "missing": sorted(required - covered),
            "unresolved": unresolved, "invalid_evidence": invalid,
            "complete": bool(required) and not (required - covered or unresolved or invalid)}


def check_delivery(store, manifest):
    architecture = store.require_contract(manifest["architecture_id"], "architecture")
    result = coverage(store)
    launch = {}
    for entry in architecture["entrypoints"]:
        try:
            evidence = store.check_evidence(manifest.get("launch_evidence", {}).get(entry["id"]))
            launch[entry["id"]] = bool(evidence["passed"] and evidence["bindings"].get("architecture_id") == architecture["id"]
                and evidence["bindings"].get("entrypoint_id") == entry["id"])
        except AWBError:
            launch[entry["id"]] = False
    checks = {"whole_goal_covered": result["complete"], "independent_entrypoint": bool(launch) and all(launch.values())}
    files = {}
    for key in ("architecture", "dependencies", "configuration", "recovery", "extensions"):
        name = manifest.get(key)
        path = inside(store.project, name) if name else None
        checks[key] = bool(path and path.is_file() and path.stat().st_size)
        if checks[key]:
            files[name] = file_digest(path)
    return {"schema_version": 1, "passed": all(checks.values()), "checks": checks, "coverage": result,
            "architecture_id": architecture["id"], "files": files, "human_acceptance": "not_inferred"}
