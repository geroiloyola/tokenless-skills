set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from shop import Cart
c = Cart(); c.add("x", 5)
assert c.apply_discount(10) == 5, c.apply_discount(10)
c2 = Cart(); c2.add("x", 999)
p = c2.apply_discount(0)
assert p == 999, p
EOF
grep -rn "apply_discount" tests/ >/dev/null || exit 1
