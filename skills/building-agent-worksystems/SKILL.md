---
name: building-agent-worksystems
description: Use when a user wants to build, improve or resume a sustained agent-assisted work system, recurring materials pipeline or recoverable workflow. Ordinary one-off questions do not need this skill.
metadata:
  version: 0.1.0a4
---

# Building Agent Worksystems

Coordinate a working system the user can inspect, recover and change. Preserve purpose and explicit limits; select the smallest useful route.

Read the shared [handoff contract](references/module-contract.md). Establish the target project, current request and observed state. Existing AWB records remain authoritative; preserve decisions and answered questions. Planning or inspection alone does not initialize or execute a project.

## Select one module

Load only the relevant module, using its Skill name in this plugin or its linked file when the host has no Skill-dispatch interface:

| Current need | Module |
|---|---|
| Unclear requirements, constraints or acceptance examples | [awb-clarify](../awb-clarify/SKILL.md) |
| Architecture, existing scripts, backends, Skills or MCP integrations | [awb-design](../awb-design/SKILL.md) |
| Authorized goal update, owned-file change or bounded run | [awb-execute](../awb-execute/SKILL.md) |
| Independent checks, saved reviews, acceptance or safe recovery | [awb-verify](../awb-verify/SKILL.md) |

For a complete new build, compose clarify → design → execute → verify, skipping already satisfied stages. For an existing checkpoint or verification-only request, start at verify. A narrow request ends with that module's output; do not force the remaining pipeline. These are instruction modules, not automatically spawned agents or background services.

Pass the observed handoff values, receive actual output/evidence and choose the next bounded action. Shared runtime and detailed references stay in this directory; modules do not copy execution or state logic. Runtime operations require the shared doctor and an explicit `--project`; MCP is optional.

Return the result supported by evidence and any concrete remaining input or gate. Execution completion, an accepted local cycle and actual user-goal acceptance remain distinct.
