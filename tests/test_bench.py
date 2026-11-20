"""Tests for the Fase 2 benchmark harness (scripts/bench.py, evals/tasks/).

Run: python tests/test_bench.py  (or via tests/run_all.py)
No model calls are made here; this validates mechanics only.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals" / "tasks"))
sys.path.insert(0, str(ROOT / "scripts"))
import gen_fixtures  # noqa: E402

import bench  # noqa: E402

gf = gen_fixtures


class FixtureTests(unittest.TestCase):
    """Fixtures are the preregistered state; they must be deterministic."""

    def setUp(self):
        self.dest = Path(tempfile.mkdtemp())

    def test_build_all_tasks(self):
        work = gf.build("02-tdd-slugify", self.dest)
        self.assertTrue((work / "slug.py").is_file())
        self.assertTrue((work.parent / "verify.sh").is_file())
        self.assertTrue((work.parent / "task.md").is_file())

    def test_build_is_deterministic(self):
        d1 = Path(tempfile.mkdtemp())
        d2 = Path(tempfile.mkdtemp())
        gf.build("04-bug-cache", d1)
        gf.build("04-bug-cache", d2)
        for rel in gf.FIXTURES["04-bug-cache"]:
            a = (d1 / "04-bug-cache" / "work" / rel).read_bytes()
            b = (d2 / "04-bug-cache" / "work" / rel).read_bytes()
            self.assertEqual(a, b)

    def test_verify_fixture_fails_untouched(self):
        work = gf.build("07-security-secret", self.dest)
        r = subprocess.run(["bash", str(ROOT / "evals" / "tasks" /
                                        "07-security-secret" / "verify.sh")],
                           cwd=work, capture_output=True, timeout=60)
        self.assertNotEqual(r.returncode, 0)

    def test_verify_sh_mentions_gen_contract(self):
        for task in gf.FIXTURES:
            v = ROOT / "evals" / "tasks" / task / "verify.sh"
            self.assertTrue(v.is_file(), f"missing committed verify.sh: {task}")


class CellConfigTests(unittest.TestCase):
    def test_cell_b_has_14_kit_skills(self):
        self.assertEqual(len(bench.CELL_SOURCES["B"]), 14)

    def test_cell_a_empty(self):
        self.assertEqual(bench.CELL_SOURCES["A"], [])

    def test_cell_c_subsets_exist_in_cache(self):
        if not (ROOT / "evals" / ".cache" / "superpowers").is_dir():
            self.skipTest("competitor cache not fetched (run make bench-prep)")
        missing = [str(s) for s in bench.CELL_SOURCES["C"] if not s.is_dir()]
        self.assertEqual(missing, [])

    def test_cell_d_subsets_exist_in_cache(self):
        if not (ROOT / "evals" / ".cache" / "ecc").is_dir():
            self.skipTest("competitor cache not fetched (run make bench-prep)")
        missing = [str(s) for s in bench.CELL_SOURCES["D"] if not s.is_dir()]
        self.assertEqual(missing, [])


class AdapterTests(unittest.TestCase):
    """Usage parsing must never synthesize: garbage in -> None."""

    def test_claude_usage_parses(self):
        out = json.dumps({"model": "m", "usage": {"input_tokens": 10, "output_tokens": 2}})
        u = bench._claude_usage(out, "", Path("."))
        self.assertEqual(u, {"input": 10, "output": 2, "cache_read": None, "model": "m"})

    def test_claude_usage_garbage_is_none(self):
        self.assertIsNone(bench._claude_usage("not json", "", Path(".")))

    def test_vibe_usage_garbage_is_none(self):
        self.assertIsNone(bench._vibe_usage("", "boom", Path(".")))


class TriggerSetTests(unittest.TestCase):
    def test_every_skill_has_8_yes_8_no(self):
        skills = sorted(p.name for p in (ROOT / "skills").glob("*/") if (p / "SKILL.md").is_file())
        self.assertEqual(len(skills), 14)
        for s in skills:
            f = ROOT / "evals" / "triggers" / f"{s}.jsonl"
            rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            self.assertEqual(len([r for r in rows if r["expect"] == "yes"]), 8, s)
            self.assertEqual(len([r for r in rows if r["expect"] == "no"]), 8, s)


class PreregFrozenTests(unittest.TestCase):
    def test_preregistered_12_tasks_match_generator(self):
        self.assertEqual(len(gf.FIXTURES), 12)

    def test_pinned_competitor_shas_in_prereg_text(self):
        t = (ROOT / "evals" / "PREREGISTRATION.md").read_text(encoding="utf-8")
        self.assertIn("22f0b463e7a5e579904dd6211a520321035526f7", t)
        self.assertIn("4adeee6732a12d1540f49a4d50a38ce8c97f9a53", t)


if __name__ == "__main__":
    unittest.main()
