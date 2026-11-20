# Release checklist

Run top to bottom before tagging. A release is cut by a human; nothing here automates publication.

1. **Doctrine gate**: `python3 scripts/check_skills.py --strict` → PASS.
2. **Tests**: `make test` (or `python3 tests/run_all.py`) → ALL SUITES PASSED.
3. **Syntax**: `bash -n install.sh && bash -n tests/test_installer.sh`.
4. **CI green on GitHub** — this is a hard gate: push the release commit, open
   the Actions tab of the repository, and confirm the workflow run for that
   exact SHA finished green. Local suite runs do not substitute: GitHub's
   runner is a clean Linux environment and is where the pipeline actually
   executes. Do not tag before the run is green.
5. **Version consistency**: every `skills/*/SKILL.md` `metadata.version` matches what the release intends; `CHANGELOG.md` has a dated section for the version.
6. **Installer reality check** (in a temp HOME, never your own):
   - `git clone --depth 1 --branch <tag> <url>` then `./install.sh` from the clone.
   - `curl | bash` (or `bash < install.sh`) prints the actionable clone-instead message and deletes nothing.
   - `--scope project` in a scratch dir creates only `.agents/skills` (+ `.vibe` extras when `--agent vibe`).
   - `--uninstall --yes` removes the 14 kit dirs from the temp HOME and nothing else.
7. **Docs**: README install command works verbatim; `docs/HOSTS.md` statuses still true for any host you claim "✅" on; `docs/SECURITY.md` matches guard behavior.
8. **Counts and token figures**: kit still ships the number of skills the README and SKILL_MASTER claim; re-verify the README's measured token figures against `python3 scripts/check_skills.py --json` (mean, range, description total, worst-case sum) and update them if skills changed. If a README claim cannot be re-measured, it must be labelled a hypothesis, not stated as a figure.
9. **Integrity**: compute and publish the tag's SHA256 (e.g. `git archive --format=tar <tag> | sha256sum`) in the release notes; the pinned `--branch <tag>` clone path gives users commit-integrity transitively.
10. **Tag**: `git tag -a vX.Y.Z` on the exact HEAD that passed; do not move tags.

## Benchmark method (for validating the capability hypothesis)

The README's "capability of larger frameworks" comparisons are hypotheses.
To turn one into a measurement, the minimal credible setup is:

1. **Configurations**: baseline (no extra skills), a recognized alternative
   suite, and this kit. Identical model + version, tool permissions, repo
   state, execution budget, temperature/reasoning settings.
2. **Tasks**: at least 3 fixed tasks over a fixed repository state, each with
   a pre-written success definition (commands whose exit codes decide) and a
   pre-written regression check. More tasks only once the pipeline works.
3. **Runs**: ≥10 per configuration; report median and p90 for total tokens,
   tool calls, and wall time; report success rate as a fraction.
4. **Honesty rules**: publish the harness, seed, and every raw run with the
   numbers; a run where the harness itself broke is discarded and reported.
   Cached input tokens are reported separately from total input tokens —
   never merged.
5. **Metric**: `successful tasks / total tokens`, alongside cost per
   successful task. Comparing a selectively-loading kit against an
   always-loaded framework must state which context frames are being
   compared (description-only vs always-loaded body).

Until such a harness has actually run, the README keeps the hypothesis label.

## Post-v1.0.0 state (2026-11)

- Tag `v1.0.0` exists at `5d93662` and tagging rules above still apply to the
  next tag (do not move tags; new tag on a HEAD that passed all gates).
- The preregistered benchmark harness (supersedes the generic method above:
  `evals/PREREGISTRATION.md`, threshold claims frozen before any run) is
  **built and mechanics-tested but has zero executed sessions** — round 0 is
  blocked on auth for a headless host CLI (`evals/LOG.md`).
- Hard gate for any future release whose notes mention capability or token
  comparisons: at least one adapter-verified session with real host `usage`
  must exist in `evals/results/` first. Without it, releases must keep every
  comparison labelled a hypothesis.
