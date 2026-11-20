#!/usr/bin/env python3
"""check_skills.py — validate every skill in skills/ against the project doctrine
(documented in skills/SKILL_MASTER.md). Standard library only.

Usage:
  python3 scripts/check_skills.py            # human output; exit 1 on errors
  python3 scripts/check_skills.py --strict   # warnings become errors
  python3 scripts/check_skills.py --json     # machine-readable output
  python3 scripts/check_skills.py --strict --json

This is validation only — it never rewrites skills.
"""
import argparse
import json
import re
import sys
from pathlib import Path

MAX_DESC_CHARS = 250          # kit contract (spec allows 1024; the kit caps harder)
MAX_BODY_LINES = 50           # non-empty lines, SKILL_MASTER rule 3
MAX_BODY_TOKENS = 1000        # est. tokens (chars/4), SKILL_MASTER rule 3
OUTPUT_SECTIONS = ["## Output", "## Closing report", "## Final report"]  # doctrine rule 10: any one satisfies
OPTIONAL_SECTIONS = ["## Steps", "## Rules", "## Escape", "## Checks",
                     "## Close", "## Housekeeping", "## Do not record",
                     "## If ECC is installed", "## Template", "## Final report",
                     "## Diff review", "## Spec check", "## Smoke", "## Gates",
                     "## Order of preference", "## Reviewer brief",
                     "## Questions that matter", "## Test level by layer",
                     "## Closing report", "## Stop signs", "## Before coding",
                     "## Hard rules (CRITICAL)", "## Audit after building",
                     "## Setup (once per repo)", "## Run", "## Compare and decide",
                     "## Self-check before delivering", "## Checks before delivering",
                     "## Quality bar", "## Test level"]

NAV = "\x1b["


def c(code):
    return f"{NAV}{code}m" if sys.stderr.isatty() or sys.stdout.isatty() else ""


GREEN, RED, YELLOW, DIM, RESET = c("32"), c("31"), c("33"), c("2"), c("0")


def parse_frontmatter(text):
    """Parse the kit's flat YAML frontmatter (--- / key: value / ---). Returns
    (meta, body, first_body_line) or (None, None, 0) if the shape is invalid."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None, None, 0
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, None, 0
    meta, unknown = {}, []
    inside_metadata = False
    for i, line in enumerate(lines[1:end], start=2):
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            inside_metadata = m.group(1) == "metadata"
            if inside_metadata:
                meta["metadata"] = {}
            else:
                meta[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        elif line.startswith(" ") and inside_metadata:
            m2 = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", line)
            if m2:
                if not isinstance(meta.get("metadata"), dict):
                    meta["metadata"] = {}
                meta["metadata"][m2.group(1)] = m2.group(2).strip().strip('"').strip("'")
        else:
            unknown.append((i, line))
    meta["_unknown_lines"] = unknown
    if "metadata" not in meta:
        meta["metadata"] = {}
    body = "\n".join(lines[end + 1:])
    return meta, body, end + 2


def quoted(value):
    return value.strip().strip('"').strip("'")


def check_skill(skill_dir):
    """Return (errors, warnings, info) for one skill directory."""
    errors, warnings, info = [], [], {}
    name_dir = skill_dir.name
    sfile = skill_dir / "SKILL.md"

    if not sfile.is_file():
        return [f"missing SKILL.md"], [], {}
    text = sfile.read_text(encoding="utf-8")
    if not text.strip():
        return [f"SKILL.md is empty"], [], {}

    meta, body, fm_end = parse_frontmatter(text)
    if meta is None:
        return ["frontmatter block (--- ... ---) not found or malformed at line 1"], [], {}

    # name / directory
    name = quoted(meta.get("name", ""))
    if not name:
        errors.append("frontmatter missing required key 'name'")
    elif not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        errors.append(f"name '{name}' is not kebab-case (lowercase + hyphens)")
    elif name != name_dir:
        errors.append(f"name '{name}' does not match directory '{name_dir}'")

    # description
    desc = quoted(meta.get("description", ""))
    if not desc:
        errors.append("frontmatter missing required key 'description'")
    elif len(desc) > MAX_DESC_CHARS:
        errors.append(f"description is {len(desc)} chars (kit limit {MAX_DESC_CHARS})")

    # license / version
    if "license" not in meta:
        errors.append("frontmatter missing required key 'license'")
    version = (meta.get("metadata") or {}).get("version", (meta.get("metadata") or {}).get(""))
    if not (meta.get("metadata") or {}).get("version"):
        errors.append("frontmatter missing metadata.version (e.g. metadata: { version: \"0.4.0\" })")
    if meta["metadata"] and not re.match(r"^\d+\.\d+\.\d+$", (meta["metadata"] or {}).get("version", "")):
        errors.append("metadata.version is not semver (e.g. \"0.4.0\")")

    # disallowed keys (doctrine rule 8)
    for banned in ("allowed-tools", "compatibility"):
        if banned in meta:
            warnings.append(f"frontmatter key '{banned}' is not part of the kit contract")

    if meta.get("_unknown_lines"):
        first_line, snippet = meta["_unknown_lines"][0]
        warnings.append(f"unrecognized frontmatter line {first_line}: {snippet[:60]!r}")

    # body budget
    body_lines = [l for l in body.split("\n") if l.strip()]
    n = len(body_lines)
    if n > MAX_BODY_LINES:
        errors.append(f"body has {n} non-empty lines (kit limit {MAX_BODY_LINES}) — move data to references/")
    body_chars = len(body.rstrip())
    est_tokens = body_chars // 4
    if est_tokens > MAX_BODY_TOKENS:
        errors.append(f"body ~{est_tokens} tokens (chars/4), over kit hard cap {MAX_BODY_TOKENS}")

    # required output section (any of the accepted alternates)
    if not any(sect in body for sect in OUTPUT_SECTIONS):
        errors.append("missing an explicit output section (one of: "
                      + ", ".join(f"'{s}'" for s in OUTPUT_SECTIONS) + ")")

    # referenced files must exist
    for m in re.finditer(r"(references|scripts)/[\w.\-]+\.(?:md|mjs|js|py|json|txt|toml|sh)", body):
        ref = m.group(0)
        if not (skill_dir / ref).is_file():
            errors.append(f"body references '{ref}' but that file is missing from the skill folder")

    # broken relative markdown links
    for m in re.finditer(r"\]\((?!https?://|#)([^)]+)\)", body):
        link = m.group(1).split("#")[0].strip()
        if link and not (skill_dir / link).exists():
            errors.append(f"relative link target '{link}' does not exist")

    # nested reference files are scanned too (release audit G12). Fenced code
    # blocks are skipped: they quote upstream tooling, not this kit's files.
    for ref_file in sorted(skill_dir.glob("references/*.md")):
        try:
            rtext = ref_file.read_text(encoding="utf-8")
        except OSError:
            warnings.append(f"could not read {ref_file.name}")
            continue
        scan = re.sub(r"```.*?```", "", rtext.replace("\r\n", "\n"), flags=re.S)
        for m in re.finditer(r"(references|scripts)/[\w.\-]+\.(?:md|mjs|js|py|json|txt|toml|sh)", scan):
            ref = m.group(0)
            if not (skill_dir / ref).is_file():
                errors.append(f"{ref_file.name} references '{ref}' but that file is missing from the skill folder")
        for m in re.finditer(r"\]\((?!https?://|#)([^)]+)\)", scan):
            link = m.group(1).split("#")[0].strip()
            # markdown links resolve relative to the file that contains them
            if link and not (ref_file.parent / link).exists():
                errors.append(f"{ref_file.name}: relative link target '{link}' does not exist")

    info.update({"name": name, "nonempty_lines": n, "body_chars": body_chars,
                 "est_tokens": est_tokens, "desc_chars": len(desc),
                 "version": (meta.get("metadata") or {}).get("version")})
    return errors, warnings, info


def main():
    ap = argparse.ArgumentParser(description="Validate skills/ against kit doctrine.")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--kit", default=None, help="kit root (default: repo of this script's parent)")
    args = ap.parse_args()

    kit = Path(args.kit) if args.kit else Path(__file__).resolve().parent.parent
    skills_dir = kit / "skills"
    if not skills_dir.is_dir():
        print(f"error: {skills_dir} not found", file=sys.stderr)
        return 2

    dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    results, total_errors, total_warnings = [], 0, 0
    names = {}
    for d in dirs:
        sf = d / "SKILL.md"
        if sf.is_file():
            m = re.search(r"^name:\s*(\S+)", sf.read_text(encoding="utf-8"), re.M)
            if m:
                names.setdefault(m.group(1), []).append(d.name)
    for d in dirs:
        errs, warns, info = check_skill(d)
        # duplicate check via frontmatter-name map
        front = info.get("name")
        if front and len(names.get(front, [])) > 1:
            errs.append(f"duplicate skill name '{front}' also defined in {names[front]}")
        results.append({"dir": d.name, **info, "errors": errs, "warnings": warns})
        total_errors += len(errs)
        total_warnings += len(warns)

    # kit-level: declared count in SKILL_MASTER.md vs actual
    master = skills_dir / "SKILL_MASTER.md"
    if not master.is_file():
        total_warnings += 0  # master is optional infrastructure
    else:
        mtext = master.read_text(encoding="utf-8")
        m = re.search(r"\b(\d+)\s+shipped ones\b", mtext)
        if m and int(m.group(1)) != len(dirs):
            total_errors_item = m.group(1)
            total_warnings += 1
            results.append({"dir": "SKILL_MASTER.md",
                            "warnings": [f"SKILL_MASTER says '{total_errors_item} shipped ones' but the kit ships {len(dirs)} skills"],
                            "errors": [], "stale_doc_count": True})

    if args.json:
        print(json.dumps({"skills": results, "errors": total_errors,
                          "warnings": total_warnings}, indent=2))
    else:
        if not results:
            print(f"{RED}error:{RESET} no skills found in {skills_dir}")
            return 1
        width = max(len(r["dir"]) for r in results)
        for r in results:
            errs = r.get("errors", [])
            wns = r.get("warnings", [])
            status = (f"{RED}FAIL{RESET}" if errs else
                      (f"{YELLOW}warn{RESET}" if wns and args.strict else
                       (f"{YELLOW}warn{RESET}" if wns else f"{GREEN}ok{RESET}")))
            detail = f"{r.get('nonempty_lines', 0):>2} lines ~{r.get('est_tokens', 0):>4} tok"
            print(f" {status}  {r['dir'].ljust(width)}  {detail}")
            for e in errs:
                print(f"        {RED}ERROR{RESET} {e}")
            for w in wns:
                print(f"        {YELLOW}WARN {RESET} {w}")
        verdict = "FAIL" if (total_errors or (args.strict and total_warnings)) else "PASS"
        strict_note = " (strict)" if args.strict else ""
        print(f"\n{len(results)} checked{strict_note}: "
              f"{total_errors} error(s), {total_warnings} warning(s) -> {verdict}")

    return 1 if (total_errors or (args.strict and total_warnings)) else 0


if __name__ == "__main__":
    sys.exit(main())
