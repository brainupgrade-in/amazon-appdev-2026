# Devpost submission — draft text (review before pasting)

Submission: https://devpost.com/submit-to/30992-build-ship-shape-amazon-developer-hackathon/manage/submissions/1220476/edit

## Step 1 — Project overview
**Project name (≤60):**
SkillUp Coach — voice upskilling on Alexa+

**Elevator pitch (≤200):**
A voice coach on Alexa+ that remembers what you got wrong. A Strands agent on Amazon Bedrock AgentCore grades what you say. Agentic AI modules, in English and Hinglish.

**Thumbnail:** live-session screenshot (3:2), unchanged.

## Step 2 — Project details

### About the project
## Inspiration
I train junior IT engineers in agentic AI. They learn in short gaps — on a commute, between tickets — where opening docs doesn't happen. A coach you can just talk to, that remembers where you struggled and explains *why* you got it wrong, fits those gaps.

## What it does
Say "Alexa, coach me on AgentCore" (or "on context engineering"). SkillUp Coach reads each question with A–D choices aloud, listens for your answer, shows a card and tells you if you're right. Wrong answers get a short spoken coach tip from Amazon Bedrock. Every session ends with one **open question you answer in your own words**, and a **Strands agent on Amazon Bedrock AgentCore Runtime** grades it point by point.

It **remembers you**: every answer is stored in **AgentCore Memory**, so next time it opens with "Welcome back! Last time you missed a question on AgentCore Memory. Let's try it again first", and the agent's feedback links today's answer to your past mistakes ("this time you nailed it").

Two learning modules, each question citing its official source: **Prompts and Context Engineering** and **Building agents with Amazon Bedrock AgentCore**. A **Hinglish** mode switches the coach to natural Hindi-English, as Indian IT teams actually talk. You can also answer with the keyboard.

## How we built it
- **MCP server** (Python stdlib), spec **2025-11-25**, **Streamable HTTP**, five tools: `start_coaching`, `next_question`, `submit_answer`, `submit_open_answer`, `get_progress`; protocol-version and Origin checks. Hosted on **AWS App Runner**.
- **Agent Skill** (`skill/SKILL.md`) tells Alexa+ when to call each tool and how to speak results.
- **AgentCore Runtime:** a **Strands** coach agent on **Amazon Nova Lite**, deployed as an arm64 zip. It grades each key point with evidence (structured output); the verdict is computed in code from those judgments, so it can't contradict them. The learner's answer is treated as untrusted data.
- **AgentCore Memory:** one event per answer per learner (anonymous ID, no login). Spaced repetition brings missed questions back first; the agent's `learner_history` tool reads the same memory to personalise feedback.
- **AgentCore Observability:** ADOT traces in CloudWatch show the whole loop — `invoke_agent` → `learner_history` → Memory `ListEvents` → Nova.
- **Bedrock Converse** writes one extra question per session and the coach tips, **grounded only in the module's own facts**.
- Least privilege throughout: each IAM role can call only Nova Lite, this one memory, or this one runtime.
- **Simulated Alexa+** web app: speech in/out, chat transcript, cards.
- **Quality:** 52 unit tests; a 12-case grading eval where the agent matches expected verdicts on 10–12 of 12 (a prompt-injection answer is graded incorrect); a smoke test after every deploy.

## Challenges we ran into
- **Real Alexa+ access.** The Alexa+ MCP Toolkit is US-only; the add-ons console shows "Coming Soon" for an India developer account, so we used the track's simulated-Alexa+ path and kept the server on the toolkit's MCP version and transport.
- **Consistent grading.** Nova Lite sometimes graded a complete answer "partial", or gave a verdict that contradicted its own reasoning. Judging each key point separately with quoted evidence, then computing the verdict in code, fixed it (10/10 on the base set).
- **Voice length.** Model tips ran 20–30 seconds aloud, especially in Hinglish; we cap them at two sentences in code.
- **Observability setup.** Spans only appear after CloudWatch Transaction Search is enabled for the account; earlier calls aren't traced.

## Accomplishments that we're proud of
- A real agentic loop on AgentCore — Runtime, Memory and Observability working together — live on AWS in a week.
- A coach that remembers you, and is honest: sourced questions, grounded AI, least privilege, measured grading.
- An open-source template extracted from it: [minimal-mcp-http](https://github.com/brainupgrade-in/minimal-mcp-http).

## What we learned
Context engineering is the product: grounding the model in a module's facts, treating answers as untrusted, and keeping spoken output short mattered more than model size. AgentCore made memory and hosting the easy part.

## What's next for SkillUp Coach
Go live on real Alexa+ when the MCP Toolkit reaches India (add OAuth 2.1 and async grading for the 500 ms budget); more modules (Kubernetes, AWS, RAG); a mentor dashboard on top of AgentCore Memory.

### Built with
python · model-context-protocol · amazon-bedrock · amazon-bedrock-agentcore · agentcore-memory · strands-agents · amazon-nova · aws-app-runner · amazon-ecr · aws-iam · amazon-cloudwatch · opentelemetry · docker · web-speech-api · javascript

### Try it out
- https://skillup-coach.gheware-ai.com
- https://github.com/brainupgrade-in/amazon-appdev-2026

### Video
https://www.youtube.com/watch?v=ncJ5iSOvbao (v2, replaces https://www.youtube.com/watch?v=d-RyZ5Es5qI once approved)

## Step 3 — Additional info
(Fill once the form's questions are visible. Sources: track = Alexa+; mini challenges = AWS Builder +
Open Source (`docs/oss-contribution.md`); product feedback + friction log = `docs/feedback-draft.md`;
built during the window: whole project, started 6 Oct 2026.)
