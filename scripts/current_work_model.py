#!/usr/bin/env python3
from __future__ import annotations

import atexit
import fcntl
import json
import os
import re
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
WORK_ID = re.compile(r"^work-[a-z0-9][a-z0-9-]*$")
DOC_ID = re.compile(r"^doc-\d{3}$")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def hold_current_work_lock(root: Path) -> None:
    lock_path = root / "data/current-work/.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        handle.close()
        raise RuntimeError(
            "another current-work mutation is already running"
        ) from error
    atexit.register(handle.close)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(nonempty_string(item) for item in value)
    )


def recursive_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(recursive_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(recursive_keys(nested))
    return keys


def parse_date(value: Any) -> date | None:
    if not nonempty_string(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def load_context(root: Path) -> dict[str, Any]:
    current_schema = read_json(root / "schemas/current-work.v1.schema.json")
    decision_schema = read_json(root / "schemas/crystallization.v1.schema.json")
    learning = read_json(root / "data/learning-map.v1.json")
    details = read_json(root / "data/details/index.v1.json")
    theories = read_json(root / "data/theory-catalog.v1.json")
    inventory = read_json(root / "data/machine-readable-inventory.json")

    topic_axis: dict[str, str] = {}
    valid_axes = {axis["id"] for axis in learning["axes"]}
    for axis in learning["axes"]:
        for topic in axis["topics"]:
            topic_axis[topic["id"]] = axis["id"]

    valid_details = {item["id"] for item in details["details"]}
    detail_paths = {item["id"]: item["path"].lstrip("/") for item in details["details"]}
    detail_paths_by_target: dict[str, set[str]] = {}
    for item in details["details"]:
        detail_path = item["path"].lstrip("/")
        for target_id in [*item.get("topicIds", []), *item.get("axisIds", [])]:
            detail_paths_by_target.setdefault(target_id, set()).add(detail_path)
    valid_theories = {item["id"] for item in theories["entries"]}
    valid_sources = {f"doc-{item['ordinal']:03d}" for item in inventory["documents"]}

    return {
        "root": root,
        "current_schema": current_schema,
        "decision_schema": decision_schema,
        "valid_axes": valid_axes,
        "topic_axis": topic_axis,
        "valid_topics": set(topic_axis),
        "valid_details": valid_details,
        "detail_paths": detail_paths,
        "detail_paths_by_target": detail_paths_by_target,
        "valid_theories": valid_theories,
        "valid_sources": valid_sources,
        "valid_targets": valid_axes | set(topic_axis) | valid_details | valid_theories,
    }


def validate_term(term: Any, schema: dict[str, Any], where: str) -> list[str]:
    problems: list[str] = []
    if not isinstance(term, dict):
        return [f"{where}: term must be object"]
    allowed_fields = {"schema", "id", "label", "startsOn", "endsOn", "status"}
    unexpected = set(term) - allowed_fields
    if unexpected:
        problems.append(f"{where}: unexpected fields {sorted(unexpected)}")
    if term.get("schema") != schema["termSchema"]:
        problems.append(f"{where}: bad schema")
    term_id = term.get("id")
    if not nonempty_string(term_id) or not ID.match(str(term_id)):
        problems.append(f"{where}: bad id")
    if not nonempty_string(term.get("label")):
        problems.append(f"{where}: label required")
    start = parse_date(term.get("startsOn"))
    end = parse_date(term.get("endsOn"))
    if start is None:
        problems.append(f"{where}: bad startsOn")
    if end is None:
        problems.append(f"{where}: bad endsOn")
    if start and end and start > end:
        problems.append(f"{where}: startsOn after endsOn")
    status = term.get("status")
    if not nonempty_string(status) or status not in set(schema["termStatuses"]):
        problems.append(f"{where}: bad status")
    return problems


def validate_item(
    item: Any, context: dict[str, Any], term_ids: set[str], where: str
) -> list[str]:
    schema = context["current_schema"]
    problems: list[str] = []
    if not isinstance(item, dict):
        return [f"{where}: item must be object"]

    required = set(schema["required"])
    missing = required - set(item)
    if missing:
        problems.append(f"{where}: missing {sorted(missing)}")
    unexpected = set(item) - required - set(schema.get("optional", []))
    if unexpected:
        problems.append(f"{where}: unexpected fields {sorted(unexpected)}")
    blocked = set(schema["blockedFields"]) & recursive_keys(item)
    if blocked:
        problems.append(f"{where}: blocked fields {sorted(blocked)}")
    if item.get("schema") != schema["dataSchema"]:
        problems.append(f"{where}: bad schema")

    work_id = item.get("id")
    if not nonempty_string(work_id) or not WORK_ID.match(str(work_id)):
        problems.append(f"{where}: bad id")
    if not nonempty_string(item.get("title")):
        problems.append(f"{where}: title required")
    content_layer = item.get("contentLayer")
    if not nonempty_string(content_layer) or content_layer not in set(
        schema["contentLayers"]
    ):
        problems.append(f"{where}: bad contentLayer")

    lifecycle = item.get("lifecycle")
    review_status = item.get("reviewStatus")
    publication_status = item.get("publicationStatus")
    if not nonempty_string(lifecycle) or lifecycle not in set(schema["lifecycles"]):
        problems.append(f"{where}: bad lifecycle")
    if not nonempty_string(review_status) or review_status not in set(
        schema["reviewStatuses"]
    ):
        problems.append(f"{where}: bad reviewStatus")
    if not nonempty_string(publication_status) or publication_status not in set(
        schema["publicationStatuses"]
    ):
        problems.append(f"{where}: bad publicationStatus")
    if publication_status == "published" and review_status != "checked":
        problems.append(f"{where}: published work requires checked reviewStatus")
    if publication_status == "withdrawn" and lifecycle != "rejected":
        problems.append(
            f"{where}: withdrawn publicationStatus requires rejected lifecycle"
        )
    if lifecycle == "rejected" and publication_status != "withdrawn":
        problems.append(
            f"{where}: rejected lifecycle requires withdrawn publicationStatus"
        )
    term_id = item.get("termId")
    if not nonempty_string(term_id) or term_id not in term_ids:
        problems.append(f"{where}: unknown termId {term_id}")

    topic_ids = item.get("topicIds")
    axis_ids = item.get("axisIds")
    if not string_list(topic_ids):
        problems.append(f"{where}: topicIds must be non-empty string list")
        topic_ids = []
    if not string_list(axis_ids):
        problems.append(f"{where}: axisIds must be non-empty string list")
        axis_ids = []
    if len(topic_ids) != len(set(topic_ids)):
        problems.append(f"{where}: duplicate topicIds")
    if len(axis_ids) != len(set(axis_ids)):
        problems.append(f"{where}: duplicate axisIds")
    for topic_id in topic_ids:
        if topic_id not in context["valid_topics"]:
            problems.append(f"{where}: unknown topicId {topic_id}")
        elif context["topic_axis"][topic_id] not in axis_ids:
            problems.append(
                f"{where}: topicId {topic_id} misses its axis {context['topic_axis'][topic_id]}"
            )
    for axis_id in axis_ids:
        if axis_id not in context["valid_axes"]:
            problems.append(f"{where}: unknown axisId {axis_id}")

    if not nonempty_string(item.get("summary")):
        problems.append(f"{where}: summary required")
    for key in ["keyFindings", "openQuestions"]:
        if not string_list(item.get(key), allow_empty=True):
            problems.append(f"{where}: {key} must be string list")

    relations = item.get("relations")
    if not isinstance(relations, list) or not relations:
        problems.append(f"{where}: relations must be non-empty list")
    else:
        for index, relation in enumerate(relations, 1):
            relation_where = f"{where}:relations[{index}]"
            if not isinstance(relation, dict):
                problems.append(f"{relation_where}: relation must be object")
                continue
            unexpected_relation_fields = set(relation) - {"type", "targetId", "note"}
            if unexpected_relation_fields:
                problems.append(
                    f"{relation_where}: unexpected fields {sorted(unexpected_relation_fields)}"
                )
            relation_type = relation.get("type")
            if not nonempty_string(relation_type) or relation_type not in set(
                schema["relationTypes"]
            ):
                problems.append(f"{relation_where}: bad type")
            target_id = relation.get("targetId")
            if not nonempty_string(target_id):
                problems.append(f"{relation_where}: targetId must be non-empty string")
            elif target_id not in context["valid_targets"]:
                problems.append(f"{relation_where}: unknown targetId {target_id}")
            if not nonempty_string(relation.get("note")):
                problems.append(f"{relation_where}: note required")

    source_refs = item.get("sourceRefs")
    if not string_list(source_refs, allow_empty=True):
        problems.append(f"{where}: sourceRefs must be string list")
        source_refs = []
    for source_ref in source_refs:
        if not DOC_ID.match(source_ref) or source_ref not in context["valid_sources"]:
            problems.append(f"{where}: unknown sourceRef {source_ref}")

    authorship = item.get("authorship")
    if not isinstance(authorship, dict) or set(authorship) != {"kind"}:
        problems.append(f"{where}: authorship must contain only kind")
    else:
        authorship_kind = authorship.get("kind")
        if not nonempty_string(authorship_kind) or authorship_kind not in set(
            schema["authorshipKinds"]
        ):
            problems.append(f"{where}: bad authorship.kind")
    if item.get("personalDataIncluded") is not False:
        problems.append(f"{where}: personalDataIncluded must be false")
    uncertainty = item.get("uncertainty")
    if (
        not isinstance(uncertainty, (int, float))
        or isinstance(uncertainty, bool)
        or not 0 <= uncertainty <= 1
    ):
        problems.append(f"{where}: bad uncertainty")

    if isinstance(lifecycle, str) and lifecycle in {"canon-candidate", "integrated"}:
        if review_status != "checked":
            problems.append(f"{where}: {lifecycle} requires checked reviewStatus")
        if not item.get("keyFindings"):
            problems.append(f"{where}: {lifecycle} requires keyFindings")
        if not source_refs:
            problems.append(f"{where}: {lifecycle} requires sourceRefs")
    if lifecycle == "rejected" and review_status != "rejected":
        problems.append(f"{where}: rejected lifecycle requires rejected reviewStatus")
    if lifecycle != "rejected" and review_status == "rejected":
        problems.append(f"{where}: rejected reviewStatus requires rejected lifecycle")
    return problems


def canonical_change_ref_valid(context: dict[str, Any], value: str) -> bool:
    if not nonempty_string(value):
        return False
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return False
    allowed = {
        *context["detail_paths"].values(),
        "data/learning-map.v1.json",
        "data/knowledge-network.v1.json",
        "data/theory-catalog.v1.json",
    }
    return value in allowed and (context["root"] / relative).is_file()


def canon_refs_cover_targets(
    context: dict[str, Any], target_ids: list[str], refs: list[str]
) -> list[str]:
    problems: list[str] = []
    ref_set = set(refs)
    structural_refs = {"data/learning-map.v1.json", "data/knowledge-network.v1.json"}
    for target_id in target_ids:
        if target_id in context["valid_details"]:
            required = context["detail_paths"][target_id]
            if required not in ref_set:
                problems.append(
                    f"targetId {target_id} requires canonChangeRef {required}"
                )
        elif target_id in context["valid_theories"]:
            required = "data/theory-catalog.v1.json"
            if required not in ref_set:
                problems.append(
                    f"targetId {target_id} requires canonChangeRef {required}"
                )
        elif target_id in context["valid_topics"] or target_id in context["valid_axes"]:
            related = context["detail_paths_by_target"].get(target_id, set())
            if not (ref_set & (structural_refs | related)):
                problems.append(
                    f"targetId {target_id} requires a matching learning-map, knowledge-network or detail canonChangeRef"
                )
    return problems


def validate_decision(
    decision: Any,
    context: dict[str, Any],
    work_by_id: dict[str, dict[str, Any]],
    where: str,
) -> list[str]:
    schema = context["decision_schema"]
    problems: list[str] = []
    if not isinstance(decision, dict):
        return [f"{where}: decision must be object"]
    required = set(schema["required"])
    missing = required - set(decision)
    if missing:
        problems.append(f"{where}: missing {sorted(missing)}")
    unexpected = set(decision) - required
    if unexpected:
        problems.append(f"{where}: unexpected fields {sorted(unexpected)}")
    blocked = set(schema["blockedFields"]) & recursive_keys(decision)
    if blocked:
        problems.append(f"{where}: blocked fields {sorted(blocked)}")
    if decision.get("schema") != schema["dataSchema"]:
        problems.append(f"{where}: bad schema")
    work_id = decision.get("workId")
    if not nonempty_string(work_id):
        problems.append(f"{where}: workId must be non-empty string")
        work = None
    else:
        work = work_by_id.get(work_id)
    if (
        not nonempty_string(decision.get("id"))
        or decision.get("id") != f"decision-{work_id}"
    ):
        problems.append(f"{where}: id must equal decision-<workId>")
    if work is None:
        problems.append(f"{where}: unknown workId {work_id}")
    decision_value = decision.get("decision")
    if not nonempty_string(decision_value) or decision_value not in set(
        schema["decisions"]
    ):
        problems.append(f"{where}: bad decision")
    if work is not None and work.get("lifecycle") != decision_value:
        problems.append(f"{where}: decision does not match work lifecycle")
    target_ids = decision.get("targetIds")
    if not string_list(target_ids, allow_empty=True):
        problems.append(f"{where}: targetIds must be string list")
        target_ids = []
    else:
        for target_id in target_ids:
            if target_id not in context["valid_targets"]:
                problems.append(f"{where}: unknown targetId {target_id}")
    if not nonempty_string(decision.get("essence")):
        problems.append(f"{where}: essence required")
    if parse_date(decision.get("decidedOn")) is None:
        problems.append(f"{where}: bad decidedOn")
    decided_by = decision.get("decidedBy")
    if not nonempty_string(decided_by) or decided_by not in set(
        schema["decisionRoles"]
    ):
        problems.append(f"{where}: bad decidedBy")
    refs = decision.get("canonChangeRefs")
    if not string_list(refs, allow_empty=True):
        problems.append(f"{where}: canonChangeRefs must be string list")
        refs = []

    if decision_value == "integrated":
        if not decision.get("targetIds"):
            problems.append(f"{where}: integrated decision requires targetIds")
        if not refs:
            problems.append(f"{where}: integrated decision requires canonChangeRefs")
        for ref in refs:
            if not canonical_change_ref_valid(context, ref):
                problems.append(f"{where}: invalid canonChangeRef {ref}")
        for target_problem in canon_refs_cover_targets(context, target_ids, refs):
            problems.append(f"{where}: {target_problem}")
        if work is not None and work.get("reviewStatus") != "checked":
            problems.append(f"{where}: integrated work must be checked")
    elif isinstance(decision_value, str) and decision_value in {
        "archived",
        "rejected",
    }:
        if decision.get("targetIds"):
            problems.append(
                f"{where}: {decision_value} decision must not have targetIds"
            )
        if refs:
            problems.append(
                f"{where}: {decision_value} decision must not have canonChangeRefs"
            )
    return problems


def index_entry(item: dict[str, Any], path: str) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "path": path,
        "termId": item.get("termId"),
        "topicIds": item.get("topicIds"),
        "axisIds": item.get("axisIds"),
        "lifecycle": item.get("lifecycle"),
        "reviewStatus": item.get("reviewStatus"),
        "publicationStatus": item.get("publicationStatus"),
    }


def coverage_for(
    index: dict[str, Any], works: list[dict[str, Any]], schema: dict[str, Any]
) -> dict[str, Any]:
    lifecycle_counts = Counter(
        value for item in works if nonempty_string(value := item.get("lifecycle"))
    )
    review_counts = Counter(
        value for item in works if nonempty_string(value := item.get("reviewStatus"))
    )
    current_term_id = index.get("currentTermId")
    current_works = [
        item
        for item in works
        if item.get("termId") == current_term_id
        and isinstance(item.get("lifecycle"), str)
        and item.get("lifecycle") in {"active", "canon-candidate"}
    ]
    published_current_works = [
        item for item in current_works if item.get("publicationStatus") == "published"
    ]
    topics_with_current_work: set[str] = set()
    for item in published_current_works:
        topic_ids = item.get("topicIds")
        if string_list(topic_ids, allow_empty=True):
            topics_with_current_work.update(topic_ids)
    return {
        "workCount": len(works),
        "currentTermWorkCount": len(current_works),
        "publishedCurrentTermWorkCount": len(published_current_works),
        "topicCountWithCurrentWork": len(topics_with_current_work),
        "byLifecycle": {key: lifecycle_counts[key] for key in schema["lifecycles"]},
        "byReviewStatus": {key: review_counts[key] for key in schema["reviewStatuses"]},
    }


def refresh_index(
    index: dict[str, Any],
    items_by_path: dict[str, dict[str, Any]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    entries = [
        index_entry(item, path)
        for path, item in sorted(items_by_path.items(), key=lambda pair: pair[1]["id"])
    ]
    refreshed = dict(index)
    refreshed["works"] = entries
    refreshed["coverage"] = coverage_for(
        refreshed, list(items_by_path.values()), schema
    )
    return refreshed


def validate_root(root: Path) -> list[str]:
    try:
        context = load_context(root)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return [f"current-work context could not be loaded: {error}"]
    current_schema = context["current_schema"]
    decision_schema = context["decision_schema"]
    problems: list[str] = []

    if current_schema.get("schema") != "erzieherausbildung.current_work.contract.v1":
        problems.append("current-work contract: bad schema")
    if (
        decision_schema.get("schema")
        != "erzieherausbildung.crystallization.contract.v1"
    ):
        problems.append("crystallization contract: bad schema")

    index_path = root / "data/current-work/index.v1.json"
    decisions_path = root / "data/current-work/decisions.v1.json"
    if not index_path.exists():
        return problems + ["missing data/current-work/index.v1.json"]
    if not decisions_path.exists():
        return problems + ["missing data/current-work/decisions.v1.json"]

    try:
        index = read_json(index_path)
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"current-work index could not be read: {error}")
        return problems
    try:
        decisions_index = read_json(decisions_path)
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"crystallization index could not be read: {error}")
        return problems
    if not isinstance(index, dict):
        problems.append("current-work index: top level must be object")
        return problems
    if not isinstance(decisions_index, dict):
        problems.append("crystallization index: top level must be object")
        return problems
    expected_index_fields = {
        "schema",
        "currentTermId",
        "terms",
        "works",
        "coverage",
        "emptyState",
    }
    if set(index) != expected_index_fields:
        problems.append(
            f"current-work index: fields differ; expected {sorted(expected_index_fields)}"
        )
    if index.get("schema") != current_schema["indexSchema"]:
        problems.append("current-work index: bad schema")
    terms = index.get("terms")
    if not isinstance(terms, list) or not terms:
        problems.append("current-work index: terms must be non-empty list")
        terms = []
    term_ids: set[str] = set()
    current_terms: list[str] = []
    term_ranges: list[tuple[date, date, str]] = []
    for position, term in enumerate(terms, 1):
        problems.extend(validate_term(term, current_schema, f"term[{position}]"))
        if isinstance(term, dict) and nonempty_string(term.get("id")):
            if term["id"] in term_ids:
                problems.append(f"term[{position}]: duplicate id {term['id']}")
            term_ids.add(term["id"])
            if term.get("status") == "current":
                current_terms.append(term["id"])
            start = parse_date(term.get("startsOn"))
            end = parse_date(term.get("endsOn"))
            if start is not None and end is not None:
                term_ranges.append((start, end, term["id"]))
    for previous, current in zip(
        sorted(term_ranges), sorted(term_ranges)[1:], strict=False
    ):
        if current[0] <= previous[1]:
            problems.append(
                f"terms {previous[2]} and {current[2]} overlap or share a date"
            )
    if len(current_terms) != 1:
        problems.append("current-work index: exactly one current term required")
    current_term_id = index.get("currentTermId")
    if not nonempty_string(current_term_id) or current_term_id not in term_ids:
        problems.append("current-work index: currentTermId unknown")
    if current_terms and index.get("currentTermId") != current_terms[0]:
        problems.append("current-work index: currentTermId does not match current term")
    if not nonempty_string(index.get("emptyState")):
        problems.append("current-work index: emptyState required")

    works_entries = index.get("works")
    if not isinstance(works_entries, list):
        problems.append("current-work index: works must be list")
        works_entries = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    item_dir = root / "data/current-work/items"
    resolved_item_dir = item_dir.resolve()
    items_by_path: dict[str, dict[str, Any]] = {}
    work_by_id: dict[str, dict[str, Any]] = {}
    for position, entry in enumerate(works_entries, 1):
        where = f"current-work index entry[{position}]"
        if not isinstance(entry, dict):
            problems.append(f"{where}: entry must be object")
            continue
        work_id = entry.get("id")
        path_text = entry.get("path")
        if not nonempty_string(work_id) or not WORK_ID.match(work_id):
            problems.append(f"{where}: bad id {work_id}")
            continue
        if work_id in seen_ids:
            problems.append(f"{where}: duplicate id {work_id}")
        seen_ids.add(work_id)
        expected_path_text = f"/data/current-work/items/{work_id}.json"
        if path_text != expected_path_text:
            problems.append(
                f"{where}: path must equal {expected_path_text}; found {path_text}"
            )
            continue
        if path_text in seen_paths:
            problems.append(f"{where}: duplicate path {path_text}")
        seen_paths.add(path_text)
        path = root / path_text.lstrip("/")
        if path.is_symlink() or path.resolve().parent != resolved_item_dir:
            problems.append(f"{where}: path must be regular file in item directory")
            continue
        if not path.is_file():
            problems.append(f"{where}: missing file {path_text}")
            continue
        try:
            item = read_json(path)
        except (OSError, json.JSONDecodeError) as error:
            problems.append(f"{where}: item could not be read: {error}")
            continue
        problems.extend(validate_item(item, context, term_ids, path_text))
        if not isinstance(item, dict):
            continue
        lifecycle = item.get("lifecycle")
        if (
            isinstance(lifecycle, str)
            and lifecycle
            in {
                "active",
                "canon-candidate",
            }
            and item.get("termId") != index.get("currentTermId")
        ):
            problems.append(
                f"{where}: active or candidate work must belong to currentTermId"
            )
        publication_status = item.get("publicationStatus")
        if not isinstance(publication_status, str) or publication_status not in {
            "published",
            "withdrawn",
        }:
            problems.append(f"{where}: indexed work must be published or withdrawn")
        if item.get("id") != work_id:
            problems.append(f"{where}: id mismatch")
        expected = index_entry(item, path_text)
        if entry != expected:
            problems.append(f"{where}: metadata differs from item")
        items_by_path[path_text] = item
        if nonempty_string(item.get("id")):
            work_by_id[item["id"]] = item

    actual_paths: set[str] = set()
    for path in item_dir.glob("*.json"):
        if path.is_symlink() or path.resolve().parent != resolved_item_dir:
            problems.append(f"current-work items: unsafe file {path.name}")
            continue
        actual_paths.add(f"/{path.relative_to(root).as_posix()}")
    if actual_paths != seen_paths:
        missing_from_index = sorted(actual_paths - seen_paths)
        missing_files = sorted(seen_paths - actual_paths)
        if missing_from_index:
            problems.append(f"current-work index: unlisted files {missing_from_index}")
        if missing_files:
            problems.append(
                f"current-work index: missing indexed files {missing_files}"
            )

    expected_coverage = coverage_for(
        index, list(items_by_path.values()), current_schema
    )
    if index.get("coverage") != expected_coverage:
        problems.append("current-work index: coverage differs from items")

    expected_decision_index_fields = {"schema", "decisions"}
    if set(decisions_index) != expected_decision_index_fields:
        problems.append(
            "crystallization index: fields differ; "
            f"expected {sorted(expected_decision_index_fields)}"
        )
    if decisions_index.get("schema") != decision_schema["indexSchema"]:
        problems.append("crystallization index: bad schema")
    decisions = decisions_index.get("decisions")
    if not isinstance(decisions, list):
        problems.append("crystallization index: decisions must be list")
        decisions = []
    decision_work_ids: set[str] = set()
    decision_ids: set[str] = set()
    for position, decision in enumerate(decisions, 1):
        where = f"crystallization decision[{position}]"
        problems.extend(validate_decision(decision, context, work_by_id, where))
        if isinstance(decision, dict):
            decision_id = decision.get("id")
            work_id = decision.get("workId")
            if nonempty_string(decision_id):
                if decision_id in decision_ids:
                    problems.append(f"{where}: duplicate id {decision_id}")
                decision_ids.add(decision_id)
            if nonempty_string(work_id):
                if work_id in decision_work_ids:
                    problems.append(f"{where}: duplicate workId {work_id}")
                decision_work_ids.add(work_id)

    for work_id, item in work_by_id.items():
        lifecycle = item.get("lifecycle")
        terminal = isinstance(lifecycle, str) and lifecycle in {
            "integrated",
            "archived",
            "rejected",
        }
        has_decision = work_id in decision_work_ids
        if terminal and not has_decision:
            problems.append(
                f"{work_id}: terminal lifecycle requires crystallization decision"
            )
        if not terminal and has_decision:
            problems.append(
                f"{work_id}: non-terminal lifecycle must not have crystallization decision"
            )
    return problems


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def require_valid_root(root: Path) -> None:
    problems = validate_root(root)
    if problems:
        raise ValueError("\n".join(problems))
