#!/usr/bin/env python3
"""Run the fixed suite in fresh baseline and kit workspaces via a host adapter."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def verify(task, work):
    return subprocess.run([sys.executable, "-E", "-B", "-c", task["check"]], cwd=work,
                          capture_output=True, timeout=10).returncode == 0


def activation(task, observed):
    if not isinstance(observed, list) or not all(isinstance(x, str) for x in observed):
        return None
    return ((task["expected"] is None or task["expected"] in observed)
            and not set(task["forbidden"]).intersection(observed))


def run(task, mode, args):
    with tempfile.TemporaryDirectory(prefix="tokenless-bench-") as tmp:
        work = Path(tmp)
        fixture = work / task.get("path", "app.py")
        fixture.write_text(task["seed"], encoding="utf-8")
        if mode == "dry-run":
            rejects_seed = not verify(task, work)
            fixture.write_text(task["solution"], encoding="utf-8")
            return {"task": task["id"], "mode": mode, "pass": rejects_seed and verify(task, work)}

        env = dict(os.environ, TOKENLESS_BENCH_MODE=mode)
        if mode == "kit":
            subprocess.run([str(ROOT / "install.sh"), "project"], cwd=work, check=True,
                           capture_output=True, timeout=10)
        try:
            proc = subprocess.run(args.adapter, input=task["prompt"], cwd=work, env=env,
                                  capture_output=True, text=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            return {"task": task["id"], "mode": mode, "pass": False, "error": "adapter timeout",
                    "tokens": None, "activation_pass": None}
        try:
            report = json.loads(proc.stdout) if proc.returncode == 0 else {}
        except ValueError:
            report = {}
        if not isinstance(report, dict):
            report = {}
        tokens = report.get("tokens")
        observed = report.get("activated_skills")
        return {"task": task["id"], "mode": mode, "pass": proc.returncode == 0 and verify(task, work),
                "adapter_exit": proc.returncode, "tokens": tokens if type(tokens) is int and tokens >= 0 else None,
                "activation_pass": activation(task, observed) if mode == "kit" else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate fixtures, no host call")
    parser.add_argument("--timeout", type=int, default=300, help="seconds per adapter run")
    parser.add_argument("--adapter", nargs=argparse.REMAINDER, help="command receiving the task on stdin")
    args = parser.parse_args()
    if args.dry_run == bool(args.adapter) or args.timeout <= 0:
        parser.error("choose exactly one of --dry-run and --adapter; timeout must be positive")
    tasks = json.loads((ROOT / "evals/tasks.json").read_text(encoding="utf-8"))
    if not tasks:
        parser.error("no eval tasks found")
    modes = ("dry-run",) if args.dry_run else ("baseline", "kit")
    passed = True
    for task in tasks:
        for mode in modes:
            result = run(task, mode, args)
            print(json.dumps(result), flush=True)
            passed &= result["pass"] and result.get("activation_pass") is not False
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
