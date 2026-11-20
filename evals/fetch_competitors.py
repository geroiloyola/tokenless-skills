#!/usr/bin/env python3
"""Fetch pinned competitor repos into evals/.cache/ (never committed).

Pinned by commit SHA per evals/PREREGISTRATION.md. Both projects are MIT;
their LICENSE and copyright stay inside the cached clones and are attributed
here and in every results file. Standard library only.

Usage: python3 evals/fetch_competitors.py [--skip-existing]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent / ".cache"

PINNED = {
    "superpowers": {
        "repo": "https://github.com/obra/superpowers.git",
        "sha": "22f0b463e7a5e579904dd6211a520321035526f7",
        "license": "MIT", "attribution": "Jesse Vincent (obra) - superpowers",
    },
    "ecc": {
        "repo": "https://github.com/affaan-m/ECC.git",
        "sha": "4adeee6732a12d1540f49a4d50a38ce8c97f9a53",
        "license": "MIT", "attribution": "affaan-m - Everything Claude Code (ECC)",
    },
}


def pinned_sha(path: Path) -> str | None:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-existing", action="store_true",
                    help="keep cached checkouts that already match their pin")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    rc = 0
    for name, spec in PINNED.items():
        dest = CACHE / name
        if dest.exists() and pinned_sha(dest) == spec["sha"]:
            print(f"  {name}: already at pinned SHA")
            if args.skip_existing:
                continue
        if dest.exists():
            subprocess.run(["git", "fetch", "-q", "origin"], cwd=dest, check=True)
            subprocess.run(["git", "checkout", "-q", spec["sha"]], cwd=dest, check=True)
            subprocess.run(["git", "clean", "-qfd"], cwd=dest, check=True)
        else:
            subprocess.run(["git", "clone", "-q", spec["repo"], str(dest)], check=True)
            subprocess.run(["git", "checkout", "-q", spec["sha"]], cwd=dest, check=True)
        actual = pinned_sha(dest)
        ok = actual == spec["sha"]
        print(f"  {name}: pinned={spec['sha'][:12]} actual={(actual or 'none')[:12]} "
              f"[{spec['license']}; {spec['attribution']}] {'OK' if ok else 'MISMATCH'}")
        rc = 0 if ok else 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
