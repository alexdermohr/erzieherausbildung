import argparse,json
from pathlib import Path
from collections import Counter
ap=argparse.ArgumentParser(); ap.add_argument("--source-root",default="source-material.local"); ap.add_argument("--output",default="data/source-summary.json"); a=ap.parse_args()
root=Path(a.source_root).expanduser().resolve()
if root.name!="erzieherausbildung": raise SystemExit("wrong source root")
exts=Counter(); clusters=[]; files_total=0; bytes_total=0
for d in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p:p.name.casefold()):
    files=[p for p in d.rglob("*") if p.is_file()]; c=Counter((p.suffix.lower().lstrip(".") or "[noext]") for p in files); size=sum(p.stat().st_size for p in files)
    clusters.append({"title":d.name,"fileCount":len(files),"totalBytes":size,"extensions":dict(sorted(c.items()))}); files_total+=len(files); bytes_total+=size; exts.update(c)
out={"schema":"erzieherausbildung.source-summary.v2","sourceRootHint":"~/iCloud/Drive/inbox/erzieherausbildung","sourceRootName":root.name,"rawFilesCopied":False,"privacyMode":"aggregate-no-filenames","clusters":clusters,"totals":{"files":files_total,"bytes":bytes_total,"extensions":dict(sorted(exts.items()))}}
Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(f"wrote {a.output} with {files_total} files")
