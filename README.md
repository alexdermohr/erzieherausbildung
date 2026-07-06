# Erzieherausbildung – Visualisierungssystem

Status: Korrektur v1. Rohmaterial bleibt lokal.

Gültige Quelle: `~/iCloud/Drive/inbox/erzieherausbildung`.

Die vorige Zuordnung zu `1. Semester` und `2. Semester` war falsch; diese Ordner sind für dieses Repo ausgeschlossen.

## Zweck

Visualisierung der Erzieherausbildung als Wissens-, Lernfeld- und Zusammenhangskarte, ohne Original-PDFs zu versionieren.

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
- Wissensnetz: [`docs/knowledge-network-v1.md`](docs/knowledge-network-v1.md) und [`data/knowledge-network.v1.json`](data/knowledge-network.v1.json)
- Darstellungsentscheidung: [`docs/visualization-decision.md`](docs/visualization-decision.md)
- Surface Policy: [`docs/surface-policy-v1.md`](docs/surface-policy-v1.md) und [`data/surface-policy.v1.json`](data/surface-policy.v1.json)
- Obsidian-Vault-Spiegel: [`docs/obsidian-vault-spiegel.md`](docs/obsidian-vault-spiegel.md) und Dry-Run mit `python3 scripts/obsidian_views.py --dry-run`

Gerendert anschauen: `index.html` im Browser öffnen; die `.canvas`-Dateien in Obsidian öffnen.

## Lokal aktualisieren

```bash
python3 scripts/build_source_summary.py --source-root "$HOME/iCloud/Drive/inbox/erzieherausbildung" --output data/source-summary.json
python3 scripts/validate_repository.py
```
