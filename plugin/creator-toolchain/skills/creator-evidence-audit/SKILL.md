---
name: creator-evidence-audit
description: Audit Creator Toolchain projects, Codex skills, prompts, slide decks, AI image/video workflows, character systems, state files, scripts, and plugin packages, then produce evidence-based findings and creator-execution-cycle remediation plans.
---

# creator-evidence-audit

Use this skill for evidence-first audit and remediation planning.

## Modes

- single-agent audit
- staged audit
- parallel subagent audit when explicitly requested by the user

## Phase Pipeline

```text
Phase 0 — Context and Threat Model
Phase 1 — Repository Signal Inventory
Phase 2 — Specialized Evidence Review
Phase 3 — Cross-Domain Reality Check
Phase 4 — Adversarial Review
Phase 5 — Synthesis
Phase 6 — Transform to Remediation Knowledge
Phase 7 — Change Risk Validation and Guardrails
Phase 8 — Execution Planning and Execution Handoff
```

## Output Model

- Findings: diagnosis, evidence, confidence, and disagreements.
- Remediation Guidance: playbooks, examples, and guardrails.
- Execution Handoff: dependency graph, risk, rollback, and verification gates.

## Guardrails

- Audit does not directly mutate target files.
- Findings are immutable after issue; corrections are addenda.
- `remediation_type` describes the changed surface.
- `intervention_level` describes audit agency: suggesting, planning, authorizing, executing.
- Executing requires explicit user approval and normally hands off to `creator-execution-cycle`.

See `references/audit-pipeline.md` and `references/audit-output-model.md`.
