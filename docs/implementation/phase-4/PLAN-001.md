# PLAN-001 — Phase 4 Registry, Health, and Reconciliation Foundation

## Status

`IN_PROGRESS`

## Goal

Begin Phase 4 by replacing duplicated surface definitions with one machine-readable registry, deriving workspace health from current evidence, and adding previewable, owner-gated state reconciliation for Intake and Execution proposals.

## Scope

- Add `config/surface-registry.json` as the canonical 10-surface registry.
- Materialize `.creator/surfaces.json`, the bootstrap template, and human-readable documentation from the registry.
- Refactor state validation to consume the canonical registry.
- Add a deterministic health engine with red/amber/green signals and a persisted evidence report.
- Correct the live false-green state to amber because behavior evidence is stale for the current package payload.
- Add dry-run and atomic apply support for `register-project` and `update-project-execution` proposals.
- Preserve proposal immutability and write a separate reconciliation receipt and append-only ledger event.
- Add rollback tests and CI drift checks.

## Explicit Boundary

This slice does not yet integrate the authoritative `creator-workspace-manager` Skill or regenerate the plugin mirror and package report. It also does not implement Phase 5 rule-conflict semantics; health only consumes rule findings already exposed by the current state validator.

## Acceptance Criteria

- Given the registry config, generated state, template, and documentation must match exactly.
- Given stale behavior evidence, repository health must not remain green.
- Given a proposal owned by another skill, preview and apply must fail without writes.
- Given a valid registration proposal, preview must be read-only and apply must atomically update `.creator/projects.json`.
- Given an injected post-project failure, project bytes must be restored exactly.
- Given a successful apply, a receipt, reconciliation ledger event, health report, and validated state update must exist.
- All existing and new tests and CI gates must pass.

## Next Phase 4 Slice

Integrate `creator-workspace-manager`, complete maintenance and archive boundaries, add proposal discovery/status workflows, regenerate the plugin mirror and package evidence, and satisfy all Phase 4 exit gates.
