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
