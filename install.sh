#!/bin/bash
# Install skills/* into an agent skills dir. Usage: ./install.sh [claude] [codex] [project]
# No args = every host config dir that already exists, plus ./.agents/skills.
set -u
cd "$(dirname "$0")" || exit 1
targets=""
add() { case " $targets " in *" $1 "*) ;; *) targets="$targets $1" ;; esac; }
for arg in "$@"; do
  case "$arg" in
    claude) add "$HOME/.claude/skills" ;;
    codex)  add "$HOME/.codex/skills" ;;
    project|agents) add "$PWD/.agents/skills" ;;
    *) echo "unknown target '$arg' (use: claude codex project)"; exit 2 ;;
  esac
done
if [ -z "$targets" ]; then
  if [ -d "$HOME/.claude" ]; then add "$HOME/.claude/skills"; fi
  if [ -d "$HOME/.codex" ]; then add "$HOME/.codex/skills"; fi
  add "$PWD/.agents/skills"
fi
rc=0
for dest in $targets; do
  mkdir -p "$dest" || rc=1
  for src in skills/*/; do
    name=$(basename "$src")
    [ -f "${src}SKILL.md" ] || continue
    if [ -e "${dest%/}/$name" ]; then
      mv "${dest%/}/$name" "${dest%/}/$name.bak.$(date +%s)" || rc=1
    fi
    cp -R "${src%/}" "${dest%/}/$name" || rc=1
    echo "installed $name -> ${dest%/}/$name"
  done
done
echo "done"; exit "$rc"
