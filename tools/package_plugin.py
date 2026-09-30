"""Build a deterministic, source-only plugin archive and its integrity receipt."""
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/building-agent-worksystems/scripts"))
from awb_core.contracts import file_digest, read_json, write_json


def package(output=None):
    manifest = read_json(ROOT / "plugin.json")
    paths = [ROOT / name for name in ("plugin.json", ".codex-plugin/plugin.json", "README.md", "PRIVACY.md", "TERMS.md", "pyproject.toml", "tools/demo.py")]
    paths += [p for folder in (ROOT / "skills", ROOT / "assets", ROOT / "examples") for p in folder.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith((".pyc", ".pyo"))]
    paths += [ROOT / "docs" / name for name in ("interfaces.md", "delivery-status.md", "plugin-submission.md")]
    output = Path(output) if output else ROOT / "dist" / f"agent-worksystem-builder-{manifest['version']}-plugin.zip"
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
    receipt = {"name": manifest["name"], "version": manifest["version"], "archive": output.name,
               "sha256": file_digest(output), "files": files, "excludes": ["user projects", "credentials", "development reports", "source planning documents", "bytecode"]}
    write_json(output.with_suffix(".manifest.json"), receipt)
    return receipt


if __name__ == "__main__":
    print(json.dumps(package(), ensure_ascii=False))
