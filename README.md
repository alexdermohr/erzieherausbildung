# Erzieherausbildung – Visualisierungssystem

Status: lebendiger Wissenskanon v1. Rohmaterial bleibt lokal.

Gültige Quelle: `~/iCloud/Drive/inbox/erzieherausbildung`.

Die vorige Zuordnung zu `1. Semester` und `2. Semester` war falsch; diese Ordner sind für dieses Repo ausgeschlossen.

## Zweck

Visualisierung der Erzieherausbildung als Wissens-, Lernfeld- und Zusammenhangskarte, ohne Original-PDFs zu versionieren. Das Repo hält den dauerhaften Ausbildungskanon und eine davon getrennte, zeitlich gebundene Ebene für freigegebene aktuelle Lehrer- und Schülerarbeiten.

## Primärordnung

- `kein lernfeld`: Bildungsleitlinien, Informatik, Sprache und Kommunikation
- `lernfeld 1`: Berufsrolle, Haltung, Arbeitsbedingungen, Arbeitsfelder
- `lernfeld 2`: Eingewöhnung, Gespräche, Selbstwirksamkeit, Aufsichtspflicht, Konflikte, Wohngruppe
- `lernfeld 3`: Ressourcenorientierte Beobachtung, Politik, Selbstbestimmung, Wohngruppe
- `lernfeld 4`: Bildungsbereiche und Lernarrangements
- `lernfeld 5`: Elternkooperation

## Darstellungsentscheidung

Vercel/Web-App als Lesefläche, Obsidian Canvas als Denkfläche, Miro via Schauwerk als spätere Kollaborationsfläche.


## Startpunkte

- Web-Lesefläche: [`index.html`](index.html)
- Systemkarte: [`visuals/erzieherausbildung-systemkarte.canvas`](visuals/erzieherausbildung-systemkarte.canvas)
- Lernlandkarte: [`visuals/learning-map-v1.canvas`](visuals/learning-map-v1.canvas) und [`docs/learning-map-v1.md`](docs/learning-map-v1.md)
- Lernfeld-Fokuskarten 1–5: [`data/learning-field-focus.v1.json`](data/learning-field-focus.v1.json), [`schemas/learning-field-focus.v1.schema.json`](schemas/learning-field-focus.v1.schema.json) und Generator [`scripts/build_learning_field_focus_maps.py`](scripts/build_learning_field_focus_maps.py)
- Homepage-Canvas- und Detailpfad: [`docs/canvas-homepage-detail-plan.md`](docs/canvas-homepage-detail-plan.md)
- Wissensnetz: [`docs/knowledge-network-v1.md`](docs/knowledge-network-v1.md) und [`data/knowledge-network.v1.json`](data/knowledge-network.v1.json)
- Pilot-Index: [`docs/pilot-index-v1.md`](docs/pilot-index-v1.md) und [`data/pilot-index.v1.json`](data/pilot-index.v1.json)
- Detail-Brückenindex: [`docs/detail-bridge-index-v1.md`](docs/detail-bridge-index-v1.md) und [`data/detail-bridge-index.v1.json`](data/detail-bridge-index.v1.json)
- Theoriekatalog: [`docs/theory-catalog-v1.md`](docs/theory-catalog-v1.md), [`data/theory-catalog.v1.json`](data/theory-catalog.v1.json), [`schemas/theory-catalog.v1.schema.json`](schemas/theory-catalog.v1.schema.json) und [`scripts/validate_theory_catalog.py`](scripts/validate_theory_catalog.py)
- Detailmodell: [`data/details/index.v1.json`](data/details/index.v1.json), [`schemas/detail.v1.schema.json`](schemas/detail.v1.schema.json), [`scripts/validate_details.py`](scripts/validate_details.py)
- Detail-Backlog: [`data/details/backlog.v1.json`](data/details/backlog.v1.json), [`schemas/detail-backlog.v1.schema.json`](schemas/detail-backlog.v1.schema.json), [`scripts/validate_detail_backlog.py`](scripts/validate_detail_backlog.py)
- Darstellungsentscheidung: [`docs/visualization-decision.md`](docs/visualization-decision.md)
- Surface Policy: [`docs/surface-policy-v1.md`](docs/surface-policy-v1.md) und [`data/surface-policy.v1.json`](data/surface-policy.v1.json)
- Lebendiger-Kanon-Plan: [`docs/living-canon-plan-v1.md`](docs/living-canon-plan-v1.md)
- Aktuelle Halbjahresarbeit: [`data/current-work/index.v1.json`](data/current-work/index.v1.json), [`schemas/current-work.v1.schema.json`](schemas/current-work.v1.schema.json) und [`docs/current-work-operations-v1.md`](docs/current-work-operations-v1.md)
- Betriebswerkzeuge: Aufnahme mit [`scripts/create_current_work.py`](scripts/create_current_work.py), Kandidatenbildung mit [`scripts/promote_current_work.py`](scripts/promote_current_work.py), Abschluss mit [`scripts/crystallize_current_work.py`](scripts/crystallize_current_work.py) und Halbjahreswechsel mit [`scripts/rollover_current_term.py`](scripts/rollover_current_term.py)
- Kristallisierungsentscheidungen: [`data/current-work/decisions.v1.json`](data/current-work/decisions.v1.json) und [`schemas/crystallization.v1.schema.json`](schemas/crystallization.v1.schema.json)
- Obsidian-Vault-Spiegel: [`docs/obsidian-vault-spiegel.md`](docs/obsidian-vault-spiegel.md) und Dry-Run mit `python3 scripts/obsidian_views.py --dry-run`

Gerendert anschauen: `index.html` im Browser öffnen; die `.canvas`-Dateien in Obsidian öffnen.

## Lokal aktualisieren

```bash
python3 scripts/build_source_summary.py --source-root "$HOME/iCloud/Drive/inbox/erzieherausbildung" --output data/source-summary.json
python3 scripts/build_learning_field_focus_maps.py
python3 scripts/build_theory_catalog.py --check
python3 scripts/validate_theory_catalog.py
python3 scripts/validate_current_work.py
python3 -m unittest -v tests.test_current_work_model
python3 scripts/validate_repository.py
```
