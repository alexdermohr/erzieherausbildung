#!/usr/bin/env python3
"""Export curated Erzieherausbildung view artifacts into an Obsidian vault.

The repository remains canonical. The vault target is a derived reading/thinking
surface and is intentionally limited to a fixed allow-list of view files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SOURCE_REPO = Path("/home/alex/repos/erzieherausbildung")
DEFAULT_VAULT_ROOT = Path.home() / "vault-gewebe"
DEFAULT_TARGET_DIR = DEFAULT_VAULT_ROOT / "schule" / "erzieherausbildung"
MANIFEST_NAME = ".erzieherausbildung-obsidian-view.json"
POLICY = "repo-canonical-vault-derived"
SCHEMA = "erzieherausbildung.obsidian_view_export.v1"
WARNING = (
    "SPIEGELDATEI aus /home/alex/repos/erzieherausbildung. "
    "Kanonische Quelle bleibt das Repo. Änderungen zuerst dort machen, dann neu spiegeln."
)

FORBIDDEN_PARTS = {
    ".git",
    "__pycache__",
    "machine-readable.local",
    "source-material.local",
}
FORBIDDEN_SUFFIXES = {
    ".pdf",
    ".docx",
    ".pptx",
    ".m4a",
    ".heic",
    ".jpg",
    ".jpeg",
    ".png",
}


@dataclass(frozen=True)
class ViewFile:
    source: str
    target: str
    mode: str


VIEW_FILES = (
    ViewFile("visuals/erzieherausbildung-systemkarte.canvas", "Systemkarte.canvas", "copy"),
    ViewFile("visuals/learning-map-v1.canvas", "Lernlandkarte.canvas", "copy"),
    ViewFile("docs/learning-map-v1.md", "Lernlandkarte.md", "markdown"),
    ViewFile("docs/knowledge-network-v1.md", "Wissensnetz.md", "markdown"),
    ViewFile("docs/pilot-index-v1.md", "Pilotindex.md", "markdown"),
    ViewFile("docs/detail-bridge-index-v1.md", "Detail-Brückenindex.md", "markdown"),
    ViewFile("docs/visualization-decision.md", "Visualisierungsentscheidung.md", "markdown"),
)
GENERATED_FILES = ("Start hier.md", MANIFEST_NAME)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET_DIR,
        help="Obsidian target directory, default: ~/vault-gewebe/schule/erzieherausbildung",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the planned export; do not create or write files.",
    )
    return parser.parse_args()


def resolve_inside_vault(target_dir: Path) -> tuple[Path, Path]:
    vault_root = DEFAULT_VAULT_ROOT.expanduser().resolve()
    target = target_dir.expanduser().resolve()
    try:
        target_relative = target.relative_to(vault_root)
    except ValueError as exc:
        raise SystemExit(f"target outside vault: {target} (vault root: {vault_root})") from exc
    ensure_safe_relative(str(target_relative), kind="target-dir")
    return vault_root, target


def ensure_safe_relative(path: str, *, kind: str) -> None:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SystemExit(f"unsafe {kind} path: {path}")
    lowered_parts = {part.lower() for part in candidate.parts}
    forbidden_parts = {part.lower() for part in FORBIDDEN_PARTS}
    if lowered_parts & forbidden_parts:
        raise SystemExit(f"forbidden path part in {kind}: {path}")
    if candidate.suffix.lower() in FORBIDDEN_SUFFIXES:
        raise SystemExit(f"forbidden suffix in {kind}: {path}")


def ensure_source_allowed(source: Path, spec: ViewFile) -> None:
    ensure_safe_relative(spec.source, kind="source")
    ensure_safe_relative(spec.target, kind="target")
    if not source.exists():
        raise SystemExit(f"missing source: {spec.source}")
    if not source.is_file():
        raise SystemExit(f"source is not a file: {spec.source}")
    if spec.mode == "copy" and source.suffix != ".canvas":
        raise SystemExit(f"copy mode is reserved for canvas files: {spec.source}")
    if spec.mode == "markdown" and source.suffix != ".md":
        raise SystemExit(f"markdown mode requires .md source: {spec.source}")


def run_git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def ensure_clean_vault(vault_root: Path) -> None:
    if not (vault_root / ".git").exists():
        raise SystemExit(f"vault root is not a git repository: {vault_root}")
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=vault_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"cannot determine vault git status: {result.stderr.strip()}")
    if result.stdout.strip():
        raise SystemExit("refusing to write: vault git status is not clean")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_with_warning(text: str) -> str:
    warning = f"> [!warning] {WARNING}\n\n"
    if text.startswith(warning):
        return text
    return warning + text.lstrip("\ufeff")


def write_markdown(source: Path, target: Path) -> None:
    target.write_text(markdown_with_warning(source.read_text(encoding="utf-8")), encoding="utf-8")


def copy_canvas(source: Path, target: Path) -> None:
    shutil.copyfile(source, target)


def build_start_text(source_head: str) -> str:
    body = f"""# Erzieherausbildung – Start hier

Quelle: `{CANONICAL_SOURCE_REPO}`  
Repo-Head beim letzten Export: `{source_head}`  
Status: Vault-Spiegel; kanonisch bleibt das Repo.

## Einstieg

1. [[Systemkarte.canvas]] – Gesamtoberfläche und Darstellungslogik.
2. [[Lernlandkarte.canvas]] – visuelle Lernachsen.
3. [[Lernlandkarte]] – textliche Orientierung zu Achsen und Themen.
4. [[Wissensnetz]] – Cluster, Brücken und Zusammenhangslogik.
5. [[Pilotindex]] – konkret lokalisierte Quellen und offene Quellenarbeit.
6. [[Detail-Brückenindex]] – Verbindungsknoten, Zielachsen und Brücken zwischen Detailkarten.
7. [[Visualisierungsentscheidung]] – warum Web, Canvas und spätere Kollaboration getrennte Rollen haben.

## Regel

Nicht hier als zweite Wahrheit weiterpflegen. Inhaltliche Änderungen zuerst im Repo machen und anschließend erneut spiegeln.
"""
    return markdown_with_warning(body)


def build_manifest(target: Path, source_head: str, managed: list[dict[str, str]]) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "policy": POLICY,
        "source_repo": str(CANONICAL_SOURCE_REPO),
        "source_worktree": str(REPO_ROOT),
        "source_remote": run_git(["remote", "get-url", "origin"]),
        "source_head": source_head,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "target_dir": str(target),
        "managed_files": managed,
        "forbidden_parts": sorted(FORBIDDEN_PARTS),
        "forbidden_suffixes": sorted(FORBIDDEN_SUFFIXES),
    }


def planned_files(target: Path) -> Iterable[tuple[str, Path]]:
    yield "generated", target / "Start hier.md"
    for spec in VIEW_FILES:
        yield spec.source, target / spec.target
    yield "generated", target / MANIFEST_NAME


def main() -> int:
    args = parse_args()
    vault_root, target = resolve_inside_vault(args.target_dir)

    for spec in VIEW_FILES:
        ensure_source_allowed(REPO_ROOT / spec.source, spec)
    for generated in GENERATED_FILES:
        ensure_safe_relative(generated, kind="generated")

    source_head = run_git(["rev-parse", "HEAD"])

    print(f"policy: {POLICY}")
    print(f"source_repo: {CANONICAL_SOURCE_REPO}")
    print(f"source_worktree: {REPO_ROOT}")
    print(f"source_head: {source_head}")
    print(f"vault_root: {vault_root}")
    print(f"target_dir: {target}")
    print("managed files:")
    for source, destination in planned_files(target):
        print(f"- {source} -> {destination}")

    if args.dry_run:
        return 0

    ensure_clean_vault(vault_root)
    target.mkdir(parents=True, exist_ok=True)

    managed: list[dict[str, str]] = []
    start_target = target / "Start hier.md"
    start_target.write_text(build_start_text(source_head), encoding="utf-8")
    managed.append({"target": start_target.name, "kind": "generated", "sha256": sha256_file(start_target)})

    for spec in VIEW_FILES:
        source = REPO_ROOT / spec.source
        destination = target / spec.target
        if spec.mode == "markdown":
            write_markdown(source, destination)
        elif spec.mode == "copy":
            copy_canvas(source, destination)
        else:
            raise SystemExit(f"unknown mode: {spec.mode}")
        managed.append({
            "source": spec.source,
            "target": spec.target,
            "mode": spec.mode,
            "sha256": sha256_file(destination),
        })

    manifest_managed = [*managed, {"target": MANIFEST_NAME, "kind": "manifest"}]
    manifest = build_manifest(target, source_head, manifest_managed)
    manifest_target = target / MANIFEST_NAME
    manifest_target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest_managed)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
