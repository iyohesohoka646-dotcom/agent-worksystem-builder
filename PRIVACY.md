# Data handling

The publisher does not operate a collection server for this plugin. The Python runtime stores goals, source hashes, review answers, execution logs and evidence in the local project selected by the user. These files can contain the supplied material and model output. Project exports include recorded state, source material and evidence; choose export destinations deliberately.

The built-in materials rules run locally. A configured Codex backend sends its task and document through the user's Codex service account, under that provider's policies. Ollama requests go to the configured endpoint. Trusted command nodes execute the configured program and inherit its access. The host application and model provider have their own data handling policies.

The optional local MCP uses stdio and the same project state. It exposes goals, source quotes, run records and review requests to the connected host. It does not call a model backend or send data to a publisher-operated service; the host may send tool output to its own model provider. Enabling it requires an explicit project binding and separate local SDK dependencies.

This plugin does not provision credentials. Users configure their own backends. Do not place secrets in source material, logs or public issue reports. Support is provided through the project's GitHub issues; any information posted there is governed by GitHub's visibility settings and policies.
