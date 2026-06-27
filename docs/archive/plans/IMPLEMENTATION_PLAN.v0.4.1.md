# creator-toolchain — IMPLEMENTATION_PLAN.md

**Version:** 0.4.1-draft  
**Status:** Audit amendment candidate; original `IMPLEMENTATION_PLAN.md` remains unchanged until user approval  
**Date:** 2026-06-26  
**Canonical Repository Name:** `creator-toolchain`  
**Former Working Names:** `creator-agentic-os-codex`, `ck-agentic-os-codex`  
**Primary Goal:** 將 ChristopherKahler 工具鏈的高價值方法論移植成 **Codex-native Creator Toolchain / Creator Agentic OS**  
**Implementation Strategy:** 先完成 MVP Skill Suite，再逐步加入 state、rules、skill factory、audit，最後包裝成 Codex Plugin。  
**Companion Document:** `SOURCE_TRACEABILITY_AND_AUDIT.md`  
**Language Policy:** 文件以繁中為主；檔案名、schema key、skill name、Codex trigger 保持英文。  

---

## 0. BLUF

`creator-toolchain` 應實作成：

```text
Codex-native Skill Suite
+ repo-local .creator/ state layer
+ CARL-style domain rule router
+ Skillsmith-style skill factory
+ AEGIS-style evidence-first audit layer
+ optional Codex Plugin package
```

它不是 ChristopherKahler 工具鏈的機械複製，而是將其核心能力轉成 Creator-first / Codex-native 工作流。`Creator Agentic OS` 只保留作架構副標題，不再作 repo 或 plugin 主名。

五個 implementation phases：

```text
Phase 1 — MVP Skill Suite
  creator-orchestrator
  creator-seed-incubator
  creator-paul-loop

Phase 2 — Add State Layer
  creator-base-workspace
  .creator/ state surfaces
  operator profile / entities / PSMM / backlog / groom / pulse / drift

Phase 3 — Add Rules + Skill Factory
  creator-rule-router
  creator-skillsmith-factory
  CARL-style domain rules
  Skillsmith-style skill anatomy / distill / audit / scoring

Phase 4 — Add Audit
  creator-aegis-audit
  AEGIS Layer A/B/C
  evidence / confidence / disagreement / remediation handoff

Phase 5 — Package as Codex Plugin
  creator-toolchain plugin
  schema-validated .codex-plugin/plugin.json
  bundled skills
  optional hooks / optional MCP / local marketplace testing
```

**Important:** Phase 1 should be implemented first and validated before Phase 2–5 work begins. This `v0.4.1` draft is not final until the amendment checklist and source-drift risks below are accepted.

---

## 1. Output Contract

| Deliverable | Format | Acceptance Criteria |
|---|---|---|
| Master plan | `IMPLEMENTATION_PLAN.md` | 明確描述 Phase 0–5，足夠作為 repo build spec |
| Source traceability | `SOURCE_TRACEABILITY_AND_AUDIT.md` | 每個 ChristopherKahler 高價值功能都有 source evidence、implementation target、acceptance test、gap status |
| Canonical naming | naming policy | active repo / plugin name 使用 `creator-toolchain`；active skill prefix 使用 `creator-*`；`ck-*` 只作 migration note |
| Codex-native design | architecture policy | 使用 Codex Skills / `AGENTS.md` / repo-local state；不照搬 Claude Code slash commands |
| Creator domain fit | creator workflow specs | 支援 creator production workflows，但不把 plugin description 寫成具體 domain 列表 |
| Risk control | trust/privacy/release gates | Hooks、MCP、Plugin packaging 均有 explicit gate |
| QA readiness | test prompts + audit protocol | 可用多回合審核檢查每一 phase |
| Amendment control | `IMPLEMENTATION_PLAN.v0.4.1.md` | 修訂版先獨立輸出；不得覆蓋原 `IMPLEMENTATION_PLAN.md`，除非 user 明確批准 |

---

## 2. Phase 0 — Research Baseline and Design Freeze

### 2.1 Purpose

Phase 0 is a documentation and decision-freeze phase. It prevents building before source analysis is complete.

### 2.2 Required Inputs

| Input | Required |
|---|---:|
| ChristopherKahler GitHub profile reviewed | Yes |
| `paul` reviewed | Yes |
| `seed` reviewed | Yes |
| `base` reviewed | Yes |
| `carl` reviewed | Yes |
| `skillsmith` reviewed | Yes |
| `aegis` reviewed | Yes |
| Codex Skills docs reviewed | Yes |
| Codex Plugin build docs reviewed | Yes |
| Codex Hooks docs reviewed | Yes |
| Codex Subagents docs reviewed | Yes |

### 2.3 Phase 0 Deliverables

```text
SOURCE_TRACEABILITY_AND_AUDIT.md
docs/source-analysis/christopherkahler-toolchain-map.md
docs/source-analysis/paul-porting-notes.md          # optional per-tool expansion unless created
docs/source-analysis/seed-porting-notes.md          # optional per-tool expansion unless created
docs/source-analysis/base-porting-notes.md          # optional per-tool expansion unless created
docs/source-analysis/carl-porting-notes.md          # optional per-tool expansion unless created
docs/source-analysis/skillsmith-porting-notes.md    # optional per-tool expansion unless created
docs/source-analysis/aegis-porting-notes.md         # optional per-tool expansion unless created
```

### 2.3.1 Canonical Source Evidence

`docs/source-analysis/christopherkahler-toolchain-map.md` is the canonical Phase 0 evidence map for this implementation plan. Per-tool porting notes may be added later, but they must not contradict the map.

| Evidence Item | Path / Source | Status | Freshness |
|---|---|---|---|
| Six-tool workflow map | `docs/source-analysis/christopherkahler-toolchain-map.md` | required | refreshed 2026-06-26 |
| Source traceability companion | `SOURCE_TRACEABILITY_AND_AUDIT.md` | required, amendment needed | pending v0.4.1 alignment |
| Upstream research clones | `upstream/{paul,seed,base,carl,skillsmith,aegis}` | local research only | must not be packaged |
| Per-tool notes | `docs/source-analysis/*-porting-notes.md` | optional expansion | required only if created |

### 2.3.2 Source Drift and Non-Inheritance Checklist

The Creator Toolchain must intentionally port capabilities, not inherit upstream inconsistencies.

- [ ] Do not inherit BASE v2 Rust / graph-storage assumptions when implementing the current `.creator/` JSON state layer.
- [ ] Do not inherit obsolete `.base/data/*.json` detection from SEED / Skillsmith when checking Creator Toolchain state.
- [ ] Do not mix `paul.toml` and `paul.json` semantics; choose one Creator manifest contract and document it.
- [ ] Do not inherit AEGIS installer behavior that depends on a non-default implementation branch.
- [ ] Do not package `upstream/` repositories, `.DS_Store`, local research notes, or private `.creator/` state.
- [ ] Treat Codex Plugin manifest examples as draft until validated against current official schema at Phase 5 packaging time.

### 2.4 Design Freeze Gate

Phase 1 may begin only when:

- [ ] source traceability matrix exists
- [ ] final active naming is `creator-toolchain`
- [ ] `.creator/` state directory is confirmed
- [ ] Phase 1 scope excludes Phase 2–5 implementation
- [ ] Codex Plugin packaging is explicitly deferred to Phase 5
- [ ] `docs/source-analysis/christopherkahler-toolchain-map.md` exists and is cited as canonical source evidence
- [ ] source drift / non-inheritance checklist above is resolved
- [ ] `SOURCE_TRACEABILITY_AND_AUDIT.md` is amended or explicitly marked stale relative to `v0.4.1`
- [ ] `SOURCE_TRACEABILITY_AND_AUDIT.md` may say “Pass” only after required P0 + v0.4.1 amendments are resolved

---

## 3. Source-Grounded Assumptions

### 3.1 Codex Assumptions

| Codex Feature | Implementation Assumption | Design Impact |
|---|---|---|
| Skills | A skill is a directory with required `SKILL.md`; `SKILL.md` requires `name` and `description`; optional directories include `references/`, `assets/`, `scripts/`, `agents/`. | Each workflow becomes a focused skill directory. |
| Progressive disclosure | Codex initially sees skill name, description, and path, then loads the full skill only when chosen. | Description must be precise, trigger-friendly, and bounded. |
| `AGENTS.md` | Repo guidance is read before work and should be stable and concise. | Put durable rules in `AGENTS.md`; put workflow logic in skills. |
| Plugins | A plugin is a distribution unit; manifest is expected under `.codex-plugin/plugin.json`, but exact schema must be validated at packaging time. | Package only after local skill suite passes audit and schema validation passes. |
| Hooks | Hooks can run at lifecycle events but require trust review. | Hooks are optional and disabled until reviewed. |
| Subagents | Subagents are explicit; they consume more tokens and should not be assumed automatic. | AEGIS personas are subagent-ready, not auto-spawned. |
| MCP | MCP is useful for external tool access but increases permission surface. | MCP remains optional and explicit. |

### 3.2 ChristopherKahler Toolchain Assumptions

| Tool | Source Role | Creator Toolchain Port |
|---|---|---|
| PAUL | Plan-Apply-Unify loop, mandatory closure, acceptance-driven execution, state reconciliation | `creator-paul-loop` |
| SEED | Type-aware project incubator, `PLANNING.md`, graduate / launch to PAUL | `creator-seed-incubator` |
| BASE | Workspace OS, data surfaces, operator profile, PSMM, pulse/groom/drift | `creator-base-workspace` |
| CARL | Domain-based just-in-time behavioral rules, keyword recall, staging | `creator-rule-router` |
| Skillsmith | Discover / Scaffold / Distill / Audit for skills; seven file type specs | `creator-skillsmith-factory` |
| AEGIS | Multi-persona audit, Layer A/B/C, evidence-first remediation planning | `creator-aegis-audit` |

---

## 4. ChristopherKahler Toolchain Extraction Summary

| Original Tool | High-Value Function | Do Not Copy Directly | Creator Toolchain Port |
|---|---|---|---|
| PAUL | disciplined execution loop with mandatory closure | Claude slash commands / `.paul/` assumptions | `creator-paul-loop` with Plan → Apply → Qualify → Unify |
| SEED | typed idea incubation and launch handoff | Claude command installer | `creator-seed-incubator` with `PLANNING.md`, graduate, launch, status, add-type |
| BASE | workspace state, data surfaces, PSMM, operator profile | global hooks / MCP-first design | `.creator/` state layer + manual pulse/groom first |
| CARL | domain rules and JIT behavioral context | automatic hook injection in early phase | domain `rules.json` + explicit rule preflight |
| Skillsmith | skill authoring factory | Claude-specific command structure | Codex skill factory with `SKILL.md`, references, assets, scoring |
| AEGIS | evidence-first multi-persona audit and PAUL handoff | automatic code changes | diagnosis → remediation → orchestration → `creator-paul-loop` handoff |

---

## 4.1 Version Drift and Integration Risk Register

This plan must preserve source intent while avoiding incompatible upstream implementation details.

| Risk | Source Pattern | Creator Decision | Acceptance Gate |
|---|---|---|---|
| PAUL manifest drift | upstream docs/code may refer to `paul.toml` or `paul.json` depending on version | define Creator-native manifests under `.creator/` and do not copy either format blindly | Phase 1 defines `project.json` + `activity_ledger.jsonl` |
| BASE architecture drift | older BASE notes mention Rust/graph storage; newer active surface is Node/MCP-oriented | keep Phase 2 repo-local JSON state first; MCP remains optional | Phase 2 has no required daemon, database, or MCP |
| SEED / Skillsmith state detection conflict | some upstream checks look for `.base/data/*.json` | Creator Toolchain checks `.creator/*.json` only | validation scripts reject `.base/data` as active dependency |
| AEGIS branch divergence | installer behavior may depend on implementation branch details | port AEGIS audit concepts, not installer mechanics | Phase 4 uses local skill workflow and explicit artifacts |
| Plugin schema freshness | Codex plugin schema may change | validate current official schema during Phase 5 | no release without schema validation evidence |
| Research artifact leakage | local `upstream/` clones and system files may exist in workspace | packaging script excludes research and local files | package manifest / archive audit passes |

---

## 5. Canonical Naming Policy

### 5.1 Project Name

| Old | New |
|---|---|
| `creator-agentic-os-codex` | `creator-toolchain` |
| `ck-agentic-os-codex` | `creator-toolchain` |

### 5.2 Skill Name Mapping

| Old Name | New Name | Phase |
|---|---|---|
| `ck-orchestrator` | `creator-orchestrator` | Phase 1 |
| `ck-seed-incubator` | `creator-seed-incubator` | Phase 1 |
| `ck-paul-loop` | `creator-paul-loop` | Phase 1 |
| `ck-base-workspace` | `creator-base-workspace` | Phase 2 |
| `ck-carl-rules` | `creator-rule-router` | Phase 3 |
| `ck-skillsmith-factory` | `creator-skillsmith-factory` | Phase 3 |
| `ck-aegis-audit` | `creator-aegis-audit` | Phase 4 |
| `ck-agentic-os-plugin` | `creator-toolchain-plugin` | Phase 5 |

### 5.3 State Directory Naming

| Old | New |
|---|---|
| `.ck/` | `.creator/` |
| `.ck/workspace.json` | `.creator/workspace.json` |
| `.ck/projects.json` | `.creator/projects.json` |
| `.ck/rules.json` | `.creator/rules.json` |
| `.ck/reports/` | `.creator/reports/` |
| `.ck/plans/` | `.creator/plans/` |

### 5.4 Naming Audit Rule

Before every release:

```bash
grep -R "ck-" .
grep -R ".ck" .
grep -R "creator-agentic-os-codex" .
```

Allowed matches:

- migration docs
- historical notes
- source comparison docs
- `SOURCE_TRACEABILITY_AND_AUDIT.md` if describing prior drafts

Not allowed:

- active skill names
- active file paths
- active examples
- plugin manifest
- README quick start
- current install instructions

---

## 6. System Vision

### 6.1 What This Is

`creator-toolchain` is a **Codex-native Creator Toolchain** for structured creator and builder workflows.

It provides:

- workflow routing
- project planning
- disciplined execution
- repo-local state
- domain rules
- skill creation
- evidence-first audit
- plugin packaging

### 6.2 Core Loop

```text
Idea
→ Route
→ Plan
→ Execute
→ Qualify
→ Unify
→ Track
→ Apply Rules
→ Build Skills
→ Audit
→ Package
```

### 6.3 What This Is Not

It is not:

- a direct Claude Code clone
- a blind port of ChristopherKahler repos
- a single mega-prompt
- a background daemon
- a mandatory MCP server
- a plugin before local workflows are validated
- a system that silently edits or archives state without user visibility

---

## 7. Codex-Native Design Doctrine

| Claude Code Pattern | Codex-Native Translation |
|---|---|
| Slash commands such as `/paul:plan` | explicit skill invocation such as `$creator-paul-loop`, plus implicit invocation |
| `.claude/commands/` | repo-local `.agents/skills/` convention during MVP; plugin package uses `plugin/creator-toolchain/skills/` |
| `.base/`, `.carl/`, `.paul/` | `.creator/` |
| Claude Code hooks | Codex hooks only after Phase 5 trust review |
| MCP-first architecture | Optional MCP only when external tool access is needed |
| Long command prompt files | short `SKILL.md` + `references/` + `assets/` |
| PAUL code-first execution | Creator production + code execution with Plan → Apply → Qualify → Unify |
| AEGIS codebase-only audit | prompt / slide / workflow / state / code / plugin audit |

---

## 8. Skill Namespace Policy

### 8.1 Repo Skill Location

During local development, repo-scoped skills live at:

```text
.agents/skills/{skill-name}/SKILL.md
```

This is a Creator Toolchain repo convention, not a universal Codex standard. Phase 5 must revalidate plugin skill locations against the active Codex Plugin schema before packaging.

### 8.2 Plugin Skill Location

Plugin-packaged skills live at:

```text
plugin/creator-toolchain/skills/{skill-name}/SKILL.md
```

### 8.3 Namespace Rules

- Skill `name` must be globally unique within the active Codex workspace.
- Do not enable both repo-local and plugin-bundled copies of the same skill unless testing override behavior.
- `creator-skillsmith-factory` must check for name collision before scaffolding a new skill.
- New skills must use `creator-*` prefix unless they are clearly external or experimental.
- Experimental skills use `x-creator-*` and cannot be packaged in v1.0 without audit.

### 8.4 Collision Checklist

Before adding a new skill:

```text
- [ ] Search .agents/skills for same name.
- [ ] Search plugin/creator-toolchain/skills for same name.
- [ ] Search .creator/skills.json registry.
- [ ] Confirm description does not duplicate another skill’s trigger scope.
```

---

## 9. Skill Description Budget Policy

Codex skill selection depends heavily on `name` and `description`.

### 9.1 Description Checklist

Each skill description must:

- start with the primary action verb
- include the primary object
- include trigger terms
- state boundaries
- avoid vague claims
- avoid marketing language
- be short enough for skill list budgets

### 9.2 Bad Description

```yaml
description: Helps with creator work.
```

### 9.3 Good Description

```yaml
description: Turn raw creator, slide deck, AI image, AI video, character system, prompt pack, or workflow ideas into a typed PLANNING.md before implementation. Do not use for executing file changes.
```

### 9.4 Lint Rules

`creator-skillsmith-factory` should flag:

- missing action verb
- missing object
- no boundary
- too broad
- overlaps with another skill
- lacks trigger terms
- claims to do multiple phases at once

---

## 10. Invocation Model

| Mode | Example | Reliability | Use Case |
|---|---|---:|---|
| explicit skill invocation | `$creator-orchestrator` | Highest | new project / mixed task |
| direct specialist skill | `$creator-seed-incubator` | High | known workflow |
| implicit invocation | “Plan a character slide deck project” | Medium | simple clear task |
| `AGENTS.md` baseline | automatic | High | repo-wide behavior |
| plugin default prompt | “Use creator-orchestrator…” | High | plugin entry |
| hooks | optional | Variable | validation / summary only |

Default for complex work:

```text
$creator-orchestrator
Help me choose the right Creator Toolchain workflow for this task.
```

---

## 11. High-Level Architecture

```text
creator-toolchain/
├── AGENTS.md
├── README.md
├── IMPLEMENTATION_PLAN.md
├── SOURCE_TRACEABILITY_AND_AUDIT.md
├── .gitignore
│
├── .agents/
│   └── skills/
│       ├── creator-orchestrator/
│       ├── creator-seed-incubator/
│       ├── creator-paul-loop/
│       ├── creator-base-workspace/
│       ├── creator-rule-router/
│       ├── creator-skillsmith-factory/
│       └── creator-aegis-audit/
│
├── .creator/
│   ├── workspace.json
│   ├── projects.json
│   ├── entities.json
│   ├── state.json
│   ├── psmm.json
│   ├── operator.json
│   ├── decisions.json
│   ├── backlog.json
│   ├── surfaces.json
│   ├── rules.json
│   ├── skills.json
│   ├── audits.json
│   ├── characters.json
│   ├── image_assets.json
│   ├── video_assets.json
│   ├── slide_decks.json
│   ├── prompt_packs.json
│   ├── campaigns.json
│   ├── tools.json
│   ├── plans/
│   ├── reports/
│   ├── templates/
│   └── archive/
│
├── scripts/
│   ├── creator-validate-state.js
│   ├── creator-pulse.js
│   ├── creator-groom.js
│   ├── creator-skill-audit.js
│   ├── creator-migrate-ck-to-creator.js
│   └── creator-package-plugin.js
│
├── docs/
│   ├── architecture/
│   ├── examples/
│   ├── qa/
│   └── source-analysis/
│
└── plugin/
    └── creator-toolchain/
        ├── .codex-plugin/
        │   └── plugin.json
        ├── skills/
        ├── assets/
        ├── hooks/
        ├── README.md
        └── CHANGELOG.md
```

---

## 12. Phase Overview

| Phase | Name | Goal | Primary Deliverables |
|---:|---|---|---|
| 0 | Research Baseline | freeze source understanding | traceability and audit docs |
| 1 | MVP Skill Suite | prove idea → plan → execute loop | `creator-orchestrator`, `creator-seed-incubator`, `creator-paul-loop`, `AGENTS.md`, `README.md` |
| 2 | Add State Layer | add workspace state and memory surfaces | `.creator/`, `creator-base-workspace`, pulse/groom/drift |
| 3 | Add Rules + Skill Factory | add rule routing and skill creation | `creator-rule-router`, `creator-skillsmith-factory` |
| 4 | Add Audit | add evidence-first audit and remediation handoff | `creator-aegis-audit`, Layer A/B/C |
| 5 | Package as Codex Plugin | make suite installable and shareable | plugin manifest, bundled skills, optional hooks/MCP |

---

# Phase 1 — MVP Skill Suite

## 13. Phase 1 Goal

Build the smallest complete loop:

```text
Raw idea
→ creator-orchestrator
→ creator-seed-incubator
→ PLANNING.md
→ creator-paul-loop
→ PLAN.md
→ APPLY / QUALIFY
→ UNIFY / SUMMARY
```

## 14. Phase 1 Scope

### In Scope

- `AGENTS.md`
- `README.md`
- `IMPLEMENTATION_PLAN.md`
- `SOURCE_TRACEABILITY_AND_AUDIT.md`
- `.agents/skills/creator-orchestrator/`
- `.agents/skills/creator-seed-incubator/`
- `.agents/skills/creator-paul-loop/`
- Minimal `.creator/plans/`, `.creator/reports/`, `.creator/templates/`
- Phase 1 test prompts
- Phase 1 acceptance checklist
- canonical Character Image Slide Project example as a test fixture, not a Phase 1 domain blocker

### Out of Scope

- full state automation
- `creator-base-workspace`
- `creator-rule-router`
- `creator-skillsmith-factory`
- `creator-aegis-audit`
- hooks
- MCP
- plugin packaging
- marketplace publishing
- full creator-domain registry surfaces such as `characters.json`, `image_assets.json`, or `slide_decks.json`

---

## 15. `AGENTS.md` Contract

Create:

```text
AGENTS.md
```

### Required Content

```md
# AGENTS.md

## Repository Identity

This repository is `creator-toolchain`, a Codex-native creator workflow system for planning, execution, state, rules, skill creation, and audit.

## Operating Principles

- Use structured planning before non-trivial implementation.
- Use `creator-orchestrator` when workflow selection is unclear.
- Use `creator-seed-incubator` for raw ideas and planning.
- Use `creator-paul-loop` for implementation from an accepted plan.
- Keep durable project state inside `.creator/`.
- Do not silently mutate `.creator/*.json`.
- Do not implement Phase 2–5 while working on Phase 1 unless explicitly requested.
- Every implementation cycle must end with Unify.

## File Conventions

- Plans: `.creator/plans/{project_slug}/PLANNING.md`
- Seed state: `.creator/plans/{project_slug}/SEED-STATE.md`
- Execution plans: `.creator/plans/{project_slug}/PLAN-{sequence}.md`
- Unify summaries: `.creator/plans/{project_slug}/UNIFY-{sequence}.md`
- Summary files: `.creator/plans/{project_slug}/SUMMARY-{sequence}.md`
- Reports: `.creator/reports/`

## Phase 1 Boundaries

Do not implement:

- `creator-base-workspace`
- `creator-rule-router`
- `creator-skillsmith-factory`
- `creator-aegis-audit`
- hooks
- MCP
- plugin packaging
```

### Acceptance Criteria

- [ ] concise
- [ ] no full workflow duplication
- [ ] routes the three MVP skills
- [ ] prevents Phase 1 scope creep

---

## 16. `README.md` Contract

Create:

```text
README.md
```

### Required Sections

```md
# creator-toolchain

Codex-native creator workflow system for planning, execution, state, rules, skill creation, and audit.

## What This Is

`creator-toolchain` is a repo-scoped Codex Skill Suite that adapts high-value workflow patterns from ChristopherKahler’s PAUL, SEED, BASE, CARL, Skillsmith, and AEGIS into a Creator-first system.

## Current Status

Phase 1 MVP Skill Suite.

## Phase 1 Skills

- `creator-orchestrator`
- `creator-seed-incubator`
- `creator-paul-loop`

## Quick Start

1. Open this repo in Codex.
2. Ask: `$creator-orchestrator Help me choose the right Creator Toolchain workflow.`
3. Use `creator-seed-incubator` to create `PLANNING.md`.
4. Use `creator-paul-loop` to execute accepted plans.

## What This Is Not

- Not a Claude Code clone
- Not a plugin yet
- Not an MCP server
- Not a background daemon
- Not a full BASE/CARL/AEGIS port in Phase 1

## Roadmap

- Phase 1: MVP Skill Suite
- Phase 2: State Layer
- Phase 3: Rules + Skill Factory
- Phase 4: Audit
- Phase 5: Codex Plugin
```

### Acceptance Criteria

- [ ] communicates purpose in under 2 minutes
- [ ] explains Phase 1 only
- [ ] does not overclaim Phase 2–5
- [ ] includes safe quick start

---

## 17. Phase 1 File Tree

```text
.agents/
└── skills/
    ├── creator-orchestrator/
    │   ├── SKILL.md
    │   └── references/
    │       └── workflow-routing.md
    ├── creator-seed-incubator/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── project-types.md
    │   │   ├── planning-quality-gate.md
    │   │   ├── graduation-workflow.md
    │   │   ├── launch-workflow.md
    │   │   ├── seed-status-output.md
    │   │   ├── add-type-workflow.md
    │   │   └── type-loadouts.md
    │   └── assets/
    │       ├── planning-template.md
    │       ├── seed-state-template.md
    │       ├── handoff-template.md
    │       ├── open-questions-template.md
    │       └── custom-type-template.md
    └── creator-paul-loop/
        ├── SKILL.md
        ├── references/
        │   ├── plan-apply-qualify-unify.md
        │   ├── acceptance-driven-work.md
        │   ├── escalation-statuses.md
        │   ├── in-session-context-policy.md
        │   └── recovery-workflows.md
        └── assets/
            ├── plan-template.md
            ├── unify-template.md
            ├── summary-template.md
            ├── decision-template.md
            └── ledger-event-template.json

.creator/
├── projects.json
├── plans/
│   └── {project_slug}/
│       ├── project.json
│       ├── activity_ledger.jsonl
│       ├── SEED-STATE.md
│       ├── PLANNING.md
│       ├── HANDOFF.md
│       ├── PLAN-001.md
│       ├── UNIFY-001.md
│       └── SUMMARY-001.md
├── reports/
└── templates/
```

### 17.1 Phase 1 Minimal State Contract

Phase 1 does not implement the full BASE state layer, but it must define enough state to preserve PAUL / SEED closure.

#### `.creator/projects.json`

```json
{
  "schema_version": "0.1.0",
  "projects": [
    {
      "project_id": "project_slug",
      "title": "",
      "type": "",
      "status": "idea|planning|graduated|launched|active|blocked|completed|archived",
      "plan_path": ".creator/plans/project_slug/PLANNING.md",
      "last_summary": "",
      "last_updated": "YYYY-MM-DD"
    }
  ]
}
```

#### `.creator/plans/{project_slug}/project.json`

```json
{
  "schema_version": "0.1.0",
  "project_id": "project_slug",
  "source_skill": "creator-seed-incubator",
  "handoff_target": "creator-paul-loop",
  "active_sequence": 1,
  "manifest_policy": "creator-native; do not copy paul.toml or paul.json"
}
```

#### `.creator/plans/{project_slug}/activity_ledger.jsonl`

Each event is append-only.

```json
{"ts":"YYYY-MM-DDTHH:MM:SSZ","skill":"creator-paul-loop","phase":"qualify","artifact":"PLAN-001.md","status":"DONE","evidence_path":"SUMMARY-001.md"}
```

Phase 1 may propose state updates, but must not silently mutate unrelated `.creator/*.json` files.

### 17.2 Phase 1 Test Prompt Contract

`docs/phase-1-test-prompts.md` must include at minimum:

- one raw idea prompt that routes to `creator-seed-incubator`
- one accepted `PLANNING.md` prompt that routes to `creator-paul-loop`
- one stale-plan prompt that records Phase 2 as unavailable backlog
- one Character Image Slide Project fixture prompt
- one negative prompt proving hooks / MCP / plugin packaging are not triggered in Phase 1

`docs/phase-1-acceptance-checklist.md` must map each test prompt to expected artifacts, expected non-actions, and manual verification evidence.

---

## 18. `creator-orchestrator`

### Skill Metadata

```yaml
---
name: creator-orchestrator
description: Route Creator Toolchain tasks to the correct Codex workflow skill for ideation, planning, implementation, rules, state, skill creation, audit, or plugin packaging. Use when the user is unsure which workflow to use.
---
```

### Purpose

Route user intent to the correct workflow. It should not execute full workflows itself.

### Routing Contract

```text
Route Decision
- Primary workflow
- Secondary workflow, if needed
- Required source files
- Expected output artifact
- Handoff prompt
- Missing inputs
- Do-not-cross boundary
```

### Routing Matrix

| Situation | Route |
|---|---|
| vague idea / undefined scope | `creator-seed-incubator` |
| accepted plan ready for work | `creator-paul-loop` |
| planning exists but stale | Phase 2: `creator-base-workspace` → `creator-seed-incubator` |
| task needs domain rules | Phase 3: `creator-rule-router` preflight |
| user asks to build new skill | Phase 3: `creator-skillsmith-factory` |
| user asks to audit | Phase 4: `creator-aegis-audit` |
| packaging / distribution | Phase 5 plugin workflow |

During Phase 1, routes to Phase 2–5 must be marked as unavailable and recorded as backlog candidates.

---

## 19. `creator-seed-incubator`

### Skill Metadata

```yaml
---
name: creator-seed-incubator
description: Turn raw creator, slide deck, AI image, AI video, character system, CharacterLock, prompt pack, content campaign, software, or workflow ideas into a typed PLANNING.md before implementation. Do not use for executing file changes.
---
```

### Core SEED Features to Port

| Original SEED Concept | Creator Port |
|---|---|
| `/seed` | idea intake / guided planning |
| `/seed graduate` | `creator-seed:graduate` — `PLANNING.md` → project scaffold |
| `/seed launch` | `creator-seed:launch` — handoff to `creator-paul-loop` |
| `/seed status` | `creator-seed:status` — list active ideation plans |
| `/seed add-type` | `creator-seed:add-type` — create custom project type |
| `SEED-STATE.md` | `.creator/plans/{slug}/SEED-STATE.md` |
| type guide/config/loadout | `references/types/{type}/guide.md`, `config.md`, `skill-loadout.md` |

### Project Types

This is the initial project-type catalog. Phase 1 only needs enough type behavior to validate routing, planning, status, add-type, graduate, and launch. Rich creator-domain registries remain Phase 2+.

| Type | Rigor | Purpose |
|---|---|---|
| `slide-deck` | standard | presentation / pitch / teaching deck |
| `ai-image-system` | deep | image generation workflows |
| `characterlock-system` | deep | identity/viewpoint locked character workflows |
| `headlock-system` | standard | head/face consistency workflows |
| `ai-video-system` | deep | shot / scene / motion workflows |
| `prompt-pack` | tight | reusable prompts and prompt QA |
| `character-registry` | deep | profile ID / variants / universe |
| `content-campaign` | creative | launch / platform publishing |
| `creator-tooling` | standard | scripts / validators / workflow tools |
| `application` | deep | software / app / UI / API |
| `workflow` | standard | repeatable SOP / skill / automation |
| `utility` | tight | script / checker / converter |
| `research-system` | standard | repo/tool analysis |

### Type Loadout Contract

Each project type must define:

```text
references/types/{type}/
├── guide.md
├── config.md
└── skill-loadout.md
```

#### `guide.md`

- purpose
- when to use
- discovery questions
- anti-patterns
- example outputs

#### `config.md`

- required sections
- optional sections
- rigor level
- minimum acceptance criteria
- recommended handoff target

#### `skill-loadout.md`

- primary skill
- secondary skills
- rule domains
- audit domains
- state surfaces

### Planning Quality Gate

Before `creator-seed:graduate`, every plan must pass:

```text
- [ ] project type selected or custom type defined
- [ ] guide.md discovery questions answered or explicitly deferred
- [ ] config.md required sections present
- [ ] minimum acceptance criteria written in observable form
- [ ] open questions categorized as blocking or non-blocking
- [ ] handoff target selected
- [ ] scope boundary states what will not be implemented yet
```

If the quality gate fails, `creator-seed-incubator` must continue planning or produce `OPEN-QUESTIONS.md`; it must not hand off to implementation.

### Output Artifacts

```text
.creator/plans/{project_slug}/
├── project.json
├── activity_ledger.jsonl
├── SEED-STATE.md
├── PLANNING.md
├── DECISIONS.md
├── OPEN-QUESTIONS.md
└── HANDOFF.md
```

### `creator-seed:status` Output

```md
# Creator Seed Pipeline Status

| Project | Type | Stage | Last Updated | Open Questions | Next Action |
|---|---|---|---|---:|---|
| {slug} | {type} | ideating / planned / graduated / launched / archived | {date} | {n} | {action} |
```

### `creator-seed:add-type` Schema

```json
{
  "type_id": "custom-type",
  "display_name": "Custom Type",
  "rigor": "tight|standard|deep|creative",
  "purpose": "",
  "required_sections": [],
  "optional_sections": [],
  "default_handoff": "creator-paul-loop",
  "rule_domains": [],
  "audit_domains": [],
  "templates": []
}
```

### Graduation Output

`creator-seed:graduate` creates or proposes a standalone project scaffold from an accepted plan. It does not execute the plan.

```text
.creator/plans/{project_slug}/PROJECT.md
.creator/plans/{project_slug}/README.md
.creator/plans/{project_slug}/HANDOFF.md
```

Graduation requires the Planning Quality Gate above to pass.

### Launch Handoff Package

`creator-seed:launch` means graduate plus immediate handoff to `creator-paul-loop`. It must not re-ask questions already answered in `PLANNING.md`, unless a required field is missing or contradictory.

`HANDOFF.md` must include:

- source plan
- accepted MVP
- first execution phase
- acceptance criteria
- risks
- open questions
- target skill: `creator-paul-loop`
- quality gate result
- handoff decision: `graduate-only|launch-to-paul`

### Planning Session Resume

`SEED-STATE.md` must include:

- current planning stage
- answered sections
- unanswered sections
- current question
- open questions
- next prompt
- last updated timestamp

---

## 20. `creator-paul-loop`

### Skill Metadata

```yaml
---
name: creator-paul-loop
description: Execute an existing plan through Plan → Apply → Qualify → Unify with BDD acceptance criteria, file changes, verification, recovery workflows, state reconciliation, and final summary. Do not use for raw ideation.
---
```

### Core PAUL Features to Port

| Original PAUL Concept | Creator Port |
|---|---|
| Plan → Apply → Unify | Plan → Apply → Qualify → Unify |
| mandatory UNIFY | every execution cycle must end with `UNIFY-{seq}.md` |
| BDD acceptance criteria | `Given / When / Then` criteria |
| Execute/Qualify loop | task-level verification after each execution step |
| escalation statuses | DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED |
| in-session context | main implementation stays in main agent |
| `STATE.md` | `.creator/state.json` + project state |
| `SUMMARY.md` | `SUMMARY-{seq}.md` |
| action ledger | append-only `activity_ledger.jsonl` |
| qualification evidence | task-level evidence path plus verification result |
| progress / one next action | Unify ends with one recommended next action |

### Submodes

```text
creator-paul:plan
creator-paul:apply
creator-paul:qualify
creator-paul:unify
creator-paul:progress
creator-paul:status
creator-paul:recover
```

### Plan Types

| Plan Type | Use |
|---|---|
| `quick-fix` | small bounded change |
| `standard` | normal project phase |
| `complex` | multi-file or multi-phase work |
| `audit-remediation` | implementation from AEGIS handoff |
| `migration` | path/name/schema migration |
| `plugin-packaging` | Phase 5 packaging task |

### Loop

```text
PLAN
→ APPLY
  → EXECUTE TASK
  → QUALIFY TASK
  → status: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
→ UNIFY
→ SUMMARY
→ LEDGER APPEND
→ STATE UPDATE PROPOSAL
```

### BDD Acceptance Criteria

```md
### AC-1: {Criterion Name}

- Given {precondition}
- When {action}
- Then {observable result}
```

### Task Verification Schema

```json
{
  "task_id": "TASK-001",
  "acceptance_criteria": [],
  "verification_method": "",
  "evidence_path": "",
  "qualification_result": "pass|pass_with_concerns|fail|blocked",
  "ledger_event_id": "EVT-001",
  "status": "DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED"
}
```

### Activity Ledger Event Schema

`activity_ledger.jsonl` records every plan/apply/qualify/unify event. It is append-only and must not be rewritten during normal execution.

```json
{
  "event_id": "EVT-001",
  "ts": "YYYY-MM-DDTHH:MM:SSZ",
  "sequence": 1,
  "phase": "plan|apply|qualify|unify|recover",
  "task_id": "TASK-001",
  "artifact": "PLAN-001.md",
  "status": "DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED",
  "evidence_path": "SUMMARY-001.md",
  "notes": ""
}
```

### Output Artifacts

```text
.creator/plans/{project_slug}/
├── INDEX.md
├── PLAN-{seq}.md
├── UNIFY-{seq}.md
├── SUMMARY-{seq}.md
├── DECISIONS-{seq}.md
└── activity_ledger.jsonl
```

### Recovery Workflows

| Recovery | Trigger | Action |
|---|---|---|
| Orphan Plan Recovery | PLAN exists but no UNIFY | generate `UNIFY-RECOVERY.md` |
| Failed Qualify Recovery | task status = failed | return to Apply or create remediation plan |
| Blocked Task Recovery | status = BLOCKED | write `BLOCKER.md` and request missing context |
| State Drift Recovery | plan / state disagree | run Phase 2 `creator-base-workspace` pulse |
| Scope Creep Recovery | unplanned work detected | pause and ask for explicit scope expansion |

### Rollback Criteria

Any high-risk plan must define:

- affected files
- blast radius
- rollback steps
- verification before rollback
- state restoration note

---

## 21. Phase 1 Acceptance Criteria

- [ ] `AGENTS.md` exists.
- [ ] `README.md` exists.
- [ ] `creator-orchestrator` exists.
- [ ] `creator-seed-incubator` exists.
- [ ] `creator-paul-loop` exists.
- [ ] Raw idea can produce `PLANNING.md`.
- [ ] `SEED-STATE.md` exists for active plans.
- [ ] `creator-seed:status` output is defined.
- [ ] `creator-seed:add-type` schema is defined.
- [ ] Planning Quality Gate is defined and blocks weak plans from graduating.
- [ ] `creator-seed:graduate` and `creator-seed:launch` are documented as separate operations.
- [ ] Execution creates `PLAN-{seq}.md`.
- [ ] Each task has BDD acceptance criteria.
- [ ] Apply includes Qualify.
- [ ] `activity_ledger.jsonl` exists and records append-only PAUL events.
- [ ] qualification evidence exists for each completed task.
- [ ] recovery workflows are documented.
- [ ] Execution ends with `UNIFY-{seq}.md` and `SUMMARY-{seq}.md`.
- [ ] Phase 1 test prompts and acceptance checklist map prompts to artifacts and non-actions.
- [ ] No hooks / MCP / plugin introduced.

---

# Phase 2 — Add State Layer

## 22. Phase 2 Goal

Add a structured Creator Toolchain state layer inspired by BASE, but Codex-native and repo-local.

## 23. Phase 2 Scope

### In Scope

- `creator-base-workspace`
- `.creator/workspace.json`
- `.creator/projects.json`
- `.creator/entities.json`
- `.creator/state.json`
- `.creator/psmm.json`
- `.creator/operator.json`
- `.creator/backlog.json`
- `.creator/surfaces.json`
- `.creator/decisions.json`
- optional validation scripts
- pulse and groom workflows
- surface CRUD workflows

### Out of Scope

- hooks
- MCP server
- automatic background sync
- external database
- silent archive / delete
- plugin packaging

## 24. `creator-base-workspace`

### Skill Metadata

```yaml
---
name: creator-base-workspace
description: Manage Creator Toolchain repo-local workspace state, projects, entities, operator profile, PSMM, backlog, custom surfaces, pulse checks, groom cycles, drift score, and surface validation.
---
```

### Data Surface Contract

| Surface | Owner Skill | Mutability | Privacy Class | Required |
|---|---|---|---|---:|
| `workspace.json` | `creator-base-workspace` | controlled | publishable template | yes |
| `projects.json` | `creator-base-workspace` | controlled | local/private | yes |
| `entities.json` | `creator-base-workspace` | controlled | private | yes |
| `state.json` | `creator-base-workspace` | controlled | local/private | yes |
| `psmm.json` | `creator-base-workspace` | append-only preferred | private | yes |
| `operator.json` | user + `creator-base-workspace` | user-controlled | private | yes |
| `backlog.json` | `creator-base-workspace` | controlled | local/private | yes |
| `surfaces.json` | `creator-base-workspace` | controlled | publishable template | yes |
| `decisions.json` | `creator-base-workspace` | append-only preferred | local/private | yes |
| `characters.json` | domain workflows | controlled | local/private | optional |
| `image_assets.json` | domain workflows | controlled | local/private | optional |
| `video_assets.json` | domain workflows | controlled | local/private | optional |
| `slide_decks.json` | domain workflows | controlled | local/private | optional |
| `prompt_packs.json` | domain workflows | controlled | local/private | optional |
| `campaigns.json` | domain workflows | controlled | local/private | optional |
| `tools.json` | research workflows | controlled | local/private | optional |

### Surface CRUD Workflows

```text
creator-base:surface list
creator-base:surface create
creator-base:surface validate
creator-base:surface archive
creator-base:surface convert
```

#### Surface Create Output

```json
{
  "surface_id": "slide_decks",
  "path": ".creator/slide_decks.json",
  "owner_skill": "creator-base-workspace",
  "privacy_class": "local/private",
  "schema_version": "0.2.0",
  "records": []
}
```

### Pulse Output Format

```md
# Creator Pulse

**Date:** {date}  
**Workspace:** creator-toolchain

## Summary

- Active projects: {n}
- Blocked projects: {n}
- Stale plans: {n}
- Drift score: {score} / {level}

## Open Items

| ID | Project | Item | Status | Next Action |
|---|---|---|---|---|

## Recommended Next Action

{one next action}
```

### Groom Output Format

```md
# Creator Groom

## Review Windows

| Backlog Item | Priority | Age | Window | Recommendation |
|---|---|---:|---:|---|

## Archive Candidates

| Item | Reason | Requires Confirmation |
|---|---|---|

## State Fixes

- [ ] {fix}

## Next Action

{one next action}
```

### PSMM Lifecycle

```text
session_entry
→ insight
→ correction
→ decision
→ rule_proposal
→ state_update_candidate
```

### PSMM to Rule Proposal Bridge

PSMM may produce `rule_proposal` entries, but it must not automatically promote them into active CARL-style rules.

```text
PSMM insight
→ staged rule proposal
→ creator-base:groom review
→ creator-rule-router conflict audit
→ explicit user approval
→ active rule
```

Rule proposals must record source session, rationale, affected domains, expiry/review date, and expected behavior change.

### State Validation Boundary

Creator Toolchain state validators must treat `.creator/*.json` as the active state contract. `.base/data/*.json` may appear in upstream research notes, but must not be required by Creator Toolchain runtime checks.

### Project State Machine

```text
idea → planning → active → blocked → paused → completed → archived
```

### Cross-Surface Consistency Checks

- every `projects.json` project with `status != archived` must have a plan folder
- every `slide_decks.json` record must reference a valid project id
- every `image_assets.json` record must reference a project or character id
- every audit report must reference a valid audit id
- every decision id must be unique

---

## 25. Phase 2 Acceptance Criteria

- [ ] all core state surfaces exist and parse.
- [ ] state surface contract exists.
- [ ] surface CRUD workflows are documented.
- [ ] pulse output works manually.
- [ ] groom output works manually.
- [ ] PSMM lifecycle is defined.
- [ ] PSMM rule proposals require groom/review and are not auto-promoted.
- [ ] validators do not depend on `.base/data/*.json`.
- [ ] project state machine is defined.
- [ ] cross-surface consistency checks exist.
- [ ] no silent archive / delete.
- [ ] no hooks / MCP / plugin introduced.

---

# Phase 3 — Add Rules + Skill Factory

## 26. Phase 3 Goal

Add:

1. CARL-inspired domain rule routing.
2. Skillsmith-inspired skill creation / distillation / audit.

## 27. `creator-rule-router`

### Skill Metadata

```yaml
---
name: creator-rule-router
description: Select, stage, update, audit, and apply Creator Toolchain domain rules for Codex workflows, including CharacterLock, slide decks, AI image, AI video, prompt packs, zh-Hant writing, coding, safety, and project execution.
---
```

### Domain Operations

```text
creator-rules:list-domains
creator-rules:get-domain
creator-rules:create-domain
creator-rules:toggle-domain
creator-rules:add-rule
creator-rules:remove-rule
creator-rules:replace-rule
creator-rules:stage-proposal
creator-rules:approve-proposal
creator-rules:reject-proposal
creator-rules:recall
creator-rules:exclude
creator-rules:list-commands
creator-rules:add-command
creator-rules:search-decisions
creator-rules:audit-conflicts
```

### Rule Domain Schema

```json
{
  "schema_version": "0.1.0",
  "domains": [
    {
      "domain_id": "GLOBAL",
      "enabled": true,
      "priority": 100,
      "trigger_keywords": [],
      "rules": [],
      "commands": [],
      "exclude_patterns": [],
      "decision_refs": []
    }
  ],
  "staged_proposals": [],
  "decision_log": []
}
```

`GLOBAL` is always eligible for preflight, but its rules must stay short and durable. Domain-specific rules override `GLOBAL` only when they are more specific and conflict-free.

### Recall and Exclude Policy

- `creator-rules:recall` retrieves relevant rules by keyword, domain, command, or decision reference.
- `creator-rules:exclude` records why a matching rule was intentionally not loaded.
- Excluded rules must appear in Rule Preflight under Non-Loaded Candidate Rules.
- A rule excluded due to conflict must create or reference a decision log entry.

### Command Registry

CARL-style command memory is represented as explicit commands inside `.creator/rules.json`, not as hidden slash commands.

```json
{
  "command_id": "review-characterlock-output",
  "domain_id": "characterlock-system",
  "trigger": "character lock review",
  "workflow": "creator-rule-router -> creator-aegis-audit",
  "status": "active|deprecated|staged"
}
```

### Rule Preflight Output

```md
# Rule Preflight

## Matched Domains

| Domain | Reason | Rules Loaded |
|---|---|---:|

## Selected Rules

| Rule ID | Severity | Rule | Reason |
|---|---|---|---|

## Non-Loaded Candidate Rules

| Rule ID | Reason Not Loaded |
|---|---|

## Conflict Warnings

- {warning}

## Next Action

{target workflow}
```

### Rule Conflict Types

| Conflict Type | Meaning |
|---|---|
| duplicate | same rule repeated |
| contradiction | two rules give incompatible instructions |
| scope overlap | two domains claim same task without precedence |
| stale rule | rule references outdated workflow/path |
| overbroad rule | rule triggers too often |
| unsafe rule | rule permits destructive or private-data action |
| duplicate command | multiple commands claim the same trigger without precedence |
| stale decision | rule references a missing or superseded decision |

### Context Budget Policy

- load only rules relevant to matched domains
- prefer high-severity rules first
- avoid loading long examples unless requested
- summarize inactive rules instead of loading them
- never load all rules by default

### `AGENTS.md` Integration

`AGENTS.md` should say:

```text
For major creator work, run creator-rule-router preflight before implementation.
Do not paste full rules into AGENTS.md.
```

---

## 28. `creator-skillsmith-factory`

### Skill Metadata

```yaml
---
name: creator-skillsmith-factory
description: Discover, scaffold, distill, score, and audit Codex Skills for Creator Toolchain workflows, including prompt skills, image/video pipeline skills, character system skills, and project execution skills.
---
```

### Codex Skill Anatomy

| File Type | Codex Path | Purpose |
|---|---|---|
| Entry Point | `SKILL.md` | metadata + concise routing + workflow entry |
| Task | `references/workflows/*.md` | detailed guided workflow |
| Framework | `references/frameworks/*.md` | domain knowledge |
| Template | `assets/templates/*.md` | output shape |
| Context | `.creator/context/*.json/md` | mutable project/user state |
| Checklist | `references/checklists/*.md` | QA gates |
| Rules | `.creator/rules.json` | rule routing / validation |
| Optional agent profile | `agents/*.md` or `agents/openai.yaml` | optional subagent/UI/dependency config |

### `SKILL-SPEC.md` Required Fields

```yaml
skill_name:
description:
tier: suite|standalone|task-only
primary_trigger:
secondary_triggers:
not_for:
inputs:
outputs:
folders:
references:
assets:
scripts:
state_surfaces:
rule_domains:
acceptance_tests:
owner:
phase_added:
```

### Distill Chunk Schema

```md
# {Chunk Name}

## Core Concept

{concept}

## When to Use

{conditions}

## Steps

1. {step}

## Templates

{template}

## Decision Rules

- {rule}

## QA Checklist

- [ ] {criterion}

## Source Notes

{source reference}
```

### Compliance Score

| Score | Status | Meaning |
|---:|---|---|
| 90–100 | compliant | ready |
| 70–89 | partial | usable but needs fixes |
| 40–69 | weak | do not package |
| 0–39 | non-compliant | rewrite required |

### Audit Checks

- `SKILL.md` has `name` and `description`
- description has trigger terms and boundary
- no mega-skill behavior
- references are not empty
- assets are reusable templates
- scripts are optional and documented
- state mutation is explicit
- acceptance tests exist
- no duplicate skill name

### Anti-Patterns

- one skill does all phases
- vague description
- hidden state mutation
- duplicated rule logic
- unbounded workflow
- missing “not for”
- no acceptance tests
- external dependencies not documented

---

## 29. Phase 3 Acceptance Criteria

- [ ] `creator-rule-router` exists.
- [ ] domain operations are documented.
- [ ] `GLOBAL` domain behavior is defined.
- [ ] recall and exclude workflows are documented.
- [ ] command registry schema exists.
- [ ] decision log and proposal staging are defined.
- [ ] rule preflight output exists.
- [ ] conflict detection is defined.
- [ ] duplicate command and stale decision conflicts are detected.
- [ ] context budget policy exists.
- [ ] `creator-skillsmith-factory` exists.
- [ ] `SKILL-SPEC.md` fields are defined.
- [ ] compliance score exists.
- [ ] distill chunk schema exists.
- [ ] no hook-based auto-injection yet.

---

# Phase 4 — Add Audit

## 30. Phase 4 Goal

Add AEGIS-inspired audit and remediation planning.

## 31. `creator-aegis-audit`

### Skill Metadata

```yaml
---
name: creator-aegis-audit
description: Audit Creator Toolchain projects, Codex skills, prompts, slide decks, AI image/video workflows, character systems, state files, scripts, and plugin packages, then produce evidence-based findings and creator-paul-loop remediation plans.
---
```

### Audit Modes

| Mode | Use |
|---|---|
| `single-agent audit` | quick or medium audit |
| `staged audit` | sequential domain-by-domain audit |
| `parallel subagent audit` | explicit user-requested multi-persona audit |

### Subagent Invocation Policy

- Subagents are never assumed automatic.
- User must explicitly request parallel audit.
- Each subagent must have a bounded domain.
- Each subagent must return evidence, confidence, and limitations.
- Main agent synthesizes; subagents do not directly mutate files.

### AEGIS Phase Pipeline

```text
Phase 0 — Context and Threat Model
Phase 1 — Automated Signal Gathering
Phase 2 — Deep Domain Audits
Phase 3 — Reality Gap Analysis
Phase 4 — Adversarial Review
Phase 5 — Synthesis
Phase 6 — Transform to Remediation Knowledge
Phase 7 — Change Risk Validation and Guardrails
Phase 8 — Execution Planning and PAUL Handoff
```

### AEGIS Layer Model

```text
Layer A — Diagnosis
  immutable findings, evidence, confidence, disagreements

Layer B — Remediation Knowledge
  playbooks, before/after examples, guardrails

Layer C — Execution Orchestration
  dependency graph, risk score, verification gates, rollback criteria, creator-paul-loop handoff
```

### Layer Immutability Policy

- Layer A is immutable once issued.
- Corrections to Layer A are addenda, not overwrites.
- Layer B must regenerate if referenced Layer A findings change.
- Layer C must regenerate if Layer B remediation strategy changes.

### Audit Artifacts

```text
.creator/reports/audits/{audit_id}/
├── LAYER-A-DIAGNOSIS.md
├── LAYER-B-REMEDIATION.md
├── LAYER-C-EXECUTION-PLAN.md
├── FINDINGS.json
├── DISAGREEMENTS.md
├── CONFIDENCE.md
├── DEVIL-ADVOCATE.md
├── REALITY-GAP.md
└── handoff/
    ├── PROJECT.md
    ├── ROADMAP.md
    ├── PHASE-01-PLAN.md
    ├── PHASE-02-PLAN.md
    ├── VERIFICATION-GATES.md
    ├── ROLLBACK-CRITERIA.md
    └── RISK-METADATA.json
```

### Remediation Task Schema

```json
{
  "task_id": "REM-001",
  "source_finding": "FIND-001",
  "remediation_type": "planning|workflow|state|rule|skill|code|plugin",
  "intervention_level": "suggesting|planning|authorizing|executing",
  "blast_radius": "low|medium|high",
  "coupling_risk": "low|medium|high",
  "regression_risk": "low|medium|high",
  "confidence": 0.82,
  "evidence_sources": [],
  "verification_gate": "",
  "rollback_criteria": "",
  "handoff": "creator-paul-loop"
}
```

`remediation_type` describes what surface changes. `intervention_level` describes how much agency the audit layer is allowed to take. Default is `suggesting` or `planning`; `authorizing` and `executing` require explicit user approval and should normally hand off to `creator-paul-loop`.

### Reality Gap Variants

| Target | Reality Gap Question |
|---|---|
| code | code as written vs system as run |
| plan | plan as written vs work actually done |
| prompt | prompt as written vs output generated |
| slide deck | outline as written vs deck produced |
| image assets | asset matrix as planned vs images approved |
| state | state files vs real project status |

### Devil’s Advocate Rule

If `DEVIL-ADVOCATE.md` is empty or purely agreeable, the audit is incomplete.

---

## 32. Phase 4 Acceptance Criteria

- [ ] `creator-aegis-audit` exists.
- [ ] audit modes are documented.
- [ ] subagent explicit invocation policy exists.
- [ ] Phase 0–8 pipeline exists with Phase 7 risk validation and Phase 8 PAUL handoff.
- [ ] Layer A/B/C model exists.
- [ ] Layer A immutability is defined.
- [ ] `remediation_type` and `intervention_level` are separate fields.
- [ ] findings require evidence.
- [ ] confidence and disagreement fields exist.
- [ ] Reality Gap and Devil’s Advocate outputs exist.
- [ ] PAUL handoff artifacts exist.
- [ ] audit never modifies target files directly.

---

# Phase 5 — Package as Codex Plugin

## 33. Phase 5 Goal

Package the stable Creator Toolchain skill suite as an installable Codex Plugin.

## 34. Phase 5 Scope

### In Scope

- plugin directory
- `.codex-plugin/plugin.json`
- bundled skills
- plugin README
- plugin assets
- optional hooks after trust review
- optional MCP after need review
- local marketplace testing
- packaging script
- privacy/sanitization checklist

### Out of Scope

- public marketplace publishing before private testing
- bundling user-private `.creator/` state
- mandatory hooks
- mandatory MCP
- external commercial distribution without docs/license review

## 35. Plugin File Tree

```text
plugin/
└── creator-toolchain/
    ├── .codex-plugin/
    │   └── plugin.json
    ├── skills/
    │   ├── creator-orchestrator/
    │   ├── creator-seed-incubator/
    │   ├── creator-paul-loop/
    │   ├── creator-base-workspace/
    │   ├── creator-rule-router/
    │   ├── creator-skillsmith-factory/
    │   └── creator-aegis-audit/
    ├── assets/
    │   ├── logo.png
    │   ├── composer-icon.png
    │   └── screenshots/
    ├── hooks/
    │   └── hooks.json
    ├── README.md
    └── CHANGELOG.md
```

## 36. Plugin Manifest Draft

Create:

```text
plugin/creator-toolchain/.codex-plugin/plugin.json
```

Manifest draft:

```json
{
  "name": "creator-toolchain",
  "version": "1.0.0",
  "description": "Codex-native creator workflow system for ideation, execution, state, rules, skill creation, and audit.",
  "author": {
    "name": "Criz leung"
  },
  "license": "TBD",
  "keywords": ["creator", "workflow", "codex", "skills", "audit"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Creator Toolchain",
    "shortDescription": "Codex-native creator workflow system for ideation, execution, state, rules, skill creation, and audit.",
    "longDescription": "Creator Toolchain packages Codex skills for turning ideas into plans, executing work through Plan → Apply → Qualify → Unify, managing repo-local state, routing domain rules, creating new skills, and auditing workflows.",
    "developerName": "Criz leung",
    "category": "Productivity",
    "capabilities": ["Skills", "Workflow", "Planning", "Audit"],
    "defaultPrompt": [
      "Use creator-orchestrator to help me choose the right Creator Toolchain workflow."
    ]
  }
}
```

**Important:** This draft is not an official schema claim. It must be validated against the current Codex Plugin schema at packaging time, and the validation evidence must be saved under `plugin/creator-toolchain/release-evidence/`.

### Manifest Validation Evidence

Phase 5 must produce:

```text
plugin/creator-toolchain/release-evidence/
├── manifest-schema-validation.md
├── skill-discovery-test.md
├── local-install-test.md
├── package-contents-audit.md
└── privacy-sanitization-audit.md
```

## 37. Plugin UX Modes

| Mode | Description |
|---|---|
| Explicit skill invocation | `$creator-orchestrator` |
| Implicit selection | Codex selects skill based on description |
| Plugin default prompt | `interface.defaultPrompt` |
| Optional hooks | validation / summary only |
| Optional MCP/apps | only after concrete need |

## 38. Hook Policy

Hooks are optional and disabled by default unless reviewed.

| Hook | Allowed Use | Default |
|---|---|---|
| SessionStart | load workspace summary, not full state | optional |
| UserPromptSubmit | rule preflight hint | optional |
| PreToolUse | warn before destructive commands | optional |
| Stop | suggest Unify if plan active | optional |
| SubagentStart | log audit persona start | optional |
| SubagentStop | collect audit persona summary | optional |

Not allowed:

- silent state mutation
- silent archive/delete
- silent plugin publishing
- large automatic rule injection
- external network calls without explicit setup

### Hook Trust Rule

Plugin-bundled hooks must be treated as untrusted until reviewed by the user. They must be deterministic, documented, and optional.

## 39. Local Marketplace Test Plan

Before release:

```text
1. Package plugin folder.
2. Add to local marketplace.
3. Install locally.
4. Confirm skills appear.
5. Run plugin default prompt.
6. Run each skill trigger prompt.
7. Confirm hooks are absent or require trust.
8. Confirm no user .creator state bundled.
9. Run naming audit.
10. Run Phase 4 packaging audit.
```

## 40. MCP / App Integration Policy

MCP and app integrations are allowed only after a concrete need appears.

Candidate future use cases:

| Need | Possible Integration |
|---|---|
| Google Slides project generation | Google Drive / Slides app or MCP |
| GitHub repo state | GitHub app / MCP |
| Figma / design assets | future integration |
| Anytype / Notion knowledge base | future integration |

## 41. Privacy Policy

- Plugin package must not bundle user `.creator/` state.
- Bundle templates only, not private project data.
- Do not bundle `upstream/` research clones, source-analysis working copies, `.DS_Store`, local cache files, or editor metadata.
- `.creator/entities.json` may contain clients/contacts; do not publish.
- `.creator/operator.json` may contain personal working preferences; keep local unless sanitized.
- Support `.creator/*.local.json` for private overrides.
- Add `.gitignore` guidance for private state when needed.

## 42. Phase 5 Packaging Gates

Phase 5 cannot start until:

- [ ] Phase 4 audit passes.
- [ ] manifest draft validates against current official schema.
- [ ] no active `ck-*` names remain.
- [ ] all skills have trigger tests.
- [ ] no stale file paths remain.
- [ ] user-private `.creator/` state is not bundled.
- [ ] `upstream/` research clones are not bundled.
- [ ] `.DS_Store` and local OS artifacts are not bundled.
- [ ] package contents audit is saved.
- [ ] hooks are absent or reviewed.
- [ ] MCP config is absent or documented.
- [ ] local install test passes.
- [ ] plugin README is complete.

---

# 43. Creator Domain Test Fixture

## 43.1 Character Image Slide Project

This example is a Phase 1 test fixture. It proves that the toolchain can route a creator-domain idea through SEED and PAUL, but it does not require Phase 1 to implement full character, image asset, or slide deck registries.

This project is the canonical end-to-end test case.

```text
docs/examples/character-image-slide-project.md
```

### Flow

```text
$creator-orchestrator
→ route to creator-seed-incubator

$creator-seed-incubator
→ create .creator/plans/character-image-slide-project/PLANNING.md
→ create SEED-STATE.md
→ create HANDOFF.md

$creator-rule-router
→ select CHARACTERLOCK + SLIDE_DECK + AI_IMAGE rules

$creator-paul-loop
→ create PLAN-001.md
→ create prompt template
→ create slide outline
→ create asset checklist
→ qualify acceptance criteria
→ create UNIFY-001.md / SUMMARY-001.md

$creator-base-workspace
→ update projects / slide_decks / image_assets

$creator-aegis-audit
→ audit completeness / consistency / prompt quality / slide flow
→ generate remediation handoff
```

## 43.2 Extended Asset Matrix Schema

```json
{
  "asset_id": "ASSET-000001",
  "project_id": "PRJ-000001",
  "slide_id": "SLIDE-001",
  "asset_role": "character_reference",
  "character_id": "PROFILE-000001",
  "character_name": "DiaoChan__貂蟬",
  "required_views": ["front", "left_profile", "rear", "left_3q", "right_3q"],
  "view_angle": "front",
  "prompt_path": "",
  "image_path": "",
  "prompt_status": "draft|approved|needs_rework",
  "generation_status": "planned|generated|approved|rework",
  "review_status": "not_reviewed|passed|failed",
  "acceptance_criteria": []
}
```

---

# 44. Superpowers Coexistence Strategy

| Tool | Role |
|---|---|
| Superpowers | coding discipline / TDD / worktrees / code review |
| creator-toolchain | creator workflow / prompt / slide / character / image / video / state / audit |

Use Superpowers when implementation is mainly coding-heavy. Use `creator-toolchain` when the work is mainly creator workflow, prompt systems, planning, state, audit, or creative production governance.

---

# 45. P2 Roadmap

P2 items are not current implementation scope.

| Roadmap Item | Future Phase |
|---|---|
| Google Slides / Drive integration profile | post-v1 |
| Anytype / Notion / Drive state sync | post-v1 |
| Creator dashboard | post-v1 |
| independent `creator-surface-manager` skill | post-v1 if surfaces become complex |
| public marketplace publishing checklist | after local plugin validation |
| MCP server for `.creator/` state | optional post-v1 |
| automated dashboard | optional post-v1 |

---

# 46. Trust Boundary

| Boundary | Policy |
|---|---|
| local repo files | allowed with user-visible plan / diff |
| `.creator/` state | never silently overwrite |
| hooks | disabled by default until reviewed |
| MCP | explicit install only |
| external services | no connection unless configured |
| destructive commands | require explicit confirmation |
| plugin packaging | audit before package |
| public publishing | separate explicit approval |

---

# 47. Migration Policy

Because early drafts used `creator-agentic-os-codex`, `ck-*`, and `.ck/`, provide:

```text
scripts/creator-migrate-ck-to-creator.js
```

Required behavior:

- detect `.ck/`
- map `.ck/*` to `.creator/*`
- replace `ck-*` names in repo files
- replace `creator-agentic-os-codex` with `creator-toolchain`
- produce migration report
- never delete original without confirmation
- preserve backups

---

# 48. Versioning Policy

| Version | Meaning |
|---|---|
| `0.1.x` | Phase 1 MVP fixes |
| `0.2.x` | State layer |
| `0.3.x` | Rules + skill factory |
| `0.4.x` | Audit |
| `1.0.0` | Plugin-ready stable release |

Release tags:

```text
v0.1.0-mvp
v0.2.0-state
v0.3.0-rules-factory
v0.4.0-audit
v1.0.0-plugin
```

---

# 49. Master Acceptance Checklist

## Phase 1

- [ ] `AGENTS.md`
- [ ] `README.md`
- [ ] three MVP skills
- [ ] `creator-seed-incubator` supports graduate / launch / status / add-type concepts
- [ ] SEED Planning Quality Gate blocks weak plans from graduation
- [ ] `creator-paul-loop` supports Plan → Apply → Qualify → Unify
- [ ] BDD acceptance criteria
- [ ] `project.json` and `activity_ledger.jsonl` are defined for active plans
- [ ] qualification evidence exists for each completed task
- [ ] recovery workflows
- [ ] Unify and Summary mandatory
- [ ] canonical Character Image Slide Project is treated as fixture, not MVP domain scope
- [ ] no hooks / MCP / plugin

## Phase 2

- [ ] state surface contract
- [ ] surface CRUD
- [ ] pulse / groom output
- [ ] PSMM lifecycle
- [ ] PSMM rule proposals require review before promotion
- [ ] `.creator/*.json` is the active state contract; `.base/data` is not required
- [ ] project state machine
- [ ] cross-surface checks

## Phase 3

- [ ] domain operations
- [ ] `GLOBAL` domain
- [ ] recall / exclude workflows
- [ ] command registry
- [ ] decision log and proposal staging
- [ ] rule preflight
- [ ] conflict detection
- [ ] skill compliance score
- [ ] SKILL-SPEC schema
- [ ] distill chunk schema

## Phase 4

- [ ] audit modes
- [ ] subagent explicit policy
- [ ] AEGIS Phase 0–8
- [ ] Layer A/B/C
- [ ] remediation type is separate from intervention level
- [ ] handoff artifacts
- [ ] rollback / risk metadata

## Phase 5

- [ ] manifest draft validates against current official schema
- [ ] local marketplace test
- [ ] no private state bundled
- [ ] no `upstream/`, `.DS_Store`, cache, or research artifacts bundled
- [ ] package contents audit saved
- [ ] hooks reviewed or absent
- [ ] MCP documented or absent
- [ ] packaging audit passed

---

# 50. Suggested Commit Plan

## Phase 1

```text
chore: initialize creator-toolchain
docs: add AGENTS.md and README.md
docs: add implementation plan v0.4.1 and source traceability amendment
feat: add creator-orchestrator skill
feat: add creator-seed-incubator skill
feat: add creator-paul-loop skill
docs: add phase 1 tests and canonical fixture
```

## Phase 2

```text
feat: add .creator state surfaces
feat: add creator-base-workspace skill
feat: add pulse groom and drift workflows
feat: add operator entities psmm backlog and surfaces
chore: add state validation scripts
```

## Phase 3

```text
feat: add creator-rule-router skill
feat: add CARL-style domain operations
feat: add creator-skillsmith-factory skill
feat: add skill compliance scoring and distill workflow
```

## Phase 4

```text
feat: add creator-aegis-audit skill
feat: add AEGIS layer abc audit artifacts
feat: add PAUL-ready handoff artifacts
docs: add optional audit personas
```

## Phase 5

```text
chore: prepare creator-toolchain plugin package
feat: add schema-validated codex plugin manifest draft
docs: add plugin install and trust policy
chore: add plugin packaging and validation script
```

---

# 51. Recommended Next Prompt

```text
Use creator-paul-loop to implement Phase 1 from IMPLEMENTATION_PLAN.v0.4.1.md.

Build only:
- AGENTS.md
- README.md
- SOURCE_TRACEABILITY_AND_AUDIT.md
- .agents/skills/creator-orchestrator/
- .agents/skills/creator-seed-incubator/
- .agents/skills/creator-paul-loop/
- docs/phase-1-test-prompts.md
- docs/phase-1-acceptance-checklist.md
- docs/examples/character-image-slide-project.md

Do not implement Phase 2–5 yet.
```

---

# 52. References

- Local source map: `docs/source-analysis/christopherkahler-toolchain-map.md`
- Local traceability companion: `SOURCE_TRACEABILITY_AND_AUDIT.md` must be amended to match this `v0.4.1` draft before final approval.
- ChristopherKahler / PAUL: https://github.com/ChristopherKahler/paul
- ChristopherKahler / SEED: https://github.com/ChristopherKahler/seed
- ChristopherKahler / BASE: https://github.com/ChristopherKahler/base
- ChristopherKahler / CARL: https://github.com/ChristopherKahler/carl
- ChristopherKahler / Skillsmith: https://github.com/ChristopherKahler/skillsmith
- ChristopherKahler / AEGIS: https://github.com/ChristopherKahler/aegis
- OpenAI Codex Skills: https://developers.openai.com/codex/skills
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex Plugin Build: https://developers.openai.com/codex/plugins/build
- OpenAI Codex Hooks: https://developers.openai.com/codex/hooks
- OpenAI Codex Subagents: https://developers.openai.com/codex/subagents
