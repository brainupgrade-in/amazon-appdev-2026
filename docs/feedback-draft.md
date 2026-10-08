# Product feedback + friction log — DRAFT (refine before submission)

## Product feedback
### MCP spec docs (modelcontextprotocol.io, 2025-11-25 transports)
- Used for: Streamable HTTP session flow (`initialize` → `MCP-Session-Id` → POST-only calls).
- Worked well: precise MUST/SHOULD language; GET→405 explicitly allowed; security warning on Origin validation.
- Needs work: versioning story across 2025-03-26 / 2025-06-18 / 2025-11-25 is easy to misread; a "minimal compliant server" checklist would help solo builders.
- Onboarding: zero → hello-world in one page read. Would reuse: yes.
### Devpost + Resources page
- Used for: track rules, credit form, starter repos.
- Worked well: per-track tool links in one place.
- Needs work: two different credit-form URLs (Rules vs Resources page); reconcile before deadline week.
- Would reuse: yes.
### Amazon Bedrock (Converse API, ap-south-1, Amazon Nova Lite)
- Used for: one AI-generated quiz question per session + spoken-style coach tip on wrong answers (`src/skillup_mcp/tools.py`).
- Worked well: Converse is model-agnostic, so swapping models is one env var (`BEDROCK_MODEL_ID`); Nova Lite answers fast and cheap enough for a per-answer call; credits applied cleanly.
- Needs work: in ap-south-1 the id to call is the `apac.` cross-region inference profile, not the base model id — only found via `aws bedrock list-inference-profiles`; an "ACTIVE" profile doesn't tell you whether your account can actually invoke it until the first call.
- Would reuse: yes.

## Friction log
1. **Task:** confirm minimal MCP server shape without an SDK.
   **Steps:** read 2025-11-25 transports page; checked GET/SSE/session-id requirements.
   **Expected vs actual:** expected mandatory SSE; actual: GET→405 allowed, POST-only is compliant.
   **Severity:** low. **Workaround:** none needed. **Suggestion:** publish a "minimal server" example.
2. **Task:** reconcile AWS credit form URL.
   **Steps:** compared Rules page vs Resources page links; they differ.
   **Expected vs actual:** expected one URL; actual: two distinct form links.
   **Severity:** medium (blocks credit request). **Workaround:** try Resources link first.
   **Suggestion:** single canonical URL on both pages.
3. **Task:** Devpost registration.
   **Steps:** created login, joined hackathon. **Expected vs actual:** as expected.
   **Severity:** info. **Suggestion:** none.
4. **Task:** first live Bedrock call from ap-south-1.
   **Steps:** checked `list-inference-profiles` → `apac.amazon.nova-lite-v1:0` ACTIVE; called Converse via boto3 through the MCP server.
   **Expected vs actual:** expected the base model id to work in-region; actual: use the `apac.` inference-profile id. Call then succeeded first try (2026-10-08).
   **Severity:** low. **Workaround:** list inference profiles first. **Suggestion:** show the exact callable id per region on the model card.
5. **Task:** connect the hosted SkillUp Coach MCP server to real Alexa+ (MCP Toolkit add-on).
   **Steps:** read MCP Toolkit overview + quickstart; signed in to developer.amazon.com (India-based account);
   opened `developer.amazon.com/alexa/console/ask/addons` (2026-10-08).
   **Expected vs actual:** expected the add-ons console + web simulator; actual: page shows only "Coming Soon".
   Docs say "The MCP Toolkit is available in the United States", while Alexa+ itself launched in India
   (Early Access, 16 Sep 2026) — so Indian users have Alexa+ but Indian developers cannot build for it.
   **Severity:** high for non-US builders in an Alexa+ track. **Workaround:** simulated Alexa+ web app (track fallback).
   **Suggestion:** open the add-on console/simulator to all developer accounts (even with US-only distribution),
   and say up front on the hackathon Resources page that the MCP Toolkit is US-only.
6. **Task:** check MCP Toolkit server requirements against an existing MCP server.
   **Observed:** quickstart requires OAuth 2.1 auth-code + PKCE (401 for unauthenticated) and <500 ms round trip.
   **Friction:** the 500 ms budget rules out a synchronous LLM call inside a tool (our Bedrock call is ~1–2 s);
   no "no-auth"/API-key option for public, non-personal tools. **Suggestion:** document an async/progressive
   pattern for LLM-backed tools and allow unauthenticated tools that touch no user data.

