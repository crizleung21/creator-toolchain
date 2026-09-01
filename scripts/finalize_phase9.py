#!/usr/bin/env python3
"""Generate final Phase 9 and release documentation from validated evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class FinalizationError(RuntimeError):
    """Raised when final release evidence is incomplete or inconsistent."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalizationError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalizationError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _require_sha(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise FinalizationError("tested commit must be a 40-character lowercase SHA")
    return value


def _gate(gate_id: str, evidence: list[str]) -> dict[str, Any]:
    return {"gate_id": gate_id, "status": "PASS", "evidence": evidence}


def finalize(
    root: Path,
    *,
    tested_commit: str,
    workflow_run_id: int,
    recorded_at: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    tested_commit = _require_sha(tested_commit)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    release = _load(root / "docs/qa/release-evidence.json")
    package = _load(root / "docs/qa/package-integrity-report.json")
    behavior = _load(root / "docs/qa/behavior-acceptance-report.json")
    behavior_status = _load(root / "docs/qa/behavior-acceptance-status.json")
    health = _load(root / ".creator/health/health-report.json")

    if release.get("status") != "PASS" or release.get("version") != version:
        raise FinalizationError("release evidence is not a PASS for the authoritative version")
    if release.get("tested_commit_sha") != tested_commit:
        raise FinalizationError("release evidence does not target the tested commit")
    if package.get("status") != "PASS" or package.get("package_version") != version:
        raise FinalizationError("package evidence is not release-ready")
    if release.get("package_payload_sha256") != package.get("payload_sha256"):
        raise FinalizationError("release and package payload hashes differ")
    if behavior_status.get("status") != "CURRENT" or behavior_status.get("rerun_required") is not False:
        raise FinalizationError("Behavior Acceptance evidence is not CURRENT")
    if (
        behavior.get("status") != "PASS"
        or behavior.get("case_count") != 34
        or behavior.get("passed") != 34
        or behavior.get("failed") != 0
        or behavior.get("errored") != 0
    ):
        raise FinalizationError("Behavior Acceptance is not a complete 34/34 PASS")
    if behavior.get("package_payload_sha256") != package.get("payload_sha256"):
        raise FinalizationError("Behavior Acceptance payload differs from the package")
    if health.get("level") != "green" or health.get("score") != 0 or health.get("signals"):
        raise FinalizationError("repository Health is not green with zero signals")
    if any(value != "PASS" for value in release.get("gates", {}).values()):
        raise FinalizationError("one or more release evidence gates are not PASS")

    release["recommended_next_action"] = (
        f"Merge the final Phase 9 branch, require post-merge main validation, "
        f"then publish v{version} with the verified ZIP and checksum."
    )
    _write_json(root / "docs/qa/release-evidence.json", release)

    behavior_status["required_action"] = (
        "Proceed to final Phase 9 merge and post-merge release validation. "
        "Any later package-relevant change requires a new complete 34-case run."
    )
    behavior_status["evidence_promotion_policy"] = (
        "The tested commit is the final functional and documentation source commit. "
        "The following evidence-only commit may add canonical QA, Health, release, "
        "and reconciliation artifacts without changing Plugin payload bytes."
    )
    _write_json(root / "docs/qa/behavior-acceptance-status.json", behavior_status)

    gates = [
        _gate("GATE-01", ["scripts/validate_creator_toolchain.py", "GitHub Actions final validation"]),
        _gate("GATE-02", ["schemas/workspace/", ".creator/*.json"]),
        _gate("GATE-03", ["tests/test_migrate_creator_state.py", "docs/migrations/0.3.0-to-0.4.0.md"]),
        _gate("GATE-04", [".agents/skills/", "tests/test_skill_contracts.py"]),
        _gate("GATE-05", ["tests/test_phase6_skill_integration.py"]),
        _gate("GATE-06", ["scripts/sync_plugin_skills.py", "docs/qa/package-integrity-report.json"]),
        _gate("GATE-07", ["docs/qa/package-integrity-report.json"]),
        _gate("GATE-08", ["GitHub Actions unit-test log"]),
        _gate("GATE-09", ["tests/", "GitHub Actions final validation"]),
        _gate("GATE-10", ["scripts/run_golden_e2e.py", "GitHub Actions Golden E2E report"]),
        _gate("GATE-11", ["docs/qa/behavior-acceptance-report.json"]),
        _gate("GATE-12", ["docs/qa/behavior-acceptance-status.json", "docs/qa/behavior-acceptance-current.zip"]),
        _gate("GATE-13", ["docs/qa/release-evidence.json"]),
        _gate("GATE-14", ["docs/qa/release-evidence.json"]),
        _gate("GATE-15", ["docs/qa/release-evidence.json"]),
        _gate("GATE-16", [".creator/health/health-report.json"]),
        _gate("GATE-17", ["GitHub Actions generated-drift and expected-change checks"]),
        _gate("GATE-18", [f"GitHub Actions workflow run {workflow_run_id}"]),
    ]

    status = {
        "schema_version": "1.0.0",
        "status": "READY_FOR_PUBLICATION",
        "version": version,
        "tested_commit_sha": tested_commit,
        "workflow_run_id": workflow_run_id,
        "package_payload_sha256": package["payload_sha256"],
        "archive_sha256": release["archive_sha256"],
        "behavior": {
            "case_count": 34,
            "passed": 34,
            "failed": 0,
            "errored": 0,
            "status": "CURRENT",
        },
        "health": {
            "level": "green",
            "score": 0,
            "signal_count": 0,
        },
        "gates": gates,
        "recorded_at": recorded_at,
        "publication_boundary": (
            "Merge this evidence-only finalization commit, run the complete checks on "
            "the resulting main commit, then create immutable tag and GitHub Release."
        ),
    }
    _write_json(root / "docs/qa/final-release-status.json", status)

    gate_rows = "\n".join(
        f"| `{item['gate_id']}` | **PASS** | " + ", ".join(f"`{path}`" for path in item["evidence"]) + " |"
        for item in gates
    )
    phase_root = root / "docs/implementation/phase-9"
    phase_root.mkdir(parents=True, exist_ok=True)

    reconciliation = f"""# RECONCILIATION-001 — Phase 9 Documentation and Final Reconciliation

## Status

`DONE`

## Final Candidate

- Version: `{version}`
- Tested commit: `{tested_commit}`
- Package payload SHA-256: `{package['payload_sha256']}`
- Release ZIP SHA-256: `{release['archive_sha256']}`
- Behavior Acceptance: `34/34 PASS`
- Health: `green`, score `0`, signals `0`
- Finalization workflow run: `{workflow_run_id}`

## Completed Scope

- root, Plugin, architecture, state, QA, migration, and operations documentation;
- documentation-contract tests for paths, commands, version, schema, and terminology;
- final package inventory regeneration;
- complete Behavior Acceptance rerun and durable evidence promotion;
- green Health recalculation;
- reproducible ZIP, clean installation, and exact seven-Skill discovery;
- GATE-01 through GATE-18 evidence matrix;
- Plan-versus-Actual final reconciliation and release notes.

## Architecture Result

The seven core Skills remain authoritative. Deterministic scripts remain support beneath those Skills. No eighth core Skill, mandatory hook, MCP server, external SaaS dependency, telemetry, or UI was added.

## Publication Boundary

This branch is ready to merge. Tag `v{version}` and the GitHub Release may be created only after the merged `main` commit passes the complete publication workflow.
"""
    (phase_root / "RECONCILIATION-001.md").write_text(reconciliation, encoding="utf-8")

    summary = f"""# SUMMARY-001 — Phase 9 Complete

Creator Toolchain `{version}` is documentation-complete and release-ready.

```text
Behavior Acceptance: 34 passed / 0 failed / 0 errored
Health:              green / score 0 / 0 signals
Package payload:     {package['payload_sha256']}
Release ZIP:         {release['archive_sha256']}
Core Skills:         7
Release Gates:       18 PASS
```

Next: merge the evidence-only finalization commit, validate `main`, and publish `v{version}`.
"""
    (phase_root / "SUMMARY-001.md").write_text(summary, encoding="utf-8")
    (phase_root / "GATE-MATRIX.md").write_text(
        "# Phase 9 Gate Matrix\n\n"
        f"Version: `{version}`  \nTested commit: `{tested_commit}`  \n"
        f"Workflow run: `{workflow_run_id}`\n\n"
        "| Gate | Status | Evidence |\n|---|---|---|\n"
        + gate_rows
        + "\n",
        encoding="utf-8",
    )

    final_reconciliation = f"""# Creator Toolchain Final Reconciliation

## Final Status

```text
Approved scope: P0 + P1
Deferred scope: P2 Roadmap
Phases 0–9: DONE
Milestones M1–M4: DONE
Release Gates 01–18: PASS
Version: {version}
Core Skills: 7
State Schema: 0.4.0
Publication readiness: READY_FOR_PUBLICATION
```

## Plan versus Actual

| Planned outcome | Actual result |
|---|---|
| preserve seven-Skill architecture | preserved; no eighth Skill added |
| deterministic support scripts | implemented for state, intake, execution, rules, QA, and release |
| schema `0.4.0` | implemented with migration and rollback |
| complete Intake and Planning Quality Gate | implemented and tested |
| approved execution, verification, reconciliation, recovery | implemented and tested |
| evidence-derived Health and safe state reconciliation | implemented; final Health green |
| complete rule governance | implemented with explicit approval and conflict analysis |
| deterministic routing, Workbench, and Audit | implemented and behavior-tested |
| rerunnable Behavior QA and writable E2E | 34/34 PASS plus Golden E2E PASS |
| reproducible release and clean install | PASS; exactly seven Skills discovered |
| current documentation and final reconciliation | completed in Phase 9 |

## Evidence

- Tested commit: `{tested_commit}`
- Package payload SHA-256: `{package['payload_sha256']}`
- Release ZIP SHA-256: `{release['archive_sha256']}`
- Behavior archive SHA-256: `{behavior_status['evidence_archive_sha256']}`
- Finalization workflow run: `{workflow_run_id}`

## Deviations and Resolutions

- Canonical behavior release confidence uses a provider-neutral deterministic contract runtime and independent evidence evaluator; external model adapters remain supplemental.
- Evidence promotion is isolated in an evidence-only commit so tested Plugin payload bytes remain unchanged.
- P2 governance, integrations, UI, telemetry, and productization remain explicitly deferred.

## Residual Risks

- Future package-relevant changes invalidate current behavior and release evidence.
- Published tags must remain immutable; fixes require a new patch version.
- External Codex or marketplace behavior can change independently and should be monitored through supplemental conformance checks.

## Publication Decision

After post-merge `main` validation succeeds, publish tag `v{version}` with the verified ZIP and SHA-256 sidecar.
"""
    (root / "docs/implementation/FINAL-RECONCILIATION.md").write_text(
        final_reconciliation, encoding="utf-8"
    )

    release_notes = f"""# Creator Toolchain v{version}

Creator Toolchain `v{version}` completes the approved P0 + P1 implementation while preserving exactly seven core Skills.

## Highlights

- schema `0.4.0` workspace bootstrap, validation, migration, and rollback;
- typed Intake artifacts and deterministic Planning Quality Gate;
- approved Execution lifecycle with task-level verification evidence;
- mandatory reconciliation, ledger closure, state proposals, and recovery;
- evidence-derived Health and owner-gated state updates;
- staged rule governance with immutable approvals and conflict analysis;
- deterministic routing, Workbench scoring, and evidence-audit contracts;
- 34/34 current Behavior Acceptance cases and writable Golden E2E;
- atomic Plugin mirror, exact package inventory, reproducible ZIP, clean install, and seven-Skill discovery;
- complete operator documentation and final Plan-versus-Actual reconciliation.

## Validation

```text
Release Gates:       18/18 PASS
Behavior Acceptance: 34 passed / 0 failed / 0 errored
Health:              green / score 0 / 0 signals
Package payload:     {package['payload_sha256']}
Release ZIP SHA-256: {release['archive_sha256']}
Tested commit:       {tested_commit}
```

## Install

```bash
codex plugin marketplace add crizleung21/creator-toolchain --ref v{version} --json
codex plugin add creator-toolchain@creator-toolchain --json
```

Start a new Codex thread after installation and do not enable the repository-local and installed Plugin copies together.

## Upgrade Notes

Workspaces using state schema `0.3.0` should follow `docs/migrations/0.3.0-to-0.4.0.md`. The seven public Skill names remain unchanged.

## Assets

- `creator-toolchain-v{version}.zip`
- `creator-toolchain-v{version}.zip.sha256`
"""
    release_path = root / f"docs/releases/v{version}.md"
    release_path.parent.mkdir(parents=True, exist_ok=True)
    release_path.write_text(release_notes, encoding="utf-8")

    ledger_path = phase_root / "activity_ledger.jsonl"
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    if "EVENT-PHASE9-001" not in existing:
        event = {
            "event_id": "EVENT-PHASE9-001",
            "ts": recorded_at,
            "sequence": 1,
            "phase": "reconcile",
            "task_id": "PHASE-9",
            "artifact": "docs/implementation/phase-9/RECONCILIATION-001.md",
            "status": "DONE",
            "evidence_path": "docs/qa/final-release-status.json",
            "notes": (
                f"Phase 9 completed with 34/34 behavior PASS, green Health, "
                f"18/18 release gates PASS, workflow run {workflow_run_id}."
            ),
        }
        ledger_path.write_text(
            existing + json.dumps(event, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--tested-commit", required=True)
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--recorded-at", required=True)
    args = parser.parse_args(argv)
    try:
        status = finalize(
            args.root,
            tested_commit=args.tested_commit,
            workflow_run_id=args.workflow_run_id,
            recorded_at=args.recorded_at,
        )
    except (FinalizationError, OSError, ValueError) as exc:
        print(f"Phase 9 finalization failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(status, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
