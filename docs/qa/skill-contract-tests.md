# Creator Toolchain Skill Contract Tests

## Protocol

Each behavior case runs in an independent session against either the installed plugin or the repository-local skill source. Review uses observable routing, artifacts, boundaries, and selected skill names rather than exact prose.

Plugin-only cases run against a neutral, read-only fixture workspace. A generic harness instruction tells the session to evaluate workflow-owned routing, gates, approvals, artifacts, and handoffs instead of using the sandbox restriction as the sole boundary reason. The harness contains no case-specific required or prohibited observations.

The same harness requires declared numbered phases to remain visible and requires evidence audits to distinguish observations, interpretations, judgments, confidence, and disagreement handling. These rules apply uniformly to all relevant audit prompts.

Every result records:

- case ID;
- Codex version and execution mode;
- selected skill;
- required observations;
- prohibited observations;
- result;
- response artifact path and SHA-256.

## Coverage

| Surface | Positive | Boundary | Required behavior |
|---|---:|---:|---|
| Routing | 1 | 1 | Select Intake for raw ideas and reject mixed-scope bypass. |
| Intake | 2 | 2 | Type ideas, enforce quality, and avoid raw execution. |
| Execution Cycle | 2 | 2 | Require acceptance and close with verified Reconcile artifacts. |
| Workspace State | 2 | 2 | Report health and stage proposals without executing backlog work. |
| Rule Governance | 2 | 2 | Recall matching rules, report conflicts, and preserve staging. |
| Skill Workbench | 2 | 2 | Produce structured skills and reject collisions or mega entry points. |
| Evidence Review | 2 | 2 | Produce named evidence outputs without automatic remediation. |
| Cross-workflow chain | 1 | 0 | Preserve identifiers and owned boundaries across handoffs. |
| Repository-local smoke | 7 | 0 | Discover every authoritative skill from the repository source. |

The machine-readable definitions live in `behavior-acceptance-cases.json`; verified results live in `behavior-acceptance-report.json` and `behavior-acceptance/`.
