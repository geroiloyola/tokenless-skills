from pathlib import Path
import subprocess
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[1] / "skills/fresh-review/scripts/review-snapshot.sh"


class SnapshotTest(unittest.TestCase):
    def test_one_diff_covers_committed_staged_and_unstaged_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            snapshot = Path(tmp) / "snapshot"
            work.mkdir()
            snapshot.mkdir()

            def git(*args):
                return subprocess.check_output(["git", "-c", "user.name=Test", "-c", "user.email=test@example.org",
                                                "-c", "commit.gpgsign=false", *args], cwd=work, text=True).strip()

            def review(*args):
                return subprocess.run(["bash", str(HELPER), *args, str(snapshot)], cwd=work,
                                      capture_output=True, text=True)

            git("init", "-q")
            (work / "tracked.txt").write_text("before\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-qm", "base")
            git("branch", "review-base")
            (work / "committed.txt").write_text("committed\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-qm", "feature")
            (work / "staged.txt").write_text("staged\n", encoding="utf-8")
            (work / "tracked.txt").write_text("unstaged\n", encoding="utf-8")
            self.assertIn("untracked", review("freeze", "review-base").stderr)
            git("add", "staged.txt")
            (work / "staged.txt").write_text("different from index\n", encoding="utf-8")
            self.assertIn("partially staged", review("freeze", "review-base").stderr)
            (work / "staged.txt").write_text("staged\n", encoding="utf-8")
            run = review("freeze", "review-base")
            self.assertEqual(run.returncode, 0, run.stderr)
            diff = (snapshot / "review.diff").read_text(encoding="utf-8")
            for line in ("+committed", "+staged", "+unstaged"):
                self.assertIn(f"\n{line}\n", diff)
            self.assertEqual(review("check").returncode, 0)
            git("branch", "-f", "review-base", "HEAD")
            self.assertEqual(review("check").returncode, 0)  # The frozen base still wins.
            (work / "tracked.txt").write_text("after approval\n", encoding="utf-8")
            self.assertIn("diff changed", review("check").stderr)
            (work / "tracked.txt").write_text("unstaged\n", encoding="utf-8")
            git("commit", "-qam", "changed HEAD")
            self.assertIn("HEAD changed", review("check").stderr)
