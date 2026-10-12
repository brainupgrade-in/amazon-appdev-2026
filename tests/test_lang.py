"""Hinglish mode: the coach's tips and the agent's feedback switch language; questions stay in English."""
import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from skillup_mcp import coach, tools

OFF = {k: v for k, v in os.environ.items() if k not in ("SKILLUP_LLM", "SKILLUP_MEMORY_ID", "SKILLUP_AGENT_ARN")}


class TestLanguage(unittest.TestCase):
    def test_default_is_english_and_unknown_falls_back(self):
        with patch.dict(os.environ, OFF, clear=True):
            self.assertEqual(tools.start_coaching()["lang"], "en")
            self.assertEqual(tools.start_coaching(lang="klingon")["lang"], "en")
            self.assertEqual(tools.start_coaching(lang="hinglish")["lang"], "hinglish")

    def test_hinglish_coach_tip_prompt(self):
        with patch.dict(os.environ, OFF, clear=True):
            s = tools.start_coaching(lang="hinglish")
        q = tools.next_question(s["session_key"])
        right = tools._sessions[s["session_key"]]["bank"][0]["answer"]
        client = MagicMock()
        client.converse.return_value = {"output": {"message": {"content": [{"text": "Arre, yeh galat hai."}]}}}
        with patch.dict(os.environ, {"SKILLUP_LLM": "1"}), patch.object(tools, "_bedrock_client", return_value=client):
            r = tools.submit_answer(s["session_key"], q["question_id"], (right + 1) % 4)
        prompt = client.converse.call_args.kwargs["messages"][0]["content"][0]["text"]
        self.assertIn("Hinglish", prompt)
        self.assertEqual(r["coach_tip"], "Arre, yeh galat hai.")

    def test_agent_payload_carries_language(self):
        client = MagicMock()
        client.invoke_agent_runtime.return_value = {"response": io.BytesIO(json.dumps(
            {"verdict": "correct", "feedback": "Bahut badhiya!"}).encode())}
        q = {"id": "x", "prompt": "p", "subtitle": "s", "key_points": ["a b c d"]}
        env = dict(OFF, SKILLUP_AGENT_ARN="arn:aws:bedrock-agentcore:ap-south-1:1:runtime/x")
        with patch.dict(os.environ, env, clear=True), patch.object(coach, "_client", return_value=client):
            coach.grade(q, "answer", "context-engineering", None, lang="hinglish")
        self.assertEqual(json.loads(client.invoke_agent_runtime.call_args.kwargs["payload"])["lang"], "hinglish")


class TestTipLength(unittest.TestCase):
    def test_coach_tip_capped_at_two_sentences_for_voice(self):
        long = "First sentence here. Second one too! Third should go. Fourth as well."
        self.assertEqual(tools._spoken(long), "First sentence here. Second one too!")
        self.assertEqual(tools._spoken("No end punctuation"), "No end punctuation")
        self.assertLessEqual(len(tools._spoken("word " * 200)), 260)
