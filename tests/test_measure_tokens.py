from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import tiktoken

from scripts.measure_tokens import main, measure


class MeasureTest(unittest.TestCase):
    def test_fails_closed_without_tokenizer(self):
        with patch.dict("sys.modules", {"tiktoken": None}), redirect_stderr(StringIO()) as err:
            self.assertEqual(main(), 1)
        self.assertIn("requires tiktoken o200k_base", err.getvalue())

    def test_empty_skill_set_and_invalid_frontmatter_are_rejected(self):
        encoding = tiktoken.get_encoding("o200k_base")
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp)
            with self.assertRaisesRegex(ValueError, "no skill directories"):
                measure(skills, encoding)
            directory = skills / "sample"
            directory.mkdir()
            with self.assertRaises(FileNotFoundError):
                measure(skills, encoding)
            for data, error in (
                ("# Body", "frontmatter"),
                ("---\nname: wrong\ndescription: okay\n---\n# Body", "matching its directory"),
                ("---\nname: sample\n---\n# Body", "nonempty string"),
                ("---\nname: sample\ndescription: first\ndescription: second\n---\n# Body", "duplicate"),
            ):
                with self.subTest(data=data):
                    (directory / "SKILL.md").write_text(data, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, error):
                        measure(skills, encoding)

    def test_folded_description_is_counted_exactly(self):
        encoding = tiktoken.get_encoding("o200k_base")
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp)
            (skills / "sample").mkdir()
            (skills / "sample/SKILL.md").write_text(
                "---\nname: sample\ndescription: >-\n  First line\n  second line\n---\n# Body\n",
                encoding="utf-8",
            )
            self.assertEqual(measure(skills, encoding), [(
                "sample", len(encoding.encode("# Body\n")), len(encoding.encode("First line second line")),
            )])
