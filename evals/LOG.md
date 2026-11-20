# evals/LOG.md — every benchmark iteration, before and after

Regla: no entry without a recorded command and raw result. Unmeasured = "hipótesis". Fase 3 addendum: every skill line must be defensible with an eval result; ablation deletes what doesn't move success.

## Round 0 — adapter verification session (BLOCKED, no model spend)

- Date: 2026-11-20. Approved budget: one cheap session, verification only.
- Attempted: install a headless host CLI and run a single probe session through
  `scripts/bench.py` to verify that real host `usage` (input+output+cache) parses.
- Executed commands and exact results:
  1. `npm install -g @anthropic-ai/claude-code` → exit 0 (claude 2.1.329).
  2. `claude --version` → `2.1.329 (Claude Code)`.
  3. `claude -p "Return exactly: OK"` → **`Not logged in · Please run /login`**
     (exit 0, no API call made, nothing spent).
- Alternative hosts checked: `vibe`, `codex`, `gemini`, `opencode` binaries
  absent from PATH (`which` all empty); `vibe-acp.exe` exists but is not a
  headless one-shot CLI. No `ANTHROPIC_API_KEY` in the environment.
- Verdict round 0: **BLOCKED**. The only remaining step is interactive
  authentication (`claude login` browser/OAuth), which cannot be automated by
  the agent and requires the account owner. This is a user action, not a code gap.
- Consequence: all A/B/C/D comparisons remain **preregistered hypotheses**
  (PREREGISTRATION.md). Nothing measured, nothing claimed. Round 1 (probe
  session) costs at most one trivial API call once login exists.

## Registered ablation hypotheses (Fase 3, executes only after round 1+)

Method (from MASTER PROMPT v2, Fase 3): each round, keep the change to as
few tokens as possible while preserving success; each round where skill B fails, identify the missing instruction, add the minimum, re-run; keep the change only
if Pareto improves (success / 1k tokens). Priority order: verify-done, security-review,
systematic-debugging, implement-tdd.

| Skill | Hypothesis | Minimal change if B fails where a competitor passes |
|---|---|---|
| verify-done | traps (09-done-contract, 10-done-releasecheck) may pass despite broken state because the gates list is read but not re-run at the end | add one hard imperative line: "re-run the full gate list immediately before reporting done; a failing gate = not done" |
| remaining failure modes | unknown until round 1 | ablation only on observed failures; no speculative edits |

Planned deletion pass (only once the claim is met): line/paragraph deletion per
skill, re-run affected tasks, keep the deletion if success stays within run
noise (+/-1 task per cell at n=3 reps).
