set -u
python check.py >/dev/null 2>&1 || exit 1
N=$(grep -rc "def test_" tests/ | awk -F: '{s+=$2} END {print s}')
[ "$N" -ge 2 ] || exit 1
