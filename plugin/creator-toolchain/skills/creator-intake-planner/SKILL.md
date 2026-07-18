---
name: creator-intake-planner
description: Turn raw creator, software, workflow, image, video, character, presentation, prompt, campaign, or research ideas into canonical, acceptance-driven Intake packages; explicitly approve scaffold-only or creator-execution-cycle handoff; and stage workspace registration proposals without implementing product work.
---

# creator-intake-planner

Use this skill for typed idea intake, deterministic planning, read-only status and resume, custom project-type governance, explicit approval, planning-only scaffolds, and execution handoff.

## Modes

- `creator-intake:start`
- `creator-intake:status`
- `creator-intake:add-type`
- `creator-intake:approve`
- `creator-intake:scaffold`
- `creator-intake:handoff`

## Core Workflow

```text
raw idea
→ select one project type
→ create the canonical seven-artifact Intake package
→ run the Planning Quality Gate
→ record explicit approval
→ scaffold-only OR handoff-to-execution
→ stage a creator-workspace-manager registration proposal
```

## Canonical Artifacts

```text
.creator/plans/{project_slug}/
├── project.json
├── activity_ledger.jsonl
├── INTAKE-STATE.md
├── PLANNING.md
├── DECISIONS.md
├── OPEN-QUESTIONS.md
└── HANDOFF.md
```

The planning directory uses an exact allowlist. Implementation files do not belong in Intake.

## Deterministic Operations

Repository-local workflows use:

```bash
python3 scripts/creator_intake_artifacts.py create --root . --request REQUEST.json
python3 scripts/creator_intake_artifacts.py status --root . --project PROJECT_SLUG
python3 scripts/creator_intake_workflow.py approve --root . --project PROJECT_SLUG --actor ACTOR --decision scaffold-only
python3 scripts/creator_intake_workflow.py scaffold --root . --project PROJECT_SLUG
python3 scripts/creator_intake_workflow.py approve --root . --project PROJECT_SLUG --actor ACTOR --decision handoff-to-execution
python3 scripts/creator_intake_workflow.py handoff --root . --project PROJECT_SLUG
python3 scripts/creator_intake_workflow.py proposal --root . --project PROJECT_SLUG
```

Plugin-only use must follow the same contracts using the packaged assets and references. Do not invent approval, mutate `.creator/projects.json`, or implement the project inside Intake.

## Approval Gate

Approval requires `pass` or `pass_with_non_blocking_questions`. Record:

- actor;
- decision: `scaffold-only` or `handoff-to-execution`;
- timestamp;
- immutable decision entry;
- append-only ledger event.

A failed gate or unresolved blocking question prohibits approval.

## Output Boundaries

- Scaffold output contains planning documents only and explicitly states that execution is unauthorized.
- Execution handoff targets only `creator-execution-cycle` and requires prior `handoff-to-execution` approval.
- Workspace registration is a staged proposal owned by `creator-workspace-manager`; Intake never writes `.creator/projects.json` directly.

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| start | `references/intake-artifact-contract.md`, `references/planning-quality-gate.md`, selected type references | `assets/project-template.json`, `assets/activity-ledger-event-template.json`, `assets/decisions-template.md` | `.creator/plans/{project_slug}/` |
| status | `references/intake-status-output.md`, `references/intake-artifact-contract.md` | none | read-only plan package |
| add-type | `references/add-type-workflow.md`, `references/project-types.md` | `assets/custom-type-template.md` | project-type registry proposal |
| approve | `references/approval-workflow.md`, `references/planning-quality-gate.md` | `assets/state-registration-proposal-template.json` | plan package and staged proposal |
| scaffold | `references/scaffolding-workflow.md` | `assets/project-readme-template.md` | `.creator/scaffolds/{project_slug}/` |
| handoff | `references/handoff-workflow.md`, `references/state-registration-proposal.md` | `assets/execution-handoff-template.json`, `assets/handoff-template.md` | `.creator/handoffs/{project_id}.json` |

## Guardrails

- Do not execute implementation work.
- Do not approve a failed plan.
- Do not treat non-blocking questions as blockers.
- Do not silently change approval decisions.
- Do not overwrite an existing Intake package, scaffold, or handoff.
- Do not silently mutate `.creator/projects.json` or any surface owned by another skill.
- Preserve one project ID across every artifact and handoff.
- Load only the selected project-type references.

See `references/intake-artifact-contract.md`, `references/planning-quality-gate.md`, `references/approval-workflow.md`, `references/scaffolding-workflow.md`, `references/handoff-workflow.md`, `references/state-registration-proposal.md`, `references/project-types.md`, and `references/type-loadouts.md`.
