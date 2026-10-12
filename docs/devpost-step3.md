# Devpost step 3 — Additional info (DRAFT, review before pasting)

Form read 12 Oct 2026. Fields marked ⚠ need the user's own answer.

## Submitter
- **Upload a file:** none
- **Submitter type:** Organization (rules check pending)
- **Organization name:** Gheware UniGPS Solutions LLP
- **Country of residence:** India
- **Canada province:** N/A

## Track and repo
- **Primary track:** Alexa+
- **Code repository:** https://github.com/brainupgrade-in/amazon-appdev-2026 (public, MIT licence shown in About)
- **New or existing before 31 Aug 2026:** New (first commit 6 Oct 2026)

## AWS Builder Mini Challenge — Yes
**Which AWS services did you incorporate and how?** (updated 13 Oct)
- **Amazon Bedrock AgentCore Runtime:** hosts the SkillUp coach agent (Strands Agents on Amazon Nova Lite), deployed
  as an arm64 zip (`agent/main.py`, `agent/deploy.py`). The MCP server invokes it for every open-ended spoken answer
  (`src/skillup_mcp/coach.py`); it grades each key point with evidence via structured output, and the verdict is
  computed in code. One warm runtime session per learner.
- **Amazon Bedrock AgentCore Memory:** one event per answer per learner (`src/skillup_mcp/memory.py`), summary and
  user-preference strategies; spaced repetition brings missed questions back first ("Welcome back…"), and the
  agent's `learner_history` tool reads the same memory to personalise feedback.
- **Amazon Bedrock AgentCore Observability:** ADOT instrumentation + CloudWatch Transaction Search; traces show
  `invoke_agent` → `execute_tool learner_history` → Memory `ListEvents` → Nova `chat`.
- **Amazon Bedrock (Converse API) with Amazon Nova Lite:** one extra question per session and spoken coach tips,
  grounded only in the module's own facts; offline fallback on any error.
- **AWS App Runner** (MCP server + demo, custom domain), **Amazon ECR** (images, rollback tag), **Amazon S3** (agent
  code package), **AWS IAM** (least privilege: Nova Lite only / this memory only / this runtime only),
  **Amazon CloudWatch** (traces, logs), **AWS Budgets** (credit alarm).
- Documented in the README and `docs/top3-plan.md`; 52 unit tests; grading eval `agent/eval_grading.py`.

## Open Source Mini Challenge — Yes
- **Contribution URL:** https://github.com/brainupgrade-in/minimal-mcp-http
- **Project repository URL:** https://github.com/brainupgrade-in/amazon-appdev-2026
- **GitHub username:** brainupgrade-in
- **What, how, why:** A new MIT-licensed template created during the hackathon window: a one-file, stdlib-only MCP
  server over Streamable HTTP (spec 2025-11-25) with `echo`/`add` example tools, 5 unit tests and an "add your own
  tool" recipe. It works as a single `POST /mcp` endpoint (`initialize` → `MCP-Session-Id` → `tools/list` →
  `tools/call`), returns 405 on `GET`, and enforces Origin and protocol-version headers; run it with
  `python3 minimal_mcp_server.py --port 8000`, no installs. It matters because solo and small-team Alexa+ builders
  get a zero-dependency, spec-shaped starting point that they can read in one sitting and extend, extracted from the
  SkillUp Coach server.

## [Optional] Feature requests
1. **Open the Alexa+ add-ons console and simulator to non-US developer accounts** (distribution can stay US-only).
   Why: Alexa+ launched in India in Sep 2026, but Indian developers can't test an MCP add-on at all. **Critical.**
2. **A documented async / progressive-response pattern for LLM-backed MCP tools** within the 500 ms budget.
   Why: a Bedrock call takes 1–2 s, so a per-answer coach tip can't run inside the tool call today. **Important.**
3. **An unauthenticated option for public tools that touch no user data** (OAuth 2.1 + PKCE is required today).
   Why: a public quiz coach has no account to link; OAuth is pure overhead for it. **Nice-to-have.**

## [Optional] Friction log
Devpost field is URL-only → link https://github.com/brainupgrade-in/amazon-appdev-2026/blob/main/docs/friction-log.md

1. **Connect the hosted MCP server to real Alexa+.** Steps: read MCP Toolkit overview + quickstart; signed in to
   developer.amazon.com (India account); opened the add-ons console (8 Oct). Expected: add-ons console + web simulator.
   Actual: "Coming Soon"; docs say the toolkit is US-only, while Alexa+ itself is live in India. **Severity: high**
   for non-US entrants in this track. Workaround: the track's simulated-Alexa+ path. Suggestion: open the console to
   all developer accounts and state the US-only limit on the hackathon Resources page.
2. **Fit an LLM call into the toolkit's limits.** Observed: OAuth 2.1 auth-code + PKCE required and a <500 ms round
   trip. Expected: guidance for tools that call an LLM. Actual: none; our Bedrock call is ~1–2 s. **Severity: medium.**
   Workaround: kept the server spec-compliant; async tips planned. Suggestion: document an async/progressive pattern.
3. **First Bedrock call from ap-south-1.** Steps: `aws bedrock list-inference-profiles` → called Converse with the
   base model id. Expected: base id works in-region. Actual: the callable id is the `apac.` cross-region inference
   profile; worked first try once switched (8 Oct). **Severity: low.** Workaround: list profiles first. Suggestion:
   show the exact callable id per region on the model card.
4. **Request AWS credits.** Steps: compared the credit-form links on the Rules and Resources pages. Expected: one URL.
   Actual: two different form links. **Severity: medium** (blocks the credit request). Workaround: used the Resources
   link. Suggestion: one canonical URL on both pages.
5. **Build an MCP server without an SDK.** Steps: read the 2025-11-25 transports page. Expected: SSE mandatory.
   Actual: POST-only with `GET` → 405 is compliant. **Severity: low.** Suggestion: publish a "minimal compliant server"
   example (we published one: minimal-mcp-http).

## [Optional] Project testing link
https://skillup-coach.gheware-ai.com (voice demo at `/`, MCP endpoint at `/mcp`, `/health`)

## Feedback Q1 — Which tools, APIs and SDKs did you use and for what?
- **Model Context Protocol spec 2025-11-25 (Streamable HTTP):** the server's transport, sessions and four tools.
- **Alexa+ MCP Toolkit docs and Agent Skill format:** `skill/SKILL.md`, which tells Alexa+ when to call each tool
  and how to speak results; server shaped to the toolkit's MCP version and transport.
- **Amazon Bedrock Converse API + Amazon Nova Lite:** one AI-generated question per session and coach tips on wrong
  answers.
- **AWS App Runner, Amazon ECR, AWS IAM:** hosting, image registry, least-privilege model access.
- **Web Speech API (browser):** speech in and out for the simulated Alexa+ experience.

## Feedback Q2 — What worked well?
- **MCP spec:** precise MUST/SHOULD language; POST-only servers are explicitly allowed; clear Origin-validation
  warning. Small enough to implement with the Python standard library.
- **Bedrock Converse:** model-agnostic, so switching models is one env var; Nova Lite is fast and cheap enough for a
  call per wrong answer; credits applied cleanly.
- **App Runner:** container to HTTPS URL in minutes, custom domain worked, no load balancer to manage.
- **IAM:** a single instance role scoped to one model kept keys out of the image entirely.

## Feedback Q3 — What needs work?
- **Alexa+ MCP Toolkit:** US-only; the add-ons console shows "Coming Soon" to an India account, so we could not test on
  real Alexa+. No guidance for LLM-backed tools under the 500 ms budget; OAuth 2.1 + PKCE is mandatory even for public
  tools with no user data.
- **Bedrock:** in ap-south-1 the callable id is the `apac.` inference profile, not the base model id; an "ACTIVE"
  profile doesn't show whether your account can invoke it until the first call.
- **MCP spec:** the differences across 2025-03-26 / 2025-06-18 / 2025-11-25 are easy to misread; a "minimal
  compliant server" checklist would help.
- **Hackathon pages:** two different AWS-credit form URLs (Rules vs Resources).

## Feedback Q4 — Onboarding (zero to hello world)
- **MCP:** one read of the transports page to a working `initialize` → `tools/list`; about an hour.
- **Bedrock:** first successful Converse call the same day, after finding the inference-profile id.
- **App Runner + ECR:** first deploy in under an hour; the access-role vs instance-role split took one re-read.
- **Alexa+ MCP Toolkit:** blocked at the console ("Coming Soon"), so no hello world on real Alexa+.

## Feedback Q5 — Would you build with these again?
Yes. Bedrock + App Runner made a least-privilege, always-on AI service cheap and quick to ship, and MCP is simple
enough to implement directly. For Alexa+ specifically: yes, as soon as the toolkit opens to Indian developers —
Alexa+ is live in India and voice coaching in Hindi/Hinglish is the next step for this project.

## Declarations ⚠ (user ticks these personally)
- Age of majority · eligible jurisdiction · not an employee/agent of the Promotion Entities.

## AI tools used
Claude Code (Anthropic) for coding, tests, deployment scripts and docs; Amazon Bedrock with Amazon Nova Lite inside
the product; ElevenLabs for the demo video's voices and background music.

## Learning
- **Level of learning:** Significant
- **AI value for your career:** Yes
