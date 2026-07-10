#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "data/learning-field-focus.v1.json"
MAP_PATH = ROOT / "data/learning-map.v1.json"
DETAIL_INDEX_PATH = ROOT / "data/details/index.v1.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def first_sentence(text: str, limit: int = 210) -> str:
    clean = " ".join(str(text).split())
    for marker in [". ", "? ", "! "]:
        if marker in clean:
            clean = clean.split(marker, 1)[0] + marker.strip()
            break
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def topic_catalog() -> dict[str, dict[str, str]]:
    learning_map = load_json(MAP_PATH)
    details_index = load_json(DETAIL_INDEX_PATH)
    details_by_topic: dict[str, dict[str, Any]] = {}
    for entry in details_index["details"]:
        payload = load_json(ROOT / entry["path"].lstrip("/"))
        for topic_id in payload.get("topicIds", []):
            details_by_topic.setdefault(topic_id, payload)

    catalog: dict[str, dict[str, str]] = {}
    for axis in learning_map["axes"]:
        for topic in axis["topics"]:
            detail = details_by_topic.get(topic["id"], {})
            summary = detail.get("summary") or f"Thema der Achse {axis['title']}."
            catalog[topic["id"]] = {
                "title": topic["title"],
                "summary": first_sentence(summary),
            }
    return catalog


def node(node_id: str, text: str, x: int, y: int, width: int, height: int) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": "text",
        "text": text,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def edge(edge_id: str, source: str, target: str) -> dict[str, str]:
    return {"id": edge_id, "fromNode": source, "toNode": target}


def build_canvas(field: dict[str, Any], catalog: dict[str, dict[str, str]]) -> dict[str, Any]:
    prefix = field["id"].replace("lernfeld-", "lf")
    center_id = f"{prefix}-center"
    nodes = [
        node(
            center_id,
            f"{field['label']}: {field['title']}\n\n{field['summary']}",
            0,
            0,
            480,
            160,
        ),
        node(
            f"{prefix}-orientation",
            f"{field['orientation']['title']}\n\n{field['orientation']['text']}",
            -240,
            -300,
            440,
            140,
        ),
        node(
            f"{prefix}-practice",
            f"{field['practice']['title']}\n\n{field['practice']['text']}",
            300,
            -300,
            440,
            140,
        ),
    ]
    edges = [
        edge(f"e-{prefix}-orientation-center", f"{prefix}-orientation", center_id),
        edge(f"e-{prefix}-practice-center", f"{prefix}-practice", center_id),
    ]

    topic_rows = (len(field["topicIds"]) + 1) // 2
    for index, topic_id in enumerate(field["topicIds"]):
        topic = catalog[topic_id]
        x = -720 if index % 2 == 0 else 620
        y = index // 2 * 190
        topic_node_id = f"topic-{topic_id}"
        nodes.append(node(topic_node_id, f"{topic['title']}\n\n{topic['summary']}", x, y, 380, 150))
        edges.append(edge(f"e-{prefix}-topic-{topic_id}", center_id, topic_node_id))

    cross_y = max(320, topic_rows * 190 + 20)
    previous = center_id
    for index, cross_link in enumerate(field["crossLinks"], start=1):
        cross_id = f"{prefix}-cross-{cross_link['id']}"
        nodes.append(node(cross_id, f"{cross_link['title']}\n\n{cross_link['text']}", 0, cross_y + (index - 1) * 210, 480, 140))
        edges.append(edge(f"e-{prefix}-cross-{index}", previous, cross_id))
        previous = cross_id

    reflection_id = f"{prefix}-reflection"
    reflection_y = cross_y + len(field["crossLinks"]) * 210
    nodes.append(node(reflection_id, f"{field['reflection']['title']}\n\n{field['reflection']['text']}", 0, reflection_y, 480, 140))
    edges.append(edge(f"e-{prefix}-reflection", previous, reflection_id))
    edges.append(edge(f"e-{prefix}-reflection-center", reflection_id, center_id))
    return {"nodes": nodes, "edges": edges}


def rendered_files() -> dict[Path, str]:
    spec = load_json(SPEC_PATH)
    catalog = topic_catalog()
    outputs: dict[Path, str] = {}
    for field in spec["fields"]:
        canvas = build_canvas(field, catalog)
        outputs[ROOT / field["canvas"]] = json.dumps(canvas, ensure_ascii=False, indent=2) + "\n"
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build learning-field focus Canvas files.")
    parser.add_argument("--check", action="store_true", help="Fail if generated Canvas files are stale.")
    args = parser.parse_args()

    stale: list[str] = []
    for path, content in rendered_files().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8")
    if stale:
        raise SystemExit("stale learning-field focus maps: " + ", ".join(stale))
    print("learning-field focus maps validation passed" if args.check else "learning-field focus maps built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
