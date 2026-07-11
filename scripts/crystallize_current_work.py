#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from current_work_model import (
    atomic_write_json,
    hold_current_work_lock,
    load_context,
    read_json,
    refresh_index,
    require_valid_root,
    validate_decision,
    validate_item,
)


def changed_paths(root: Path) -> set[str]:
    commands = [
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    paths: set[str] = set()
    for command in commands:
        completed = subprocess.run(
            command, cwd=root, check=False, capture_output=True, text=True
        )
        if completed.returncode == 0:
            paths.update(
                line.strip() for line in completed.stdout.splitlines() if line.strip()
            )
    return paths


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Record a validated half-year crystallization decision."
    )
    result.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    result.add_argument("--work-id", required=True)
    result.add_argument(
        "--decision", required=True, choices=["integrated", "archived", "rejected"]
    )
    result.add_argument("--essence", required=True)
    result.add_argument("--decided-on", required=True)
    result.add_argument("--target-id", action="append", default=[])
    result.add_argument("--canon-change-ref", action="append", default=[])
    result.add_argument(
        "--apply",
        action="store_true",
        help="Write decision and update lifecycle. Without this flag only a preview is printed.",
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
    decisions_path = root / "data/current-work/decisions.v1.json"
    index = read_json(index_path)
    decisions_index = read_json(decisions_path)
    entry = next(
        (item for item in index["works"] if item.get("id") == args.work_id), None
    )
    if entry is None:
        print(f"unknown work item: {args.work_id}")
        return 1
    if any(item.get("workId") == args.work_id for item in decisions_index["decisions"]):
        print(f"decision already exists for {args.work_id}")
        return 1

    item_path = root / entry["path"].lstrip("/")
    item = read_json(item_path)
    if item["lifecycle"] not in {"active", "canon-candidate"}:
        print(f"work lifecycle cannot be crystallized: {item['lifecycle']}")
        return 1
    if args.decision == "integrated" and item["lifecycle"] != "canon-candidate":
        print("integrated decision requires lifecycle canon-candidate")
        return 1

    updated_item = dict(item)
    updated_item["lifecycle"] = args.decision
    if args.decision == "rejected":
        updated_item["reviewStatus"] = "rejected"
        updated_item["publicationStatus"] = "withdrawn"
    decision = {
        "schema": context["decision_schema"]["dataSchema"],
        "id": f"decision-{args.work_id}",
        "workId": args.work_id,
        "decision": args.decision,
        "targetIds": args.target_id,
        "essence": args.essence,
        "decidedOn": args.decided_on,
        "decidedBy": "editorial-team",
        "canonChangeRefs": args.canon_change_ref,
    }

    item_problems = validate_item(
        updated_item, context, {term["id"] for term in index["terms"]}, args.work_id
    )
    decision_problems = validate_decision(
        decision, context, {args.work_id: updated_item}, decision["id"]
    )
    if item_problems or decision_problems:
        print("\n".join(item_problems + decision_problems))
        return 1
    if args.decision == "integrated":
        unchanged = sorted(set(args.canon_change_ref) - changed_paths(root))
        if unchanged:
            print(
                f"integrated decision requires changed canon files in this branch: {unchanged}"
            )
            return 1

    print(
        json.dumps(
            {"updatedWork": updated_item, "decision": decision},
            ensure_ascii=False,
            indent=2,
        )
    )
    if not args.apply:
        print("preview only; pass --apply to write")
        return 0

    items_by_path = {
        item_entry["path"]: (
            updated_item
            if item_entry["id"] == args.work_id
            else read_json(root / item_entry["path"].lstrip("/"))
        )
        for item_entry in index["works"]
    }
    refreshed_index = refresh_index(index, items_by_path, context["current_schema"])
    refreshed_decisions = dict(decisions_index)
    refreshed_decisions["decisions"] = sorted(
        [*decisions_index["decisions"], decision], key=lambda item: item["workId"]
    )
    old_item = item
    old_index = index
    old_decisions = decisions_index
    try:
        atomic_write_json(item_path, updated_item)
        atomic_write_json(index_path, refreshed_index)
        atomic_write_json(decisions_path, refreshed_decisions)
        require_valid_root(root)
    except Exception as error:
        atomic_write_json(item_path, old_item)
        atomic_write_json(index_path, old_index)
        atomic_write_json(decisions_path, old_decisions)
        print(f"crystallization rolled back: {error}")
        return 1
    print(f"recorded {decision['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
