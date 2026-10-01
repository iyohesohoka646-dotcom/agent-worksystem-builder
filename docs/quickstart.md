# Quick start / 快速上手

[English overview](../README.md) · [中文首页](../README.zh-CN.md) · [Downloads / 下载](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4)

Choose the plugin route to work in Codex, or the CLI walkthrough to inspect a repeatable local example without calling a model. The walkthrough uses synthetic documents and a simulated reviewer; it is not a benchmark or a real human-acceptance test.

在 Codex 中协作可选插件安装；想先看实际记录和产物，可运行不调用模型的本地 CLI 示例。示例使用合成材料与模拟复核者，不代表真实模型基准或真实人工验收。

## 1. Install in Codex / 安装到 Codex

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

Open a new session and select the coordinator `agent-worksystem-builder:building-agent-worksystems`. Say what should be preserved, which outputs you want and when a human must decide. Narrow requests can select a focused module directly.

开启新会话并选择总控 `agent-worksystem-builder:building-agent-worksystems`。说明哪些内容必须保留、需要什么输出，以及哪些情况必须由人决定。窄任务也可直接选择相应小模块。

> Build a local document-triage workflow. Keep my existing parser and source files, export JSONL/CSV with source evidence, stop for ambiguous cases and preserve a checkpoint. Do not use cloud services.

> 构筑本地文档分类流程。保留现有解析器和源文件，输出带来源证据的 JSONL/CSV，遇到争议条目停止并保存断点，不使用云服务。

Python execution needs Python 3.11+ and the packaged dependencies. Run the shared doctor first, reuse a compatible project environment and keep target state outside the plugin cache. The Skill does not initialize a project merely to discuss a plan.

Python 执行需要 Python 3.11+ 及随包依赖。先运行共享 doctor，复用兼容项目环境，目标状态不要放在插件缓存中。仅讨论方案不会触发项目初始化。

If Git access fails, download and extract the plugin ZIP and use the [local marketplace instructions](../README.md#git-connection-restricted). The complete Skill-suite ZIP belongs in a Skill host, not a plugin upload dialog.

如果 Git 访问失败，可下载插件 ZIP，解压后按 [本地 marketplace 步骤](../README.zh-CN.md#git-连接受限怎么办) 安装。完整 Skill 套件用于 Skill 主机，不应放进插件上传窗口。

## 2. Run the model-free example / 运行不调用模型的示例

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
