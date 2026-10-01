# 插件结构与可选 MCP

本轮 0.2 候选版保留构筑层、目标普通程序架构与可选智能层三个层次。目标无需采用 AWB DAG、SQLite 或总控 Agent；业务状态与建设状态各自管理。交互智能通过本地 app-server、非交互智能通过 exec 接入，模型／资源／权限按项目契约配置。

默认发行包保持 skills-only：`plugin.json` 提供插件身份，`skills/` 下有一个总控和五个职责入口。`building-agent-worksystems/` 负责完整目标的建设循环、选择模块和衔接结果，同时保管共享参考文件与唯一一份 Python 运行时。用户项目及 `.worksystem-build/` 状态始终放在插件安装目录以外。CLI、MCP 和各 Skill 共用契约、状态、复核及核验实现，不另建一套调度或存储。

```text
building-agent-worksystems（总控）
├── awb-clarify：需求与验收条件
├── awb-explore：自适应探索与候选试验
├── awb-design：架构与集成
├── awb-execute：变更与运行
└── awb-verify：证据、复核与恢复
```

总控只读取当前需要的模块；新建系统可以按需求 → 设计 → 执行 → 核验衔接，已有阶段可以跳过。只检查 checkpoint 会直接进入核验后结束。小 Skill 可按名称直接调用，也可由总控读取同级 `SKILL.md`；这些指令模块不自动创建子智能体。每个模块说明自身输入、输出及停止条件，共享 [交接契约](../skills/building-agent-worksystems/references/module-contract.md) 绑定项目、目标版本、授权范围、预算、实际编号与证据。交接内容是权威状态的派生视图，不能授予权限或覆盖 SQLite。

完整插件和非插件 Skill 套件都保留六个同级目录及其共享引用。套件不能按单个目录拆开安装，也不能当成单插件 ZIP 上传。评测器默认冻结完整套件；传入任一新版模块路径时都会纳入其余模块，并用总控作为比较入口，旧版单 Skill 仍可比较。不相关的已安装 Skill 不会进入冻结快照。打包器在创建归档前检查六个入口及共享资源，缺失模块会拒绝；任一模块变动都会改变评测上下文绑定。该分离调整指令层和分发边界，未改 CLI/MCP 的执行接口。

本地 MCP 随包提供代码，默认不自动启用。它通过 stdio 连接，启动时固定目标项目，不需要 API key 或托管服务。`requirements-mcp.txt` 单独声明官方 Python SDK；不用 MCP 时只安装 `requirements.txt`。参见 skill 的 [MCP 使用说明](../skills/building-agent-worksystems/references/mcp.md)。

MCP 提供八个结构化工具：项目绑定查询、初始化、状态、下一步建议、待复核请求、材料规则处理、恢复和独立核验，以及 `awb://project/goal`、`awb://project/status` 两个资源。材料处理使用确定性规则，模型调用预算固定为零，输入必须是独立子目录，避免读取自身生成的状态。请求的分类时间预算不能超过启动时指定的上限，恢复保留原运行预算。原材料流程只在条目之间检查剩余时间，不计入清单哈希、源文件读取、状态落盘和导出；最后一个条目可能超出预算后完成，无法提供整个调用的硬超时。它不提供通用执行、后端切换、修改目标、文件变更或批准工具；这些操作通过 skill/CLI 在原有授权与验证流程中完成。其他任务领域仍通过 skill 构筑，当前 MCP 没有通用领域处理承诺。

只有项目绑定查询严格只读；状态读取会按既有恢复逻辑重建缺失的 JSON 镜像，所以其工具没有标记为严格只读。目录约束限制这些工具的项目访问范围，运行进程仍持有当前用户的操作系统权限，无法提供沙箱隔离。复核等待返回 `needs_human`，无需保持进程或在 stdin 上等待。

包中没有启用外部集成引用。已有解析器、其他 Skill、文档与仓库 MCP 的选择路径，以及持久工作流框架的引入条件，见随包的 [复用指南](../skills/building-agent-worksystems/references/integrations-and-skills.md)。这些链接提供选型依据，不自动安装或执行外部项目。保持参考说明本地可读，具体复用先检查版本、许可证、指令、数据目的地与当前主机支持。公开包不包含凭据或用户数据；示例宿主路径可按环境修改，不携带本机业务路径、虚拟环境、开发元数据或已启用的 MCP 配置。

默认插件安装包只分发六个 Skill、共享运行时、可选 MCP 代码、元数据与使用说明，不含 `examples/`、`evals/` 或 `tools/`。网站及其他目标样例留在源码仓库；开发者可用 `tools/package_plugin.py --developer` 生成单独的 `*-development.zip`，其中保留评测执行器及题库。开发包不作为用户安装交付。评测参考文件中的“完整插件／仓库”路径指这套开发资源。独立 Skill ZIP 与 wheel 同样不包含开发评测工具；运行时仍只有一份。当前检查验证执行器与分发接口，没有建立真实模型效果提升。

这种分离符合 OpenAI 的 [插件打包说明](https://developers.openai.com/plugins/build/plugins)。MCP Skills 扩展需要客户端支持，OpenAI 门户 [导入 MCP Skill](https://developers.openai.com/plugins/build/skills) 则在扫描时制作草稿快照，ChatGPT/Codex 不在运行时从服务器拉取 Skill。若将来提交带 MCP 的官方插件，须在首次 ZIP 中声明所需 MCP；当前平台不支持给已发布 skills-only 插件再新增 MCP，见 [官方提交说明](https://developers.openai.com/plugins/deploy/submission)。当前候选只构筑和核验本地插件，不提交官方目录。
