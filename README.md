# creator-toolchain

`creator-toolchain` is a Codex-native skill suite that adapts high-value workflow patterns from ChristopherKahler's PAUL, SEED, BASE, CARL, Skillsmith, and AEGIS into a Creator-first system.

It is not a direct Claude Code clone. The active architecture is:

```text
Codex Skills
+ repo-local .creator/ state
+ CARL-style domain rules
+ Skillsmith-style skill factory
+ AEGIS-style evidence-first audit
+ optional Codex Plugin package
```

## Skill Suite

| Phase | Skill | Purpose |
|---:|---|---|
| 1 | `creator-orchestrator` | Route user intent to the right workflow. |
| 1 | `creator-seed-incubator` | Turn raw ideas into typed `PLANNING.md` files. |
| 1 | `creator-paul-loop` | Execute accepted plans through Plan, Apply, Qualify, Unify. |
| 2 | `creator-base-workspace` | Manage repo-local state, pulse, groom, drift, and surfaces. |
| 3 | `creator-rule-router` | Load, stage, recall, exclude, and audit domain rules. |
| 3 | `creator-skillsmith-factory` | Discover, scaffold, distill, score, and audit Codex skills. |
| 4 | `creator-aegis-audit` | Produce evidence-first audits and PAUL-ready remediation handoffs. |

## Quick Start

1. Use `creator-orchestrator` when the workflow is unclear.
2. Use `creator-seed-incubator` for raw ideas.
3. Use `creator-paul-loop` after a plan is accepted.
4. Run `python3 scripts/validate_creator_toolchain.py` before treating the repo as release-ready.

## Current Package

The repo contains a local skill suite under `.agents/skills/` and a plugin packaging scaffold under `plugin/creator-toolchain/`.

Plugin packaging is a Phase 5 surface. The manifest is a draft until validated against the current Codex plugin schema.
