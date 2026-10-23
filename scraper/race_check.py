#!/usr/bin/env python3
"""Race gear list check (Oct 22, 2026; Bastien OK'd "a monthly automatic check that rereads each race's gear page and emails if it changed").

Once a month (race-check.yml), from GitHub's servers, one polite visit to each race's own gear page or PDF (`src` / `src_fr` in
scraper/race_pages.py RACES). Keeps only the lines that talk about gear (mandatory, recommended, jacket, headlamp…) plus the
files the page links (a new PDF or picture of the list = a new version), and compares them with last month's
(race-check.json on the history branch). Emails Bastien (HEALTH_EMAIL) ONLY when a list changed or a page stopped answering,
with the lines that appeared or went away, so Claude can update that race. The first run just saves the starting point.

  python scraper/race_check.py STATE.json      (needs RESEND_API_KEY + HEALTH_EMAIL to email; prints either way)
"""
import datetime as dt
import io
import json
import os
import re
import sys
import time
from html import unescape
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from race_pages import RACES  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (compatible; TheGearFoxBot/1.0; +https://thegearfox.com/about.html)",
      "Accept-Language": "en-CA,en;q=0.8,fr-CA;q=0.6"}
GEAR = re.compile(r"mandatory|obligatoire|required|requis|recommend|recommand|suggest|equipment|équipement|gear\b|matériel|"
                  r"jacket|manteau|veste|headlamp|frontale|lamp|gloves?\b|gants|tuque|toque|beanie|\bhat\b|chapeau|cap\b|casquette|"
                  r"cup\b|gobelet|blanket|couverture|bivv?y|whistle|sifflet|water|eau\b|litre|liter|\bml\b|\bl\b|calorie|food|"
                  r"nourriture|pants|pantalon|tights|collant|layer|couche|poles?\b|bâtons|phone|téléphone|inreach|tracker|balise|"
                  r"battery|batterie|filter|filtre|bear|ours|orange|kit\b|weather|météo|cold|froid|heat|chaleur", re.I)
# a linked file counts when it is a PDF or a picture named like a gear list (Fat Dog's page rotates its photos: not a change)
FILE = re.compile(r"\.pdf$|gear|equip|kit|mandat|obligatoire|materiel|matériel|guide|list", re.I)


def page_lines(r):
    """The page as short lines of text, plus one "[file] …" line per PDF/picture it links."""
    if "pdf" in r.headers.get("content-type", "") or r.url.lower().split("?")[0].endswith(".pdf"):
        from pypdf import PdfReader
        text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(r.content)).pages)
        files = []
    else:
        h = r.text
        files = sorted({f"[file] {m.split('?')[0].rsplit('/', 1)[-1]}" for m in
                        re.findall(r"""(?:href|src)=["']([^"']+\.(?:pdf|png|jpe?g|webp)(?:\?[^"']*)?)["']""", h, re.I)})
        h = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", h)
        text = unescape(re.sub(r"(?s)<[^>]+>", "\n", h))
    out, seen = [], set()
    for ln in text.splitlines():
        ln = re.sub(r"\s+", " ", ln).strip(" -–•·*")
        if 3 <= len(ln) <= 300 and ln not in seen and GEAR.search(ln):
            seen.add(ln)
            out.append(ln)
    return out + [f for f in files if FILE.search(f)]


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "race-check.json")
    old = json.loads(path.read_text()) if path.exists() else {}
    new, changed, broken, first = {}, [], [], []
    today = dt.date.today().isoformat()
    for slug, race in RACES.items():
        if race.get("nocheck"):    # Oct 23: the race site answers robots with a challenge (TORX): checked by hand
            continue
        for url in dict.fromkeys(u for u in (race.get("check") or race.get("src"), race.get("src_fr")) if u):
            key = f"{slug} {url}"
            prev = old.get(key)
            try:
                r = requests.get(url, headers=UA, timeout=60)
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                lines = page_lines(r)
                if not lines:
                    raise RuntimeError("no gear text on the page (a page filled by script, or a different page now)")
            except Exception as e:   # keep last month's lines: the next run compares with the last good read
                broken.append(f"- {race['name']}: {url} ({e})")
                if prev:
                    new[key] = prev
                time.sleep(2)
                continue
            new[key] = {"lines": lines, "checked": today}
            if not prev:
                first.append(race["name"])
            elif prev["lines"] != lines:
                a, b = set(prev["lines"]), set(lines)
                gone, added = [x for x in prev["lines"] if x not in b], [x for x in lines if x not in a]
                if gone or added:
                    changed.append(f"{race['name']} ({url}), last read {prev.get('checked', '?')}:\n"
                                   + "".join(f"  + {x}\n" for x in added[:25]) + "".join(f"  - {x}\n" for x in gone[:25])
                                   + ("  (more lines changed)\n" if len(added) > 25 or len(gone) > 25 else ""))
            time.sleep(2)
    path.write_text(json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True))
    print(f"{len(new)} race pages read; {len(changed)} changed, {len(broken)} not answering, {len(first)} new (starting point saved)")
    for c in changed:
        print(c)
    for b in broken:
        print(b)
    if not changed and not broken:
        return   # nothing to say: no email
    subject = (f"Race gear lists: {len(changed)} changed" if changed else "Race gear lists: no change") + \
              (f", {len(broken)} page{'s' if len(broken) != 1 else ''} not answering" if broken else "")
    text = ("Once a month we reread every race's own gear list. Lines that appeared (+) or went away (-) since last month:\n\n"
            + ("\n".join(changed) if changed else "No list changed.\n")
            + ("\nNOT ANSWERING (the link may have moved; the race page keeps its last list):\n" + "\n".join(broken) + "\n" if broken else "")
            + "\nAsk Claude to update the race page (scraper/race_pages.py) from the race's own list.\n")
    key, to = os.environ.get("RESEND_API_KEY"), os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com"
    if key:
        r = requests.post("https://api.resend.com/emails", timeout=60, headers={"Authorization": f"Bearer {key}"},
                          json={"from": os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>"), "to": [to],
                                "subject": subject, "text": text})
        print(f"emailed: HTTP {r.status_code}")


if __name__ == "__main__":
    main()
