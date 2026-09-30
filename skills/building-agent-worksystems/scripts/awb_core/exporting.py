import sqlite3
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path

from .contracts import AWBError, canonical, file_digest, inside, read_json
from .locking import mutation


@mutation
def export_project(store, destination):
    destination = inside(store.project, destination)
    if destination.exists() or destination.is_relative_to(store.root):
        raise AWBError("export", "Export needs a new destination outside internal state")
    store.goal()
    files = set()
    for path in store.root.rglob("*"):
        if path.is_file() and path.name not in {"state.sqlite", "state.sqlite-wal", "state.sqlite-shm"} and "locks" not in path.relative_to(store.root).parts:
            files.add(inside(store.project, path))
    for run in store.list("run"):
        files.update(inside(store.project, s["path"]) for s in run.get("sources", []))
    spec = store.root / "system.spec.json"
    if spec.exists():
        files.update(inside(store.project, p) for p in read_json(spec).get("files", {}))
    hashes = {p.relative_to(store.project).as_posix(): file_digest(p) for p in files}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="awb-export-") as temporary:
        backup = Path(temporary) / "state.sqlite"
        with store.connection() as source, closing(sqlite3.connect(backup)) as target:
            source.backup(target)
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(backup, ".worksystem-build/state.sqlite")
            for path in sorted(files):
                relative = path.relative_to(store.project).as_posix()
                if file_digest(path) != hashes[relative]:
                    raise AWBError("drift", "Project changed during export; archive is incomplete")
                archive.write(path, relative)
            archive.writestr("export-manifest.json", canonical({"schema_version": 1, "files": hashes, "database_sha256": file_digest(backup)}))
    return {"path": str(destination), "sha256": file_digest(destination), "files": len(files) + 2}
