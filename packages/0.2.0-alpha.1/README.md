# Codex plugin delivery / Codex 插件交付

[Download the plugin ZIP / 下载插件](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/raw/refs/heads/main/packages/0.2.0-alpha.1/agent-worksystem-builder-0.2.0-alpha.1-plugin.zip) · [File integrity / 完整性清单](agent-worksystem-builder-0.2.0-alpha.1-plugin.manifest.json) · [Usage / 使用说明](../../docs/quickstart.md)

This is the installable **0.2 candidate**, published with its GitHub source for use and inspection. It is not a release-qualified version or an official-directory listing. The immutable alpha.4 tag/assets are unchanged.

这是可安装的 **0.2 候选插件**，随 GitHub 源码交付，供使用和审查。合格版本发布及官方上架仍未完成；alpha.4 固定标签和附件保持不变。

SHA256: `bdc107e34689d4687e0bf707871b4cb10de196cc37ff79e8963c40086274c3f8`

The 79-file plugin contains one coordinator, five focused Skills, a shared Python runtime, optional local MCP code, metadata and bilingual usage documents. No `examples/`, `evals/`, `tools/`, HTML UI, target business data or credentials are installed. Use the native Codex conversation; target application architecture is chosen for the user's actual goal.

安装包共 79 个文件，包含一个总控、五个职责 Skill、共享 Python 运行时、可选本地 MCP 代码、元数据及双语说明。不安装 `examples/`、`evals/`、`tools/`、HTML 界面、目标业务数据或凭据。入口在 Codex 原生会话；目标应用架构按用户实际目标选择。

## Checked on 2026-10-01 / 本次验证

- Full local regression: 165 passed. Two distribution regressions were observed failing before correction; the focused distribution suite then passed 28 checks.
- Native isolated-home installation, cached CLI and all six enabled Skill discoveries passed.
- Native installation into both existing user Codex homes passed; all 79 cache files matched the archive manifest, six Skills were enabled, and parsed host settings remained unchanged. Backup configurations and raw receipts stay local and are not included here.
- The owned evaluation process was stopped for the requested plugin installation. Fourteen attempts finished; attempt 15 is preserved as interrupted, with its original running receipt and unknown final metrics retained. No construction attempt was repeated or promoted. The 120-attempt matrix, known strict-budget gaps and representative human acceptance remain unresolved.

- 本地完整回归通过 165 项。两个分发问题先由测试复现，修正后 28 项聚焦分发检查通过。
- 原生隔离安装、缓存 CLI 和全部六个启用 Skill 的发现通过。
- 两处现有 Codex 配置目录均已原生安装，79 个缓存文件全部匹配清单，六个 Skill 启用，解析后的宿主配置保持不变。配置备份和原始回执留在本地，不随包发布。
- 为此次安装停止了自有评测进程。14 次尝试已结束，第 15 次保留为中断；原始运行中回执及未知的最终指标保留，不重试、不改判。120 次矩阵、已知严格预算缺口及代表性人工验收仍未解决。

GitHub CI covers runtime/distribution engineering only; it does not establish general construction effectiveness. Current gates: [delivery status](../../docs/delivery-status.md), [review ledger](../../docs/upgrade-review.md).

GitHub CI 只检查工程运行及分发，不证明广义构筑效果。当前门槛见[交付状态](../../docs/delivery-status.md)和[审查记录](../../docs/upgrade-review.md)。
