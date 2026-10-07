#!/usr/bin/env python3
"""Store finder (Oct 6, 2026): which shops in a candidates file have a readable Shopify product feed, and what's in it.
One light look per shop (2 pages of /products.json at most, 1 s apart): shoes, on-sale share, currency. Never anything blocked.

  python tools/find_stores.py tools/us_candidates.txt      (workflow: .github/workflows/store-finder.yml)
"""
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
SHOE = re.compile(r"shoe|footwear|running shoe", re.I)


def platform(base):
    """Not Shopify: which shop system the homepage mentions (RunFree stores are readable at night, scraper/runfree.py)."""
    try:
        h = requests.get(base, headers=H, timeout=20).text.lower()
    except Exception:
        return ""
    for k, label in (("runfree", "RunFree"), ("lightspeed", "Lightspeed"), ("woocommerce", "WooCommerce"), ("bigcommerce", "BigCommerce"),
                     ("squarespace", "Squarespace"), ("wix.com", "Wix"), ("magento", "Magento"), ("cdn.shopify", "Shopify (feed closed)")):
        if k in h:
            return f", {label}"
    return ""


def look(line):
    state, name, hosts = [x.strip() for x in line.split("|")]
    bases = [b for host in hosts.split(",") for b in ([f"https://{host.strip()}"] if host.count(".") > 1
                                                   else [f"https://www.{host.strip()}", f"https://{host.strip()}"])]
    res = (state, name, hosts, "no answer", 0, 0, 0, "")
    for base in bases:
        try:
            r = requests.get(f"{base}/products.json?limit=250&page=1", headers=H, timeout=25)
        except Exception as e:
            res = (state, name, hosts, f"no answer ({type(e).__name__})", 0, 0, 0, "")
            continue
        if r.status_code != 200 or not r.text.lstrip().startswith("{"):
            res = (state, name, hosts, f"not Shopify (HTTP {r.status_code}){platform(base)}", 0, 0, 0, "")
            continue
        ps = r.json().get("products", [])
        if len(ps) == 250:
            time.sleep(1)
            try:
                ps += requests.get(f"{base}/products.json?limit=250&page=2", headers=H, timeout=25).json().get("products", [])
            except Exception:
                pass
        shoes = [p for p in ps if SHOE.search(f"{p.get('product_type', '')} {' '.join(p.get('tags') or []) if isinstance(p.get('tags'), list) else p.get('tags', '')}")]
        sale = sum(1 for p in ps if any(float(v.get("compare_at_price") or 0) > float(v.get("price") or 0) for v in p.get("variants", [])))
        cur = ""
        try:
            cur = requests.get(f"{base}/cart.js", headers=H, timeout=15).json().get("currency", "")
        except Exception:
            pass
        more = "+" if len(ps) >= 500 else ""
        return (state, name, base.replace("https://", ""), "READABLE", len(ps), len(shoes), sale, cur + more)
    return res


lines = [l for l in open(sys.argv[1]).read().splitlines() if l.strip() and not l.startswith("#")]
if os.environ.get("SHOPS"):        # one-off check from the workflow button: "NH | Run the Whites | runthewhites.com; ..."
    lines = [l.strip() for l in os.environ["SHOPS"].split(";") if l.strip()]
skip = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()     # e.g. shops already added
lines = [l for l in lines if l.split("|")[2].strip().split(",")[0] not in skip]
with ThreadPoolExecutor(6) as ex:
    rows = list(ex.map(look, lines))
rows.sort(key=lambda r: (r[3] != "READABLE", r[0], -r[5]))
out = [f"{r[0]:6} {r[1][:34]:34} {r[2][:34]:34} {r[3]:26} products {r[4]:4}{'+' if r[7].endswith('+') else ' '} shoes {r[5]:4} on sale {r[6]:4} {r[7].rstrip('+')}"
       for r in rows]
ok = sum(1 for r in rows if r[3] == "READABLE")
text = f"{ok} of {len(rows)} readable\n" + "\n".join(out)
print(text)
if os.environ.get("GITHUB_ACTIONS"):
    print("::notice title=Stores::" + text.replace("%", "%25").replace("\n", "%0A"))
