import json
import sys
from types import SimpleNamespace
import unittest

from scripts.bench import ROOT, activation, run


class BenchTest(unittest.TestCase):
    def test_adapter_receives_task_in_fresh_workspace_and_metrics_are_separate(self):
        task = json.loads((ROOT / "evals/tasks.json").read_text(encoding="utf-8"))[0]
        adapter = f"""
import json, os, sys
from pathlib import Path
mode = os.environ['TOKENLESS_BENCH_MODE']
assert sys.stdin.read() == {task['prompt']!r}
assert Path('app.py').read_text() == {task['seed']!r}
assert Path('.agents/skills/implement-tdd/SKILL.md').is_file() == (mode == 'kit')
Path('app.py').write_text({task['solution']!r})
print(json.dumps({{'tokens': 8, 'activated_skills': ['implement-tdd']}} if mode == 'kit' else {{}}))
"""
        args = SimpleNamespace(adapter=[sys.executable, "-c", adapter], timeout=10)
        baseline, kit = (run(task, mode, args) for mode in ("baseline", "kit"))
        self.assertTrue(baseline["pass"] and kit["pass"])
        self.assertIsNone(baseline["tokens"])
        self.assertEqual(kit["tokens"], 8)
        self.assertTrue(kit["activation_pass"])
        self.assertFalse(activation(task, ["implement-tdd", "webapp-testing"]))
        self.assertFalse(activation(task, []))
        self.assertIsNone(activation(task, None))
