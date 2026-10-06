"""Offline-first coaching state machine. Optional LLM hook reads env at runtime."""
import os
import uuid

QUESTION_BANK = {
    "linux-basics": [
        {
            "id": "lb-1",
            "prompt": "Which command lists files including hidden ones?",
            "choices": ["ls -la", "ls -l", "dir /a", "list -h"],
            "answer": 0,
            "explain": "`ls -la` shows dotfiles; `-a` is the key flag.",
            "card": {"title": "ls -la", "subtitle": "List all files", "image": None},
        },
        {
            "id": "lb-2",
            "prompt": "Which file holds user account info on Linux?",
            "choices": ["/etc/passwd", "/etc/shadow", "/etc/hosts", "/var/log/auth"],
            "answer": 0,
            "explain": "`/etc/passwd` is world-readable account metadata; hashes live in shadow.",
            "card": {"title": "/etc/passwd", "subtitle": "Account metadata", "image": None},
        },
        {
            "id": "lb-3",
            "prompt": "How do you check disk usage of a directory?",
            "choices": ["du -sh .", "df -h .", "free -m", "top"],
            "answer": 0,
            "explain": "`du -sh` summarizes; `df` is for filesystems.",
            "card": {"title": "du -sh", "subtitle": "Directory usage", "image": None},
        },
    ]
}

_sessions: dict = {}


def _bank(topic):
    return QUESTION_BANK.get(topic, QUESTION_BANK["linux-basics"])


def start_coaching(topic="linux-basics"):
    """Start a coaching run. Returns session handle for next_question/submit_answer."""
    key = uuid.uuid4().hex
    _sessions[key] = {"topic": topic, "idx": 0, "answered": 0, "correct": 0}
    # Hook point for AWS Builder mini-challenge: if MODEL_ENDPOINT/AWS creds are set,
    # a Bedrock/Strands call can personalize the bank here. Stub is default; never required.
    if os.environ.get("SKILLUP_LLM", "") == "1" and os.environ.get("MODEL_ENDPOINT"):
        pass  # documented extension; offline bank still serves the demo
    return {"session_key": key, "topic": topic, "total": len(_bank(topic))}


def next_question(session_key):
    st = _sessions[session_key]  # KeyError on unknown ->  auth boundary
    bank = _bank(st["topic"])
    if st["idx"] >= len(bank):
        return {"done": True, "total": len(bank)}
    q = bank[st["idx"]]
    return {
        "question_id": q["id"],
        "prompt": q["prompt"],
        "choices": q["choices"],
        "card": q["card"],
        "index": st["idx"],
        "total": len(bank),
    }


def submit_answer(session_key, question_id, choice):
    st = _sessions[session_key]
    bank = _bank(st["topic"])
    if st["idx"] >= len(bank) or bank[st["idx"]]["id"] != question_id:
        raise KeyError(question_id)
    q = bank[st["idx"]]
    if isinstance(choice, int):
        picked = choice
    elif choice in q["choices"]:
        picked = q["choices"].index(choice)
    else:
        picked = -1
    ok = picked == q["answer"]
    st["answered"] += 1
    st["correct"] += 1 if ok else 0
    st["idx"] += 1
    return {
        "correct": ok,
        "explain": q["explain"],
        "answer": q["choices"][q["answer"]],
        "has_next": st["idx"] < len(bank),
    }


def get_progress(session_key):
    st = _sessions[session_key]
    acc = st["correct"] / st["answered"] if st["answered"] else 0.0
    return {
        "answered": st["answered"],
        "correct": st["correct"],
        "accuracy": round(acc, 3),
        "remaining": len(_bank(st["topic"])) - st["idx"],
    }
