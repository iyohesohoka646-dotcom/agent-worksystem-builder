# Use the Codex plugin / 使用 Codex 插件

AWB runs in your native Codex conversation. Install the six-Skill plugin, select its coordinator and describe the complete system you want. There is no AWB website to open and no Builder server to launch. For desktop/web ZIP upload or a standalone cross-host Skill, use the distinct [installation packages](distribution.md). Full behavior qualification remains pending. See [upgrade and rollback](upgrade-0.2.md).

AWB 在 Codex 原生会话中运行。安装六模块插件，选择总控并描述完整系统目标，无需打开网站或启动 Builder 服务。桌面／网页 ZIP 上传和跨宿主独立 Skill 使用不同的[安装包](distribution.md)。完整能力评测仍待验收；升级与回退见[说明](upgrade-0.2.md)。

[English overview](../README.md) · [中文首页](../README.zh-CN.md) · [Plugin ZIP / 插件下载](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/raw/refs/heads/main/packages/0.2.0-alpha.1/agent-worksystem-builder-0.2.0-alpha.1-plugin.zip)

The plugin ZIP contains no target application, HTML interface or evaluation jobs. The optional developer walkthrough below needs a repository checkout and uses synthetic documents and a simulated reviewer; it is not the plugin entrypoint, a benchmark or a real human-acceptance test.

插件 ZIP 不包含目标应用、HTML 界面或评测任务。下方可选开发示例须在源码检出目录运行，使用合成材料和模拟复核者；不作为插件入口、真实模型基准或人工验收。

## 1. Install in Codex / 安装到 Codex

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref main
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

Open a new session and select the coordinator `agent-worksystem-builder:building-agent-worksystems`. Say what should be preserved, which outputs you want and when a human must decide. Narrow requests can select a focused module directly.

开启新会话并选择总控 `agent-worksystem-builder:building-agent-worksystems`。说明哪些内容必须保留、需要什么输出，以及哪些情况必须由人决定。窄任务也可直接选择相应小模块。

> Build a complete system for my actual workflow. Discover existing resources, grill consequential requirements, explore architecture choices, then implement and verify the whole goal. Preserve existing interfaces and unrelated changes. Ask before new credentials, costs or changed data destinations.

> 为我的实际工作构筑完整系统。发现现有资源，持续讨论关键需求，探索架构选择，再实施并核验整体目标。保留已有接口和无关改动；新凭据、费用或数据去向变化先和我讨论。

Python execution needs Python 3.11+ and the packaged dependencies. Run the shared doctor first, reuse a compatible project environment and keep target state outside the plugin cache. The Skill does not initialize a project merely to discuss a plan.

Python 执行需要 Python 3.11+ 及随包依赖。先运行共享 doctor，复用兼容项目环境，目标状态不要放在插件缓存中。仅讨论方案不会触发项目初始化。

If Git access fails, use the plugin ZIP and a fresh extraction directory. Compare SHA256 with the accompanying manifest before installation. Keep the extracted source directory for refresh or rollback; native Codex manages its own installed cache copy. The complete Skill-suite ZIP belongs in a Skill host, not a plugin upload dialog.

Git 访问失败时，使用插件 ZIP 和新的解压目录，安装前比对随包清单中的 SHA256。保留解压源目录供刷新或回退，安装缓存由 Codex 原生管理。完整 Skill 套件用于 Skill 主机，不应放进插件上传窗口。

```powershell
Get-FileHash ./agent-worksystem-builder-0.2.0-alpha.1-plugin.zip -Algorithm SHA256
Expand-Archive ./agent-worksystem-builder-0.2.0-alpha.1-plugin.zip ./awb-0.2-candidate
codex plugin marketplace add ./awb-0.2-candidate/agent-worksystem-builder
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

If an existing app session still exposes the old Skills, save your work and restart the app, then start a new conversation. MCP is optional and is not enabled automatically.

应用仍显示旧模块时，保存工作并重启应用，再开启新会话。MCP 可选，不自动启用。

## 2. Optional developer example / 可选开发示例（源码仓库）

From a fresh repository checkout, create a project-local environment. Dependency installation may use the network; the demo itself runs local Python processors and makes no model call. If a compatible `.venv` already exists, reuse it.

在新的仓库检出目录中创建项目环境。安装依赖可能使用网络；示例本身只运行本地 Python 处理器，不调用模型。已有兼容 `.venv` 时直接复用。

```powershell
git clone https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder.git
cd agent-worksystem-builder
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-user -e .
.\.venv\Scripts\python.exe -X utf8 tools/demo.py --project workspaces/quickstart-demo
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py status --project workspaces/quickstart-demo --json
```

Use a new demo directory each time; the demo refuses to replace an existing project. On Linux/macOS, use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

每次使用新的示例目录；示例会拒绝替换已有项目。Linux/macOS 将解释器路径换成 `.venv/bin/python`。

### What happens? / 实际发生什么？

| Stage / 阶段 | Observed behavior / 可观察行为 |
|---|---|
| Inputs / 输入 | Three synthetic research, procedure and mixed-content documents / 三份研究、操作步骤和混合内容材料 |
| First candidate / 首个候选 | A local processor misclassifies mixed content; independent labels refute it / 本地处理器错分混合材料，独立标签反驳该候选 |
| Correction / 修正 | The candidate is rolled back, then a revised processor routes mixed content to review / 回退候选，修正处理器后将混合内容送往复核 |
| Human checkpoint / 人工断点 | A simulated reviewer supplies the example answer / 模拟复核者提交示例答案 |
| Resume and verify / 恢复与核验 | A fresh process resumes the same run and independent labels support the corrected candidate / 新进程恢复同一运行，独立标签支持修正后的候选 |

The report contains these values; run/cycle IDs vary:

报告包含以下值；运行与循环编号会变化：

```json
{
  "synthetic_fixture": true,
  "real_model_used": false,
  "human_review": "simulated-demo-reviewer",
  "baseline_passed": false,
  "candidate_passed": true,
  "accepted": true
}
```

Inspect `workspaces/quickstart-demo/demo-report.json`, the preserved `input/` files and `.worksystem-build/`. Completed run outputs are under `.worksystem-build/runs/RUN_ID/outputs/` as `materials.jsonl` and `materials.csv`; the run record names the exact output paths and hashes. Keep failed-cycle evidence as well as the accepted candidate.

查看 `workspaces/quickstart-demo/demo-report.json`、保留的 `input/` 文件和 `.worksystem-build/`。完成运行的输出位于 `.worksystem-build/runs/RUN_ID/outputs/`，包括 `materials.jsonl` 与 `materials.csv`；运行记录提供准确路径和哈希。保留失败循环与已接受候选的两类证据。

## 3. Use your own material / 换成自己的材料

Create a separate target directory and edit `examples/goal.json` for the actual purpose, constraints and acceptance criteria. Put TXT/Markdown inputs in its `input/` subdirectory. The following commands run the bundled rules example; its three example categories are `research`, `procedure` and `other`, not a universal domain classifier.

建立独立目标目录，按实际用途、约束与验收条件编辑 `examples/goal.json`，将 TXT/Markdown 放在目标的 `input/` 子目录。下面的命令使用随包规则，三个示例类别为 `research`、`procedure` 和 `other`，不构成通用领域分类器。

```powershell
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py init --goal examples/goal.json --project workspaces/my-materials
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py run --input input --project workspaces/my-materials
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py review --project workspaces/my-materials
```

When the run returns `needs_human`, keep the checkpoint. Inspect the review ID, question and source quote; supply a genuine answer, such as `{"category":"procedure"}`, in an `answer.json` file. Then use the actual IDs returned by the tool:

出现 `needs_human` 时保留断点，查看复核编号、问题和原文引用，再将真实答案（例如 `{"category":"procedure"}`）保存为 `answer.json`。使用工具实际返回的编号：

```powershell
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py review --project workspaces/my-materials --id REVIEW_ID --answer answer.json --actor your-name
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py resume --project workspaces/my-materials --id RUN_ID
.\.venv\Scripts\python.exe -X utf8 skills/building-agent-worksystems/scripts/awb.py verify --project workspaces/my-materials --id RUN_ID --reference reference.json
```

`reference.json` maps source filenames to independently obtained labels, for example `{"a.txt":"research"}`. Complete all required reviews before resume. Structural output checks alone do not establish semantic correctness or real user acceptance.

`reference.json` 将源文件名映射到独立取得的标签，例如 `{"a.txt":"research"}`。恢复前须完成所需复核。仅通过结构检查不证明语义正确或真实用户验收。

## Next steps / 深入了解

- [Module handoff / 模块交接](../skills/building-agent-worksystems/references/module-contract.md)
- [Optional MCP / 可选 MCP](../skills/building-agent-worksystems/references/mcp.md)
- [Runtime interfaces / 运行时接口](interfaces.md)
- [Evidence and remaining gates / 证据与待验证项](delivery-status.md)
- [Report a sanitized reproduction / 提交脱敏复现](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/issues)
