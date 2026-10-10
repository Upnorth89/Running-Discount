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
    """Stores only in `base` stay as they were. For a store in `new` (Oct 10: GPT often re-reads only a store's sale pages):
    an item in `new` replaces all of its old rows; an old item `new` doesn't have is kept only where it was at full price
    (a sale it didn't re-confirm may have ended: never show a stale sale price)."""
    b, n = (openpyxl.load_workbook(p, read_only=True, data_only=True) for p in (base, new))
    h1, s1 = sheet(b, "Sizes & availability")
    h2, s2 = sheet(n, "Sizes & availability")
    if h1 != h2:
        raise SystemExit("FAIL: the two files have different columns in Sizes & availability")
    ri, ii, cp, rp = (h1.index(c) for c in ("Retailer", "Item ID", "Current price", "Regular price"))
    fresh = {r[ri] for r in s2}
    seen = {(r[ri], r[ii]) for r in s2}

    def full_price(r):
        try:
            return float(r[cp]) >= float(r[rp]) * 0.99
        except (TypeError, ValueError):
            return False
    sizes = [r for r in s1 if r[ri] not in fresh or ((r[ri], r[ii]) not in seen and full_price(r))] + s2
    keep = {(r[ri], r[ii]) for r in sizes}
    wb = openpyxl.Workbook(write_only=True)
    hp, p1 = sheet(b, "Products")
    hq, p2 = sheet(n, "Products")
    if hp != hq:
        raise SystemExit("FAIL: the two files have different columns in Products")
    pi, pk = hp.index("Retailer"), hp.index("Item ID")
    for name, head, rows in (("Products", hp, [r for r in p1 if (r[pi], r[pk]) in keep and (r[pi], r[pk]) not in seen] + p2),
                             ("Sizes & availability", h1, sizes)):
        ws = wb.create_sheet(name)
        ws.append(head)
        for r in rows:
            ws.append(list(r))
    wb.save(out)


def without(ship, new, urls):
    """The shipped file minus the rows whose link is in `urls` (written to saved-pages/)."""
    out = ship
    if ship == new or ship.parent != SAVED:
        today = datetime.now(ZoneInfo("America/Vancouver")).strftime("%Y-%m-%d")
        n = 0
        while (SAVED / f"catalog-{today}{chr(97 + n) if n else ''}.xlsx").exists():
            n += 1
        out = SAVED / f"catalog-{today}{chr(97 + n) if n else ''}.xlsx"
    b = openpyxl.load_workbook(ship, read_only=True, data_only=True)
    wb = openpyxl.Workbook(write_only=True)
    for name in ("Products", "Sizes & availability"):     # sizes only: a product row with no sizes left shows nothing
        h, rows = sheet(b, name)
        ws = wb.create_sheet(name)
        ws.append(h)
        for r in rows:
            if name == "Products" or r[h.index("Variant URL")] not in urls:
                ws.append(list(r))
    wb.save(out)
    print(f"  note {len(urls)} item link(s) taken out of {out.name}")
    return out


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

    # 3b. empty sizes (Oct 10: 327 Running Warehouse rows had no Size; a shoe then matched every visitor). They're skipped now;
    # listed here so GPT can be asked to fill them
    nosize = collections.Counter(r["Retailer"] for r in rows if r.get("Online availability") == "In stock" and not r.get("Size"))
    print("  " + ("note " if nosize else "ok   ") + "Sizes: " + (", ".join(f"{s} {n} in-stock rows" for s, n in nosize.items())
                                                       + " have no size (left out; ask GPT to fill Size)" if nosize else "every in-stock row has a size"))

    # 3c. where each link lands (Oct 10, Bastien: "every link brings to actual size and item linked"): with the store's size code
    # added (sc.catalog_link), a link must at least open on the item's colour; one link shared by several colours opens on
    # whichever colour the store shows first, maybe one without the size = FAIL until that store gets a link rule
    lands = collections.defaultdict(lambda: (collections.defaultdict(set), collections.defaultdict(set)))
    for r in rows:
        if r.get("Online availability") != "In stock" or not r.get("Size"):
            continue
        u = str(r.get("Variant URL") or "")
        u = sc.catalog_link(u, r.get("SKU")) or u
        by_link, by_col = lands[r["Retailer"]]
        by_link[u].add(str(r.get("Colour") or "").lower())
        by_col[(r.get("Item ID"), str(r.get("Colour") or "").lower())].add(u)
    for s_, (by_link, by_col) in sorted(lands.items()):
        shared = sum(len(c) > 1 for c in by_link.values()) / max(1, len(by_link))
        per_size = sum(len(v) > 1 for v in by_col.values()) / max(1, len(by_col))
        if shared > 0.05:
            say(False, f"Links, {s_}: {shared:.0%} of links are shared by several colours (opens on the wrong colour): needs a link rule")
        else:
            print(f"  ok   Links, {s_}: " + ("open on the colour and size" if per_size > 0.5 else
                                          "open on the colour (size picked on the store's page)"))

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
    blocked, bad, wrong = [], [], collections.defaultdict(list)

    def check(r):
        """'ok', 'bad' (price not on the page), 'gone' (404) or 'blocked' (can't tell)."""
        url, price = r["Variant URL"], float(r["Current price"])
        try:
            resp = requests.get(url, timeout=30, headers={"User-Agent": livecheck.S.headers["User-Agent"]})
            code = resp.status_code
        except requests.RequestException:
            code = 0
        time.sleep(1)
        if code in (202, 403, 406, 429) or code == 0 or (code == 200 and len(resp.text) < 2000):
            return "blocked"
        if code in (404, 410):
            return "gone"
        res = livecheck.still_on_sale(url, price) if code == 200 else None
        page = re.sub(r"<[^>]+>", " ", resp.text)
        if res is None or (res is False and not re.search(r"\$\s?\d+(?:\.\d\d)?", page)):
            return "blocked"              # turned away (406), or no price in the page (filled in by a script): tap-check
        if res is False:                  # Zappos moves prices by cents during the day: within 2% is the same deal
            near = [float(x) for x in re.findall(r"\$\s?(\d+\.\d\d)", page)]
            if any(abs(x - price) <= price * 0.02 for x in near):
                notes.append(f"{r['Retailer']}: ${price:.2f} is now ${min(near, key=lambda x: abs(x - price)):.2f} on the page")
                return "ok"
        return "ok" if res else "bad"

    for s, rs in sorted(by.items()):
        ok = tried = 0
        for r in random.sample(rs, min(4, len(rs))):
            got_ = check(r)
            if got_ == "blocked":
                blocked.append(s)
                break
            tried += 1
            ok += got_ == "ok"
            if got_ != "ok":
                wrong[s].append((r, got_))
        if tried:
            print(f"  {'ok  ' if ok == tried else 'note'} Live links, {s}: {ok} of {tried} pages show the file's sale price")
    # one wrong price (Oct 10: a Zappos SuperComp Elite colour went from $198.71 to $252.35 after GPT's read): 10 more of that
    # store; 9+ right = it's that item, which is taken out of the file; fewer = the store's data is off, don't ship
    drop = set()
    for s, rs in wrong.items():
        more = [r for r in random.sample(by[s], min(14, len(by[s]))) if r not in [x for x, _ in rs]][:10]
        res = [check(r) for r in more]
        seen_ = [x for x in res if x != "blocked"]
        good = sum(x == "ok" for x in seen_)
        what = "; ".join(f"${float(r['Current price']):.2f} {'page gone' if why == 'gone' else 'not on the page'} "
                         f"({r['Variant URL']})" for r, why in rs)
        if len(seen_) >= 8 and good >= len(seen_) - 1:
            drop |= {r["Variant URL"] for r, _ in rs}
            print(f"  note Live links, {s}: {what}; {good} of {len(seen_)} more pages match, so that item is taken out of the file")
        else:
            bad.append(f"{s}: {what}; only {good} of {len(seen_)} more pages match")
    if blocked:
        print(f"  note Live links: {', '.join(sorted(set(blocked)))}: blocks robots or shows prices only with a script, tap-check below")
    for n_ in notes:
        print("  note Live links, price moved a little: " + n_)
    say(not bad, "Live links: " + ("all opened pages match" if not bad else "; ".join(bad[:6])))
    if drop and not bad:
        ship = without(ship, new, drop)
        by = {s: [r for r in rs if r["Variant URL"] not in drop] for s, rs in by.items()}

    # 6. five deals to tap
    print("\nTap to check (price and size we'll show):")
    pool = [r for s in by for r in random.sample(by[s], min(2, len(by[s])))]
    for r in random.sample(pool, min(5, len(pool))):
        print(f"  {r['Retailer']}: {r['Item']}, size {r['Size']}, ${float(r['Current price']):.2f} {r.get('Currency') or ''} "
              f"(was ${float(r['Regular price']):.2f})\n    {sc.catalog_link(str(r['Variant URL']), r.get('SKU')) or r['Variant URL']}")
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
