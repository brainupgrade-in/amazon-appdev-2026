# Plan to reach Alexa+ top 3 — spec (rev 2, 12 Oct 2026)

Submitted 12 Oct: https://devpost.com/software/skillup-coach-voice-upskilling-on-alexa — editable until
**23 Oct 2026, 12:00 PDT (24 Oct 00:30 IST)**. Judging 9–20 Nov; winners around 3 Dec (Official Rules, read 12 Oct).

Rev 2 folds in: an independent spec review (12 Oct), the user's theme change (Prompts and Context Engineering), and
the user's decision to use **Amazon Bedrock AgentCore** both as the runtime stack and as a learning module.

## What the Official Rules settle
- The simulated Alexa+ web app is an explicitly allowed path, so Stage 1 (pass/fail) should pass.
- Stage 2: four equally weighted criteria — Tech Implementation, Design, Potential Impact, Quality of the Idea.
  Ties go to Tech Implementation first.
- Judges "may judge based solely on the text description, images, and video" — the video and write-up carry most
  of the weight.
- Friction log: worth up to a 10% bonus — done (`docs/friction-log.md`); new AgentCore friction gets added.
- Prizes, Alexa+ track: 1st $25k + $15k AWS credits · 2nd $15k + $5k · 3rd $4k + $1k. A project can win one
  track prize and one mini-challenge prize, so we push **AWS Builder** (Open Source stays entered as is).
- AWS credit codes ran out on 7 Oct (Rules page update); new AWS usage draws on the existing $150 credit.
- Devpost showed ~54,000 participants on 12 Oct (45,341 on 6 Oct).

## Where we stand against the rules' own examples
| | Rules call it "obvious" | Rules call it "creative" | SkillUp Coach today |
|---|---|---|---|
| Alexa+ | single-turn Q&A bot, basic MCP wrapper | agentic workflow, state across sessions, cards/carousels, MCP Apps, Agent Skills | Agent Skill ✓, cards ✓, memory only within one session ✗ |
| AWS Builder | single Bedrock call for text generation | Bedrock + AgentCore + Strands, agent orchestration | close to "obvious" |
| Open Source | README or typo fixes | feature addition with tests, new integration pattern | template with tests — middle |

## Target architecture
```
Simulated Alexa+ page ──POST /mcp──▶ MCP server (App Runner, fast tools, < 500 ms)
                                        │  invoke (async where slow)
                                        ▼
                     AgentCore Runtime: Strands coach agent ──▶ Bedrock (Nova Lite)
                                        │
                                        ▼
                     AgentCore Memory: per-learner history + missed topics (cross-session)
                     AgentCore Observability: traces per session (evidence for judges)
```
AgentCore APIs (Runtime, Memory, Gateway) verified reachable in **ap-south-1** for account 316777659122 on 12 Oct
(list calls return OK, no resources yet).

## Work items (in order)

### S. Safety first (13 Oct, ~2 h) — DONE 13 Oct
- Done: ECR `skillup-coach:submitted-v1` = live digest `sha256:d7af80…`; AWS Budget `skillup-coach-credit-burn`
  ($60/month excl. credits, alerts 50%/80% actual + 100% forecast → rajesh@unigps.in; Oct gross to 12 Oct $16.35);
  `start_coaching` capped at 30/hour per client IP; `scripts/smoke.py` passes live + local; story wording fixed in
  `docs/devpost-submission.md` (Devpost copy updated with item 5).
- Tag the current image `skillup-coach:submitted-v1` before any deploy; new features behind env flags so the
  submitted behaviour stays one flag away.
- AWS Budgets alarm on the $150 credit (e.g. 50% / 80%); simple per-IP rate limit on `/mcp`.
- Fix write-up wording now: the story says the coach "remembers where you are" — true within a session only until
  item 1 ships.
- Done when: rollback tag exists in ECR; budget alarm visible; smoke script (`/health`, `/`, MCP `initialize` →
  `tools/call`) passes.

### 0. Re-theme: two learning modules (13–14 Oct) — DONE 13 Oct (code; not yet deployed)
- Done: `packs/context-engineering.json` (18 q) + `packs/agentcore.json` (18 q, AgentCore dev-guide sources);
  engine loads packs, 4-question sessions, AI question + coach tip grounded in pack facts; demo has both module
  buttons; Agent Skill + README updated; 32 tests green; live Bedrock check OK. Devpost text + video script: item 5.
Module A — **Prompts and Context Engineering** (replaces Linux basics):
- 15–20 voice-friendly questions: role/instructions/examples, few-shot vs zero-shot, system prompts,
  context-window budgeting, retrieval and chunking, tool descriptions, prompt-injection defence, eval loops.

Module B — **Building agents with Amazon Bedrock AgentCore** (user decision, 12 Oct):
- 15–20 questions on what each AgentCore service is for and when to use it: Runtime (hosting agents, session
  isolation), Memory (short-term vs long-term, memory strategies), Gateway (turning APIs/Lambda into MCP tools),
  Identity (agent auth to tools), Observability (traces), built-in tools (Code Interpreter, Browser); plus
  framework-agnostic hosting (e.g. Strands) and choosing AgentCore vs a self-managed stack.
- Every question and explanation is checked against the official AWS AgentCore documentation before it ships
  (source URL kept per question in the bank); no claims from memory.
- **"Learn it from the thing itself"**: the coach runs on AgentCore, so Module B explanations point at the coach's
  own behaviour — e.g. after a Memory question: "I remembered your last mistake using AgentCore Memory — that's
  long-term memory." This links the learning content to the live architecture (Quality of the Idea + AWS Builder).
- Natural learning path: Module A (how to talk to models) → Module B (how to run agents in production), matching
  the entrant's agentic-AI training courses.

Both modules:
- Packs stay **public** in the repo (user decision, 13 Oct) as versioned data files (one JSON per module, a
  `source` URL per question), loaded from a configurable directory — not hard-coded Python.
- Fix the hard-coded "Linux-basics" wording in `_llm_extra_question` so AI questions follow the session's module.
- Learner picks a module by voice ("coach me on context engineering" / "coach me on AgentCore"); update demo
  buttons, Agent Skill, README, tests, Devpost story and video.
- Done when: `grep -ri linux src demo skill` is empty; each module has ≥15 questions, each with a source URL;
  a test proves an AI question for module M is requested about M; all tests green.

### G. AgentCore go/no-go spike (13 Oct, ≤ half a day)
- Deploy a hello-world Strands agent to **AgentCore Runtime** in ap-south-1 calling Nova Lite; create one
  **AgentCore Memory** resource and write/read one event.
- Go: continue with items 1–2 on AgentCore. No-go by end of day: run the Strands agent inside App Runner and keep
  AgentCore Memory if it worked; log the blocker in the friction log.

### 1. Cross-session memory + adaptive practice — AgentCore Memory (14–15 Oct)
- Learner id: random UUID generated in the browser, kept in localStorage; no login, no names, no PII
  (simulated Alexa+). Privacy note in the README.
- Memory namespace `org/cohort/learner` (hackathon: `public/demo/<uuid>`); each answer logged as an event
  (module, question, correct, time) so progress views are possible later.
- AgentCore Memory stores each learner's answers and missed topics (long-term memory strategy); MCP sessions stop
  living only in process memory.
- Spaced repetition: missed topics return early in later sessions. Greeting names the topic, e.g. "Welcome back —
  last time you mixed up few-shot and zero-shot prompting."
- Hits the rules' "maintains state across sessions" example.
- Done when: given learner L missed question Q in session 1, when L starts session 2 after a server restart, Q is
  among the first 2 questions and the greeting names its topic — passes in a unit test with Memory mocked and in one
  live run across two App Runner deploys.

### 2. Agentic coach — Strands Agents on AgentCore Runtime (16–18 Oct)
- The agent plans the session from the learner's memory, asks one open-ended question ("why put examples before the
  task in a prompt?") and grades the spoken free-form answer with a rubric; multiple-choice flow stays.
- MCP tools call the agent asynchronously so tool replies stay < 500 ms (ready for the real Alexa+ toolkit).
- AgentCore Observability traces each session; a trace id is shown in logs as evidence.
- Biggest lift for Tech Implementation and AWS Builder (Bedrock + AgentCore + Strands, agent orchestration).
- Done when: live `/` runs a session whose plan comes from the agent (trace id visible); a free-form answer is graded
  against a 10-case fixture with ≥ 8/10 agreement; on any agent failure the multiple-choice flow still completes.

### 3. Hindi/Hinglish mode + accessibility (19 Oct, then code freeze)
- Hinglish coaching via Nova Lite plus browser `hi-IN` speech — strong India impact story (already in "What's next").
- Accessibility pass on `demo/index.html`: keyboard-only flow, ARIA live region, captions — feeds the Design score.
- Done when: one full session runs in Hinglish; the whole flow works with keyboard only.

### 4. Learner feedback — opt-in volunteers (in parallel, 15–19 Oct)
- 5+ volunteers try it voluntarily, with written consent and a short privacy notice; client permission if they are
  from a paid cohort. No names or voices in the video without consent.
- Report only "N learners tried it; X% said…" — no learning-gain claims.

### 5. Video re-cut + Devpost update (20–21 Oct — a full day for the video)
- New features (memory greeting, agent-graded open answer) on screen before 0:30; total under 2:55; no
  third-party UI.
- Update the Devpost story, AWS Builder write-up (AgentCore Runtime + Memory + Observability + Strands), test counts,
  friction log; re-check every claim against the live build.
- Re-render tooling: `~/Videos/amazon-appdev-2026-demo/` (`record.py`, `edit.py`).

### 22–23 Oct: buffer only
Any Devpost edit, public push or video publish needs the user's explicit yes.

## Cut from rev 1
- **MCP Apps** — no demo client without third-party branding in the video; one mini prize only, and AgentCore
  helps AWS Builder more than MCP Apps helps Open Source.
- **OAuth 2.1 / Discord ask** — no judged benefit while the real toolkit is US-only.
- **Before/after learning study** — replaced by item 4 (ethics, consent, and too little data for an impact claim).

## Regression guard (every deploy)
All unit tests green; smoke script passes (`/health`, `/`, MCP `initialize` → `tools/call`); rollback = redeploy
`:submitted-v1`.

## Honest odds
With items 0–2 plus Hinglish and real volunteer feedback, the project moves from "competent quiz bot" to "creative"
on every judged criterion: a realistic shot at Alexa+ top 3 and a stronger one at AWS Builder. Not a sure thing
given ~54,000 registered participants.

## Constraints
- Only competition- or sponsor-provided endpoints and credits; no self-paid aggregators.
- Keep App Runner (and AgentCore resources) running through judging (ends 20 Nov); pause/delete after.
