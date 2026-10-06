"""TDD red-first: server dispatch + spec headers. Must fail until server.py lands."""
import unittest

from skillup_mcp.server import (
    PROTOCOL_VERSION,
    check_origin,
    dispatch,
    new_session_id,
)


class TestServerContract(unittest.TestCase):
    def test_protocol_version_pinned(self):
        self.assertEqual(PROTOCOL_VERSION, "2025-11-25")

    def test_session_ids_unique_ascii(self):
        a, b = new_session_id(), new_session_id()
        self.assertNotEqual(a, b)
        a.encode("ascii")

    def test_origin_check(self):
        self.assertTrue(check_origin(None))
        self.assertTrue(check_origin("http://localhost:8000"))
        self.assertTrue(check_origin("http://127.0.0.1:8000"))
        self.assertFalse(check_origin("https://evil.example"))

    def test_dispatch_initialize_and_tools(self):
        init = dispatch(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            headers={},
            session_id=None,
        )
        self.assertIn("body", init)
        self.assertIn("result", init["body"])
        sid = init["session_id"]
        self.assertTrue(sid)
        listed = dispatch(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            headers={},
            session_id=sid,
        )
        names = [t["name"] for t in listed["body"]["result"]["tools"]]
        for expected in ("start_coaching", "next_question", "submit_answer", "get_progress"):
            self.assertIn(expected, names)

    def test_dispatch_rejects_unknown_session(self):
        with self.assertRaises(KeyError):
            dispatch(
                {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
                headers={},
                session_id="bad",
            )


if __name__ == "__main__":
    unittest.main()
