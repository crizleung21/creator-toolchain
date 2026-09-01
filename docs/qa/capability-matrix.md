# Creator Toolchain Capability Matrix

## Authority

- stable version: `1.1.0`
- state schema: `0.4.0`
- authoritative implementation: `.agents/skills/`
- generated Plugin mirror: `plugin/creator-toolchain/skills/`
- structural tests: `tests/`
- behavior catalog: `docs/qa/behavior-acceptance-cases.json`
- canonical behavior report: `docs/qa/behavior-acceptance-report.json`
- package report: `docs/qa/package-integrity-report.json`
- final release status: `docs/qa/final-release-status.json`

## Capabilities

| Capability | Owner | Deterministic support | Boundary | Release evidence |
|---|---|---|---|---|
| Routing | `creator-orchestrator` | `creator_workflow_router.py` | selects one primary workflow; does not absorb downstream work | routing cases |
| Intake | `creator-intake-planner` | intake artifacts, project types, Planning Quality Gate | does not implement product work | intake cases and typed artifacts |
| Execution Cycle | `creator-execution-cycle` | lifecycle, task verification, closure, recovery | requires explicit approval | execution and recovery tests |
| Workspace State | `creator-workspace-manager` | bootstrap, schemas, transactions, Health, reconciliation | owns declared state surfaces except rules | state, migration, and Health tests |
| Rule Governance | `creator-rule-router` | rule store, conflict engine, decision records | proposals never auto-promote | rule cases and conflict tests |
| Skill Workbench | `creator-skill-workbench` | deterministic scoring and collision checks | does not create a mega-Skill or duplicate name | Workbench cases and scoring tests |
| Evidence Audit | `creator-evidence-audit` | finding, remediation, correction, handoff schemas | does not mutate the reviewed target | audit cases and evidence tests |
| Release | `creator-orchestrator` coordinates scripts | versioning, mirror sync, package inventory, behavior QA, clean install | does not add an eighth Skill | release evidence and Gates 01–18 |

## Cross-Workflow Handoffs

| From | To | Required artifact |
|---|---|---|
| Intake | Execution Cycle | approved execution handoff |
| Execution Cycle | Workspace State | reconciliation summary and state-update proposal |
| Workspace State | Rule Governance | staged rule proposal requiring review |
| Skill Workbench | Plugin package | validated unique Skill tree |
| Evidence Audit | Execution Cycle | evidence-backed remediation handoff |

## Stable Release Criteria

- exactly seven authoritative and seven packaged Skills;
- thirteen project types with three required references each;
- schema `0.4.0` and transactional migration/rollback;
- byte-equivalent Plugin mirror;
- exact package allowlist and payload hash;
- 34/34 current Behavior Acceptance cases;
- writable Golden E2E and green Health;
- byte-identical ZIP builds;
- clean installation and exact seven-Skill discovery;
- final branch and post-merge `main` validation.
