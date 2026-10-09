#!/usr/bin/env python3
"""Featured deals, checked on the store's own page before the site goes live (Oct 8, 2026; Bastien: "I want the most
accurate information for our users. This is where the trust happens").

The deals most people see (the welcome screen's shoes, Top deals, the first rows of each category, the Friday email's
picks) all come from the best-scoring sale items. Each refresh, the top ones on each side are opened on the store's own
page (scraper/livecheck.py). A sale that ended or a size that sold out since the read is taken out of sale.json and
deals.json (and the -us twins), so it's never shown. A page that blocks robots counts as "couldn't check" and stays.

  python scraper/featured_check.py site [--top 60]      -> /tmp/featured.json (the health email reads it)
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import livecheck  # noqa: E402

SITE = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
TOP = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 60
OUT = Path(os.environ.get("FEATURED", "/tmp/featured.json"))
CORE = {"shoes": 15, "tops": 6, "bottoms": 6, "packs": 4}   # the same pull toward shoes and clothing as the site's ranking


def key(i):
    return f"{i['b']}|{i['n']}|{i['g']}|{1 if i.get('w') else 0}".lower()


def best_sale(i):
    s = [e for e in i.get("sz", []) if len(e) > 3 and e[1] < e[3] * 0.99]
    return min(s, key=lambda e: e[1]) if s else None


def score(i, e):
    pct = 100 * (1 - e[1] / e[3])
    return pct + min(e[3] - e[1], 200) / 10 + CORE.get(i["g"], 0)


def featured(items, n, canada):
    rows = []
    for i in items:
        if canada and i.get("ca") is False:
            continue
        e = best_sale(i)
        if e and 1 - e[1] / e[3] <= 0.85:
            rows.append((score(i, e), i, e))
    rows.sort(key=lambda r: -r[0])
    return rows[:n]


def drop(items, k, url, price):
    """Take the sizes at that store and price off this item; return how many."""
    n = 0
    for i in items:
        if key(i) != k:
            continue
        keep = []
        for e in i.get("sz", []):
            u = (i.get("of") or [""])[e[2]] if e[2] < len(i.get("of") or []) else ""
            if u.split("?")[0] == url.split("?")[0] and abs(e[1] - price) < 0.01:
                n += 1
            else:
                keep.append(e)
        i["sz"] = keep
    return n


def main():
    out = {"checked": 0, "ok": 0, "cant": 0, "removed": []}
    for side, sale_f, deals_f in (("Canada", "sale.json", "deals.json"), ("USA", "sale-us.json", "deals-us.json")):
        sp, dp = SITE / sale_f, SITE / deals_f
        if not sp.exists():
            continue
        sale, deals = json.loads(sp.read_text()), (json.loads(dp.read_text()) if dp.exists() else None)
        changed, usd = False, float((sale.get("fx") or {}).get("USD") or 1.38)
        for _, i, e in featured(sale["items"], TOP if side == "Canada" else TOP // 2, True):   # USA: US shops only (USD)
            url = i["of"][e[2]] if e[2] < len(i["of"]) else i["of"][0]
            us = side == "USA"           # the USA side keeps prices in CAD: back to the shop's own US dollars
            res = livecheck.still_on_sale(url, round(e[1] / usd, 2) if us else e[1], e[4] if len(e) > 4 else None, us=us)
            out["checked"] += 1
            if res is None:
                out["cant"] += 1
            elif res:
                out["ok"] += 1
            else:
                k = key(i)
                drop(sale["items"], k, url, e[1])
                if deals:
                    drop(deals["items"], k, url, e[1])
                changed = True
                out["removed"].append(f"{i['b']} {i['n']} at {url.split('/')[2].replace('www.', '')} (${e[1]:.2f}, {side})")
            time.sleep(0.5)
        if changed:
            sale["items"] = [i for i in sale["items"] if best_sale(i)]
            sp.write_text(json.dumps(sale, separators=(",", ":")))
            if deals:
                deals["items"] = [i for i in deals["items"] if i.get("sz")]
                dp.write_text(json.dumps(deals, separators=(",", ":")))
    OUT.write_text(json.dumps(out))
    print(f"featured deals: {out['checked']} checked on the store's page, {out['ok']} confirmed, {out['cant']} couldn't check, "
          f"{len(out['removed'])} ended and taken off" + "".join(f"\n  - {r}" for r in out["removed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
