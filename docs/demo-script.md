# Demo video script — SkillUp Coach (target 2:30, hard cap 3:00)

Rules: public YouTube/Vimeo, English, lead with the best material (judges stop at 3:00).
No third-party trademarks, no copyrighted music/footage. Screen-record + voiceover only.

## Shots & narration (approx timings)
### 0:00–0:15 — Hook (the idea in one breath)
- SHOW: title card "SkillUp Coach — hands-free upskilling on Alexa+".
- SAY: "SkillUp Coach is a self-hosted MCP server for the Alexa+ track that coaches
  junior IT learners by voice, with quiz cards, instant feedback and progress tracking."

### 0:15–1:10 — Live demo (best material first)
- SHOW: terminal `PYTHONPATH=src python3 -m skillup_mcp.server --port 8000`.
- SHOW: MCP round-trip (curl or inspector): `initialize` → session id →
  `tools/call start_coaching` → `next_question` card JSON.
- SHOW: `demo/index.html` in browser: click Start, answer one card right, one wrong,
  progress line updates ("Answered 2, accuracy 0.5").
- SAY: "Four tools, stateful sessions, cards a screen can render — all offline by default."

### 1:10–1:50 — How it's built (Tech Implementation)
- SHOW: `src/skillup_mcp/server.py` + `tools.py` briefly; `skill/SKILL.md`.
- SAY: "Single POST /mcp endpoint following MCP spec 2025-11-25: session headers,
  protocol-version check, Origin validation. Stdlib only — no install. An Agent Skill
  file fronts it for Alexa+, and an env-gated hook adds Bedrock personalization
  for the AWS Builder mini-challenge without ever breaking the offline demo."

### 1:50–2:25 — Why it matters (Impact + Idea)
- SHOW: progress JSON / second topic card.
- SAY: "Corporate upskilling is a paying market; voice-plus-cards coaching reaches
  learners where docs don't. Unlike a single-turn Q&A bot, sessions persist state
  across turns, and the question bank is swappable per team."

### 2:25–2:35 — Close
- SHOW: repo URL + `python3 -m unittest` green run.
- SAY: "Open source, MIT, runs in one command. Links in the description."

## Recording checklist
- [ ] Fresh terminal, large font, `127.0.0.1:8000` visible.
- [ ] Browser demo pre-loaded; rehearse the two answers once.
- [ ] `PYTHONPATH=src python3 -m unittest discover -s tests` green on screen for the close.
- [ ] Export 1080p, check audio levels, upload unlisted-first to review, then public.
