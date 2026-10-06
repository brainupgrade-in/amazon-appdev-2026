# Open Source mini-challenge — record (copy into Devpost submission form)

- **Contribution URL:** https://github.com/brainupgrade-in/minimal-mcp-http
- **Primary project repo URL:** https://github.com/brainupgrade-in/amazon-appdev-2026
- **GitHub username:** brainupgrade-in (individual entrant: rajeshgheware)
- **What:** new standalone MIT-licensed template — a one-file, stdlib-only MCP server
  over Streamable HTTP (spec 2025-11-25) with `echo`/`add` example tools, 5 unittests,
  and a "add your own tool" recipe. Extracted and generalized from the SkillUp Coach
  server built during the hackathon window (Oct 2026).
- **How it works:** single `POST /mcp` endpoint (`initialize` → `MCP-Session-Id` →
  `tools/list` → `tools/call`); `GET` → 405; Origin + protocol-version enforcement.
  Run: `python3 minimal_mcp_server.py --port 8000`. No dependencies.
- **Why it matters:** solo/small-team Alexa+ builders get a zero-install, spec-shaped
  starting point that passes the track's runtime-technology requirement pattern
  (real import + entry point + served endpoint, not a README mention).
