# Host compatibility matrix

Status vocabulary — do not upgrade a claim without evidence:

- **Verified** — worked in an executed test against (or from) the host itself in this repository's CI or a documented local run.
- **Partially verified** — filesystem/installer verified in isolated tests; runtime behavior documented from the host's public documentation but not executed headless here.
- **Theoretical** — folder-convention compatible per the Agent Skills 1.0 spec; runtime behavior unconfirmed.
- **Unsupported** — the host or the feature is known not to work.

Installer paths are what `install.sh` targets; activation details describe how a host finds and loads `skills/<name>/SKILL.md`.

| Host | Skills dir (user) | Skills dir (project) | Activation | Rules block seeded | Memory (lessons/instincts) read | Hooks/guard | Status |
|---|---|---|---|---|---|---|---|
| Claude Code | `~/.claude/skills` | `.claude/skills` | `/` picker, auto-match | ✅ `~/.claude/CLAUDE.md` | ✅ | ❌ (Claude uses its own hooks; guard not wired) | Partially verified (installer ✅; runtime per public docs) |
| Codex CLI | `~/.codex/skills` | `.codex/skills` | auto / `$skill` | ✅ `~/.codex/AGENTS.md` | ✅ | ❌ | Partially verified |
| OpenCode | `~/.config/opencode/skills` | `.opencode/skills` | `@skill` mentions | ✅ `~/.config/opencode/AGENTS.md` | ✅ | ❌ | Partially verified |
| Gemini CLI | `~/.gemini/skills` | `.gemini/skills` | auto-match with user consent prompt | ✅ `~/.gemini/GEMINI.md` | ✅ | ❌ | Partially verified |
| Vibe | `~/.vibe/skills` | `.vibe/skills` | `/skill`, auto-match | ✅ `~/.vibe/AGENTS.md` | ✅ | ✅ full (hooks.toml → `guard.py`, `qa.py`, reviewer/plan agents) | Partially verified (hook contract per Vibe docs; not executed headless in CI) |
| Antigravity | `~/.gemini/config/skills` | `.agents/skills` | theoretical | ⚠️ best-effort `~/.gemini/config/AGENTS.md` | via rules block only if the host reads it | ❌ | Theoretical |
| Cursor | `~/.cursor/skills` | `.cursor/skills` | auto-match (2.4+) | ❌ no documented global instruction file | ❌ unless the user adds the rules block to their Cursor rules | ❌ (Cursor has its own hooks, not integrated) | Partially verified (installer ✅; skills supported per Cursor changelog) |
| Any Agent Skills host | `~/.agents/skills` | `.agents/skills` | per host | ✅ `~/.agents/AGENTS.md` (dotfiles users) | via host's own tuning | ❌ | Theoretical |
| OpenCat | `~/.opencat/skills` | `.opencat/skills` | theoretical | ❌ | ❌ | ❌ | Theoretical |

## What the installer does about the gaps (no silent partial function)

- Hosts with a known global instruction file get the managed memory-rules block appended (once, idempotent).
- Hosts without one (today: **cursor**, **opencat**) receive the skills but the installer **prints an explicit notice that lessons/instincts will not load automatically** and points here.
- The guard/qa hooks exist only in the Vibe adapter (`extras/vibe/`). Other hosts can wire `guard.py` themselves if their hook contract matches the JSON-over-stdin shape described in `extras/vibe/guard.py`.

## Memory workflow availability

`remember-correction` and `learn-instinct` write to `~/.agents/memory/`. Reading that file at session start is what makes the memory worth writing — and that only happens where the rules block (or the user's own instruction file) loads it. If you use a host marked ❌ in "Memory read", add the two `~/.agents/memory/` lines to your host's custom instructions manually.

## Upgrade policy for this table

Every supported-host claim in the README must link to this table. New statuses require either an executed integration test or a published documentation source.
