---
name: awb-execute
description: Use when an intelligent system has an authorized implementation, goal update, target configuration or bounded candidate run to carry out.
metadata:
  version: 0.2.0a1
---

# AWB Controlled Execution

Apply the authorized change and preserve its actual execution evidence; leave acceptance to independent verification.

Implement the target application's actual components and independent entrypoints through native Codex engineering tools and suitable libraries. The AWB CLI records controlled candidates and evidence; its material processor and optional graph are examples/reusable facilities, not the only implementation routes. Use ArchitecturePlan and IntelligenceProfile IDs on cycles when available. Unresolved consequential contract reviews block execution; no fabricated approvals or missing historical contracts.

For target interactive intelligence, use the local stdio app-server client, persist thread/turn IDs in the target's business state, forward events and explicit user requests, and support resume/interrupt. For noninteractive intelligence, use `codex exec` with actual working config/rules, bounded calls, JSONL events and separately validated structured output. Workspace-write is explicit and scoped to the target directory; noninteractive execution denies unresolved approval prompts. Read [intelligence-modes.md](../building-agent-worksystems/references/intelligence-modes.md) when implementing these modes.

Read the shared [handoff contract](../building-agent-worksystems/references/module-contract.md), then [lifecycle.md](../building-agent-worksystems/references/lifecycle.md) for CLI operations. Read [recovery-and-security.md](../building-agent-worksystems/references/recovery-and-security.md) before rollback, replay or side-effectful execution. Input is the goal revision, implementation contracts, change scope, current identifiers and remaining budget.

Resolve the shared runtime and run its doctor before runtime imports. For a new system, initialize only after a build/run is requested and a goal is ready. Existing state and owned-file manifests take precedence over generated mirrors. Replace a goal through revision-checked `goal --file NEW.json --expected-revision N`; retain history and invalidate affected evidence.

Record the cycle's requirement, gap, hypothesis, refuting result, baseline, bounded change and declared checks. Inspect candidate ownership and the actual diff before apply. Preserve unrelated edits; stop the conflicting operation on drift. Execute with explicit call/time limits and declared input/script dependencies. Do not retry unchanged authentication, permission, input or schema errors; transient retries are bounded to two additional attempts and consume budget.

Return cycle/change/run identifiers, actual artifact paths and hashes, consumed/remaining budget, failures, uncertain effects and the next check. Do not equate execution completion with task acceptance. On `needs_human`, return the saved requests to `awb-verify` and preserve the checkpoint; do not answer for the user. After two repeated refutations or three stagnant cycles, return the evidence to `awb-design` for reassessment.

Example: Apply a bounded parser wrapper without changing parser.py; retain both failed and corrected runs and pass actual outputs to the verifier.
