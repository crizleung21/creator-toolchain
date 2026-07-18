# PLAN-002 — Phase 4 Workspace Manager Integration and Maintenance Governance

## Status

`DONE`

## Goal

Complete Phase 4 by integrating the deterministic registry, health, proposal, reconciliation, maintenance, and archive contracts into `creator-workspace-manager` and the packaged plugin.

## Tasks

| Task | Acceptance | Verification | Status |
|---|---|---|---|
| Proposal lifecycle | List and inspect staged/applied/invalid proposals without mutating proposal evidence | Unit tests and schema validation | `DONE` |
| Maintenance review | Produce a read-only report containing health, proposal counts, archive candidates, state fixes, rule proposals, and one next action | Read-only byte comparison | `DONE` |
| Archive guardrails | Require a staged proposal and exact confirmation; block root/control/referenced/symlink targets; move without deletion; roll back on failure | Positive and negative archive tests | `DONE` |
| Workspace Manager Skill | Add modes, commands, Mode-to-Resource Map, ownership boundaries, and current schema assets | Skill contract and mirror tests | `DONE` |
| Plugin evidence | Regenerate mirror, package-integrity report, behavior freshness status, and health cache for the final payload | Full CI and package candidate | `DONE` |

## Boundaries Preserved

- The seven-skill architecture remains unchanged.
- Maintenance does not implement backlog work.
- Workspace Manager does not mutate `.creator/rules.json` or promote rule proposals.
- Archive does not delete evidence or move root state surfaces.
- State proposals remain immutable; lifecycle status is derived from receipts.
- Phase 5 owns semantic rule-conflict handling.

## Rollback

Revert the Phase 4 squash commit. State reconciliation and archive apply retain operation-level byte restoration on failure.
