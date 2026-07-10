#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "theory-catalog.v1.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data" / "theory-catalog.v1.json").read_text(encoding="utf-8"))
LEARNING = json.loads((ROOT / "data" / "learning-map.v1.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((ROOT / "data" / "machine-readable-inventory.json").read_text(encoding="utf-8"))

ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DOC = re.compile(r"^doc-\d{3}$")
VALID_AXES = {axis["id"] for axis in LEARNING["axes"]}
VALID_DOCS = {f"doc-{item['ordinal']:03d}": item for item in INVENTORY["documents"]}
KINDS = set(SCHEMA["kinds"])
STATUSES = set(SCHEMA["evidenceStatuses"])
ROLES = set(SCHEMA["evidenceRoles"])
BLOCKED = set(SCHEMA["blockedFields"])
ENTRY_REQUIRED = set(SCHEMA["entryRequired"])


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: object, *, allow_empty: bool = False) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value)) and all(nonempty(item) for item in value)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(value.split())


problems: list[str] = []
if CATALOG.get("schema") != SCHEMA["dataSchema"]:
    problems.append("catalog: bad schema")
for key in SCHEMA["required"]:
    if key not in CATALOG:
        problems.append(f"catalog: missing {key}")

serialized_catalog = json.dumps(CATALOG, ensure_ascii=False)
for forbidden_marker in ["machine-readable.local", "source-material.local", "/home/", "file://"]:
    if forbidden_marker in serialized_catalog:
        problems.append(f"catalog: forbidden local path marker {forbidden_marker}")

entries = CATALOG.get("entries")
if not isinstance(entries, list) or not entries:
    problems.append("catalog: entries must be non-empty list")
    entries = []
ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
if len(ids) != len(set(ids)):
    problems.append("catalog: duplicate ids")
valid_ids = set(ids)

for index, entry in enumerate(entries, 1):
    where = f"entry[{index}]"
    if not isinstance(entry, dict):
        problems.append(f"{where}: must be object")
        continue
    missing = ENTRY_REQUIRED - set(entry)
    if missing:
        problems.append(f"{where}: missing {sorted(missing)}")
    blocked = BLOCKED & set(entry)
    if blocked:
        problems.append(f"{where}: blocked fields {sorted(blocked)}")
    if not nonempty(entry.get("id")) or not ID.match(entry.get("id", "")):
        problems.append(f"{where}: bad id")
    if not nonempty(entry.get("title")):
        problems.append(f"{where}: title required")
    if entry.get("kind") not in KINDS:
        problems.append(f"{where}: bad kind")
    if entry.get("evidenceStatus") not in STATUSES:
        problems.append(f"{where}: bad evidenceStatus")
    if not string_list(entry.get("axisIds")):
        problems.append(f"{where}: axisIds must be non-empty string list")
    else:
        for axis in entry["axisIds"]:
            if axis not in VALID_AXES:
                problems.append(f"{where}: unknown axis {axis}")
    for key in ["attributedTo", "aliases", "relatedIds"]:
        if not string_list(entry.get(key), allow_empty=True):
            problems.append(f"{where}: {key} must be string list")
    if not nonempty(entry.get("summary")):
        problems.append(f"{where}: summary required")
    if not string_list(entry.get("cautions")):
        problems.append(f"{where}: cautions required")
    if entry.get("evidenceStatus") == "named-only":
        if entry.get("coreIdeas") != [] or entry.get("pedagogicalRelevance") != []:
            problems.append(f"{where}: named-only must not synthesize coreIdeas or pedagogicalRelevance")
    else:
        if not string_list(entry.get("coreIdeas")):
            problems.append(f"{where}: coreIdeas required")
        if not string_list(entry.get("pedagogicalRelevance")):
            problems.append(f"{where}: pedagogicalRelevance required")
    for related in entry.get("relatedIds", []):
        if related not in valid_ids:
            problems.append(f"{where}: unknown relatedId {related}")
        if related == entry.get("id"):
            problems.append(f"{where}: self-related id")
    mentions = entry.get("sourceMentions")
    if not isinstance(mentions, list) or not mentions:
        problems.append(f"{where}: sourceMentions required")
        continue
    for mention_index, mention in enumerate(mentions, 1):
        source_where = f"{where}.sourceMentions[{mention_index}]"
        if not isinstance(mention, dict):
            problems.append(f"{source_where}: must be object")
            continue
        doc_id = mention.get("docId")
        if not isinstance(doc_id, str) or not DOC.match(doc_id) or doc_id not in VALID_DOCS:
            problems.append(f"{source_where}: bad docId {doc_id}")
        start = mention.get("startLine")
        end = mention.get("endLine")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            problems.append(f"{source_where}: bad line range")
        if mention.get("evidenceRole") not in ROLES:
            problems.append(f"{source_where}: bad evidenceRole")
        if not string_list(mention.get("evidenceTerms")):
            problems.append(f"{source_where}: evidenceTerms required")
            continue
        inventory_item = VALID_DOCS.get(doc_id)
        if not inventory_item:
            continue
        local_path = Path(inventory_item["local_text_path"])
        if not local_path.exists() or not isinstance(start, int) or not isinstance(end, int):
            continue
        lines = local_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if end > len(lines):
            problems.append(f"{source_where}: range exceeds local text ({len(lines)} lines)")
            continue
        context = normalize("\n".join(lines[start - 1:end]))
        for term in mention["evidenceTerms"]:
            if normalize(term) not in context:
                problems.append(f"{source_where}: local evidence term not found: {term}")

local_corpus_parts = []
for inventory_item in VALID_DOCS.values():
    local_path = Path(inventory_item["local_text_path"])
    if local_path.exists():
        local_corpus_parts.append(local_path.read_text(encoding="utf-8", errors="replace"))
if local_corpus_parts:
    local_corpus = normalize("\n".join(local_corpus_parts))
    for index, entry in enumerate(entries, 1):
        for person in entry.get("attributedTo", []):
            name_parts = [part for part in re.split(r"\W+", normalize(person)) if len(part) >= 4]
            if name_parts and name_parts[-1] not in local_corpus:
                problems.append(f"entry[{index}]: attributed person not found in local corpus: {person}")

coverage = CATALOG.get("coverage", {})
expected = {
    "entries": len(entries),
    "explained": sum(entry.get("evidenceStatus") == "explained" for entry in entries),
    "applied": sum(entry.get("evidenceStatus") == "applied" for entry in entries),
    "namedOnly": sum(entry.get("evidenceStatus") == "named-only" for entry in entries),
}
source_docs = sorted({mention["docId"] for entry in entries for mention in entry.get("sourceMentions", []) if isinstance(mention, dict) and mention.get("docId") in VALID_DOCS})
expected["sourceDocumentsWithFindings"] = len(source_docs)
expected["sourceDocumentIds"] = source_docs
for key, value in expected.items():
    if coverage.get(key) != value:
        problems.append(f"coverage: bad {key}")
if CATALOG.get("method", {}).get("documentsScanned") != len(INVENTORY["documents"]):
    problems.append("method.documentsScanned does not match inventory")
policy = CATALOG.get("sourcePolicy", {})
for key, expected_value in {
    "raw_text_committed": False,
    "source_refs_only": True,
    "own_synthesis": True,
    "local_origin_material_only": True,
}.items():
    if policy.get(key) is not expected_value:
        problems.append(f"sourcePolicy: bad {key}")

if problems:
    print("\n".join(problems))
    raise SystemExit(1)
print("theory catalog validation passed")
