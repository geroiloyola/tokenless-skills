# Changelog

All notable changes to tokenless-skills. Format inspired by Keep a Changelog; not every patch is listed.

## [1.0.0] — 2026

### Added
- `install.sh`: `--dry-run`, `--uninstall` (dry-run by default, `--yes` to apply), `--help`, `--host` alias for `--agent`, strict argument validation.
- Non-destructive installation: existing kit-named skills are backed up to `~/.tsk-backup/` (user scope) or `./.tsk-backup/` (project scope) with a timestamp before replacement; replacement is staged and swapped, so a failed copy leaves the previous skill intact.
- Conservative uninstall: removes only kit-owned skills — frontmatter `name:` must match **and** the installed copy must be byte-identical to the kit's (`diff -qr`); customized or older-version copies are moved to `.tsk-backup/` with collision-safe naming and backup-content verification instead of deleted; symlinked skill directories are never followed or removed; third-party skill names never touched; dry-run by default, `--yes` to apply.
- `--agent` host ids are validated up front: unknown ids are named in the error (exit 2 when none remain); backward-compatible with comma lists.
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
- Uninstall deleted user-customized kit-named skills without backup (independent release audit G7) — now moved to `.tsk-backup/` first, content-verified before the uninstall reports success. Same-second backup collisions no longer nest (audit G11).
- `chmod -R 777` never matched (case bug); `.env`/`id_rsa` missed on case variations; `secrets.env` not covered.
- Guard misses confirmed by the independent audit: `rm -rf --no-preserve-root /`; depth-1 system dirs (`/home`, `/etc`, `/usr`, …), Git Bash mount roots (`/c/`) and Windows drive roots (`C:/`, `C:/Users/…`); bare `chmod 777 /` with no flags; `${HOME}` brace expansion; `find . -delete` without a narrowing predicate (release audit G1–G5). Includes two false-positive fixes found by the same audit: `rm -f ./file` and `rm -rf ~/.cache/…` (subpath home deletes) are legal again.
- Protect mode now also covers cloud/container/GPG credentials: `.aws/`, `.kube/config`, `.docker/config.json`, `.gnupg/` (release audit G6).
- `git push -ff` shorthand and remote-content pipes to `node`, `deno`, `bun`, `perl`, `ruby` now denied (release audit P2).
- `install.sh` backup never nests on name collision; `.tsk-backup` retention is documented (never auto-pruned).
- `scripts/check_skills.py` now scans `references/*.md` for broken file references and relative links (fenced code blocks are skipped — they quote upstream tooling); `design-review/references/uiux.md` no longer implies `search.py` is shipped with the kit (release audit G12).
- README token figures corrected to the measured values (470 avg / 360–581 range / 718 always-loaded / 7,285 worst case) with method disclosure.
- Silent overwrite of user `hooks.toml` (now backed up first).
