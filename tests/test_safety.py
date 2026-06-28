from __future__ import annotations

import unittest

from storyseed_app.safety import check_state
from storyseed_app.storage import load_default_state


class SafetyTests(unittest.TestCase):
    def test_default_seed_bank_is_green(self) -> None:
        report = check_state(load_default_state())

        self.assertEqual(report["status"], "green")
        self.assertFalse(report["issues"])
        self.assertGreaterEqual(report["counts"]["characters"], 3)

    def test_missing_structured_fields_are_reported(self) -> None:
        state = load_default_state()
        state["characters"] = [{"name": "A learner", "trait": "", "wish": ""}]
        state["vocabulary"]["8-11"] = ["orbit", "orbit"]

        report = check_state(state)

        self.assertEqual(report["status"], "amber")
        messages = " ".join(issue["message"] for issue in report["issues"])
        self.assertIn("missing trait", messages)
        self.assertIn("repeats", messages)

    def test_empty_required_seed_bank_is_red(self) -> None:
        state = load_default_state()
        state["objects"] = []

        report = check_state(state)

        self.assertEqual(report["status"], "red")
        self.assertTrue(any(issue["area"] == "Objects" for issue in report["issues"]))

    def test_risky_terms_trigger_teacher_review(self) -> None:
        state = load_default_state()
        state["topics"].append("a weapon in the lost property box")

        report = check_state(state)

        self.assertEqual(report["status"], "amber")
        self.assertTrue(any(issue["area"] == "Teacher Review" for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
