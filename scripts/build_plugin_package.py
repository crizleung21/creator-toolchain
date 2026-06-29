#!/usr/bin/env python3
"""Build a reproducible Creator Toolchain plugin ZIP and checksum sidecar."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

try:
    from package_integrity import enumerate_package_files
except ImportError:  # Imported as scripts.build_plugin_package in tests.
    from scripts.package_integrity import enumerate_package_files


ARCHIVE_PREFIX = "creator-toolchain"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
REGULAR_FILE_MODE = 0o100644


def build_plugin_package(root: Path, output: Path) -> dict[str, object]:
    root = root.resolve()
    package_root = root / "plugin/creator-toolchain"
    files = enumerate_package_files(root, package_root)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    with zipfile.ZipFile(
        temporary,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            relative = path.relative_to(package_root).as_posix()
            info = zipfile.ZipInfo(f"{ARCHIVE_PREFIX}/{relative}", FIXED_TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = REGULAR_FILE_MODE << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    temporary.replace(output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    sidecar = output.with_name(output.name + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {"output": str(output), "sha256": digest, "file_count": len(files)}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = build_plugin_package(args.root, args.output)
    print(f"Built {result['file_count']} files: {result['output']}")
    print(f"SHA-256: {result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
