# Agent Worksystem Builder

Codex 插件，用于把重复任务构筑为可运行、可核验、可恢复的本地工作系统，包含一个总控和四个职责 Skill，共享 Python CLI、环境自检和可选本地 MCP。支持目标契约、受控文件变更、独立证据验收、人工复核、断点恢复和有界任务图，首个示例为材料批处理。当前版本为 `0.1.0-alpha.4`，Python 包版本为 `0.1.0a4`；下载和发布状态见 [GitHub 预发布页面](https://github.com/iyohesohoka646-dotcom/agent-worksystem-builder/releases/tag/v0.1.0-alpha.4)。验收范围见 [交付状态](docs/delivery-status.md)。

## 模块化 Skill

| 入口 | 职责 |
|---|---|
| `building-agent-worksystems` | 总控：选择当前模块、传递上下文、衔接结果 |
| `awb-clarify` | 需求、约束与验收条件澄清 |
| `awb-design` | 架构选型、现有脚本及 Skill/MCP 集成 |
| `awb-execute` | 已授权目标更新、受控变更和有界运行 |
| `awb-verify` | 独立核验、人工复核、验收与安全恢复 |

可以直接调用某个小 Skill，也可由总控按需组合；仅做规划或检查时，输出当前结果后停止。共享运行时和参考文件位于 `building-agent-worksystems/`，各模块通过 [交接契约](skills/building-agent-worksystems/references/module-contract.md) 传递同一个项目、目标版本、运行编号、预算及证据，不另建状态账本。完整插件安装后会发现全部五个入口。

非插件主机可解压 `agent-worksystem-skills-0.1.0-alpha.4.zip`，把全部五个同级文件夹放进主机的 Skill 目录；只复制某个模块或只复制总控会丢失共享依赖。这份套件 ZIP 用于本地 Skill 安装；ChatGPT“添加插件”应使用带插件清单的 `agent-worksystem-builder-0.1.0-alpha.4-plugin.zip`。

## 安装与使用

从 GitHub 安装 alpha.4，再开启新会话：

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.4
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

也可在本地项目或解压后的插件根目录中安装：

```powershell
codex plugin marketplace add .
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

alpha.4 插件 ZIP 可解压安装；这条路径适用于 Git 连接受限的环境。旧版 alpha.1 的公开包仍保留在 GitHub，尚不包含模块化、自检和可选 MCP 改进。

```powershell
Expand-Archive ./agent-worksystem-builder-0.1.0-alpha.4-plugin.zip ./awb-plugin
codex plugin marketplace add ./awb-plugin/agent-worksystem-builder
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

在新会话中使用 `agent-worksystem-builder:building-agent-worksystems`，例如：“使用 Agent Worksystem Builder，把这批材料处理成可人工复核、可恢复运行的系统。”插件会查看现有项目、记录目标与验收条件，再执行构筑循环。Python 工具要求 Python 3.11+；`scripts/awb_doctor.py --project PROJECT` 在依赖尚未安装时也能返回环境问题和安装命令，不改环境、不联网。优先复用兼容环境，否则在目标项目创建 `.venv` 并安装 skill 内的 `requirements.txt`。

默认插件不自动启用 MCP，也不要求 API key。可选 MCP 提供八个结构化工具和两个上下文资源，启动时绑定一个项目；只运行本地材料规则流程，保留人工复核、预算、恢复和核验机制。其他领域、受控变更及模型后端继续通过 skill/CLI 构筑。安装与连接步骤见 [MCP 使用说明](skills/building-agent-worksystems/references/mcp.md)，取舍见 [插件结构](docs/plugin-architecture.md)。

已有脚本、其他 Skill、文档或 GitHub MCP 可以按 [复用指南](skills/building-agent-worksystems/references/integrations-and-skills.md) 选取；不自动下载外部指令或替换可用的解析器。完整插件随包提供 `tools/evaluate.py` 和合成题库，可冻结旧版/新版 Skill，在同一主机配置下核验实际产物并汇总配对结果。具体预算、主机隔离要求与未知指标见 [评测协议](evals/README.md)；独立 Skill ZIP 和 wheel 不含该评测工具。

独立运行或开发时克隆仓库，在项目目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-user -e .
.\.venv\Scripts\python.exe tools/demo.py --project workspaces/materials-demo
.\.venv\Scripts\python.exe skills/building-agent-worksystems/scripts/awb.py status --project workspaces/materials-demo --json
```

示例创建三份合成材料，实际执行两个本地候选处理器，保留第一次失败证据，修正后模拟一次人工答复，再通过新进程恢复并验收。示例使用确定性规则，真实用户材料、模型效果和人工体验需要各自的验证。

## 处理自己的材料

初始化一个独立目录，再把 TXT/Markdown 材料放入该目录下的 `input`。`examples/goal.json` 是可编辑的目标示例，调用预算与时间预算需要明确设置；材料规则模式不调用模型。

```powershell
awb init --goal examples/goal.json --project workspaces/my-project
awb run --input input --project workspaces/my-project
awb review --project workspaces/my-project
awb review --id REVIEW_ID --answer answer.json --actor your-name --project workspaces/my-project
awb resume --id RUN_ID --project workspaces/my-project
awb verify --id RUN_ID --reference reference.json --project workspaces/my-project
```

人工分类答复形如 `{"category":"research"}`，独立参考标签形如 `{"a.txt":"research"}`。`research`、`procedure`、`other` 是示例分类，正式领域应接入自己的分类契约与校验器。CSV 对公式前缀作转义，JSONL 保留权威结果；未完成的人工请求返回 `needs_human`，跨进程恢复沿用同一运行记录。

## 执行、恢复与扩展

支持 `command`、`codex`、`ollama` 三种后端，配置示例位于 `examples/`。命令节点需要可信 argv 和可执行文件白名单，离线目标禁止 Codex 云调用及无法证明离线性的通用命令。Ollama 离线运行限制为回环地址与明确的本地模型，超时由所属进程监督执行。模型输出通过 JSON Schema 后仍需要独立任务核验。

验收规格与状态在 SQLite 事务中提交，JSON 规格和交接文档可重建；候选绑定当前规格修订，人工答复绑定输入与目标，证据绑定实际核验的字节及执行依赖。拥有未知副作用的失败任务暂停供人工核对，只有无副作用节点或带明确 `idempotency_key` 的幂等契约可自动重放。任务图时间预算按累计执行时间预留，崩溃保留已预留额度。已验收变更需通过新候选作补偿修改。

新节点遵循 [接口说明](docs/interfaces.md)，每个目标项目的状态位于 `.worksystem-build/`。`awb export` 将项目状态、原始材料与证据导出到新文件；源输入和安装目录应保持分离。运行工具需要正常主机权限，严格隔离要求必须由主机提供可核验的边界。

## 验证与发布

```powershell
python -m pip install --no-user -e '.[test,mcp]'
python -m pytest -q -p no:cacheprovider
python tools/verify.py
python tools/package_plugin.py
python tools/plugin_smoke.py
```

`tools/verify.py --live-codex` 额外执行一次最长 120 秒的真实推理探针。插件 ZIP、完整 Skill 套件 ZIP、Python wheel 与 SHA256 收据生成到 `dist/`。本次候选尚未发布 GitHub 或上传官方目录；[官方目录提交说明](docs/plugin-submission.md) 记录打包与平台要求。未验证的兼容性在交付状态中注明。

数据处理说明见 [PRIVACY.md](PRIVACY.md)，使用与支持说明见 [TERMS.md](TERMS.md)。
