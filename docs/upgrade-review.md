# 0.2 verification and qualification / 验证与资格审查

**Engineering and native-plugin verification passed on 2026-10-01.** This report separates verified plugin behavior, bounded access/fault checks and the remaining whole-system comparison.

**2026-10-01 工程与原生插件验证通过。** 本报告分开记录已验证的插件行为、有界访问及故障检查，以及尚在进行的完整系统对照。

## Verified checks / 已通过检查

| Check / 检查 | Result / 结果 |
|---|---|
| Full Windows regression / Windows 完整回归 | 165 passed / 165 项通过 |
| Cross-platform regression and packaging / 跨平台回归与打包 | Windows and Linux CI passed / Windows、Linux CI 通过 |
| Public installation ZIP / 公开安装包 | SHA256 matches the manifest; 79 files; no target application, HTML interface or evaluation jobs / SHA256 与清单一致，79 个文件，不含目标应用、HTML 界面或评测任务 |
| Existing native installations / 现有原生安装 | Two homes match the ZIP; six enabled Skill entrypoints each; doctor passed, target state and host settings unchanged / 两处安装与 ZIP 一致，各有六个已启用入口，依赖检查通过，目标状态与宿主设置未改动 |
| Credential-free fresh installation / 无凭据全新安装 | Native marketplace registration, installation and six-Skill discovery passed / 原生 marketplace 注册、安装及六模块发现通过 |
| Actual dual-mode access / 真实双模式访问 | Codex 0.158.0, gpt-6-sol/max: exec and app-server completed / exec 与 app-server 均完成真实推理 |
| Deterministic artifact fault checks / 确定性产物故障检查 | Six passed: wrong-result rejection, output binding or explicit rejection, explicit backend failure, no retry in each fault phase, and source preservation; zero model calls / 六项通过，覆盖错误结果拒绝、输出绑定或明确拒绝、后端失败、两阶段无重试、原文件保持，模型调用为零 |

Public CI evidence: [runtime and distribution checks](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml). Local raw receipts are preserved in reports/verification-refresh-20261001-runtime.xml, reports/plugin-verification-refresh-20261001-2.json, reports/host-preflight-verification-20261001/receipt.json and reports/fault-verification-20261001/receipt.json. Raw host paths, logs and configuration snapshots are excluded from public source.

公开工程证据见 [CI](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml)。本地回执保留完整检查结果；原始日志、配置快照和宿主路径不随公开源码分发。

## Reviewed corrections / 已核验修正

These corrections are covered by failing-before-fix regressions and the fresh full suite.

下列修正由修复前失败的回归用例及本轮完整测试共同覆盖。

| Finding / 发现 | Implemented correction / 修正 | Regression evidence / 回归 |
|---|---|---|
| Embedded profile bypassed review / 架构内配置绕过审批 | Inherit selected profile; reject conflicts; bind evidence / 继承配置、拒绝冲突、绑定证据 | test_architecture_cannot_bypass_its_embedded_pending_intelligence_profile; test_omitted_cycle_profile_is_inherited_from_architecture_and_bound |
| Resume stopped on old quota; external quota was lost / 恢复重复旧额度失败、外部额度错误丢失 | Keep old cells; launch only unattempted cells; preserve structured errors / 保留旧尝试，仅推进未尝试项，保留环境错误 | test_resume_skips_old_quota_checkpoint_and_only_launches_unattempted_jobs; test_external_grader_model_quota_is_an_environment_checkpoint |
| Streaming extended deadlines / 持续事件绕过截止时间 | Explicit remaining-time checks and owned turn interruption / 显式检查剩余时间并中断自有回合 | test_streaming_events_do_not_extend_the_wall_clock_deadline |
| Effective config was not frozen / 实际配置未冻结 | Fingerprint config, controller, Python and dependencies / 冻结有效配置、控制器、Python及依赖 | test_effective_host_configuration_changes_invalidate_frozen_matrix |
| Unrelated service credited to new startup / 无关服务可能被记作新启动 | Reject pre-existing endpoints; verify owned instance token / 拒绝已运行端点，核验自有实例 | test_startup_cannot_claim_an_already_running_unrelated_service |
| Zero interactive budget ignored / 交互零调用预算被忽略 | Reserve budget before transport start / 接入前占用预算 | test_interactive_zero_call_budget_stops_before_transport_start |

## Whole-system comparison / 完整系统对照

- **Progress:** 14 finished attempts and one interrupted attempt are retained out of the planned 120. None is silently retried or regraded. / **进展：** 计划 120 次，目前保留 14 次已结束尝试与 1 次中断，不自动重试或改分。
- **Frozen environment:** the latest read-only audit detects host-configuration drift. Historical attempts remain bound to their original snapshots; the old matrix cannot resume with current host settings. / **冻结环境：** 最新只读审查发现宿主配置漂移，历史尝试保留原快照绑定，旧矩阵不能直接沿用当前宿主设置续跑。
- **Budget evidence:** attempts 2 and 7 exceeded the wall-clock budget; attempt 4 exceeded the observed change-cycle budget. These results stay failed. / **预算证据：** 第 2、7 次尝试超过墙钟预算，第 4 次超过可观察变更轮次预算，均保留失败结果。
- **Output evidence:** the frozen workbench grader does not establish node-output binding by itself. Independent copied-artifact checks cover rejection and failure behavior for the inspected artifact; other artifacts require their own evidence. / **输出证据：** 冻结工作台评分器不能独立证明节点输出绑定；产物副本检查验证了被检对象的拒绝与失败行为，其他产物分别核验。
- **Acceptance:** representative multi-component, multi-work-unit system acceptance remains open. The local workbench is a transport/recovery fixture with no project model or cross-task scheduler. / **验收：** 代表性多组件、多工作单元系统验收尚未完成，局部工作台仅为接入与恢复样例，未包含项目模型或跨任务调度。
- **Claims:** the incomplete comparison does not establish general construction improvements. Other hosts/models, ChatGPT web import and official-directory review need separate checks. / **结论：** 未完成的对照不支持普遍构筑效果提升，其他宿主／模型、ChatGPT 网页导入与官方目录审核分别验证。

Whole-goal coverage, multiple components/launch points, independent business state and drift invalidation are exercised by test_multiple_components_tasks_and_launches_need_whole_goal_coverage. This is engineering evidence, not a cross-domain effectiveness benchmark.

整体目标覆盖、多组件与启动点、独立业务状态及漂移后验收失效，由 test_multiple_components_tasks_and_launches_need_whole_goal_coverage 实际执行检查；该证据支持工程机制，不等同于跨领域效果基准。

## Reproduce checks / 复现检查

Run from the source checkout with a compatible project-local environment. Use new output paths so earlier evidence is retained.

在源码检出目录使用兼容的项目环境运行，输出使用新路径，保留既有证据。

~~~powershell
python -X utf8 -m pytest -q -p no:cacheprovider
python -X utf8 tools/plugin_smoke.py
python -X utf8 tools/host_preflight.py --model gpt-6-sol --output ./reports/access-fresh
python -X utf8 tools/qualify_systems.py --matrix ./reports/system-matrix-0.2-qualified-input --output ./reports/qualification-fresh.json
~~~

The access probe makes two bounded real inference calls on the configured account. The read-only qualifier does not run construction or approve a release. Artifact fault probes operate on copies with simulated nodes.

访问预检在现有账户上执行两次有界真实推理；只读资格检查不启动构筑或批准发行，产物故障检查在副本上使用模拟节点。原始计划、alpha.4 标签与附件保持不变；官方审核单独记录。
