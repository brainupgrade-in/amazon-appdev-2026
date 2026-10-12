"""Learner memory across sessions.

Amazon Bedrock AgentCore Memory when SKILLUP_MEMORY_ID is set (one event per answer, actor
public/demo/<learner>, session progress-<module>); otherwise an in-process store for offline use.
Like the Bedrock hook, it never raises: coaching works even if memory is unavailable.
"""
import json
import os
import re
from datetime import datetime, timezone

_LEARNER = re.compile(r"^[a-f0-9-]{8,64}$")  # browser-generated UUID; no names, no PII
_local: dict = {}


def valid(learner):
    return bool(learner) and bool(_LEARNER.match(learner))


def _actor(learner):
    return f"public/demo/{learner}"  # org/cohort/learner


def _client():
    import boto3

    return boto3.client("bedrock-agentcore", region_name=os.environ.get("AWS_REGION", "ap-south-1"))


def record(module, learner, question, correct):
    if not valid(learner):
        return
    item = {"question": question, "correct": bool(correct)}
    memory_id = os.environ.get("SKILLUP_MEMORY_ID")
    if not memory_id:
        _local.setdefault((module, learner), []).append(item)
        return
    try:
        _client().create_event(
            memoryId=memory_id, actorId=_actor(learner), sessionId=f"progress-{module}",
            eventTimestamp=datetime.now(timezone.utc),
            payload=[{"blob": json.dumps(dict(item, module=module))}],
        )
    except Exception:
        pass


def history(module, learner):
    """This learner's answers in a module, oldest first: [{"question", "correct"}]."""
    if not valid(learner):
        return []
    memory_id = os.environ.get("SKILLUP_MEMORY_ID")
    if not memory_id:
        return list(_local.get((module, learner), []))
    try:
        events, token = [], None
        while True:
            kw = dict(memoryId=memory_id, actorId=_actor(learner), sessionId=f"progress-{module}",
                      includePayloads=True, maxResults=100)
            if token:
                kw["nextToken"] = token
            page = _client().list_events(**kw)
            events += page.get("events", [])
            token = page.get("nextToken")
            if not token or len(events) >= 1000:
                break
        events.sort(key=lambda e: e["eventTimestamp"])
        out = []
        for e in events:
            for p in e.get("payload", []):
                if "blob" in p:
                    d = json.loads(p["blob"])
                    out.append({"question": d["question"], "correct": bool(d["correct"])})
        return out
    except Exception:
        return []
