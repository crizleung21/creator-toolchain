# Package Integrity

## Runtime Scope

The Plugin package contains only:

```text
.codex-plugin/plugin.json
README.md
CHANGELOG.md
LICENSE
skills/<seven generated Skills>/**
```

No other top-level entry is allowed.

## Safety Rules

The package rejects symbolic links, non-regular files, private state, environment files, caches, local overrides, editor metadata, nested archives, unknown Skill files, and unknown paths.

## Deterministic Inventory

`scripts/package_integrity.py`:

1. derives the expected Skill files from `.agents/skills/`;
2. compares the generated Plugin mirror;
3. records every package-relative path and file SHA-256;
4. computes one payload SHA-256 from path bytes and file bytes;
5. emits a deterministic report without timestamps.

Validate the committed inventory:

```bash
python3 scripts/package_integrity.py \
  --root . \
  --package-root plugin/creator-toolchain \
  --check docs/qa/package-integrity-report.json
```

## Reproducible Archive

`scripts/build_plugin_package.py` uses sorted paths, fixed ZIP timestamps, normalized file modes, and deterministic compression. Two builds from the same tree must be byte-identical and produce a matching `.sha256` sidecar.

## Release Gate

Release requires:

- mirror parity;
- exact package inventory;
- current 34/34 Behavior Acceptance for the package payload;
- repository and schema validation;
- byte-identical ZIP builds;
- clean installation;
- discovery of exactly seven Skills;
- green Health;
- successful final CI.
