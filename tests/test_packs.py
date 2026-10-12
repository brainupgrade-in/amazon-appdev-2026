"""Question packs are data (packs/*.json); sessions draw from the chosen module."""
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from skillup_mcp import tools

ROOT = Path(__file__).resolve().parents[1]
OFF = {k: v for k, v in os.environ.items() if k != "SKILLUP_LLM"}


class TestPackFiles(unittest.TestCase):
    def test_every_pack_is_valid(self):
        packs = sorted((ROOT / "packs").glob("*.json"))
        self.assertTrue(packs)
        for path in packs:
            with self.subTest(pack=path.name):
                d = json.loads(path.read_text())
                self.assertTrue(d["id"] and d["title"] and d["version"])
                qs = d["questions"]
                self.assertGreaterEqual(len(qs), 15)
                self.assertEqual(len({q["id"] for q in qs}), len(qs))
                for q in qs:
                    self.assertEqual(len(q["choices"]), 4, q["id"])
                    self.assertIn(q["answer"], range(4), q["id"])
                    self.assertTrue(q["explain"] and q["subtitle"], q["id"])
                    self.assertTrue(q["source"].startswith("https://"), q["id"])

    def test_context_engineering_is_available(self):
        self.assertIn("context-engineering", tools.available_modules())


class TestSessions(unittest.TestCase):
    def start(self, topic=None):
        with patch.dict(os.environ, OFF, clear=True):
            return tools.start_coaching(topic) if topic else tools.start_coaching()

    def test_default_module_and_session_size(self):
        s = self.start()
        self.assertEqual(s["topic"], "context-engineering")
        self.assertEqual(s["title"], "Prompts and Context Engineering")
        self.assertEqual(s["total"], tools.SESSION_SIZE + 1)
        pack_ids = {q["id"] for q in tools.load_pack("context-engineering")["questions"]}
        self.assertTrue({q["id"] for q in tools._sessions[s["session_key"]]["bank"]} <= pack_ids)

    def test_unknown_topic_falls_back_to_default(self):
        self.assertEqual(self.start("no-such-module")["topic"], "context-engineering")

    def test_card_carries_subtitle(self):
        s = self.start()
        q = tools.next_question(s["session_key"])
        self.assertTrue(q["card"]["subtitle"])


class TestGroundedAiQuestion(unittest.TestCase):
    def test_prompt_names_module_and_is_grounded_in_pack_facts(self):
        client = MagicMock()
        client.converse.return_value = {"output": {"message": {"content": [{"text": "not json"}]}}}
        with patch.dict(os.environ, {"SKILLUP_LLM": "1"}):
            with patch.object(tools, "_bedrock_client", return_value=client):
                tools.start_coaching("context-engineering")
        prompt = client.converse.call_args.kwargs["messages"][0]["content"][0]["text"]
        self.assertIn("Prompts and Context Engineering", prompt)
        facts = [q["explain"] for q in tools.load_pack("context-engineering")["questions"]]
        self.assertTrue(any(f in prompt for f in facts))


class TestNoLinuxLeft(unittest.TestCase):
    def test_product_path_has_no_linux_topic(self):
        out = subprocess.run(["grep", "-ril", "linux", "src", "demo", "skill"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "")
