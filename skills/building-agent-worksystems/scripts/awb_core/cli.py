import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .contracts import AWBError, read_json, write_json
from .cycle import apply_decision, stagnation
from .execution import probe_backend
from .exporting import export_project
from .generation import apply_change, prepare_change, rollback_change
from .intent import propose_next_action, write_handoff
from .materials import run_materials, resume_materials
from .scheduler import run_graph, plan_from_selection
from .state import Store, identifier
from .verification import verify_candidate, verify_materials
from .exploration import next_action, answer_question, reopen_question
from .delivery import coverage, check_delivery
from .intelligence import compile_profile, discover_resources


def parser():
    root = argparse.ArgumentParser(prog="awb", description="Build and run evidence-backed work systems")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    parsers = {}
    for name in ("init", "goal", "probe", "status", "next", "cycle", "run", "review", "resume", "verify", "export", "cancel", "plan", "explore", "architecture", "profile", "delivery"):
        p = commands.add_parser(name)
        p.add_argument("--project", type=Path, default=Path.cwd())
        p.add_argument("--json", action="store_true", help="Output is always machine-readable JSON")
        parsers[name] = p
    parsers["init"].add_argument("--goal", type=Path, required=True)
    parsers["goal"].add_argument("--file", type=Path)
    parsers["goal"].add_argument("--expected-revision", type=int)
    parsers["probe"].add_argument("--config", type=Path, required=True)
    parsers["probe"].add_argument("--live", action="store_true")
    parsers["next"].add_argument("--uncertainties", type=Path)
    for name in ("explore", "architecture", "profile"):
        parsers[name].add_argument("--file", type=Path)
        parsers[name].add_argument("--id")
        parsers[name].add_argument("--expected-revision", type=int)
    parsers["explore"].add_argument("--action", choices=["record", "next", "answer", "reopen"], default="record")
    parsers["explore"].add_argument("--source", choices=["user", "environment", "experiment"])
    parsers["explore"].add_argument("--reason")
    parsers["profile"].add_argument("--compile", action="store_true")
    parsers["profile"].add_argument("--discover", type=Path, help="Metadata-only inventory in this Codex home")
    parsers["delivery"].add_argument("--file", type=Path)
    p = parsers["cycle"]
    p.add_argument("--action", choices=["start", "transition", "decide", "prepare", "apply", "rollback"], required=True)
    p.add_argument("--id")
    p.add_argument("--file", type=Path)
    p.add_argument("--hypothesis")
    p.add_argument("--status")
    p.add_argument("--change-id")
    p = parsers["run"]
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--input")
    source.add_argument("--graph", type=Path)
    p.add_argument("--task", type=Path)
    p.add_argument("--backend", type=Path)
    p.add_argument("--max-calls", type=int, default=0)
    p.add_argument("--max-seconds", type=float, default=60)
    p.add_argument("--concurrency", type=int, default=1)
    p = parsers["review"]
    p.add_argument("--id")
    p.add_argument("--answer", type=Path)
    p.add_argument("--actor")
    for name in ("resume", "cancel"):
        parsers[name].add_argument("--id", required=True)
    parsers["verify"].add_argument("--id")
    parsers["verify"].add_argument("--reference", type=Path)
    parsers["verify"].add_argument("--cycle-id")
    parsers["verify"].add_argument("--change-id")
    parsers["verify"].add_argument("--acceptance", type=Path, help="Registered verifier and frozen acceptance configuration")
    parsers["export"].add_argument("--output", required=True)
    parsers["plan"].add_argument("--selection", type=Path, required=True)
    parsers["plan"].add_argument("--catalog", type=Path, required=True)
    return root


def required(value, label):
    if value is None:
        raise AWBError("arguments", f"{label} is required for this action")
    return value


def dispatch(args):
    if args.command == "init":
        store = Store.initialize(args.project, read_json(args.goal))
        write_handoff(store)
        return {"status": "initialized", "project": str(store.project), "goal": store.goal()}
    if args.command == "plan":
        return plan_from_selection(read_json(args.selection), read_json(args.catalog))
    store = Store(args.project)
    if args.command == "delivery":
        return check_delivery(store, read_json(args.file)) if args.file else coverage(store)
    if args.command in {"explore", "architecture", "profile"}:
        kind = "exploration" if args.command == "explore" else args.command
        if args.command == "profile":
            if args.discover:
                return discover_resources(store.project, args.discover)
            if args.compile:
                return compile_profile(store.require_contract(required(args.id, "--id"), "profile"))
        if args.command == "explore":
            if args.action == "next":
                return next_action(store)
            if args.action == "answer":
                return answer_question(store, required(args.id, "--id"), read_json(required(args.file, "--file")), required(args.source, "--source"))
            if args.action == "reopen":
                return reopen_question(store, required(args.id, "--id"), required(args.reason, "--reason"))
        if args.file:
            record = store.record_contract(kind, read_json(args.file), args.id, args.expected_revision)
            write_handoff(store)
            return record
        if args.id:
            record = store.get(args.id)
            if record["kind"] != kind:
                raise AWBError("schema", "Record has a different contract kind")
            return record
        return store.list(kind)
    if args.command == "goal":
        return store.update_goal(read_json(args.file), required(args.expected_revision, "--expected-revision")) if args.file else store.goal()
    if args.command == "probe":
        config = read_json(args.config)
        report = probe_backend(config, store.root / "probes", args.live)
        record = store.create("probe", report)
        write_json(store.root / "probes" / f"{record['id']}.json", record)
        return record
    if args.command == "status":
        return {"goal": store.goal(), "cycles": store.list("cycle"), "runs": store.list("run"),
                "pending_reviews": [r for r in store.list("review") if r["status"] == "needs_human"],
                "stagnation": stagnation(store.list("cycle"))}
    if args.command == "next":
        return next_action(store, read_json(args.uncertainties) if args.uncertainties else [])
    if args.command == "cycle":
        return cycle_command(store, args)
    if args.command == "run":
        if args.graph:
            return run_graph(store, read_json(args.graph), read_json(args.task) if args.task else {},
                             args.max_calls, args.max_seconds, args.concurrency)
        return run_materials(store, args.input, read_json(args.backend) if args.backend else None, args.max_calls, args.max_seconds)
    if args.command == "review":
        if args.answer:
            return store.approve(required(args.id, "--id"), read_json(args.answer), required(args.actor, "--actor"))
        return [r for r in store.list("review") if r["status"] == "needs_human"]
    if args.command == "resume":
        run = store.get(args.id)
        if run.get("workflow") == "graph":
            return run_graph(store, run["graph"], run["task"], run["max_calls"], run["remaining_seconds"], run["concurrency"], run["id"])
        return resume_materials(store, args.id)
    if args.command == "verify":
        if args.acceptance:
            return verify_candidate({"store": store, "cycle_id": required(args.cycle_id, "--cycle-id"), "change_id": args.change_id}, read_json(args.acceptance))
        reference = read_json(args.reference) if args.reference else None
        if args.cycle_id:
            return verify_candidate({"store": store, "cycle_id": args.cycle_id, "change_id": args.change_id},
                                    {"kind": "materials", "run_id": args.id, "reference": reference})
        return verify_materials(store, required(args.id, "--id"), reference)
    if args.command == "export":
        return export_project(store, args.output)
    if args.command == "cancel":
        run = store.get(args.id)
        if run["kind"] == "cycle":
            return store.record_transition(run["id"], run["revision"], "cancelled", [])
        if run["kind"] != "run" or run["status"] == "completed":
            raise AWBError("run", "Only an unfinished run can be cancelled")
        write_json(store.root / "cancellations" / (run["id"] + ".json"), {"requested": True})
        return {"status": "cancel_requested", "run_id": run["id"], "note": "Active process nodes observe this request; waiting runs apply it on resume."}


def cycle_command(store, args):
    if args.action == "start":
        payload = read_json(args.file) if args.file else {"hypothesis": required(args.hypothesis, "--hypothesis")}
        return store.create("cycle", payload)
    if args.action == "prepare":
        baseline = store.accepted_spec()
        change = prepare_change(baseline, read_json(required(args.file, "--file")), store)
        if args.id:
            cycle = store.get(args.id)
            store.update(cycle["id"], cycle["revision"], {"change_id": change["id"]})
        return change
    if args.action == "apply":
        return apply_change(store, {"id": required(args.change_id, "--change-id")})
    if args.action == "rollback":
        return rollback_change(store, required(args.change_id, "--change-id"))
    cycle = store.get(required(args.id, "--id"))
    if args.action == "transition":
        return store.record_transition(cycle["id"], cycle["revision"], required(args.status, "--status"), [])
    return apply_decision(store, cycle["id"], read_json(required(args.file, "--file")))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        result = dispatch(args)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        if isinstance(result, dict):
            if result.get("status") in {"needs_human", "budget_exhausted"}:
                return 3
            if result.get("status") in {"failed", "timed_out", "cancelled"} or result.get("passed") is False:
                return 1
        return 0
    except (AWBError, OSError, UnicodeError, ValueError) as exc:
        error = exc.as_dict() if isinstance(exc, AWBError) else {"code": "io", "message": str(exc)}
        print(json.dumps({"status": "failed", "error": error}, ensure_ascii=False))
        return 1
