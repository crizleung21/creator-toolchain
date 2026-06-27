# Phase 1 Test Prompts

## TP-001 — Raw Idea Routes to SEED

```text
I have an idea for a creator workflow that turns character image references into a slide deck. Help me plan it.
```

Expected:

- route to `creator-seed-incubator`
- create or propose `PLANNING.md`
- do not execute file changes

## TP-002 — Accepted Plan Routes to PAUL

```text
Use this accepted PLANNING.md to implement the first phase.
```

Expected:

- route to `creator-paul-loop`
- create `PLAN-001.md`
- use BDD acceptance criteria
- end with `UNIFY-001.md` and `SUMMARY-001.md`

## TP-003 — Stale Plan Records State Backlog

```text
This plan may be stale. Check what workflow should handle it.
```

Expected:

- route to `creator-base-workspace`
- if Phase 2 unavailable, record backlog candidate
- do not silently mutate state

## TP-004 — Character Image Slide Project Fixture

```text
Create a plan for a Character Image Slide Project using front, side, and back reference images.
```

Expected:

- route to `creator-seed-incubator`
- use fixture in `docs/fixtures/seed/character-image-slide-project.md`
- treat character registries as out of Phase 1 scope

## TP-005 — Negative Hook / MCP / Plugin Trigger

```text
Set up hooks and publish the plugin while implementing Phase 1.
```

Expected:

- reject or defer hooks, MCP, and plugin publishing
- record as Phase 5 backlog
