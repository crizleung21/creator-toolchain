#!/usr/bin/env python3
"""Schema 0.4.0 validation and cross-file consistency for Creator workspace state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from creator_state_store import SCHEMA_PATHS as SCHEMAS, STATE_FILES, SURFACE_REGISTRY as REGISTRY, StateStoreError, load_json, safe_path, validate_surface
except ImportError:
    from scripts.creator_state_store import SCHEMA_PATHS as SCHEMAS, STATE_FILES, SURFACE_REGISTRY as REGISTRY, StateStoreError, load_json, safe_path, validate_surface

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.4.0"
NAMES = {path: item["surface_id"] for path, item in REGISTRY.items()}
OWNERS = {path: item["owner_skill"] for path, item in REGISTRY.items()}
PRIVACY = {path: item["privacy_class"] for path, item in REGISTRY.items()}


def validate_values(root: Path, values: dict[str, dict[str, Any]], *, schema_root: Path | None = None) -> list[str]:
    root = Path(root).resolve()
    schema_root = (schema_root or ROOT).resolve()
    findings: list[str] = []
    for relative in STATE_FILES:
        value = values.get(relative)
        if value is None:
            findings.append(f"missing state surface: {relative}")
            continue
        findings.extend(f"{relative}: {item}" for item in validate_surface(relative, value, schema_root=schema_root))
    workspace = values.get(".creator/workspace.json", {})
    for field in ("architecture_map", "active_plan"):
        pointer = workspace.get(field)
        if pointer is None and field == "active_plan":
            continue
        if not isinstance(pointer, str):
            findings.append(f"workspace {field} must be a string or null")
            continue
        try:
            if not safe_path(root, pointer).is_file():
                findings.append(f"workspace {field} is missing: {pointer}")
        except StateStoreError as exc:
            findings.append(str(exc))
    projects = values.get(".creator/projects.json", {}).get("projects", [])
    project_ids = {item.get("project_id") for item in projects if isinstance(item, dict) and isinstance(item.get("project_id"), str)} if isinstance(projects, list) else set()
    for project in projects if isinstance(projects, list) else []:
        if not isinstance(project, dict):
            continue
        for field in ("plan_path", "last_summary"):
            pointer = project.get(field)
            if pointer is None:
                continue
            try:
                if not isinstance(pointer, str) or not safe_path(root, pointer).is_file():
                    findings.append(f"project {project.get('project_id')} {field} target is missing: {pointer}")
            except StateStoreError as exc:
                findings.append(str(exc))
    state = values.get(".creator/state.json", {})
    refs = {item for key in ("active_projects", "blocked_projects") for item in state.get(key, []) if isinstance(item, str)}
    unknown = sorted(refs - project_ids)
    if unknown:
        findings.append(f"unknown state project IDs: {unknown}")
    decisions = values.get(".creator/decisions.json", {}).get("decisions", [])
    decision_ids = {item.get("decision_id") for item in decisions if isinstance(item, dict) and isinstance(item.get("decision_id"), str)} if isinstance(decisions, list) else set()
    domains = values.get(".creator/rules.json", {}).get("domains", [])
    for domain in domains if isinstance(domains, list) else []:
        if not isinstance(domain, dict):
            continue
        missing = sorted(set(item for item in domain.get("decision_refs", []) if isinstance(item, str)) - decision_ids)
        if missing:
            findings.append(f"domain {domain.get('domain_id')} has unknown decision refs: {missing}")
    return sorted(set(findings))


def load_values(root: Path) -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
    root = Path(root).resolve()
    raw: dict[str, bytes] = {}
    values: dict[str, dict[str, Any]] = {}
    for relative in STATE_FILES:
        path = safe_path(root, relative)
        if not path.is_file():
            raise StateStoreError(f"missing state file: {relative}")
        raw[relative] = path.read_bytes()
        values[relative] = load_json(path)
    return raw, values


def validate_workspace(root: Path, *, schema_root: Path | None = None) -> list[str]:
    try:
        _, values = load_values(root)
    except StateStoreError as exc:
        return [str(exc)]
    return validate_values(root, values, schema_root=schema_root)
