# tokenless-skills

**14 ultra-light agent skills (369-572 body tokens each, 464 measured mean) with an always-loaded cost of 600 tokens.** The design goal: maximum practical agent workflow capability per token, without sacrificing verification discipline.

> **Claims, honestly** — token figures are **measured with tiktoken `o200k_base`** by `scripts/measure_tokens.py --json evals/results/tokens-baseline.json` (raw JSON and command are in the repo): bodies 369-572 tokens per skill (mean 464); always-loaded description cost 600 total. The chars/4 fallback was validated against the tokenizer at 2.6% mean error. Worst case, if a session actually loaded every skill body: ~7,096 tokens (descriptions + all 14 bodies) — unrealistic; a session typically loads 2-4 skills (~1,000 tokens). Claims about matching the capability of larger frameworks, or any %-comparison against other skill systems, are **hypotheses: none has been benchmarked yet. A preregistered A/B/D harness (no skills / tokenless / competitor core) with raw results versioned in `evals/results/` is the follow-up work; until then, treat those comparisons as design intent, not evidence.**

## Install

The installer reads the repository, so distribution is clone-then-run (pinned clones give you git-level integrity):

```bash
# Global (user scope: all agents on this machine with an existing config dir)
git clone --depth 1 --branch v1.0.0 https://github.com/geroiloyola/tokenless-skills.git
cd tokenless-skills && ./install.sh

# Project-only (commits to your repo; installs the universal .agents/skills)
./install.sh --scope project

# Pick hosts explicitly (vibe, claude, codex, opencode, gemini, antigravity, cursor, agents, opencat)
./install.sh --agent claude,codex
```

> `curl .../install.sh | bash` is intentionally **not** supported — the installer reads sibling files. If you pipe it by mistake it exits with exact clone instructions and touches nothing.

**Safety by construction** ([details in `docs/HOSTS.md`](docs/HOSTS.md)): overwriting an existing kit skill moves the old one to `~/.tsk-backup/` first; third-party skills are never touched; `--dry-run` previews every change; `--uninstall` removes only unmodified kit-owned skills and moves customized copies to the backup instead of deleting.

## Skills

| Skill | Purpose |
|-------|---------|
| repo-context | Build verified AGENTS.md |
| spec-brainstorm | Turn ambiguity into specs with acceptance criteria |
| write-plan | Split work into 10–30 min tasks with file contracts |
| implement-tdd | Red → Green → Refactor, test-first always |
| systematic-debugging | Root-cause via falsifiable hypotheses |
| verify-done | Gates + diff review + spec checks before "done" |
| remember-correction | Persist user corrections as 1-line rules |
| learn-instinct | Confidence-scored patterns that promote or prune |
| subagent-execute | 1 task = 1 worktree = 1 subagent |
| fresh-review | Blocking, read-only review in clean context |
| webapp-testing | Browser: console, network, a11y (with script + MCP ladder) |
| security-review | Secrets, injection, authz over the diff |
| design-review | Aesthetic direction + contrast script audit |
| eval-harness | Re-run 5 fixed tasks on every kit change |

Protocol: `spec-brainstorm → write-plan → implement-tdd → fresh-review → verify-done`, with `subagent-execute` as parallel runner and the two memory skills accumulating rules between sessions.

## Supported hosts

✅ Claude Code • ✅ Codex • ✅ OpenCode • ✅ Vibe (incl. hooks: security guard + QA) • ✅ Gemini CLI • ⚠️ Antigravity • ⚠️ Cursor • ⚠️ Any [Agent Skills 1.0](https://agentskills.io) host

⚠️ = installer creates the right directories and Agent Skills-conformant folders, but check `docs/HOSTS.md` for per-host capability (activation, memory loading, hooks) before relying on it. Do not assume "files copied" means "features active".

## Usage

Skills are standard Agent Skills 1.0 folders — your host discovers them automatically; invoke by the host's convention (`/` picker, `$name`, `@name`, or just describe the task to match a description). Start with `repo-context` in a new repo: it builds the AGENTS.md every other skill consults.

Editing skills? Author against `skills/SKILL_MASTER.md`, then validate:

```bash
python3 scripts/check_skills.py --strict
```

## Update / uninstall

```bash
git -C tokenless-skills pull && cd tokenless-skills && ./install.sh   # backs up what it replaces
./install.sh --uninstall            # dry-run: lists what would go
./install.sh --uninstall --yes      # applies kit-owned skills
```

Uninstall is conservative: frontmatter `name:` must match a kit skill, and the
installed copy must be byte-identical to the kit's before it is removed.
**Customized or older-version copies are moved to `~/.tsk-backup/` (or
`./.tsk-backup/` in project scope), never deleted.** Third-party skills and
symlinks are left untouched. `~/.agents/memory/` (lessons, instincts) — it is
yours and survives uninstall. Backups are never auto-deleted; prune
`.tsk-backup` manually when convenient.

## Security limitations (read this)

The Vibe-mode guard (`extras/vibe/guard.py`) is a **best-effort accident filter, not a sandbox, not a security boundary**; bash mode fails open and protect mode fails closed; obfuscated/in-interpreter attacks are outside its threat model by construction. Full analysis and known-bypass ledger: `docs/SECURITY.md`. Report issues per `SECURITY.md`.

## Project layout

```
skills/            14 skills + SKILL_MASTER.md (authoring doctrine)
scripts/           check_skills.py (doctrine validation)
tests/             guard / checker / installer suites, python3 tests/run_all.py
extras/vibe/       Vibe adapter (guard.py, qa.py, hooks.toml, reviewer/plan agents)
extras/chatbot/    concatenated single-file export for chat UIs
docs/              HOSTS.md (compat matrix), SECURITY.md (threat model)
```

Contributing: `CONTRIBUTING.md` — the short version: a change that grows context must measurably grow capability. Changelog: `CHANGELOG.md`. Releases: `RELEASE.md`. License: MIT (`LICENSE`).
