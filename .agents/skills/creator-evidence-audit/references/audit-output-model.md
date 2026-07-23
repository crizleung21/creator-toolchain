# Audit Output Model

## Findings

Immutable JSON records containing observation, interpretation, judgment, severity, confidence band, evidence quality, citations, disagreements, limitations, actor, and timestamp.

## Remediation Tasks

Bounded actions linked to one Finding. Risk score is deterministic and every task has a verification gate, rollback criterion, and `creator-execution-cycle` handoff.

## Correction Addenda

New evidence never rewrites the original Finding. An addendum records the original SHA-256, correction type, updated judgment, resulting effective status, reason, actor, and timestamp.

## Execution Handoff

Contains selected Findings, remediation tasks, dependency graph, risks, verification gates, rollback criteria, and explicit authorization status.

## Status

Effective Finding status is derived from immutable Findings plus ordered addenda.
