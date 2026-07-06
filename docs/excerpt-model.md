# Exzerptmodell v1

## These
Die Lernfeldkarte wird erst belastbar, wenn sie nicht nur Dateititel, sondern geprüfte Exzerpte nutzt.

## Antithese
Zu viele Exzerpte machen aus der Karte wieder eine Textdeponie. Dann gewinnt die Ameise gegen die Landkarte.

## Synthese
Exzerpte bleiben kurz, quellenbezogen und nach Reifegrad markiert. `title-derived` ist Strukturhinweis, kein Inhaltsbeweis. `question` ist Arbeitsauftrag, kein Claim.

## Felder

Pflichtfelder stehen in `schemas/excerpt.v1.schema.json` und werden durch `scripts/validate_excerpts.py` geprüft:

- `id`
- `sourceCluster`
- `sourceTitle`
- `sourceLocator`
- `claimType`
- `summary`
- `concepts`
- `practiceUse`
- `links`
- `reviewStatus`
- `uncertainty`

## Claim-Disziplin

- `title-derived`: nur Strukturhinweis aus Metadaten; darf nicht `checked` sein und braucht `uncertainty >= 0.5`.
- `question`: offene Arbeitsfrage; darf nicht `checked` sein und braucht `uncertainty >= 0.5`.
- `excerpted`: quellennahe eigene Zusammenfassung; braucht konkrete Fundstelle.
- `interpreted`: Deutung aus einem Exzerpt; braucht konkrete Fundstelle und bleibt als Interpretation markiert.
- `checked`: nur für `excerpted` oder `interpreted`, nie für `title-derived` oder `question`.

## Verbotene Felder

`examRelevance`, `rawText`, `quote`, `pageImage` und `ocrText` sind verboten. Das Repo speichert keine Rohtexte und ordnet nicht nach Prüfungsnutzen.

## Resonanz- und Kontrastprüfung

Deutung A: Exzerpte sind kleine Inhaltsbausteine. Dann könnte man schnell viel Text sammeln.

Deutung B: Exzerpte sind Belegknoten. Dann muss jeder starke Claim Fundstelle, Reifegrad und Unsicherheit tragen. Dieses Modell folgt Deutung B.

## Epistemische Leere

Noch fehlen echte Exzerpte aus den Unterlagen. Nötig für Detailkarten: zwei Pilotquellen, eine aus Lernfeld 2 und eine aus Lernfeld 4.
