import importlib.util
import os
import sys
from pathlib import Path

import pytest

from awb_core.contracts import AWBError, file_digest, read_json

ROOT = Path(__file__).resolve().parents[1]


def evaluator():
    spec = importlib.util.spec_from_file_location("awb_evaluate", ROOT / "tools/evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_host():
    return {"argv": [sys.executable, "-c",
                     "import pathlib,sys; print(sys.stdin.read()); pathlib.Path('result.json').write_text('{\"count\":2}')"],
            "allowed_executables": [sys.executable], "trusted": True, "timeout": 5,
            "host_version": "local-fixture", "model": None}


def fixture_scenario():
    return {"id": "parser", "split": "development", "prompt": "Keep the source and write result.json.",
            "files": {"input.txt": "fixed input"}, "unchanged": ["input.txt"],
            "expected": {"result.json": {"count": 2}}, "human_checks": ["Inspect the implementation."]}


def skill(tmp_path, name, text):
    folder = tmp_path / name
    folder.mkdir()
    (folder / "SKILL.md").write_text(text, encoding="utf-8")
    (folder / "references").mkdir()
    (folder / "references/context.md").write_text("Frozen context", encoding="utf-8")
    return folder


@pytest.mark.parametrize("source", [ROOT / "skills"] + [ROOT / "skills" / name for name in (
    "building-agent-worksystems", "awb-clarify", "awb-design", "awb-execute", "awb-verify", "awb-explore",
)])
def test_evaluator_freezes_complete_suite_with_resolvable_module_links(tmp_path, source):
    module = evaluator()
    destination = tmp_path / "context/builder"
    snapshot = module.freeze_skill(source, destination)
    assert {name for name in snapshot["files"] if name.endswith("/SKILL.md")} == {
        "building-agent-worksystems/SKILL.md", "awb-clarify/SKILL.md", "awb-design/SKILL.md",
        "awb-execute/SKILL.md", "awb-verify/SKILL.md", "awb-explore/SKILL.md",
    }
    assert (destination / "awb-design/../building-agent-worksystems/references/architecture-selection.md").is_file()
    assert module.context_checks(tmp_path, {"builder": snapshot}) == {"preserved:context:builder": True}
    from awb_core.contracts import atomic_write
    atomic_write(destination / "awb-design/SKILL.md", b"Changed module")
    assert module.skill_files(destination) != snapshot["files"]
    assert module.context_checks(tmp_path, {"builder": snapshot}) == {"preserved:context:builder": False}


def test_suite_evaluation_host_can_read_coordinator_sibling_modules(tmp_path):
    module = evaluator()
    frozen = tmp_path / "suite"
    module.freeze_skill(ROOT / "skills", frozen)
    # This actual local process follows the supplied Skill path and reads its siblings.
    host_code = (
        "import pathlib,re,sys,json; text=sys.stdin.buffer.read().decode('utf-8'); "
        "entry=pathlib.Path(re.search(r'Skill at (.+?SKILL[.]md)',text).group(1)); "
        "names=sorted(p.parent.name for p in entry.parent.parent.glob('*/SKILL.md') if p.read_text(encoding='utf-8')); "
        "pathlib.Path('result.json').write_text(json.dumps({'modules':names,'entry':str(entry),'exists':entry.exists()}))"
    )
    host = fixture_host() | {"argv": [sys.executable, "-c", host_code]}
    scenario = fixture_scenario() | {"expected": {"result.json": {"modules": [
        "awb-clarify", "awb-design", "awb-execute", "awb-explore", "awb-verify", "building-agent-worksystems",
    ]}}}
    attempt = module.run_attempt(scenario, "builder", host, tmp_path / "attempt", skill_path=frozen)
    assert attempt["execution_completed"]
    assert attempt["artifact_checks_passed"], read_json(tmp_path / "attempt/workspace/result.json")
    assert attempt["binding"]["skill_sha256"]


def test_evaluator_refuses_a_modular_coordinator_without_its_modules(tmp_path):
    source = tmp_path / "partial/building-agent-worksystems"
    (source / "references").mkdir(parents=True)
    (source / "SKILL.md").write_bytes((ROOT / "skills/building-agent-worksystems/SKILL.md").read_bytes())
    (source / "references/module-contract.md").write_bytes(
        (ROOT / "skills/building-agent-worksystems/references/module-contract.md").read_bytes())
    destination = tmp_path / "frozen"
    with pytest.raises(AWBError, match="incomplete"):
        evaluator().freeze_skill(source, destination)
    assert not destination.exists()


@pytest.mark.parametrize("name", ["awb-clarify", "awb-design", "awb-execute", "awb-verify"])
def test_evaluator_refuses_an_orphaned_leaf_module(tmp_path, name):
    source = tmp_path / name
    source.mkdir()
    (source / "SKILL.md").write_bytes((ROOT / "skills" / name / "SKILL.md").read_bytes())
    destination = tmp_path / "frozen"
    with pytest.raises(AWBError, match="incomplete"):
        evaluator().freeze_skill(source, destination)
    assert not destination.exists()


def test_evaluator_coordinator_selection_does_not_snapshot_unrelated_skills(tmp_path):
    module = evaluator()
    source = tmp_path / "installed-skills"
    original = module.freeze_skill(ROOT / "skills", source)
    unrelated = source / "unrelated-skill"
    unrelated.mkdir()
    (unrelated / "SKILL.md").write_text("Unrelated private workflow", encoding="utf-8")
    snapshot = module.freeze_skill(source / "building-agent-worksystems", tmp_path / "frozen")
    assert snapshot == original
    assert not (tmp_path / "frozen/unrelated-skill").exists()


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


def test_attempt_records_measured_time_and_artifact_binding(tmp_path):
    report = evaluator().run_attempt(fixture_scenario(), "baseline", fixture_host(), tmp_path / "attempt")
    assert report["artifact_checks_passed"]
    assert report["elapsed_seconds"] > 0
    assert report["cost"] is None and report["tokens"] is None
    assert report["artifact_hashes"]["result.json"] == file_digest(tmp_path / "attempt/workspace/result.json")
    assert len(report["binding"]["scenario_sha256"]) == 64
    assert len(report["binding"]["host_sha256"]) == 64
    assert report["full_behavior_acceptance"] is False


def test_attempt_without_any_output_assertion_cannot_pass(tmp_path):
    scenario = fixture_scenario() | {"expected": {}, "unchanged": []}
    with pytest.raises(AWBError, match="output assertion"):
        evaluator().run_attempt(scenario, "baseline", fixture_host(), tmp_path / "attempt")
    assert not (tmp_path / "attempt").exists()


def test_error_attempt_keeps_unknown_metrics_and_failure_in_summary(tmp_path):
    module = evaluator()
    bad_host = fixture_host() | {"trusted": False}
    failed = module.run_attempt(fixture_scenario(), "baseline", bad_host, tmp_path / "failed")
    assert failed["status"] == "failed"
    assert failed["elapsed_seconds"] >= 0
    assert failed["cost"] is None and failed["tokens"] is None
    summary = module.summarize([failed])
    assert summary["conditions"]["baseline"]["attempts"] == 1
    assert summary["conditions"]["baseline"]["artifact_pass_rate"] == 0
    assert summary["qualification"] == "not_established"


def test_matrix_freezes_old_and_new_skills_with_paired_inputs(tmp_path):
    old = skill(tmp_path, "old", "Old instructions")
    new = skill(tmp_path, "new", "New instructions")
    (new / "__pycache__").mkdir()
    (new / "__pycache__/module.pyc").write_bytes(b"generated")
    corpus = {"schema_version": 1, "minimum_repeats": 5, "conditions": ["baseline", "generic", "builder"],
              "scenarios": [fixture_scenario()]}
    output = tmp_path / "matrix"
    report = evaluator().run_matrix(corpus, fixture_host(), output, repeats=5, max_attempts=20,
                                    builder_skill=new, baseline_skill=old, seed=17)
    assert report["complete"]
    assert len(report["attempts"]) == 20
    for condition in ("baseline", "generic", "previous", "builder"):
        trials = [a for a in report["attempts"] if a["condition"] == condition]
        assert {a["repetition"] for a in trials} == set(range(5))
        assert len({a["binding"]["scenario_sha256"] for a in trials}) == 1
    assert report["comparisons"]["builder"]["reference_condition"] == "previous"
    assert report["comparisons"]["builder"]["matched_pairs"] == 5
    assert report["comparisons"]["builder"]["artifact_pass_rate_delta"] == 0
    frozen = output / "context/builder"
    assert (frozen / "SKILL.md").read_text(encoding="utf-8") == "New instructions"
    assert not (frozen / "__pycache__").exists()
    (new / "SKILL.md").write_text("Later edit", encoding="utf-8")
    assert (frozen / "SKILL.md").read_text(encoding="utf-8") == "New instructions"
    manifest = read_json(output / "manifest.json")
    assert manifest["skills"]["builder"]["files"]["SKILL.md"] == file_digest(frozen / "SKILL.md")
    assert manifest["planned_attempts"] == 20
    assert report["human_validation"] == "pending"


def test_matrix_budget_is_checked_before_creating_output(tmp_path):
    corpus = {"minimum_repeats": 5, "conditions": ["baseline", "generic", "builder"],
              "scenarios": [fixture_scenario()]}
    with pytest.raises(AWBError, match="budget"):
        evaluator().run_matrix(corpus, fixture_host(), tmp_path / "matrix", repeats=5, max_attempts=14)
    assert not (tmp_path / "matrix").exists()


def test_comparison_refuses_changed_input_or_host(tmp_path):
    module = evaluator()
    first = module.run_attempt(fixture_scenario(), "baseline", fixture_host(), tmp_path / "first")
    changed = fixture_scenario() | {"files": {"input.txt": "different input"}}
    second = module.run_attempt(changed, "generic", fixture_host(), tmp_path / "second")
    summary = module.summarize([first, second])
    comparison = summary["comparisons"]["generic"]
    assert comparison["matched_pairs"] == 0
    assert comparison["artifact_pass_rate_delta"] is None
    assert comparison["incomparable_pairs"] == ["parser:0"]


def test_changed_skill_during_attempt_invalidates_result(tmp_path):
    snapshot = skill(tmp_path, "snapshot", "Frozen instructions")
    host = fixture_host()
    host["argv"][-1] += f"; pathlib.Path({str(snapshot / 'SKILL.md')!r}).write_text('tampered')"
    report = evaluator().run_attempt(fixture_scenario(), "builder", host, tmp_path / "attempt", skill_path=snapshot)
    assert report["execution_completed"]
    assert report["artifact_checks"]["preserved:skill"] is False
    assert report["artifact_checks_passed"] is False


def test_matrix_stops_before_reusing_changed_frozen_skill(tmp_path, monkeypatch):
    module = evaluator()
    source = skill(tmp_path, "source", "Frozen instructions")
    output = tmp_path / "matrix"
    original = module.run_attempt
    calls = []

    def changed_after_attempt(*args, **kwargs):
        report = original(*args, **kwargs)
        calls.append(report)
        (output / "context/builder/SKILL.md").write_text("Changed between attempts", encoding="utf-8")
        return report

    monkeypatch.setattr(module, "run_attempt", changed_after_attempt)
    corpus = {"conditions": ["builder"], "scenarios": [fixture_scenario()]}
    with pytest.raises(AWBError, match="Frozen Skill"):
        module.run_matrix(corpus, fixture_host(), output, max_attempts=5, builder_skill=source)
    assert len(calls) == 1
    summary = read_json(output / "summary.json")
    assert summary["complete"] is False and len(summary["attempts"]) == 1


def test_preserved_input_junction_is_a_recorded_artifact_failure(tmp_path):
    module = evaluator()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "data.txt").write_text("outside data", encoding="utf-8")
    scenario = fixture_scenario() | {"files": {"input/data.txt": "fixed input"}, "unchanged": ["input/data.txt"]}
    code = "import pathlib,sys,subprocess,os; print(sys.stdin.read()); pathlib.Path('result.json').write_text('{\"count\":2}'); pathlib.Path('input').rename('saved-input'); "
    if os.name == "nt":
        code += f"subprocess.run(['cmd.exe','/c','mklink','/J',str(pathlib.Path('input').resolve()),{str(outside)!r}],check=True,capture_output=True)"
    else:
        code += f"os.symlink({str(outside)!r},'input',target_is_directory=True)"
    host = fixture_host()
    host["argv"][-1] = code
    report = module.run_attempt(scenario, "baseline", host, tmp_path / "attempt")
    assert report["execution_completed"] and report["elapsed_seconds"] > 0
    assert report["artifact_checks"]["preserved:input/data.txt"] is False
    assert report["artifact_checks_passed"] is False
    assert read_json(tmp_path / "attempt/attempt.json")["status"] == "completed"
    assert module.summarize([report])["conditions"]["baseline"]["artifact_pass_rate"] == 0


def test_final_baseline_job_cannot_silently_modify_builder_snapshot(tmp_path):
    module = evaluator()
    source = skill(tmp_path, "source", "Frozen instructions")
    output = tmp_path / "matrix"
    host = fixture_host()
    host["argv"][-1] += f"; pathlib.Path({str(output / 'context/builder/SKILL.md')!r}).write_text('tampered') if pathlib.Path.cwd().parent.name == 'parser-baseline-2' else None"
    corpus = {"conditions": ["baseline", "builder"], "scenarios": [fixture_scenario()]}
    with pytest.raises(AWBError, match="Frozen Skill"):
        module.run_matrix(corpus, host, output, max_attempts=10, builder_skill=source, seed=1)
    summary = read_json(output / "summary.json")
    assert summary["complete"] is False and len(summary["attempts"]) == 10
    final = summary["attempts"][-1]
    assert final["condition"] == "baseline" and final["repetition"] == 2
    assert final["artifact_checks"]["preserved:context:builder"] is False
    assert final["artifact_checks_passed"] is False
