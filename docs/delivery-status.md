# Delivery status / 交付与验证状态

## 0.2.0-alpha.2 distribution update / 分发升级

The new dedicated `codex-import.zip` contains one Codex manifest and no marketplace catalog. It installed through native Codex commands in a fresh credential-free home and exposed all six enabled Skills. The separate standalone `skill.zip` contains one entrypoint, five local reference modules and the shared runtime; its validator, relative-link checks, real CLI launch, preservation/path-escape installer tests and read-only host-adaptive instruction-consumption checks passed. The latter checks used a simulated non-Codex tool boundary and are not actual Claude/Gemini host acceptance. See [packages and installation](distribution.md).

新增 `codex-import.zip` 仅含一个 Codex 清单，不夹带市场目录；已在无凭据的新宿主中原生安装，六个 Skill 均可发现。独立 `skill.zip` 包含一个入口、五个内部模块与共享运行时；入口校验、相对引用检查、真实 CLI 启动、安装保留／路径越界测试和只读宿主适配消费检查通过。宿主适配检查采用模拟的非 Codex 工具边界，不计作 Claude／Gemini 产品验收。安装方式见[分发说明](distribution.md)。

**Desktop/web hosted ZIP import remains unverified.** The browser controller can list the ChatGPT plugin tab but repeatedly times out reading it; native app UI control is unavailable. The dedicated upload ZIP is a packaging compatibility remediation, not a captured server-side diagnosis or proof of hosted acceptance. The historical `Expected a single plugin archive` error is retained. Do not use native CLI success to close this issue.

**桌面／网页 ZIP 导入仍待实际复验。** 浏览器控制可列出 ChatGPT 插件页，但读取页面连续超时，当前无原生应用 UI 控制能力。专用上传包属于结构兼容修正，尚无服务端根因或托管接受证据。保留历史 `Expected a single plugin archive` 错误，原生 CLI 成功不用于关闭此问题。

This update preserves prior archives, source plan, broad system-building scope and construction/runtime interfaces. It does not change the frozen behavioral evaluation or imply official approval. The following sections retain their explicitly versioned alpha.1 and alpha.4 evidence.

本次保留旧包、原始创建计划、广义系统构筑目标与运行接口，不改写冻结行为评测，也不代表官方审核通过。下列 alpha.1 与 alpha.4 证据按原版本保留。

## 0.2 plugin verification passed / 0.2 插件验证通过

**0.2.0-alpha.1 has passed engineering, native installation and dual-mode Codex access checks.** It is distributed as an experimental preview; whole-system behavioral qualification and official-directory review are tracked separately.

**0.2.0-alpha.1 已通过工程回归、原生安装及 Codex 双模式访问验证。** 当前提供实验性预览包，系统级行为评测与官方目录审核分别记录。

Verification refreshed on 2026-10-01 / 验证更新日期：2026-10-01。

| Area / 范围 | Observed evidence / 实际证据 | State / 状态 |
|---|---|---|
| Engineering regression / 工程回归 | 165 tests passed, including contracts, requirements/decisions, exploration, scoped changes, verifiers, whole-goal coverage and recovery / 165 项通过，覆盖契约、需求决策、探索、受控变更、验证器、整体目标覆盖及恢复 | Passed / 通过 |
| Existing installations / 现有安装 | Both configured Codex homes match all 79 public-package files; six enabled Skills discovered; dependency doctor passed without initializing target state or changing host settings / 两处安装的 79 个文件一致，六个 Skill 已启用；依赖检查通过，未初始化目标或改动宿主设置 | Passed / 通过 |
| Fresh installation / 全新安装 | Public ZIP installed through native marketplace commands in a credential-free temporary home; all six Skill entrypoints discovered / 公开 ZIP 在无凭据临时宿主中原生安装成功，六个入口可发现 | Passed / 通过 |
| Real Codex access / 真实 Codex 访问 | Codex 0.158.0, gpt-6-sol / max: exec and app-server both completed actual inference / exec 与 app-server 均完成真实推理 | Passed / 通过 |
| Artifact fault checks / 产物故障检查 | Six checks passed: wrong-result rejection, output binding or explicit rejection, explicit backend failure, no retries in either fault phase, and original-file preservation / 六项通过，覆盖错误结果拒绝、输出绑定或明确拒绝、后端失败、两阶段无重试及原文件保持 | Passed; deterministic injected faults / 通过；确定性故障注入 |
| Cross-platform CI / 跨平台 CI | Full regression and packaging passed on Windows and Linux / Windows、Linux 完整回归与打包通过 | [Passed / 通过](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/workflows/ci.yml) |

The package contains one coordinator, five focused Skills and the shared runtime. Target applications, HTML interfaces and evaluation jobs stay in the source/development resources. Native Codex conversations are the plugin entrypoint. The original creation plan and immutable alpha.4 tag/assets remain unchanged.

安装包包含一个总控、五个专职 Skill 与共享运行时，目标应用、HTML 界面和评测任务保留在源码／开发资源中。插件从原生 Codex 会话使用，完整系统的范围与交付方式见[系统级构筑](system-level-construction.md)。原始创建计划及 alpha.4 固定标签、附件保持不变。

## Qualification still in progress / 持续评测

The frozen 120-attempt comparison contains 14 finished attempts and one interrupted attempt. Failed and timed-out outcomes retain their original grades. A fresh read-only audit found host-configuration drift, so the old matrix cannot resume under the current configuration. The comparison, representative system-level acceptance and official review are not complete; no general performance-improvement claim is made.

冻结的 120 次对照目前包含 14 次已结束尝试和 1 次中断，失败与超时保留原评分。最新只读审查发现宿主配置已偏离冻结快照，旧矩阵不能在当前配置下直接续跑。完整对照、代表性系统级验收及官方审核尚未完成，不据此宣称普遍效果提升。

The local workbench is a dual-mode/recovery test fixture. Its deterministic fault checks use copied artifacts and zero model calls; they do not change construction scores or count as representative human acceptance. See [verification and qualification details](upgrade-review.md).

局部工作台用于双模式与恢复测试。故障检查在产物副本上运行，模型调用为零；它们不改写构筑评分，也不计为代表性人工验收。详见[验证与资格审查](upgrade-review.md)。

## Historical alpha.4 evidence

Alpha version: `0.1.0-alpha.4` plugin / `0.1.0a4` Python package, checked on 2026-10-01. The Skill layer now comprises one coordinator and four focused modules sharing a handoff contract and runtime. Downloads and publication status are on the [GitHub prerelease page](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4). Official-directory submission and complete v0.1 task/compatibility qualification remain open.

| Area | Observed evidence | State |
|---|---|---|
| Windows runtime | Fresh alpha.4 full run: 108 tests passed with Python 3.11.9, including real processes, CLI, recovery, review fault injection, MCP and complete-suite evaluation/packaging boundaries | Passed |
| Construction example | Actual failed candidate, rollback, correction, independent labels, simulated reviewer and fresh-process resume | Passed on synthetic material |
| Native Codex plugin | Codex CLI 0.158.0 installed the alpha.4 ZIP in an isolated home, listed it as enabled and ran its cached CLI | Passed |
| Skill discovery | Native app-server `skills/list` returned all five enabled namespaced Skills: coordinator, clarify, design, execute and verify | Passed |
| Git marketplace fetch in this environment | GitHub HTTPS Git connections were reset; public source was uploaded through the API with matching commit/tree hashes | Network-limited; use the release ZIP/local marketplace |
| Portable Skill suite | All five Skill validators passed; complete-suite extraction resolves module links, runs the shared doctor/CLI and reproduces identical ZIP bytes; missing modules fail before packaging | Passed |
| Python wheel | Alpha.4 wheel build and fresh temporary-directory installation passed; imported the installed package version 0.1.0a4, validated its node schema and ran its CLI | Passed |
| Dependency doctor | Actual installed-dependency check and Python `-S` missing-dependency process; neither initializes target state | Passed |
| Optional local MCP | Official SDK 2.2.0 client: rules run, saved review, externally supplied simulated answer, fresh stdio-process resume, reference verification, resources, path/budget/scope errors | Passed on synthetic material |
| MCP time accounting | Startup cap validates requested classification budget; inherited checks are cooperative between items and exclude inventory/I/O/persistence/export | Known limitation; no strict wall-clock guarantee |
| Modular entrypoint usability | Independent read-only exercises used narrow clarify/design tasks without reading the coordinator, selected verify for an inspection-only checkpoint and stopped execution at file drift; earlier alpha.3 reuse/comparison checks remain separately scoped | Passed for bounded routing checks; not a behavioral benchmark |
| Packaged evaluator | Complete suite frozen from any of its five module paths; missing siblings rejected, unrelated installed Skills excluded and module drift invalidated. Legacy single-Skill comparison, corpus/input/host bindings, paired rates, budget and process boundaries remain covered | Passed on fixtures; no model-effect claim |
| Codex live inference | One corrected structured-output probe reached turn start and reconnection attempts, then hit its 120-second deadline | Pending; transport timeout |
| Ollama | Local endpoint refused connection; transport normalization and total deadline covered by fixtures | Pending real inference |
| Claude Code | Executable unavailable in this environment | Pending host checks |
| Skill behavior | Artifact-based baseline/generic/previous/Builder driver and synthetic corpus shipped; matched real-model matrix not run | Pending |
| Representative domain task | Domain material and acceptance evidence remain unavailable | Pending |
| Linux and Windows CI | Released alpha.4 source run [36823390117](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/runs/36823390117) passed: Windows 108 tests, Linux 107 passed with one platform-specific skip | Passed on release source; independent from model/task acceptance |
| Official plugin directory | Upload package, listing, icon and submission notes prepared | Pending platform identity/access, scans and review |
| ChatGPT web import | Earlier alpha.3 upload returned HTTP 400, `Expected a single plugin archive`; the actual request payload has not been inspected, and alpha.4 web import has not been retried | Unresolved; modularization is not a verified upload fix |

Current receipts are stored under `reports/runtime-tests.xml`, `reports/verification.json` and `reports/plugin-install.json`; the previous synthetic construction trial remains in `workspaces/materials-demo-alpha2`. Raw logs and user workspaces are excluded from public source. Previous-version cross-platform logs and artifacts are in [GitHub Actions](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/actions/runs/36705151697). ZIP file lists and hashes are supplied in `dist/*.manifest.json`. Source planning documents remain in the local development project. Optional MCP is bundled as source and tested through the official SDK client; no claim is made that a current Codex/ChatGPT chat has connected to it.

The alpha.4 review reproduced two distribution defects before correction: freezing a leaf module omitted its siblings, and incomplete suites could be packaged successfully. Regression checks now cover all five input paths, orphaned leaf modules and each missing module for both plugin and Skill-suite packaging. The packager refuses incomplete suites before creating an archive, including when the verification command skips tests. New routing exercises test instruction boundaries; they do not establish a matched real-model performance improvement.

The first two alpha.3 full runs retained one failure in an existing timeout fixture: its 0.4-second deadline ended before the required startup write. Those logs/XML remain under `reports/alpha3-first-full-runtime-tests.*` and `reports/alpha3-second-full-runtime-tests.*`. The test now allows 2 seconds of startup headroom and explicitly asserts timeout, exactly one attempt and exactly one write; its retry policy and runtime deadlines are unchanged. The fresh full run passed all 82 tests. Independent review also reproduced and closed two evaluator defects: lost records after preserved-input path errors, and undetected mutation of a different condition's frozen context by the final job. These are regression checks, not real-model acceptance evidence.

The final review identified eight consequential issues. Regression checks now cover transactional accepted-spec recovery, stale candidate revisions, uncertain side-effect replay, verification/snapshot byte consistency, Windows process-job assignment, Windows path aliases, worker failure checkpointing and HTTP total deadlines. No complete-model or task-acceptance claim is derived from fixture success.
