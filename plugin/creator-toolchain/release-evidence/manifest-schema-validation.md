# Manifest Schema Validation

## Evidence Header

- status: `PASS_LOCAL`
- tested_at: `2026-06-27T15:12:46+0800`
- tested_commit: `ab507f6807b838bf3b4d04a65ac28e45c7e1cd44`
- operating_system: `macOS 26.5.1 (25F80)`
- codex_cli: `0.142.3`
- python: `3.12.3`
- manifest_sha256: `39b97cbd956841eb7995349c159e8344ecfc1dde4e97c22e5a4f6e9996a608cc`
- official_reference: `https://developers.openai.com/codex/plugins/build`

## Commands and Results

```text
python3 $HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugin/creator-toolchain
exit: 0
result: Plugin validation passed

python3 scripts/validate_creator_toolchain.py --scope plugin
exit: 0
result: manifest, marketplace, mirror parity, and package hygiene passed
```

The manifest uses `name: creator-toolchain`, strict-semver prerelease version `1.0.0-draft`, `skills: ./skills/`, and a populated `interface` object. Hooks, apps, and MCP server fields are absent because no reviewed companion configuration is packaged.

## Limitation

This proves local schema ingestion and package validation for the tested Codex CLI. It is not public Plugin Directory approval. Re-run against the then-current official validator before any public release.
