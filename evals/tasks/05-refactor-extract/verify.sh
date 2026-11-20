set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from invoice import calculate_total, line_subtotal
assert line_subtotal({"qty": 2, "unit_cents": 500, "discount_cents": 100}) == 900
assert line_subtotal({"qty": 1, "unit_cents": 10, "discount_cents": 500}) == 0
assert calculate_total([{"qty": 2, "unit_cents": 500, "discount_cents": 100}]) == 900
EOF
grep -q "def line_subtotal" invoice.py || exit 1
