# SkillUp Coach — Alexa+ track (Amazon AppDev 2026)

Hands-free upskilling for junior IT learners: self-hosted MCP server
(spec 2025-11-25, Streamable HTTP) + Agent Skill + simulated Alexa+ web demo.
Offline question bank by default; optional Bedrock/Strands hook for the AWS Builder mini-challenge.

## Run (stdlib only, no pip install)
```bash
PYTHONPATH=src python3 -m skillup_mcp.server --port 8000
# demo: open demo/index.html, click Start (calls http://127.0.0.1:8000/mcp)
PYTHONPATH=src python3 -m unittest discover -s tests
```
MCP endpoint: single POST `/mcp` (`initialize` → `MCP-Session-Id` → `tools/list` → `tools/call`
`start_coaching|next_question|submit_answer|get_progress`). GET returns 405 (spec-allowed, no SSE stream).
See `skill/SKILL.md`, `todo/skillup-coach.md`. Brief, tracks and status: `CLAUDE.md`.