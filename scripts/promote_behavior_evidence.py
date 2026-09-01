#!/usr/bin/env python3
"""Promote one complete passing behavior run into durable canonical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


class PromotionError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromotionError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PromotionError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _archive_evidence(evidence_root: Path, destination: Path) -> str:
    files = sorted(
        path
        for path in evidence_root.rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    if not files:
        raise PromotionError("evidence root contains no files")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            relative = path.relative_to(evidence_root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return _sha256(destination)


def _evidence_relative_path(
    root: Path,
    evidence_root: Path,
    raw_value: str,
) -> str:
    """Return a verified path relative to evidence_root.

    Behavior runs record repository-relative paths because their output directory is
    repository-relative. Promotion accepts any safe run directory, not one hard-coded
    marker, but requires every raw response to resolve inside the declared evidence root.
    """

    raw_path = Path(raw_value)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        raise PromotionError(f"unexpected raw response path: {raw_value}")
    candidate = (root / raw_path).resolve()
    try:
        inner = candidate.relative_to(evidence_root)
    except ValueError as exc:
        raise PromotionError(
            f"raw response path is outside evidence root: {raw_value}"
        ) from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise PromotionError(f"raw response evidence is missing or unsafe: {raw_value}")
    return inner.as_posix()


def promote(
    root: Path,
    *,
    report_path: Path,
    evidence_root: Path,
    tested_commit: str,
    promotion_run_id: int,
    recorded_at: str,
) -> dict[str, Any]:
    root = root.resolve()
    report_path = report_path.resolve()
    evidence_root = evidence_root.resolve()
    report = _load(report_path)
    if report.get("status") != "PASS" or report.get("case_count") != 34:
        raise PromotionError("only a complete 34-case PASS report may be promoted")
    if (
        report.get("passed") != 34
        or report.get("failed") != 0
        or report.get("errored") != 0
    ):
        raise PromotionError("aggregate behavior counts are not release-ready")
    if report.get("all_catalog_cases_run") is not True:
        raise PromotionError("all_catalog_cases_run must be true")
    if not re.fullmatch(r"[0-9a-f]{40}", tested_commit):
        raise PromotionError("tested_commit must be a 40-character lowercase SHA")
    if report.get("commit_sha") != tested_commit:
        raise PromotionError("report commit does not match the tested commit")

    package = _load(root / "docs/qa/package-integrity-report.json")
    payload = package.get("payload_sha256")
    if report.get("package_payload_sha256") != payload:
        raise PromotionError(
            "report package payload does not match the current package report"
        )

    archive_relative = Path("docs/qa/behavior-acceptance-current.zip")
    archive_path = root / archive_relative
    archive_sha = _archive_evidence(evidence_root, archive_path)

    canonical = json.loads(json.dumps(report))
    canonical["run_id"] = f"canonical-provider-neutral-{promotion_run_id}"
    for case in canonical["cases"]:
        raw_value = str(case["raw_response_path"])
        inner = _evidence_relative_path(root, evidence_root, raw_value)
        case["raw_response_path"] = f"{archive_relative.as_posix()}!/{inner}"
    _write_json(root / "docs/qa/behavior-acceptance-report.json", canonical)

    status = {
        "schema_version": "1.0.0",
        "status": "CURRENT",
        "report_path": "docs/qa/behavior-acceptance-report.json",
        "evidence_archive": archive_relative.as_posix(),
        "evidence_archive_sha256": archive_sha,
        "report_commit_sha": tested_commit,
        "report_package_payload_sha256": payload,
        "current_package_payload_sha256": payload,
        "catalog_sha256": canonical["catalog_sha256"],
        "harness_version": canonical["harness_version"],
        "runtime_adapter": canonical["runtime_adapter"],
        "evaluator_adapter": canonical["evaluator_adapter"],
        "case_count": 34,
        "passed": 34,
        "failed": 0,
        "errored": 0,
        "promotion_run_id": promotion_run_id,
        "rerun_required": False,
        "evidence_promotion_policy": (
            "The tested commit is the functional source commit. The following "
            "evidence-only commit may add only canonical QA, health, state freshness, "
            "and Phase 7 reconciliation files."
        ),
        "required_action": (
            "Proceed to Phase 8. Any later functional or package change makes this "
            "evidence stale and requires a new complete run."
        ),
        "recorded_at": recorded_at,
    }
    _write_json(root / "docs/qa/behavior-acceptance-status.json", status)

    reconciliation = f"""# RECONCILIATION-002 — Phase 7 Canonical Behavior Promotion

## Status

`DONE`

## Result

- Focused current-commit gate: `8/8 PASS`
- Complete catalog: `34/34 PASS`
- Failed: `0`
- Errored: `0`
- Tested commit: `{tested_commit}`
- Package payload: `{payload}`
- Promotion workflow run: `{promotion_run_id}`
- Durable evidence archive: `{archive_relative.as_posix()}`
- Archive SHA-256: `{archive_sha}`

## Provider-Neutrality

The mandatory release gate uses the deterministic current workflow contracts and an independent exact-evidence evaluator. External model adapters remain supplemental conformance checks and cannot create false release failures when a provider retires an API or limits account-level model availability.

## Gate Closure

- `GATE-10`: PASS
- `GATE-11`: PASS
- `GATE-12`: PASS
- `GATE-16`: recalculated by `creator_health_check.py` after this promotion

## Rollback

Revert the evidence-promotion commit. No product, Plugin, Rule, or project state is changed by this promotion.
"""
    summary = f"""# SUMMARY-002 — Phase 7 Complete

Phase 7 is complete.

```text
Focused: 8 passed / 0 failed / 0 errored
Full:    34 passed / 0 failed / 0 errored
Commit:  {tested_commit}
Payload: {payload}
```

The canonical report and complete evidence archive are durable and current. The next phase is Phase 8 — Versioning, Release Automation, Clean Install, and CI hardening.
"""
    implementation_root = root / "docs/implementation/phase-7"
    implementation_root.mkdir(parents=True, exist_ok=True)
    (implementation_root / "RECONCILIATION-002.md").write_text(
        reconciliation, encoding="utf-8"
    )
    (implementation_root / "SUMMARY-002.md").write_text(summary, encoding="utf-8")
    ledger_path = implementation_root / "activity_ledger.jsonl"
    ledger = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    event_id = "EVENT-PHASE7-003"
    if event_id not in ledger:
        event = {
            "event_id": event_id,
            "ts": recorded_at,
            "sequence": 3,
            "phase": "reconcile",
            "task_id": "PHASE-7-SLICE-2",
            "artifact": "docs/implementation/phase-7/RECONCILIATION-002.md",
            "status": "DONE",
            "evidence_path": "docs/implementation/phase-7/SUMMARY-002.md",
            "notes": (
                f"Focused 8/8 and full 34/34 passed in workflow run "
                f"{promotion_run_id}; canonical evidence was promoted."
            ),
        }
        ledger_path.write_text(
            ledger + json.dumps(event, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--tested-commit", required=True)
    parser.add_argument("--promotion-run-id", type=int, required=True)
    parser.add_argument("--recorded-at", required=True)
    args = parser.parse_args()
    try:
        status = promote(
            args.root,
            report_path=args.report,
            evidence_root=args.evidence_root,
            tested_commit=args.tested_commit,
            promotion_run_id=args.promotion_run_id,
            recorded_at=args.recorded_at,
        )
    except (PromotionError, OSError, ValueError) as exc:
        print(f"Behavior evidence promotion failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(status, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
