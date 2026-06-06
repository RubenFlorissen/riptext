from __future__ import annotations

import unittest

from riptext.selection import loc_to_offset, offset_to_loc


class SelectionOffsetTests(unittest.TestCase):
    def test_offset_to_loc_round_trips_with_loc_to_offset(self) -> None:
        text = "alpha\nbeta\ngamma"

        for location in [(0, 0), (0, 3), (1, 0), (1, 4), (2, 5)]:
            with self.subTest(location=location):
                offset = loc_to_offset(text, *location)

                self.assertEqual(offset_to_loc(text, offset), location)

    def test_offset_to_loc_clamps_to_document_bounds(self) -> None:
        text = "alpha\nbeta"

        self.assertEqual(offset_to_loc(text, -10), (0, 0))
        self.assertEqual(offset_to_loc(text, 999), (1, 4))


if __name__ == "__main__":
    unittest.main()
