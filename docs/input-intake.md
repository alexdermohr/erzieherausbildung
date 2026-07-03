# Input-Aufnahmeprozess v1

## Ziel
Neue Materialien werden kontrolliert aufgenommen, ohne falsche Quellen, Rohdatenlecks oder unklare Zuordnung.

## Ablauf
1. Neue Datei lokal in den Ordner `erzieherausbildung` legen.
2. Scanner laufen lassen: `python3 scripts/build_source_summary.py --source-root source-material.local --output data/source-summary.json`.
3. Diff prüfen: neues Lernfeld, neuer Dateityp, neue Menge?
4. Entscheiden: Strukturupdate oder Exzerpt?
5. Exzerpt nach `schemas/excerpt.v1.schema.json` anlegen.
6. Repository- und Exzerpt-Validator ausführen: `python3 scripts/validate_repository.py` und `python3 scripts/validate_excerpts.py`.
7. Feature-Branch und PR.

## Organe
Quellenwächter, Datenschutzwächter, Sinnachsenredaktion, Visualisierungsorgan, Review-Gate.

## Oberflächen
Web für stabile Lesefläche, Canvas für Denken, Miro via Schauwerk für Kollaboration.
