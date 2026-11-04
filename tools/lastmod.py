#!/usr/bin/env python3
"""Sitemap <lastmod> = the day each page's visible text last changed (Nov 4, growth's SEO audit: every URL said "today" every
day, which tells Google nothing; 5 entries had none). Runs after every page builder, before the site test.

Each sitemap page is read from the BUILT site folder, fingerprinted the way tools/indexnow.py does it (visible text minus date
stamps and countdowns), and compared with the last run's fingerprints (STATE, kept by the workflow's cache "lastmod-*"):
changed or new = today; unchanged = the day it last changed. No state yet (first run, cache lost) = today for every page, once.

  python tools/lastmod.py SITE_DIR [STATE.json]
"""
import hashlib
import json
import re
import sys
from datetime import datetime
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
MOIS = r"(?:janv|févr|fevr|mars|avr|mai|juin|juil|août|aout|sept|oct|nov|déc|dec)[a-zéû]*\.?"
STAMPS = [re.compile(p, re.I) for p in (
    rf"\b{MON} \d{{1,2}}(?:, \d{{4}})?",            # Oct 23 / October 23, 2026 / Oct. 22
    rf"\b\d{{1,2}}(?:er)? {MOIS}(?: \d{{4}})?",      # 23 oct. / 1er novembre 2026
    r"\b\d{4}-\d{2}-\d{2}(?:T[\d:.+Z-]+)?",           # 2026-10-23
    r"\b\d+ days? to go|\bencore \d+ jours?",          # Black Friday / Boxing Day countdowns
    r"\b\d+ (?:h|hours?|heures?|min) ago|il y a \d+ ?(?:h|min)",
)]


def fingerprint(html):
    t = re.sub(r"(?is)<(script|style|noscript|template)\b.*?</\1>", " ", html)   # scripts carry dateModified etc.
    t = unescape(re.sub(r"<[^>]+>", " ", t))
    for p in STAMPS:
        t = p.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def main():
    site = Path(sys.argv[1])
    state_p = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/lastmod-state.json")
    sm = site / "sitemap.xml"
    if not sm.exists():
        print("lastmod: no sitemap.xml")
        return
    try:
        state = json.loads(state_p.read_text())
    except Exception:
        state = {}
    today = datetime.now(ZoneInfo("America/Vancouver")).date().isoformat()
    xml = sm.read_text()
    changed = same = 0

    def one(m):
        nonlocal changed, same
        loc = m.group(1)
        path = re.sub(r"^https?://[^/]+", "", loc)
        f = site / path.lstrip("/")
        f = f / "index.html" if path.endswith("/") else f
        try:
            fp = fingerprint(f.read_text(errors="ignore"))
        except Exception:
            fp = ""
        old = state.get(loc) or {}
        if fp and old.get("fp") == fp and old.get("day"):
            day = old["day"]
            same += 1
        else:
            day = today
            changed += 1
        if fp:
            state[loc] = {"fp": fp, "day": day}
        return f"<url><loc>{loc}</loc><lastmod>{day}</lastmod></url>"

    xml = re.sub(r"<url>\s*<loc>([^<]+)</loc>(?:\s*<lastmod>[^<]*</lastmod>)?\s*</url>", one, xml)
    sm.write_text(xml)
    state_p.write_text(json.dumps(state, separators=(",", ":")))
    print(f"lastmod: {changed} pages changed or new today, {same} unchanged (kept their day)")


if __name__ == "__main__":
    main()
