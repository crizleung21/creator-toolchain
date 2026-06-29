# Package Integrity

## Runtime Scope

The plugin package contains its manifest, README, changelog, MIT license, and the exact generated skill mirror. No other top-level entry is allowed.

## Safety Rules

The package rejects symbolic links, non-regular files, private state, environment files, caches, local overrides, nested archives, unknown skill files, and unknown top-level paths.

## Deterministic Inventory

`scripts/package_integrity.py` sorts package-relative POSIX paths, records every file SHA-256, and computes one combined payload SHA-256 from each relative path and file body.

The committed report has no timestamp or commit identifier. `--check` recomputes the complete report and fails on any difference.

## Reproducible Archive

`scripts/build_plugin_package.py` uses the validated inventory, sorted paths, fixed ZIP timestamps, and normalized file modes. Two builds from one tree must be byte-identical.

## Release Gate

Release requires a passing report, mirror parity, reproducible archive output, repository validation, current behavior acceptance, and CI validation.
