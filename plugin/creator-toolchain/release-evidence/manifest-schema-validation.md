# Manifest Schema Validation

## Evidence Header

- status: `PASS_LOCAL`
- tested_at: `2026-06-27T21:23:43+0800`
- tested_commit: `11d7e5991a2d0c00d4a392e23b52bc5311ed50f9`
- operating_system: `macOS 26.5.1 (25F80)`
- codex_cli: `0.142.3`
- python: `3.12.3`
- manifest_sha256: `5c4b0638284b565517364549bd9da62161db0c22f6fa76a9d660df1fc78cfb65`
- official_reference: `https://developers.openai.com/codex/plugins/build`

## Commands and Results

```text
/opt/miniconda3/bin/python3 $HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugin/creator-toolchain
exit: 0
result: Plugin validation passed

python3 scripts/validate_creator_toolchain.py --scope plugin
exit: 0
result: manifest, marketplace, mirror parity, and package hygiene passed
```

The Homebrew `python3` selected by the shell lacked `PyYAML`; the existing Miniconda runtime supplied the validator dependency without installing or changing packages.

The manifest uses `name: creator-toolchain`, strict-semver prerelease version `1.0.0-draft.1`, `skills: ./skills/`, and a populated `interface` object. Hooks, apps, and MCP server fields are absent because no reviewed companion configuration is packaged.

## Limitation

This proves local schema ingestion and package validation for the tested Codex CLI. It is not public Plugin Directory approval. Re-run against the then-current official validator before any public release.
