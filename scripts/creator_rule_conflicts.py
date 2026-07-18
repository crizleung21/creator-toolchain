#!/usr/bin/env python3
"""Deterministic semantic conflict audit for Creator Toolchain rule governance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_ids import deterministic_id
    from creator_state_store import load_json, safe_path
    from creator_transactions import atomic_write_json
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_rule_conflicts in tests.
    from scripts.creator_ids import deterministic_id
    from scripts.creator_state_store import load_json, safe_path
    from scripts.creator_transactions import atomic_write_json
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
RULES_RELATIVE = ".creator/rules.json"
CONFLICT_REPORT_RELATIVE = Path(".creator/rule-conflicts/conflict-report.json")
CONFLICT_REPORT_SCHEMA = Path("schemas/rules/conflict-report.schema.json")
BLOCKING_TYPES = {"duplicate", "contradiction", "unsafe_rule", "duplicate_command"}
NEGATION_TOKENS = (" must not ", " may not ", " do not ", " don't ", " never ", " cannot ", " can't ", " no ")


class RuleConflictError(RuntimeError):
    """Raised when a rule conflict report cannot be produced safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize(text: str) -> str:
    value = " " + re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip() + " "
    return re.sub(r"\s+", " ", value)


def _polarity(text: str) -> tuple[str, bool]:
    normalized = _normalize(text)
    negative = any(token in normalized for token in NEGATION_TOKENS)
    base = normalized
    for token in NEGATION_TOKENS:
        base = base.replace(token, " ")
    base = re.sub(r"\b(?:must|may|should|can|always)\b", " ", base)
    return re.sub(r"\s+", " ", base).strip(), negative


def _conflict(
    conflict_type: str,
    severity: str,
    message: str,
    *,
    domains: list[str] | None = None,
    rule_ids: list[str] | None = None,
    command_ids: list[str] | None = None,
    decision_refs: list[str] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    domains = sorted(set(domains or []))
    rule_ids = sorted(set(rule_ids or []))
    command_ids = sorted(set(command_ids or []))
    decision_refs = sorted(set(decision_refs or []))
    evidence = sorted(set(evidence or []))
    conflict_id = deterministic_id(
        "CONFLICT",
        conflict_type,
        domains,
        rule_ids,
        command_ids,
        decision_refs,
        message,
    )
    return {
        "conflict_id": conflict_id,
        "conflict_type": conflict_type,
        "severity": severity,
        "blocking": conflict_type in BLOCKING_TYPES,
        "status": "unresolved",
        "domains": domains,
        "rule_ids": rule_ids,
        "command_ids": command_ids,
        "decision_refs": decision_refs,
        "message": message,
        "evidence": evidence,
    }


def _validate_report(report: dict[str, Any], schema_root: Path) -> None:
    findings = validate_json_schema(report, load_schema(Path(schema_root).resolve() / CONFLICT_REPORT_SCHEMA))
    if findings:
        raise RuleConflictError("conflict report failed schema validation: " + "; ".join(findings))


def audit_document(
    document: dict[str, Any],
    *,
    audited_at: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    audited_at = audited_at or _now()
    now = _parse_time(audited_at)
    if now is None:
        raise RuleConflictError("audited_at must be ISO-8601")
    domains = document.get("domains", [])
    if not isinstance(domains, list):
        raise RuleConflictError("rules domains must be an array")

    conflicts: list[dict[str, Any]] = []
    rules: list[tuple[str, dict[str, Any]]] = []
    commands: list[tuple[str, dict[str, Any]]] = []

    for domain in domains:
        if not isinstance(domain, dict):
            continue
        domain_id = str(domain.get("domain_id", ""))
        for rule in domain.get("rules", []):
            if isinstance(rule, dict):
                rules.append((domain_id, rule))
        for command in domain.get("commands", []):
            if isinstance(command, dict):
                commands.append((domain_id, command))

    by_rule_id: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    by_text: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for domain_id, rule in rules:
        rule_id = str(rule.get("rule_id", ""))
        by_rule_id.setdefault(rule_id, []).append((domain_id, rule))
        if rule.get("status", "active") == "active":
            by_text.setdefault(_normalize(str(rule.get("text", ""))), []).append((domain_id, rule))
    for rule_id, items in sorted(by_rule_id.items()):
        if rule_id and len(items) > 1:
            conflicts.append(
                _conflict(
                    "duplicate",
                    "critical",
                    f"Rule ID {rule_id} appears more than once.",
                    domains=[item[0] for item in items],
                    rule_ids=[rule_id],
                    evidence=[str(item[1].get("text", "")) for item in items],
                )
            )
    for normalized, items in sorted(by_text.items()):
        ids = [str(item[1].get("rule_id", "")) for item in items]
        if normalized and len(set(ids)) > 1:
            conflicts.append(
                _conflict(
                    "duplicate",
                    "high",
                    "Active rules contain duplicate normalized text.",
                    domains=[item[0] for item in items],
                    rule_ids=ids,
                    evidence=[str(item[1].get("text", "")) for item in items],
                )
            )

    polarity_groups: dict[str, list[tuple[str, dict[str, Any], bool]]] = {}
    for domain_id, rule in rules:
        if rule.get("status", "active") != "active":
            continue
        base, negative = _polarity(str(rule.get("text", "")))
        if base:
            polarity_groups.setdefault(base, []).append((domain_id, rule, negative))
    for base_text, items in sorted(polarity_groups.items()):
        if len({item[2] for item in items}) > 1:
            conflicts.append(
                _conflict(
                    "contradiction",
                    "critical",
                    f"Rules express opposite polarity for: {base_text}.",
                    domains=[item[0] for item in items],
                    rule_ids=[str(item[1].get("rule_id", "")) for item in items],
                    evidence=[str(item[1].get("text", "")) for item in items],
                )
            )

    enabled = [item for item in domains if isinstance(item, dict) and item.get("enabled") is True]
    for index, first in enumerate(enabled):
        for second in enabled[index + 1 :]:
            first_id = str(first.get("domain_id", ""))
            second_id = str(second.get("domain_id", ""))
            if "GLOBAL" in {first_id, second_id}:
                continue
            first_triggers = {str(item).casefold() for item in first.get("trigger_keywords", [])}
            second_triggers = {str(item).casefold() for item in second.get("trigger_keywords", [])}
            shared = sorted(first_triggers & second_triggers)
            same_scope = str(first.get("scope", "")).casefold() == str(second.get("scope", "")).casefold()
            if shared or same_scope:
                conflicts.append(
                    _conflict(
                        "scope_overlap",
                        "medium",
                        f"Domains {first_id} and {second_id} overlap in scope or triggers.",
                        domains=[first_id, second_id],
                        evidence=shared or [str(first.get("scope", ""))],
                    )
                )

    unsafe_terms = (
        "bypass approval",
        "silently mutate",
        "delete without",
        "disable validation",
        "ignore safety",
        "skip verification",
    )
    for domain_id, rule in rules:
        if rule.get("status", "active") != "active":
            continue
        rule_id = str(rule.get("rule_id", ""))
        review_date = _parse_time(rule.get("review_date"))
        if review_date is not None and review_date < now:
            conflicts.append(
                _conflict(
                    "stale_rule",
                    "medium",
                    f"Rule {rule_id} passed its review date.",
                    domains=[domain_id],
                    rule_ids=[rule_id],
                    evidence=[str(rule.get("review_date"))],
                )
            )
        scope = str(rule.get("scope", "")).strip().casefold()
        text = str(rule.get("text", ""))
        if domain_id != "GLOBAL" and (scope in {"*", "all", "everything", "any task"} or " always " in _normalize(text)):
            conflicts.append(
                _conflict(
                    "overbroad_rule",
                    "medium",
                    f"Rule {rule_id} may be broader than its domain.",
                    domains=[domain_id],
                    rule_ids=[rule_id],
                    evidence=[text],
                )
            )
        lowered = text.casefold()
        matched: list[str] = []
        for term in unsafe_terms:
            if term not in lowered:
                continue
            prohibited_forms = (
                f"do not {term}",
                f"must not {term}",
                f"never {term}",
                f"cannot {term}",
            )
            if any(form in lowered for form in prohibited_forms):
                continue
            matched.append(term)
        if matched:
            conflicts.append(
                _conflict(
                    "unsafe_rule",
                    "critical",
                    f"Rule {rule_id} contains an unsafe governance instruction.",
                    domains=[domain_id],
                    rule_ids=[rule_id],
                    evidence=matched,
                )
            )

    by_command_id: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    by_command_key: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}
    for domain_id, command in commands:
        command_id = str(command.get("command_id", ""))
        by_command_id.setdefault(command_id, []).append((domain_id, command))
        if command.get("status", "active") == "active":
            key = (_normalize(str(command.get("trigger", ""))), str(command.get("workflow", "")).strip())
            by_command_key.setdefault(key, []).append((domain_id, command))
    for command_id, items in sorted(by_command_id.items()):
        if command_id and len(items) > 1:
            conflicts.append(
                _conflict(
                    "duplicate_command",
                    "critical",
                    f"Command ID {command_id} appears more than once.",
                    domains=[item[0] for item in items],
                    command_ids=[command_id],
                )
            )
    for key, items in sorted(by_command_key.items()):
        ids = [str(item[1].get("command_id", "")) for item in items]
        if key[0] and len(set(ids)) > 1:
            conflicts.append(
                _conflict(
                    "duplicate_command",
                    "high",
                    "Active commands share the same trigger and workflow.",
                    domains=[item[0] for item in items],
                    command_ids=ids,
                    evidence=[f"trigger={key[0].strip()}", f"workflow={key[1]}"],
                )
            )

    for decision in document.get("decision_log", []):
        if not isinstance(decision, dict):
            continue
        review_date = _parse_time(decision.get("review_date"))
        if review_date is not None and review_date < now:
            decision_id = str(decision.get("decision_id", ""))
            conflicts.append(
                _conflict(
                    "stale_decision",
                    "low",
                    f"Decision {decision_id} passed its review date.",
                    decision_refs=[decision_id],
                    evidence=[str(decision.get("review_date"))],
                )
            )

    unique = {item["conflict_id"]: item for item in conflicts}
    ordered = sorted(
        unique.values(),
        key=lambda item: (not item["blocking"], item["conflict_type"], item["conflict_id"]),
    )
    report = {
        "schema_version": "1.0.0",
        "audited_at": audited_at,
        "status": "BLOCKED"
        if any(item["blocking"] for item in ordered)
        else "PASS_WITH_ADVISORIES"
        if ordered
        else "PASS",
        "blocking_count": sum(bool(item["blocking"]) for item in ordered),
        "advisory_count": sum(not bool(item["blocking"]) for item in ordered),
        "conflicts": ordered,
    }
    _validate_report(report, schema_root)
    return report


def audit_rules(
    root: Path,
    *,
    audited_at: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    document = load_json(safe_path(root, RULES_RELATIVE))
    return audit_document(document, audited_at=audited_at, schema_root=Path(schema_root).resolve())


def write_conflict_report(
    root: Path,
    report: dict[str, Any],
    *,
    schema_root: Path = ROOT,
) -> str:
    """Persist derived conflict evidence without mutating the Rule surface."""

    root = Path(root).resolve()
    _validate_report(report, Path(schema_root).resolve())
    path = safe_path(root, CONFLICT_REPORT_RELATIVE)
    atomic_write_json(path, report, mode=0o600)
    return CONFLICT_REPORT_RELATIVE.as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--audited-at")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = audit_rules(args.root, audited_at=args.audited_at)
        if args.write:
            write_conflict_report(args.root, report)
    except (RuleConflictError, OSError, ValueError) as exc:
        print(f"Rule conflict audit failed: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if report["blocking_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
