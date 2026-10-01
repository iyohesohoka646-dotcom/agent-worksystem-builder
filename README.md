<p align="center">
  <img src="assets/icon.svg" width="80" height="80" alt="Agent Worksystem Builder logo">
</p>

<h1 align="center">Agent Worksystem Builder</h1>

<p align="center">From an idea to a complete intelligent system — inside Codex.</p>

<p align="center">
  English · <a href="README.zh-CN.md">简体中文</a> · <a href="#get-started">Get started</a> · <a href="docs/quickstart.md">User guide</a>
</p>

[![Runtime and distribution CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)

**Describe the system you want. Explore the choices. Build and verify it with Codex.**

Agent Worksystem Builder (AWB) is a Codex plugin for designing, orchestrating, implementing and improving complete intelligent systems through ongoing conversation. It connects requirements, software architecture and optional intelligence orchestration in one construction process — from ordinary programs, interfaces and services to models, agents, Skills, plugins and MCP.

Experimental preview: **0.2.0-alpha.2**. A dedicated plugin-upload archive and a self-contained portable Skill are now available. See [installation packages](docs/distribution.md) and [validation scope](docs/delivery-status.md).

## Why AWB?

- **Keep the whole goal in view.** Revisit requirements and consequential decisions as new evidence appears, and check the complete goal before delivery.
- **Explore before committing.** Discover existing resources, research alternatives and try prototypes; adapt the search to the task, uncertainty and budget.
- **Choose architecture that fits.** Compose software and intelligence separately. Your target owns its runtime and data; use deterministic code when AI adds no value.

## Get started

Install in Codex:

~~~powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref main
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
~~~

Open a new Codex conversation, select `agent-worksystem-builder:building-agent-worksystems` and describe your goal. Everything starts in that conversation; no AWB website or Builder service is required.

> My goal is: &lt;describe your workflow, existing project or system idea&gt;.
>
> Use AWB to discover existing resources, discuss key requirements and explore architecture choices. Then implement and verify the complete system. Preserve existing interfaces and unrelated changes; discuss major trade-offs with me.

Prefer a ZIP? [Plugin upload ZIP](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/raw/refs/heads/main/packages/0.2.0-alpha.2/agent-worksystem-builder-0.2.0-alpha.2-codex-import.zip) · [Portable Skill ZIP](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/raw/refs/heads/main/packages/0.2.0-alpha.2/agent-worksystem-builder-0.2.0-alpha.2-skill.zip) · [Installation instructions](docs/distribution.md). Upload acceptance is tracked separately from native CLI installation. The portable Skill uses your current agent's tools; Python 3.11+ is needed only for the shared runtime.

## How it works

**Discuss the goal → explore options → design → implement → verify → decide what comes next.**

Requirements grilling continues throughout the work: reuse earlier answers, investigate discoverable facts and return consequential choices to you. The evaluate–create–verify–decide loop can revisit a design when evidence, goals or budgets change.

One coordinator composes five focused Skills: **clarify, explore, design, execute and verify**. Together they address the target's overall software architecture and its optional intelligence layer, including interactive and noninteractive participation, models, resources and permissions. See [architecture and module responsibilities](docs/plugin-architecture.md).

## Build for your workflow

Possible starting points — the architecture follows your needs:

- **A new system:** coordinate multiple projects, task types, data flows, services and intelligent participation points.
- **An existing application:** preserve its interfaces and tests, and add intelligence where exploration shows it is useful.
- **A focused tool:** deliver a standalone program without unnecessary model calls, agents or services.

The design space is open. [System-level construction](docs/system-level-construction.md) explains how these pieces fit together.

## Explore the project

- **Use it:** [installation and first conversation](docs/quickstart.md) · [upgrade and rollback](docs/upgrade-0.2.md)
- **Understand it:** [plugin architecture](docs/plugin-architecture.md) · [runtime interfaces](docs/interfaces.md)
- **Check the evidence:** [delivery status and limitations](docs/delivery-status.md) · [evaluation protocol](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/blob/main/evals/README.md) · [engineering CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)
- **Join in:** [report a problem or propose an idea](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/issues) · [bilingual project introduction](docs/share.md)
