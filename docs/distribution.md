# Installation packages / 安装包

The Builder constructs complete systems from the current agent conversation. These packages do not turn it into a website or replace its original runtime.

构筑器在当前智能体会话中构筑完整系统。下列分发包保留原有功能，不将插件改成网站。

| Package / 包 | Destination / 用途 |
| --- | --- |
| `agent-worksystem-builder-0.2.0-alpha.2-codex-import.zip` | Desktop/web plugin ZIP upload: one Codex manifest, six Skills, no marketplace catalog / 桌面与网页插件上传：单一 Codex 清单、六个 Skill，不夹带市场目录 |
| `agent-worksystem-builder-0.2.0-alpha.2-plugin.zip` | CLI/local marketplace installation / 命令行与本地市场安装 |
| `agent-worksystem-builder-0.2.0-alpha.2-skill.zip` | One standalone Agent Skill, all modules and shared runtime inside its own folder / 单个通用 Skill，模块与运行时全部位于自身目录 |

Upload only the `codex-import.zip` in a plugin upload dialog; do not upload the source checkout, marketplace bundle, integrity JSON or Skill ZIP there. The import ZIP is a compatibility package, not evidence that the hosted service accepted it. CLI installation and hosted ZIP import are separate checks. The historical HTTP 400 `Expected a single plugin archive` has no captured upload payload, so its exact server-side cause remains unconfirmed.

插件上传窗口仅选 `codex-import.zip`，不要上传源码仓库、市场包、校验 JSON 或 Skill 包。上传专用 ZIP 满足单插件交付结构；最终是否被宿主接受须以实际上传结果为准。CLI 安装与托管导入分别核验。历史 HTTP 400 `Expected a single plugin archive` 缺少上传请求记录，服务端具体原因仍未确认。

## Native Codex installation / 原生 Codex 安装

The dependency-free installer accepts the import ZIP and creates the marketplace outside the upload bundle. Use a fresh source directory and keep it for upgrades. It refuses overwriting an existing installation or catalog.

无第三方 Python 依赖的安装器使用上传包，在包外建立本地市场。使用新的源码安装目录并保留供升级使用；安装器拒绝覆盖已有安装或市场。

```powershell
python -X utf8 tools/install_awb.py --kind plugin --archive ./agent-worksystem-builder-0.2.0-alpha.2-codex-import.zip --destination ./awb-alpha2-install --codex-home C:/codex
```

Run that command from a source checkout. A separately downloadable `install_awb.py` is also provided alongside the archives; use its actual path instead of `tools/install_awb.py`. The installer uses native Codex marketplace/add commands; it does not manually replace host settings or copy credentials. Start a new conversation after installation; if the desktop list remains stale, save work and restart the app.

上面的命令在源码仓库中运行；安装包旁另提供 `install_awb.py` 下载，可将 `tools/install_awb.py` 换成其实际路径。安装器调用 Codex 原生市场和安装命令，不手写替换宿主设置，不复制凭据。安装后新开会话；桌面列表仍未刷新时，保存工作并重启应用。

## Standalone Skill / 独立通用 Skill

Extract the Skill ZIP and copy the **whole `agent-worksystem-builder` folder** into the host's supported Skill directory. It contains exactly one `SKILL.md`, with five composable modules as ordinary references. No sibling registration or plugin namespace is required.

解压 Skill ZIP，将整个 `agent-worksystem-builder` 文件夹放入宿主支持的 Skill 目录。包内仅有一个 `SKILL.md`，五个专职模块作为普通参考文件组合，不依赖兄弟 Skill 注册或插件命名空间。

| Host / 宿主 | Skill directory / 目录 |
| --- | --- |
| Codex | Active `CODEX_HOME/skills/`, or supported `.agents/skills/` / 当前生效的技能目录 |
| Claude Code | `.claude/skills/` in the project, or `~/.claude/skills/` |
| Gemini CLI | `.gemini/skills/` or `.agents/skills/`; user scope also supports these under the home directory |
| Other Agent Skills hosts | Their documented Skill directory / 按宿主文档放置 |
| No Skill loader | Tell the agent to read the installed `SKILL.md` and linked files / 显式让智能体读取入口与关联文件 |

You may use `python tools/install_awb.py --kind skill --archive SKILL_ZIP --destination SKILLS_DIRECTORY`. The installer requires only Python's standard library and preserves other Skills. The same script is also bundled under the standalone Skill's `scripts/` directory.

也可使用 `python tools/install_awb.py --kind skill --archive SKILL_ZIP --destination SKILLS_DIRECTORY`。安装器仅用 Python 标准库，保留其它 Skill；脚本也包含在独立 Skill 的 `scripts/` 中。

Invoke `$agent-worksystem-builder` where supported; Claude Code may use `/agent-worksystem-builder`. Without an invocation syntax: “Read PATH/SKILL.md; use its modules to explore, build and verify my complete system.”

支持时调用 `$agent-worksystem-builder`；Claude Code 可用 `/agent-worksystem-builder`。没有专用调用语法时：“读取 PATH/SKILL.md，使用其中的模块探索、构筑并验证完整系统。”

The instruction workflow uses the current host's tools and model. It does not require Codex, MCP or a new API account. Python 3.11+ and packaged requirements are optional dependencies for AWB journal/CLI operations. An agent without file execution can plan and hand off, but cannot build or verify software. “Portable” describes packaging and capability-aware instructions, not actual testing on every agent product.

指令流程使用当前宿主的工具和模型，不强制依赖 Codex、MCP 或新 API 账户。只有 AWB 记录库／CLI 操作需要 Python 3.11+ 和随包依赖。缺少文件执行能力的智能体只能规划与交接，不能宣称实现或核验软件。“通用”指自包含分发与能力适配，实际兼容证据按宿主分别记录。

Directory references: [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins), [Claude Code Skills](https://code.claude.com/docs/en/skills), [Gemini CLI Skills](https://geminicli.com/docs/cli/skills/).

## Upgrade and rollback / 升级与回退

Keep the previous archive and source directory. Install the new version from a fresh directory; never overwrite another Skill or edited installation. For a same-marketplace Codex upgrade, update only this plugin's catalog entry to the new source and let native `plugin add` refresh its cache. Roll back by selecting the saved previous source and reinstalling through native commands. Do not delete target business data or construction state. Older tags and archives are unchanged.

保留旧包和源码安装目录。新版本使用新目录，避免覆盖其它 Skill 或本地修改。原市场内升级时，仅将本插件的目录项指向新源码，再用原生 `plugin add` 刷新缓存；回退时重新选择保存的旧源码并安装。不删除目标业务数据或构筑状态，旧标签与附件保持不变。
