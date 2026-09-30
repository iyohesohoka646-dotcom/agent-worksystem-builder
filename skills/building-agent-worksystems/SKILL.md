---
name: building-agent-worksystems
description: Build or improve a user's agent-assisted work system through bounded changes, persistent goals, real task verification, and recovery across sessions. Use for a working pipeline or a sustained system-building task; ordinary one-off questions do not need this workflow.
metadata:
  version: 0.1.0a1
---

# Building Agent Worksystems

Requirements: Python 3.11+ with jsonschema and httpx. Probe host tools and backend capabilities before use; strict isolation requires an independently verified host boundary.

Check the interpreter's imports before calling the runtime. If dependencies are missing, create a virtual environment inside the user's target project and install this Skill's `requirements.txt` there, subject to the user's existing network constraints. Use that interpreter for subsequent commands. Never put project state into the plugin cache.

Help the user obtain a working system they can run, inspect, recover and change. Keep the user's original purpose and explicit limits visible while choosing the smallest useful implementation. Deterministic scripts, human decisions and model calls are all valid nodes; add orchestration only when the task needs it.

## Start or resume

The executable entry is `scripts/awb.py` relative to this Skill. Run it with the host's Python 3.11+ interpreter; `--help` lists commands. The `awb` console command is also available after package installation. Use an explicit `--project` for every operation. Never treat the Skill installation directory as the user's project.

If `.worksystem-build/state.sqlite` exists, read `awb status --project PROJECT --json` and the versioned goal before making proposals. Inspect current artifacts and any invalidated evidence. `handoff.md` is a generated summary, so reconstruct it from persistent state when needed. Preserve recorded decisions and answered questions. An accepted cycle records a local improvement, not final acceptance of every user goal.

For a new project, inspect the existing files and environment, then record the user's wording, requirements and actual acceptance examples in a goal JSON. Distinguish user statements, environment facts, experiments and your inferences; an inference remains unconfirmed. Keep hard limits separate from preferences. Use `awb init --goal GOAL.json --project PROJECT` after the project scope is clear. For goal changes use `awb goal --file NEW.json --expected-revision N`; preserve the old goal and revalidate affected results.

Ask only about an uncertainty that can change the next action, data destination, budget or acceptance. Detect discoverable facts with tools. Reuse existing scripts when suitable. Read [adaptive-interview.md](references/adaptive-interview.md) when deciding what to ask and [architecture-selection.md](references/architecture-selection.md) when choosing node types or backends.

## Construction loop

For each cycle, record the target requirement, gap, hypothesis and a result that would refute it, current baseline, proposed change, predeclared checks and limits, actual evidence, decision and next step. Read [lifecycle.md](references/lifecycle.md) for the concrete CLI/API sequence. Keep the Builder's own development/evaluation records separate from the target system's runs.

Prepare a limited candidate against the accepted baseline. `prepare_change` describes owned files and captures before/after content; inspect its diff before applying. Existing session authorization covers routine steps within the agreed scope. If the candidate requires new authority or a data destination not already approved, obtain that decision before execution. Preserve user edits; a drift error requires reconciliation, not forced regeneration.

Execute within an explicit call/time budget. Node completion establishes execution only; a separate verifier checks artifacts and task correctness. A worker's success claim cannot replace those checks. Use `awb verify --reference REFERENCE.json` for the materials example; structural verification without a reference does not establish classification accuracy. Read [evidence-and-decisions.md](references/evidence-and-decisions.md) before accepting, replacing or rolling back a candidate.

Let results change the plan: accept, revise, replace, rollback, wait or cancel. Two consecutive refutations of the same hypothesis require reassessment. Three cycles without progress or a reduction in key uncertainty require a route review. Never retry unchanged authentication, permission, input or schema errors. Transient retries are bounded to at most two additional attempts and count toward the budget.

## Human decisions, recovery and delivery

An unattended run must return `needs_human` with a saved request rather than wait silently on stdin. Show that request to the user; submit their structured answer with `awb review --id ID --answer ANSWER.json --actor USER`, then resume. Do not manufacture a user's approval. Existing approval is valid only for its bound goal revision, input and action.

Check input hashes, dependencies, backend/configuration versions and artifact integrity before reusing a result. An interrupted external side effect requires checking external state; when that cannot be established, keep it pending. Read [recovery-and-security.md](references/recovery-and-security.md) before operations with side effects or strict isolation requirements.

Deliver the independent run command, configurations, dependencies, task evidence, recovery/rollback steps and known limitations. Report runtime tests, Skill behavior tests and target-system acceptance separately. A local rules demonstration is a local rules demonstration; label synthetic fixtures, mocked transports and untested hosts. Completion of system construction requires the agreed task evidence and user acceptance. Saving a checkpoint does not start a background service.
