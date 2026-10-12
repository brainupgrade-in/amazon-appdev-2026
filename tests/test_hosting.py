"""TDD red-first: public hosting (App Runner behind skillup-coach.gheware-ai.com)."""
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from skillup_mcp import server


class TestAllowedOrigins(unittest.TestCase):
    def test_env_origin_allowed(self):
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "skillup-coach.gheware-ai.com, other.example"}):
            self.assertTrue(server.check_origin("https://skillup-coach.gheware-ai.com"))
            self.assertTrue(server.check_origin("https://other.example"))
            self.assertFalse(server.check_origin("https://evil.example"))

    def test_without_env_only_localhost(self):
        env = {k: v for k, v in os.environ.items() if k != "ALLOWED_ORIGINS"}
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(server.check_origin("https://skillup-coach.gheware-ai.com"))


class TestHttpSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.make_server("127.0.0.1", 0)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_threaded(self):
        self.assertIsInstance(self.httpd, ThreadingHTTPServer)

    def test_root_serves_demo(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertEqual(r.status, 200)
            self.assertIn("text/html", r.headers["Content-Type"])
            self.assertIn(b"SkillUp", r.read())

    def test_health(self):
        with urllib.request.urlopen(self.base + "/health") as r:
            self.assertEqual(r.status, 200)

    def test_get_mcp_still_405(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.base + "/mcp")
        self.assertEqual(cm.exception.code, 405)


if __name__ == "__main__":
    unittest.main()


class TestRateLimit(unittest.TestCase):
    """start_coaching calls Bedrock, so it is capped per client IP (public endpoint on a fixed credit)."""

    def setUp(self):
        server._starts.clear()

    def test_allows_up_to_limit_then_blocks(self):
        for _ in range(server.STARTS_PER_HOUR):
            self.assertTrue(server.allow_start("1.2.3.4", now=1000.0))
        self.assertFalse(server.allow_start("1.2.3.4", now=1000.0))

    def test_limit_is_per_ip(self):
        for _ in range(server.STARTS_PER_HOUR):
            server.allow_start("1.2.3.4", now=1000.0)
        self.assertTrue(server.allow_start("5.6.7.8", now=1000.0))

    def test_window_slides(self):
        for _ in range(server.STARTS_PER_HOUR):
            server.allow_start("1.2.3.4", now=1000.0)
        self.assertTrue(server.allow_start("1.2.3.4", now=1000.0 + 3601))

    def test_client_ip_prefers_forwarded_for(self):
        self.assertEqual(server.client_ip({"X-Forwarded-For": "9.9.9.9, 10.0.0.1"}, "10.0.0.2"), "9.9.9.9")
        self.assertEqual(server.client_ip({}, "10.0.0.2"), "10.0.0.2")
