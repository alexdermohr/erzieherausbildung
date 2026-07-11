#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from current_work_model import (
    atomic_write_json,
    hold_current_work_lock,
    load_context,
    read_json,
    refresh_index,
    require_valid_root,
    validate_item,
)


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Promote one checked active work item to a source-bound canon candidate."
    )
    result.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    result.add_argument("--work-id", required=True)
    result.add_argument("--key-finding", action="append", default=[])
    result.add_argument("--source-ref", action="append", default=[])
    result.add_argument(
        "--apply",
        action="store_true",
        help="Write candidate and update index. Without this flag only a preview is printed.",
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
    entry = next(
        (item for item in index["works"] if item.get("id") == args.work_id), None
    )
    if entry is None:
        print(f"unknown work item: {args.work_id}")
        return 1
    item_path = root / entry["path"].lstrip("/")
    item = read_json(item_path)
    if item.get("lifecycle") != "active":
        print(f"only active work can be promoted; found {item.get('lifecycle')}")
        return 1
    if (
        item.get("publicationStatus") != "published"
        or item.get("reviewStatus") != "checked"
    ):
        print("promotion requires checked, published work")
        return 1

    updated = dict(item)
    updated["lifecycle"] = "canon-candidate"
    updated["keyFindings"] = unique([*item.get("keyFindings", []), *args.key_finding])
    updated["sourceRefs"] = unique([*item.get("sourceRefs", []), *args.source_ref])
    problems = validate_item(
        updated, context, {term["id"] for term in index["terms"]}, args.work_id
    )
    if problems:
        print("\n".join(problems))
        return 1

    print(json.dumps(updated, ensure_ascii=False, indent=2))
    if not args.apply:
        print("preview only; pass --apply to promote")
        return 0

    items_by_path = {
        item_entry["path"]: (
            updated
            if item_entry["id"] == args.work_id
            else read_json(root / item_entry["path"].lstrip("/"))
        )
        for item_entry in index["works"]
    }
    refreshed_index = refresh_index(index, items_by_path, context["current_schema"])
    try:
        atomic_write_json(item_path, updated)
        atomic_write_json(index_path, refreshed_index)
        require_valid_root(root)
    except Exception as error:
        atomic_write_json(item_path, item)
        atomic_write_json(index_path, index)
        print(f"promotion rolled back: {error}")
        return 1
    print(f"promoted {args.work_id} to canon-candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
