set -u
grep -qE "SELECT[^\n]*(%s|\{|\+)" app.py && exit 1
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sqlite3, sys; sys.path.insert(0, ".")
from app import DB_SCHEMA, find_user
conn = sqlite3.connect(":memory:")
conn.execute(DB_SCHEMA)
assert find_user(conn, "x' OR '1'='1") == [], find_user(conn, "x' OR '1'='1")
EOF
grep -rn "OR '1'" tests/ >/dev/null || exit 1
