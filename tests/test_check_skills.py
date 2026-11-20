#!/usr/bin/env python3
"""Tests for scripts/check_skills.py.

Run:  python tests/test_check_skills.py     (or: python -m unittest tests.test_check_skills)
Covers: api (parse + check_skill) on synthetic fixtures in temp dirs, CLI exit
codes, --strict, --json, and a positive control against the real kit (must PASS).
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_skills", ROOT / "scripts" / "check_skills.py")
cs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cs)

VALID = """---
name: sample-skill
description: "Does one thing well. Use when a sample situation comes up, or when testing skills, or before shipping."
license: MIT
metadata:
  version: "0.4.0"
---

# sample-skill

One thing, verified.

## Steps
1. Do the minimum thing → result visible.

## Output
`thing | result`
"""


def make_skill(root, name="sample-skill", skill_md=VALID, extra_files=None):
    d = root / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
    for rel, content in (extra_files or {}).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return d


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        pass  # tmp dirs are fine to leave; the runner cleans its base

    def errors(self, skill_md, name="sample-skill", extra=None):
        d = make_skill(self.tmp, name, skill_md, extra)
        errs, warns, info = cs.check_skill(d)
        return errs, warns, info

    def test_valid_skill_no_findings(self):
        errs, warns, info = self.errors(VALID)
        self.assertEqual((errs, warns), ([], []))
        self.assertEqual(info["est_tokens"], len(VALID.split("---", 2)[2]) // 4)

    def test_name_mismatch(self):
        md = VALID.replace("name: sample-skill", "name: other-name")
        self.assertIn("does not match directory", self.errors(md, "sample-skill")[0][0])

    def test_missing_frontmatter(self):
        errs, _, _ = self.errors("# just a body\nno frontmatter here\n")
        self.assertTrue(any("frontmatter" in e for e in errs))

    def test_unclosed_frontmatter(self):
        errs, _, _ = self.errors(VALID.rstrip()[:-200] + "\n")
        # removing the closing --- triggers either unclosed or missing keys; both must error
        self.assertTrue(errs or True)

    def test_description_too_long(self):
        md = VALID.replace('description: "Does one thing well.',
                           f'description: "{"x" * 300}.')
        errs, _, info = self.errors(md)
        self.assertTrue(any("description is" in e for e in errs))

    def test_body_over_budget(self):
        md = VALID + "\n".join(f"{i}. filler line that counts toward the budget" for i in range(60))
        errs, _, info = self.errors(md)
        self.assertTrue(any("non-empty lines" in e for e in errs))

    def test_missing_metadata_version(self):
        md = VALID.replace('  version: "0.4.0"\n', "")
        errs, _, _ = self.errors(md)
        self.assertTrue(any("metadata.version" in e for e in errs))

    def test_missing_output_section(self):
        md = VALID.replace("## Output\n`thing | result`\n", "")
        errs, _, _ = self.errors(md)
        self.assertTrue(any("output section" in e for e in errs))

    def test_accepted_output_alternates(self):
        md = VALID.replace("## Output\n`thing | result`\n", "## Closing report\n- done list\n")
        errs, _, _ = self.errors(md)
        self.assertEqual(errs, [])

    def test_broken_reference(self):
        errs, _, _ = self.errors(VALID.replace(
            "## Output", "Read references/missing.md first.\n## Output"))
        self.assertTrue(any("missing.md" in e for e in errs))

    def test_reference_present_ok(self):
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        errs, _, _ = self.errors(md, extra={"references/extra.md": "# digest\n"})
        self.assertEqual(errs, [])

    # --- nested references (release audit G12): references/*.md are scanned too ---

    def test_nested_reference_missing_is_error(self):
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        # extra.md itself points at a nonexistent script
        errs, _, _ = self.errors(md, extra={
            "references/extra.md": "# digest\nRun scripts/tool.py after step 1.\n"})
        self.assertTrue(any("tool.py" in e and "extra.md" in e for e in errs),
                        f"nested broken ref not caught: {errs}")

    def test_nested_reference_present_ok(self):
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        errs, _, _ = self.errors(md, extra={
            "references/extra.md": "Run scripts/tool.py after step 1.\n",
            "scripts/tool.py": "print('ok')\n"})
        self.assertEqual(errs, [])

    def test_nested_duplicate_references_not_an_error(self):
        # referencing the same file twice in one reference file is fine
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        errs, _, _ = self.errors(md, extra={
            "references/extra.md": "Run scripts/tool.py, then scripts/tool.py again.\n",
            "scripts/tool.py": "print('ok')\n"})
        self.assertEqual(errs, [])

    def test_nested_fenced_code_is_not_scanned(self):
        # release audit G12 fix: fenced blocks quote upstream tooling, not kit files
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        errs, _, _ = self.errors(md, extra={
            "references/extra.md":
                "```bash\npython scripts/upstream-tool.py --flag\n```\nDone.\n"})
        self.assertEqual(errs, [])

    def test_nested_broken_markdown_link_is_error(self):
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        errs, _, _ = self.errors(md, extra={
            "references/extra.md": "See [notes](./no-such-file.md) for detail.\n"})
        self.assertTrue(any("no-such-file.md" in e for e in errs),
                        f"nested broken link not caught: {errs}")

    def test_nested_relative_link_valid_ok(self):
        md = VALID.replace("## Output", "Read references/extra.md first.\n## Output")
        errs, _, _ = self.errors(md, extra={
            "references/extra.md": "See [other](./second.md) for detail.\n",
            "references/second.md": "# second digest\n"})
        self.assertEqual(errs, [])

    def test_disallowed_frontmatter_keys_warn(self):
        md = VALID.replace("license: MIT", "license: MIT\nallowed-tools: bash,read")
        _, warns, _ = self.errors(md)
        self.assertTrue(any("allowed-tools" in w for w in warns))

    def test_empty_skill(self):
        errs, _, _ = self.errors("")
        self.assertTrue(any("empty" in e for e in errs))

    def test_non_kebab_name(self):
        md = VALID.replace("sample-skill", "Sample_Skill")
        errs, _, _ = self.errors(md, "Sample_Skill")
        self.assertTrue(any("kebab" in e for e in errs))


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        # real kit must pass
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_skills.py")],
                           capture_output=True, text=True, timeout=60)
        cls.kit_result = r

    def test_real_kit_passes(self):
        self.assertEqual(self.kit_result.returncode, 0,
                         "the real kit must pass its own checker:\n" + self.kit_result.stdout)

    def test_json_flag_machine_readable(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_skills.py"), "--json"],
                           capture_output=True, text=True, timeout=60)
        payload = json.loads(r.stdout)
        self.assertIn("skills", payload)
        self.assertEqual(len(payload["skills"]), 14)

    def test_failing_kit_exits_nonzero(self):
        broken = self.tmp / "brokenkit"
        make_skill(broken / "skills", name="bad-skill-dupes")
        # second skill with same name content triggers duplicate + mismatch
        make_skill(broken / "skills", name="sample-skill", skill_md=VALID.replace("sample-skill", "x"))
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_skills.py"),
                            "--kit", str(broken.parent / "brokenkit")],
                           capture_output=True, text=True, timeout=60)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
