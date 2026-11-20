# Release Audit — tokenless-skills v1.0.0 (commit `abb4f89`)

Independent adversarial release audit. Every finding below was reproduced by
executing the actual code in isolated temporary directories; nothing was taken
from comments, docs, or prior reports without verification. No implementation
files were modified during this audit.

## 1. Commit and working-tree status

| Item | Value |
|---|---|
| Audited commit | `abb4f89` (`feat: harden installer, guard and self-validation for v1.0`) |
| Full SHA | `abb4f8975b85ac7bb757ea01991035dde160dd2c` |
| Working tree at start | Clean (`git status --porcelain` → 0 entries) |
| Working tree at end | Clean except this report (`docs/RELEASE_AUDIT.md`) |
| Platform | Windows 11 / Git Bash (MSYS2) / native Python 3.10 |

## 2. Executive verdict

**READY WITH DOCUMENTED LIMITATIONS — conditional on four pre-tag documentation corrections (§9).**

No P0 issues: the install path cannot silently destroy user data (every
overwrite is backed up, third-party skills are untouched, a SIGKILL
mid-install leaves no inconsistent state, symlinked skill dirs are replaced
without following into the target). The guard does exactly what its docstring
claims — a best-effort accident tripwire — but seven realistic accident
shapes are not caught and are missing from the "honest bypass list" in
`docs/SECURITY.md`, and one documented claim about uninstall behavior is
false. All are cheap fixes; none requires design changes.

## 3. Findings

### P0 — none

### P1

#### G1. Guard allows `rm -rf --no-preserve-root /`
- **Where:** `extras/vibe/guard.py:20` (flag group `(?:-\w+\s+)+` cannot match `--no-preserve-root`, whose second dash is followed by `-`, failing the required `\s+`).
- **Impact:** The single most famous catastrophic rm is allowed by a guard whose stated purpose is to catch exactly this class of accident.
- **Reproduce:** `echo '{"tool_input":{"command":"rm -rf --no-preserve-root /"}}' | python extras/vibe/guard.py bash` → empty stdout (ALLOW).
- **Expected:** deny. **Fix:** add `(r"\brm\s+[^;\n]*--no-preserve-root", "rm with --no-preserve-root")` to `DANGEROUS`.

#### G2. Guard allows catastrophic deletes of absolute paths other than bare `/` and `~`
- **Where:** `extras/vibe/guard.py:20` target list is `(/|/\*|~|\$home|\*|\.\.?|\.git)(/|\s|$)`.
- **Impact:** `rm -rf /home`, `rm -rf /usr`, `rm -rf /c/` (Git Bash root — the actual root on the platform this repo targets), and a fully expanded `rm -rf C:/Users/<user>` are all allowed. `/home` kills all user data on Linux CI.
- **Reproduce:** `bash` mode with `rm -rf /home` → ALLOW (`/h` fails the required boundary after `/`); `rm -rf /c/` → ALLOW; `rm -rf C:/Users/Jerry` → ALLOW.
- **Fix:** add a pattern for `rm -rf` followed by a bare POSIX absolute path with depth ≤ 2 (e.g. `(?:^|[;&|]\s*)rm\s+(?:-\w+\s+)*/(?!\w)`-style, plus drive-root `(?i)[a-z]:/?(?:\s|$)` for Windows roots). Also match one level deep (`/home`, `/etc`, `/usr`).

#### G3. Guard allows bare `chmod 777 /` and `chmod 777 .`
- **Where:** `extras/vibe/guard.py:29` — both alternatives require at least one flag token: `\bchmod\s+777\b(?:\s+-\w+)+` or `\bchmod(?:\s+-\w+)+\s+777\b`.
- **Impact:** `chmod 777 /` (no flags) — the shortest world-writable-root accident — is allowed. The swap-flag fix over-corrected: it now requires flags in either order.
- **Reproduce:** `chmod 777 /` → ALLOW; `chmod 777 .` → ALLOW. (`chmod -R 777 /` correctly denies.)
- **Fix:** `(r"\bchmod\s+777\b", "chmod 777")` after removing the redundant flag variants (the audit's `chmod -R 777 /` regression case still passes).

#### G4. Guard allows `rm -rf ${HOME}` (brace expansion form)
- **Where:** `extras/vibe/guard.py:20` — literal `\$\home` matches `$home` but not `${home}`.
- **Impact:** A common brace-style spelling of the home delete is allowed. Quoted/tilde forms are caught; this one is not.
- **Reproduce:** `rm -rf ${HOME}` → ALLOW.
- **Fix:** add `\$\{?home\}?` to the target alternation.

#### G5. Guard allows `find . -delete` / `find . -type f -delete`
- **Where:** `extras/vibe/guard.py:25` — `\bfind\s+(/\s*|~\s*)...` only anchors `/` or `~` starts.
- **Impact:** Cwd-tree deletion via find — equivalent to `rm -rf *`, which *is* denied — is allowed. Note `tests/test_guard.py:106` explicitly allows `find . -name '*.pyc' -delete` (correct), but the unqualified `-delete` form is a different animal.
- **Reproduce:** `find . -type f -delete` → ALLOW.
- **Fix:** `(r"\bfind\s+\.?\s*[^;\n]*\s-delete\b(?!.*-name)", ...)` — deny when `-delete` appears and no narrower `-name` predicate constrains it. Keep `find . -name '*.pyc' -delete` as the allowance regression.

#### G6. Protect mode does not protect cloud/container/GPG credentials
- **Where:** `extras/vibe/guard.py:56-66` (`PROTECTED_PATHS`) — `.netrc`, `.npmrc`, `.pypirc` are listed, but `.aws/credentials`, `.kube/config`, `.docker/config.json`, `.gnupg/*` are absent.
- **Impact:** An agent told to "configure AWS" can overwrite real cloud credentials without a warning; the audit brief explicitly listed cloud credentials as must-protect.
- **Reproduce:** `bash`-style JSON `{"tool_input":{"path":".aws/credentials"}}` in `protect` mode → ALLOW (as are `.kube/config`, `.docker/config.json`, `.gnupg/secring.gpg`).
- **Fix:** add `(r"(^|/)\.aws/", "AWS credentials"), (r"(^|/)\.kube/config$", "k8s cluster config"), (r"(^|/)\.docker/config\.json$", "docker registry auth"), (r"(^|/)\.gnupg/", "GPG keyring")`.

#### G7. Uninstall deletes a user-customized (kit-named) skill without backup; CHANGELOG claim is false
- **Where:** `install.sh:139-160` (`uninstall_host` does `rm -rf "$dir"` after a frontmatter check, no backup); contradiction with `CHANGELOG.md:10` — "removes only kit-owned skills ..., never third-party or **user-customized directories**".
- **Reproduce:** install kit → edit body of an installed skill (keep `name:` frontmatter) → `./install.sh --uninstall --yes --agent claude` → the customized skill is silently gone; `.tsk-backup/` does not receive it (verified: user-edit test above).
- **Impact:** Irreversible destruction of user customization, plus a false documented claim. Mitigated only by the dry-run default.
- **Fix (one line):** in `uninstall_host`, `mv "$dir" "$BACKUP_DIR/$name-$(date +%Y%m%d-%H%M%S)-$$"` instead of `rm -rf "$dir"`. Then the CHANGELOG claim becomes true (customized copies are preserved in the backup).

### P2

#### G8. `git push -ff origin main` bypasses force-push denial
- **Where:** `extras/vibe/guard.py:31` — `\s-f\b` needs a word boundary after `-f`; `-ff` has none; `--force\b` doesn't match. Verified: ALLOW.
- **Impact:** Two-force shorthand is a real force push. (Earlier probe expectation for `git push -ff-only` was wrong — it is not a valid push flag and correctly allows; the finding is `-ff`.) Frequency: rare spelling.
- **Fix:** change `\s-f\b` to `\s-f{1,2}\b` (keeping the `--force-with-lease` negative lookahead).

#### G9. `curl … | node` RCE pipe allowed
- **Where:** `extras/vibe/guard.py:81` — pipe-to-shell covers `ba|z|da|k sh` and `python(3)?`, not `node`/`deno`/`bun`.
- **Impact:** Remote-content-to-interpreter RCE via the most common JS runtime is missed. Note `docs/SECURITY.md:34` ("interpreters") arguably covers interpreter misuse generally, but remote-content pipes are a different, more dangerous class than `python -c`.
- **Fix:** extend the pipe pattern alternation with `node|deno|bun`.

#### G10. Guard allows `rm -rf ~user`
- **Where:** `extras/vibe/guard.py:20` — `~` requires a `/`, `\s`, or `$` boundary; `~user` fails it. Verified: ALLOW.
- **Impact:** Low (another user's home on shared hosts). **Fix:** extend with `~\w*`.

#### G11. Backup directory collision would nest (theoretical, not reproduced)
- **Where:** `install.sh:172-181` (`backup_existing`) — target name is `name-YYYYmmdd-HHMMSS-$$`. Two overwrites of the *same* skill name in the *same process, same second* (multi-host run, both hosts having pre-existing versions, tiny kit on a fast disk) produce the same backup name; POSIX `mv dir existing-dir` then nests inside instead of failing.
- **Reproduce:** not reproduced in 6 rapid two-host reinstall rounds (backs-up land 2–4 s apart); semantics proved by a unit-level `mv` into an existing dir. Theoretical.
- **Impact:** No data loss (nested copy is intact), but the backup layout is silently mangled.
- **Fix:** `while [ -e "$bdir" ]; do ts="$ts-1"; done` guard before the `mv`.

#### G12. Checker does not validate references inside `references/*.md`
- **Where:** `scripts/check_skills.py:152` — only the SKILL.md body is scanned.
- **Impact:** `skills/design-review/references/uiux.md:88-89` instructs `python <skill-dir>/scripts/search.py …`, which does not exist in the kit (it belongs to the upstream `ui-ux-pro-max-cli` package; the surrounding text says "upstream repo" but an agent following the digest verbatim hits a missing file until it reads the context).
- **Fix:** scan `references/*.md` too, or add one clarifying phrase ("tooling from the optional upstream skill") in uiux.md. Related: `SKILL_MASTER.md §5` already demands a one-line fallback for tool-backed content; uiux.md lacks it.

#### G13. Test coverage gaps
Verified by reading `tests/test_guard.py` and `tests/test_installer.sh` and running them:
- Guard tests cover every *previously documented* bypass, but none of the seven new P1 gaps (G1–G6) or P2 shapes — i.e. the "honest list" and the tests agree with each other but undercount reality.
- Installer tests do not cover: symlinked existing skill dir, SIGKILL mid-run (orphans/recovery), uninstall of a customized kit skill, multi-host backup retention, rollback after webh failure, or `--agent` with an unknown host name.
- No test exercises `hooks.toml` 2× reinstall (overwrite of the backup file) or the `.tsk-backup` retention policy (it grows unboundedly — informational G17).

### Informational

#### I1. CI cannot be executed locally here
`act` (or Docker-based local workflow runners) is not available on this machine; YAML was validated by parse (`yaml.safe_load`) and every step was executed manually with identical commands. **GitHub-hosted CI execution remains unverified** until the first push triggers it.

#### I2. CI minor redundancies
`.github/workflows/ci.yml` runs `check_skills --strict` twice (steps 2 and 6); the README link check greps only `scripts/*.py` in README.md (not `docs/`). Pinned checkout SHA ✔; `permissions: contents: read` ✔; no third-party actions besides pinned checkout ✔; runtime versions are the runner's own (no `setup-python`) — acceptable for a stdlib-only project.

#### I3. Unknown guard mode fails open by design
`guard.py:172` prints to stderr and allows. Only two modes are wired by `hooks.toml`, so unreachable in practice; the docstring documents behavior. A deny-by-default for unknown modes would be safer and is a one-line change.

#### I4. Unknown `--agent` typo gives a generic error
`--agent cluade` (typo) → "❌ No hosts detected or matched." — correct exit code, but the message does not echo that the *host id* was unrecognized. One line of improvement.

#### I5. `.tsk-backup/` grows unboundedly
Reinstalls accumulate timestamped backups; there is no prune policy. Threat-free (gitignore'd), but worth a 10-line prune in a future version.

#### I6. Per-skill version vs kit version relationship undocumented
All 14 skills declare `metadata.version: "0.4.0"` while the kit/version, CHANGELOG, and installer say 1.0.0; the intended relationship (independent semver per skill? bumped together?) is documented nowhere, and `RELEASE.md` checklist does not mention skill metadata versions. One sentence in RELEASE.md or SKILL_MASTER §2 resolves it.

## 4. Reproduction steps for critical findings

All reproduction was done in `mktemp -d` sandboxes against a full copy of the kit; the real `$HOME` was never touched.

```bash
KIT=$(mktemp -d); cp -R . "$KIT"
HOME=$(mktemp -d) bash "$KIT/install.sh" --agent claude   # sandbox install
```
- G1: `echo '{"tool_input":{"command":"rm -rf --no-preserve-root /"}}' | python extras/vibe/guard.py bash` → no stdout (allow). Expected: `{"decision":"deny",...}`.
- G2: same harness, `rm -rf /home` and `rm -rf /c/` → allow.
- G3: same harness, `chmod 777 /` → allow.
- G4: same harness, `rm -rf ${HOME}` → allow.
- G5: same harness, `find . -type f -delete` → allow.
- G6: `echo '{"tool_input":{"path":".aws/credentials"}}' | python extras/vibe/guard.py protect` → allow.
- G7:
```bash
KIT=$(mktemp -d); cp -R . "$KIT"; H=$(mktemp -d)
HOME="$H" bash "$KIT/install.sh" --agent claude >/dev/null
echo "# user customization" >> "$H/.claude/skills/verify-done/SKILL.md"
HOME="$H" bash "$KIT/install.sh" --uninstall --yes --agent claude >/dev/null
ls "$H/.claude/skills" "$H/.tsk-backup"    # skill gone, not in backup
```

Installer adversarial results (all in sandboxes, 32 repo checks + 19 new independent checks):

| Scenario | Result |
|---|---|
| Fresh install (user + project scope) | ✅ rc=0, expected trees only |
| Reinstall over existing | ✅ backup + swap, user data kept |
| `SIGKILL` mid-install | ✅ no `.tmp-old` orphans, old skill intact, reinstall recovers |
| Symlinked existing skill dir → outside target | ✅ install rc=0; target file survived; symlink archived in backup |
| Uninstall after user customization | ❌ G7 — deleted, no backup |
| 3× install/uninstall cycle | ✅ stable, all 14 skills re-consistent |
| Backup collision (6 rapid 2-host reinstalls) | ✅ no nesting observed; theoretical only (G11) |
| Invalid `--scope`/unknown/missing-value args | ✅ all exit 2 |
| Unknown host name | ✅ exits nonzero (generic message, I4) |
| Empty skills dir / all-junk skills dir | ✅ refuses, nothing deleted |
| Junk dir skipped | ✅ warning, not installed |
| stdin (`cat install.sh | bash`) from random dir | ✅ rc=1, actionable "clone" message |
| stdin from *inside* the kit | ✅ rc=0 (kit detected via `$PWD/install.sh`) |
| hooks.toml overwrite | ✅ backed up pre-replace; restore is manual (disclosed in output) |

## 5. Tests executed and exact results

| Command | Result |
|---|---|
| `python tests/run_all.py` | `ALL SUITES PASSED` (4/4 suites), rc=0 |
| `python tests/test_guard.py` (inside suite) | 11/11 test methods pass |
| `python tests/test_check_skills.py` (inside suite) | 17/17 pass |
| `bash tests/test_installer.sh` (inside suite) | 32/32 checks pass |
| `python scripts/check_skills.py --strict` | `14 checked (strict): 0 error(s), 0 warning(s) -> PASS` |
| `bash -n install.sh` / `bash -n tests/test_installer.sh` | OK |
| `python -m py_compile …` (guard, checker, both test files) | OK |
| Independent guard matrix (66 bash-mode + 17 protect-mode + 12 malformed-input cases) | 47+13 matched expectations; 5 confirmed allow-side gaps (G1–G6) + 2 P2 |
| Independent installer adversarial set (19 checks) | 19/19 pass |
| `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` | OK |

## 6. Coverage gaps

Summarized above: G1–G6 untested in the shipped suites; installer suites lack
symlink/kill/customized-uninstall/unknown-host cases; checker misses
references-internal links; CI unverified on GitHub infrastructure.

## 7. Host compatibility evidence

`docs/HOSTS.md` was cross-checked against the installer's actual host table
(`install.sh:107-117`) and observed behavior. Its status vocabulary is honest:

| Host category | Status | Evidence in this audit |
|---|---|---|
| Any host with a `skills/` dir (Claude Code, Codex, Gemini CLI, Cursor, OpenCode paths) | **Partially verified** | Multi-host install to isolated `$HOME` sandboxes works; per-host *runtime* behavior (activation, rules loading) was not executed against any real host here and is labeled "per public docs" — correctly |
| Vibe extras (guard/qa hooks) | **Partially verified** | Files render to target layout; hook contract not executed live in this audit |
| Antigravity, OpenCat, generic `.agents` | **Theoretical** | Labeled theoretical; matches what can actually be proven |

No overclaims were found in the shipped status matrix.

## 8. Token-claim evidence

Reproduced with `python scripts/check_skills.py --json` (chars/4 estimator):

| Claim (README.md:3,5) | Measured | Classification |
|---|---|---|
| "~450 measured average" tokens/skill | **469.0** (26,266 body chars /4 = 6,567 total; /14 skills) — claim is 4% optimistic | **Reproducibly measured** (estimator-based; labelled as such) — recommend README says "~470" |
| "~350–600 tokens each" | 360–581 | **Reproducibly measured** ✔ |
| "~0.7k always-loaded" | 2,874 desc chars /4 = 718 | **Reproducibly measured** ✔ |
| Worst case ≈7.3k if all 14 fire (SKILL_MASTER §9) | 718 + 6,567 = 7,285 | **Reproducibly measured** ✔ |
| Capability parity with larger frameworks | — | **Hypothesis** — labelled as such in README (`Claims, honestly` block), with a measurement protocol in RELEASE.md; no benchmark executed |
| Every number in this audit's token column | chars/4, deterministic, re-runnable | **Reproducible** ✔ |

The smallest credible benchmark to close the gap: 3 tasks × 1 repo state
(the kit's own `tests/fixtures/demos`, or a tiny public repo), run headless
against 2 hosts with `--print-raw` style token capture, comparing
baseline/no-skills vs tokenless-skills vs one always-loaded framework.
Semantics (success rate) fixed in advance; 10 runs; report p50/p90. No need
for 20 tasks to validate the core economic claim.

## 9. Release blockers

None at the code level. Four **pre-tag documentation/code corrections are
required before `v1.0.0` is tagged** (they are one-liners):

1. CHANGELOG.md:10 claim corrected (or G7's one-line backup fix makes it true — preferable).
2. `docs/SECURITY.md` "What it cannot detect" list extended with G1–G4, G9, G10.
3. G1–G6 patterns added to `guard.py` + regression tests (30 min of work including tests).
4. `uiux.md` search.py reference clarified (upstream tool) or checker scope widened (G12).

## 10. Prioritized remediation plan

| Priority | Item | Est. effort | Acceptance criterion |
|---|---|---|---|
| P1 | G1–G6 patterns + regression tests | ~1 h | new cases deny in both modes; old MUST_ALLOW set unchanged |
| P1 | G7 uninstall backup-fefore-delete | ~10 min | customized kit skill survives uninstall in `.tsk-backup/`; CHANGELOG claim now true |
| P2 | G8, G9, G10 patterns | ~15 min | same test style as G1–G6 |
| P2 | G11 backup-collision guard (`while [ -e ]`) | ~5 min | forced same-second overwrite no longer nests |
| P2 | G12 checker scans `references/*.md` + uiux.md clarification | ~20 min | `check_skills.py --strict` flags a future missing reference case |
| P2 | G13 add missing installed-test scenarios (symlink, kill, customize, unknown-host, 2× hooks) | ~1 h | new `tests/test_installer.sh` sections all green |
| P3 | I3 unknown-mode deny, I4 unknown-agent hint, I5 backup prune | ~30 min | cosmetic; no behavior change for valid inputs |
| P3 | First real push → verify CI green on GitHub | 0 (event) | run link on the workflow tab is green |

## 11. Final decision

**READY WITH DOCUMENTED LIMITATIONS.** No P0s. All P1s are cheap, localized,
and have explicit one-line fixes; every one of them is regressed-testable
within an hour. The limitation set is exactly the guard's known regex ceiling
(now fully enumerated in §3) and the hosts' unverified runtime path — both
accurately disclosed, with the CHANGELOG uninstall line being the single
false statement to correct before tagging.
