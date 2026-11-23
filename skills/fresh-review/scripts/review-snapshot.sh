#!/usr/bin/env bash
# freeze <base-ref> <empty-directory> | check <snapshot-directory>
set -euo pipefail

fail() { echo "$*" >&2; exit 1; }
case "${1-}:$#" in
  freeze:3) snapshot=$3 ;;
  check:2) snapshot=$2 ;;
  *) fail 'usage: review-snapshot.sh freeze <base-ref> <empty-dir> | check <dir>' ;;
esac

snapshot=$(cd -- "$snapshot" && pwd -P)
root=$(git rev-parse --show-toplevel)
cd -- "$root"
root=$(pwd -P)
case "$snapshot/" in "$root/"*) fail 'snapshot directory must be outside the worktree' ;; esac
head=$(git rev-parse --verify HEAD)
[ -z "$(git ls-files --unmerged)" ] || fail 'resolve unmerged files first'
[ -z "$(git ls-files --others --exclude-standard)" ] || fail 'stage intended untracked files before review'
while IFS= read -r -d '' path; do
  git --literal-pathspecs diff --quiet -- "$path" || fail "stage or unstage partially staged file: $path"
done < <(git diff --cached --no-renames --name-only -z "$head" --)

diff_from_base() {
  git diff --binary --no-color --no-ext-diff --no-textconv --no-renames --no-relative "$1" --
}

if [ "$1" = freeze ]; then
  # Refuse reuse: a previous verdict only applies to its original snapshot.
  for file in root head base review.diff; do
    [ ! -e "$snapshot/$file" ] && [ ! -L "$snapshot/$file" ] || fail 'use a new snapshot directory'
  done
  base_ref=$(git rev-parse --verify --end-of-options "$2^{commit}")
  base=$(git merge-base "$base_ref" "$head")
  diff_from_base "$base" > "$snapshot/review.diff"
  printf '%s\n' "$root" > "$snapshot/root"
  printf '%s\n' "$head" > "$snapshot/head"
  printf '%s\n' "$base" > "$snapshot/base"
  printf '%s\n' "$snapshot/review.diff"
else
  [ "$(<"$snapshot/root")" = "$root" ] || fail 'snapshot belongs to another worktree'
  [ "$(<"$snapshot/head")" = "$head" ] || fail 'HEAD changed; run fresh-review again'
  base=$(git rev-parse --verify --end-of-options "$(<"$snapshot/base")^{commit}")
  diff_from_base "$base" | cmp -s - "$snapshot/review.diff" || fail 'diff changed; run fresh-review again'
fi
