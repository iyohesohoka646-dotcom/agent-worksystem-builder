# Integration and Skill reuse

Inspect existing scripts, installed tools and task contracts before adding dependencies. Keep a working deterministic parser intact; wrap it with explicit inputs, outputs and an independent verifier. Reading a reference or finding a repository does not authorize installation, remote calls or publication. Reuse only when a concrete task gap remains; the examples below are candidates, not required dependencies.

| Need | Smallest suitable route | Check before use |
|---|---|---|
| Repeatable local transformation | Existing script through the CLI command adapter | Declared inputs/outputs, executable trust, preserved-source hash and actual parser invocation |
| Reusable agent instructions | An inspected, pinned local Skill with bundled references | Trigger scope, license, source/version, instructions and scripts; avoid competing entrypoints or automatic downloads |
| Version-specific library documentation | An existing documentation MCP, such as Context7 | Available client tool, supported library/version, query data destination and offline constraint |
| Repository context or permitted GitHub operations | An existing GitHub MCP | Account/repository scope; read access never implies permission for writes, issues or publishing |
| AWB project state and material rules | Bundled optional stdio MCP | Run doctor, confirm `awb_project_info` binding, then follow [mcp.md](mcp.md); human approval stays outside MCP |
| Long-running or distributed orchestration | A durable framework only after local CLI/state no longer meets a demonstrated need | Restart recovery, external effects, worker/service ownership and deployment cost; in-memory checkpoints are insufficient |

For offline or sensitive material, prefer local tools and bundled references. Do not send source content to a remote documentation/repository service without authority for that destination. MCP supplies typed calls and resources, not an operating-system sandbox; the host must enforce access and execution boundaries. A public registry entry does not establish code safety, license compatibility or host support.

Useful Skill sources include Anthropic's `skill-creator` and `mcp-builder`, Superpowers' testing/review workflows, and `planning-with-files` for continuity. Inspect files/license, pin a revision and select complementary resources rather than bundle repositories wholesale. Preserve AWB's construction ledger; target business storage remains independent. MCP does not remove the need for concise instructions about when/how tools apply. Resources outside this initial list may be discovered through adaptive exploration.

`ext-skills` describes negotiated Skill discovery through MCP; client support must be verified. OpenAI's plugin portal instead imports MCP-provided Skills into a draft snapshot during Scan Tools. ChatGPT and Codex do not fetch those Skills at runtime; server changes require a rescan and new plugin version. `ext-tasks` describes reconnectable task handles; it does not implement server persistence or authorize a background service. Neither extension is needed by this plugin's default local Skill/CLI.

LangGraph persistence, Mastra suspend/resume and Temporal durable-agent examples are alternatives when a demonstrated multi-worker or long-lived service need justifies them. Verify recovery across a fresh process and real side-effect reconciliation before selecting a framework. A successful in-process resume or a demo is insufficient evidence of that property in the target system.

## Compare a Skill change

The source repository and separate `*-development.zip` include `tools/evaluate.py` and `evals/README.md`; the installable plugin ZIP, standalone Skill ZIP and Python wheel do not. Use a source checkout/development bundle and resolve its actual runner path. Run that artifact-based runner with an explicit trusted host configuration, `--baseline-skill OLD_SKILL_DIR` and `--builder-skill NEW_SKILL_DIR`. It freezes both directories and the corpus, binds host/input hashes and preserves every attempted result. Five repeats on the two development scenarios and four conditions require `--max-attempts 40`. Run holdout separately without tuning against it. Configure clean host sessions with identical model, permissions and limits; a nominal no-Skill condition is invalid if the host implicitly loads this plugin. Cost, tokens and model-call counts remain null unless separately measured. Inspect actual implementation and artifacts; a fixture pass or automatic summary never establishes real-model improvement or user acceptance.

## Primary references (checked 2026-10-01)

- [Agent Skills specification](https://agentskills.io/specification); [Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) and [mcp-builder](https://github.com/anthropics/skills/tree/main/skills/mcp-builder)
- [Superpowers](https://github.com/obra/superpowers); [planning-with-files](https://github.com/OthmanAdi/planning-with-files)
- [Context7](https://github.com/upstash/context7); [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [MCP Skills extension](https://github.com/modelcontextprotocol/ext-skills); [MCP Tasks extension](https://github.com/modelcontextprotocol/ext-tasks); [MCP registry](https://modelcontextprotocol.io/registry/about)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence); [Mastra suspend and resume](https://mastra.ai/docs/workflows/suspend-and-resume); [Temporal durable agent Skills example](https://github.com/temporal-sa/durable-agent-skills)
- [OpenAI Skill import](https://developers.openai.com/plugins/build/skills); [portable MCP configuration](https://agent-plugins.org/plugin-authors/mcp-servers); [OpenAI submission constraints](https://developers.openai.com/plugins/deploy/submission)
