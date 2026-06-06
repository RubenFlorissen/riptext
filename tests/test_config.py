from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riptext.config import RiptextConfig, load_config


class ConfigTests(unittest.TestCase):
    def test_missing_config_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_config(Path(temp_dir) / "missing.toml")

        self.assertEqual(config, RiptextConfig())

    def test_loads_supported_config_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.toml"
            path.write_text(
                """
user_rips_dir = "~/custom-rips"
default_mode = "lines"

[display]
show_line_numbers = false
word_wrap = true

[keybindings]
open_palette = "ctrl+p"
redo = "ctrl+shift+z"
""",
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.user_rips_dir, Path("~/custom-rips").expanduser())
        self.assertEqual(config.default_mode, "lines")
        self.assertFalse(config.show_line_numbers)
        self.assertTrue(config.word_wrap)
        self.assertEqual(
            config.keybindings,
            {"open_palette": "ctrl+p", "redo": "ctrl+shift+z"},
        )

    def test_invalid_default_mode_falls_back_to_full(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.toml"
            path.write_text('default_mode = "everything"\n', encoding="utf-8")

            config = load_config(path)

        self.assertEqual(config.default_mode, "full")


if __name__ == "__main__":
    unittest.main()
