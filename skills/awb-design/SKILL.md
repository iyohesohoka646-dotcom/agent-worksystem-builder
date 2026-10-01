---
name: awb-design
description: Use when choosing a target system's software architecture or intelligence participation, model, Skill, plugin, MCP and tool configuration, including adapting an existing project.
metadata:
  version: 0.2.0a1
---

# AWB Architecture and Integration

Design the entire target software and its optional intelligence layer independently. Fit architecture to the user's requirements, existing interfaces and actual deployment environment.

Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md). Input is the goal/brief, constraints, acceptance examples, existing interfaces and observed host capabilities. Read [architecture-selection.md](../building-agent-worksystems/references/architecture-selection.md) for node/backend choices and [integrations-and-skills.md](../building-agent-worksystems/references/integrations-and-skills.md) only when considering reuse or external integration.

Inspect working programs and interfaces first. Preserve their inputs and implementation; define regression checks and additive intelligence participation. Describe components, interfaces, dependencies, entrypoints and requirement-linked acceptance in ArchitecturePlan; do not introduce a universal workflow language. Ordinary control flow, event-driven code, UI/service/database architecture and durable/distributed frameworks are all candidates when appropriate. Deterministic code alone is a valid result.

Describe target intelligence separately in IntelligenceProfile, including interactive app-server sessions and noninteractive `codex exec`, model/resources/context, authority and budgets. Preserve working provider configuration and applicable rules. Target business state belongs to the target application; AWB's construction journal remains authoritative only for construction. Link lifecycles by actual identifiers/artifacts, never force target business data into the Builder's SQLite or DAG.

Classify capability evidence as tested, documented, unknown or unsupported. A version check does not prove inference; an HTTP fixture does not prove model behavior. Offline goals exclude undeclared remote destinations. MCP provides typed operations, not OS isolation, and optional MCP absence does not prevent a CLI design. Reading documentation does not authorize downloads, host configuration or publication.

Return both contracts, alternatives, evidence, independent verification, launch/recovery/extension boundaries and capability gaps. Use `awb-explore` when evidence is insufficient; use `awb-clarify` for consequential choices. Planning-only requests stop here; an authorized construction package continues to `awb-execute` within existing authority.

Example: “Keep parser.py and add recoverable orchestration, offline.” Specify how the existing parser is invoked and verified; do not replace it or introduce a cloud service.
