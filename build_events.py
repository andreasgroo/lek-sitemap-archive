#!/usr/bin/env python3
"""Baut aus allen Snapshots in ./snapshots eine events.csv im Repo-Root.

Eine Zeile = ein Publikations-Event, also die Kombination aus Node-ID und
publication_date. Ändert sich das publication_date eines Artikels (Republishing),
entsteht eine zweite Zeile mit repub_no = 2 — genau das ist die Frage, die man
hinterher an die Daten stellt. Die URL identifiziert den Artikel NICHT, weil sie
sich beim Republishing ändern kann; die Node-ID am URL-Ende tut es.

Läuft in GitHub Actions nach jedem Fetch, funktioniert aber auch lokal:
    python3 build_events.py
"""

import csv
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(ROOT, "snapshots")
OUT = os.path.join(ROOT, "events.csv")
NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
}
# news-sitemap-2026-07-22.xml oder news-sitemap-2026-07-22-0930.xml
SNAP_RE = re.compile(r"news-sitemap-(\d{4}-\d{2}-\d{2})(?:-(\d{4}))?\.xml$")


def node_of(url):
    """Node-ID = letztes Pfadsegment, sofern rein numerisch."""
    seg = url.rstrip("/").rsplit("/", 1)[-1]
    return seg if seg.isdigit() else ""


def parse(path):
    """Liefert [(url, node, pubdate, title), ...] aus einem Snapshot."""
    out = []
    root = ET.parse(path).getroot()
    for u in root.findall("sm:url", NS):
        loc = u.findtext("sm:loc", "", NS).strip()
        n = u.find("news:news", NS)
        if not loc or n is None:
            continue
        out.append((
            loc,
            node_of(loc),
            n.findtext("news:publication_date", "", NS).strip(),
            (n.findtext("news:title", "", NS) or "").strip(),
        ))
    return out


def snapshots():
    """[(sortierschluessel, tag, pfad), ...] chronologisch."""
    found = []
    if not os.path.isdir(SNAP_DIR):
        return found
    for f in os.listdir(SNAP_DIR):
        m = SNAP_RE.search(f)
        if m:
            day, hhmm = m.group(1), m.group(2) or "0000"
            found.append((f"{day}-{hhmm}", day, os.path.join(SNAP_DIR, f)))
    return sorted(found)


def main():
    snaps = snapshots()
    if not snaps:
        print("Keine Snapshots gefunden — noch nichts zu bauen.")
        return 0

    events = {}  # (node_or_url, pubdate) -> dict
    for _, day, path in snaps:
        try:
            rows = parse(path)
        except ET.ParseError as e:
            print(f"  WARNUNG: {os.path.basename(path)} nicht lesbar ({e})")
            continue
        for url, node, pub, title in rows:
            key = (node or url, pub)
            e = events.get(key)
            if e is None:
                events[key] = {
                    "node_id": node,
                    "publication_date": pub,
                    "url": url,
                    "title": title,
                    "first_seen": day,
                    "last_seen": day,
                    "_days": {day},
                }
            else:
                e["last_seen"] = day
                e["_days"].add(day)
                e["url"] = url      # jüngste beobachtete URL-Variante
                e["title"] = title  # jüngster beobachteter Card-Titel

    # repub_no: wievieltes Publikationsdatum ist das für diesen Artikel?
    by_node = {}
    for e in events.values():
        by_node.setdefault(e["node_id"] or e["url"], []).append(e)
    for group in by_node.values():
        for i, e in enumerate(sorted(group, key=lambda x: x["publication_date"]), 1):
            e["repub_no"] = i

    for e in events.values():
        e["seen_days"] = len(e.pop("_days"))

    rows = sorted(events.values(), key=lambda e: (e["publication_date"], e["node_id"]))
    cols = ["node_id", "publication_date", "url", "title",
            "first_seen", "last_seen", "seen_days", "repub_no"]
    tmp = OUT + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, OUT)

    repubs = sum(1 for e in rows if e["repub_no"] > 1)
    print(f"  {len(rows)} Events aus {len(snaps)} Snapshots "
          f"({snaps[0][1]} bis {snaps[-1][1]}), "
          f"{len(by_node)} Artikel, davon {repubs} Republish-Events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
