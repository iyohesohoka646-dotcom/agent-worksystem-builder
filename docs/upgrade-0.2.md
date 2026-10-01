# 0.2 candidate upgrade / 候选版升级

Status: 0.2.0-alpha.1 plugin / 0.2.0a1 Python package is available as an experimental preview with engineering and native-plugin checks passed. Preserve v0.1.0-alpha.4 and its downloads. See [validation status](delivery-status.md).

状态：0.2 预览包已通过工程与原生插件验证，完整系统级资格仍在评测；不改写 alpha.4 标签或附件。构筑记录与目标业务状态分别保存，详见[验证状态](delivery-status.md)。

## Local build / 本地构建

From the repository / 在仓库内：

~~~powershell
python -m pip install -e ".[test,mcp]"
python -X utf8 -m pytest -q
python -X utf8 tools/package_plugin.py
Expand-Archive ./dist/agent-worksystem-builder-0.2.0-alpha.1-plugin.zip ./workspaces/awb-candidate
codex plugin marketplace add ./workspaces/awb-candidate/agent-worksystem-builder
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
~~~

Select the same plugin identity in a new conversation. The full six-folder suite must stay together; the wheel supplies only the Python runtime. Do not overwrite the user's existing plugin cache by hand.

新会话中选择原有插件身份。完整六文件夹 Skill 套件需要一起安装；wheel 只提供 Python 运行时。不要手工覆盖用户插件缓存。

The default installation ZIP contains only the plugin resources, not target examples, HTML UI or evaluation jobs. Developer tools and corpus remain in the source checkout; `python tools/package_plugin.py --developer` creates a separate `*-development.zip`. Candidate download and local installation instructions are in [quick start](quickstart.md); the native conversation is the plugin entrypoint.

默认安装 ZIP 仅包含插件资源，不含目标样例、HTML 界面或评测任务。开发工具与语料保留在源码检出目录；`python tools/package_plugin.py --developer` 生成独立开发包。候选下载与本地安装见[快速上手](quickstart.md)，插件入口在原生会话中。

## Compatibility / 兼容

Existing CLI commands and construction state remain supported. The SQLite state format stays at v1; new contracts are additional versioned records. Legacy projects with no saved architecture/profile/exploration retain unknown fields. The original goal comes from actual saved history, never an invented reconstruction. A goal change makes related architecture/profile stale and reopens decisions. New acceptance evidence must match current contracts, candidate bytes, configuration and verifier versions.

旧命令和状态保持兼容，不捏造历史架构、配置或审批。新项目的验收使用架构中已声明的 acceptance_id 与精确配置；重大决策审批绑定当前契约。历史 evidence 的验证器代码变化会使其失效，需要按当前真实产物重新核验，不能沿用旧通过结论。

Back up the project directory and stop active target/Builder processes before changing versions. Construction records are in .worksystem-build; target business data has its own location. Never mix their rollback lifecycles.

升级前备份项目并停止相关进程；建设状态位于 .worksystem-build，业务状态由目标程序独立管理。回退前判断版本兼容性，不用旧运行时写入新增契约。

## Rollback / 回退

Use the immutable alpha.4 ZIP and a separate extracted marketplace/runtime environment. Restore a pre-upgrade project backup if the old runtime must write state. Preserve all new records and failure artifacts for inspection. No automatic destructive migration or rollback runs.

使用 alpha.4 固定附件和独立解压目录／环境。旧运行时需要写状态时，恢复升级前备份；保留新版记录和失败工件，不自动删除或降级状态。

## Access and qualification / 访问与评测

The verified access configuration is Codex 0.158.0 with gpt-6-sol/max on the same host. Both exec and app-server passed actual inference with a per-call model override; no global setting was edited and no credential was copied. A new matrix must freeze the current effective configuration rather than reuse a drifted historical snapshot.

~~~powershell
python -X utf8 tools/host_preflight.py --model gpt-6-sol --output ./reports/access-fresh
python -X utf8 tools/evaluate_systems.py --preflight ./reports/access-fresh/receipt.json --output ./reports/system-matrix
# After an actual external checkpoint, resume only unattempted cells:
python -X utf8 tools/evaluate_systems.py --resume --output ./reports/system-matrix
~~~

The corpus/context/checker/host are frozen. Six cases, four conditions and five repeats yield 120 jobs. No cell is silently retried. Per attempt: 30 host turns, eight observed code-change cycles, 900 seconds including validation. Internal reasoning cycles cannot be observed; this limitation is recorded. Target calls use the same trusted real dual-mode loopback gateway for every condition. Actual human trial remains separate from scripted simulated users. Frozen fixtures constrain test interfaces, not the product's architecture space.

The full matrix runner needs a Git checkout containing the immutable alpha.4 tag, because it freezes the previous suite with `git archive`. A plugin ZIP alone is not sufficient for starting a matched matrix. Use the same Python environment, host and approved model throughout; stop and preserve a checkpoint if fingerprints change. On Codex 0.158.0, the actual isolation proof uses native-reported SKILL.md entrypoint paths; folder overrides did not disable the installed Skills. All overrides are process-local.

完整矩阵须在含 alpha.4 标签的 Git 仓库内启动，插件 ZIP 不能单独提供历史版本冻结。冻结后不改控制器、Skill、语料或评分器。当前六组接口不能单独证明广义架构与自适应搜索效果；工作台节点结果绑定和错误结果拒绝通过独立产物检查核验。局部工程样例与代表性系统级验收分别记录，参见[系统级说明](system-level-construction.md)。

~~~powershell
# Read-only snapshot: no construction reruns, no release approval.
python -X utf8 tools/qualify_systems.py --matrix ./reports/system-matrix --output ./reports/qualification-snapshot-1.json
# Separate artifact fault check, copied workspace, simulated nodes, zero model calls:
python -X utf8 tools/workbench_fault_probe.py --attempt ./reports/system-matrix/attempt-002 --output ./reports/fault-probe-002
~~~

发布门槛：完整真实矩阵、目标保持与硬约束审查、代表性交付的实际人工试用。配额或外部条件不足时保存检查点，矩阵未完成不能标为完成。官方目录审核不随 GitHub 发布自动完成。
