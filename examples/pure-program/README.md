# Deterministic counterexample / 纯程序反例

```powershell
python summarize.py input.csv result.json
```

Input CSV has `name,value`; values are integers. Output is a JSON mapping from name to summed values. No model calls, agent, service, Builder state, third-party dependency or new database. Deterministic code satisfies this task, so the target intelligence profile is `none`. Tested against actual subprocess output; this is an engineering example, not a real-model build qualification.

标准库程序按名称汇总整数，保留输入。部署只需要 Python 和这个文件；扩展 `summarize` 函数即可。恢复方法为保留输入、重新运行到新的输出路径。不要把材料分类或智能节点作为必需组件。
