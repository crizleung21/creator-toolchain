# Creator Toolchain Plugin Package

This package bundles the Creator Toolchain skill suite.

## Contents

- `.codex-plugin/plugin.json`
- `skills/` generated from the repository's authoritative `.agents/skills/` source
- `release-evidence/`

## Generated Skill Mirror

Run from repository root:

```bash
python3 scripts/materialize_seed_type_refs.py
python3 scripts/sync_plugin_skills.py --write
python3 scripts/sync_plugin_skills.py --check
```

Do not hand-edit `plugin/creator-toolchain/skills/`. Repo-local and installed plugin copies should not be enabled together except during an explicit collision or provenance test.

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
