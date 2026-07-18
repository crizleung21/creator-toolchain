from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_intake_artifacts import create_intake_package
from scripts.creator_intake_workflow import (
    IntakeWorkflowError,
    approve_intake,
    handoff_intake,
    inspect_registration_proposal,
    scaffold_intake,
)
from scripts.creator_ledger import read_events

ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = "2026-07-18T00:00:00Z"
APPROVED_AT = "2026-07-18T01:00:00Z"
COMPLETED_AT = "2026-07-18T02:00:00Z"


def complete_request() -> dict[str, object]:
    return {
        "title": "Creator Asset Naming Checker",
        "project_type": "utility",
        "goal": "Create a deterministic naming checker.",
        "context": "A reusable creator workflow needs safe asset names.",
        "scope": ["Manifest input", "Validation report"],
        "out_of_scope": ["Automatic renaming"],
        "acceptance_criteria": [
            {"id": "AC-1", "title": "Duplicates", "given": "duplicates", "when": "checked", "then": "duplicates are listed"},
            {"id": "AC-2", "title": "Invalid", "given": "invalid names", "when": "checked", "then": "rules are listed"},
            {"id": "AC-3", "title": "Repeatable", "given": "same input", "when": "run twice", "then": "output matches"},
        ],
        "risks": ["Unsafe paths"],
    }


def initialize(root: Path, request: dict[str, object] | None = None) -> tuple[str, Path]:
    creator = root / ".creator"
    creator.mkdir(parents=True, exist_ok=True)
    (creator / "projects.json").write_text('{"sentinel":"unchanged"}\n', encoding="utf-8")
    result = create_intake_package(root, request or complete_request(), timestamp=CREATED_AT, registry_root=ROOT)
    return result["slug"], Path(result["plan_dir"])


class CreatorIntakeWorkflowTests(unittest.TestCase):
    def test_approval_creates_staged_proposal_without_mutating_projects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slug, plan_dir = initialize(root)
            projects = root / ".creator/projects.json"
            before = projects.read_bytes()
            result = approve_intake(
                root, slug, actor="crizleung21", decision="handoff-to-execution", timestamp=APPROVED_AT
            )
            self.assertEqual(projects.read_bytes(), before)
            proposal = inspect_registration_proposal(root, slug)
            self.assertEqual(proposal["status"], "staged")
            self.assertEqual(proposal["owner_skill"], "creator-workspace-manager")
            self.assertEqual(proposal["project"]["status"], "approved")
            self.assertEqual(result["state_registration_proposal"], str(root / proposal["proposal_path"]))
            project = json.loads((plan_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["approval_status"], "approved")
            self.assertEqual(project["approval_decision"], "handoff-to-execution")
            self.assertIn("crizleung21", (plan_dir / "DECISIONS.md").read_text(encoding="utf-8"))

    def test_failed_gate_cannot_be_approved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = complete_request()
            request["blocking_questions"] = ["Which naming policy is authoritative?"]
            slug, plan_dir = initialize(root, request)
            before = {path.name: path.read_bytes() for path in plan_dir.iterdir()}
            with self.assertRaises(IntakeWorkflowError):
                approve_intake(root, slug, actor="owner", decision="scaffold-only", timestamp=APPROVED_AT)
            self.assertEqual(before, {path.name: path.read_bytes() for path in plan_dir.iterdir()})

    def test_scaffold_only_generates_documents_and_never_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slug, plan_dir = initialize(root)
            approve_intake(root, slug, actor="owner", decision="scaffold-only", timestamp=APPROVED_AT)
            result = scaffold_intake(root, slug, timestamp=COMPLETED_AT)
            scaffold = Path(result["scaffold_path"])
            self.assertEqual({path.name for path in scaffold.iterdir()}, {"PROJECT.md", "README.md", "HANDOFF.md"})
            self.assertFalse(any(path.suffix == ".py" for path in scaffold.rglob("*")))
            self.assertIn("Execution authorized: `false`", (scaffold / "HANDOFF.md").read_text(encoding="utf-8"))
            project = json.loads((plan_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["stage"], "graduated")
            self.assertEqual(project["scaffold_path"], ".creator/scaffolds/creator-asset-naming-checker")
            self.assertEqual([event["phase"] for event in read_events(plan_dir / "activity_ledger.jsonl")], ["intake", "gate", "approval", "scaffold"])

    def test_execution_handoff_requires_matching_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slug, plan_dir = initialize(root)
            approve_intake(root, slug, actor="owner", decision="scaffold-only", timestamp=APPROVED_AT)
            before = {path.name: path.read_bytes() for path in plan_dir.iterdir()}
            with self.assertRaises(IntakeWorkflowError):
                handoff_intake(root, slug, timestamp=COMPLETED_AT)
            self.assertEqual(before, {path.name: path.read_bytes() for path in plan_dir.iterdir()})

    def test_execution_handoff_is_schema_valid_and_targets_execution_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slug, plan_dir = initialize(root)
            approve_intake(root, slug, actor="owner", decision="handoff-to-execution", timestamp=APPROVED_AT)
            result = handoff_intake(root, slug, timestamp=COMPLETED_AT)
            payload = json.loads(Path(result["execution_handoff_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["target_skill"], "creator-execution-cycle")
            self.assertEqual(payload["approval_decision"], "handoff-to-execution")
            self.assertEqual(len(payload["artifact_paths"]), 7)
            project = json.loads((plan_dir / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["stage"], "graduated")
            self.assertEqual(project["execution_handoff_path"], f".creator/handoffs/{project['project_id']}.json")
            self.assertEqual([event["phase"] for event in read_events(plan_dir / "activity_ledger.jsonl")], ["intake", "gate", "approval", "handoff"])

    def test_approval_is_explicit_and_cannot_be_repeated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slug, _ = initialize(root)
            approve_intake(root, slug, actor="owner", decision="scaffold-only", timestamp=APPROVED_AT)
            with self.assertRaises(IntakeWorkflowError):
                approve_intake(root, slug, actor="owner", decision="scaffold-only", timestamp=APPROVED_AT)

    def test_custom_scaffold_output_must_remain_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            slug, _ = initialize(root)
            approve_intake(root, slug, actor="owner", decision="scaffold-only", timestamp=APPROVED_AT)
            with self.assertRaises(IntakeWorkflowError):
                scaffold_intake(root, slug, output=Path(outside) / "scaffold", timestamp=COMPLETED_AT)


if __name__ == "__main__":
    unittest.main()
