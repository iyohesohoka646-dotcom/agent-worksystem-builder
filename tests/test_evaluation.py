import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evaluator_uses_artifacts_instead_of_self_reported_success(tmp_path):
    path = ROOT / "tools/evaluate.py"
    assert path.is_file(), "Behavioral evaluation runner is not implemented"
    spec = importlib.util.spec_from_file_location("awb_evaluate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scenario = {"id": "s", "prompt": "Return correct data", "files": {"input.txt": "keep"}, "unchanged": ["input.txt"],
                "expected": {"result.json": {"count": 2}}, "human_checks": []}
    config = {"argv": [sys.executable, "-c", "print('I passed every test')"], "allowed_executables": [sys.executable],
              "trusted": True, "timeout": 5, "host_version": "fixture", "model": None}
    result = module.run_attempt(scenario, "baseline", config, tmp_path / "trial")
    assert result["artifact_checks_passed"] is False
    assert result["execution_completed"] is True
