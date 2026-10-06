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
