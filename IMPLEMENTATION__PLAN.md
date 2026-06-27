# IMPLEMENTATION__PLAN.md

## Status

Draft for approval.

## Target

- Repo: `crizleung21/creator-toolchain`
- Branch: `main`
- Architecture target: plugin-first Creator Toolchain skill suite
- Main package root: `plugin/creator-toolchain/`
- Main skill root: `plugin/creator-toolchain/skills/`

## BLUF

This plan aligns the repository with the current Creator Toolchain direction. It cleans up historical Phase 1 docs, fixes the validator, restores the missing plugin manifest surface, reconciles release evidence, completes remaining skill surfaces, and removes every tracked `.gitkeep` placeholder.

This file is a plan only. File removals should be executed later as a separate reviewed PAUL cycle.

## Evidence Basis

The current repo direction is based on these existing files:

- `README.md`
- `AGENTS.md`
- `plugin/creator-toolchain/README.md`
- `plugin/creator-toolchain/CHANGELOG.md`
- `plugin/creator-toolchain/release-evidence/`
- `plugin/creator-toolchain/skills/`
- `scripts/validate_creator_toolchain.py`
- `docs/phase-1-acceptance-checklist.md`
- `docs/phase-1-test-prompts.md`
- `docs/examples/character-image-slide-project.md`

## Goals

1. Make active docs match the plugin-first repo direction.
2. Preserve useful Phase 1 records as archive material.
3. Update validation so it checks the real current repo, not legacy scaffolding.
4. Add the plugin manifest path referenced by package docs and release evidence.
5. Remove all `.gitkeep` placeholder files.
6. Keep private `.creator/` state and upstream research out of the plugin package.
7. End with observable verification evidence.

## Non-Goals

- No public plugin publishing in this plan.
- No hooks setup.
- No MCP setup.
- No private `.creator/` data bundled into the plugin package.
- No upstream clone bundled into the plugin package.

## Problems To Fix

| ID | Problem | Plan |
|---|---|---|
| P-001 | Phase 1 docs remain in active `docs/`. | Move to `docs/archive/phase-1/`. |
| P-002 | `validate_creator_toolchain.py` still requires obsolete paths. | Rewrite for current plugin-first package. |
| P-003 | Plugin docs mention `.codex-plugin/plugin.json`, but the file is missing. | Add `plugin/creator-toolchain/.codex-plugin/plugin.json`. |
| P-004 | `.gitkeep` placeholder files remain after real files were added. | Remove all tracked `.gitkeep` files. |
| P-005 | Release evidence may reference local-only results. | Mark current evidence clearly and refresh where needed. |
| P-006 | `creator-skillsmith-factory` may still need its real skill files. | Complete before final release validation. |

## Target Final Shape

```text
creator-toolchain/
├── AGENTS.md
├── README.md
├── IMPLEMENTATION__PLAN.md
├── docs/
│   ├── archive/phase-1/
│   └── fixtures/seed/
├── plugin/creator-toolchain/
│   ├── .codex-plugin/plugin.json
│   ├── CHANGELOG.md
│   ├── README.md
│   ├── release-evidence/
│   └── skills/
└── scripts/
```

## Phase 0 — Inventory

### Tasks

| Task | Action | Acceptance |
|---|---|---|
| P0-T1 | Confirm work targets `main`. | Branch is correct. |
| P0-T2 | Inventory tracked files. | Current structure is known before edits. |
| P0-T3 | Inventory all `.gitkeep` files. | Final placeholder list is recorded. |
| P0-T4 | Check whether `plugin/creator-toolchain/.codex-plugin/plugin.json` exists. | Manifest add/update mode is known. |
| P0-T5 | Check whether `IMPLEMENTATION__PLAN.md` exists. | Plan add/update mode is known. |

### Verification

```bash
find . -name .gitkeep -type f | sort
python3 scripts/validate_creator_toolchain.py
```

A validator failure before Phase 2 is expected because the current validator is stale.

## Phase 1 — Add Plugin Manifest

### Target

```text
plugin/creator-toolchain/.codex-plugin/plugin.json
```

### Minimal Draft Content

```json
{
  "name": "creator-toolchain",
  "version": "1.0.0-draft",
  "description": "Creator Toolchain Codex skill suite for creator planning, execution, state, rules, skill creation, and audit workflows.",
  "skills": "./skills/",
  "interface": {}
}
```

### Acceptance Criteria

- Given the plugin package README references `.codex-plugin/plugin.json`,
- When the manifest is added,
- Then the path exists and contains no private state, hooks, MCP configuration, or upstream research files.

## Phase 2 — Rewrite Validator

### Target

```text
scripts/validate_creator_toolchain.py
```

### Remove Legacy Required Paths

The new validator should no longer require:

```text
IMPLEMENTATION_PLAN.v0.4.1.md
SOURCE_TRACEABILITY_AND_AUDIT.md
docs/source-analysis/christopherkahler-toolchain-map.md
.creator/*
.agents/skills/*
.agents/plugins/marketplace.json
```

### Required Current Paths

The new validator should require:

```text
AGENTS.md
README.md
IMPLEMENTATION__PLAN.md
plugin/creator-toolchain/README.md
plugin/creator-toolchain/CHANGELOG.md
plugin/creator-toolchain/.codex-plugin/plugin.json
plugin/creator-toolchain/release-evidence/local-install-test.md
plugin/creator-toolchain/release-evidence/manifest-schema-validation.md
plugin/creator-toolchain/release-evidence/package-contents-audit.md
plugin/creator-toolchain/release-evidence/privacy-sanitization-audit.md
plugin/creator-toolchain/release-evidence/skill-discovery-test.md
scripts/materialize_seed_type_refs.py
scripts/validate_creator_toolchain.py
```

### Skill Checks

Require valid `SKILL.md` files for:

```text
creator-orchestrator
creator-seed-incubator
creator-paul-loop
creator-base-workspace
creator-rule-router
creator-skillsmith-factory
creator-aegis-audit
```

For each skill:

- `plugin/creator-toolchain/skills/{skill}/SKILL.md` exists.
- YAML frontmatter starts with `---`.
- `name:` matches the folder name.
- `description:` exists.

### Package Hygiene Checks

The plugin package must not contain:

```text
.creator/
upstream/
.DS_Store
__pycache__/
*.pyc
```

The validator should also fail if any `.gitkeep` remains after Phase 4.

### Acceptance Criteria

- Given the current plugin-first repo,
- When `python3 scripts/validate_creator_toolchain.py` runs,
- Then it validates only current required files and no longer requires legacy `.creator` or `.agents` paths.

## Phase 3 — Normalize Docs

### Move Historical Phase 1 Docs

```text
docs/phase-1-acceptance-checklist.md
→ docs/archive/phase-1/phase-1-acceptance-checklist.md

docs/phase-1-test-prompts.md
→ docs/archive/phase-1/phase-1-test-prompts.md
```

### Move Seed Fixture

```text
docs/examples/character-image-slide-project.md
→ docs/fixtures/seed/character-image-slide-project.md
```

### Update References

Update `README.md` if it points to any old docs path.

### Acceptance Criteria

- Given Phase 1 files are historical,
- When docs are normalized,
- Then active docs no longer present Phase 1 as the current validation surface.

## Phase 4 — Remove All `.gitkeep` Placeholders

### Rule

Every tracked `.gitkeep` should be removed. If a directory becomes empty, it may disappear from Git. That is acceptable unless a real file is added to that directory in the same cleanup cycle.

### Required Pre-Removal Inventory

```bash
find . -name .gitkeep -type f | sort
```

### Known Placeholder Candidates

```text
docs/.gitkeep
docs/examples/.gitkeep
plugin/.gitkeep
plugin/creator-toolchain/.gitkeep
plugin/creator-toolchain/skills/.gitkeep
plugin/creator-toolchain/skills/creator-aegis-audit/assets/.gitkeep
plugin/creator-toolchain/skills/creator-aegis-audit/references/.gitkeep
plugin/creator-toolchain/skills/creator-base-workspace/assets/.gitkeep
plugin/creator-toolchain/skills/creator-base-workspace/references/.gitkeep
plugin/creator-toolchain/skills/creator-orchestrator/assets/.gitkeep
plugin/creator-toolchain/skills/creator-orchestrator/references/.gitkeep
plugin/creator-toolchain/skills/creator-paul-loop/assets/.gitkeep
plugin/creator-toolchain/skills/creator-paul-loop/references/.gitkeep
plugin/creator-toolchain/skills/creator-rule-router/assets/.gitkeep
plugin/creator-toolchain/skills/creator-rule-router/references/.gitkeep
plugin/creator-toolchain/skills/creator-seed-incubator/assets/.gitkeep
plugin/creator-toolchain/skills/creator-seed-incubator/references/.gitkeep
plugin/creator-toolchain/skills/creator-skillsmith-factory/assets/.gitkeep
plugin/creator-toolchain/skills/creator-skillsmith-factory/references/.gitkeep
scripts/.gitkeep
```

### Acceptance Criteria

- Given placeholder files are no longer needed,
- When the cleanup runs,
- Then no `.gitkeep` remains anywhere in the repository.

### Verification

```bash
find . -name .gitkeep -type f | sort
```

Expected result: no output.

## Phase 5 — Reconcile Release Evidence

### Review These Files

```text
plugin/creator-toolchain/release-evidence/local-install-test.md
plugin/creator-toolchain/release-evidence/manifest-schema-validation.md
plugin/creator-toolchain/release-evidence/package-contents-audit.md
plugin/creator-toolchain/release-evidence/privacy-sanitization-audit.md
plugin/creator-toolchain/release-evidence/skill-discovery-test.md
```

### Required Updates

- Mark which evidence is historical local evidence.
- Mark which evidence is current repo-verifiable evidence.
- Confirm that the manifest path exists after Phase 1.
- Confirm package exclusions remain true.
- Keep public release validation as a later gate.

### Acceptance Criteria

- Given release evidence supports trust,
- When evidence files are reconciled,
- Then every claim either points to a current repo path or is marked as historical/local evidence.

## Phase 6 — Complete Remaining Skill Files

### Target

```text
plugin/creator-toolchain/skills/creator-skillsmith-factory/
```

### Required Checks

Confirm whether these exist:

```text
plugin/creator-toolchain/skills/creator-skillsmith-factory/SKILL.md
plugin/creator-toolchain/skills/creator-skillsmith-factory/assets/
plugin/creator-toolchain/skills/creator-skillsmith-factory/references/
```

If not complete, add the real files before final validation.

### Acceptance Criteria

- Given README lists seven skills,
- When validation runs,
- Then all seven skills have valid `SKILL.md` files under `plugin/creator-toolchain/skills/`.

## Phase 7 — Final Verification

### Commands

```bash
python3 scripts/validate_creator_toolchain.py
find . -name .gitkeep -type f | sort
```

### Expected Results

- Validator passes.
- `.gitkeep` inventory returns no files.
- Plugin package contains no private state or upstream clone.
- All seven skills are present.

## Risk Register

| Risk | Severity | Mitigation |
|---|---:|---|
| Empty directories disappear after `.gitkeep` removal. | Low | Accept or add real files later. |
| Validator rewrite misses a current required file. | Medium | Keep required list explicit and review against README. |
| Plugin manifest schema changes. | Medium | Keep manifest minimal and re-check before public release. |
| Docs moves break old references. | Low | Update README references. |
| Release evidence is misunderstood as fresh evidence. | Medium | Label historical versus current evidence. |

## Rollback Plan

- Revert individual commits if a phase causes regression.
- Restore archived Phase 1 docs only if they must become active again.
- Reintroduce a placeholder only with explicit approval and only if no real file can represent the directory.
- Revert validator rewrite if it blocks urgent work, then patch it in a follow-up commit.

## Execution Order

| Order | Phase | Output |
|---:|---|---|
| 1 | Phase 1 | Add plugin manifest. |
| 2 | Phase 2 | Rewrite validator. |
| 3 | Phase 3 | Move Phase 1 docs and fixture. |
| 4 | Phase 4 | Remove all `.gitkeep`. |
| 5 | Phase 5 | Update release evidence. |
| 6 | Phase 6 | Complete remaining skill files. |
| 7 | Phase 7 | Record final validation. |

## Definition of Done

Cleanup is complete when:

- `IMPLEMENTATION__PLAN.md` exists in repo root.
- Plugin manifest exists at `plugin/creator-toolchain/.codex-plugin/plugin.json`.
- Validator checks the current plugin-first repo.
- Phase 1 files are no longer active docs.
- Seed example is clearly a fixture.
- No `.gitkeep` remains.
- Release evidence is internally consistent.
- Final validation passes.
