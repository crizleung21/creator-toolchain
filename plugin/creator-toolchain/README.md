# Creator Toolchain Plugin Package

This package bundles the Creator Toolchain skill suite.

## Contents

- `.codex-plugin/plugin.json`
- `skills/`
- `release-evidence/`

## Trust Policy

- Hooks are absent by default.
- MCP/app integrations are absent by default.
- User-private `.creator/` state must not be bundled.
- `upstream/` research clones must not be bundled.
- The manifest is a draft until validated against the current Codex plugin schema.

## Local Test

Run from repo root:

```bash
python3 scripts/validate_creator_toolchain.py
```
