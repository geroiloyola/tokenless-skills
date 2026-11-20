---
name: eval-harness
description: "Measures whether changes to skills, AGENTS.md, hooks or configs improved the agent by rerunning fixed repo eval tasks. Use after editing any skill or config, or when output regresses. Not for one-off changes with no eval baseline."
license: MIT
metadata:
  version: "0.1.0"
---

# eval-harness

A change without a rerun is an opinion. Five fixed tasks prove it.

## Setup (once per repo)
1. Pick 5 real tasks: 1 small feature, 1 bug, 1 refactor, 1 UI change, 1 migration or contract change.
2. Save each under `prompts/eval/` as `0N-<slug>.md` with the 5-block anatomy
   (objective, context, constraints, done-when, output), and its pass criterion.
   Full templates: `evals/tasks/README.md` in the tokenless-skills repo.
3. Record the baseline row for each task: iterations, tokens, artifacts produced.

## Run
1. Run each task in one fresh headless session of your agent (for example `vibe --prompt`, `claude -p`, `codex exec`, `opencode run`, `gemini -p`).
2. Record per task: pass/fail of the stated criterion, iterations, tokens, artifacts.
3. Never modify an eval task to make a run pass. Broken setup: fix the setup, not the criterion.

## Compare and decide
| task | baseline iters | new iters | verdict |
Pass = criterion met with equal or fewer iterations. A regression (new fail, or +
1 iteration) = reject the change and revert it; the change ships only if no task
regressed. Pre-existing fails in the baseline are Skip rows, not verdicts.

## Output
`task | criterion | pass | iterations | tokens | verdict` + one line: KEEP / REVERT / INVESTIGATE.

## Escape
Two consecutive reruns that flip verdicts without an intervening change → the
eval tasks are unstable; rewrite them with the user, never alone.
