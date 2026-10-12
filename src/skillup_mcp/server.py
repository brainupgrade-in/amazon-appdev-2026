"""Minimal spec-shaped MCP server over Streamable HTTP (stdlib only).

Compliant subset of MCP 2025-11-25: single POST /mcp endpoint, JSON-RPC,
`initialize` -> MCP-Session-Id, `tools/list`, `tools/call`, `ping`.
GET returns 405 (spec-allowed when no SSE stream is offered).
"""
import argparse
import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import tools as coaching

PROTOCOL_VERSION = "2025-11-25"
DEMO_PAGE = Path(__file__).resolve().parents[2] / "demo" / "index.html"

_mcp_sessions: set = set()

# start_coaching calls Bedrock; cap it per client IP so a public endpoint can't drain the credit.
STARTS_PER_HOUR = 30
_starts: dict = {}
_starts_lock = threading.Lock()


def allow_start(ip, now=None):
    now = time.time() if now is None else now
    with _starts_lock:
        recent = [t for t in _starts.get(ip, []) if now - t < 3600]
        if len(recent) >= STARTS_PER_HOUR:
            _starts[ip] = recent
            return False
        recent.append(now)
        _starts[ip] = recent
        return True


def client_ip(headers, peer):
    """App Runner sits behind a proxy: the first X-Forwarded-For entry is the client."""
    fwd = headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() or peer

TOOL_DEFS = [
    {
        "name": "start_coaching",
        "description": "Start a coaching run on a learning module. Returns a session_key, the module title "
        "and the number of questions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["context-engineering", "agentcore"],
                    "default": "context-engineering",
                    "description": "context-engineering = Prompts and Context Engineering; "
                    "agentcore = Building agents with Amazon Bedrock AgentCore",
                },
                "lang": {
                    "type": "string",
                    "enum": ["en", "hinglish"],
                    "default": "en",
                    "description": "Coach language: en, or hinglish (Hindi-English mix; questions stay in English).",
                },
                "learner_id": {
                    "type": "string",
                    "description": "Optional anonymous learner id (UUID). Enables cross-session memory: "
                    "questions missed last time come back first.",
                },
            },
        },
    },
    {
        "name": "next_question",
        "description": "Get the current quiz card for a coaching session.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_key": {"type": "string"}},
            "required": ["session_key"],
        },
    },
    {
        "name": "submit_answer",
        "description": "Submit an answer (choice text or index) for the current question.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_key": {"type": "string"},
                "question_id": {"type": "string"},
                "choice": {},
            },
            "required": ["session_key", "question_id", "choice"],
        },
    },
    {
        "name": "submit_open_answer",
        "description": "Submit the learner's free-form spoken answer to the session's open question. The SkillUp "
        "coach agent on Amazon Bedrock AgentCore Runtime grades it against key points (verdict, feedback).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_key": {"type": "string"},
                "question_id": {"type": "string"},
                "answer": {"type": "string"},
            },
            "required": ["session_key", "question_id", "answer"],
        },
    },
    {
        "name": "get_progress",
        "description": "Get answered/correct/accuracy for a coaching session.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_key": {"type": "string"}},
            "required": ["session_key"],
        },
    },
]


def new_session_id():
    return uuid.uuid4().hex


def check_origin(origin):
    if not origin:
        return True
    try:
        host = urlparse(origin).hostname or ""
    except Exception:
        return False
    allowed = {"localhost", "127.0.0.1"}
    allowed |= {h.strip() for h in os.environ.get("ALLOWED_ORIGINS", "").split(",") if h.strip()}
    return host in allowed


def _ok(req_id, result, session_id=None):
    body = {"jsonrpc": "2.0", "id": req_id, "result": result}
    return {"body": body, "session_id": session_id}


def dispatch(msg, headers=None, session_id=None):
    """Pure dispatch for tests; HTTP layer maps exceptions to JSON-RPC errors."""
    headers = headers or {}
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        sid = new_session_id()
        _mcp_sessions.add(sid)
        return _ok(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "skillup-coach", "version": "0.1.0"},
            },
            session_id=sid,
        )
    if method == "notifications/initialized":
        return {"body": None, "session_id": session_id}
    if session_id not in _mcp_sessions:
        raise KeyError("unknown-session")
    if method == "ping":
        return _ok(req_id, {}, session_id=session_id)
    if method == "tools/list":
        return _ok(req_id, {"tools": TOOL_DEFS}, session_id=session_id)
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = {
            "start_coaching": coaching.start_coaching,
            "next_question": coaching.next_question,
            "submit_answer": coaching.submit_answer,
            "submit_open_answer": coaching.submit_open_answer,
            "get_progress": coaching.get_progress,
        }.get(name)
        if fn is None:
            raise KeyError(name)
        out = fn(**args)
        return _ok(req_id, {"content": [{"type": "text", "text": json.dumps(out)}]}, session_id=session_id)
    raise KeyError(method)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj=None, session_id=None, proto=None):
        raw = b"" if obj is None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        if session_id:
            self.send_header("MCP-Session-Id", session_id)
        if proto:
            self.send_header("MCP-Protocol-Version", proto)
        self.end_headers()
        if raw:
            self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/mcp":
            self._send(405, {"error": "SSE stream not offered; use POST"})
        elif path == "/health":
            self._send(200, {"status": "ok"})
        elif path == "/":
            raw = DEMO_PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/mcp":
            self._send(404, {"error": "not found"})
            return
        if not check_origin(self.headers.get("Origin")):
            self._send(403, {"error": "bad origin"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            msg = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._send(400, {"error": "invalid json"})
            return
        if msg.get("method") != "initialize":
            ver = self.headers.get("MCP-Protocol-Version")
            if ver is not None and ver != PROTOCOL_VERSION:
                self._send(400, {"error": f"unsupported protocol version {ver}"})
                return
        if (msg.get("method") == "tools/call" and (msg.get("params") or {}).get("name") == "start_coaching"
                and not allow_start(client_ip(self.headers, self.client_address[0]))):
            self._send(
                200,
                {"jsonrpc": "2.0", "id": msg.get("id"),
                 "error": {"code": -32000, "message": "rate limited: too many sessions, try again later"}},
            )
            return
        try:
            out = dispatch(msg, dict(self.headers), self.headers.get("MCP-Session-Id"))
        except KeyError as e:
            code = -32001 if "unknown-session" in str(e) else -32601
            self._send(
                200,
                {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": code, "message": str(e)}},
            )
            return
        except TypeError as e:
            self._send(
                200,
                {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32602, "message": str(e)}},
            )
            return
        if out["body"] is None:
            self.send_response(202)
            if out.get("session_id"):
                self.send_header("MCP-Session-Id", out["session_id"])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send(200, out["body"], session_id=out.get("session_id"), proto=PROTOCOL_VERSION)


def make_server(host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), Handler)


def run(port=8000, host="127.0.0.1"):
    httpd = make_server(host, port)
    print(f"skillup-coach MCP on http://{host}:{port}/mcp (protocol {PROTOCOL_VERSION})")
    httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ns = ap.parse_args()
    run(ns.port, ns.host)
