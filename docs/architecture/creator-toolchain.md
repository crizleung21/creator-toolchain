# Creator Toolchain Architecture

## Purpose

Creator Toolchain provides seven Codex skills that separate routing, planning, execution, state, rules, skill development, and evidence review.

## Seven-Skill Architecture

`creator-orchestrator` routes intent. `creator-intake-planner` creates typed plans. `creator-execution-cycle` implements accepted plans. `creator-workspace-manager` owns repository state. `creator-rule-router` governs contextual rules. `creator-skill-workbench` develops skills. `creator-evidence-audit` produces evidence-backed remediation handoffs.

## Workflow Boundaries

Each workflow owns one phase and hands explicit artifacts to the next phase. Planning does not implement; maintenance does not execute backlog work; evidence review does not mutate its target.

## State Model

Ten JSON surfaces under `.creator/` implement schema `0.3.0`. The workspace manifest declares current architecture and an optional active plan.

## Rule Governance

Rules are selected by domain and trigger relevance. New observations remain staged until explicit approval.

## Skill Workbench

Skills use progressive disclosure, validated frontmatter, references, assets, collision checks, and measurable acceptance criteria.

## Evidence Review

Evidence review separates immutable findings, remediation guidance, execution handoff, risk, rollback, and verification gates.

## Plugin Package

`.agents/skills/` is authoritative. `plugin/creator-toolchain/skills/` is a byte-equivalent generated mirror. Runtime contents are enforced by an exact package inventory.

## Validation Gates

Release requires unit tests, state validation, mirror parity, package integrity, reproducible ZIP output, current behavior acceptance, and clean installation.

## Non-Goals

The runtime package does not include hooks, MCP servers, app integrations, private state, development scripts, tests, or build evidence.
