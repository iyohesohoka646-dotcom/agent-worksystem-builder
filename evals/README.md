# Behavioral evaluation protocol

## 0.2 full construction matrix

`tools/evaluate_systems.py` uses systems.json: three families, development/holdout, four conditions and five repeats = 120 attempts. Freeze the user-approved gpt-6-sol/max override on C:/codex 0.158.0; both actual modes passed preflight, base provider/config/rules stay unchanged.

Disable implicit Skills/plugins/MCP with process-local overlays and check native skills/list. Freeze alpha.4 from its immutable tag, current suite, corpus, external checker/gateway, host fingerprints and randomized order. Every condition gets the same trusted loopback gateway running real app-server and exec. This fixture constrains evaluation interfaces, not product architecture.

Multi-turn responses select continued implementation, one question, completion or blockage. Questions use frozen **simulated-user** scripts. External graders launch targets, inspect outputs, preserve inputs, bind existing-project annotations and interactive discussion to real gateway answers, require task approval, restart business state and test backend replacement. Completion claims do not grade themselves. The workbench grader checks the expected execution output and a completed noninteractive call separately; this does not prove their binding or rejection of wrong node output. Those remain independent qualification gates.

Limits: 30 host turns, eight observed code-tree change batches and 900 seconds including validation. Internal reasoning cycles are unobservable, recorded as a limitation. No hidden retries or reruns of attempted cells. Quota/access/isolation failures preserve checkpoints. Unknown usage remains null. A complete matrix alone does not establish qualification; real human trial and goal/hard-constraint review remain separate. No superiority claims before matched reviewed evidence. [Run/resume](../docs/upgrade-0.2.md).

`tools/qualify_systems.py` creates a read-only, uniquely named snapshot without altering the frozen grader or running more construction. It checks bindings/integrity, preserved inputs, observed budgets, actual artifact results, question burden and per-scenario repetition stability. It leaves unmeasured usage and missing semantic/resource/recovery/human checks unknown. `release_qualified` remains false; a complete fixture matrix is not broad system-level acceptance. A deadline cleanup overrun remains visible rather than being subtracted from measured wall time.

`tools/workbench_fault_probe.py` separately starts a copied workbench artifact with deterministic wrong-result and failing-backend nodes. It tests explicit rejection, output binding and absence of automatic retries, preserves original sources, and records exact HTTP responses and task state. It makes zero model calls and does not change the original attempt's budget, status or frozen grade. It is supplemental artifact evidence, not a construction retry, general-architecture proof or human qualification.

## Retained single-turn development harness

The scenario file separates development cases from holdout cases. All conditions receive the same raw task, fixture, declared permissions and limits. Baseline receives no dedicated Skill; generic receives only ordinary engineering guidance; Builder receives the portable Skill entrypoint and tool path. Expected JSON is a task output contract shared by all conditions, not a required internal architecture.

`tools/evaluate.py` runs explicitly configured native host commands in separate workspaces and evaluates actual artifacts. It does not infer success from the host's final text. The host configuration is trusted local configuration with argv, allowed_executables, host_version, model, timeout and trusted=true; use `{workspace}` in arguments and read the supplied prompt from stdin. Set the host's own workspace sandbox and ephemeral-session options. Use a clean host home/session without implicit Builder or global Skills, otherwise the no-Skill baseline is contaminated. The driver cannot attest host isolation or declared model/host versions. Do not use an unsandboxed host to process untrusted evaluation fixtures.

Use at least five repeats per condition for key behavior cases. Preserve every attempt, return code, duration, input/output hashes, host/model versions and raw logs. Environment failures are classified separately. Human rubric items remain pending until assessed with actual evidence; an automatic artifact pass does not imply full behavior acceptance. The holdout cases must remain excluded from rule tuning.

This initial corpus is synthetic and small. A complete release also needs actual user material and multi-session trials, with baseline quality, time, cost and human effort measured comparably. Unknown cost stays unknown. The local harness test uses a deterministic Python fixture to test the runner, with no claim about model behavior.

## Previous/new Skill comparison

From the full plugin or repository root (not the standalone Skill ZIP or wheel), supply your verified host configuration and a previous Skill directory:

```powershell
python tools/evaluate.py --host-config HOST.json --output NEW_TRIAL_DIRECTORY --baseline-skill OLD_SKILL_DIRECTORY --split development --repeats 5 --max-attempts 40
python tools/evaluate.py --host-config HOST.json --output NEW_HOLDOUT_DIRECTORY --baseline-skill OLD_SKILL_DIRECTORY --split holdout --repeats 5 --max-attempts 40
```

Without `--baseline-skill`, the original baseline/generic/Builder matrix needs 30 attempts per split. Adding it creates a `previous` condition and makes previous Skill the paired reference. `--builder-skill` selects an alternate Skill or complete suite; by default it freezes the entire packaged `skills/` directory. Passing any of the five modular Skill directories also includes its sibling modules and uses the coordinator as the evaluation entrypoint. An incomplete suite is rejected before output is created; unrelated installed Skills are excluded from its snapshot. Legacy single-Skill directories remain supported. `--corpus` selects a task corpus, and `--seed` controls randomized order. Required budget is checked before creating an output directory or invoking the host. The output must be new and outside the source Skill/suite directories.

Before attempts, the driver copies distributable Skill files into `context/`, freezes the corpus and records file hashes, host/config digest, seed and job order in `manifest.json`. Every attempt records scenario/host/Skill bindings, actual input and inspected JSON artifact hashes, elapsed execution time, return status and raw stdout/stderr. It checks preserved inputs and Skill context. Skill drift between attempts stops the matrix with partial results retained. A process error remains a failed attempt; the runner never drops failed/timeout attempts from aggregate rates. The time measure covers host process execution and includes host startup, not the evaluator's setup/verification work.

`summary.json` is refreshed after each attempted job. It reports artifact pass counts/rates, elapsed mean/sample standard deviation and paired artifact-pass-rate deltas. A pair requires the same scenario, repetition, host/config and input binding. A mismatched comparison has a null delta; partial summaries describe attempted jobs so far, not the full scheduled matrix. Check `complete` and the minimum-repeat flag before interpreting a comparison; these remain separate from human review and qualification. Costs, tokens and model-call counts remain null because this driver has no trusted usage collector. Do not infer zero consumption or population effects from these values. Human rubric checks stay pending and `qualification` stays `not_established`, even when all automated artifacts pass. Exit 0 means the matrix completed, not that its conditions passed. An interruption leaves `complete=false`; use a fresh output directory for a rerun and keep the old evidence.

For offline material, independently verify that the configured host and tools are offline. An argv allowlist and trusted flag do not establish that property. Local fixture tests validate freezing, binding, budget checks and aggregation only; they do not execute a language-model comparison.
