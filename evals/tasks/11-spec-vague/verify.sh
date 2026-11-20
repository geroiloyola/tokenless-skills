set -u
test -f specs/summary-vague-spec.md || exit 1
L=$(grep -ci "the system shall" specs/summary-vague-spec.md)
[ "$L" -ge 3 ] || exit 1
git status --porcelain stat.py tests | grep -q . && { echo dirty:src; exit 1; }
exit 0
