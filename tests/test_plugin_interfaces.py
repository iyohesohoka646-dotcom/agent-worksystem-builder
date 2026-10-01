"""Exercise the packaged entrypoints, workspace boundary and review handoff."""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from test_state import goal

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/building-agent-worksystems/scripts"


def test_doctor_explains_missing_dependencies_without_creating_state(tmp_path):
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-S", str(SCRIPTS / "awb_doctor.py"), "--project", str(tmp_path), "--mcp"],
        capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    assert result.returncode == 2, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "requires_setup"
    assert set(report["missing"]) == {"jsonschema", "httpx", "mcp"}
    assert report["setup"][0][-2:] == ["venv", str(tmp_path / ".venv")]
    assert not list(tmp_path.iterdir())


def test_doctor_recognizes_installed_runtime_without_optional_mcp(tmp_path):
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(SCRIPTS / "awb_doctor.py"), "--project", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "ready"
    assert report["missing"] == []
    assert "mcp" not in report["dependencies"]
    assert not list(tmp_path.iterdir())


def interfaces():
    try:
        from awb_core.mcp_server import create_server
    except ImportError:
        pytest.fail("The project-bound MCP interface is not implemented")
    from mcp import Client
    return create_server, Client


def test_mcp_review_is_preserved_across_cli_answer_and_stdio_resume(tmp_path):
    create_server, Client = interfaces()
    from mcp.client.stdio import StdioServerParameters
    from awb_core.state import Store

    inputs = tmp_path / "材料"
    inputs.mkdir()
    (inputs / "a.txt").write_text("research experiment", encoding="utf-8")
    (inputs / "b.txt").write_text("uncertain item", encoding="utf-8")

    async def start():
        async with Client(create_server(tmp_path), mode="legacy") as client:
            binding = await client.call_tool("awb_project_info", {})
            assert binding.structured_content["project"] == str(tmp_path.resolve())
            assert binding.structured_content["initialized"] is False
            assert not (tmp_path / ".worksystem-build").exists()
            initialized = await client.call_tool("awb_initialize", {"goal": goal()})
            assert initialized.structured_content["status"] == "initialized"
            result = await client.call_tool("awb_run_materials", {"input_dir": "材料"})
            assert not result.is_error
            run = result.structured_content
            assert run["status"] == "needs_human"
            assert run["model_calls"] == 0
            reviews = await client.call_tool("awb_pending_reviews", {})
            assert len(reviews.structured_content["reviews"]) == 1
            tools = (await client.list_tools()).tools
            assert not any("approve" in t.name or "answer" in t.name for t in tools)
            resources = (await client.list_resources()).resources
            assert {str(r.uri) for r in resources} >= {"awb://project/goal", "awb://project/status"}
            status = await client.read_resource("awb://project/status")
            assert json.loads(status.contents[0].text)["runs"][0]["id"] == run["id"]
            return run["id"], reviews.structured_content["reviews"][0]["id"]

    run_id, review_id = asyncio.run(start())
    Store(tmp_path).approve(review_id, {"category": "other"}, "actual-user-fixture")

    async def resume_from_packaged_script():
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(SCRIPTS / "awb_mcp.py"), "--project", str(tmp_path)],
        )
        async with Client(parameters, mode="legacy") as client:
            resumed = await client.call_tool("awb_resume", {"run_id": run_id})
            assert not resumed.is_error
            assert resumed.structured_content["status"] == "completed"
            verified = await client.call_tool("awb_verify_materials", {
                "run_id": run_id, "reference": {"a.txt": "research", "b.txt": "other"},
            })
            assert verified.structured_content["passed"] is True
            assert verified.structured_content["semantic_reference_used"] is True
            pending = await client.call_tool("awb_pending_reviews", {})
            assert pending.structured_content == {"reviews": []}

    asyncio.run(resume_from_packaged_script())
    assert (inputs / "b.txt").read_text(encoding="utf-8") == "uncertain item"


def test_mcp_rejects_escape_and_unknown_run_with_protocol_errors(tmp_path):
    create_server, Client = interfaces()
    from awb_core.state import Store
    store = Store.initialize(tmp_path / "project", goal())
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.txt").write_text("research", encoding="utf-8")

    async def check():
        async with Client(create_server(store.project), mode="legacy") as client:
            for args in ({"input_dir": "../outside"}, {"input_dir": str(outside)}):
                result = await client.call_tool("awb_run_materials", args)
                assert result.is_error
                assert '"code": "path"' in result.content[0].text
            result = await client.call_tool("awb_resume", {"run_id": "missing"})
            assert result.is_error
            assert '"code": "missing"' in result.content[0].text
            assert Store(store.project).list("run") == []

    asyncio.run(check())


def test_mcp_rejects_project_root_as_input_before_creating_a_run(tmp_path):
    create_server, Client = interfaces()
    from awb_core.state import Store
    Store.initialize(tmp_path, goal())
    (tmp_path / "research.txt").write_text("research", encoding="utf-8")

    async def check():
        async with Client(create_server(tmp_path), mode="legacy") as client:
            result = await client.call_tool("awb_run_materials", {"input_dir": "."})
            assert result.is_error
            assert '"code": "input"' in result.content[0].text
            assert Store(tmp_path).list("run") == []

    asyncio.run(check())


def test_mcp_does_not_replay_backend_runs_or_exceed_startup_budget(tmp_path):
    create_server, Client = interfaces()
    from awb_core.state import Store
    store = Store.initialize(tmp_path, goal())
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "a.txt").write_text("research", encoding="utf-8")
    # A run prepared through the unrestricted CLI must not expand MCP authority.
    run = store.create("run", {"workflow": "materials", "backend": {"backend": "command"},
                               "status": "needs_human"})

    async def check():
        async with Client(create_server(tmp_path, max_seconds=5), mode="legacy") as client:
            for seconds in (0, -1, 6):
                result = await client.call_tool("awb_run_materials", {"input_dir": "input", "max_seconds": seconds})
                assert result.is_error
                assert '"code": "budget"' in result.content[0].text
            result = await client.call_tool("awb_resume", {"run_id": run["id"]})
            assert result.is_error
            assert '"code": "scope"' in result.content[0].text
            result = await client.call_tool("awb_next", {"uncertainties": [
                {"id": "destination", "impact": 10, "question": "Where should outputs go?"},
            ]})
            assert result.structured_content["action"] == "ask"
            assert result.structured_content["uncertainty_id"] == "destination"
            assert len(Store(tmp_path).list("run")) == 1

    asyncio.run(check())


def test_mcp_default_budget_uses_startup_ceiling_and_keeps_existing_goal(tmp_path):
    create_server, Client = interfaces()
    from awb_core.state import Store
    Store.initialize(tmp_path, goal())
    (tmp_path / "input").mkdir()
    (tmp_path / "input/a.txt").write_text("research", encoding="utf-8")

    async def check():
        async with Client(create_server(tmp_path, max_seconds=5), mode="legacy") as client:
            duplicate = await client.call_tool("awb_initialize", {"goal": goal() | {"text": "Overwrite"}})
            assert duplicate.is_error
            assert Store(tmp_path).goal()["text"] == "Classify materials without changing sources"
            result = await client.call_tool("awb_run_materials", {"input_dir": "input"})
            assert not result.is_error, result.content
            assert result.structured_content["status"] == "completed"
            assert 0 < result.structured_content["remaining_seconds"] <= 5

    asyncio.run(check())


def test_initialized_project_releases_database_handle(tmp_path):
    from awb_core.state import Store
    store = Store.initialize(tmp_path, goal())
    moved = store.path.with_suffix(".moved")
    store.path.rename(moved)
    moved.rename(store.path)
    assert Store(tmp_path).goal()["revision"] == 1


def test_plugin_archive_runs_without_shipping_development_metadata(tmp_path):
    import hashlib
    import zipfile
    sys.path.insert(0, str(SCRIPTS.parents[2]))
    from tools.package_plugin import package
    archive_path = tmp_path / "plugin.zip"
    receipt = package(archive_path)
    assert receipt["sha256"] == hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive_path) as archive:
        assert not any(".egg-info/" in name or "__pycache__/" in name for name in archive.namelist())
        archive.extractall(tmp_path / "extracted")
    doctor = tmp_path / "extracted/agent-worksystem-builder/skills/building-agent-worksystems/scripts/awb_doctor.py"
    result = subprocess.run([sys.executable, "-X", "utf8", str(doctor), "--project", str(tmp_path / "target")],
                            capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "ready"
    assert not (tmp_path / "target").exists()


def test_packaged_evaluator_checks_matrix_budget_before_running_host(tmp_path):
    import zipfile
    from tools.package_plugin import package
    archive_path = tmp_path / "plugin.zip"
    package(archive_path, developer=True)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(tmp_path / "extracted")
    root = tmp_path / "extracted/agent-worksystem-builder"
    host = tmp_path / "host.json"
    host.write_text(json.dumps({"argv": [sys.executable, "-c", "raise RuntimeError('must not run')"],
                                "allowed_executables": [sys.executable], "trusted": True, "timeout": 5}), encoding="utf-8")
    output = tmp_path / "trials"
    result = subprocess.run([sys.executable, "-X", "utf8", str(root / "tools/evaluate.py"),
                             "--host-config", str(host), "--output", str(output), "--max-attempts", "1"],
                            capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 2
    assert json.loads(result.stdout)["code"] == "eval"
    assert json.loads(result.stdout)["details"]["required"] == 30
    assert not output.exists()


def test_installable_plugin_does_not_ship_target_apps_or_evaluation_jobs(tmp_path):
    import zipfile
    from tools.package_plugin import package
    archive_path = tmp_path / "plugin.zip"
    package(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        files = {name.removeprefix("agent-worksystem-builder/") for name in archive.namelist()}
        assert not any(name.startswith(("examples/", "evals/", "tools/", "tests/")) for name in files)
        assert "skills/building-agent-worksystems/scripts/awb.py" in files
        assert "skills/building-agent-worksystems/scripts/awb_mcp.py" in files
        assert "skills/awb-explore/SKILL.md" in files
        assert "docs/quickstart.md" in files
        assert not any(name.endswith(".html") for name in files)


def test_installable_plugin_archive_is_reproducible(tmp_path):
    from tools.package_plugin import package
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    package(first)
    package(second)
    assert first.read_bytes() == second.read_bytes()
