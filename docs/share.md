# Share the project / 分享项目

[English overview](../README.md) · [中文首页](../README.zh-CN.md) · [Quick start / 快速上手](quickstart.md)

Use the copy below to introduce the project. These are publication-ready drafts, not posts sent to any community. Keep the alpha status and current validation boundaries when shortening them.

以下文案可直接用于介绍项目，尚未代发到任何社区。缩写时请保留 alpha 状态和实际验证范围。

## One sentence / 一句话

Agent Worksystem Builder is a Codex plugin for building local agent workflows with explicit goals, inspectable changes, saved human review and recoverable execution.

Agent Worksystem Builder 是一个 Codex 插件，用明确目标、可检查变更、保存的人工复核与可恢复执行，构筑本地智能体工作流。

## Short announcement — English

Meet **Agent Worksystem Builder**, an experimental Codex plugin for repeatable workflows you can inspect, verify and resume.

One coordinator composes four focused Skills: clarify requirements, choose architecture, execute scoped changes, and verify or recover. They share one Python runtime and project state. Start with document triage: preserve source files, export traceable JSONL/CSV, keep human decisions explicit, and continue from saved checkpoints.

The alpha.4 release includes the plugin, a complete portable Skill suite and a Python wheel. Release-source Windows/Linux CI passed, and native Codex discovered all five Skills. Optional local MCP is opt-in. Real-model improvement and real-user acceptance are not established.

Project: https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder

Quick start: https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/blob/main/docs/quickstart.md

## 中文简短介绍

**Agent Worksystem Builder** 是一个实验性的 Codex 插件，让重复工作有目标、有证据，能复核、可恢复。

一个总控按需组合四个小 Skill：澄清需求、选择架构、实施受控改动、核验与恢复，共用一份 Python 运行时和项目状态。先从文档分类示例开始：保留原文，输出可追溯的 JSONL/CSV，争议条目由人决定，再从保存的断点继续。

alpha.4 提供插件、完整可移植 Skill 套件和 Python wheel。发布源码已通过 Windows/Linux CI，原生 Codex 已发现全部五个入口；本地 MCP 按需启用。真实模型效果提升与真实用户验收仍需验证。

项目：https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder

上手：https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/blob/main/docs/quickstart.md

## Show, then explain / 演示后再解释

1. Run the [local synthetic walkthrough](quickstart.md) and show its report. / 运行本地合成示例并展示报告。
2. Explain why the first candidate failed and how independent labels exposed it. / 说明首个候选为何失败、独立标签如何发现问题。
3. Show the saved review, simulated answer and fresh-process resume. / 展示保存的复核请求、模拟答案和新进程恢复。
4. Show the corrected result and distinguish local acceptance from real-user acceptance. / 展示修正结果，区分本地候选接受与真实用户验收。

Describe the demo as synthetic and its reviewer as simulated. Do not present it as a model benchmark or a real user's endorsement. Do not describe the optional MCP as universal automation, a hosted service or a sandbox.

明确说明合成材料与模拟复核者，不将示例包装成模型基准或真实用户背书。可选 MCP 不应被宣传为通用自动化、托管服务或沙箱。

## Useful feedback / 有价值的反馈

Ask for a small, sanitized task, the expected output and the missing step. A reproducible issue is more useful than an unqualified success claim. No open-source license is designated; sharing a project link does not change the [use and licensing terms](../TERMS.md).

征集小型脱敏任务、预期输出和欠缺的步骤，可复现问题比无证据的成功宣称更有用。项目尚未指定开源许可证；分享项目链接不改变 [使用与许可说明](../TERMS.md)。

Repository topics and the overview follow GitHub's [README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) and [topic guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics). These help describe and categorize the project; they do not promise traffic, rankings or adoption.

仓库首页和主题设置参考 GitHub 的说明，用于描述与分类项目，不承诺流量、排名或用户增长。
