#!/usr/bin/env python3
"""Repository-local Creator Toolchain state loading, validation, and atomic writes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from creator_transactions import atomic_write_json
except ImportError:  # pragma: no cover
    from scripts.creator_transactions import atomic_write_json

SCHEMA_VERSION = "0.4.0"
STATE_FILES = (
    ".creator/workspace.json",
    ".creator/projects.json",
    ".creator/entities.json",
    ".creator/state.json",
    ".creator/session-insights.json",
    ".creator/operator.json",
    ".creator/backlog.json",
    ".creator/surfaces.json",
    ".creator/decisions.json",
    ".creator/rules.json",
)

SURFACE_OWNERS = {".creator/rules.json": "creator-rule-router"}

PRIVACY_CLASSES = {
    ".creator/workspace.json": "publishable_template",
    ".creator/projects.json": "repository_workflow_state",
    ".creator/entities.json": "private",
    ".creator/state.json": "repository_workflow_state",
    ".creator/session-insights.json": "private",
    ".creator/operator.json": "private",
    ".creator/backlog.json": "repository_workflow_state",
    ".creator/surfaces.json": "publishable_template",
    ".creator/decisions.json": "repository_workflow_state",
    ".creator/rules.json": "repository_contract",
}

COLLECTION_FIELDS = {
    ".creator/projects.json": "projects",
    ".creator/entities.json": "entities",
    ".creator/session-insights.json": "entries",
    ".creator/backlog.json": "items",
    ".creator/surfaces.json": "surfaces",
    ".creator/decisions.json": "decisions",
}


class StateStoreError(RuntimeError):
    """Raised when repository state cannot be safely accessed or updated."""


def safe_path(root: Path, relative: str | Path) -> Path:
    root = Path(root).resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise StateStoreError(f"unsafe relative path: {relative}")
    candidate = root / relative_path
    resolved_parent = candidate.parent.resolve()
    try:
        resolved_parent.relative_to(root)
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
    return SURFACE_OWNERS.get(relative, "creator-workspace-manager")


def validate_surface(relative: str, value: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if relative not in STATE_FILES:
        return [f"undeclared state surface: {relative}"]
    if value.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version must be {SCHEMA_VERSION}")
    if value.get("owner_skill") != expected_owner(relative):
        findings.append(f"owner_skill must be {expected_owner(relative)}")
    if value.get("privacy_class") != PRIVACY_CLASSES[relative]:
        findings.append(f"privacy_class must be {PRIVACY_CLASSES[relative]}")
    for field in ("created_at", "updated_at"):
        if not isinstance(value.get(field), str) or not value[field]:
            findings.append(f"{field} must be a non-empty string")
    collection = COLLECTION_FIELDS.get(relative)
    if collection is not None and not isinstance(value.get(collection), list):
        findings.append(f"{collection} must be an array")
    if relative == ".creator/workspace.json":
        for field in ("workspace_id", "display_name", "state_contract", "architecture_map"):
            if not isinstance(value.get(field), str) or not value[field]:
                findings.append(f"{field} must be a non-empty string")
        if value.get("active_plan") is not None and not isinstance(value.get("active_plan"), str):
            findings.append("active_plan must be null or a string")
    elif relative == ".creator/state.json":
        for field in ("active_projects", "blocked_projects"):
            if not isinstance(value.get(field), list):
                findings.append(f"{field} must be an array")
        if not isinstance(value.get("state_divergence"), dict):
            findings.append("state_divergence must be an object")
    elif relative == ".creator/operator.json":
        if not isinstance(value.get("owner"), str) or not value["owner"]:
            findings.append("owner must be a non-empty string")
        if not isinstance(value.get("preferences"), dict):
            findings.append("preferences must be an object")
    elif relative == ".creator/rules.json":
        for field in ("domains", "staged_proposals", "decision_log"):
            if not isinstance(value.get(field), list):
                findings.append(f"{field} must be an array")
        domains = value.get("domains", [])
        if isinstance(domains, list) and not any(isinstance(item, dict) and item.get("domain_id") == "GLOBAL" for item in domains):
            findings.append("GLOBAL domain is required")
    return findings


def validate_workspace(root: Path) -> list[str]:
    root = Path(root).resolve()
    findings: list[str] = []
    parsed: dict[str, dict[str, Any]] = {}
    for relative in STATE_FILES:
        path = safe_path(root, relative)
        if not path.is_file():
            findings.append(f"missing state surface: {relative}")
            continue
        try:
            value = load_json(path)
        except StateStoreError as exc:
            findings.append(str(exc))
            continue
        parsed[relative] = value
        findings.extend(f"{relative}: {item}" for item in validate_surface(relative, value))
    workspace = parsed.get(".creator/workspace.json", {})
    architecture_map = workspace.get("architecture_map")
    if isinstance(architecture_map, str):
        try:
            if not safe_path(root, architecture_map).is_file():
                findings.append(f"workspace architecture_map is missing: {architecture_map}")
        except StateStoreError as exc:
            findings.append(str(exc))
    active_plan = workspace.get("active_plan")
    if isinstance(active_plan, str):
        try:
            if not safe_path(root, active_plan).is_file():
                findings.append(f"workspace active_plan is missing: {active_plan}")
        except StateStoreError as exc:
            findings.append(str(exc))
    surfaces = parsed.get(".creator/surfaces.json", {}).get("surfaces", [])
    if isinstance(surfaces, list):
        declared = {item.get("path") for item in surfaces if isinstance(item, dict) and item.get("required") is True}
        missing_declarations = sorted(set(STATE_FILES) - declared)
        if missing_declarations:
            findings.append(f"required surfaces not declared: {missing_declarations}")
    projects = parsed.get(".creator/projects.json", {}).get("projects", [])
    project_ids = {item.get("project_id") for item in projects if isinstance(item, dict) and isinstance(item.get("project_id"), str)}
    active = parsed.get(".creator/state.json", {}).get("active_projects", [])
    if isinstance(active, list):
        unknown = sorted(item for item in active if isinstance(item, str) and item not in project_ids)
        if unknown:
            findings.append(f"unknown active projects: {unknown}")
    return findings


def write_surface(root: Path, relative: str, value: dict[str, Any], *, expected_sha256: str | None = None) -> str:
    path = safe_path(root, relative)
    findings = validate_surface(relative, value)
    if findings:
        raise StateStoreError("; ".join(findings))
    if expected_sha256 is not None and (not path.is_file() or surface_sha256(path) != expected_sha256):
        raise StateStoreError("optimistic-lock mismatch")
    def validate_written(candidate: Path) -> None:
        written = load_json(candidate)
        errors = validate_surface(relative, written)
        if errors:
            raise StateStoreError("; ".join(errors))
    atomic_write_json(path, value, validator=validate_written, mode=0o600)
    return surface_sha256(path)
