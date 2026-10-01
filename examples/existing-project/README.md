# Existing-project enhancement / 现有项目智能化改造

Keep `parser.py` and its `parse(text)` interface. `enhance.py` adds optional structured annotation using a replaceable IntelligenceProfile; no target DAG, Builder journal or resident service. Run the regression/fallback path:

```powershell
python enhance.py --input input.txt --output result.json --no-intelligence
```

To request real annotation use `--profile PROFILE.json` instead, with existing accessible Codex model/auth. Calls are bounded, read-only and event logs retained. Replacing the profile does not replace the parser. The adapter checks parser/input hashes again after execution. Results preserve `parsed`; model commentary is separate and needs semantic acceptance.

现有接口回归、纯程序替代与源文件保留已做实际子进程测试。当前指定模型的账户预检失败，真实智能增强仍待验证。恢复时重新运行 `--no-intelligence` 到新输出文件，保留失败尝试；扩展接口为 `parse` 和独立的 annotation 适配器。依赖为 Python 3.11+；启用智能注释还需安装本地 AWB runtime 库及 Codex。
