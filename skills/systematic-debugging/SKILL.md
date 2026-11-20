---
name: systematic-debugging
description: "Finds root causes with falsifiable hypotheses instead of random edits. Use for flaky bugs, unexplained failures, or after two failed fix attempts. Not for the expected red test of a TDD cycle or for requested spikes."
license: MIT
metadata:
  version: "0.4.0"
---

# systematic-debugging

Reproduce → isolate → hypothesize → instrument → fix cause → verify.

## Steps
1. Reproduce with the exact command, input, runtime and flags. Intermittent: run N times and record the failure rate. No reliable repro: stop and build one, including a failing test.
2. Read the trace bottom-up (cause first) and find the first frame that is your code, not the framework's.
3. Isolate by bisection: disable half the flow, keep the half where it fails. `git bisect` if it regressed between commits. Shrink config, data and steps to the minimum that still fails.
   **For race conditions**: use the real detector of the runtime — `go test -race`, ThreadSanitizer (`-fsanitize=thread`) for C/C++, `jcstress` for the JVM; in JS, force interleaving by injecting `await new Promise(setImmediate)` between operations. Do not rely on repeated runs.
4. Write one hypothesis in this shape before touching code:
   `H: fails because X. Prediction: <probe> will show Y. Test: <command or log>.`
   One hypothesis at a time. Prediction false → hypothesis dead, next one. No fix without a hypothesis.
5. Fix the root cause with the smallest change. Add a regression test and prove it fails without the fix (revert in place). Grep for sibling occurrences of the same bug and cover null, empty, limit and concurrency variants.
6. Run the full suite plus the affected E2E flow.

## Stop signs
- 3+ attempts and the error changes shape but never disappears.
- You start swallowing exceptions or silencing warnings.
- 3+ files touched with no confirmed hypothesis.
→ Stop, write 5 lines of what you learned, return to step 1 or 3.

## Output
Cause in one sentence · evidence (hypothesis + result) · fix diff · regression test · lesson: what would have caught this earlier (test, type, validation).
