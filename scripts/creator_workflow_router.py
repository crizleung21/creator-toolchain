#!/usr/bin/env python3
"""Deterministically route Creator Toolchain requests to one primary workflow."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
CONFIG_RELATIVE = Path("config/workflow-routing.json")
SCHEMA_RELATIVE = Path("schemas/routing/route-decision.schema.json")


class WorkflowRoutingError(RuntimeError):
    """Raised when a deterministic route decision cannot be produced."""


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def load_routing_config(root: Path = ROOT) -> dict[str, Any]:
    path = Path(root) / CONFIG_RELATIVE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowRoutingError(f"cannot load routing config: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1.0.0":
        raise WorkflowRoutingError("routing config schema_version must be 1.0.0")
    routes = value.get("routes")
    if not isinstance(routes, list) or not routes:
        raise WorkflowRoutingError("routing config routes must be a non-empty array")
    route_ids: set[str] = set()
    priorities: set[int] = set()
    fallbacks = 0
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise WorkflowRoutingError(f"routes[{index}] must be an object")
        route_id = route.get("route_id")
        priority = route.get("priority")
        if not isinstance(route_id, str) or not route_id:
            raise WorkflowRoutingError(f"routes[{index}].route_id is invalid")
        if route_id in route_ids:
            raise WorkflowRoutingError(f"duplicate route_id: {route_id}")
        route_ids.add(route_id)
        if not isinstance(priority, int) or priority in priorities:
            raise WorkflowRoutingError(f"route priority must be a unique integer: {route_id}")
        priorities.add(priority)
        if route.get("fallback") is True:
            fallbacks += 1
        for field in ("match_any", "match_all", "exclude_any", "required_sources"):
            if not isinstance(route.get(field), list) or not all(isinstance(item, str) for item in route[field]):
                raise WorkflowRoutingError(f"{route_id}.{field} must be an array of strings")
        for field in ("primary_workflow", "expected_artifact", "boundary"):
            if not isinstance(route.get(field), str) or not route[field]:
                raise WorkflowRoutingError(f"{route_id}.{field} must be non-empty")
    if fallbacks != 1:
        raise WorkflowRoutingError("routing config must declare exactly one fallback route")
    return value


def _match(route: dict[str, Any], normalized: str) -> tuple[bool, list[str]]:
    if route.get("fallback") is True:
        return False, []
    matched_all = [signal for signal in route["match_all"] if _normalize(signal) in normalized]
    matched_any = [signal for signal in route["match_any"] if _normalize(signal) in normalized]
    excluded = [signal for signal in route["exclude_any"] if _normalize(signal) in normalized]
    is_match = len(matched_all) == len(route["match_all"]) and (not route["match_any"] or bool(matched_any)) and not excluded
    return is_match, sorted(set(matched_all + matched_any))


def route_request(root: Path, request: str, *, available_sources: list[str] | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    if not isinstance(request, str) or not request.strip():
        raise WorkflowRoutingError("request must be non-empty")
    normalized = _normalize(request)
    available = set(available_sources or [])
    config = load_routing_config(schema_root)
    routes = sorted(config["routes"], key=lambda item: (-int(item["priority"]), item["route_id"]))
    fallback = next(item for item in routes if item.get("fallback") is True)
    chosen = fallback
    chosen_signals: list[str] = []
    considered: list[dict[str, Any]] = []
    for route in routes:
        matched, signals = _match(route, normalized)
        considered.append({"route_id": route["route_id"], "priority": route["priority"], "matched": matched, "signals": signals})
        if matched and chosen is fallback:
            chosen = route
            chosen_signals = signals
    support_script = chosen.get("support_script")
    support_available = bool(support_script and (root / support_script).is_file()) if support_script else False
    missing_inputs = [item for item in chosen["required_sources"] if item not in available]
    if support_script and not support_available:
        missing_inputs.append(f"{support_script} (deterministic support not yet available)")
    missing_inputs = sorted(set(missing_inputs))
    handoff_prompt = (
        f"Use {chosen['primary_workflow']} for route {chosen['route_id']}. "
        f"Produce {chosen['expected_artifact']}. Boundary: {chosen['boundary']}"
    )
    decision = {
        "schema_version": "1.0.0",
        "request": request.strip(),
        "route_id": chosen["route_id"],
        "primary_workflow": chosen["primary_workflow"],
        "secondary_workflow": chosen.get("secondary_workflow"),
        "required_sources": sorted(set(chosen["required_sources"])),
        "expected_artifact": chosen["expected_artifact"],
        "missing_inputs": missing_inputs,
        "boundary": chosen["boundary"],
        "handoff_prompt": handoff_prompt,
        "support_script": support_script,
        "support_script_available": support_available,
        "matched_signals": chosen_signals,
        "considered_routes": considered,
    }
    findings = validate_json_schema(decision, load_schema(schema_root / SCHEMA_RELATIVE))
    if findings:
        raise WorkflowRoutingError("route decision failed schema validation: " + "; ".join(findings))
    return decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--request", required=True)
    parser.add_argument("--source", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        decision = route_request(args.root, args.request, available_sources=args.source)
    except (WorkflowRoutingError, OSError, ValueError) as exc:
        print(f"Creator workflow routing failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(decision, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
