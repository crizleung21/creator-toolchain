# Creator Toolchain Creator-Native Naming Migration Plan

## Goal

Replace active upstream-derived product names with descriptive Creator-native workflow names while preserving source research, archives, completed project records, and append-only ledgers.

## Naming Contract

| Capability | Previous interface | Creator-native interface |
|---|---|---|
| Intake | `creator-seed-incubator` | `creator-intake-planner` |
| Execution | `creator-paul-loop` | `creator-execution-cycle` |
| Workspace | `creator-base-workspace` | `creator-workspace-manager` |
| Rules | CARL-derived labels | Rule Governance / `creator-rule-router` |
| Skill creation | `creator-skillsmith-factory` | `creator-skill-workbench` |
| Audit | `creator-aegis-audit` | `creator-evidence-audit` |

Commands, artifacts, state fields, QA identifiers, plugin metadata, and generated skill paths must use the Creator-native vocabulary. No callable compatibility aliases are retained.

## Tasks

1. Add failing naming, schema, mirror-cleanup, and legacy-marker tests.
2. Rename authoritative skills, commands, templates, references, and project-type generator.
3. Upgrade active `.creator` state to schema `0.2.0` and preserve completed histories.
4. Update active docs, QA contracts, fixtures, and validator allowlists.
5. Regenerate the plugin mirror and release evidence at version `1.0.0-draft.1`.
6. Run full qualification and create Reconciliation and Summary artifacts.

## Acceptance

- seven authoritative and generated skills use the new names;
- 13 project types retain three reference files each;
- active surfaces contain no legacy product markers outside explicit provenance/history allowlists;
- tests, state/repo/plugin validation, plugin schema validation, and payload hashes pass;
- completed ledger files remain byte-for-byte unchanged.

## Rollback

Revert the migration commits as a unit. Do not restore only selected old skill directories or mix state schema versions.
