#!/usr/bin/env python3
"""Validate Agent Skills frontmatter and exact o200k_base budgets."""
import re
import sys
from pathlib import Path

DESC_BUDGET = 55
BODY_BUDGET = 600
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def measure(skills: Path, encoding) -> list[tuple[str, int, int]]:
    import yaml

    directories = sorted(p for p in skills.iterdir() if p.is_dir())
    if not directories:
        raise ValueError("no skill directories found")
    rows = []
    for directory in directories:
        skill_md = directory / "SKILL.md"
        fm = FM_RE.match(raw := skill_md.read_text(encoding="utf-8"))
        if not fm:
            raise ValueError(f"{skill_md}: missing or unclosed frontmatter")
        try:
            # Compose before constructing to reject duplicate keys instead of silently overwriting them.
            node = yaml.compose(fm[1], Loader=yaml.SafeLoader)
            if not isinstance(node, yaml.MappingNode):
                raise ValueError(f"{skill_md}: frontmatter must be a YAML mapping")
            keys = [key.value for key, _ in node.value if isinstance(key, yaml.ScalarNode)]
            if len(keys) != len(node.value) or len(keys) != len(set(keys)):
                raise ValueError(f"{skill_md}: invalid or duplicate frontmatter keys")
            fields = yaml.safe_load(fm[1])
        except yaml.YAMLError as exc:
            raise ValueError(f"{skill_md}: invalid YAML: {exc}") from exc
        name, desc = fields.get("name"), fields.get("description")
        if name != directory.name or len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise ValueError(f"{skill_md}: name must be a valid skill name matching its directory")
        if not isinstance(desc, str) or not desc.strip():
            raise ValueError(f"{skill_md}: description must be a nonempty string")
        body = raw[fm.end():]
        if not body.strip():
            raise ValueError(f"{skill_md}: body must not be empty")
        rows.append((name, len(encoding.encode_ordinary(body)), len(encoding.encode_ordinary(desc))))
    return rows


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("o200k_base")
        rows = measure(root / "skills", encoding)
    except Exception as exc:
        print(f"FAIL: validation requires tiktoken o200k_base and valid skills: {exc}", file=sys.stderr)
        return 1
    over = {name for name, bt, dt in rows if bt > BODY_BUDGET or dt > DESC_BUDGET}

    print(f"tokenizer: tiktoken {encoding.name} | budget: desc<={DESC_BUDGET} body<={BODY_BUDGET}")
    print(f"{'skill':<22} {'body':>6} {'desc':>5}")
    for name, bt, dt in rows:
        flag = "  OVER" if name in over else ""
        print(f"{name:<22} {bt:>6} {dt:>5}{flag}")
    print(f"skills: {len(rows)} | body total: {sum(r[1] for r in rows)} | desc total: {sum(r[2] for r in rows)}")
    if over:
        print(f"FAIL: budget exceeded by: {', '.join(sorted(over))}")
        return 1
    print("PASS: all skills within budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
