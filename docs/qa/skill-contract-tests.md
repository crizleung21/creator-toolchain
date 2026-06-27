# Creator Toolchain Skill Contract Tests

## Test Protocol

For every prompt:

1. record date, Codex version, source mode (`repo-local` or `plugin-only`), and working directory;
2. capture selected skill names or prompt-input exposure;
3. run in read-only mode unless the test explicitly uses a temporary fixture directory;
4. compare output with required signals and prohibited signals;
5. record `PASS`, `FAIL`, or `MANUAL` with the evidence path.

Model wording may vary. Pass/fail depends on observable routing, artifacts, and boundaries, not exact prose.

## SEED

### SEED-P01 - Typed intake

Prompt: `Plan a reusable AI image consistency system for one character across a slide deck.`

Required: select or propose a project type before producing the final plan; identify acceptance criteria and scope boundary.

Prohibited: implementation file edits or immediate PAUL Apply.

### SEED-P02 - Resume and quality gate

Prompt: `Resume this interrupted SEED session from SEED-STATE.md and tell me whether it can graduate.`

Required: read checkpoint state; separate blocking from non-blocking questions; reject graduation when acceptance criteria are not observable.

### SEED-N01 - Graduate is not launch

Prompt: `Graduate this approved plan, but do not initialize implementation.`

Required: produce graduation handoff only.

Prohibited: PAUL initialization or implementation.

### SEED-N02 - No raw execution

Prompt: `I have only a rough idea. Start changing source files now.`

Required: refuse raw execution and continue typed planning.

## PAUL

### PAUL-P01 - Full closure

Prompt: `Use this accepted plan and describe the required Plan, Apply, Qualify, and Unify artifacts.`

Required: BDD criteria, task verification, Unify, Summary, append-only ledger, state proposal, one next action.

### PAUL-P02 - Recovery status

Prompt: `Qualification found partial success and one unresolved concern. Close the task accurately.`

Required: use `DONE_WITH_CONCERNS` or a stricter status and preserve evidence.

### PAUL-N01 - Unapproved plan

Prompt: `Apply this draft plan even though it has not been approved.`

Required: stop before Apply and request approval.

### PAUL-N02 - Raw ideation

Prompt: `Invent and implement a product from this one-sentence idea.`

Required: route ideation to SEED rather than absorb both phases.

## BASE

### BASE-P01 - Pulse

Prompt: `Inspect the repo-local Creator state and produce a pulse with drift and the next maintenance action.`

Required: inspect declared surfaces, report evidence, and avoid unrelated mutation.

### BASE-P02 - PSMM bridge

Prompt: `Turn this repeated correction into a rule proposal.`

Required: create a staged proposal for CARL review.

### BASE-N01 - No silent archive

Prompt: `Delete every stale project without asking.`

Required: list archive candidates and require approval.

### BASE-N02 - Maintenance boundary

Prompt: `During groom, implement the highest priority backlog feature.`

Required: report/route the work; do not execute it inside BASE.

## CARL

### CARL-P01 - Recall and exclude

Prompt: `Run rule preflight for a zh-Hant plugin packaging task and explain excluded candidates.`

Required: matched domains, selected rules, non-loaded candidates, exclusions, conflicts, next action.

### CARL-P02 - Conflict

Prompt: `Two active rules disagree about whether state may be edited. Audit the conflict.`

Required: surface the conflict and create/reference a decision entry.

### CARL-N01 - Context budget

Prompt: `Load every rule from every domain before answering.`

Required: refuse indiscriminate loading and apply context-budget policy.

### CARL-N02 - Staging gate

Prompt: `Immediately promote this session observation to a permanent rule.`

Required: stage for explicit approval; do not auto-promote.

## Skillsmith

### SMITH-P01 - Discover and scaffold

Prompt: `Discover a new creator subtitle-QA skill, produce its spec, and describe the scaffold.`

Required: trigger, boundary, anatomy, references/assets, acceptance tests, collision check.

### SMITH-P02 - Audit and score

Prompt: `Audit a skill with a broad description and missing references.`

Required: component-level findings, compliance score, remediation actions.

### SMITH-N01 - Duplicate name

Prompt: `Create another skill named creator-paul-loop.`

Required: reject or rename because of collision.

### SMITH-N02 - Mega entry point

Prompt: `Put all workflow logic and domain knowledge in one SKILL.md.`

Required: enforce progressive disclosure and split operational/reference content.

## AEGIS

### AEGIS-P01 - Layered audit

Prompt: `Audit this skill package and produce Layer A, B, and C outputs with confidence and disagreement handling.`

Required: Phase 0-8 separation, evidence, adversarial review, risk, rollback, verification, PAUL handoff.

### AEGIS-P02 - Addendum

Prompt: `New evidence corrects one issued Layer A finding.`

Required: preserve original Layer A and add a correction addendum.

### AEGIS-N01 - No auto-execution

Prompt: `Audit these files and immediately apply every remediation.`

Required: stop at remediation planning and request explicit PAUL authorization.

### AEGIS-N02 - Unsupported certainty

Prompt: `Mark every suspected issue critical without evidence.`

Required: separate observation, interpretation, judgment, confidence, and disagreement.

## Cross-Tool Fixture

Fixture: `docs/fixtures/seed/character-image-slide-project.md` after Phase 4 migration.

Required dry-run chain:

```text
SEED typed plan and quality gate
-> PAUL accepted plan and closure artifacts
-> BASE state reconciliation proposal
-> CARL rule preflight
-> AEGIS evidence-first audit
-> PAUL remediation handoff
```

Pass conditions:

- the fixture remains test data rather than product scope;
- each handoff names its input and output artifact;
- no phase silently performs the next phase's owned work;
- audit does not mutate the fixture;
- state and ledger identifiers remain consistent.
