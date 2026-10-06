"""Minimal spec-shaped MCP server over Streamable HTTP (stdlib only).

Compliant subset of MCP 2025-11-25: single POST /mcp endpoint, JSON-RPC,
`initialize` -> MCP-Session-Id, `tools/list`, `tools/call`, `ping`.
GET returns 405 (spec-allowed when no SSE stream is offered).
"""
import argparse
import json
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from . import tools as coaching

PROTOCOL_VERSION = "2025-11-25"

_mcp_sessions: set = set()

TOOL_DEFS = [
    {
        "name": "start_coaching",
        "description": "Start a coaching run on a topic. Returns a session_key.",
        "inputSchema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "default": "linux-basics"}},
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
    return host in ("localhost", "127.0.0.1")


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
        if urlparse(self.path).path == "/mcp":
            self._send(405, {"error": "SSE stream not offered; use POST"})
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


def run(port=8000, host="127.0.0.1"):
    httpd = HTTPServer((host, port), Handler)
    print(f"skillup-coach MCP on http://{host}:{port}/mcp (protocol {PROTOCOL_VERSION})")
    httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ns = ap.parse_args()
    run(ns.port, ns.host)
