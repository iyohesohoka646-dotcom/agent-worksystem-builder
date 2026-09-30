# Behavioral evaluation protocol

The scenario file separates development cases from holdout cases. All conditions receive the same raw task, fixture, declared permissions and limits. Baseline receives no dedicated Skill; generic receives only ordinary engineering guidance; Builder receives the portable Skill entrypoint and tool path. Expected JSON is a task output contract shared by all conditions, not a required internal architecture.

`tools/evaluate.py` runs explicitly configured native host commands in separate workspaces and evaluates actual artifacts. It does not infer success from the host's final text. The host configuration is trusted local configuration with argv, allowed_executables, host_version, model, timeout and trusted=true; use `{workspace}` in arguments and read the supplied prompt from stdin. Set the host's own workspace sandbox and ephemeral-session options. Do not use an unsandboxed host to process untrusted evaluation fixtures.

Use at least five repeats per condition for key behavior cases. Preserve every attempt, return code, duration, input/output hashes, host/model versions and raw logs. Environment failures are classified separately. Human rubric items remain pending until assessed with actual evidence; an automatic artifact pass does not imply full behavior acceptance. The holdout cases must remain excluded from rule tuning.

This initial corpus is synthetic and small. A complete release also needs actual user material and multi-session trials, with baseline quality, time, cost and human effort measured comparably. Unknown cost stays unknown. The local harness test uses a deterministic Python fixture to test the runner, with no claim about model behavior.
