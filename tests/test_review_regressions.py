import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from test_state import goal
from test_execution import node as process_node
from test_scheduler import node


def accept_change(store, change):
    from awb_core.cycle import apply_decision
    from awb_core.generation import apply_change
    cycle = store.create("cycle", {"hypothesis": "Controlled change", "change_id": change["id"]})
    apply_change(store, change)
    for status in ("implementing", "verifying", "deciding"):
        cycle = store.record_transition(cycle["id"], cycle["revision"], status, [])
    files = [store.project / e["path"] for e in change["entries"] if e["after"] is not None]
    evidence = store.add_evidence(cycle["id"], files, {"correct": True}, {"goal_revision": 1, "candidate_digest": change["candidate_digest"]})
    return apply_decision(store, cycle["id"], {"action": "accept", "reason": "Checked result", "evidence_refs": [evidence["id"]]})


def test_accepted_spec_is_recovered_after_interrupted_publication(tmp_path, monkeypatch):
    from awb_core.state import Store
    from awb_core.generation import prepare_change
    import awb_core.state as state
    import awb_core.cycle as cycle
    original = state.write_json
    db = Store.initialize(tmp_path, goal())
    change = prepare_change({"files": {}}, {"files": {"a.txt": "A"}}, db)
    def fail_publication(path, payload):
        if path.name == "system.spec.json":
            raise OSError("injected crash after accepted transaction")
        return original(path, payload)
    with monkeypatch.context() as patch:
        patch.setattr(state, "write_json", fail_publication)
        patch.setattr(cycle, "write_json", fail_publication)
        with pytest.raises(OSError):
            accept_change(db, change)
    restored = Store(tmp_path)
    assert (restored.root / "system.spec.json").is_file()
    spec = json.loads((restored.root / "system.spec.json").read_text())
    assert "a.txt" in spec["files"]


def test_stale_candidate_cannot_discard_previous_acceptance(tmp_path):
    from awb_core.state import Store
    from awb_core.generation import prepare_change, rollback_change
    from awb_core.contracts import AWBError
    db = Store.initialize(tmp_path, goal())
    one = prepare_change({"files": {}}, {"files": {"a.txt": "A"}}, db)
    two = prepare_change({"files": {}}, {"files": {"b.txt": "B"}}, db)
    accept_change(db, one)
    with pytest.raises(AWBError):
        accept_change(db, two)
    assert "a.txt" in json.loads((db.root / "system.spec.json").read_text())["files"]
    with pytest.raises(AWBError):
        rollback_change(db, one["id"])


def test_failed_side_effect_is_not_replayed_on_resume(tmp_path):
    from awb_core.scheduler import run_graph
    from awb_core.state import Store
    counter = tmp_path / "counter.txt"
    code = f"from pathlib import Path; p=Path({str(counter)!r}); p.write_text((p.read_text() if p.exists() else '')+'x'); raise SystemExit(2)"
    step = process_node(code) | {"id": "charge", "side_effect": "unknown"}
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    first = run_graph(db, {"nodes": [step]}, {}, 3, 10)
    again = run_graph(db, {"nodes": [step]}, {}, 3, 10, run_id=first["id"])
    assert again["status"] == "needs_human"
    assert counter.read_text() == "x"


def test_uncertain_timeout_is_not_automatically_retried(tmp_path):
    from awb_core.execution import execute_node, Budget
    counter = tmp_path / "counter.txt"
    code = f"from pathlib import Path; import time; p=Path({str(counter)!r}); p.write_text((p.read_text() if p.exists() else '')+'x'); time.sleep(5)"
    # Leave startup headroom: this regression needs the side effect before timeout.
    result = execute_node(process_node(code) | {"retries": 2, "timeout": 2, "side_effect": "unknown"}, {}, {"workspace": tmp_path}, Budget(3, 8))
    assert result["status"] == "timed_out"
    assert len(result["attempts"]) == 1
    assert counter.exists(), result
    assert counter.read_text() == "x"


def test_evidence_rejects_artifact_swapped_after_verification(tmp_path, monkeypatch):
    from awb_core.state import Store
    from awb_core.materials import run_materials
    from awb_core.verification import verify_candidate
    from awb_core.contracts import AWBError
    db = Store.initialize(tmp_path, goal())
    folder = tmp_path / "input"
    folder.mkdir()
    (folder / "a.txt").write_text("Research")
    run = run_materials(db, folder)
    cycle = db.create("cycle", {"hypothesis": "Correct category"})
    original = db.add_evidence
    def swap(*args, **kwargs):
        (tmp_path / run["outputs"]["jsonl"]).write_text('{"category":"wrong"}\n')
        return original(*args, **kwargs)
    monkeypatch.setattr(db, "add_evidence", swap)
    with pytest.raises(AWBError):
        verify_candidate({"store": db, "cycle_id": cycle["id"]}, {"kind": "materials", "run_id": run["id"], "reference": {"a.txt": "research"}})


@pytest.mark.parametrize("files", [
    {"dir/a.txt": "A", "dir\\a.txt": "B"}, {"a.txt": "A", "./a.txt": "B"},
    {"file": "A", "file/child": "B"}, {"bad.txt.": "x"}, {"CON.txt": "x"}, {"a.txt:stream": "x"},
])
def test_manifest_rejects_windows_aliases_before_mutation(tmp_path, files):
    from awb_core.generation import prepare_change
    from awb_core.state import Store
    from awb_core.contracts import AWBError
    db = Store.initialize(tmp_path, goal())
    with pytest.raises(AWBError):
        prepare_change({"files": {}}, {"files": files}, db)
    assert not db.list("change")


@pytest.mark.skipif(os.name != "nt", reason="Windows ownership race")
def test_failed_job_assignment_never_starts_user_code(tmp_path, monkeypatch):
    import awb_core.process as process
    from awb_core.execution import execute_node, Budget
    from awb_core.contracts import AWBError
    marker = tmp_path / "started.txt"
    def fail_job(child):
        time.sleep(0.3)
        raise AWBError("process", "simulated assignment failure")
    monkeypatch.setattr(process, "WindowsJob", fail_job)
    result = execute_node(process_node(f"from pathlib import Path; Path({str(marker)!r}).write_text('started'); import time; time.sleep(5)"), {}, {"workspace": tmp_path}, Budget(1, 5))
    assert result["status"] == "failed"
    assert not marker.exists()


@pytest.mark.parametrize("body", [None, [], "text"])
def test_malformed_http_payload_is_a_normalized_failure(body):
    from awb_core.adapters.ollama import parse_response
    from awb_core.contracts import AWBError
    with pytest.raises(AWBError):
        parse_response(body)


def test_http_drip_cannot_exceed_total_deadline(tmp_path):
    from awb_core.execution import execute_node, Budget
    contacted = threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            contacted.set()
            self.send_response(200)
            self.end_headers()
            try:
                for _ in range(80):
                    self.wfile.write(b" ")
                    self.wfile.flush()
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    started = time.monotonic()
    try:
        result = execute_node({"id": "slow", "backend": "ollama", "model": "fixture", "endpoint": f"http://127.0.0.1:{server.server_port}",
                               "timeout": 1.5, "output_schema": {"type": "object"}}, {}, {"workspace": tmp_path}, Budget(1, 2))
        elapsed = time.monotonic() - started
    finally:
        server.shutdown()
        server.server_close()
    assert contacted.is_set(), (result, (tmp_path / result["logs"]["stderr"]).read_text(encoding="utf-8"))
    assert result["status"] == "timed_out"
    assert elapsed < 3


def test_worker_exception_preserves_successful_parallel_sibling(tmp_path, monkeypatch):
    import awb_core.scheduler as scheduler
    from awb_core.state import Store
    from awb_core.contracts import AWBError
    db = Store.initialize(tmp_path, goal() | {"offline": False})
    original = scheduler._node
    def fail(node_spec, *args):
        if node_spec["id"] == "bad":
            raise AWBError("budget", "injected budget exhaustion")
        return original(node_spec, *args)
    monkeypatch.setattr(scheduler, "_node", fail)
    result = scheduler.run_graph(db, {"nodes": [node("bad"), node("good")]}, {}, 2, 10, 2)
    assert result["status"] != "running"
    assert result["nodes"]["good"]["status"] == "completed"
