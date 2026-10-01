# Target intelligence modes

Versioned IntelligenceProfile separates model/mode/resources/context/permissions/budget from the target's ArchitecturePlan. `none` is appropriate when deterministic code satisfies the task. `interactive`, `noninteractive` and `mixed` are available with explicit tested access.

Interactive target UI: local `codex app-server --stdio`, initialized JSON-RPC connection, thread/start or resume, turn/start, events, explicit server-request responses, turn/interrupt and actual turn completion. The target application owns UI, storage, approvals and lifecycle. `awb_core.adapters.app_server.AppServerClient` supplies bounded owned-process transport, not a ready hosted UI or autonomous approval service. Save actual session identifiers and events in target state. Unsupported server requests fail rather than receiving invented approval.

Noninteractive target node: `codex exec` with closed stdin, separate JSONL events and structured final output, explicit working directory, model and limits. Preserve user/provider config and rules by default; override only explicit project options. Read-only is the default; workspace-write requires authorized scope. Noninteractive approval policy is `never`, so unresolved permissions fail instead of silently escalating. Final JSON does not prove resulting files or task semantics.

`profile --compile --id PROFILE_ID` validates the current review-bound profile and emits config without credentials. The native Builder does not need to call itself through exec or run a background service. Target applications may use these adapters as ordinary libraries and remain independent of Builder state/DAG. Validate live access on the exact intended host/model; executable/version/protocol fixtures are distinct evidence.

Primary interfaces: [app-server](https://learn.chatgpt.com/docs/app-server), [noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode). Generate protocol schemas using the actual CLI version when needed; experimental APIs require explicit opt-in. No remote app-server hosting is required.
