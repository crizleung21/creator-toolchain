# Evidence Audit Pipeline

## Phase 0 — Context and Threat Model

Define target, decision use, scope, exclusions, risks, expected evidence, and prohibited mutations.

## Phase 1 — Evidence Inventory

Collect repository-relative files, Schemas, test output, hashes, source references, and known limitations. Record missing evidence rather than inventing it.

## Phase 2 — Specialized Review

Review each relevant domain using the same observation, interpretation, judgment, severity, confidence, and evidence-quality contract.

## Phase 3 — Reality Gap

Compare claimed behavior with executable or byte-level evidence.

## Phase 4 — Adversarial Review

Challenge assumptions, seek counterevidence, and record disagreement states.

## Phase 5 — Synthesis

Issue immutable Findings with evidence citations and limitations.

## Phase 6 — Remediation Knowledge

Create bounded remediation tasks without changing the target.

## Phase 7 — Risk and Guardrails

Calculate blast radius, coupling risk, regression risk, verification gates, and rollback criteria.

## Phase 8 — Execution Handoff

Create a planned or explicitly approved handoff to `creator-execution-cycle`. Audit itself does not execute remediation.
