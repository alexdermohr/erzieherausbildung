#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from current_work_model import validate_root


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate current work and crystallization contracts."
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    problems = validate_root(args.root.resolve())
    if problems:
        print("\n".join(problems))
        return 1
    print("current-work validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
