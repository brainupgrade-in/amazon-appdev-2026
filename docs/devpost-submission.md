# Devpost submission — draft text (review before pasting)

Submission: https://devpost.com/submit-to/30992-build-ship-shape-amazon-developer-hackathon/manage/submissions/1220476/edit

## Step 1 — Project overview
**Project name (≤60):**
SkillUp Coach — voice upskilling on Alexa+

**Elevator pitch (≤200):**
A self-hosted MCP server for Alexa+ that coaches junior IT learners by voice: quiz cards, instant feedback, and Amazon Bedrock coach tips when you're wrong. Live on AWS.

**Thumbnail:** 3:2 screenshot of the live page mid-session (ring + card + Bedrock tip) — capture before submit.

## Step 2 — Project details

### About the project
## Inspiration
I train junior IT engineers in DevOps and agentic AI. They learn in short gaps — on a commute, between tickets — where opening docs doesn't happen. A coach you can just talk to, that keeps track of your progress and explains *why* you got it wrong, fits those gaps.

## What it does
Say "Alexa, coach me on Linux basics" and SkillUp Coach starts a session: it reads each question with A–D choices aloud, listens for your answer ("B", "the second one", or "slash etc slash passwd"), shows a card, and tells you if you're right. When you're wrong, Amazon Bedrock writes a short, spoken coach tip about *your* mistake. Each session also gets one fresh AI-generated question, and progress (answered, correct, accuracy) carries across turns.

## How we built it
- **MCP server** (Python, stdlib `http.server`), MCP spec **2025-11-25** over **Streamable HTTP**: a single `POST /mcp` with `initialize` → `MCP-Session-Id`, `tools/list`, `tools/call`; protocol-version and `Origin` checks; four tools — `start_coaching`, `next_question`, `submit_answer`, `get_progress`.
- **Agent Skill** (`skill/SKILL.md`) tells Alexa+ when and how to call each tool and how to speak results.
- **Amazon Bedrock** Converse API with **Amazon Nova Lite** (ap-south-1) for the extra question and coach tips; any Bedrock error falls back to the offline question bank, so the coach never breaks.
- **AWS App Runner** hosts the container at https://skillup-coach.gheware-ai.com; its IAM role can call only Nova Lite — no keys in the image.
- **Simulated Alexa+** web app: browser speech synthesis and recognition, chat-style transcript, cards. Bedrock output is rendered as text, never HTML.
- 21 unit tests (Bedrock mocked), test-first throughout.

## Challenges we ran into
- **Real Alexa+ access.** Alexa+ launched in India in September 2026, but the Alexa+ MCP Toolkit is US-only; the add-ons console shows "Coming Soon" for an India-based developer account. We used the track's simulated-Alexa+ path and kept the server on the toolkit's MCP version and transport so it is ready when access opens.
- **Speech is messy.** People say "ls dash la", not "ls -la"; we map spoken symbols and ordinals before matching.
- **Latency.** A Bedrock call takes 1–2 s; fine for a coach, but over the toolkit's 500 ms budget — next step is to generate tips off the request path.

## Accomplishments that we're proud of
- A spec-shaped MCP server with zero dependencies, live on AWS with a custom domain, in under a week.
- Least-privilege Bedrock access and a demo that degrades gracefully instead of failing.
- An open-source template extracted from it: [minimal-mcp-http](https://github.com/brainupgrade-in/minimal-mcp-http).

## What we learned
MCP's Streamable HTTP transport is small enough to implement directly; the hard parts of voice coaching are understanding spoken answers and keeping feedback short enough to say out loud.

## What's next for SkillUp Coach
OAuth 2.1 + async Bedrock calls to meet the Alexa+ MCP Toolkit requirements and go live on real Alexa+ when it reaches India; more topic banks (Kubernetes, AWS, Git); Hindi/Hinglish coaching to match Alexa+ in India; mentor dashboards from `get_progress`.

### Built with
python · model-context-protocol · amazon-bedrock · amazon-nova · aws-app-runner · amazon-ecr · aws-iam · docker · web-speech-api · javascript · cloudflare

### Try it out
- https://skillup-coach.gheware-ai.com
- https://github.com/brainupgrade-in/amazon-appdev-2026

### Video
(YouTube link — record ~19–20 Oct per `docs/demo-script.md`)

## Step 3 — Additional info
(Fill once the form's questions are visible. Sources: track = Alexa+; mini challenges = AWS Builder +
Open Source (`docs/oss-contribution.md`); product feedback + friction log = `docs/feedback-draft.md`;
built during the window: whole project, started 6 Oct 2026.)
