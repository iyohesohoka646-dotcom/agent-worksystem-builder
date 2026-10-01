"""Bounded, resumable full construction evaluation. Grading is external to the model."""
import argparse
import io
import importlib.metadata
import json
import random
import subprocess
import sys
import time
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from awb_core.adapters.app_server import AppServerClient
from awb_core.adapters.codex import executable
from awb_core.contracts import AWBError, atomic_write, digest, file_digest, inside, read_json, write_json
from awb_core.intelligence import app_server_command
from awb_core.process import run_process
from evaluate import freeze_skill, skill_files, skill_entrypoint

CONDITIONS = ("baseline", "generic", "previous", "builder")
LIMITS = {"host_turns": 30, "construction_cycles": 8, "seconds": 900}
SCHEMA = {"type": "object", "properties": {
    "state": {"type": "string", "enum": ["need_input", "continue", "done", "blocked"]},
    "question": {"type": "string"}, "reason": {"type": "string"}},
    "required": ["state", "question", "reason"], "additionalProperties": False}


def tree_hashes(root):
    return {p.relative_to(root).as_posix(): file_digest(p) for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in {".py", ".js", ".ts", ".html", ".css", ".toml"}
            and not any(s in {".git", ".venv", "__pycache__", ".worksystem-build"} for s in p.parts)}


class HostSession:
    def __init__(self, workspace, config, directory, **kwargs):
        self.workspace, self.config, self.directory = workspace, config, directory

    def __enter__(self):
        self.client = AppServerClient(app_server_command(self.config), self.workspace,
            self.directory / "host", self.config, timeout=30, max_bytes=32 * 1024 * 1024, experimental=True)
        self.client.__enter__()
        try:
            data = self.client.request("skills/list", {"cwds": [str(self.workspace)], "forceReload": True})
            skills = [s for entry in data.get("data", []) for s in entry.get("skills", [])]
            write_json(self.directory / "isolation.json", {"skills": skills})
            if any(s.get("enabled") for s in skills):
                raise AWBError("isolation", "Implicit Skills remain enabled; condition comparison is not isolated")
            self.thread_id = self.client.start_thread()
            return self
        except BaseException:
            self.client.close()
            raise

    def __exit__(self, *exc):
        self.client.close()

    def turn(self, text, timeout, event_callback):
        started = time.monotonic()
        turn = self.client.start_turn(self.thread_id, text, SCHEMA)
        messages = []
        try:
            while True:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise AWBError("budget", "Host turn wall-clock deadline exhausted")
                event = self.client.next_event(remaining)
                if time.monotonic() - started >= timeout:
                    raise AWBError("budget", "Host turn wall-clock deadline exhausted")
                event_callback(event)
                if event.get("id") is not None:
                    # No unbudgeted installation, external mutation or approval escalation.
                    self.client._send({"id": event["id"], "error": {"code": -32000,
                        "message": "Evaluation grants workspace writes only; ask the simulated user in the final response."}})
                    self.client.pending.pop(event["id"], None)
                params = event.get("params", {})
                if event.get("method") == "item/completed" and params.get("item", {}).get("type") == "agentMessage":
                    messages.append(params["item"].get("text", ""))
                if event.get("method") == "turn/completed" and params["turn"]["id"] == turn["id"]:
                    if params["turn"]["status"] != "completed":
                        raise AWBError("backend", "Host turn failed", response=params["turn"])
                    for message in reversed(messages):
                        try:
                            value = json.loads(message)
                            if value.get("state") in {"need_input", "continue", "done", "blocked"}:
                                return value
                        except (ValueError, AttributeError):
                            pass
                    raise AWBError("invalid_output", "Host did not produce a structured turn result")
        except BaseException:
            try:
                self.client.interrupt(self.thread_id, turn["id"])
            except AWBError:
                pass
            raise


def run_attempt(case, condition, config, directory, session_factory=HostSession, limits=None, skill_path=None, checker=None):
    bounds = LIMITS | (limits or {})
    if any(not 0 < bounds[key] <= LIMITS[key] for key in LIMITS):
        raise AWBError("budget", "Attempt limits cannot exceed the approved budget")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    workspace = directory / "workspace"
    workspace.mkdir()
    hashes = {}
    for name, content in case["files"].items():
        target = inside(workspace, name)
        atomic_write(target, content.encode("utf-8"))
        hashes[name] = file_digest(target)
    record = {"schema_version": 1, "scenario": case["id"], "family": case["family"], "split": case["split"],
        "condition": condition, "status": "running", "host_turns": 0, "construction_cycles": 0,
        "hidden_retries": 0, "simulated_user": True, "synthetic_fixture": session_factory is not HostSession,
        "qualification": "not_established", "cost": None, "tokens": None, "model_calls": None,
        "question_count": 0, "repeated_questions": 0, "input_hashes": hashes, "limits": bounds,
        "binding": {"scenario": digest(case), "host": digest(config),
                    "skill": digest(skill_files(skill_path)) if skill_path else None},
        "artifact_checks_passed": False, "human_trial": "pending"}
    write_json(directory / "attempt.json", record)
    prompt = case["prompt"] + "\nImplement in this workspace, inspect discoverable facts, preserve supplied inputs. No installation, global configuration edits or external publishing."
    if condition == "generic":
        prompt += "\nUse ordinary engineering rules: understand requirements, explore alternatives, preserve existing code, implement and independently test the whole goal. Ask consequential questions and document launch/configuration/recovery/extensions."
    if skill_path:
        prompt += "\nUse the frozen building-agent-worksystems Skill at " + str(skill_entrypoint(skill_path)) + ". References and modules are under " + str(skill_path) + "; read necessary resources, do not modify them."
    prompt += "\nReturn the required structured response after each host turn: need_input for one question, continue if more implementation is needed, done when your whole implementation is ready for external checks, blocked for an actual blocker. Completion statements are not acceptance evidence."
    conversation = [{"role": "user", "text": prompt}]
    asked, started = set(), time.monotonic()
    last_tree = tree_hashes(workspace)

    def event_callback(event):
        nonlocal last_tree
        if event.get("method") == "item/completed" and event.get("params", {}).get("item", {}).get("type") in {"fileChange", "commandExecution"}:
            current = tree_hashes(workspace)
            if current != last_tree:
                record["construction_cycles"] += 1
                last_tree = current
            if record["construction_cycles"] > bounds["construction_cycles"]:
                record["cycle_budget_exceeded"] = True
                raise AWBError("budget", "Construction change-cycle budget exhausted")

    try:
        with session_factory(workspace=workspace, config=config, directory=directory) as session:
            while record["host_turns"] < bounds["host_turns"]:
                remaining = bounds["seconds"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise AWBError("budget", "Attempt wall-clock budget exhausted")
                record["host_turns"] += 1
                write_json(directory / "attempt.json", record)
                response = session.turn(prompt, timeout=remaining, event_callback=event_callback)
                conversation.append({"role": "assistant", "response": response})
                write_json(directory / "conversation.json", conversation)
                state = response.get("state")
                if state in {"done", "blocked"}:
                    record["status"] = "completed" if state == "done" else "blocked"
                    break
                if state == "need_input":
                    question = response.get("question", "")
                    record["question_count"] += 1
                    record["repeated_questions"] += int(question in asked)
                    asked.add(question)
                    script = next((s for s in case.get("user_script", [])
                                   if any(word.lower() in question.lower() for word in s["match"])), None)
                    if not script:
                        raise AWBError("user_script", "Question has no frozen simulated-user answer", question=question)
                    prompt = "Simulated user: " + script["answer"]
                else:
                    prompt = "Continue the authorized whole-goal implementation within remaining limits. No hidden retries or scope reduction."
                conversation.append({"role": "user", "text": prompt, "simulated": True})
                write_json(directory / "conversation.json", conversation)
            else:
                raise AWBError("budget", "Host-turn budget exhausted")
    except KeyboardInterrupt:
        record.update(status="cancelled", error={"code": "cancelled", "message": "User interrupted evaluation"})
    except Exception as exc:
        error = exc.as_dict() if isinstance(exc, AWBError) else {"code": "environment", "message": str(exc)}
        code = error["code"]
        record.update(status="budget_exhausted" if code in {"budget", "timed_out"} else "failed", error=error)
    remaining = bounds["seconds"] - (time.monotonic() - started)
    checks = {}
    for name in case.get("unchanged", []):
        target = inside(workspace, name)
        checks["preserved:" + name] = target.is_file() and file_digest(target) == hashes[name]
    if skill_path:
        checks["preserved:skill"] = digest(skill_files(skill_path)) == record["binding"]["skill"]
    if remaining > 0 and record["status"] == "completed":
        try:
            validation = case["validator"]
            args = ([sys.executable, str(checker), "--case", str(directory / "case.json"),
                     "--workspace", str(workspace), "--config", str(directory / "host-config.json"),
                     "--evidence", str(directory / "validation")] if checker else validation["argv"])
            write_json(directory / "case.json", case)
            write_json(directory / "host-config.json", config)
            atomic_write(directory / "empty.txt", b"")
            execution = run_process(args, workspace, directory / "empty.txt", directory / "validator.stdout",
                directory / "validator.stderr", min(remaining, 300))
            stdout = (directory / "validator.stdout").read_text(encoding="utf-8", errors="replace")
            checks["actual_program"] = execution["returncode"] == 0 and execution["reason"] is None
            checks["expected_stdout"] = validation.get("stdout_contains", "") in stdout
            record["validation"] = execution
            receipt_path = directory / "validation/receipt.json"
            if checker and receipt_path.is_file():
                validation_receipt = read_json(receipt_path)
                if validation_receipt.get("environment_error"):
                    record.update(status="environment_error", environment_error=validation_receipt["environment_error"])
        except Exception as exc:
            checks["actual_program"] = False
            record["validation_error"] = str(exc)
    else:
        checks["actual_program"] = False
    record.update(artifact_checks=checks, artifact_checks_passed=all(checks.values()),
        elapsed_seconds=time.monotonic() - started, artifact_hashes=tree_hashes(workspace))
    record["cycle_measurement"] = "observed code-tree changes after completed file/command items; internal model reasoning cycles are not observable"
    write_json(directory / "conversation.json", conversation)
    write_json(directory / "attempt.json", record)
    return record


def prepare_matrix(corpus, preflight, output, max_attempts=120, repeats=5):
    count = len(corpus["cases"]) * len(CONDITIONS) * repeats
    if repeats != 5 or count != 120 or max_attempts < count:
        raise AWBError("budget", "The complete matrix requires exactly five repeats and budget for 120 attempts")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    order = [{"scenario": case["id"], "condition": condition, "repetition": n}
             for n in range(repeats) for case in corpus["cases"] for condition in CONDITIONS]
    random.Random(20261001).shuffle(order)
    plan = {"schema_version": 1, "planned_attempts": count, "order": order,
            "corpus_sha256": digest(corpus), "preflight": preflight, "limits": LIMITS,
            "simulated_user": True, "human_trial": "pending"}
    write_json(output / "corpus.json", corpus)
    write_json(output / "plan.json", plan)
    write_json(output / "summary.json", {"complete": False, "qualified": False, "attempts": [],
        "checkpoint": None if preflight.get("passed") else {"reason": "real_access_preflight_failed"}})
    return plan


def freeze_context(output):
    current = freeze_skill(ROOT / "skills", output / "context/builder")
    archive = subprocess.run(["git", "archive", "--format=zip", "v0.1.0-alpha.4"], cwd=ROOT,
                             capture_output=True, check=True).stdout
    previous = output / "context/previous"
    previous.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        for member in source.infolist():
            if member.filename.startswith("skills/") and not member.is_dir():
                atomic_write(inside(previous, member.filename.removeprefix("skills/")), source.read(member))
    frozen = {"builder": current, "previous": {"sha256": digest(skill_files(previous)), "files": skill_files(previous)}}
    controls = [Path(__file__), ROOT / "tools/evaluate.py", * (ROOT / "skills/building-agent-worksystems/scripts/awb_core").rglob("*.py"),
                * (ROOT / "skills/building-agent-worksystems/scripts/awb_core/schemas").glob("*.json")]
    frozen["controller_files"] = {str(path.resolve()): file_digest(path) for path in controls}
    frozen["python_sha256"] = file_digest(Path(sys.executable))
    frozen["dependencies"] = {name: importlib.metadata.version(name) for name in ("jsonschema", "httpx")}
    for name in ("system_checks.py", "system_gateway.py"):
        atomic_write(output / "context" / name, (ROOT / "evals" / name).read_bytes())
        frozen[name] = file_digest(output / "context" / name)
    write_json(output / "context.json", frozen)


def disabled_skill_overlay(inventory):
    # Frozen 0.158.0 reports and matches SKILL.md paths; folder overrides failed the real no-inference precheck.
    return [{"path": str(path), "enabled": False} for path in sorted({Path(s["path"]).resolve()
        for item in inventory.get("data", []) for s in item.get("skills", [])}, key=str)]


def disabled_integrations(host):
    overrides = {}
    for section in ("plugins", "mcp_servers"):
        for name in host.get(section, {}):
            if "." in name or '"' in name:
                raise AWBError("isolation", "Native CLI cannot safely address this integration key", section=section, name=name)
            # Native -c parses dot segments literally, not TOML quoted-key syntax.
            overrides[section + "." + name + ".enabled"] = False
    return overrides


def isolated_config(output, receipt):
    home = Path(receipt["codex_home"])
    config = {"model": receipt["model"], "reasoning_effort": "max", "codex_home": str(home),
              "executable": executable({}), "sandbox": "workspace-write", "workspace_write_authorized": True,
              "approval_policy": "never", "inherit_rules": True, "inherit_user_config": True}
    with AppServerClient(app_server_command(config), output, output / "inventory", config,
                         experimental=True) as client:
        inventory = client.request("skills/list", {"cwds": [str(output)], "forceReload": True})
    host = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
    overlay = {"skills.config": disabled_skill_overlay(inventory)}
    overlay.update(disabled_integrations(host))
    config["config_overrides"] = overlay
    with AppServerClient(app_server_command(config), output, output / "isolation-precheck", config,
                         experimental=True) as client:
        proof = client.request("skills/list", {"cwds": [str(output)], "forceReload": True})
    active = [s["name"] for item in proof.get("data", []) for s in item.get("skills", []) if s.get("enabled")]
    write_json(output / "isolation-precheck/receipt.json", {"enabled_skills": active, "passed": not active})
    if active:
        raise AWBError("isolation", "Implicit Skills remain enabled before matrix launch", skills=active)
    write_json(output / "host-config.json", config)
    context = read_json(output / "context.json")
    context["host_config_sha256"] = digest(config)
    write_json(output / "context.json", context)
    plan = read_json(output / "plan.json")
    plan["frozen_context_sha256"] = digest(context)
    write_json(output / "plan.json", plan)
    return config


def validate_frozen(output, plan, config, context):
    receipt = plan["preflight"]
    checks = {
        "controller": all(Path(path).is_file() and file_digest(Path(path)) == sha for path, sha in context.get("controller_files", {}).items()),
        "python": file_digest(Path(sys.executable)) == context.get("python_sha256"),
        "dependencies": {name: importlib.metadata.version(name) for name in ("jsonschema", "httpx")} == context.get("dependencies"),
        "effective_config": digest(config) == context.get("host_config_sha256"),
        "context_manifest": digest(context) == plan.get("frozen_context_sha256"),
        "approved_model": config.get("model") == receipt["model"] and config.get("reasoning_effort") == "max",
        "approved_home": Path(config["codex_home"]).resolve() == Path(receipt["codex_home"]).resolve(),
        "host_config": file_digest(Path(receipt["codex_home"]) / "config.toml") == receipt["config_sha256"],
        "host_binary": file_digest(config["executable"]) == receipt["binary_sha256"],
        "corpus": digest(read_json(output / "corpus.json")) == plan["corpus_sha256"]}
    for condition in ("builder", "previous"):
        checks[condition] = digest(skill_files(output / "context" / condition)) == context[condition]["sha256"]
    for name in ("system_checks.py", "system_gateway.py"):
        checks[name] = file_digest(output / "context" / name) == context[name]
    if not all(checks.values()):
        raise AWBError("drift", "Frozen evaluation context changed; resume is forbidden", checks=checks)


def evaluate(output):
    output = Path(output).resolve()
    plan, corpus = read_json(output / "plan.json"), read_json(output / "corpus.json")
    summary = read_json(output / "summary.json")
    if not plan["preflight"].get("passed"):
        return summary
    if not (output / "context.json").exists():
        freeze_context(output)
        isolated_config(output, plan["preflight"])
        plan = read_json(output / "plan.json")
    config, context = read_json(output / "host-config.json"), read_json(output / "context.json")
    cases = {c["id"]: c for c in corpus["cases"]}
    attempts = []
    summary["checkpoint"] = None
    for index, job in enumerate(plan["order"]):
        validate_frozen(output, plan, config, context)
        directory = output / ("attempt-%03d" % (index + 1))
        already_attempted = (directory / "attempt.json").is_file()
        if already_attempted:
            attempt = read_json(directory / "attempt.json")
            if attempt["status"] == "running":
                attempt.update(status="interrupted", error={"code": "interrupted", "message": "Previous process ended without a final receipt"})
                write_json(directory / "attempt.json", attempt)
        else:
            skill = output / "context" / job["condition"] if job["condition"] in {"builder", "previous"} else None
            print(json.dumps({"starting": index + 1, **job}), flush=True)
            attempt = run_attempt(cases[job["scenario"]], job["condition"], config, directory,
                skill_path=skill, limits=plan["limits"], checker=output / "context/system_checks.py")
            attempt["repetition"] = job["repetition"]
            write_json(directory / "attempt.json", attempt)
        attempts.append(attempt)
        summary.update(attempts=attempts, complete=len(attempts) == 120, qualified=False)
        summary["conditions"] = {c: {"attempts": sum(a["condition"] == c for a in attempts),
            "artifact_passes": sum(a["condition"] == c and a["artifact_checks_passed"] for a in attempts),
            "question_count": sum(a["question_count"] for a in attempts if a["condition"] == c),
            "failed_or_cancelled": sum(a["condition"] == c and a["status"] != "completed" for a in attempts)}
            for c in CONDITIONS}
        write_json(output / "summary.json", summary)
        print(json.dumps({"finished": index + 1, "status": attempt["status"], "artifact_passed": attempt["artifact_checks_passed"]}), flush=True)
        error_text = json.dumps([attempt.get("error", {}), attempt.get("environment_error", {})]).lower()
        if not already_attempted and (attempt["status"] == "cancelled" or any(s in error_text for s in ("usage limit", "quota", "429", "unsupported", "model_unavailable", "isolation"))):
            summary["checkpoint"] = {"reason": "external_condition", "attempt": index + 1, "error": attempt.get("environment_error") or attempt.get("error")}
            write_json(output / "summary.json", summary)
            break
    summary["release_gate"] = "pending actual human trial, goal-retention/recovery/hard-constraint review; complete matrix alone is not qualification"
    write_json(output / "summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not args.resume:
        if not args.preflight:
            parser.error("--preflight is required for a new matrix")
        prepare_matrix(read_json(ROOT / "evals/systems.json"), read_json(args.preflight), args.output)
    try:
        result = evaluate(args.output)
    except (AWBError, OSError, subprocess.SubprocessError) as exc:
        result = read_json(args.output / "summary.json")
        error = exc.as_dict() if isinstance(exc, AWBError) else {"code": "environment", "message": str(exc)}
        result.update(complete=False, qualified=False, checkpoint={"reason": "setup_or_frozen_context", "error": error})
        write_json(args.output / "summary.json", result)
        print(json.dumps(result["checkpoint"], ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps({"complete": result["complete"], "attempts": len(result["attempts"]),
                      "qualified": result["qualified"], "checkpoint": result["checkpoint"]}, ensure_ascii=False))
