"""Read-only qualification audit; never promotes model claims to release approval."""
import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
sys.path.insert(0, str(ROOT / "tools"))
from awb_core.contracts import AWBError, digest, file_digest, read_json, write_json
from evaluate_systems import CONDITIONS, LIMITS, validate_frozen


def audit_attempt(attempt, directory):
    directory = Path(directory)
    violations = [key for key, limit in LIMITS.items()
        if attempt.get("elapsed_seconds" if key == "seconds" else key, 0) > limit]
    if attempt.get("hidden_retries") != 0:
        violations.append("hidden_retries")
    violations.extend(key for key, value in attempt.get("artifact_checks", {}).items()
        if key.startswith("preserved:") and value is False)
    checks = attempt.get("artifact_checks", {})
    actual_pass = (attempt.get("status") == "completed"
        and attempt.get("artifact_checks_passed") is True and checks.get("actual_program") is True
        and not attempt.get("synthetic_fixture") and not violations)
    report = {"status": attempt["status"], "actual_artifact_pass": actual_pass,
        "hard_constraint_violations": violations, "human_trial": "pending",
        "release_qualified": False, "pending_checks": ["semantic_goal_retention", "resource_and_recovery_review"]}
    receipt = directory / "validation/receipt.json"
    if receipt.is_file():
        report["validation_receipt_sha256"] = file_digest(receipt)
        report["observed_validation_checks"] = read_json(receipt).get("checks", {})
    if attempt.get("family") == "workbench":
        report["pending_checks"] += ["target_output_bound_to_node", "reject_wrong_node_result"]
        calls_path = directory / "validation/gateway/calls.json"
        case_path = directory / "case.json"
        match = None
        if calls_path.is_file() and case_path.is_file():
            calls = [c for c in read_json(calls_path)
                if c.get("mode") == "noninteractive" and c.get("status") == "completed"]
            if len(calls) == 1:
                try:
                    match = digest(json.loads(calls[0]["text"])) == digest(read_json(case_path)["task"]["expected"])
                except (ValueError, KeyError, TypeError):
                    match = False
        report["node_answer_matches_expected"] = match
        if match is False:
            report["actual_artifact_pass"] = False
    return report


def audit(matrix):
    matrix = Path(matrix).resolve()
    plan, corpus = read_json(matrix / "plan.json"), read_json(matrix / "corpus.json")
    summary = read_json(matrix / "summary.json")
    context, config = read_json(matrix / "context.json"), read_json(matrix / "host-config.json")
    integrity = {"passed": True}
    try:
        validate_frozen(matrix, plan, config, context)
    except AWBError as exc:
        integrity = {"passed": False, "error": exc.as_dict()}
    records, mismatches, running = [], [], []
    cases = {c["id"]: c for c in corpus["cases"]}
    for index, job in enumerate(plan["order"], 1):
        directory = matrix / ("attempt-%03d" % index)
        source = directory / "attempt.json"
        if not source.is_file():
            continue
        attempt = read_json(source)
        if attempt["status"] == "running":
            running.append(index)
            continue
        binding = attempt.get("binding", {})
        skill_sha = context[job["condition"]]["sha256"] if job["condition"] in {"builder", "previous"} else None
        if (attempt.get("scenario"), attempt.get("condition"), attempt.get("repetition")) != (
                job["scenario"], job["condition"], job["repetition"]) or binding != {
                "scenario": digest(cases[job["scenario"]]), "host": digest(config), "skill": skill_sha}:
            mismatches.append(index)
        row = audit_attempt(attempt, directory) | job | {"index": index,
            "receipt_sha256": file_digest(source), "question_count": attempt.get("question_count", 0),
            "repeated_questions": attempt.get("repeated_questions", 0),
            "host_turns": attempt.get("host_turns"), "construction_cycles": attempt.get("construction_cycles"),
            "elapsed_seconds": attempt.get("elapsed_seconds"),
            "cost": attempt.get("cost"), "tokens": attempt.get("tokens"), "model_calls": attempt.get("model_calls")}
        records.append(row)
    complete = len(records) == 120 and not running
    conditions = {}
    for condition in CONDITIONS:
        rows = [r for r in records if r["condition"] == condition]
        durations = [r["elapsed_seconds"] for r in rows if r["elapsed_seconds"] is not None]
        conditions[condition] = {"attempts": len(rows), "actual_artifact_passes": sum(r["actual_artifact_pass"] for r in rows),
            "pass_rate": sum(r["actual_artifact_pass"] for r in rows) / len(rows) if rows else None,
            "questions": sum(r["question_count"] for r in rows), "repeated_questions": sum(r["repeated_questions"] for r in rows),
            "median_seconds": statistics.median(durations) if durations else None,
            "by_scenario": {case: {"attempts": sum(r["scenario"] == case for r in rows),
                "passes": sum(r["scenario"] == case and r["actual_artifact_pass"] for r in rows)} for case in cases}}
    violations = [{"index": r["index"], "violations": r["hard_constraint_violations"]}
        for r in records if r["hard_constraint_violations"]]
    return {"schema_version": 1, "matrix": str(matrix), "plan_sha256": file_digest(matrix / "plan.json"),
        "summary_sha256": file_digest(matrix / "summary.json"), "complete": complete,
        "frozen_integrity": integrity, "record_binding_mismatches": mismatches, "running_attempts": running,
        "hard_constraint_violations": violations, "conditions": conditions, "attempts": records,
        "checkpoint": summary.get("checkpoint"), "simulated_user": True, "human_trial": "pending",
        "release_qualified": False, "effect_improvement_claim": "not_established",
        "pending_checks": ["full matrix" if not complete else "semantic review of all outcomes",
            "target output binding and wrong-node-result fault checks", "actual representative system-level human use",
            "resource provenance, recovery and hard-constraint review"],
        "limitations": ["This read-only snapshot does not change the frozen grader or rerun construction.",
            "Observed artifact pass rates are scoped to the six fixture interfaces; they are not general system-building effectiveness.",
            "The workbench fixture does not establish that the target used the node answer or rejected a wrong answer.",
            "Unmeasured costs, tokens and model-call totals remain null; simulated users are not human acceptance."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve earlier audits; choose a new output path")
    result = audit(args.matrix)
    write_json(args.output, result)
    print(json.dumps({"complete": result["complete"], "attempts": len(result["attempts"]),
        "release_qualified": result["release_qualified"], "running": result["running_attempts"],
        "hard_constraint_violations": result["hard_constraint_violations"]}, ensure_ascii=False))
