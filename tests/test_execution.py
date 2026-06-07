from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riptext.core.execution import run_script, run_script_sequence
from riptext.core.models import SelectionRange
from riptext.core.scripts import load_user_scripts


class MultiSelectionExecutionTests(unittest.TestCase):
    def _script_from_text(self, text: str):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        script_path = Path(temp_dir.name) / "test_rip.py"
        script_path.write_text(text, encoding="utf-8")
        return load_user_scripts(Path(temp_dir.name))[0]

    def _scripts_from_texts(self, texts: list[str]):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        script_dir = Path(temp_dir.name)
        for index, text in enumerate(texts):
            (script_dir / f"test_rip_{index}.py").write_text(text, encoding="utf-8")
        return {script.slug: script for script in load_user_scripts(script_dir)}

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

    def test_script_sequence_keeps_selection_target_across_steps(self) -> None:
        scripts = self._scripts_from_texts(
            [
                '''"""
{
  "name": "Wrap",
  "slug": "wrap",
  "description": "Wrap text",
  "tags": []
}
"""


def transform(text: str) -> str:
    return f"[{text}]"
''',
                '''"""
{
  "name": "Bang",
  "slug": "bang",
  "description": "Add bang",
  "tags": []
}
"""


def transform(text: str) -> str:
    return f"{text}!"
''',
            ]
        )

        result, _, errors = run_script_sequence(
            [scripts["wrap"], scripts["bang"]],
            "aa bb cc",
            [SelectionRange(3, 5)],
        )

        self.assertEqual(errors, [])
        self.assertEqual(result, "aa [bb]! cc")

    def test_sequence_selection_execution_sees_full_contract(self) -> None:
        script = self._script_from_text(
            '''"""
{
  "name": "Selection Contract",
  "slug": "selection_contract",
  "description": "Uses execution contract",
  "tags": []
}
"""


def main(exec):
    exec.insert(
        f"{exec.text}:{len(exec.full_text)}:{exec.is_selection}:{len(exec.selection)}"
    )
'''
        )

        result, _, errors = run_script_sequence(
            [script],
            "aa bb",
            [SelectionRange(0, 2), SelectionRange(3, 5)],
        )

        self.assertEqual(errors, [])
        self.assertEqual(result, "aa:5:True:2 bb:5:True:2")

    def test_insert_is_discarded_when_script_raises(self) -> None:
        script = self._script_from_text(
            '''"""
{
  "name": "Insert Then Raise",
  "slug": "insert_then_raise",
  "description": "Fails after inserting",
  "tags": []
}
"""


def main(exec):
    exec.insert("changed")
    raise RuntimeError("boom")
'''
        )

        result, _, errors = run_script(script, "original", [])

        self.assertEqual(result, "original")
        self.assertEqual(errors, ["Script error: boom"])


if __name__ == "__main__":
    unittest.main()
