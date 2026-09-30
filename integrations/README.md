# Skill host integration

The canonical portable Skill is `skills/building-agent-worksystems`. Codex distribution uses root `plugin.json`, the `.codex-plugin/plugin.json` compatibility manifest and the repository marketplace. Installation commands are in the root README. Claude Code can use the same portable Skill in a host-supported Skill directory; its actual loading and behavior have not been tested here.

Validate a host by opening a fresh session, explicitly requesting this Skill, using a new isolated project and observing actual state/artifacts across a pause and restart. Record host version, model, permissions, task and resulting evidence. A successful Codex CLI model call only validates that backend transport; it does not independently validate Skill discovery or the Claude Code host.

Upgrade by installing the new Skill package alongside the old copy, checking dependencies and running a sample against an exported copy of project state. Swap the package only after validation. User `.worksystem-build` directories remain outside installation locations. Schema version 1 is the initial format; incompatible future versions must supply an explicit migration with backup and tests. Uninstalling the Skill removes only its installation copy, preserving user projects and exports.

The Codex wrapper uses the same core and declares no MCP servers or hooks. Public distribution is a GitHub prerelease with a repository marketplace; the official-directory upload package is prepared separately. Native installation/discovery checks use an isolated, credential-free Codex home and leave the user's host settings unchanged. Unattended scheduling is outside this implementation.
