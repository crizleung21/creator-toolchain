# Creator Toolchain Implementation Checklist

This checklist tracks execution of `IMPLEMENTATION_PLAN.v0.4.1.md`.

## Phase 1 — MVP Skill Suite

- [x] `AGENTS.md`
- [x] `README.md`
- [x] `.agents/skills/creator-orchestrator/`
- [x] `.agents/skills/creator-seed-incubator/`
- [x] `.agents/skills/creator-paul-loop/`
- [x] Phase 1 test prompts
- [x] Phase 1 acceptance checklist
- [x] Character Image Slide Project fixture
- [x] Minimal `.creator/projects.json`
- [x] Minimal plan manifest and activity ledger template

## Phase 2 — State Layer

- [x] `.creator/workspace.json`
- [x] `.creator/projects.json`
- [x] `.creator/entities.json`
- [x] `.creator/state.json`
- [x] `.creator/psmm.json`
- [x] `.creator/operator.json`
- [x] `.creator/backlog.json`
- [x] `.creator/surfaces.json`
- [x] `.creator/decisions.json`
- [x] `creator-base-workspace`

## Phase 3 — Rules + Skill Factory

- [x] `.creator/rules.json`
- [x] `GLOBAL` domain
- [x] recall / exclude policy
- [x] command registry policy
- [x] decision log and proposal staging
- [x] `creator-rule-router`
- [x] `creator-skillsmith-factory`

## Phase 4 — Audit

- [x] `creator-aegis-audit`
- [x] AEGIS Phase 0-8 model
- [x] Layer A/B/C artifacts
- [x] remediation type and intervention level separated
- [x] PAUL-ready handoff contract

## Phase 5 — Plugin Package

- [x] `plugin/creator-toolchain/.codex-plugin/plugin.json`
- [x] plugin skills copied from local skill suite
- [x] plugin README
- [x] release evidence placeholders
- [x] packaging privacy gates

## Verification

- [x] `python3 scripts/validate_creator_toolchain.py` passes
- [x] package contents audit confirms no private state or research clones are bundled
- [x] Codex CLI temporary marketplace discovery and install smoke test passes
- [x] Codex debug prompt-input exposes all seven skill names
- [ ] repeat UI skill-selection test before public release
