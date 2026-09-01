# Creator Toolchain Skill Contract Tests

## Protocol

Each behavior case runs in an isolated session against either the installed Plugin or the repository-local Skill source. Evaluation uses observable routing, artifacts, approvals, boundaries, selected Skill names, and evidence spans rather than exact prose.

The mandatory release gate uses a provider-neutral deterministic response adapter and an independent evaluator. Supplemental external-model adapters remain diagnostic experiments and do not replace canonical evidence.

Every result records:

- case ID;
- tested commit and package payload;
- runtime and evaluator adapters;
- selected Skill;
- required and prohibited observations;
- line-linked evidence;
- raw-response path and SHA-256;
- result, timestamps, and exit code.

## Evidence Freshness

`docs/qa/behavior-acceptance-status.json` is the authoritative freshness overlay:

- `CURRENT` means the complete report matches the current package payload;
- `STALE` means the preserved report is historical and cannot satisfy release gates;
- commit-, payload-, catalog-, or harness-relevant changes require a new complete run;
- stored `PASS` text without evidence spans cannot satisfy the gate.

The durable raw-response archive is `docs/qa/behavior-acceptance-current.zip`.

## Coverage

| Surface | Positive | Boundary | Required behavior |
|---|---:|---:|---|
| Routing | 1 | 1 | choose Intake for raw ideas and reject mixed-scope bypass |
| Intake | 2 | 2 | type ideas, enforce planning quality, and avoid raw execution |
| Execution Cycle | 2 | 2 | require approval and close with verified Reconcile artifacts |
| Workspace State | 2 | 2 | report Health and stage proposals without executing backlog |
| Rule Governance | 2 | 2 | recall matching rules, report conflicts, and preserve staging |
| Skill Workbench | 2 | 2 | produce structured Skills and reject collisions/mega entry points |
| Evidence Audit | 2 | 2 | produce named evidence outputs without automatic remediation |
| Cross-workflow chain | 1 | 0 | preserve identifiers and ownership across handoffs |
| Repository-local smoke | 7 | 0 | discover every authoritative Skill |
| **Total** |  |  | **34 cases** |

## Structural and Operational Tests

The unit suite additionally covers schema assets, path safety, atomic rollback, IDs, ledgers, lifecycle transitions, task evidence, recovery, Health, rule conflicts, Workbench scoring, mirror parity, package integrity, release build reproducibility, clean installation, documentation commands, and seven-Skill discovery.
