import json
import shutil
from pathlib import Path

from ..contracts import AWBError


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
    return [executable(config), "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--sandbox", "read-only", "--skip-git-repo-check", "--color", "never", "--json",
            "--model", config["model"], "--output-schema", str(schema), "-o", str(final), "-C", str(directory), "-"]


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
        raise AWBError("backend", "Codex did not produce a successful final response")
    try:
        return json.loads(final_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise AWBError("invalid_output", "Codex final response is not JSON") from exc
