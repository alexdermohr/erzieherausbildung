#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "obsidian_views.py"


def load_obsidian_views():
    spec = importlib.util.spec_from_file_location("obsidian_views", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


OBSIDIAN_VIEWS = load_obsidian_views()
EXPECTED_FILES = {file.target for file in OBSIDIAN_VIEWS.VIEW_FILES} | set(OBSIDIAN_VIEWS.GENERATED_FILES)
MARKDOWN_TARGETS = {file.target for file in OBSIDIAN_VIEWS.VIEW_FILES if file.mode == "markdown"} | {"Start hier.md"}
POLICY = "repo-canonical-vault-derived"
SCHEMA = "erzieherausbildung.obsidian_view_export.v1"
WARNING = "SPIEGELDATEI aus /home/alex/repos/erzieherausbildung"


def run(args, *, cwd=None, env=None, check=True):
    result = subprocess.run(
        args,
        cwd=cwd or ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\n{result.stdout}\n{result.stderr}")
    return result


def init_clean_vault(vault: Path) -> None:
    vault.mkdir(parents=True)
    run(["git", "init"], cwd=vault)
    (vault / "seed.md").write_text("seed\n", encoding="utf-8")
    run(["git", "add", "seed.md"], cwd=vault)
    run([
        "git",
        "-c",
        "user.name=Validation",
        "-c",
        "user.email=validation@example.invalid",
        "commit",
        "-m",
        "init temp vault",
    ], cwd=vault)


def validate_with_temp_home(home: Path) -> None:
    env = {**os.environ, "HOME": str(home)}
    vault = home / "vault-gewebe"
    init_clean_vault(vault)
    target = vault / "schule" / "erzieherausbildung"

    dry = run([sys.executable, str(SCRIPT), "--dry-run"], env=env)
    assert str(target) in dry.stdout
    assert not target.exists()

    run([sys.executable, str(SCRIPT)], env=env)
    produced = {path.name for path in target.iterdir() if path.is_file()}
    assert produced == EXPECTED_FILES

    manifest = json.loads((target / ".erzieherausbildung-obsidian-view.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == SCHEMA
    assert manifest["policy"] == POLICY
    assert manifest["source_repo"] == "/home/alex/repos/erzieherausbildung"
    assert manifest["source_head"] != "UNKNOWN"
    assert manifest["target_dir"] == str(target)
    assert {entry["target"] for entry in manifest["managed_files"]} == EXPECTED_FILES
    assert "machine-readable.local" in manifest["forbidden_parts"]
    assert ".pdf" in manifest["forbidden_suffixes"]

    for name in MARKDOWN_TARGETS:
        assert WARNING in (target / name).read_text(encoding="utf-8")

    assert (ROOT / "visuals" / "erzieherausbildung-systemkarte.canvas").read_bytes() == (target / "Systemkarte.canvas").read_bytes()
    assert (ROOT / "visuals" / "learning-map-v1.canvas").read_bytes() == (target / "Lernlandkarte.canvas").read_bytes()
    pilot_text = (target / "Pilotindex.md").read_text(encoding="utf-8")
    assert "Offene Quellenarbeit" in pilot_text
    assert "Konkret lokalisierte Quellen im Pilot" in pilot_text
    bridge_text = (target / "Detail-Brückenindex.md").read_text(encoding="utf-8")
    assert "Detail-Brückenindex v1" in bridge_text
    assert "stärkste Verbindungsknoten" in bridge_text
    assert "Orientierung, keine neue Quelle" in bridge_text

    (vault / "dirty.md").write_text("dirty\n", encoding="utf-8")
    dirty = run([sys.executable, str(SCRIPT)], env=env, check=False)
    assert dirty.returncode != 0
    assert "refusing to write: vault git status is not clean" in dirty.stderr

    outside = run([sys.executable, str(SCRIPT), "--target-dir", str(home / "outside")], env=env, check=False)
    assert outside.returncode != 0
    assert "target outside vault" in outside.stderr


run([sys.executable, "-m", "py_compile", str(SCRIPT)])
with tempfile.TemporaryDirectory(prefix="erz-obsidian-export-") as temp:
    validate_with_temp_home(Path(temp) / "home")
print("obsidian export validation passed")
