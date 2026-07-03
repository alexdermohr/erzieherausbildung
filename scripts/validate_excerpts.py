#!/usr/bin/env python3
import json
from pathlib import Path
REQ={'id','sourceCluster','sourceTitle','claimType','summary','concepts','practiceUse','reviewStatus','uncertainty'}
CLAIMS={'title-derived','excerpted','interpreted','question'}
STATUS={'draft','checked','needs-source','rejected'}
root=Path(__file__).resolve().parents[1]
errors=[]
for path in sorted((root/'data'/'excerpts').glob('*.jsonl')):
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: item=json.loads(line)
        except Exception as e:
            errors.append(f'{path}:{i}: invalid json: {e}'); continue
        miss=REQ-set(item)
        if miss: errors.append(f'{path}:{i}: missing {sorted(miss)}')
        if item.get('claimType') not in CLAIMS: errors.append(f'{path}:{i}: bad claimType')
        if item.get('reviewStatus') not in STATUS: errors.append(f'{path}:{i}: bad reviewStatus')
        if not isinstance(item.get('concepts'),list): errors.append(f'{path}:{i}: concepts must be list')
        u=item.get('uncertainty')
        if not isinstance(u,(int,float)) or not 0<=u<=1: errors.append(f'{path}:{i}: bad uncertainty')
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
print('excerpt validation passed')
