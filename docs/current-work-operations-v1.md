# Aktuelle Arbeit aufnehmen und kristallisieren

## Neue Arbeit vorbereiten

Der Befehl schreibt standardmäßig nichts. Er zeigt zunächst die erzeugte Struktur:

```bash
python3 scripts/create_current_work.py \
  --id work-2026-sommer-eingewoehnung-vergleich \
  --title "Vergleich von Eingewöhnungsansätzen" \
  --topic eingewoehnung \
  --summary "Knappe eigene Zusammenfassung ohne Personenbezug." \
  --open-question "Welche Rolle spielt die Beteiligung der Eltern?"
```

Die Vorschau bleibt außerhalb des Repo. Erst nach Prüfung wird derselbe Befehl um `--publication-status published --review-status checked --apply` ergänzt. Das Repo ist öffentlich; eine nur ausgeblendete Datei wäre nicht vertraulich.

## Zum Kanon-Kandidaten machen

Eine neu aufgenommene Arbeit beginnt immer als `active`. Erst nach fachlicher Prüfung und Quellenbindung macht das eigene Werkzeug sie zum Kandidaten:

```bash
python3 scripts/promote_current_work.py \
  --work-id work-... \
  --key-finding "Dauerhaft relevante Erkenntnis" \
  --source-ref doc-XXX
```

Nach der Vorschau schreibt erst `--apply`.

## Halbjahresentscheidung

### Archivieren

```bash
python3 scripts/crystallize_current_work.py \
  --work-id work-... \
  --decision archived \
  --essence "Für den Lernprozess wertvoll, aber keine dauerhafte Kanonerweiterung." \
  --decided-on 2026-07-31
```

### Fachlich zurückziehen

```bash
python3 scripts/crystallize_current_work.py \
  --work-id work-... \
  --decision rejected \
  --essence "Fachlich nicht tragfähig; nicht weiter anzeigen." \
  --decided-on 2026-07-31
```

Die Arbeit erhält `publicationStatus: withdrawn` und wird nicht mehr gerendert. Sie bleibt jedoch im öffentlichen Git-Verlauf. Dieser Weg ist daher keine Lösung für versehentlich veröffentlichte personenbezogene Daten.

### Integrieren

Vorher muss die genannte Kanondatei im aktuellen Branch tatsächlich verändert werden. Danach:

```bash
python3 scripts/crystallize_current_work.py \
  --work-id work-... \
  --decision integrated \
  --target-id detail-eingewoehnung-v1 \
  --canon-change-ref data/details/detail-eingewoehnung-v1.json \
  --essence "Verdichtete, dauerhaft relevante Aussage." \
  --decided-on 2026-07-31
```

Auch hier schreibt erst `--apply`.

## Nächstes Halbjahr öffnen

Ein Halbjahr kann nur geschlossen werden, wenn keine Arbeit mehr `active` oder `canon-candidate` ist:

```bash
python3 scripts/rollover_current_term.py \
  --id 2026-winter \
  --label "Winterhalbjahr 2026/27" \
  --starts-on 2026-08-01 \
  --ends-on 2027-01-31
```

Nach der Vorschau schreibt erst `--apply`. Das Werkzeug schließt das bisherige Halbjahr und setzt genau ein neues Halbjahr auf `current`.

## Pflichtprüfungen

```bash
python3 scripts/validate_current_work.py
python3 -m unittest -v tests.test_current_work_model
python3 scripts/validate_repository.py
```

## Schreib- und Wiederherstellungsvertrag

Jedes Werkzeug ersetzt einzelne JSON-Dateien atomar und hält während der gesamten Mutation eine exklusive lokale Sperre. Dadurch können zwei Prozesse dieselben Indizes nicht gleichzeitig verändern. Mehrere Dateien bilden jedoch keine gemeinsame Datenbanktransaktion. Bei einem erkannten Fehler stellt das Werkzeug die vorherigen Inhalte wieder her; nach einem abrupten Prozess- oder Rechnerabbruch muss Git den Zwischenstand prüfen und gegebenenfalls zurücksetzen.

## Grenzen

- Die Werkzeuge ersetzen keine fachliche Entscheidung.
- Vollständige Originalarbeiten bleiben lokal.
- Eine Integration gilt nur, wenn die zum Ziel passende Kanondatei in derselben Änderung fachlich angepasst wurde.
- Klarnamen, E-Mail-Adressen und personenbezogene Falldaten gehören nicht in die Eingabe. Die Feldprüfung erkennt keine Namen, die in Freitext versteckt sind; deshalb bleibt eine manuelle Datenschutzprüfung zwingend.
