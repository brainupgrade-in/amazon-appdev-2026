# SkillUp Coach — hands-free upskilling on Alexa+

**Alexa+ track · Amazon AppDev 2026 ("Build, Ship, Shape")** · MIT licensed

SkillUp Coach is a self-hosted **MCP server** (spec 2025-11-25, Streamable HTTP) that coaches junior IT
learners by voice: quiz cards, instant feedback, a spoken coach tip when you get it wrong, and progress
tracking across turns. Two learning modules: **Prompts and Context Engineering** and **Building agents with
Amazon Bedrock AgentCore**. An **Agent Skill** fronts it for Alexa+, a **simulated Alexa+ web app** speaks and
listens in the browser, and **Amazon Bedrock** (Nova Lite) personalises each session.

**Try it live:** https://skillup-coach.gheware-ai.com — press Start, allow the microphone, answer by voice
("B", "the second one", "three to five") or tap. MCP endpoint: `https://skillup-coach.gheware-ai.com/mcp`.

## Why
Junior engineers learn agentic AI in short gaps — commuting, between tickets — where reading docs doesn't
work. Voice-first coaching with a card on screen meets them there. Sessions keep state across turns, so the
coach knows where you are and how you're doing; question packs are data files, swappable per team.

## Learning modules (`packs/*.json`)
| Module | Covers | Sources |
|---|---|---|
| `context-engineering` — Prompts and Context Engineering | few-shot vs zero-shot, system prompts, structure, long context, context budgets, compaction, just-in-time retrieval, RAG, tool descriptions, prompt injection, evals | Anthropic and AWS prompt-engineering docs, OWASP LLM01 |
| `agentcore` — Building agents with Amazon Bedrock AgentCore | Runtime, Memory and its strategies, Gateway, Identity, Observability, Code Interpreter, Browser, when to use which | Official AgentCore developer guide |

Each question carries a `source` URL. A session draws 4 questions; with Bedrock on, one more question is
generated **grounded only in the module's own facts** (the AI may not add facts from elsewhere).

## How it works
```
 Alexa+ (simulated web app: speech in/out)          Agent Skill (skill/SKILL.md)
              │  JSON-RPC over Streamable HTTP              │ tells Alexa+ when/how to call the tools
              ▼                                             ▼
   POST /mcp ── SkillUp Coach MCP server (src/skillup_mcp/server.py, stdlib http.server)
              │  initialize → MCP-Session-Id → tools/list → tools/call
              ▼
   coaching state machine (src/skillup_mcp/tools.py)
     start_coaching · next_question · submit_answer · get_progress
              │  optional, env-gated (SKILLUP_LLM=1)
              ▼
   Amazon Bedrock Converse API (Nova Lite, ap-south-1)
     + 1 AI question per session, grounded in the pack's facts · + coach_tip on wrong answers
     any error → offline question bank (demo never breaks)
```
- **MCP compliance:** single `POST /mcp`; `initialize` returns `MCP-Session-Id`, later calls must send it;
  `MCP-Protocol-Version` checked (400 on mismatch); `Origin` validated (403) per the spec's DNS-rebinding
  warning; `GET /mcp` → 405 (allowed when no SSE stream is offered).
- **Hosting:** AWS App Runner (ap-south-1) from the `Dockerfile`; an instance role allows only
  `bedrock:InvokeModel` on Nova Lite — no keys in the container. `GET /` serves the demo, `GET /health` for checks.
- **Safety:** Bedrock output is treated as untrusted — the demo renders it as text, never HTML.

## Run locally (stdlib only — no install)
```bash
PYTHONPATH=src python3 -m skillup_mcp.server --port 8000
# open http://127.0.0.1:8000/  (demo page, same-origin /mcp)
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/smoke.py http://127.0.0.1:8000             # end-to-end check (also run after each deploy)
```

### With Amazon Bedrock (AWS Builder mini-challenge)
```bash
python3 -m venv .venv && .venv/bin/pip install boto3
export SKILLUP_LLM=1 AWS_PROFILE=<profile> AWS_REGION=ap-south-1
export BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0   # default; any Converse-capable model id
PYTHONPATH=src .venv/bin/python -m skillup_mcp.server --port 8000
```
IAM needs only `bedrock:InvokeModel` on the chosen model / inference profile.

### Container / deploy
```bash
docker build -t skillup-coach .
docker run -p 8080:8080 -e SKILLUP_LLM=0 skillup-coach          # offline
# App Runner: push to ECR, then `aws apprunner start-deployment --service-arn <arn>`
```
`ALLOWED_ORIGINS` (comma-separated hostnames) adds browser origins beyond localhost.

## Repo map
| Path | What |
|---|---|
| `src/skillup_mcp/server.py` | Streamable HTTP + JSON-RPC dispatch, sessions, Origin/version checks |
| `src/skillup_mcp/tools.py` | Coaching state machine, question bank, Bedrock hook |
| `skill/SKILL.md` | Agent Skill: when and how Alexa+ should call the tools |
| `demo/index.html` | Simulated Alexa+: speech synthesis + recognition, cards, transcript |
| `tests/` | `unittest` suites (server contract, tools, Bedrock hook mocked, hosting) |
| `docs/feedback-draft.md` | Product feedback + friction log |

## Status and limits
- Real Alexa+ integration: the Alexa+ **MCP Toolkit** is US-only today; the add-ons console shows
  "Coming Soon" for our India-based developer account, so this entry uses the track's simulated-Alexa+
  fallback. The server already matches the toolkit's MCP version and transport; going live there would add
  OAuth 2.1 (PKCE) and move Bedrock calls off the request path to meet the 500 ms budget.
- In-memory sessions, single instance — fine for a demo, not for scale.

## Open source mini-challenge
[`brainupgrade-in/minimal-mcp-http`](https://github.com/brainupgrade-in/minimal-mcp-http) — a one-file,
stdlib-only MCP server template extracted from this project during the hackathon.

## License
MIT — see `LICENSE`.
