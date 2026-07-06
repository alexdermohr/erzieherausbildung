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

Prüfungsnutzen, Rohtext, Direktzitat, Seitenbild und OCR-Artefakt sind keine Exzerptfelder. Das Repo speichert keine Rohtexte und ordnet nicht nach Prüfungsnutzen.

## Pilotstatus

`data/excerpts/pilot-v1.jsonl` enthält zwei erste `draft`-Exzerpte:

- Lernfeld 2 / `doc-008`: Eingewöhnung, Bindung und Übergang.
- Lernfeld 4 / `doc-021`: Lernarrangements, Interessen- und Ressourcenorientierung.

Beide Einträge sind paraphrasiert, kurz gehalten und mit konkreter Fundstelle versehen. Sie sind Einstiegsknoten, keine vollständige Inhaltserschließung.

## Resonanz- und Kontrastprüfung

Deutung A: Exzerpte sind kleine Inhaltsbausteine. Dann könnte man schnell viel Text sammeln.

Deutung B: Exzerpte sind Belegknoten. Dann muss jeder starke Claim Fundstelle, Reifegrad und Unsicherheit tragen. Dieses Modell folgt Deutung B.

## Epistemische Leere

Die Pilotexzerpte beweisen den Pfad, aber sie ersetzen noch keine systematische Tiefenerschließung. Nötig für Detailkarten: mehr geprüfte Exzerpte je Lernfeld und klare Entscheidung, wann ein Entwurf zu `checked` hochgestuft werden darf.
