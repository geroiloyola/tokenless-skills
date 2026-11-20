set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from cache import Cache
c = Cache(); c.put("user", "a", 1)
c.invalidate("user", "a")
assert c.by_kind("user") == [], c.by_kind("user")
assert c.get("user", "a") is None
EOF
git diff --name-only -- tests | grep -q . || exit 1
