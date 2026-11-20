#!/usr/bin/env python3
"""Preregistered benchmark Fase 2 (see evals/PREREGISTRATION.md before running).

Runs each preregistered task in an isolated temp dir through a headless host
CLI, records the REAL usage the host reports, and verifies outcomes with the
task's verify.sh. Standard library only.

Honesty contract enforced here:
- No token number is ever synthesized. If the adapter cannot parse the
  host's usage, the run records `usage: null` and the cell is excluded from
  token claims downstream.
- Adapters marked `unverified` are refused unless --allow-unverified is
  passed; such runs are labeled `host_verified: false` in results.

Usage:
  python3 scripts/bench.py --dry-run           # fixtures must fail untouched
  python3 scripts/bench.py --host claude       # full matrix, 3 reps
  python3 scripts/bench.py --host claude --triggers
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "evals" / "tasks"
RUNS = ROOT / "evals" / ".run"
RESULTS = ROOT / "evals" / "results"

ALL_CELLS = ["A", "B", "C", "D"]

def rmtree_force(p: Path) -> None:
    """shutil.rmtree that clears the read-only bits git sets on objects."""
    import os
    import stat

    def onerr(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(p, onerror=onerr)


def shas():
    out = {}
    for name in ("superpowers", "ecc"):
        p = ROOT / "evals" / ".cache" / name
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=p, capture_output=True, text=True)
        out[name] = r.stdout.strip() if r.returncode == 0 else None
    return out

CELL_SOURCES: dict[str, list[Path]] = {
    "A": [],
    "B": sorted(p for p in (ROOT / "skills").iterdir()
                if p.is_dir() and (p / "SKILL.md").is_file()),
    "C": [(ROOT / "evals" / ".cache" / "superpowers" / "skills" / s) for s in (
        "using-superpowers", "test-driven-development", "systematic-debugging",
        "verification-before-completion", "writing-plans", "brainstorming",
        "requesting-code-review")],
    "D": [(ROOT / "evals" / ".cache" / "ecc" / "skills" / s) for s in (
        "tdd-workflow", "security-review", "plan-orchestrate",
        "conventional-commit-review")],
}

# ---- host adapters ----------------------------------------------------------
# VERIFIED=True only after a real headless run produced usage on this machine.

def _vibe_cmd(prompt: str):
    return ["vibe", "--prompt", prompt]


def _vibe_usage(stdout: str, stderr: str, work: Path):
    # Parse only if the CLI actually printed usage. Nothing synthesized.
    try:
        data = json.loads(stdout)
    except Exception:
        return None
    u = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(u, dict):
        return None
    return {
        "input": u.get("input_tokens"),
        "output": u.get("output_tokens"),
        "cache_read": u.get("cache_read_tokens"),
        "model": data.get("model"),
    }


def _claude_cmd(prompt: str):
    return ["claude", "-p", prompt, "--output-format", "json"]


def _claude_usage(stdout: str, stderr: str, work: Path):
    try:
        data = json.loads(stdout)
    except Exception:
        return None
    u = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(u, dict):
        return None
    return {
        "input": u.get("input_tokens"),
        "output": u.get("output_tokens"),
        "cache_read": u.get("cache_read_input_tokens"),
        "model": data.get("model"),
    }


ADAPTERS = {
    # adapter: (build_cmd, parse_usage, verified_on_this_machine)
    "vibe": (_vibe_cmd, _vibe_usage, False),
    "claude": (_claude_cmd, _claude_usage, False),
    "none": (None, None, True),
}


def msys_path(p: Path) -> str:
    """C:\\a\\b -> /c/a/b (bash cannot open backslash paths as arguments)."""
    s = str(p)
    if len(s) > 2 and s[1] == ":":
        return "/" + s[0].lower() + s[2:].replace("\\", "/")
    return s.replace("\\", "/")


def bash_env(home: Path | None = None, cwd: Path | None = None) -> dict:
    """Env for bash child processes on Windows: PATH must be MSYS-style."""
    import os
    env = dict(os.environ)
    p = env.get("PATH", "")
    if ";" in p:  # Windows form -> MSYS form, else bash cannot find commands
        def to_msys(x: str) -> str:
            x = x.strip().strip('"')
            if len(x) > 2 and x[1] == ":":
                return "/" + x[0].lower() + x[2:].replace("\\", "/")
            return x.replace("\\", "/")
        env["PATH"] = ":".join(to_msys(x) for x in p.split(";") if x)
    if home is not None:
        env["HOME"] = str(home)
    return env


def install_cell(cell: str, home: Path, cwd: Path) -> None:
    for src in CELL_SOURCES[cell]:
        if not src.is_dir():
            raise SystemExit(f"cell {cell}: missing source {src} (run make bench-prep)")
    if cell == "B":
        subprocess.run(["bash", msys_path(ROOT / "install.sh")], cwd=cwd,
                       env=bash_env(home=home), check=True, capture_output=True)
        return
    if cell in ("C", "D"):
        target = home / "agents-skills" / "skills"
        target.mkdir(parents=True, exist_ok=True)
        for src in CELL_SOURCES[cell]:
            shutil.copytree(src, target / src.name)
    # cell A: intentionally nothing


def run_one(host: str, task: str, cell: str, rep: int, timeout: int,
            allow_unverified: bool, work: Path) -> dict:
    build_cmd, parse_usage, verified = ADAPTERS[host]
    if build_cmd is None:
        raise SystemExit("--host none only makes sense with --dry-run")
    if not verified and not allow_unverified:
        raise SystemExit(
            f"adapter '{host}' is UNVERIFIED on this machine; pass "
            "--allow-unverified to record host_verified=false results")
    prompt = (TASKS_DIR / task / "task.md").read_text(encoding="utf-8")
    # prompt = the "## Prompt" block, first line after it to EOF
    body = prompt.split("## Prompt", 1)[1].strip()
    home = work.parent / "home"
    home.mkdir(exist_ok=True)
    env = bash_env(home=home)
    install_cell(cell, home, cwd=work.parent)
    cmd = build_cmd(body)
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=work, env=env, capture_output=True,
                              text=True, timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        proc = None
        timed_out = True
    duration = round(time.time() - started, 1)
    record = {"task": task, "cell": cell, "rep": rep, "host": host,
              "host_verified": ADAPTERS[host][2], "timed_out": timed_out,
              "duration_s": duration, "usage": None, "success": False}
    if proc is not None:
        v = parse_usage(proc.stdout or "", proc.stderr or "", work)
        if v:
            v["verified"] = True
            record["usage"] = v
        check = subprocess.run(["bash", msys_path(TASKS_DIR / task / "verify.sh")],
                               cwd=work, env=bash_env(), capture_output=True,
                               timeout=120)
        record["success"] = check.returncode == 0
        record["verify_stderr"] = (check.stderr or "")[-2000:]
    return record


def tasks_list(sel: str | None, limit: int | None) -> list[str]:
    ts = sorted(p.name for p in TASKS_DIR.glob("0*/")) if not sel else sel.split(",")
    return ts[:limit] if limit else ts


def dry_run() -> int:
    """Mechanical prereg check: every untouched fixture must FAIL its verifier."""
    if RUNS.exists():
        rmtree_force(RUNS)
    sys.path.insert(0, str(TASKS_DIR))
    import importlib
    gf = importlib.import_module("gen_fixtures")
    ok = True
    for task in sorted(gf.FIXTURES):
        work = gf.build(task, RUNS)
        r = subprocess.run(["bash", msys_path(TASKS_DIR / task / "verify.sh")],
                           cwd=work, env=bash_env(), capture_output=True, timeout=120)
        status = "OK (fails untouched)" if r.returncode != 0 else "BAD (passes untouched)"
        if r.returncode == 0:
            ok = False
        print(f"  {task:<24} exit={r.returncode} {status}")
    print("PREREG CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", choices=sorted(ADAPTERS), default="none")
    ap.add_argument("--cells", default=",".join(ALL_CELLS))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--tasks", help="comma list, e.g. 01-tdd-discount,08-security-sqli")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-unverified", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        return dry_run()
    if args.host == "none":
        ap.error("real runs need --host (see adapters); 'none' exists only for --dry-run")

    cells = args.cells.split(",")
    unknown = [c for c in cells if c not in ALL_CELLS]
    if unknown:
        ap.error(f"unknown cells: {unknown}")
    sys.path.insert(0, str(TASKS_DIR))
    import importlib
    gf = importlib.import_module("gen_fixtures")
    if RUNS.exists():
        rmtree_force(RUNS)

    kit_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
    out = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "prereg": "evals/PREREGISTRATION.md",
        "kit_commit": kit_sha,
        "competitor_shas": shas(),
        "host": args.host,
        "host_verified": ADAPTERS[args.host][2],
        "reps": args.reps,
        "runs": [],
    }
    for task in tasks_list(args.tasks, args.limit):
        for cell in cells:
            for rep in range(1, args.reps + 1):
                cell_tag = f"{cell.lower()}{rep}"
                work = gf.build(task, RUNS / cell_tag)
                rec = run_one(args.host, task, cell, rep, args.timeout,
                              args.allow_unverified, work)
                out["runs"].append(rec)
                print(f"  {task} {cell}{rep}: success={rec['success']} "
                      f"usage={'real' if rec['usage'] else 'unverified'} "
                      f"({rec['duration_s']}s)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = RESULTS / f"bench-{args.host}-{stamp}.json"
    RESULTS.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"results -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
