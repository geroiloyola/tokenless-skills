---
name: implement-tdd
description: "Writes a failing test first, then minimal code, then refactors. Use when implementing a feature or fixing a bug, or when the user says implement, build it, or make it work. Not for unreproducible bugs or pure documentation changes."
license: MIT
metadata:
  version: "0.4.0"
---

# implement-tdd

Per unit of work: RED → GREEN → REFACTOR → COMMIT.

## Rules
1. No production code before a failing test proves it is needed. Exception: a spike the user explicitly requested; delete it or redo it with TDD.
2. Bug fixes: reproduce with a failing regression test first. A bug without a regression test is not fixed.
3. "Minimal" = the simplest code that makes the test pass. If the test needs 3 methods, write 3, not 5 "just in case". If it needs no abstraction, add none.
4. One change, one commit. Never mix a refactor with a feature.
5. Never delete, skip, or weaken a test to get green. If a test looks wrong, say why and ask.
6. Do not touch files outside the plan. Report every deviation at the end.
7. Gate order (typecheck, lint, tests, build) lives in verify-done; do not redefine it. Per commit: run affected checks with AGENTS.md commands. Failures caused by your change: fix. Pre-existing failures: report, do not fix as a side effect.
8. An "attempt" = one code edit plus one test run. After 2 failed attempts on the same error, stop and run the systematic-debugging skill. Do not keep guessing.

## Test level by layer
| Layer | Minimum test |
|---|---|
| Function / logic | happy path + 2 edge cases |
| API endpoint | status, body, error path, validation |
| UI component | render + main interaction; snapshot only for stable layout, never for dynamic data |
| Data migration | up + down + existing rows |
| External service | contract test using fixtures copied from the real API |

## Steps
1. Read the task, the affected files, and AGENTS.md. **Language-specific test commands**: see `references/tests.md`.
2. Write the smallest test that captures "done".
3. Run only that test. Paste the real failure output; never claim a failure you did not see.
4. Implement the minimum. Run the test. Iterate to green.
5. Run the full suite of the package that contains the files you changed. In a monorepo use the workspace command from AGENTS.md (pnpm -F <pkg>, yarn workspace <pkg>, cargo test -p, pytest <path>).
6. Commit with the repo's convention; the body states why.
7. Update the todo list, then start the next task.

## Closing report
- Done: task ids + commit hashes
- Tests: new / modified, full suite result
- Deviations from the plan and the reason
- Next: next task; after the last task run fresh-review, then verify-done
