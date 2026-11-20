---
name: verify-done
description: "Runs build, typecheck, lint and tests, then reviews the full diff against the spec before declaring work finished. Run after fresh-review, before a final commit, push or pull request. Not for sanity checks after every edit."
license: MIT
metadata:
  version: "0.4.0"
---

# verify-done

"Done" means verified, not believed.

## Gates (this list is the kit's single source of truth; implement-tdd and fresh-review defer to it. Run in order, keep the output)
0. **Performance (optional)**: only if the repo ships a real benchmark (script in package.json, `cargo bench`, pytest-benchmark) or records one in AGENTS.md: run it and compare to the last recorded baseline. Regression ≥5% = MAJOR. No baseline: skip and name it as skipped — never invent numbers.
1. typecheck (cheapest failures first)
2. lint
3. unit tests
4. tests of the affected package
5. build

Any failure: fix and restart from the gate that failed. Pre-existing failure (confirm with `git stash` if unsure): report it, do not fix it here.

## Diff review
Read `git diff --stat`, then the entire `git diff`, file by file.
- [ ] Changes outside the spec's scope? Revert them.
- [ ] Debug leftovers: console.log, print, dbg!, new TODO, sleeps, commented code?
- [ ] Secrets, tokens or .env content in the diff?
- [ ] Lockfiles or generated files changed by accident?
- [ ] Untracked files left behind (git status)? Artifacts from this run (screenshots, diffs, JSON) are outside the repo or deleted.
- [ ] Names and style match the repo's canonical patterns?
- [ ] Error paths handled: null, empty, timeout, permission denied?

## Spec check
| Acceptance criterion | How verified | Pass |
|---|---|---|
| ... | test X / manual step Y | ✅/❌ |

An unchecked criterion is not done. "Should work" is not a verification.

## Smoke (if UI or a user flow changed)
Start the project, walk the happy path plus one error case. Capture output or screenshot as evidence.

## Final report
- Status: READY / READY WITH PENDING ITEMS / NOT READY
- Gates: results per gate, test count
- Criteria: X/Y verified
- Pending: known risks
- Diff: N files, +A/−B, all within scope

Anything not green means the status is not READY.
