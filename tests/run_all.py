#!/usr/bin/env python3
"""Run the entire tokenless-skills test suite. Standard library only.

  python3 tests/run_all.py          # all suites
  python3 tests/run_all.py --quiet
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUIET = "--quiet" in sys.argv

SUITES = [
    ("check_skills on the real kit", [sys.executable, "scripts/check_skills.py", "--strict"]),
    ("skill checker tests",          [sys.executable, "-m", "unittest", "-q", "tests.test_check_skills"]),
    ("guard tests",                  [sys.executable, "tests/test_guard.py"]),
    ("installer tests (isolated)",   ["bash", "tests/test_installer.sh"]),
]

results = []
for name, cmd in SUITES:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
    tail = (r.stdout or r.stderr).strip().splitlines()
    summary = next((ln for ln in reversed(tail) if any(k in ln.lower()
                    for k in ("passed", "ok", "-> pass", "-> fail"))), "")
    results.append((name, r.returncode, summary if QUIET else (r.stdout + r.stderr)))

for name, rc, detail in results:
    marker = "PASS" if rc == 0 else "FAIL"
    print(f"[{marker}] {name}")
    if not QUIET and rc != 0:
        print(detail)

failed = [n for n, rc, _ in results if rc != 0]
print()
print("ALL SUITES PASSED" if not failed else f"FAILED: {failed}")
sys.exit(1 if failed else 0)
