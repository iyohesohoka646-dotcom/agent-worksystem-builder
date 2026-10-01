# Host capabilities and optional runtime

The Builder is the agent currently reading the Skill. It uses that host's model and tools without requiring an OpenAI account, subscription, API key or Codex subprocess. The target may choose a different intelligence provider or no intelligence.

Shared reference examples mention Codex because the original plugin uses it. Interpret construction steps through the current host. App-server and `codex exec` are literal Codex-specific adapters: never fabricate equivalent support in another host. If a target needs another provider, inspect its official interfaces and implement an authorized project-local adapter, then verify access and result semantics. No credential copying or global configuration replacement is implied.

| Observed capability | Available work |
| --- | --- |
| Text only | Requirements, alternatives, design and implementation handoff; execution unverified |
| Read/search | Real project/environment inspection and source-backed decisions |
| Edit and shell | Implementation and real tests within current authority |
| Python 3.11+ with dependencies | Optional AWB journal, CLI and bound evidence |
| Host supports Agent Skills | Automatic discovery from its supported Skill directory |
| No Skill loader | Ask the agent to read the installed `SKILL.md` and linked resources explicitly |

For optional runtime operations, `runtime_root` is the directory containing this Skill's `SKILL.md`. Run `PYTHON runtime_root/scripts/awb_doctor.py --project ABSOLUTE_TARGET` first. If dependencies are missing, reuse a project environment or, when authorized, install `runtime_root/requirements.txt` into a target-local environment. Never install into the Skill folder. Then use `PYTHON runtime_root/scripts/awb.py --help`; every state operation must name `--project` outside the Skill.

Discussion and read-only inspection do not initialize AWB state. If the host cannot run Python, keep an attributable project handoff with goals, decisions, evidence and next action through its existing file tools; do not claim SQLite transaction, drift protection or automatic recovery from ordinary notes.
