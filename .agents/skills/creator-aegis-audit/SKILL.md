---
name: creator-aegis-audit
description: Audit Creator Toolchain projects, Codex skills, prompts, slide decks, AI image/video workflows, character systems, state files, scripts, and plugin packages, then produce evidence-based findings and creator-paul-loop remediation plans.
---

# creator-aegis-audit

Use this skill for evidence-first audit and remediation planning.

## Modes

- single-agent audit
- staged audit
- parallel subagent audit when explicitly requested by the user

## Phase Pipeline

```text
Phase 0 — Context and Threat Model
Phase 1 — Automated Signal Gathering
Phase 2 — Deep Domain Audits
Phase 3 — Reality Gap Analysis
Phase 4 — Adversarial Review
Phase 5 — Synthesis
Phase 6 — Transform to Remediation Knowledge
Phase 7 — Change Risk Validation and Guardrails
Phase 8 — Execution Planning and PAUL Handoff
```

## Layer Model

- Layer A: diagnosis, findings, evidence, confidence, disagreements.
- Layer B: remediation knowledge, playbooks, examples, guardrails.
- Layer C: execution orchestration, dependency graph, risk, rollback, PAUL handoff.

## Guardrails

- Audit does not directly mutate target files.
- Layer A is immutable after issue; corrections are addenda.
- `remediation_type` describes the changed surface.
- `intervention_level` describes audit agency: suggesting, planning, authorizing, executing.
- Executing requires explicit user approval and normally hands off to `creator-paul-loop`.

See `references/aegis-pipeline.md`.
