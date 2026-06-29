# Creator Toolchain

Creator Toolchain is a Codex-native skill suite for planning creator work, executing accepted plans, maintaining repository state, routing domain rules, building skills, and producing evidence-based reviews.

## Install

Install the immutable `v1.0.1` marketplace snapshot, then install the plugin:

```bash
codex plugin marketplace add crizleung21/creator-toolchain --ref v1.0.1 --json
codex plugin add creator-toolchain@creator-toolchain --json
```

Start a new Codex thread after installation. Do not enable the repository-local and installed plugin copies together.

## Skill Suite

| Skill | Purpose |
|---|---|
| `creator-orchestrator` | Route a request to the correct Creator Toolchain workflow. |
| `creator-intake-planner` | Turn raw ideas into typed, acceptance-driven plans. |
| `creator-execution-cycle` | Execute accepted plans through Plan, Execute, Verify, and Reconcile. |
| `creator-workspace-manager` | Manage repository-local state, health, maintenance, and surfaces. |
| `creator-rule-router` | Select, stage, recall, exclude, and review domain rules. |
| `creator-skill-workbench` | Discover, scaffold, distill, score, and review Codex skills. |
| `creator-evidence-audit` | Produce evidence-first findings and execution-ready handoffs. |

## Development

Authoritative skills live under `.agents/skills/`. The plugin mirror is generated and must remain byte-equivalent:

```bash
python3 scripts/sync_plugin_skills.py --write
python3 scripts/sync_plugin_skills.py --check
```

Validate repository, state, plugin, and package contracts:

```bash
python3 scripts/package_integrity.py \
  --root . \
  --package-root plugin/creator-toolchain \
  --check docs/qa/package-integrity-report.json

python3 scripts/validate_creator_toolchain.py --scope all
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Build a reproducible release archive:

```bash
python3 scripts/build_plugin_package.py \
  --root . \
  --output dist/creator-toolchain-v1.0.1.zip
```

## Distribution and License

The runtime plugin contains its manifest, documentation, MIT license, and generated skills only. Creator Toolchain is distributed through the GitHub release and Git-backed marketplace under the [MIT License](LICENSE).
