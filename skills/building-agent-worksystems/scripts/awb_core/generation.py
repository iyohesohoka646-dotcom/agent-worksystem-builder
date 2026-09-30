import base64
import hashlib
import re
from pathlib import Path

from .contracts import AWBError, atomic_write, digest, file_digest, inside, write_json
from .locking import project_lock, mutation


def canonical_name(name):
    if not isinstance(name, str) or not name or name.startswith(("/", "\\")):
        raise AWBError("ownership", "A relative managed path is required")
    parts = name.replace("\\", "/").split("/")
    for part in parts:
        if (not part or part in {".", ".."} or part.endswith((".", " "))
                or re.search(r'[<>:"|?*\x00-\x1f]', part)
                or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)):
            raise AWBError("ownership", "Ambiguous or reserved managed path")
    return "/".join(parts)


def managed_path(store, name):
    name = canonical_name(name)
    path = Path(name)
    if path.is_absolute() or not path.parts or path.parts[0].lower() in {".git", ".worksystem-build"}:
        raise AWBError("ownership", "Cannot generate reserved state or absolute paths")
    return inside(store.project, name)


def prepare_change(accepted_spec, candidate_spec, workspace_state):
    with project_lock(workspace_state, "mutation"):
        return _prepare_change(accepted_spec, candidate_spec, workspace_state)


def _prepare_change(accepted_spec, candidate_spec, workspace_state):
    store = workspace_state
    files = candidate_spec.get("files", {})
    names = [canonical_name(name) for name in files]
    folded = [name.casefold() for name in names]
    if not files or len(set(folded)) != len(files) or any(a != b and b.startswith(a + "/") for a in folded for b in folded):
        raise AWBError("change", "A candidate needs distinct file paths, including case-insensitive platforms")
    files = dict(zip(names, files.values()))
    baseline = store.accepted_spec()
    if baseline["revision"] and accepted_spec.get("files", {}) != baseline["files"]:
        raise AWBError("revision", "Candidate baseline differs from the accepted specification")
    entries = []
    for name, content in files.items():
        path = managed_path(store, name)
        if path.exists() and not path.is_file():
            raise AWBError("ownership", "Managed target must be a regular file")
        before = path.read_bytes() if path.exists() else None
        before_hash = hashlib.sha256(before).hexdigest() if before is not None else None
        if before is not None and accepted_spec.get("files", {}).get(name) != before_hash:
            raise AWBError("drift", "Unowned or modified file; preserve user edits", path=name)
        if content is not None and not isinstance(content, str):
            raise AWBError("change", "Candidate file contents must be text or null")
        after = content.encode("utf-8") if content is not None else None
        entries.append({"path": name, "before_hash": before_hash,
                        "after_hash": hashlib.sha256(after).hexdigest() if after is not None else None,
                        "before": base64.b64encode(before).decode() if before is not None else None,
                        "after": base64.b64encode(after).decode() if after is not None else None})
    record = store.create("change", {"status": "prepared", "entries": entries,
                                      "goal_revision": store.goal()["revision"], "baseline": accepted_spec,
                                      "baseline_spec_revision": baseline["revision"],
                                      "candidate_digest": digest(entries)})
    write_json(store.root / "changes" / f"{record['id']}.json", record)
    return record


def _current(path):
    return file_digest(path) if path.is_file() else None


def _reconcile(store, change_id, reverse):
    record = store.get(change_id)
    if record["kind"] != "change":
        raise AWBError("change", "Not a change record")
    if reverse and any(c.get("change_id") == change_id and c["status"] == "accepted" for c in store.list("cycle")):
        raise AWBError("change", "Accepted changes require a new compensating candidate")
    if not reverse and record.get("baseline_spec_revision", 0) != store.accepted_spec()["revision"]:
        raise AWBError("revision", "Candidate baseline is stale")
    if record["goal_revision"] != store.goal()["revision"] and not reverse:
        raise AWBError("change", "Goal changed after this change was prepared")
    if record["status"] == "rolled_back" and not reverse:
        raise AWBError("change", "Prepare a new change after rollback")
    if digest(record["entries"]) != record["candidate_digest"]:
        raise AWBError("drift", "Change manifest drift")
    source, target = ("after", "before") if reverse else ("before", "after")
    for entry in record["entries"]:
        path = managed_path(store, entry["path"])
        if path.exists() and not path.is_file():
            raise AWBError("drift", "Managed file was replaced by a directory")
        if _current(path) not in {entry[source + "_hash"], entry[target + "_hash"]}:
            raise AWBError("drift", "File drift prevents applying or rolling back the change", path=entry["path"])
    record = store.update(change_id, record["revision"], {"status": "rolling_back" if reverse else "applying"})
    for entry in record["entries"]:
        path = managed_path(store, entry["path"])
        current = _current(path)
        if current == entry[target + "_hash"]:
            continue
        if current != entry[source + "_hash"]:
            raise AWBError("drift", "File changed while applying the manifest")
        if entry[target] is None:
            path.unlink()
        else:
            atomic_write(path, base64.b64decode(entry[target]))
    return store.update(change_id, record["revision"], {"status": "rolled_back" if reverse else "applied"})


@mutation
def apply_change(store, manifest):
    return _reconcile(store, manifest["id"], False)


@mutation
def rollback_change(store, change_id):
    return _reconcile(store, change_id, True)
