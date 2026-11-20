#!/usr/bin/env bash
# tokenless-skills installer
#
# Usage:
#   ./install.sh                          # auto-detect hosts (user scope)
#   ./install.sh --scope project          # project-only: universal .agents/skills
#   ./install.sh --agent claude,codex     # only these hosts
#   ./install.sh --uninstall [--yes]      # conservative uninstall (dry-run by default)
#   ./install.sh --dry-run                # show what would happen, write nothing
#   ./install.sh --help
#
# Non-destructive by design:
#   - overwriting an existing kit-named skill first moves it to .tsk-backup/
#   - third-party skills with other names are never touched
#   - replacement is staged then swapped, so a failed copy leaves the old dir intact
set -euo pipefail
shopt -s nullglob

VERSION="1.0.0"
KNOWN_HOST_IDS=" vibe claude codex opencode gemini antigravity cursor agents opencat "
AGENTS=""
SCOPE="user"
DRY_RUN=0
UNINSTALL=0
ASSUME_YES=0
SCRIPT_FILE="${BASH_SOURCE[0]:-}"

# === KIT LOCATION ==========================================================
# Works for ./install.sh and bash path/to/install.sh. Fails with an
# actionable message for `curl | bash` (stdin), which has no kit directory.
if [ -n "$SCRIPT_FILE" ] && [ -f "$SCRIPT_FILE" ]; then
  KIT="$(cd "$(dirname "$SCRIPT_FILE")" && pwd)"
elif [ -f "$PWD/install.sh" ] && [ -d "$PWD/skills" ]; then
  KIT="$PWD"
else
  cat >&2 <<'EOF'
❌ Cannot locate the tokenless-skills kit.

`curl ... | bash` is not supported (the installer needs the repository files).
Install like this instead:

  git clone --depth 1 --branch v1.0.0 https://github.com/geroiloyola/tokenless-skills.git
  cd tokenless-skills && ./install.sh            # --branch takes a tag or commit
EOF
  exit 1
fi

if [ ! -d "$KIT/skills" ]; then
  echo "❌ $KIT/skills not found — run the installer from a tokenless-skills checkout." >&2
  exit 1
fi

# === HELP ==================================================================
usage() {
  cat <<EOF
tokenless-skills $VERSION — install lightweight, portable agent skills.

  ./install.sh [--scope user|project] [--agent host,host] [--dry-run]
  ./install.sh --uninstall [--dry-run] [--yes] [--agent ...]

Flags:
  --agent / --host <csv>   Restrict to hosts: vibe, claude, codex, opencode,
                           gemini, antigravity, cursor, agents, opencat
  --scope <user|project>   user: \$HOME dirs (default). project: current repo
  --uninstall              Remove kit-owned skills only (never third-party).
                           Dry-run by default; add --yes to apply.
  --dry-run                Print actions, change nothing
  --yes                    Apply uninstall without confirmation
  -h, --help               This help

Backups of replaced skills go to \$HOME/.tsk-backup/ (user scope) or
./.tsk-backup/ (project scope), one timestamped directory per overwrite.
Backups are never auto-deleted; prune .tsk-backup manually when convenient.
EOF
}
case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

# === ARG PARSING ===========================================================
while [ $# -gt 0 ]; do
  case "$1" in
    --agent|--host)
      [ $# -ge 2 ] || { echo "❌ $1 needs a value" >&2; exit 2; }
      AGENTS="$(echo "$2" | tr ',' ' ')"
      # validate host ids up front; typos must not be silently dropped
      checked="" a=""
      for a in $AGENTS; do
        case "$KNOWN_HOST_IDS" in
          *" $a "*) checked="$checked $a" ;;
          *) echo "⚠️  '$a' is not a recognized host id — ignored." >&2
             echo "    known ids:$KNOWN_HOST_IDS" >&2 ;;
        esac
      done
      if [ -z "$checked" ] && [ -n "$AGENTS" ]; then
        echo "❌ no recognized host id in '$2' (known:$KNOWN_HOST_IDS)" >&2
        exit 2
      fi
      AGENTS="$(echo "$checked" | xargs)"
      shift 2 ;;
    --scope)
      [ $# -ge 2 ] || { echo "❌ --scope needs a value" >&2; exit 2; }
      case "$2" in user|project) SCOPE="$2" ;; *) echo "❌ invalid --scope '$2' (use user|project)" >&2; exit 2 ;; esac
      shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --yes) ASSUME_YES=1; shift ;;
    *) echo "❌ unknown argument '$1'" >&2; usage >&2; exit 2 ;;
  esac
done

# === HOST TABLE: id|user_skills_dir|project_skills_dir|rules_file ==========
# rules_file: the per-host global instruction file the installer appends its
# managed memory rules block to. Empty = the host has no documented global
# instruction file we can seed; those hosts get a notice instead (see README).
# Expanded with bash parameter expansion (no eval, no sed metachar issues).
ALL_HOSTS=(
  "vibe|$HOME/.vibe/skills|$PWD/.vibe/skills|$HOME/.vibe/AGENTS.md"
  "claude|$HOME/.claude/skills|$PWD/.claude/skills|$HOME/.claude/CLAUDE.md"
  "codex|$HOME/.codex/skills|$PWD/.codex/skills|$HOME/.codex/AGENTS.md"
  "opencode|$HOME/.config/opencode/skills|$PWD/.opencode/skills|$HOME/.config/opencode/AGENTS.md"
  "gemini|$HOME/.gemini/skills|$PWD/.gemini/skills|$HOME/.gemini/GEMINI.md"
  "antigravity|$HOME/.gemini/config/skills|$PWD/.agents/skills|$HOME/.gemini/config/AGENTS.md"
  "cursor|$HOME/.cursor/skills|$PWD/.cursor/skills|"
  "agents|$HOME/.agents/skills|$PWD/.agents/skills|$HOME/.agents/AGENTS.md"
  "opencat|$HOME/.opencat/skills|$PWD/.opencat/skills|"
)

RULES='<!-- BEGIN tokenless-skills managed block -->
## Memory
- At session start, read ~/.agents/memory/lessons.md and apply its rules.
- Read ~/.agents/memory/instincts.md only if file has <=40 lines, when:/scope: match, not expired.
- When corrected: remember-correction. After a non-obvious pattern works: learn-instinct.

## Quality
- Never declare work done without real verification output (tests/typecheck/build).
- No production code without a failing test first (spikes are the exception).

## Workflow
- Respect repo AGENTS.md over this block.
- Skills are host-agnostic; invoke by your agent’s syntax (/, $, @, etc.).
<!-- END tokenless-skills managed block -->'

BACKUP_DIR=""; # set per scope below
NOTICE_HOSTS=""

resolve_targets() {
  TARGETS=()
  local row id user_dir proj_dir rules_file
  for row in "${ALL_HOSTS[@]}"; do
    IFS='|' read -r id user_dir proj_dir rules_file <<< "$row"
    if [ -n "$AGENTS" ]; then
      echo "$AGENTS" | grep -qiw "$id" || continue
    else
      # user scope, no --agent: only hosts whose config root already exists
      if [ "$SCOPE" = "user" ]; then
        [ -d "${user_dir%/skills}" ] || continue
      else
        # project scope, no --agent: only the universal .agents/skills dir.
        # Committing nine host trees to a repo is noise; pass --agent to add more.
        [ "$id" = "agents" ] || continue
      fi
    fi
    if [ "$SCOPE" = "user" ]; then
      TARGETS+=("$id|$user_dir|$rules_file")
    else
      TARGETS+=("$id|$proj_dir|$rules_file")
    fi
  done
}

# === UNINSTALL =============================================================
# Conservative: only the 14 kit skill names, and only if the installed
# SKILL.md frontmatter declares name: <name>. Never touches anything else.
kit_names() {
  local d
  for d in "$KIT"/skills/*/; do echo "$(basename "$d")"; done
}

uninstall_host() {
  local dest="$1" name dir removed=0
  local bdir ts
  for name in $(kit_names); do
    dir="${dest%/}/$name"
    [ -d "$dir" ] || continue
    if [ -L "$dir" ]; then
      echo "  ↳ $name is a symlink — left in place (install.sh never follows it)."
      continue
    fi
    # ownership proof: frontmatter must name this skill exactly
    if ! head -5 "$dir/SKILL.md" 2>/dev/null | grep -q "^name: $name\$"; then
      echo "  ⚠️  $name exists but is not the kit's original — left in place."
      continue
    fi
    # integrity check: identical to the kit's copy → safe to remove outright.
    # Anything else (user-customized or installed from an older kit version)
    # is MOVED to .tsk-backup/, never deleted. Conservative over destructive.
    local customized=0
    if ! diff -qr "$KIT/skills/$name" "$dir" >/dev/null 2>&1; then
      customized=1
    fi
    if [ "$customized" -eq 1 ]; then
      if [ "$DRY_RUN" -eq 0 ]; then
        [ "$ASSUME_YES" -eq 1 ] || { echo "  ⚠️  $name is customized or an older kit version"; removed=$((removed + 1)); continue; }
        ts="$(date +%Y%m%d-%H%M%S)-$$"
        [ -d "$BACKUP_DIR" ] || mkdir -p "$BACKUP_DIR"
        bdir="$BACKUP_DIR/$name-$ts"
        while [ -e "$bdir" ]; do bdir="$bdir-x"; done
        if mv "$dir" "$bdir" && [ -f "$bdir/SKILL.md" ]; then
          echo "  ⚠️  $name is customized or an older kit version — moved to $bdir (not deleted)."
        else
          echo "❌ backup verification failed for $name; aborting uninstall (no data touched)." >&2
          exit 1
        fi
      else
        echo "  backup + remove $name (customized or older kit version)"
      fi
      removed=$((removed + 1))
      continue
    fi
    echo "  remove $name (unmodified)"
    removed=$((removed + 1))
    if [ "$DRY_RUN" -eq 0 ] && [ "$ASSUME_YES" -eq 1 ]; then
      rm -rf "$dir"
    fi
  done
  [ "$removed" -eq 0 ] && echo "  (no kit-owned skills found)"
  return 0
}

run_uninstall() {
  # same backup location policy as install: user scope → $HOME, project → cwd
  if [ "$SCOPE" = "user" ]; then BACKUP_DIR="$HOME/.tsk-backup"; else BACKUP_DIR="$PWD/.tsk-backup"; fi
  resolve_targets
  for row in "${TARGETS[@]}"; do
    IFS='|' read -r id dest _ <<< "$row"
    [ -d "$dest" ] || { echo "  - $id: $dest absent, skipping"; continue; }
    echo "→ $id ($dest)"
    uninstall_host "$dest"
  done
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY-RUN complete. Apply with: install.sh --uninstall --yes"
  elif [ "$ASSUME_YES" -ne 1 ]; then
    echo "Nothing deleted. Re-run with --yes to apply."
  fi
}

# === INSTALL HELPERS =======================================================
backup_existing() {
  # $1 = existing skill dir (kit-named). Move to timestamped backup.
  local existing="$1" ts bdir
  ts="$(date +%Y%m%d-%H%M%S)-$$"
  [ -d "$BACKUP_DIR" ] || mkdir -p "$BACKUP_DIR"
  bdir="$BACKUP_DIR/${existing##*/}-$ts"
  # collision-safe: never mv INTO an existing backup dir (mv would nest)
  while [ -e "$bdir" ]; do bdir="$bdir-x"; done
  mv "$existing" "$bdir"
  echo "     ↳ previous version backed up → $bdir" >&2
}

install_host() {
  local id="$1" dest="$2" staged_name="$3" src="$4"
  # stage (atomic-ish): copy first, swap second. If the copy fails, the
  # existing skill (or absence) is untouched.
  local tmp
  tmp="$(mktemp -d)"
  cp -R "$src" "$tmp/$staged_name" || { rm -rf "$tmp"; echo "❌ staging failed for $id/$staged_name" >&2; return 1; }
  [ -f "$tmp/$staged_name/SKILL.md" ] || { rm -rf "$tmp"; echo "❌ staged skill missing SKILL.md: $staged_name" >&2; return 1; }
  [ -d "$dest" ] || { [ "$DRY_RUN" -eq 1 ] || mkdir -p "$dest"; }
  if [ -e "${dest%/}/$staged_name" ]; then
    [ "$DRY_RUN" -eq 1 ] || backup_existing "${dest%/}/$staged_name"
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "     install $staged_name → $dest"
  else
    rm -rf "${dest%/}/$staged_name.tmp-old" 2>/dev/null || true
    [ -e "${dest%/}/$staged_name" ] && mv "${dest%/}/$staged_name" "${dest%/}/$staged_name.tmp-old"
    mv "$tmp/$staged_name" "${dest%/}/$staged_name"
    [ -e "${dest%/}/$staged_name.tmp-old" ] && rm -rf "${dest%/}/$staged_name.tmp-old"
    [ -f "${dest%/}/$staged_name/SKILL.md" ] || { echo "❌ verify failed after swap: $staged_name" >&2; return 1; }
  fi
  rm -rf "$tmp"
}

seed_rules() {
  local file="$1"
  [ -n "$file" ] || return 0
  if grep -qF "tokenless-skills managed block" "$file" 2>/dev/null; then return 0; fi
  [ "$DRY_RUN" -eq 1 ] && { echo "     rules → $file"; return 0; }
  mkdir -p "$(dirname "$file")"
  printf '\n%s\n' "$RULES" >> "$file"
}

# bash template expansion without sed metachar issues: {{KIT_DIR}} and
# {{HOME}} replaced via bash parameter substitution (safe for &, |, /, etc.)
render_template() { # $1=src $2=outfile $3=kit_dir_value
  local content
  content="$(cat "$1")"
  content="${content//\{\{KIT_DIR\}\}/$3}"
  content="${content//\{\{HOME\}\}/$HOME}"
  printf '%s\n' "$content" > "$2"
}

# === INSTALL ===============================================================
run_install() {
  resolve_targets
  [ ${#TARGETS[@]} -eq 0 ] && { echo "❌ No hosts detected or matched. Use --agent to pick ones explicitly from:$KNOWN_HOST_IDS" >&2; exit 1; }

  if [ "$SCOPE" = "user" ]; then BACKUP_DIR="$HOME/.tsk-backup"; else BACKUP_DIR="$PWD/.tsk-backup"; fi

  # Build the skills list ONCE and require it to be non-empty (nullglob means
  # an unmatched pattern yields nothing — never a literal '*'). Only dirs with
  # a real SKILL.md are installable; junk dirs are skipped with a warning.
  local skills=()
  local d
  for d in "$KIT"/skills/*/; do skills+=("$d"); done
  if [ ${#skills[@]} -eq 0 ]; then
    echo "❌ no skills found in $KIT/skills — refusing to install anything." >&2
    exit 1
  fi
  warn_junk=""
  local valid=()
  for src in "${skills[@]}"; do
    if [ -f "${src%/}/SKILL.md" ]; then valid+=("$src"); else
      warn_junk+=" $(basename "$src")"
    fi
  done
  [ -n "$warn_junk" ] && echo "⚠️  skipping (no SKILL.md):$warn_junk" >&2
  skills=("${valid[@]}")
  if [ ${#skills[@]} -eq 0 ]; then
    echo "❌ none of the entries in $KIT/skills contain a SKILL.md — nothing to install." >&2
    exit 1
  fi

  # Snapshot originals to restore if a host fails mid-run
  local installed=0 row id dest rules_file name
  for row in "${TARGETS[@]}"; do
    IFS='|' read -r id dest rules_file <<< "$row"
    echo "→ $id → $dest"
    local failed=0
    for src in "${skills[@]}"; do
      name="$(basename "$src")"
      install_host "$id" "$dest" "$name" "$src" || failed=1
    done
    [ "$failed" -eq 1 ] && { echo "❌ install to $id failed; nothing else was removed pre-swap." >&2; exit 1; }
    installed=$((installed + 1))
    echo "  ✅ $id ($installed/${#TARGETS[@]})"

    if [ "$DRY_RUN" -eq 0 ] && [ "$id" = "vibe" ]; then
      local VROOT="${dest%/skills}"
      mkdir -p "$VROOT/agents" "$VROOT/scripts"
      if [ -f "$VROOT/hooks.toml" ]; then
        [ -d "$BACKUP_DIR" ] || mkdir -p "$BACKUP_DIR"
        cp "$VROOT/hooks.toml" "$BACKUP_DIR/hooks.toml.$(date +%Y%m%d-%H%M%S)"
        echo "  🔧  existing hooks.toml backed up; the new file replaces it — merge manually if you had custom hooks."
      fi
      render_template "$KIT/extras/vibe/guard.py" "$VROOT/scripts/guard.py" "$VROOT"
      render_template "$KIT/extras/vibe/qa.py" "$VROOT/scripts/qa.py" "$VROOT"
      render_template "$KIT/extras/vibe/hooks.toml" "$VROOT/hooks.toml" "$VROOT"
      cp "$KIT/extras/vibe/agents/"*.toml "$VROOT/agents/" 2>/dev/null || true
      cp "$KIT/extras/vibe/qa.json.example" "$VROOT/" 2>/dev/null || true
      echo "  🔧  Vibe extras → $VROOT"
    fi

    if [ "$SCOPE" = "user" ]; then
      if [ -n "$rules_file" ]; then
        seed_rules "$rules_file"
      else
        NOTICE_HOSTS+="$id "
      fi
    fi
  done

  if [ "$SCOPE" = "user" ] && [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$HOME/.agents/memory"
    for f in lessons.md instincts.md; do
      [ -f "$HOME/.agents/memory/$f" ] || printf '# %s — one entry per line\n' "${f%.md}" > "$HOME/.agents/memory/$f"
    done
    echo "  💾 ~/.agents/memory/{lessons,instincts}.md shared across agents"
  fi

  if [ -n "$NOTICE_HOSTS" ]; then
    echo "⚠️  $NOTICE_HOSTS: no documented global instruction file, so the managed"
    echo "    memory-rules block was NOT installed there. Skills work without it,"
    echo "    but lessons/instincts (remember-correction, learn-instinct) must be"
    echo "    referenced manually in that host's instruction file. See docs/HOSTS.md."
  fi
  echo "✅ tokenless-skills installed to $installed host(s). Restart your agent(s) to use."
}

# === MAIN ==================================================================
if [ "$UNINSTALL" -eq 1 ]; then
  run_uninstall
else
  run_install
fi
