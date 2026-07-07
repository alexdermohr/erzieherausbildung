#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
report_path = root / "data" / "source-health.v1.json"
report = json.loads(report_path.read_text(encoding="utf-8"))

problems: list[str] = []

if report.get("schema") != "erzieherausbildung.source_health.v1":
    problems.append("bad schema")

policy = report.get("sourcePolicy", {})
if policy.get("raw_text_committed") is not False:
    problems.append("raw_text_committed must be false")
if policy.get("diagnostic_metadata_only") is not True:
    problems.append("diagnostic_metadata_only must be true")

sources = report.get("sources", [])
if not isinstance(sources, list) or not sources:
    problems.append("sources must be non-empty list")

summary = report.get("summary", {})
for key in ["sourceCount", "okCount", "emptyCount", "missingCount"]:
    if key not in summary:
        problems.append(f"missing summary field {key}")

if sources:
    if summary.get("sourceCount") != len(sources):
        problems.append("sourceCount mismatch")
    if summary.get("okCount") != sum(1 for item in sources if item.get("status") == "ok"):
        problems.append("okCount mismatch")
    if summary.get("emptyCount") != sum(1 for item in sources if item.get("status") == "empty"):
        problems.append("emptyCount mismatch")
    if summary.get("missingCount") != sum(1 for item in sources if item.get("status") == "missing"):
        problems.append("missingCount mismatch")

    for item in sources:
        if item.get("status") not in {"ok", "empty", "missing"}:
            problems.append(f"{item.get('sourceRef')}: bad status")
        local_path = item.get("localTextPath", "")
        if local_path.startswith("/"):
            problems.append(f"{item.get('sourceRef')}: absolute local path forbidden")
        if ".." in Path(local_path).parts:
            problems.append(f"{item.get('sourceRef')}: parent traversal forbidden")
        if item.get("status") == "empty" and item.get("sizeBytes") != 0:
            problems.append(f"{item.get('sourceRef')}: empty status requires sizeBytes 0")
        if item.get("status") == "missing" and item.get("exists") is not False:
            problems.append(f"{item.get('sourceRef')}: missing status requires exists false")

# Source health is a snapshot. It may improve when local text extraction is repaired.
# The validator checks consistency, not a frozen status for any one document.

if problems:
    print("\n".join(problems))
    raise SystemExit(1)

print("source health validation passed")
