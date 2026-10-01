# Task workbench / 任务工作台

Scope: a local dual-mode/recovery engineering sample. It saves multiple independent tasks, but does not implement projects, task dependencies or system-level construction. It is not the Builder product UI or a representative whole-system acceptance target. See [system-level construction](../../docs/system-level-construction.md). The user rejected the earlier line-count human trial as too narrow; that trial is not accepted and no human qualification is inferred.

范围：局部双模式与恢复测试样例，尚无项目层或跨任务调度。总控在原生 Codex 会话中构筑完整系统。本页面不能替代完整产品定位或系统级人工验收。

Standalone local target application: browser UI + Python HTTP service + its own `workbench.sqlite`. It never initializes `.worksystem-build`, uses no AWB DAG and works after the Builder conversation closes. Install the project wheel/library into a local environment, then run:

```powershell
python workbench.py --data D:/workbench-data --profile profile.json --port 8766
```

Open `http://127.0.0.1:8766`. Create a task and independent expected JSON, discuss requirements, approve the task version, execute it, then inspect actual `result.json` verification. Input and profile digests bind approval. Updates create new versions. At most one attempt per task version; failed and interrupted attempts remain. Restart keeps tasks, versions, approval records and events; interrupted effects require reconciliation rather than automatic replay.

交互讨论使用本地 app-server，会话编号持久保存、重启后恢复，审批和用户提问由界面显示并要求明确答复。非交互执行使用 `codex exec`，文件修改限定在该任务目录；普通 Python 检查实际结果与输入哈希。目标系统业务状态与构筑记录独立。

Dependency: Python 3.11+ and the AWB runtime library (`pip install` the local wheel or repository). No new credentials or model services are created. `profile.json` is an example using existing C:/codex auth. Actual preflight passed gpt-6-sol/max in both modes on Codex 0.158.0; the unsupported gpt-6.1-sol attempt is retained. The example uses the user-approved per-call override without global edits. Changing model/host requires an explicit configuration decision and fresh preflight; local fixture tests do not qualify real intelligence or the 120-attempt matrix.

Single-user loopback demonstration, not a multi-user production service. Only loopback Host/Origin accepted; no cross-origin API access. Keep data and process logs private. Export/share is separate. Extend task-specific verification in `execute`, or replace adapters without changing the task API. Back up `workbench.sqlite` using SQLite backup and copy the tasks/attempts/discussions directories while stopped; restore them together. No perpetual Builder service is required.
