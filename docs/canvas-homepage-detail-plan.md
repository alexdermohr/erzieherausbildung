# Canvas-Homepage- und Detailverlinkungsplan v1

## These
Die Homepage soll die vorhandenen `.canvas`-Dateien nicht nur erwähnen, sondern direkt als visuelle Denkfläche anzeigen. Dadurch wird die Weboberfläche zur schnellen Lesefläche mit räumlicher Orientierung.

## Antithese
Eine native Canvas-Ansicht in der Homepage kann die Obsidian-Canvas-Erfahrung nicht vollständig ersetzen. Obsidian bleibt für manuelles Verschieben, räumliches Denken und spätere Verdichtung überlegen.

## Synthese
Die Homepage rendert `.canvas` read-only als Browseransicht. Obsidian bleibt Denkwerkzeug. Beide Flächen verwenden dieselben abgeleiteten Daten und dürfen keine Rohquellen veröffentlichen.

## Zielbild

```text
Übersicht
  -> Canvas-Knoten
    -> Themen- oder Achsendetail
      -> doc-ID-Rückbindung
        -> Exzerptschicht
          -> spätere Detailaufbereitung
            -> lokale Ursprungsquelle, nicht öffentlich
```

Die alternative Sinnachse kippt von „Welche Datei ist wo sichtbar?“ zu „Wie tief kann ein Lernender von der Karte zum belegten Wissen zoomen?“.

## Phase 1 - Homepage rendert vorhandene Canvas-Dateien

Akzeptanz:

- `index.html` enthält eine eigene Canvas-Sektion.
- `assets/app.js` lädt die Haupt- und Systemkarte sowie die aus `data/learning-field-focus.v1.json` erzeugten Fokuskarten für Lernfeld 1 bis 5.
- Die Canvas-Knoten und Kanten werden ohne externe Bibliothek als SVG gerendert.
- Die Ansicht bleibt read-only; die kanonischen `.canvas`-Dateien bleiben im Repo.

## Phase 2 - Knoten öffnen Detailkontext

Akzeptanz:

- Klick auf einen Canvas-Knoten öffnet ein Detailpanel.
- Achsenknoten werden mit `data/learning-map.v1.json` verbunden.
- Themenknoten werden über stabile IDs und Titelnormalisierung mit ihren Quellen verbunden.
- Das Panel zeigt Status, Quellen-IDs, vorhandene Pilotexzerpte und fehlende Detailtiefe.

## Phase 3 - Detailschicht ausbauen

Zielartefakte:

```text
data/details/*.v1.json
data/excerpts/*.jsonl
schemas/detail.v1.schema.json
scripts/validate_details.py
```

Jede Detaildatei soll enthalten:

- Begriff oder Thema
- Kurzdefinition
- fachliche Einordnung
- Praxisbezug
- typische Missverständnisse
- Brücken zu anderen Themen
- Exzerpte und Belegstatus
- offene Fragen

## Phase 4 - Canvas aus Daten generieren

Ziel:

```text
data/learning-map.v1.json
+ data/details/*.v1.json
+ data/excerpts/*.jsonl
  -> scripts/generate_canvas.py
  -> visuals/*.canvas
  -> Homepage und Obsidian
```

Damit wird vermieden, dass Web, Canvas und Markdown drei auseinanderlaufende Wahrheiten bilden. Drei Wahrheiten sind gut für Philosophie-Seminare, schlecht für Lernlandkarten.

## Quellen- und Oberflächenpolitik

Belegt sichtbar:

- eigene Strukturierung
- eigene Zusammenfassungen
- `doc-XXX`-Beleganker
- Fundstellenbeschreibungen aus Exzerpten
- Status der Aufbereitung

Nicht sichtbar:

- Roh-PDFs
- OCR-Rohtexte
- lokale Pfade
- `.local`-Arbeitsbereiche
- urheberrechtlich riskante Volltextauszüge

## Resonanz- und Kontrastprüfung

Deutung A: Die Karte ist primär eine schulische Lernfeldübersicht. Dann sind Sinnachsen, Lernfelder und Themenabdeckung entscheidend.

Deutung B: Die Karte ist primär eine Praxisbibliothek. Dann sind Beziehung, Beobachtung, Elternkooperation, Aufsicht, Sprache und Lernarrangements zentraler als Lernfeldnummern.

Das Modell hält beide Deutungen offen: Achsen geben Ordnung, Details geben Praxisnähe.

## Risiken und Gegenmaßnahmen

- Risiko: Die Browseransicht wirkt wie ein Ersatz für Obsidian. Gegenmaßnahme: read-only kennzeichnen.
- Risiko: grobe Zusammenfassungen werden als fertiges Wissen missverstanden. Gegenmaßnahme: Status und Detailtiefe sichtbar machen.
- Risiko: Rohmaterial wird versehentlich veröffentlicht. Gegenmaßnahme: nur abgeleitete Dateien laden, keine lokalen Quellenpfade.
- Risiko: Canvas, Web und Exzerpte driften auseinander. Gegenmaßnahme: späterer Generator und Validator.

## Unsicherheit

Unsicherheitsgrad: 0.24.
Ursachen: Die `.canvas`-Dateien sind vorhanden und renderbar, aber Detaildaten sind noch Pilotstand.

Interpolationsgrad: 0.31.
Hauptannahme: Die Homepage soll nicht nur eine Liste der Inhalte sein, sondern ein navigierbarer Einstieg vom Raumplan zur belegten Detailaufbereitung.

## Nächste Umsetzungsschritte

1. Canvas-Sektion in Homepage einbauen.
2. Canvas-Dateien als SVG rendern.
3. Knoten-Detailpanel mit vorhandenen `doc-XXX`-Quellen verbinden.
4. Pilotexzerpte anzeigen, wenn sie zur Quelle passen.
5. Spätere Detailschicht als offene Lücke sichtbar machen.


## Umsetzungsstand nach Detailmodell v1

Der erste Detailmodell-Slice ist bewusst klein: Er erzeugt fünf Detailaufbereitungen aus vorhandenen `excerpted`-Pilotexzerpten. Dadurch wird keine flächendeckende Tiefe behauptet. Sichtbar werden nur Themen, für die ein Detailobjekt mit `sourceRefs`, `excerptRefs`, `detailStatus`, `uncertainty` und `interpolation` existiert.

Aktive Detailthemen:

- Berufsrolle (`doc-004`)
- Eingewöhnung (`doc-008`)
- Beobachtung (`doc-014`)
- Lernarrangements (`doc-021`)
- Elternkooperation (`doc-029`)

Neue Artefakte:

```text
data/details/index.v1.json
data/details/detail-*.json
schemas/detail.v1.schema.json
scripts/validate_details.py
```

Resonanzprüfung: Die Detailschicht stärkt die Homepage als Lernfläche, ohne Obsidian als Denkfläche zu ersetzen. Kontrastprüfung: Wenn später alle 44 Themen sofort mit generischen Details gefüllt würden, entstünde Scheingenauigkeit. Deshalb bleibt die Detailschicht excerpt-gebunden und validiert.


## Detail-Coverage v1

Die Detailschicht weist nun explizit aus, wie viel Themenabdeckung sie hat. `data/details/index.v1.json` enthält eine `coverage`-Sektion mit Gesamtzahl, Detailzahl, fehlenden Themen und Achsenaufschlüsselung.

These: Coverage-Signale machen die Lernlandkarte ehrlicher, weil sie Tiefe nicht behaupten, sondern anzeigen.
Antithese: Sichtbare Lücken können unfertig wirken.
Synthese: Das ist erwünscht. Die Lücke ist ein Arbeitsauftrag, kein Makel.

Nutzen: Die Homepage kann `Detail vorhanden` und `Detail offen` markieren.
Risiko: Nutzer könnten offene Themen als unwichtig lesen. Gegenmittel: Der Text benennt die epistemische Leere ausdrücklich.

## Detail-Backlog v1

Die Detailausweitung bleibt quellengebunden. Da derzeit nur fünf `excerpted`-Exzerpte vorhanden sind, erzeugt der nächste Schritt keine erfundenen Detailseiten, sondern eine validierte Arbeitsliste der 39 offenen Themen.

These: Ein Backlog ist hier produktiver als generische Details, weil es die nächste Exzerptarbeit steuert.
Antithese: Der sichtbare Fortschritt wirkt kleiner als neue Detailkarten.
Synthese: Das ist fachlich sauberer. Erst Exzerpt, dann Detail.

Neue Artefakte:

```text
data/details/backlog.v1.json
schemas/detail-backlog.v1.schema.json
scripts/validate_detail_backlog.py
```

Regel: Kein Thema wandert aus dem Backlog in `data/details/*.json`, bevor ein neues `excerpted` oder `interpreted` Exzerpt vorliegt.

## Detail-Slice Sprache und Kommunikation v1

Der erste Backlog-Eintrag `sprache-kommunikation` wurde aus `needs-source-location` herausgelöst: `doc-011` liefert eine konkrete Fundstelle zur dialogischen Bilderbuchbetrachtung und Literacy. Daraus wurden ein excerpted Exzerpt und eine Detaildatei erzeugt. Coverage steigt von 5/44 auf 6/44; der Backlog sinkt von 39 auf 38 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.


## Detail-Slice Ressourcenorientierung v1

Der Medium-Backlog-Eintrag `ressourcenorientierung` wurde aus `doc-014` herausgelöst. Die lokale Fundstelle beschreibt Ressourcen als Fähigkeiten, Interessen, Stärken und unterstützende Kontexte und grenzt Ressourcenorientierung von Defizitblindheit ab. Coverage steigt von 6/44 auf 7/44; der Backlog sinkt von 38 auf 37 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.


## Detail-Slice Fallverstehen v1

Der Medium-Backlog-Eintrag `fallverstehen` wurde aus `doc-014` herausgelöst. Die lokale Fundstelle verbindet Beobachtung, Reflexion, kollegialen Austausch, Hypothesenbildung und nächste Schritte. Coverage steigt von 7/44 auf 8/44; der Backlog sinkt von 37 auf 36 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.


## Detail-Slice Förderplanung v1

Der Backlog-Eintrag `foerderplanung` wurde aus `doc-014` herausgelöst. Die lokale Fundstelle beschreibt Förderplanung als gezielte Planung nächster Schritte auf Basis dokumentierter Beobachtungen, kollegialem Austausch, Dialog mit dem Kind und Gestaltung der Lernumgebung. Coverage steigt von 8/44 auf 9/44; der Backlog sinkt von 36 auf 35 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.


## Detail-Slice Bindung und Beziehung v1

Der Medium-Backlog-Eintrag `bindung-beziehung` wurde aus `doc-008` herausgelöst. Die lokale Fundstelle beschreibt eine tragfähige Fachkraft-Kind-Beziehung mit bindungsähnlichen Eigenschaften als Sicherheitsgrundlage für Eingewöhnung, Exploration und Bildungsprozesse. Coverage steigt von 9/44 auf 10/44; der Backlog sinkt von 35 auf 34 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.


## Detail-Slice Übergänge v1

Der Medium-Backlog-Eintrag `uebergaenge` wurde aus `doc-008` herausgelöst. Die lokale Fundstelle beschreibt Übergänge als sensible Wechselprozesse, die stabile Rahmenbedingungen, Vorhersagbarkeit, Übergangsobjekte, Elternbezug und kindorientierte Sicherheit benötigen. Coverage steigt von 10/44 auf 11/44; der Backlog sinkt von 34 auf 33 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.

## Source-Health v1

Die Detailausweitung darf nicht nur Backlog-getrieben sein. Vor neuen Details muss sichtbar sein, ob die lokale Textgrundlage tragfähig ist.

Befund: `doc-029` ist lokal als Textdatei vorhanden, aber leer. Daher werden `erziehungspartnerschaft` und `familienperspektive` vorerst nicht ausgebaut, obwohl sie im Backlog als `medium` erscheinen.

Synthese: Eine Source-Health-Projektion macht solche Lücken sichtbar, ohne Rohtexte, OCR oder lokale absolute Pfade zu veröffentlichen.


## Detail-Slice Erziehungspartnerschaft v1

Der Medium-Backlog-Eintrag `erziehungspartnerschaft` wurde nach der lokalen Reparatur von `doc-029` herausgelöst. Die lokale Fundstelle fokussiert Eltern-Erzieher-Kooperation, Sprachbarrieren, Augenhöhe, Vertrauensaufbau und die Priorität auf dem Kind. Coverage steigt von 11/44 auf 12/44; der Backlog sinkt von 33 auf 32 offene Themen.

Prämisse: Nur eigene Zusammenfassung und Beleganker werden committed. Rohtext bleibt lokal.
