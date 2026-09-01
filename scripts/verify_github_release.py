#!/usr/bin/env python3
"""Validate stable GitHub Release metadata emitted by ``gh release view``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class GitHubReleaseVerificationError(ValueError):
    """Raised when GitHub Release metadata does not satisfy the stable-release contract."""


def validate_release_metadata(
    value: dict[str, Any],
    *,
    tag: str,
    version: str,
) -> dict[str, Any]:
    """Validate one stable release and return a deterministic verification summary."""

    if not isinstance(value, dict):
        raise GitHubReleaseVerificationError("release metadata must be a JSON object")
    if tag != f"v{version}":
        raise GitHubReleaseVerificationError(
            f"tag/version mismatch: expected v{version}, received {tag}"
        )
    if value.get("tagName") != tag:
        raise GitHubReleaseVerificationError(
            f"release tag mismatch: expected {tag}, received {value.get('tagName')!r}"
        )
    if value.get("isDraft") is not False:
        raise GitHubReleaseVerificationError("release must not be a draft")
    if value.get("isPrerelease") is not False:
        raise GitHubReleaseVerificationError("release must not be a prerelease")

    assets = value.get("assets")
    if not isinstance(assets, list):
        raise GitHubReleaseVerificationError("release assets must be an array")
    names = {
        item.get("name")
        for item in assets
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    expected = {
        f"creator-toolchain-v{version}.zip",
        f"creator-toolchain-v{version}.zip.sha256",
    }
    missing = sorted(expected - names)
    if missing:
        raise GitHubReleaseVerificationError(
            f"release assets are incomplete; missing: {', '.join(missing)}"
        )

    target = value.get("targetCommitish")
    if not isinstance(target, str) or not target.strip():
        raise GitHubReleaseVerificationError("release targetCommitish must be non-empty")
    url = value.get("url")
    if not isinstance(url, str) or not url.strip():
        raise GitHubReleaseVerificationError("release URL must be non-empty")

    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "tag": tag,
        "version": version,
        "target_commitish": target,
        "url": url,
        "assets": sorted(names),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--version", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        value = json.loads(args.metadata.read_text(encoding="utf-8"))
        result = validate_release_metadata(value, tag=args.tag, version=args.version)
    except (OSError, json.JSONDecodeError, GitHubReleaseVerificationError) as exc:
        print(f"GitHub Release verification failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
