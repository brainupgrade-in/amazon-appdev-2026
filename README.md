# SkillUp Coach — Alexa+ track (Amazon AppDev 2026)

Hands-free upskilling for junior IT learners: self-hosted MCP server
(spec 2025-11-25, Streamable HTTP) + Agent Skill + simulated Alexa+ web demo.
Offline question bank by default; optional Amazon Bedrock hook for the AWS Builder mini-challenge.

## Run (stdlib only, no pip install)
```bash
PYTHONPATH=src python3 -m skillup_mcp.server --port 8000
# demo: open demo/index.html, click Start (calls http://127.0.0.1:8000/mcp)
PYTHONPATH=src python3 -m unittest discover -s tests
```
MCP endpoint: single POST `/mcp` (`initialize` → `MCP-Session-Id` → `tools/list` → `tools/call`
`start_coaching|next_question|submit_answer|get_progress`). GET returns 405 (spec-allowed, no SSE stream).

## Optional: Amazon Bedrock personalization (AWS Builder)
With `SKILLUP_LLM=1`, `src/skillup_mcp/tools.py` calls the Bedrock **Converse API** (boto3
`bedrock-runtime`) to add one AI-generated question per session and a spoken-style `coach_tip`
on wrong answers. Any Bedrock error falls back to the offline bank, so the demo never breaks.
```bash
python3 -m venv .venv && .venv/bin/pip install boto3
export SKILLUP_LLM=1 AWS_PROFILE=<profile> AWS_REGION=ap-south-1
export BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0   # default; any Converse-capable model id
PYTHONPATH=src .venv/bin/python -m skillup_mcp.server --port 8000
```
IAM needs only `bedrock:InvokeModel` on the chosen model / inference profile.

## Hosted
Live on AWS App Runner (ap-south-1) with Bedrock on: demo page at `/`, MCP at `/mcp`, health at `/health`.
Image: `Dockerfile` (`docker build -t skillup-coach .`); `ALLOWED_ORIGINS` lists extra browser origins.

See `skill/SKILL.md`, `todo/skillup-coach.md`. Brief, tracks and status: `CLAUDE.md`.