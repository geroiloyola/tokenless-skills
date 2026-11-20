# Contributing

Thank you for keeping this kit small. The kit's value is discipline, so contribution rules are strict by design.

## The one rule

**A change that grows context must measurably grow capability.** If a line does not change what an agent does in a concrete situation, it does not ship. Default answer to "add more documentation inside skills" is no — put theory in `references/` or drop it.

## Adding or editing a skill

1. Read `skills/SKILL_MASTER.md` end to end. It is the contract.
2. Create the skill via the hand-off prompt in SKILL_MASTER §0.
3. Validate: `python3 scripts/check_skills.py --strict` — the checker enforces what SKILL_MASTER states (frontmatter contract, ≤250-char description, ≤50 non-empty body lines, ≤1000 est. tokens, explicit output section, referenced files exist).
4. Run the trigger/overlap/zero-context tests from SKILL_MASTER §7 manually; paste reasoning in the PR.

## Code (scripts, installer, guard)

- Standard library only. No new runtime dependencies, period. (Dev deps already free: bash, python3, node for the two ui scripts.)
- `guard.py` pattern changes must come with a test in `tests/test_guard.py` for both the deny and the false-positive side.
- Installer changes must keep `bash tests/test_installer.sh` green and must not grow an install database/config system.
- `docs/SECURITY.md` is the guard's contract; a guard PR that changes detection behavior without updating that file is rejected.

## Testing

```bash
make test          # or: python3 tests/run_all.py
```

Every test runs in isolated temp directories. If your change needs to touch a real user config to be testable, the design is wrong — ask instead.

## Commits

Conventional commits, one logical change per commit. The project body: what changed, why, and the failure mode it fixes.

## What will be declined

- Frameworks, dashboards, plugin systems, package managers, telemetry.
- Host-specific forks of skills (portability notes in the skill, adapters in `extras/`).
- "It would be nice if…" additions without a failing scenario or measured failure.
