# PLAN-002 — Phase 4 Workspace Manager Integration and Maintenance Governance

## Status

`IN_PROGRESS`

## Goal

Complete Phase 4 by integrating the deterministic registry, health, proposal, reconciliation, maintenance, and archive contracts into `creator-workspace-manager` and the packaged plugin.

## Tasks

| Task | Acceptance | Verification | Status |
|---|---|---|---|
| Proposal lifecycle | List and inspect staged/applied/invalid proposals without mutating proposal evidence | Unit tests and schema validation | `IN_PROGRESS` |
| Maintenance review | Produce a read-only report containing health, proposal counts, archive candidates, state fixes, rule proposals, and one next action | Read-only byte comparison | `IN_PROGRESS` |
| Archive guardrails | Require a staged proposal and exact confirmation; block root/control/referenced/symlink targets; move without deletion; roll back on failure | Positive and negative archive tests | `IN_PROGRESS` |
| Workspace Manager Skill | Add modes, commands, Mode-to-Resource Map, ownership boundaries, and current schema assets | Skill contract and mirror tests | `IN_PROGRESS` |
| Plugin evidence | Regenerate mirror, package-integrity report, behavior freshness status, and health cache for the final payload | Full CI and package candidate | `IN_PROGRESS` |

## Boundaries

- Preserve the seven-skill architecture.
- Do not implement backlog work during maintenance.
- Do not mutate `.creator/rules.json` or promote rule proposals.
- Do not archive root state surfaces or delete workspace evidence.
- Keep proposals immutable; lifecycle status is derived from separate receipts.
- Phase 5 owns semantic rule-conflict handling.

## Rollback

Revert this Slice or squash PR #5. Archive apply and state reconciliation both retain operation-level rollback paths.
