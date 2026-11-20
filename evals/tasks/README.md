# eval/tasks — anatomy every eval task must follow

Referenced by the `eval-harness` skill and by `evals/` in this repo.

Each task is one Markdown file, `NN-<slug>.md`, with exactly these 5 blocks:

```markdown
# NN-<slug>
## Objective
<one sentence, no "and">
## Context
<files, fixtures, commands the agent gets; everything else is off-limits>
## Constraints
<hard limits: tools allowed, files that must not change, time/call budget>
## Done when
<the pass criterion: a command that must exit 0 / a test that must pass /
a grep that must hit. No LLM judges.>
## Output
<the exact artifact: commit, file, stdout block>
```

Rules: the pass criterion is executable (test, script exit code, grep);
fixtures are tiny; the initial repo state is committed so runs are
reproducible; never edit a task's criterion to make a run pass.
