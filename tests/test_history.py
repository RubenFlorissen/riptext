from __future__ import annotations

import unittest

from riptext.history import TransformHistory, TransformHistoryEntry


def entry(label: str, before: str, after: str) -> TransformHistoryEntry:
    return TransformHistoryEntry(
        label=label,
        slugs=(label.lower(),),
        before_text=before,
        after_text=after,
    )


class TransformHistoryTests(unittest.TestCase):
    def test_undo_redo_walks_transform_stack(self) -> None:
        history = TransformHistory()
        first = entry("Uppercase", "hello", "HELLO")
        second = entry("Trim", "HELLO ", "HELLO")

        self.assertTrue(history.record(first))
        self.assertTrue(history.record(second))

        self.assertEqual(history.undo(), second)
        self.assertEqual(history.undo(), first)
        self.assertIsNone(history.undo())

        self.assertEqual(history.redo(), first)
        self.assertEqual(history.redo(), second)
        self.assertIsNone(history.redo())

    def test_no_op_entries_are_skipped_and_new_records_clear_redo(self) -> None:
        history = TransformHistory()

        self.assertFalse(history.record(entry("Noop", "same", "same")))
        self.assertEqual(history.undo_count, 0)

        first = entry("Uppercase", "hello", "HELLO")
        second = entry("Lowercase", "HELLO", "hello")
        history.record(first)
        history.undo()
        self.assertEqual(history.redo_count, 1)

        history.record(second)

        self.assertEqual(history.redo_count, 0)
        self.assertEqual(history.undo(), second)

    def test_history_is_bounded_and_recent_is_newest_first(self) -> None:
        history = TransformHistory(max_entries=2)
        history.record(entry("One", "a", "b"))
        history.record(entry("Two", "b", "c"))
        history.record(entry("Three", "c", "d"))

        self.assertEqual(
            [item.label for item in history.recent()],
            ["Three", "Two"],
        )


if __name__ == "__main__":
    unittest.main()
