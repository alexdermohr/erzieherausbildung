#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
schema = json.loads((root / "schemas" / "detail.v1.schema.json").read_text(encoding="utf-8"))
learning = json.loads((root / "data" / "learning-map.v1.json").read_text(encoding="utf-8"))
excerpts = []
for path in sorted((root / "data" / "excerpts").glob("*.jsonl")):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            excerpts.append(json.loads(line))

REQ = set(schema["required"])
BLOCKED = set(schema["blockedFields"])
STATUS = set(schema["detailStatuses"])
DOC = re.compile(r"^doc-\d{3}$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
valid_topics = {topic["id"] for axis in learning["axes"] for topic in axis["topics"]}
valid_axes = {axis["id"] for axis in learning["axes"]}
valid_bridge_targets = valid_topics | valid_axes
valid_sources = {source for axis in learning["axes"] for source in axis["sources"]} | {source for axis in learning["axes"] for topic in axis["topics"] for source in topic["sources"]}
excerpt_ids = {item["id"] for item in excerpts}


def nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_string(item) for item in value)


def check_range(value) -> bool:
    return isinstance(value, (int, float)) and 0 <= value <= 1


def validate_bridge(value, where, problems):
    if not isinstance(value, dict):
        problems.append(f"{where}: bridge must be object")
        return
    target_id = value.get("targetId")
    if not nonempty_string(target_id):
        problems.append(f"{where}: bridge targetId required")
    elif target_id not in valid_bridge_targets:
        problems.append(f"{where}: unknown bridge targetId {target_id}")
    if not nonempty_string(value.get("relation")):
        problems.append(f"{where}: bridge relation required")


def validate_detail(item: dict, where: str) -> list[str]:
    problems: list[str] = []
    missing = REQ - set(item)
    if missing:
        problems.append(f"{where}: missing {sorted(missing)}")
    blocked = BLOCKED & set(item)
    if blocked:
        problems.append(f"{where}: blocked fields {sorted(blocked)}")
    if item.get("schema") != schema["dataSchema"]:
        problems.append(f"{where}: bad schema")
    if not nonempty_string(item.get("id")) or not ID.match(str(item.get("id", ""))):
        problems.append(f"{where}: bad id")
    if not nonempty_string(item.get("title")):
        problems.append(f"{where}: title required")
    if not string_list(item.get("topicIds")):
        problems.append(f"{where}: topicIds must be non-empty string list")
    else:
        for topic in item["topicIds"]:
            if topic not in valid_topics:
                problems.append(f"{where}: unknown topicId {topic}")
    if not string_list(item.get("axisIds")):
        problems.append(f"{where}: axisIds must be non-empty string list")
    else:
        for axis in item["axisIds"]:
            if axis not in valid_axes:
                problems.append(f"{where}: unknown axisId {axis}")
    if not string_list(item.get("sourceRefs")):
        problems.append(f"{where}: sourceRefs must be non-empty string list")
    else:
        for source in item["sourceRefs"]:
            if not DOC.match(source):
                problems.append(f"{where}: bad sourceRef {source}")
            if source not in valid_sources:
                problems.append(f"{where}: unknown sourceRef {source}")
    if not string_list(item.get("excerptRefs")):
        problems.append(f"{where}: excerptRefs must be non-empty string list")
    else:
        for excerpt in item["excerptRefs"]:
            if excerpt not in excerpt_ids:
                problems.append(f"{where}: unknown excerptRef {excerpt}")
    for key in ["summary", "detailStatus"]:
        if key in item and not nonempty_string(item.get(key)):
            problems.append(f"{where}: {key} required")
    if item.get("detailStatus") not in STATUS:
        problems.append(f"{where}: bad detailStatus")
    for key in ["coreIdeas", "practiceAnchors", "commonMisunderstandings", "openQuestions"]:
        if not string_list(item.get(key)):
            problems.append(f"{where}: {key} must be non-empty string list")
    if not isinstance(item.get("bridges"), list) or not item.get("bridges"):
        problems.append(f"{where}: bridges must be non-empty list")
    else:
        for index, bridge in enumerate(item["bridges"], 1):
            validate_bridge(bridge, f"{where}:bridges[{index}]", problems)
    if not check_range(item.get("uncertainty")):
        problems.append(f"{where}: bad uncertainty")
    if not check_range(item.get("interpolation")):
        problems.append(f"{where}: bad interpolation")
    policy = item.get("sourcePolicy")
    if not isinstance(policy, dict):
        problems.append(f"{where}: sourcePolicy object required")
    else:
        for key in ["raw_text_committed", "source_refs_only", "no_direct_citation", "local_origin_material_only"]:
            if policy.get(key) is not (False if key == "raw_text_committed" else True):
                problems.append(f"{where}: bad sourcePolicy.{key}")
    return problems


problems: list[str] = []
assert schema["schema"] == "erzieherausbildung.detail.contract.v1"
assert schema["dataSchema"] == "erzieherausbildung.detail.v1"
assert schema["indexSchema"] == "erzieherausbildung.detail_index.v1"
index_path = root / "data" / "details" / "index.v1.json"
if not index_path.exists():
    problems.append("missing data/details/index.v1.json")
else:
    detail_index = json.loads(index_path.read_text(encoding="utf-8"))
    if detail_index.get("schema") != schema["indexSchema"]:
        problems.append("detail index: bad schema")
    for key in schema.get("indexRequired", []):
        if key not in detail_index:
            problems.append(f"detail index: missing {key}")
    coverage = detail_index.get("coverage")
    if not isinstance(coverage, dict):
        problems.append("detail index: coverage object required")
    else:
        for key in schema.get("coverageFields", []):
            if key not in coverage:
                problems.append(f"detail index: coverage missing {key}")
        if coverage.get("coverageStatus") not in set(schema.get("coverageStatuses", [])):
            problems.append("detail index: bad coverageStatus")
        topic_ids = sorted(valid_topics)
        detailed_topic_ids = sorted({topic for entry in detail_index.get("details", []) for topic in entry.get("topicIds", [])})
        missing_topic_ids = sorted(set(topic_ids) - set(detailed_topic_ids))
        if coverage.get("topicCount") != len(topic_ids):
            problems.append("detail index: bad coverage.topicCount")
        if coverage.get("detailCount") != len(detail_index.get("details", [])):
            problems.append("detail index: bad coverage.detailCount")
        if coverage.get("detailedTopicCount") != len(detailed_topic_ids):
            problems.append("detail index: bad coverage.detailedTopicCount")
        if coverage.get("missingTopicCount") != len(missing_topic_ids):
            problems.append("detail index: bad coverage.missingTopicCount")
        if coverage.get("detailedTopicIds") != detailed_topic_ids:
            problems.append("detail index: bad coverage.detailedTopicIds")
        if coverage.get("missingTopicIds") != missing_topic_ids:
            problems.append("detail index: bad coverage.missingTopicIds")
        ratio = round(len(detailed_topic_ids) / len(topic_ids), 3) if topic_ids else 0
        if coverage.get("detailCoverageRatio") != ratio:
            problems.append("detail index: bad coverage.detailCoverageRatio")
        if not coverage.get("epistemicEmpty"):
            problems.append("detail index: missing epistemicEmpty")
        axes = {axis["id"]: [topic["id"] for topic in axis["topics"]] for axis in learning["axes"]}
        by_axis = coverage.get("byAxis")
        if not isinstance(by_axis, list) or len(by_axis) != len(axes):
            problems.append("detail index: bad coverage.byAxis")
        else:
            seen_axes = set()
            for entry in by_axis:
                axis_id = entry.get("axisId")
                if axis_id not in axes:
                    problems.append(f"detail index: unknown coverage axis {axis_id}")
                    continue
                seen_axes.add(axis_id)
                axis_topics = set(axes[axis_id])
                axis_detailed = sorted(axis_topics & set(detailed_topic_ids))
                axis_missing = sorted(axis_topics - set(detailed_topic_ids))
                if entry.get("topicCount") != len(axis_topics):
                    problems.append(f"detail index: bad topicCount for {axis_id}")
                if entry.get("detailedTopicCount") != len(axis_detailed):
                    problems.append(f"detail index: bad detailedTopicCount for {axis_id}")
                if entry.get("detailedTopicIds") != axis_detailed:
                    problems.append(f"detail index: bad detailedTopicIds for {axis_id}")
                if entry.get("missingTopicIds") != axis_missing:
                    problems.append(f"detail index: bad missingTopicIds for {axis_id}")
            if seen_axes != set(axes):
                problems.append("detail index: coverage.byAxis misses axes")
    seen = set()
    for entry in detail_index.get("details", []):
        detail_id = entry.get("id")
        if detail_id in seen:
            problems.append(f"detail index: duplicate id {detail_id}")
        seen.add(detail_id)
        path_text = entry.get("path", "")
        if not path_text.startswith("/data/details/"):
            problems.append(f"detail index: bad path {path_text}")
            continue
        path = root / path_text.lstrip("/")
        if not path.exists():
            problems.append(f"detail index: missing file {path_text}")
            continue
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("id") != detail_id:
            problems.append(f"detail index: id mismatch {path_text}")
        problems.extend(validate_detail(item, path_text))

if problems:
    print("\n".join(problems))
    raise SystemExit(1)
print("detail validation passed")
