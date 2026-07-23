---
name: creator-evidence-audit
description: Audit Creator Toolchain repositories, systems, packages, workflows, and multi-surface artifacts; issue immutable evidence-backed findings, deterministic remediation plans, correction addenda, and creator-execution-cycle handoffs. Use for system-level audit; do not mutate the audit target.
---

# creator-evidence-audit

Use this skill for evidence-first repository, system, package, or multi-surface audit. A single-skill build or score belongs to `creator-skill-workbench`.

## Modes

- `creator-audit:single-agent`
- `creator-audit:staged`
- `creator-audit:parallel` only when explicitly requested
- `creator-audit:issue-finding`
- `creator-audit:plan-remediation`
- `creator-audit:add-correction`
- `creator-audit:create-handoff`
- `creator-audit:status`

## Phase Pipeline

```text
0 Context and threat model
→ 1 Evidence inventory
→ 2 Specialized review
→ 3 Claimed-versus-actual reality check
→ 4 Adversarial review
→ 5 Findings synthesis
→ 6 Remediation knowledge
→ 7 Risk, verification, and rollback
→ 8 creator-execution-cycle handoff
```

## Deterministic Runtime

```bash
python3 scripts/creator_evidence_audit.py --help
```

The runtime writes audit evidence only under:

```text
.creator/audits/{audit_id}/
├── findings/
├── remediation/
├── addenda/
└── handoffs/
```

Evidence citations use repository-relative paths, line ranges, and SHA-256. Issued Findings are immutable; new evidence creates an addendum.

## Judgment Contract

Every Finding separates:

- observation: directly evidenced fact;
- interpretation: what the fact plausibly means;
- judgment: the decision-relevant conclusion;
- severity definition;
- numeric confidence and confidence band;
- evidence quality;
- disagreement state, disagreements, and limitations.

Risk score is deterministic:

```text
blast_radius*4 + coupling_risk*3 + regression_risk*3
```

## Output Model

- Findings: immutable diagnosis with citations and calibrated judgment.
- Remediation: suggested, planned, or authorized work with risk, verification, and rollback.
- Correction Addenda: clarify, correct, or supersede without rewriting history.
- Execution Handoff: dependency graph and authorized boundary for `creator-execution-cycle`.

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| single-agent | `references/audit-pipeline.md`, `references/judgment-model.md`, `references/evidence-citations.md` | `assets/findings-template.md` | read audit target; write `.creator/audits/{audit_id}/` only |
| staged | `references/audit-pipeline.md`, `references/audit-output-model.md` | all output assets | read target; write audit evidence only |
| parallel | `references/audit-pipeline.md`, `references/judgment-model.md` | `assets/findings-template.md` | read-only target; merge evidence deterministically |
| issue-finding | `references/judgment-model.md`, `references/evidence-citations.md` | `assets/findings-template.md` | immutable finding file |
| plan-remediation | `references/remediation-schema.md`, `references/judgment-model.md` | `assets/remediation-guidance-template.md` | remediation evidence only |
| add-correction | `references/correction-policy.md`, `references/evidence-citations.md` | `assets/correction-addendum-template.json` | append addendum; original finding unchanged |
| create-handoff | `references/remediation-schema.md`, `references/audit-output-model.md` | `assets/execution-handoff-template.md` | execution handoff evidence only |
| status | `references/correction-policy.md` | none | read-only audit evidence |

## Acceptance Tests

- the audit target bytes remain unchanged;
- every Finding has direct citations and calibrated confidence;
- observation, interpretation, and judgment are distinct fields;
- risk scores are reproducible;
- correction addenda preserve original Finding bytes;
- execution handoff targets only `creator-execution-cycle`;
- executing remediation is rejected inside Audit;
- unsupported certainty and evidence-free critical severity are not accepted.

## Guardrails

- Do not mutate the audit target.
- Do not rewrite or delete an issued Finding.
- Do not apply remediation directly.
- Do not mark every suspected issue critical.
- Do not conceal disagreements, limitations, or weak evidence.
- Do not treat a planned handoff as execution authorization.
- Do not use this workflow for a single-skill score when Workbench is sufficient.

See `references/audit-pipeline.md`, `references/audit-output-model.md`, `references/remediation-schema.md`, `references/judgment-model.md`, `references/correction-policy.md`, and `references/evidence-citations.md`.
