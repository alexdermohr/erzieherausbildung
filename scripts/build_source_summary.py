#!/usr/bin/env python3
"""Build an aggregate source summary from a local iCloud source tree.

This deliberately does not copy raw files and does not emit individual filenames.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def extension(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "[noext]"


def summarize_module(path: Path) -> dict[str, Any]:
    files = [item for item in path.rglob("*") if item.is_file()]
    ext = Counter(extension(item) for item in files)
    total_bytes = sum(item.stat().st_size for item in files)
    return {
        "title": path.name,
        "fileCount": len(files),
        "totalBytes": total_bytes,
        "extensions": dict(sorted(ext.items())),
    }


def build(source_root: Path) -> dict[str, Any]:
    semesters = []
    totals = Counter()
    for semester_name in ["1. Semester", "2. Semester"]:
        semester_path = source_root / semester_name
        if not semester_path.is_dir():
            semesters.append({"title": semester_name, "exists": False, "modules": []})
            continue
        modules = []
        for module_path in sorted([item for item in semester_path.iterdir() if item.is_dir()], key=lambda p: p.name.casefold()):
            module = summarize_module(module_path)
            modules.append(module)
            totals["files"] += module["fileCount"]
            totals["bytes"] += module["totalBytes"]
        semesters.append({"title": semester_name, "exists": True, "modules": modules})

    ext_totals = Counter()
    for semester in semesters:
        for module in semester["modules"]:
            ext_totals.update(module["extensions"])

    return {
        "schema": "erzieherausbildung.source-summary.v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceRootHint": "~/iCloud/Drive/inbox",
        "sourceRootObserved": str(source_root),
        "rawFilesCopied": False,
        "privacyMode": "aggregate-no-filenames",
        "expectedNamedFolderFound": (source_root / "erzieherausbildung").is_dir(),
        "semesters": semesters,
        "totals": {
          "files": totals["files"],
          "bytes": totals["bytes"],
          "extensions": dict(sorted(ext_totals.items())),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=os.environ.get("ERZ_SOURCE_ROOT", "~/iCloud/Drive/inbox"))
    parser.add_argument("--output", default="data/source-summary.json")
    args = parser.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    if not source_root.is_dir():
        raise SystemExit(f"source root not found: {source_root}")

    summary = build(source_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output} with {summary['totals']['files']} files aggregated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
