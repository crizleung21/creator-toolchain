from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creator_transactions import TransactionError, atomic_write_text


class CreatorTransactionTests(unittest.TestCase):
    def test_atomic_write_replaces_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("old\n", encoding="utf-8")
            atomic_write_text(path, "new\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "new\n")

    def test_validation_failure_restores_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("old\n", encoding="utf-8")
            def fail(_: Path) -> None:
                raise ValueError("invalid")
            with self.assertRaises(TransactionError):
                atomic_write_text(path, "new\n", validator=fail)
            self.assertEqual(path.read_text(encoding="utf-8"), "old\n")

    def test_symlink_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("source", encoding="utf-8")
            link = root / "link.txt"
            try:
                link.symlink_to(source)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(TransactionError):
                atomic_write_text(link, "changed")


if __name__ == "__main__":
    unittest.main()
