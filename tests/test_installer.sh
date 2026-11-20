#!/usr/bin/env bash
# Installer tests for tokenless-skills. Every test runs in an isolated
# temporary HOME; the real user configuration is never touched.
#
# Run:  bash tests/test_installer.sh
set -u
PASS=0; FAIL=0; FAILED_NAMES=()

check() { # $1 name, $2 = 0 (pass) or 1 (fail)
  if [ "$2" -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); FAILED_NAMES+=("$1"); echo "  FAIL: $1"; fi
}
ok_if() { [ "$1" -ne 0 ] && echo 0 || echo 1; }         # invert an exit code
yes_if() { [ "$1" -eq 0 ] && echo 0 || echo 1; }        # 0 when condition true

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$(mktemp -d)"
trap 'rm -rf "$BASE"' EXIT

setup_kit() { # copy kit to $1/kit, isolated home at $2
  mkdir -p "$1/kit" "$2"
  cp -r "$KIT_ROOT"/. "$1/kit/"
  rm -rf "$1/kit/.git"
  export HOME="$2"
}

# ---------- 1: fresh install, unrelated skills preserved ----------
T="$BASE/t1"; H="$T/h"
setup_kit "$T" "$H"
mkdir -p "$H/.claude/skills/third-party-skill" "$H/.claude/skills/my-custom"
echo "user data" > "$H/.claude/skills/third-party-skill/SKILL.md"
echo "custom"   > "$H/.claude/skills/my-custom/SKILL.md"
(cd "$T/kit" && bash install.sh --agent claude >/dev/null 2>&1)
check "fresh install creates kit skills" $([ -d "$H/.claude/skills/implement-tdd" ] && [ -d "$H/.claude/skills/verify-done" ] && echo 0 || echo 1)
check "skill count is 14" $([ "$(ls "$H/.claude/skills" | wc -l)" -eq 16 ] && echo 0 || echo 1) # 14 kit + 2 user
check "third-party skill preserved" $([ -f "$H/.claude/skills/third-party-skill/SKILL.md" ] && echo 0 || echo 1)
check "user custom skill preserved" $([ -f "$H/.claude/skills/my-custom/SKILL.md" ] && echo 0 || echo 1)
check "memory files created" $([ -f "$H/.agents/memory/lessons.md" ] && [ -f "$H/.agents/memory/instincts.md" ] && echo 0 || echo 1)
check "rules block seeded" $([ -f "$H/.claude/CLAUDE.md" ] && grep -q "tokenless-skills managed block" "$H/.claude/CLAUDE.md" && echo 0 || echo 1)

# ---------- 2: reinstall is non-destructive (backup + swap) ----------
T2="$BASE/t2"; H2="$T2/h"
setup_kit "$T2" "$H2"
(cd "$T2/kit" && bash install.sh --agent claude >/dev/null 2>&1)
echo "# HEAVILY CUSTOMIZED" > "$H2/.claude/skills/verify-done/SKILL.md"
echo "notes" > "$H2/.claude/skills/verify-done/personal-notes.md"
(cd "$T2/kit" && bash install.sh --agent claude >/dev/null 2>&1)
check "customization backed up, not destroyed" $([ -d "$H2/.tsk-backup" ] && find "$H2/.tsk-backup" -name "verify-done-*" -maxdepth 1 -type d | grep -q . && echo 0 || echo 1)
check "backup contains personal notes" $(find "$H2/.tsk-backup" -name "personal-notes.md" | grep -q . && echo 0 || echo 1)
check "kit version active after backup-swap" $(head -2 "$H2/.claude/skills/verify-done/SKILL.md" | grep -q "name: verify-done" && echo 0 || echo 1)

# ---------- 3: stdin execution fails safely with guidance ----------
T3="$BASE/t3"; H3="$T3/h"
setup_kit "$T3" "$H3"
mkdir -p "$H3/.claude/skills/precious"
echo "precious" > "$H3/.claude/skills/precious/SKILL.md"
cd "$T3" || exit 1
stdin_out=$(HOME="$H3" bash < "$T3/kit/install.sh" 2>&1); rc3=$?
check "stdin execution exits nonzero with guidance" $( [ $rc3 -ne 0 ] && echo "$stdin_out" | grep -q "git clone" && echo 0 || echo 1 )
check "stdin execution deletes nothing" $([ -f "$H3/.claude/skills/precious/SKILL.md" ] && echo 0 || echo 1)

# ---------- 4: empty skills dir refuses (no glob-to-'*' deletion) ----------
T4="$BASE/t4"; H4="$T4/h"
setup_kit "$T4" "$H4"
mkdir -p "$H4/.claude/skills/precious2"
echo "precious" > "$H4/.claude/skills/precious2/SKILL.md"
mkdir -p "$T4/emptykit/skills"
cp "$T4/kit/install.sh" "$T4/emptykit/"
(cd "$T4/emptykit" && bash install.sh --agent claude >/dev/null 2>&1); rc4=$?
check "empty skills dir exits nonzero" "$(ok_if $rc4)"
check "empty skills dir deletes nothing" $([ -f "$H4/.claude/skills/precious2/SKILL.md" ] && echo 0 || echo 1)
check "no stray dirs created under host" $([ "$(ls -d "$H4"/.claude/skills/*/ 2>/dev/null | grep -v precious2 | wc -l)" -eq 0 ] && echo 0 || echo 1)

# ---------- 5: argument validation ----------
T5="$BASE/t5"; H5="$T5/h"
setup_kit "$T5" "$H5"
(cd "$T5/kit" && bash install.sh --scope bogus >/dev/null 2>&1); rcS=$?
(cd "$T5/kit" && bash install.sh --definitely-not-a-flag >/dev/null 2>&1); rcA=$?
(cd "$T5/kit" && bash install.sh --help >/dev/null 2>&1); rcH=$?
check "invalid scope rejected" "$(ok_if $rcS)"
check "unknown flag rejected" "$(ok_if $rcA)"
check "help exits 0" "$(yes_if $rcH)"

# ---------- 6: dry-run writes nothing ----------
T6="$BASE/t6"; H6="$T6/h"
setup_kit "$T6" "$H6"
(cd "$T6/kit" && bash install.sh --agent codex --dry-run >/dev/null 2>&1)
check "dry-run creates nothing" $([ ! -e "$H6/.codex" ] && [ ! -e "$H6/.agents" ] && echo 0 || echo 1)

# ---------- 7: project scope = universal .agents by default ----------
T7="$BASE/t7"; H7="$T7/h"
setup_kit "$T7" "$H7"
mkdir -p "$T7/proj"
(cd "$T7/proj" && HOME="$H7" bash "$T7/kit/install.sh" --scope project >/dev/null 2>&1)
check "project scope installs universal .agents/skills" $([ -d "$T7/proj/.agents/skills/verify-done" ] && echo 0 || echo 1)
check "project scope: no other host dirs by default" $([ ! -d "$T7/proj/.claude" ] && [ ! -d "$T7/proj/.vibe" ] && echo 0 || echo 1)
(cd "$T7/proj" && HOME="$H7" bash "$T7/kit/install.sh" --scope project --agent vibe >/dev/null 2>&1)
check "project scope + --agent adds .vibe extras" $([ -f "$T7/proj/.vibe/hooks.toml" ] && [ -f "$T7/proj/.vibe/scripts/guard.py" ] && echo 0 || echo 1)
check "rendered hooks.toml resolves KIT_DIR" $(grep -q "python3 .*\.vibe/scripts/guard.py bash" "$T7/proj/.vibe/hooks.toml" && echo 0 || echo 1)

# ---------- 8: multi-host ----------
T8="$BASE/t8"; H8="$T8/h"
setup_kit "$T8" "$H8"
mkdir -p "$H8/.codex"
(cd "$T8/kit" && bash install.sh --agent claude,codex >/dev/null 2>&1)
check "multi-host installs to both" $([ -d "$H8/.claude/skills/write-plan" ] && [ -d "$H8/.codex/skills/write-plan" ] && echo 0 || echo 1)

# ---------- 9: conservative uninstall ----------
T9="$BASE/t9"; H9="$T9/h"
setup_kit "$T9" "$H9"
mkdir -p "$H9/.claude/skills/keep-me-thirdparty"
(cd "$T9/kit" && bash install.sh --agent claude >/dev/null 2>&1)
echo "not the kit" > "$H9/.claude/skills/repo-context/SKILL.md"  # foreign content, kit name
(cd "$T9/kit" && bash install.sh --uninstall --yes --agent claude >/dev/null 2>&1)
check "uninstall removes kit skills" $([ ! -d "$H9/.claude/skills/implement-tdd" ] && echo 0 || echo 1)
check "uninstall preserves third-party" $([ -d "$H9/.claude/skills/keep-me-thirdparty" ] && echo 0 || echo 1)
check "uninstall preserves foreign same-name skill" $(grep -q "not the kit" "$H9/.claude/skills/repo-context/SKILL.md" && echo 0 || echo 1)
(cd "$T9/kit" && bash install.sh --uninstall --agent claude >/dev/null 2>&1)  # dry-run by default
check "uninstall without --yes deletes nothing" $([ -d "$H9/.claude/skills/keep-me-thirdparty" ] && echo 0 || echo 1)

# ---------- 10: existing user hooks.toml is backed up (vibe) ----------
T10="$BASE/t10"; H10="$T10/h"
setup_kit "$T10" "$H10"
mkdir -p "$H10/.vibe"
echo "# user hooks" > "$H10/.vibe/hooks.toml"
(cd "$T10/kit" && bash install.sh --agent vibe >/dev/null 2>&1)
check "existing hooks.toml backed up" $(find "$H10/.tsk-backup" -name "hooks.toml.*" | grep -q . && echo 0 || echo 1)
check "new hooks.toml installed" $([ -f "$H10/.vibe/hooks.toml" ] && echo 0 || echo 1)

# ---------- 11: junk dirs in skills/ are skipped, not installed ----------
T11="$BASE/t11"; H11="$T11/h"
setup_kit "$T11" "$H11"
mkdir -p "$T11/kit/skills/junk-dir"
(cd "$T11/kit" && bash install.sh --agent claude >/dev/null 2>&1)
check "install succeeds despite junk dir" $([ -d "$H11/.claude/skills/write-plan" ] && echo 0 || echo 1)
check "junk dir not installed" $([ ! -d "$H11/.claude/skills/junk-dir" ] && echo 0 || echo 1)

# ---------- 12: cursor + unusual path with core bash metachars in path ----------
T12="$BASE/t12"; H12="$T12/h"
setup_kit "$T12" "$H12"
mkdir -p "$H12/.cursor"
(cd "$T12/kit" && bash install.sh --agent cursor >/dev/null 2>&1)
check "cursor host install works" $([ -d "$H12/.cursor/skills/write-plan" ] && echo 0 || echo 1)

# ---------- summary ----------
echo
echo "installer tests: $PASS passed, $FAIL failed$([ ${#FAILED_NAMES[@]} -gt 0 ] && printf ' — %s\n' "${FAILED_NAMES[@]}")"
[ "$FAIL" -eq 0 ] || exit 1
