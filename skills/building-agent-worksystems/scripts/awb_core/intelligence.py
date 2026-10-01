"""Target intelligence configuration; no provider credential copying or installation."""
import os
from pathlib import Path

from .adapters.codex import executable, toml_literal
from .contracts import AWBError, validate_record, read_json


def compile_profile(profile):
    p = validate_record("profile", profile)
    if p["mode"] == "none":
        return {"mode": "none", "resources": []}
    if not p["model"]:
        raise AWBError("configuration", "An intelligence profile requires an explicit model")
    permissions = p["permissions"]
    if permissions["sandbox"] == "workspace-write" and not permissions.get("workspace_write_authorized"):
        raise AWBError("policy", "Workspace writes must be authorized")
    overrides = {}
    for resource in p["resources"]:
        if resource["compatibility"] != "verified":
            raise AWBError("compatibility", f"Resource {resource['id']} needs an actual compatibility check")
        overrides.update(resource.get("configuration", {}))
    result = {"backend": "codex", "model": p["model"], "mode": p["mode"],
              "sandbox": permissions["sandbox"], "approval_policy": permissions["approval_policy"],
              "workspace_write_authorized": permissions.get("workspace_write_authorized", False),
              "inherit_user_config": p["context"]["inherit_user_config"], "inherit_rules": p["context"]["inherit_rules"],
              "reasoning_effort": p.get("reasoning_effort"), "config_overrides": overrides,
              "timeout": p["budget"]["max_seconds"], "retries": 0}
    if p.get("codex_home"):
        result["codex_home"] = str(Path(p["codex_home"]).resolve())
    if p.get("executable"):
        result["executable"] = p["executable"]
    return result


def app_server_command(config):
    args = [executable(config), "app-server", "--stdio"]
    if config.get("inherit_user_config", True) is False:
        args.append("--ignore-user-config")
    if config.get("inherit_rules", True) is False:
        args.append("--ignore-rules")
    for key, value in config.get("config_overrides", {}).items():
        args += ["-c", key + "=" + toml_literal(value)]
    return args


def host_environment(config):
    env = dict(os.environ)
    if config.get("codex_home"):
        env["CODEX_HOME"] = str(Path(config["codex_home"]).resolve())
    return env


def discover_resources(project, codex_home, extra_skill_roots=()):
    """Metadata inventory only. Presence is not compatibility or a license grant."""
    project, home = Path(project).resolve(), Path(codex_home).resolve()
    result = []
    roots = [project / ".agents/skills", home / "skills", *map(Path, extra_skill_roots)]
    for root in roots:
        for entry in sorted(root.glob("*/SKILL.md")):
            result.append({"id": entry.parent.name, "kind": "skill", "source": str(entry.parent.resolve()),
                           "version": None, "license": None, "compatibility": "unknown", "operation": "use"})
    for entry in sorted((home / "plugins/cache").glob("*/*/*/plugin.json")):
        try:
            manifest = read_json(entry)
            result.append({"id": manifest.get("name", entry.parent.parent.name), "kind": "plugin",
                           "source": str(entry.parent), "version": manifest.get("version"), "license": None,
                           "compatibility": "unknown", "operation": "use"})
        except AWBError:
            continue
    return {"schema_version": 1, "resources": result, "automatic_installation": False,
            "limitation": "Inspect active host tools/MCP configuration and externally discovered candidates in the native conversation; no credentials are read here."}
