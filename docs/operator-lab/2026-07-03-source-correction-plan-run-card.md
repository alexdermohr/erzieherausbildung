# Operator-Lab Run Card: Erzieherausbildung Source Correction and Plan

Datum: 2026-07-03

## Trigger-Check

- PR-/Agentenlauf? yes — Korrektur eines Repos mit Feature-Branch und PR.
- Starker Claim möglich? yes — falsche Quellannahme wird korrigiert; Plan für Web/Canvas/Miro/Inputaufnahme wird gesetzt.
- Run Card nötig? yes — Quellenfehler und Korrekturprozess sind lernrelevant.

## Operation

Dokumentation, Datenmodell, Scanner, Canvas und Plan von falscher Semesterstruktur auf den korrekten Ordner `erzieherausbildung` umstellen.

## Befund

- Korrekte Quelle: iCloud-Inbox-Ordner `erzieherausbildung`.
- Enthaltene Cluster: `kein lernfeld`, `lernfeld 1`, `lernfeld 2`, `lernfeld 3`, `lernfeld 4`, `lernfeld 5`.
- Aktueller Dateibestand: 29 PDF-Dateien.
- Falsche Quellen der Vorversion: `1. Semester`, `2. Semester`; diese gehören zu Nicoles Studium.

## Entscheidung

Repo bleibt erhalten, wird aber semantisch korrigiert: Lernfelder werden Primärachse, Sinnachsen werden Verstehensachse, Exzerpte werden spätere Evidenzachse.

## Risiko

Hauptfehlerklasse: falsche Quellwurzel. Gegenmaßnahme: Scanner/Validator prüfen den korrigierten Quellenrahmen und Rohdaten bleiben ignoriert.
