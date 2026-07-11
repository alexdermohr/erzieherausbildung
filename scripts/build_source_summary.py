#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a privacy-preserving aggregate summary of local source material."
    )
    parser.add_argument("--source-root", default="source-material.local")
    parser.add_argument("--output", default="data/source-summary.json")
    return parser.parse_args()


def build_summary(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if root.name != "erzieherausbildung":
        raise SystemExit("wrong source root")
    if not root.is_dir():
        raise SystemExit(f"source root is not a directory: {root}")

    extensions: Counter[str] = Counter()
    clusters: list[dict[str, Any]] = []
    files_total = 0
    bytes_total = 0

    directories = sorted(
        (path for path in root.iterdir() if path.is_dir() and not path.is_symlink()),
        key=lambda path: path.name.casefold(),
    )
    for directory in directories:
        files: list[Path] = []
        for current_root, directory_names, file_names in os.walk(
            directory, followlinks=False
        ):
            current = Path(current_root)
            directory_names[:] = sorted(
                (
                    name
                    for name in directory_names
                    if not (current / name).is_symlink()
                ),
                key=str.casefold,
            )
            for name in sorted(file_names, key=str.casefold):
                path = current / name
                if path.is_file() and not path.is_symlink():
                    files.append(path)
        cluster_extensions = Counter(
            path.suffix.lower().lstrip(".") or "[noext]" for path in files
        )
        cluster_size = sum(path.stat().st_size for path in files)
        clusters.append(
            {
                "title": directory.name,
                "fileCount": len(files),
                "totalBytes": cluster_size,
                "extensions": dict(sorted(cluster_extensions.items())),
            }
        )
        files_total += len(files)
        bytes_total += cluster_size
        extensions.update(cluster_extensions)

    return {
        "schema": "erzieherausbildung.source-summary.v2",
        "sourceRootHint": "~/iCloud/Drive/inbox/erzieherausbildung",
        "sourceRootName": root.name,
        "rawFilesCopied": False,
        "privacyMode": "aggregate-no-filenames",
        "clusters": clusters,
        "totals": {
            "files": files_total,
            "bytes": bytes_total,
            "extensions": dict(sorted(extensions.items())),
        },
    }


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    summary = build_summary(Path(args.source_root))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output} with {summary['totals']['files']} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
