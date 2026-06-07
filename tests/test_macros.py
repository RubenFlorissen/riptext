from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from riptext import favorites, macros


class MacroPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.old_macros_dir = macros.MACROS_DIR
        self.old_state_file = favorites.STATE_FILE
        macros.MACROS_DIR = root / "macros"
        favorites.STATE_FILE = root / "state.json"

    def tearDown(self) -> None:
        macros.MACROS_DIR = self.old_macros_dir
        favorites.STATE_FILE = self.old_state_file
        self.temp_dir.cleanup()

    def test_save_list_rename_and_delete_macro(self) -> None:
        path = macros.save_macro("Clean JSON!", ["trim", "json_prettify"])

        self.assertEqual(path.name, "clean_json.json")
        self.assertEqual(
            macros.list_macros(),
            [
                {
                    "name": "Clean JSON!",
                    "slug": "clean_json",
                    "slugs": ["trim", "json_prettify"],
                    "path": str(path),
                }
            ],
        )

        renamed_path = macros.rename_macro("Clean JSON!", "Pretty JSON")

        self.assertIsNotNone(renamed_path)
        assert renamed_path is not None
        self.assertEqual(renamed_path.name, "pretty_json.json")
        self.assertFalse(path.exists())
        self.assertEqual(macros.list_macros()[0]["name"], "Pretty JSON")

        self.assertTrue(macros.delete_macro("Pretty JSON"))
        self.assertEqual(macros.list_macros(), [])

    def test_macro_favorites_can_rename_and_remove(self) -> None:
        self.assertTrue(favorites.toggle_favorite_macro("clean_json"))
        self.assertTrue(favorites.is_favorite_macro("clean_json"))

        favorites.rename_favorite_macro("clean_json", "pretty_json")

        self.assertFalse(favorites.is_favorite_macro("clean_json"))
        self.assertTrue(favorites.is_favorite_macro("pretty_json"))

        favorites.remove_favorite_macro("pretty_json")

        self.assertFalse(favorites.is_favorite_macro("pretty_json"))

    def test_malformed_state_file_falls_back_to_empty_lists(self) -> None:
        favorites.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        favorites.STATE_FILE.write_text("[]", encoding="utf-8")

        self.assertEqual(favorites.get_favorites(), [])
        self.assertEqual(favorites.get_recent(), [])
        self.assertEqual(favorites.get_script_priority("trim"), (1, 999, 999))

    def test_rename_macro_does_not_overwrite_existing_macro(self) -> None:
        first_path = macros.save_macro("First Macro", ["trim"])
        second_path = macros.save_macro("Second Macro", ["json_prettify"])

        renamed_path = macros.rename_macro("First Macro", "Second Macro")

        self.assertIsNone(renamed_path)
        self.assertTrue(first_path.exists())
        self.assertTrue(second_path.exists())
        self.assertEqual(
            [macro["name"] for macro in macros.list_macros()],
            ["First Macro", "Second Macro"],
        )


if __name__ == "__main__":
    unittest.main()
