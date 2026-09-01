# AGENTS.md

## Repository Identity

This repository is `creator-toolchain`, a Codex-native creator workflow system for planning, execution, workspace state, rule governance, Skill development, evidence review, and reproducible Plugin release.

## Operating Principles

- Use structured planning before non-trivial implementation.
- Preserve exactly seven core Skills.
- Treat `.agents/skills/` as the authoritative Skill source.
- Generate `plugin/creator-toolchain/skills/` with `python3 scripts/sync_plugin_skills.py --write`; never hand-edit the mirror.
- Do not enable repository-local and installed Plugin copies together.
- Use `creator-orchestrator` when workflow selection is unclear.
- Use `creator-intake-planner` for raw ideas and typed planning.
- Use `creator-execution-cycle` only after explicit plan approval.
- End implementation with Verify and Reconcile.
- Keep durable repository state inside declared `.creator/*.json` surfaces.
- Do not silently mutate a surface unless the active workflow owns it.
- Treat Python modules as deterministic support, not an eighth Skill.

## State and Evidence Invariants

- Current state schema: `0.4.0`.
- State writes require validation, safe repository-relative paths, atomic replacement, and rollback.
- Rule proposals never auto-promote.
- Task completion requires observable evidence.
- Audit corrections preserve the original finding and add an immutable correction record.
- Health is evidence-derived; known release-blocking defects cannot coexist with green Health.
- Behavior evidence becomes stale when the relevant commit, package payload, catalog, or harness changes.

## Package Contract

- Runtime contents are defined by `scripts/package_integrity.py`.
- The committed inventory must match `docs/qa/package-integrity-report.json`.
- Release ZIP files are built by `scripts/build_plugin_package.py` or `scripts/release_creator_toolchain.py --build`.
- Do not package private state, caches, environment files, editor metadata, nested archives, or operating-system artifacts.

## Validation

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/materialize_surface_registry.py --root . --check
python3 scripts/materialize_project_type_refs.py --root . --check
python3 scripts/sync_plugin_skills.py --check
python3 scripts/package_integrity.py \
  --root . \
  --package-root plugin/creator-toolchain \
  --check docs/qa/package-integrity-report.json
python3 scripts/validate_creator_toolchain.py --scope all
python3 scripts/release_creator_toolchain.py \
  --root . \
  --check \
  --commit-sha "$(git rev-parse HEAD)"
```

## Release Boundary

A stable release requires:

1. Phase reconciliation marked `DONE`;
2. all 18 release gates recorded as `PASS`;
3. current 34/34 Behavior Acceptance evidence;
4. green Health;
5. a successful final branch validation;
6. a successful post-merge `main` validation;
7. a tag that points to the validated `main` commit;
8. uploaded ZIP and SHA-256 assets.

## Safety

- Hooks, MCP servers, app integrations, telemetry, and publishing automation are opt-in.
- Destructive file or remote operations require explicit authorization.
- Never publish user-private `.creator` state.
