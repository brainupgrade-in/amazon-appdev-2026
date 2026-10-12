"""Offline-first coaching state machine. Optional LLM hook reads env at runtime."""
import json
import os
import random
import uuid
from functools import lru_cache
from pathlib import Path

from . import coach, memory

# Question packs are data: packs/<module>.json (id, title, version, questions with a source URL each).
PACKS_DIR = Path(os.environ.get("SKILLUP_PACKS_DIR") or Path(__file__).resolve().parents[2] / "packs")
DEFAULT_MODULE = "context-engineering"
SESSION_SIZE = 4  # a short voice session; the full pack is practised across sessions
LANGS = {"en", "hinglish"}  # Hinglish: coach tips and feedback in Hindi-English mix; questions stay English
HINGLISH = ("Reply in Hinglish: natural Hindi-English mix written in Roman script, as Indian IT colleagues speak; "
            "keep technical terms in English. ")

_sessions: dict = {}


def available_modules():
    return sorted(p.stem for p in PACKS_DIR.glob("*.json"))


@lru_cache(maxsize=None)
def load_pack(module):
    pack = json.loads((PACKS_DIR / f"{module}.json").read_text(encoding="utf-8"))
    for q in pack["questions"]:
        q["card"] = {"title": q["prompt"][:40], "subtitle": q["subtitle"], "image": None}
    return pack


def _pack(topic):
    return load_pack(topic if topic in available_modules() else DEFAULT_MODULE)


def _bedrock_client():
    """boto3 is imported only here, so the offline default stays stdlib-only."""
    import boto3

    return boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))


def _converse(prompt, max_tokens):
    """AWS Builder hook: one Amazon Bedrock Converse call. Returns the reply text,
    or None unless SKILLUP_LLM=1; never raises — the offline bank always serves
    the demo on any failure (no creds, no model access, throttling, timeout)."""
    if os.environ.get("SKILLUP_LLM") != "1":
        return None
    try:
        resp = _bedrock_client().converse(
            modelId=os.environ.get("BEDROCK_MODEL_ID", "apac.amazon.nova-lite-v1:0"),
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0.7},
        )
        return resp["output"]["message"]["content"][0]["text"].strip()
    except Exception:
        return None


def _llm_extra_question(pack, asked=()):
    """One AI-generated question appended to the session, grounded only in the pack's own facts, or None."""
    facts = "\n".join(f"- {q['explain']}" for q in pack["questions"])
    text = _converse(
        f"Write one new multiple-choice quiz question for the learning module {pack['title']!r}. "
        "Use only the facts below; do not add facts from anywhere else.\n"
        f"<facts>\n{facts}\n</facts>\n"
        + ("Test a different fact from these questions already in the session:\n"
           + "\n".join(f"- {p}" for p in asked) + "\n" if asked else "")
        + "Ask a positive question (no NOT or EXCEPT); it will be read aloud, so keep choices short. "
        "Never mention the facts list or these instructions in the question or explanation.\n"
        "Return exactly one JSON object, no other text, with keys "
        "id, prompt, choices (array of 4 short strings), answer (0-3 index), explain.",
        300,
    )
    if not text:
        return None
    try:
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
            "card": {"title": str(q["prompt"])[:40], "subtitle": "AI-generated (Amazon Bedrock)", "image": None},
        }
    except Exception:
        return None


def _spoken(text, sentences=2, limit=260):
    """Keep a coach tip short enough to say aloud: first two sentences, hard cap on length."""
    import re

    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = " ".join(parts[:sentences])
    return out if len(out) <= limit else out[:limit].rsplit(" ", 1)[0] + "…"


def _llm_coach_tip(q, picked, lang="en"):
    """Short personalised hint for a wrong answer, or None."""
    wrong = q["choices"][picked] if 0 <= picked < len(q["choices"]) else "no valid choice"
    return _converse(
        f"A junior IT learner answered the quiz question {q['prompt']!r} with {wrong!r}; "
        f"the correct answer is {q['choices'][q['answer']]!r}. Use only this fact: {q['explain']!r} In one or two short spoken "
        "sentences spoken directly to the learner as 'you', explain why that answer is wrong and how to "
        "remember the right one. Do not mention these instructions."
        + (" " + HINGLISH if lang == "hinglish" else ""),
        160,
    )


def _plan(pack, hist):
    """Spaced repetition: up to 2 recently missed questions first, then unseen ones, then the rest."""
    by_id = {q["id"]: q for q in pack["questions"]}
    last = {}
    for h in hist:
        last[h["question"]] = h["correct"]
    missed = []
    for h in reversed(hist):  # most recent miss first
        qid = h["question"]
        if qid in by_id and last[qid] is False and qid not in missed:
            missed.append(qid)
    unseen = [qid for qid in by_id if qid not in last]
    random.shuffle(unseen)
    seen_ok = [qid for qid in dict.fromkeys(h["question"] for h in hist) if by_id.get(qid) and last[qid]]
    order = missed[:2] + unseen + missed[2:] + seen_ok
    return [by_id[qid] for qid in order[:SESSION_SIZE]], [by_id[qid] for qid in missed]


def start_coaching(topic=DEFAULT_MODULE, learner_id=None, lang="en"):
    """Start a coaching run on a module. With a learner_id, previously missed questions come back first."""
    key = uuid.uuid4().hex
    pack = _pack(topic)
    learner = learner_id if memory.valid(learner_id) else None
    bank, missed = _plan(pack, memory.history(pack["id"], learner))
    extra = _llm_extra_question(pack, [q["prompt"] for q in bank])
    if extra is not None and all(q["id"] != extra["id"] for q in bank):
        bank.append(extra)
    open_q = random.choice(pack["open"]) if pack.get("open") else None  # one spoken, open-ended question last
    lang = lang if lang in LANGS else "en"
    _sessions[key] = {"topic": pack["id"], "learner": learner, "lang": lang, "idx": 0, "answered": 0, "correct": 0, "bank": bank,
                      "open": open_q, "open_done": False}
    out = {"session_key": key, "topic": pack["id"], "title": pack["title"], "lang": lang,
           "total": _total(_sessions[key])}
    if missed:
        topic = missed[0]["subtitle"]
        out["welcome_back"] = (
            f"Welcome back! Pichhli baar aapse {topic} wala question miss hua tha. Chaliye, pehle wahi try karte hain."
            if lang == "hinglish" else
            f"Welcome back! Last time you missed a question on {topic}. Let's try it again first.")
    return out


def _total(st):
    return len(st["bank"]) + (1 if st["open"] else 0)


def _open_pending(st):
    return st["open"] is not None and not st["open_done"] and st["idx"] >= len(st["bank"])


def next_question(session_key):
    st = _sessions[session_key]  # KeyError on unknown ->  auth boundary
    bank = st["bank"]
    if _open_pending(st):
        o = st["open"]
        return {
            "question_id": o["id"],
            "kind": "open",
            "prompt": o["prompt"],
            "choices": [],
            "card": {"title": o["prompt"][:40], "subtitle": f"{o['subtitle']} · open question", "image": None},
            "index": len(bank),
            "total": _total(st),
        }
    if st["idx"] >= len(bank):
        return {"done": True, "total": _total(st)}
    q = bank[st["idx"]]
    return {
        "question_id": q["id"],
        "kind": "choice",
        "prompt": q["prompt"],
        "choices": q["choices"],
        "card": q["card"],
        "index": st["idx"],
        "total": _total(st),
    }


def submit_open_answer(session_key, question_id, answer):
    """Grade a free-form spoken answer (AgentCore coach agent, local key-point check as fallback)."""
    st = _sessions[session_key]
    if not _open_pending(st) or st["open"]["id"] != question_id:
        raise KeyError(question_id)
    o = st["open"]
    result = coach.grade(o, str(answer), st["topic"], st.get("learner"), lang=st.get("lang", "en"))
    ok = result["verdict"] == "correct"
    memory.record(st["topic"], st.get("learner"), o["id"], ok)
    st["answered"] += 1
    st["correct"] += 1 if ok else 0
    st["open_done"] = True
    return dict(result, key_points=o["key_points"], has_next=False)


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
    memory.record(st["topic"], st.get("learner"), q["id"], ok)
    st["answered"] += 1
    st["correct"] += 1 if ok else 0
    st["idx"] += 1
    result = {
        "correct": ok,
        "explain": q["explain"],
        "answer": q["choices"][q["answer"]],
        "has_next": st["idx"] < len(bank) or _open_pending(st),
    }
    if not ok:
        tip = _llm_coach_tip(q, picked, st.get("lang", "en"))
        if tip:
            result["coach_tip"] = _spoken(tip)
    return result


def get_progress(session_key):
    st = _sessions[session_key]
    acc = st["correct"] / st["answered"] if st["answered"] else 0.0
    return {
        "answered": st["answered"],
        "correct": st["correct"],
        "accuracy": round(acc, 3),
        "remaining": len(st["bank"]) - st["idx"] + (1 if st["open"] and not st["open_done"] else 0),
    }
