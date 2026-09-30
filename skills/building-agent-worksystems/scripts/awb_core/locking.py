import os
import re
import threading
from contextlib import contextmanager
from functools import wraps

from .contracts import AWBError, inside

_held = threading.local()


def mutation(function):
    @wraps(function)
    def locked(store, *args, **kwargs):
        with project_lock(store, "mutation"):
            return function(store, *args, **kwargs)
    return locked


class Cancellation:
    def __init__(self, store, run_id):
        self.path = inside(store.project, store.root / "cancellations" / (run_id + ".json"))

    def is_set(self):
        return self.path.is_file()


@contextmanager
def project_lock(store, resource):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", resource):
        raise AWBError("lock", "Invalid lock resource")
    path = inside(store.project, store.root / "locks" / (resource + ".lock"))
    key = str(path).casefold()
    held = getattr(_held, "keys", set())
    if key in held:
        yield
        return
    path.parent.mkdir(exist_ok=True)
    stream = path.open("a+b")
    locked = False
    try:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            raise AWBError("busy", "Another process owns this operation") from exc
        _held.keys = held | {key}
        yield
    finally:
        _held.keys = held
        if locked:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()
