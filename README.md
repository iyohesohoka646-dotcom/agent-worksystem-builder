# Agent Worksystem Builder

Build the intelligent system you need through dialogue, adaptive exploration, implementation and evidence.

[English](README.md) · [简体中文](README.zh-CN.md) · [Quick start](docs/quickstart.md) · [Upgrade / rollback](docs/upgrade-0.2.md)

[![Runtime and distribution CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)

An experimental Codex plugin for automatically designing, orchestrating, implementing and improving **whole intelligent systems**. Continuous requirement and decision grilling preserves the original goal. An evaluate → create → verify → decide loop explores alternatives, implements authorized changes, checks real software and returns consequential trade-offs to you.

## Three layers, open architecture

| Layer | Responsibility |
|---|---|
| Builder | Your native Codex conversation understands the goal, explores choices, builds and verifies. |
| Target system | Ordinary software: programs, UI, services, storage, scheduling, interfaces and deployment, composed to suit the task. |
| Optional intelligence | Interactive and noninteractive participation; models, agents, Skills, plugins, MCP, tools, context, permissions and budgets. |

The target can run after the Builder conversation closes. It owns its business data. It does not have to adopt AWB's DAG, SQLite or a controller agent. A deterministic program is the right outcome when AI is unnecessary.

## One coordinator, five focused Skills

| Skill | Role |
|---|---|
| building-agent-worksystems | Coordinate the whole-goal construction loop and resumption. |
| awb-clarify | Ongoing grill: requirements, unanswered questions, consequential decisions and reasons. |
| awb-explore | Environment/resource discovery, primary-source research, architecture candidates, prototype trials and comparison. |
| awb-design | Suitable software architecture and a separate intelligence profile. |
| awb-execute | Authorized engineering and bounded interactive/noninteractive integration. |
| awb-verify | Actual program/service/artifact/domain checks, whole-goal coverage and recovery. |

Modules share versioned ArchitecturePlan, IntelligenceProfile and ExplorationRecord contracts, the original goal and immutable evidence. They are composable instructions, not automatically spawned agents. A successful local candidate does not complete uncovered requirements.

## Try these requests

> Build a task workbench with a UI, service and persistent tasks. Use interactive Codex to discuss tasks and noninteractive Codex to execute them; ordinary code must check the actual outputs. Make it usable after this conversation closes.

> Preserve my existing application's API and tests. Explore where intelligence helps, compare alternatives and add only the justified participation points. Pause for credentials, costs or changed data destinations.

> Build a deterministic CSV summary tool. If ordinary code is enough, do not add model calls, agents or a service.

The materials-classification example remains available; it is one domain example.

System-level goals can span multiple projects, task types, component dependencies, events/scheduling and intelligence participation points, with architecture chosen through exploration and decisions. See [system-level construction](docs/system-level-construction.md). `examples/task-workbench` is only a local dual-mode/recovery sample; it has no project model or cross-task scheduler and cannot replace the complete product or representative system-level human acceptance.

## Implemented and validated are separate

The 0.2.0-alpha.1 **unreleased candidate** includes persistent contracts/grill/exploration, review-bound configuration, scoped workspace writes, app-server sessions/approvals/events, exec structured results, registered verifiers, goal coverage and three standalone example paths.

Actual Codex 0.158.0 access on C:/codex passed in both modes using the user-approved gpt-6-sol / max override. gpt-6.1-sol was unsupported on this login. Existing provider configuration and rules are inherited; no new account, key or paid service is provisioned.

Engineering tests and access probes do not establish improved construction behavior. The qualification matrix is six cases × four conditions × five repeats = 120 complete attempts, with simulated users, actual artifact/run checks, frozen resources and bounded attempts. Human trial and official-directory review remain separate gates. Current evidence and limitations: [delivery status](docs/delivery-status.md), [evaluation protocol](evals/README.md).

## Install

Latest published version remains [0.1.0-alpha.4](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4); its tag and assets are immutable. It has the earlier five-Skill suite, not the new 0.2 capabilities.

For that published version:

~~~powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
~~~

For a local 0.2 candidate, build the plugin ZIP and register its extracted local marketplace as described in [upgrade instructions](docs/upgrade-0.2.md). Open a new Codex conversation and select agent-worksystem-builder:building-agent-worksystems. Python runtime: Python 3.11+; reuse a compatible project environment and run the bundled doctor. Keep business/build data outside the plugin cache.

The optional local MCP retains its eight materials tools and two resources. Broader construction uses native Skills/CLI; MCP is not enabled automatically. A Skill-suite ZIP is not a plugin-upload ZIP, and the Python wheel does not include Skills. ChatGPT import and official listing are not confirmed.

[Architecture](docs/plugin-architecture.md) · [Runtime interfaces](docs/interfaces.md) · [Bilingual sharing text](docs/share.md) · [Issues](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/issues)
