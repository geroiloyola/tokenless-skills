---
name: spec-brainstorm
description: "Turns a vague request into a short spec with acceptance criteria, asking questions first. Use when a request is ambiguous or before write-plan on a new feature. Not for approved specs or trivial one-line fixes."
license: MIT
metadata:
  version: "0.4.0"
---

# spec-brainstorm

## Rules
1. Max 4 questions per round via ask_user_question, 2–4 options each, one marked "(recommended)". Host without that tool: list the questions as numbered options in the reply and wait for the user's picks.
2. "Whatever you decide" → decide, and record the decision plus the reason in the spec.
3. Trivial request (typo, copy change, obvious one-line bug) → say so and propose skipping to the fix.
4. Requirements you had to assume are labeled "assumed", never presented as confirmed.
5. **Every acceptance criterion must start with "The system shall..." or "When [X], then [Y]". Reject criteria that are opinions or non-observable.**

## Questions that matter (pick 3–4)
- Scope: what is explicitly out of this iteration?
- Flow: who uses it and the happy path in 3 steps?
- Data: source, missing data, corrupt data?
- Constraints: fixed stack, offline, permissions, i18n?
- Success: which command or action proves it works?
- Reversibility: is this a one-way door (migration, public API)? If yes, require more validation.

## Output
Save to `specs/<slug>.md` (respect the repo's docs folder):
```markdown
# <Feature>
## Context — why this exists, 2 lines
## Scope — includes / excludes
## Behavior — numbered flow + edge cases (empty, error, limit, permission, concurrency)
## Contract — inputs, outputs, errors, UI states, real table/endpoint names
## Decision — chosen option + rejected alternative and why
## Acceptance criteria
- [ ] The system shall <observable action> when <condition>
- [ ] When <input>, then <output>
## Risks — max 3, each with a mitigation
## Open — unanswered questions; empty means the spec is ready
```

## Close
Rewrite any acceptance criterion that is an opinion into an observable check. Show the spec and ask: "Approve and continue to write-plan?" Wait for an explicit yes.
