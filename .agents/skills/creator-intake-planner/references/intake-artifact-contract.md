# Intake Artifact Contract

## Canonical Directory

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

The directory is created through a hidden staging directory and one atomic replacement. Duplicate creation is rejected. Status and resume inspection are read-only.

## Identity

- `project.json` owns the canonical `PROJECT-*` identifier.
- `INTAKE-STATE.md`, `PLANNING.md`, `DECISIONS.md`, and `HANDOFF.md` preserve the same identifier.
- Ledger events use unique deterministic `EVENT-*` IDs and monotonically increasing sequences.

## Boundary

Only the seven declared artifacts may exist in the planning directory. Source code, generated media, archives, and implementation outputs cause the Planning Quality Gate to fail.
