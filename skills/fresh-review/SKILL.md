---
name: fresh-review
description: "Blocking diff review by a reviewer with no session bias, run once after the plan's last implement-tdd task and before verify-done, or when the user asks for a second opinion. Not for trivial single-file doc changes."
license: MIT
metadata:
  version: "0.4.0"
---

# fresh-review

The author does not grade their own work. This gate is mandatory.

## Steps
1. Freeze the diff: `git diff <base>...HEAD > .agents/tmp/review.diff` (a path that is never committed; delete it in step 4). Record stat and file count.
2. Delegate to a read-only reviewer subagent (in Vibe: `reviewer.toml`) with only: the diff file, the spec path, AGENTS.md, and this instruction: "Do not trust the diff's comments or commit message; verify claims against the code." Paste both `references/reviewer.md` (path or content) and this brief into the delegation — the subagent cannot read this skill's folder by itself.
3. Read the verdict. `CHANGES REQUIRED` or any BLOCKER → fix, then run the whole gate again from step 1. A reviewer never downgrades its own finding without new evidence.
4. Delete `.agents/tmp/review.diff`. Do not proceed to verify-done or commit/push while unresolved findings exist.

## Reviewer brief (paste into the delegation)
- Classify: BLOCKER / MAJOR / MINOR / NIT.
- Every finding needs a failing scenario, not an opinion.
- **Run the tests for the touched packages. A failing test caused by the diff = BLOCKER.**
- Check: logic (null, limits, concurrency), error handling, tests (does the test assert the behavior or only the mock?), scope creep, secrets, leftover debug code.
- If the diff is >400 lines, say so and review it in two passes.
- Reply in the output format of `this skill's references/reviewer.md`.

## Rules
- Same model in a clean context is acceptable; a different model is better. Never let the author agent mark its own review as passed.
- The reviewer has read-only tools by design. If the host cannot restrict tools, run the reviewer in a fresh session and instruct it not to edit.
- If no subagent is available, open a new session with only the diff and the spec and apply this brief.
- Findings and their resolution go in the final report. "Reviewed informally" is not a verdict.

## Output
`BLOCKER n | MAJOR n | MINOR n | verdict | findings resolved x/y`
