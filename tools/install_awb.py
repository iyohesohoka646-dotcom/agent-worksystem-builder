"""Install an AWB upload/Skill ZIP without third-party Python dependencies."""
import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


def install(archive_path, destination, kind, codex_home=None, codex=None):
    destination = Path(destination).resolve()
    catalog = destination / ".agents/plugins/marketplace.json"
    if kind == "plugin" and catalog.exists():
        raise FileExistsError("refusing to replace an existing marketplace: " + str(catalog))
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        normalized = set()
        for entry in archive.infolist():
            parts = entry.filename.split("/")
            mode = entry.external_attr >> 16
            if (entry.filename.startswith(("/", "\\")) or "\\" in entry.filename or any(":" in p for p in parts)
                    or any(p in ("..", ".") for p in parts) or any(not p for p in parts[:-1])
                    or not PurePosixPath(entry.filename).is_relative_to("agent-worksystem-builder")
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError("unsafe archive path: " + entry.filename)
            key = entry.filename.rstrip("/").casefold()
            if key in normalized:
                raise ValueError("duplicate archive path: " + entry.filename)
            normalized.add(key)
        required = "SKILL.md" if kind == "skill" else ".codex-plugin/plugin.json"
        if "agent-worksystem-builder/" + required not in names:
            raise ValueError("archive does not contain the requested " + kind + " entrypoint")
        target = destination / "agent-worksystem-builder"
        if target.exists():
            raise FileExistsError("installation already exists; choose a fresh destination: " + str(target))
        bad_member = archive.testzip()
        if bad_member:
            raise zipfile.BadZipFile("invalid archive checksum: " + bad_member)
        destination.mkdir(parents=True, exist_ok=True)
        archive.extractall(destination)
    result = {"kind": kind, "installed_path": str(target), "native_installation": False}
    if kind == "plugin":
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text(json.dumps({"name": "agent-worksystem-builder-plugins", "plugins": [{
            "name": "agent-worksystem-builder", "source": {"source": "local", "path": "./agent-worksystem-builder"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"}}]}, indent=2) + "\n", encoding="utf-8")
        binary = codex or shutil.which("codex.exe") or shutil.which("codex")
        if not binary:
            raise RuntimeError("Codex executable not found; source prepared at " + str(destination))
        launcher = Path(binary)
        if launcher.suffix.lower() in (".cmd", ".bat", ".ps1"):
            natives = list((launcher.parent / "node_modules/@openai/codex").glob("node_modules/@openai/codex-*/vendor/*/bin/codex.exe"))
            if not natives:
                raise RuntimeError("Native Codex executable not found; pass --codex PATH_TO_CODEX_EXE")
            binary = str(natives[0])
        env = dict(os.environ)
        if codex_home:
            env["CODEX_HOME"] = str(Path(codex_home).resolve())
        for args in (["plugin", "marketplace", "add", str(destination), "--json"],
                     ["plugin", "add", "agent-worksystem-builder@agent-worksystem-builder-plugins", "--json"]):
            completed = subprocess.run([binary, *args], env=env, capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=60)
            if completed.returncode:
                raise RuntimeError(completed.stderr or completed.stdout)
        result["native_installation"] = True
    return result


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True, help="Skill directory or fresh plugin source parent")
    parser.add_argument("--kind", choices=("plugin", "skill"), required=True)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--codex", help="Explicit native Codex executable")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.archive, args.destination, args.kind, args.codex_home, args.codex), ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
