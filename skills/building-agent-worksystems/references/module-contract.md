# Module handoff and shared runtime

The five Skills are distributed together. The coordinator selects only the module needed now; modules can also be invoked directly. Their shared resources live in the sibling `building-agent-worksystems/` directory. Resolve paths from the loaded Skill file, not from the target project's current directory. Install or copy the complete Skill suite; an individual module folder does not contain the shared runtime.

## Handoff

Pass a short context record containing the following observed values. Leave unavailable identifiers null rather than inventing them:

| Field | Source |
|---|---|
| `project` | Explicit absolute target path, outside the plugin cache |
| `request` and `mode` | Current user instruction; inspect, plan, change or resume |
| `goal_revision` and `goal_source` | Existing goal state or the unconfirmed proposed goal file |
| `constraints`, `authority` and `budget` | User's limits, already authorized actions and remaining call/time limits |
| `runtime_root` and `python` | Resolved shared Skill directory and verified compatible interpreter, if execution is needed |
| `cycle_id`, `change_id`, `run_id`, `review_ids` | Actual records used by the current operation |
| `artifacts` and `evidence` | Actual paths, hashes, checks, limitations and unresolved effects |
| `next_action` | One bounded operation or a concrete missing input |

Return the updated record and the module's task output. This is a derived handoff, not a second ledger or permission grant. SQLite remains authoritative for initialized AWB projects. Read current state on resume; preserve answered questions and earlier decisions. Explicit user instructions take precedence over Skill procedures.

## Runtime access

Planning or discussing requirements does not require Python, project initialization or a model call. Before a runtime operation, use Python 3.11+ to run `runtime_root/scripts/awb_doctor.py --project PROJECT`. The doctor does not write target state or use the network. Reuse a ready interpreter; if setup is needed, use a project-local environment and the shared `requirements.txt` with `pip install --no-user`, within the user's network constraints. Do not install into the plugin cache.

Run CLI operations as `PYTHON runtime_root/scripts/awb.py COMMAND --project PROJECT`; inspect `--help` for actual arguments. This interpreter/script pair is shared by every module. CLI status may reconstruct generated mirrors: for an explicit no-write inspection, inspect existing records/files without calling repairing operations. Never initialize state just to answer a planning question.

If an AWB MCP is available, read [mcp.md](mcp.md) and call `awb_project_info` before other tools. Use it only for the matching project and supported operations. It cannot approve reviews, run arbitrary backends or implement construction changes. CLI fallback is available; absent MCP does not authorize creating a server or changing host settings.

## Boundaries

Carry limits and evidence through every handoff. A worker result is execution evidence; independent checks establish task correctness, and actual user acceptance establishes goal achievement. Unknown metrics remain null. Review requests require actual user answers. Unknown external effects remain unresolved until reconciled. Saving state does not create a background service, and a project directory is not an OS sandbox.
