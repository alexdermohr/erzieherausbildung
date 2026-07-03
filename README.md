# Erzieherausbildung – Visualisierungssystem

Status: Korrektur v1. Rohmaterial bleibt lokal.

Gültige Quelle: `~/iCloud/Drive/inbox/erzieherausbildung`.

Die vorige Zuordnung zu `1. Semester` und `2. Semester` war falsch; diese Ordner sind für dieses Repo ausgeschlossen.

## Zweck

Visualisierung der Erzieherausbildung als Lernfeld-, Kompetenz- und Prüfungskarte, ohne Original-PDFs zu versionieren.

## Primärordnung

- `kein lernfeld`: Bildungsleitlinien, Informatik, Sprache und Kommunikation
- `lernfeld 1`: Berufsrolle, Haltung, Arbeitsbedingungen, Arbeitsfelder
- `lernfeld 2`: Eingewöhnung, Gespräche, Selbstwirksamkeit, Aufsichtspflicht, Konflikte, Wohngruppe
- `lernfeld 3`: Ressourcenorientierte Beobachtung, Politik, Selbstbestimmung, Wohngruppe
- `lernfeld 4`: Bildungsbereiche und Lernarrangements
- `lernfeld 5`: Elternkooperation

## Darstellungsentscheidung

Vercel/Web-App als Lesefläche, Obsidian Canvas als Denkfläche, Miro via Schauwerk als spätere Kollaborationsfläche.

## Lokal aktualisieren

```bash
python3 scripts/build_source_summary.py --source-root "$HOME/iCloud/Drive/inbox/erzieherausbildung" --output data/source-summary.json
python3 scripts/validate_repository.py
```
