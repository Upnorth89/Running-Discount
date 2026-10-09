#!/usr/bin/env python3
"""Test a GPT catalog file before it ships (Oct 9, 2026; Bastien: "Always test this before shipping it").

  python tools/catalog_test.py NEW.xlsx            test it; a file holding only some stores (a Backcountry batch) is merged
                                                   into the newest full file in saved-pages/ first -> saved-pages/catalog-<date><x>.xlsx
Steps (any FAIL = don't ship):
  1. File scan (catalog_validate): columns, 500+ sizes in stock, links, photos, prices.
  2. Store counts vs the current file: a store missing or halved is flagged.
  3. Gender: the name says Men's/Women's but the Gender column says the other (the name wins on the site; listed here).
  4. Sorting check (scraper/sortcheck.py) on today's live data merged with this file, for every store in the file.
  5. Live links: 4 random sale sizes per store opened on the store's own page (one page a second): the page loads and shows
     that price. Stores that block robots (403/429/202) are listed as "tap to check" instead (we never get around a block).
  6. Five random deals for Bastien to tap on his phone, with the price and size we'll show.
Writes the report to stdout; exit code 1 when a step fails.
"""
import collections
import json
import random
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
import scrape as sc          # noqa: E402
import livecheck             # noqa: E402

SAVED = ROOT / "saved-pages"
fails, notes = [], []


def say(ok, line):
    print(("  ok   " if ok else "  FAIL ") + line)
    if not ok:
        fails.append(line)


def sheet(wb, name):
    it = wb[name].iter_rows(values_only=True)
    head = next(r for r in it if r and r[0] == "Retailer")
    return list(head), [r for r in it if r and r[0]]


def stores_of(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    h, rows = sheet(wb, "Sizes & availability")
    i, a = h.index("Retailer"), h.index("Online availability")
    c = collections.Counter(r[i] for r in rows if r[a] == "In stock")
    return c


def merge(base, new, out):
    """Rows of `new` replace the same product/colour/size in `base`; everything else in `base` stays."""
    b, n = (openpyxl.load_workbook(p, read_only=True, data_only=True) for p in (base, new))
    wb = openpyxl.Workbook(write_only=True)
    for name, key in (("Products", ("Retailer", "Item ID")), ("Sizes & availability", ("Retailer", "Item ID", "Colour", "Size", "Width / fit"))):
        h1, r1 = sheet(b, name)
        h2, r2 = sheet(n, name)
        if h1 != h2:
            raise SystemExit(f"FAIL: the two files have different columns in {name}")
        idx = [h1.index(k) for k in key]
        newk = {tuple(r[i] for i in idx) for r in r2}
        ws = wb.create_sheet(name)
        ws.append(h1)
        for r in [r for r in r1 if tuple(r[i] for i in idx) not in newk] + r2:
            ws.append(list(r))
    wb.save(out)


def load(path, tmp):
    """The scraper's own reading of one file (the same code the site uses)."""
    d = Path(tempfile.mkdtemp(dir=tmp))
    (d / path.name).write_bytes(path.read_bytes())
    sc.SAVED_DIR, sc.OUT = d, d / "deals.json"
    sc._catalog_cache.clear()
    rows = sc._catalog_rows()
    rep = json.loads((d / "catalog-check.json").read_text())
    return rows, rep


def main(new):
    new = Path(new).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="cattest-"))
    cur = sorted(SAVED.glob("catalog-*.xlsx"), key=lambda f: f.stat().st_mtime)
    cur = cur[-1] if cur else None
    print(f"Testing {new.name}" + (f" (current file: {cur.name})" if cur else ""))

    # 0. a batch with only some stores is merged into the current full file
    got, before = stores_of(new), stores_of(cur) if cur else collections.Counter()
    ship = new
    missing = [s for s in before if s not in got]
    if cur and missing:
        today = datetime.now(ZoneInfo("America/Vancouver")).strftime("%Y-%m-%d")
        n = 0
        while (SAVED / f"catalog-{today}{chr(97 + n) if n else ''}.xlsx").exists():
            n += 1
        ship = SAVED / f"catalog-{today}{chr(97 + n) if n else ''}.xlsx"
        merge(cur, new, ship)
        print(f"  note this file holds only {', '.join(got)}: merged into {cur.name} -> {ship.name} "
              f"(keeps {', '.join(missing)})")

    # 1. file scan
    rows, rep = load(ship, tmp)
    chk = rep["checked"][0] if rep.get("checked") else {"problems": ["can't read it"]}
    say(not chk["problems"], "File scan: " + ("; ".join(chk["problems"]) or "columns, sizes, links, photos and prices fine"))
    for w in rep.get("warnings") or []:
        print("  warn " + w)
    if chk["problems"]:
        return finish(ship, new)
    stores = rep.get("stores") or {}

    # 2. store counts
    if cur and ship != cur:
        prev = load(cur, tmp)[1].get("stores") or {}
        for s, (n, _) in prev.items():
            if s not in stores:
                say(False, f"Store counts: {s} is gone ({n} products in the current file)")
            elif stores[s][0] < n / 2:
                say(False, f"Store counts: {s} fell from {n} to {stores[s][0]} products")
        sc._catalog_cache.clear()
        rows, rep = load(ship, tmp)
    say(True, "Store counts: " + ", ".join(f"{s} {n} ({k} on sale)" for s, (n, k) in sorted(stores.items())))

    # 3. gender column vs name
    wrong = collections.Counter()
    for r in rows:
        nm, g = str(r.get("Item") or ""), r.get("Gender")
        w, m = re.search(r"\bwom[ae]n[’']?s?\b", nm, re.I), re.search(r"(?<!wo)\bmen[’']?s?\b", nm, re.I)
        if (w and not m and g == "Men") or (m and not w and g == "Women"):
            wrong[r["Retailer"]] += 1
    print("  " + ("note " if wrong else "ok   ") + "Gender: " + (", ".join(f"{s} {n} rows" for s, n in wrong.items())
                                                           + " where the name and the Gender column disagree (the name wins)" if wrong else "names and Gender column agree"))

    # 4. sorting check on today's live data + this file
    rm = tmp / "rm"
    rm.mkdir()
    r = requests.get("https://thegearfox.com/offers.json", timeout=300)
    offers = r.json()
    offers["catalog"] = sc.scrape_catalog_others()
    for st, ret in (("sportchek", "Sport Chek"), ("adidasca", "Adidas"), ("rei", "REI")):
        got_ = sc.scrape_catalog(ret)
        if got_:
            for o in got_:
                if st == "rei":
                    o.update(ca=False, no_ca=True, us=True)
                else:
                    o.setdefault("ca", True)
                    o["no_us"] = True
            offers[st] = got_
    (rm / "offers.json").write_text(json.dumps(offers))
    p = subprocess.run([sys.executable, str(ROOT / "scraper" / "scrape.py"), str(rm / "deals.json"), "--remerge"],
                       capture_output=True, text=True)
    if p.returncode:
        say(False, "Merge with today's data failed: " + p.stderr[-300:])
        return finish(ship, new)
    doms = set()
    for o in offers["catalog"] + offers.get("sportchek", []) + offers.get("adidasca", []) + offers.get("rei", []):
        doms.add(re.sub(r"^https?://(www\.)?", "", o["u"]).split("/")[0])
    hits = []
    for dom in sorted(doms):
        out = subprocess.run([sys.executable, str(ROOT / "scraper" / "sortcheck.py"), str(rm / "deals.json"), dom],
                             capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.startswith("    "):
                hits.append(line.strip())
    say(not hits, f"Sorting check ({len(doms)} stores): " + ("clean" if not hits else f"{len(hits)} to fix: " + " | ".join(hits[:8])))

    # 5. live links: 4 random sale sizes per store
    random.seed(time.time())
    sale = [r for r in rows if r.get("Online availability") == "In stock" and r.get("Current price") and r.get("Regular price")
            and float(r["Current price"]) < float(r["Regular price"]) * 0.99 and r.get("Variant URL")]
    by = collections.defaultdict(list)
    for r in sale:
        by[r["Retailer"]].append(r)
    blocked, bad = [], []
    for s, rs in sorted(by.items()):
        ok = tried = 0
        for r in random.sample(rs, min(4, len(rs))):
            url, price = r["Variant URL"], float(r["Current price"])
            try:
                resp = requests.get(url, timeout=30, headers={"User-Agent": livecheck.S.headers["User-Agent"]})
                code = resp.status_code
            except requests.RequestException:
                code = 0
            time.sleep(1)
            if code in (202, 403, 406, 429) or code == 0 or (code == 200 and len(resp.text) < 2000):
                blocked.append(s)
                break
            tried += 1
            if code in (404, 410):
                bad.append(f"{s}: page gone ({url})")
                continue
            res = livecheck.still_on_sale(url, price) if code == 200 else None
            if res is False and not re.search(r"\$\s?\d+(?:\.\d\d)?", re.sub(r"<[^>]+>", "", resp.text)):
                tried -= 1                 # no price in the page at all (Zappos fills it in with a script): can't tell, tap-check
                blocked.append(s)
                continue
            if res is True:
                ok += 1
            elif res is False:
                bad.append(f"{s}: ${price:.2f} not on the page ({url})")
        if tried:
            print(f"  {'ok  ' if ok == tried else 'note'} Live links, {s}: {ok} of {tried} pages show the file's sale price")
    if blocked:
        print(f"  note Live links: {', '.join(sorted(set(blocked)))}: blocks robots or shows prices only with a script, tap-check below")
    say(not bad, "Live links: " + ("all opened pages match" if not bad else "; ".join(bad[:6])))

    # 6. five deals to tap
    print("\nTap to check (price and size we'll show):")
    pool = [r for s in by for r in random.sample(by[s], min(2, len(by[s])))]
    for r in random.sample(pool, min(5, len(pool))):
        print(f"  {r['Retailer']}: {r['Item']}, size {r['Size']}, ${float(r['Current price']):.2f} {r.get('Currency') or ''} "
              f"(was ${float(r['Regular price']):.2f})\n    {r['Variant URL']}")
    return finish(ship, new)


def finish(ship, new):
    print()
    if fails:
        print(f"NOT READY: {len(fails)} problem(s). Don't ship {ship.name}.")
        if ship != new and ship.parent == SAVED:
            ship.unlink(missing_ok=True)
        return 1
    print(f"READY: {ship.name} passed. Ship it (python tools/check.py, then push).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
