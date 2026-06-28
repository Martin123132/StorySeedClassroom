from __future__ import annotations

import unittest

from storyseed_app.engine import generate_prompt, prompt_to_html
from storyseed_app.storage import load_default_state


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load_default_state()

    def test_same_seed_is_deterministic(self) -> None:
        options = {"seed": 1234, "mode": "Story Starter", "age_band": "8-11", "creativity": 60}
        self.assertEqual(generate_prompt(self.state, options), generate_prompt(self.state, options))

    def test_different_seed_changes_prompt(self) -> None:
        first = generate_prompt(self.state, {"seed": 111, "mode": "Mystery Hook"})
        second = generate_prompt(self.state, {"seed": 222, "mode": "Mystery Hook"})
        self.assertNotEqual(first["prompt"], second["prompt"])

    def test_trace_has_seven_steps(self) -> None:
        prompt = generate_prompt(self.state, {"seed": 999, "mode": "Vocabulary Quest"})
        for ingredient in prompt["ingredients"]:
            self.assertEqual(len(ingredient["trace"]), 7)

    def test_prompt_contains_classroom_structure(self) -> None:
        prompt = generate_prompt(self.state, {"seed": 77, "mode": "Drawing Prompt", "age_band": "5-7"})
        text = prompt["prompt"]
        self.assertIn("Student Task:", text)
        self.assertIn("Challenge:", text)
        self.assertIn("Subject Focus:", text)
        self.assertIn("Success Checklist:", text)
        self.assertIn("Teacher Note:", text)
        self.assertEqual(prompt["traffic"]["generated_prompt"], "green")

    def test_subject_pack_changes_prompt_focus_and_vocabulary(self) -> None:
        prompt = generate_prompt(self.state, {"seed": 808, "mode": "What If?", "subject": "Science", "age_band": "8-11"})
        science_words = set(self.state["subject_packs"]["Science"]["vocabulary"]["8-11"])
        self.assertIn("subject_focus", prompt)
        self.assertTrue(set(prompt["vocabulary"]) & science_words)
        self.assertEqual(len(prompt["vocabulary"]), len(set(prompt["vocabulary"])))
        self.assertIn(prompt["subject_focus"], prompt["teacher_note"])

    def test_subject_pack_topics_take_priority(self) -> None:
        prompt = generate_prompt(self.state, {"seed": 2027, "mode": "Vocabulary Quest", "subject": "Science", "age_band": "8-11"})
        science_topics = set(self.state["subject_packs"]["Science"]["topics"])
        self.assertTrue(any(f"problem about {topic}" in prompt["task"] for topic in science_topics))

    def test_printable_html_is_worksheet_shaped(self) -> None:
        prompt = generate_prompt(self.state, {"seed": 909, "mode": "Mystery Hook", "subject": "Mystery"})
        sheet = prompt_to_html(prompt)
        self.assertIn("StorySeed Classroom Worksheet", sheet)
        self.assertIn("Name", sheet)
        self.assertIn("Student Task", sheet)
        self.assertIn("Teacher Notes", sheet)
        self.assertIn("@media print", sheet)


if __name__ == "__main__":
    unittest.main()
