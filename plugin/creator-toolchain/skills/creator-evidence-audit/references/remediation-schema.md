# Remediation and Handoff Contract

## Remediation Task

```text
task_id
source_finding
remediation_type
intervention_level: suggesting|planning|authorizing
blast_radius
coupling_risk
regression_risk
risk_score
risk_level
confidence and confidence_band
evidence_sources
verification_gate
rollback_criteria
recommended_action
handoff: creator-execution-cycle
```

Evidence Audit does not accept `executing` as an intervention level. Execution occurs only in the Execution Cycle after authorization.

## Risk Formula

```text
low=1, medium=2, high=3
risk_score = blast_radius*4 + coupling_risk*3 + regression_risk*3
1–14 low; 15–22 medium; 23–30 high
```

## Handoff

A handoff must reference existing Findings and remediation tasks, include verification and rollback criteria, and state `planned` or `approved`. `approved` requires an actor and timestamp.
