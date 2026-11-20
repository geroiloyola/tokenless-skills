# Eval task template (referenced by the eval-harness skill)

Save one `.md` per task under `prompts/eval/` in your repo, named `0N-<slug>.md`.
Five blocks, nothing else. If a block hits zero words, the task is not eval-ready.

```markdown
# 0N-<slug>

## Objective
One sentence: what the agent must end with. (A repo state, not a feeling.)

## Context
2–4 lines: the relevant entry points, files or patterns the agent may assume.

## Constraints
- Files the agent may not touch
- Tool/time budget
- Anything out of scope

## Done when
- [ ] Observable check 1 (a command output, a test result, a file state)
- [ ] Observable check 2

## Output
What the final message must contain (report format, files touched, evidence links).
```

Quality bar (from the kit doctrine): every "done when" item is executable or observable by a human; the task must fail loudly; and it must accumulate baseline data (iterations, tokens, artifacts) before any kit/config change is judged against it.
