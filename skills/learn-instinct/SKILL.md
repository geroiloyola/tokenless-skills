---
name: learn-instinct
description: "Captures a non-obvious pattern that worked into a confidence-scored instinct and prunes failed ones. Use after a trick solved a hard problem or when the user says remember that. Not for one-time workarounds, secrets, or duplicated docs."
license: MIT
metadata:
  version: "0.4.0"
---

# learn-instinct

One instinct = one trigger + one action + confidence.

## Steps
1. Write the instinct in this format and append it to `~/.agents/memory/lessons.md` (the kit's single memory file, shared with remember-correction):
   `- YYYY-MM-DD | type:instinct | scope:global|repo:<name> | rule: <imperative, ≤15 words> | conf: 0.5 | evidence: <where it worked> | expires: <date>`
   `expires:` only for instincts tied to a tool version or a workaround (set 30-90 days out); omit for stable patterns.
2. Same pattern worked again → add 0.1 to `conf:` (cap 0.9). It failed → subtract 0.2.
3. Delete anything at or below 0.2 or expired. Do not keep dead weight.
4. At 0.7+ with evidence from 2+ sessions, propose promotion:
   re-tag the same line as `type:lesson` (drop `conf:`), or move it to the repo AGENTS.md if it is project-specific. Ask before promoting.
5. Keep the file under 40 lines. Prune lowest confidence first.
   **On session start, load only instincts with matching scope (global or current repo).**

## Output
`instinct | confidence <new> | action (appended/bumped/pruned) | file`

## Quality bar
- Reject instincts that restate the framework docs, obvious language rules, or a one-time workaround.
- Reject instincts that are not falsifiable: if you cannot say when it should NOT apply, rewrite it.
- Never record secrets, customer data, or anything that changes per environment.

## If ECC is installed
Use ECC's continuous-learning-v2 instead (`/instinct-status`, `/evolve`, `/prune`), which stores instincts with project scope and confidence. Keep this file only as a fallback when ECC is not available; never maintain both in parallel.
