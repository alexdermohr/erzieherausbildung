#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "index.html",
    "data/module-map.json",
    "data/source-summary.json",
    "visuals/visual-spec.v1.json",
    "visuals/erzieherausbildung-systemkarte.canvas",
    "visuals/m08-paedagogische-anwendungsfelder.canvas",
    "visuals/schauwerk-erzieherausbildung-board.dsl",
]


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def validate_canvas(rel: str) -> None:
    data = load_json(rel)
    nodes = {node["id"] for node in data.get("nodes", [])}
    assert nodes, f"{rel}: no nodes"
    for edge in data.get("edges", []):
        assert edge["fromNode"] in nodes, f"{rel}: missing fromNode {edge['fromNode']}"
        assert edge["toNode"] in nodes, f"{rel}: missing toNode {edge['toNode']}"


def main() -> int:
    for rel in REQUIRED:
        assert (ROOT / rel).exists(), f"missing {rel}"

    module_map = load_json("data/module-map.json")
    axes = {axis["id"] for axis in module_map["axes"]}
    assert len(module_map["modules"]) >= 8
    for module in module_map["modules"]:
        assert set(module["axes"]).issubset(axes), module["id"]
        assert 0 <= module["confidence"] <= 1, module["id"]
        assert 1 <= module["visualWeight"] <= 5, module["id"]

    spec = load_json("visuals/visual-spec.v1.json")
    assert spec["schema"] == "erzieherausbildung.visual-spec.v1"

    validate_canvas("visuals/erzieherausbildung-systemkarte.canvas")
    validate_canvas("visuals/m08-paedagogische-anwendungsfelder.canvas")
    print("repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
