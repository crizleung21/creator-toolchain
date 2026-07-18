from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_execution_lifecycle import (
    ExecutionLifecycleError,
    initialize_execution,
    inspect_execution,
    record_verification,
    transition_execution,
    transition_task,
)

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T05:00:00Z"
PROJECT_ID = "PROJECT-AAAAAAAA"


class CreatorExecutionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.handoff_relative = f".creator/handoffs/{PROJECT_ID}.json"
        plan_dir = self.root / ".creator/plans/demo"
        plan_dir.mkdir(parents=True)
        artifact_paths = []
        for name in (
            "project.json",
            "activity_ledger.jsonl",
            "INTAKE-STATE.md",
            "PLANNING.md",
            "DECISIONS.md",
            "OPEN-QUESTIONS.md",
            "HANDOFF.md",
        ):
            path = plan_dir / name
            path.write_text("{}\n" if name.endswith(".json") else f"# {name}\n", encoding="utf-8")
            artifact_paths.append(path.relative_to(self.root).as_posix())
        handoff_path = self.root / self.handoff_relative
        handoff_path.parent.mkdir(parents=True)
        self.handoff = {
            "schema_version": "1.0.0",
            "project_id": PROJECT_ID,
            "source_plan": ".creator/plans/demo/PLANNING.md",
            "target_skill": "creator-execution-cycle",
            "quality_gate_result": "pass",
            "approval_status": "approved",
            "approval_decision": "handoff-to-execution",
            "approved_by": "tester",
            "approved_at": TIMESTAMP,
            "artifact_paths": artifact_paths,
            "open_questions": [],
            "generated_at": TIMESTAMP,
        }
        handoff_path.write_text(json.dumps(self.handoff, indent=2) + "\n", encoding="utf-8")
        self.tasks = [
            {
                "title": "Implement deterministic checker",
                "acceptance_criteria": ["Given valid input, when checked, then a deterministic report is produced."],
                "affected_files": ["src/checker.py"],
                "verification": {
                    "method": "command",
                    "command": "python3 -m unittest",
                    "expected_result": "Exit code 0 and deterministic output.",
                },
            }
        ]

    def _initialize(self):
        return initialize_execution(
            self.root,
            self.handoff_relative,
            self.tasks,
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )

    def _execution_dir(self) -> Path:
        return self.root / ".creator/executions" / PROJECT_ID

    def _task_id(self) -> str:
        tasks = json.loads((self._execution_dir() / "tasks.json").read_text(encoding="utf-8"))
        return tasks["tasks"][0]["task_id"]

    def test_initialize_requires_explicitly_approved_handoff(self) -> None:
        handoff_path = self.root / self.handoff_relative
        self.handoff["approval_status"] = "pending"
        handoff_path.write_text(json.dumps(self.handoff) + "\n", encoding="utf-8")
        with self.assertRaises(ExecutionLifecycleError):
            self._initialize()
        self.assertFalse(self._execution_dir().exists())

    def test_initialize_creates_approved_workspace_transactionally(self) -> None:
        result = self._initialize()
        self.assertEqual(result["current_state"], "APPROVED")
        self.assertEqual(result["task_statuses"], {"PLANNED": 1})
        self.assertEqual(result["ledger_event_count"], 1)
        self.assertEqual(
            {path.name for path in self._execution_dir().iterdir()},
            {"execution-state.json", "tasks.json", "PLAN-001.md", "activity_ledger.jsonl"},
        )

    def test_illegal_transition_leaves_all_bytes_unchanged(self) -> None:
        self._initialize()
        before = {path.name: path.read_bytes() for path in self._execution_dir().iterdir()}
        with self.assertRaises(ExecutionLifecycleError):
            transition_execution(
                self.root,
                PROJECT_ID,
                "VERIFYING",
                actor="tester",
                reason="skip execution",
                timestamp=TIMESTAMP,
                schema_root=ROOT,
            )
        after = {path.name: path.read_bytes() for path in self._execution_dir().iterdir()}
        self.assertEqual(before, after)

    def test_task_evidence_allows_reconciling(self) -> None:
        self._initialize()
        transition_execution(
            self.root,
            PROJECT_ID,
            "EXECUTING",
            actor="tester",
            reason="begin accepted tasks",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        task_id = self._task_id()
        transition_task(
            self.root,
            PROJECT_ID,
            task_id,
            "EXECUTING",
            actor="tester",
            reason="start task",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_task(
            self.root,
            PROJECT_ID,
            task_id,
            "EXECUTED",
            actor="tester",
            reason="implementation complete",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        transition_execution(
            self.root,
            PROJECT_ID,
            "VERIFYING",
            actor="tester",
            reason="verify task evidence",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        evidence = self.root / "evidence/task.txt"
        evidence.parent.mkdir()
        evidence.write_text("deterministic result\n", encoding="utf-8")
        record_verification(
            self.root,
            PROJECT_ID,
            task_id,
            result="PASS",
            actual_result="Command exited 0.",
            evidence_relative="evidence/task.txt",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        result = transition_execution(
            self.root,
            PROJECT_ID,
            "RECONCILING",
            actor="tester",
            reason="all tasks verified",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "RECONCILING")
        self.assertTrue(result["all_tasks_verified"])
        tasks = json.loads((self._execution_dir() / "tasks.json").read_text(encoding="utf-8"))
        verification = tasks["tasks"][0]["verification"]
        self.assertEqual(verification["status"], "PASS")
        self.assertEqual(len(verification["evidence_hash"]), 64)

    def test_missing_evidence_does_not_mutate_task_or_ledger(self) -> None:
        self._initialize()
        transition_execution(self.root, PROJECT_ID, "EXECUTING", actor="tester", reason="begin", timestamp=TIMESTAMP, schema_root=ROOT)
        task_id = self._task_id()
        transition_task(self.root, PROJECT_ID, task_id, "EXECUTING", actor="tester", reason="start", timestamp=TIMESTAMP, schema_root=ROOT)
        transition_task(self.root, PROJECT_ID, task_id, "EXECUTED", actor="tester", reason="complete", timestamp=TIMESTAMP, schema_root=ROOT)
        transition_execution(self.root, PROJECT_ID, "VERIFYING", actor="tester", reason="verify", timestamp=TIMESTAMP, schema_root=ROOT)
        tasks_path = self._execution_dir() / "tasks.json"
        ledger_path = self._execution_dir() / "activity_ledger.jsonl"
        before = (tasks_path.read_bytes(), ledger_path.read_bytes())
        with self.assertRaises(ExecutionLifecycleError):
            record_verification(
                self.root,
                PROJECT_ID,
                task_id,
                result="PASS",
                actual_result="claimed pass",
                evidence_relative="evidence/missing.txt",
                timestamp=TIMESTAMP,
                schema_root=ROOT,
            )
        self.assertEqual(before, (tasks_path.read_bytes(), ledger_path.read_bytes()))

    def test_terminal_completion_requires_closure_artifacts(self) -> None:
        self.test_task_evidence_allows_reconciling()
        with self.assertRaises(ExecutionLifecycleError):
            transition_execution(
                self.root,
                PROJECT_ID,
                "DONE",
                actor="tester",
                reason="claim completion",
                timestamp=TIMESTAMP,
                schema_root=ROOT,
            )

    def test_blocked_and_recovering_create_required_artifacts(self) -> None:
        self._initialize()
        result = transition_execution(
            self.root,
            PROJECT_ID,
            "BLOCKED",
            actor="tester",
            reason="dependency unavailable",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "BLOCKED")
        self.assertTrue((self._execution_dir() / "BLOCKER.md").is_file())
        result = transition_execution(
            self.root,
            PROJECT_ID,
            "RECOVERING",
            actor="tester",
            reason="dependency restored",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertEqual(result["current_state"], "RECOVERING")
        self.assertTrue((self._execution_dir() / "RECOVERY-PLAN.md").is_file())

    def test_status_is_read_only(self) -> None:
        self._initialize()
        before = {path.name: path.read_bytes() for path in self._execution_dir().iterdir()}
        result = inspect_execution(self.root, PROJECT_ID, schema_root=ROOT)
        after = {path.name: path.read_bytes() for path in self._execution_dir().iterdir()}
        self.assertEqual(result["current_state"], "APPROVED")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
