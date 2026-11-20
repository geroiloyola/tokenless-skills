---
name: write-plan
description: "Splits an approved spec into small verifiable tasks with exact files, order and human checkpoints. Use after spec-brainstorm, or when the user asks for a plan before implementing a multi-file feature."
license: MIT
metadata:
  version: "0.4.0"
---

# write-plan

A plan another agent could execute without you.

## Steps
1. Grep and read the files that already do something similar. Name existing files to modify and new files to create; if a name is unknown, write the pattern and say so.
2. Choose the most boring implementation that satisfies the spec. YAGNI: no abstraction for future needs.
3. Slice vertically: each task leaves the repo green (build + tests). A task that breaks the build and does not fix it is mis-cut.
4. Size: 1 task = 1 commit = 10–30 agent minutes = ≤3 files. More than 5 files means split.
5. Mark human checkpoints: migrations, public API changes, dependency changes, code deletion.

## Output
Save to `specs/<slug>-plan.md`:
```markdown
# Plan: <feature>
## Strategy — 3 lines
## Tasks
### T1 — <imperative title>
- Files: `path` (modify) / `path` (create)
- Touches: `path` `path` — exact files this task may edit; used by subagent-execute
  for parallelism (only disjoint sets run in parallel)
- Est: <minutes> — time estimate based on similar tasks or user input
- Change: 1–3 lines
- Test: which test covers it + single-file command
- Done when: observable check
- Human checkpoint: yes/no
## Plan risks — where it is most likely to break and how to detect it
## Out of scope — copied from the spec
```

## Self-check before delivering
- [ ] Every task has an observable "done".
- [ ] Nothing forces the implementer to guess: names, schemas and config are resolved now.
- [ ] No shorter order exists; if one does, propose it.
- [ ] Commands match AGENTS.md.
- [ ] No file outside the spec's scope is touched.

## Close
Show the plan and ask: "Execute T1→Tn with the implement-tdd skill, or adjust tasks?" Do not implement here.
