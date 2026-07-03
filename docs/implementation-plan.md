# Umsetzungsplan: Erzieherausbildung optimal visualisieren

## These
Die optimale Umsetzung ist kein einzelnes Bild, sondern eine Pipeline: lokale Quellen werden sicher aufgenommen, semantisch verdichtet und auf mehreren Oberflaechen dargestellt.

## Antithese
Eine Pipeline kann zur Maschinenbuerokratie werden. Fuer Lernen zaehlt am Ende eine klare, schoene, verwendbare Karte. Wenn der Prozess schwerer ist als der Stoff, hat die Landkarte das Gelaende gefressen.

## Synthese
Minimal robuste Pipeline, maximal anschauliche Oberflaechen: Quellen lokal halten, Metadaten versionieren, Web fuer Ueberblick, Canvas fuer Denken, Miro/Schauwerk erst bei Kollaboration.

## Zielbild
Das Repo beantwortet drei Fragen: Was gibt es? Wie haengt es zusammen? Was mache ich damit?

## Phase 0 – Korrektur und Sicherung

- falsche Semesterordner als Quelle entfernen
- korrekten Quellordner `erzieherausbildung` setzen
- Scanner auf Lernfeldstruktur umstellen
- Rohdaten weiterhin ignorieren
- Validator gegen Rueckfall auf falsche Quelle aerweitern

Akzeptanz: `data/source-summary.json` zaehlt nur `erzieherausbildung`; Validierung laeuft lokal und in CI.

## Phase 1 – Strukturkarte v1
Web-App mit Lernfeldkarten, Obsidian-Systemkarte, Fokuskarte Lernfeld 4 und Schauwerk-DSL als Boardentwurf. Inhalte: Lernfelder 1–5 plus Querschnitt, Sinnachsen und Kernfragen.

## Phase 2 – Exzerptmodell
Von Dateititeln zu belastbaren Inhalten.

```text
data/excerpts/lernfeld-1.jsonl
docs/exzerpte/lernfeld-1.md
```

Jeder Eintrag braucht Quelle, Seiten-/Abschnittshinweis, Kurzinhalt, paedagogischen Begriff, Praxisbezug, Pruefungsrelevanz und Unsicherheitsgrad. Regel: Kein starker Claim ohne Exzerpt.

## Phase 3 – Web-App v2
Filter nach Lernfeld, Sinnachse, Praxisbezug und Pruefungsnaehe; Detailseiten pro Lernfeld; Querverbindungen; Lernmodus; Markdown-Export.

## Phase 4 – Canvas-Generator
`scripts/generate_canvas.py` erzeugt Systemkarte, Lernfeldkarten und Querschnittskarten aus `data/module-map.json`, `data/excerpts/*.jsonl` und `visuals/visual-spec.v1.json`.

## Phase 5 – Schauwerk/Miro
Aktivieren, wenn gemeinsame Sortierung, Praesentation oder grosse Zoomlandkarte gebraucht wird. Miro ist Arbeitsflaeche, nicht Quellenwahrheit.

## Phase 6 – Input-Aufnahmeprozess

1. Neue Dateien lokal in `erzieherausbildung/_eingang` oder ins passende Lernfeld legen.
6. Scanner laufen lassen.
3. Diff pruefen: Was ist neu? Welches Lernfeld? Welche Sinnachse?
4. Optional Exzerpt anlegen.
5. Web/Canvas generieren.
6. PR erstellen.
7. Review: Datenschutz, Quellenbezug, Visualisierungsnutzen.

## Repoarbeit
`main` bleibt stabil. Jede Strukturaenderung auf Feature-Branch. PR statt Direktpush. Pflichtcheck: `python3 scripts/validate_repository.py`.

## Risiko- und Nutzenabschaetzung
Nutzen: Orientierung, Lernen, Pruefung, Praxis, Nachtaltigkeit.
Risiken: Datenschutz, Falschzuordnung, Scheingenauigkeit, Tooldrift, Aesthetikfalle.
Gegenmassnahmen: `.gitignore`, Validator, gemeinsame Visual Spec, Exzerptmodell, PR-Review.

## Optimierungsgrad
Was: falsche Studienmodulkarte auf Lernfeldsystem korrigieren.

Wie: Datenmodell, Doku, Scanner, Canvas und Plan auf `erzieherausbildung` umstellen.

Wodurch: Lernfelder als Herkunftsachse, Sinnachsen als Verstehensachse, Exzerpte als spaetere Evidenzachse.

Wirkung: weniger Datenschutzrisiko, weniger Fehlzuordnung, bessere Erweiterbarkeit.

Nebenwirkung: Erste Version bleibt abstrakt; Detailkarten kommen erst nach Exzerptarbeit.

## Belegt / plausibel / spekulativ
Belegt: korrekter Ordner `erzieherausbildung`, Cluster `kein lernfeld` und `lernfeld 1`– lernfeld 5`, Bestand aus PDFs.
Plausibel: Lernfeld 4 braucht Fokuskarte; Sprache/Kommunikation ist Querschnitt; Web/Canvas/Miro ist robuster als eine Einzelflaeche.
Spekulativ: Pruefungsrelevanz einzelner Themen, Gewichtung einzelner PDFs, Miro-Sofortbedarf.

## Essenz
Hebel: Lernfeldstruktur plus Sinnachsen statt Dateisammlung.
Entscheidung: Web ist Leseflaeche, Canvas Denkflaeche, Miro Kollaborationsflaeche.
Naechste Aktion: Korrektur-PR abschliessen, dann Exzerptmodell bauen.
