#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
report_path = root / "data" / "source-health.v1.json"
detail_backlog_path = root / "data" / "details" / "backlog.v1.json"
detail_index_path = root / "data" / "details" / "index.v1.json"
learning_path = root / "data" / "learning-map.v1.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
detail_backlog = json.loads(detail_backlog_path.read_text(encoding="utf-8"))
detail_index = json.loads(detail_index_path.read_text(encoding="utf-8"))
learning = json.loads(learning_path.read_text(encoding="utf-8"))

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

empty_or_missing_sources = {item.get("sourceRef") for item in sources if item.get("status") in {"empty", "missing"}}
current_backlog_topic_ids = {entry.get("topicId") for entry in detail_backlog.get("entries", [])}

reported_backlog_impacts = set()
reported_detail_impacts = set()
affected_backlog = report.get("affectedBacklogEntries", [])
if not isinstance(affected_backlog, list):
    problems.append("affectedBacklogEntries must be list")
else:
    for entry in affected_backlog:
        topic_id = entry.get("topicId")
        if topic_id not in current_backlog_topic_ids:
            problems.append(f"{topic_id}: affectedBacklogEntries must match current detail backlog")
        refs = entry.get("affectedSourceRefs", [])
        if not isinstance(refs, list) or not refs:
            problems.append(f"{entry.get('topicId')}: affectedSourceRefs must be non-empty list")
        for ref in refs:
            reported_backlog_impacts.add((topic_id, ref))
            if ref not in empty_or_missing_sources:
                problems.append(f"{topic_id}: affectedSourceRef {ref} is not empty or missing")

details_by_id = {}
for entry in detail_index.get("details", []):
    path_text = entry.get("path", "")
    if path_text.startswith("/"):
        path = root / path_text.lstrip("/")
        if path.exists():
            details_by_id[entry.get("id")] = json.loads(path.read_text(encoding="utf-8"))

topics_by_id = {topic.get("id"): topic for axis in learning.get("axes", []) for topic in axis.get("topics", [])}
affected_details = report.get("affectedDetails", [])
if not isinstance(affected_details, list):
    problems.append("affectedDetails must be list")
else:
    for entry in affected_details:
        detail_id = entry.get("detailId")
        detail = details_by_id.get(detail_id)
        if detail is None:
            problems.append(f"{detail_id}: affectedDetail unknown detailId")
            continue
        topic_id = entry.get("topicId")
        if topic_id not in detail.get("topicIds", []):
            problems.append(f"{detail_id}: affectedDetail topicId not on detail")
        topic = topics_by_id.get(topic_id)
        if topic is None:
            problems.append(f"{entry.get('detailId')}: affectedDetail unknown topicId")
            continue
        empty_refs = entry.get("emptyTopicSourceRefs", [])
        committed_refs = entry.get("committedSourceRefs", [])
        if not isinstance(empty_refs, list) or not empty_refs:
            problems.append(f"{entry.get('detailId')}: emptyTopicSourceRefs must be non-empty list")
        if not isinstance(committed_refs, list) or not committed_refs:
            problems.append(f"{entry.get('detailId')}: committedSourceRefs must be non-empty list")
        if entry.get("status") not in {"covered-by-background-source"}:
            problems.append(f"{detail_id}: affectedDetail bad status")
        if entry.get("title") != topic.get("title"):
            problems.append(f"{detail_id}: affectedDetail title mismatch")
        for ref in empty_refs:
            reported_detail_impacts.add((topic_id, ref, detail_id))
            if ref not in topic.get("sources", []):
                problems.append(f"{detail_id}: emptyTopicSourceRef {ref} not in topic sources")
            if ref not in empty_or_missing_sources:
                problems.append(f"{detail_id}: emptyTopicSourceRef {ref} is not empty or missing")
            if ref in detail.get("sourceRefs", []):
                problems.append(f"{detail_id}: emptyTopicSourceRef {ref} must not be committed detail sourceRef")
        for ref in committed_refs:
            if ref not in detail.get("sourceRefs", []):
                problems.append(f"{entry.get('detailId')}: committedSourceRef {ref} not on detail")
            if ref in empty_or_missing_sources:
                problems.append(f"{entry.get('detailId')}: committedSourceRef {ref} must not be empty or missing")

for topic_id, topic in topics_by_id.items():
    impacted_refs = sorted(set(topic.get("sources", [])) & empty_or_missing_sources)
    if not impacted_refs:
        continue
    detail_ids = [detail_id for detail_id, detail in details_by_id.items() if topic_id in detail.get("topicIds", [])]
    for ref in impacted_refs:
        if topic_id in current_backlog_topic_ids:
            if (topic_id, ref) not in reported_backlog_impacts:
                problems.append(f"{topic_id}: missing affectedBacklogEntries impact for {ref}")
        elif detail_ids:
            if not any((topic_id, ref, detail_id) in reported_detail_impacts for detail_id in detail_ids):
                problems.append(f"{topic_id}: missing affectedDetails impact for {ref}")
        else:
            problems.append(f"{topic_id}: empty/missing source {ref} has no backlog or detail impact")

# Source health is a snapshot. It may improve when local text extraction is repaired.
# The validator checks consistency with the current detail backlog/index and diagnostic metadata only.

if problems:
    print("\n".join(problems))
    raise SystemExit(1)

print("source health validation passed")
