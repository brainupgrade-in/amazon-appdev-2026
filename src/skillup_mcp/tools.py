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


def _llm_extra_question(topic):
    """AWS Builder hook: one optional extra question via an OpenAI-compatible
    endpoint (Bedrock/AgentCore proxy or any sponsor endpoint). Returns None
    unless SKILLUP_LLM=1 and MODEL_ENDPOINT are set; never raises — the
    offline bank always serves the demo on any failure."""
    if os.environ.get("SKILLUP_LLM") != "1":
        return None
    endpoint = (os.environ.get("MODEL_ENDPOINT") or "").rstrip("/")
    if not endpoint:
        return None
    import json
    import urllib.request

    prompt = (
        "Return exactly one JSON object, no other text, with keys "
        'id, prompt, choices (array of 4 strings), answer (0-3 index), explain: '
        f"a Linux-basics quiz question about {topic}."
    )
    body = json.dumps(
        {
            "model": os.environ.get("MODEL_NAME", "default"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7,
        }
    ).encode()
    try:
        req = urllib.request.Request(
            endpoint + "/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('MODEL_TOKEN', '')}",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        text = data["choices"][0]["message"]["content"]
        q = json.loads(text[text.index("{") : text.rindex("}") + 1])
        if (
            not isinstance(q.get("choices"), list)
            or len(q["choices"]) != 4
            or not 0 <= int(q["answer"]) <= 3
        ):
            return None
        return {
            "id": str(q.get("id", "llm-1")),
            "prompt": str(q["prompt"]),
            "choices": [str(c) for c in q["choices"]],
            "answer": int(q["answer"]),
            "explain": str(q.get("explain", "")),
            "card": {"title": str(q["prompt"])[:40], "subtitle": "AI-generated", "image": None},
        }
    except Exception:
        return None


def start_coaching(topic="linux-basics"):
    """Start a coaching run. Returns session handle for next_question/submit_answer."""
    key = uuid.uuid4().hex
    bank = list(_bank(topic))
    extra = _llm_extra_question(topic)
    if extra is not None and all(q["id"] != extra["id"] for q in bank):
        bank.append(extra)
    _sessions[key] = {"topic": topic, "idx": 0, "answered": 0, "correct": 0, "bank": bank}
    return {"session_key": key, "topic": topic, "total": len(bank)}


def next_question(session_key):
    st = _sessions[session_key]  # KeyError on unknown ->  auth boundary
    bank = st["bank"]
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
    bank = st["bank"]
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
        "remaining": len(st["bank"]) - st["idx"],
    }
