#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
DOC = re.compile(r"doc-\d{3}")

problems: list[str] = []

excerpts: dict[str, set[str]] = {}
for path in sorted((root / "data" / "excerpts").glob("*.jsonl")):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        excerpt_id = item.get("id")
        if not isinstance(excerpt_id, str) or not excerpt_id:
            problems.append(f"{path}:{line_no}: excerpt id required")
            continue
        locator_text = " ".join(
            str(item.get(key, ""))
            for key in ["id", "sourceLocator", "sourceTitle"]
        )
        docs = set(DOC.findall(locator_text))
        if not docs:
            problems.append(f"{path}:{line_no}: excerpt must expose at least one doc-XXX source reference")
        excerpts[excerpt_id] = docs

for path in sorted((root / "data" / "details").glob("detail-*-v1.json")):
    detail = json.loads(path.read_text(encoding="utf-8"))
    detail_id = detail.get("id", path.name)
    source_refs = set(detail.get("sourceRefs", []))
    excerpt_refs = detail.get("excerptRefs", [])
    excerpt_docs: set[str] = set()
    for excerpt_ref in excerpt_refs:
        if excerpt_ref not in excerpts:
            problems.append(f"{detail_id}: unknown excerptRef {excerpt_ref}")
            continue
        excerpt_docs |= excerpts[excerpt_ref]
    uncovered = sorted(source_refs - excerpt_docs)
    if uncovered:
        problems.append(
            f"{detail_id}: sourceRefs not covered by excerptRefs {uncovered}; "
            f"covered={sorted(excerpt_docs)} excerptRefs={excerpt_refs}"
        )

if problems:
    print("\n".join(problems))
    raise SystemExit(1)

print("detail source alignment validation passed")
