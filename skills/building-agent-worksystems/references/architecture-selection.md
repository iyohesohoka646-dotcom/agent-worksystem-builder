# Architecture and adapter choices

Use ordinary program control flow for fixed dependencies. The runtime's graph supports explicit dependencies, equality conditions on a direct parent, 1–10 bounded repetitions and concurrency 1–8. Each node gets a distinct artifact directory. A planner may select and connect nodes from an approved catalog using `plan_from_selection`; it cannot inject shell text, arguments or a new tool.

The command adapter accepts trusted argv configurations with explicit executable paths. On Windows use a native executable, not an interpolated `.cmd` command line. A Python script is invoked as `[python_executable, script_path]`; declare input/script dependencies in `input_files` so changes invalidate reuse. Tool execution is a capability, not a property shared by every model.

Codex uses event JSONL plus a separate final Schema response. Ollama uses its HTTP `/api/chat` envelope and requires a model name. Probe before use; report capabilities as tested, documented, unknown or unsupported. A version command establishes availability, not working inference. Fresh model/host versions require repeat probes. An HTTP fixture tests normalization only.

The generic command adapter does not enforce an offline boundary. The built-in rules workflow avoids model/network calls; the Ollama adapter limits offline endpoints to loopback and rejects declared cloud model tags. End-to-end offline inference additionally requires a local-only Ollama server configured by its operator; the client cannot attest the server's own routing. A request for verified OS isolation is rejected by the runtime until a suitable enforcement adapter is supplied.
