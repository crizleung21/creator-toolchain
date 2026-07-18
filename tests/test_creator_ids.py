from __future__ import annotations

import unittest

from scripts.creator_ids import CreatorIdError, deterministic_id, validate_id


class CreatorIdTests(unittest.TestCase):
    def test_deterministic_id_is_stable(self) -> None:
        self.assertEqual(deterministic_id("PROJECT", "creator-toolchain", 1), deterministic_id("PROJECT", "creator-toolchain", 1))

    def test_different_input_changes_id(self) -> None:
        self.assertNotEqual(deterministic_id("EVENT", 1), deterministic_id("EVENT", 2))

    def test_validate_prefix(self) -> None:
        value = deterministic_id("TASK", "a")
        self.assertEqual(validate_id(value, prefix="TASK"), value)
        with self.assertRaises(CreatorIdError):
            validate_id(value, prefix="PROJECT")

    def test_invalid_prefix_is_rejected(self) -> None:
        with self.assertRaises(CreatorIdError):
            deterministic_id("bad-prefix", "a")


if __name__ == "__main__":
    unittest.main()
