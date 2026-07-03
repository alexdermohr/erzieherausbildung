# Architektur

## Ziel

Ein Visualisierungssystem für Ausbildungsstoff, das mit weiteren Quellen wachsen kann.

## Ebenen

### 1. Lokale Quellenebene

Ort: `~/iCloud/Drive/inbox`

Funktion: Rohmaterial bleibt lokal. Scanner erzeugen nur aggregierte, bereinigte Arbeitsdaten.

### 2. Semantische Ebene

Ort: `data/module-map.json`, `visuals/visual-spec.v1.json`

Funktion: Module, Themen, Sinnachsen, Lernziele, Prüfungsnähe und Visualisierungsformen werden getrennt von Rohdateien modelliert.

### 3. Darstellungsflächen

- Web-App: Überblick, Navigation, Filter, Prüfungsvorbereitung
- Obsidian Canvas: Denk-, Lehr- und Lernkarte
- Miro via Schauwerk: kollaborative, präsentierbare Zoomlandkarte

## Alternative Sinnachse

Die naheliegende Ordnung wäre Semester → Modul → Datei. Diese Ordnung ist administrativ korrekt, aber lernpsychologisch schwach.

Die zweite Ordnung ist Begriff → Praxis → Prüfung:

- Mensch/Person/Identität
- Kunst/Wissenschaft
- Beziehung/Anamnese/Wirkfaktoren
- Bildung/Pädagogik/Soziokultur
- Neuro/EEG/Emotion
- wissenschaftliches Arbeiten/Prüfung

Diese zweite Ordnung wird als Lernlandkarte bevorzugt; die Semesterstruktur bleibt als Such- und Herkunftsachse erhalten.
