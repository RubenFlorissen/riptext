from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riptext.core.scripts import load_user_scripts, validate_scripts
from riptext.core.search import rank_scripts


SCRIPT = '''"""
{
  "name": "JSON Pretty",
  "slug": "json_pretty",
  "description": "Format JSON",
  "tags": ["json", "format"],
  "aliases": ["prettify", "beautify"],
  "category": "Data",
  "bias": 0.0
}
"""


def transform(text: str) -> str:
    return text
'''


class ScriptMetadataTests(unittest.TestCase):
    def test_aliases_are_loaded_validated_and_ranked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "json_pretty.py"
            script_path.write_text(SCRIPT, encoding="utf-8")

            scripts = load_user_scripts(Path(temp_dir))
            diagnostics = validate_scripts(Path(temp_dir))
            matches = rank_scripts("beautify", scripts)

        self.assertEqual(scripts[0].aliases, ("prettify", "beautify"))
        self.assertEqual(diagnostics, [])
        self.assertEqual(matches[0].script.slug, "json_pretty")


if __name__ == "__main__":
    unittest.main()
