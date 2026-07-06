#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
schema = json.loads((root / "schemas" / "excerpt.v1.schema.json").read_text(encoding="utf-8"))
REQ = set(schema["required"])
OPTIONAL = set(schema.get("optional", []))
BLOCKED = set(schema.get("blockedFields", []))
ALLOWED = REQ | OPTIONAL
CLAIMS = set(schema["claimTypes"])
STATUS = set(schema["reviewStatuses"])
LOCATOR_PLACEHOLDERS = set(schema.get("sourceLocatorPlaceholders", []))
ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def is_nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(is_nonempty_string(item) for item in value)


def has_concrete_locator(item: dict) -> bool:
    locator = item.get("sourceLocator")
    return is_nonempty_string(locator) and locator not in LOCATOR_PLACEHOLDERS


def validate_item(item: dict, where: str) -> list[str]:
    problems: list[str] = []
    missing = REQ - set(item)
    if missing:
        problems.append(f"{where}: missing {sorted(missing)}")
    blocked = BLOCKED & set(item)
    if blocked:
        problems.append(f"{where}: blocked fields {sorted(blocked)}")
    extra = set(item) - ALLOWED - BLOCKED
    if extra:
        problems.append(f"{where}: unknown fields {sorted(extra)}")
    if not is_nonempty_string(item.get("id")) or not ID.match(str(item.get("id", ""))):
        problems.append(f"{where}: bad id")
    for key in ["sourceCluster", "sourceTitle", "sourceLocator", "claimType", "summary", "practiceUse", "reviewStatus"]:
        if key in item and not is_nonempty_string(item.get(key)):
            problems.append(f"{where}: {key} must be non-empty string")
    if item.get("claimType") not in CLAIMS:
        problems.append(f"{where}: bad claimType")
    if item.get("reviewStatus") not in STATUS:
        problems.append(f"{where}: bad reviewStatus")
    if not is_string_list(item.get("concepts")):
        problems.append(f"{where}: concepts must be non-empty string list")
    if not is_string_list(item.get("links")):
        problems.append(f"{where}: links must be non-empty string list")
    uncertainty = item.get("uncertainty")
    if not isinstance(uncertainty, (int, float)) or not 0 <= uncertainty <= 1:
        problems.append(f"{where}: bad uncertainty")
    claim = item.get("claimType")
    status = item.get("reviewStatus")
    if claim in {"title-derived", "question"} and status == "checked":
        problems.append(f"{where}: {claim} must not be checked")
    if claim in {"title-derived", "question"} and isinstance(uncertainty, (int, float)) and uncertainty < 0.5:
        problems.append(f"{where}: {claim} needs uncertainty >= 0.5")
    if claim in {"excerpted", "interpreted"} and not has_concrete_locator(item):
        problems.append(f"{where}: {claim} needs concrete sourceLocator")
    if status == "checked" and claim not in {"excerpted", "interpreted"}:
        problems.append(f"{where}: checked requires excerpted or interpreted claimType")
    if status == "checked" and not has_concrete_locator(item):
        problems.append(f"{where}: checked requires concrete sourceLocator")
    return problems


problems: list[str] = []
assert schema["schema"] == "erzieherausbildung.excerpt.contract.v1"
assert schema["dataSchema"] == "erzieherausbildung.excerpt.v1"
assert "sourceLocator" in REQ
assert "links" in REQ

template = json.loads((root / "templates" / "excerpt.v1.json").read_text(encoding="utf-8"))
problems.extend(validate_item(template, "templates/excerpt.v1.json"))

for path in sorted((root / "data" / "excerpts").glob("*.jsonl")):
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception as exc:
            problems.append(f"{path}:{line_number}: invalid json: {exc}")
            continue
        problems.extend(validate_item(item, f"{path}:{line_number}"))

if problems:
    print("\n".join(problems))
    raise SystemExit(1)
print("excerpt validation passed")
