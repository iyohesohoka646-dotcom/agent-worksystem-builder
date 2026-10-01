# v0.1.0-alpha.4 — Modular workflows / 模块化工作流

[English overview](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder#readme) · [中文首页](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/blob/main/README.zh-CN.md) · [Quick start / 快速上手](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/blob/main/docs/quickstart.md)

## English

**Build repeatable agent workflows you can inspect, verify and resume.** Agent Worksystem Builder is an experimental Codex plugin for turning recurring tasks into local systems with explicit goals, controlled changes, saved human reviews and evidence-backed recovery.

This release introduces one coordinator and four focused Skills. They share a handoff contract, one Python runtime and the same authoritative project state. CLI/MCP execution interfaces are unchanged.

| Skill | Role |
|---|---|
| `building-agent-worksystems` | Coordinator and context routing |
| `awb-clarify` | Requirements and acceptance criteria |
| `awb-design` | Architecture and script/Skill/MCP reuse |
| `awb-execute` | Authorized changes and bounded execution |
| `awb-verify` | Independent checks, human review and recovery |

Also includes the dependency doctor, optional project-bound MCP source and artifact-based comparison tools developed in the previously local alpha.2/alpha.3 iterations. Default installation is skills-only: MCP is opt-in, and the local rules example needs no model API key.

### Install

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

Open a new session. Python execution requires Python 3.11+ and packaged dependencies. If Git access is restricted, use the plugin ZIP and the local marketplace steps in the [quick start](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/blob/main/docs/quickstart.md).

### Downloads and evidence

Use the **plugin ZIP** for Codex, the **complete five-folder Skill-suite ZIP** for other Skill hosts, or the **Python wheel** for standalone runtime use. Two manifests provide archive and per-file SHA256 checks. The suite ZIP is not a plugin-upload archive.

The [release-source CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/runs/36823390117) passed 108 tests on Windows and 107 on Linux, with one platform-specific skip. Native Codex 0.158.0 discovered all five enabled Skills; all five published assets were downloaded with matching SHA256. Linux/Windows archive member contents agree, while ZIP ordering/platform markers can change the outer checksum. This release uses the verified Windows archive.

The walkthrough uses synthetic material and a simulated reviewer. Real-model improvement, real-user acceptance, ChatGPT web import and official-directory approval remain unverified. The documentation refresh improves bilingual explanations without replacing the published tag or binaries.

## 简体中文

**构筑可检查、可核验、可恢复的智能体工作系统。** Agent Worksystem Builder 是实验性的 Codex 插件，将重复任务构筑为有明确目标、有受控变更、有保存的人工复核和恢复证据的本地系统。

本次拆成一个总控与四个小 Skill：`building-agent-worksystems` 负责路由，`awb-clarify` 澄清需求，`awb-design` 选择架构与复用工具，`awb-execute` 执行已授权改动，`awb-verify` 核验、复核与恢复。它们共用交接契约、Python 运行时与权威项目状态，CLI/MCP 执行接口保持不变。

同时公开此前 alpha.2/alpha.3 的依赖自检、可选的项目绑定 MCP 源码和实际产物比较工具。默认安装保持 skills-only，MCP 按需启用，本地规则示例不需要模型 API key。上方安装命令适用于两种语言；安装后开启新会话，Python 执行需要 3.11+ 及随包依赖，Git 受限时可用插件 ZIP 进行本地安装。

### 下载与验证

Codex 使用**插件 ZIP**，其他 Skill 主机使用须整体安装的**五目录 Skill 套件 ZIP**，独立 Python 运行使用 **wheel**。两份清单提供归档与逐文件 SHA256；Skill 套件不能作为单插件归档上传。

[发布源码 CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/runs/36823390117) 在 Windows 通过 108 项测试，在 Linux 通过 107 项、跳过 1 项平台限定检查。原生 Codex 0.158.0 已发现并启用全部五个 Skill，五个发布附件重新下载后的 SHA256 均与本地一致。Linux/Windows 包的文件内容一致，ZIP 排序和平台标记会影响整体哈希；本次附件使用已验证的 Windows 构建。

演示使用合成材料与模拟复核者。真实模型效果提升、真实用户验收、ChatGPT 网页导入及官方目录批准仍需验证。本次文档更新提供双语讲解，不替换已发布的版本标签或下载附件。
