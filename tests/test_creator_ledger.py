from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creator_ledger import LedgerError, append_event, new_event, read_events


class CreatorLedgerTests(unittest.TestCase):
    def test_append_preserves_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            append_event(path, new_event(event_id="EVENT-AAAAAAAA", sequence=1, phase="plan", task_id="TASK-AAAAAAAA", artifact="PLAN.md", status="IN_PROGRESS", ts="2026-07-16T00:00:00Z"))
            append_event(path, new_event(event_id="EVENT-BBBBBBBB", sequence=2, phase="verify", task_id="TASK-AAAAAAAA", artifact="VERIFY.md", status="DONE", ts="2026-07-16T00:01:00Z"))
            self.assertEqual([item["sequence"] for item in read_events(path)], [1, 2])

    def test_duplicate_event_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            event = new_event(event_id="EVENT-AAAAAAAA", sequence=1, phase="plan", task_id="TASK-AAAAAAAA", artifact="PLAN.md", status="IN_PROGRESS", ts="2026-07-16T00:00:00Z")
            append_event(path, event)
            with self.assertRaises(LedgerError):
                append_event(path, {**event, "sequence": 2})

    def test_out_of_order_sequence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            with self.assertRaises(LedgerError):
                append_event(path, new_event(event_id="EVENT-AAAAAAAA", sequence=2, phase="plan", task_id="TASK-AAAAAAAA", artifact="PLAN.md", status="IN_PROGRESS", ts="2026-07-16T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
