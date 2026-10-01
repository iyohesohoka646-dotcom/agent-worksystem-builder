---
name: building-agent-worksystems
description: Use when a user wants to design, implement, improve or resume an intelligent system spanning ordinary software architecture and optional interactive or noninteractive intelligence. Ordinary one-off questions do not need this skill.
metadata:
  version: 0.2.0a2
---

# Building Agent Worksystems

Build the user's complete system through ongoing grill, adaptive exploration and evaluate → create → verify → decide cycles. Preserve the original goal and current scope, including UI, services, data, scheduling, interfaces, deployment and ordinary programs when required. Materials classification is one example.

Separate three layers: this Builder runs in the native Codex conversation; the target software chooses its own modern program architecture and business state; its optional intelligence layer chooses participation modes, models, agents, Skills, plugins, MCP, tools, context, permissions and budgets. A deterministic target may need no intelligence. AWB's journal, SQLite and optional DAG are construction tools, not mandatory target components. No always-on Builder service is implied.

Read the shared [handoff contract](references/module-contract.md). Establish the target project, current request and observed state. Existing AWB records remain authoritative; preserve decisions and answered questions. Planning or inspection alone does not initialize or execute a project.

## Select the next module

Load only the relevant module, using its Skill name in this plugin or its linked file when the host has no Skill-dispatch interface:

| Current need | Module |
|---|---|
| Unclear requirements, constraints or acceptance examples | [awb-clarify](../awb-clarify/SKILL.md) |
| Uncertain facts, resource discovery, research, prototypes or competing solutions | [awb-explore](../awb-explore/SKILL.md) |
| Architecture, existing scripts, backends, Skills or MCP integrations | [awb-design](../awb-design/SKILL.md) |
| Authorized goal update, owned-file change or bounded run | [awb-execute](../awb-execute/SKILL.md) |
| Independent checks, saved reviews, acceptance or safe recovery | [awb-verify](../awb-verify/SKILL.md) |

For a complete build, choose the next action from the current goal, unresolved questions, explored evidence, architecture/profile and remaining budget. Clarify and explore continue throughout construction; new evidence can reopen a decision. Reuse answers, discover discoverable facts, and ask the question with greatest influence on the next meaningful action. Proceed within agreed authority and budget; return consequential architecture, cost, privacy, installation or acceptance changes to the user. Read [construction-loop.md](references/construction-loop.md) for complete-build checkpoints.

After local candidate acceptance, compare all active requirements with actual evidence using `delivery`; keep building uncovered parts. Stop a complete build only at whole-goal delivery, an explicit user stop, or a concrete authority/budget/access gate with a saved checkpoint. A direct planning, inspection or narrow module request still ends at its requested output. These are composable instruction modules, not automatically spawned agents or background services.

Pass the observed handoff values, receive actual output/evidence and choose the next bounded action. Shared runtime and detailed references stay in this directory; modules do not copy execution or state logic. Runtime operations require the shared doctor and an explicit `--project`; MCP is optional.

Return the result supported by evidence and any concrete remaining input or gate. Execution completion, an accepted local cycle and actual user-goal acceptance remain distinct.
