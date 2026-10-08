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
import re
import sys
from urllib.parse import urlparse

import requests

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128 Safari/537.36", "Accept-Language": "en-CA,en;q=0.9"})
CA_COOKIES = {"cart_currency": "CAD", "localization": "CA"}


def _shopify(url, price, variant, us=False, tol=0.01):
    """Shopify product page: its .js twin has every variant's price, regular price and stock (in cents).
    us=True: a US shop in its own market (USD), the price given in USD with a small tolerance (converted from CAD)."""
    u = urlparse(url)
    m = re.match(r"(.*/products/[^/?#]+)", u.path)
    r = S.get(f"{u.scheme}://{u.netloc}{m.group(1)}.js", cookies=None if us else CA_COOKIES, timeout=30)
    if r.status_code in (403, 429) or r.status_code >= 500:
        return None
    if r.status_code != 200:
        return False                    # 404: the product is gone
    vs = r.json().get("variants") or []
    if variant:
        vs = [v for v in vs if str(v.get("id")) == str(variant)]
    ok = [v for v in vs if v.get("available") and v["price"] / 100 <= price + tol
          and (v.get("compare_at_price") or 0) > v["price"]]
    return bool(ok)


def _page(url, price):
    """Any other store: the page (or its product data) must show this price."""
    r = S.get(url, timeout=30)
    if r.status_code in (403, 429) or r.status_code >= 500:
        return None
    if r.status_code != 200:
        return False
    whole = f"{price:.2f}"
    forms = {whole, whole.replace(".", ",")}
    if whole.endswith("0") and not whole.endswith(".00"):
        forms.add(whole[:-1])                               # 63.90 written "63.9" in the page's data
    return any(re.search(r"(?<![\d.,])" + re.escape(f) + r"(?![\d])", r.text) for f in forms)


def still_on_sale(url, price, variant=None, us=False):
    """us=True (the USA side, Oct 9): price is in USD converted back from our CAD copy, so allow 2%; only Shopify shops can
    be checked that way (another page has to show the exact price string)."""
    try:
        if "/products/" in url:
            return _shopify(url, price, variant if variant and str(variant).isdigit() else None, us=us,
                            tol=max(0.01, price * 0.02) if us else 0.01)
        return None if us else _page(url, price)
    except (requests.RequestException, ValueError, KeyError, AttributeError):
        return None


if __name__ == "__main__":
    print(still_on_sale(sys.argv[1], float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None))
