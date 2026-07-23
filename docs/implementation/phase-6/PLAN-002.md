# PLAN-002 — Phase 6 Skill Integration and Audit Runtime

## Status

`IN_PROGRESS`

## Goal

Complete Phase 6 by integrating `creator-orchestrator`, `creator-skill-workbench`, and `creator-evidence-audit`; provide deterministic Audit judgment, immutable correction, remediation, and execution-handoff runtime; regenerate the Plugin mirror and package evidence; and satisfy all Phase 6 exit gates.

## Scope

- Replace the undefined release route with explicit deterministic release-script coordination.
- Add complete Mode-to-Resource Maps to the three remaining Skills.
- Integrate the approved 100-point Workbench score model and progressive-disclosure contracts.
- Add severity definitions, confidence bands, evidence-quality levels, disagreement states, portable citation format, deterministic risk formula, correction addenda, and supersession policy.
- Add `scripts/creator_evidence_audit.py` for immutable Findings, remediation tasks, correction addenda, handoffs, and read-only status.
- Regenerate the three packaged Skill mirrors and refresh package/behavior/health evidence.

## Boundaries

- Preserve exactly seven core Skills.
- Audit never mutates its target or executes remediation.
- Issued Findings remain byte-immutable.
- Corrections are append-only addenda.
- Plugin release support remains unavailable until `scripts/release_creator_toolchain.py` is implemented in Phase 8.
- Historical Behavior evidence remains stale until Phase 7 reruns all cases.

## Acceptance Criteria

- Every one of the seven Skills has a valid Mode-to-Resource Map.
- Routing selects one primary workflow and disambiguates single-skill versus system audit.
- Evidence Audit route resolves to an available deterministic runtime.
- Workbench scores are deterministic and evidence-backed.
- Audit Findings contain portable evidence citations and calibrated judgment fields.
- Risk calculation is deterministic.
- Correction addenda preserve original Finding bytes.
- Execution handoffs target only `creator-execution-cycle`.
- Authoritative and packaged Skill trees are byte-equivalent.
- Exact package integrity, reproducible ZIP, repository/state/plugin validation, and full CI pass.
