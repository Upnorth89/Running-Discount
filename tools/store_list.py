#!/usr/bin/env python3
"""Rewrite the "All stores we cover" table in STORES.md from the live site's data (Oct 9, 2026; Bastien: "Update the list
with all the stores we cover").

Every store with at least one product on the site today, per side (Canada / USA), how we read it, products and on sale.
Counts come from the live deals(-us).json / sale(-us).json; names from the STORES map in site/index.html.

  python tools/store_list.py            # fetch https://thegearfox.com/ and rewrite the table between the markers
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
import runfree as RF  # noqa: E402

SITE = (sys.argv[1] if len(sys.argv) > 1 else "https://thegearfox.com/").rstrip("/") + "/"
START, END = "<!--STORE-LIST-->", "<!--/STORE-LIST-->"


def get(name):
    r = requests.get(SITE + name, timeout=120)
    r.raise_for_status()
    return r.json()


def host(u):
    h = urlparse(u).netloc.lower()
    return h[4:] if h.startswith("www.") else h


html = (ROOT / "site" / "index.html").read_text()
NAMES = {k: v[0] for k, v in json.loads(re.search(r"const STORES=(\{.*?\});", html, re.S).group(1)).items()}


def name_of(h):
    parts = h.split(".")
    for i in range(len(parts) - 1):
        if ".".join(parts[i:]) in NAMES:
            return NAMES[".".join(parts[i:])]
    return h


# how each store is read, from the offers' store keys
src = (ROOT / "scraper" / "scrape.py").read_text()
shopify = set(re.findall(r'^\s+\("([a-z0-9]+)",\s*"https?://', src[src.index("SHOPIFY_STORES = ["):], re.M))
runfree = {st for st, *_ in RF.RUNFREE_STORES}
METHOD = {"mec": "saved pages (Grab deals)", "rei": "GPT file / saved pages", "sportchek": "GPT file", "adidasca": "GPT file",
          "decathlon": "slow night read", "thefeed": "night read"}
how = {}
for st, offers in get("offers.json").items():
    for o in offers if isinstance(offers, list) else []:
        h = host(o.get("u") or "")
        if not h or h in how:
            continue
        s = o.get("st") or st
        how[h] = ("GPT file" if str(s).startswith("cat-") else METHOD.get(st) or
                  ("Shopify" if st in shopify else "RunFree (night read)" if st in runfree else "own reader"))

rows = defaultdict(lambda: {"ca": [0, 0], "us": [0, 0]})
for side, deals, sale in (("ca", "deals.json", "sale.json"), ("us", "deals-us.json", "sale-us.json")):
    for i, f in enumerate((deals, sale)):
        for it in get(f)["items"]:
            for h in {host(u) for u in it["of"]}:
                rows[h][side][i] += 1

ca = sorted((h for h in rows if rows[h]["ca"][0]), key=lambda h: name_of(h).lower())
us = sorted((h for h in rows if rows[h]["us"][0] and not rows[h]["ca"][0]), key=lambda h: name_of(h).lower())
both = [h for h in ca if rows[h]["us"][0]]


def table(hs, side):
    out = ["| Store | Website | How we read it | Products | On sale |", "|---|---|---|---:|---:|"]
    for h in hs:
        n, s = rows[h][side]
        out.append(f"| {name_of(h)} | {h} | {how.get(h, 'own reader')} | {n:,} | {s:,} |")
    return "\n".join(out)


now = datetime.now(ZoneInfo("America/Vancouver"))
body = f"""{START}
## All stores we cover ({len(ca) + len(us)} stores; live site, {now:%b} {now.day}, {now:%Y})

Made by `python tools/store_list.py` from the live site: every store with at least one product on the site that day.
Products = items on the site with that store; On sale = those on sale. A store missing here had nothing on the site that
day (e.g. no catalog file). Stores on both sides: {", ".join(name_of(h) for h in both) or "none"} (USA counts not shown).

### Canada side ({len(ca)})
{table(ca, "ca")}

### USA side only ({len(us)})
{table(us, "us")}
{END}"""

p = ROOT / "STORES.md"
s = p.read_text()
if START in s:
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: body, s, flags=re.S)
else:
    i = s.index("## Master list")
    s = s[:i] + body + "\n\n" + s[i:]
p.write_text(s)
print(f"STORES.md: {len(ca)} Canada side, {len(us)} USA only")
