"""TDD red-first: optional Bedrock hook. Offline default must never break; failures fall back."""
import os
import unittest
from unittest.mock import MagicMock, patch

from skillup_mcp import tools

QUESTION_JSON = (
    '{"id": "llm-1", "prompt": "What does chmod 644 mean?", '
    '"choices": ["rw-r--r--", "rwxr-xr-x", "rw-------", "r--r--r--"], '
    '"answer": 0, "explain": "Owner rw, group/others r."}'
)


def converse_reply(text):
    return {"output": {"message": {"role": "assistant", "content": [{"text": text}]}}}


def fake_client(*texts):
    client = MagicMock()
    client.converse.side_effect = [converse_reply(t) for t in texts]
    return client


def _right(s):
    return tools._sessions[s["session_key"]]["bank"][0]["answer"]


def _wrong(s):
    return (_right(s) + 1) % 4


OFF = {k: v for k, v in os.environ.items() if k != "SKILLUP_LLM"}
ON = {"SKILLUP_LLM": "1"}


class TestBedrockHook(unittest.TestCase):
    def test_no_env_uses_offline_bank(self):
        with patch.dict(os.environ, OFF, clear=True):
            with patch.object(tools, "_bedrock_client") as factory:
                s = tools.start_coaching("context-engineering")
        self.assertEqual(s["total"], tools.SESSION_SIZE)
        factory.assert_not_called()

    def test_bedrock_appends_question(self):
        client = fake_client(QUESTION_JSON)
        with patch.dict(os.environ, ON):
            with patch.object(tools, "_bedrock_client", return_value=client):
                s = tools.start_coaching("context-engineering")
        self.assertEqual(s["total"], tools.SESSION_SIZE + 1)
        q4 = tools._sessions[s["session_key"]]["bank"][-1]
        self.assertEqual(q4["id"], "llm-1")
        self.assertEqual(q4["card"]["subtitle"], "AI-generated (Amazon Bedrock)")

    def test_converse_called_with_model_from_env(self):
        client = fake_client(QUESTION_JSON)
        env = dict(ON, BEDROCK_MODEL_ID="my-model")
        with patch.dict(os.environ, env):
            with patch.object(tools, "_bedrock_client", return_value=client):
                tools.start_coaching("context-engineering")
        kwargs = client.converse.call_args.kwargs
        self.assertEqual(kwargs["modelId"], "my-model")
        self.assertEqual(kwargs["messages"][0]["role"], "user")

    def test_malformed_question_ignored(self):
        client = fake_client('{"prompt": "x", "choices": ["a"], "answer": 9}')
        with patch.dict(os.environ, ON):
            with patch.object(tools, "_bedrock_client", return_value=client):
                s = tools.start_coaching("context-engineering")
        self.assertEqual(s["total"], tools.SESSION_SIZE)

    def test_bedrock_failure_falls_back_silently(self):
        client = MagicMock()
        client.converse.side_effect = Exception("AccessDeniedException")
        with patch.dict(os.environ, ON):
            with patch.object(tools, "_bedrock_client", return_value=client):
                s = tools.start_coaching("context-engineering")
                q = tools.next_question(s["session_key"])
                r = tools.submit_answer(s["session_key"], q["question_id"], _wrong(s))
        self.assertEqual(s["total"], tools.SESSION_SIZE)
        self.assertFalse(r["correct"])
        self.assertNotIn("coach_tip", r)

    def test_wrong_answer_gets_coach_tip(self):
        with patch.dict(os.environ, OFF, clear=True):
            s = tools.start_coaching("context-engineering")
        q = tools.next_question(s["session_key"])
        client = fake_client("`-a` means all, including dotfiles.")
        with patch.dict(os.environ, ON):
            with patch.object(tools, "_bedrock_client", return_value=client):
                r = tools.submit_answer(s["session_key"], q["question_id"], _wrong(s))
        self.assertEqual(r["coach_tip"], "`-a` means all, including dotfiles.")

    def test_right_answer_skips_bedrock(self):
        with patch.dict(os.environ, OFF, clear=True):
            s = tools.start_coaching("context-engineering")
        q = tools.next_question(s["session_key"])
        client = fake_client()
        with patch.dict(os.environ, ON):
            with patch.object(tools, "_bedrock_client", return_value=client):
                r = tools.submit_answer(s["session_key"], q["question_id"], _right(s))
        self.assertTrue(r["correct"])
        self.assertNotIn("coach_tip", r)
        client.converse.assert_not_called()


if __name__ == "__main__":
    unittest.main()
