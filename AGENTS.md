# AGENTS.md

## Repository Identity

This repository is `creator-toolchain`, a Codex-native creator workflow system for planning, execution, state, rules, skill creation, audit, and plugin packaging.

## Operating Principles

- Use structured planning before non-trivial implementation.
- Treat `.agents/skills/` as the authoritative development source for Creator Toolchain skills.
- Generate `plugin/creator-toolchain/skills/` with `python3 scripts/sync_plugin_skills.py --write`; do not hand-edit the plugin skill mirror.
- Do not enable repo-local and plugin copies of the same skill together except during an explicit collision or provenance test.
- Use `creator-orchestrator` when workflow selection is unclear.
- Use `creator-intake-planner` for raw ideas and typed planning.
- Use `creator-execution-cycle` for implementation from an accepted plan.
- Keep durable project state inside `.creator/`.
- Do not silently mutate `.creator/*.json`; propose state updates unless the workflow explicitly owns that surface.
- Do not use `upstream/` repos as runtime dependencies; they are research evidence only.
- Every implementation cycle must end with Reconcile.

## File Conventions

- Plans: `.creator/plans/{project_slug}/PLANNING.md`
- Intake state: `.creator/plans/{project_slug}/INTAKE-STATE.md`
- Project manifest: `.creator/plans/{project_slug}/project.json`
- Activity ledger: `.creator/plans/{project_slug}/activity_ledger.jsonl`
- Execution plans: `.creator/plans/{project_slug}/PLAN-{sequence}.md`
- Reconciliation records: `.creator/plans/{project_slug}/RECONCILIATION-{sequence}.md`
- Summary files: `.creator/plans/{project_slug}/SUMMARY-{sequence}.md`
- Reports: `.creator/reports/`

## Phase Boundaries

- Phase 1 proves the MVP skill loop only.
- Phase 2 adds repo-local state surfaces.
- Phase 3 adds domain-rule governance and a skill workbench.
- Phase 4 adds evidence-first audit and remediation handoff.
- Phase 5 packages the suite as a Codex plugin.

## Safety

- Hooks, MCP, app integrations, and plugin publishing are opt-in only.
- Do not package user-private `.creator/` state.
- Do not package `upstream/`, `.DS_Store`, caches, or local research artifacts.
- Destructive file operations require explicit user approval.
