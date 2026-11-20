---
name: subagent-execute
description: "Executes plan tasks one at a time in isolated worktrees so the main session keeps a clean context. Use for multi-task plans, long autonomous runs, or when the user asks to run the whole plan, parallelize tasks, or work in a worktree."
license: MIT
metadata:
  version: "0.4.0"
---

# subagent-execute

One task per worktree. The main session plans and reviews, never edits.

## Steps
1. Pick the next pending task from `specs/<slug>-plan.md`. Tasks with `touches:` labels that share a file never run in parallel; if the plan omits `touches:`, derive it from the task's Files list.
2. Create an isolated tree:
   `git worktree add ../wt-<task-id> -b task/<slug>-<task-id>`
   If git worktree is unavailable (Web sandbox): run tasks serially in the main
   worktree, one task = one commit on one branch; isolation comes from serial
   execution, not the filesystem. No parallelism in this mode.
3. Spawn a subagent with this prompt:
   ```
   Work only in <worktree path>. Read AGENTS.md there.
   Task: <full task block from the plan>.
   Follow the implement-tdd skill. Run the single-file test, then the package suite.
   Commit with the repo convention.
   Reply only with: status, commit hash, tests run, files touched, deviations.
   If unsure about a requirement, stop and reply BLOCKED with the question.
   Do not touch files outside the task.
   ```
4. While it runs, keep working on independent tasks only if they share no `touches:` files.
5. On reply: run verify-done-style gates in that worktree, then merge `task/<slug>-<task-id>` into the base branch with `--no-ff`, one branch at a time; if the base moved, rebase the task branch first.
6. Close out: `git worktree remove ../wt-<task-id>`. The branch, and any push of the base branch, require the user's explicit approval — never push on your own.
7. If BLOCKED: answer the question or escalate to the human. Never let the subagent guess.

## Rules
- The main agent does not implement in this mode; if it starts editing, the mode is broken.
- A subagent gets one task, no backlog, and never sees the whole plan beyond its block.
- Every merge requires green gates in the worktree. A red task does not merge.
- Context budget: the subagent's transcript never enters the main session; only its 5-line report does.
- Parallel only when `touches:` sets are disjoint. When in doubt, serialize.

## Output
`task | branch | commit | gates | merged? | deviations` — one row per task, plus the final branch state.
