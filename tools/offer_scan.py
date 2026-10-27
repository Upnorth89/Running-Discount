"""Store offers reader (Oct 27, Bastien: "we can't build a reader that does this every morning?"; "If something says up to 50% off,
would the robot be able to see this and investigate further?").

One polite visit per Shopify store homepage (robots.txt checked, honest name): the announcement / promo bar text, kept only when it
names a real store-wide offer ("20% off", "up to 50% off", "code FALL15", "extra 20% off sale"). Then the check against our own
prices for that store (deals.json): how many items are really on sale, the median and biggest discount, so an "up to 50% off" is
shown with what it really means. A code taken off at checkout can't be checked (we never fill carts): the store's words are quoted.

  python tools/offer_scan.py DEALS.json OUT.json [store keys…]
"""
import concurrent.futures as cf
import html
import json
import re
import statistics
import sys
import urllib.parse
import urllib.robotparser
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import scrape  # noqa: E402

UA = "TheGearFoxBot/1.0 (+https://thegearfox.com/about.html; store offers, one visit a day)"
# a bar or banner: Shopify themes call it announcement-bar / announcement / promo-bar / header__message / ticker
BAR = re.compile(r'<(div|p|a|span|section|aside|marquee|li|h\d)[^>]*class="[^"]*(announcement|promo[-_ ]?bar|header__message|ticker|top[-_]?bar|marquee|banner__text|notification-bar)[^"]*"[^>]*>(.*?)</\1>',
                 re.S | re.I)
PCT = re.compile(r"(?:up to\s+)?(\d{1,2})\s?%\s*(?:off|de rabais|de réduction|sur)|(?:jusqu'à|jusqu’à)\s+(\d{1,2})\s?%", re.I)
CODE = re.compile(r"\b(?:code|promo code|use code|with code|avec le code|code promo)\s*:?\s*[\"“']?([A-Z0-9][A-Z0-9-]{2,19})\b", re.I)
SKIP = re.compile(r"free (?:shipping|returns|delivery)|livraison gratuite|retours gratuits|gift card|carte[- ]cadeau|sign up|inscri|newsletter|first order|premi[eè]re commande|members?\b|membership|collective|subscri|abonne|rewards?|points|loyalty", re.I)


def text(h):
    h = re.sub(r"(?s)<(script|style|svg|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def allowed(base):
    rp = urllib.robotparser.RobotFileParser()
    try:
        r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=15)
        rp.parse(r.text.splitlines() if r.ok else [])
        return rp.can_fetch(UA, base + "/")
    except Exception:
        return True


def bars(base):
    """The offer lines on the store's homepage (deduplicated, short)."""
    if not allowed(base):
        return None, "robots.txt says no"
    try:
        r = requests.get(base + "/", headers={"User-Agent": UA, "Accept-Language": "en-CA,en;q=0.8,fr-CA;q=0.6"}, timeout=25)
    except Exception as e:
        return None, f"no answer ({type(e).__name__})"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    seen, out = set(), []
    for m in BAR.finditer(r.text):
        t = text(m.group(3))
        for part in re.split(r"\s{2,}|\s[|•·]\s", t):
            part = part.strip(" -–|")
            if 8 <= len(part) <= 160 and part.lower() not in seen:
                seen.add(part.lower())
                out.append(part)
    return out, ""


def offer(lines):
    """Lines that name a store-wide offer: a percentage off or a code; free shipping / sign-up perks / member points don't count."""
    keep = []
    for l in lines or []:
        if SKIP.search(l):            # member / sign-up / subscription perks aren't a store-wide sale (naak "15% off subscriptions for members")
            continue
        p, c = PCT.search(l), CODE.search(l)
        if p or c:
            keep.append({"text": l, "pct": int(p.group(1) or p.group(2)) if p else None, "upto": bool(re.search(r"up to|jusqu", l, re.I)),
                         "code": c.group(1).upper() if c else None})
    return keep


def truth(items, host):
    """What our own prices say about the store today: items with a size on sale there, median and biggest % off."""
    on, total = [], 0
    for d in items:
        offs = [i for i, u in enumerate(d.get("of", [])) if urllib.parse.urlparse(u).netloc.replace("www.", "").endswith(host)]
        if not offs:
            continue
        total += 1
        best = max((1 - z[1] / z[3] for z in d.get("sz", []) if len(z) > 3 and z[3] and z[2] in offs and z[1] < z[3] * 0.99), default=0)
        if best > 0:
            on.append(round(best * 100))
    if not total:
        return None
    return {"items": total, "on_sale": len(on), "share": round(100 * len(on) / total), "median": int(statistics.median(on)) if on else 0,
            "max": max(on) if on else 0}


def main():
    deals, out = Path(sys.argv[1]), Path(sys.argv[2])
    only = set(sys.argv[3:])
    items = json.loads(deals.read_text())["items"]
    stores = [(k, u) for k, u, *_ in scrape.SHOPIFY_STORES if not only or k in only]

    def one(ku):
        k, u = ku
        lines, why = bars(u.rstrip("/"))
        host = urllib.parse.urlparse(u).netloc.replace("www.", "")
        return {"store": k, "host": host, "why": why, "lines": lines or [], "offers": offer(lines), "truth": truth(items, host)}

    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, stores))
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    found = [r for r in res if r["offers"]]
    print(f"{len(res)} stores read, {sum(1 for r in res if r['why'])} not read, {len(found)} with an offer")
    for r in found:
        t = r["truth"]
        for o in r["offers"]:
            print(f"  {r['store']:16} {o['text'][:90]!r}", f"| our prices: {t['on_sale']}/{t['items']} on sale ({t['share']}%), median {t['median']}%, max {t['max']}%" if t else "| not in our data")


if __name__ == "__main__":
    main()
