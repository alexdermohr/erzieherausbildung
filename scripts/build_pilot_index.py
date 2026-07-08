#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "excerpts"
JSON_TARGET = ROOT / "data" / "pilot-index.v1.json"
DOC_TARGET = ROOT / "docs" / "pilot-index-v1.md"
LOCATOR_PLACEHOLDERS = {"unknown", "not-yet-located", "Seite oder Abschnitt falls bekannt"}


def has_concrete_locator(item: dict) -> bool:
    locator = item.get("sourceLocator", "")
    return isinstance(locator, str) and bool(locator.strip()) and locator.strip() not in LOCATOR_PLACEHOLDERS


def load_items() -> list[dict]:
    items: list[dict] = []
    for path in sorted(SOURCE_DIR.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            item = json.loads(line)
            item["_file"] = path.relative_to(ROOT).as_posix()
            item["_line"] = line_number
            items.append(item)
    return items


def build_json(items: list[dict]) -> dict:
    by_status = Counter(item["reviewStatus"] for item in items)
    by_claim = Counter(item["claimType"] for item in items)
    by_cluster = Counter(item["sourceCluster"] for item in items)
    concepts = Counter(concept for item in items for concept in item["concepts"])
    source_titles = sorted({item["sourceTitle"] for item in items})
    unresolved_source_work = [
        {
            "id": item["id"],
            "sourceTitle": item["sourceTitle"],
            "sourceLocator": item["sourceLocator"],
            "claimType": item["claimType"],
            "reviewStatus": item["reviewStatus"],
            "uncertainty": item["uncertainty"],
        }
        for item in items
        if not has_concrete_locator(item)
    ]
    return {
        "schema": "erzieherausbildung.pilot_index.v1",
        "source": "data/excerpts/*.jsonl",
        "purpose": "Aggregierter Abdeckungsstand der ersten Belegknoten; keine Rohtextablage und keine Vollständigkeitsbehauptung.",
        "totals": {"entries": len(items)},
        "byReviewStatus": dict(sorted(by_status.items())),
        "byClaimType": dict(sorted(by_claim.items())),
        "bySourceCluster": dict(sorted(by_cluster.items())),
        "sourceTitles": source_titles,
        "unresolvedSourceWork": unresolved_source_work,
        "concepts": dict(sorted(concepts.items())),
        "knownLimits": [
            "nur Pilotstand",
            "needs-source-Einträge sind offene Quellenarbeit, keine Belege",
            "keine systematische Tiefenerschließung",
        ],
    }


def render_doc(index: dict) -> str:
    lines = [
        "# Pilot-Index v1",
        "",
        "Status: abgeleitete Übersicht aus `data/excerpts/*.jsonl`, keine neue Inhaltsquelle.",
        "",
        "## These / Antithese / Synthese",
        "",
        "These: Nach den ersten Belegknoten braucht die Karte eine sichtbare Abdeckung.",
        "",
        "Antithese: Ein Index kann Vollständigkeit vortäuschen, obwohl erst zwei Entwurfsnoten existieren.",
        "",
        "Synthese: Der Index zeigt bewusst nur Aggregation, Status und Grenzen. Kanon bleiben die JSONL-Einträge und ihre Quellenrückbindung.",
        "",
        "## Stand",
        "",
        f"- Einträge: {index['totals']['entries']}",
        f"- Reviewstatus: {index['byReviewStatus']}",
        f"- Claim-Typen: {index['byClaimType']}",
        f"- Lernfelder/Cluster: {index['bySourceCluster']}",
        "",
        "## Offene Quellenarbeit",
        "",
    ]
    unresolved = index.get("unresolvedSourceWork", [])
    if unresolved:
        lines.append("Diese Einträge sind Arbeitsfragen ohne konkrete Fundstelle; sie zählen nicht als Detailbelege.")
        lines.append("")
        for item in unresolved:
            lines.append(f"- `{item['id']}` — {item['sourceTitle']} ({item['reviewStatus']}, Unsicherheit {item['uncertainty']})")
    else:
        lines.append("Keine offenen Quellenarbeits-Einträge.")
    lines += [
        "",
        "## Quellen im Pilot",
        "",
    ]
    for title in index["sourceTitles"]:
        lines.append(f"- {title}")
    lines += ["", "## Begriffe im Pilot", ""]
    for concept, count in index["concepts"].items():
        lines.append(f"- {concept}: {count}")
    lines += [
        "",
        "## Grenze",
        "",
        "Der Index beweist den Pfad von Struktur zu belegten Knoten. Er beweist nicht, dass ein Lernfeld bereits vollständig erschlossen ist. Gerade hier lauert die kleine Bürokratie-Krake: Sie zählt sauber und weiß trotzdem noch wenig.",
        "",
        "## Nächste Aktion",
        "",
        "Weitere Pilotknoten je Lernfeld ergänzen oder Detailkarten erst ab einer Mindestabdeckung ableiten.",
    ]
    return "\n".join(lines) + "\n"


def build_outputs() -> tuple[str, str]:
    index = build_json(load_items())
    json_text = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    doc_text = render_doc(index)
    return json_text, doc_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed outputs are stale")
    args = parser.parse_args()
    json_text, doc_text = build_outputs()
    if args.check:
        errors = []
        if JSON_TARGET.read_text(encoding="utf-8") != json_text:
            errors.append(str(JSON_TARGET.relative_to(ROOT)))
        if DOC_TARGET.read_text(encoding="utf-8") != doc_text:
            errors.append(str(DOC_TARGET.relative_to(ROOT)))
        if errors:
            print("stale pilot index: " + ", ".join(errors))
            return 1
        print("pilot index validation passed")
        return 0
    JSON_TARGET.write_text(json_text, encoding="utf-8")
    DOC_TARGET.write_text(doc_text, encoding="utf-8")
    print("pilot index built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
