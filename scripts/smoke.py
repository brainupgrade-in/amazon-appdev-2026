"""Post-deploy smoke test: python3 scripts/smoke.py [base_url]  (default: the live App Runner URL).

Checks /health, the demo page, and one MCP round trip: initialize -> tools/list -> start_coaching -> next_question.
Exits non-zero on the first failure.
"""
import json
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://skillup-coach.gheware-ai.com").rstrip("/")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
           "MCP-Protocol-Version": "2025-11-25"}


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return r.status, r.read().decode()


def rpc(method, params=None, sid=None, rid=1):
    h = dict(HEADERS, **({"MCP-Session-Id": sid} if sid else {}))
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}).encode()
    with urllib.request.urlopen(urllib.request.Request(BASE + "/mcp", body, h), timeout=30) as r:
        return r.headers.get("MCP-Session-Id"), json.loads(r.read())


def call(sid, name, args, rid):
    _, out = rpc("tools/call", {"name": name, "arguments": args}, sid, rid)
    assert "error" not in out, out
    return json.loads(out["result"]["content"][0]["text"])


def main():
    status, body = get("/health")
    assert status == 200 and json.loads(body)["status"] == "ok", body
    status, page = get("/")
    assert status == 200 and "SkillUp Coach" in page
    sid, init = rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                   "clientInfo": {"name": "smoke", "version": "1"}})
    assert sid and init["result"]["protocolVersion"] == "2025-11-25", init
    _, tl = rpc("tools/list", sid=sid, rid=2)
    names = [t["name"] for t in tl["result"]["tools"]]
    assert {"start_coaching", "next_question", "submit_answer", "get_progress"} <= set(names), names
    s = call(sid, "start_coaching", {}, 3)
    q = call(sid, "next_question", {"session_key": s["session_key"]}, 4)
    assert q.get("prompt") and len(q.get("choices", [])) == 4, q
    print(f"smoke OK: {BASE} · tools={len(names)} · questions={s['total']} · first={q['prompt'][:60]!r}")


if __name__ == "__main__":
    main()
