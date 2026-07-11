# Input-Aufnahmeprozess v2

## Ziel

Neue Quellen und aktuelle Unterrichtsarbeiten werden kontrolliert aufgenommen, ohne Rohdatenlecks, Personenbezug oder unklare Autorität.

## Pfad A – Neue Quelle für den Kanon

1. Neue Datei lokal in den gültigen Ordner `erzieherausbildung` legen.
2. Scanner ausführen: `python3 scripts/build_source_summary.py --source-root source-material.local --output data/source-summary.json`.
3. Diff prüfen: neues Lernfeld, neuer Dateityp oder neue Menge?
4. Entscheiden: Strukturupdate, Exzerpt oder Detailänderung.
5. Exzerpt nach `schemas/excerpt.v1.schema.json` anlegen.
6. Repository-, Exzerpt- und Detailvalidatoren ausführen.
7. Feature-Branch und PR.

## Pfad B – Aktuelle Halbjahresarbeit

1. Vollständige Arbeit lokal behalten.
2. Namen, personenbezogene Falldaten und geschützte Materialien entfernen.
3. Kurze eigene Zusammenfassung, zugehörige Themen und offene Fragen bestimmen.
4. Mit `python3 scripts/create_current_work.py ...` eine schreibfreie Vorschau erzeugen.
5. Vorschau fachlich und datenschutzbezogen prüfen.
6. Denselben Befehl mit `--apply` ausführen.
7. `python3 scripts/validate_current_work.py` und die Gesamtvalidierung ausführen.
8. Feature-Branch und PR.

## Halbjahresabschluss

1. Aktive Arbeiten sichten.
2. Relevante Arbeiten fachlich prüfen und bei ausreichender Quellenbindung zu `canon-candidate` machen.
3. Bei Integration zuerst das konkrete Kanonziel ändern.
4. Mit `scripts/crystallize_current_work.py` die Entscheidung als Vorschau prüfen.
5. Mit `--apply` Arbeit, Index und Entscheidung unter exklusiver Sperre aktualisieren; erkannte Fehler werden zurückgerollt.
6. Nicht kanonische Arbeiten archivieren oder begründet verwerfen.

## Organe

- Quellenwächter;
- Datenschutzwächter;
- fachliche Redaktion;
- Visualisierungsorgan;
- Review-Gate.

## Oberflächen

Web ist Lesefläche, Canvas Denkfläche und Schauwerk/Miro eine spätere Kollaborationsfläche. Keine Oberfläche darf still zur zweiten Quelle werden.
