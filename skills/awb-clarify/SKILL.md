---
name: awb-clarify
description: Use when requirements, acceptance examples or consequential constraints are unclear for an agent work system, or its recorded goal needs revision. Ordinary factual questions do not need this module.
metadata:
  version: 0.1.0a4
---

# AWB Requirements

Turn the user's actual task into an inspectable goal without choosing or executing an implementation.

Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md). Input is the current request, target project, existing goal/answers if available and observed uncertainties. Read [adaptive-interview.md](../building-agent-worksystems/references/adaptive-interview.md) for consequential unknowns.

Keep the user's wording, hard limits and acceptance examples distinct from assumptions and environment observations. Reuse answered questions. Ask only when the answer can change the next action, budget, privacy boundary or destination; reversible presentation choices need not delay work. Prefer a safe local probe when it answers the uncertainty more directly.

Return the proposed goal or goal delta, confirmed constraints, acceptance examples and the one unresolved item that matters next. For batch materials, cover representative inputs, tolerated errors, human-review conditions and output. A request for a plan ends here: do not initialize state, install dependencies or run a workflow.

For an authorized goal change, pass the proposed file and observed revision to `awb-execute`; it uses revision-checked replacement and retains history. For architecture work, pass the confirmed brief to `awb-design`. Module handoff does not approve either operation.

Example: “Clarify acceptance for an offline document sorter; do not run it.” Return a local-only brief and concrete test examples, with unknown domain labels left unconfirmed.
