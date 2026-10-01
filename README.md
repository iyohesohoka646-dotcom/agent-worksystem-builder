# Agent Worksystem Builder

**Build repeatable agent workflows you can inspect, verify and resume.**

**构筑可检查、可核验、可恢复的智能体工作系统。**

[English](README.md) · [简体中文](README.zh-CN.md) · [Quick start / 快速上手](docs/quickstart.md) · [Download alpha.4](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4)

[![Runtime and distribution CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)

Agent Worksystem Builder is an experimental **Codex plugin** for turning a recurring task into a local, evidence-backed workflow. One coordinator composes four focused Skills for requirements, architecture, controlled execution and verification. They share a Python CLI, saved project state and an optional local MCP server.

Start with the included document-triage example: preserve source files, produce traceable JSONL/CSV results, ask for human review when needed and continue from a saved checkpoint. Other domains require their own contracts and checks.

## Why use it?

- **Keep existing tools.** Wrap a working parser or script instead of replacing it.
- **Make changes inspectable.** Track goals, owned files, candidate changes and actual evidence.
- **Keep human decisions explicit.** Save review requests; never invent an approval.
- **Resume from the project.** Retain run IDs and checkpoints across processes and conversations.

Useful for recurring materials processing, document triage and small local pipelines that need review and recovery. A one-off factual question does not need this system.

## Quick start

With a Codex version supporting plugin marketplaces:

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

Open a new session, select `agent-worksystem-builder:building-agent-worksystems`, and try:

> Build a local workflow for these Markdown files. Preserve the originals, export traceable JSONL and CSV, ask me about ambiguous classifications, and make the run resumable. Keep it offline and inspect existing scripts first.

The plugin guides construction; it does not start a background service. Its Python runtime requires Python 3.11+ and the packaged dependencies. Reuse a compatible project environment; the bundled doctor checks readiness without initializing the target project. The local rules example does not require a model API key. Configured model backends use your own provider access.

### Git connection restricted?

Download the plugin ZIP from the [release page](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4), then:

```powershell
Expand-Archive ./agent-worksystem-builder-0.1.0-alpha.4-plugin.zip ./awb-plugin
codex plugin marketplace add ./awb-plugin/agent-worksystem-builder
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

For a repeatable, model-free CLI walkthrough with expected results, see the [bilingual quick-start guide](docs/quickstart.md).

## One coordinator, four focused Skills

| Entry point | Responsibility | Example request |
|---|---|---|
| `building-agent-worksystems` | Select the relevant module and carry context | “Build or resume this workflow.” |
| `awb-clarify` | Requirements, constraints and acceptance examples | “Clarify the goal; do not run anything.” |
| `awb-design` | Architecture, existing scripts and Skill/MCP integration | “Keep my parser and add recoverable orchestration.” |
| `awb-execute` | Authorized changes and bounded execution | “Apply this scoped change and record the run.” |
| `awb-verify` | Independent checks, human review and safe recovery | “Inspect this checkpoint without modifying it.” |

For a new build, the coordinator can compose `clarify → design → execute → verify`. A narrow request stops at its own result; already satisfied stages can be skipped. Modules can be invoked directly, but must be installed together. They are instruction modules, not automatically spawned agents.

The [handoff contract](skills/building-agent-worksystems/references/module-contract.md) carries the same project, goal revision, permissions, budget, identifiers and evidence. Shared runtime and references remain in one directory; SQLite remains authoritative for initialized projects.

## What do you get?

| Artifact | What it makes inspectable |
|---|---|
| Versioned goals and decisions | What the system is meant to do, and why it changed |
| Candidate manifests and execution records | Which owned files changed and what actually ran |
| JSONL/CSV materials outputs with hashes | Results traceable to source inputs |
| Saved reviews and checkpoints | What needs a human answer and where work can resume |
| Independent verification evidence | What passed, what failed and what remains unknown |

Project data lives outside the plugin cache. Execution completion, independent task verification and real user-goal acceptance are separate checks.

## Which download should I use?

All files are on the [alpha.4 release page](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4).

| Download | Use it for |
|---|---|
| `agent-worksystem-builder-0.1.0-alpha.4-plugin.zip` | Full Codex plugin and local marketplace installation |
| `agent-worksystem-skills-0.1.0-alpha.4.zip` | The complete five-folder suite for other Skill hosts; copy all folders together |
| `agent_worksystem_builder-0.1.0a4-py3-none-any.whl` | Standalone Python runtime |
| The two `.manifest.json` files | Archive SHA256 and per-file integrity checks |

The Skill-suite ZIP is not a plugin-upload archive. The wheel does not include Skills or the development evaluator. The plugin ZIP is prepared for official submission, but official-directory approval and ChatGPT web import are not established.

## Optional MCP and existing integrations

The optional project-bound stdio MCP exposes eight structured tools and two resources for the local materials rules example. It shares the CLI's state, checkpoints and verifier. It does not approve human reviews, execute arbitrary commands or provide an OS sandbox; it is not enabled automatically.

See [MCP setup](skills/building-agent-worksystems/references/mcp.md), [integration and reuse guidance](skills/building-agent-worksystems/references/integrations-and-skills.md), and [architecture](docs/plugin-architecture.md). Model backends and other construction work continue through the existing Skill/CLI interfaces.

## Status and limits

Released version: **0.1.0-alpha.4**; Python package: **0.1.0a4**. The [release-source CI run](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/runs/36823390117) passed 108 tests on Windows and 107 on Linux, with one platform-specific Linux skip. Native Codex 0.158.0 installation discovered all five enabled Skills. The five release assets were downloaded and matched their local SHA256 values.

These checks cover runtime, packaging and bounded routing exercises. They do not prove improved model performance or acceptance on real user material. Live Codex/Ollama/Claude compatibility, current-chat MCP connection, ChatGPT web import and official-directory approval remain separate gates. This is an alpha, with no background-running or OS-isolation guarantee. Full evidence and limits are in [delivery status](docs/delivery-status.md).

The published tag and release binaries remain fixed; the main branch's documentation can improve independently. See [release notes](docs/release-alpha4.md) for a bilingual summary.

## Learn, share and report a problem

- [Quick-start walkthrough / 快速上手](docs/quickstart.md)
- [Copy-ready bilingual introduction / 双语推广文案](docs/share.md)
- [Runtime interfaces](docs/interfaces.md) and [evaluation protocol](evals/README.md)
- [Issues and support](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/issues)

For a useful issue, include the version, host/OS, intended result, observed result and a small sanitized reproduction. Keep credentials and private source material out of public reports.

Data handling: [PRIVACY.md](PRIVACY.md). Use and licensing: [TERMS.md](TERMS.md). No open-source license is designated; public availability does not grant a broad redistribution or modification license.
