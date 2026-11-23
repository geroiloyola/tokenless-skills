---
name: verify-done
description: "Runs build, typecheck, lint and tests, then reviews the full diff against the spec before declaring work finished. Run after fresh-review, before a final commit, push or pull request. Not for sanity checks after every edit."
license: MIT
metadata:
  version: "0.4.0"
---

# verify-done

## Gates (implement-tdd and fresh-review defer here; run in order and keep output)
For final verification, require the approved fresh-review snapshot. Run `bash <fresh-review-helper> check <snapshot-dir>` before gates and again after all checks and smoke tests. The helper is `scripts/review-snapshot.sh` under fresh-review. Missing snapshot or failed check → rerun fresh-review; never substitute another diff.

0. **Performance (optional)**: run a repo benchmark if one exists, compare to a recorded baseline. Regression ≥5% = MAJOR. No baseline: report skipped.
1. typecheck (cheapest failures first)
2. lint
3. unit tests
4. tests of the affected package
5. build

Any failure: fix and restart from the gate that failed. Edits invalidate approval. Confirm unrelated failures in a separate checkout; report, don't fix them here.

## Diff review
Read the approved `review.diff` file by file; derive the stat from it (`git apply --stat <review.diff>`). For any authorized commit, stage exactly the reviewed changes.
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

Anything not green means the status is not READY. Remove the temporary snapshot after the verdict.
