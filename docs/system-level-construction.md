# System-level construction / 系统级构筑

## Product scope / 产品范围

The plugin's controller lives in a native Codex conversation. It constructs the user's whole target system: ordinary software architecture, multiple components and work units, and optional intelligence at appropriate participation points. Interactive discussion and noninteractive execution are participation modes, not the complete system architecture. A target may have many task types, cooperating services, event handlers, scheduled jobs and independent deterministic components. Choose their architecture from requirements; do not prescribe one global Agent, one task, a chat UI or an AWB graph.

插件总控由原生 Codex 会话承载，构筑对象是用户需要的整个系统。普通程序的结构、数据生命周期、界面、外部接口和部署决定整体组织方式；多个智能参与点可各自包含模型、工具、Skill、插件、MCP、上下文及交接安排。问答、单次执行、任务队列都只是设计空间中的局部。允许多个任务类型和工作单元，允许确定性组件承担主要职责；不预设一个全局 Agent 或固定流程。

## Example system brief / 系统级示例需求

The following is an illustrative design brief, **not a delivered application or a fixed template**:

以下只说明构筑范围，**尚未交付该应用，也不作为固定产品模板**：构筑一个可扩展的项目交付系统，管理多个项目，每个项目拥有整体目标、多个任务及依赖、工件和验收条件。普通程序负责数据一致性、任务状态、触发、依赖与恢复；交互智能参与需求讨论和重大决策，非交互智能在合适的实现、资料处理及验证环节参与。用户可以替换模型和资源；插件构筑会话关闭后，目标系统继续运行。

| Requirement / 需求 | Architectural responsibility / 架构职责 | Acceptance / 验收 |
|---|---|---|
| Multiple projects and evolving goals / 多项目与目标变更 | Project domain model and durable storage / 项目领域模型与持久存储 | Changes retain history and invalidate affected approvals / 保留历史，受影响审批失效 |
| Multiple work types and dependencies / 多工作类型与依赖 | Application services, task handlers and suitable scheduling / 应用服务、处理器与合适调度 | Dependent work is released only after actual prerequisites / 依赖有实际证据后才推进 |
| Interactive intelligence / 交互智能 | Session/event/approval integration at selected participation points / 选定参与点的会话、事件和审批接入 | Real decisions and interruptions survive resume / 真实决策和中断可恢复 |
| Noninteractive intelligence / 非交互智能 | Bounded workers, structured results and scoped resources / 有界工作单元、结构化结果与局部资源 | Actual outputs are independently checked; errors are retained / 核验实际输出，保留错误 |
| Ordinary program verification / 普通程序验证 | Domain checks, API tests and artifact checks / 领域、接口与工件核验 | A wrong intelligent output fails even when a model call succeeds / 模型调用成功但结果错误时仍失败 |
| Independent operation and extension / 独立运行与扩展 | Target-owned startup/configuration/state and extension interfaces / 目标自己的启动、配置、状态和扩展接口 | Restart without Builder; replace a handler/resource without breaking unrelated work / 无 Builder 重启，替换组件不破坏其他工作 |

These are example responsibilities. Exploration may choose an existing framework, ordinary application code, event-driven services or another architecture. The plugin must investigate compatibility and compare candidates before committing to consequential choices. It must not turn this table into a mandatory workflow language.

表中职责由需求推导，具体架构可以复用既有框架、采用普通应用代码、事件驱动服务或其他合适方式。探索应记录环境事实、检索来源、候选、原型与淘汰原因，重大选择返回用户讨论。选择能够改变后续路线；表格不构成通用工作流语言。

## Whole-system construction sequence / 整体构筑方式

1. Preserve the original system goal and all active requirements. Inspect the existing project and available resources before asking discoverable questions. / 保留系统原始目标及全部有效需求，先探查环境和资源，再 grill 不可发现的决策。
2. Explore competing architectures and intelligence participation, choosing search/prototype methods from uncertainty and budget. / 按不确定性和预算自适应选择资料检索、资源发现、原型试验及方案比较。
3. Record components, interfaces, dependencies, launch points and requirement-linked acceptance separately from the intelligence configuration. / 分开记录整体组件、接口、依赖、启动与验收关联，以及智能参与、模型、资源和交接。
4. Implement ordinary components and intelligent participation together, in authorized bounded changes; verify actual programs and artifacts, then accept, revise or replace with reasons. / 按已授权有界变更贯通普通程序和智能参与，实际核验后决定接受、修改或替换。
5. Reconcile all requirements after each local acceptance. Deliver the independent whole system only when coverage, actual execution, recovery and real user acceptance support it. / 每次局部通过后对照全部需求，独立运行、恢复及真实用户验收有证据后才交付整体。

## Current evidence boundaries / 当前证据边界

The contracts can describe multiple components, interfaces, dependencies, entrypoints and acceptance criteria. The coordinator and modules instruct the complete construction loop; the runtime journals changes, decisions and general verification. This is not evidence that every architecture or intelligence configuration has been built successfully.

当前契约可以记录多个组件、接口、依赖、启动入口和验收项，总控与模块指令覆盖完整循环，运行时提供建设记录、决策、变更和通用核验。它们不能证明各种系统架构和智能编排已全部构筑成功；具体目标仍需真实实施与验收。

`examples/task-workbench` is a **local dual-mode/recovery engineering sample**. It stores multiple independent tasks but has no project model, dependency scheduler or system-level construction UI. Its earlier line-count defaults were removed after the user rejected the narrow trial. It must not be used as a substitute for the plugin's broad goal or representative system-level human acceptance.

`examples/task-workbench` 仅用于双模式与恢复的局部工程测试，可以保存多个独立任务，尚无项目层、跨任务依赖调度或系统构筑界面。用户指出先前试用过窄后，已撤回用它做最终人工验收的安排并删除统计行数的默认任务。后续人工验收应在原生总控中构筑真实的多组件、多工作单元系统，核验完整交付。

The frozen 120-attempt matrix tests six controlled interfaces across three families. It continues unchanged, preserves failures and is not general-architecture or adaptive-search qualification. A separate read-only audit reports evidence gaps, hard constraints, repetition stability, question burden and unmeasured metrics. Actual human use and broader semantic/resource/recovery review remain release gates.

冻结的 120 次矩阵覆盖三类任务的六组受控接口，继续保留全部结果，评分规则不随观察到的结果改变。它不能单独证明广义架构或自适应搜索能力；独立只读资格报告列出证据缺口、硬约束、重复稳定性、提问负担及未知指标，系统级人工使用与语义、资源和恢复审查仍是发布门槛。
