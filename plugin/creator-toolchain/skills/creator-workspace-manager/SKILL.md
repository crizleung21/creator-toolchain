---
name: creator-workspace-manager
description: Inspect and maintain Creator Toolchain repository-local workspace state through the canonical surface registry, evidence-derived health, immutable proposal lifecycle, owner-gated reconciliation, read-only maintenance review, and explicitly confirmed non-destructive archives. Do not implement product backlog work or promote rules.
---

# creator-workspace-manager

Use this skill for `.creator/` state ownership, health, proposal review, reconciliation, maintenance, and archive governance. Do not use it to implement product work, bypass another skill's ownership, or auto-promote rules.

## Owned Root Surfaces

`creator-workspace-manager` owns nine root surfaces:

- `.creator/workspace.json`
- `.creator/projects.json`
- `.creator/entities.json`
- `.creator/state.json`
- `.creator/session-insights.json`
- `.creator/operator.json`
- `.creator/backlog.json`
- `.creator/surfaces.json`
- `.creator/decisions.json`

`creator-rule-router` owns `.creator/rules.json`. Workspace Manager may inspect that surface for health and references but must not mutate it.

## Modes

- `creator-workspace:surface list`
- `creator-workspace:surface validate`
- `creator-workspace:health-check`
- `creator-workspace:proposal list`
- `creator-workspace:proposal status`
- `creator-workspace:proposal preview`
- `creator-workspace:proposal apply`
- `creator-workspace:maintenance-review`
- `creator-workspace:archive plan`
- `creator-workspace:archive status`
- `creator-workspace:archive apply`
- `creator-workspace:session-insight stage-rule-proposal`

## Core Workflow

```text
inspect canonical registry
→ calculate evidence-derived health
→ discover immutable staged proposals
→ preview candidate state and checksums
→ verify owner and evidence
→ atomically apply or leave staged
→ append receipt and ledger evidence
→ recalculate health
```

## Deterministic Commands

```bash
python3 scripts/creator_surface_registry.py list --root .
python3 scripts/creator_surface_registry.py validate --root .
python3 scripts/creator_health_check.py --root .
python3 scripts/creator_health_check.py --root . --write
python3 scripts/creator_workspace_proposals.py list --root .
python3 scripts/creator_workspace_proposals.py status --root . --proposal PROPOSAL_PATH
python3 scripts/reconcile_creator_state.py preview --root . --proposal PROPOSAL_PATH
python3 scripts/reconcile_creator_state.py apply --root . --proposal PROPOSAL_PATH --actor ACTOR
python3 scripts/creator_workspace_maintenance.py review --root .
python3 scripts/creator_workspace_maintenance.py archive-plan --root . --target TARGET --actor ACTOR --reason REASON
python3 scripts/creator_workspace_maintenance.py archive-status --root . --proposal PROPOSAL_PATH
python3 scripts/creator_workspace_maintenance.py archive-apply --root . --proposal PROPOSAL_PATH --actor ACTOR --confirm ARCHIVE_ID
```

## Proposal Lifecycle

State proposals remain immutable with `status: staged`. Lifecycle status is derived from separate evidence:

```text
staged proposal
→ read-only preview
→ owner-gated atomic apply
→ immutable reconciliation receipt
→ applied status
```

Do not edit the proposal to claim it was applied. Do not apply a proposal twice.

## Health Contract

Health is calculated from current evidence and can be:

- `green`: no red or amber signals;
- `amber`: non-blocking risk such as stale behavior evidence or a stale plan;
- `red`: broken schema, pointer, ownership, package, mirror, or terminal-execution contract.

A stored health value is not authoritative until it has been recalculated.

## Maintenance and Archive Boundary

Maintenance review is read-only. It may list archive candidates, state fixes, rule proposals, and one next action. It must not execute backlog work.

Archive is non-destructive and two-step:

```text
archive-plan
→ review target, references, digest, and destination
→ archive-apply with exact proposal ID confirmation
→ atomic move, receipt, ledger, and health recalculation
```

Root state surfaces, control directories, referenced artifacts, symlinks, and changed targets cannot be archived. Deletion is not provided by this workflow.

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| surface list / validate | `references/state-surfaces.md` | `assets/surface-template.json` | `config/surface-registry.json`, `.creator/surfaces.json` |
| health-check | `references/health-maintenance.md` | `assets/health-report-template.json` | all root surfaces, `.creator/health/health-report.json` |
| proposal list / status | `references/proposal-lifecycle.md` | none | `.creator/state-proposals/`, `.creator/executions/*/state-update-proposal.json`, `.creator/reconciliation/` |
| proposal preview / apply | `references/proposal-lifecycle.md` | `assets/reconciliation-receipt-template.json` | `.creator/projects.json`, `.creator/state.json`, health and reconciliation evidence |
| maintenance-review | `references/health-maintenance.md`, `references/maintenance-archive.md` | `assets/maintenance-review-template.md` | read-only workspace evidence |
| archive plan / status / apply | `references/maintenance-archive.md` | `assets/archive-proposal-template.json` | non-root `.creator/` artifacts, `.creator/archive/`, `.creator/maintenance/` |
| session-insight stage-rule-proposal | `references/session-insight-rule-bridge.md` | none | `.creator/session-insights.json`; staged rule proposal only |

## Guardrails

- Use `config/surface-registry.json` as the only canonical root-surface registry.
- Preview state changes before apply.
- Require `creator-workspace-manager` ownership and evidence before mutation.
- Preserve proposals as immutable evidence and write separate receipts.
- Recalculate health after successful state or archive changes.
- Roll back all touched bytes when post-write validation fails.
- Do not silently archive or delete state.
- Do not implement backlog features during maintenance review.
- Do not mutate `.creator/rules.json` or auto-promote a rule.

See `references/state-surfaces.md`, `references/health-maintenance.md`, `references/proposal-lifecycle.md`, `references/maintenance-archive.md`, and `references/session-insight-rule-bridge.md`.
