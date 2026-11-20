# Changelog

All notable changes to tokenless-skills. Format inspired by Keep a Changelog; not every patch is listed.

## [1.0.0] — 2026

### Added
- `install.sh`: `--dry-run`, `--uninstall` (dry-run by default, `--yes` to apply), `--help`, `--host` alias for `--agent`, strict argument validation.
- Non-destructive installation: existing kit-named skills are backed up to `~/.tsk-backup/` (user scope) or `./.tsk-backup/` (project scope) with a timestamp before replacement; replacement is staged and swapped, so a failed copy leaves the previous skill intact.
- Conservative uninstall: removes only kit-owned skills (frontmatter `name:` must match), never third-party or user-customized directories.
- Rules block seeding now explicit per host: hosts without a documented global instruction file (cursor, opencat) get a printed notice instead of silent partial functionality. See `docs/HOSTS.md`.
- `scripts/check_skills.py`: validates all skills against the kit doctrine (frontmatter contract, name/dir match, metadata limits, body budget, referenced files, explicit output section). `--strict` and `--json` flags.
- `tests/`: guard test suite (real CLI interface), checker unit tests, installer end-to-end tests in isolated temp homes, unified runner `python3 tests/run_all.py`.
- CI (`.github/workflows/ci.yml`): syntax checks, doctrine validation, all suites, artifact hygiene, minimum permissions, SHA-pinned action.
- `docs/HOSTS.md` (compatibility matrix with evidence statuses), `docs/SECURITY.md` (guard threat model and honest limitations), `SECURITY.md` (disclosure), `RELEASE.md` (release checklist), `prompts/task-templates.md` (eval task anatomy referenced by eval-harness).

### Changed
- `install.sh`: `curl | bash` now fails fast with an actionable message instead of aborting mid-script; removed `eval` on path variables and `sed`-based template rendering (bash parameter substitution — immune to special characters in installation paths); project scope now installs only the universal `.agents/skills` dir by default (`--agent` to add hosts).
- `guard.py`: case-insensitive protection (`.ENV`, `ID_RSA`), new deny patterns (quoted `$HOME`, command substitution, `find -delete`, `curl | zsh`, process substitution, `+refspec` force push, flag-order `chmod 777`, `secrets.env`, `.ssh/`), protect mode fails closed on malformed input (bash mode stays fail-open), English messages.
- `README.md`: claims rescoped (measured vs hypothesized), install/uninstall/update/security-limitations documented, host claims linked to the matrix.
- Skills: `learn-instinct` and `remember-correction` gained the explicit `## Output` section required by the kit doctrine; minor portability notes in `spec-brainstorm`, `fresh-review`, `webapp-testing`, `security-review`.

### Fixed
- `curl | bash` aborted with an unbound-variable error before completing (the advertised install path).
- A glob miss could turn the installer's per-skill delete into `rm -rf <host-skills>/*` (deleting every skill in a host directory).
- Silent destruction of user-customized skills on reinstall.
- `chmod -R 777` never matched (case bug); `.env`/`id_rsa` missed on case variations; `secrets.env` not covered.
- Silent overwrite of user `hooks.toml` (now backed up first).
