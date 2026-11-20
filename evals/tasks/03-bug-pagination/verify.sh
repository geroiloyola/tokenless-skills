set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from pager import paginate
items = list(range(25))
assert paginate(items, 1, 10) == items[0:10], paginate(items, 1, 10)
assert paginate(items, 2, 10) == items[10:20], paginate(items, 2, 10)
assert paginate(items, 3, 10) == items[20:25], paginate(items, 3, 10)
EOF
git diff --name-only -- tests | grep -q . || exit 1
