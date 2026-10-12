"""AgentCore go/no-go check (13 Oct): invoke the Runtime agent, then write + read one learner event in Memory.

Run: AWS_PROFILE=<profile> python agent/gonogo.py
"""
import json
import time
import uuid
from datetime import datetime, timezone

import boto3

REGION = "ap-south-1"
cp = boto3.client("bedrock-agentcore-control", region_name=REGION)
dp = boto3.client("bedrock-agentcore", region_name=REGION)
# Look resources up by name so no account-specific ids live in the public repo.
RUNTIME_ARN = next(r["agentRuntimeArn"] for r in cp.list_agent_runtimes()["agentRuntimes"]
                   if r["agentRuntimeName"] == "skillup_coach_agent")
MEMORY_ID = next(m["id"] for m in cp.list_memories()["memories"] if m["id"].startswith("skillup_coach_memory-"))

# 1. Runtime: one invocation of the Strands agent (session ids must be >= 33 chars).
session = f"gonogo-{uuid.uuid4().hex}"
t0 = time.time()
resp = dp.invoke_agent_runtime(agentRuntimeArn=RUNTIME_ARN, runtimeSessionId=session, qualifier="DEFAULT",
                               payload=json.dumps({"prompt": "In one sentence, what is few-shot prompting?"}))
body = json.loads(resp["response"].read())
print(f"runtime OK in {time.time() - t0:.1f}s:", body["result"][:200])

# 2. Memory: record one answer event for a demo learner, then list it back.
actor, msession = f"public-demo-{uuid.uuid4().hex[:8]}", "progress"
dp.create_event(memoryId=MEMORY_ID, actorId=actor, sessionId=msession, eventTimestamp=datetime.now(timezone.utc),
                payload=[{"blob": json.dumps({"module": "context-engineering", "question": "ce-01", "correct": False})}])
events = dp.list_events(memoryId=MEMORY_ID, actorId=actor, sessionId=msession, includePayloads=True)["events"]
print("memory OK:", len(events), "event(s) for", actor, "->", events[0]["payload"][0]["blob"])
