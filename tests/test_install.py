import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallTest(unittest.TestCase):
    def test_install_from_consumer_with_spaces_and_explicit_targets(self):
        with tempfile.TemporaryDirectory(prefix="install smoke ") as tmp:
            parent = Path(tmp)
            kit = parent / "kit checkout"
            project = parent / "consumer project"
            home = parent / "home directory"
            for path in (kit, project, home):
                path.mkdir()
            installer = shutil.copy2(ROOT / "install.sh", kit)
            shutil.copytree(ROOT / "skills", kit / "skills")
            expected = {p.parent.name: p.read_bytes() for p in (kit / "skills").glob("*/SKILL.md")}
            self.assertTrue(expected)
            def run(*targets):
                return subprocess.run([installer, *targets], cwd=project,
                                      env=dict(os.environ, HOME=str(home)),
                                      capture_output=True, text=True)

            result = run("project", "claude", "codex", "agents")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("installed "), 3 * len(expected))
            for dest in (project / ".agents", home / ".claude", home / ".codex"):
                self.assertEqual({p.parent.name: p.read_bytes() for p in dest.glob("skills/*/SKILL.md")}, expected)
            self.assertFalse((kit / ".agents").exists())

            old = project / ".agents/skills/repo-context/SKILL.md"
            old.write_text("local copy", encoding="utf-8")
            result = run()  # Detect both configured hosts and the consumer project.
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("installed "), 3 * len(expected))
            self.assertEqual(old.read_bytes(), expected["repo-context"])
            backups = list(old.parents[2].glob(".tokenless-backup.*/repo-context/SKILL.md"))
            self.assertEqual([p.read_text(encoding="utf-8") for p in backups], ["local copy"])

    def test_unwritable_target_does_not_report_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".agents").touch()
            result = subprocess.run([str(ROOT / "install.sh"), "project"], cwd=project,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("installed ", result.stdout)
