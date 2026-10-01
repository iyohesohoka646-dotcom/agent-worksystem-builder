import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from awb_core.contracts import AWBError, file_digest
from awb_core.state import Store
from awb_core.verification import verify_candidate
from awb_core.generation import prepare_change, apply_change
from test_state import goal
from test_system_contracts import architecture, profile


def candidate(tmp_path):
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "A standalone program preserves sources", "requirement_ids": ["R1"]})
    change = prepare_change(db.accepted_spec(), {"files": {"main.py": "print('correct output')\n"}}, db)
    apply_change(db, change)
    db.update(cycle["id"], cycle["revision"], {"change_id": change["id"]})
    return db, {"store": db, "cycle_id": cycle["id"], "change_id": change["id"]}


def test_program_verifier_executes_actual_candidate_and_binds_dependencies(tmp_path):
    db, ref = candidate(tmp_path)
    acceptance = {"kind": "program", "requirement_ids": ["R1"], "argv": [sys.executable, "main.py"],
                  "allowed_executables": [sys.executable], "trusted": True, "timeout": 3,
                  "stdout_contains": "correct output", "input_files": ["main.py"]}
    result = verify_candidate(ref, acceptance)
    assert result["passed"]
    assert result["bindings"]["requirement_ids"] == ["R1"]
    (tmp_path / "main.py").write_text("raise SystemExit(2)\n", encoding="utf-8")
    with pytest.raises(AWBError, match="drifted"):
        db.check_evidence(result["id"])
    assert not verify_candidate(ref, acceptance)["passed"]


def test_artifact_verifier_rejects_claims_without_matching_actual_bytes(tmp_path):
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Inspect real JSON"})
    (tmp_path / "result.json").write_text('{"passed":true,"count":1}', encoding="utf-8")
    ref = {"store": db, "cycle_id": cycle["id"]}
    result = verify_candidate(ref, {"kind": "artifact", "requirement_ids": ["R1"],
                                    "assertions": [{"path": "result.json", "json_value": {"count": 2}}]})
    assert result["passed"] is False


def test_service_verifier_checks_real_response_and_rejects_external_destination(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ready":true}')
        def log_message(self, *args):
            pass
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Check running service"})
    ref = {"store": db, "cycle_id": cycle["id"]}
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        result = verify_candidate(ref, {"kind": "service", "requirement_ids": ["R1"], "timeout": 2,
              "requests": [{"url": f"http://127.0.0.1:{server.server_port}/health", "status": 200, "json_value": {"ready": True}}]})
        assert result["passed"]
        assert not verify_candidate(ref, {"kind": "service", "requirement_ids": ["R1"], "timeout": 2,
              "requests": [{"url": f"http://127.0.0.1:{server.server_port}/health", "status": 201}]})["passed"]
        with pytest.raises(AWBError, match="loopback"):
            verify_candidate(ref, {"kind": "service", "requirement_ids": ["R1"], "timeout": 2,
                                  "requests": [{"url": "https://example.com", "status": 200}]})
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


def test_registered_domain_verifier_and_profile_version_are_bound(tmp_path):
    from awb_core.verification import register_verifier
    db = Store.initialize(tmp_path, goal())
    p = db.record_contract("profile", profile())
    a = db.record_contract("architecture", architecture() | {"intelligence_profile_id": p["id"],
         "acceptance": [{"id": "domain", "requirement_ids": ["R1"], "verifier": "example-domain", "config": {"expected": "domain output"}}]})
    cycle = db.create("cycle", {"hypothesis": "Check domain", "architecture_id": a["id"], "profile_id": p["id"]})
    (tmp_path / "item.txt").write_text("domain output", encoding="utf-8")
    def domain(store, acceptance, directory):
        return {"checks": {"domain_correct": (store.project / "item.txt").read_text() == acceptance["expected"]},
                "artifacts": [store.project / "item.txt"], "dependency_hashes": {}}
    register_verifier("example-domain", "1", domain)
    result = verify_candidate({"store": db, "cycle_id": cycle["id"]},
                              {"kind": "example-domain", "acceptance_id": "domain", "expected": "domain output", "requirement_ids": ["R1"]})
    assert result["passed"]
    db.record_contract("profile", profile() | {"budget": {"max_calls": 0, "max_seconds": 20}}, p["id"], p["revision"])
    with pytest.raises(AWBError, match="profile|contract"):
        db.check_evidence(result["id"])


def test_accepted_local_candidate_does_not_complete_uncovered_whole_goal(tmp_path):
    from awb_core.delivery import coverage
    from awb_core.cycle import apply_decision
    g = goal()
    g["requirements"].append({"id": "R2", "text": "Second independent outcome", "kind": "acceptance", "source": "user", "status": "confirmed"})
    db = Store.initialize(tmp_path, g)
    (tmp_path / "item.txt").write_text("first", encoding="utf-8")
    cycle = db.create("cycle", {"hypothesis": "First outcome", "requirement_ids": ["R1"]})
    ev = verify_candidate({"store": db, "cycle_id": cycle["id"]},
                          {"kind": "artifact", "requirement_ids": ["R1"], "assertions": [{"path": "item.txt", "contains": "first"}]})
    for status in ("implementing", "verifying", "deciding"):
        cycle = db.record_transition(cycle["id"], cycle["revision"], status, [])
    apply_decision(db, cycle["id"], {"action": "accept", "reason": "Actual output passed", "evidence_refs": [ev["id"]]})
    assert coverage(db)["complete"] is False
    assert coverage(db)["missing"] == ["R2"]


def test_architecture_acceptance_cannot_be_replaced_after_candidate_results(tmp_path):
    db = Store.initialize(tmp_path, goal())
    cfg = {"assertions": [{"path": "result.json", "json_value": {"count": 2}}]}
    a = db.record_contract("architecture", architecture() | {"acceptance": [{"id": "count", "requirement_ids": ["R1"], "verifier": "artifact", "config": cfg}]})
    cycle = db.create("cycle", {"hypothesis": "Count", "architecture_id": a["id"]})
    (tmp_path / "result.json").write_text('{"count":1}')
    with pytest.raises(AWBError, match="acceptance"):
        verify_candidate({"store": db, "cycle_id": cycle["id"]}, {"kind": "artifact", "acceptance_id": "count", "requirement_ids": ["R1"],
             "assertions": [{"path": "result.json", "json_value": {"count": 1}}]})


def test_artifact_boolean_is_not_an_integer_result(tmp_path):
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Strict independent result"})
    (tmp_path / "result.json").write_text('{"count":true}')
    result = verify_candidate({"store": db, "cycle_id": cycle["id"]}, {"kind": "artifact", "requirement_ids": ["R1"],
                             "assertions": [{"path": "result.json", "json_value": {"count": 1}}]})
    assert not result["passed"]


def test_delivery_requires_actual_current_launch_evidence(tmp_path):
    from awb_core.delivery import check_delivery
    db = Store.initialize(tmp_path, goal())
    a = db.record_contract("architecture", architecture())
    for name in ("architecture", "dependencies", "configuration", "recovery", "extensions"):
        (tmp_path / (name + ".md")).write_text("Real description", encoding="utf-8")
    manifest = {name: name + ".md" for name in ("architecture", "dependencies", "configuration", "recovery", "extensions")}
    result = check_delivery(db, manifest | {"architecture_id": a["id"]})
    assert result["checks"]["independent_entrypoint"] is False


def test_service_verifier_owns_startup_and_binds_the_launched_program(tmp_path):
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    source = "import os\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\nclass H(BaseHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200); self.send_header('X-AWB-Instance', os.environ['AWB_VERIFICATION_TOKEN']); self.end_headers(); self.wfile.write(b'{\"ready\":true}')\nHTTPServer(('127.0.0.1', " + str(port) + "), H).serve_forever()\n"
    (tmp_path / "server.py").write_text(source, encoding="utf-8")
    db = Store.initialize(tmp_path, goal())
    config = {"entrypoint_id": "service", "instance_header": "X-AWB-Instance", "startup": {"argv": [sys.executable, "server.py"], "allowed_executables": [sys.executable], "trusted": True, "input_files": ["server.py"]},
              "timeout": 5, "requests": [{"url": f"http://127.0.0.1:{port}", "status": 200, "json_value": {"ready": True}}]}
    a = db.record_contract("architecture", architecture() | {"entrypoints": [{"id": "service", "component_id": "cli", "argv": [sys.executable, "server.py"]}],
             "acceptance": [{"id": "healthy", "requirement_ids": ["R1"], "verifier": "service", "config": config}]})
    cycle = db.create("cycle", {"hypothesis": "Launch independent service", "architecture_id": a["id"]})
    ev = verify_candidate({"store": db, "cycle_id": cycle["id"]}, config | {"kind": "service", "acceptance_id": "healthy", "requirement_ids": ["R1"]})
    assert ev["passed"] and ev["bindings"]["entrypoint_id"] == "service"
    (tmp_path / "server.py").write_text("raise SystemExit(1)", encoding="utf-8")
    with pytest.raises(AWBError, match="drift"):
        db.check_evidence(ev["id"])


def test_startup_cannot_claim_an_already_running_unrelated_service(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{}')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    db = Store.initialize(tmp_path, goal())
    cycle = db.create("cycle", {"hypothesis": "Unrelated service is not owned startup"})
    try:
        with pytest.raises(AWBError, match="running|instance"):
            verify_candidate({"store": db, "cycle_id": cycle["id"]}, {"kind": "service", "requirement_ids": ["R1"], "timeout": 2,
                "instance_header": "X-AWB-Instance", "startup": {"argv": [sys.executable, "-c", "import time;time.sleep(60)"], "allowed_executables": [sys.executable], "trusted": True},
                "requests": [{"url": f"http://127.0.0.1:{server.server_port}", "status": 200}]})
    finally:
        server.shutdown(); server.server_close(); worker.join()


def test_omitted_cycle_profile_is_inherited_from_architecture_and_bound(tmp_path):
    db = Store.initialize(tmp_path, goal())
    p = db.record_contract("profile", profile())
    cfg = {"assertions": [{"path": "result.txt", "contains": "actual"}]}
    a = db.record_contract("architecture", architecture() | {"intelligence_profile_id": p["id"], "acceptance": [{"id": "actual", "requirement_ids": ["R1"], "verifier": "artifact", "config": cfg}]})
    cycle = db.create("cycle", {"hypothesis": "Selected configuration is not optional", "architecture_id": a["id"]})
    (tmp_path / "result.txt").write_text("actual")
    ev = verify_candidate({"store": db, "cycle_id": cycle["id"]}, cfg | {"kind": "artifact", "acceptance_id": "actual", "requirement_ids": ["R1"]})
    assert ev["bindings"]["profile_id"] == p["id"]
    other = db.record_contract("profile", profile() | {"budget": {"max_calls": 0, "max_seconds": 30}})
    wrong = db.create("cycle", {"hypothesis": "Conflicting configuration", "architecture_id": a["id"], "profile_id": other["id"]})
    with pytest.raises(AWBError, match="conflicts"):
        db.record_transition(wrong["id"], wrong["revision"], "implementing", [])
