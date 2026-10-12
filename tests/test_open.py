"""Open-ended question at the end of a session, graded against key points by the AgentCore coach agent."""
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from skillup_mcp import coach, memory, tools

ROOT = Path(__file__).resolve().parents[1]
OFF = {k: v for k, v in os.environ.items() if k not in ("SKILLUP_LLM", "SKILLUP_MEMORY_ID", "SKILLUP_AGENT_ARN")}
LEARNER = "3f2b9c1e-7a4d-4e8b-9c2a-1b2c3d4e5f60"


def finish_choices(s):
    for q in list(tools._sessions[s["session_key"]]["bank"]):
        nq = tools.next_question(s["session_key"])
        tools.submit_answer(s["session_key"], nq["question_id"], q["answer"])


class TestOpenPacks(unittest.TestCase):
    def test_every_pack_has_open_questions_with_key_points(self):
        for path in sorted((ROOT / "packs").glob("*.json")):
            with self.subTest(pack=path.name):
                opens = json.loads(path.read_text())["open"]
                self.assertGreaterEqual(len(opens), 3)
                for o in opens:
                    self.assertGreaterEqual(len(o["key_points"]), 2, o["id"])
                    self.assertTrue(o["prompt"] and o["subtitle"], o["id"])
                    self.assertTrue(o["source"].startswith("https://"), o["id"])


class TestOpenFlow(unittest.TestCase):
    def setUp(self):
        memory._local.clear()

    def start(self):
        with patch.dict(os.environ, OFF, clear=True):
            return tools.start_coaching("context-engineering", learner_id=LEARNER)

    def test_open_question_follows_choices(self):
        s = self.start()
        self.assertEqual(s["total"], tools.SESSION_SIZE + 1)
        finish_choices(s)
        q = tools.next_question(s["session_key"])
        self.assertEqual(q["kind"], "open")
        self.assertTrue(q["question_id"].startswith("ce-open-"))
        self.assertEqual(q["index"], tools.SESSION_SIZE)

    def grade(self, answer):
        s = self.start()
        finish_choices(s)
        q = tools.next_question(s["session_key"])
        with patch.dict(os.environ, OFF, clear=True):
            r = tools.submit_open_answer(s["session_key"], q["question_id"], answer)
        return s, q, r

    def test_local_fallback_grades_key_points(self):
        s, q, _ = self.grade("x")
        o = tools._sessions[s["session_key"]]["open"]
        full = " ".join(o["key_points"])
        tools._sessions.clear()
        with patch.object(tools.random, "choice", return_value=o):
            _, _, r_full = self.grade(full)
            _, _, r_half = self.grade(o["key_points"][0])
            _, _, r_none = self.grade("I am not sure, sorry")
        self.assertEqual((r_full["verdict"], r_half["verdict"], r_none["verdict"]), ("correct", "partial", "incorrect"))
        self.assertEqual(r_full["graded_by"], "local")
        self.assertTrue(r_none["feedback"])

    def test_open_answer_counts_in_progress_and_memory_then_done(self):
        s, q, r = self.grade("not sure")
        p = tools.get_progress(s["session_key"])
        self.assertEqual(p["answered"], tools.SESSION_SIZE + 1)
        self.assertTrue(tools.next_question(s["session_key"])["done"])
        with patch.dict(os.environ, OFF, clear=True):
            hist = memory.history("context-engineering", LEARNER)
        self.assertIn({"question": q["question_id"], "correct": False}, hist)

    def test_wrong_open_question_id_rejected(self):
        s = self.start()
        finish_choices(s)
        tools.next_question(s["session_key"])
        with self.assertRaises(KeyError):
            tools.submit_open_answer(s["session_key"], "ce-open-999", "x")


class TestAgentCoreGrading(unittest.TestCase):
    QUESTION = {"id": "ce-open-1", "prompt": "Why do examples help?", "subtitle": "Few-shot prompting",
                "key_points": ["Examples show the format", "Three to five examples"], "source": "https://x"}

    def client_returning(self, obj):
        client = MagicMock()
        client.invoke_agent_runtime.return_value = {"response": io.BytesIO(json.dumps(obj).encode())}
        return client

    def test_invokes_agentcore_runtime_when_configured(self):
        client = self.client_returning({"verdict": "partial", "covered": ["Examples show the format"],
                                        "missing": ["Three to five examples"], "feedback": "Good start, you…"})
        env = dict(OFF, SKILLUP_AGENT_ARN="arn:aws:bedrock-agentcore:ap-south-1:1:runtime/x")
        with patch.dict(os.environ, env, clear=True), patch.object(coach, "_client", return_value=client):
            r = coach.grade(self.QUESTION, "they show the format", "context-engineering", LEARNER)
        kw = client.invoke_agent_runtime.call_args.kwargs
        payload = json.loads(kw["payload"])
        self.assertEqual(kw["agentRuntimeArn"], env["SKILLUP_AGENT_ARN"])
        self.assertGreaterEqual(len(kw["runtimeSessionId"]), 33)
        self.assertEqual(payload["action"], "grade")
        self.assertEqual(payload["key_points"], self.QUESTION["key_points"])
        self.assertEqual(payload["learner_id"], LEARNER)
        self.assertEqual((r["verdict"], r["graded_by"]), ("partial", "agentcore"))

    def test_agent_failure_falls_back_to_local(self):
        client = MagicMock()
        client.invoke_agent_runtime.side_effect = Exception("ThrottlingException")
        env = dict(OFF, SKILLUP_AGENT_ARN="arn:aws:bedrock-agentcore:ap-south-1:1:runtime/x")
        with patch.dict(os.environ, env, clear=True), patch.object(coach, "_client", return_value=client):
            r = coach.grade(self.QUESTION, "examples show the format, use three to five", "context-engineering", None)
        self.assertEqual((r["verdict"], r["graded_by"]), ("correct", "local"))

    def test_bad_agent_verdict_falls_back_to_local(self):
        client = self.client_returning({"verdict": "excellent!!", "feedback": "x"})
        env = dict(OFF, SKILLUP_AGENT_ARN="arn:aws:bedrock-agentcore:ap-south-1:1:runtime/x")
        with patch.dict(os.environ, env, clear=True), patch.object(coach, "_client", return_value=client):
            r = coach.grade(self.QUESTION, "no idea", "context-engineering", None)
        self.assertEqual(r["graded_by"], "local")
