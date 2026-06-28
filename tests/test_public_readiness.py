from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PublicReadinessTests(unittest.TestCase):
    def test_public_docs_and_license_are_present(self) -> None:
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        license_text = (PROJECT_ROOT / "LICENSE.md").read_text(encoding="utf-8")

        self.assertIn("PolyForm Noncommercial License 1.0.0", license_text)
        self.assertIn("StorySeed Classroom is source-available", license_text)
        self.assertIn("docs/screenshots/storyseed-generate-desktop.png", readme)
        self.assertIn("docs/GITHUB_FEEDBACK.md", readme)
        self.assertIn("docs/SELF_TEST_GAUNTLET.md", readme)

    def test_public_screenshots_are_checked_in_ready(self) -> None:
        screenshots = [
            PROJECT_ROOT / "docs" / "screenshots" / "storyseed-generate-desktop.png",
            PROJECT_ROOT / "docs" / "screenshots" / "storyseed-generate-mobile-top.png",
            PROJECT_ROOT / "docs" / "screenshots" / "storyseed-prompt-forge-mobile.png",
        ]

        for screenshot in screenshots:
            with self.subTest(screenshot=screenshot.name):
                self.assertTrue(screenshot.exists())
                self.assertGreater(screenshot.stat().st_size, 20_000)


if __name__ == "__main__":
    unittest.main()
