# Creator Toolchain Capability Matrix

## Status

- baseline date: `2026-06-27`
- authority: `docs/source-analysis/upstream-toolchain-map.md`
- implementation source: `.agents/skills/`
- package mirror: `plugin/creator-toolchain/skills/`
- structural verification: `tests/test_skill_contracts.py`
- behavioral evidence gate: `docs/qa/skill-contract-tests.md`

## Must-Preserve Capabilities

| Capability | Creator skill | Source evidence | Implementation evidence | Positive contract | Boundary contract | Expected artifact | Verification |
|---|---|---|---|---|---|---|---|
| Intake | `creator-intake-planner` | toolchain map sections 3.1 and 4.2 | `SKILL.md`; planning, scaffolding, handoff, status, add-type references; 13 type sets | raw idea is typed before planning and weak plans remain in intake | intake must not change implementation files; scaffold must not imply execution handoff | `INTAKE-STATE.md`, `PLANNING.md`, `OPEN-QUESTIONS.md`, `HANDOFF.md` | automated structure plus prompts `INTAKE-P01` to `INTAKE-N02` |
| Execution Cycle | `creator-execution-cycle` | toolchain map sections 3.1 and 4.1 | `SKILL.md`; lifecycle, acceptance, status, context, and recovery references | approved plan runs Plan -> Execute -> Verify -> Reconcile and appends closure evidence | unapproved plan and raw ideation are rejected or routed | `PLAN-*`, `RECONCILIATION-*`, `SUMMARY-*`, ledger event, state proposal | automated structure plus prompts `EXEC-P01` to `EXEC-N02` |
| Workspace State | `creator-workspace-manager` | toolchain map sections 3.2 and 4.3 | `SKILL.md`; state surfaces, health check, maintenance review, and Session Insights bridge references | health and maintenance report state divergence through structured surfaces | maintenance must not silently delete state or execute project work | health check, maintenance review, surface report, staged rule proposal | automated JSON/state checks plus prompts `STATE-P01` to `STATE-N02` |
| Rule Governance | `creator-rule-router` | toolchain map sections 3.3 and 4.4 | `SKILL.md`; rule schema, preflight, context budget references | recall selects matching domains and reports exclusions/conflicts | all rules must not load by default; staged proposals must not auto-promote | Rule Preflight and decision reference | automated rule fixture checks plus prompts `RULE-P01` to `RULE-N02` |
| Skill Workbench | `creator-skill-workbench` | toolchain map section 4.5 | `SKILL.md`; skill spec, distill chunk, compliance score references | discover/scaffold/distill/score/audit use progressive disclosure | duplicate names, missing boundaries, and stale references are rejected | skill spec, scaffold, framework chunk, compliance report | automated anatomy checks plus prompts `SKILL-P01` to `SKILL-N02` |
| Evidence Audit | `creator-evidence-audit` | toolchain map sections 3.4 and 4.6 | `SKILL.md`; Phase 0-8, named audit outputs, remediation schema references | audit separates Findings, Remediation Guidance, and Execution Handoff | audit must not directly mutate the target; Findings corrections use addenda | findings report, remediation playbook, execution-ready plan | automated boundary checks plus prompts `AUDIT-P01` to `AUDIT-N02` |

## Cross-Tool Handoffs

| ID | Handoff | Input | Output | Pass condition |
|---|---|---|---|---|
| X-01 | Intake -> Execution Cycle | approved `PLANNING.md` and `HANDOFF.md` | accepted Execution Cycle execution context | resolved questions are not asked again |
| X-02 | Execution Cycle -> Workspace State | Reconcile summary, ledger event, state proposal | reconciled project and workspace state | project IDs and statuses agree across surfaces |
| X-03 | Workspace State -> Rule Governance | Session Insights observation | staged proposal | no active rule is created without approval |
| X-04 | Rule Governance -> workflow | task prompt and active domains | compact Rule Preflight | matching rules load; excluded/nonmatching rules do not |
| X-05 | Skill Workbench -> skill suite | skill spec or raw source | validated skill structure | name collision and boundary checks pass before packaging |
| X-06 | Evidence Audit -> Execution Cycle | completed Findings diagnosis | Remediation Guidance and execution-ready handoff | no target change occurs during audit/transform |

## Verification State

| Gate | Status | Evidence |
|---|---|---|
| source snapshot freshness | PASS | six upstream HEAD values matched the source map on 2026-06-27 |
| authoritative skill count | PASS | seven `SKILL.md` files under `.agents/skills/` |
| project type sets | PASS | 13 directories, each with three required files |
| plugin mirror parity | PASS | `python3 scripts/sync_plugin_skills.py --check` |
| structural capability terms | PASS | `tests/test_skill_contracts.py` |
| behavioral prompt definitions | PASS | `docs/qa/skill-contract-tests.md` |
| installed-plugin provenance | PHASE-8 | must run from neutral directory with temporary `CODEX_HOME` |

`PHASE-8` is an explicit downstream gate, not a capability pass claim.
