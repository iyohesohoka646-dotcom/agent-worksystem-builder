# v0.1.0-alpha.1

Initial public Codex plugin distribution of Agent Worksystem Builder. Includes the portable `building-agent-worksystems` Skill, Python CLI, persistent goal/history contracts, transactional accepted specifications, controlled file changes, independent evidence verification, bound human decisions, materials processing, resumable graphs and command/Codex/Ollama adapters. The plugin declares no MCP servers or lifecycle hooks.

Windows verification passed 62 runtime tests. Codex CLI 0.158.0 successfully installed the plugin in an isolated home, listed it as enabled, ran its cached CLI and discovered the namespaced Skill through native app-server metadata. A local synthetic materials trial recorded failure, rollback, correction, simulated human review, fresh-process resume and acceptance. The portable Skill and Python wheel were built and checked.

Download the plugin ZIP for installation or official-directory upload, the standalone Skill ZIP for other hosts, or the Python wheel for standalone runtime use. The plugin `.manifest.json` records each packaged file's SHA256. Installation commands are in the repository README.

Cross-platform GitHub Actions run 36704420379 passed on both Windows and Linux with Python 3.11. The Python wheel also passed an isolated installation, CLI and packaged-schema check.

This is an alpha. A real Codex inference probe hit its 120-second connection deadline. Live Ollama and Claude Code checks, the repeated Skill behavior comparison and real user task acceptance remain pending. The official directory package is prepared; platform upload, verification, review and publication remain separate steps.
