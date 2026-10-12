"""Cross-session learner memory: missed questions come back first, with a welcome-back line."""
import os
import unittest
from unittest.mock import MagicMock, patch

from skillup_mcp import memory, tools

OFF = {k: v for k, v in os.environ.items() if k not in ("SKILLUP_LLM", "SKILLUP_MEMORY_ID")}
LEARNER = "3f2b9c1e-7a4d-4e8b-9c2a-1b2c3d4e5f60"


def restart_process():
    """Simulate a server restart: coaching sessions are lost, learner memory is not."""
    tools._sessions.clear()


class TestSpacedRepetition(unittest.TestCase):
    def setUp(self):
        memory._local.clear()

    def answer_all(self, s, wrong_ids=()):
        bank = tools._sessions[s["session_key"]]["bank"]
        for q in list(bank):
            nq = tools.next_question(s["session_key"])
            right = q["answer"]
            tools.submit_answer(s["session_key"], nq["question_id"], (right + 1) % 4 if q["id"] in wrong_ids else right)

    def test_missed_question_returns_first_after_restart(self):
        with patch.dict(os.environ, OFF, clear=True):
            s1 = tools.start_coaching("context-engineering", learner_id=LEARNER)
            missed = tools._sessions[s1["session_key"]]["bank"][2]
            self.answer_all(s1, wrong_ids={missed["id"]})
            restart_process()
            s2 = tools.start_coaching("context-engineering", learner_id=LEARNER)
        first_two = [q["id"] for q in tools._sessions[s2["session_key"]]["bank"][:2]]
        self.assertIn(missed["id"], first_two)
        self.assertIn(missed["subtitle"], s2["welcome_back"])

    def test_first_session_has_no_welcome_back(self):
        with patch.dict(os.environ, OFF, clear=True):
            s = tools.start_coaching("context-engineering", learner_id=LEARNER)
        self.assertNotIn("welcome_back", s)

    def test_corrected_question_is_no_longer_missed(self):
        with patch.dict(os.environ, OFF, clear=True):
            s1 = tools.start_coaching("context-engineering", learner_id=LEARNER)
            q = tools._sessions[s1["session_key"]]["bank"][0]
            self.answer_all(s1, wrong_ids={q["id"]})
            s2 = tools.start_coaching("context-engineering", learner_id=LEARNER)
            self.assertEqual(tools._sessions[s2["session_key"]]["bank"][0]["id"], q["id"])
            self.answer_all(s2)
            s3 = tools.start_coaching("context-engineering", learner_id=LEARNER)
        self.assertNotIn("welcome_back", s3)

    def test_unseen_questions_preferred_over_seen_correct(self):
        with patch.dict(os.environ, OFF, clear=True):
            s1 = tools.start_coaching("context-engineering", learner_id=LEARNER)
            seen = {q["id"] for q in tools._sessions[s1["session_key"]]["bank"]}
            self.answer_all(s1)
            s2 = tools.start_coaching("context-engineering", learner_id=LEARNER)
        self.assertFalse(seen & {q["id"] for q in tools._sessions[s2["session_key"]]["bank"]})

    def test_memory_is_per_module_and_per_learner(self):
        with patch.dict(os.environ, OFF, clear=True):
            s1 = tools.start_coaching("context-engineering", learner_id=LEARNER)
            self.answer_all(s1, wrong_ids={q["id"] for q in tools._sessions[s1["session_key"]]["bank"]})
            other = tools.start_coaching("context-engineering", learner_id="aaaaaaaa-0000-4000-8000-000000000000")
            agentcore = tools.start_coaching("agentcore", learner_id=LEARNER)
        self.assertNotIn("welcome_back", other)
        self.assertNotIn("welcome_back", agentcore)

    def test_invalid_learner_id_is_ignored(self):
        with patch.dict(os.environ, OFF, clear=True):
            s = tools.start_coaching("context-engineering", learner_id="../../etc")
            q = tools.next_question(s["session_key"])
            tools.submit_answer(s["session_key"], q["question_id"], 0)
        self.assertEqual(memory._local, {})


class TestAgentCoreBackend(unittest.TestCase):
    def test_uses_agentcore_memory_when_configured(self):
        client = MagicMock()
        client.list_events.return_value = {"events": [
            {"eventTimestamp": 1, "payload": [{"blob": '{"question": "ce-05", "correct": false}'}]}]}
        env = dict(OFF, SKILLUP_MEMORY_ID="mem-123")
        with patch.dict(os.environ, env, clear=True), patch.object(memory, "_client", return_value=client):
            memory.record("context-engineering", LEARNER, "ce-01", True)
            hist = memory.history("context-engineering", LEARNER)
        kw = client.create_event.call_args.kwargs
        self.assertEqual(kw["memoryId"], "mem-123")
        self.assertEqual(kw["actorId"], f"public/demo/{LEARNER}")
        self.assertEqual(kw["sessionId"], "progress-context-engineering")
        self.assertEqual(hist, [{"question": "ce-05", "correct": False}])

    def test_agentcore_failure_never_breaks_coaching(self):
        client = MagicMock()
        client.create_event.side_effect = Exception("ThrottlingException")
        client.list_events.side_effect = Exception("ThrottlingException")
        env = dict(OFF, SKILLUP_MEMORY_ID="mem-123")
        with patch.dict(os.environ, env, clear=True), patch.object(memory, "_client", return_value=client):
            memory.record("context-engineering", LEARNER, "ce-01", True)
            self.assertEqual(memory.history("context-engineering", LEARNER), [])
