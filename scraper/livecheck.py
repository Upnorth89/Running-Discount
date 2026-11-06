#!/usr/bin/env python3
"""Is it still on sale right now? One look at the store's own page just before an email features a deal.

Oct 7, 2026: Bushtukah ended a 25% sale a few hours after the morning read, and the Instagram email featured an
Arc'teryx jacket that was back at full price. Bastien: "This should be double checked before sending the email so I
don't post fake stuff."

  still_on_sale(url, price, variant=None) -> True   the store's page shows this price (or lower), below its regular price
                                             False  it doesn't (sale over, sold out, price went up)
                                             None   couldn't check (blocked, timeout)
Callers feature only True: what we can't see today, we don't post.

  python scraper/livecheck.py URL PRICE [VARIANT]     check one by hand
"""
import json
import re
import sys
from urllib.parse import urlparse

import requests

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polite      # Nov 1: our own name, robots.txt obeyed, a pace per site (a refused page = "can't tell", never "ended")
S = polite.PoliteSession()
S.headers.update({"Accept-Language": "en-CA,en;q=0.9"})
CA_COOKIES = {"cart_currency": "CAD", "localization": "CA"}


def _shopify(url, price, variant, us=False, tol=0.01):
    """Shopify product page: its .js twin has every variant's price, regular price and stock (in cents).
    us=True: a US shop in its own market (USD), the price given in USD with a small tolerance (converted from CAD)."""
    u = urlparse(url)
    m = re.match(r"(.*/products/[^/?#]+)", u.path)
    r = S.get(f"{u.scheme}://{u.netloc}{m.group(1)}.js", cookies=None if us else CA_COOKIES, timeout=30)
    if r.status_code in (202, 403, 406, 429) or r.status_code >= 500:     # the store said no (Oct 10: Running Warehouse 406s
        return None                                                     # us): can't tell, never "sale ended"
    if r.status_code != 200:
        # Oct 31: The Feed moved to a headless Shopify front (Next.js): every product.js 404s while the product page is fine,
        # so all its featured deals read "sale ended". A 404 only means "gone" when the product page is gone too.
        p = S.get(url, cookies=None if us else CA_COOKIES, timeout=30)
        return _jsonld(p.text, price, variant, tol) if p.status_code == 200 else False
    if "json" not in (r.headers.get("content-type") or "") and not r.text.lstrip().startswith("{"):
        return None
    vs = r.json().get("variants") or []
    if variant:
        vs = [v for v in vs if str(v.get("id")) == str(variant)]
    ok = [v for v in vs if v.get("available") and v["price"] / 100 <= price + tol
          and (v.get("compare_at_price") or 0) > v["price"]]
    return bool(ok)


def _jsonld(html, price, variant, tol=0.01):
    """Nov 6 (data audit): headless Shopify fronts (Playmakers, The Feed) answer 404 for product.js while the page carries JSON-LD
    offers: price, availability and a ListPrice (the regular price). Their offers name colour/size, not our variant id, so one size
    can't be told apart: with a variant, only a page where EVERY offer is in stock at this price (or lower) on sale counts; without
    one, any such offer does. Anything else = None (can't tell), never "ended"."""
    offers = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html or "", re.S):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        for x in d if isinstance(d, list) else [d]:
            if isinstance(x, dict) and x.get("@type") == "Product":
                o = x.get("offers") or []
                offers += o if isinstance(o, list) else (o.get("offers") or [o]) if isinstance(o, dict) else []
    def sale(o):
        try:
            now = float(o.get("price") or 0)
            ps = o.get("priceSpecification") or []
            reg = max((float(q.get("price") or 0) for q in (ps if isinstance(ps, list) else [ps])
                       if isinstance(q, dict) and "ListPrice" in str(q.get("priceType"))), default=0)
        except (TypeError, ValueError):
            return False
        return "InStock" in str(o.get("availability")) and 0 < now <= price + tol and reg > now
    if not offers:
        return None
    if variant:
        return True if all(sale(o) for o in offers) else None
    return True if any(sale(o) for o in offers) else None


def _page(url, price):
    """Any other store: the page (or its product data) must show this price."""
    r = S.get(url, timeout=30)
    if r.status_code in (202, 403, 406, 429) or r.status_code >= 500:     # the store said no (Oct 10: Running Warehouse 406s
        return None                                                     # us): can't tell, never "sale ended"
    if r.status_code != 200:
        return False
    whole = f"{price:.2f}"
    forms = {whole, whole.replace(".", ",")}
    if whole.endswith("0") and not whole.endswith(".00"):
        forms.add(whole[:-1])                               # 63.90 written "63.9" in the page's data
    # Oct 8: Running Free writes "<sup>$</sup>49<sup>.99</sup>" and whole dollars as "$20": read the page's text without
    # its tags too, and accept "$20" for 20.00 (always with the $ sign, so "20" in a size or a date doesn't count)
    text = re.sub(r"<[^>]+>", "", r.text)
    found = any(re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d])", s) for f in forms for s in (r.text, text))
    if not found and whole.endswith(".00"):
        found = bool(re.search(r"\$\s?" + re.escape(whole[:-3]) + r"(?![\d.,])", text))
    return found


SC_API = "https://www.sportchek.ca/api/v1/product/api"
SC_HEAD = {"User-Agent": "Mozilla/5.0 (compatible; TheGearFoxBot/1.0; +https://thegearfox.com/about.html)",
           "ocp-apim-subscription-key": "c01ef3612328420c9f5cd9277e815a0e", "bannerid": "SC", "basesiteid": "SC"}


def _sportchek(url, price, variant):
    """Sport Chek (Oct 13): its pages fill in prices with a script, so ask the price service its pages use (same key and calls
    as scrape_sportchek). The size's link ends in its colour+size code (".333330634.html"); without one, any size of the product."""
    m = re.search(r"\.(\d{6,12})\.html", str(variant or "")) or re.search(r"\.(\d{6,12})\.html", url)
    if m:
        codes = [m.group(1)]
    else:
        f = re.search(r"-(\d+f)\.html", url, re.I)
        if not f:
            return None
        r = S.get(f"{SC_API}/v1/product-families/{f.group(1).lower()}?lang=en_CA", headers=SC_HEAD, timeout=30)
        if r.status_code != 200:
            return None if r.status_code in (403, 406, 429) or r.status_code >= 500 else False
        codes = [x["code"] for x in r.json().get("skus") or []]
    r = S.post(f"{SC_API}/v2/product/sku/PriceAvailability?lang=en_CA&storeId=314&cache=true", headers=SC_HEAD, timeout=30,
               json={"skus": [{"code": c, "lowStockThreshold": 0, "brand": ""} for c in codes]})
    if r.status_code != 200:
        return None
    for x in r.json().get("skus") or []:
        fu = x.get("fulfillment") or {}
        now = (x.get("currentPrice") or {}).get("value") or 0
        reg = (x.get("originalPrice") or {}).get("value") or 0
        if (((fu.get("availability") or {}).get("Corporate") or {}).get("Quantity") or 0) > 0 \
                and (fu.get("shipToHome") or {}).get("enabled") and 0 < now <= price + 0.01 and reg > now:
            return True
    return False


def still_on_sale(url, price, variant=None, us=False):
    """us=True (the USA side, Oct 8): price is in USD converted back from our CAD copy, so allow 2%; only Shopify shops can
    be checked that way (another page has to show the exact price string)."""
    try:
        # Shopify paths end at the product's handle (/products/<handle>); Running Free's "/products/All-Womens-66508/
        # Clothing-113/..." isn't Shopify and its .js twin 404s (Oct 8: 5 false "sale ended" in the noon check)
        if re.search(r"/products/[^/?#]+/?$", urlparse(url).path):
            return _shopify(url, price, variant if variant and str(variant).isdigit() else None, us=us,
                            tol=max(0.01, price * 0.02) if us else 0.01)
        if urlparse(url).netloc.endswith("sportchek.ca"):
            return None if us else _sportchek(url, price, variant)
        return None if us else _page(url, price)
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        return None


# Nov 5 (Bastien: "dont give me shoes that would be on sale for sizes that arent common. this hurts the brand"; "i just dont want
# people to end up on a sold out shoe"): a shoe we feature (Reddit, Bluesky, Pinterest, Instagram) needs 3+ COMMON sizes at the shown
# price, each one opened on the store's page right before posting. Common = men's 8-11.5, women's 6.5-9 (unisex "M:"/"W:" keys by
# their own cut; a plain size on a unisex shoe = men's). Wide/narrow sizes never count.
COMMON = {"men": {x / 2 for x in range(16, 24)}, "women": {x / 2 for x in range(13, 19)}}


def size_cut(key, women_item=False):
    """("men"|"women", 10.5) for a shoe size key ("10.5", "M:10", "W:8.5"); None for wide/narrow or unreadable keys."""
    k = str(key)
    if k.endswith(("~W", "~N")):
        return None
    m = re.fullmatch(r"(?:([MW]):)?(\d{1,2}(?:\.5)?)", k)
    if not m:
        return None
    cut = {"M": "men", "W": "women"}.get(m.group(1)) or ("women" if women_item else "men")
    return cut, float(m.group(2))


def women_item(it):
    return bool(re.search(r"women'?s|\bfemme\b", it.get("n", ""), re.I)) or it.get("sx") == ["women"]


def is_common(key, women=False):
    c = size_cut(key, women)
    return bool(c) and c[1] in COMMON[c[0]]


def size_label(key):
    c = size_cut(key)
    return f"{'W ' if str(key).startswith('W:') else ''}{c[1]:g}" if c else str(key)


def live_sizes(it, at, fx=1.0, us=False):
    """Open every size of `at` ([size, price, offer, regular, variant?] rows of a deals.json item) on the store's page.
    Returns (confirmed rows, blocked rows): confirmed = the store shows that size at that price (or lower) right now;
    blocked = the store wouldn't let us look (None). Gone/changed sizes are in neither."""
    best = {}
    for s in at:                                    # one row per size: its cheapest offer
        if s[0] not in best or s[1] < best[s[0]][1]:
            best[s[0]] = s
    ok, blocked = [], []
    for s in best.values():
        u = it["of"][s[2]]
        r = still_on_sale(u, round(s[1] / fx, 2), s[4] if len(s) > 4 else None, us=us and "/products/" in u)
        (ok if r is True else blocked if r is None else []).append(s)
    return ok, blocked


def shoe_ok(it, rows, need_common=3, need_total=5):
    """The featuring rule: 3+ common sizes and 5+ sizes in all among `rows` (live-confirmed rows). Returns (ok, common labels)."""
    w = women_item(it)
    keys = {s[0] for s in rows if size_cut(s[0], w)}
    com = sorted((k for k in keys if is_common(k, w)), key=lambda k: size_cut(k, w))
    return len(com) >= need_common and len(keys) >= need_total, [size_label(k) for k in com]


if __name__ == "__main__":
    print(still_on_sale(sys.argv[1], float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None))
