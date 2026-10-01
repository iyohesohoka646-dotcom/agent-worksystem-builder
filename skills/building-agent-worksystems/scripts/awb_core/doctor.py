"""Dependency checks that work even before the runtime can be imported."""
import argparse
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path

from . import __version__


def inspect_environment(project, with_mcp=False):
    project = Path(project).resolve()
    packages = {"jsonschema": "4.26.0", "httpx": "0.28.1"}
    if with_mcp:
        packages["mcp"] = "2.2.0"
    dependencies, missing = {}, []
    for name, expected in packages.items():
        try:
            version = importlib.metadata.version(name)
            importlib.import_module(name)
            ready = version == expected
            dependencies[name] = {"installed": version, "required": expected, "ready": ready}
        except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
            ready = False
            dependencies[name] = {"installed": None, "required": expected, "ready": False, "error": str(exc)}
        if not ready:
            missing.append(name)
    python_ready = sys.version_info >= (3, 11)
    interpreter = project / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    requirements = Path(__file__).resolve().parents[2] / ("requirements-mcp.txt" if with_mcp else "requirements.txt")
    install_args = ["-r", str(requirements)] if requirements.is_file() else [f"{name}=={version}" for name, version in packages.items()]
    return {"status": "ready" if python_ready and not missing else "requires_setup", "version": __version__,
            "project": str(project), "initialized": (project / ".worksystem-build/state.sqlite").is_file(),
            "python": {"executable": sys.executable, "version": sys.version.split()[0], "ready": python_ready},
            "dependencies": dependencies, "missing": missing,
            "setup": [[sys.executable, "-m", "venv", str(project / ".venv")],
                      [str(interpreter), "-m", "pip", "install", "--no-user", *install_args]],
            "note": "Checks only; no installation, network request or project initialization is performed."}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the packaged runtime without changing the environment")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--mcp", action="store_true", help="Also check the optional MCP SDK")
    args = parser.parse_args(argv)
    report = inspect_environment(args.project, args.mcp)
    print(json.dumps(report, ensure_ascii=True))
    return 0 if report["status"] == "ready" else 2
