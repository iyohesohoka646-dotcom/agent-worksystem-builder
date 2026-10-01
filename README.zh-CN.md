# Agent Worksystem Builder

**构筑可检查、可核验、可恢复的智能体工作系统。**

**Build repeatable agent workflows you can inspect, verify and resume.**

[English](README.md) · [简体中文](README.zh-CN.md) · [快速上手](docs/quickstart.md) · [下载 alpha.4](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4)

[![运行时与分发 CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)

Agent Worksystem Builder 是一个实验性的 **Codex 插件**，用于把重复任务构筑为有证据、能复核、可恢复的本地工作流。一个总控按需组合四个小 Skill，分别负责需求、架构、受控执行和核验；它们共享 Python CLI、项目状态和可选的本地 MCP。

先从随包的材料分类示例开始：保留源文件，输出可追溯的 JSONL/CSV，遇到需要人工判断的条目保存复核请求，再从断点继续。其他领域需要自己的任务契约与核验规则。

## 为什么使用它？

- **复用已有工具。** 给可用的解析器或脚本增加编排，保留原有实现。
- **让变更可检查。** 记录目标、文件归属、候选改动和实际证据。
- **让人工决定明确。** 保存复核请求，不代替用户编造批准。
- **从项目状态恢复。** 跨进程、跨会话保留运行编号与检查点。

适合重复材料处理、文档分类，以及需要人工复核和恢复的小型本地流程。普通的一次性事实问答无需引入工作系统。

## 快速安装

在支持插件 marketplace 的 Codex 中执行：

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

开启新会话，选择 `agent-worksystem-builder:building-agent-worksystems`，可以这样提出任务：

> 把这些 Markdown 文件构筑成一个本地工作流：保留原文，输出可追溯的 JSONL 和 CSV，争议分类交给我复核，并支持断点恢复。保持离线，先检查现有脚本。

插件提供构筑流程指引，不会自行启动后台服务。Python 运行时需要 Python 3.11+ 及随包声明的依赖；优先复用兼容的项目环境。随包的 doctor 可检查环境是否就绪，不初始化目标项目。本地规则示例不需要模型 API key；使用模型后端时，需要自己的提供商访问权限。

### Git 连接受限怎么办？

从 [发布页面](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4) 下载插件 ZIP，再执行：

```powershell
Expand-Archive ./agent-worksystem-builder-0.1.0-alpha.4-plugin.zip ./awb-plugin
codex plugin marketplace add ./awb-plugin/agent-worksystem-builder
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

想先运行一个不调用模型、结果可复现的 CLI 示例，参见 [双语快速上手](docs/quickstart.md)。

## 一个总控，四个小 Skill

| 入口 | 职责 | 示例任务 |
|---|---|---|
| `building-agent-worksystems` | 总控：选择模块、传递上下文、衔接结果 | “构筑或恢复这个流程。” |
| `awb-clarify` | 需求、约束和验收样例 | “澄清目标，先不要运行。” |
| `awb-design` | 架构选型、现有脚本及 Skill/MCP 集成 | “保留解析器，增加可恢复编排。” |
| `awb-execute` | 已授权改动与有界执行 | “实施这个限定范围的改动并记录运行。” |
| `awb-verify` | 独立核验、人工复核和安全恢复 | “只检查这个断点，不修改文件。” |

新建系统可按 `澄清 → 设计 → 执行 → 核验` 衔接，已有阶段可以跳过。窄任务在完成当前结果后停止。小模块可以直接调用，但必须与整个套件一起安装；这些指令模块不会自动创建子智能体。

[交接契约](skills/building-agent-worksystems/references/module-contract.md) 传递同一个项目、目标版本、权限、预算、编号及证据。共享运行时和参考文件只保留一份；已初始化项目以 SQLite 为权威状态。

## 最终能检查什么？

| 产物 | 能回答的问题 |
|---|---|
| 版本化目标与决策 | 系统要做什么，为什么发生变更 |
| 候选文件清单与执行记录 | 哪些受控文件改变，实际执行了什么 |
| 带哈希的 JSONL/CSV 材料输出 | 结果来自哪些源材料 |
| 保存的复核请求与断点 | 哪些条目等待人工决定，从哪里继续 |
| 独立核验的证据 | 哪些检查通过、失败或仍未知 |

项目数据放在插件缓存目录之外。执行结束、独立任务核验通过、真实用户目标达成分别判断。

## 应该下载哪个文件？

全部附件见 [alpha.4 发布页面](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4)。

| 下载文件 | 用途 |
|---|---|
| `agent-worksystem-builder-0.1.0-alpha.4-plugin.zip` | 完整 Codex 插件，可通过本地 marketplace 安装 |
| `agent-worksystem-skills-0.1.0-alpha.4.zip` | 其他 Skill 主机使用的完整五目录套件，须一起复制 |
| `agent_worksystem_builder-0.1.0a4-py3-none-any.whl` | 独立 Python 运行时 |
| 两份 `.manifest.json` | 归档 SHA256 与逐文件完整性检查 |

Skill 套件 ZIP 不能作为单插件归档上传；wheel 不包含 Skills 或开发评测器。插件 ZIP 已准备好用于官方提交，但这不代表已获官方目录批准或已通过 ChatGPT 网页导入。

## 可选 MCP 与外部复用

可选的本地 stdio MCP 在启动时绑定项目，为材料规则示例提供八个结构化工具和两个资源，共用 CLI 的状态、断点与核验器。它不提供人工批准、任意命令执行或操作系统沙箱，也不会自动启用。

参见 [MCP 安装与连接](skills/building-agent-worksystems/references/mcp.md)、[集成与复用指南](skills/building-agent-worksystems/references/integrations-and-skills.md) 和 [架构说明](docs/plugin-architecture.md)。模型后端及其他构筑操作继续通过现有 Skill/CLI 接口进行。

## 当前状态与边界

已发布版本为 **0.1.0-alpha.4**，Python 包版本为 **0.1.0a4**。[发布源码的 CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/runs/36823390117) 在 Windows 通过 108 项测试，在 Linux 通过 107 项、跳过 1 项平台限定检查。原生 Codex 0.158.0 安装发现并启用了全部五个 Skill；五个发布附件重新下载后的 SHA256 均与本地一致。

这些检查覆盖运行时、分发和有限路由场景，未证明真实模型效果提升或真实用户材料验收。Codex/Ollama/Claude 的真实推理兼容性、当前会话的 MCP 连接、ChatGPT 网页导入和官方目录批准仍需分别验证。当前为 alpha，不承诺后台持续运行或操作系统隔离。完整证据与限制见 [交付状态](docs/delivery-status.md)。

已发布的版本标签与下载附件保持固定，主分支文档可独立更新。双语版本介绍见 [发布说明](docs/release-alpha4.md)。

## 深入了解、分享与反馈

- [快速上手与预期输出](docs/quickstart.md)
- [可直接复制的双语推广文案](docs/share.md)
- [运行时接口](docs/interfaces.md) 与 [评测协议](evals/README.md)
- [问题反馈与支持](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/issues)

反馈时请附版本、主机与操作系统、预期结果、实际结果，以及脱敏的最小复现。不要在公开问题中上传凭据或私人材料。

数据处理见 [PRIVACY.md](PRIVACY.md)，使用与许可见 [TERMS.md](TERMS.md)。项目尚未指定开源许可证；公开可见不授予广泛的再分发或修改许可。
