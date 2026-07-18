# PLAN-001 — Phase 6 Routing and Workbench Foundation

## Status

`IN_PROGRESS`

## Goal

Begin Phase 6 by replacing ambiguous workflow routing with a deterministic precedence contract, adding reproducible Skill Workbench scoring, and establishing formal Audit output Schemas without changing the packaged Skills before their contracts are integrated.

## Scope

- Add a single machine-readable routing table and one-primary-workflow router.
- Replace the undefined release route with deterministic release-script coordination and an explicit capability gap until Phase 8.
- Make skill-build and skill-audit requests route to Skill Workbench while system/package audits route to Evidence Audit.
- Add the approved 100-point Workbench scoring model with evidence-backed deductions.
- Add formal Schemas for Audit Findings, Remediation, Correction Addenda, and Execution Handoff.
- Add unit tests and Phase 6 execution evidence.

## Explicit Boundary

This slice does not yet modify `creator-orchestrator`, `creator-skill-workbench`, or `creator-evidence-audit` authoritative Skill files or the Plugin mirror. Skill integration, Mode-to-Resource Maps, full Audit judgment logic, package regeneration, and final Phase 6 evidence remain for Slice 2.

## Acceptance Criteria

- Every routing fixture selects exactly one primary workflow.
- Skill audit requests resolve to `creator-skill-workbench`; repository/package audit requests resolve to `creator-evidence-audit`.
- Plugin release requests no longer reference an undefined phase workflow.
- Workbench dimension weights total 100 and every deduction includes evidence.
- Broken references and naming collisions reduce the Workbench score deterministically.
- All four Audit Schemas accept valid examples and reject malformed examples.
- Full repository CI passes without changing the current Plugin payload.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Next Slice

Integrate the three remaining Skills, complete all Mode-to-Resource Maps, implement the Audit judgment and correction model, regenerate the Plugin mirror and package report, and satisfy every Phase 6 exit gate.
