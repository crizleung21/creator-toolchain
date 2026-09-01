#!/usr/bin/env python3
"""Validate Creator Toolchain using VERSION as the authoritative release version."""

from __future__ import annotations

from pathlib import Path

try:
    import validate_creator_toolchain_impl as _impl
    from versioning import read_version
except ImportError:  # Imported as scripts.validate_creator_toolchain in tests.
    from scripts import validate_creator_toolchain_impl as _impl
    from scripts.versioning import read_version

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PLUGIN_VERSION = read_version(ROOT)
_impl.CURRENT_PLUGIN_VERSION = CURRENT_PLUGIN_VERSION

for _name in dir(_impl):
    if not _name.startswith("__") and _name != "CURRENT_PLUGIN_VERSION":
        globals()[_name] = getattr(_impl, _name)


if __name__ == "__main__":
    raise SystemExit(_impl.main())
