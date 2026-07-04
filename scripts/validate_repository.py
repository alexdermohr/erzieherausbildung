import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
required=["README.md","data/module-map.json","data/source-summary.json","docs/implementation-plan.md"]
for r in required: assert (root/r).exists(), f"missing {r}"
for p in root.rglob("*"):
    if any(part in p.parts for part in {".git", "source-material.local", "machine-readable.local"}): continue
    if p.is_file() and p.suffix.lower() in {".pdf",".docx",".pptx",".m4a",".heic",".jpg",".jpeg",".png"}: raise AssertionError(f"raw artifact committed: {p}")
mm=json.loads((root/"data/module-map.json").read_text(encoding="utf-8")); ss=json.loads((root/"data/source-summary.json").read_text(encoding="utf-8"))
assert ss["schema"]=="erzieherausbildung.source-summary.v2"
assert ss["sourceRootName"]=="erzieherausbildung"
assert ss["totals"]["files"]==29
assert ss["totals"]["extensions"]=={"pdf":29}
assert len(mm["modules"])==6
print("repository validation passed")
