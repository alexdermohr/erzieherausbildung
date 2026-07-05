# Obsidian-Vault-Spiegel

Status: Hilfsoberfläche, nicht Kanon.

## These / Antithese / Synthese

These: Die vorhandenen Markdown- und Canvas-Views gehören in Obsidian, weil sie dort als Denk- und Navigationsfläche sofort nutzbar sind.

Antithese: Ein unkontrollierter Vault-Spiegel erzeugt eine zweite Wahrheit, Drift und versehentlich versionierte Rohmaterialien.

Synthese: Der Export ist deterministisch und Safe-List-basiert. Das Repo bleibt kanonisch; der Vault enthält nur abgeleitete View-Dateien.

## Zielpfad

Default:

```bash
~/vault-gewebe/schule/erzieherausbildung
```

Der Export verweigert Zielpfade außerhalb von `~/vault-gewebe`.

## Erlaubte Quellen

Nur diese Repo-Dateien werden gespiegelt:

- `visuals/erzieherausbildung-systemkarte.canvas` -> `Systemkarte.canvas`
- `visuals/learning-map-v1.canvas` -> `Lernlandkarte.canvas`
- `docs/learning-map-v1.md` -> `Lernlandkarte.md`
- `docs/knowledge-network-v1.md` -> `Wissensnetz.md`
- `docs/visualization-decision.md` -> `Visualisierungsentscheidung.md`

Zusätzlich werden erzeugt:

- `Start hier.md`
- `.erzieherausbildung-obsidian-view.json`

## Bedienung

Dry-Run ohne Vault-Mutation:

```bash
python3 scripts/obsidian_views.py --dry-run
```

Sync in den Default-Zielpfad:

```bash
python3 scripts/obsidian_views.py
```

Alternativer Zielpfad innerhalb des Vaults:

```bash
python3 scripts/obsidian_views.py --target-dir "$HOME/vault-gewebe/schule/erzieherausbildung-test"
```

## Sicherheitsregeln

- Keine PDFs, Rohtexte, OCR-Artefakte, Bilder oder Office-Dateien spiegeln.
- Kein `machine-readable.local/` spiegeln.
- Kein `source-material.local/` spiegeln.
- Kein gesamtes Repo ins Vault kopieren. Das heißt auch: kein gesamtes Repo spiegeln.
- Markdown-Spiegeldateien bekommen den Warnhinweis: „SPIEGELDATEI aus /home/alex/repos/erzieherausbildung. Kanonische Quelle bleibt das Repo. Änderungen zuerst dort machen, dann neu spiegeln.“
- Canvas-Dateien werden unverändert kopiert.
- Schreibmodus stoppt, wenn der Vault-Git-Status nicht sauber belegbar ist.

## Risiken

Drift entsteht, wenn Inhalte im Vault editiert und nicht ins Repo zurückgeführt werden. Das Manifest hilft beim Erkennen des letzten Export-Heads, ersetzt aber keine inhaltliche Rückführung.

Die Hauptfehlannahme wäre: „Obsidian ist bequemer, also wird es Quelle.“ Genau das soll der Export verhindern. Bequemlichkeit ist hier Oberfläche, nicht Autorität.
