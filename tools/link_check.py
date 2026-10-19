"""Nightly sale-link check (Oct 19, 2026; Bastien found a 2XU deal whose page said "not found": the store removed that colour
after our morning read, and the site test only opens 2 links per store).

Every store link that carries a sale price on today's site (sale.json + sale-us.json) is opened once, politely: an honest
bot name, one page per second per store, all stores side by side. A page that answers 404/410 twice is written to
deadlinks.json; the morning refresh (scrape.py DEADLINKS_FILE) leaves those offers out and the health email counts them.
403/429/timeouts are "couldn't check" (the store said no or was busy), never dead. Stores that block robots are skipped.

    python tools/link_check.py OUT.json [site_base]
"""
import concurrent.futures as cf
import collections
import datetime as dt
import json
import sys
import time
import random
import re
import urllib.parse
import urllib.robotparser

import requests

BASE = (sys.argv[2] if len(sys.argv) > 2 else "https://thegearfox.com").rstrip("/")
OUT = sys.argv[1] if len(sys.argv) > 1 else "deadlinks.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; TheGearFox/1.0; +https://thegearfox.com/about.html)"}
SKIP = {"mec.ca", "rei.com", "decathlon.ca", "sportinglife.ca", "sportchek.ca", "sportsexperts.ca", "backcountry.com",
        "roka.com"}   # they block robots or are read from saved pages: their links can't be checked this way


def host(u):
    h = urllib.parse.urlsplit(u).hostname or ""
    return h[4:] if h.startswith("www.") else h


def sale_links():
    out = set()
    for f in ("sale.json", "sale-us.json"):
        try:
            d = requests.get(f"{BASE}/{f}", headers=UA, timeout=60).json()
        except Exception as e:
            print(f"  {f}: {e}", file=sys.stderr)
            continue
        for it in d.get("items", []):
            of = it.get("of") or []
            for e in it.get("sz", []):
                if len(e) > 3 and e[3] and e[1] < e[3] * 0.99 and e[2] < len(of):
                    out.add(of[e[2]])
    return out


def robots(h):
    """The store's robots.txt: what we may open and how long to wait between pages (Running Free asks 30 s)."""
    rp = urllib.robotparser.RobotFileParser()
    try:
        r = requests.get(f"https://{h}/robots.txt", headers=UA, timeout=20)
        rp.parse(r.text.splitlines() if r.status_code == 200 else [])
    except Exception:
        rp.parse([])
        r = None
    # read any "Crawl-delay" line, even one after a blank line (Running Free's sits alone and Python's parser drops it)
    found = [float(x) for x in re.findall(r"(?im)^\s*crawl-delay\s*:\s*([\d.]+)", r.text if r is not None and r.status_code == 200 else "")]
    return rp, max([1.0] + found)


def check_host(h, urls):
    s = requests.Session()
    s.headers.update(UA)
    rp, wait = robots(h)
    urls = [u for u in sorted(urls) if rp.can_fetch(UA["User-Agent"], u)]
    if wait > 1.5:                                  # slow-rule stores: what fits in an hour, a different sample each night
        urls = random.sample(urls, min(len(urls), int(3600 / wait)))
    dead, unsure, ok = [], 0, 0
    for u in urls:
        code = None
        for attempt in range(2):            # a 404 counts only when it says so twice
            try:
                code = s.get(u, timeout=20, allow_redirects=True).status_code
            except Exception:
                code = None
            time.sleep(wait)
            if code not in (404, 410):
                break
        if code in (404, 410):
            dead.append(u)
        elif code in (403, 429):
            unsure += 1
            if unsure >= 5 and not ok:      # the store says no: stop asking
                break
        elif code and code < 400:
            ok += 1
        else:
            unsure += 1
    return h, dead, ok, unsure


def main():
    links = sale_links()
    by = collections.defaultdict(set)
    for u in links:
        if host(u) not in SKIP:
            by[urllib.parse.urlsplit(u).netloc].add(u)     # the exact address, so robots.txt comes from the same host
    print(f"{len(links)} sale links, {sum(len(v) for v in by.values())} to check at {len(by)} stores", file=sys.stderr)
    dead, stats = {}, {}
    with cf.ThreadPoolExecutor(16) as ex:
        for h, d, ok, unsure in ex.map(lambda kv: check_host(*kv), by.items()):
            stats[h] = {"ok": ok, "dead": len(d), "unsure": unsure}
            for u in d:
                dead[u] = h
            if d:
                print(f"  {h}: {len(d)} dead of {len(by[h])}", file=sys.stderr)
    json.dump({"checked": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "dead": dead, "stores": stats},
              open(OUT, "w"), indent=0)
    print(f"{len(dead)} dead links -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
