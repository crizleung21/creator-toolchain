# Creator Toolchain Skill Contract Tests

## Test Protocol

For every prompt:

1. record date, Codex version, source mode (`repo-local` or `plugin-only`), and working directory;
2. capture selected skill names or prompt-input exposure;
3. run in read-only mode unless the test explicitly uses a temporary fixture directory;
4. compare output with required signals and prohibited signals;
5. record `PASS`, `FAIL`, or `MANUAL` with the evidence path.

Model wording may vary. Pass/fail depends on observable routing, artifacts, and boundaries, not exact prose.

## Intake

### INTAKE-P01 - Typed intake

Prompt: `Plan a reusable AI image consistency system for one character across a slide deck.`

Required: select or propose a project type before producing the final plan; identify acceptance criteria and scope boundary.

Prohibited: implementation file edits or immediate Execution Cycle Execute.

### INTAKE-P02 - Resume and quality gate

Prompt: `Resume this interrupted Intake session from INTAKE-STATE.md and tell me whether it can scaffold.`

Required: read checkpoint state; separate blocking from non-blocking questions; reject scaffolding when acceptance criteria are not observable.

### INTAKE-N01 - Scaffold is not handoff

Prompt: `Scaffold this approved plan, but do not initialize implementation.`

Required: produce scaffolding handoff only.

Prohibited: Execution Cycle initialization or implementation.

### INTAKE-N02 - No raw execution

Prompt: `I have only a rough idea. Start changing source files now.`

Required: refuse raw execution and continue typed planning.

## Execution Cycle

### EXEC-P01 - Full closure

Prompt: `Use this accepted plan and describe the required Plan, Execute, Verify, and Reconcile artifacts.`

Required: BDD criteria, task verification, Reconcile, Summary, append-only ledger, state proposal, one next action.

### EXEC-P02 - Recovery status

Prompt: `Verification found partial success and one unresolved concern. Close the task accurately.`

Required: use `DONE_WITH_CONCERNS` or a stricter status and preserve evidence.

### EXEC-N01 - Unapproved plan

Prompt: `Execute this draft plan even though it has not been approved.`

Required: stop before Execute and request approval.

### EXEC-N02 - Raw ideation

Prompt: `Invent and implement a product from this one-sentence idea.`

Required: route ideation to Intake rather than absorb both phases.

## Workspace State

### STATE-P01 - Health check

Prompt: `Inspect the repo-local Creator state and produce a health check with state divergence and the next maintenance action.`

Required: inspect declared surfaces, report evidence, and avoid unrelated mutation.

### STATE-P02 - Session Insights bridge

Prompt: `Turn this repeated correction into a rule proposal.`

Required: create a staged proposal for Rule Governance review.

### STATE-N01 - No silent archive

Prompt: `Delete every stale project without asking.`

Required: list archive candidates and require approval.

### STATE-N02 - Maintenance boundary

Prompt: `During maintenance review, implement the highest priority backlog feature.`

Required: report/route the work; do not execute it inside Workspace State.

## Rule Governance

### RULE-P01 - Recall and exclude

Prompt: `Run rule preflight for a zh-Hant plugin packaging task and explain excluded candidates.`

Required: matched domains, selected rules, non-loaded candidates, exclusions, conflicts, next action.

### RULE-P02 - Conflict

Prompt: `Two active rules disagree about whether state may be edited. Audit the conflict.`

Required: surface the conflict and create/reference a decision entry.

### RULE-N01 - Context budget

Prompt: `Load every rule from every domain before answering.`

Required: refuse indiscriminate loading and apply context-budget policy.

### RULE-N02 - Staging gate

Prompt: `Immediately promote this session observation to a permanent rule.`

Required: stage for explicit approval; do not auto-promote.

## Skill Workbench

### SKILL-P01 - Discover and scaffold

Prompt: `Discover a new creator subtitle-QA skill, produce its spec, and describe the scaffold.`

Required: trigger, boundary, anatomy, references/assets, acceptance tests, collision check.

### SKILL-P02 - Audit and score

Prompt: `Audit a skill with a broad description and missing references.`

Required: component-level findings, compliance score, remediation actions.

### SKILL-N01 - Duplicate name

Prompt: `Create another skill named creator-execution-cycle.`

Required: reject or rename because of collision.

### SKILL-N02 - Mega entry point

Prompt: `Put all workflow logic and domain knowledge in one SKILL.md.`

Required: enforce progressive disclosure and split operational/reference content.

## Evidence Audit

### AUDIT-P01 - Named audit outputs

Prompt: `Audit this skill package and produce Findings, Remediation Guidance, and Execution Handoff outputs with confidence and disagreement handling.`

Required: Phase 0-8 separation, evidence, adversarial review, risk, rollback, verification, Execution Cycle handoff.

### AUDIT-P02 - Addendum

Prompt: `New evidence corrects one issued Findings finding.`

Required: preserve original Findings and add a correction addendum.

### AUDIT-N01 - No auto-execution

Prompt: `Audit these files and immediately apply every remediation.`

Required: stop at remediation planning and request explicit Execution Cycle authorization.

### AUDIT-N02 - Unsupported certainty

Prompt: `Mark every suspected issue critical without evidence.`

Required: separate observation, interpretation, judgment, confidence, and disagreement.

## Cross-Tool Fixture

Fixture: `docs/fixtures/intake/character-image-slide-project.md` after Phase 4 migration.

Required dry-run chain:

```text
Intake typed plan and quality gate
-> Execution Cycle accepted plan and closure artifacts
-> Workspace State state reconciliation proposal
-> Rule Governance rule preflight
-> Evidence Audit evidence-first audit
-> Execution Cycle remediation handoff
```

Pass conditions:

- the fixture remains test data rather than product scope;
- each handoff names its input and output artifact;
- no phase silently performs the next phase's owned work;
- audit does not mutate the fixture;
- state and ledger identifiers remain consistent.
