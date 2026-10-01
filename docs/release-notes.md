# v0.1.0-alpha.4

Splits workflow instructions into the existing coordinator and four focused Skills: `awb-clarify`, `awb-design`, `awb-execute` and `awb-verify`. Each module has its own trigger, inputs, outputs and stopping conditions. Shared references, handoff context and the single Python runtime preserve goal/state and permission boundaries; CLI/MCP interfaces are unchanged.

Portable packaging includes the complete five-folder Skill suite. The evaluator now freezes all modules while retaining legacy single-Skill comparisons, and rejects incomplete modular inputs. Independent read-only exercises cover narrow planning, inspection-only checkpoints and drifted candidates; they are not a repeated model benchmark. This change does not establish a fix for the earlier ChatGPT web archive-upload error or official publication.

Includes the previously local alpha.2/alpha.3 dependency doctor, optional project-bound MCP source and integration/evaluation tooling. Windows verification passed 108 tests, and native Codex 0.158.0 installed the plugin and discovered all five enabled Skills. GitHub prerelease assets are the plugin ZIP/receipt, complete Skill-suite ZIP/receipt and Python wheel. Live model comparisons, real user-task acceptance, ChatGPT web import and official-directory publication remain separate gates.

# v0.1.0-alpha.3

Adds a focused integration/Skill reuse guide covering preserved local parsers, pinned instructions, existing documentation/repository MCPs, offline boundaries and evidence-led framework selection. Documents the difference between negotiated MCP Skill discovery and OpenAI's scan-time Skill import, plus the initial-submission MCP constraint. No external Skill or framework is vendored or automatically enabled.

Extends the existing artifact evaluation driver with optional previous-Skill comparison, frozen Skill/corpus bindings, randomized matched runs, measured elapsed time, actual artifact hashes and incrementally saved failure/pass summaries. Empty output assertions and mutated frozen contexts fail closed. Costs, tokens and model calls remain unknown, human rubric checks remain pending, and automated results never establish full qualification. The full plugin now ships the driver and synthetic corpus; standalone Skill/wheel scope is unchanged.

This is a local candidate, with no GitHub release or official-directory submission. Local fixtures test the evaluator, not model effects. Current evidence is in [delivery-status.md](delivery-status.md).

# v0.1.0-alpha.2

Adds an optional project-bound stdio MCP with eight tools and two JSON resources, sharing the CLI's goal/state, deterministic materials processing, review checkpoints and independent verifier. No generic command, backend switch or approval tool is exposed. The portable plugin stays skills-only; local MCP configuration is explicit and uses separately installed SDK dependencies.

Adds a standard-library dependency doctor, explicit optional-MCP routing and setup references, compact Skill entry instructions and user-facing Skill metadata. Distribution filters exclude generated package metadata and bytecode. Project initialization now closes its SQLite connection immediately, avoiding Windows file-handle retention.

This candidate is not yet a GitHub release or an official-directory submission. Current evidence and remaining acceptance gates are in [delivery-status.md](delivery-status.md).

# v0.1.0-alpha.1

Initial public Codex plugin distribution of Agent Worksystem Builder. Includes the portable `building-agent-worksystems` Skill, Python CLI, persistent goal/history contracts, transactional accepted specifications, controlled file changes, independent evidence verification, bound human decisions, materials processing, resumable graphs and command/Codex/Ollama adapters. The plugin declares no MCP servers or lifecycle hooks.

Windows verification passed 62 runtime tests. Codex CLI 0.158.0 successfully installed the plugin in an isolated home, listed it as enabled, ran its cached CLI and discovered the namespaced Skill through native app-server metadata. A local synthetic materials trial recorded failure, rollback, correction, simulated human review, fresh-process resume and acceptance. The portable Skill and Python wheel were built and checked.

Download the plugin ZIP for installation or official-directory upload, the standalone Skill ZIP for other hosts, or the Python wheel for standalone runtime use. The plugin `.manifest.json` records each packaged file's SHA256. Installation commands are in the repository README.

Cross-platform GitHub Actions run 36704420379 passed on both Windows and Linux with Python 3.11. The Python wheel also passed an isolated installation, CLI and packaged-schema check.

This is an alpha. A real Codex inference probe hit its 120-second connection deadline. Live Ollama and Claude Code checks, the repeated Skill behavior comparison and real user task acceptance remain pending. The official directory package is prepared; platform upload, verification, review and publication remain separate steps.
