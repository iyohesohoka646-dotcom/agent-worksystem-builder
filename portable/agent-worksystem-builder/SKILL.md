---
name: agent-worksystem-builder
description: Use when designing, implementing, improving or resuming a complete intelligent system across software architecture and optional intelligence, in any agent host with suitable project tools.
metadata:
  version: 0.2.0a2
---

# Agent Worksystem Builder / 智能系统构筑器

Build the user's complete system through continuous requirements grill, adaptive exploration and evaluate → create → verify → decide cycles. Preserve ordinary programs, UI, services, data, scheduling and deployment in the original goal; agents are only one possible intelligence component. Keep target software architecture, optional intelligence orchestration and construction records separate. Deterministic software is a valid result.

## Bind to the current host

This is one self-contained Skill. All modules, references and optional Python tools are inside this directory. Resolve paths relative to this `SKILL.md`, never the target cwd or a sibling Skill. No plugin installation, Skill registry, Codex CLI or MCP is required to use the instructions. Read a linked module as a document when the host cannot dispatch Skills.

Use the current host's actual read/edit/search/shell tools, model and approvals. Inspect available capabilities first; do not invent tool names or install Codex to make this Skill work. Codex app-server/exec, Ollama and Claude references describe optional target adapters, not a requirement on the Builder host. Only use an adapter when the target needs it and its actual access is verified. `profile --discover CODEX_HOME` applies only to a discovered Codex installation; otherwise inventory the current host through its own supported interface.

Planning works without Python or filesystem writes. Implementation requires real file-edit and execution access; a text-only agent can deliver a design and handoff, but cannot claim it built or verified the system. Python 3.11+ and bundled dependencies are needed only for optional construction-journal/CLI operations. Follow [host capabilities and runtime](references/portable-host.md) before using them.

## Compose the next action

Read the [handoff contract](references/module-contract.md), preserving original goal, existing answers, decisions, authority and budget. Load only the module needed next:

- [Clarify / 澄清](references/modules/awb-clarify.md): consequential requirements and acceptance decisions.
- [Explore / 探索](references/modules/awb-explore.md): environment facts, research, architecture alternatives and prototypes.
- [Design / 设计](references/modules/awb-design.md): whole-system architecture and optional intelligence configuration.
- [Execute / 执行](references/modules/awb-execute.md): authorized implementation through current host tools.
- [Verify / 核验](references/modules/awb-verify.md): independent actual checks, recovery and whole-goal coverage.

For a full build, keep cycling as evidence changes. Reuse answers, investigate discoverable facts, then ask the highest-impact unresolved question. Proceed with ordinary reversible work inside the agreed scope; return consequential cost, credentials, data-destination or product changes for a real decision. A local accepted candidate does not complete uncovered requirements. Read [construction checkpoints](references/construction-loop.md); host binding above applies wherever shared references mention native Codex.

Deliver independent target entrypoints, configuration/dependencies, architecture explanation, requirement-linked real acceptance evidence, recovery and extension interfaces. Preserve failed attempts, unknown effects and limits. Stop at requested narrow output, whole-goal delivery, an explicit stop or a concrete authority/budget/access checkpoint. A checkpoint never implies success.
