from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riptext.core.execution import run_script
from riptext.core.scripts import load_builtin_scripts, validate_scripts


def builtin(slug: str):
    scripts = {script.slug: script for script in load_builtin_scripts()}
    return scripts[slug]


class BuiltinRipTests(unittest.TestCase):
    def test_builtin_scripts_validate_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostics = validate_scripts(Path(temp_dir))

        self.assertEqual(diagnostics, [])

    def test_new_text_rips_run_through_execution_pipeline(self) -> None:
        cases = [
            ("html_escape", "<b>R&D</b>", "&lt;b&gt;R&amp;D&lt;/b&gt;"),
            ("html_unescape", "&lt;b&gt;R&amp;D&lt;/b&gt;", "<b>R&D</b>"),
            ("slugify", "Hello, Wörld!", "hello-world"),
            ("strip_html", "<p>Hello <strong>world</strong></p>", "Hello world"),
            ("regex_extract", "\\d+\na1 b22 c333", "1\n22\n333"),
            ("regex_replace", "\\d+\n#\na1 b22", "a# b#"),
        ]

        for slug, text, expected in cases:
            with self.subTest(slug=slug):
                result, _, errors = run_script(builtin(slug), text, [])

                self.assertEqual(errors, [])
                self.assertEqual(result, expected)

    def test_timestamp_convert_handles_unix_and_iso(self) -> None:
        unix_result, _, unix_errors = run_script(
            builtin("timestamp_convert"),
            "0",
            [],
        )
        iso_result, _, iso_errors = run_script(
            builtin("timestamp_convert"),
            "1970-01-01T00:00:00+00:00",
            [],
        )

        self.assertEqual(unix_errors, [])
        self.assertEqual(iso_errors, [])
        self.assertEqual(unix_result, "1970-01-01T00:00:00+00:00")
        self.assertEqual(iso_result, "0")

    def test_yaml_json_conversion_rips(self) -> None:
        json_result, json_info, json_errors = run_script(
            builtin("yaml_to_json"),
            "name: riptext\ncount: 2\nitems:\n  - json\n  - yaml\n",
            [],
        )
        yaml_result, yaml_info, yaml_errors = run_script(
            builtin("json_to_yaml"),
            '{"name": "riptext", "count": 2, "items": ["json", "yaml"]}',
            [],
        )

        self.assertEqual(json_errors, [])
        self.assertEqual(yaml_errors, [])
        self.assertEqual(json_info, ["Converted YAML to JSON"])
        self.assertEqual(yaml_info, ["Converted JSON to YAML"])
        self.assertIn('"name": "riptext"', json_result)
        self.assertIn("items:\n- json\n- yaml\n", yaml_result)


if __name__ == "__main__":
    unittest.main()
