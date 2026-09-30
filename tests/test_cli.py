import json
import subprocess
import sys
from pathlib import Path

from test_state import goal

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "building-agent-worksystems" / "scripts" / "awb.py"


def invoke(project, *args):
    result = subprocess.run([sys.executable, "-X", "utf8", str(CLI), *args, "--project", str(project), "--json"],
                            capture_output=True, text=True, encoding="utf-8", timeout=15)
    return result


def test_cli_fresh_process_review_resume_and_export(tmp_path):
    goal_file = tmp_path / "goal-input.json"
    goal_file.write_text(json.dumps(goal()), encoding="utf-8")
    result = invoke(tmp_path, "init", "--goal", str(goal_file))
    assert result.returncode == 0, result.stderr
    inputs = tmp_path / "材料"
    inputs.mkdir()
    (inputs / "question.txt").write_text("uncertain item", encoding="utf-8")
    result = invoke(tmp_path, "run", "--input", "材料")
    assert result.returncode == 3, result.stderr
    run = json.loads(result.stdout)
    review = json.loads(invoke(tmp_path, "review").stdout)[0]
    answer = tmp_path / "answer.json"
    answer.write_text('{"category":"other"}', encoding="utf-8")
    assert invoke(tmp_path, "review", "--id", review["id"], "--answer", str(answer), "--actor", "user").returncode == 0
    result = invoke(tmp_path, "resume", "--id", run["id"])
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "completed"
    assert invoke(tmp_path, "verify", "--id", run["id"]).returncode == 0
    result = invoke(tmp_path, "export", "--output", "bundle.zip")
    assert result.returncode == 0, result.stderr
    import zipfile
    with zipfile.ZipFile(tmp_path / "bundle.zip") as archive:
        assert ".worksystem-build/state.sqlite" in archive.namelist()
        assert "材料/question.txt" in archive.namelist()


def test_cli_reports_structured_error_for_unknown_run(tmp_path):
    goal_file = tmp_path / "goal-input.json"
    goal_file.write_text(json.dumps(goal()), encoding="utf-8")
    assert invoke(tmp_path, "init", "--goal", str(goal_file)).returncode == 0
    result = invoke(tmp_path, "resume", "--id", "missing")
    assert result.returncode == 1
    assert json.loads(result.stdout)["error"]["code"] == "missing"


def test_goal_revision_update_is_available_from_cli(tmp_path):
    path = tmp_path / "goal-input.json"
    path.write_text(json.dumps(goal()), encoding="utf-8")
    assert invoke(tmp_path, "init", "--goal", str(path)).returncode == 0
    path.write_text(json.dumps(goal() | {"revision": 2, "text": "updated"}), encoding="utf-8")
    result = invoke(tmp_path, "goal", "--file", str(path), "--expected-revision", "1")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["revision"] == 2
