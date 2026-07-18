# Scaffolding Workflow

`creator-intake:scaffold` requires an approved `scaffold-only` decision and a passing Planning Quality Gate.

## Default Output

```text
.creator/scaffolds/{project_slug}/
├── PROJECT.md
├── README.md
└── HANDOFF.md
```

## Rules

- Generate planning documents only.
- Do not create source code, media, build files, dependencies, or execution state.
- State clearly that execution is not authorized.
- Preserve the canonical project ID and source-plan path.
- Reject an existing scaffold instead of overwriting it.
- Update the Intake package and staged state-registration proposal transactionally.
