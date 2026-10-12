"""TDD red-first: tools state machine. Must fail until tools.py lands."""
import unittest

from skillup_mcp.tools import (
    get_progress,
    next_question,
    start_coaching,
    submit_answer,
)


class TestCoachingFlow(unittest.TestCase):
    def test_start_next_answer_progress(self):
        s = start_coaching("context-engineering")
        self.assertIn("session_key", s)
        q = next_question(s["session_key"])
        self.assertIn("question_id", q)
        self.assertIn("prompt", q)
        self.assertIn("choices", q)
        r = submit_answer(s["session_key"], q["question_id"], q["choices"][0])
        self.assertIn("correct", r)
        p = get_progress(s["session_key"])
        self.assertEqual(p["answered"], 1)
        self.assertIn("accuracy", p)

    def test_unknown_session_rejected(self):
        with self.assertRaises(KeyError):
            next_question("nope")

    def test_wrong_question_rejected(self):
        s = start_coaching("context-engineering")
        with self.assertRaises(KeyError):
            submit_answer(s["session_key"], "bad-id", "x")


if __name__ == "__main__":
    unittest.main()
