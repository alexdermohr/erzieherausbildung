#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARNING_MAP = ROOT / "data" / "learning-map.v1.json"
DETAIL_INDEX = ROOT / "data" / "details" / "index.v1.json"
JSON_TARGET = ROOT / "data" / "detail-bridge-index.v1.json"
DOC_TARGET = ROOT / "docs" / "detail-bridge-index-v1.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def learning_lookup() -> tuple[dict[str, dict], dict[str, dict]]:
    learning = load_json(LEARNING_MAP)
    axes: dict[str, dict] = {}
    topics: dict[str, dict] = {}
    for axis in learning["axes"]:
        axes[axis["id"]] = {"id": axis["id"], "title": axis["title"]}
        for topic in axis.get("topics", []):
            topics[topic["id"]] = {"id": topic["id"], "title": topic["title"], "axisId": axis["id"], "axisTitle": axis["title"]}
    return axes, topics


def load_details() -> list[dict]:
    index = load_json(DETAIL_INDEX)
    details: list[dict] = []
    for entry in sorted(index["details"], key=lambda item: item["id"]):
        detail = load_json(ROOT / entry["path"].lstrip("/"))
        detail["_indexPath"] = entry["path"]
        details.append(detail)
    return details


def target_label(target_id: str, axes: dict[str, dict], topics: dict[str, dict]) -> tuple[str, str, str | None]:
    if target_id in topics:
        topic = topics[target_id]
        return "topic", topic["title"], topic["axisId"]
    if target_id in axes:
        axis = axes[target_id]
        return "axis", axis["title"], target_id
    return "unknown", target_id, None


def build_index() -> dict:
    axes, topics = learning_lookup()
    valid_targets = set(axes) | set(topics)
    details = load_details()
    bridges: list[dict] = []
    by_target: dict[str, dict] = {}
    by_source: list[dict] = []
    target_counter: Counter[str] = Counter()
    axis_counter: Counter[str] = Counter()
    outgoing_counter: Counter[str] = Counter()
    incoming_sources: dict[str, list[str]] = defaultdict(list)

    for detail in details:
        source_title = detail["title"]
        source_item = {
            "detailId": detail["id"],
            "title": source_title,
            "topicIds": detail["topicIds"],
            "axisIds": detail["axisIds"],
            "bridgeCount": len(detail.get("bridges", [])),
            "targets": [],
        }
        for index, bridge in enumerate(detail.get("bridges", []), 1):
            target_id = bridge["targetId"]
            target_type, label, target_axis_id = target_label(target_id, axes, topics)
            if target_id not in valid_targets:
                raise AssertionError(f"unknown bridge target {target_id!r} in {detail['id']}")
            bridge_id = f"{detail['id']}--{index:02d}--{target_id}"
            bridge_item = {
                "id": bridge_id,
                "sourceDetailId": detail["id"],
                "sourceTitle": source_title,
                "sourceTopicIds": detail["topicIds"],
                "sourceAxisIds": detail["axisIds"],
                "targetId": target_id,
                "targetType": target_type,
                "targetTitle": label,
                "targetAxisId": target_axis_id,
                "relation": bridge["relation"],
            }
            bridges.append(bridge_item)
            source_item["targets"].append({"targetId": target_id, "targetTitle": label, "relation": bridge["relation"]})
            target_counter[target_id] += 1
            outgoing_counter[detail["id"]] += 1
            incoming_sources[target_id].append(detail["id"])
            if target_axis_id:
                axis_counter[target_axis_id] += 1
        by_source.append(source_item)

    for target_id, count in sorted(target_counter.items(), key=lambda item: (-item[1], item[0])):
        target_type, label, axis_id = target_label(target_id, axes, topics)
        by_target[target_id] = {
            "targetId": target_id,
            "targetTitle": label,
            "targetType": target_type,
            "axisId": axis_id,
            "incomingBridgeCount": count,
            "sourceDetailIds": sorted(set(incoming_sources[target_id])),
        }

    hubs = [
        {
            "targetId": target_id,
            "targetTitle": by_target[target_id]["targetTitle"],
            "incomingBridgeCount": count,
        }
        for target_id, count in target_counter.most_common(12)
    ]

    return {
        "schema": "erzieherausbildung.detail_bridge_index.v1",
        "source": "data/details/*.json",
        "purpose": "Abgeleitete Orientierungsfläche über Brücken zwischen Detailkarten; keine neue Inhaltsquelle und keine Rohtextablage.",
        "totals": {
            "details": len(details),
            "bridges": len(bridges),
            "targets": len(by_target),
            "axesWithIncomingBridges": len(axis_counter),
        },
        "hubs": hubs,
        "byTargetAxis": [
            {"axisId": axis_id, "axisTitle": axes[axis_id]["title"], "incomingBridgeCount": count}
            for axis_id, count in sorted(axis_counter.items(), key=lambda item: (-item[1], item[0]))
        ],
        "byTarget": by_target,
        "bySource": by_source,
        "bridges": bridges,
        "limits": [
            "Brücken sind aus Detailkarten abgeleitet und nicht eigenständig belegt.",
            "Ein hoher Eingangswert zeigt Orientierungsknoten, nicht automatisch Wichtigkeit im Ausbildungsplan.",
            "Relationstexte bleiben Kurzsynthesen und ersetzen keine Detailkarte.",
        ],
    }


def render_doc(index: dict) -> str:
    lines = [
        "# Detail-Brückenindex v1",
        "",
        "Status: abgeleitete Orientierungsfläche aus `data/details/*.json`; kanonisch bleiben die Detailkarten.",
        "",
        "## These / Antithese / Synthese",
        "",
        "These: Nach vollständiger erster Detailcoverage braucht die Karte eine Sicht auf Zusammenhänge, nicht nur eine Liste einzelner Themen.",
        "",
        "Antithese: Ein Brückenindex kann scheinbar Systematik erzeugen, obwohl die Brücken weiterhin kurze Synthesen aus Detailkarten sind.",
        "",
        "Synthese: Der Index zeigt Verbindungsknoten, Hubs und Zielachsen als Navigation. Er ist Orientierung, keine neue Quelle.",
        "",
        "## Stand",
        "",
        f"- Detailkarten: {index['totals']['details']}",
        f"- Brücken: {index['totals']['bridges']}",
        f"- Zielknoten: {index['totals']['targets']}",
        f"- Zielachsen mit eingehenden Brücken: {index['totals']['axesWithIncomingBridges']}",
        "",
        "## stärkste Verbindungsknoten",
        "",
    ]
    for hub in index["hubs"]:
        lines.append(f"- `{hub['targetId']}` — {hub['targetTitle']}: {hub['incomingBridgeCount']} eingehende Brücken")
    lines += ["", "## Zielachsen", ""]
    for axis in index["byTargetAxis"]:
        lines.append(f"- `{axis['axisId']}` — {axis['axisTitle']}: {axis['incomingBridgeCount']} eingehende Brücken")
    lines += ["", "## Brücken nach Detailkarte", ""]
    for source in index["bySource"]:
        lines.append(f"### {source['title']} (`{source['detailId']}`)")
        lines.append("")
        if source["targets"]:
            for target in source["targets"]:
                lines.append(f"- → `{target['targetId']}` — {target['relation']}")
        else:
            lines.append("- keine Brücken")
        lines.append("")
    lines += ["## Grenze", ""]
    for limit in index["limits"]:
        lines.append(f"- {limit}")
    return "\n".join(lines).rstrip() + "\n"


def build_outputs() -> tuple[str, str]:
    index = build_index()
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n", render_doc(index)


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
            print("stale detail bridge index: " + ", ".join(errors))
            return 1
        print("detail bridge index validation passed")
        return 0
    JSON_TARGET.write_text(json_text, encoding="utf-8")
    DOC_TARGET.write_text(doc_text, encoding="utf-8")
    print("detail bridge index built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
