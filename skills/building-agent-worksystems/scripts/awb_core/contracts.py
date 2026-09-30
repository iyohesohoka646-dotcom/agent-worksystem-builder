from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


class AWBError(Exception):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code, self.details = code, details

    def as_dict(self):
        return {"code": self.code, "message": str(self), "details": self.details}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inside(root, path):
    root = Path(root).resolve()
    candidate = Path(path)
    candidate = candidate if candidate.is_absolute() else root / candidate
    if ".." in candidate.parts or not candidate.resolve().is_relative_to(root):
        raise AWBError("path", "path points outside the permitted workspace")
    current = root
    for part in candidate.relative_to(root).parts:
        current /= part
        if current.exists() or current.is_symlink():
            info = current.lstat()
            if current.is_symlink() or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024):
                raise AWBError("path", "symlinks and junctions are not managed artifacts")
    return candidate.resolve()


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".awb-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, payload):
    atomic_write(path, canonical(payload) + b"\n")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise AWBError("record", f"Cannot read JSON record: {Path(path).name}") from exc


def validate_schema(schema, value):
    try:
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(value))
    except Exception as exc:
        raise AWBError("schema", "Invalid JSON schema") from exc
    if errors:
        raise AWBError("schema", f"Invalid schema result: {errors[0].message}")
    return value


def validate_record(kind, payload):
    path = Path(__file__).with_name("schemas") / f"{kind}.json"
    if not path.is_file() or kind not in {"goal", "node", "result"}:
        raise AWBError("schema", f"Unknown schema kind: {kind}")
    validate_schema(read_json(path), payload)
    if kind == "goal":
        ids = [r["id"] for r in payload["requirements"]]
        if len(ids) != len(set(ids)):
            raise AWBError("schema", "Requirement IDs must be unique")
        for r in payload["requirements"]:
            if r["source"] == "inference" and r["status"] == "confirmed":
                raise AWBError("schema", "An inference cannot be confirmed without a new source")
    return json.loads(canonical(payload))
