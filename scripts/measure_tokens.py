#!/usr/bin/env python3
"""Reproducible token measurement for skills (Tokenless Standard, Fase 0).

Measures real token counts with tiktoken when available; otherwise degrades
to the chars/4 estimator and says so. Standard library + optional tiktoken
(dev-only dependency; hosts never run this script).

Usage:
    python3 scripts/measure_tokens.py                 # table on stdout
    python3 scripts/measure_tokens.py --json PATH     # also write raw JSON
    python3 scripts/measure_tokens.py --encoding cl100k_base

Exit code: 0 if a tokenizer was used, 2 if only the chars/4 estimator was
available (so CI can distinguish estimates from measurements).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"name:\s*[\"]?([^\"\n]+)")


def split_frontmatter(text: str) -> tuple[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(0), text[m.end():]


def estimator_tokens(text: str) -> int:
    """The chars/4 heuristic used previously in the README."""
    return max(1, round(len(text) / 4))


def load_tokenizer(encoding: str):
    try:
        import tiktoken  # type: ignore

        return tiktoken.get_encoding(encoding), None
    except Exception as exc:  # tiktoken missing, or no cached weights/network
        return None, f"tiktoken unavailable ({type(exc).__name__}: {exc})"


def measure(skills_dir: Path, encoding_name: str) -> dict:
    tok, error = load_tokenizer(encoding_name)
    rows = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        raw = skill_md.read_text(encoding="utf-8")
        fm, body = split_frontmatter(raw)
        desc = ""
        nm = NAME_RE.search(fm)
        dm = re.search(r"description:\s*[\"'](.+?)[\"']\s*$", fm, re.MULTILINE)
        if dm:
            desc = dm.group(1)
        row = {
            "skill": nm.group(1).strip() if nm else skill_md.parent.name,
            "dir": skill_md.parent.name,
            "lines": raw.count("\n") + 1,
            "body_chars": len(body),
            "desc_chars": len(desc),
        }
        if tok:
            row["body_tokens"] = len(tok.encode(body))
            row["desc_tokens"] = len(tok.encode(desc))
        else:
            row["body_tokens"] = estimator_tokens(body)
            row["desc_tokens"] = estimator_tokens(desc)
        row["body_tokens_est4"] = estimator_tokens(body)
        row["desc_tokens_est4"] = estimator_tokens(desc)
        row["estimator_abs_err_body"] = abs(row["body_tokens_est4"] - row["body_tokens"])
        row["estimator_err_pct"] = round(
            100.0 * (row["body_tokens_est4"] - row["body_tokens"]) / row["body_tokens"], 1
        )
        rows.append(row)
    return {
        "tokenizer": encoding_name if tok else "chars/4 estimator (UNMEASURED)",
        "tiktoken_error": error,
        "measured": tok is not None,
        "skills": rows,
    }


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-dir", type=Path, default=root / "skills",
        help="directory containing <skill>/SKILL.md subdirectories",
    )
    parser.add_argument(
        "--encoding", default="o200k_base",
        help="tiktoken encoding (default: o200k_base, GPT-4o era)",
    )
    parser.add_argument("--json", type=Path, help="also write raw results as JSON")
    args = parser.parse_args()

    if not args.skills_dir.is_dir():
        print(f"ERROR: skills dir not found: {args.skills_dir}", file=sys.stderr)
        return 2

    result = measure(args.skills_dir, args.encoding)

    header = f"tokenizer: {result['tokenizer']}"
    print(header)
    cols = (
        f"{'skill':<22} {'body':>6} {'desc':>5} {'lines':>6} "
        f"{'est4':>5} {'err%':>6}"
    )
    print(cols)
    print("-" * len(cols))
    bodies = []
    for r in result["skills"]:
        print(
            f"{r['skill']:<22} {r['body_tokens']:>6} {r['desc_tokens']:>5} "
            f"{r['lines']:>6} {r['body_tokens_est4']:>5} {r['estimator_err_pct']:>6}"
        )
        bodies.append(r["body_tokens"])
    bodies.sort()
    n = len(bodies)
    mean = sum(bodies) / n
    median = bodies[n // 2]
    mean_est = sum(r["body_tokens_est4"] for r in result["skills"]) / len(result["skills"])
    mean_err = sum(r["estimator_abs_err_body"] for r in result["skills"]) / len(result["skills"])
    desc_total = sum(r["desc_tokens"] for r in result["skills"])
    tot_body = sum(bodies)
    print("-" * len(cols))
    if len(bodies) >= 2:
        print(f"body tokens: min {bodies[0]} / median {median} / mean {mean:.0f} / max {bodies[-1]}")
    print(f"always-loaded context cost = sum of description tokens: {desc_total}")
    print(f"sum body tokens: {tot_body} | chars/4 mean err vs tokenizer: {mean_err:.1f} tokens ({100*mean_err/mean:.1f}% of mean)")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"raw JSON -> {args.json}")

    return 0 if result["measured"] else 2


if __name__ == "__main__":
    sys.exit(main())
