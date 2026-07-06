# Review-Gates v1

## Pflichtchecks

- `python3 scripts/validate_repository.py`
- `python3 scripts/validate_excerpts.py`
- `python3 scripts/validate_view_export.py`

## Zweck

Der Repository-Validator schützt Struktur, Rohdaten-Grenze, Surface Policy und Quellenrahmen. Der Exzerpt-Validator schützt künftige JSONL-Exzerpte vor fehlenden Pflichtfeldern, falschem Claim-Typ, falschem Reviewstatus, ungültigem Unsicherheitsgrad und verbotenen Roh-/Prüfungsfeldern.

## Entscheidungsregel

Ein Exzerpt-PR darf nicht gemergt werden, wenn einer der Pflichtchecks fehlschlägt. Titelbasierte Einträge sind nur Strukturhinweise. Geprüfte inhaltliche Aussagen brauchen `excerpted` oder `interpreted`, eine konkrete `sourceLocator`-Fundstelle und `reviewStatus: checked`.

## Claim-Disziplin

- `title-derived` und `question` dürfen nicht `checked` sein.
- `title-derived` und `question` brauchen `uncertainty >= 0.5`.
- `excerpted` und `interpreted` brauchen eine konkrete Fundstelle.
- Prüfungsnutzen ist kein Ordnungsfeld; das Projekt ordnet nach Erkenntnisfunktion.
- Rohtexte, Zitate, Seitenbilder und OCR-Text bleiben außerhalb des Repos.

## Learning map v1

- `data/learning-map.v1.json` is the canonical data file.
- `docs/learning-map-v1.md` is the review surface.
- `visuals/learning-map-v1.canvas` is the first canvas render.
- `schemas/learning-map.v1.schema.json` documents the local contract; `scripts/validate_repository.py` enforces it.
