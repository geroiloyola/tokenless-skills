---
name: remember-correction
description: "Persists a user correction as a one-line rule so the same mistake is not repeated. Use when the user says no, don't do that, I already told you, or otherwise corrects your approach."
license: MIT
metadata:
  version: "0.4.0"
---

# remember-correction

A correction is a bug report against your behavior. Fix it permanently.

## Steps
1. Stop the current approach. Restate the correction in one line and confirm it is understood.
2. Grep `~/.agents/memory/lessons.md` and the repo AGENTS.md. If a rule already covers it, tighten that line instead of adding a duplicate.
3. Append one line to `~/.agents/memory/lessons.md` (create the file if missing):
   `- YYYY-MM-DD | priority:HIGH|MEDIUM|LOW | scope: global | rule: <imperative, ≤15 words> | why: <what went wrong>`
   Use `scope: repo:<name>` for rules that only apply to this project. `expires: <date>`
   goes last, only for rules tied to a temporary workaround or a dependency version.
4. Re-read the line you wrote and check it is actionable by a different agent with no context.
5. Confirm to the user with the exact line, no explanation.

## Output
`appended | <the exact line written to lessons.md>` — quote it verbatim to the user.

## Do not record
- One-off task preferences, secrets, or anything already in AGENTS.md.
- Vague lessons ("be more careful"). If you cannot state a concrete action, ask one question and record the answer.

## Housekeeping
Keep the file under 80 lines: merge duplicates, delete rules the repo has since encoded, keep the newest phrasing. The file is loaded at session start via AGENTS.md, so every line costs tokens in every session.

## If ECC is installed
ECC's continuous-learning handles this. Still write the line here: it survives plugin updates and is readable at a glance.
