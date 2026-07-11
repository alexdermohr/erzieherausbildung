#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from current_work_model import (
    atomic_write_json,
    hold_current_work_lock,
    load_context,
    parse_date,
    read_json,
    refresh_index,
    require_valid_root,
    validate_term,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Close a resolved term and open the next current term."
    )
    result.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    result.add_argument("--id", required=True, dest="term_id")
    result.add_argument("--label", required=True)
    result.add_argument("--starts-on", required=True)
    result.add_argument("--ends-on", required=True)
    result.add_argument(
        "--apply",
        action="store_true",
        help="Write term rollover. Without this flag only a preview is printed.",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    root = args.root.resolve()
    try:
        hold_current_work_lock(root)
    except RuntimeError as error:
        print(str(error))
        return 1
    require_valid_root(root)
    context = load_context(root)
    index_path = root / "data/current-work/index.v1.json"
    index = read_json(index_path)
    current = next(
        term for term in index["terms"] if term["id"] == index["currentTermId"]
    )
    unresolved = [
        entry["id"]
        for entry in index["works"]
        if entry.get("termId") == current["id"]
        and entry.get("lifecycle") in {"active", "canon-candidate"}
    ]
    if unresolved:
        print(f"cannot close {current['id']}; unresolved work remains: {unresolved}")
        return 1
    if any(term["id"] == args.term_id for term in index["terms"]):
        print(f"term already exists: {args.term_id}")
        return 1

    new_term = {
        "schema": context["current_schema"]["termSchema"],
        "id": args.term_id,
        "label": args.label,
        "startsOn": args.starts_on,
        "endsOn": args.ends_on,
        "status": "current",
    }
    problems = validate_term(new_term, context["current_schema"], args.term_id)
    old_end = parse_date(current.get("endsOn"))
    new_start = parse_date(new_term.get("startsOn"))
    if old_end and new_start and new_start <= old_end:
        problems.append(f"{args.term_id}: startsOn must be after current term endsOn")
    if problems:
        print("\n".join(problems))
        return 1

    terms = []
    for term in index["terms"]:
        updated_term = dict(term)
        if term["id"] == current["id"]:
            updated_term["status"] = "closed"
        terms.append(updated_term)
    terms.append(new_term)
    refreshed = dict(index)
    refreshed["terms"] = terms
    refreshed["currentTermId"] = new_term["id"]
    items_by_path = {
        entry["path"]: read_json(root / entry["path"].lstrip("/"))
        for entry in index["works"]
    }
    refreshed = refresh_index(refreshed, items_by_path, context["current_schema"])

    print(
        json.dumps(
            {"closedTermId": current["id"], "newTerm": new_term},
            ensure_ascii=False,
            indent=2,
        )
    )
    if not args.apply:
        print("preview only; pass --apply to roll over")
        return 0
    try:
        atomic_write_json(index_path, refreshed)
        require_valid_root(root)
    except Exception as error:
        atomic_write_json(index_path, index)
        print(f"term rollover rolled back: {error}")
        return 1
    print(f"closed {current['id']} and opened {new_term['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
