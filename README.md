# lek-sitemap-archive

Snapshots der News-Sitemap von leckerschmecker.me, zweimal täglich automatisch
via GitHub Actions (`.github/workflows/fetch.yml`, 5:00 und 15:00 UTC).
Läuft in der Cloud — unabhängig davon, ob ein Rechner an ist.

- `snapshots/` — die rohen XML-Dateien, Dateiname `news-sitemap-JJJJ-MM-TT-HHMM.xml`
  (Zeitstempel in Europe/Berlin).
- `events.csv` — wird nach jedem Fetch aus **allen** Snapshots neu gebaut.

## events.csv

Eine Zeile ist ein Publikations-Event, nicht eine URL. Leckerschmecker hängt die
Node-ID hinten an die URL (`.../buttertoast-cookies-cookie/63743511721431`) — die
identifiziert den Artikel, die URL tut es nicht, weil sie sich beim Republishing
ändern kann.

| Spalte | Bedeutung |
|---|---|
| `node_id` | Artikel-Identität (letztes URL-Segment, numerisch) |
| `publication_date` | `news:publication_date` aus der Sitemap |
| `url` | zuletzt beobachtete URL-Variante |
| `title` | zuletzt beobachteter `news:title` (Discover-Card-Titel) |
| `first_seen` / `last_seen` | erster/letzter Snapshot-Tag mit diesem Event |
| `seen_days` | an wie vielen Tagen das Event in der Sitemap stand |
| `repub_no` | 1 = erste beobachtete Veröffentlichung, 2+ = Republishing |

Ändert sich das `publication_date` einer Node, entsteht eine neue Zeile mit
höherem `repub_no`. So wird Republishing sichtbar, statt in URL-Varianten
unterzugehen.

**Wichtig zur Interpretation:** `repub_no = 1` heißt „erstes Publikationsdatum,
das dieses Archiv gesehen hat" — nicht zwingend die echte Erstveröffentlichung.
Artikel, die vor dem ersten Snapshot erschienen sind, können älter sein.

## Manuell auslösen

Actions-Tab → „Sitemap-Snapshot holen" → „Run workflow".

Hinweis: GitHub deaktiviert geplante Workflows in Repos ohne Commit-Aktivität
nach 60 Tagen. Da dieser Job selbst committet, bleibt er aktiv.
