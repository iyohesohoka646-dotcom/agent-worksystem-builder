"""Check module distribution by extracting and using the actual archives."""
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "building-agent-worksystems", "awb-clarify", "awb-design",
    "awb-execute", "awb-verify",
}


def packager():
    spec = importlib.util.spec_from_file_location("skill_suite_packager", ROOT / "tools/package_plugin.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_suite_usable(skills, tmp_path):
    discovered = {p.parent.name for p in skills.glob("*/SKILL.md")}
    assert discovered == SKILLS, "Every modular entrypoint must ship with the coordinator"
    for folder in sorted(skills.iterdir()):
        if not folder.is_dir():
            continue
        assert (folder / "agents/openai.yaml").is_file()
        for document in folder.rglob("*.md"):
            for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if "://" in link or link.startswith("#"):
                    continue
                target = (document.parent / link.split("#", 1)[0]).resolve()
                assert target.is_relative_to(skills.resolve()), (document, link)
                assert target.is_file(), (document, link)
    # Modules use one shared runtime rather than maintaining executable copies.
    assert len(list(skills.rglob("awb.py"))) == 1
    doctor = skills / "building-agent-worksystems/scripts/awb_doctor.py"
    target = tmp_path / "uninitialized-target"
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(doctor), "--project", str(target)],
        capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert not target.exists()


def test_plugin_archive_keeps_every_module_and_shared_resources(tmp_path):
    archive_path = tmp_path / "plugin.zip"
    packager().package(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(tmp_path / "extracted")
    assert_suite_usable(tmp_path / "extracted/agent-worksystem-builder/skills", tmp_path)


def test_portable_suite_includes_modules_but_not_evaluation_or_plugin_metadata(tmp_path):
    module = packager()
    assert callable(getattr(module, "package_skill_suite", None)), "Portable suite packager is missing"
    archive_path = tmp_path / "skills.zip"
    receipt = module.package_skill_suite(archive_path)
    assert receipt["sha256"] == hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive_path) as archive:
        assert not any(n.startswith(("tools/", "evals/", ".codex-plugin/")) for n in archive.namelist())
        assert not any(".egg-info/" in n or "__pycache__/" in n for n in archive.namelist())
        archive.extractall(tmp_path / "extracted")
    assert_suite_usable(tmp_path / "extracted", tmp_path)


def test_portable_suite_packaging_is_reproducible(tmp_path):
    module = packager()
    assert callable(getattr(module, "package_skill_suite", None)), "Portable suite packager is missing"
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    module.package_skill_suite(first)
    module.package_skill_suite(second)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize("method", ["package", "package_skill_suite"])
@pytest.mark.parametrize("missing", sorted(SKILLS))
def test_packaging_refuses_incomplete_suite_before_creating_archive(tmp_path, monkeypatch, method, missing):
    module = packager()
    source = tmp_path / "partial"
    shutil.copytree(ROOT / "skills", source / "skills", ignore=shutil.ignore_patterns(missing, "__pycache__", "*.egg-info"))
    for name in ("plugin.json", ".codex-plugin/plugin.json", ".agents/plugins/marketplace.json", "README.md", "PRIVACY.md", "TERMS.md", "pyproject.toml", "tools/demo.py", "tools/evaluate.py", "evals/README.md", "evals/scenarios.json", "docs/interfaces.md", "docs/delivery-status.md", "docs/plugin-submission.md", "docs/plugin-architecture.md"):
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    monkeypatch.setattr(module, "ROOT", source)
    output = tmp_path / "output/suite.zip"
    with pytest.raises(ValueError, match="incomplete"):
        getattr(module, method)(output)
    assert not output.parent.exists()
