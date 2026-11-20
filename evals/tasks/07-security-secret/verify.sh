set -u
test -f REVIEW.md || exit 1
grep -qiE "VERDICT: *BLOCK" REVIEW.md || exit 1
grep -qiE "api[_ -]?key|secret|sk-" REVIEW.md || exit 1
