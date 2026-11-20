---
name: repo-context
description: "Creates or updates AGENTS.md with verified commands, repo map and canonical patterns. Use in an unfamiliar repo, before a first task there, or when the agent keeps breaking project conventions."
license: MIT
metadata:
  version: "0.4.0"
---

# repo-context

Produce an AGENTS.md the agent can trust: facts verified, no prose.

## Steps
1. If AGENTS.md exists, switch to update mode (step 5). Otherwise create it.
2. Read in plan mode: 2–3 levels of the tree, package manifest, lockfiles, README, lint/test/CI config, and 3–5 representative files per layer.
   **Runtime**: check `asdf current <lang>` or `.tool-versions` first; fall back to `engines` in package.json or `.python-version`.
3. Verify every command before writing it. No verification, no line.
4. Write AGENTS.md with the template below, 60–120 lines maximum.
5. Update mode: diff each section against the current repo and report a table `section | stale | fix`. Apply only what the user approves; keep the team's wording.

## Template
```markdown
# AGENTS.md

## Project
One line: what it is, stack, pinned runtime (from .nvmrc / engines / .python-version).

## Language
Reply in the language the user speaks; keep code, comments and commit messages in English.

## Commands (verified)
- Install / Dev / Test / Test one file / Lint / Typecheck / Build

## Repo map
- `src/<layer>/` — responsibility in ≤10 words (3–8 entries)

## Canonical patterns (copy these, do not invent)
- UI component: `path/to/example.tsx`
- API endpoint: `path/to/example.py`
- Test: `path/to/example.test.ts`
- Error handling: <pattern + path>

## Hard rules
- 5–10 non-negotiables: naming, imports, state, where logic must not live.

## Do not
- Real traps only: edit lockfiles by hand, run migrations manually, touch `generated/`.
```

## Checks before delivering
- [ ] Every command exists or was executed.
- [ ] ≤120 lines; no section duplicated from the README.
- [ ] Example paths exist in the repo.
- [ ] Monorepo: root AGENTS.md holds global rules and links each package's own AGENTS.md.

## Output
The full file in one code block, plus a short list of facts you could not verify.
