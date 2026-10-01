---
name: awb-explore
description: Use when intelligent-system construction needs evidence about environments, resources, architectures or uncertain implementation decisions, including research, prototypes and solution comparisons.
metadata:
  version: 0.2.0a1
---

# AWB Adaptive Exploration

Reduce the uncertainty most consequential to the next construction decision. Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md) and [exploration.md](../building-agent-worksystems/references/exploration.md).

Read existing answers, decisions, interfaces, installed resources and capability evidence first. Choose environment discovery, primary-source research, architecture alternatives, a reversible prototype or comparison according to uncertainty, task, reversibility, authority and remaining budget. Keep looking beyond an initial catalog when evidence supports another solution; an approved execution catalog restricts execution authority, not the design space.

Record question, search strategy/reason, candidates, sources/version/license/compatibility, actual experiments, rejected alternatives/reasons and next action in ExplorationRecord. Unknown licensing and unsupported capabilities stay unknown. Finding or documenting a resource does not authorize installing it, adding credentials/fees or sending data to a new destination. Pass such choices to `awb-clarify`; implementation goes to `awb-design` or `awb-execute` after authority is resolved.

Reuse known facts and saved answers. Reopen an affected decision on contradictory evidence, a failed backend/prototype, changed goals, user drift or budget limits, explaining why the construction route changes. Native Codex supplies semantic judgment and uses available search/tools; the deterministic helper ranks supplied uncertainty records, not natural language.

Return updated evidence/candidates, confidence limitations and one next bounded action. An exploration-only request ends here; a complete build returns to the coordinator and continues until the whole goal or a concrete checkpoint gate.
