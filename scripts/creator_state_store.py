#!/usr/bin/env python3
"""Repository-local Creator Toolchain state loading, schema validation, and atomic writes."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from creator_surface_registry import load_surface_registry
    from creator_transactions import atomic_write_json
    from json_schema_lite import JsonSchemaError, load_schema, validate as validate_json_schema
except ImportError:
    from scripts.creator_surface_registry import load_surface_registry
    from scripts.creator_transactions import atomic_write_json
    from scripts.json_schema_lite import JsonSchemaError, load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.4.0"
SURFACE_REGISTRY = load_surface_registry(ROOT)
STATE_FILES = tuple(SURFACE_REGISTRY)
SURFACE_NAMES = {path: item["surface_id"] for path, item in SURFACE_REGISTRY.items()}
SURFACE_OWNERS = {path: item["owner_skill"] for path, item in SURFACE_REGISTRY.items()}
PRIVACY_CLASSES = {path: item["privacy_class"] for path, item in SURFACE_REGISTRY.items()}
SCHEMA_PATHS = {path: item["schema"] for path, item in SURFACE_REGISTRY.items()}
ID_FIELDS = {
    ".creator/projects.json": ("projects", "project_id"),
    ".creator/entities.json": ("entities", "entity_id"),
    ".creator/session-insights.json": ("entries", "insight_id"),
    ".creator/backlog.json": ("items", "item_id"),
    ".creator/decisions.json": ("decisions", "decision_id"),
}


class StateStoreError(RuntimeError):
    pass


def safe_path(root: Path, relative: str | Path) -> Path:
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise StateStoreError(f"unsafe relative path: {relative}")
    candidate = root / rel
    parent = candidate.parent.resolve()
    try:
        parent.relative_to(root)
    except ValueError as exc:
        raise StateStoreError(f"path escapes workspace: {relative}") from exc
    return candidate


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateStoreError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateStoreError(f"state surface must contain a JSON object: {path}")
    return value


def surface_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_owner(relative: str) -> str:
    try:
        return SURFACE_OWNERS[relative]
    except KeyError as exc:
        raise StateStoreError(f"undeclared state surface: {relative}") from exc


def _valid_time(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _schema_root(schema_root: Path | None) -> Path:
    return (schema_root or ROOT).resolve()


def validate_surface(relative: str, value: dict[str, Any], *, schema_root: Path | None = None) -> list[str]:
    if relative not in STATE_FILES:
        return [f"undeclared state surface: {relative}"]
    findings: list[str] = []
    schema_path = _schema_root(schema_root) / SCHEMA_PATHS[relative]
    try:
        schema = load_schema(schema_path)
        findings.extend(validate_json_schema(value, schema))
    except JsonSchemaError as exc:
        findings.append(str(exc))
    if value.get("owner_skill") != expected_owner(relative):
        findings.append(f"owner_skill must be {expected_owner(relative)}")
    if value.get("privacy_class") != PRIVACY_CLASSES[relative]:
        findings.append(f"privacy_class must be {PRIVACY_CLASSES[relative]}")
    for field in ("created_at", "updated_at"):
        if not _valid_time(value.get(field)):
            findings.append(f"{field} must be ISO-8601")
    spec = ID_FIELDS.get(relative)
    if spec:
        collection, id_field = spec
        items = value.get(collection, [])
        ids = [item.get(id_field) for item in items if isinstance(item, dict) and isinstance(item.get(id_field), str)] if isinstance(items, list) else []
        if len(ids) != len(set(ids)):
            findings.append(f"duplicate {id_field}")
    if relative == ".creator/surfaces.json":
        items = value.get("surfaces", [])
        by_path = {item.get("path"): item for item in items if isinstance(item, dict)} if isinstance(items, list) else {}
        if tuple(by_path) != STATE_FILES:
            findings.append("surface registry must declare the canonical ordered ten state surfaces")
        for path, expected in SURFACE_REGISTRY.items():
            if by_path.get(path) != expected:
                findings.append(f"surface registry mismatch: {path}")
    if relative == ".creator/rules.json":
        domains = value.get("domains", [])
        domain_ids: list[str] = []
        rule_ids: list[str] = []
        command_ids: list[str] = []
        if isinstance(domains, list):
            for domain in domains:
                if not isinstance(domain, dict):
                    continue
                if isinstance(domain.get("domain_id"), str):
                    domain_ids.append(domain["domain_id"])
                if not _valid_time(domain.get("updated_at")):
                    findings.append(f"domain {domain.get('domain_id')}: updated_at must be ISO-8601")
                for rule in domain.get("rules", []):
                    if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str):
                        rule_ids.append(rule["rule_id"])
                for command in domain.get("commands", []):
                    if isinstance(command, dict) and isinstance(command.get("command_id"), str):
                        command_ids.append(command["command_id"])
        if len(domain_ids) != len(set(domain_ids)):
            findings.append("duplicate domain_id")
        if len(rule_ids) != len(set(rule_ids)):
            findings.append("duplicate rule_id")
        if len(command_ids) != len(set(command_ids)):
            findings.append("duplicate command_id")
    return sorted(set(findings))


def validate_workspace_values(root: Path, values: dict[str, dict[str, Any]], *, schema_root: Path | None = None) -> list[str]:
    root = Path(root).resolve()
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
    active = set(item for item in state.get("active_projects", []) if isinstance(item, str)) if isinstance(state.get("active_projects"), list) else set()
    blocked = set(item for item in state.get("blocked_projects", []) if isinstance(item, str)) if isinstance(state.get("blocked_projects"), list) else set()
    unknown = sorted((active | blocked) - project_ids)
    if unknown:
        findings.append(f"unknown state project IDs: {unknown}")
    decisions = values.get(".creator/decisions.json", {}).get("decisions", [])
    decision_ids = {item.get("decision_id") for item in decisions if isinstance(item, dict) and isinstance(item.get("decision_id"), str)} if isinstance(decisions, list) else set()
    domains = values.get(".creator/rules.json", {}).get("domains", [])
    for domain in domains if isinstance(domains, list) else []:
        if not isinstance(domain, dict):
            continue
        refs = [ref for ref in domain.get("decision_refs", []) if isinstance(ref, str)]
        missing = sorted(set(refs) - decision_ids)
        if missing:
            findings.append(f"domain {domain.get('domain_id')} has unknown decision refs: {missing}")
    return sorted(set(findings))


def validate_workspace(root: Path, *, schema_root: Path | None = None) -> list[str]:
    root = Path(root).resolve()
    values: dict[str, dict[str, Any]] = {}
    findings: list[str] = []
    for relative in STATE_FILES:
        path = safe_path(root, relative)
        if not path.is_file():
            findings.append(f"missing state surface: {relative}")
            continue
        try:
            values[relative] = load_json(path)
        except StateStoreError as exc:
            findings.append(str(exc))
    findings.extend(validate_workspace_values(root, values, schema_root=schema_root))
    return sorted(set(findings))


def write_surface(root: Path, relative: str, value: dict[str, Any], *, expected_sha256: str | None = None, schema_root: Path | None = None) -> str:
    path = safe_path(root, relative)
    errors = validate_surface(relative, value, schema_root=schema_root)
    if errors:
        raise StateStoreError("; ".join(errors))
    if expected_sha256 is not None and (not path.is_file() or surface_sha256(path) != expected_sha256):
        raise StateStoreError("optimistic-lock mismatch")

    def check(candidate: Path) -> None:
        errors = validate_surface(relative, load_json(candidate), schema_root=schema_root)
        if errors:
            raise StateStoreError("; ".join(errors))

    atomic_write_json(path, value, validator=check, mode=0o600)
    return surface_sha256(path)
