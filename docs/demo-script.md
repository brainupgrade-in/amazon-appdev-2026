# Demo video script — SkillUp Coach (target 2:30, hard cap 3:00)

Rules: public YouTube/Vimeo, English, lead with the best material (judges stop at 3:00).
No third-party trademarks, no copyrighted music/footage. Screen-record + voiceover only.
Record in Chrome at https://skillup-coach.gheware-ai.com with sound on (the coach's voice is the demo).

## Shots & narration (approx timings)
### 0:00–0:12 — Hook
- SHOW: the live page, ring idle.
- SAY: "SkillUp Coach is an MCP server for Alexa+ that coaches junior IT learners by voice —
  you talk, it quizzes you, and when you're wrong, Amazon Bedrock explains why."

### 0:12–1:15 — Live voice demo (best material first)
- SHOW: press "Alexa, coach me on Linux basics". Coach speaks the first question and A–D choices.
- DO: say "A" → "Correct!". Next question: say "slash etc slash passwd" → correct.
- DO: deliberately say a wrong answer → red/green highlight, coach speaks a **Bedrock coach tip**.
- SHOW: question 4 tagged "AI-generated (Amazon Bedrock)"; finish → "You got N of 4 right".
- NOTE: start_coaching waits ~1–2 s for Bedrock — keep talking over it, don't cut.

### 1:15–1:55 — How it's built (Tech Implementation)
- SHOW: README diagram; `server.py` (POST /mcp, session id, Origin check); `skill/SKILL.md`.
- SHOW: terminal: curl `initialize` → `MCP-Session-Id`; `tools/list` → 4 tools.
- SAY: "A self-hosted MCP server on spec 2025-11-25, Streamable HTTP. An Agent Skill tells Alexa+ when to call
  each tool. It runs on AWS App Runner; the Bedrock Converse API with Amazon Nova Lite writes a fresh question
  and personal coach tips — with an IAM role that can only call that one model, and an offline fallback."

### 1:55–2:25 — Why it matters (Impact + Idea)
- SAY: "Junior engineers learn in short gaps where docs don't work. Voice plus a card meets them there; the
  session remembers progress, and the question bank is swappable per team — Linux today, Kubernetes next."
- SAY (honest, brief): "Alexa+ launched in India last month, but the MCP Toolkit is US-only, so this runs as a
  simulated Alexa+ — the server already speaks the toolkit's MCP version and transport."

### 2:25–2:40 — Close
- SHOW: repo URL + `python3 -m unittest` green (21 tests); live URL.
- SAY: "Open source, MIT. Try it live — link below."

## Recording checklist
- [ ] Chrome, mic allowed for skillup-coach.gheware-ai.com, system audio captured, quiet room.
- [ ] Rehearse once; Bedrock text varies per run — that's fine, it proves it's live.
- [ ] Big font in terminal; README diagram zoomed.
- [ ] Export 1080p, check audio levels, upload unlisted first to review, then public.
