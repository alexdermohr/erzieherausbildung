# Review-Gates v1

## Pflichtchecks

- `python3 scripts/validate_repository.py`
- `python3 scripts/validate_excerpts.py`

## Zweck

Der Repository-Validator schützt Struktur, Rohdaten-Grenze und Quellenrahmen. Der Exzerpt-Validator schützt künftige JSONL-Exzerpte vor fehlenden Pflichtfeldern, falschem Claim-Typ, falschem Reviewstatus und ungültigem Unsicherheitsgrad.

## Entscheidungsregel

Ein Exzerpt-PR darf nicht gemergt werden, wenn einer der beiden Checks fehlschlägt. Titelbasierte Einträge sind nur Strukturhinweise; geprüfte inhaltliche Aussagen brauchen `excerpted` oder `interpreted` plus Reviewstatus.

## Learning map v1

- `data/learning-map.v1.json` is the canonical data file.
- `docs/learning-map-v1.md` is the review surface.
- `visuals/learning-map-v1.canvas` is the first canvas render.
- `schemas/learning-map.v1.schema.json` documents the local contract; `scripts/validate_repository.py` enforces it.
