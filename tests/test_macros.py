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


if __name__ == "__main__":
    unittest.main()
