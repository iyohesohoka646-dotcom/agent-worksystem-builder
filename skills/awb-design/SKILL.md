---
name: awb-design
description: Use when choosing architecture, backends or existing script, Skill and MCP integrations for an agent work system. Implementation and acceptance decisions belong to separate modules.
metadata:
  version: 0.1.0a4
---

# AWB Architecture and Integration

Select the smallest architecture that meets the confirmed task and explain its evidence and integration boundaries.

Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md). Input is the goal/brief, constraints, acceptance examples, existing interfaces and observed host capabilities. Read [architecture-selection.md](../building-agent-worksystems/references/architecture-selection.md) for node/backend choices and [integrations-and-skills.md](../building-agent-worksystems/references/integrations-and-skills.md) only when considering reuse or external integration.

Inspect working scripts first. Preserve their inputs and implementation; specify a trusted argv wrapper, declared script/input dependencies and independent output checks. Fixed steps can remain ordinary program control flow. Choose a graph or durable framework only when dependencies, recovery or long-lived workers demonstrate the need. Do not add a second ledger alongside AWB state.

Classify capability evidence as tested, documented, unknown or unsupported. A version check does not prove inference; an HTTP fixture does not prove model behavior. Offline goals exclude undeclared remote destinations. MCP provides typed operations, not OS isolation, and optional MCP absence does not prevent a CLI design. Reading documentation does not authorize downloads, host configuration or publication.

Return an architecture choice with alternatives, input/output contracts, verifier, declared dependencies, budget and concrete capability gaps. Planning-only requests stop here. Send unresolved consequential requirements to `awb-clarify`; send an authorized implementation package to `awb-execute` without enlarging authority.

Example: “Keep parser.py and add recoverable orchestration, offline.” Specify how the existing parser is invoked and verified; do not replace it or introduce a cloud service.
