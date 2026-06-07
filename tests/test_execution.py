from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riptext.core.execution import run_script
from riptext.core.models import SelectionRange
from riptext.core.scripts import load_user_scripts


class MultiSelectionExecutionTests(unittest.TestCase):
    def _script_from_text(self, text: str):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        script_path = Path(temp_dir.name) / "test_rip.py"
        script_path.write_text(text, encoding="utf-8")
        return load_user_scripts(Path(temp_dir.name))[0]

    def test_multiple_selections_are_replaced_independently(self) -> None:
        script = self._script_from_text(
            '''"""
{
  "name": "Wrap",
  "slug": "wrap",
  "description": "Wrap text",
  "tags": []
}
"""


def transform(text: str) -> str:
    return f"[{text.upper()}]"
'''
        )

        result, _, errors = run_script(
            script,
            "one two three",
            [SelectionRange(0, 3), SelectionRange(8, 13)],
        )

        self.assertEqual(errors, [])
        self.assertEqual(result, "[ONE] two [THREE]")

    def test_selection_execution_sees_original_full_text(self) -> None:
        script = self._script_from_text(
            '''"""
{
  "name": "Full Text Length",
  "slug": "full_text_length",
  "description": "Uses full text",
  "tags": []
}
"""


def main(exec):
    exec.insert(f"{exec.text}:{len(exec.full_text)}")
'''
        )

        result, _, errors = run_script(
            script,
            "aa bb",
            [SelectionRange(0, 2), SelectionRange(3, 5)],
        )

        self.assertEqual(errors, [])
        self.assertEqual(result, "aa:5 bb:5")


if __name__ == "__main__":
    unittest.main()
