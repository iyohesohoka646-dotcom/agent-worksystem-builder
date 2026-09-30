# Delivery status

Release candidate: `0.1.0-alpha.1` plugin / `0.1.0a1` Python package, checked on 2026-09-30. The local implementation and distribution checks below passed. Complete v0.1 task and compatibility qualification remains open.

| Area | Observed evidence | State |
|---|---|---|
| Windows runtime | 62 tests passed with Python 3.11.9, including real processes, CLI, recovery and review fault injection | Passed |
| Construction example | Actual failed candidate, rollback, correction, independent labels, simulated reviewer and fresh-process resume | Passed on synthetic material |
| Native Codex plugin | Codex CLI 0.158.0 added the marketplace, installed the ZIP, listed the enabled plugin and ran its cached CLI | Passed |
| Skill discovery | Native app-server `skills/list` returned the enabled `agent-worksystem-builder:building-agent-worksystems` from installed cache | Passed |
| Portable Skill and wheel | Skill validator, archive extraction/entrypoint and Python wheel build | Passed |
| Codex live inference | One corrected structured-output probe reached turn start and reconnection attempts, then hit its 120-second deadline | Pending; transport timeout |
| Ollama | Local endpoint refused connection; transport normalization and total deadline covered by fixtures | Pending real inference |
| Claude Code | Executable unavailable in this environment | Pending host checks |
| Skill behavior | Artifact-based evaluation harness implemented; matched baseline/generic/Builder matrix not run | Pending |
| Real user task | User-held material and task acceptance not supplied | Pending |
| Linux | GitHub Actions matrix prepared; local session ran on Windows | Pending CI |
| Official plugin directory | Upload package, listing, icon and submission notes prepared | Pending platform identity/access, scans and review |

Local receipts are stored under `reports/runtime-tests.xml`, `reports/verification.json`, `reports/plugin-install.json` and the demonstration workspace; raw logs and user workspaces are excluded from public source. ZIP file lists and hashes are supplied in the release's `.manifest.json` receipt. Source planning documents remain in the local development project.

The final review identified eight consequential issues. Regression checks now cover transactional accepted-spec recovery, stale candidate revisions, uncertain side-effect replay, verification/snapshot byte consistency, Windows process-job assignment, Windows path aliases, worker failure checkpointing and HTTP total deadlines. No complete-model or task-acceptance claim is derived from fixture success.
