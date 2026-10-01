"""Build a deterministic, source-only plugin archive and its integrity receipt."""
import argparse
import hashlib
import json
import sys
import tempfile
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
    paths += [ROOT / "docs/system-level-construction.md", ROOT / "docs/upgrade-review.md", ROOT / "docs/distribution.md"]
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


def write_content_bundle(contents, output, kind):
    """Write one deterministic directory; never mix catalogs with upload inputs."""
    manifest = read_json(ROOT / "plugin.json")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(contents.items()):
            entry = zipfile.ZipInfo("agent-worksystem-builder/" + name, (2026, 9, 30, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, content)
    receipt = {"name": manifest["name"], "version": manifest["version"], "archive": output.name,
               "bundle_kind": kind, "sha256": file_digest(output),
               "files": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(contents.items())}}
    write_json(output.with_suffix(".manifest.json"), receipt)
    return receipt


def package_codex_import(output=None):
    """A single Codex-format upload, without the CLI marketplace or dual manifests."""
    manifest = read_json(ROOT / "plugin.json")
    native = read_json(ROOT / ".codex-plugin/plugin.json")
    extension = manifest["extensions"]["com.openai"]
    native["interface"] = extension["interface"]
    native["extensions"] = {"com.openai": {k: v for k, v in extension.items() if k != "interface"}}
    with tempfile.TemporaryDirectory(prefix="awb-upload-source-") as temporary:
        source = Path(temporary) / "source.zip"
        package(source)
        with zipfile.ZipFile(source) as archive:
            contents = {n.removeprefix("agent-worksystem-builder/"): archive.read(n) for n in archive.namelist()
                        if n not in ("agent-worksystem-builder/plugin.json", "agent-worksystem-builder/.agents/plugins/marketplace.json")}
    contents[".codex-plugin/plugin.json"] = (json.dumps(native, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return write_content_bundle(contents, output or ROOT / "dist" / f"agent-worksystem-builder-{manifest['version']}-codex-import.zip", "codex-import")


def package_portable_skill(output=None):
    """One Agent Skill containing every module and the unchanged shared runtime."""
    validate_skill_suite()
    manifest = read_json(ROOT / "plugin.json")
    primary = ROOT / "skills/building-agent-worksystems"
    contents = {p.relative_to(primary).as_posix(): p.read_bytes() for p in primary.rglob("*")
                if distributable(p) and p.relative_to(primary).as_posix() not in ("SKILL.md", "agents/openai.yaml")}
    entry = ROOT / "portable/agent-worksystem-builder"
    contents.update({p.relative_to(entry).as_posix(): p.read_bytes() for p in entry.rglob("*") if distributable(p)})
    contract = contents["references/module-contract.md"].decode("utf-8")
    paragraph = contract.split("\n\n")[1]
    contract = contract.replace(paragraph, "The coordinator and five focused modules are distributed inside this single Skill. Read references/modules/awb-clarify.md, awb-explore.md, awb-design.md, awb-execute.md or awb-verify.md as needed. Shared resources and scripts are inside this Skill root; resolve paths from SKILL.md. No sibling Skill or separate registration is required.", 1)
    contract = contract.replace("AWB SQLite is authoritative for construction records;", "When the optional AWB runtime is actually in use, its SQLite is authoritative for construction records; otherwise preserve an attributable handoff without claiming transactional guarantees;")
    contents["references/module-contract.md"] = contract.encode("utf-8")
    loop = contents["references/construction-loop.md"].decode("utf-8")
    loop = loop.replace("Native Codex hosts the Builder.", "The current agent host runs the Builder.")
    loop = loop.replace("Persist goal, architecture/profile/exploration, cycle/change/evidence and decisions in the existing Store.", "When using the optional AWB runtime, persist goal, architecture/profile/exploration, cycle/change/evidence and decisions in its Store. Otherwise preserve these in an attributable host-supported handoff without claiming AWB transaction guarantees.")
    contents["references/construction-loop.md"] = loop.encode("utf-8")
    exploration = contents["references/exploration.md"].decode("utf-8")
    exploration = exploration.replace("Inventory project/global Skills and installed plugins with `profile --discover CODEX_HOME`; inspect host-exposed tools/MCP separately in native Codex.", "Inventory resources through the current host's supported interfaces. Only for an actually discovered Codex installation, use `profile --discover CODEX_HOME`; inspect host-exposed tools/MCP separately. Codex discovery is optional and does not substitute for another host's inventory.")
    contents["references/exploration.md"] = exploration.encode("utf-8")
    for name in SUITE_NAMES[1:]:
        text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        # Reference modules are plain documents, not separately registered Skills.
        text = text.split("---", 2)[2].lstrip()
        text = text.replace("../building-agent-worksystems/references/", "../")
        text = text.replace("native Codex engineering tools", "the current host's engineering tools")
        text = text.replace("Native Codex supplies semantic judgment", "The current host agent supplies semantic judgment")
        contents[f"references/modules/{name}.md"] = text.encode("utf-8")
    contents["scripts/install_awb.py"] = (ROOT / "tools/install_awb.py").read_bytes()
    return write_content_bundle(contents, output or ROOT / "dist" / f"agent-worksystem-builder-{manifest['version']}-skill.zip", "standalone-skill")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--developer", action="store_true", help="Separate development bundle with target examples and evaluation tools; not the installation deliverable")
    parser.add_argument("--format", choices=("marketplace", "codex-import", "skill", "suite", "all"), default="marketplace")
    args = parser.parse_args()
    methods = {"marketplace": lambda: package(developer=args.developer), "codex-import": package_codex_import,
               "skill": package_portable_skill, "suite": package_skill_suite}
    result = {name: method() for name, method in methods.items()} if args.format == "all" else methods[args.format]()
    print(json.dumps(result, ensure_ascii=False))
