# Release checklist

Run top to bottom before tagging. A release is cut by a human; nothing here automates publication.

1. **Doctrine gate**: `python3 scripts/check_skills.py --strict` → PASS.
2. **Tests**: `make test` (or `python3 tests/run_all.py`) → ALL SUITES PASSED.
3. **Syntax**: `bash -n install.sh && bash -n tests/test_installer.sh`.
4. **CI green** on the release commit (the workflow runs everything above).
5. **Version consistency**: every `skills/*/SKILL.md` `metadata.version` matches what the release intends; `CHANGELOG.md` has a dated section for the version.
6. **Installer reality check** (in a temp HOME, never your own):
   - `git clone --depth 1 --branch <tag> <url>` then `./install.sh` from the clone.
   - `curl | bash` (or `bash < install.sh`) prints the actionable clone-instead message and deletes nothing.
   - `--scope project` in a scratch dir creates only `.agents/skills` (+ `.vibe` extras when `--agent vibe`).
   - `--uninstall --yes` removes the 14 kit dirs from the temp HOME and nothing else.
7. **Docs**: README install command works verbatim; `docs/HOSTS.md` statuses still true for any host you claim "✅" on; `docs/SECURITY.md` matches guard behavior.
8. **Counts**: kit still ships the number of skills the README and SKILL_MASTER claim; always-loaded description total still ≤ ~1k tokens (`python3 scripts/check_skills.py --json` → sum desc? statically review).
9. **Integrity**: compute and publish the tag's SHA256 (e.g. `git archive --format=tar <tag> | sha256sum`) in the release notes; the pinned `--branch <tag>` clone path gives users commit-integrity transitively.
10. **Tag**: `git tag -a vX.Y.Z` on the exact HEAD that passed; do not move tags.
