#!/usr/bin/env python3
"""Validate aggregate behavior evidence for focused or complete release gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--require-all-catalog", action="store_true")
    args = parser.parse_args()
    try:
        value = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Behavior report validation failed: {exc}", file=sys.stderr)
        return 2
    failures = []
    if value.get("case_count") != args.expected_count:
        failures.append(f"case_count={value.get('case_count')} expected={args.expected_count}")
    if value.get("passed") != args.expected_count:
        failures.append(f"passed={value.get('passed')} expected={args.expected_count}")
    if value.get("failed") != 0:
        failures.append(f"failed={value.get('failed')}")
    if value.get("errored") != 0:
        failures.append(f"errored={value.get('errored')}")
    if args.require_all_catalog:
        if value.get("status") != "PASS" or value.get("all_catalog_cases_run") is not True:
            failures.append("complete catalog must have status PASS and all_catalog_cases_run=true")
    else:
        if value.get("status") != "INCOMPLETE" or value.get("all_catalog_cases_run") is not False:
            failures.append("focused report must have status INCOMPLETE and all_catalog_cases_run=false")
    for case in value.get("cases", []):
        if case.get("result") != "PASS":
            failures.append(f"{case.get('case_id')}: result={case.get('result')}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS",
        "run_id": value.get("run_id"),
        "case_count": value.get("case_count"),
        "commit_sha": value.get("commit_sha"),
        "package_payload_sha256": value.get("package_payload_sha256"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
