#!/usr/bin/env python3
"""Verify stable GitHub Release metadata emitted by the GitHub CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ReleaseVerificationError(RuntimeError):
    """Raised when a GitHub Release is missing required stable-release properties."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseVerificationError(f"cannot load GitHub Release JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseVerificationError("GitHub Release JSON root must be an object")
    return value


def verify_release(path: Path, *, tag: str, version: str) -> dict[str, Any]:
    release = _load(Path(path))
    if release.get("tagName") != tag:
        raise ReleaseVerificationError(
            f"release tag mismatch: expected {tag!r}, got {release.get('tagName')!r}"
        )
    if release.get("isDraft") is not False:
        raise ReleaseVerificationError("release must not be a draft")
    if release.get("isPrerelease") is not False:
        raise ReleaseVerificationError("release must not be a prerelease")

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ReleaseVerificationError("release assets must be an array")
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
        raise ReleaseVerificationError(
            "release assets are incomplete: missing " + ", ".join(missing)
        )

    url = release.get("url")
    if not isinstance(url, str) or not url.startswith("https://github.com/"):
        raise ReleaseVerificationError("release URL is missing or invalid")

    return {
        "status": "PASS",
        "tag": tag,
        "version": version,
        "url": url,
        "asset_names": sorted(names),
        "target_commitish": release.get("targetCommitish"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_release(
            args.input,
            tag=args.tag,
            version=args.version,
        )
    except ReleaseVerificationError as exc:
        print(f"GitHub Release verification failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
