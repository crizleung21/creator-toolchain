# Creator Toolchain Capability Matrix

## Status

- baseline date: `2026-06-27`
- authority: `docs/source-analysis/christopherkahler-toolchain-map.md`
- implementation source: `.agents/skills/`
- package mirror: `plugin/creator-toolchain/skills/`
- structural verification: `tests/test_skill_contracts.py`
- behavioral evidence gate: `docs/qa/skill-contract-tests.md`

## Must-Preserve Capabilities

| Source | Creator skill | Source evidence | Implementation evidence | Positive contract | Boundary contract | Expected artifact | Verification |
|---|---|---|---|---|---|---|---|
| SEED | `creator-seed-incubator` | toolchain map sections 3.1 and 4.2 | `SKILL.md`; planning, graduation, launch, status, add-type references; 13 type sets | raw idea is typed before planning and weak plans remain in ideation | ideation must not change implementation files; graduate must not imply launch | `SEED-STATE.md`, `PLANNING.md`, `OPEN-QUESTIONS.md`, `HANDOFF.md` | automated structure plus prompts `SEED-P01` to `SEED-N02` |
| PAUL | `creator-paul-loop` | toolchain map sections 3.1 and 4.1 | `SKILL.md`; lifecycle, acceptance, status, context, and recovery references | approved plan runs Plan -> Apply -> Qualify -> Unify and appends closure evidence | unapproved plan and raw ideation are rejected or routed | `PLAN-*`, `UNIFY-*`, `SUMMARY-*`, ledger event, state proposal | automated structure plus prompts `PAUL-P01` to `PAUL-N02` |
| BASE | `creator-base-workspace` | toolchain map sections 3.2 and 4.3 | `SKILL.md`; state surfaces, pulse/groom, PSMM bridge references | pulse/groom report state and drift through structured surfaces | maintenance must not silently delete state or execute project work | pulse, groom, surface report, staged rule proposal | automated JSON/state checks plus prompts `BASE-P01` to `BASE-N02` |
| CARL | `creator-rule-router` | toolchain map sections 3.3 and 4.4 | `SKILL.md`; rule schema, preflight, context budget references | recall selects matching domains and reports exclusions/conflicts | all rules must not load by default; staged proposals must not auto-promote | Rule Preflight and decision reference | automated rule fixture checks plus prompts `CARL-P01` to `CARL-N02` |
| Skillsmith | `creator-skillsmith-factory` | toolchain map section 4.5 | `SKILL.md`; skill spec, distill chunk, compliance score references | discover/scaffold/distill/score/audit use progressive disclosure | duplicate names, missing boundaries, and stale references are rejected | skill spec, scaffold, framework chunk, compliance report | automated anatomy checks plus prompts `SMITH-P01` to `SMITH-N02` |
| AEGIS | `creator-aegis-audit` | toolchain map sections 3.4 and 4.6 | `SKILL.md`; Phase 0-8, Layer A/B/C, remediation schema references | audit separates diagnosis, remediation knowledge, and PAUL handoff | audit must not directly mutate the target; Layer A corrections use addenda | Layer A findings, Layer B playbook, Layer C PAUL plan | automated boundary checks plus prompts `AEGIS-P01` to `AEGIS-N02` |

## Cross-Tool Handoffs

| ID | Handoff | Input | Output | Pass condition |
|---|---|---|---|---|
| X-01 | SEED -> PAUL | approved `PLANNING.md` and `HANDOFF.md` | accepted PAUL execution context | resolved questions are not asked again |
| X-02 | PAUL -> BASE | Unify summary, ledger event, state proposal | reconciled project and workspace state | project IDs and statuses agree across surfaces |
| X-03 | BASE -> CARL | PSMM observation | staged proposal | no active rule is created without approval |
| X-04 | CARL -> workflow | task prompt and active domains | compact Rule Preflight | matching rules load; excluded/nonmatching rules do not |
| X-05 | Skillsmith -> skill suite | skill spec or raw source | validated skill structure | name collision and boundary checks pass before packaging |
| X-06 | AEGIS -> PAUL | completed Layer A diagnosis | Layer B/C and PAUL-ready remediation | no target change occurs during audit/transform |

## Verification State

| Gate | Status | Evidence |
|---|---|---|
| source snapshot freshness | PASS | six upstream HEAD values matched the source map on 2026-06-27 |
| authoritative skill count | PASS | seven `SKILL.md` files under `.agents/skills/` |
| SEED type sets | PASS | 13 directories, each with three required files |
| plugin mirror parity | PASS | `python3 scripts/sync_plugin_skills.py --check` |
| structural capability terms | PASS | `tests/test_skill_contracts.py` |
| behavioral prompt definitions | PASS | `docs/qa/skill-contract-tests.md` |
| installed-plugin provenance | PHASE-8 | must run from neutral directory with temporary `CODEX_HOME` |

`PHASE-8` is an explicit downstream gate, not a capability pass claim.
