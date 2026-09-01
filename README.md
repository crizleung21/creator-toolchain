# Creator Toolchain

Creator Toolchain is a repository-first, Codex-native workflow system for planning creator work, executing approved plans, maintaining durable workspace state, governing contextual rules, developing Skills, and producing evidence-backed audits.

The stable release is **v1.1.0**. It preserves exactly seven core Skills and adds deterministic Python support for bootstrap, schema validation, atomic state mutation, execution lifecycle, recovery, behavior QA, clean installation, and reproducible release packaging.

## Install

Install the immutable marketplace snapshot, then install the Plugin:

```bash
codex plugin marketplace add crizleung21/creator-toolchain --ref v1.1.0 --json
codex plugin add creator-toolchain@creator-toolchain --json
```

Start a new Codex thread after installation. Do not enable the repository-local `.agents/skills/` source and the installed Plugin copy at the same time.

## Seven-Skill Architecture

| Skill | Responsibility |
|---|---|
| `creator-orchestrator` | Select one primary workflow and preserve explicit handoffs. |
| `creator-intake-planner` | Convert raw ideas into typed, acceptance-driven plans. |
| `creator-execution-cycle` | Execute approved plans through Plan, Execute, Verify, and Reconcile. |
| `creator-workspace-manager` | Own repository-local state, health, maintenance, and reconciliation. |
| `creator-rule-router` | Select, stage, approve, reject, recall, exclude, and audit rules. |
| `creator-skill-workbench` | Discover, scaffold, distill, score, and audit Skills. |
| `creator-evidence-audit` | Produce evidence-backed findings, remediation guidance, and execution handoffs. |

Python modules under `scripts/` are deterministic support beneath these Skills. They do not form an eighth core Skill.

## Core Workflow

```text
BOOTSTRAP
→ INTAKE
→ PLAN QUALITY GATE
→ APPROVAL
→ EXECUTION
→ VERIFICATION
→ RECONCILIATION
→ LEDGER APPEND
→ STATE UPDATE
→ RULE PREFLIGHT
→ HEALTH CHECK
→ AUDIT / REMEDIATION HANDOFF
```

## Quick Start

Validate or bootstrap a Creator workspace:

```bash
python3 scripts/bootstrap_creator_workspace.py --root . --dry-run
python3 scripts/bootstrap_creator_workspace.py --root .
python3 scripts/bootstrap_creator_workspace.py --root . --check
```

Validate the repository and package:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/sync_plugin_skills.py --check
python3 scripts/package_integrity.py \
  --root . \
  --package-root plugin/creator-toolchain \
  --check docs/qa/package-integrity-report.json
python3 scripts/validate_creator_toolchain.py --scope all
```

Run the unified release gate:

```bash
python3 scripts/release_creator_toolchain.py \
  --root . \
  --check \
  --commit-sha "$(git rev-parse HEAD)"
```

Build the reproducible Plugin archive through the unified release command:

```bash
python3 scripts/release_creator_toolchain.py \
  --root . \
  --build \
  --output-dir dist \
  --commit-sha "$(git rev-parse HEAD)"
```

The low-level deterministic archive builder remains available for direct packaging checks:

```bash
python3 scripts/build_plugin_package.py \
  --root . \
  --output dist/creator-toolchain-v1.1.0.zip
```

## State Contract

Creator workspace state uses schema `0.4.0`. Canonical surfaces live under `.creator/`, are owned by the declared workflow, and must be validated before and after atomic mutation. See [`docs/architecture/state-contract.md`](docs/architecture/state-contract.md).

## Operations

- [Bootstrap](docs/operations/bootstrap.md)
- [Execution lifecycle](docs/operations/execution-lifecycle.md)
- [Recovery](docs/operations/recovery.md)
- [Release](docs/operations/release.md)
- [Troubleshooting](docs/operations/troubleshooting.md)

## Release Evidence

The release process requires all 18 gates to pass, including 34/34 Behavior Acceptance cases, writable Golden E2E, green Health, exact package integrity, byte-identical ZIP output, clean installation, and discovery of exactly seven Skills.

Canonical evidence lives in:

```text
docs/qa/package-integrity-report.json
docs/qa/behavior-acceptance-report.json
docs/qa/behavior-acceptance-status.json
docs/qa/release-evidence.json
docs/qa/final-release-status.json
```

## Distribution and License

The runtime Plugin contains its manifest, documentation, MIT license, and generated Skill mirror only. Private workspace state, development scripts, tests, and build evidence are not packaged.

Creator Toolchain is released under the [MIT License](LICENSE).
