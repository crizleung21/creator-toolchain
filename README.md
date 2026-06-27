# creator-toolchain

`creator-toolchain` is a Codex-native skill suite for turning creator ideas into plans, executing accepted work, maintaining repository state, routing rules, building skills, and auditing evidence. Upstream research remains documented in the [source map](docs/source-analysis/upstream-toolchain-map.md).

It is not a direct Claude Code clone. The active architecture is:

```text
Codex Skills
+ repo-local .creator/ state
+ domain-rule governance
+ skill creation and audit workbench
+ evidence-first workflow audit
+ optional Codex Plugin package
```

## Skill Suite

| Phase | Skill | Purpose |
|---:|---|---|
| 1 | `creator-orchestrator` | Route user intent to the right workflow. |
| 1 | `creator-intake-planner` | Turn raw ideas into typed `PLANNING.md` files. |
| 1 | `creator-execution-cycle` | Execute accepted plans through Plan, Execute, Verify, Reconcile. |
| 2 | `creator-workspace-manager` | Manage repo-local state, health, maintenance, divergence, and surfaces. |
| 3 | `creator-rule-router` | Load, stage, recall, exclude, and audit domain rules. |
| 3 | `creator-skill-workbench` | Discover, scaffold, distill, score, and audit Codex skills. |
| 4 | `creator-evidence-audit` | Produce evidence-first audits and execution-ready remediation handoffs. |

## Quick Start

1. Use `creator-orchestrator` when the workflow is unclear.
2. Use `creator-intake-planner` for raw ideas.
3. Use `creator-execution-cycle` after a plan is accepted.
4. Run `python3 scripts/validate_creator_toolchain.py` before treating the repo as release-ready.

## Current Package

The authoritative development skill suite lives under `.agents/skills/`. The installable mirror under `plugin/creator-toolchain/skills/` is generated with:

```bash
python3 scripts/materialize_project_type_refs.py
python3 scripts/sync_plugin_skills.py --write
python3 scripts/sync_plugin_skills.py --check
```

Do not hand-edit the generated plugin skill mirror. Do not enable repo-local and plugin copies simultaneously except in an explicit provenance test.

Plugin packaging is a Phase 5 surface. The draft manifest has passed local bundled validation, isolated install, and plugin-only discovery on Codex CLI `0.142.3`; public release remains gated by license and manual Codex App acceptance.
