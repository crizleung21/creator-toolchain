# PLAN-001 — Phase 2 Intake Artifact Foundation

## Status

`IN_PROGRESS`

## Goal

Begin Phase 2 by implementing the canonical Intake artifact package, deterministic Planning Quality Gate, resumable read-only status, and a machine-readable registry for all thirteen project types.

## Scope

- Create the exact seven-artifact planning directory under `.creator/plans/{project_slug}/`.
- Create formal project, intake-state, handoff, and ledger-event Schemas.
- Add canonical project templates.
- Add transactional Intake package creation that leaves no partial directory.
- Add deterministic `pass`, `pass_with_non_blocking_questions`, and `fail_needs_more_planning` gate results.
- Require three observable Given/When/Then acceptance criteria.
- Preserve a single deterministic project ID across the planning package.
- Resolve source assets or mark them explicitly missing.
- Reject implementation files inside the planning directory.
- Add thirteen domain-specific project-type contracts.

## Explicit Boundary

This slice does not yet modify the packaged `creator-intake-planner` Skill or generated plugin mirror. It does not register projects in `.creator/projects.json`, create standalone scaffolds, or approve execution handoff. Those surfaces remain for the next Phase 2 slice after the deterministic package and gate contracts are accepted.

## Acceptance Criteria

- Given a complete Intake request, when package creation runs, then exactly seven canonical artifacts are committed atomically.
- Given the same title and project type, when an ID is generated, then the project ID is stable.
- Given three observable acceptance criteria and no blocking questions, when the gate runs, then it returns `pass`.
- Given non-blocking questions only, when the gate runs, then it returns `pass_with_non_blocking_questions`.
- Given blocking questions, missing required sections, unsafe source paths, or implementation artifacts, when the gate runs, then it returns `fail_needs_more_planning`.
- Given an existing package, when status runs, then it performs no writes.
- Given a duplicate create request, when creation runs, then existing bytes are preserved.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/creator_intake_artifacts.py create --root /tmp/workspace --request request.json
python3 scripts/creator_intake_artifacts.py status --root /tmp/workspace --project creator-asset-naming-checker
```

## Next Slice

Wire the accepted contracts into the authoritative Intake Skill, regenerate the plugin mirror and package report, implement explicit approval and scaffold/handoff modes, register state through an owned proposal, and materialize the thirteen type-specific Skill references.
