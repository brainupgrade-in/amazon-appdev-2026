"""TDD red-first: optional LLM hook. Offline default must never break; failures fall back."""
import os
import unittest
from unittest.mock import patch

from skillup_mcp import tools


class FakeResp:
    def __init__(self, payload):
        import json

        self._raw = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._raw


GOOD = {
    "choices": [
        {
            "message": {
                "content": (
                    '{"id": "llm-1", "prompt": "What does chmod 644 mean?", '
                    '"choices": ["rw-r--r--", "rwxr-xr-x", "rw-------", "r--r--r--"], '
                    '"answer": 0, "explain": "Owner rw, group/others r."}'
                )
            }
        }
    ]
}


class TestLLMHook(unittest.TestCase):
    def test_no_env_uses_offline_bank(self):
        env = {k: v for k, v in os.environ.items() if k not in ("SKILLUP_LLM", "MODEL_ENDPOINT")}
        with patch.dict(os.environ, env, clear=True):
            s = tools.start_coaching("linux-basics")
            self.assertEqual(s["total"], 3)

    def test_mocked_llm_appends_question(self):
        env = {"SKILLUP_LLM": "1", "MODEL_ENDPOINT": "http://llm.local", "MODEL_NAME": "m"}
        with patch.dict(os.environ, env):
            with patch("urllib.request.urlopen", return_value=FakeResp(GOOD)):
                s = tools.start_coaching("linux-basics")
        self.assertEqual(s["total"], 4)
        q4 = tools._sessions[s["session_key"]]["bank"][3]
        self.assertEqual(q4["id"], "llm-1")

    def test_llm_failure_falls_back_silently(self):
        env = {"SKILLUP_LLM": "1", "MODEL_ENDPOINT": "http://llm.local", "MODEL_NAME": "m"}
        with patch.dict(os.environ, env):
            with patch("urllib.request.urlopen", side_effect=Exception("down")):
                s = tools.start_coaching("linux-basics")
        self.assertEqual(s["total"], 3)


if __name__ == "__main__":
    unittest.main()
