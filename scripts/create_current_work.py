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


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Create a validated current-work item without editing JSON by hand."
    )
    result.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    result.add_argument("--id", required=True, help="Stable id beginning with work-")
    result.add_argument("--title", required=True)
    result.add_argument("--term-id", default=None, help="Defaults to currentTermId")
    result.add_argument("--topic", action="append", required=True, dest="topics")
    result.add_argument("--summary", required=True)
    result.add_argument("--key-finding", action="append", default=[])
    result.add_argument("--open-question", action="append", default=[])
    result.add_argument("--source-ref", action="append", default=[])
    result.add_argument("--relation-type", default="applies")
    result.add_argument("--relation-target", default=None)
    result.add_argument(
        "--relation-note",
        default="Verknüpft die aktuelle Arbeit mit dem bestehenden Wissenskanon.",
    )
    result.add_argument("--authorship", default="anonymized-group")
    result.add_argument("--review-status", default="draft")
    result.add_argument(
        "--publication-status",
        default="local-preview",
        choices=["local-preview", "published"],
    )
    result.add_argument("--uncertainty", type=float, default=0.5)
    result.add_argument(
        "--apply",
        action="store_true",
        help="Write item and update index. Without this flag only a preview is printed.",
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
    term_id = args.term_id or index["currentTermId"]
    if term_id != index["currentTermId"]:
        print("new active work must belong to the current term")
        return 1
    axis_ids = sorted(
        {context["topic_axis"].get(topic, "") for topic in args.topics} - {""}
    )
    relation_target = args.relation_target or args.topics[0]
    item = {
        "schema": context["current_schema"]["dataSchema"],
        "id": args.id,
        "title": args.title,
        "contentLayer": "current-work",
        "lifecycle": "active",
        "reviewStatus": args.review_status,
        "publicationStatus": args.publication_status,
        "termId": term_id,
        "topicIds": args.topics,
        "axisIds": axis_ids,
        "summary": args.summary,
        "keyFindings": args.key_finding,
        "openQuestions": args.open_question,
        "relations": [
            {
                "type": args.relation_type,
                "targetId": relation_target,
                "note": args.relation_note,
            }
        ],
        "sourceRefs": args.source_ref,
        "authorship": {"kind": args.authorship},
        "personalDataIncluded": False,
        "uncertainty": args.uncertainty,
    }
    problems = validate_item(
        item, context, {term["id"] for term in index["terms"]}, args.id
    )
    if problems:
        print("\n".join(problems))
        return 1

    relative_path = f"/data/current-work/items/{args.id}.json"
    item_path = root / relative_path.lstrip("/")
    if item_path.exists() or any(
        entry.get("id") == args.id for entry in index["works"]
    ):
        print(f"current-work item already exists: {args.id}")
        return 1

    print(
        json.dumps({"item": item, "path": relative_path}, ensure_ascii=False, indent=2)
    )
    if not args.apply:
        print(
            "preview only; pass --publication-status published --review-status checked --apply to write"
        )
        return 0
    if args.publication_status != "published":
        print(
            "refusing to write: indexed current work is public; choose --publication-status published explicitly"
        )
        return 1

    items_by_path = {
        entry["path"]: read_json(root / entry["path"].lstrip("/"))
        for entry in index["works"]
    }
    items_by_path[relative_path] = item
    refreshed_index = refresh_index(index, items_by_path, context["current_schema"])
    old_index = index
    try:
        atomic_write_json(item_path, item)
        atomic_write_json(index_path, refreshed_index)
        require_valid_root(root)
    except Exception as error:
        item_path.unlink(missing_ok=True)
        atomic_write_json(index_path, old_index)
        print(f"creation rolled back: {error}")
        return 1
    print(f"created {relative_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
