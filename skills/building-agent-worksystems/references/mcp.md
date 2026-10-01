# Optional local MCP

Load this reference when an AWB MCP is available or the user wants to configure one. The CLI and this skill work without MCP. First call `awb_project_info()`, which reports the startup binding without initializing state or repairing mirrors. Use the server only if that project matches the user's target. If the binding is unavailable or differs, use CLI with the explicit target project. Do not initialize an unknown bound project as a shortcut.

## Tool routing

| Operation | MCP tool | Scope |
|---|---|---|
| Check binding | `awb_project_info()` | Project, initialization flag and requested-budget cap; strictly read-only |
| New project | `awb_initialize(goal)` | Validated goal contract; refuses replacement of existing state |
| Inspect checkpoint | `awb_status()` | Goal, cycles, runs, reviews and bound project |
| Select next action | `awb_next(uncertainties)` | Uses recorded answers, hard limits and stagnation |
| Show human requests | `awb_pending_reviews()` | Returns `{reviews: [...]}`; no answer/approval tool |
| Materials rules example | `awb_run_materials(input_dir, max_seconds?)` | Dedicated relative input subdirectory, no model/backend calls; project root is rejected to avoid scanning generated state |
| Resume that example | `awb_resume(run_id)` | Rules-only materials runs; preserves remaining budget |
| Check outputs | `awb_verify_materials(run_id, reference?)` | Independent labels establish category accuracy; absent labels only check structure/integrity |

Resources `awb://project/goal` and `awb://project/status` expose JSON context. Status reads may restore missing generated mirrors and are not strictly read-only. Construction changes, goal updates, task graphs, model backends and project export use the existing CLI; MCP cannot start arbitrary commands or replay backend-enabled runs.

## Setup from the plugin root

The optional SDK is installed into a project environment, never into the plugin cache. Run the doctor with `--mcp` first. If a compatible `.venv` already exists, reuse it rather than recreate it. The example below assumes a new environment; replace the project path with the user's actual target.

```powershell
$awbSkill = (Resolve-Path './skills/building-agent-worksystems').Path
$awbProject = 'D:\tasks\papers'
python "$awbSkill/scripts/awb_doctor.py" --project "$awbProject" --mcp
python -m venv "$awbProject/.venv"
$awbPython = "$awbProject/.venv/Scripts/python.exe"
& $awbPython -m pip install --no-user -r "$awbSkill/requirements-mcp.txt"
& $awbPython "$awbSkill/scripts/awb_doctor.py" --project "$awbProject" --mcp
codex mcp add awb-papers -- "$awbPython" -X utf8 "$awbSkill/scripts/awb_mcp.py" --project "$awbProject" --max-seconds 60
```

`codex mcp add` changes the selected Codex profile; desktop and CLI may use different `CODEX_HOME` values. Configure the intended profile, then start a new session. Other local MCP clients can run the same interpreter and argv through stdio. `awb-mcp --project PROJECT` is available after installing the Python package with `[mcp]`. No API key or remote service is needed. A web/cloud client unable to launch local processes cannot use this server; the default packaged skill remains independent of it.

The startup `--max-seconds` caps the requested cumulative classification-time budget, default 60. An omitted tool parameter uses that cap; explicit parameters cannot exceed it. The inherited materials runtime checks remaining time between items. Inventory hashing, source reads, state persistence and export are outside that timer; a final item can overrun the budget and still complete. This is cooperative accounting, not a strict wall-clock timeout or filesystem sandbox. Resume preserves the recorded remaining budget.

## Human review handoff

`needs_human` is an expected saved state. Show each returned request ID, quote and available categories to the user; do not infer an answer. If the user will answer later, keep the checkpoint and stop the affected execution. No server needs to remain running.

After the real answer arrives, write its JSON in the target project, such as `{"category":"other"}`, and submit it using the same project interpreter:

```powershell
& $awbPython "$awbSkill/scripts/awb.py" review --project "$awbProject" --id REVIEW_ID --answer "$awbProject/answer.json" --actor USER
```

Then call `awb_resume(run_id)`, followed by `awb_verify_materials` with independently obtained reference labels. Use `awb_pending_reviews()` to check remaining requests. These are the same persisted approvals and artifacts used by the CLI; a new MCP process can continue them.
