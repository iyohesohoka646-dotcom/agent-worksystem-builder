# Intelligent-system builder upgrade / 智能系统构筑器升级

This is the approved 0.2.0-alpha.1 implementation scope. The original creation plan and alpha.4 release remain unchanged.

本轮依据用户批准的升级计划执行，保留原始创建计划及 alpha.4 标签、附件。材料分类只是示例。

## Construction contract / 构筑契约

Builder runs in a native Codex conversation. The target application chooses ordinary program architecture and owns its business state. Its optional intelligence layer independently chooses interactive app-server, noninteractive exec, models, Skills, plugins, MCP, context, permissions and budgets. AWB's state journal, optional graph executor and SQLite are construction facilities, not a mandatory target architecture.

构筑层由原生 Codex 会话承载；目标系统整体架构包含普通程序、界面、服务、存储、调度、外部接口与部署；智能层按需编排交互和非交互参与及资源。常规建设在已约定权限和预算内推进，重大取舍返回用户 grill。局部候选通过不能代替整体目标达成。

## Stages / 实施与独立验收

1. Goal retention and versioned ArchitecturePlan, IntelligenceProfile, ExplorationRecord; existing state and CLI compatibility.
2. Persisted grill, adaptive environment/documentation/prototype/comparison exploration, answers, evidence and reopened decisions.
3. Independent target architecture and project-scoped intelligence configuration; resource provenance/version/license/compatibility and consequential decisions.
4. Local app-server sessions/approvals/events and exec structured execution; preserve existing provider config and applicable rules.
5. Registered program, service, artifact and domain verification, goal coverage, independent launch/dependencies/recovery/extensions.
6. Cross-type real builds and full frozen, matched behavior qualification; truthful bilingual docs, packaging, upgrade/rollback and gated release.

## Qualification / 评测与发布门槛

Three families: new task workbench, intelligence enhancement of an existing project, pure deterministic program. Each has one development and one holdout case. Conditions: no dedicated Skill, generic engineering rules, frozen alpha.4, current suite; five repeats each = 120 full construction attempts. Scripted users are labeled simulated; representative actual human use remains a separate gate.

Freeze C:/codex, Codex 0.158.0, gpt-6-sol / max (user-approved per-call override; base configuration unchanged) and identical permissions/resources. Verify real access first. Each attempt: at most 30 host turns, eight construction cycles and 900 seconds; no hidden retries. Preserve failed/cancelled/timed-out/environment outcomes and checkpoint insufficient quota. Inspect running software and actual artifacts; unknown metrics stay null. Never label an incomplete matrix complete. Hard constraint violations block release; improvement claims require actual comparisons.

Publish 0.2.0-alpha.1 under the existing repository/plugin identity only after acceptance. Official directory review is independent. Do not create paid services or license grants.

## Execution ledger / 执行记录

- 2026-10-01: clean checkout at 7cb2552, feature branch `feat/intelligent-system-builder`; original source plan retained. Implementation inline with a fresh final review.
- Ruling: work in the user's named checkout on a feature branch; do not create another worktree without their preference. This keeps the project location and existing Python environment intact.
- Stage 1 RED: eight tests fail on absent contract schemas/state/CLI and missing persisted exploration.
- Development Skill baseline: independent agent designed the standalone workbench using alpha.4; observed adapter and materials-only runtime gaps. No inference was called. This baseline is not a qualification attempt or proof of Skill improvement.
- Stage 1–5 engineering checks: versioned contracts, persisted exploration, review gates, general verifiers, whole-goal coverage, dual-mode transport and three standalone example paths are implemented and focused tests pass. Real intelligence is assessed separately.
- Access gate: both interfaces rejected gpt-6.1-sol with account/model unsupported (400). User explicitly requested trying gpt-6-sol on the same C:/codex host; override only the model and retain max/base config, with a separate preflight receipt and no global edits.
- Alternate preflight: gpt-6-sol/max passed exec (22.391 s) and app-server (9.75 s). Freeze this same effective model for every condition.
