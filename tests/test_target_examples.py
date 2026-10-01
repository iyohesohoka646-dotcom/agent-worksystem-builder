import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pure_program_runs_without_builder_state_model_or_service(tmp_path):
    inputs = tmp_path / "input.csv"
    inputs.write_text("name,value\na,3\nb,4\na,2\n", encoding="utf-8")
    output = tmp_path / "result.json"
    process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "examples/pure-program/summarize.py"), str(inputs), str(output)],
                             capture_output=True, text=True, encoding="utf-8", timeout=5)
    assert process.returncode == 0, process.stderr
    assert json.loads(output.read_text(encoding="utf-8")) == {"a": 5, "b": 4}
    assert not (tmp_path / ".worksystem-build").exists()


def test_existing_parser_api_and_bytes_survive_optional_intelligence_enhancement(tmp_path):
    from awb_core.contracts import file_digest
    parser = ROOT / "examples/existing-project/parser.py"
    before = file_digest(parser)
    inputs = tmp_path / "input.txt"
    inputs.write_text("a\n\nb\n", encoding="utf-8")
    output = tmp_path / "result.json"
    process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "examples/existing-project/enhance.py"),
        "--input", str(inputs), "--output", str(output), "--no-intelligence"], capture_output=True, text=True, encoding="utf-8", timeout=5)
    assert process.returncode == 0, process.stderr
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["parsed"] == {"count": 2, "items": ["a", "b"]}
    assert result["intelligence"] is None
    assert file_digest(parser) == before
