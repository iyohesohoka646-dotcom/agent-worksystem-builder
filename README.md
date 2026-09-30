# Agent Worksystem Builder

Codex 插件，用于把重复任务构筑为可运行、可核验、可恢复的本地工作系统，包含 `building-agent-worksystems` Skill 和 Python CLI。支持目标契约、受控文件变更、独立证据验收、人工复核、断点恢复和有界任务图，首个示例为材料批处理。当前发布为 `0.1.0-alpha.1`，Python 包版本为 `0.1.0a1`，验收范围见 [交付状态](docs/delivery-status.md)。

## 安装与使用

在支持插件管理的 Codex CLI 中添加仓库目录并安装，然后开启新会话；也可在 Codex 桌面插件目录中通过仓库地址添加来源。

```powershell
codex plugin marketplace add iyohesohoka646-dotcom/agent-worksystem-builder --ref v0.1.0-alpha.1
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

也可下载版本中的插件 ZIP，解压后使用本地安装目录；这条路径适用于 Git 连接受限的环境。

```powershell
Expand-Archive ./agent-worksystem-builder-0.1.0-alpha.1-plugin.zip ./awb-plugin
codex plugin marketplace add ./awb-plugin/agent-worksystem-builder
codex plugin add agent-worksystem-builder@agent-worksystem-builder-plugins
```

在新会话中使用 `agent-worksystem-builder:building-agent-worksystems`，例如：“使用 Agent Worksystem Builder，把这批材料处理成可人工复核、可恢复运行的系统。”插件会查看现有项目、记录目标与验收条件，再执行构筑循环。Python 工具要求 Python 3.11+，依赖列在 Skill 内的 `requirements.txt`；首次使用时在目标项目创建 `.venv` 并安装这些依赖。

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
python -m pip install --no-user -e .[test]
python -m pytest -q -p no:cacheprovider
python tools/verify.py
python tools/package_plugin.py
python tools/plugin_smoke.py
```

`tools/verify.py --live-codex` 额外执行一次最长 120 秒的真实推理探针。插件 ZIP、独立 Skill ZIP、Python wheel 与 SHA256 收据位于版本下载，[官方目录提交说明](docs/plugin-submission.md) 记录已准备的上传材料与平台步骤。未验证的兼容性在交付状态中注明。

数据处理说明见 [PRIVACY.md](PRIVACY.md)，使用与支持说明见 [TERMS.md](TERMS.md)。
