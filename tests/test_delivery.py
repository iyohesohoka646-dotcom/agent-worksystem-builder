import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_records_real_failure_correction_and_acceptance(tmp_path):
    result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "demo.py"), "--project", str(tmp_path / "demo")],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["baseline_passed"] is False
    assert report["candidate_passed"] is True
    assert report["accepted"] is True
    assert report["synthetic_fixture"] is True
    assert report["real_model_used"] is False


def test_evidence_keeps_original_bytes_after_artifact_changes(tmp_path):
    from awb_core.state import Store
    from test_state import goal
    db = Store.initialize(tmp_path, goal())
    item = tmp_path / "item.txt"
    item.write_text("original", encoding="utf-8")
    ev = db.add_evidence("cycle-1", [item], {"ok": True}, {"goal_revision": 1})
    item.write_text("new", encoding="utf-8")
    assert "snapshot" in ev["artifacts"][0]
    assert (tmp_path / ev["artifacts"][0]["snapshot"]).read_text(encoding="utf-8") == "original"
