# SKILL_MASTER.md — the standard for every skill in this kit

> Human note: hand this file plus your request to the agent. It will produce a
> skill in the same shape, size and doctrine as the 14 shipped ones. Do not edit
> it per-skill; extend it only when the doctrine changes.

## 0. Hand-off prompt (copy, fill, paste)

```
Read skills/SKILL_MASTER.md (in the kit repo) and follow it exactly.
Create a skill named <kebab-name> for <one workflow, one sentence>.
It must produce: <observable outputs>.
Triggers I would say: "<phrase 1>", "<phrase 2>", "<phrase 3>".
Stack/context: <repo tooling, framework>.
Then validate it with scripts/check_skills.py and show me: line count,
estimated tokens, description length, and any trigger overlap with existing skills.
```

## 1. Hard rules (violating any of these rejects the skill)

1. **English only.** Body, description and comments. Spanish lives in `AGENTS.md`.
2. **One skill = one workflow.** Two purposes means two skills.
3. **Body ≤ 50 non-empty lines and ≤ 1000 tokens** (`chars / 4`, frontmatter included).
   Over budget means the content belongs in `references/` or does not belong at all.
4. **Numbered, imperative steps.** "Do X", never "you should consider X".
5. **No prose about why a rule exists.** State the rule. Delete the rationale.
6. **No `Note:`, `Important:`, `Remember:`, no intros, no conclusions, no "you are a helpful...".**
7. **No examples** unless a step is genuinely ambiguous. One 3-line example max.
8. **No `allowed-tools`** — most hosts read it but do not enforce it. Permissions live in the host's own config (for Vibe: `agents/*.toml`).
9. **Define every vague word operationally**: "minimal", "attempt", "done", "large".
10. **Every skill ends with an explicit output format** the agent must fill.
11. **Every skill that can loop needs an escape**: N failures → name the next skill.
12. **Claims need evidence**: if the skill asserts a state (tests pass, UI works, review clean),
    it must require pasted output, a file, or a screenshot in the same session.

## 2. Frontmatter (exact, nothing else)

```yaml
---
name: kebab-case-must-equal-folder-name
description: "<WHAT it does, third person>. Use when <situation>, <trigger 2>, <trigger 3>."
license: MIT
metadata:
  version: "0.1.0"
---
```

- `description` ≤ **250 chars** (the spec allows 1024; we cap for precision). It is the
  **index**: the only thing loaded at startup (~100 tokens per skill) and the only thing
  the model uses to decide whether to activate. Write the phrases a human would actually type.
- `name` = folder name, lowercase, hyphens, no underscores.
- `version` goes under `metadata`; a top-level `version:` is not in the Agent Skills spec.
- Do not add `compatibility`, `allowed-tools`, or custom keys.

## 3. Canonical body skeleton

```markdown
# <name>

<one-line purpose, ≤ 12 words>

## Rules
1. <hard constraint, testable>
2. ...

## Steps
1. <imperative action> → <observable result>
2. ...

## <Optional data block>
<A table, a checklist, or a fixed list — only if the step needs reference data.
Max 8 rows. Anything bigger goes to references/.>

## Output
`field | field | field` or a 5-line template the agent fills verbatim.

## Escape
<Condition> → <next skill or human checkpoint>. Never loop more than N times.
```

Optional sections, chosen only when they earn their lines: `## Questions` (max 4),
`## Checks` (checkboxes), `## Test level` (table), `## Do not record`, `## If ECC is installed`.

## 4. Doctrine behind the rules (the part that makes it "senior")

| Principle | How it shows up in a skill |
|---|---|
| Anti-hallucination | "Paste the real failure output; never claim a failure you did not see" |
| Operational definitions | `"attempt" = one code edit plus one test run` |
| Escape hatches | `2 failed attempts on the same error → the systematic-debugging skill` |
| Scope control | `pre-existing failures: report, do not fix as a side effect` |
| Evidence over assertion | `no UI claim without a screenshot or DOM assertion from this session` |
| Human checkpoints | `migrations, public API, dependency changes → ask first` |
| Memory hygiene | `lessons.md ≤ 80 lines, instincts.md ≤ 40, prune before appending` |
| Fresh context | `the author does not grade their own work; reviewer is read-only` |
| Cost discipline | `always-loaded ≈ 100 tokens; green run = empty stdout` |

If a draft rule does not change what the agent does in a concrete situation, delete it.
Test: "would a different agent, with zero context, act differently because of this line?"

## 5. Skill types and the template to start from

| Type | When | Template | Kit example |
|---|---|---|---|
| **A. Workflow** | A repeatable process with phases | Rules → Steps → Output | `implement-tdd`, `write-plan` |
| **B. Gate** | Blocks progress until a condition is met | Gates (ordered list) → Checks → Verdict | `fresh-review`, `verify-done` |
| **C. Memory** | Persists knowledge between sessions | When to record → Format → Caps → Housekeeping | `remember-correction`, `learn-instinct` |
| **D. Digest** | Large reference data, read on demand | No frontmatter, ≤500 lines, sections + checklist | `design-review/references/uiux.md` |
| **E. Tool-backed** | Needs a script or an MCP server | Steps → Script contract → Fallback when the tool is absent | `webapp-testing` + `scripts/webcheck.mjs` |

Type E rule: the skill must work **without** the tool (manual fallback stated in one line),
and the script must be silent on success, exit non-zero on defects, and never require a
network service the repo does not already have.

## 6. Worked example — correct density (38 lines total)

```markdown
---
name: api-contract
description: "Detects breaking changes in HTTP or DB contracts and writes the migration note. Use when a route, payload, schema or index changes, or before publishing an API version."
license: MIT
metadata:
  version: "0.1.0"
---

# api-contract

A contract change is a promise change. Prove compatibility or declare the break.

## Rules
1. Breaking = removed field, narrowed type, new required input, changed status code,
   changed auth rule, renamed table/column, dropped index used in a hot query.
2. Additive is not automatically safe: check consumers inside the repo before calling it safe.
3. Every break gets a migration path, a version bump, or an explicit "accepted, no consumers".

## Steps
1. `git diff` the changed routes, DTOs, schemas and queries. List every touched contract.
2. Classify each: additive / breaking / internal-only.
3. Grep the repo for consumers of each changed contract (client, tests, mocks, docs).
4. For breaking changes, write the migration note in `docs/api/<slug>.md`.
5. Update the OpenAPI/schema file if the repo keeps one.

## Output
`contract | change | class | consumers found | action (migration/version/accepted)`
```

Why it passes: description carries 3 trigger phrases; "breaking" is defined; no theory;
one output line; no example needed; 38 lines.

## 7. Validation protocol (run before delivering)

1. `python3 scripts/check_skills.py` (from the kit repo root) → lines, tokens, description length, frontmatter fields.
2. **Trigger test**: read the description alone. Would it fire on the intended prompt?
   Would it fire on a neighbouring one by mistake? Adjust the trigger words, not the body.
3. **Overlap test**: compare against the existing kit skills (run check_skills.py for the count). If two skills could fire on the same
   prompt, add a discriminator to one description ("use after X", "only when Y").
4. **Zero-context test**: could an agent with no session history execute the steps? Any step
   requiring a guess (file name, command, schema) must be resolved in the skill or by a question.
5. **Budget test**: if body > 50 lines, move data to `references/<x>.md` and leave exactly
   one pointer line: `Read references/x.md before step 3.`
6. **Silence test** for tool-backed skills: green path prints nothing; failure path exits non-zero.

## 8. Anti-patterns that reject a skill

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Essay skill | Paragraphs explaining methodology | Numbered rules only |
| Vague verb | "handle", "ensure", "consider", "appropriately" | Replace with an observable action |
| Undefined threshold | "large diff", "too many", "slow" | Give the number |
| Skill that repeats AGENTS.md | Commands, stack, conventions | Move to AGENTS.md, keep the workflow here |
| Skill that owns two phases | Plan + implement inside one file | Split |
| Trigger collision | "use when coding" | Name the specific situation |
| Reference dump | 300 lines of tables inline | `references/` + one pointer |
| Silent failure | Tool errors swallowed | Exit codes + explicit fallback |
| Ceremony | Roles, meetings, RACI, personas | Delete; keep gates that change behavior |

## 9. Budget reference (this kit)

| Item | Value |
|---|---|
| Always loaded | ~100 tokens per skill (name + description) |
| Body target | 350–650 tokens; hard cap 1000 |
| Digest | ≤ 500 lines, no frontmatter, read only on demand |
| Kit total | 14 skills ≈ 0.7k always-loaded (descriptions), ≈ 7.3k worst case if every skill fires (trust `check_skills.py` over this row) |

## 10. Where to install

| Host | User scope | Project scope |
|---|---|---|
| Vibe | `~/.vibe/skills/<name>/` | `.vibe/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| Codex | `~/.codex/skills/<name>/` | `.codex/skills/<name>/` |
| OpenCode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` |
| Gemini CLI | `~/.gemini/skills/<name>/` | `.gemini/skills/<name>/` |
| Antigravity | `~/.gemini/config/skills/<name>/` | `.agents/skills/<name>/` |
| Any agent (dotfiles) | `~/.agents/skills/<name>/` | `.agents/skills/<name>/` |

Install to all detected hosts with `./install.sh` (see the kit README). Verify with your host's skill listing (`/skills` in Vibe, the `/` picker in Claude Code, `@skill-id` in OpenCode, `$skill-name` in Codex).