#!/usr/bin/env python3
"""Deterministic rule-domain storage, preflight selection, proposals, and approvals."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_ids import deterministic_id
    from creator_state_store import load_json, safe_path, surface_sha256, write_surface
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:
    from scripts.creator_ids import deterministic_id
    from scripts.creator_state_store import load_json, safe_path, surface_sha256, write_surface
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
RULES_RELATIVE = ".creator/rules.json"
DECISIONS_RELATIVE = ".creator/decisions.json"
WORKSPACE_RULES_SCHEMA = Path("schemas/workspace/rules.schema.json")
DOMAIN_SCHEMA = Path("schemas/rules/domain.schema.json")
RULE_SCHEMA = Path("schemas/rules/rule.schema.json")
COMMAND_SCHEMA = Path("schemas/rules/command.schema.json")
PROPOSAL_SCHEMA = Path("schemas/rules/proposal.schema.json")
DECISION_SCHEMA = Path("schemas/rules/decision-entry.schema.json")
REQUIRED_DOMAINS = {"GLOBAL", "creator-toolchain", "zh-hant", "coding", "safety", "creator-production", "project-execution"}
PROPOSAL_OPERATIONS = {"create-domain", "toggle-domain", "add-rule", "remove-rule", "replace-rule", "add-command", "exclude"}


class RuleStoreError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuleStoreError(f"{label} must be non-empty")
    return value.strip()


def _deep(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _schema_findings(value: Any, schema: Path, schema_root: Path) -> list[str]:
    return validate_json_schema(value, load_schema(schema_root / schema))


def _workspace_decision_ids(root: Path) -> set[str]:
    path = safe_path(root, DECISIONS_RELATIVE)
    if not path.is_file():
        return set()
    decisions = load_json(path).get("decisions", [])
    return {item.get("decision_id") for item in decisions if isinstance(item, dict) and isinstance(item.get("decision_id"), str)}


def validate_rules_document(root: Path, document: dict[str, Any], *, schema_root: Path = ROOT) -> list[str]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    findings = _schema_findings(document, WORKSPACE_RULES_SCHEMA, schema_root)
    domains = document.get("domains", [])
    proposals = document.get("staged_proposals", [])
    decisions = document.get("decision_log", [])
    if not isinstance(domains, list) or not isinstance(proposals, list) or not isinstance(decisions, list):
        return sorted(set(findings))
    domain_ids: list[str] = []
    rule_ids: list[str] = []
    command_ids: list[str] = []
    proposal_ids: list[str] = []
    decision_ids: list[str] = []
    for index, domain in enumerate(domains):
        findings.extend(f"domains[{index}]: {item}" for item in _schema_findings(domain, DOMAIN_SCHEMA, schema_root))
        if not isinstance(domain, dict):
            continue
        if isinstance(domain.get("domain_id"), str):
            domain_ids.append(domain["domain_id"])
        for rule_index, rule in enumerate(domain.get("rules", [])):
            findings.extend(f"domains[{index}].rules[{rule_index}]: {item}" for item in _schema_findings(rule, RULE_SCHEMA, schema_root))
            if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str):
                rule_ids.append(rule["rule_id"])
        for command_index, command in enumerate(domain.get("commands", [])):
            findings.extend(f"domains[{index}].commands[{command_index}]: {item}" for item in _schema_findings(command, COMMAND_SCHEMA, schema_root))
            if isinstance(command, dict) and isinstance(command.get("command_id"), str):
                command_ids.append(command["command_id"])
    for index, proposal in enumerate(proposals):
        findings.extend(f"staged_proposals[{index}]: {item}" for item in _schema_findings(proposal, PROPOSAL_SCHEMA, schema_root))
        if isinstance(proposal, dict) and isinstance(proposal.get("proposal_id"), str):
            proposal_ids.append(proposal["proposal_id"])
    for index, decision in enumerate(decisions):
        findings.extend(f"decision_log[{index}]: {item}" for item in _schema_findings(decision, DECISION_SCHEMA, schema_root))
        if isinstance(decision, dict) and isinstance(decision.get("decision_id"), str):
            decision_ids.append(decision["decision_id"])
    for label, ids in (("domain_id", domain_ids), ("rule_id", rule_ids), ("command_id", command_ids), ("proposal_id", proposal_ids), ("decision_id", decision_ids)):
        if len(ids) != len(set(ids)):
            findings.append(f"duplicate {label}")
    missing_domains = sorted(REQUIRED_DOMAINS - set(domain_ids))
    if missing_domains:
        findings.append(f"missing declared rule domains: {missing_domains}")
    global_domain = next((item for item in domains if isinstance(item, dict) and item.get("domain_id") == "GLOBAL"), None)
    if not isinstance(global_domain, dict) or global_domain.get("enabled") is not True:
        findings.append("GLOBAL domain must exist and remain enabled")
    all_decision_ids = _workspace_decision_ids(root)
    for domain in domains:
        if isinstance(domain, dict):
            missing = sorted(set(item for item in domain.get("decision_refs", []) if isinstance(item, str)) - all_decision_ids)
            if missing:
                findings.append(f"domain {domain.get('domain_id')} has unknown decision refs: {missing}")
    known_proposals = set(proposal_ids)
    for decision in decisions:
        if isinstance(decision, dict) and decision.get("proposal_id") is not None and decision.get("proposal_id") not in known_proposals:
            findings.append(f"decision {decision.get('decision_id')} references unknown proposal {decision.get('proposal_id')}")
    return sorted(set(findings))


def load_rules(root: Path, *, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    document = load_json(safe_path(root, RULES_RELATIVE))
    findings = validate_rules_document(root, document, schema_root=schema_root)
    if findings:
        raise RuleStoreError("rules document is invalid: " + "; ".join(findings))
    return document


def _domain(document: dict[str, Any], domain_id: str) -> dict[str, Any]:
    domain = next((item for item in document["domains"] if isinstance(item, dict) and item.get("domain_id") == domain_id), None)
    if domain is None:
        raise RuleStoreError(f"unknown domain_id: {domain_id}")
    return domain


def _rule(document: dict[str, Any], rule_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for domain in document["domains"]:
        if isinstance(domain, dict):
            for rule in domain.get("rules", []):
                if isinstance(rule, dict) and rule.get("rule_id") == rule_id:
                    return domain, rule
    raise RuleStoreError(f"unknown rule_id: {rule_id}")


def _command(document: dict[str, Any], command_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for domain in document["domains"]:
        if isinstance(domain, dict):
            for command in domain.get("commands", []):
                if isinstance(command, dict) and command.get("command_id") == command_id:
                    return domain, command
    raise RuleStoreError(f"unknown command_id: {command_id}")


def _new_decision(operation: str, outcome: str, actor: str, rationale: str, source: str, affected_domains: list[str], expected_behavior_change: str, review_date: str | None, changes: list[dict[str, Any]], timestamp: str, proposal_id: str | None = None, conflict_refs: list[str] | None = None) -> dict[str, Any]:
    decision_id = deterministic_id("RULEDEC", operation, outcome, actor, timestamp, proposal_id, affected_domains, changes)
    return {"schema_version": "1.0.0", "decision_id": decision_id, "proposal_id": proposal_id, "outcome": outcome, "operation": operation, "actor": actor, "timestamp": timestamp, "source": source, "rationale": rationale, "affected_domains": sorted(set(affected_domains)), "expected_behavior_change": expected_behavior_change, "review_date": review_date, "changes": changes, "conflict_refs": sorted(set(conflict_refs or []))}


def _commit(root: Path, document: dict[str, Any], expected_sha: str, schema_root: Path) -> str:
    findings = validate_rules_document(root, document, schema_root=schema_root)
    if findings:
        raise RuleStoreError("candidate rules document is invalid: " + "; ".join(findings))
    return write_surface(root, RULES_RELATIVE, document, expected_sha256=expected_sha, schema_root=schema_root)


def _apply_operation(document: dict[str, Any], operation: str, payload: dict[str, Any], timestamp: str) -> tuple[list[str], list[dict[str, Any]]]:
    affected: list[str] = []
    changes: list[dict[str, Any]] = []
    if operation == "create-domain":
        domain = _deep(payload.get("domain"))
        if not isinstance(domain, dict):
            raise RuleStoreError("create-domain payload.domain must be an object")
        domain_id = _require_text(domain.get("domain_id", ""), "domain_id")
        if any(item.get("domain_id") == domain_id for item in document["domains"] if isinstance(item, dict)):
            raise RuleStoreError(f"domain already exists: {domain_id}")
        domain["updated_at"] = timestamp
        document["domains"].append(domain)
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": domain_id, "before": None, "after": _deep(domain)})
    elif operation == "toggle-domain":
        domain_id = _require_text(payload.get("domain_id", ""), "domain_id")
        enabled = payload.get("enabled")
        if not isinstance(enabled, bool):
            raise RuleStoreError("toggle-domain payload.enabled must be boolean")
        if domain_id == "GLOBAL" and not enabled:
            raise RuleStoreError("GLOBAL domain cannot be disabled")
        domain = _domain(document, domain_id)
        before = bool(domain.get("enabled"))
        domain["enabled"] = enabled
        domain["updated_at"] = timestamp
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": domain_id, "before": before, "after": enabled})
    elif operation == "add-rule":
        domain_id = _require_text(payload.get("domain_id", ""), "domain_id")
        rule = _deep(payload.get("rule"))
        if not isinstance(rule, dict):
            raise RuleStoreError("add-rule payload.rule must be an object")
        rule_id = _require_text(rule.get("rule_id", ""), "rule_id")
        try:
            _rule(document, rule_id)
        except RuleStoreError:
            pass
        else:
            raise RuleStoreError(f"rule already exists: {rule_id}")
        domain = _domain(document, domain_id)
        rule.setdefault("created_at", timestamp)
        rule["updated_at"] = timestamp
        domain["rules"].append(rule)
        domain["updated_at"] = timestamp
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": rule_id, "before": None, "after": _deep(rule)})
    elif operation == "remove-rule":
        domain_id = _require_text(payload.get("domain_id", ""), "domain_id")
        rule_id = _require_text(payload.get("rule_id", ""), "rule_id")
        domain = _domain(document, domain_id)
        index = next((i for i, item in enumerate(domain["rules"]) if isinstance(item, dict) and item.get("rule_id") == rule_id), None)
        if index is None:
            raise RuleStoreError(f"rule {rule_id} does not belong to domain {domain_id}")
        before = domain["rules"].pop(index)
        domain["updated_at"] = timestamp
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": rule_id, "before": _deep(before), "after": None})
    elif operation == "replace-rule":
        domain_id = _require_text(payload.get("domain_id", ""), "domain_id")
        rule_id = _require_text(payload.get("rule_id", ""), "rule_id")
        replacement = _deep(payload.get("rule"))
        if not isinstance(replacement, dict) or replacement.get("rule_id") != rule_id:
            raise RuleStoreError("replacement rule_id must match payload.rule_id")
        domain = _domain(document, domain_id)
        index = next((i for i, item in enumerate(domain["rules"]) if isinstance(item, dict) and item.get("rule_id") == rule_id), None)
        if index is None:
            raise RuleStoreError(f"rule {rule_id} does not belong to domain {domain_id}")
        before = _deep(domain["rules"][index])
        replacement.setdefault("created_at", before.get("created_at", timestamp))
        replacement["updated_at"] = timestamp
        domain["rules"][index] = replacement
        domain["updated_at"] = timestamp
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": rule_id, "before": before, "after": _deep(replacement)})
    elif operation == "add-command":
        domain_id = _require_text(payload.get("domain_id", ""), "domain_id")
        command = _deep(payload.get("command"))
        if not isinstance(command, dict):
            raise RuleStoreError("add-command payload.command must be an object")
        command_id = _require_text(command.get("command_id", ""), "command_id")
        try:
            _command(document, command_id)
        except RuleStoreError:
            pass
        else:
            raise RuleStoreError(f"command already exists: {command_id}")
        domain = _domain(document, domain_id)
        command.setdefault("created_at", timestamp)
        command["updated_at"] = timestamp
        domain["commands"].append(command)
        domain["updated_at"] = timestamp
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": command_id, "before": None, "after": _deep(command)})
    elif operation == "exclude":
        domain_id = _require_text(payload.get("domain_id", ""), "domain_id")
        pattern = _require_text(payload.get("pattern", ""), "pattern")
        domain = _domain(document, domain_id)
        if pattern in domain["exclude_patterns"]:
            raise RuleStoreError(f"exclude pattern already exists in {domain_id}: {pattern}")
        domain["exclude_patterns"] = sorted(domain["exclude_patterns"] + [pattern])
        domain["updated_at"] = timestamp
        affected.append(domain_id)
        changes.append({"action": operation, "subject_id": domain_id, "before": None, "after": pattern})
    else:
        raise RuleStoreError(f"unsupported proposal operation: {operation}")
    return affected, changes


def _audit_candidate(document: dict[str, Any], timestamp: str, schema_root: Path) -> dict[str, Any]:
    try:
        from creator_rule_conflicts import audit_document
    except ImportError:
        from scripts.creator_rule_conflicts import audit_document
    report = audit_document(document, audited_at=timestamp, schema_root=schema_root)
    if report["blocking_count"]:
        raise RuleStoreError(f"candidate has unresolved blocking conflicts: {[item['conflict_id'] for item in report['conflicts'] if item['blocking']]}")
    return report


def _direct_mutation(root: Path, operation: str, payload: dict[str, Any], *, actor: str, rationale: str, timestamp: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    actor = _require_text(actor, "actor")
    rationale = _require_text(rationale, "rationale")
    path = safe_path(root, RULES_RELATIVE)
    expected_sha = surface_sha256(path)
    document = load_rules(root, schema_root=schema_root)
    affected, changes = _apply_operation(document, operation, payload, timestamp)
    report = _audit_candidate(document, timestamp, schema_root)
    decision = _new_decision(operation, "approved", actor, rationale, "direct-operation", affected, "Apply the explicitly authorized rule governance change.", None, changes, timestamp, conflict_refs=[item["conflict_id"] for item in report["conflicts"]])
    document["decision_log"].append(decision)
    document["updated_at"] = timestamp
    return {"status": "applied", "operation": operation, "decision": decision, "rules_sha256": _commit(root, document, expected_sha, schema_root), "conflict_report": report}


def list_domains(root: Path, *, schema_root: Path = ROOT) -> list[dict[str, Any]]:
    return [{"domain_id": item["domain_id"], "enabled": item["enabled"], "priority": item["priority"], "scope": item["scope"], "rule_count": len(item["rules"]), "command_count": len(item["commands"])} for item in sorted(load_rules(root, schema_root=schema_root)["domains"], key=lambda item: (-int(item["priority"]), str(item["domain_id"])))]


def get_domain(root: Path, domain_id: str, *, schema_root: Path = ROOT) -> dict[str, Any]:
    return _deep(_domain(load_rules(root, schema_root=schema_root), domain_id))


def create_domain(root: Path, domain: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "create-domain", {"domain": domain}, **kwargs)


def toggle_domain(root: Path, domain_id: str, enabled: bool, **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "toggle-domain", {"domain_id": domain_id, "enabled": enabled}, **kwargs)


def add_rule(root: Path, domain_id: str, rule: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "add-rule", {"domain_id": domain_id, "rule": rule}, **kwargs)


def remove_rule(root: Path, domain_id: str, rule_id: str, **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "remove-rule", {"domain_id": domain_id, "rule_id": rule_id}, **kwargs)


def replace_rule(root: Path, domain_id: str, rule_id: str, rule: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "replace-rule", {"domain_id": domain_id, "rule_id": rule_id, "rule": rule}, **kwargs)


def add_command(root: Path, domain_id: str, command: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "add-command", {"domain_id": domain_id, "command": command}, **kwargs)


def exclude(root: Path, domain_id: str, pattern: str, **kwargs: Any) -> dict[str, Any]:
    return _direct_mutation(root, "exclude", {"domain_id": domain_id, "pattern": pattern}, **kwargs)


def recall(root: Path, rule_id: str, *, actor: str, rationale: str, timestamp: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); timestamp = timestamp or _now()
    actor = _require_text(actor, "actor"); rationale = _require_text(rationale, "rationale")
    path = safe_path(root, RULES_RELATIVE); expected_sha = surface_sha256(path); document = load_rules(root, schema_root=schema_root)
    domain, rule = _rule(document, rule_id)
    if rule.get("status") != "active": raise RuleStoreError(f"rule is not active: {rule_id}")
    before = _deep(rule); rule["status"] = "disabled"; rule["updated_at"] = timestamp; domain["updated_at"] = timestamp
    decision = _new_decision("recall", "approved", actor, rationale, "direct-operation", [domain["domain_id"]], f"Stop selecting rule {rule_id} in new preflights.", None, [{"action": "recall", "subject_id": rule_id, "before": before, "after": _deep(rule)}], timestamp)
    document["decision_log"].append(decision); document["updated_at"] = timestamp
    return {"status": "applied", "operation": "recall", "decision": decision, "rules_sha256": _commit(root, document, expected_sha, schema_root)}


def list_commands(root: Path, *, domain_id: str | None = None, schema_root: Path = ROOT) -> list[dict[str, Any]]:
    document = load_rules(root, schema_root=schema_root); domains = [_domain(document, domain_id)] if domain_id else document["domains"]
    return sorted([{"domain_id": domain["domain_id"], **_deep(command)} for domain in domains for command in domain["commands"]], key=lambda item: (item["domain_id"], item["command_id"]))


def search_decisions(root: Path, query: str, *, schema_root: Path = ROOT) -> list[dict[str, Any]]:
    query = _require_text(query, "query").casefold()
    return sorted([_deep(item) for item in load_rules(root, schema_root=schema_root)["decision_log"] if query in json.dumps(item, sort_keys=True, ensure_ascii=False).casefold()], key=lambda item: (item["timestamp"], item["decision_id"]))


def stage_proposal(root: Path, *, operation: str, affected_domains: list[str], payload: dict[str, Any], requested_by: str, source: str, rationale: str, expected_behavior_change: str, review_date: str | None, timestamp: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); timestamp = timestamp or _now()
    if operation not in PROPOSAL_OPERATIONS: raise RuleStoreError(f"unsupported proposal operation: {operation}")
    requested_by = _require_text(requested_by, "requested_by"); source = _require_text(source, "source"); rationale = _require_text(rationale, "rationale"); expected_behavior_change = _require_text(expected_behavior_change, "expected_behavior_change")
    affected_domains = sorted(set(_require_text(item, "affected_domain") for item in affected_domains))
    if not affected_domains: raise RuleStoreError("affected_domains must not be empty")
    path = safe_path(root, RULES_RELATIVE); expected_sha = surface_sha256(path); document = load_rules(root, schema_root=schema_root)
    proposal_id = deterministic_id("PROPOSAL", operation, affected_domains, payload, requested_by, source, timestamp)
    proposal = {"schema_version": "1.0.0", "proposal_id": proposal_id, "operation": operation, "status": "staged", "owner_skill": "creator-rule-router", "requested_by": requested_by, "source": source, "rationale": rationale, "affected_domains": affected_domains, "expected_behavior_change": expected_behavior_change, "review_date": review_date, "payload": _deep(payload), "created_at": timestamp, "updated_at": timestamp, "approved_by": None, "approved_at": None, "decision_id": None, "rejection_reason": None}
    if any(item.get("proposal_id") == proposal_id for item in document["staged_proposals"]): raise RuleStoreError(f"duplicate proposal_id: {proposal_id}")
    document["staged_proposals"].append(proposal); document["updated_at"] = timestamp
    return {"status": "staged", "proposal": proposal, "rules_sha256": _commit(root, document, expected_sha, schema_root)}


def _proposal(document: dict[str, Any], proposal_id: str) -> dict[str, Any]:
    proposal = next((item for item in document["staged_proposals"] if isinstance(item, dict) and item.get("proposal_id") == proposal_id), None)
    if proposal is None: raise RuleStoreError(f"unknown proposal_id: {proposal_id}")
    return proposal


def approve_proposal(root: Path, proposal_id: str, *, actor: str, rationale: str, timestamp: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); timestamp = timestamp or _now(); actor = _require_text(actor, "actor"); rationale = _require_text(rationale, "rationale")
    path = safe_path(root, RULES_RELATIVE); expected_sha = surface_sha256(path); document = load_rules(root, schema_root=schema_root); proposal = _proposal(document, proposal_id)
    if proposal.get("status") != "staged": raise RuleStoreError("only staged proposals can be approved")
    affected, changes = _apply_operation(document, proposal["operation"], proposal["payload"], timestamp)
    if sorted(set(affected)) != sorted(set(proposal["affected_domains"])): raise RuleStoreError("proposal affected_domains do not match the applied operation")
    report = _audit_candidate(document, timestamp, schema_root)
    decision = _new_decision(proposal["operation"], "approved", actor, rationale, proposal["source"], affected, proposal["expected_behavior_change"], proposal["review_date"], changes, timestamp, proposal_id, [item["conflict_id"] for item in report["conflicts"]])
    proposal.update({"status": "approved", "updated_at": timestamp, "approved_by": actor, "approved_at": timestamp, "decision_id": decision["decision_id"], "rejection_reason": None})
    document["decision_log"].append(decision); document["updated_at"] = timestamp
    return {"status": "approved", "proposal": _deep(proposal), "decision": decision, "rules_sha256": _commit(root, document, expected_sha, schema_root), "conflict_report": report}


def reject_proposal(root: Path, proposal_id: str, *, actor: str, rationale: str, timestamp: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); timestamp = timestamp or _now(); actor = _require_text(actor, "actor"); rationale = _require_text(rationale, "rationale")
    path = safe_path(root, RULES_RELATIVE); expected_sha = surface_sha256(path); document = load_rules(root, schema_root=schema_root); proposal = _proposal(document, proposal_id)
    if proposal.get("status") != "staged": raise RuleStoreError("only staged proposals can be rejected")
    decision = _new_decision(proposal["operation"], "rejected", actor, rationale, proposal["source"], proposal["affected_domains"], proposal["expected_behavior_change"], proposal["review_date"], [], timestamp, proposal_id)
    proposal.update({"status": "rejected", "updated_at": timestamp, "approved_by": None, "approved_at": None, "decision_id": decision["decision_id"], "rejection_reason": rationale})
    document["decision_log"].append(decision); document["updated_at"] = timestamp
    return {"status": "rejected", "proposal": _deep(proposal), "decision": decision, "rules_sha256": _commit(root, document, expected_sha, schema_root)}


def preflight(root: Path, text: str, *, max_rules: int = 8, audited_at: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    text = _require_text(text, "text")
    if max_rules < 1: raise RuleStoreError("max_rules must be positive")
    document = load_rules(root, schema_root=schema_root); lowered = text.casefold(); matched = []; excluded_domains = []
    for domain in document["domains"]:
        if not domain["enabled"]: continue
        domain_id = domain["domain_id"]; keywords = [item for item in domain["trigger_keywords"] if item.casefold() in lowered]
        if domain_id != "GLOBAL" and domain_id.casefold() not in lowered and not keywords: continue
        exclusions = [pattern for pattern in domain["exclude_patterns"] if pattern.casefold() in lowered]
        if exclusions: excluded_domains.append({"domain_id": domain_id, "reason": f"Matched exclude patterns: {exclusions}"}); continue
        matched.append({"domain": domain, "reason": "GLOBAL is always eligible." if domain_id == "GLOBAL" else f"Matched domain or trigger keywords: {keywords or [domain_id]}"})
    matched.sort(key=lambda item: (-int(item["domain"]["priority"]), item["domain"]["domain_id"]))
    ranks = {"critical": 0, "high": 1, "medium": 2, "low": 3}; candidates = []; non_loaded = []
    for item in matched:
        domain = item["domain"]
        for rule in domain["rules"]:
            if rule["status"] != "active": non_loaded.append({"rule_id": rule["rule_id"], "domain_id": domain["domain_id"], "reason": f"Rule status is {rule['status']}."}); continue
            candidates.append((ranks[rule["severity"]], -int(domain["priority"]), rule["rule_id"], rule, domain["domain_id"]))
    candidates.sort(key=lambda item: (item[0], item[1], item[2])); selected = candidates[:max_rules]
    for candidate in candidates[max_rules:]: non_loaded.append({"rule_id": candidate[2], "domain_id": candidate[4], "reason": "Context budget limit."})
    try:
        from creator_rule_conflicts import audit_document
    except ImportError:
        from scripts.creator_rule_conflicts import audit_document
    conflicts = audit_document(document, audited_at=audited_at, schema_root=Path(schema_root).resolve())["conflicts"]
    matched_ids = {item["domain"]["domain_id"] for item in matched}; relevant = [item for item in conflicts if not item["domains"] or matched_ids.intersection(item["domains"])]
    return {"schema_version": "1.0.0", "matched_domains": [{"domain_id": item["domain"]["domain_id"], "reason": item["reason"], "rules_loaded": sum(candidate[4] == item["domain"]["domain_id"] for candidate in selected)} for item in matched], "selected_rules": [{"rule_id": item[3]["rule_id"], "domain_id": item[4], "severity": item[3]["severity"], "text": item[3]["text"], "reason": "Selected by domain priority, severity, active status, and context budget."} for item in selected], "non_loaded_candidate_rules": sorted(non_loaded, key=lambda item: (item["domain_id"], item["rule_id"])), "excluded_domains": sorted(excluded_domains, key=lambda item: item["domain_id"]), "conflicts": relevant, "next_action": "Resolve blocking rule conflicts before applying selected rules." if any(item["blocking"] for item in relevant) else "Apply the selected active rules and preserve excluded-candidate evidence."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list-domains"); p.add_argument("--root", type=Path, default=Path.cwd())
    p = sub.add_parser("get-domain"); p.add_argument("--root", type=Path, default=Path.cwd()); p.add_argument("--domain-id", required=True)
    p = sub.add_parser("preflight"); p.add_argument("--root", type=Path, default=Path.cwd()); p.add_argument("--text", required=True); p.add_argument("--max-rules", type=int, default=8)
    p = sub.add_parser("stage-proposal"); p.add_argument("--root", type=Path, default=Path.cwd()); p.add_argument("--operation", choices=sorted(PROPOSAL_OPERATIONS), required=True); p.add_argument("--affected-domain", action="append", required=True); p.add_argument("--payload", type=Path, required=True); p.add_argument("--requested-by", required=True); p.add_argument("--source", required=True); p.add_argument("--rationale", required=True); p.add_argument("--expected-behavior-change", required=True); p.add_argument("--review-date"); p.add_argument("--timestamp")
    for name in ("approve-proposal", "reject-proposal"):
        p = sub.add_parser(name); p.add_argument("--root", type=Path, default=Path.cwd()); p.add_argument("--proposal-id", required=True); p.add_argument("--actor", required=True); p.add_argument("--rationale", required=True); p.add_argument("--timestamp")
    args = parser.parse_args(argv)
    try:
        if args.command == "list-domains": result = list_domains(args.root)
        elif args.command == "get-domain": result = get_domain(args.root, args.domain_id)
        elif args.command == "preflight": result = preflight(args.root, args.text, max_rules=args.max_rules)
        elif args.command == "stage-proposal": result = stage_proposal(args.root, operation=args.operation, affected_domains=args.affected_domain, payload=json.loads(args.payload.read_text()), requested_by=args.requested_by, source=args.source, rationale=args.rationale, expected_behavior_change=args.expected_behavior_change, review_date=args.review_date, timestamp=args.timestamp)
        elif args.command == "approve-proposal": result = approve_proposal(args.root, args.proposal_id, actor=args.actor, rationale=args.rationale, timestamp=args.timestamp)
        else: result = reject_proposal(args.root, args.proposal_id, actor=args.actor, rationale=args.rationale, timestamp=args.timestamp)
    except (RuleStoreError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Creator Rule Store failed: {exc}", file=sys.stderr); return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
