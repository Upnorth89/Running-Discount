"""Store offers reader (Oct 27, Bastien: "we can't build a reader that does this every morning?"; "If something says up to 50% off,
would the robot be able to see this and investigate further?").

One polite visit per Shopify store homepage (robots.txt checked, honest name): the announcement / promo bar text, kept only when it
names a real store-wide offer ("20% off", "up to 50% off", "code FALL15", "extra 20% off sale"). Then the check against our own
prices for that store (deals.json): how many items are really on sale, the median and biggest discount, so an "up to 50% off" is
shown with what it really means. A code taken off at checkout can't be checked (we never fill carts): the store's words are quoted.

  python tools/offer_scan.py SITE_DIR [store keys…]   (morning refresh, after the merge)
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
NOT_CODE = {"auto", "automatically", "applied", "applies", "at", "in", "required", "needed", "appliqué", "automatique", "requis", "not", "no"}
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
        if c and c.group(1).lower() in NOT_CODE:    # "code auto applied to cart" (Wigwam, Oct 27) is not a code called AUTO
            c = None
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


def published(r, o, t, today):
    """One offer for the site, or None. A sale banner our own prices don't back up (nothing on sale there today) stays off."""
    if not t or t["items"] < 5:
        return None
    if not o["code"] and t["on_sale"] == 0:
        return None
    sale = o["upto"] or bool(re.search(r"sale|clearance|selected|solde|liquidation|sélection", o["text"], re.I))
    # a sale banner ("up to 50% off selected") gets our check of the store's sale items; a cart-wide offer ("20% off, auto applied",
    # a code) is about full-price gear: the note goes on that store's full-price cards instead
    return {"store": r["host"], "side": r["side"], "en": o["text"], "fr": o["text"], "code": o["code"], "auto": True,
            "until": today, "url": r["base"], "cards": not sale, "sale": sale,
            "chk": {"n": t["items"], "on": t["on_sale"], "med": t["median"]} if sale and t["items"] >= 10 else None}


def main():
    """python tools/offer_scan.py SITE_DIR [--carry] [store keys…]: reads SITE/deals.json + deals-us.json, writes SITE/promos.json (hand-made
    offers from SITE/promos-hand.json still within their dates, then today's banners) and /tmp/offer-scan.json (everything read)."""
    import datetime
    from zoneinfo import ZoneInfo
    site = Path(sys.argv[1])
    carry = "--carry" in sys.argv
    only = {a for a in sys.argv[2:] if not a.startswith("--")}
    today = datetime.datetime.now(ZoneInfo("America/Vancouver")).date().isoformat()
    hand = []
    try:
        hand = [p for p in json.loads((site / "promos-hand.json").read_text()) if not p.get("until") or p["until"] >= today]
    except Exception:
        pass
    if carry:   # every run but the morning one: this morning's banners (live promos.json) + today's hand-made offers, no store visits
        try:
            live = [p for p in json.loads(Path("/tmp/promos-live.json").read_text()) if p.get("auto") and p.get("until", "") >= today]
        except Exception:
            live = []
        (site / "promos.json").write_text(json.dumps(hand + [p for p in live if p["store"] not in {h["store"] for h in hand}], ensure_ascii=False, indent=1))
        print(f"store offers carried: {len(live)} from this morning + {len(hand)} by hand")
        return
    items = {s: json.loads((site / f).read_text())["items"] if (site / f).exists() else [] for s, f in (("ca", "deals.json"), ("us", "deals-us.json"))}
    stores = [(k, u) for k, u, *_ in scrape.SHOPIFY_STORES if not only or k in only]

    def one(ku):
        k, u = ku
        base = u.rstrip("/")
        lines, why = bars(base)
        host = urllib.parse.urlparse(u).netloc.replace("www.", "")
        side = "us" if k in scrape.US_SHOPS or k.endswith("us") and k[:-2] in dict((x[0], 1) for x in scrape.SHOPIFY_STORES) else "ca"
        return {"store": k, "host": host, "base": base, "side": side, "why": why, "lines": lines or [], "offers": offer(lines),
                "truth": truth(items[side], host)}

    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, stores))
    Path("/tmp/offer-scan.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    auto, seen = [], {p["store"] for p in hand}
    for r in res:
        for o in r["offers"]:
            p = published(r, o, r["truth"], today)
            if p and p["store"] not in seen:     # one offer per store: the first banner line that names one
                seen.add(p["store"])
                auto.append(p)
    auto.sort(key=lambda p: -((p["chk"] or {}).get("on") or 0))
    (site / "promos.json").write_text(json.dumps(hand + auto, ensure_ascii=False, indent=1))
    print(f"{len(res)} stores read, {sum(1 for r in res if r['why'])} not read, {sum(1 for r in res if r['offers'])} with an offer line, "
          f"{len(auto)} on the site today (+ {len(hand)} by hand)")
    for p in hand + auto:
        c = p.get("chk")
        print(f"  {p['side']} {p['store']:24} {p['en'][:80]!r}" + (f" | our check: {c['on']} of {c['n']} on sale, median {c['med']}%" if c else ""))


if __name__ == "__main__":
    main()
