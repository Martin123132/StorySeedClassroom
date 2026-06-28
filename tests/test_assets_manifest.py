from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_assets.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_assets", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load asset checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AssetManifestTests(unittest.TestCase):
    def test_visual_asset_manifest_is_valid(self) -> None:
        checker = load_checker()
        self.assertEqual(checker.validate(PROJECT_ROOT), [])


if __name__ == "__main__":
    unittest.main()
