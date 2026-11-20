---
name: webapp-testing
description: "Drives a real browser to verify UI rendering, console errors, network failures and basic accessibility. Use after building or changing UI, before claiming a page works, or when the user asks to test the frontend."
license: MIT
metadata:
  version: "0.4.0"
---

# webapp-testing

A passing unit test is not evidence that a page renders. Prove it in a browser.

## Order of preference
1. Playwright MCP tools if this session has them (Vibe exposes them as `<server>_<tool>`, e.g. `playwright_browser_navigate`). navigate → snapshot → click → screenshot.
2. `scripts/webcheck.mjs` from this skill when Playwright is in the repo or can be added. Exit 2 = Playwright absent → fall to rung 3 (manual) and say so.
3. Manual steps only as a last resort, and say explicitly that it was not automated.

## Steps
1. Read the dev command and port from AGENTS.md. Start the server in the background and poll until ready (`curl -sf http://localhost:PORT`); never use a fixed sleep.
2. Run: `node <skill-dir>/scripts/webcheck.mjs http://localhost:PORT/<route> --out .agents/artifacts`
3. Read the JSON: console errors, HTTP ≥400, **a11y violations (axe-core)**, missing accessible names, images without alt, horizontal overflow at 375px. Exit 1 means defects.
4. Open the screenshot. Check layout integrity, clipped text, placeholder content, and that empty / loading / error states exist.
5. Exercise the changed flow: fill, submit, navigate, go back. Assert on visible text, not DOM internals.
6. Fix defects in the code, never in the check.

## Rules
- Never claim a UI change works without a screenshot or a DOM assertion produced in this session.
- Test the states the spec names: empty, loading, error, long text, 375px and 1440px.
- Kill the server when done. Leave no background processes.
- Artifacts go to `.agents/artifacts/`; never commit them.

## Output
`route | states | console | network | a11y | verdict + artifact paths`
