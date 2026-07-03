# Erzieherausbildung – Visualisierungssystem

Status: initiale Repo-Anlage, ohne Rohmaterial.

Dieses Repository macht Ausbildungs-/Studienmaterial aus der lokalen iCloud-Inbox sichtbar, ohne private oder urheberrechtlich geschützte Originaldateien zu versionieren.

## Ausgangslage

In der iCloud-Inbox wurde kein Ordner `erzieherausbildung` gefunden. Die relevante Materialstruktur liegt derzeit als `1. Semester` und `2. Semester` vor. Inhaltlich handelt es sich überwiegend um künstlerische Therapien, Musiktherapie, wissenschaftliches Arbeiten, Psychologie, pädagogische Anwendungsfelder und das Wahlmodul Kunst/EEG.

## Darstellungsentscheidung

Die beste Darstellung ist eine Kombination aus drei Ebenen:

1. **Vercel/Web-App**: publizierbare, schnelle Lernlandkarte für Navigation, Filter und Prüfungsvorbereitung.
2. **Obsidian `.canvas`**: lokale Denkfläche für Verdichtung, Ergänzungen und Seminar-/Prüfungslogik.
3. **Miro via Schauwerk**: kollaborative Zoomlandkarte, sobald ein Board aktiv erzeugt oder aktualisiert werden soll.

Die gemeinsame Quelle ist `visuals/visual-spec.v1.json`. Daraus können Web-App, Canvas und später Schauwerk/Miro gespeist werden.

## Was nicht ins Repo gehört

- keine PDFs, DOCX, PPTX, Bilder, HEIC-Dateien oder Audios aus der iCloud
- keine Atteste, Prüfungsunterlagen, personenbezogenen Dateien oder Seminararbeiten als Rohdatei
- keine OCR-Volltexte ohne explizite Prüfung

## Erste Artefakte

- `index.html` – statische Vercel-fähige Lernlandkarte
- `data/module-map.json` – kuratierte Modulachsen und Visualisierungslogik
- `data/source-summary.json` – aggregierte Quellenstatistik ohne Dateiliste
- `visuals/erzieherausbildung-systemkarte.canvas` – Obsidian-Systemkarte
- `visuals/m08-paedagogische-anwendungsfelder.canvas` – Fokuskarte für pädagogische Anwendungsfelder
- `visuals/schauwerk-erzieherausbildung-board.dsl` – Miro/Schauwerk-Boardentwurf
- `scripts/build_source_summary.py` – lokaler Scanner für aggregierte Metadaten
- `scripts/validate_repository.py` – Struktur-/JSON-/Canvas-Prüfung

## Lokal aktualisieren

```bash
python3 scripts/build_source_summary.py --source-root "$HOME/iCloud/Drive/inbox" --output data/source-summary.json
python3 scripts/validate_repository.py
```

## Vercel

Das Repo ist bewusst als statische Web-App angelegt. Vercel kann es ohne Build-Schritt ausliefern.

## Leitprinzip

Nicht: „alle Dateien irgendwo hübsch anzeigen“.

Sondern: **Ausbildungsstoff als navigierbare Sinnachsen sichtbar machen: Person, Bildung, Therapie, Wissenschaft, Kunst, Gesellschaft, Prüfung.**
