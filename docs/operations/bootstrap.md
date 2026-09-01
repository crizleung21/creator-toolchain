# Bootstrap Operations

## Purpose

Create or validate the ten schema `0.4.0` Creator workspace surfaces without overwriting existing user state.

## Preview

```bash
python3 scripts/bootstrap_creator_workspace.py \
  --root /path/to/workspace \
  --dry-run
```

## Create Missing Surfaces

```bash
python3 scripts/bootstrap_creator_workspace.py \
  --root /path/to/workspace \
  --workspace-id creator-workspace \
  --display-name "Creator Workspace"
```

Bootstrap is idempotent: valid existing surfaces are loaded and preserved; only missing canonical files are created.

## Validate

```bash
python3 scripts/bootstrap_creator_workspace.py \
  --root /path/to/workspace \
  --check
```

## Invariants

- paths remain inside the workspace;
- symlink escapes are rejected;
- existing non-empty state is not overwritten;
- generated surfaces pass schema and cross-file validation;
- failure does not leave partial state.

## Evidence

Record the command, exit code, generated path list, and subsequent `validate_creator_toolchain.py --scope state` result.
