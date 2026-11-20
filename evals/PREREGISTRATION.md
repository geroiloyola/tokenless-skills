# PREREGISTRATION — benchmark Tokenless vs competidores (Fase 2)

FROZEN: this file is committed **before any model call is made**. Thresholds,
cells, tasks and metrics below may only change in a new committed revision
with the change justified in CHANGELOG. Raw results land in `evals/results/`.

## Claim under test (fixed now)

Against each competitor, on identical tasks, model and limits:

1. `tokens`: tokenless (B) total session tokens ≤ **50%** of competitor's
   (stretch goal 30%). Session tokens = real host `usage` (input + output +
   cache read, counted separately), including always-loaded bootstrap and
   subagents.
2. `success`: tokenless success rate ≥ **90%** of the best competitor's, with
   a 95% confidence interval (Wilson) on the difference.

If either fails, the real number is published. Never massaged.

## Cells

| Cell | What runs | Pinned source |
|---|---|---|
| A | no installed skills | — |
| B | the 14 tokenless-skills, user scope in an isolated temp HOME | this repo, tested commit |
| C | superpowers equivalent core | obra/superpowers @ `22f0b463e7a5e579904dd6211a520321035526f7` |
| D | ECC minimal profile | affaan-m/ECC @ `4adeee6732a12d1540f49a4d50a38ce8c97f9a53` |

Equivalence choices (why these subsets):

- **C core (superpowers)**: `using-superpowers` (activation backbone) +
  `test-driven-development`, `systematic-debugging`, `verification-before-completion`,
  `writing-plans`, `brainstorming`, `requesting-code-review` — the direct
  workflow equivalents of implement-tdd/systematic-debugging/verify-done/
  write-plan/spec-brainstorm/fresh-review. Excluded: gemini/branch-management
  helpers with no tokenless counterpart.
- **D minimal profile (ECC)**: of 328 skills, the equivalents:
  `tdd-workflow`, `security-review`, `plan-orchestrate`,
  `conventional-commit-review`. A full-kit D would be an always-loaded cost
  no host can bootstrap equally; the minimal profile is the fairest
  comparison and the one ECC itself documents for minimal setups.

Both competitors are MIT; attribution lives here and in results metadata.
Fetched by `evals/fetch_competitors.py` into `evals/.cache/` (never committed).

## Tasks

12 preregistered tasks in `evals/tasks/` (2 per category), fixtures
materialized by `evals/tasks/gen_fixtures.py`, each with `.task.md` (prompt
with the 5-block anatomy) and `verify.sh` whose exit code is the verdict
(no LLM judge). Untouched fixtures MUST fail verification (checked by
`bench.py --dry-run`).

| # | Category | Task |
|---|---|---|
| 01 | feature/tdd | rounding discount on Cart |
| 02 | feature/tdd | slugify CLI extensions |
| 03 | bug/root-cause | pagination off-by-one (tests encode the bug) |
| 04 | bug/root-cause | cache invalidate misses derived index |
| 05 | refactor/safety | extract line_subtotal, API stable |
| 06 | refactor/safety | remove dead code, byte-identical output |
| 07 | security/secret | planted API key in a review diff |
| 08 | security/injection | f-string SQL to parameterized |
| 09 | done/trap | flaky-ish test with a contract marker must not be gutted |
| 10 | done/trap | release check exits 2, README claims green |
| 11 | spec/ambiguity | vague "prettier + faster" spec |
| 12 | spec/ambiguity | contradictory requirements must be surfaced |

## Protocol

- 3 repetitions per (task, cell). No rep reuse. Runs isolated in
  `evals/.run/<task>/<cell>-<rep>` — fresh fixture copy, fresh HOME.
- Headless host configured once for all cells; same model, same budget
  (per-task timeout 900 s, no manual retries). Temperature/seed are whatever
  the host exposes; if not controllable it is recorded in results as
  `uncontrolled: temperature`.
- Trigger set: 8 must-activate + 8 must-NOT-activate prompts per skill
  (`evals/triggers/<skill>.jsonl`), cell B only, 1 rep, activation read from
  the host transcript/skill-invocation log; no judge.
- `make bench` = fetch competitors + run the full matrix.
  `make bench-dry` = materialize fixtures + verify fixtures fail untouched.

## Metrics and decision

- Per run: success (verify.sh exit 0), usage tokens (in/out/cache read),
  turns, wall time, uncontrolled flags.
- Aggregates: success rate per cell with Wilson 95% CI; mean and max session
  tokens per cell (3 reps → report all 3, no cherry-picking); tokens per
  successful task; Pareto index = successes / 1,000 tokens.
- Decision rule (pre-committed): claim 1 uses mean total tokens across the
  12 tasks; if B's mean is > competitors' 50% → claim FAILED, publish real
  number. Claim 2 compares success counts with Wilson CI; B ≥ 0.9 × best
  competitor → PASSED. Cells with `usage: null` (host without usage
  accounting) are excluded from token claims, not faked.

## Known limitations (declared up front)

- Hosts run with their own defaults; temperature/cache behavior may be
  uncontrollable → recorded, not assumed equal.
- Task selection is ours (12 small tasks, Python-only fixtures): results say
  "on these 12 tasks", never "in general".
- Benchmark infrastructure itself is new: first run is always also a
  shakedown rep (labeled `shakedown: true` in results).

## Cost estimate (rule: approval before spending)

- Full matrix: 12 tasks × 4 cells × 3 reps = **144 sessions** + 224 trigger
  activations (B only) = **368 host sessions**.
- Smoke round (recommended first): 12 tasks × 4 cells × 1 rep = **48 sessions**
  + the 224 triggers = **272 sessions**.
- Tokens per session are unknown until one honest run: estimate 20k-60k
  tokens/session → smoke ≈ 5M-16M tokens; full ≈ 7M-22M. Cost = sessions ×
  measured usage × model price; **no cost figure is claimed until the first
  real session reports usage.**

## What will NOT be verified

- Any host whose CLI cannot print/emit token usage per session: token
  columns stay null for it and its cells are excluded from claim 1.
- Inter-host variance (one host only per benchmark run).
