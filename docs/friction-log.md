# Friction log — SkillUp Coach (Amazon Developer Hackathon 2026, Alexa+ track)

Each entry: task attempted, steps taken, expected vs actual result, severity, workaround, suggestion.
Entrant based in India; dates are 2026.

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
6. **Call AgentCore from the AWS CLI.** Steps: `aws bedrock-agentcore-control list-memories` with AWS CLI v2.17
   (13 Oct). Expected: the command to exist. Actual: "Invalid choice"; the CLI version predates AgentCore, while
   boto3 1.43 worked. **Severity: low.** Workaround: boto3 scripts. Suggestion: state the minimum AWS CLI version in
   the AgentCore getting-started guide.
7. **Deploy a Strands agent to AgentCore Runtime from an x86 laptop.** Steps: followed "Direct code deployment for
   Python"; packaged arm64 wheels with `uv pip install --python-platform aarch64-manylinux2014`; zipped, uploaded to
   S3, `create_agent_runtime` (13 Oct). Expected vs actual: worked first time; the only surprises were that the docs'
   boto3 sample is hard-coded to us-west-2 role and bucket names, and that `runtimeSessionId` must be at least 33
   characters (a short id fails at invoke time). **Severity: low.** Suggestion: parameterise region in the sample and
   mention the session-id length next to `invoke_agent_runtime`.
8. **See AgentCore traces.** Steps: added `aws-opentelemetry-distro` and the `opentelemetry-instrument` entry point,
   invoked the agent, opened CloudWatch (13 Oct). Expected: spans. Actual: none until CloudWatch Transaction Search
   was enabled account-wide (resource policy + `update-trace-segment-destination`), which then sat in PENDING for
   several minutes; earlier invocations were never traced. **Severity: medium.** Workaround: enable it first.
   Suggestion: have `create_agent_runtime` (or the console) warn when Transaction Search is off, or offer to enable it.
9. **Get consistent structured grades from a small model.** Steps: Strands agent on Nova Lite with
   `structured_output_model` returning a verdict plus covered/missing points (13 Oct). Expected: verdict consistent
   with the points. Actual: occasional "partial" for complete answers, and verdicts that contradicted the model's own
   point list; also, changing `agent.system_prompt` after constructing the Agent had no effect on the next call.
   **Severity: medium.** Workaround: judge each key point with quoted evidence and compute the verdict in code; build
   the system prompt before constructing the Agent. Suggestion: a Strands docs example of "per-criterion structured
   grading", and a note on whether `system_prompt` is mutable.
