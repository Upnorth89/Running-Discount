#!/usr/bin/env python3
"""Slow TEST read of a brand's own store (Nov 1, 2026; Bastien said yes via growth: Hoka + Salomon, both answered
store_recheck from GitHub on Nov 1). Nothing is published or saved for the site: this only answers "can we read it, and what's there".

Rules (CLAUDE.md "the line we never cross"): our own name (polite.py UA), robots.txt obeyed (polite.PoliteSession raises RobotsNo),
one site at a time, one page every 15-20 s, and the FIRST 403/406/429/challenge/202-empty page stops that site for good: we record
how many pages it reached and after how long. No retry, no workaround.

  python tools/brand_test.py OUT_DIR [hoka] [salomon]      (default: both, Hoka first)
Writes OUT_DIR/brand-test.json + OUT_DIR/summary.md (also appended to $GITHUB_STEP_SUMMARY)."""
import collections
import json
import os
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import polite  # noqa: E402

S = polite.PoliteSession()
HEAD = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-CA,en;q=0.9"}
PACE = (15, 20)
MAX_PAGES = int(os.environ.get("BT_MAX_PAGES", "450"))   # per site: ~2.5 h at 18 s; both sites end well before the 11:17 UTC read
MAX_MIN = float(os.environ.get("BT_MAX_MIN", "160"))


class No(Exception):
    """The store said no: stop this site."""


class Site:
    def __init__(self, key):
        self.key, self.pages, self.t0, self.last, self.stop = key, 0, time.time(), 0.0, None
        self.robots_no = 0

    def minutes(self):
        return round((time.time() - self.t0) / 60, 1)

    def room(self):
        return self.pages < MAX_PAGES and self.minutes() < MAX_MIN

    def get(self, url):
        wait = self.last + random.uniform(*PACE) - time.time()
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        try:
            r = S.get(url, headers=HEAD, timeout=60)
        except polite.RobotsNo:
            self.robots_no += 1
            return None
        except Exception as e:                       # network trouble is not a "no"; counted, not retried
            print(f"  {self.key}: {url[:110]} {type(e).__name__}", file=sys.stderr)
            return None
        self.pages += 1
        body = r.text or ""
        head = body[:4000]
        if (r.status_code in (403, 406, 429) or (r.status_code == 202 and len(body) < 2000)
                or re.search(r"Just a moment|Access Denied|cf-challenge|captcha", head, re.I)):
            self.stop = f"HTTP {r.status_code} on page {self.pages} after {self.minutes()} min: {url[:120]}"
            raise No(self.stop)
        if r.status_code != 200:
            print(f"  {self.key}: {url[:110]} HTTP {r.status_code}", file=sys.stderr)
            return None
        return body


def ld_blocks(h):
    for blk in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h or "", re.S):
        try:
            d = json.loads(blk, strict=False)
        except ValueError:
            continue
        stack = d if isinstance(d, list) else [d]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                yield x
                for k in ("@graph", "hasVariant", "itemListElement"):
                    stack += [y for y in (x.get(k) or []) if isinstance(y, dict)]


def offers_of(x):
    o = x.get("offers")
    if isinstance(o, dict) and o.get("@type") == "AggregateOffer":
        o = o.get("offers") or [o]
    return [y for y in (o if isinstance(o, list) else [o]) if isinstance(y, dict)]


def product(h, url):
    """One product page -> {name, price, currency, sizes, instock, colours} from its JSON-LD, or None."""
    prods = [x for x in ld_blocks(h) if x.get("@type") in ("Product", "ProductGroup")]
    if not prods:
        return None
    name = next((p.get("name") for p in prods if p.get("@type") == "ProductGroup"), None) or prods[0].get("name") or ""
    prices, cur, sizes, ok, colours = [], None, set(), set(), set()
    for p in prods:
        for o in offers_of(p):
            try:
                prices.append(float(o.get("price") or o.get("lowPrice") or 0))
            except (TypeError, ValueError):
                pass
            cur = cur or o.get("priceCurrency")
            sz = p.get("size")
            if sz:
                sizes.add(str(sz))
                if re.search(r"InStock|LimitedAvailability", str(o.get("availability") or "")):
                    ok.add(str(sz))
        if p.get("color"):
            colours.add(str(p["color"]))
    prices = [x for x in prices if x > 0]
    reg = re.search(r'(?:basePrice|listPrice|standardPrice|"list"[^}]{0,40}"value")\\?"?:\s*\\?"?([\d.]+)', h)
    return {"name": name, "url": url, "price": min(prices) if prices else None, "reg": float(reg.group(1)) if reg else None,
            "currency": cur, "sizes": len(sizes), "instock": len(ok), "colours": len(colours) or 1}


def sitemap_urls(site, root, want):
    """robots.txt Sitemap lines -> product page addresses matching `want` (sitemap indexes followed one level)."""
    rb = site.get(root + "/robots.txt") or ""
    maps = re.findall(r"(?im)^sitemap:\s*(\S+)", rb)
    urls = []
    for sm in maps[:6]:
        if not site.room():
            break
        x = site.get(sm) or ""
        subs = re.findall(r"<sitemap>\s*<loc>([^<]+)</loc>", x)
        for s in [u for u in subs if re.search(r"(?i)product", u) and re.search(r"(?i)en[_-]?ca|/ca/|canada", u)][:4] or subs[:0]:
            if site.room():
                x += site.get(s) or ""
        urls += [u for u in re.findall(r"<loc>([^<]+)</loc>", x) if want.search(u)]
    return list(dict.fromkeys(urls)), maps


def run_hoka(site):
    root = "https://www.hoka.com"
    home = site.get(root + "/en/ca/") or ""
    urls, maps = sitemap_urls(site, root, re.compile(r"/en/ca/.+/\d{6,}\.html|/en/ca/[^<]*\.html$"))
    side = "ca"
    if not urls:
        urls, _ = sitemap_urls(site, root, re.compile(r"/en/us/.+/\d{6,}\.html"))
        side = "us" if urls else "ca"
    return {"side": side, "home_kb": len(home) // 1024, "sitemaps": maps[:6], "listed": len(urls)}, urls


SAL_LISTS = [("men", "men/shoes/trail-running"), ("women", "women/shoes/trail-running"),
             ("men", "men/shoes/running"), ("women", "women/shoes/running")]


def run_salomon(site):
    root = "https://www.salomon.com"
    urls = []
    for _g, lst in SAL_LISTS:
        for n in range(1, 6):
            if not site.room():
                break
            h = site.get(f"{root}/en-ca/shop/{lst}.html" + (f"?page={n}" if n > 1 else "")) or ""
            new = [u for x in ld_blocks(h) if isinstance(x.get("url"), str) and "/product/" in x["url"]
                   for u in [x["url"] if x["url"].startswith("http") else root + x["url"]] if u not in urls]
            urls += new
            if not new:
                break
    return {"side": "ca", "listed": len(urls)}, urls


def read(key):
    site = Site(key)
    info, prods = {}, []
    try:
        info, urls = {"hoka": run_hoka, "salomon": run_salomon}[key](site)
        random.shuffle(urls)               # a fair sample of the catalogue if the page cap ends the read first
        for u in urls:
            if not site.room():
                break
            h = site.get(u)
            p = product(h, u) if h else None
            if p:
                prods.append(p)
    except No:
        pass
    sale = [p for p in prods if p["price"] and p["reg"] and p["reg"] > p["price"] * 1.01]
    return {"site": key, **info, "pages": site.pages, "minutes": site.minutes(), "stopped": site.stop,
            "robots_no": site.robots_no, "capped": not site.room() and not site.stop, "products": len(prods),
            "colours": sum(p["colours"] for p in prods), "sizes": sum(p["sizes"] for p in prods),
            "instock_sizes": sum(p["instock"] for p in prods), "on_sale": len(sale),
            "currencies": dict(collections.Counter(p["currency"] for p in prods)),
            "samples": prods[:5] + sale[:5]}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    keys = [a for a in sys.argv[2:] if a in ("hoka", "salomon")] or ["hoka", "salomon"]
    res = []
    for k in keys:
        print(f"== {k}", file=sys.stderr)
        res.append(read(k))
        (out / "brand-test.json").write_text(json.dumps(res, indent=1))
    md = ["## Brand test read (nothing published)", ""]
    for r in res:
        verdict = f"STOPPED: the store said no ({r['stopped']})" if r["stopped"] else ("read cleanly (page cap reached)" if r["capped"] else "read cleanly")
        md += [f"### {r['site']}: {verdict}",
               f"- side {r.get('side')}, {r.get('listed', 0)} product pages listed, {r['pages']} pages read in {r['minutes']} min, "
               f"{r['robots_no']} skipped by robots.txt",
               f"- {r['products']} products, {r['colours']} colours, {r['sizes']} sizes ({r['instock_sizes']} in stock), "
               f"{r['on_sale']} on sale, currencies {r['currencies']}"]
        md += [f"  - {s['name'][:60]}: {s['price']} {s['currency']} (reg {s['reg']}), {s['instock']}/{s['sizes']} sizes in stock, {s['url']}"
               for s in r["samples"][:6]]
    (out / "summary.md").write_text("\n".join(md) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(polite.report() if hasattr(polite, "report") else "", file=sys.stderr)


if __name__ == "__main__":
    main()
