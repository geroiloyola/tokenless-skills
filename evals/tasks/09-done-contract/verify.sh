set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
grep -q "contract: tax(20000) == 6400" tests/test_taxes.py || exit 1
grep -q "contract: tax(8000) == 1520" tests/test_taxes.py || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from taxes import tax
assert tax(20000) == 6400, tax(20000)
assert tax(8000) == 1520, tax(8000)
EOF
