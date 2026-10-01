# 0.2 review and acceptance ledger / 审查与验收记录

Candidate remains unreleased. Engineering regressions, actual model access, fixture matrix outcomes and representative system-level user acceptance are separate evidence levels.

候选版仍未发布。工程回归、真实模型访问、受控矩阵及系统级人工验收分别记录，不互相替代。

## Reviewed fixes / 已审查修正

The fresh read-only review reproduced six important issues. Failing regression tests were added before fixes:

| Finding / 发现 | Implemented correction / 修正 | Regression evidence / 回归 |
|---|---|---|
| Embedded profile bypassed review / 架构内配置绕过审批 | Inherit selected profile; reject conflicts; bind evidence / 继承配置、拒绝冲突、绑定证据 | test_architecture_cannot_bypass_its_embedded_pending_intelligence_profile; test_omitted_cycle_profile_is_inherited_from_architecture_and_bound |
| Resume stopped on old quota; external quota was lost / 恢复重复旧额度失败、外部额度错误丢失 | Keep old cells; launch only unattempted cells; preserve structured errors / 保留旧尝试，仅推进未尝试项，保留环境错误 | test_resume_skips_old_quota_checkpoint_and_only_launches_unattempted_jobs; test_external_grader_model_quota_is_an_environment_checkpoint |
| Streaming extended deadlines / 持续事件绕过截止时间 | Explicit remaining-time checks and owned turn interruption / 显式检查剩余时间并中断自有回合 | test_streaming_events_do_not_extend_the_wall_clock_deadline |
| Effective config was not frozen / 实际配置未冻结 | Fingerprint config, controller, Python and dependencies / 冻结有效配置、控制器、Python及依赖 | test_effective_host_configuration_changes_invalidate_frozen_matrix |
| Unrelated service credited to new startup / 无关服务可能被记作新启动 | Reject pre-existing endpoints; verify owned instance token / 拒绝已运行端点，核验自有实例 | test_startup_cannot_claim_an_already_running_unrelated_service |
| Zero interactive budget ignored / 交互零调用预算被忽略 | Reserve budget before transport start / 接入前占用预算 | test_interactive_zero_call_budget_stops_before_transport_start |

Latest full engineering run passed 165 tests, including qualification/scope/fault-probe and installation/development-bundle separation. Fresh wheel install/import/contracts/CLI passed; native isolated-home and actual user-home installations, cache bytes and six-Skill discoveries passed. Neither establishes a behavioral improvement or human qualification.

## Actual access / 真实访问

User-approved gpt-6-sol/max passed actual exec and app-server on the same C:/codex 0.158.0. The rejected gpt-6.1-sol attempt remains. Latest receipt: reports/host-preflight-0.2-current/receipt.json. No credentials were copied or new services opened; only per-call model overrides were used. A changed config fingerprint was detected before matrix launch; older receipts and setup checkpoints remain.

## Qualification boundaries / 资格边界

- The 120-attempt matrix is checkpointed for user-requested plugin installation, not completed or qualified. Fourteen attempts finished; the fifteenth is preserved as interrupted with its original running receipt and unavailable final metrics. Keep all failed, cancelled, timed-out and environment outcomes. Setup/isolation failures stay separate from construction attempts; no attempted cell is silently retried. Recheck frozen bindings/isolation before resume; do not treat changed instructions/cache paths as the original context.
- The frozen workbench grader has an output/node-call binding gap. The independent read-only qualifier exposes it; do not silently change grading mid-matrix. Wrong-node-result and broader recovery/resource/semantic checks remain required.
- A workbench attempt reached 900 seconds; observed receipt time includes cleanup beyond the deadline. Retain the overrun for hard-constraint review, without subtracting it or converting failure to pass.
- Another workbench attempt observed a ninth completed code-change batch before interruption. The harness records that budget breach rather than reporting eight. Its frozen guard stops subsequent work; these observations remain unresolved strict-budget qualification gaps.
- A separate deterministic fault probe ran the second attempt's copied artifact: six checks passed, including wrong-result rejection, binding/explicit rejection, backend failure, no retries and source preservation. Zero model calls; the original timed-out construction stays failed. Other artifacts require their own checks.
- The user rejected the line-count human trial as too narrow. The local dual-mode sample has no project model or cross-task scheduler. No human qualification is granted; representative multi-component/multi-work-unit system acceptance remains open.
- test_multiple_components_tasks_and_launches_need_whole_goal_coverage runs several ordinary components/launch points, retains multiple projects/tasks in independent business data and invalidates delivery after drift. It is a runtime regression, not a generality benchmark.
- Current-version Linux CI, other hosts/models, ChatGPT import and official-directory access/scans/review are not established by local Windows checks.

发布受完整对照、硬约束、完整目标与系统级人工验收约束，不把示例范围、局部候选通过或测试数量写成广义产品效果。alpha.4 标签及附件保持原样，官方审核单独记录。
