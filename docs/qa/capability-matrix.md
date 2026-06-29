# Creator Toolchain Capability Matrix

## Status

- contract date: `2026-06-28`
- authority: current Creator-native skill contracts
- implementation: `.agents/skills/`
- package mirror: `plugin/creator-toolchain/skills/`
- structural verification: `tests/test_skill_contracts.py`
- behavior catalog: `docs/qa/behavior-acceptance-cases.json`
- behavior report: `docs/qa/behavior-acceptance-report.json`
- package report: `docs/qa/package-integrity-report.json`

## Capabilities

| Capability | Skill | Design contract | Boundary | Evidence |
|---|---|---|---|---|
| Intake | `creator-intake-planner` | Type raw ideas and produce acceptance-driven planning artifacts. | Does not implement product work. | Intake behavior cases and required type references. |
| Execution Cycle | `creator-execution-cycle` | Plan, Execute, Verify, Reconcile, summarize, and append ledger evidence. | Requires an accepted plan. | Execution behavior cases and lifecycle references. |
| Workspace State | `creator-workspace-manager` | Maintain declared state surfaces and report divergence. | Does not silently delete or execute backlog work. | State behavior cases and schema validation. |
| Rule Governance | `creator-rule-router` | Select matching rules, stage proposals, and report conflicts. | Does not load or promote every rule automatically. | Rule behavior cases and rule references. |
| Skill Workbench | `creator-skill-workbench` | Discover, scaffold, distill, score, and review skills. | Rejects collisions and oversized entry points. | Skill behavior cases and structure tests. |
| Evidence Audit | `creator-evidence-audit` | Separate Findings, Remediation Guidance, and Execution Handoff. | Does not mutate the reviewed target. | Evidence-audit behavior cases and phase references. |
| Routing | `creator-orchestrator` | Select one primary workflow and preserve downstream handoffs. | Does not absorb planning or execution. | Routing behavior cases. |

## Handoffs

| From | To | Required handoff |
|---|---|---|
| Intake | Execution Cycle | Approved planning context and unresolved-question status. |
| Execution Cycle | Workspace State | Reconcile summary, ledger event, and state proposal. |
| Workspace State | Rule Governance | Staged proposal requiring explicit review. |
| Skill Workbench | Plugin Package | Validated skill tree with unique names and resolved references. |
| Evidence Audit | Execution Cycle | Evidence-backed remediation handoff with rollback and verification gates. |

## Release Gates

- exactly seven authoritative skills;
- thirteen project types with three required references each;
- byte-equivalent plugin mirror;
- exact runtime package allowlist;
- deterministic package report and ZIP build;
- 34 passing behavior cases;
- repository, state, plugin, and CI validation.
