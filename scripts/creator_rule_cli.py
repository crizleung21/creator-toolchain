#!/usr/bin/env python3
"""Complete command-line interface for Creator Toolchain Rule Governance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from creator_rule_conflicts import audit_rules, write_conflict_report
    from creator_rule_store import (
        PROPOSAL_OPERATIONS,
        RuleStoreError,
        add_command,
        add_rule,
        approve_proposal,
        create_domain,
        exclude,
        get_domain,
        list_commands,
        list_domains,
        preflight,
        recall,
        reject_proposal,
        remove_rule,
        replace_rule,
        search_decisions,
        stage_proposal,
        toggle_domain,
    )
except ImportError:
    from scripts.creator_rule_conflicts import audit_rules, write_conflict_report
    from scripts.creator_rule_store import (
        PROPOSAL_OPERATIONS,
        RuleStoreError,
        add_command,
        add_rule,
        approve_proposal,
        create_domain,
        exclude,
        get_domain,
        list_commands,
        list_domains,
        preflight,
        recall,
        reject_proposal,
        remove_rule,
        replace_rule,
        search_decisions,
        stage_proposal,
        toggle_domain,
    )


class RuleCliError(RuntimeError):
    """Raised when CLI input cannot be converted into a governed operation."""


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleCliError(f"cannot load {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuleCliError(f"{label} must contain a JSON object")
    return value


def _enabled(value: str) -> bool:
    normalized = value.casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("enabled must be true or false")


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=Path.cwd())


def _add_governance_actor(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--actor", required=True)
    parser.add_argument("--rationale", required=True)
    parser.add_argument("--timestamp")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    child = sub.add_parser("list-domains")
    _add_root(child)

    child = sub.add_parser("get-domain")
    _add_root(child)
    child.add_argument("--domain-id", required=True)

    child = sub.add_parser("preflight")
    _add_root(child)
    child.add_argument("--text", required=True)
    child.add_argument("--max-rules", type=int, default=8)
    child.add_argument("--audited-at")

    child = sub.add_parser("create-domain")
    _add_root(child)
    child.add_argument("--domain", type=Path, required=True)
    _add_governance_actor(child)

    child = sub.add_parser("toggle-domain")
    _add_root(child)
    child.add_argument("--domain-id", required=True)
    child.add_argument("--enabled", type=_enabled, required=True)
    _add_governance_actor(child)

    child = sub.add_parser("add-rule")
    _add_root(child)
    child.add_argument("--domain-id", required=True)
    child.add_argument("--rule", type=Path, required=True)
    _add_governance_actor(child)

    child = sub.add_parser("remove-rule")
    _add_root(child)
    child.add_argument("--domain-id", required=True)
    child.add_argument("--rule-id", required=True)
    _add_governance_actor(child)

    child = sub.add_parser("replace-rule")
    _add_root(child)
    child.add_argument("--domain-id", required=True)
    child.add_argument("--rule-id", required=True)
    child.add_argument("--rule", type=Path, required=True)
    _add_governance_actor(child)

    child = sub.add_parser("stage-proposal")
    _add_root(child)
    child.add_argument("--operation", choices=sorted(PROPOSAL_OPERATIONS), required=True)
    child.add_argument("--affected-domain", action="append", required=True)
    child.add_argument("--payload", type=Path, required=True)
    child.add_argument("--requested-by", required=True)
    child.add_argument("--source", required=True)
    child.add_argument("--rationale", required=True)
    child.add_argument("--expected-behavior-change", required=True)
    child.add_argument("--review-date")
    child.add_argument("--timestamp")

    for command in ("approve-proposal", "reject-proposal"):
        child = sub.add_parser(command)
        _add_root(child)
        child.add_argument("--proposal-id", required=True)
        _add_governance_actor(child)

    child = sub.add_parser("recall")
    _add_root(child)
    child.add_argument("--rule-id", required=True)
    _add_governance_actor(child)

    child = sub.add_parser("exclude")
    _add_root(child)
    child.add_argument("--domain-id", required=True)
    child.add_argument("--pattern", required=True)
    _add_governance_actor(child)

    child = sub.add_parser("list-commands")
    _add_root(child)
    child.add_argument("--domain-id")

    child = sub.add_parser("add-command")
    _add_root(child)
    child.add_argument("--domain-id", required=True)
    child.add_argument("--command-file", type=Path, required=True)
    _add_governance_actor(child)

    child = sub.add_parser("search-decisions")
    _add_root(child)
    child.add_argument("--query", required=True)

    child = sub.add_parser("audit-conflicts")
    _add_root(child)
    child.add_argument("--audited-at")
    child.add_argument("--write", action="store_true")
    child.add_argument("--report", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    exit_code = 0
    try:
        if args.command == "list-domains":
            result = list_domains(args.root)
        elif args.command == "get-domain":
            result = get_domain(args.root, args.domain_id)
        elif args.command == "preflight":
            result = preflight(
                args.root,
                args.text,
                max_rules=args.max_rules,
                audited_at=args.audited_at,
            )
        elif args.command == "create-domain":
            result = create_domain(
                args.root,
                _load_object(args.domain, "domain"),
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "toggle-domain":
            result = toggle_domain(
                args.root,
                args.domain_id,
                args.enabled,
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "add-rule":
            result = add_rule(
                args.root,
                args.domain_id,
                _load_object(args.rule, "rule"),
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "remove-rule":
            result = remove_rule(
                args.root,
                args.domain_id,
                args.rule_id,
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "replace-rule":
            result = replace_rule(
                args.root,
                args.domain_id,
                args.rule_id,
                _load_object(args.rule, "rule"),
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "stage-proposal":
            result = stage_proposal(
                args.root,
                operation=args.operation,
                affected_domains=args.affected_domain,
                payload=_load_object(args.payload, "proposal payload"),
                requested_by=args.requested_by,
                source=args.source,
                rationale=args.rationale,
                expected_behavior_change=args.expected_behavior_change,
                review_date=args.review_date,
                timestamp=args.timestamp,
            )
        elif args.command == "approve-proposal":
            result = approve_proposal(
                args.root,
                args.proposal_id,
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "reject-proposal":
            result = reject_proposal(
                args.root,
                args.proposal_id,
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "recall":
            result = recall(
                args.root,
                args.rule_id,
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "exclude":
            result = exclude(
                args.root,
                args.domain_id,
                args.pattern,
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "list-commands":
            result = list_commands(args.root, domain_id=args.domain_id)
        elif args.command == "add-command":
            result = add_command(
                args.root,
                args.domain_id,
                _load_object(args.command_file, "command"),
                actor=args.actor,
                rationale=args.rationale,
                timestamp=args.timestamp,
            )
        elif args.command == "search-decisions":
            result = search_decisions(args.root, args.query)
        else:
            result = audit_rules(args.root, audited_at=args.audited_at)
            if args.write:
                write_conflict_report(args.root, result)
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            exit_code = 1 if result["blocking_count"] else 0
    except (RuleStoreError, RuleCliError, OSError, ValueError) as exc:
        print(f"Creator Rule Governance failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
