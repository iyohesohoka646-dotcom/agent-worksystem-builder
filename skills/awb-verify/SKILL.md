---
name: awb-verify
description: Use when independently checking intelligent-system software, services or artifacts, deciding a construction candidate, inspecting checkpoints, or handling human review and recovery.
metadata:
  version: 0.2.0a1
---

# AWB Verification and Recovery

Determine what the actual evidence supports and preserve the checkpoint when a decision or effect remains unresolved.

Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md). Input is the current goal/revision, run/change identifiers, artifact paths, declared checks and actual human answers if any. Read [evidence-and-decisions.md](../building-agent-worksystems/references/evidence-and-decisions.md) for acceptance, [recovery-and-security.md](../building-agent-worksystems/references/recovery-and-security.md) for resume/reuse/rollback and [lifecycle.md](../building-agent-worksystems/references/lifecycle.md) only for an authorized state transition.

Separate structure, execution, task correctness and goal achievement. Check actual artifacts and their hashes, input/dependency bindings, goal revision, verifier and acceptance fingerprints. Independent domain labels or real user acceptance are needed for semantic claims. Missing labels mean only structural/integrity evidence. Retain failed attempts and unknown metrics; do not tune acceptance criteria after observing a candidate without versioning and rerunning baseline and candidate.

Use registered program, loopback-service, artifact or domain verifiers, with materials as one implementation. Bind actual checks to requirement IDs, candidate bytes, ArchitecturePlan/IntelligenceProfile, acceptance and verifier versions. Run the target outside the original Builder session; test its independent entrypoint, dependencies/configuration, persistence/recovery and extension points. A source inspection or a fake backend is not a live intelligence check.

After accepting a local candidate, query whole-goal `delivery` coverage and return uncovered requirements to the coordinator. Check cross-type regressions, pure-program simplification and target business-state independence. Missing new fields in old projects stay unknown. Return unresolved access/budget/authority gates with the checkpoint; they cannot establish whole-goal completion or release qualification.

For inspection-only work, report findings and stop; do not initialize, repair mirrors, approve, resume, rollback or implement corrections. On `needs_human`, show saved review IDs, quotations and choices. Submit `review` only after the genuine user answer arrives and only within the authorized operation; MCP cannot approve. Keep unanswered requests pending.

Before authorized resume, validate current goals, inputs, approvals and outputs. Reconcile unknown external effects before replay; automatic replay needs a no-side-effect or explicit trusted idempotency contract. Preserve user drift on rollback. Accepted changes need a compensating candidate through `awb-execute`.

Return observed checks, evidence paths, missing acceptance, actual review requests, unresolved effects and a bounded recommendation. Record a candidate decision only when requested and evidence supports it. Complete delivery includes commands, dependencies, task evidence, recovery steps and limitations; a local accepted cycle does not close overall user acceptance.

Example: “Only inspect this needs_human checkpoint.” Show the pending request and check source/output bindings without manufacturing an answer or resuming execution.
