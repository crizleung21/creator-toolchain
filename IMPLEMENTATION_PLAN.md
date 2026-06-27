# Creator Toolchain Repository Stabilization and Capability Preservation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task by task. Every execution cycle must also use `creator-paul-loop` and close with Unify.

**Goal:** Stabilize `crizleung21/creator-toolchain` without weakening the six ChristopherKahler-derived capability families, establish `.agents/skills/` as the development source of truth, generate the plugin skill mirror deterministically, preserve `.creator/` as the repo-local state contract, and produce reproducible local release evidence.

**Architecture:** The repository uses a dual-surface model. Repo-local skills under `.agents/skills/` are authoritative for development; `plugin/creator-toolchain/skills/` is a generated, validated distribution mirror. `.creator/` remains the local runtime and project-state layer but is never bundled into the plugin package. Source research remains an active governance input rather than an unvalidated historical note.

**Tech Stack:** Codex Skills, Codex Plugin manifest and marketplace, Markdown, JSON/JSONL, Python 3 standard library, Git, shell verification commands.

---

## 0. Document Control

| Field | Value |
|---|---|
| Document version | `reviewed-1.0` |
| Prepared date | `2026-06-27` |
| Status | Reviewed draft for final human approval; execution is not authorized by this file alone |
| Approved architecture | Option A: `.agents/skills` authoritative, plugin skills generated |
| Repository | `https://github.com/crizleung21/creator-toolchain` |
| Merge target | `main` |
| Required work branch | `codex/stabilize-creator-toolchain` |
| Baseline commit | `38a57bb` |
| Source draft | `/Users/criz/Downloads/IMPLEMENTATION__PLAN.md` |
| Source draft SHA-256 | `8b852dc83fab67f509831e194dfa5a1248d1420c2ed6ddc48e40afe67ffdb18f` |
| Reviewed output | `/Users/criz/Downloads/IMPLEMENTATION_PLAN.reviewed.md` |

### 0.1 Authority Statement

This document supersedes the source draft only after the repository owner explicitly promotes it into the repository as `IMPLEMENTATION_PLAN.md`. It does not overwrite or delete the source draft.

### 0.2 Execution Authorization Boundary

- Approval of architecture Option A and the 20 review amendments authorizes creation of this reviewed plan.
- It does not authorize file deletion, state mutation, committing, pushing, plugin publishing, hook installation, MCP installation, or public release.
- Destructive cleanup requires a separate reviewed PAUL Apply cycle.
- Public plugin publishing remains out of scope.

## 1. BLUF

The current repository contains useful implementation work but mixes three different states:

1. committed plugin skill assets on `main`;
2. untracked repo-local skills, `.creator/` state, marketplace metadata, `.gitignore`, and plugin manifest;
3. missing research and plan files still referenced by the validator and `.creator/workspace.json`.

The correct repair is not to stop validating `.agents/` and `.creator/`. That would hide state and capability regressions. The repair must first reconcile the architecture and pointers, then make one skill tree authoritative, then validate the generated plugin mirror, and only then regenerate release evidence.

Official Codex guidance treats local skills as the appropriate starting point for one-repository iteration and plugins as the packaging and sharing surface. This plan adopts that model while retaining installable plugin output.

## 2. Decision Record

### 2.1 Accepted Decision: Option A

| Surface | Role | Authority |
|---|---|---|
| `.agents/skills/` | Development and repo-local skill execution | Authoritative skill source |
| `plugin/creator-toolchain/skills/` | Installable plugin distribution | Generated mirror; never hand-edited |
| `.creator/` | Repo-local workspace, project, rule, decision, and audit state | Runtime state contract; excluded from plugin |
| `docs/source-analysis/` | ChristopherKahler source evidence and drift notes | Active governance evidence |
| `plugin/creator-toolchain/release-evidence/` | Evidence tied to an exact package revision | Regenerated after all package changes |

### 2.2 Consequences

- `scripts/materialize_seed_type_refs.py` continues to write only into the authoritative `.agents/skills` tree.
- A new deterministic sync command copies approved skill content into the plugin mirror.
- Direct edits under `plugin/creator-toolchain/skills/` are prohibited by repository policy.
- Validation checks both source completeness and mirror parity.
- Plugin-only tests run outside the repository skill-discovery context to avoid false positives from duplicate repo-local skills.

### 2.3 Rejected Alternatives

| Alternative | Reason rejected |
|---|---|
| Plugin tree as the only authority | Conflicts with the current materializer, current README direction, and local-skill-first development model. |
| Cleanup-only plan | Would not prove preservation of SEED, PAUL, BASE, CARL, Skillsmith, and AEGIS capabilities. |
| Continue hand-maintaining both trees | Creates silent drift and ambiguous provenance. |

## 3. Evidence Baseline

### 3.1 Required Source Evidence

| Evidence | Required repository destination | Baseline SHA-256 |
|---|---|---|
| ChristopherKahler toolchain map | `docs/source-analysis/christopherkahler-toolchain-map.md` | `89d55a444ac5aff7eefb49c036592555ad4edfca2aca28fdcfb920887b3ccbb2` |
| Prior implementation plan v0.4.1 | `docs/archive/plans/IMPLEMENTATION_PLAN.v0.4.1.md` | `42ce35404faee56e552ef9f1abc0aec0ed90ba26403773e58f5f733a8ba8573a` |
| Prior source traceability audit | `docs/archive/audits/SOURCE_TRACEABILITY_AND_AUDIT.md` | `8763426f14a901d4f39e40933ba601939167b99bd9e5815b0241bde3c20ccc1c` |

Known local source locations at plan-authoring time:

```text
/Users/criz/Desktop/未命名資料夾 5/source-analysis/christopherkahler-toolchain-map.md
/Users/criz/Desktop/未命名資料夾 5/IMPLEMENTATION_PLAN.v0.4.1.md
/Users/criz/Desktop/未命名資料夾 5/SOURCE_TRACEABILITY_AND_AUDIT.md
```

The SHA-256 values, not the external folder name, define the accepted source snapshot.

### 3.2 Upstream Sources

- `https://github.com/ChristopherKahler/paul`
- `https://github.com/ChristopherKahler/seed`
- `https://github.com/ChristopherKahler/base`
- `https://github.com/ChristopherKahler/carl`
- `https://github.com/ChristopherKahler/skillsmith`
- `https://github.com/ChristopherKahler/aegis`
- `https://developers.openai.com/codex/plugins/build`

### 3.3 Observed Repository Baseline

At review time:

- branch: `main`
- HEAD: `38a57bb`
- repository remote: `https://github.com/crizleung21/creator-toolchain.git`
- the plugin manifest exists locally but is untracked;
- most repo-local skill entry points and `.creator/` state are untracked;
- `creator-skillsmith-factory` already exists in both skill trees;
- 19 tracked `.gitkeep` files exist;
- 5 physical `.DS_Store` files cause current validation failure;
- the current validator also fails because three referenced governance files are absent from the repository;
- all seven plugin skills pass the bundled `quick_validate.py` check;
- the current complete plugin manifest passes the bundled plugin validator.

## 4. Goals and Non-Goals

### 4.1 Goals

1. Preserve the high-value behaviors of SEED, PAUL, BASE, CARL, Skillsmith, and AEGIS.
2. Make `.agents/skills/` the explicit development source of truth.
3. Generate and verify an exact plugin skill mirror.
4. Repair all `.creator` paths before enforcing state validation.
5. Preserve source traceability and version-drift warnings.
6. Archive historical Phase 1 documents without breaking references.
7. Replace the monolithic pass/fail assumption with repo, state, and plugin validation scopes.
8. Remove obsolete placeholders and OS artifacts only after an approved inventory.
9. Regenerate release evidence after the final package content is fixed.
10. End every execution cycle with PAUL Unify and reproducible evidence.

### 4.2 Non-Goals

- Public plugin publishing.
- Hook installation or activation.
- MCP or app integration.
- Bundling `.creator/`, research clones, local caches, or personal state in the plugin.
- Reimplementing ChristopherKahler tools line for line.
- Treating Claude Code command layouts as Codex runtime dependencies.
- Resolving public-release licensing without a repository-owner decision.
- Editing the original `/Users/criz/Downloads/IMPLEMENTATION__PLAN.md`.

## 5. Capability Preservation Contract

### 5.1 Must-Preserve Matrix

| Source tool | Creator skill | Required behaviors | Evidence required |
|---|---|---|---|
| SEED | `creator-seed-incubator` | type-first intake; type guides/config/loadouts; `SEED-STATE.md`; planning quality gate; separate graduate and launch flows | structural validation plus ideate, resume, graduate, and launch contract tests |
| PAUL | `creator-paul-loop` | Plan -> Apply -> Qualify -> Unify; BDD acceptance; explicit statuses; recovery; summary, state, and append-only ledger closure | artifact schema tests plus one complete dry-run cycle |
| BASE | `creator-base-workspace` | structured state surfaces; operator and PSMM; pulse, groom, drift; maintenance separate from execution | JSON/schema checks plus pulse/groom fixtures and cross-surface consistency tests |
| CARL | `creator-rule-router` | domains; recall and exclude; explicit activation; staging; decision log; conflict audit; compact rule preflight | rule fixtures plus positive, negative, conflict, and staging tests |
| Skillsmith | `creator-skillsmith-factory` | discover; scaffold; distill; score; audit; progressive disclosure; collision detection | skill spec fixture, scaffold validation, compliance scoring, and negative anti-pattern tests |
| AEGIS | `creator-aegis-audit` | phases 0-8; Layer A/B/C; evidence/confidence/disagreement; adversarial review; intervention gates; no direct execution; PAUL handoff | audit fixture, layer schema checks, adversarial finding, and handoff boundary test |

### 5.2 Cross-Tool Contracts

| Contract | Acceptance |
|---|---|
| SEED -> PAUL | Approved `PLANNING.md` and `HANDOFF.md` enter PAUL without re-asking resolved questions. |
| PAUL -> BASE | Project state and ledger updates reconcile with `.creator/projects.json` and `.creator/state.json`. |
| BASE -> CARL | PSMM observations can create staged proposals but cannot promote permanent rules automatically. |
| CARL -> workflows | Only matching, non-excluded rules appear in Rule Preflight output. |
| Skillsmith -> skills | New or changed skills pass metadata, anatomy, collision, reference, and acceptance-test checks. |
| AEGIS -> PAUL | Layer C produces a PAUL-ready remediation plan; audit mode never edits the audited target. |

### 5.3 Capability Gate

No phase may claim capability preservation merely because `SKILL.md` exists. Each behavior above must map to:

1. an authoritative source or reference file;
2. a deterministic structural check where possible;
3. a bounded behavioral prompt test where model execution is required;
4. an evidence record with date, environment, command, result, and limitations.

## 6. Problem Register

| ID | Severity | Problem | Required correction |
|---|---:|---|---|
| P-001 | Critical | Proposed plugin-first wording conflicts with README and local-skill architecture. | Adopt and document Option A. |
| P-002 | Critical | `.creator/workspace.json` points to governance files absent from the repository. | Restore/archive files and update all pointers atomically. |
| P-003 | Critical | The proposed validator rewrite would stop validating core state and local skills. | Keep three validation scopes and preserve state/capability checks. |
| P-004 | High | The plugin manifest is present and valid locally but untracked; the source draft calls it missing. | Preserve, review, and track the existing full manifest. |
| P-005 | High | The source draft's empty `interface` object is weaker than the validated local manifest. | Do not overwrite the full interface block. |
| P-006 | High | Skills are maintained in two trees without an explicit generation contract. | Add deterministic sync and `--check` parity mode. |
| P-007 | High | `materialize_seed_type_refs.py` writes only the local skill tree. | Declare that behavior canonical and sync afterward. |
| P-008 | High | `creator-skillsmith-factory` is described as possibly missing even though it exists. | Replace the completion task with capability verification. |
| P-009 | High | Release evidence can become stale when skill or manifest files change later. | Generate evidence only after package freeze. |
| P-010 | High | Plugin discovery tests run inside a repo that can also expose local skills. | Separate local-only and plugin-only test environments. |
| P-011 | Medium | Historical Phase 1 moves do not update every reference. | Use repository-wide reference scans before and after moves. |
| P-012 | Medium | One known `.gitkeep` candidate does not exist; 19 are tracked. | Generate the deletion list from Git, not prose. |
| P-013 | High | Five physical `.DS_Store` files are omitted from the cleanup task. | Inventory and remove them after approval. |
| P-014 | Medium | Package hygiene checks are path-based but release claims imply content-level privacy review. | Add secret/PII review and exact package inventory evidence. |
| P-015 | High | Final verification commands do not prove plugin install, provenance, behavior, or state consistency. | Add the full verification matrix in Phase 9. |
| P-016 | Medium | The rollback section assumes all relevant files are already tracked. | Snapshot untracked inputs before edits and commit by phase. |
| P-017 | Medium | Direct work on `main` weakens review and rollback. | Use `codex/stabilize-creator-toolchain`. |
| P-018 | Medium | The target tree omits active architecture surfaces. | Replace it with the complete target tree below. |
| P-019 | Medium | Public-release license metadata remains unresolved. | Keep public publishing blocked; record the decision separately. |
| P-020 | High | The execution order updates evidence before all skill work is complete. | Use the dependency order defined in Section 10. |

## 7. Target Repository Shape

```text
creator-toolchain/
|-- AGENTS.md
|-- README.md
|-- IMPLEMENTATION_PLAN.md
|-- .gitignore
|-- .agents/
|   |-- plugins/
|   |   `-- marketplace.json
|   `-- skills/
|       |-- creator-orchestrator/
|       |-- creator-seed-incubator/
|       |-- creator-paul-loop/
|       |-- creator-base-workspace/
|       |-- creator-rule-router/
|       |-- creator-skillsmith-factory/
|       `-- creator-aegis-audit/
|-- .creator/
|   |-- workspace.json
|   |-- projects.json
|   |-- entities.json
|   |-- state.json
|   |-- psmm.json
|   |-- operator.json
|   |-- backlog.json
|   |-- surfaces.json
|   |-- decisions.json
|   |-- rules.json
|   |-- plans/
|   |-- reports/
|   `-- private/                 # ignored; never packaged
|-- docs/
|   |-- source-analysis/
|   |   `-- christopherkahler-toolchain-map.md
|   |-- archive/
|   |   |-- phase-1/
|   |   |-- plans/
|   |   `-- audits/
|   |-- fixtures/
|   |   `-- seed/
|   `-- qa/
|       |-- capability-matrix.md
|       `-- skill-contract-tests.md
|-- plugin/
|   `-- creator-toolchain/
|       |-- .codex-plugin/plugin.json
|       |-- README.md
|       |-- CHANGELOG.md
|       |-- skills/              # generated mirror
|       `-- release-evidence/
|-- scripts/
|   |-- materialize_seed_type_refs.py
|   |-- sync_plugin_skills.py
|   `-- validate_creator_toolchain.py
`-- tests/
    |-- test_sync_plugin_skills.py
    |-- test_validate_creator_toolchain.py
    `-- fixtures/
```

Empty directories are not part of the contract. Real files, not `.gitkeep`, preserve required directories.

## 8. Safety and Privacy Boundaries

### 8.1 Prohibited Package Content

The plugin package must not contain:

```text
.creator/
.agents/
upstream/
.git/
.DS_Store
__pycache__/
*.pyc
.env
.env.*
*.local.json
private/
package/
*.zip
```

### 8.2 State Classification

Before any `.creator` file is staged, classify it as one of:

| Class | Treatment |
|---|---|
| repository contract state | sanitize, validate, and allow tracking |
| fixture or template | store under an explicit fixture/template path |
| user-private state | move under `.creator/private/` or `*.local.json`; never stage |
| obsolete state | archive only after explicit approval |

`operator.json`, entities, project notes, and decision logs require content review before tracking. Path-based exclusion alone is insufficient.

### 8.3 Destructive Action Gate

Deletion commands may run only when all conditions are true:

- the exact file inventory is recorded;
- the target files are either tracked or copied into a recoverable snapshot;
- the user has approved the deletion phase;
- `git status --short` has been reviewed immediately before deletion;
- the phase includes a rollback command or restoration source.

## 9. Validation Architecture

`scripts/validate_creator_toolchain.py` remains the single entry point but exposes three scopes:

```text
--scope repo     authoritative skills, docs, scripts, links, generated-source policy
--scope state    .creator JSON/JSONL, schema versions, required domains, pointer integrity
--scope plugin   manifest, marketplace, mirror parity, package hygiene, skill discovery structure
--scope all      repo + state + plugin
```

### 9.1 Exit Contract

| Result | Exit | Output requirement |
|---|---:|---|
| all checks pass | `0` | counts by scope and explicit pass summary |
| validation failure | `1` | one actionable line per failure with path and check ID |
| invalid CLI usage | `2` | usage message and allowed scopes |

### 9.2 Validation Principles

- Parse JSON and JSONL structurally.
- Parse skill frontmatter structurally; do not rely only on substring matching.
- Resolve every active state pointer and report broken targets.
- Validate all 13 SEED project types and their three required files in the authoritative tree.
- Check that the plugin mirror equals the authoritative tree after applying the documented exclusion policy.
- Delegate official manifest freshness to the current Codex/plugin validator and record that external result.
- Keep release-evidence freshness separate from structural repository validation.

## 10. Execution Order and Dependency Graph

```text
Phase 0  Freeze baseline and create work branch
   |
Phase 1  Promote reviewed governance inputs and repair pointers
   |
Phase 2  Establish authoritative skills and deterministic plugin sync
   |
Phase 3  Verify and complete six-tool capability contracts
   |
Phase 4  Normalize docs and state references
   |
Phase 5  Remove placeholders and OS artifacts
   |
Phase 6  Refactor validator and add regression tests
   |
Phase 7  Freeze and validate plugin package metadata
   |
Phase 8  Regenerate release evidence from the frozen package
   |
Phase 9  Run full qualification and PAUL Unify
```

Evidence generation cannot precede the final package freeze. Phase 8 is therefore downstream of all skill, documentation, cleanup, validator, manifest, and marketplace changes.

---

## Phase 0 - Baseline Freeze and Work Branch

### 11. Phase 0 Goal

Create a recoverable, evidence-backed baseline without mutating or deleting existing work.

#### Task 0.1: Record Repository Identity

**Files:**

- Create during execution: `.creator/reports/stabilization-baseline.md`

- [ ] Record the output of:

```bash
git status --short --branch
git rev-parse HEAD
git remote -v
git ls-files
git ls-files '*.gitkeep'
find . -name .DS_Store -type f -print
```

**Expected:** The report identifies `38a57bb` as the reviewed baseline or explicitly stops if HEAD has changed.

- [ ] Record SHA-256 values for every untracked file proposed for promotion.
- [ ] Record which `.creator` files contain potentially private values.

#### Task 0.2: Verify Governance Inputs

Run:

```bash
shasum -a 256 '/Users/criz/Desktop/未命名資料夾 5/source-analysis/christopherkahler-toolchain-map.md'
shasum -a 256 '/Users/criz/Desktop/未命名資料夾 5/IMPLEMENTATION_PLAN.v0.4.1.md'
shasum -a 256 '/Users/criz/Desktop/未命名資料夾 5/SOURCE_TRACEABILITY_AND_AUDIT.md'
shasum -a 256 '/Users/criz/Downloads/IMPLEMENTATION_PLAN.reviewed.md'
```

**Expected:** The first three hashes equal Section 3.1. Record the reviewed-plan hash in the baseline report.

#### Task 0.3: Create the Work Branch

Run only after reviewing the dirty worktree:

```bash
git switch -c codex/stabilize-creator-toolchain
```

**Expected:** `git branch --show-current` returns `codex/stabilize-creator-toolchain`.

Do not stash, reset, clean, or delete untracked work.

#### Task 0.4: Capture Baseline Validation

Run:

```bash
python3 scripts/validate_creator_toolchain.py
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugin/creator-toolchain
find plugin/creator-toolchain/skills -mindepth 2 -maxdepth 2 -type f -name SKILL.md -execdir python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" . \;
```

**Expected:** Record the current creator validator failures as baseline defects. The plugin validator and seven skill validations must pass before their current files are promoted.

#### Phase 0 Acceptance Criteria

- **Given** the current dirty worktree,
- **When** Phase 0 finishes,
- **Then** every existing tracked and untracked artifact relevant to this plan is inventoried and recoverable, and no file has been deleted.

#### Phase 0 Commit

Do not commit baseline reports containing private values. Commit only a sanitized report after review:

```bash
git add .creator/reports/stabilization-baseline.md
git commit -m "docs: record creator toolchain stabilization baseline"
```

---

## Phase 1 - Governance Promotion and Pointer Repair

### 12. Phase 1 Goal

Promote the reviewed plan and verified source evidence into canonical repository paths, then repair every active pointer atomically.

#### Task 1.1: Promote the Reviewed Plan

**Files:**

- Create: `IMPLEMENTATION_PLAN.md`
- Preserve unchanged: `/Users/criz/Downloads/IMPLEMENTATION__PLAN.md`
- Preserve unchanged: `/Users/criz/Downloads/IMPLEMENTATION_PLAN.reviewed.md`

- [ ] Copy the reviewed output to repository root as `IMPLEMENTATION_PLAN.md` only after final human approval.
- [ ] Recompute hashes and confirm the repository copy exactly matches the reviewed output.

Run:

```bash
cmp -s IMPLEMENTATION_PLAN.md /Users/criz/Downloads/IMPLEMENTATION_PLAN.reviewed.md
```

**Expected:** exit `0`.

#### Task 1.2: Restore Source Evidence

**Files:**

- Create: `docs/source-analysis/christopherkahler-toolchain-map.md`
- Create: `docs/archive/plans/IMPLEMENTATION_PLAN.v0.4.1.md`
- Create: `docs/archive/audits/SOURCE_TRACEABILITY_AND_AUDIT.md`

- [ ] Copy only the three hash-verified snapshots listed in Section 3.1.
- [ ] Add an archive header to copies only if doing so does not invalidate the recorded source hash; otherwise add a sibling `README.md` explaining provenance.
- [ ] Keep the source map active because capability claims depend on it.

#### Task 1.3: Repair Active State Pointers

**Files:**

- Modify: `.creator/workspace.json`
- Modify as required: `.creator/projects.json`
- Modify as required: `.creator/plans/creator-toolchain-implementation/PLANNING.md`
- Modify as required: `.creator/plans/creator-toolchain-implementation/HANDOFF.md`
- Modify as required: `.creator/plans/creator-toolchain-implementation/SUMMARY-001.md`
- Append only: `.creator/plans/creator-toolchain-implementation/activity_ledger.jsonl`

Required pointer values:

```json
{
  "source_map": "docs/source-analysis/christopherkahler-toolchain-map.md",
  "active_plan": "IMPLEMENTATION_PLAN.md"
}
```

- [ ] Replace stale references to missing root files with active or archived canonical paths.
- [ ] Do not rewrite prior ledger events; append a reconciliation event.
- [ ] Validate every referenced path exists.

#### Task 1.4: Review State Privacy Before Tracking

- [ ] Inspect `.creator/operator.json`, `.creator/entities.json`, `.creator/projects.json`, and decisions for private or personal values.
- [ ] Move private values to ignored local overlays rather than deleting them.
- [ ] Confirm `.gitignore` covers `.creator/private/` and `.creator/*.local.json`.
- [ ] Stage only sanitized state contract files.

#### Phase 1 Acceptance Criteria

- **Given** `.creator` contains active pointers,
- **When** the reviewed governance artifacts are promoted,
- **Then** every active pointer resolves, historical evidence remains recoverable, and no private state enters the plugin package or Git staging set.

#### Phase 1 Commit

```bash
git add IMPLEMENTATION_PLAN.md docs/source-analysis docs/archive .gitignore
git add .creator/workspace.json .creator/projects.json .creator/entities.json
git add .creator/state.json .creator/psmm.json .creator/operator.json
git add .creator/backlog.json .creator/surfaces.json .creator/decisions.json .creator/rules.json
git add .creator/plans/creator-toolchain-implementation
git diff --cached --check
git commit -m "docs: restore governance evidence and reconcile state pointers"
```

Run `git diff --cached --name-only` and `git diff --cached` before committing. If any
allowlisted state file still contains private values, unstage that specific file and replace the
private fields with an ignored local overlay before continuing.

---

## Phase 2 - Authoritative Skills and Plugin Mirror

### 13. Phase 2 Goal

Make `.agents/skills/` complete and authoritative, then generate the plugin mirror deterministically.

#### Task 2.1: Promote Authoritative Repo-Local Skills

**Files:**

- Review and track: `.agents/skills/creator-orchestrator/`
- Review and track: `.agents/skills/creator-seed-incubator/`
- Review and track: `.agents/skills/creator-paul-loop/`
- Review and track: `.agents/skills/creator-base-workspace/`
- Review and track: `.agents/skills/creator-rule-router/`
- Review and track: `.agents/skills/creator-skillsmith-factory/`
- Review and track: `.agents/skills/creator-aegis-audit/`

- [ ] Confirm each skill has `SKILL.md`, all referenced files, and useful assets.
- [ ] Confirm all 13 SEED project types contain `guide.md`, `config.md`, and `skill-loadout.md`.
- [ ] Run quick validation on all seven authoritative skills.
- [ ] Remove no skill content merely because the plugin copy exists.

#### Task 2.2: Add Deterministic Sync Command

**Files:**

- Create: `scripts/sync_plugin_skills.py`
- Create: `tests/test_sync_plugin_skills.py`

Required CLI:

```text
python3 scripts/sync_plugin_skills.py --write
python3 scripts/sync_plugin_skills.py --check
```

Required behavior:

| Mode | Behavior | Exit |
|---|---|---:|
| `--write` | replace the seven plugin skill directories from authoritative source; exclude generated junk | `0` on success |
| `--check` | perform no write; report missing, extra, or different files after exclusions | `0` when equal, `1` on drift |
| invalid/missing mode | print usage | `2` |

Exclusions:

```python
EXCLUDED_NAMES = {".DS_Store", ".gitkeep", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc"}
```

Safety requirements:

- source root must resolve inside `.agents/skills`;
- destination root must resolve inside `plugin/creator-toolchain/skills`;
- only the seven allowlisted skill directories may be replaced;
- symbolic links that resolve outside the source tree must fail validation;
- output order must be deterministic;
- `--check` must never change mtimes or content.

#### Task 2.3: Write Sync Tests First

Tests must cover:

```text
test_check_passes_for_equal_trees
test_check_reports_changed_file
test_check_reports_extra_plugin_file
test_write_copies_all_allowlisted_skills
test_write_excludes_ds_store_gitkeep_and_pyc
test_write_rejects_unknown_skill_directory
test_write_rejects_external_symlink
test_check_is_read_only
```

Run before implementation and confirm at least one expected failure:

```bash
python3 -m unittest tests.test_sync_plugin_skills -v
```

After implementation, expected result: all sync tests pass.

#### Task 2.4: Update Repository Policy

**Files:**

- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `plugin/creator-toolchain/README.md`

Required policy text:

```text
.agents/skills is the authoritative development source.
plugin/creator-toolchain/skills is generated by scripts/sync_plugin_skills.py.
Do not hand-edit the generated plugin skill mirror.
Do not enable repo-local and plugin copies simultaneously except in an explicit collision test.
```

#### Task 2.5: Materialize Then Sync

Run:

```bash
python3 scripts/materialize_seed_type_refs.py
python3 scripts/sync_plugin_skills.py --write
python3 scripts/sync_plugin_skills.py --check
```

**Expected:** 13 SEED type sets materialized; plugin mirror parity check exits `0`.

#### Phase 2 Acceptance Criteria

- **Given** a change is made to an authoritative skill,
- **When** materialization and sync run,
- **Then** the plugin mirror is deterministic, contains no excluded artifacts, and `--check` proves parity without writing.

#### Phase 2 Commit

```bash
git add .agents/skills plugin/creator-toolchain/skills scripts/sync_plugin_skills.py tests/test_sync_plugin_skills.py AGENTS.md README.md plugin/creator-toolchain/README.md
git diff --cached --check
git commit -m "build: make local skills authoritative and generate plugin mirror"
```

---

## Phase 3 - Six-Tool Capability Verification

### 14. Phase 3 Goal

Prove that each high-value source capability is represented by usable Creator Toolchain behavior, not just filenames.

#### Task 3.1: Create the Capability Matrix

**Files:**

- Create: `docs/qa/capability-matrix.md`
- Create: `docs/qa/skill-contract-tests.md`

Each matrix row must include:

```text
source repository and evidence path
Creator Toolchain skill and reference path
behavioral contract
positive test
negative or boundary test
expected artifact
verification method
status and evidence date
```

#### Task 3.2: Verify SEED Contract

Required tests:

1. Raw image-system idea selects a project type before planning.
2. Interrupted planning produces resumable `SEED-STATE.md`.
3. Weak acceptance criteria block graduation.
4. `graduate` can complete without PAUL initialization.
5. `launch` produces a PAUL handoff without repeating resolved questions.
6. All 13 type reference sets load from the authoritative tree.

Expected artifacts:

```text
PLANNING.md
SEED-STATE.md
OPEN-QUESTIONS.md when blocked
HANDOFF.md after approval
```

#### Task 3.3: Verify PAUL Contract

Required tests:

1. Apply refuses an unapproved plan.
2. Every task includes files, action, verify, done, and BDD acceptance mapping.
3. Qualify re-reads actual outputs and runs fresh verification.
4. Recovery distinguishes `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, and `BLOCKED`.
5. Unify writes summary, updates state proposal, and appends one valid JSONL event.
6. A cycle cannot claim completion without Unify.

#### Task 3.4: Verify BASE Contract

Required tests:

1. All required `.creator` JSON files parse and carry schema versions where required.
2. Pulse reports drift without mutating unrelated state.
3. Groom separates archive candidates from automatic deletion.
4. Operator and PSMM summaries respect privacy and context budgets.
5. Cross-surface project identifiers resolve consistently.
6. PSMM can stage a CARL proposal but cannot approve it.

#### Task 3.5: Verify CARL Contract

Required tests:

1. `GLOBAL` remains eligible but compact.
2. Matching recall keywords select only relevant domain rules.
3. Excluded rules are omitted and recorded with reason.
4. Conflicting rules produce a conflict warning and decision reference.
5. Staged proposals require explicit approval before promotion.
6. Repeated preflight does not duplicate identical rules.

#### Task 3.6: Verify Skillsmith Contract

Required tests:

1. Discovery produces a complete skill spec.
2. Scaffold separates entry point, workflows, frameworks, templates, and checklists.
3. Distill creates source-noted framework chunks.
4. Score reports component-level and total compliance.
5. Audit identifies missing boundaries, trigger overlap, and stale references.
6. Duplicate skill names are rejected before scaffolding.

#### Task 3.7: Verify AEGIS Contract

Required tests:

1. Audit runs the Phase 0-5 diagnostic pipeline.
2. Transform runs Phases 6-8 only from completed Layer A evidence.
3. Findings separate observation, interpretation, judgment, confidence, and disagreement.
4. Devil's Advocate challenges at least one material assumption.
5. Layer A remains immutable except for an addendum.
6. Audit mode does not edit the audited target.
7. Layer C includes dependencies, risk, rollback, verification, and PAUL handoff.

#### Task 3.8: Verify Cross-Tool Handoffs

Run one bounded fixture through:

```text
creator-seed-incubator
-> creator-paul-loop
-> creator-base-workspace state reconciliation
-> creator-rule-router preflight
-> creator-aegis-audit review
-> creator-paul-loop remediation handoff
```

Use `docs/fixtures/seed/character-image-slide-project.md` as a fixture, not as a claim that the system only supports character-image projects.

#### Phase 3 Acceptance Criteria

- **Given** the six source-tool capability families,
- **When** the structural and behavioral contract tests run,
- **Then** every must-preserve behavior has an implementation path, positive evidence, and a tested boundary; unresolved gaps block release evidence generation.

#### Phase 3 Commit

```bash
git add .agents/skills plugin/creator-toolchain/skills docs/qa tests
git diff --cached --check
git commit -m "test: add six-tool capability preservation contracts"
```

---

## Phase 4 - Documentation and State Normalization

### 15. Phase 4 Goal

Archive historical Phase 1 documents, move the SEED fixture, and repair every reference without removing active source traceability.

#### Task 4.1: Move Historical Phase 1 Documents

**Files:**

- Move: `docs/phase-1-acceptance-checklist.md` -> `docs/archive/phase-1/phase-1-acceptance-checklist.md`
- Move: `docs/phase-1-test-prompts.md` -> `docs/archive/phase-1/phase-1-test-prompts.md`

Use `git mv` so history remains visible.

#### Task 4.2: Move the SEED Fixture

**Files:**

- Move: `docs/examples/character-image-slide-project.md` -> `docs/fixtures/seed/character-image-slide-project.md`

#### Task 4.3: Repair References

Before moving, record matches:

```bash
rg -n --hidden --glob '!.git/**' --glob '!.codebase-memory/**' 'docs/(phase-1-(acceptance-checklist|test-prompts)|examples/character-image-slide-project)' .
```

After moving:

- [ ] update README and AGENTS references;
- [ ] update references inside the archived test prompts;
- [ ] update validator paths and test fixtures;
- [ ] update `.creator` pointers and summaries;
- [ ] add archive status and provenance without changing the historical test content;
- [ ] rerun the same search and require zero stale active references.

#### Task 4.4: Normalize Plan Naming

- Repository canonical plan: `IMPLEMENTATION_PLAN.md`.
- Reviewed delivery artifact: `/Users/criz/Downloads/IMPLEMENTATION_PLAN.reviewed.md`.
- Original source draft with double underscore remains unchanged and external.
- Historical plans live under `docs/archive/plans/` with versioned filenames.

#### Phase 4 Acceptance Criteria

- **Given** historical Phase 1 documents and an active fixture,
- **When** normalization finishes,
- **Then** history is preserved, every active reference resolves, the source map remains active, and the fixture is clearly identified as test data.

#### Phase 4 Commit

```bash
git add docs README.md AGENTS.md .creator scripts tests
git diff --cached --check
git commit -m "docs: archive phase one records and normalize fixture paths"
```

---

## Phase 5 - Placeholder and OS Artifact Cleanup

### 16. Phase 5 Goal

Remove obsolete tracked placeholders and physical OS artifacts only after explicit approval of the generated inventory.

#### Task 5.1: Inventory Tracked Placeholders

Run:

```bash
git ls-files '*.gitkeep'
```

Reviewed baseline expectation: 19 tracked files. Do not rely on the stale prose candidate `plugin/creator-toolchain/skills/creator-orchestrator/assets/.gitkeep`, which was not tracked at review time.

#### Task 5.2: Confirm Every Directory Has Real Content or May Disappear

For each tracked placeholder:

- [ ] list sibling files;
- [ ] confirm the directory is not a required empty runtime contract;
- [ ] record whether the directory remains or disappears;
- [ ] obtain explicit approval for the exact deletion list.

#### Task 5.3: Remove Approved Placeholders

Use explicit paths from the approved inventory. Do not use a broad unreviewed deletion command.

Verification:

```bash
git ls-files '*.gitkeep'
find . -name .gitkeep -type f -print
```

**Expected:** no tracked or physical `.gitkeep` files remain.

#### Task 5.4: Remove Physical `.DS_Store` Files

Inventory:

```bash
find . -name .DS_Store -type f -print
```

Reviewed baseline expectation: five files outside `.git` and ignored research clones. Remove only the approved list, then rerun the command.

**Expected:** no output outside explicitly excluded external research directories.

#### Task 5.5: Confirm Ignore Policy

Required `.gitignore` entries:

```gitignore
.DS_Store
*.pyc
__pycache__/
.venv/
.env
.env.*
.creator/*.local.json
.creator/private/
plugin/creator-toolchain/package/
plugin/creator-toolchain/*.zip
upstream/
```

#### Phase 5 Acceptance Criteria

- **Given** an approved exact cleanup inventory,
- **When** Phase 5 finishes,
- **Then** no `.gitkeep` or disallowed `.DS_Store` remains, no unrelated file is deleted, and required directories contain real artifacts.

#### Phase 5 Commit

```bash
git add -u
git add .gitignore
git diff --cached --check
git commit -m "chore: remove obsolete placeholders and OS artifacts"
```

---

## Phase 6 - Layered Validator and Regression Tests

### 17. Phase 6 Goal

Refactor the current validator without deleting coverage for the architecture it is supposed to protect.

#### Task 6.1: Write Validator Regression Tests First

**Files:**

- Create: `tests/test_validate_creator_toolchain.py`
- Create: `tests/fixtures/validator/valid/`
- Create: `tests/fixtures/validator/broken-state-pointer/`
- Create: `tests/fixtures/validator/plugin-extra-file/`
- Create: `tests/fixtures/validator/invalid-skill-frontmatter/`

Required tests:

```text
test_scope_repo_passes_valid_fixture
test_scope_state_rejects_broken_pointer
test_scope_state_rejects_invalid_jsonl_line
test_scope_state_requires_global_rule_domain
test_scope_plugin_rejects_private_state
test_scope_plugin_rejects_ds_store
test_scope_plugin_rejects_extra_mirror_file
test_scope_repo_requires_all_seven_skills
test_scope_repo_requires_all_thirteen_seed_types
test_scope_repo_rejects_invalid_skill_frontmatter
test_scope_all_aggregates_failures
test_invalid_scope_exits_two
```

Run before implementation:

```bash
python3 -m unittest tests.test_validate_creator_toolchain -v
```

**Expected:** new tests fail because scope behavior is not yet implemented.

#### Task 6.2: Refactor the Validator Entry Point

**File:** `scripts/validate_creator_toolchain.py`

Required public functions:

```text
validate_repo_contract(root) -> list[Finding]
validate_state_contract(root) -> list[Finding]
validate_plugin_package(root) -> list[Finding]
validate_all(root) -> list[Finding]
main(argv=None) -> int
```

`Finding` must contain:

```text
check_id
scope
path
message
```

Use standard-library parsing. If YAML parsing is unavailable, implement a bounded frontmatter parser that validates the opening delimiter, closing delimiter, unique `name`, and non-empty `description`; do not use unconstrained substring matching.

#### Task 6.3: Preserve Core Checks

Repo scope must verify:

- seven authoritative skills;
- all required references and assets named by each skill;
- all 13 SEED type sets;
- materializer and sync scripts;
- source map and canonical plan;
- no stale active documentation paths;
- plugin mirror parity via the sync checker.

State scope must verify:

- JSON and JSONL syntax;
- schema versions where required;
- active path resolution;
- `GLOBAL` rules domain;
- staged proposals and decision log;
- cross-surface project identifiers;
- no private overlay is accidentally staged.

Plugin scope must verify:

- manifest and marketplace presence;
- plugin name and skills path;
- seven mirrored skills;
- no excluded package content;
- no `.gitkeep`, `.DS_Store`, cache, private state, or escaping symlink;
- exact package inventory can be generated.

#### Task 6.4: Run Tests and Full Validation

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_creator_toolchain.py --scope repo
python3 scripts/validate_creator_toolchain.py --scope state
python3 scripts/validate_creator_toolchain.py --scope plugin
python3 scripts/validate_creator_toolchain.py --scope all
```

**Expected:** all unit tests pass and every validation scope exits `0`.

#### Task 6.5: Prove Generator Idempotency

```bash
python3 scripts/materialize_seed_type_refs.py
python3 scripts/sync_plugin_skills.py --write
git diff --exit-code -- .agents/skills plugin/creator-toolchain/skills
```

**Expected:** no diff after committed generated output.

#### Phase 6 Acceptance Criteria

- **Given** valid and intentionally broken fixtures,
- **When** each validation scope runs,
- **Then** valid state passes, every broken fixture fails for the intended reason, and removal of `.creator` or `.agents` coverage is impossible without a regression-test change.

#### Phase 6 Commit

```bash
git add scripts tests
git diff --cached --check
git commit -m "test: add layered creator toolchain validation"
```

---

## Phase 7 - Plugin Package Freeze

### 18. Phase 7 Goal

Freeze a locally installable plugin package from the authoritative skill source without changing the approved capability content.

#### Task 7.1: Preserve and Review the Existing Manifest

**File:** `plugin/creator-toolchain/.codex-plugin/plugin.json`

Required actions:

- [ ] preserve the populated `interface` metadata;
- [ ] preserve `skills: "./skills/"`;
- [ ] confirm name matches the plugin directory;
- [ ] confirm every declared path exists;
- [ ] keep hooks, apps, and MCP fields absent because no companion config is in scope;
- [ ] retain draft/pre-release status until public-release metadata is approved;
- [ ] do not replace the manifest with the source draft's empty `interface` object.

#### Task 7.2: Validate Marketplace Metadata

**File:** `.agents/plugins/marketplace.json`

Required values:

```json
{
  "name": "creator-toolchain-local",
  "plugins": [
    {
      "name": "creator-toolchain",
      "source": {
        "source": "local",
        "path": "./plugin/creator-toolchain"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

#### Task 7.3: Run Current Plugin Validation

```bash
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugin/creator-toolchain
python3 scripts/sync_plugin_skills.py --check
python3 scripts/validate_creator_toolchain.py --scope plugin
```

**Expected:** all three commands exit `0`.

#### Task 7.4: Freeze Exact Package Inventory

Create a sorted inventory and SHA-256 list for all package files. The inventory must be generated from `plugin/creator-toolchain/` after exclusions and must not include release evidence claiming a later state.

Required checks:

```bash
find plugin/creator-toolchain -type f -print | sort
find plugin/creator-toolchain -name .DS_Store -o -name .gitkeep -o -name '*.pyc'
```

**Expected:** the first command lists only approved package files; the second prints nothing.

#### Phase 7 Acceptance Criteria

- **Given** authoritative skills have been synchronized,
- **When** the plugin package is frozen,
- **Then** the manifest, marketplace, mirrored skills, and exact package inventory all validate, and no optional integration or private state is bundled.

#### Phase 7 Commit

```bash
git add .agents/plugins/marketplace.json plugin/creator-toolchain
git diff --cached --check
git commit -m "build: freeze creator toolchain plugin package"
```

---

## Phase 8 - Release Evidence Regeneration

### 19. Phase 8 Goal

Replace ambiguous or stale claims with evidence tied to the exact frozen commit and test environment.

#### Task 8.1: Define Evidence Header

Every file under `plugin/creator-toolchain/release-evidence/` must record:

```text
status
evidence date and timezone
tested commit
operating system
Codex CLI version
Python version
command
exit code
relevant output
package or manifest hash
limitations and required repeat gates
```

#### Task 8.2: Regenerate Manifest Evidence

**File:** `plugin/creator-toolchain/release-evidence/manifest-schema-validation.md`

- cite the current official plugin build documentation;
- record the bundled validator path/version available in the environment;
- record command, exit code, manifest hash, and result;
- distinguish local schema acceptance from public marketplace approval.

#### Task 8.3: Regenerate Package and Privacy Evidence

**Files:**

- `plugin/creator-toolchain/release-evidence/package-contents-audit.md`
- `plugin/creator-toolchain/release-evidence/privacy-sanitization-audit.md`

Required evidence:

- sorted package file list or its checked-in digest;
- negative search for `.creator`, `upstream`, `.DS_Store`, cache, local overrides, and secrets;
- manual review of author, paths, prompts, fixtures, and release notes for personal data;
- explicit statement that path hygiene does not replace content review.

#### Task 8.4: Run Local-Only Skill Discovery Test

Test the authoritative `.agents/skills` surface with the plugin disabled or absent.

**File:** `plugin/creator-toolchain/release-evidence/local-skill-discovery-test.md`

Required result: all seven skills are discoverable from the repository and provenance is local.

#### Task 8.5: Run Plugin-Only Install and Discovery Test

Use a temporary `CODEX_HOME` and a neutral working directory that does not contain this repository's `.agents/skills`.

**Files:**

- Update: `plugin/creator-toolchain/release-evidence/local-install-test.md`
- Update: `plugin/creator-toolchain/release-evidence/skill-discovery-test.md`

Required sequence:

```text
create temporary CODEX_HOME
add the repo marketplace
install creator-toolchain from creator-toolchain-local
run plugin list and confirm installed/enabled
run prompt-input or equivalent discovery from a neutral directory
confirm all seven skill names originate from the installed plugin
remove the temporary environment
```

Do not count repo-local discovery as plugin discovery.

#### Task 8.6: Record Behavioral Trigger Evidence

For each skill, record one positive trigger and one boundary trigger:

| Skill | Positive | Boundary |
|---|---|---|
| orchestrator | ambiguous mixed workflow | must route, not execute |
| seed | raw idea | must not modify implementation files |
| paul | accepted plan | must reject raw ideation |
| base | state pulse | must not silently archive/delete |
| rule router | domain preflight | must not load every rule |
| skillsmith | skill audit/scaffold | must detect collision and boundaries |
| aegis | evidence-first audit | must not apply remediation directly |

#### Phase 8 Acceptance Criteria

- **Given** an exact frozen plugin commit,
- **When** release evidence is regenerated,
- **Then** every claim names its environment, command, result, hash, and limitation; plugin-only evidence cannot be satisfied by repo-local skills.

#### Phase 8 Commit

```bash
git add plugin/creator-toolchain/release-evidence
git diff --cached --check
git commit -m "docs: regenerate creator toolchain release evidence"
```

---

## Phase 9 - Final Qualification and Unify

### 20. Phase 9 Goal

Run the complete verification matrix, reconcile plan versus actual changes, and close the PAUL cycle.

#### Task 9.1: Run Structural Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_creator_toolchain.py --scope all
python3 scripts/sync_plugin_skills.py --check
python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugin/creator-toolchain
```

**Expected:** all commands exit `0`; the recorded test count equals the discovered test count.

#### Task 9.2: Run Hygiene and Reference Checks

```bash
git ls-files '*.gitkeep'
find . -name .gitkeep -type f -print
find . -name .DS_Store -type f -print
rg -n --hidden --glob '!.git/**' --glob '!.codebase-memory/**' 'docs/(phase-1-(acceptance-checklist|test-prompts)|examples/character-image-slide-project)' .
git diff --check
```

**Expected:** the first four commands produce no stale or disallowed results; `git diff --check` exits `0`.

#### Task 9.3: Prove Generated Output Is Stable

```bash
python3 scripts/materialize_seed_type_refs.py
python3 scripts/sync_plugin_skills.py --write
git diff --exit-code -- .agents/skills plugin/creator-toolchain/skills
```

**Expected:** exit `0` with no generated drift.

#### Task 9.4: Review Git Scope

```bash
git status --short --branch
git diff main...HEAD --stat
git diff main...HEAD --name-status
```

Review requirements:

- no private `.creator` overlays;
- no research clone;
- no cache or OS artifacts;
- no unrelated edits;
- every deletion appears in the approved cleanup inventory;
- every release-evidence file refers to the current tested commit or clearly records the pre-evidence package commit.

#### Task 9.5: Run PAUL Unify

**Files:**

- Create: `.creator/plans/creator-toolchain-stabilization/UNIFY-001.md`
- Create: `.creator/plans/creator-toolchain-stabilization/SUMMARY-001.md`
- Append: `.creator/plans/creator-toolchain-stabilization/activity_ledger.jsonl`
- Propose updates: `.creator/projects.json`, `.creator/state.json`, `.creator/decisions.json`

Unify must record:

```text
planned versus actual files
accepted deviations
verification commands and results
remaining concerns
release limitations
rollback points
one next action
```

Do not silently mutate state files. Present proposed state changes for review unless the approved PAUL cycle explicitly owns those surfaces.

#### Phase 9 Acceptance Criteria

- **Given** all implementation phases are complete,
- **When** final qualification and Unify run,
- **Then** tests, validators, sync parity, package install/discovery, capability contracts, hygiene, state pointers, and release evidence all agree with the exact repository state.

#### Phase 9 Commit

```bash
git add .creator/plans .creator/projects.json .creator/state.json .creator/decisions.json
git diff --cached --check
git commit -m "docs: unify creator toolchain stabilization cycle"
```

If state updates are not approved, commit only the reviewed Unify and Summary artifacts and leave state changes as proposals.

## 21. Risk Register

| ID | Risk | Severity | Detection | Mitigation | Rollback trigger |
|---|---|---:|---|---|---|
| RSK-01 | authoritative and plugin skill trees drift | High | sync `--check` | generated mirror and CI/test gate | any unexplained mirror difference |
| RSK-02 | both skill copies are loaded and tests pass for the wrong source | High | provenance-specific discovery test | neutral plugin-only environment | provenance cannot be established |
| RSK-03 | `.creator` pointer repair loses history | High | before/after pointer inventory | archive evidence and append-only ledger | active pointer target missing |
| RSK-04 | private state is staged | Critical | content review and staged-file inspection | private overlays and explicit staging | any personal/client/secret value found |
| RSK-05 | validator simplification hides capability regression | High | broken fixtures and scope tests | preserve repo/state/plugin checks | a known broken fixture passes |
| RSK-06 | materializer overwrites manual type edits | Medium | idempotency diff | generated-source policy and review | unexpected diff after generation |
| RSK-07 | release evidence becomes stale | High | commit/hash comparison | evidence generated after package freeze | tested hash differs from package |
| RSK-08 | plugin cache serves old content | Medium | version/hash and new-thread test | reinstall/cachebuster flow when needed | installed hash differs from source |
| RSK-09 | docs moves break references | Medium | pre/post `rg` and link scan | atomic moves and reference repair | any active stale path remains |
| RSK-10 | broad cleanup removes needed files | High | exact approved inventory | explicit deletion list and phase commit | deletion outside inventory |
| RSK-11 | manifest schema changes | Medium | current official validator | revalidate at packaging time | current validator rejects manifest |
| RSK-12 | unresolved license blocks public release | High for public release | metadata review | public publishing remains out of scope | any publish request before decision |
| RSK-13 | baseline HEAD changes before execution | Medium | `git rev-parse HEAD` | re-audit affected sections | HEAD differs from `38a57bb` |
| RSK-14 | source research drifts upstream | Medium | source commit/date refresh | record snapshots and addendum | material upstream behavior changes |

## 22. Rollback Plan

### 22.1 General Rules

- Never use `git reset --hard`, `git clean`, or checkout-based destructive recovery.
- Each phase is an independent commit after its acceptance criteria pass.
- Revert only the phase commit that introduced the regression.
- Preserve archival and ledger history; corrections use addenda or new events.
- Untracked baseline files must be hash-inventoried before any operation that can replace them.

### 22.2 Phase Rollback Map

| Phase | Rollback action |
|---:|---|
| 0 | delete no evidence; abandon branch only after confirming no unique untracked work depends on it |
| 1 | revert pointer and governance promotion commit together so pointers never reference half-migrated paths |
| 2 | revert sync script, generated mirror, and policy text as one unit |
| 3 | revert capability changes while retaining audit findings as historical evidence |
| 4 | reverse `git mv` operations and restore all references in the same commit |
| 5 | revert the cleanup commit; do not recreate placeholders manually unless the revert restores them |
| 6 | revert validator and test commit together only when the prior validator remains available; prefer fix-forward |
| 7 | revert manifest/marketplace freeze and reinstall the prior local package |
| 8 | mark invalid evidence superseded; do not silently rewrite historical results |
| 9 | add an Unify correction addendum and revert only the faulty implementation phase |

## 23. Commit Plan

| Order | Commit message | Primary scope |
|---:|---|---|
| 1 | `docs: record creator toolchain stabilization baseline` | sanitized baseline evidence |
| 2 | `docs: restore governance evidence and reconcile state pointers` | plan, map, archive, state |
| 3 | `build: make local skills authoritative and generate plugin mirror` | source skills, sync, policy |
| 4 | `test: add six-tool capability preservation contracts` | skill behavior and QA |
| 5 | `docs: archive phase one records and normalize fixture paths` | docs and references |
| 6 | `chore: remove obsolete placeholders and OS artifacts` | approved cleanup only |
| 7 | `test: add layered creator toolchain validation` | validator and regression tests |
| 8 | `build: freeze creator toolchain plugin package` | manifest, marketplace, mirror |
| 9 | `docs: regenerate creator toolchain release evidence` | evidence tied to package |
| 10 | `docs: unify creator toolchain stabilization cycle` | PAUL closure |

Do not combine phases merely to reduce commit count. A phase commit is a rollback boundary.

## 24. Definition of Done

The stabilization cycle is complete only when all conditions are true:

- [ ] reviewed plan is promoted as repository `IMPLEMENTATION_PLAN.md` after final approval;
- [ ] original download draft remains unchanged;
- [ ] source map is active and prior plan/audit are archived with provenance;
- [ ] every `.creator` active pointer resolves;
- [ ] private state is excluded from staging and packaging;
- [ ] `.agents/skills` is documented and tested as authoritative;
- [ ] plugin skills are generated and parity check passes;
- [ ] all seven skills pass structural validation;
- [ ] all 13 SEED type sets exist in source and generated mirror;
- [ ] all six capability families pass their contract matrix;
- [ ] all cross-tool handoffs have evidence;
- [ ] historical docs and fixture paths have no stale active references;
- [ ] no tracked or physical `.gitkeep` remains;
- [ ] no disallowed `.DS_Store`, cache, local override, private state, or research clone is packaged;
- [ ] repo, state, plugin, and all-scope validators pass;
- [ ] validator negative fixtures fail for the intended reasons;
- [ ] materialization and sync are idempotent;
- [ ] current plugin validator passes;
- [ ] plugin-only install and discovery pass from a neutral directory;
- [ ] local-only discovery passes without the plugin;
- [ ] release evidence names exact environment, commit, command, result, hash, and limitation;
- [ ] public release remains blocked until license and publishing review are approved;
- [ ] Git diff contains no unrelated or unapproved deletion;
- [ ] PAUL Unify, Summary, ledger append, and state proposals exist;
- [ ] exactly one next action is recorded.

## 25. Twenty-Amendment Traceability Matrix

| Amendment | Incorporated in |
|---:|---|
| 1. Add status/version/date/approval/baseline | Sections 0 and 3 |
| 2. Treat `main` as merge target; use work branch | Sections 0, 11, 21 |
| 3. Reframe BLUF as stabilization, not missing-surface creation | Sections 1 and 6 |
| 4. Resolve plugin-first versus local-skill contradiction | Sections 2 and 7 |
| 5. Expand evidence basis | Section 3 |
| 6. Add capability and state-consistency goals | Sections 4 and 5 |
| 7. Correct inaccurate problem statements | Section 6 |
| 8. Replace incomplete target tree | Section 7 |
| 9. Expand Phase 0 inventory and hashes | Phase 0 |
| 10. Preserve validated full manifest | Phase 7 |
| 11. Retain `.creator`, `.agents`, rules, and SEED validation | Sections 5, 9, and Phase 6 |
| 12. Split validation into repo/state/plugin scopes with tests | Section 9 and Phase 6 |
| 13. Define canonical skill source and deterministic sync | Section 2 and Phase 2 |
| 14. Repair broken `.creator` pointers rather than masking them | Phase 1 |
| 15. Preserve source map and repair all document references | Phases 1 and 4 |
| 16. Correct `.gitkeep` count and include `.DS_Store` cleanup | Phase 5 |
| 17. Regenerate evidence after package freeze | Phase 8 |
| 18. Replace Skillsmith existence check with seven-skill behavior tests | Phase 3 |
| 19. Expand final verification and provenance testing | Phase 9 |
| 20. Reorder execution, strengthen rollback/DoD, and require Unify | Sections 10, 22, 24 and Phase 9 |

## 26. References

### Repository Evidence

- `README.md`
- `AGENTS.md`
- `scripts/materialize_seed_type_refs.py`
- `scripts/validate_creator_toolchain.py`
- `.creator/workspace.json`
- `.agents/plugins/marketplace.json`
- `plugin/creator-toolchain/.codex-plugin/plugin.json`
- `plugin/creator-toolchain/release-evidence/`

### Source Toolchain

- `https://github.com/ChristopherKahler/paul`
- `https://github.com/ChristopherKahler/seed`
- `https://github.com/ChristopherKahler/base`
- `https://github.com/ChristopherKahler/carl`
- `https://github.com/ChristopherKahler/skillsmith`
- `https://github.com/ChristopherKahler/aegis`

### Codex Plugin Guidance

- `https://developers.openai.com/codex/plugins/build`

## 27. Execution Handoff

Do not execute this plan until the repository owner completes final review and explicitly authorizes the PAUL Apply cycle.

Recommended execution mode after approval:

1. use `superpowers:subagent-driven-development` for independent phase workers with review between phases; or
2. use `superpowers:executing-plans` inline with checkpoints after Phases 1, 3, 6, and 8.

In either mode, Phase 0 must run first, every destructive action remains approval-gated, and Phase 9 Unify is mandatory.
