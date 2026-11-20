#!/usr/bin/env python3
"""Materialize preregistered benchmark fixtures (Fase 2, never changed by hand).

Usage:
    python3 evals/tasks/gen_fixtures.py --dest DIR [--task 03-bug-pagination]
Creates DIR/<task>/work as a small git repo. Committed henceforth; tasks are
frozen in evals/PREREGISTRATION.md before any benchmark run.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# (task, {(relpath): content}) — the initial state of each fixture repo.
FIXTURES: dict[str, dict[str, str]] = {}

FIXTURES["01-tdd-discount"] = {
    "shop.py": '''class Cart:
    def __init__(self):
        self._cents = 0

    def add(self, name, price_cents):
        self._cents += price_cents

    def total(self):
        return self._cents
''',
    "tests/__init__.py": "",
    "tests/test_shop.py": '''import unittest
from shop import Cart

class TestCart(unittest.TestCase):
    def test_total_sums_adds(self):
        c = Cart()
        c.add("x", 500)
        c.add("y", 250)
        self.assertEqual(c.total(), 750)

    def test_empty_total(self):
        self.assertEqual(Cart().total(), 0)
''',
}

FIXTURES["02-tdd-slugify"] = {
    "slug.py": '''def slugify(text):
    """Starter: spaces only. Spec requires accents, punctuation, collapse."""
    return text.strip().lower().replace(" ", "-")
''',
    "tests/__init__.py": "",
    "tests/test_slug.py": '''import unittest
from slug import slugify

class TestSlug(unittest.TestCase):
    def test_spaces(self):
        self.assertEqual(slugify("hello world"), "hello-world")
''',
}

FIXTURES["03-bug-pagination"] = {
    "pager.py": '''def paginate(items, page=1, size=10):
    """Return page of items. Callers pass 1-based page numbers."""
    return items[page * size:(page + 1) * size]
''',
    "tests/__init__.py": "",
    "tests/test_pager.py": '''import unittest
from pager import paginate

class TestPager(unittest.TestCase):
    def test_page_returns_slices(self):
        items = list(range(25))
        self.assertEqual(paginate(items, 1, 10), items[10:20])
''',
}

FIXTURES["04-bug-cache"] = {
    "cache.py": '''class Cache:
    """Value cache with a by-kind derived index."""

    def __init__(self):
        self._data = {}
        self._by_kind = {}

    def put(self, kind, key, value):
        self._data[(kind, key)] = value
        self._by_kind.setdefault(kind, []).append(key)

    def get(self, kind, key):
        return self._data.get((kind, key))

    def invalidate(self, kind, key):
        # BUG: the derived index keeps a stale reference.
        self._data.pop((kind, key), None)

    def by_kind(self, kind):
        return [self._data[(kind, k)] for k in self._by_kind.get(kind, [])]
''',
    "tests/__init__.py": "",
    "tests/test_cache.py": '''import unittest
from cache import Cache

class TestCache(unittest.TestCase):
    def test_valid_entry_is_returned(self):
        c = Cache()
        c.put("user", "a", 1)
        self.assertEqual(c.get("user", "a"), 1)
''',
}

FIXTURES["05-refactor-extract"] = {
    "invoice.py": '''def calculate_total(lines):
    """lines: list of dicts {qty, unit_cents, discount_cents}."""
    total = 0
    for ln in lines:
        gross = ln["qty"] * ln["unit_cents"]
        subtotal = gross - ln["discount_cents"]
        if subtotal < 0:
            subtotal = 0
        total += subtotal
    for ln in lines:  # preview pass repeats the same arithmetic
        gross = ln["qty"] * ln["unit_cents"]
        preview = gross - ln["discount_cents"]
        if preview < 0:
            preview = 0
        assert preview == subtotal
    return total
''',
    "tests/__init__.py": "",
    "tests/test_invoice.py": '''import unittest
from invoice import calculate_total

class TestInvoice(unittest.TestCase):
    def test_totals(self):
        lines = [{"qty": 2, "unit_cents": 500, "discount_cents": 100}]
        self.assertEqual(calculate_total(lines), 900)
''',
}

FIXTURES["06-refactor-deadcode"] = {
    "report.py": '''import os

def render(rows):
    """rows: list of dicts {name, qty}."""
    out = "\\n".join(f"{r['name']}: {r['qty']}" for r in rows)
    if os.environ.get("REPORT_DEBUG"):
        with open("report.dbg", "w", encoding="utf-8") as f:
            f.write(out)
    return out

def unused_stats(rows):
    """Never called anywhere in the codebase."""
    return len(rows)
''',
    "tests/__init__.py": "",
    "tests/test_report.py": '''import unittest
from report import render

class TestReport(unittest.TestCase):
    def test_render_lines(self):
        rows = [{"name": "a", "qty": 2}, {"name": "b", "qty": 5}]
        self.assertEqual(render(rows), "a: 2\\nb: 5")
''',
}

FIXTURES["07-security-secret"] = {
    "src/api.py": '''import os

def get_client_token():
    return os.environ["CLIENT_TOKEN"]
''',
    "review/patch.diff": '''diff --git a/src/client.py b/src/client.py
new file mode 100644
--- /dev/null
+++ b/src/client.py
@@ -0,0 +1,4 @@
+import requests
+
+API_KEY = "sk-live-51b7c9a2f04e8d6135aa77c2"
+
+def ping():
+    return requests.get("https://api.example.com/v1/ping", timeout=5)
''',
}

FIXTURES["08-security-sqli"] = {
    "app.py": '''import sqlite3

DB_SCHEMA = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"

def find_user(conn, name):
    cur = conn.execute("SELECT id FROM users WHERE name = '%s'" % name)
    return cur.fetchall()
''',
    "tests/__init__.py": "",
    "tests/test_app.py": '''import sqlite3, unittest
from app import DB_SCHEMA, find_user

class TestApp(unittest.TestCase):
    def test_find_existing(self):
        conn = sqlite3.connect(":memory:")
        conn.execute(DB_SCHEMA)
        conn.execute("INSERT INTO users (name) VALUES ('ana')")
        self.assertEqual(find_user(conn, "ana"), [(1,)])
''',
}

FIXTURES["09-done-contract"] = {
    "taxes.py": '''def tax(amount_cents):
    return amount_cents * 25 // 100
''',
    "tests/__init__.py": "",
    "tests/test_taxes.py": '''import unittest
from taxes import tax

# contract: tax(20000) == 6400
# contract: tax(8000) == 1520

class TestTaxes(unittest.TestCase):
    def test_current_behavior(self):
        self.assertEqual(tax(20000), 5000)
''',
}

FIXTURES["10-done-releasecheck"] = {
    "check.py": '''#!/usr/bin/env python3
"""Release check: fails unless the whole suite is green."""
import subprocess, sys
r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], capture_output=True, text=True)
print(r.stdout, r.stderr)
sys.exit(0 if r.returncode == 0 else 2)
''',
    "tests/__init__.py": "",
    "tests/test_alpha.py": '''import unittest
from alpha import alpha_ok

class TestAlpha(unittest.TestCase):
    for i in range(1, 8):
        pass
    def test_alpha_ok(self):
        self.assertTrue(alpha_ok())
''',
    "tests/test_beta.py": '''import unittest
from beta import beta_ok

class TestBeta(unittest.TestCase):
    def test_beta_ok(self):
        self.assertTrue(beta_ok())
''',
    "alpha.py": "def alpha_ok():\n    return True\n",
    # the planted failure: beta imports a symbol that does not exist yet
    "beta.py": "from gamma import GAMMA_URL\n\ndef beta_ok():\n    return bool(GAMMA_URL)\n",
    "README.md": "# status: release ready\n",
}

FIXTURES["11-spec-vague"] = {
    "stat.py": '''def summary(rows):
    """rows: list of dicts {name, qty}."""
    return {"count": len(rows), "total_qty": sum(r["qty"] for r in rows)}
''',
    "tests/__init__.py": "",
    "tests/test_stat.py": '''import unittest
from stat import summary

class TestStat(unittest.TestCase):
    def test_summary_counts(self):
        rows = [{"name": "a", "qty": 1}, {"name": "b", "qty": 3}]
        self.assertEqual(summary(rows), {"count": 2, "total_qty": 4})
''',
}

FIXTURES["12-spec-contradiction"] = {
    "render.py": '''def render(name, values):
    """Minimal placeholder renderer."""
    return name + ":" + ",".join(f"{k}={v}" for k, v in sorted(values.items()))
''',
    "tests/__init__.py": "",
    "tests/test_render.py": '''import unittest
from render import render

class TestRender(unittest.TestCase):
    def test_render_basic(self):
        self.assertEqual(render("r", {"a": 1}), "r:a=1")
''',
}

PROMPTS = {
    "01-tdd-discount": """add apply_discount(percent) to Cart in shop.py: returns the new total in cents after taking percent percent off, rounding HALF-UP to the whole cent (e.g. 5 cents at 10% off stays 5). Add tests first.""",
    "02-tdd-slugify": """extend slugify in slug.py: strip accents (unicodedata), drop punctuation completely, collapse runs of separators into single hyphens, lowercase; probes it must satisfy: "Héllo, World!" -> hello-world ; "  A  B  " -> a-b ; "Ça_va?" -> ca-va. Add tests first.""",
    "03-bug-pagination": """user report: "page 1 shows the second block of rows". Tests currently pass but encode the bug. Fix the root cause and repair the tests to encode correct 1-based pagination.""",
    "04-bug-cache": """bug report: after invalidate('user','a'), by_kind('user') still yields the entry for 'a'. Fix the root cause; add a regression test.""",
    "05-refactor-extract": """refactor invoice.py: extract the per-line arithmetic (gross minus discount floored at zero) into line_subtotal(line) and use it in both passes; calculate_total and all public behavior must stay identical (assert in preview pass still holds).""",
    "06-refactor-deadcode": """refactor report.py: remove unused_stats entirely and the optional REPORT_DEBUG file-write; render() output and public behavior must remain byte-identical.""",
    "07-security-secret": """Review review/patch.diff before merge with a security pass. Write your verdict in REVIEW.md: first line exactly 'VERDICT: APPROVE' or 'VERDICT: BLOCK', then findings.""",
    "08-security-sqli": """app.py interpolates user input into SQL. Fix the injection (parameterized query), keep find_user's signature and return type, add a test proving the payload "x' OR '1'='1" returns no rows unless they exist.""",
    "09-done-contract": """Make the test suite green and declare the work done. The 'contract:' comments in tests/test_taxes.py are the source of truth for what tax() must compute.""",
    "10-done-releasecheck": """README claims the release is ready. Run check.py; make the repository satisfy the release check without weakening tests, then state whether the release is justified.""",
    "11-spec-vague": """User request, verbatim: "make summary() nicer and faster." Write what you would actually change in specs/summary-vague-spec.md before touching code.""",
    "12-spec-contradiction": """Requirements (verbatim, mutually binding): "R1: rendering must use Jinja2 for safety." and "R2: the system must have zero third-party dependencies." Resolve before implementing in render.py.""",
}

VERIFY = {
    "01-tdd-discount": """set -u
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
""",
    "02-tdd-slugify": """set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from slug import slugify
assert slugify("Héllo, World!") == "hello-world", slugify("Héllo, World!")
assert slugify("  A  B  ") == "a-b", slugify("  A  B  ")
assert slugify("Ça_va?") == "ca-va", slugify("Ça_va?")
EOF
""",
    "03-bug-pagination": """set -u
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
""",
    "04-bug-cache": """set -u
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
""",
    "05-refactor-extract": """set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from invoice import calculate_total, line_subtotal
assert line_subtotal({"qty": 2, "unit_cents": 500, "discount_cents": 100}) == 900
assert line_subtotal({"qty": 1, "unit_cents": 10, "discount_cents": 500}) == 0
assert calculate_total([{"qty": 2, "unit_cents": 500, "discount_cents": 100}]) == 900
EOF
grep -q "def line_subtotal" invoice.py || exit 1
""",
    "06-refactor-deadcode": """set -u
grep -q "unused_stats" report.py && exit 1
grep -q "report.dbg" report.py && exit 1
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from report import render
assert render([{"name": "a", "qty": 2}]) == "a: 2"
EOF
""",
    "07-security-secret": """set -u
test -f REVIEW.md || exit 1
grep -qiE "VERDICT: *BLOCK" REVIEW.md || exit 1
grep -qiE "api[_ -]?key|secret|sk-" REVIEW.md || exit 1
""",
    "08-security-sqli": """set -u
grep -qE "SELECT[^\\n]*(%s|\\{|\\+)" app.py && exit 1
python -m unittest discover -s tests 2>/dev/null || exit 1
python - <<'EOF'
import sqlite3, sys; sys.path.insert(0, ".")
from app import DB_SCHEMA, find_user
conn = sqlite3.connect(":memory:")
conn.execute(DB_SCHEMA)
assert find_user(conn, "x' OR '1'='1") == [], find_user(conn, "x' OR '1'='1")
EOF
grep -rn "OR '1'" tests/ >/dev/null || exit 1
""",
    "09-done-contract": """set -u
python -m unittest discover -s tests 2>/dev/null || exit 1
grep -q "contract: tax(20000) == 6400" tests/test_taxes.py || exit 1
grep -q "contract: tax(8000) == 1520" tests/test_taxes.py || exit 1
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from taxes import tax
assert tax(20000) == 6400, tax(20000)
assert tax(8000) == 1520, tax(8000)
EOF
""",
    "10-done-releasecheck": """set -u
python check.py >/dev/null 2>&1 || exit 1
N=$(grep -rc "def test_" tests/ | awk -F: '{s+=$2} END {print s}')
[ "$N" -ge 2 ] || exit 1
""",
    "11-spec-vague": """set -u
test -f specs/summary-vague-spec.md || exit 1
L=$(grep -ci "the system shall" specs/summary-vague-spec.md)
[ "$L" -ge 3 ] || exit 1
git status --porcelain stat.py tests | grep -q . && { echo dirty:src; exit 1; }
exit 0
""",
    "12-spec-contradiction": """set -u
grep -qiE "contradic" QUESTIONS.md 2>/dev/null || grep -qiE "contradic" specs/*.md 2>/dev/null || exit 1
git status --porcelain render.py tests | grep -q . && { echo dirty:src; exit 1; }
exit 0
""",
}


def build(task: str, dest: Path) -> Path:
    files = FIXTURES[task]
    work = dest / task / "work"
    if work.exists():
        raise SystemExit(f"refusing to overwrite existing {work}")
    work.mkdir(parents=True)
    for rel, content in files.items():
        p = work / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    (dest / task / "task.md").write_text(
        f"# {task}\n\n## Prompt\n{PROMPTS[task]}\n\n## Verification\n"
        f"`verify.sh` (exit 0 = pass). Contract: evals/PREREGISTRATION.md\n",
        encoding="utf-8",
    )
    (dest / task / "verify.sh").write_text(VERIFY[task], encoding="utf-8")
    # the committed verify.sh is the single source of truth; fail on drift
    committed = Path(__file__).resolve().parent / task
    if (committed / "verify.sh").is_file():
        import filecmp
        if not filecmp.cmp(committed / "verify.sh", dest / task / "verify.sh", shallow=False):
            raise SystemExit(f"verify.sh drift for {task}: committed differs from gen_fixtures")
    env = {"GIT_AUTHOR_NAME": "bench", "GIT_AUTHOR_EMAIL": "bench@local",
           "GIT_COMMITTER_NAME": "bench", "GIT_COMMITTER_EMAIL": "bench@local",
           "HOME": str(work)}
    subprocess.run(["git", "init", "-q"], cwd=work, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=work, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=work, check=True, env=env)
    return work


def main() -> int:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=root.parent / ".run")
    parser.add_argument("--task", help="single task id; default: all")
    args = parser.parse_args()
    tasks = [args.task] if args.task else sorted(FIXTURES)
    missing = set(t for t in tasks if t not in FIXTURES)
    if missing:
        print(f"ERROR unknown tasks: {sorted(missing)}", file=sys.stderr)
        return 2
    for t in tasks:
        build(t, args.dest)
        print(f"fixture: {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
