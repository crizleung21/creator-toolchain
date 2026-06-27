# ChristopherKahler Toolchain Map

**Status:** Research baseline  
**Date:** 2026-06-26  
**Scope:** `paul`, `seed`, `base`, `carl`, `skillsmith`, `aegis`  
**Purpose:** 建立 ChristopherKahler 工具鏈的端到端工作流、核心功能、交接點、移植價值與版本漂移風險。

---

## 0. BLUF

ChristopherKahler 的工具鏈不是單一程式，而是一套 Claude Code 導向的 agentic workflow stack：

```text
SEED        idea -> typed PLANNING.md
PAUL        PLANNING/PROJECT -> Plan -> Apply -> Unify execution loop
BASE        workspace state, surfaces, hooks, MCP, drift/groom maintenance
CARL        just-in-time behavioral rules, decisions, staging, prompt injection
Skillsmith  skill discovery/scaffold/distill/audit factory
AEGIS       evidence-first codebase audit -> remediation knowledge -> PAUL handoff
```

最高價值不在 install script，而在六個可移植概念：

1. **Typed intake:** 先分類工作類型，再決定探索深度和輸出模板。
2. **Closure-enforced execution:** 每個 plan 必須經過 Plan -> Apply -> Unify，不容許半完成。
3. **Repo/workspace state surfaces:** 將狀態轉成結構化 JSON/TOML/Markdown，讓 agent 可以恢復、審核和同步。
4. **JIT rule routing:** 規則只在 prompt 相關時注入，降低 context bloat。
5. **Skill manufacturing:** 用 spec、scaffold、audit 統一 skill 形狀和品質。
6. **Audit-to-remediation separation:** AEGIS 只診斷和產生 PAUL-ready plan，不直接修改代碼。

---

## 1. Research Baseline

Local source snapshot was cloned into `upstream/` on 2026-06-26 and indexed with `codebase-memory-mcp`.

| Repo | Package / install surface | Local HEAD checked | Commit time |
|---|---|---:|---|
| `paul` | `paul-framework` v1.4.0, `npx paul-framework` | `960b05c0b8e1f876f49674a700c9a087afebb8ac` | 2026-06-25T22:28:20-05:00 |
| `seed` | `@chrisai/seed` v1.0.0, `npx @chrisai/seed` | `1183a1e43df06171a4d91719f28e22ff0b28e3f4` | 2026-06-03T16:17:05-05:00 |
| `skillsmith` | `@chrisai/skillsmith` v1.0.0, `npx @chrisai/skillsmith` | `7a9ff943ae8905cdbaf858436f8da961ebc2ebfe` | 2026-06-03T16:17:25-05:00 |
| `base` | `@chrisai/base` v3.1.5, `npx @chrisai/base` / `base-framework` bin | `85f861c0a1efc90504f1b29e932b7145336c067e` | 2026-04-29T14:33:31-05:00 |
| `carl` | `carl-core` v2.0.2, `npx carl-core` | `479319fc6da1176aa2f36203d42c7e0e43ad1c94` | 2026-04-29T14:31:28-05:00 |
| `aegis` | shell installer, no npm package in repo | `73a64618a6f74d6bf74b0ad535197f196be73fd4` | 2026-04-29T14:31:32-05:00 |

Primary evidence is local cloned source plus public GitHub URLs:

- https://github.com/ChristopherKahler/paul
- https://github.com/ChristopherKahler/seed
- https://github.com/ChristopherKahler/base
- https://github.com/ChristopherKahler/carl
- https://github.com/ChristopherKahler/skillsmith
- https://github.com/ChristopherKahler/aegis

---

## 2. System Architecture

### 2.1 Functional layers

| Layer | Tool | Job |
|---|---|---|
| Ideation / intake | SEED | Convert raw ideas into typed `PLANNING.md`; optionally graduate to build directory. |
| Execution loop | PAUL | Convert approved project context into executable plans; enforce Apply/Qualify and Unify closure. |
| Workspace state | BASE | Maintain `.base/` data surfaces, hooks, MCP tools, operator profile, drift/groom lifecycle. |
| Behavioral context | CARL | Load domain rules/decisions only when recall keywords or star commands match. |
| Skill production | Skillsmith | Create, scaffold, distill, and audit Claude Code skill packs. |
| Codebase audit | AEGIS | Run multi-agent audit, synthesize evidence, generate remediation playbooks and PAUL-ready plans. |

### 2.2 Runtime surface types

| Surface type | Repos | Examples |
|---|---|---|
| Markdown slash-command packs | PAUL, SEED, Skillsmith, BASE, AEGIS | `commands/*.md`, `tasks/*.md`, `workflows/*.md` |
| Install scripts | All | `bin/install.js`, `install.sh` |
| Structured state | PAUL, BASE, CARL, SEED, AEGIS | `.paul/STATE.md`, `.paul/paul.toml`, `.base/data/*.json`, `.carl/carl.json`, `.aegis/STATE.md` |
| Hooks | BASE, CARL | `UserPromptSubmit`, `SessionStart` |
| MCP servers | BASE, CARL | `base-mcp`, `carl-mcp` |
| Knowledge/spec references | Skillsmith, AEGIS, PAUL | syntax specs, schemas, personas, rules, quality references |

---

## 3. End-to-End Workflow

### 3.1 Normal creator/build flow

```text
Raw idea
  -> /seed
  -> select project type
  -> guided conversation via data/{type}/guide.md
  -> projects/{name}/PLANNING.md
  -> /seed graduate or /seed launch
  -> apps/{name}/README.md + git repo
  -> /paul:init
  -> .paul/PROJECT.md, ROADMAP.md, STATE.md, paul.toml
  -> /paul:plan
  -> /paul:apply
  -> /paul:unify
  -> repeat until milestone complete
```

SEED owns the **idea-to-plan** boundary. PAUL owns the **plan-to-implementation** boundary.

### 3.2 Workspace maintenance flow

```text
BASE install
  -> .base/workspace.json + .base/data/*.json
  -> hooks inject pulse/operator/PSMM/surfaces
  -> base-mcp provides structured CRUD
  -> /base:pulse reports drift
  -> /base:groom reviews projects/backlog/satellites/system layer
  -> staged CARL proposals reviewed via /base:carl-hygiene
```

BASE is the portfolio/workspace owner. It should not own project execution logic; that stays in PAUL.

### 3.3 Rule learning flow

```text
Session event / correction / decision
  -> BASE PSMM can log ephemeral session memory
  -> CARL proposal can be staged
  -> human reviews staging during hygiene
  -> approved rule enters .carl/carl.json
  -> CARL hook injects rule when prompt matches recall keywords
```

CARL prevents global prompt bloat by routing only relevant rules into context.

### 3.4 Audit/remediation flow

```text
/aegis:audit
  -> Phase 0 context/threat model
  -> Phase 1 automated signals
  -> Phase 2 domain audits
  -> Phase 3 cross-domain synthesis
  -> Phase 4 Devil's Advocate
  -> Phase 5 final report
  -> /aegis:transform
  -> Phase 6 playbooks
  -> Phase 7 risk validation + guardrails
  -> Phase 8 PAUL-compatible remediation project
  -> PAUL executes with human checkpoints
```

AEGIS deliberately stops before code changes. PAUL is the execution handoff.

---

## 4. Repo-by-Repo Analysis

### 4.1 PAUL

**Role:** disciplined implementation loop.

Evidence:

- README defines PAUL as Plan-Apply-Unify for Claude Code and lists principles: loop integrity, in-session context, acceptance-driven development.
- Quick workflow is `/paul:init` -> `/paul:plan` -> `/paul:apply` -> `/paul:unify` -> `/paul:progress`.
- Project state lives under `.paul/`: `PROJECT.md`, `ROADMAP.md`, `STATE.md`, `paul.toml`, `ledger.toml`, phase plans and summaries.
- `src/workflows/plan-phase.md` classifies scope as quick-fix, standard, or complex, then creates acceptance criteria and task specs.
- `src/workflows/apply-phase.md` enforces explicit plan approval, required-skill checks, Execute/Qualify loop, task statuses, and checkpoint routing.
- `src/workflows/unify-phase.md` reconciles plan vs actual, writes `SUMMARY.md`, updates `STATE.md`, syncs `paul.toml`, appends `ledger.toml`, and handles phase transition.

Core functions:

1. Initialize a project with durable context.
2. Create executable `PLAN.md` with BDD-style acceptance criteria.
3. Execute tasks only after approval.
4. Re-read and verify outputs before claiming completion.
5. Close every plan with `UNIFY`.
6. Maintain machine-readable project state for external systems.

High-value transplant:

- Keep Plan -> Apply -> Qualify -> Unify as a required lifecycle.
- Port the E/Q loop and anti-rationalization rules.
- Preserve explicit statuses: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`.
- Preserve closure artifacts: plan, summary, state update, ledger.

Risk:

- PAUL docs are tightly Claude Code slash-command oriented. For Codex, convert command pack semantics into Codex skill workflows instead of copying `.claude/commands` layout directly.

### 4.2 SEED

**Role:** project incubator before build starts.

Evidence:

- README defines SEED as typed project incubator that produces structured `PLANNING.md`.
- Default project types: application, workflow, client, utility, campaign.
- `/seed launch` graduates a project and initializes PAUL using PLANNING/README context.
- `tasks/ideate.md` writes `SEED-STATE.md` checkpoints, loads type-specific guide/config/template files, and deletes checkpoint after `PLANNING.md` is approved.
- `tasks/graduate.md` creates `apps/{name}/`, initializes git, synthesizes README, and optionally registers in BASE.
- `tasks/launch.md` delegates graduation, checks PAUL, and instructs PAUL init not to re-ask questions already answered by SEED.

Core functions:

1. Type-first routing.
2. Type-specific exploration files under `data/{type}/`.
3. Checkpointable ideation with `SEED-STATE.md`.
4. Quality gate before graduation.
5. Build handoff through `PLANNING.md` and synthesized README.

High-value transplant:

- Use typed intake to prevent one-size-fits-all planning.
- Keep `PLANNING.md` as a stable bridge between ideation and execution.
- Keep `graduate` and `launch` separate: graduation can stand alone; launch is graduation plus PAUL init.

Risk:

- SEED has stale assumptions about BASE v2 Rust binary and `.base/data/*.json` being v1 artifacts, while current BASE v3 uses `.base/data/*.json`.

### 4.3 BASE

**Role:** workspace operating layer.

Evidence:

- README positions BASE as workspace memory, health tracking, drift prevention, and manifest-driven data surfaces.
- Data surfaces are JSON files plus hooks that inject compact summaries.
- Built-in data: projects, entities, state, PSMM.
- Installer creates global commands/skills and optional `.base/` workspace layer.
- `.base/` contains `workspace.json`, `operator.json`, `.base/data/*.json`, hooks, schemas, MCP server.
- `base-mcp` exposes projects, state, entities, operator, PSMM, satellite tools.
- `base-pulse-check.py` recalculates drift and reports overdue groom/CARL hygiene.
- `groom.md` walks projects, backlog, directories, satellites, and system layer; then logs groom and resets drift.

Core functions:

1. Workspace manifest and state surfaces.
2. Passive prompt context injection via hooks.
3. Structured workspace CRUD via MCP.
4. Drift and groom maintenance cycle.
5. Operator profile injection.
6. PAUL satellite discovery and health checks.
7. PSMM session memory.

High-value transplant:

- Use repo-local `.creator/` or equivalent state surfaces.
- Keep data surface model: JSON source -> summarizer/injector -> agent context.
- Separate maintenance from execution; BASE reports and organizes, PAUL executes.

Risk:

- Current BASE repo is v3.1.5, Node + MCP + `.base/data/*.json`. Other repos still call BASE v2 Rust/graph. Treat BASE integration as unstable until reconciled.

### 4.4 CARL

**Role:** just-in-time rule router.

Evidence:

- README defines CARL as Context Augmentation & Reinforcement Layer.
- Installed artifacts include `.carl/carl.json`, `sessions/`, `carl-mcp`, `hooks/carl-hook.py`, settings hook registration, and `.mcp.json` registration.
- CARL v2 architecture uses one `carl.json` with `config`, `domains`, and `staging`.
- MCP tools manage domains, rules, decisions, staging, and config.
- `hooks/carl-hook.py` reads all `.carl/carl.json` scopes, merges global/local config, detects star commands, matches recall keywords, injects `<carl-rules>`, and deduplicates repeated context.

Core functions:

1. Domain-based rule storage.
2. Recall keyword activation.
3. Global/local scope merge.
4. Star-command explicit activation.
5. Decision log attached to domains.
6. Proposal staging before permanent rules.
7. Deduplicated context injection.

High-value transplant:

- Keep CARL as behavioral rule layer, not project state layer.
- Keep staging review; do not let session observations become permanent rules automatically.
- Use explicit rule preflight if hooks are not available.

Risk:

- Hook-based hidden injection has trust and debuggability implications. In Codex-native design, prefer explicit rule-router skill first, hooks later behind review gate.

### 4.5 Skillsmith

**Role:** skill factory and compliance layer.

Evidence:

- README defines four workflows: Discover, Scaffold, Distill, Audit.
- It defines seven file types: entry points, tasks, templates, frameworks, context, checklists, rules.
- Architecture separates operational skill files from reference `specs/`.
- Installer copies `commands/skillsmith/` plus `skillsmith-specs/`.
- `tasks/scaffold.md` parses a skill spec, chooses location, creates directory structure, generates entry point and auxiliary files, validates, optionally hands off large skills to PAUL.
- `tasks/audit.md` inventories a skill, classifies tier, checks files against specs, scores compliance, and writes a remediation report.

Core functions:

1. Guided skill discovery into `SKILL-SPEC.md`.
2. Spec-to-directory scaffold.
3. Raw source distillation into framework chunks.
4. Compliance audit with per-component scores.
5. Thin entry point, process logic in tasks, knowledge in frameworks.

High-value transplant:

- Use Skillsmith as a quality gate for any local Creator Toolchain skills.
- Preserve progressive disclosure: entry point routes; tasks load only when invoked; specs are on-demand references.

Risk:

- Claude Code slash-command skill conventions do not map one-to-one to Codex `SKILL.md`. Port the architecture principles, not the exact file syntax.

### 4.6 AEGIS

**Role:** evidence-first codebase audit and controlled remediation planning.

Evidence:

- README defines AEGIS as multi-session, multi-agent codebase audit across 14 domains and 12 senior engineering personas.
- Core phases: 0 context/threat model, 1 automated signals, 2 domain audits, 3 cross-domain, 4 adversarial review, 5 final report.
- Output layers: Layer A diagnostic artifact, Layer B remediation knowledge, Layer C change orchestration.
- Transform phases 6-8 generate playbooks, risk-scored plans, guardrails, verification plans, and PAUL-compatible remediation project.
- README states Transform never applies changes directly; execution happens through PAUL.
- `commands/audit.md` shows scope selection, tool selection, user confirmation, phase checkpoints, and resumability.
- `commands/transform.md` requires completed Layer A, displays intervention levels/confidence, then runs phases 6-8.
- `phase-8-execution-planning.md` writes dependency graph, verification plan, and `execution/paul-project/`.

Core functions:

1. Formal domain coverage.
2. Evidence schema: observations, interpretations, judgments, confidence, disagreement.
3. Independent personas with narrow responsibilities.
4. Devil's Advocate challenge before synthesis.
5. Principal Engineer synthesis and disagreement resolution.
6. Transform pipeline with intervention levels and safety gates.
7. PAUL-ready execution handoff.

High-value transplant:

- Separate diagnosis from remediation from execution.
- Keep confidence thresholds and intervention-level gates.
- Keep "no auto-execution" as a hard boundary.

Risk:

- AEGIS installer on `main` sets `AEGIS_BRANCH="feature/v1-implementation"` for remote tarball download, so the apparent main branch and installed branch can diverge.

---

## 5. Cross-Tool Integration Matrix

| Integration | Intended flow | Evidence status | Design note |
|---|---|---|---|
| SEED -> PAUL | `PLANNING.md` and README feed headless PAUL init. | Strong in SEED README/tasks. | Good to port. |
| PAUL -> BASE | PAUL manifest is read by BASE for workspace/project awareness. | Concept strong, file-format drift present. | Reconcile `paul.toml` vs `paul.json` before implementation. |
| BASE -> CARL | BASE groom/hygiene reviews CARL staged proposals. | Strong in BASE groom docs and README. | Good to port as explicit hygiene workflow. |
| CARL -> PAUL | CARL loads PAUL rules only inside relevant project/context. | Strong in CARL README. | Good concept; hook implementation optional. |
| Skillsmith -> SEED | SEED was built with Skillsmith conventions. | Stated in README. | Use as pattern, not hard dependency. |
| Skillsmith -> PAUL | Large skill scaffold can be handed to PAUL for phased build. | Strong in Skillsmith tasks. | Good to port for large generated artifacts. |
| AEGIS -> PAUL | Layer C generates PAUL-compatible execution artifacts. | Strong in AEGIS README/workflows. | Critical boundary: audit never executes. |

---

## 6. Version Drift and Contradictions

These are not minor wording issues; they affect any faithful port.

### 6.1 BASE v2 Rust vs BASE v3 Node/MCP

Several repos describe BASE v2 as Rust binary / knowledge graph / no MCP. Current `base` repo package is `@chrisai/base` v3.1.5 and installs `.base/base-mcp`, `.base/data/*.json`, hooks, schemas, and `workspace.json`.

Impact:

- Do not copy "BASE v2 Rust graph" assumptions into `creator-toolchain` unless separately verified.
- Use the current `base` repo as primary evidence for BASE implementation behavior.
- Treat SEED/Skillsmith BASE integration text as stale unless updated.

### 6.2 `paul.toml` vs `paul.json`

PAUL v1.4 docs and workflows prefer `.paul/paul.toml` and migrate from `paul.json`. Current BASE satellite hooks still scan `.paul/paul.json` in multiple places.

Impact:

- Cross-tool state sync is not currently self-consistent across repos.
- A port should choose one manifest contract and adapt all satellite detection to it.
- Recommended: use TOML or JSON consistently, but not both as active sources.

### 6.3 SEED / Skillsmith BASE detection conflicts with current BASE

SEED and Skillsmith hard-stop when `.base/data/*.json` exists, calling it BASE v1 JSON store. Current BASE v3 installer intentionally creates `.base/data/*.json`.

Impact:

- Running these tools together as-is may misclassify current BASE as old/incompatible.
- A port should not inherit this check.

### 6.4 AEGIS installer branch divergence

AEGIS README quick install fetches `install.sh` from `main`, but the script downloads framework tarball from `feature/v1-implementation`.

Impact:

- Installed AEGIS may not exactly match the main branch reviewed.
- For migration, pin a specific release/commit instead of branch indirection.

---

## 7. Core Function Checklist for Creator Toolchain Port

### Must preserve

- [ ] SEED-style typed intake before planning.
- [ ] PAUL-style closure loop with mandatory `Unify`.
- [ ] Apply-phase qualification by re-reading actual outputs and running verification fresh.
- [ ] Structured state surfaces for project/workspace status.
- [ ] CARL-style explicit domain/rule model with staging.
- [ ] Skillsmith-style skill anatomy and compliance audit.
- [ ] AEGIS-style diagnostic/remediation/execution separation.
- [ ] Evidence, confidence, disagreement, and safety gates.

### Should adapt

- [ ] Replace `.claude/commands` assumption with Codex skill layout.
- [ ] Replace hidden hook-first behavior with explicit skill-first workflows unless a hook trust gate passes.
- [ ] Rename `.base`, `.carl`, `.paul` state if the local product wants a unified `.creator/` state layer.
- [ ] Convert Claude slash-command entry points into Codex `SKILL.md` triggers and references.
- [ ] Reconcile manifest contracts before implementing satellite/project sync.

### Should not copy blindly

- [ ] BASE v2 Rust / graph claims without current source.
- [ ] Any `paul.json` sync logic if active PAUL target is `paul.toml`.
- [ ] SEED/Skillsmith checks that treat `.base/data/*.json` as obsolete.
- [ ] AEGIS branch-download behavior.
- [ ] CLAUDE.md injection blocks as-is for Codex.

---

## 8. Recommended Creator Toolchain Model

For a Codex-native Creator Toolchain, use this mapping:

| ChristopherKahler source | Creator Toolchain module | Porting principle |
|---|---|---|
| SEED | `creator-seed-incubator` | Type-aware project intake and `PLANNING.md` equivalent. |
| PAUL | `creator-paul-loop` | Plan -> Apply -> Qualify -> Unify execution closure. |
| BASE | `creator-base-workspace` | `.creator/` state surfaces, pulse/groom/drift, operator profile. |
| CARL | `creator-rule-router` | Domain rules, recall, staging, explicit preflight; hooks optional later. |
| Skillsmith | `creator-skillsmith-factory` | Codex skill scaffold/audit/spec factory. |
| AEGIS | `creator-aegis-audit` | Evidence-first audit, Layer A/B/C, PAUL-ready remediation handoff. |

The minimal viable build should start with:

```text
creator-orchestrator
creator-seed-incubator
creator-paul-loop
```

Then add:

```text
.creator/ state
creator-rule-router
creator-skillsmith-factory
creator-aegis-audit
plugin packaging
```

---

## 9. Evidence Map

High-signal local source references:

- `upstream/paul/README.md:41-48` — PAUL principles.
- `upstream/paul/README.md:83-102` — quick workflow.
- `upstream/paul/README.md:248-278` — `.paul/` project state.
- `upstream/paul/src/workflows/plan-phase.md:51-80` — scope routing.
- `upstream/paul/src/workflows/apply-phase.md:89-160` — Execute/Qualify loop.
- `upstream/paul/src/workflows/unify-phase.md:91-208` — summary, state, manifest sync.
- `upstream/seed/README.md:54-58` — typed incubator purpose.
- `upstream/seed/README.md:98-117` — SEED workflow.
- `upstream/seed/tasks/ideate.md:27-63` — `SEED-STATE.md`.
- `upstream/seed/tasks/graduate.md:121-220` — graduation flow.
- `upstream/seed/tasks/launch.md:168-183` — headless PAUL init.
- `upstream/base/README.md:76-85` — managed workspace purpose.
- `upstream/base/README.md:108-128` — data surfaces.
- `upstream/base/README.md:141-166` — hooks.
- `upstream/base/README.md:356-370` — MCP modules.
- `upstream/base/src/hooks/base-pulse-check.py:28-126` — drift recalculation.
- `upstream/base/src/framework/tasks/groom.md:18-139` — groom workflow.
- `upstream/carl/README.md:140-168` — `carl.json` architecture.
- `upstream/carl/README.md:234-256` — MCP tools.
- `upstream/carl/hooks/carl-hook.py:215-356` — scope discovery and merge.
- `upstream/carl/hooks/carl-hook.py:381-411` — prompt-domain matching.
- `upstream/carl/hooks/carl-hook.py:566-740` — hook main flow and injection.
- `upstream/skillsmith/README.md:40-50` — four workflows.
- `upstream/skillsmith/README.md:152-190` — operational/spec layers.
- `upstream/skillsmith/tasks/scaffold.md:89-207` — spec parsing and entry point generation.
- `upstream/skillsmith/tasks/audit.md:57-172` — inventory and compliance checks.
- `upstream/aegis/README.md:89-120` — AEGIS philosophy.
- `upstream/aegis/README.md:495-591` — core phases and output layers.
- `upstream/aegis/README.md:742-790` — transform phases.
- `upstream/aegis/README.md:888-955` — no auto-execution and PAUL handoff.
- `upstream/aegis/commands/audit.md:96-220` — audit scope/config/phase loop.
- `upstream/aegis/commands/transform.md:30-193` — transform command flow.
- `upstream/aegis/src/transform/workflows/phase-8-execution-planning.md:61-150` — PAUL-compatible execution plan generation.

---

## 10. Research Limitations

- Analysis is source-level and README-level; I did not execute the tools inside Claude Code.
- GitHub/NPM package publication state may differ from cloned repo state.
- AEGIS remote installer may install `feature/v1-implementation`, not the `main` tree inspected here.
- The BASE v2/v3 inconsistency should be treated as an active integration risk until upstream docs/scripts are reconciled.
