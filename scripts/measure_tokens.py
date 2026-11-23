#!/usr/bin/env python3
"""Token budget validator: fails if any skill exceeds the budget.

Budget: description <= 55 tokens, body <= 600 tokens (o200k_base via tiktoken;
chars/4 estimator as fallback, marked as estimate).
"""
import re
import sys
from pathlib import Path

DESC_BUDGET = 55
BODY_BUDGET = 600
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def count(text: str) -> tuple[int, str]:
    try:
        import tiktoken

        return len(tiktoken.get_encoding("o200k_base").encode(text)), "tiktoken o200k_base"
    except Exception:
        return max(1, round(len(text) / 4)), "chars/4 estimator (unmeasured)"


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    tokenizer = None
    rows, over = [], []
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        raw = skill_md.read_text(encoding="utf-8")
        fm = FM_RE.match(raw)
        body = raw[fm.end():] if fm else raw
        desc = ""
        if fm:
            dm = re.search(r"description:\s*[\"'](.+?)[\"']\s*$", fm.group(1), re.MULTILINE)
            desc = dm.group(1) if dm else ""
        dt, tokenizer2 = count(desc)
        bt, tokenizer2 = count(body)
        tokenizer = tokenizer or tokenizer2
        rows.append((skill_md.parent.name, bt, dt))
        if bt > BODY_BUDGET or dt > DESC_BUDGET:
            over.append(skill_md.parent.name)

    print(f"tokenizer: {tokenizer} | budget: desc<={DESC_BUDGET} body<={BODY_BUDGET}")
    print(f"{'skill':<22} {'body':>6} {'desc':>5}")
    for name, bt, dt in rows:
        flag = "  OVER" if name in over else ""
        print(f"{name:<22} {bt:>6} {dt:>5}{flag}")
    print(f"skills: {len(rows)} | body total: {sum(r[1] for r in rows)}")
    if over:
        print(f"FAIL: budget exceeded by: {', '.join(over)}")
        return 1
    print("PASS: all skills within budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
