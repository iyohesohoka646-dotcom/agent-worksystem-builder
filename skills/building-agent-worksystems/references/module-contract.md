# Module handoff and shared runtime

The coordinator and five focused Skills are distributed together: clarify, explore, design, execute and verify. Load only what the next decision needs; modules can be invoked directly. Shared resources live in the sibling `building-agent-worksystems/` directory. Resolve paths from the loaded Skill, not the target cwd. Install/copy the complete suite; leaf folders do not contain the shared runtime.

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
| `architecture_id`, `profile_id`, `exploration_ids` | Actual versioned construction contracts; missing historical fields stay null |
| `artifacts` and `evidence` | Actual paths, hashes, checks, limitations and unresolved effects |
| `next_action` | One bounded operation or a concrete missing input |

Return updated context and actual output. This handoff is not a ledger or permission grant. AWB SQLite is authoritative for construction records; the target application owns separate business state and lifecycle, linked by identifiers/artifacts. Read current state on resume; preserve original goal, answers and decision reasons. Explicit user instructions take precedence.

## Runtime access

Planning or discussing requirements does not require Python, project initialization or a model call. Before a runtime operation, use Python 3.11+ to run `runtime_root/scripts/awb_doctor.py --project PROJECT`. The doctor does not write target state or use the network. Reuse a ready interpreter; if setup is needed, use a project-local environment and the shared `requirements.txt` with `pip install --no-user`, within the user's network constraints. Do not install into the plugin cache.

Run CLI operations as `PYTHON runtime_root/scripts/awb.py COMMAND --project PROJECT`; inspect `--help` for actual arguments. This interpreter/script pair is shared by every module. CLI status may reconstruct generated mirrors: for an explicit no-write inspection, inspect existing records/files without calling repairing operations. Never initialize state just to answer a planning question.

If an AWB MCP is available, read [mcp.md](mcp.md) and call `awb_project_info` before other tools. Use it only for the matching project and supported operations. It cannot approve reviews, run arbitrary backends or implement construction changes. CLI fallback is available; absent MCP does not authorize creating a server or changing host settings.

## Boundaries

Carry limits and evidence through every handoff. A worker result is execution evidence; independent checks establish task correctness, and actual user acceptance establishes goal achievement. Unknown metrics remain null. Review requests require actual user answers. Unknown external effects remain unresolved until reconciled. Saving state does not create a background service, and a project directory is not an OS sandbox.
