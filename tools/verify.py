"""Reproducible delivery checks; live invocation is an explicit separate flag."""
import argparse
import importlib.metadata as metadata
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "building-agent-worksystems" / "scripts"))
from awb_core import __version__
from awb_core.contracts import file_digest, read_json, write_json
from awb_core.execution import probe_backend
from package_plugin import SUITE_NAMES, package_skill_suite


def command(args, log, timeout=180):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    return {"argv": args, "returncode": result.returncode, "log": str(log.relative_to(ROOT))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-codex", action="store_true", help="One inference probe, max 120 seconds, configured example model")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    reports, dist = ROOT / "reports", ROOT / "dist"
    reports.mkdir(exist_ok=True)
    dist.mkdir(exist_ok=True)
    result = {"version": __version__, "platform": platform.platform(), "python": sys.version, "checks": {}, "live": {}}
    source = ROOT / "docs/specs/creation-plan.v0.1.md"
    original = ROOT.parent / "agent-worksystem-builder-creation-plan.md"
    receipt = {"source": str(original), "snapshot": str(source.relative_to(ROOT)), "sha256": file_digest(source), "matches_original": original.is_file() and file_digest(source) == file_digest(original)}
    write_json(ROOT / "docs/specs/source.json", receipt)
    result["checks"]["source_snapshot"] = receipt["matches_original"]
    result["packages"] = {name: metadata.version(name) for name in ["pytest", "jsonschema", "httpx", "setuptools", "wheel", "mcp"]}
    if not args.skip_tests:
        test = command([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=short", "--junitxml", str(reports / "runtime-tests.xml")], reports / "runtime-tests.log")
        result["checks"]["runtime_tests"] = test
    codex = read_json(ROOT / "examples/codex-backend.json")
    result["live"]["codex"] = probe_backend(codex, reports / "codex-live", args.live_codex)
    result["live"]["ollama"] = probe_backend({"backend": "ollama"})
    result["live"]["claude_code"] = {"executable": shutil.which("claude"), "host_test": "not_run"}
    built = command([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "--wheel-dir", str(dist)], reports / "wheel-build.log")
    result["checks"]["wheel"] = built
    suite = package_skill_suite()
    bundle = dist / suite["archive"]
    result["checks"]["portable_skill_suite"] = {"passed": set(suite["skills"]) == set(SUITE_NAMES),
                                                "skills": suite["skills"], "sha256": suite["sha256"]}
    with tempfile.TemporaryDirectory(prefix="awb-package-") as temporary:
        with zipfile.ZipFile(bundle) as archive:
            archive.extractall(temporary)
        smoke = command([sys.executable, str(Path(temporary) / "building-agent-worksystems/scripts/awb.py"), "--help"], reports / "portable-package.log")
    result["checks"]["portable_package"] = smoke
    result["artifacts"] = {p.name: file_digest(p) for p in dist.iterdir() if p.is_file()}
    result["release_qualified"] = False
    result["pending_gates"] = ["matched behavioral comparisons", "real user acceptance", "Claude Code Skill host", "Ollama real local inference", "current-version Linux CI"]
    if result["live"]["codex"].get("live_result", {}).get("status") != "completed":
        result["pending_gates"].append("Codex real inference")
    write_json(reports / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False))
    failed = any(v is False or (isinstance(v, dict) and (v.get("returncode", 0) != 0 or v.get("passed") is False)) for v in result["checks"].values())
    if args.live_codex and result["live"]["codex"].get("live_result", {}).get("status") != "completed":
        failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
