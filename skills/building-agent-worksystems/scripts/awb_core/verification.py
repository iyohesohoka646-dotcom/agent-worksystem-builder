import json
import hashlib
import inspect
import ipaddress
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

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
    cycle = store.get(candidate_ref["cycle_id"])
    contract_bindings = _acceptance_bindings(store, cycle, acceptance_ref)
    if acceptance_ref["kind"] != "materials":
        return _verify_general_candidate(candidate_ref, acceptance_ref)
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
    bindings.update(verifier_binding("materials"))
    bindings.update(contract_bindings)
    bindings["requirement_ids"] = acceptance_ref.get("requirement_ids", [])
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


VERIFIERS = {}


def register_verifier(name, version, verify, dependency_paths=()):
    """An explicit Python extension boundary. Never import model-selected arbitrary modules."""
    if not name or not version or not callable(verify):
        raise AWBError("verification", "A registered verifier needs a name, version and callable")
    if name in VERIFIERS:
        raise AWBError("verification", "Verifier is already registered; use a distinct versioned name")
    source = inspect.getsourcefile(verify)
    paths = set(map(lambda p: str(Path(p).resolve()), dependency_paths))
    if source:
        paths.add(str(Path(source).resolve()))
    VERIFIERS[name] = {"version": version, "verify": verify, "sources": sorted(paths)}


def verifier_binding(name):
    if name not in VERIFIERS:
        raise AWBError("verification", f"No registered verifier for {name}")
    verifier = VERIFIERS[name]
    return {"verifier_name": name, "verifier_version": verifier["version"],
            "verifier_dependencies": {path: file_digest(path) for path in verifier["sources"]}}


def check_verifier_binding(bindings):
    name = bindings.get("verifier_name")
    if name and verifier_binding(name) != {key: bindings[key] for key in ("verifier_name", "verifier_version", "verifier_dependencies")}:
        raise AWBError("evidence", "Registered verifier changed; revalidation is required")


def _matches(value, expected):
    if isinstance(expected, dict):
        return isinstance(value, dict) and all(key in value and _matches(value[key], item) for key, item in expected.items())
    return type(value) is type(expected) and value == expected


def _acceptance_bindings(store, cycle, acceptance):
    if cycle["kind"] != "cycle" or cycle["goal_revision"] != store.goal()["revision"]:
        raise AWBError("revision", "Verification requires a current construction cycle")
    bindings = {}
    for kind, contract in store.require_cycle_contracts(cycle).items():
        bindings[kind + "_id"] = contract["id"]
        bindings[kind + "_digest"] = contract["contract_digest"]
        if kind == "architecture":
            spec = next((item for item in contract["acceptance"] if item["id"] == acceptance.get("acceptance_id")), None)
            actual = {key: value for key, value in acceptance.items() if key not in {"acceptance_id", "kind", "requirement_ids"}}
            if not spec or spec["verifier"] != acceptance["kind"] or spec["requirement_ids"] != acceptance.get("requirement_ids") or spec["config"] != actual:
                raise AWBError("verification", "Candidate acceptance differs from the current architecture acceptance contract")
            if actual.get("entrypoint_id"):
                entry = next((e for e in contract["entrypoints"] if e["id"] == actual["entrypoint_id"]), None)
                launch_argv = actual.get("argv") if acceptance["kind"] == "program" else actual.get("startup", {}).get("argv") if acceptance["kind"] == "service" else None
                if not entry or entry["argv"] != launch_argv:
                    raise AWBError("verification", "Entrypoint acceptance must execute the declared launch argv")
                bindings["entrypoint_id"] = entry["id"]
    return bindings


def _artifact_check(store, acceptance, directory):
    assertions = acceptance.get("assertions", [])
    if not assertions:
        raise AWBError("verification", "Artifact verification needs independent assertions")
    checks, artifacts, observed = {}, [], {}
    for index, assertion in enumerate(assertions):
        if not set(assertion) & {"sha256", "contains", "json_value", "nonempty"}:
            raise AWBError("verification", "Each artifact needs an explicit content assertion")
        path = inside(store.project, assertion["path"])
        passed = path.is_file()
        if passed:
            content = path.read_bytes()
            actual = hashlib.sha256(content).hexdigest()
            observed[path.relative_to(store.project).as_posix()] = actual
            artifacts.append(path)
            if "sha256" in assertion:
                passed &= actual == assertion["sha256"]
            if "nonempty" in assertion:
                passed &= bool(content) == assertion["nonempty"]
            try:
                if "contains" in assertion:
                    passed &= assertion["contains"] in content.decode("utf-8")
                if "json_value" in assertion:
                    passed &= _matches(json.loads(content.decode("utf-8")), assertion["json_value"])
            except (ValueError, UnicodeError):
                passed = False
        checks[f"artifact:{index}"] = bool(passed)
    return {"checks": checks, "artifacts": artifacts, "observed_hashes": observed, "dependency_hashes": {}}


def _program_check(store, acceptance, directory):
    from .adapters.command import command_argv
    from .execution import dependency_hashes
    from .process import run_process
    config = acceptance | {"backend": "command"}
    args = command_argv(config)
    timeout = acceptance.get("timeout", 60)
    if not 0 < timeout <= 900:
        raise AWBError("budget", "Program verification timeout must be in (0,900]")
    inputs = directory / "input.json"
    write_json(inputs, acceptance.get("input", {}))
    stdout, stderr = directory / "stdout.log", directory / "stderr.log"
    deps = dependency_hashes(config, store.project)
    # Resolve relative script arguments against the actual target cwd, not this Builder's cwd.
    for part in args[1:]:
        try:
            path = inside(store.project, part)
            if path.is_file():
                deps[str(path)] = file_digest(path)
        except AWBError:
            continue
    process = run_process(args, store.project, inputs, stdout, stderr, timeout)
    checks = {"program_exit": process["returncode"] == acceptance.get("expected_exit", 0) and process["reason"] is None,
              "execution_dependencies": all(Path(p).is_file() and file_digest(p) == h for p, h in deps.items())}
    if "stdout_contains" in acceptance:
        checks["stdout_contains"] = acceptance["stdout_contains"] in stdout.read_text(encoding="utf-8", errors="replace")
    return {"checks": checks, "artifacts": [inputs, stdout, stderr], "dependency_hashes": deps,
            "execution": process}


def _service_check(store, acceptance, directory):
    if not acceptance.get("startup"):
        return _service_requests(store, acceptance, directory)
    import threading
    import time
    from .adapters.command import command_argv
    from .execution import dependency_hashes
    from .process import run_process
    timeout = acceptance.get("timeout", 5)
    if not 0 < timeout <= 60:
        raise AWBError("budget", "Service startup timeout must be in (0,60]")
    # Validate destinations before starting the explicitly trusted target process.
    for request in acceptance.get("requests", []):
        _validate_service_url(request["url"])
    header = acceptance.get("instance_header")
    if not isinstance(header, str) or not header.strip() or not acceptance.get("requests"):
        raise AWBError("verification", "Owned service startup requires an instance_header probe")
    with httpx.Client(timeout=0.2, follow_redirects=False, trust_env=False) as client:
        for request in acceptance["requests"]:
            try:
                client.get(request["url"])
            except httpx.HTTPError:
                continue
            raise AWBError("verification", "Service endpoint is already running; cannot claim this startup instance")
    import os
    import uuid
    instance = uuid.uuid4().hex
    env = dict(os.environ, AWB_VERIFICATION_TOKEN=instance)
    startup = acceptance["startup"] | {"backend": "command"}
    args = command_argv(startup)
    deps = dependency_hashes(startup, store.project)
    for part in args[1:]:
        try:
            path = inside(store.project, part)
            if path.is_file():
                deps[str(path)] = file_digest(path)
        except AWBError:
            continue
    stdin, stdout, stderr = directory / "startup-input.json", directory / "startup.stdout", directory / "startup.stderr"
    write_json(stdin, {})
    cancel, outcome = threading.Event(), {}
    def worker():
        try:
            outcome.update(run_process(args, store.project, stdin, stdout, stderr, timeout, cancel, env=env))
        except Exception as exc:
            outcome["error"] = str(exc)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    started = time.monotonic()
    try:
        ready = False
        with httpx.Client(timeout=0.2, follow_redirects=False, trust_env=False) as client:
            while thread.is_alive() and time.monotonic() - started < timeout:
                try:
                    client.get(acceptance["requests"][0]["url"])
                    ready = True
                    break
                except httpx.HTTPError:
                    time.sleep(0.05)
        report = _service_requests(store, acceptance | {"timeout": max(0.01, timeout - (time.monotonic() - started)), "_instance_token": instance}, directory)
        report["checks"].update(startup_owned=ready and thread.is_alive(), execution_dependencies=all(Path(p).is_file() and file_digest(p) == h for p, h in deps.items()))
        report["artifacts"] += [stdin, stdout, stderr]
        report["dependency_hashes"] = deps
        return report
    finally:
        cancel.set()
        thread.join(timeout=5)


def _validate_service_url(url):
    parsed = urlparse(url)
    try:
        loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        loopback = parsed.hostname == "localhost"
    if parsed.scheme not in {"http", "https"} or not loopback or parsed.username or parsed.password:
        raise AWBError("policy", "Built-in service verification is limited to explicit loopback destinations")


def _service_requests(store, acceptance, directory):
    requests = acceptance.get("requests", [])
    timeout = acceptance.get("timeout", 5)
    if not requests or not 0 < timeout <= 60:
        raise AWBError("verification", "Service checks need requests and a timeout in (0,60]")
    for request in requests:
        _validate_service_url(request["url"])
    checks, artifacts = {}, []
    with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
        for index, request in enumerate(requests):
            path = directory / f"response-{index}.json"
            try:
                with client.stream("GET", request["url"]) as response:
                    body = bytearray()
                    for block in response.iter_bytes():
                        body.extend(block)
                        if len(body) > 4 * 1024 * 1024:
                            raise AWBError("output_limit", "Service response exceeded its evidence limit")
                passed = response.status_code == request["status"]
                if acceptance.get("_instance_token"):
                    passed &= response.headers.get(acceptance["instance_header"]) == acceptance["_instance_token"]
                if "json_value" in request:
                    passed &= _matches(json.loads(body), request["json_value"])
                observation = {"status": response.status_code, "body": body.decode("utf-8", errors="replace")}
            except (httpx.HTTPError, ValueError, AWBError) as exc:
                passed, observation = False, {"error": str(exc)}
            write_json(path, observation)
            artifacts.append(path)
            checks[f"service:{index}"] = bool(passed)
    return {"checks": checks, "artifacts": artifacts, "dependency_hashes": {}}


def _verify_general_candidate(candidate_ref, acceptance_ref):
    store = candidate_ref["store"]
    cycle = store.get(candidate_ref["cycle_id"])
    if cycle["kind"] != "cycle" or cycle["goal_revision"] != store.goal()["revision"]:
        raise AWBError("revision", "Verification requires a current construction cycle")
    name = acceptance_ref["kind"]
    bindings = {"goal_revision": store.goal()["revision"], "acceptance_digest": digest(acceptance_ref),
                "verifier_sha256": file_digest(Path(__file__)), **verifier_binding(name)}
    requirements = acceptance_ref.get("requirement_ids", [])
    known = {r["id"] for r in store.goal()["requirements"] if r["status"] != "replaced"}
    if not requirements or set(requirements) - known:
        raise AWBError("verification", "Acceptance needs current requirement IDs")
    bindings["requirement_ids"] = requirements
    bindings.update(_acceptance_bindings(store, cycle, acceptance_ref))
    directory = store.root / "evidence" / cycle["id"] / identifier("verification")
    directory.mkdir(parents=True)
    # The acceptance record itself is frozen with the executed result.
    write_json(directory / "acceptance.json", acceptance_ref)
    report = VERIFIERS[name]["verify"](store, acceptance_ref, directory)
    bindings["execution_dependencies"] = report.get("dependency_hashes", {})
    checks = dict(report["checks"])
    artifacts = [directory / "acceptance.json", *report["artifacts"]]
    observed = report.get("observed_hashes", {})
    change_id = candidate_ref.get("change_id") or cycle.get("change_id")
    if change_id:
        change = store.get(change_id)
        if cycle.get("change_id") and cycle["change_id"] != change_id:
            raise AWBError("evidence", "Candidate differs from the construction cycle")
        bindings["candidate_digest"] = change["candidate_digest"]
        bindings["absent_paths"] = [e["path"] for e in change["entries"] if e["after"] is None]
        checks["candidate_files"] = change["status"] == "applied"
        for entry in change["entries"]:
            path = inside(store.project, entry["path"])
            checks["candidate_files"] &= not path.exists() if entry["after"] is None else path.is_file() and file_digest(path) == entry["after_hash"]
            if entry["after"] is not None and path.is_file():
                artifacts.append(path)
                observed.setdefault(entry["path"], file_digest(path))
        if name in {"program", "service"}:
            checks["candidate_execution_binding"] = all(report.get("dependency_hashes", {}).get(str(inside(store.project, e["path"]))) == e["after_hash"]
                for e in change["entries"] if e["after"] is not None and e["path"].endswith(".py"))
    report_path = directory / "report.json"
    write_json(report_path, {"schema_version": 1, "checks": checks, "bindings": bindings,
                            "dependency_hashes": report.get("dependency_hashes", {}), "passed": all(checks.values())})
    artifacts.append(report_path)
    artifacts = list(dict.fromkeys(artifacts))
    for path in artifacts:
        observed.setdefault(path.relative_to(store.project).as_posix(), file_digest(path))
    return store.add_evidence(cycle["id"], artifacts, checks, bindings, expected_hashes=observed)


register_verifier("materials", "1", verify_materials)
register_verifier("program", "1", _program_check)
register_verifier("service", "1", _service_check)
register_verifier("artifact", "1", _artifact_check)
