import os
import shutil
from pathlib import Path

from ..contracts import AWBError


def command_argv(config):
    argv = config.get("argv")
    if not config.get("trusted") or not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise AWBError("policy", "Command nodes require trusted configuration and an argv array")
    executable = shutil.which(argv[0])
    if not executable:
        raise AWBError("backend", "Command executable is unavailable")
    allowed = {os.path.normcase(str(Path(p).resolve())) for p in config.get("allowed_executables", [])}
    if os.path.normcase(str(Path(executable).resolve())) not in allowed:
        raise AWBError("policy", "Command executable is not allowlisted")
    if Path(executable).suffix.lower() in {".bat", ".cmd"}:
        raise AWBError("policy", "Batch launchers require a native executable adapter")
    return [executable, *argv[1:]]
