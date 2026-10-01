---
name: awb-clarify
description: Use when an intelligent system's requirements, acceptance examples or consequential decisions are unclear, including during construction or when its goal changes.
metadata:
  version: 0.2.0a2
---

# AWB Requirements

Grill the requirement or consequential decision that matters next, keeping the user's broad system goal intact. Clarification can recur after a prototype, failed check, goal change or new resource discovery.

Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md). Input is the current request, target project, existing goal/answers if available and observed uncertainties. Read [adaptive-interview.md](../building-agent-worksystems/references/adaptive-interview.md) for consequential unknowns.

Keep the user's wording, hard limits and acceptance examples distinct from assumptions and environment observations. Reuse answered questions. Ask only when the answer can change the next action, budget, privacy boundary or destination; reversible presentation choices need not delay work. Prefer a safe local probe when it answers the uncertainty more directly.

Keep original wording, confirmed requirements, pending issues, answer sources and decision reasons. Reuse saved answers; reopen only affected decisions with the evidence and reason. Save stable question IDs in ExplorationRecord for initialized projects; inferred preferences are unconfirmed. Ask one high-impact question at a time when interaction permits, or a compact related group when needed. Facts discoverable from files/tools go to `awb-explore` before asking. Do not promote an example or successful local candidate into the entire product scope.

Return the proposed goal or delta, actual answer, consequential decision, acceptance examples and next unresolved item. For batch materials, cover representative inputs and human-review conditions as one domain example. Planning ends here; an ongoing build returns to the coordinator without treating clarification as whole-goal completion.

For an authorized goal change, pass the proposed file and observed revision to `awb-execute`; it uses revision-checked replacement and retains history. For architecture work, pass the confirmed brief to `awb-design`. Module handoff does not approve either operation.

Example: “Clarify acceptance for an offline document sorter; do not run it.” Return a local-only brief and concrete test examples, with unknown domain labels left unconfirmed.
