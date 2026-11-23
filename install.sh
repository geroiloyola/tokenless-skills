#!/bin/bash
# Install skills/* into an agent skills dir. Usage: ./install.sh [claude] [codex] [project]
# No args = every host config dir that already exists, plus ./.agents/skills.
set -e
project_dir=$PWD
source_dir=$(cd -- "$(dirname -- "$0")" && pwd)
targets=()
add() {
  local dest
  for dest in "${targets[@]}"; do
    [ "$dest" != "$1" ] || return 0
  done
  targets+=("$1")
}
for arg in "$@"; do
  case "$arg" in
    claude) add "$HOME/.claude/skills" ;;
    codex)  add "$HOME/.codex/skills" ;;
    project|agents) add "$project_dir/.agents/skills" ;;
    *) echo "unknown target '$arg' (use: claude codex project)" >&2; exit 2 ;;
  esac
done
if [ "$#" -eq 0 ]; then
  if [ -d "$HOME/.claude" ]; then add "$HOME/.claude/skills"; fi
  if [ -d "$HOME/.codex" ]; then add "$HOME/.codex/skills"; fi
  add "$project_dir/.agents/skills"
fi
for dest in "${targets[@]}"; do
  mkdir -p -- "$dest"
  backup=''
  for src in "$source_dir"/skills/*/; do
    [ -f "${src}SKILL.md" ] || continue
    name=${src%/}
    name=${name##*/}
    target=$dest/$name
    if [ -e "$target" ] || [ -L "$target" ]; then
      if [ -z "$backup" ]; then
        backup=$(mktemp -d "$dest/../.tokenless-backup.XXXXXX")
        echo "backups -> $backup"
      fi
      mv -- "$target" "$backup/$name"
    fi
    cp -R -- "${src%/}" "$target"
    echo "installed $name -> $target"
  done
done
echo "done"
