from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest


class StorageTests(unittest.TestCase):
    def test_storage_saves_state_favourite_and_exports(self) -> None:
        base = os.getenv("STORYSEED_TEST_TMP") or tempfile.gettempdir()
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            old_home = os.environ.get("STORYSEED_HOME")
            old_disable_open = os.environ.get("STORYSEED_DISABLE_OPEN")
            os.environ["STORYSEED_HOME"] = tmp
            os.environ.pop("STORYSEED_DISABLE_OPEN", None)
            try:
                from storyseed_app import storage
                from storyseed_app.engine import generate_prompt

                state = storage.load_default_state()
                state["characters"][0]["name"] = "Test Learner"
                storage.save_state(state)
                self.assertEqual(storage.load_state()["characters"][0]["name"], "Test Learner")

                prompt = generate_prompt(storage.load_state(), {"seed": 42})
                favourite = storage.save_favourite(prompt)
                self.assertEqual(storage.list_favourites()[0]["id"], favourite["id"])

                txt = storage.export_prompt(prompt, "txt")
                html = storage.export_prompt(prompt, "html")
                self.assertTrue(Path(txt["path"]).exists())
                self.assertTrue(Path(html["path"]).exists())
                self.assertIn("StorySeed Classroom Worksheet", Path(html["path"]).read_text(encoding="utf-8"))
                self.assertTrue(str(txt["path"]).startswith(tmp))

                opened_paths = []
                result = storage.open_exports_folder(opener=lambda path: opened_paths.append(path))
                self.assertTrue(result["opened"])
                self.assertEqual(opened_paths[0], Path(tmp, "exports").resolve())

                opened_files = []
                file_result = storage.open_export_file(html["path"], opener=lambda path: opened_files.append(path))
                self.assertTrue(file_result["opened"])
                self.assertEqual(opened_files[0], Path(html["path"]).resolve())

                outside = Path(tmp, "outside.html")
                outside.write_text("not an export", encoding="utf-8")
                refused = storage.open_export_file(str(outside), opener=lambda path: opened_files.append(path))
                self.assertFalse(refused["opened"])
                self.assertIn("outside the StorySeed exports folder", refused["error"])
            finally:
                if old_home is None:
                    os.environ.pop("STORYSEED_HOME", None)
                else:
                    os.environ["STORYSEED_HOME"] = old_home
                if old_disable_open is None:
                    os.environ.pop("STORYSEED_DISABLE_OPEN", None)
                else:
                    os.environ["STORYSEED_DISABLE_OPEN"] = old_disable_open

    def test_existing_state_is_normalized_with_new_subject_packs(self) -> None:
        base = os.getenv("STORYSEED_TEST_TMP") or tempfile.gettempdir()
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            old_home = os.environ.get("STORYSEED_HOME")
            os.environ["STORYSEED_HOME"] = tmp
            try:
                from storyseed_app import storage

                old_state = storage.load_default_state()
                old_state.pop("subject_packs", None)
                storage.save_state(old_state)
                raw_path = storage.user_state_path()
                raw_text = raw_path.read_text(encoding="utf-8").replace(',\n  "subject_packs"', ',\n  "_removed_subject_packs"')
                raw_path.write_text(raw_text, encoding="utf-8")

                loaded = storage.load_state()
                self.assertIn("subject_packs", loaded)
                self.assertIn("Science", loaded["subject_packs"])
            finally:
                if old_home is None:
                    os.environ.pop("STORYSEED_HOME", None)
                else:
                    os.environ["STORYSEED_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
