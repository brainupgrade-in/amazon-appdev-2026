"""Grades a spoken, open-ended answer against the question's key points.

The SkillUp coach agent (Strands on Amazon Bedrock AgentCore Runtime) grades when SKILLUP_AGENT_ARN is set.
Without it, or on any failure or malformed reply, a local key-point check grades instead, so a session
always completes.
"""
import json
import os
import re
import uuid

VERDICTS = {"correct", "partial", "incorrect"}
_STOP = {"about", "with", "that", "this", "they", "their", "what", "from", "into", "kept", "like", "work",
         "best", "each", "must", "does", "help", "helps", "more", "less", "only", "your", "when", "where"}


def _client():
    import boto3

    return boto3.client("bedrock-agentcore", region_name=os.environ.get("AWS_REGION", "ap-south-1"))


def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3 and w not in _STOP}


def local_grade(question, answer):
    said = _words(answer)
    covered, missing = [], []
    for point in question["key_points"]:
        need = _words(point)
        (covered if need and 2 * len(need & said) >= len(need) else missing).append(point)
    if not missing:
        verdict, feedback = "correct", "Great answer, you covered the key points."
    elif covered:
        verdict = "partial"
        feedback = f"Good start: {covered[0]} To complete it, also mention: {' '.join(missing)}"
    else:
        verdict = "incorrect"
        feedback = f"Not quite. A strong answer mentions: {' '.join(question['key_points'])}"
    return {"verdict": verdict, "covered": covered, "missing": missing, "feedback": feedback, "graded_by": "local"}


def grade(question, answer, module, learner):
    arn = os.environ.get("SKILLUP_AGENT_ARN")
    if arn:
        try:
            resp = _client().invoke_agent_runtime(
                agentRuntimeArn=arn,
                # One warm runtime session per learner (ids must be >= 33 chars); anonymous callers get their own.
                runtimeSessionId=f"skillup-learner-{learner or uuid.uuid4().hex}",
                qualifier="DEFAULT",
                payload=json.dumps({"action": "grade", "module": module, "topic": question.get("subtitle", ""),
                                    "question": question["prompt"],
                                    "key_points": question["key_points"], "answer": answer[:1000],
                                    "learner_id": learner}),
            )
            body = json.loads(resp["response"].read())
            if body.get("verdict") in VERDICTS and body.get("feedback"):
                return {"verdict": body["verdict"], "covered": list(body.get("covered") or []),
                        "missing": list(body.get("missing") or []), "feedback": str(body["feedback"])[:600],
                        "graded_by": "agentcore", "tools_used": list(body.get("tools_used") or [])}
        except Exception:
            pass
    return local_grade(question, answer)
