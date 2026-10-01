"""Build a deterministic, source-only plugin archive and its integrity receipt."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
from awb_core.contracts import file_digest, read_json, write_json

SUITE_NAMES = ("building-agent-worksystems", "awb-clarify", "awb-explore", "awb-design", "awb-execute", "awb-verify")


def validate_skill_suite():
    skills = ROOT / "skills"
    required = [f"{name}/{entry}" for name in SUITE_NAMES for entry in ("SKILL.md", "agents/openai.yaml")]
    required += ["building-agent-worksystems/" + entry for entry in (
        "references/module-contract.md", "scripts/awb.py", "scripts/awb_doctor.py",
    )]
    missing = [name for name in required if not (skills / name).is_file()]
    if missing:
        raise ValueError("Modular Skill suite is incomplete: " + ", ".join(missing))


def package(output=None, *, developer=False):
    validate_skill_suite()
    manifest = read_json(ROOT / "plugin.json")
    paths = [ROOT / name for name in ("plugin.json", ".codex-plugin/plugin.json", ".agents/plugins/marketplace.json", "README.md", "README.zh-CN.md", "PRIVACY.md", "TERMS.md", "pyproject.toml")]
    folders = [ROOT / "skills", ROOT / "assets"]
    if developer:
        paths += [ROOT / name for name in ("tools/demo.py", "tools/evaluate.py", "tools/host_preflight.py", "tools/evaluate_systems.py", "tools/qualify_systems.py", "tools/workbench_fault_probe.py", "evals/README.md", "evals/scenarios.json", "evals/systems.json", "evals/system_checks.py", "evals/system_gateway.py")]
        folders.append(ROOT / "examples")
    paths += [p for folder in folders for p in folder.rglob("*")
              if distributable(p)]
    paths += [ROOT / "docs" / name for name in ("interfaces.md", "delivery-status.md", "plugin-submission.md", "plugin-architecture.md", "quickstart.md", "share.md", "release-alpha4.md", "upgrade-0.2.md", "intelligent-system-upgrade-plan.md")]
    paths += [ROOT / "docs/system-level-construction.md", ROOT / "docs/upgrade-review.md"]
    kind = "development" if developer else "plugin"
    output = Path(output) if output else ROOT / "dist" / f"agent-worksystem-builder-{manifest['version']}-{kind}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    files = {}
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            relative = path.relative_to(ROOT).as_posix()
            entry = zipfile.ZipInfo("agent-worksystem-builder/" + relative, (2026, 9, 30, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
            files[relative] = file_digest(path)
    receipt = {"name": manifest["name"], "version": manifest["version"], "archive": output.name, "bundle_kind": kind,
               "sha256": file_digest(output), "files": files, "excludes": ["user projects", "credentials", "development reports", "source planning documents", "bytecode"] + ([] if developer else ["target application examples", "evaluation drivers and corpus"])}
    write_json(output.with_suffix(".manifest.json"), receipt)
    return receipt


def distributable(path):
    return path.is_file() and not any(part == "__pycache__" or part.endswith(".egg-info") for part in path.parts) and not path.name.endswith((".pyc", ".pyo"))


def package_skill_suite(output=None):
    """Keep sibling module paths intact, with one shared runtime, outside a plugin."""
    validate_skill_suite()
    manifest = read_json(ROOT / "plugin.json")
    output = Path(output) if output else ROOT / "dist" / f"agent-worksystem-skills-{manifest['version']}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    skills = ROOT / "skills"
    files = {}
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(skills.rglob("*")):
            if not distributable(path):
                continue
            relative = path.relative_to(skills).as_posix()
            entry = zipfile.ZipInfo(relative, (2026, 9, 30, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
            files[relative] = file_digest(path)
    receipt = {"name": manifest["name"], "version": manifest["version"], "archive": output.name,
               "sha256": file_digest(output), "files": files,
               "skills": sorted(p.parent.name for p in skills.glob("*/SKILL.md"))}
    write_json(output.with_suffix(".manifest.json"), receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--developer", action="store_true", help="Separate development bundle with target examples and evaluation tools; not the installation deliverable")
    args = parser.parse_args()
    print(json.dumps(package(developer=args.developer), ensure_ascii=False))
