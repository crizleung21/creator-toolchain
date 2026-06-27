# creator-toolchain — SOURCE_TRACEABILITY_AND_AUDIT.md

**Version:** 0.4.1  
**Status:** Amended companion for implemented `v0.4.1` Creator Toolchain scaffold; public plugin schema validation remains pending  
**Date:** 2026-06-26  
**Canonical Repository:** `creator-toolchain`  
**Related Files:** `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_PLAN.v0.4.1.md`  
**Purpose:** 追蹤 ChristopherKahler 工具鏈高價值功能如何移植到 `creator-toolchain`，並記錄對 implementation plan 的多回合審核結果。  

---

## 0. BLUF

本文件回答：

> ChristopherKahler 工具鏈的核心高價值功能，有沒有完整、準確、專業地移植到 `creator-toolchain`？

Current verdict:

```text
Pass for local scaffold completeness; not yet a public release pass until current Codex plugin schema validation is recorded.
```

本版已加入或落地：

- source evidence
- implementation target
- acceptance test
- gap status
- `v0.4.1` source drift / non-inheritance amendments
- `.creator/` state surfaces
- seven local Codex skill directories
- plugin package scaffold
- validation script
- Codex Skill compliance audit
- Codex Plugin manifest compliance audit
- Hook trust audit
- Subagent explicit invocation audit
- release gate evidence requirements

## 0.1 v0.4.1 Amendment

`IMPLEMENTATION_PLAN.v0.4.1.md` supersedes the `v0.4.0` final/pass language for implementation execution. The following corrections are now part of the acceptance baseline:

- Treat `docs/source-analysis/christopherkahler-toolchain-map.md` as canonical Phase 0 evidence.
- Preserve PAUL closure through `project.json`, `activity_ledger.jsonl`, task qualification evidence, Unify, and Summary.
- Preserve SEED via typed planning, Planning Quality Gate, `graduate`, `launch`, `status`, and `add-type`.
- Preserve BASE as repo-local `.creator/*.json` state, without requiring upstream `.base/data/*.json`.
- Preserve CARL via `GLOBAL`, recall, exclude, command registry, staged proposals, decision log, and conflict audit.
- Preserve Skillsmith through skill anatomy, `SKILL-SPEC`, distill chunks, compliance scoring, and audit checks.
- Preserve AEGIS through Phase 0-8, Layer A/B/C, Reality Gap, Devil's Advocate, and PAUL-ready remediation handoff.
- Mark plugin manifest as draft until validated against the current official schema.
- Exclude `upstream/`, private `.creator/` state, `.DS_Store`, caches, and local research artifacts from plugin packages.

---

## 1. Reviewed Inputs

### 1.1 User Documents

| File | Role | Status |
|---|---|---|
| `IMPLEMENTATION_PLAN.md` | original master build plan | retained |
| `IMPLEMENTATION_PLAN.v0.4.1.md` | amended execution baseline | active |
| `SOURCE_TRACEABILITY_AND_AUDIT.md` | traceability companion | amended to v0.4.1 |
| `docs/source-analysis/christopherkahler-toolchain-map.md` | canonical six-tool source map | active |

### 1.2 Public Sources

| Source | URL | Primary Evidence Used |
|---|---|---|
| ChristopherKahler profile | https://github.com/ChristopherKahler | repo ecosystem overview |
| PAUL | https://github.com/ChristopherKahler/paul | Plan-Apply-Unify, mandatory Unify, BDD AC, Execute/Qualify |
| SEED | https://github.com/ChristopherKahler/seed | typed ideation, graduate, launch, status, add-type |
| BASE | https://github.com/ChristopherKahler/base | data surfaces, PSMM, operator profile, pulse/groom/drift |
| CARL | https://github.com/ChristopherKahler/carl | domain rules, keyword recall, staging, JIT context |
| Skillsmith | https://github.com/ChristopherKahler/skillsmith | Discover/Scaffold/Distill/Audit, seven file types, skill tiers |
| AEGIS | https://github.com/ChristopherKahler/aegis | Layer A/B/C, audit personas, PAUL-ready handoff |
| Codex Skills | https://developers.openai.com/codex/skills | `SKILL.md`, name/description, progressive disclosure |
| Codex AGENTS.md | https://developers.openai.com/codex/guides/agents-md | repo guidance |
| Codex Plugin Build | https://developers.openai.com/codex/plugins/build | official plugin manifest structure |
| Codex Hooks | https://developers.openai.com/codex/hooks | lifecycle hook events and trust implications |
| Codex Subagents | https://developers.openai.com/codex/subagents | explicit subagent invocation and token cost |

---

## 2. Source-by-Source Mini Summaries

### 2.1 PAUL

PAUL is valuable because it turns implementation into a closure-enforced loop. The essential migration is not just “make a plan,” but: plan, apply, qualify, unify, summarize, and reconcile state.

Creator port:

```text
creator-paul-loop
```

Must include:

- Plan → Apply → Qualify → Unify
- BDD acceptance criteria
- escalation statuses
- mandatory summary
- recovery workflows
- state update proposal
- in-session implementation preference

### 2.2 SEED

SEED is valuable because it turns raw ideas into typed project plans and provides graduation / launch handoff into execution.

Creator port:

```text
creator-seed-incubator
```

Must include:

- typed ideation
- project type rigor
- `SEED-STATE.md`
- `PLANNING.md`
- status
- add-type
- graduate
- launch
- type-specific guides/config/loadouts

### 2.3 BASE

BASE is valuable because it gives the agent a structured workspace state model.

Creator port:

```text
creator-base-workspace
```

Must include:

- `.creator/workspace.json`
- `.creator/projects.json`
- `.creator/entities.json`
- `.creator/state.json`
- `.creator/psmm.json`
- `.creator/operator.json`
- `.creator/backlog.json`
- `.creator/surfaces.json`
- pulse
- groom
- drift score
- surface CRUD

### 2.4 CARL

CARL is valuable because it prevents giant static instruction files by routing relevant rules only when needed.

Creator port:

```text
creator-rule-router
```

Must include:

- domain model
- recall keywords
- rule lifecycle
- proposal staging
- domain operations
- preflight output
- conflict detection
- context budget policy

### 2.5 Skillsmith

Skillsmith is valuable because it standardizes how skills are discovered, scaffolded, distilled, and audited.

Creator port:

```text
creator-skillsmith-factory
```

Must include:

- Discover
- Scaffold
- Distill
- Audit
- seven file types
- skill tiers
- compliance score
- `SKILL-SPEC.md`
- generated skill registry

### 2.6 AEGIS

AEGIS is valuable because it separates diagnosis from remediation and execution.

Creator port:

```text
creator-aegis-audit
```

Must include:

- audit modes
- optional subagent personas
- Layer A Diagnosis
- Layer B Remediation
- Layer C Orchestration
- evidence/confidence/disagreement
- Reality Gap
- Devil’s Advocate
- PAUL-ready handoff artifacts
- audit never modifies files directly

---

## 3. Multi-Round Audit Protocol

### Round 1 — Structural Audit

Check:

- phase hierarchy
- file tree coherence
- skill separation
- naming consistency
- repo-local state design

Result:

```text
Pass.
```

### Round 2 — Source Fidelity Audit

Check:

- PAUL high-value features
- SEED high-value features
- BASE high-value features
- CARL high-value features
- Skillsmith high-value features
- AEGIS high-value features

Result:

```text
Pass with P0 amendments resolved.
```

### Round 3 — Codex-native Compliance Audit

Check:

- Skill-centric design
- `AGENTS.md` usage
- official plugin manifest structure
- hooks optional and trust-reviewed
- MCP optional
- subagents explicit

Result:

```text
Pass after official plugin manifest correction.
```

### Round 4 — Creator Workflow Fit Audit

Check:

- slide project support
- character asset matrix
- prompt workflow support
- image/video asset support
- rule routing
- creator audit

Result:

```text
Pass.
```

### Round 5 — Risk / Security / Packaging Audit

Check:

- hooks trust boundary
- MCP policy
- privacy / user state
- plugin packaging gates
- destructive command safeguards

Result:

```text
Pass.
```

### Round 6 — Naming / Path / Schema Audit

Check:

- no active `ck-*`
- no active `.ck/`
- `.creator/` used consistently
- `creator-toolchain` active naming
- historical names only in migration notes

Result:

```text
Pass.
```

### Round 7 — Final Acceptance Audit

Check:

- implementation-ready
- source-traceable
- not over-engineered in Phase 1
- Phase 2–5 staged correctly

Result:

```text
Accepted.
```

---

## 4. Source Traceability Matrix

### 4.1 PAUL → `creator-paul-loop`

| Source Feature | Evidence | Implementation Target | Acceptance Test | Gap Status |
|---|---|---|---|---|
| Plan → Apply → Unify | PAUL repo | `IMPLEMENTATION_PLAN.md` Phase 1 / `creator-paul-loop` | execution produces PLAN + UNIFY | Included |
| Mandatory Unify | PAUL repo | `UNIFY-{seq}.md` rule | no execution cycle complete without Unify | Included |
| Summary artifact | PAUL repo | `SUMMARY-{seq}.md` | summary exists after Unify | Included |
| BDD acceptance criteria | PAUL repo | BDD AC section | criteria use Given/When/Then | Included |
| Execute/Qualify loop | PAUL repo | Apply / Qualify loop | each task has qualification status | Included |
| Escalation statuses | PAUL repo | escalation status schema | statuses include DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED | Included |
| In-session context preference | PAUL repo | subagent policy | core implementation does not auto-spawn subagents | Included |
| State reconciliation | PAUL repo | state proposal | Unify includes state update proposal | Included |
| Recovery workflows | derived from PAUL closure model | recovery section | orphan plan recovery test passes | Included |

### 4.2 SEED → `creator-seed-incubator`

| Source Feature | Evidence | Implementation Target | Acceptance Test | Gap Status |
|---|---|---|---|---|
| type-aware ideation | SEED repo | project types + rigor | raw idea classified into one type | Included |
| `PLANNING.md` | SEED repo | planning output | PLANNING.md generated | Included |
| `SEED-STATE.md` | SEED repo / ported session state | seed state output | active planning session has SEED-STATE.md | Included |
| graduate | SEED repo | graduation workflow | plan creates project scaffold proposal | Included |
| launch | SEED repo | launch workflow | handoff to `creator-paul-loop` exists | Included |
| status | SEED repo | status output table | pipeline status can be printed | Included |
| add-type | SEED repo | custom type schema | new project type requires schema fields | Included |
| type loadouts | SEED repo | type guide/config/loadout | every type has guide/config/loadout | Included |

### 4.3 BASE → `creator-base-workspace`

| Source Feature | Evidence | Implementation Target | Acceptance Test | Gap Status |
|---|---|---|---|---|
| workspace manifest | BASE repo | `.creator/workspace.json` | workspace parses | Included |
| Projects surface | BASE repo | `.creator/projects.json` | active projects listed | Included |
| Entities surface | BASE repo | `.creator/entities.json` | entities parse | Included |
| State surface | BASE repo | `.creator/state.json` | drift score available | Included |
| PSMM | BASE repo | `.creator/psmm.json` | PSMM lifecycle documented | Included |
| Operator profile | BASE repo | `.creator/operator.json` | private operator template exists | Included |
| Pulse | BASE repo | `creator-pulse` output | pulse report generated | Included |
| Groom | BASE repo | `creator-groom` output | groom report generated | Included |
| Custom surfaces | BASE repo | surface CRUD | surface create/list/validate works manually | Included |
| MCP server | BASE repo | Phase 5 optional | not required pre-v1 | Roadmap |

### 4.4 CARL → `creator-rule-router`

| Source Feature | Evidence | Implementation Target | Acceptance Test | Gap Status |
|---|---|---|---|---|
| domain rules | CARL repo | domain model | rules grouped by domain | Included |
| keyword recall | CARL repo | `recall` terms | prompt matches expected domain | Included |
| JIT rule loading | CARL repo | manual preflight first | preflight selects relevant rules | Included |
| global rules | CARL repo | `GLOBAL` domain | global rules always considered | Included |
| staging | CARL repo | rule lifecycle | proposed → staged → active flow | Included |
| domain operations | CARL repo | operations list | create/toggle/add/stage actions documented | Included |
| conflict detection | CARL repo + governance extension | conflict audit | duplicate/contradiction detected | Included |
| hook runtime | CARL repo | Phase 5 optional | not required pre-v1 | Roadmap |

### 4.5 Skillsmith → `creator-skillsmith-factory`

| Source Feature | Evidence | Implementation Target | Acceptance Test | Gap Status |
|---|---|---|---|---|
| Discover | Skillsmith repo | discover workflow | skill spec generated | Included |
| Scaffold | Skillsmith repo | scaffold workflow | folder created | Included |
| Distill | Skillsmith repo | distill workflow | framework chunk generated | Included |
| Audit | Skillsmith repo | audit workflow | compliance score produced | Included |
| seven file types | Skillsmith repo | file type specs | all specs documented | Included |
| skill tiers | Skillsmith repo | tier table | tier assigned | Included |
| `SKILL-SPEC.md` | Skillsmith repo / Codex port | required fields | all fields complete | Included |
| scoring | Skillsmith audit concept | compliance score | score 0–100 exists | Included |

### 4.6 AEGIS → `creator-aegis-audit`

| Source Feature | Evidence | Implementation Target | Acceptance Test | Gap Status |
|---|---|---|---|---|
| multi-persona audit | AEGIS repo | audit personas | optional persona files exist | Included |
| Layer A | AEGIS repo | `LAYER-A-DIAGNOSIS.md` | findings immutable | Included |
| Layer B | AEGIS repo | `LAYER-B-REMEDIATION.md` | playbook generated | Included |
| Layer C | AEGIS repo | `LAYER-C-EXECUTION-PLAN.md` | execution plan generated | Included |
| Devil’s Advocate | AEGIS repo | `DEVIL-ADVOCATE.md` | non-empty critique required | Included |
| Reality Gap | AEGIS repo | `REALITY-GAP.md` | plan vs actual checked | Included |
| confidence | AEGIS repo | finding schema | confidence field exists | Included |
| disagreements | AEGIS repo | disagreements report | disagreements tracked | Included |
| PAUL-ready handoff | AEGIS repo | handoff folder | PROJECT/ROADMAP/verification/rollback exist | Included |
| audit does not modify | AEGIS separation model | audit boundary | audit produces reports only | Included |

---

## 5. Codex Compliance Audit

### 5.1 Skill Compliance

| Requirement | Evidence | Status |
|---|---|---|
| Each skill has `SKILL.md` | Codex Skills docs | Required |
| `SKILL.md` includes `name` | Codex Skills docs | Required |
| `SKILL.md` includes `description` | Codex Skills docs | Required |
| Description supports progressive disclosure | Codex Skills docs | Required |
| Skills are focused, not mega-skills | Codex design implication | Required |
| Optional references/assets/scripts documented | Codex Skills docs | Required |

### 5.2 Plugin Manifest Compliance

| Requirement | Status |
|---|---|
| `.codex-plugin/plugin.json` required | Included |
| top-level `name` | Included |
| top-level `version` | Included |
| top-level `description` | Included |
| `skills`: `./skills/` | Included |
| `interface.displayName` | Included |
| `interface.shortDescription` | Included |
| `interface.longDescription` | Included |
| `interface.defaultPrompt` array | Included |
| no top-level `schema_version` | Corrected |
| no top-level `defaultPrompt` | Corrected |
| no private `.creator/` state bundled | Gate required |

### 5.3 Hooks Trust Audit

| Hook | Risk | Policy |
|---|---|---|
| SessionStart | too much context injection | load summary only |
| UserPromptSubmit | overactive rule injection | hint only |
| PreToolUse | blocking too aggressively | destructive warning only |
| Stop | looping / forced continuation | suggest Unify only |
| SubagentStart/Stop | token/cost | audit logging only |

### 5.4 Subagent Explicit Invocation Audit

| Requirement | Status |
|---|---|
| subagents optional | Included |
| user must explicitly ask | Included |
| no automatic persona spawning | Included |
| subagents return evidence and limits | Included |
| main agent synthesizes | Included |

---

## 6. Modification Log

### P0 — Must-Have Changes Applied

| ID | Change | Applied To |
|---|---|---|
| IP-P0-01 | official plugin manifest with `interface` object | Phase 5 |
| IP-P0-02 | removed top-level `schema_version` from plugin manifest | Phase 5 |
| IP-P0-03 | moved `defaultPrompt` to `interface.defaultPrompt` array | Phase 5 |
| IP-P0-04 | added top-level `description` | Phase 5 |
| IP-P0-05 | added Skill Namespace Policy | main plan |
| IP-P0-06 | added Skill Description Budget Policy | main plan |
| IP-P0-07 | added AEGIS PAUL handoff artifacts | Phase 4 |
| IP-P0-08 | added audit modes and subagent policy | Phase 4 |
| IP-P0-09 | added BASE surface CRUD | Phase 2 |
| IP-P0-10 | added CARL domain operations and rule preflight | Phase 3 |
| IP-P0-11 | added Skillsmith compliance scoring | Phase 3 |
| IP-P0-12 | added SEED status and add-type output formats | Phase 1 |
| IP-P0-13 | added PAUL recovery workflows | Phase 1 |
| IP-P0-14 | added AGENTS.md contract | Phase 1 |
| IP-P0-15 | added README.md contract | Phase 1 |
| STA-P0-01 | added Evidence column | this file |
| STA-P0-02 | added Implementation Target column | this file |
| STA-P0-03 | added Acceptance Test column | this file |
| STA-P0-04 | added Gap Status column | this file |
| STA-P0-05 | added Codex Plugin Compliance Audit | this file |
| STA-P0-06 | added Codex Skill Compliance Audit | this file |
| STA-P0-07 | added Plugin Manifest Audit Checklist | this file |
| STA-P0-08 | added Hook Trust Audit | this file |
| STA-P0-09 | added Subagent Explicit Invocation Audit | this file |
| STA-P0-10 | updated final verdict | this file |

### P1 — Strong Recommendations Applied

| ID | Change | Applied To |
|---|---|---|
| IP-P1-01 | normalized Creator Toolchain naming | main plan |
| IP-P1-02 | added source-analysis docs list | Phase 0 |
| IP-P1-03 | strengthened canonical example | main plan |
| IP-P1-04 | extended asset matrix | main plan |
| IP-P1-05 | added creator-pulse output format | Phase 2 |
| IP-P1-06 | added creator-groom output format | Phase 2 |
| IP-P1-07 | added state privacy classification | Phase 2 / Privacy |
| IP-P1-08 | added Superpowers coexistence to main plan | main plan |
| IP-P1-09 | added source evidence appendix references | both files |
| IP-P1-10 | added Phase 0 Research Baseline | main plan |
| STA-P1-01 | changed pass wording to “Pass with P0 amendments resolved” | this file |
| STA-P1-02 | added source mini summaries | this file |
| STA-P1-03 | retained shorter Superpowers coexistence | this file |
| STA-P1-04 | risk register includes phase/status | this file |
| STA-P1-05 | release gate evidence added | this file |
| STA-P1-06 | no-final-file-until-confirmed workflow fulfilled | this process |

### P2 — Roadmap Only

| ID | Change | Roadmap Status |
|---|---|
| IP-P2-01 | Google Slides / Drive integration profile | post-v1 |
| IP-P2-02 | Anytype / Notion / Drive state sync | post-v1 |
| IP-P2-03 | Creator dashboard | post-v1 |
| IP-P2-04 | independent `creator-surface-manager` | post-v1 if needed |
| IP-P2-05 | public marketplace publishing checklist | after local validation |
| P2-06 | MCP server for `.creator/` state | optional post-v1 |
| P2-07 | automated dashboard | optional post-v1 |

---

## 7. Creator Domain Coverage Audit

| Domain | Coverage in Final Plan | Status |
|---|---|---|
| Slide Deck | project type, rule domain, canonical example, asset matrix | Covered |
| AI Image | project type, rule domain, asset matrix | Covered |
| CharacterLock | project type, rule domain, asset matrix | Covered |
| HeadLock | project type | Covered |
| AI Video | project type, rule domain, future surface | Covered |
| Prompt Pack | project type, rule domain, skill factory target | Covered |
| Character Registry | project type, surface candidate, asset schema | Covered |
| Content Campaign | project type, custom surface | Covered |
| Tool Research | project type, `tools.json` surface | Covered |
| Plugin Packaging | Phase 5 + trust gates | Covered |

---

## 8. Release Gate Evidence Required

### v0.1.0-mvp

Required evidence:

- `AGENTS.md`
- `README.md`
- three MVP `SKILL.md` files
- sample `PLANNING.md`
- sample `PLAN-001.md`
- sample `UNIFY-001.md`
- Phase 1 acceptance checklist

### v0.2.0-state

Required evidence:

- all core `.creator/*.json` files
- valid JSON check output
- `Creator Pulse` sample
- `Creator Groom` sample
- cross-surface consistency report

### v0.3.0-rules-factory

Required evidence:

- sample `rules.json`
- rule preflight report
- rule conflict audit
- sample `SKILL-SPEC.md`
- skill audit score

### v0.4.0-audit

Required evidence:

- Layer A/B/C reports
- `FINDINGS.json`
- `DEVIL-ADVOCATE.md`
- `REALITY-GAP.md`
- handoff folder
- remediation risk metadata

### v1.0.0-plugin

Required evidence:

- official `plugin.json`
- local install result
- skill trigger test result
- private-state exclusion proof
- hook trust review result
- Phase 4 packaging audit

---

## 9. Privacy Audit

| File | Risk | Policy |
|---|---|---|
| `.creator/operator.json` | personal working profile | local only unless sanitized |
| `.creator/entities.json` | people / clients / tools | do not bundle in plugin |
| `.creator/projects.json` | project data | template only in plugin |
| `.creator/psmm.json` | session decisions / corrections | local only |
| `.creator/rules.json` | may include personal working preferences | review before publish |
| `.creator/*.local.json` | private overrides | never package |

---

## 10. Risk Register

| ID | Risk | Phase | Severity | Status | Mitigation |
|---|---|---:|---:|---|---|
| RISK-001 | overbuilding before MVP validation | 1 | High | open | Phase gates |
| RISK-002 | orchestrator becomes mega-skill | 1 | High | open | routing-only contract |
| RISK-003 | state becomes hidden memory | 2 | High | open | repo-local `.creator/` |
| RISK-004 | rule conflicts | 3 | Medium | open | conflict audit |
| RISK-005 | generated skills inconsistent | 3 | Medium | open | compliance score |
| RISK-006 | audit overclaims | 4 | High | open | evidence/confidence/disagreement |
| RISK-007 | subagents too expensive | 4 | Medium | open | explicit invocation only |
| RISK-008 | plugin packages private data | 5 | High | open | privacy packaging gate |
| RISK-009 | hooks become unsafe | 5 | High | open | disabled until reviewed |
| RISK-010 | `ck-*` remnants remain | all | Low | open | naming audit |
| RISK-011 | creator domain underfit | all | High | mitigated | canonical example |
| RISK-012 | external integrations over-scoped | roadmap | Medium | open | P2 roadmap only |

---

## 11. Superpowers Coexistence Strategy

| Tool | Role |
|---|---|
| Superpowers | coding discipline / TDD / worktrees / code review |
| creator-toolchain | creator workflow / prompt / slide / character / image / video / state / audit |

Rule:

```text
Superpowers handles engineering discipline.
creator-toolchain handles creator production discipline.
```

If both are needed:

```text
creator-seed-incubator defines the creator project.
creator-paul-loop controls creator deliverables.
Superpowers can assist implementation-heavy coding steps.
creator-aegis-audit checks final workflow and creator artifacts.
```

---

## 12. Final Audit Verdict

| Dimension | Verdict |
|---|---|
| source fidelity | Pass |
| Codex-native architecture | Pass |
| official plugin manifest alignment | Pass after correction |
| creator domain fit | Pass |
| phase separation | Pass |
| naming policy | Pass |
| privacy/trust boundary | Pass |
| plugin readiness path | Pass |
| implementation clarity | Pass |

Final recommendation:

```text
Proceed to Phase 1 implementation only.
Do not build Phase 2–5 until Phase 1 passes acceptance tests.
```

---

## 13. Next Implementation Prompt

```text
Use creator-paul-loop to implement Phase 1 from IMPLEMENTATION_PLAN.md.

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
