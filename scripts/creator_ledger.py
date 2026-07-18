#!/usr/bin/env python3
"""Append-only JSONL ledger operations for Creator Toolchain workflows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_transactions import atomic_write_text
except ImportError:  # pragma: no cover
    from scripts.creator_transactions import atomic_write_text

ALLOWED_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED", "IN_PROGRESS"}


class LedgerError(RuntimeError):
    """Raised when an append-only ledger invariant is violated."""


def _validate_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError(f"invalid timestamp: {value}") from exc


def read_events(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"invalid JSONL at line {number}: {exc}") from exc
        if not isinstance(value, dict):
            raise LedgerError(f"ledger line {number} must be an object")
        events.append(value)
    return events


def validate_event(event: dict[str, Any]) -> None:
    for field in ("event_id", "ts", "phase", "task_id", "artifact", "status"):
        if not isinstance(event.get(field), str) or not event[field]:
            raise LedgerError(f"{field} must be a non-empty string")
    if not isinstance(event.get("sequence"), int) or event["sequence"] < 1:
        raise LedgerError("sequence must be a positive integer")
    if event["status"] not in ALLOWED_STATUSES:
        raise LedgerError(f"unsupported status: {event['status']}")
    _validate_timestamp(event["ts"])


def append_event(path: Path, event: dict[str, Any]) -> None:
    validate_event(event)
    events = read_events(path)
    ids = {item.get("event_id") for item in events}
    if event["event_id"] in ids:
        raise LedgerError(f"duplicate event_id: {event['event_id']}")
    expected_sequence = (events[-1].get("sequence", 0) + 1) if events else 1
    if event["sequence"] != expected_sequence:
        raise LedgerError(f"sequence must be {expected_sequence}")
    lines = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in events + [event]]
    atomic_write_text(Path(path), "\n".join(lines) + "\n", mode=0o600)


def new_event(*, event_id: str, sequence: int, phase: str, task_id: str, artifact: str, status: str, evidence_path: str = "", notes: str = "", ts: str | None = None) -> dict[str, Any]:
    return {"event_id": event_id, "ts": ts or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "sequence": sequence, "phase": phase, "task_id": task_id, "artifact": artifact, "status": status, "evidence_path": evidence_path, "notes": notes}
