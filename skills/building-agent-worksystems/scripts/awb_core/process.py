"""Owned process trees, closed stdin and bounded log files."""
import ctypes
import os
import signal
import subprocess
import time
from ctypes import wintypes

from .contracts import AWBError


class WindowsJob:
    def __init__(self, process):
        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t),
                        ("active", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ("read", "write", "other", "rb", "wb", "ob")]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle or not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise AWBError("process", "Cannot establish owned process job")
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            self.close()
            raise AWBError("process", "Cannot attach process to owned job")

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def resume_owned_process(process):
    class ThreadEntry(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD), ("thread_id", wintypes.DWORD),
                    ("owner_id", wintypes.DWORD), ("base_priority", wintypes.LONG),
                    ("delta_priority", wintypes.LONG), ("flags", wintypes.DWORD)]
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    api.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    api.Thread32First.argtypes = api.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
    api.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenThread.restype = wintypes.HANDLE
    api.ResumeThread.argtypes = [wintypes.HANDLE]
    api.ResumeThread.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = api.CreateToolhelp32Snapshot(4, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise AWBError("process", "Cannot inspect suspended process thread")
    entry = ThreadEntry()
    entry.size = ctypes.sizeof(entry)
    try:
        found = api.Thread32First(snapshot, ctypes.byref(entry))
        while found:
            if entry.owner_id == process.pid:
                thread = api.OpenThread(2, False, entry.thread_id)
                if not thread:
                    raise AWBError("process", "Cannot open owned process thread")
                try:
                    if api.ResumeThread(thread) == 0xffffffff:
                        raise AWBError("process", "Cannot resume owned process thread")
                    return
                finally:
                    api.CloseHandle(thread)
            found = api.Thread32Next(snapshot, ctypes.byref(entry))
        raise AWBError("process", "Suspended process thread was not found")
    finally:
        api.CloseHandle(snapshot)


def run_process(argv, cwd, input_path, stdout_path, stderr_path, timeout, cancel=None, max_bytes=4 * 1024 * 1024):
    process, job = None, None
    reason = None
    started = time.monotonic()
    try:
        with input_path.open("rb") as stdin, stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(argv, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr,
                                       shell=False, creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | 4) if os.name == "nt" else 0,
                                       start_new_session=os.name != "nt")
            if os.name == "nt":
                job = WindowsJob(process)
                resume_owned_process(process)
            while process.poll() is None:
                if cancel is not None and cancel.is_set():
                    reason = "cancelled"
                    break
                if time.monotonic() - started >= timeout:
                    reason = "timed_out"
                    break
                if stdout_path.stat().st_size + stderr_path.stat().st_size > max_bytes:
                    reason = "output_limit"
                    break
                time.sleep(0.02)
            if not reason and stdout_path.stat().st_size + stderr_path.stat().st_size > max_bytes:
                reason = "output_limit"
    finally:
        if job:
            job.close()
        elif process is not None and os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
    return {"returncode": process.returncode, "reason": reason, "elapsed_seconds": time.monotonic() - started}
