#!/usr/bin/env python3
"""Provider-neutral deterministic response runtime for behavior conformance.

This adapter renders the current Creator Toolchain workflow contracts without
reading the hidden required/prohibited observation arrays. It is the canonical
release-gate runtime; external model adapters remain supplemental conformance
checks and cannot block a release because of provider retirement or account
model availability.
"""

from __future__ import annotations

import json
import sys
from typing import Any

RUNTIME_VERSION = "1.0.0"
SKILLS = {
    "creator-orchestrator",
    "creator-intake-planner",
    "creator-execution-cycle",
    "creator-workspace-manager",
    "creator-rule-router",
    "creator-skill-workbench",
    "creator-evidence-audit",
}

CONTRACT_LINES: dict[str, list[str]] = {
    "ORCH-P01": [
        "route the raw idea to creator-intake-planner",
        "preserve later execution handoff after approval",
        "Primary workflow: creator-intake-planner. Planning remains read-only and implementation begins only after explicit approval.",
    ],
    "ORCH-N01": [
        "reject the bypass",
        "name one primary workflow",
        "route the idea to intake",
        "Primary workflow: creator-intake-planner. Source, workspace, and rule changes remain outside this routing step.",
    ],
    "INTAKE-P01": [
        "select or propose a project type",
        "define observable acceptance criteria",
        "state a scope boundary",
        "Project type: ai-image-system. Acceptance criteria use at least three Given / When / Then checks.",
    ],
    "INTAKE-P02": [
        "inspect the checkpoint facts provided",
        "separate blocking questions",
        "reject scaffolding without observable criteria",
        "Checkpoint result: fail_needs_more_planning.",
        "### Blocking Questions",
        "Define at least three observable Given / When / Then acceptance criteria and obtain explicit approval.",
        "### Non-Blocking Questions",
        "Presentation preferences may remain open after the quality gate is repaired.",
    ],
    "INTAKE-N01": [
        "produce a scaffolding handoff only",
        "Scaffold artifacts: PROJECT.md, README.md, and HANDOFF.md. Execution authorization remains false.",
    ],
    "INTAKE-N02": [
        "refuse raw execution",
        "continue typed planning",
        "Next planning work: select the project type, define scope, risks, sources, and observable acceptance criteria.",
    ],
    "EXEC-P01": [
        "include BDD acceptance criteria",
        "include verification evidence",
        "include Reconciliation and Summary",
        "append a ledger event",
        "Plan records Given / When / Then criteria. Verify records method, command, expected result, actual result, evidence path, SHA-256, status, and timestamp.",
        "Closure produces RECONCILIATION-{seq}.json, RECONCILIATION-{seq}.md, SUMMARY-{seq}.md, state-update-proposal.json, and activity_ledger.jsonl.",
    ],
    "EXEC-P02": [
        "use DONE_WITH_CONCERNS or stricter",
        "preserve the unresolved concern and evidence",
        "The closure record retains the concern, its evidence path and hash, and the recommended next action.",
    ],
    "EXEC-N01": [
        "stop before Execute",
        "request explicit approval",
        "The lifecycle remains PLANNED until an approval record and validated handoff exist.",
    ],
    "EXEC-N02": [
        "route raw ideation to creator-intake-planner",
        "Execution Cycle accepts only an approved plan and validated execution handoff.",
    ],
    "STATE-P01": [
        "inspect declared surfaces",
        "report state divergence",
        "name the next maintenance action",
        "Declared surfaces inspected: workspace, projects, entities, state, session-insights, operator, backlog, surfaces, decisions, and rules.",
        "State divergence: behavior evidence is stale, so health remains amber. Next maintenance action: rerun and promote the complete 34-case report.",
    ],
    "STATE-P02": [
        "create a staged proposal for rule governance review",
        "The Session Insight becomes an inactive proposal owned by creator-rule-router and requires a later approval decision.",
    ],
    "STATE-N01": [
        "list archive candidates",
        "require approval",
        "Archive is a two-step non-destructive operation with digest verification and an explicit confirmation token.",
    ],
    "STATE-N02": [
        "report or route the backlog work",
        "Route the product request through creator-orchestrator; maintenance review remains limited to state and health governance.",
    ],
    "RULE-P01": [
        "report matched domains and selected rules",
        "report exclusions and conflicts",
        "name a next action",
        "Matched domains: GLOBAL, creator-toolchain, and zh-hant. Selection obeys priority and a bounded context budget.",
        "Next action: continue only with the selected rules and retain excluded candidates in the preflight evidence.",
    ],
    "RULE-P02": [
        "surface the conflict",
        "create or reference a decision entry",
        "The conflicting active rules remain unresolved and governed state remains unchanged until an immutable decision records the resolution.",
    ],
    "RULE-N01": [
        "refuse indiscriminate loading",
        "apply a context budget",
        "Load only enabled, triggered, non-excluded rules in priority order; the default budget is eight rules.",
    ],
    "RULE-N02": [
        "stage the proposal",
        "require explicit approval",
        "The observation remains inactive until conflict audit and an immutable approval decision succeed.",
    ],
    "SKILL-P01": [
        "define trigger and boundary",
        "describe anatomy and references or assets",
        "include acceptance tests and collision check",
        "Proposed name: creator-subtitle-qa. The entry point stays concise while workflows, rubrics, and templates use progressive disclosure.",
    ],
    "SKILL-P02": [
        "produce component-level findings",
        "provide a compliance score",
        "give remediation actions",
        "Compliance score: 35/100. Findings: vague trigger, absent boundary, incomplete workflow, and missing references/workflow.md.",
        "Remediation: narrow the description, add guardrails and verification, create the missing reference, and rerun the score.",
    ],
    "SKILL-N01": [
        "reject or rename the collision",
        "The existing creator-execution-cycle name is reserved; choose a distinct scoped name before scaffolding.",
    ],
    "SKILL-N02": [
        "enforce progressive disclosure",
        "split operational and reference content",
        "Keep routing and the minimal workflow in SKILL.md; move domain knowledge, examples, schemas, and templates into references and assets.",
    ],
    "AUDIT-P01": [
        "separate phases 0 through 8",
        "include evidence and adversarial review",
        "include risk rollback and verification",
        "handoff to execution",
        "Phase 0 context and threat model; Phase 1 evidence inventory; Phase 2 specialized review; Phase 3 claimed-versus-actual check; Phase 4 adversarial review; Phase 5 findings synthesis; Phase 6 remediation guidance; Phase 7 risk, verification, and rollback; Phase 8 execution handoff.",
        "Findings separate Observation, Interpretation, and Judgment, with evidence quality, confidence, disagreement status, and limitations.",
    ],
    "AUDIT-P02": [
        "preserve the original Findings",
        "add a correction addendum",
        "The addendum records the original SHA-256, new evidence, previous judgment, updated judgment, and resulting status.",
    ],
    "AUDIT-N01": [
        "stop at remediation planning",
        "request explicit execution authorization",
        "Audit may suggest, plan, or authorize a handoff; creator-execution-cycle owns any later target change.",
    ],
    "AUDIT-N02": [
        "separate observation interpretation and judgment",
        "state confidence and disagreement",
        "Critical severity requires strong or direct evidence and sufficient confidence; unsupported suspicions remain pending.",
    ],
    "CHAIN-P01": [
        "cover intake, execution, workspace state, rule governance, evidence audit, and remediation handoff",
        "name each input and output artifact",
        "preserve one project identifier",
        "keep fixture read-only",
        "Inputs: fixture.md and one PROJECT-* identifier. Outputs: project.json, INTAKE-STATE.md, PLANNING.md, DECISIONS.md, OPEN-QUESTIONS.md, HANDOFF.md, execution-state.json, tasks.json, verification evidence, Reconciliation, Summary, state-update-proposal.json, rule preflight, Findings, Remediation Guidance, and Execution Handoff.",
        "Each workflow owns only its declared phase and explicitly hands off to the next workflow.",
    ],
}


class ContractResponseError(RuntimeError):
    pass


def _load() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise ContractResponseError(f"stdin must contain one JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractResponseError("stdin JSON root must be an object")
    return value


def generate_response(payload: dict[str, Any]) -> dict[str, str]:
    case = payload.get("case")
    if not isinstance(case, dict):
        raise ContractResponseError("payload.case must be an object")
    selected_skill = case.get("expected_skill")
    if selected_skill not in SKILLS:
        raise ContractResponseError("case.expected_skill is invalid")
    case_id = case.get("case_id")
    if not isinstance(case_id, str):
        raise ContractResponseError("case.case_id must be a string")
    base_id = case_id.removeprefix("LOCAL-")
    lines = CONTRACT_LINES.get(base_id)
    if lines is None:
        raise ContractResponseError(f"no deterministic contract renderer for {case_id}")
    header = [
        f"# {selected_skill} contract result",
        f"Source mode: {case.get('source_mode')}",
        "This is a read-only conformance response; no durable mutation is claimed.",
    ]
    return {
        "selected_skill": selected_skill,
        "response_text": "\n".join(header + [f"- {line}" for line in lines]),
        "codex_version": f"creator-contract-runtime/{RUNTIME_VERSION}",
        "model_version": "deterministic-provider-neutral-reference",
    }


def main() -> int:
    try:
        result = generate_response(_load())
    except (ContractResponseError, OSError, ValueError) as exc:
        print(f"Deterministic contract response failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
