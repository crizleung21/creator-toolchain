# AGENTS.md

## Repository Identity

This repository is `creator-toolchain`, a Codex-native creator workflow system for planning, execution, state, rules, skill creation, audit, and plugin packaging.

## Operating Principles

- Use structured planning before non-trivial implementation.
- Use `creator-orchestrator` when workflow selection is unclear.
- Use `creator-seed-incubator` for raw ideas and typed planning.
- Use `creator-paul-loop` for implementation from an accepted plan.
- Keep durable project state inside `.creator/`.
- Do not silently mutate `.creator/*.json`; propose state updates unless the workflow explicitly owns that surface.
- Do not use `upstream/` repos as runtime dependencies; they are research evidence only.
- Every implementation cycle must end with Unify.

## File Conventions

- Plans: `.creator/plans/{project_slug}/PLANNING.md`
- Seed state: `.creator/plans/{project_slug}/SEED-STATE.md`
- Project manifest: `.creator/plans/{project_slug}/project.json`
- Activity ledger: `.creator/plans/{project_slug}/activity_ledger.jsonl`
- Execution plans: `.creator/plans/{project_slug}/PLAN-{sequence}.md`
- Unify summaries: `.creator/plans/{project_slug}/UNIFY-{sequence}.md`
- Summary files: `.creator/plans/{project_slug}/SUMMARY-{sequence}.md`
- Reports: `.creator/reports/`

## Phase Boundaries

- Phase 1 proves the MVP skill loop only.
- Phase 2 adds repo-local state surfaces.
- Phase 3 adds CARL-style rules and Skillsmith-style skill factory.
- Phase 4 adds AEGIS-style audit and remediation handoff.
- Phase 5 packages the suite as a Codex plugin.

## Safety

- Hooks, MCP, app integrations, and plugin publishing are opt-in only.
- Do not package user-private `.creator/` state.
- Do not package `upstream/`, `.DS_Store`, caches, or local research artifacts.
- Destructive file operations require explicit user approval.
