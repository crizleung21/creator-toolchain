#!/usr/bin/env python3
"""Mark canonical behavior evidence stale after a functional or package change."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from creator_transactions import atomic_write_json
except ImportError:  # pragma: no cover
    from scripts.creator_transactions import atomic_write_json


def mark_stale(root: Path, *, reason: str, recorded_at: str | None = None) -> dict[str, object]:
    root = Path(root).resolve()
    package = json.loads((root / "docs/qa/package-integrity-report.json").read_text(encoding="utf-8"))
    report = json.loads((root / "docs/qa/behavior-acceptance-report.json").read_text(encoding="utf-8"))
    timestamp = recorded_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    value: dict[str, object] = {
        "schema_version": "1.0.0",
        "status": "STALE",
        "report_path": "docs/qa/behavior-acceptance-report.json",
        "report_commit_sha": report.get("commit_sha"),
        "report_package_payload_sha256": report.get("package_payload_sha256"),
        "current_package_payload_sha256": package.get("payload_sha256"),
        "invalidated_by": reason,
        "reason": "The stored complete report remains historical evidence, but its package payload does not represent the current candidate.",
        "rerun_required": True,
        "required_action": "Rerun the complete 34-case provider-neutral behavior gate and promote only a passing current report.",
        "recorded_at": timestamp,
    }
    atomic_write_json(root / "docs/qa/behavior-acceptance-status.json", value, mode=0o644)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--reason", required=True)
    parser.add_argument("--recorded-at")
    args = parser.parse_args()
    value = mark_stale(args.root, reason=args.reason, recorded_at=args.recorded_at)
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
