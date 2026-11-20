#!/usr/bin/env bash
# tokenless-skills — install with zero args (auto-detect) or pick hosts/scopes
# Zero-args: installs to all hosts with existing config dirs (user scope)
#    ./install.sh                                         # auto
#    curl -fsSL .../install.sh | bash                    # same
# Pick: ./install.sh --agent claude,vibe --scope project
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# === ARG PARSING ===========================================================
SCOPE="user"
AGENTS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --agent) AGENTS="$(echo "$2" | tr ',' ' ')"; shift 2 ;;
    --scope) SCOPE="$2"; shift 2 ;;
    *) echo "Usage: $0 [--agent <comma,list>] [--scope user|project]"; exit 1 ;;
  esac
done

# === ALL HOSTS WE KNOW =====================================================
ALL_HOSTS=(
  "vibe|$HOME/.vibe/skills|.vibe/skills"
  "claude|$HOME/.claude/skills|.claude/skills"
  "codex|$HOME/.codex/skills|.codex/skills"
  "opencode|$HOME/.config/opencode/skills|.opencode/skills"
  "gemini|$HOME/.gemini/skills|.gemini/skills"
  "antigravity|$HOME/.gemini/config/skills|.agents/skills"
  "cursor|$HOME/.cursor/skills|.cursor/skills"
  "agents|$HOME/.agents/skills|.agents/skills"
  "opencat|$HOME/.opencat/skills|.opencat/skills"
)

# === DETECT OR SELECT HOSTS =================================================
TARGETS=()
for row in "${ALL_HOSTS[@]}"; do
  IFS='|' read -r id user_dir proj_dir <<< "$row"
  # Filter by --agent
  if [ -n "$AGENTS" ]; then
    echo "$AGENTS" | grep -qiw "$id" || continue
  else
    # Auto: for project scope include all hosts; for user only hosts with config root
    if [ "$SCOPE" = "user" ]; then
      parent_dir="${user_dir%/*}"
      eval parent_dir="$parent_dir"
      [ -d "$parent_dir" ] || continue
    fi
  fi
  # Expand ~
  eval ud="$user_dir"
  eval pd="$proj_dir"
  if [ "$SCOPE" = "user" ]; then TARGETS+=("$id|$ud");
  else TARGETS+=("$id|${PWD}/$pd"); fi
done

[ ${#TARGETS[@]} -eq 0 ] && { echo "❌ No hosts detected or matched."; exit 1; }

# === RULES BLOCK ===========================================================
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

seed_rules() {
  local file="$1";
  grep -qF "tokenless-skills managed block" "$file" 2>/dev/null && return
  printf '\n%s\n' "$RULES" >> "$file"
}

# === CORE INSTALL =========================================================
installed=0
for row in "${TARGETS[@]}"; do
  IFS='|' read -r id dest <<< "$row"
  mkdir -p "$dest"
  for d in "$KIT"/skills/*/; do
    name="$(basename "$d")"
    rm -rf "${dest%/}/$name"
    cp -R "$d" "${dest%/}/$name"
  done
  echo "  ✅ $id → $dest"
  installed=$((installed + 1))

  # --- Vibe extras (hooks, agents, qa) live in Vibe root ---
  if [ "$id" = "vibe" ]; then
    VROOT="${dest%/skills}"
    mkdir -p "$VROOT/agents" "$VROOT/scripts"
    sed "s|{{KIT_DIR}}|$VROOT|g" "$KIT/extras/vibe/guard.py" > "$VROOT/scripts/guard.py" 2>/dev/null || cp "$KIT/extras/vibe/guard.py" "$VROOT/scripts/guard.py"
    sed "s|{{KIT_DIR}}|$VROOT|g" "$KIT/extras/vibe/qa.py"   > "$VROOT/scripts/qa.py"   2>/dev/null || cp "$KIT/extras/vibe/qa.py"   "$VROOT/scripts/qa.py"
    sed "s|{{KIT_DIR}}|$VROOT|g" "$KIT/extras/vibe/hooks.toml" > "$VROOT/hooks.toml"
    cp "$KIT/extras/vibe/agents/"*.toml "$VROOT/agents/" 2>/dev/null || true
    cp "$KIT/extras/vibe/qa.json.example" "$VROOT/" 2>/dev/null || true
    echo "  🔧  Vibe extras → $VROOT"
  fi

  # --- Seed global rules (user scope only) ---
  if [ "$SCOPE" = "user" ]; then
    case "$id" in
      vibe)    seed_rules "$HOME/.vibe/AGENTS.md" ;;
      claude)  seed_rules "$HOME/.claude/CLAUDE.md" ;;
      codex)   seed_rules "$HOME/.codex/AGENTS.md" ;;
      opencode) seed_rules "$HOME/.config/opencode/AGENTS.md" ;;
      gemini)  seed_rules "$HOME/.gemini/GEMINI.md" ;;
    esac
  fi
done

# === SHARED MEMORY =========================================================
mkdir -p "$HOME/.agents/memory"
for f in lessons.md instincts.md; do
  [ -f "$HOME/.agents/memory/$f" ] || printf '# %s — one entry per line\n' "${f%.md}" > "$HOME/.agents/memory/$f"
done
echo "  💾 ~/.agents/memory/{lessons,instincts}.md shared across agents"

# === DONE =================================================================
echo "✅ tokenless-skills installed to $installed host(s). Restart your agent(s) to use."
