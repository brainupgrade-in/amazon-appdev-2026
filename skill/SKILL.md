# SkillUp Coach — Agent Skill

Front-door for Alexa+. Routes coaching requests to the self-hosted MCP server
(`src/skillup_mcp/server.py`, Streamable HTTP, spec 2025-11-25).
Hosted endpoint: `https://skillup-coach.gheware-ai.com/mcp`.

## Invoke
- "Coach me on context engineering" / "on prompting" → `start_coaching(topic="context-engineering")`
- "Coach me on AgentCore" / "on building agents" → `start_coaching(topic="agentcore")`
- Say the returned module `title` and question count before the first card.
- Render `next_question` as a card (title + prompt + choices).
- Speak the prompt and choices as A–D; accept a letter, an ordinal, or the answer text.
- `submit_answer(session_key, question_id, choice)` → speak `coach_tip` if present, else `explain`; show next card.
- `get_progress(session_key)` → "Answered N, accuracy X".

## Grounding
Tools are the source of truth; never invent question ids. Unknown session → restart
with `start_coaching`. Question packs (`packs/*.json`) cite a source URL per question; the offline packs are the default; `SKILLUP_LLM=1`
enables the optional Amazon Bedrock (Converse API) hook, grounded only in the module's pack facts
(AWS Builder mini-challenge), never required for the demo.
