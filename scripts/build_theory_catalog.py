#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "theory-catalog.v1.json"
DOC = ROOT / "docs" / "theory-catalog-v1.md"


def load_catalog() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def source_anchor(source: dict) -> str:
    return f"`{source['docId']}:{source['startLine']}–{source['endLine']}`"


def render_list(title: str, values: list[str], lines: list[str]) -> None:
    if not values:
        return
    lines += [f"**{title}**", ""]
    lines.extend(f"- {value}" for value in values)
    lines.append("")


def render_entry(entry: dict, catalog: dict, lines: list[str]) -> None:
    kinds = catalog["vocabulary"]["kinds"]
    evidence = catalog["vocabulary"]["evidenceStatuses"]
    axes = catalog["vocabulary"]["axes"]
    lines += [f"### {entry['title']}", ""]
    meta = [kinds[entry["kind"]], evidence[entry["evidenceStatus"]]]
    if entry["attributedTo"]:
        meta.append("Bezug: " + ", ".join(entry["attributedTo"]))
    lines += [" · ".join(meta), "", entry["summary"], ""]
    lines += ["**Wissensbereiche:** " + "; ".join(axes[axis] for axis in entry["axisIds"]), ""]
    if entry["evidenceStatus"] != "named-only":
        render_list("Kernideen", entry["coreIdeas"], lines)
        render_list("Pädagogische Bedeutung", entry["pedagogicalRelevance"], lines)
    render_list("Einordnung und Grenzen", entry["cautions"], lines)
    lines += ["**Quellenanker:** " + ", ".join(source_anchor(source) for source in entry["sourceMentions"]), ""]
    if entry["relatedIds"]:
        titles = {item["id"]: item["title"] for item in catalog["entries"]}
        lines += ["**Verwandte Positionen:** " + "; ".join(titles[item] for item in entry["relatedIds"]), ""]


def render_doc(catalog: dict) -> str:
    coverage = catalog["coverage"]
    lines = [
        "# Theoriekatalog v1",
        "",
        "Status: quellengebundene Synthese aus den lokal erschlossenen Ausbildungsmaterialien. Rohtexte bleiben lokal; kanonisch ist `data/theory-catalog.v1.json`.",
        "",
        "## Was hier als Theorie erfasst wird",
        "",
        catalog["method"]["inclusionRule"],
        "",
        "Der Katalog unterscheidet Theorien, Modelle, theoretische Kernkonzepte und pädagogische Ansätze. Eine bloße Namensnennung wird ausdrücklich nicht zu einer ausgearbeiteten Theorie ergänzt.",
        "",
        "## Rechercheweg",
        "",
    ]
    lines.extend(f"- {item}" for item in catalog["method"]["searchStrategy"])
    lines += ["", "## Abgrenzung", "", catalog["method"]["exclusionRule"], "", "## Grenzen", ""]
    lines.extend(f"- {item}" for item in catalog["method"]["limits"])
    lines += [
        "",
        "## Korpusstand",
        "",
        f"- durchsuchte Dokumente: {catalog['method']['documentsScanned']}",
        f"- erklärte Positionen: {coverage['explained']}",
        f"- angewandte oder knapp eingeordnete Positionen: {coverage['applied']}",
        f"- nur genannte Positionen: {coverage['namedOnly']}",
        f"- Quelldokumente mit Fundstellen: {coverage['sourceDocumentsWithFindings']}",
        "",
        "Die Zahlen dokumentieren den Rechercheumfang; sie sind keine Rangfolge der Theorien.",
        "",
    ]

    axis_order = list(catalog["vocabulary"]["axes"])
    by_axis: dict[str, list[dict]] = defaultdict(list)
    named_only: list[dict] = []
    for entry in catalog["entries"]:
        if entry["evidenceStatus"] == "named-only":
            named_only.append(entry)
        else:
            by_axis[entry["axisIds"][0]].append(entry)

    lines += ["## Erklärte und angewandte Positionen", ""]
    for axis_id in axis_order:
        entries = sorted(by_axis.get(axis_id, []), key=lambda item: item["title"].casefold())
        if not entries:
            continue
        lines += [f"## {catalog['vocabulary']['axes'][axis_id]}", ""]
        for entry in entries:
            render_entry(entry, catalog, lines)

    lines += ["## Nur genannt, im Korpus nicht erklärt", ""]
    lines += [
        "Diese Einträge sichern Vollständigkeit, ohne fehlende Aussagen aus externem Wissen zu ergänzen.",
        "",
    ]
    for entry in sorted(named_only, key=lambda item: item["title"].casefold()):
        render_entry(entry, catalog, lines)

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = render_doc(load_catalog())
    if args.check:
        if not DOC.exists() or DOC.read_text(encoding="utf-8") != output:
            print("stale theory catalog documentation")
            return 1
        print("theory catalog documentation validation passed")
        return 0
    DOC.write_text(output, encoding="utf-8")
    print("theory catalog documentation built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
