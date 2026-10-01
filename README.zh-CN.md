# Agent Worksystem Builder · 智能系统构筑器

通过持续对话、自适应探索、实现与证据，构筑用户需要的完整智能系统。

[简体中文](README.zh-CN.md) · [English](README.md) · [快速上手](docs/quickstart.md) · [升级与回退](docs/upgrade-0.2.md)

[![工程与分发检查](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)

这是一个实验性 Codex 插件，目标是自动设计、编排、实现并持续改进**完整智能系统**。持续需求与决策 grill 保留原始目标；“评估—创造—验证—决策”循环探索候选、实施已授权变更、检查真实软件，并将重大取舍交还用户讨论。

## 三层职责，开放架构

| 层次 | 职责 |
|---|---|
| 构筑层 | 由你的 Codex 原生会话理解目标、探索方案、建设与验证。 |
| 目标系统整体架构 | 按任务组合普通程序、界面、服务、存储、调度、外部接口与部署方式。 |
| 可选智能层 | 配置交互式及非交互式参与，编排模型、Agent、Skill、插件、MCP、工具、上下文、权限与预算。 |

目标系统在 Builder 会话关闭后仍能运行，并拥有独立业务数据。无需强制采用 AWB 的 DAG、SQLite 或总控 Agent。确定性程序足够时，交付可以不包含智能层。

## 一个总控，五个职责模块

| Skill | 职责 |
|---|---|
| building-agent-worksystems | 统筹完整目标的建设循环与恢复，避免局部候选通过后提前结束。 |
| awb-clarify | 持续 grill：需求、未决问题、重大决策与理由；复用答案，必要时重新打开。 |
| awb-explore | 环境及资源发现、权威资料检索、架构候选、原型试验与方案比较。 |
| awb-design | 选择合适的现代程序架构，独立配置智能层。 |
| awb-execute | 执行已授权工程变更，接入有预算和权限边界的双模式智能节点。 |
| awb-verify | 核验实际程序、服务、产物与领域结果，检查整体目标覆盖及恢复。 |

模块共享版本化 ArchitecturePlan、IntelligenceProfile、ExplorationRecord 契约、原始目标和不可变证据。这些模块是可组合指令，调用它们不会自动创建多个 Agent。重大取舍需要真实用户答案。

## 可以这样开始

> 构筑任务工作台，包含界面、服务与持久任务数据。交互式 Codex 讨论任务，非交互式 Codex 执行任务，普通程序核验真实输出。会话关闭后仍可使用，并交付启动、配置、恢复与扩展说明。

> 保留现有程序的接口和回归测试，探索哪些位置适合智能参与，比较候选方案，再实施有依据的改造。新安装、凭据、费用或数据去向变化先和我讨论。

> 构筑确定性 CSV 汇总工具。普通代码足够时，不额外引入模型调用、Agent 或常驻服务。

材料分类继续作为一个领域示例，产品设计空间不限于材料处理或重复流水线。

系统级目标可以包含多个项目、多个任务类型、组件依赖、事件或调度及多处智能参与，具体组织方式通过探索和决策确定。参见[系统级构筑说明](docs/system-level-construction.md)。`examples/task-workbench` 只测试局部双模式与恢复，尚无项目层或跨任务调度，不能替代完整产品或系统级人工验收。

## 能力与验证范围

0.2.0-alpha.1 当前为**尚未发布的候选版**。已加入持久契约、持续 grill 与探索、重大决策门槛、受控写入、app-server 会话／审批／事件、exec 结构化结果、可注册验证器、整体目标覆盖，以及三类独立示例路径。

同一个 C:/codex、Codex 0.158.0 宿主已通过 gpt-6-sol / max 的双模式真实访问；这是用户批准的模型覆盖，未修改全局配置。gpt-6.1-sol 在该登录下不受支持。复用现有提供商配置和规则，不自动开通账户、密钥或收费服务。

工程测试和访问预检不能证明构筑效果提升。完整对照要求六个场景、四个条件、各五次，共 120 次完整构筑尝试，固定宿主与资源、保留所有失败，并检查实际运行结果。模拟用户明确标注；真实人工试用、ChatGPT 导入及官方目录审核分别记录。详见[交付状态](docs/delivery-status.md)和[评测协议](evals/README.md)。

## 安装与使用

最新已发布版本仍为 [0.1.0-alpha.4](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4)，旧标签及附件保持不变。该版本包含旧五模块套件，不包含本轮全部升级。

~~~powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
~~~

本地候选版按[升级说明](docs/upgrade-0.2.md)构建插件 ZIP，解压并注册本地 marketplace；开启新会话，选择 agent-worksystem-builder:building-agent-worksystems。Python 运行时需要 3.11+ 及随包依赖，优先复用兼容项目环境并运行 doctor。目标业务数据和建设记录放在插件缓存之外。

可选本地 MCP 仍提供八个材料工具和两个资源；广义建设通过原生 Skill／CLI 完成，不自动启用 MCP。Skill 套件 ZIP 与插件上传 ZIP 用途不同，wheel 不包含 Skill。ChatGPT 导入与官方上架尚未确认。

[架构说明](docs/plugin-architecture.md) · [运行接口](docs/interfaces.md) · [双语推广文案](docs/share.md) · [问题反馈](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/issues)
