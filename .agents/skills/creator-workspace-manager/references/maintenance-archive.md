# Maintenance and Archive Guardrails

## Non-Destructive Two-Step Archive

```bash
python3 scripts/creator_workspace_maintenance.py archive-plan \
  --root . --target .creator/plans/example --actor ACTOR --reason REASON

python3 scripts/creator_workspace_maintenance.py archive-status \
  --root . --proposal .creator/maintenance/archive-proposals/ARCHIVE-ID.json

python3 scripts/creator_workspace_maintenance.py archive-apply \
  --root . \
  --proposal .creator/maintenance/archive-proposals/ARCHIVE-ID.json \
  --actor ACTOR \
  --confirm ARCHIVE-ID
```

`archive-plan` records target type, digest, destination, actor, and reason without moving the target. `archive-apply` requires the exact proposal ID as confirmation, rechecks references and digest, atomically moves the target under `.creator/archive/`, writes a receipt and ledger event, and recalculates health.

## Prohibited Targets

- all ten root state surfaces;
- `.creator/archive/`, `.creator/maintenance/`, `.creator/health/`, and `.creator/reconciliation/`;
- targets outside `.creator/`;
- symlinks or directories containing symlinks;
- targets still referenced by active workspace JSON evidence;
- targets changed after proposal creation.

The workflow does not provide deletion. A failed apply restores the original path and all touched state evidence.
