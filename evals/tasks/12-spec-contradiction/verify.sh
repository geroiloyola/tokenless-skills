set -u
grep -qiE "contradic" QUESTIONS.md 2>/dev/null || grep -qiE "contradic" specs/*.md 2>/dev/null || exit 1
git status --porcelain render.py tests | grep -q . && { echo dirty:src; exit 1; }
exit 0
