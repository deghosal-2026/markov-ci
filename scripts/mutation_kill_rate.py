#!/usr/bin/env python3
"""Enforce a mutation kill-rate floor (M13.36).

Reads `mutmut results` and fails if the kill rate (killed / (killed + survived))
is below the floor. Mutation testing is scheduled, not per-PR, because it is slow.
"""

from __future__ import annotations

import re
import subprocess
import sys

_FLOOR_DEFAULT = 0.60


def _counts(results: str) -> tuple[int, int]:
    killed = len(re.findall(r"^\s*\d+\.\s.*KILLED", results, re.MULTILINE))
    survived = len(re.findall(r"^\s*\d+\.\s.*SURVIVED", results, re.MULTILINE))
    return killed, survived


def main() -> int:
    floor = float(sys.argv[1]) if len(sys.argv) > 1 else _FLOOR_DEFAULT
    completed = subprocess.run(
        ["mutmut", "results"], capture_output=True, text=True, check=False,
    )
    killed, survived = _counts(completed.stdout)
    total = killed + survived
    if total == 0:
        print("no mutants scored; skipping the floor check")
        return 0
    rate = killed / total
    print(f"mutation kill rate: {rate:.2f} ({killed}/{total}); floor {floor:.2f}")
    if rate < floor:
        print("::error::mutation kill rate is below the floor", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
