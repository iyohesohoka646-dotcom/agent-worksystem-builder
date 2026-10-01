"""Check the built wheel in a fresh target directory, without changing dependencies."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheel = ROOT / "dist/agent_worksystem_builder-0.2.0a1-py3-none-any.whl"
    report = {"wheel": wheel.name, "version_expected": "0.2.0a1", "checks": {}}
    with tempfile.TemporaryDirectory(prefix="awb-wheel-upgrade-") as temporary:
        installed = subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-index",
            "--target", temporary, str(wheel)], capture_output=True, text=True, encoding="utf-8", timeout=90)
        report["checks"]["install"] = installed.returncode == 0
        report["install_output"] = installed.stdout + installed.stderr
        script = """import importlib,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import awb_core
from awb_core.contracts import read_json,validate_schema
root=Path(awb_core.__file__).resolve().parent
assert root.is_relative_to(Path(sys.argv[1]).resolve())
assert awb_core.__version__=='0.2.0a1'
for name in ('architecture','profile','exploration'):
 from jsonschema import Draft202012Validator
 Draft202012Validator.check_schema(read_json(root/'schemas'/ (name+'.json')))
for name in ('delivery','exploration','intelligence','adapters.app_server'):
 importlib.import_module('awb_core.'+name)
print(json.dumps({'version':awb_core.__version__,'from_fresh_target':True,'new_schemas':3,'new_modules':4}))
"""
        check = subprocess.run([sys.executable, "-I", "-c", script, temporary], capture_output=True,
            text=True, encoding="utf-8", timeout=15)
        report["checks"]["fresh_import_and_contracts"] = check.returncode == 0
        report["import_output"] = check.stdout + check.stderr
        cli = subprocess.run([sys.executable, "-I", "-c",
            "import sys;sys.path.insert(0,sys.argv.pop(1));from awb_core.cli import main;raise SystemExit(main())",
            temporary, "--help"], capture_output=True, text=True, encoding="utf-8", timeout=15)
        report["checks"]["installed_cli"] = cli.returncode == 0 and all(s in cli.stdout for s in ("architecture", "profile", "explore", "delivery"))
        report["cli_output"] = cli.stdout + cli.stderr
    report["passed"] = all(report["checks"].values())
    report["qualification"] = "distribution_only"
    output = ROOT / "reports/wheel-install-0.2.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("wheel", "checks", "passed", "qualification")}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
