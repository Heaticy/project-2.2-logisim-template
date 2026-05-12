#!/usr/bin/env python3

from __future__ import annotations

from .logisim_grader import run_one


CASE_NAMES = [
    "p22_localtest",
]


def main() -> int:
    failed = 0
    for case_name in CASE_NAMES:
        failed += run_one(case_name)
    total = len(CASE_NAMES)
    passed = total - failed
    print(f"Passed {passed}/{total} tests")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
