import json
import math
import shutil
from pathlib import Path

from ..contracts import AWBError


def toml_literal(value):
    """Serialize CLI -c values as TOML (JSON objects are not TOML tables)."""
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and math.isfinite(value):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_literal(item) for item in value) + "]"
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return "{" + ", ".join(json.dumps(key) + " = " + toml_literal(item) for key, item in value.items()) + "}"
    raise AWBError("configuration", "Unsupported TOML override value")


def executable(config):
    requested = config.get("executable") or shutil.which("codex")
    if not requested:
        raise AWBError("backend", "Codex executable is unavailable")
    path = Path(requested).resolve()
    if path.suffix.lower() in {".cmd", ".bat"} or path.suffix == "":
        candidates = list((path.parent / "node_modules" / "@openai" / "codex").glob("node_modules/@openai/codex-*/vendor/*/bin/codex.exe"))
        if candidates:
            return str(candidates[0])
    if path.suffix.lower() in {".cmd", ".bat"}:
        raise AWBError("backend", "Resolve Codex to a native executable")
    return str(path)


def argv(config, directory, schema, final):
    if not config.get("model"):
        raise AWBError("configuration", "Codex model must be explicitly configured")
    sandbox = config.get("sandbox", "read-only")
    if sandbox not in {"read-only", "workspace-write"}:
        raise AWBError("policy", "Codex supports only read-only or scoped workspace-write here")
    if sandbox == "workspace-write" and config.get("workspace_write_authorized") is not True:
        raise AWBError("policy", "Workspace writes must be authorized before execution")
    args = [executable(config), "exec", "--ephemeral", "--sandbox", sandbox,
            "--skip-git-repo-check", "--color", "never", "--json", "--model", config["model"]]
    if config.get("inherit_user_config", True) is False:
        args.append("--ignore-user-config")
    if config.get("inherit_rules", True) is False:
        args.append("--ignore-rules")
    overrides = dict(config.get("config_overrides", {}))
    # Noninteractive exec cannot resolve interactive prompts: fail/deny instead of silently escalating.
    overrides["approval_policy"] = "never"
    if config.get("reasoning_effort"):
        overrides["model_reasoning_effort"] = config["reasoning_effort"]
    for key, value in overrides.items():
        args += ["-c", key + "=" + toml_literal(value)]
    return args + ["--output-schema", str(schema), "-o", str(final), "-C", str(directory), "-"]


def normalize(final_path, events_path):
    failed = False
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError as exc:
            raise AWBError("invalid_output", "Codex emitted invalid event JSONL") from exc
        if event.get("type") in {"turn.failed", "error"}:
            failed = True
    if failed or not final_path.is_file():
        raise failure_error(events_path) or AWBError("backend", "Codex did not produce a successful final response")
    try:
        return json.loads(final_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise AWBError("invalid_output", "Codex final response is not JSON") from exc


def failure_error(events_path):
    """Classify actual host error events, never assistant-authored completion text."""
    if not Path(events_path).is_file():
        return None
    for line in Path(events_path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") not in {"error", "turn.failed"}:
            continue
        raw = event.get("error", event.get("message", "Codex turn failed"))
        message = raw.get("message", str(raw)) if isinstance(raw, dict) else str(raw)
        lower = message.lower()
        code = "quota" if any(word in lower for word in ("usage limit", "quota", "429")) else "model_unavailable" if any(word in lower for word in ("not supported", "unsupported", "not available")) else "backend"
        return AWBError(code, message)
    return None
