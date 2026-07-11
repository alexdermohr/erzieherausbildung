# Lebendiger Wissenskanon der Erzieherausbildung – Plan v1

Status: technische Grundlage umgesetzt; realer Halbjahresbetrieb beginnt mit den ersten freigegebenen Arbeitsergebnissen.

## These

Die Visualisierung soll zugleich eine übersichtliche Gesamtschau des dauerhaften Ausbildungswissens und eine aktuelle Darstellung gegenwärtiger Unterrichtsarbeit sein.

## Antithese

Werden Kanon und laufende Arbeit gleich dargestellt, wirken vorläufige Ergebnisse wie gesichertes Wissen. Eine ungebremste Ablage aller Arbeiten würde außerdem die Übersicht zerstören und Datenschutzrisiken erhöhen.

## Synthese

Ein gemeinsamer Wissensraum mit zwei ausdrücklich getrennten Inhaltsebenen:

- `canon`: geprüftes, dauerhaft relevantes und quellengebundenes Wissen;
- `current-work`: laufende Ausarbeitungen, Fragen und Ergebnisse eines Halbjahres.

Die Weboberfläche ist eine abgeleitete Lesefläche. Kanonisch bleiben die strukturierten Daten und Verträge im Repo. Aktuelle Arbeit verändert den Kanon erst durch eine dokumentierte Kristallisierungsentscheidung.

## Zielbild

```text
lokale Unterrichtsarbeit
        │
        ▼
strukturierte aktuelle Arbeit
        │
        ├──────────────► Webansicht „Aktuelles Halbjahr“
        │
        ▼
fachliche und quellenbezogene Prüfung
        │
        ▼
Kanon-Kandidat
        │
   ┌────┴──────────┐
   ▼               ▼
integrieren   archivieren / verwerfen
   │
   ▼
bestehender Ausbildungskanon
```

## Autoritäten

| Bestandteil | Funktion | Autorität |
| --- | --- | --- |
| strukturierte Repo-Daten | Inhalt, Reife und Beziehungen | kanonisch |
| Web | Überblick und Lesen | abgeleitet |
| Obsidian Canvas | Denken und räumliches Ordnen | abgeleitet |
| Schauwerk/Miro | spätere gemeinsame Sortierung | abgeleitet |
| lokale Originale | Herkunftsmaterial | privat |
| CI und Validatoren | Konsistenz- und Datenschutzprüfung | prüfend |

## Datenmodell

### Inhaltsebene

Aktuelle Arbeiten tragen immer:

```json
"contentLayer": "current-work"
```

Der bestehende Kanon wird nicht rückwirkend mit einem zusätzlichen Statusfeld überzogen. Seine kanonische Rolle ergibt sich aus den bestehenden Detail-, Theorie-, Lernkarten- und Wissensnetzverträgen.

### Lebenszyklus

- `active`: laufende Arbeit;
- `canon-candidate`: geprüft und für dauerhafte Verdichtung geeignet;
- `integrated`: Essenz wurde in konkret benannte Kanondateien übernommen;
- `archived`: für den Lernprozess relevant, aber nicht kanonisch;
- `rejected`: ungeeignet, redundant, unbelegt oder nicht veröffentlichbar.

### Prüfstatus

- `draft`;
- `checked`;
- `needs-source`;
- `rejected`.

Lebenszyklus und Prüfstatus bleiben getrennt. Ein Kanon-Kandidat braucht `checked`, mindestens eine Erkenntnis und mindestens eine Quellenreferenz.

### Veröffentlichung und Datenschutz

Das Repo ist öffentlich. Deshalb ist Ausblenden keine Vertraulichkeit: `local-preview` darf nur als schreibfreie Vorschau erscheinen und niemals im Index landen. Jede neu eingecheckte Arbeit trägt `publicationStatus: published` und muss fachlich sowie datenschutzbezogen geprüft sein. Eine fachlich verworfene Arbeit wechselt zu `withdrawn`; sie verschwindet aus der Website, bleibt aber im öffentlichen Git-Verlauf. Das ist keine Datenschutzreparatur.

- keine Klarnamenfelder;
- keine freien Personenangaben;
- nur rollenbezogene Urheberschaft;
- `personalDataIncluded` muss `false` sein;
- Rohmaterial, direkte Zitate, Screenshots, OCR-Artefakte und lokale Pfade sind blockiert.

## Kristallisierung

Am Halbjahresende erhält jede relevante Arbeit genau eine Entscheidung:

1. `integrated`: bestehender Kanon wurde nachweislich verändert;
2. `archived`: Arbeit bleibt nachvollziehbar, erscheint aber nicht mehr als aktuell;
3. `rejected`: Arbeit wird fachlich verworfen und als `withdrawn` nicht mehr angezeigt. Personenbezogene Veröffentlichungsfehler dürfen nicht durch bloßes Zurückziehen behandelt werden.

Eine Integration braucht:

- konkrete Kanon-Ziel-IDs;
- eine verdichtete Essenz;
- konkret benannte geänderte Kanondateien;
- eine bereits geprüfte Arbeit im Zustand `canon-candidate`.

Das Kristallisierungswerkzeug prüft zusätzlich, dass die genannten Kanondateien im aktuellen Branch tatsächlich geändert wurden.

## Phasen und Stand

### Phase 0 – Vertrag und Begriffe

**Stand: umgesetzt**

- Zielbild und Autoritätsgrenzen dokumentiert;
- Kanon und aktuelle Arbeit getrennt;
- Datenschutz- und Nicht-Ziele festgelegt;
- Surface Policy erweitert.

### Phase 1 – Datenverträge und Validatoren

**Stand: umgesetzt**

- `schemas/current-work.v1.schema.json`;
- `schemas/crystallization.v1.schema.json`;
- Halbjahresindex und Entscheidungsindex;
- Referenz-, Lebenszyklus-, Quellen- und Datenschutzprüfung;
- Testabdeckung für zentrale Fehlfälle.

### Phase 2 – Aufnahme ohne JSON-Handarbeit

**Stand: umgesetzt**

`scripts/create_current_work.py` erzeugt im Vorschaumodus ein geprüftes Arbeitsergebnis. Erst `--apply` ersetzt die einzelne Arbeitsdatei und den Index unter exklusiver Sperre. Erkannte Fehler werden zurückgerollt; ein abrupter Prozessabbruch bleibt über Git prüf- und reparierbar.

### Phase 3 – Webdarstellung

**Stand: umgesetzt**

- ruhige Kanonansicht bleibt Standard;
- Umschalter zwischen Gesamtschau und aktuellem Halbjahr;
- aktuelle Arbeiten erscheinen in einer eigenen Halbjahresfläche;
- bei vorhandenen Arbeiten werden sie zusätzlich an den betroffenen Themen sichtbar;
- leerer Live-Bestand wird ehrlich und verständlich angezeigt.

### Phase 4 – Kristallisierungswerkzeug

**Stand: umgesetzt**

`scripts/promote_current_work.py` bildet quellengebundene Kanon-Kandidaten. `scripts/crystallize_current_work.py` aktualisiert Arbeit, Index und Entscheidung unter exklusiver Sperre mit Fehler-Rollback; eine Integration ist nur mit der zum Ziel passenden, tatsächlich geänderten Kanondatei zulässig. `scripts/rollover_current_term.py` öffnet ein neues Halbjahr erst, wenn keine Arbeit des alten Halbjahres offen bleibt.

### Phase 5 – CI und Betriebsdokumentation

**Stand: umgesetzt**

- Validator und Modelltests in der GitHub-Action;
- Aufnahme- und Abschlussprozess dokumentiert;
- Repository-Validator verlangt alle neuen Verträge und Datenquellen.

### Phase 6 – Realer Halbjahreszyklus

**Stand: fachlich offen, nicht technisch blockiert**

Der öffentliche Live-Bestand bleibt leer, bis reale, anonymisierte und freigegebene Lehrer- oder Schülerarbeiten vorliegen. Es werden keine Arbeitsergebnisse erfunden.

Nach dem ersten realen Zyklus werden geprüft:

- Beitragsmenge und redaktioneller Aufwand;
- Verständlichkeit der Trennung von Kanon und aktueller Arbeit;
- Nutzen der Arbeiten für Orientierung und Lernen;
- unnötige Statuswerte und Oberflächenelemente;
- Qualität der Kristallisierungsentscheidungen.

## Aufnahmeprozess

1. Material bleibt zunächst lokal.
2. Personenbezug und geschützte Inhalte entfernen.
3. Thema, Halbjahr und knappe eigene Zusammenfassung bestimmen.
4. Mit `scripts/create_current_work.py` eine Vorschau erzeugen.
5. Vorschau fachlich und datenschutzbezogen prüfen.
6. Mit `--apply` schreiben.
7. Gesamtvalidator ausführen.
8. Änderung über Branch und PR veröffentlichen.

## Nicht-Ziele

- kein Lernmanagementsystem;
- keine Noten- oder Anwesenheitsverwaltung;
- keine öffentliche Ablage vollständiger Schülerarbeiten;
- keine direkte Browserbearbeitung des Kanons;
- keine automatische KI-Kanonisierung;
- kein zweites Statussystem außerhalb des Repos;
- keine chronologische Vollarchivierung jeder Unterrichtsstunde.

## Risiken

| Risiko | Gewicht | Gegenmaßnahme |
| --- | ---: | --- |
| Entwurf wirkt wie Kanon | hoch | getrennte Inhaltsebene und Standardansicht Kanon |
| Oberfläche wird metareich | hoch | nur ein Umschalter; technische Statusdaten eingeklappt |
| personenbezogene Daten | kritisch | blockierende Felder und rollenbezogene Urheberschaft |
| Kanon wächst ungebremst | hoch | Integration bevorzugt bestehende Kanonziele |
| Abschluss bleibt aus | hoch | explizites Kristallisierungswerkzeug und Entscheidungsindex |
| erfundener Live-Bestand | hoch | leerer Zustand bis reale Inhalte freigegeben sind |

## Abnahmekriterien

- Kanon bleibt ohne aktuelle Arbeiten vollständig lesbar.
- Vorläufige Inhalte sind nicht mit Kanon verwechselbar.
- Jede aktuelle Arbeit besitzt mindestens einen fachlichen Zielbezug.
- Kanon-Kandidaten sind geprüft und quellengebunden.
- Terminale Lebenszyklen besitzen genau eine Kristallisierungsentscheidung.
- Eine Integration benennt bestehende und im Branch geänderte Kanondateien.
- Keine blockierten Roh- oder Personendaten passieren die CI.
- Leere Halbjahre erzeugen eine verständliche, nicht kaputte Oberfläche.

## Evidenzlage

### Belegt

Das Repo besitzt bereits strukturierte Lernkarten, Details, Exzerpte, Theorien, Wissensnetze, Quellenverträge und mehrere abgeleitete Oberflächen.

### Plausibel

Aktuelle Arbeit kann über dieselben Themen- und Wissensachsen angebunden werden, ohne eine zweite Anwendung einzuführen.

### Spekulativ

Beitragsmenge, redaktionelle Zuständigkeit und tatsächlicher Pflegeaufwand sind erst nach einem realen Halbjahr belastbar.

**Fehlt:** reale freigegebene Arbeit; nötig für den inhaltlichen Live-Betrieb.

**Unsicherheit:** 0,23. Ursache: technische Verträge sind prüfbar; der soziale Betrieb ist noch unerprobt.

**Interpolationsgrad:** 0,27. Ursache: die Architektur setzt vorhandene Repo-Prinzipien auf einen neuen Halbjahresprozess fort.

## Schluss

**Hebel:** harte Autoritätstrennung, fachliche Verankerung und verbindliche Kristallisierung.

**Entscheidung:** technische Infrastruktur vollständig bereitstellen, aber keine Beispielarbeiten als reale Unterrichtsergebnisse ausgeben.

**Nächste Aktion:** erstes reales, anonymisiertes Arbeitsergebnis über den Aufnahmebefehl hinzufügen und im Web prüfen.
