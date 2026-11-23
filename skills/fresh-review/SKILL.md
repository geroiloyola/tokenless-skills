---
name: fresh-review
description: "Blocking diff review by a reviewer with no session bias, run once after the plan's last implement-tdd task and before verify-done, or when the user asks for a second opinion. Not for trivial single-file doc changes."
license: MIT
metadata:
  version: "0.4.0"
---

# fresh-review

## Steps
1. Stage intended new files; resolve partially staged files. From the worktree run `bash <skill-dir>/scripts/review-snapshot.sh freeze <base-ref> <snapshot-dir>` with a fresh `mktemp -d` outside the worktree. This freezes committed, staged and unstaged tracked changes from one merge base.
2. Give the read-only reviewer the resulting `review.diff`, spec, AGENTS.md and `references/reviewer.md` brief. The saved diff is authoritative; verify claims against code, not comments or commit messages.
3. Read the verdict. `CHANGES REQUIRED` or any BLOCKER → fix, then run the whole gate again from step 1. A reviewer never downgrades its own finding without new evidence.
4. On approval, pass the snapshot directory and helper path to verify-done. Keep the snapshot until that gate finishes. Do not commit or push with unresolved findings.

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
