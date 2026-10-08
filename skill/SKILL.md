# SkillUp Coach — Agent Skill

Front-door for Alexa+. Routes coaching requests to the self-hosted MCP server
(`src/skillup_mcp/server.py`, Streamable HTTP, spec 2025-11-25).

## Invoke
- "Coach me on Linux basics" → `start_coaching(topic="linux-basics")`
- Render `next_question` as a card (title + prompt + choices).
- `submit_answer(session_key, question_id, choice)` → speak `explain`, show next card.
- `get_progress(session_key)` → "Answered N, accuracy X".

## Grounding
Tools are the source of truth; never invent question ids. Unknown session → restart
with `start_coaching`. Offline question bank is default; `SKILLUP_LLM=1`
enables the optional Amazon Bedrock (Converse API) personalization hook
(AWS Builder mini-challenge), never required for the demo.
