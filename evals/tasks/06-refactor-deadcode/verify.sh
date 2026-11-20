set -u
grep -q "unused_stats" report.py && exit 1
grep -q "report.dbg" report.py && exit 1
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from report import render
assert render([{"name": "a", "qty": 2}]) == "a: 2"
EOF
