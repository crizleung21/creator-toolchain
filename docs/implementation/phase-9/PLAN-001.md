# PLAN-001 — Phase 9 Documentation and Final Reconciliation

## Status

`IN_PROGRESS`

## Goal

Complete all user-facing and operator-facing documentation, validate every documented command and capability claim, regenerate final package and behavior evidence after packaged-document changes, and reconcile the full approved `IMPLEMENTATION__PLAN.md` against the implemented repository before publication.

## Scope

1. Update root and packaged README／CHANGELOG content for `v1.1.0`.
2. Update `AGENTS.md`, architecture, state, QA, package, and migration documentation.
3. Add tested operations guides for Bootstrap, Execution Lifecycle, Recovery, Release, and Troubleshooting.
4. Add documentation-contract tests for commands, paths, capability claims, schema `0.4.0`, generated registries, and deprecated terminology.
5. Regenerate Package Integrity after packaged-document changes.
6. Rerun all 34 behavior cases against the final package payload.
7. Recalculate repository Health to Green.
8. Rebuild, clean-install, and validate exactly seven Skills.
9. Produce Phase 9 Reconciliation, Summary, Gate Matrix, and the full Plan-versus-Actual final reconciliation.
10. Run the final Phase 9 Head CI and post-merge `main` CI before tagging or publishing.

## Acceptance Criteria

- Every documented command is syntactically validated or executed by tests.
- No active documentation references the undefined `Phase 5 plugin workflow`.
- No active lifecycle documentation uses deprecated `Apply`／`Qualify` terminology.
- The canonical Surface Registry has one machine-readable source and generated documentation remains current.
- Capability documentation matches implemented scripts and seven Skills.
- All examples use state schema `0.4.0`.
- Package, behavior, health, release, clean-install, and CI evidence are current for the final documentation payload.
- GATE-01 through GATE-18 are recorded as PASS with evidence.
- Final reconciliation records planned versus actual work, deviations, deferred P2 scope, residual risks, rollback boundaries, and publication readiness.

## Publication Boundary

No tag or GitHub Release is created until this phase, the final Phase 9 Head CI, and the post-merge `main` CI all succeed.
