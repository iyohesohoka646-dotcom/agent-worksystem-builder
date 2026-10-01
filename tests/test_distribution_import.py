"""Exercise upload-specific packaging and standalone Skill installation."""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
import pytest

from tools import package_plugin
from tools.install_awb import install

ROOT = Path(__file__).resolve().parents[1]


def test_codex_upload_has_one_manifest_and_no_marketplace(tmp_path):
    output = tmp_path / "upload.zip"
    method = getattr(package_plugin, "package_codex_import", None)
    assert callable(method), "A ZIP upload needs a separate single-plugin deliverable"
    method(output)
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert {name.split('/')[0] for name in names} == {"agent-worksystem-builder"}
        manifests = [n for n in names if n.endswith("plugin.json")]
        assert manifests == ["agent-worksystem-builder/.codex-plugin/plugin.json"]
        assert not any("marketplace.json" in n for n in names)
        manifest = json.loads(archive.read(manifests[0]))
        assert manifest["skills"] == "./skills/"
        assert "interface" in manifest
        assert "mcpServers" not in manifest
        assert len([n for n in names if n.endswith('/SKILL.md')]) == 6


def test_standalone_skill_resolves_every_reference_without_siblings(tmp_path):
    output = tmp_path / "skill.zip"
    method = getattr(package_plugin, "package_portable_skill", None)
    assert callable(method), "One-skill hosts need an actually self-contained bundle"
    method(output)
    with zipfile.ZipFile(output) as archive:
        archive.extractall(tmp_path / "extracted")
    skill = tmp_path / "extracted/agent-worksystem-builder"
    assert len(list(skill.rglob("SKILL.md"))) == 1
    assert not list(skill.rglob("plugin.json"))
    assert "sibling `building-agent-worksystems/`" not in (skill / "references/module-contract.md").read_text(encoding="utf-8")
    assert (skill / "requirements.txt").is_file()
    for document in skill.rglob("*.md"):
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            target = (document.parent / link.split("#", 1)[0]).resolve()
            assert target.is_relative_to(skill.resolve()) and target.is_file(), (document, link)
    cli = subprocess.run([sys.executable, str(skill / "scripts/awb.py"), "--help"],
                         capture_output=True, text=True, timeout=15)
    assert cli.returncode == 0, cli.stderr
    assert "architecture" in cli.stdout


def test_skill_installer_preserves_other_skills_and_refuses_overwrite(tmp_path):
    output = tmp_path / "skill.zip"
    method = getattr(package_plugin, "package_portable_skill", None)
    assert callable(method), "Standalone skill packaging is missing"
    method(output)
    destination = tmp_path / "skills"
    destination.mkdir()
    (destination / "unrelated.txt").write_text("keep")
    command = [sys.executable, str(ROOT / "tools/install_awb.py"), "--kind", "skill",
               "--archive", str(output), "--destination", str(destination)]
    installed = subprocess.run(command, capture_output=True, text=True, timeout=15)
    assert installed.returncode == 0, installed.stderr
    assert (destination / "agent-worksystem-builder/SKILL.md").is_file()
    sentinel = destination / "agent-worksystem-builder/my-note.txt"
    sentinel.write_text("keep")
    again = subprocess.run(command, capture_output=True, text=True, timeout=15)
    assert again.returncode != 0
    assert sentinel.read_text() == "keep"
    assert (destination / "unrelated.txt").read_text() == "keep"


@pytest.mark.parametrize("name", ["agent-worksystem-builder/../../escaped.txt", "agent-worksystem-builder/..", "agent-worksystem-builder/evil.txt:stream"])
def test_installer_rejects_path_escape_before_writing(tmp_path, name):
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(name, "no")
    destination = tmp_path / "skills"
    result = subprocess.run([sys.executable, str(ROOT / "tools/install_awb.py"), "--kind", "skill",
                             "--archive", str(archive_path), "--destination", str(destination)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert "unsafe archive path" in result.stderr.lower()
    assert not destination.exists()


def test_plugin_installer_rejects_existing_catalog_before_extraction(tmp_path):
    output = tmp_path / "upload.zip"
    package_plugin.package_codex_import(output)
    destination = tmp_path / "source"
    catalog = destination / ".agents/plugins/marketplace.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="existing marketplace"):
        install(output, destination, "plugin")
    assert catalog.read_text(encoding="utf-8") == "keep"
    assert not (destination / "agent-worksystem-builder").exists()
