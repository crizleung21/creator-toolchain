---
name: creator-skill-workbench
description: Discover, scaffold, distill, restructure, score, and audit one Codex Skill with deterministic progressive-disclosure, reference-integrity, state-safety, naming-collision, and acceptance-test checks. Use for a single skill; route repository or package audits to creator-evidence-audit.
---

# creator-skill-workbench

Use this skill to design or evaluate one focused Codex Skill. It does not perform a system-wide evidence audit and does not overwrite an existing skill name.

## Modes

- `creator-skill:discover`
- `creator-skill:scaffold`
- `creator-skill:distill`
- `creator-skill:restructure`
- `creator-skill:score`
- `creator-skill:audit`

## Deterministic Scoring

```bash
python3 scripts/creator_skill_workbench.py score \
  --root . \
  --skill .agents/skills/SKILL-NAME

python3 scripts/creator_skill_workbench.py score-all --root .
```

The approved model totals 100 points:

| Dimension | Weight |
|---|---:|
| Trigger precision | 15 |
| Boundary clarity | 15 |
| Workflow completeness | 20 |
| Progressive disclosure | 15 |
| State safety | 10 |
| Reference integrity | 10 |
| Acceptance tests | 10 |
| Naming and collision | 5 |

Every deduction includes a check ID and concrete evidence. The same repository bytes must produce the same score report.

## Skill Anatomy

| Role | Path | Purpose |
|---|---|---|
| Entry point | `SKILL.md` | trigger, modes, boundaries, output, resource map |
| Workflow | `references/*.md` | operational detail loaded by mode |
| Framework | `references/*.md` | durable domain knowledge |
| Asset | `assets/*` | reusable output shape |
| Runtime | `scripts/*.py` | deterministic support where needed |
| Tests | `tests/test_*.py` | acceptance and negative-path evidence |

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| discover | `references/skill-spec.md`, `references/workbench-operations.md` | `assets/skill-spec-template.yaml` | read existing skill names and request context |
| scaffold | `references/skill-spec.md`, `references/progressive-disclosure.md` | `assets/skill-spec-template.yaml` | create one approved skill tree; no unrelated state mutation |
| distill | `references/progressive-disclosure.md`, `references/workbench-operations.md` | none | read one source skill |
| restructure | `references/progressive-disclosure.md`, `references/workbench-operations.md` | `assets/score-report-template.json` | modify only the selected skill after authorization |
| score | `references/compliance-score.md`, `references/skill-spec.md` | `assets/score-report-template.json` | read one skill and repository tests |
| audit | `references/compliance-score.md`, `references/workbench-operations.md` | `assets/score-report-template.json` | read one skill; system audits route elsewhere |

## Required Output

Depending on mode, produce:

- a skill specification;
- a collision-safe scaffold plan;
- a progressive-disclosure restructuring plan;
- an evidence-backed 100-point score report;
- remediation actions and verification criteria.

## Acceptance Tests

- frontmatter name and description are valid;
- trigger and not-for boundary are explicit;
- duplicate names are rejected or renamed;
- every referenced resource exists;
- workflow detail is progressively disclosed;
- state mutation and ownership are explicit;
- acceptance tests or verification gates exist;
- every score deduction cites observable evidence.

## Guardrails

- Do not overwrite or duplicate an existing skill name.
- Do not put all domain knowledge in one oversized `SKILL.md`.
- Do not claim missing references exist.
- Do not silently mutate `.creator/` state or files owned by another workflow.
- Do not use this skill for repository-wide, system-wide, or package-wide evidence audits.
- Do not package a weak or non-compliant skill without explicit exception evidence.

See `references/skill-spec.md`, `references/compliance-score.md`, `references/workbench-operations.md`, and `references/progressive-disclosure.md`.
