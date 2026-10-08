#!/usr/bin/env python3
"""The Gear Fox scraper.

Pulls the full running catalogue (full price and on sale) from Altitude Sports, The Last Hunt,
The Feed, Sea2Sky Nutrition, Sporting Life, Stampeak, MEC and REI, merges the same product sold by several stores, and writes
site/deals.json in the compact format the page reads:

  {v:2, updated, stores:{id: iso}, items:[{b,n,g,sx,w,img,lp,bb,ca,sz:[[size,price,offer,reg]],of:[url,...]}]}
  ca = sold and shipped from a Canadian store (no cross-border shipping, duties or currency conversion).

  sz = in-stock sizes: [size, today's lowest price, index of the offer (store link) that has it,
  that size's regular price]. A size is on sale when its price is below its regular price.
  lp = highest regular price across sizes (for display only).

If one store fails, its items from the previous run are kept so the site never goes blank.
Usage:  python scraper/scrape.py [out_path] [--remerge]
"""
import collections, json, os, re, sys, time, datetime as dt
import html as html_lib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlencode
import requests

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
REMERGE = "--remerge" in sys.argv   # rebuild deals.json from offers.json without scraping (for testing)
OUT = Path(ARGS[0] if ARGS else Path(__file__).resolve().parents[1] / "site" / "deals.json")
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128 Safari/537.36", "Accept-Language": "en-CA,en;q=0.9"})

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def get(url, tries=4, cookies=None):
    for i in range(tries):
        wait = 3 * (i + 1)
        try:
            r = S.get(url, timeout=45, cookies=cookies)
            if r.status_code == 429:                 # "too many requests": wait as long as the shop asks (Oct 8: The Feed)
                ra = r.headers.get("Retry-After", "")
                wait = min(int(ra), 60) if ra.isdigit() else 10 * (i + 1)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code} {url}")
            r.raise_for_status()
            return r
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(wait)

# ---------------------------------------------------------------- grouping
# Altitude / Last Hunt tag every product with a product_type_level; map those directly.
PTL = {
    "running-shoes": "shoes", "trail-running-shoes": "shoes", "road-running-shoes": "shoes", 
    "track-and-field-shoes": "shoes",
    "shorts": "bottoms", "leggings-and-tights": "bottoms", "technical-pants": "bottoms", "base-layer-bottoms": "bottoms",
    "joggers-and-sweatpants": "bottoms", "hardshell-and-rain-pants": "bottoms", "skirts-and-skorts": "bottoms",
    "t-shirts-and-polos": "tops", "tank-tops": "tops", "softshells-and-windbreakers": "tops", "long-sleeve-t-shirts": "tops",
    "base-layer-tops": "tops", "hoodies-and-sweatshirts": "tops", "hardshells-and-rain-jackets": "tops", "fleeces": "tops",
    "vests": "tops", "lightweight-insulated-jackets": "tops", "shirts": "tops", "sweaters-and-cardigans": "tops",
    "casual-jackets": "tops", "base-layer-one-piece-and-set": "tops",
    "bras": "bras", "socks": "socks", "gloves": "gloves", "mittens": "gloves",
    "caps-and-sun-hats": "headwear", "headbands-and-hair-accessories": "headwear", "beanies-and-winter-hats": "headwear",
    "neck-gaiters": "headwear",
    "hydration-packs": "packs", "running-belts": "packs", "belts": "packs", "hydration-pack-accessories": "packs",
    "arm-and-leg-warmers": "gear", "sunglasses": "gear", "headlamps": "gear", "bottles": "gear", "gaiters": "gear",
    "insoles": "gear", "trekking-poles": "gear", "soft-flasks": "gear",
    "smartwatches-and-fitness-trackers": "watches", "gps-watches": "watches", "heart-rate-monitors-and-sensors": "watches",
    "poles": "gear", "energy-food-and-drinks": "nutrition",
}
# Fallback on product names (first match wins). Kept strict so "Short Sleeve" isn't shorts, "Light Jacket" isn't a light.
RULES = [
    ("shoes",     r"\bshoes?\b|\bchaussures?\b|\bspikes\b|\bfootwear\b|\bsneakers?\b"),
    ("bras",      r"\bbras?\b"),
    ("socks",     r"\bsocks?\b|\bchaussettes?\b|mini crew|micro crew|mid crew|crew height|no[- ]show|over[- ]the[- ]calf|\bquarter\b(?![- ]?zip)|cushion\b.*\bcrew\b"),
    ("gloves",    r"\bgloves?\b|\bmitts?\b|mittens"),
    ("watches",   r"\bwatch(es)?\b(?! cap)"),      # a "Watch Cap Beanie" is a hat (Territory, Oct 8)
    ("gear",      r"\b(filter|bottle|flask|flex) caps?\b|^(?!.*\b(vests?|belts?|packs?)\b).*\bsoft flasks?\b|\b(safety|led|reflective) vest\b"),   # caps that aren't hats, a flask "with bite top", LED vests (Oct 8)
    ("headwear",  r"\bhats?\b|\bcaps?\b|\b(?:go|trl|trk|crw|fst|alz|ss|gt)cap\b|beanie|toque|tuque|headband|\bbuffs?\b|neck ?gaiter|neckwear|neck ?warmer|visor"),
    ("packs",     r"hydration (vest|pack)|race vest|running vest|backpack|\bbelts?\b|waist ?pack|\bvest \d|"
                  r"(?:\bpinnacle\b|(?<![.\d])\d+ ?l\b)(?!.*\b(jacket|pants?|shell|parka|singlet|tee|shirt|shorts?|tank|tights?|bra)\b)"),   # not "3L Jacket", Janji "Pinnacle Tee"
    ("bottoms",   r"\bbottoms?\b|(?<!short sleeve )\bshorts\b|\bshort\b(?! sleeve)|tights?\b|\bpants?\b|leggings?|joggers?|skirts?|skorts?|boxers?|briefs?"),
    ("tops",      r"t-?shirts?|\btees?\b|\bshirts?|\btops?\b|tanks?|singlets?|jackets?|\bcoats?\b|raincoats?|hood(ie|y)|\bvests?\b|gilets?|jersey|sweaters?|base ?layer|pullovers?|fleece|anorak|windbreaker|\bcrew\b|half zip|quarter zip|1/2 zip|1/4 zip|long sleeve|longsleeve|short sleeve|\bcrop\b"),
    ("gear",      r"poles?\b|headlamp|bottles?|flasks?|sunglass|(?:arm|calf|leg|compression) sleeves?\b|gaiters|roller|massage|insoles?|chafe|chafing|\bbalm\b|\bglide\b"),
]
def group_of(*texts):
    t = " ".join(x for x in texts if x).lower()
    for g, rx in RULES:
        if re.search(rx, t):
            return g
    return None

WORD = {"ONE SIZE": "OS", "O/S": "OS", "NA": "OS", "": "OS", "X-SMALL": "XS", "SMALL": "S", "MEDIUM": "M",
        "LARGE": "L", "X-LARGE": "XL", "XX-LARGE": "2XL", "XXL": "2XL", "XXXL": "3XL", "XXS": "2XS",
        "EXTRA SMALL": "XS", "EXTRA LARGE": "XL", "EXTRA EXTRA LARGE": "2XL", "EXTRA EXTRA SMALL": "2XS",
        "SM": "S", "MD": "M", "MED": "M", "LG": "L", "LRG": "L", "XLG": "XL", "XLARGE": "XL", "XSMALL": "XS", "XXLARGE": "2XL"}
def norm_size(s):
    s = str(s or "").strip()
    if re.fullmatch(r"(?i)os|x{0,3}[sl]|m|[2-4]?x[sl]", s):
        s = s.upper()                       # Balmoral writes "xs", "m", "os" (Oct 8)
    return WORD.get(s.upper(), s)

# ---------------------------------------------------------------- shoe sizes
# Stores write shoe sizes many ways. Every label becomes zero or more standard keys:
#   "10"      US size, for whatever gender the product is
#   "M:10"    men's US 10 / "W:11" women's US 11 (from unisex labels like "10 H / 11 F")
#   "…~W"     wide width, "…~N" narrow (the site never shows narrow; there's no narrow option)
# Anything we can't read with confidence (kids, EU/UK-only, fractions) gives no key rather than a wrong match.
def _us(n):
    try:
        v = float(n.replace("½", ".5").replace(",", "."))
    except ValueError:
        return None
    if not (3 <= v <= 17) or (v * 2) % 1:
        return None
    return str(int(v)) if v == int(v) else str(v)

def canon_shoe(label):
    t = str(label or "").strip().replace("½", ".5")
    if not t or t.upper() in ("OS", "ONE SIZE"):
        return ["OS"]
    low = t.lower()
    if re.search(r"\d\s*k\b|\bkids?\b|\byouth\b|\btoddler\b|\binfant\b|\d+\s+\d/\d", low):
        return []                                           # kids' sizes, EU/UK fractions
    width = ""
    if re.search(r"x-?wide|extra wide|\b4e\b|\d4e\b", low) or re.search(r"\bwide\b|\b2e\b|\d2e\b|\bee\b|\d\s?ee\b", low):
        width = "~W"
    elif re.search(r"\bnarrow\b|\d\s?[a2]a\b", low):
        width = "~N"
    # both genders in one label: "5.0 H / 6.0 F", "US M 4.5 / W 5.5", "W7/M5.5", "US M5.5 / US W6.5 / UK 5 / EU 38"
    m = re.search(r"(?:us\s*)?m(?:en'?s?)?\s*(\d+(?:\.\d)?)\b", low) if re.search(r"(?<![a-z])w(?:omen'?s?)?\s*\d", low) else None
    f = re.search(r"(?:us\s*)?w(?:omen'?s?)?\s*(\d+(?:\.\d)?)\b", low) if m else None
    if not (m and f):
        m = re.search(r"(\d+(?:\.\d)?)\s*h\b", low); f = re.search(r"(\d+(?:\.\d)?)\s*f\b", low)
    if m and f:
        out = []
        if _us(m.group(1)): out.append("M:" + _us(m.group(1)) + width)
        if _us(f.group(1)): out.append("W:" + _us(f.group(1)) + width)
        return out
    # one gender named: "Men / 7.5", "Women / 5.5", "W6", "US W5.5", "M10", "Men's 10"
    m = re.match(r"^(?:us\s*)?(men'?s?|women'?s?|m|w)\s*[/:-]?\s*(\d+(?:\.\d)?)\b", low)
    if m:
        v = _us(m.group(2))
        return [("W:" if m.group(1).startswith("w") else "M:") + v + width] if v else []
    # "Medium / 7.0", "Wide / 10.5", "10.5 Wide", "11D", "10.5B", "11 2E", "US 10", "8.0"
    t2 = re.sub(r"(?i)\b(medium|regular|standard|wide|x-?wide|extra wide|narrow)\b", " ", t)
    t2 = re.sub(r"(?i)^\s*us\s*", "", t2).strip(" /|-")
    m = re.match(r"^(\d+(?:[.,]\d)?)\s*(?:\+|[a-e]|[24]e|ee)?\s*$", t2, re.I)
    if m:
        v = _us(m.group(1))
        return [v + width] if v else []
    return []

# ---------------------------------------------------------------- Altitude / Last Hunt (same Next.js + commercetools platform)

# ---------------------------------------------------------------- Altitude / Last Hunt (same Next.js + commercetools platform)
# Product types (as the stores name them in their "running" category) worth listing, and our group.
CT_TYPES = {
    "Running Shoes": "shoes",
    "Shorts": "bottoms", "Leggings and Tights": "bottoms", "Technical Pants": "bottoms", "Base Layer Bottoms": "bottoms",
    "Joggers and Sweatpants": "bottoms", "Hardshell and Rain Pants": "bottoms",
    "T-Shirts and Polos": "tops", "Tank Tops": "tops", "Long Sleeve T-Shirts": "tops", "Softshells and Windbreakers": "tops",
    "Hardshells and Rain Jackets": "tops", "Base Layer Tops": "tops", "Fleeces": "tops", "Vests": "tops",
    "Lightweight Insulated Jackets": "tops", "Hoodies and Sweatshirts": "tops",
    "Bras": "bras", "Socks": "socks", "Gloves": "gloves", "Mittens": "gloves",
    "Caps and Sun Hats": "headwear", "Headbands and Hair Accessories": "headwear", "Beanies and Winter Hats": "headwear",
    "Hydration Packs": "packs", "Hydration Pack Accessories": "packs", "Belts": "packs",
    "Sunglasses": "gear", "Insoles": "gear", "Headlamps": "gear", "Poles": "gear", "Arm and Leg Warmers": "gear",
    "Gaiters": "gear", "Bottles": "gear",
    "Smartwatches and Fitness Trackers": "watches", "Heart Rate Monitors and Sensors": "watches",
    "Energy Food and Drinks": "nutrition",
}

def next_data(url):
    html = get(url).text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1))

def plp(url):
    ir = next_data(url)["props"]["pageProps"]["serverState"]["initialResults"]
    return ir[[k for k in ir if k.startswith("PRODUCTS")][0]]["results"][0]

def list_all(url):
    first = plp(url)
    hits = list(first["hits"])
    for p in range(2, first["nbPages"] + 1):
        hits += plp(f"{url}&page={p}")["hits"]
    return first, hits

def list_catalogue(base):
    """Every running listing, tagged with our group. The stores' search caps a listing at 1000
    results, so we list one product type at a time and split big types by gender."""
    types = plp(f"{base}/c/running")["facets"].get("attributes.product_type_name", {})
    found = {}
    for t, n in types.items():
        g = CT_TYPES.get(t)
        if not g:
            continue
        url = f"{base}/c/running?product_type_name={quote(t)}"
        parts = [url] if n <= 1000 else [f"{url}&gender={x}" for x in ("Men", "Women", "NA")]
        for u in parts:
            first, hits = list_all(u)
            if first["nbHits"] > 1000:
                print(f"  ! {u} has {first['nbHits']} listings, only 1000 reachable", file=sys.stderr)
            for h in hits:
                found.setdefault(h["slug"], (g, h.get("image_url")))
    return found

def attr(attrs, name):
    for a in attrs:
        if a["name"] == name:
            return a["value"]
    return None

def product(base, slug, st, g, img):
    d = next_data(f"{base}/p/{slug}")
    q = [q for q in d["props"]["pageProps"]["dehydratedState"]["queries"] if q["queryKey"][0] == "useProductBySlug"]
    p = q[0]["state"]["data"] if q else None
    if not p:
        return None
    mv = p["masterVariant"]
    A = mv["attributesRaw"]
    name = p["name"]
    genders = [x["key"] for x in (attr(A, "gender") or []) if isinstance(x, dict)]
    sx = ["men", "women"] if ("unisex" in genders or {"men", "women"} <= set(genders)) else [x for x in genders if x in ("men", "women")]
    if not sx:
        low = name.lower()
        sx = ["men"] if "men's" in low and "women's" not in low else ["women"] if "women's" in low else []
    width = attr(A, "width")
    wkey = (width.get("key") if isinstance(width, dict) else str(width or "")).lower()
    wide = "wide" in wkey or bool(re.search(r"\bwide\b", name, re.I))
    lp, sizes = 0, {}
    for v in [mv] + p.get("variants", []):
        pr = v.get("price") or {}
        reg = ((pr.get("value") or {}).get("centAmount") or 0) / 100
        disc = (((pr.get("discounted") or {}).get("value")) or {}).get("centAmount")
        res = (((v.get("availability") or {}).get("channels") or {}).get("results")) or []
        if not reg:
            continue
        lp = max(lp, reg)
        if not any((r.get("availability") or {}).get("isOnStock") for r in res):
            continue
        raw = attr(v["attributesRaw"], "size_1") or attr(v["attributesRaw"], "size")
        sz = norm_size(raw)
        price = round((disc if disc is not None else reg * 100) / 100, 2)
        if sz not in sizes or price < sizes[sz][0]:
            # the product page opens on this colour and size (?color=…&size=…, checked in a browser Oct 1, 2026)
            q = {"color": attr(v["attributesRaw"], "color"), "size": attr(v["attributesRaw"], "size") or raw}
            link = f"{base}/p/{slug}?" + urlencode({k: x for k, x in q.items() if isinstance(x, str) and x}, quote_via=quote)
            sizes[sz] = (price, reg, link)
    if not sizes:
        return None                      # nothing in stock
    if not img:
        a = (mv.get("assets") or [{}])[0].get("sources") or [{}]
        img = a[0].get("uri")
    return {"st": st, "b": attr(A, "brand_name") or "", "n": name, "u": f"{base}/p/{slug}", "g": g,
            "sx": sx, "w": wide, "img": img, "lp": lp, "bb": None, "sz": [[k, pr, rg, u] for k, (pr, rg, u) in sizes.items()]}

def scrape_commercetools(st, base):
    listing = list_catalogue(base)
    print(f"  {st}: {len(listing)} running listings", file=sys.stderr)
    out, errors = [], 0
    def one(item):
        slug, (g, img) = item
        try:
            return product(base, slug, st, g, img)
        except Exception as e:
            return e
    with ThreadPoolExecutor(10) as ex:
        for r in ex.map(one, listing.items()):
            if isinstance(r, Exception):
                errors += 1
            elif r:
                out.append(r)
    if listing and errors > len(listing) * 0.3:
        raise RuntimeError(f"{st}: {errors}/{len(listing)} product pages failed")
    return out

# ---------------------------------------------------------------- Decathlon Canada (server-rendered pages; robots.txt allows them)
DEC_BASE = "https://www.decathlon.ca"
# the whole running section (full price too, Oct 5, 2026: every reader reads full price), plus running clearance
DEC_LISTS = ["/en/clearance/running-clearance"] + [f"/en/sports/running/{c}" for c in (
    "running-shoes", "mens-running-shoes", "womens-running-shoes", "carbon-shoes", "mens-running-clothes", "womens-running-clothes",
    "mens-running-jackets", "womens-running-jackets", "mens-running-shorts", "womens-running-shorts", "mens-running-tops",
    "womens-running-top", "mens-running-socks", "womens-running-socks", "hydration-vests", "bottles-flasks", "running-accessories",
    "running-headwear", "running-poles", "running-neck-warmers", "winter-running-gear", "run-night")]
DEC_SOCKS = {"3.5 - 6": "S", "5 - 6": "S", "6.5 - 9": "M", "9.5 - 12": "L", "13 - 13.5": "XL", "12.5 - 14": "XL"}

def dec_skus(html):
    """Every size of every colour on a product page (the page embeds them as JSON)."""
    s = html.replace('\\"', '"').replace('\\\\', '\\')
    out = {}
    for m in re.finditer(r'"skus":\[\{"skuId"', s):
        seg, depth = s[m.start() + 7:m.start() + 400000], 0
        for k, ch in enumerate(seg):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    break
        try:
            for x in json.loads(seg[:k + 1]):
                out[x["skuId"]] = x
        except Exception:
            pass
    return list(out.values())

def dec_size(label, g):
    t = str(label or "").strip()
    if t in ("", "$undefined", "No Size", "One size") or re.search(r"\d+\s*(ml|mm)$", t, re.I):
        return "OS"
    if g == "shoes":
        m = re.match(r"US\s*(\d+(?:[.,]5)?)\b", t)
        return m.group(1).replace(",", ".") if m else None
    if g == "socks" and t in DEC_SOCKS:
        return DEC_SOCKS[t]
    t = re.sub(r"\s*\(.*?\)|\s*/\s*W\d.*$", "", t).strip()        # "XS (L30)", "XL / W39 L34"
    return t

def dec_price(x):
    for o in x.get("offers") or []:
        for fp in o.get("fixedPrices") or []:
            for tt in fp.get("typeTargets") or []:
                c = (tt.get("currencies") or {}).get("main") or {}
                p = c.get("valueWithoutTaxes")
                if isinstance(p, (int, float)):
                    r = c.get("referenceValueWithoutTaxes")
                    return float(p), float(r) if isinstance(r, (int, float)) and r > p else float(p)
    return None, None

def dec_group(x):
    t = x.get("title") or ""
    lvl = ((x.get("productNatureGroupLevel2") or {}).get("name") or "").lower()
    lvl1 = ((x.get("productNatureGroupLevel1") or {}).get("name") or "").lower()
    g = group_of(t)
    if g == "packs" and lvl1 == "apparel":             # a running vest you wear, not a hydration vest
        g = "tops"
    if not g:
        g = "shoes" if "footwear" in lvl else "tops" if "top" in lvl else "bottoms" if "bottom" in lvl else None
    return g

def dec_get(url):
    """Decathlon answers "429 too many requests" to GitHub's servers at our old pace (Oct 5, 2026): wait as long as it asks
    (Retry-After, else 30 s, 60 s), then try again."""
    for i in range(3):
        r = S.get(url, timeout=45)
        if r.status_code != 429:
            r.raise_for_status()
            return r
        wait = r.headers.get("Retry-After", "")
        time.sleep(min(int(wait), 120) if wait.isdigit() else 30 * (i + 1))
    raise requests.HTTPError(f"429 {url}")

DEC_BUDGET = 18 * 60     # seconds: Decathlon never holds up the whole refresh (a 429 storm ran into GitHub's 50-min limit, Oct 5)
DEC_PACE = 1.5           # seconds between product pages; the night job (--decathlon-night) reads much slower
DECATHLON_FILE = os.environ.get("DECATHLON_FILE", "/tmp/decathlon.json")

class DecBusy(Exception):
    """Decathlon said "429 too many requests" even after waiting: stop asking for today."""

def dec_links(budget):
    t0, links = time.time(), []
    for path in DEC_LISTS:
        start = 0
        while start < 2000 and time.time() - t0 < budget:
            try:
                html = dec_get(f"{DEC_BASE}{path}?from={start}&size=40").text
            except Exception as e:
                print(f"  decathlon: {path} stopped at {start} ({str(e)[:60]})", file=sys.stderr)
                if "429" in str(e):
                    raise DecBusy(str(e))
                break                                     # keep what the other lists gave
            new = [u for u in dict.fromkeys(re.findall(r'href="(/en/p/[^"]+)"', html)) if u not in links]
            if not new:
                break
            links += new
            start += 40
            time.sleep(max(3, DEC_PACE))
    seen, out = set(), []
    for u in links:                                       # one link per product (colours share a product id)
        m = re.search(r"/p/[^/]+/(\d+)/", u)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(u)
    return out

def dec_offer(u):
    """One product page -> an offer (None when nothing in stock / not for us). Raises DecBusy on a lasting 429."""
    try:
        skus = [x for x in dec_skus(dec_get(DEC_BASE + u).text) if x.get("isAvailable")]
    except Exception as e:
        if "429" in str(e):
            raise DecBusy(str(e))
        return None
    if not skus:
        return None
    x0 = skus[0]
    title = x0.get("title") or ""
    if re.search(r"\b(kids?|children|boys?|girls?|junior|baby)'?s?\b", title, re.I):
        return None
    g = dec_group(x0)
    if not g:
        return None
    gs = {(y.get("name") or "").lower() for y in x0.get("genders") or []}
    sx = (["men"] if "men" in gs else []) + (["women"] if "women" in gs else [])
    if g == "shoes" and len(sx) != 1:
        return None                                       # unisex US sizes are ambiguous without a gender
    sizes, lp = {}, 0
    for x in skus:
        price, reg = dec_price(x)
        if not price:
            continue
        lp = max(lp, reg)
        lab = dec_size(x.get("sizeLabel"), g)
        if not lab:
            continue
        m2 = re.match(r"^(2?XS|S|M|L|XL|2XL|3XL)\s*-\s*(S|M|L|XL|2XL|3XL|4XL)$", lab)
        for one in ([m2.group(1), m2.group(2)] if m2 else [lab]):
            if one not in sizes or price < sizes[one][0]:
                sizes[one] = (price, reg)
    if g in ("shoes", "tops", "bottoms", "bras", "socks", "gloves") and len(sizes) > 1:
        sizes.pop("OS", None)                             # an unlabelled size must not match everyone
    if not sizes:
        return None
    brand = ((x0.get("brand") or {}).get("name") or "Decathlon").title()
    img = (x0.get("mainImage") or {}).get("url")
    return {"st": "decathlon", "b": brand, "n": title, "u": DEC_BASE + u, "g": g, "sx": sx,
            "w": bool(re.search(r"\bwide\b", title, re.I)), "img": img + "?format=auto&f=500x0" if img else None,
            "lp": round(lp, 2), "bb": None, "sz": [[k, p, r] for k, (p, r) in sizes.items()], "ca": True}

def scrape_decathlon():
    t0, out, stopped = time.time(), [], ""
    try:
        links = dec_links(DEC_BUDGET / 3)
        for u in links:
            if time.time() - t0 > DEC_BUDGET:
                stopped = "out of time"
                break
            time.sleep(DEC_PACE)
            o = dec_offer(u)
            if o:
                out.append(o)
    except DecBusy:
        stopped = "429 too many requests"
        links = []
    print(f"  decathlon: {len(out)} products in stock" + (f" (stopped early: {stopped}, {time.time() - t0:.0f}s)" if stopped else ""),
          file=sys.stderr)
    if stopped and len(out) < 100:
        raise RuntimeError(f"no full read ({stopped} after {len(out)} products)")
    return out

# ---------------------------------------------------------------- Foot Locker Canada (checked Oct 4, 2026)
# Server-rendered pages; robots.txt allows category and product pages but not paging (currentPage=), so the
# performance-running collection (full price and sale, like every store: people watch full-price shoes for a drop) is
# read in slices that each fit on one page (48 cards): gender x price band, a band split again while it's full.
# Each product page carries every size with its own price and stock. Only shoes tagged "performancerunning" are kept
# (Foot Locker files lifestyle sneakers under Running too). Relaxed pace: one page at a time, ~1 s apart.
FL_BASE = "https://www.footlocker.ca"
FL_LISTS = [("/en/category/collection/performance-running.html", 'performancerunning:relevance:gender:{g}:price:"{lo}"-"{hi}"'),
            ("/en/category/sale/shoes.html", 'sale:relevance:collection_id:sale-shoes:sport:Running:gender:{g}:price:"{lo}"-"{hi}"')]
FL_CARD = re.compile(r'data-productcard="\{"name":"[^"]*","pos":\d+,"sku":"(\d+)"\}')

def fl_state(html):
    m = re.search(r"window\.__REACT_QUERY_STATE__\s*=\s*", html)
    return json.JSONDecoder().raw_decode(html[m.end():])[0] if m else None

def fl_page(path, q):
    page = html_lib.unescape(get(f"{FL_BASE}{path}?query={quote(q, safe='')}").text)
    time.sleep(1)
    m = re.search(r"([0-9,]+) results", page)
    return (int(m.group(1).replace(",", "")) if m else 0), FL_CARD.findall(page)

def fl_list(g, lo, hi, depth=0):
    """Every running shoe for one gender and price band: the collection first, the sale list in another order when a
    band can't be split any further (dozens of shoes at exactly $99.99)."""
    n, skus = fl_page(FL_LISTS[0][0], FL_LISTS[0][1].format(g=g, lo=lo, hi=hi))
    if n > len(skus):
        a, b = (0 if lo == "-inf" else float(lo)), (500 if hi == "inf" else float(hi))
        if b - a >= 1 and depth < 7:                        # full page: split the price band in two
            mid = round((a + b) / 2, 2)
            return fl_list(g, lo, f"{mid:g}", depth + 1) + fl_list(g, f"{mid:g}", hi, depth + 1)
        _, more = fl_page(FL_LISTS[1][0], FL_LISTS[1][1].format(g=g, lo=lo, hi=hi))
        skus += [x for x in more if x not in skus]
        if n > len(skus):
            print(f"  ! footlocker: {g} {lo}-{hi} has {n} shoes, {len(skus)} reachable", file=sys.stderr)
    return skus

def fl_product(sku):
    d = fl_state(get(f"{FL_BASE}/en/product/~/{sku}.html").text)
    q = [x for x in (d or {}).get("queries", []) if x.get("queryKey", [None])[0] == "product"]
    p = q[0]["state"]["data"] if q else None
    if not p:
        return None
    st, mo = p["style"], p["model"]
    if not any("performancerunning" in k.lower() for k in st.get("keywords") or []):
        return None                                         # lifestyle sneaker filed under Running
    name = re.sub(r"\s+", " ", mo["name"].replace("®", "").replace("™", "")).strip()
    brand = (mo.get("brand") or "").replace("®", "").strip()
    if brand and name.lower().startswith(brand.lower()):
        name = name[len(brand):].strip()
    gs = [x.lower() for x in mo.get("genders") or []]
    sx = ["men"] if any(x.startswith("men") for x in gs) else ["women"] if any(x.startswith("women") for x in gs) else []
    if len(sx) != 1:
        return None                                         # kids' or unisex sizing we can't place
    wide = "wide" in (st.get("width") or "").lower()
    sizes, lp = {}, 0
    for z in p.get("sizes") or []:
        pr = z.get("price") or {}
        reg, price = pr.get("listPrice"), pr.get("salePrice")
        if not reg or not price:
            continue
        lp = max(lp, reg)
        if not (z.get("active") and (z.get("inventory") or {}).get("inventoryAvailable")):
            continue
        lab = _us(str(z.get("size") or "").lstrip("0") or "0")
        if lab and (lab not in sizes or price < sizes[lab][0]):
            sizes[lab] = (float(price), float(reg))
    if not sizes:
        return None
    color = (st.get("color") or "").strip()
    return {"st": "footlocker", "b": brand, "n": name + (f" — {color}" if color else ""), "u": f"{FL_BASE}/en/product/~/{sku}.html",
            "g": "shoes", "sx": sx, "w": wide, "img": f"https://images.footlocker.com/is/image/EBFL2/{sku}?wid=500",
            "lp": float(lp), "bb": None, "sz": [[k + ("~W" if wide else ""), a, b] for k, (a, b) in sizes.items()], "ca": True}

def scrape_footlocker():
    skus = []
    for g in ("Men's", "Women's"):
        for lo, hi in (("-inf", "100"), ("100", "150"), ("150", "200"), ("200", "inf")):
            skus += [x for x in fl_list(g, lo, hi) if x not in skus]
    out, errors = [], 0
    for sku in skus:
        time.sleep(1)
        try:
            o = fl_product(sku)
        except Exception:
            errors += 1
            continue
        if o:
            out.append(o)
    if skus and errors > len(skus) * 0.3:
        raise RuntimeError(f"footlocker: {errors}/{len(skus)} product pages failed")
    print(f"  footlocker: {len(skus)} running listings, {len(out)} running shoes in stock", file=sys.stderr)
    return out

# ---------------------------------------------------------------- Shopify stores (The Feed in USD, Sea2Sky in CAD)
def usd_cad():
    for url, pick in [
        ("https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1",
         lambda j: float(j["observations"][0]["FXUSDCAD"]["v"])),
        ("https://open.er-api.com/v6/latest/USD", lambda j: float(j["rates"]["CAD"])),
    ]:
        try:
            return pick(get(url, tries=2).json())
        except Exception:
            pass
    return 1.38

_FX = {"CAD": 1.0}
FX_FALLBACK = {"USD": 1.38, "EUR": 1.50, "GBP": 1.80, "AUD": 0.90, "NZD": 0.82, "CHF": 1.60}
def fx_to_cad(cur):
    """Daily rate to convert a store's currency into CAD (Bank of Canada, then a public API)."""
    cur = (cur or "CAD").upper()
    if cur in _FX:
        return _FX[cur]
    rate = None
    for url, pick in [
        (f"https://www.bankofcanada.ca/valet/observations/FX{cur}CAD/json?recent=1",
         lambda j: float(j["observations"][0][f"FX{cur}CAD"]["v"])),
        (f"https://open.er-api.com/v6/latest/{cur}", lambda j: float(j["rates"]["CAD"])),
    ]:
        try:
            rate = pick(get(url, tries=2).json())
            break
        except Exception:
            pass
    _FX[cur] = rate or FX_FALLBACK.get(cur)
    return _FX[cur]

BB = re.compile(r"\s*\(?\s*best\s*by:?\s*([0-9/.-]+)\s*\)?", re.I)

# Shopify stores can show prices in the visitor's currency. Our daily run happens on US servers, so we ask
# Canadian stores for Canadian prices (the cookies a Canadian shopper would have) and then check which
# currency the prices actually came back in (cart.js reports it), converting if it isn't CAD.
CA_COOKIES = {"cart_currency": "CAD", "localization": "CA"}

def shopify_price_currency(base, cookies=None):
    """Currency of the prices this store is serving us right now, or None."""
    for path in ("/cart.js", "/cart.json"):
        try:
            cur = get(f"{base}{path}", tries=2, cookies=cookies).json().get("currency")
            if cur:
                return cur.upper()
        except Exception:
            pass
    return None

def shopify_products(base, max_pages=40, cookies=None):
    # A later page that fails (usually 429 "too busy") gets one more try after a pause; if it fails again the whole read
    # fails, so the store keeps yesterday's full catalogue instead of publishing a partial one (Oct 6: Athletic Annex
    # showed 180 of ~1,830 products, Mountain Run 222 of 924).
    prods, page = [], 1
    while page <= max_pages:
        url = f"{base}/products.json?limit=250&page={page}"
        try:
            batch = get(url, cookies=cookies).json()["products"]
        except Exception as e:
            if page == 1:
                raise
            print(f"  ! {base}: page {page} failed ({str(e)[:60]}), trying again in 30 s", file=sys.stderr)
            time.sleep(30)
            try:
                batch = get(url, cookies=cookies).json()["products"]
            except Exception as e2:
                raise RuntimeError(f"page {page} failed twice ({str(e2)[:60]}); keeping the last full read") from e2
        if not batch:
            break
        prods += batch
        page += 1
    return prods

SIZE_OPT = re.compile(r"^(size|taille|pointure|shoe size)( ?\([^)]*\))?$", re.I)   # "Size (US M)" (Ski Uphill)
WIDTH_OPT = re.compile(r"^(width|shoe width|shoe fit|fit|largeur)$", re.I)

def width_word(w, title):
    """A width option value -> the words canon_shoe() reads. Men's D and women's B are regular; women's D is wide."""
    w = (w or "").strip().lower()
    women = re.search(r"\bwom[ae]n", title, re.I)
    if re.search(r"wide|\b[246]e\b|\bee+\b|extra", w) or (women and w == "d"):
        return " Wide"
    if re.search(r"narrow|\b2a\b|\baa\b", w) or (not women and w == "b"):
        return " Narrow"
    return ""

SUBSCRIBE = re.compile(r"\b(picky club|subscri\w*|auto[- ]?ship)\b|\(\d+% off\)", re.I)


def shopify_items(st, base, prods, group_fn, fx=1.0, size_aware=False, size_fn=None, collapse=False):
    """One card per first option (pack size / colour) when a product has several options;
    flavours or sizes become the card's "sizes". Every in-stock variant is included."""
    out = []
    for p in prods:
        g = group_fn(p)
        if not g:
            continue
        opts = [o["name"].lower() for o in p.get("options", [])]
        img = (p.get("images") or [{}])[0].get("src")
        if img:
            img += ("&" if "?" in img else "?") + "width=360"
        buckets = {}
        for v in p["variants"]:
            if not v.get("available"):
                continue
            if SUBSCRIBE.search(v.get("title") or ""):
                continue                  # "Picky Club (20% off)": a subscription price, not a sale (Oct 8)
            price = float(v["price"])
            if price <= 0:
                continue
            cmp_ = max(price, float(v.get("compare_at_price") or 0))
            o1 = v.get("option1") or ""
            vals = [v.get(f"option{i}") or "" for i in (1, 2, 3)][:len(opts)]
            si = next((i for i, n in enumerate(opts) if SIZE_OPT.match(n)), None) if size_aware else None
            wi = next((i for i, n in enumerate(opts) if WIDTH_OPT.match(n)), None) if si is not None else None
            if si is not None:            # apparel: one card per colour, sizes as the "sizes"
                key = " / ".join(x for i, x in enumerate(vals) if i not in (si, wi) and x)
                label = vals[si]
                if wi is not None and g == "shoes":   # US shops: width as its own option ("D", "2E", "Wide", "Medium")
                    label += width_word(vals[wi], p.get("title") or "")
            else:
                rest = " / ".join(x for x in (v.get("option2"), v.get("option3")) if x)
                key = o1 if len(opts) > 1 else ""
                label = rest if len(opts) > 1 else o1
            if size_fn and g != "shoes":        # shoe labels are read by canon_shoe() in merge()
                label = size_fn(label)
            if collapse and si is not None:
                key = ""                  # one card per product; colours folded together
            bb = None
            m = BB.search(label) or BB.search(o1)
            if m:
                bb = m.group(1)
                label = BB.sub("", label).strip()
            b = buckets.setdefault(key, {"lp": 0, "sz": {}, "bb": None, "vid": v["id"]})
            b["lp"] = max(b["lp"], cmp_)
            lab = label or o1 or "OS"
            if lab.lower() == "default title":
                lab = "OS"
            cad, reg = round(price * fx, 2), round(cmp_ * fx, 2)
            m2 = re.match(r"^(2?XS|S|M|L|XL|2XL|XXL)\s*[-/]\s*(S|M|L|XL|2XL|XXL|3XL)$", lab.strip(), re.I)
            for one in ([m2.group(1).upper(), m2.group(2).upper()] if m2 and g != "headwear" else [lab]):  # "S - M" fits S and M
                if one not in b["sz"] or cad < b["sz"][one][0]:
                    b["sz"][one] = (cad, reg, v["id"])
            b["bb"] = b["bb"] or bb
        for key, b in buckets.items():
            out.append({"st": st, "b": p.get("vendor") or "", "n": p["title"] + (f" · {key}" if key else ""),
                        "u": f"{base}/products/{p['handle']}?variant={b['vid']}", "g": g, "sx": tag_gender(p) if g in ("tops", "bottoms", "bras") else [], "w": False,
                        "img": img, "lp": round(b["lp"] * fx, 2), "bb": b["bb"],
                        "sz": [[k, pr, rg, vid] for k, (pr, rg, vid) in b["sz"].items()]}
                       | ({"fs": 1} if any(FINAL_TAG.search(t) for t in p.get("tags") or []) or FINAL_TAG.search(p["title"]) else {}))
    return out

FEED_FOOD = {"Gels", "Hydration", "Bars", "Chews", "Waffles", "Protein", "Breakfast", "Snacks", "Pack", "Drink Mix", "Recovery"}
def feed_group(p):
    ptype = (p.get("product_type") or "").strip()
    cats = [t for t in (p.get("tags") or []) if t.startswith("Category:")]
    if ptype in FEED_FOOD or any(c.startswith("Category:Nutrition") for c in cats):
        return "nutrition"           # skips vitamins/supplements that aren't race fuel
    if ptype != "Gear":
        return None
    if any(c.startswith("Category:Gear>Bags") for c in cats):
        return "packs"
    g = group_of(p["title"]) or "gear"
    if g in ("tops", "bottoms", "bras") and not any(c.startswith(("Category:Gear>Clothing", "Category:Gear>Compression")) for c in cats):
        g = "gear"                   # e.g. "Crew Drop One organizer" is not a top
    return g

THEFEED_FILE = os.environ.get("THEFEED_FILE", "/tmp/thefeed.json")


def _feed_slim(p):
    """Only what the reader uses, so the saved copy stays small."""
    q = {k: p.get(k) for k in ("id", "title", "handle", "vendor", "product_type", "tags", "options")}
    q["images"] = (p.get("images") or [])[:1]
    q["variants"] = [{k: v.get(k) for k in ("id", "title", "price", "compare_at_price", "available", "option1", "option2", "option3")}
                     for v in p.get("variants") or []]
    return q


def _feed_page(url, cookies=None):
    """One page, patiently: The Feed answers "429 local_rate_limited" (a limit per internet address; GitHub's servers share
    theirs) with Retry-After: 60. Wait what it asks (else 1, 2, 3… min), up to 15 times per page."""
    for t in range(15):
        try:
            r = S.get(url, cookies=cookies, timeout=40)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                return r.json()["products"]
            wait = int(r.headers.get("Retry-After") or 0) or 60 * (t + 1)
            print(f"  thefeed: {url[-24:]} HTTP {r.status_code}, waiting {min(wait, 300)} s", file=sys.stderr)
        except requests.RequestException as e:
            wait = 60 * (t + 1)
            print(f"  thefeed: {url[-24:]} {type(e).__name__}, waiting {wait} s", file=sys.stderr)
        time.sleep(min(wait, 300))
    raise RuntimeError(f"The Feed kept saying no ({url})")


def thefeed_night(out):
    """The Feed (Oct 9, 2026; it answered our morning reads "429" twice in two days): read once a night, slowly
    (a page every 10 s, patient waits on 429), saved to thefeed.json on the history branch; the refresh uses that copy.
    If the night read fails, the last good copy stays."""
    base = "https://thefeed.com"
    prods, page = [], 1
    while page <= 40:
        batch = _feed_page(f"{base}/products.json?limit=250&page={page}", cookies=CA_COOKIES)
        if not batch:
            break
        prods += [_feed_slim(p) for p in batch]
        page += 1
        time.sleep(10)
    time.sleep(10)
    us = {str(v["id"]): float(v["price"]) for p in _feed_page(f"{base}/products.json?limit=250&page=1") for v in p["variants"]}
    Path(out).write_text(json.dumps({"updated": now(), "prods": prods, "us": us}, separators=(",", ":")))
    print(f"thefeed night read: {len(prods)} products in {page - 1} pages -> {out}", file=sys.stderr)
    return 0


def scrape_thefeed():
    # Read The Feed as a Canadian visitor: it then lists only what it ships to Canada (about 500 products fewer)
    # with its own CAD prices. Its site is custom-built (no cart.js), so check the currency against a page of
    # US prices: CAD prices run ~1.4x the USD ones; if they don't, the Canadian view was ignored -> convert.
    # Oct 9: the night copy (thefeed_night) first; a live read only when it's missing or older than 36 h.
    base = "https://thefeed.com"
    saved = None
    try:
        d = json.loads(Path(THEFEED_FILE).read_text())
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d["updated"])).total_seconds() / 3600
        if age < 36 and d.get("prods"):
            saved = d
            print(f"  thefeed: night copy from {d['updated']} ({age:.0f} h old)", file=sys.stderr)
    except Exception:
        pass
    if saved:
        prods = saved["prods"]
        us = {int(k): v for k, v in saved["us"].items()}
    else:
        prods = shopify_products(base, cookies=CA_COOKIES)
        us = {v["id"]: float(v["price"]) for p in get(f"{base}/products.json?limit=250&page=1").json()["products"] for v in p["variants"]}
    ratios = sorted(float(v["price"]) / us[v["id"]] for p in prods for v in p["variants"] if us.get(v["id"]))
    ratio = ratios[len(ratios) // 2] if ratios else 1.0
    fx = 1.0 if ratio > 1.2 else usd_cad()
    print(f"  thefeed: {len(prods)} products shipping to Canada, CAD/USD price ratio {ratio:.2f} -> "
          + ("prices in CAD" if fx == 1.0 else f"prices in USD x{fx}"), file=sys.stderr)
    feed_report(prods)
    return shopify_items("thefeed", base, prods, feed_group, fx)

def feed_report(prods):
    """Log The Feed's catalogue by product type: how many are on sale, and which types we leave out."""
    def sale(p):
        return any(v.get("available") and float(v.get("compare_at_price") or 0) > float(v["price"]) for v in p["variants"])
    def tagged(p):      # marked sale/clearance in tags but with no "was" price we can read
        return any(re.search(r"sale|clearance|closeout|short.?dated|bargain", t, re.I) for t in p.get("tags") or [])
    types = {}
    for p in prods:
        n = types.setdefault((p.get("product_type") or "").strip() or "(none)", [0, 0, 0, bool(feed_group(p))])
        n[0] += 1
        n[1] += sale(p)
        n[2] += tagged(p) and not sale(p)
    print(f"  thefeed: {len(prods)} products, {sum(sale(p) for p in prods)} with a was-price, "
          f"{sum(tagged(p) and not sale(p) for p in prods)} tagged sale without one", file=sys.stderr)
    for t, (a, b, c, kept) in sorted(types.items(), key=lambda x: -x[1][1]):
        print(f"    {'kept' if kept else 'left out'}: {t}: {a} products, {b} on sale, {c} tagged sale only", file=sys.stderr)

S2S_GEAR = {"sunglasses": "gear", "bottles": "gear", "flasks": "gear", "clothing": None}
def s2s_group(p):
    t = (p.get("product_type") or "").strip().lower()
    if t in S2S_GEAR:
        return S2S_GEAR[t] or group_of(p["title"]) or "gear"
    if "gift card" in p["title"].lower():
        return None
    return "nutrition"

def scrape_sea2sky():
    base = "https://sea2skynutrition.ca"   # Vancouver, prices already in CAD
    return shopify_items("sea2sky", base, shopify_products(base, cookies=CA_COOKIES), s2s_group, fx=ca_store_fx("sea2sky", base))



# ---------------------------------------------------------------- Stampeak (Montreal, Shopify, CAD; English catalogue under /en)
SP_TYPES = {
    "running shoes": "shoes", "nutrition": "nutrition", "caps / visors": "headwear", "hydration packs": "packs",
    "socks": "socks", "recovery & wellness socks": "socks", "headlamp": "gear", "watch": "watches", "sensors": "watches",
    "men's tops": "tops", "women's tops": "tops", "tops": "tops", "flasks": "gear", "short": "bottoms",
    "bib shorts / leggings": "bottoms", "running/trail belt": "packs", "belts": "packs", "anti-friction": "gear",
    "arm warmers": "gear", "neck gaiter": "headwear", "glasses": "gear", "ice crampons": "gear",
}
SP_BY_TITLE = {"clothing", "compression socks & sleeves", "beanies & mittens", "tuques & mittens", "bib shorts", "", "bands"}
def sp_group(p):
    t = (p.get("product_type") or "").strip().lower()
    title = p["title"]
    if re.search(r"cycling|\bbike\b|\bski\b|gift card", title, re.I):
        return None
    if t in SP_TYPES:
        return SP_TYPES[t]
    if t in SP_BY_TITLE:
        g = group_of(title)
        if t == "compression socks & sleeves" and g != "socks":
            g = "gear"                      # calf/arm sleeves
        return g
    return None                             # electrostimulation, braces, luggage, paddleboards, ...

SOCK_EU = {"36/38": "S", "39/41": "M", "42/44": "L", "45/47": "XL"}
def sp_size(label):
    """'10 M / 11 W' (unisex shoes) -> men's US '10'; EU sock ranges -> S/M/L/XL."""
    m = re.match(r"^\s*(\d+(?:\.\d)?)\s*M\b", label or "")
    if m:
        return m.group(1)
    m = re.search(r"\b(3[5-9]|4[0-7])/(3[5-9]|4[0-7])\b", label or "")
    if m and m.group(0) in SOCK_EU:
        return SOCK_EU[m.group(0)]
    return norm_size(label)

def ca_store_fx(st, base):
    """A Canadian store should now be serving CAD; if it still isn't, convert what it serves."""
    cur = shopify_price_currency(base, CA_COOKIES) or "CAD"
    if cur != "CAD":
        print(f"  ! {st}: prices came back in {cur}, converting to CAD", file=sys.stderr)
    return fx_to_cad(cur)

def scrape_stampeak():
    base = "https://www.stampeak.com/en"
    return shopify_items("stampeak", base, shopify_products(base, cookies=CA_COOKIES), sp_group, size_aware=True, size_fn=sp_size,
                         fx=ca_store_fx("stampeak", base))


# ---------------------------------------------------------------- MEC (Next.js + Algolia; everything we need is in the listing pages)
MEC_BASE = "https://www.mec.ca"
MEC_CAT = {  # "Products > Running > X" -> our group
    "running and training footwear": "shoes", "running clothing": None, "running packs": "packs",
    "sunglasses": "gear", "headlamps": "gear", "water bottles": "gear", "injury prevention": "gear",
    "training electronics": "watches", "training food & drinks": "nutrition",
}

def mec_results(url):
    d = next_data(url)
    ir = d["props"]["pageProps"]["serverState"]["initialResults"]
    return ir[[k for k in ir if k.startswith("products")][0]]["results"][0], d

def mec_list(url):
    """All hits for one listing URL; figures out whether ?page= is 0- or 1-based."""
    first, d = mec_results(url)
    hits, pages = list(first["hits"]), first.get("nbPages", 1)
    sep = "&" if "?" in url else "?"
    offset = None
    for n in range(1, pages):
        for cand in ([n + 1, n] if offset is None else [n + offset]):
            r, _ = mec_results(f"{url}{sep}page={cand}")
            if r.get("page") == n:
                offset = cand - n
                hits += r["hits"]
                break
        else:
            print(f"  ! mec: could not page {url}", file=sys.stderr)
            break
        time.sleep(0.5)
    return first, d, hits

def mec_group(h):
    cats = [c for c in (h.get("categories") or {}).get("lvl2", []) if c.startswith("Products > Running > ")]
    for c in cats:
        key = c.split(" > ")[-1].lower()
        if key in MEC_CAT:
            return MEC_CAT[key] or group_of(h.get("title", "")) or "tops"
    return group_of(h.get("title", ""))

def mec_running(h):
    """Saves from MEC's all-deals page also hold ski, bike, camping and kids' gear: keep running items only
    (items without categories, from older saves, pass)."""
    cats = h.get("categories") or {}
    if not cats:
        return True
    return any(c.startswith("Products > Running") or c.endswith("> Running packs")
               for c in cats.get("lvl1", []) + cats.get("lvl2", []))

def mec_item(h):
    if (h.get("inventoryStatus") or "IN_STOCK") == "OUT_OF_STOCK":
        return None
    g = mec_group(h)
    if not g:
        return None
    best, reg, img = None, None, h.get("image")
    for v in (h.get("variants") or {}).values():
        gp = ((v.get("prices") or {}).get("guest")) or {}
        price, sale = gp.get("price") or v.get("price"), gp.get("salePrice") or v.get("salePrice")
        if not price:
            continue
        now = sale or gp.get("effectivePrice") or price
        if best is None or now < best:
            best, reg, img = now, price, v.get("image") or img
    if best is None:
        gp = ((h.get("prices") or {}).get("guest")) or {}
        reg = gp.get("price") or h.get("price")
        best = gp.get("salePrice") or h.get("salePrice") or reg
    if not best:
        return None
    sz = h.get("size") or {}
    g_ = h.get("gender")
    sizes = (sz.get("US Men's") if g_ != "womens" else None) or sz.get("US Women's") or sz.get("US Men's") \
        or h.get("sizeClothingMens") or h.get("sizeClothingWomens") or (h.get("clothingSize") or {}).get("Alpha") \
        or sz.get("Alpha") or ["OS"]
    sx = {"mens": ["men"], "womens": ["women"], "unisex": ["men", "women"]}.get(g_, [])
    if img:
        img = img.replace(".1280.1280.", ".500.500.")
    return {"st": "mec", "b": h.get("brand") or "", "n": h.get("title") or "", "u": MEC_BASE + h["url"], "g": g,
            "sx": sx, "w": (h.get("shoeWidth") or "").lower() == "wide" or bool(re.search(r"\bwide\b", h.get("title", ""), re.I)),
            "img": img, "lp": round(float(reg), 2), "bb": None,
            "sz": [[norm_size(x), round(float(best), 2), round(float(reg), 2)] for x in dict.fromkeys(sizes)]}

def scrape_mec():
    root = f"{MEC_BASE}/en/products/running"
    first, d, hits = mec_list(root)
    total = first.get("nbHits", 0)
    print(f"  mec: {total} running listings", file=sys.stderr)
    if total > 1000:        # search caps at 1000; walk the sub-categories instead
        html = get(root).text + json.dumps(d)
        subs = sorted(set(re.findall(r'/en/products/running/[a-z0-9-]+(?:/[a-z0-9-]+)?(?=["?#])', html)))
        subs = {x[:-len("/deals")] if x.endswith("/deals") else x for x in subs}
        subs = sorted(x for x in subs if x.count("/") > 3 and "new-arrivals" not in x)
        print(f"  mec: walking {len(subs)} sub-categories", file=sys.stderr)
        for sub in subs:
            try:
                f2, _, h2 = mec_list(MEC_BASE + sub)
                hits += h2
                if f2.get("nbHits", 0) > 1000:
                    print(f"  ! mec: {sub} has {f2['nbHits']} listings, only 1000 reachable", file=sys.stderr)
            except Exception as e:
                print(f"  ! mec: {sub} failed ({e})", file=sys.stderr)
    seen, out = set(), []
    for h in hits:
        key = h.get("parentSku") or h.get("url")
        if key in seen:
            continue
        seen.add(key)
        it = mec_item(h)
        if it:
            out.append(it)
    return out


# ---------------------------------------------------------------- REI (US store, prices in USD -> CAD; data is embedded in the listing pages)
REI_BASE = "https://www.rei.com"

def rei_page(url):
    html = get(url).text
    m = re.search(r'<script type="application/json" id="initial-props">(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("no product data on page (blocked or redesigned)")
    return json.loads(m.group(1))["ProductSearch"]["products"]["searchResults"]

def rei_item(r, fx):
    if not r.get("available", True):
        return None
    title = r.get("cleanTitle") or r.get("title") or ""
    g = "nutrition" if re.search(SL_FOOD, title.lower()) else group_of(title)
    if not g:
        return None
    dp = r.get("displayPrice") or {}
    now = dp.get("min")
    reg = dp.get("compareAt") or (float(r["regularPrice"]) if r.get("regularPrice") else None) or now
    if not now:
        return None
    sizes = [x["size"] for x in ((r.get("sizeDetails") or {}).get("sizeDetails") or [])
             if x.get("filterState", "available") == "available" and x.get("size")]
    sizes = sizes or ["OS"]
    now_c, reg_c = round(float(now) * fx, 2), round(max(float(reg), float(now)) * fx, 2)
    return {"st": "rei", "b": r.get("brand") or "", "n": title, "u": REI_BASE + r["link"], "g": g, "sx": [],
            "w": bool(re.search(r"\bwide\b", title, re.I)), "img": r.get("thumbnailImageLink"),
            "lp": reg_c, "bb": None,
            "sz": [[norm_size(re.sub(r"\s*wide\s*$", "", x, flags=re.I)), now_c, reg_c] for x in dict.fromkeys(sizes)]}

def scrape_rei():
    fx = usd_cad()
    out, seen, page, last = [], set(), 1, None
    while last is None or page <= last:
        sr = rei_page(f"{REI_BASE}/c/running?page={page}&pagesize=90")
        if last is None:
            q = ((sr.get("pagination") or {}).get("lastPage") or {}).get("queryString") or ""
            m = re.search(r"[?&]page=(\d+)", q)
            last = int(m.group(1)) if m else 1
            print(f"  rei: {last} pages of running gear, USD->CAD {fx}", file=sys.stderr)
        results = sr.get("results") or []
        if not results:
            break
        for r in results:
            if r.get("prodId") in seen:
                continue
            seen.add(r.get("prodId"))
            it = rei_item(r, fx)
            if it:
                out.append(it)
        page += 1
        time.sleep(1)
    return out

# ---------------------------------------------------------------- Sporting Life (Salesforce Commerce Cloud)
SL_BASE = "https://www.sportinglife.ca"
SL_TILE = re.compile(r'<div class="product-tile[^"]*"[^>]*data-itemid="([^"]+)"[^>]*>(.*?)<!-- END: \.product-tile -->', re.S)

def _txt(html):
    import html as H
    return H.unescape(re.sub(r"<[^>]+>", " ", html or "")).strip()

def _money(t):
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", t or "")
    return float(m.group(1).replace(",", "")) if m else None

def sl_parse_listing(html):
    """Tiles on a category page: link, brand, name, image, regular + current price."""
    import html as H
    out = []
    for itemid, t in SL_TILE.findall(html):
        link = re.search(r'class="name-link"\s+href="([^"]+)"', t)
        brand = re.search(r'class="product-brand">(.*?)</span>', t, re.S)
        name = re.search(r'class="product-name">(.*?)</span>', t, re.S)
        img = re.search(r'<img src="(https://cdn\.media\.amplience\.net/[^"]+)"', t)
        std = re.search(r'class="price-standard">(.*?)</span>', t, re.S)
        sale = re.search(r'class="price-sales[^"]*">(.*?)</span>', t, re.S)
        if not (link and name):
            continue
        u = H.unescape(link.group(1))
        out.append({"id": itemid, "u": u if u.startswith("http") else SL_BASE + u,
                    "b": _txt(brand.group(1)) if brand else "", "n": _txt(name.group(1)),
                    "img": re.sub(r"w=\d+&h=\d+", "w=400&h=400", H.unescape(img.group(1))) if img else None,
                    "std": _money(_txt(std.group(1))) if std else None,
                    "cur": _money(_txt(sale.group(1))) if sale else None})
    return out

def sl_parse_product(html):
    """Per-size price + stock and the product type, from the page's schema.org data."""
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        nodes = d.get("@graph", [d]) if isinstance(d, dict) else d
        for n in nodes:
            if not isinstance(n, dict) or n.get("@type") != "Product":
                continue
            ptype = ""
            for pv in n.get("additionalProperty") or []:
                if pv.get("name") == "Product Type":
                    ptype = pv.get("value") or ""
            offers = (n.get("offers") or {}).get("offers") or []
            sizes, links = {}, {}
            for o in offers:
                if "InStock" not in (o.get("availability") or "") and "LimitedAvailability" not in (o.get("availability") or ""):
                    continue
                sz = norm_size(o.get("size"))
                pr = float(o.get("price") or 0)
                if pr and (sz not in sizes or pr < sizes[sz]):
                    sizes[sz] = pr
                    u = o.get("url") or ""      # the page with this size selected, when the store gives one
                    if "sportinglife.ca" in u and ("dwvar" in u or "size" in u.lower()):
                        links[sz] = u
            return ptype, sizes, links
    return "", {}, {}

SL_FOOD = r"\bgels?\b|\bchews?\b|\bbars?\b|electrolyte|drink mix|energy|hydration mix|nutrition"
def sl_group(ptype, name):
    if re.search(SL_FOOD, (ptype or "").lower()):
        return "nutrition"
    return group_of(ptype) or group_of(name)

def scrape_sportinglife():
    listing, start, total = {}, 0, None
    while total is None or start < total:
        html = get(f"{SL_BASE}/en-CA/running/?start={start}&sz=48").text
        if total is None:
            m = re.search(r"([\d,]+)\s+Items", html)
            total = int(m.group(1).replace(",", "")) if m else 0
            print(f"  sportinglife: {total} running listings", file=sys.stderr)
        tiles = sl_parse_listing(html)
        if not tiles:
            break
        for t in tiles:
            listing.setdefault(t["id"], t)
        start += 48
        time.sleep(1)
    out, errors = [], 0
    def one(t):
        try:
            ptype, sizes, links = sl_parse_product(get(t["u"]).text)
        except Exception as e:
            return e
        g = sl_group(ptype, t["n"])
        if not g or not sizes:
            return None
        std = t["std"]                          # regular price shown on the tile, if on sale
        sz = [[k, v, max(std or v, v)] + ([links[k]] if k in links else []) for k, v in sizes.items()]
        return {"st": "sportinglife", "b": t["b"], "n": t["n"], "u": t["u"], "g": g, "sx": [],
                "w": bool(re.search(r"\bwide\b", t["n"], re.I)), "img": t["img"],
                "lp": max(r for _, _, r in sz), "bb": None, "sz": sz}
    with ThreadPoolExecutor(4) as ex:          # gentle: 4 pages at a time
        for r in ex.map(one, listing.values()):
            if isinstance(r, Exception):
                errors += 1
            elif r:
                out.append(r)
    if listing and errors > len(listing) * 0.3:
        raise RuntimeError(f"sportinglife: {errors}/{len(listing)} product pages failed")
    n_sz = sum(len(o["sz"]) for o in out)
    print(f"  sportinglife: {sum(len(e) > 3 for o in out for e in o['sz'])} of {n_sz} sizes have their own link", file=sys.stderr)
    return out

# ---------------------------------------------------------------- merge + main


# ---------------------------------------------------------------- Pages you save yourself (MEC, REI)
# MEC and REI block automated access, so instead you save their running-deals pages from your own
# browser (Cmd+S, "Webpage, HTML only") and upload them to the saved-pages/ folder in the repo.
# Files older than SAVED_MAX_DAYS are ignored so stale prices never linger.
SAVED_DIR = Path(__file__).resolve().parents[1] / "saved-pages"
SAVED_MAX_DAYS = 10

def _file_age_days(path):
    """Age from the git commit that last touched the file (upload date on GitHub); falls back to mtime."""
    import subprocess
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(path)], cwd=path.parent,
                             capture_output=True, text=True, timeout=20).stdout.strip()
        ts = float(out) if out else path.stat().st_mtime
    except Exception:
        ts = path.stat().st_mtime
    return (time.time() - ts) / 86400

def saved_pages():
    files = []
    if SAVED_DIR.is_dir():
        for f in list(SAVED_DIR.glob("*.htm*")) + list(SAVED_DIR.glob("*.json")):
            age = _file_age_days(f)
            if f.suffix == ".json":         # files from the "Grab deals" bookmark carry their own date
                try:
                    import datetime as _d
                    saved = json.loads(f.read_text()).get("saved")
                    age = (time.time() - _d.datetime.fromisoformat(saved.replace("Z", "+00:00")).timestamp()) / 86400
                except Exception:
                    pass
            if age > SAVED_MAX_DAYS:
                print(f"  saved page {f.name} is {age:.0f} days old, skipped (upload a fresh one)", file=sys.stderr)
                continue
            files.append((age, f))
    return [f for _, f in sorted(files)]    # newest first, so this week's price wins over last week's

def scrape_mec_saved():
    out, seen, used = [], set(), 0
    for f in saved_pages():
        text = f.read_text(errors="ignore")
        if f.suffix == ".json":
            try:
                d = json.loads(text)
            except Exception:
                continue
            if d.get("store") != "mec":
                continue
            hits = d.get("hits") or []
        else:
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.S)
            if not m or "mec.ca" not in text[:200000]:
                continue
            try:
                ir = json.loads(m.group(1))["props"]["pageProps"]["serverState"]["initialResults"]
                hits = ir[[k for k in ir if k.startswith("products")][0]]["results"][0]["hits"]
            except Exception:
                continue
        used += 1
        for h in hits:
            key = h.get("parentSku") or h.get("url")
            if key in seen or not mec_running(h):
                continue
            seen.add(key)
            it = mec_item(h)
            if it:
                out.append(it)
    print(f"  mec: {used} saved page(s)", file=sys.stderr)
    return out                      # no fresh pages -> no MEC items (never keep stale prices)

def scrape_svp_saved():
    """SVP Sports (Québec): Shopify behind a Cloudflare check, so read from the collection Bastien saves with the
    Grab deals bookmark (svp-YYYY-MM-DD.json: Shopify products as the store serves them, in CAD)."""
    prods, seen, used = [], set(), 0
    for f in saved_pages():
        if f.suffix != ".json":
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if d.get("store") != "svp":
            continue
        used += 1
        for p in d.get("products") or []:
            if p.get("id") in seen:
                continue
            seen.add(p.get("id"))
            prods.append(p)
    print(f"  svp: {used} saved page(s), {len(prods)} products", file=sys.stderr)
    items = shopify_items("svp", "https://www.svpsports.ca", prods, generic_group("gear"), size_aware=True, collapse=True,
                          size_fn=generic_size)
    for o in items:
        o["ca"] = True
    return items

def scrape_rei_saved():
    fx = usd_cad()
    out, seen, used = [], set(), 0
    for f in saved_pages():
        text = f.read_text(errors="ignore")
        if f.suffix == ".json":
            try:
                d = json.loads(text)
            except Exception:
                continue
            if d.get("store") != "rei":
                continue
            results = d.get("results") or []
        else:
            m = re.search(r'<script type="application/json" id="initial-props">(.*?)</script>', text, re.S)
            if not m:
                continue
            try:
                results = json.loads(m.group(1))["ProductSearch"]["products"]["searchResults"]["results"]
            except Exception:
                continue
        used += 1
        for r in results:
            if r.get("prodId") in seen:
                continue
            seen.add(r.get("prodId"))
            it = rei_item(r, fx)
            if it:
                out.append(it)
    print(f"  rei: {used} saved page(s), USD->CAD {fx}", file=sys.stderr)
    return out

# ---------------------------------------------------------------- Catalog file (Sport Chek, adidas.ca, REI)
# Oct 9, 2026: these stores block automated reads, so Bastien brings a catalog file (Excel, "Running_Gear_Catalog.xlsx":
# a "Sizes & availability" sheet, one row per size and colour: retailer, item, size, width, gender, currency, regular and
# current price, online availability, variant URL, observed time) and uploads it to saved-pages/. Before using the first one
# we checked 9 random sale sizes by hand on the stores' pages: all 9 right. Only sizes marked "In stock" are used, and a
# file older than CATALOG_MAX_DAYS (by its own "Observed" time) is ignored: sales end, and our page check can't see these stores.
CATALOG_MAX_DAYS = 3
SAVED_STORES = {"mec", "rei", "svp", "sportchek", "adidasca"}   # from files Bastien brings: no file = no deals, never stale ones
CATALOG_STORES = {"Sport Chek": ("sportchek", "https://www.sportchek.ca"), "Adidas": ("adidasca", "https://www.adidas.ca"),
                  "REI": ("rei", "https://www.rei.com")}
_catalog_cache = {}
import threading
_catalog_lock = threading.Lock()      # the three stores read in parallel lanes: open the file once

def _catalog_size(label, width, group, gender):
    s = re.sub(r'\s*\d+(\.\d+)?"$', "", str(label or "").strip())            # shorts inseam: 'S/P 5"'
    if s.upper() in ("NONE", "ONE SIZE", ""):
        return "OS"
    if group == "shoes":
        w = (width or "").lower()
        wide = w in ("wide", "2e", "4e", "extra wide") or (w == "d" and gender == "Women")
        narrow = w == "narrow" or (w == "b" and gender == "Men")
        return s + (" Wide" if wide else " Narrow" if narrow else "")
    s = re.sub(r"^(\S+)\s*/\s*(2?T?[PMG]|TG|2TG|2TP)$", r"\1", s)            # adidas.ca 'L/G', 'XS/TP', '2XL/2TG'
    s = re.sub(r"^(\d?X{0,3}[SL]|M)(TP|TG|T)$", r"\1", s)                    # 'XSTP', '2XLTG', '2XST'
    return norm_size(s)

def catalog_rows():
    """The newest catalog file in saved-pages/ that's fresh enough: [row dict], or [] (cached for the run)."""
    with _catalog_lock:
        return _catalog_rows()

def _catalog_rows():
    if "rows" in _catalog_cache:
        return _catalog_cache["rows"]
    rows = []
    files = sorted(SAVED_DIR.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True) if SAVED_DIR.is_dir() else []
    for f in files:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
            def sheet(name):
                it = wb[name].iter_rows(values_only=True)
                head = next(r for r in it if r and r[0] == "Retailer")
                return [dict(zip(head, r)) for r in it if r and r[0]]
            got, prods = sheet("Sizes & availability"), sheet("Products")
            _catalog_cache["products"] = {(p["Retailer"], p["Item ID"]): p for p in prods}
        except Exception as e:
            print(f"  catalog file {f.name}: can't read it ({str(e)[:80]})", file=sys.stderr)
            continue
        seen = [r["Observed (UTC)"] for r in got if isinstance(r.get("Observed (UTC)"), dt.datetime)]
        age = (dt.datetime.utcnow() - max(seen)).total_seconds() / 86400 if seen else _file_age_days(f)
        if age > CATALOG_MAX_DAYS:
            print(f"  catalog file {f.name} is {age:.1f} days old, skipped (bring a fresh one)", file=sys.stderr)
            continue
        print(f"  catalog file {f.name}: {len(got)} size rows, {age:.1f} days old", file=sys.stderr)
        rows = got
        break
    _catalog_cache["rows"] = rows
    return rows

def scrape_catalog(retailer):
    """One retailer's products from the catalog file, in the offers format (prices in CAD)."""
    st, base = CATALOG_STORES[retailer]
    prods = {}
    for r in catalog_rows():
        if r.get("Retailer") != retailer or r.get("Online availability") != "In stock":
            continue
        g_ = r.get("Gender") or ""
        if g_.startswith("Kids"):
            continue
        now, reg = r.get("Current price"), r.get("Regular price")
        if not now:
            continue
        name, iid = str(r.get("Item") or "").strip(), r.get("Item ID")
        p = prods.get(iid)
        if p is None:
            g = "nutrition" if re.search(SL_FOOD, name.lower()) else group_of(name)
            if not g:
                continue
            fx = 1.0 if r.get("Currency") == "CAD" else fx_to_cad(r.get("Currency") or "USD")
            info = _catalog_cache.get("products", {}).get((retailer, iid)) or {}
            url = info.get("Product URL") or (r.get("Variant URL") or "").split("?")[0]
            p = prods[iid] = {"st": st, "b": info.get("Brand") or "", "n": name, "u": url, "g": g, "fx": fx, "gender": g_,
                              "sx": {"Men": ["men"], "Women": ["women"], "Unisex": ["men", "women"]}.get(g_, []),
                              "w": False, "img": None, "bb": None, "sizes": {}}
        size = _catalog_size(r.get("Size"), r.get("Width / fit"), p["g"], g_)
        now_c, reg_c = round(float(now) * p["fx"], 2), round(max(float(reg or now), float(now)) * p["fx"], 2)
        old = p["sizes"].get(size)
        if old is None or now_c < old[0]:
            p["sizes"][size] = (now_c, reg_c)
    out = []
    for iid, p in prods.items():
        if not p["sizes"]:
            continue
        sz = [[s, a, b_] for s, (a, b_) in p["sizes"].items()]
        out.append({"st": p["st"], "b": p["b"], "n": p["n"], "u": p["u"], "g": p["g"], "sx": p["sx"], "w": p["w"], "img": None,
                    "lp": max(e[2] for e in sz), "bb": None, "sz": sz})
    print(f"  {st}: {len(out)} products from the catalog file", file=sys.stderr)
    return out

# ---------------------------------------------------------------- Any Shopify store (brands + shops): one line each
# Each store is tested during the run: if it isn't Shopify, blocks us, or sells nothing running-related,
# it is skipped and noted in the log. Currency is read from the store and converted to CAD.
# kind: "gear" = classify each product; "food" = race-fuel brand; "socks" = sock brand; "eyewear" = sunglasses brand.
SHOPIFY_STORES = [
    # Canadian running & outdoor shops (sell in CAD)
    ("vanrunco",       "https://vanrunco.com",               "gear"),   # Run As You Are / Vancouver Running Co.
    ("coureurnordique","https://lecoureurnordique.ca",       "gear"),   # Le Coureur Nordique (QC)
    ("bushtukah",      "https://bushtukah.com",              "gear"),   # Bushtukah (Ottawa)
    ("nordarun",       "https://nordarun.com",               "gear"),
    ("ciele",          "https://ca.cieleathletics.com",      "gear"),   # Ciele's Canadian store
    ("xact",           "https://xactnutrition.com",          "food"),
    ("naak",           "https://naak.com",                   "food"),
    ("brix",           "https://brixrechargeparlanature.com", "food"),   # Brix (Québec maple fuel: gels, chews, waffles; Oct 7)
    ("upika",          "https://upika.ca",                   "food"),   # Upika (Québec drink mixes and bars; Oct 7)
    ("grynd",          "https://grynd.ca",                   "food"),   # Grynd (Calgary / Prince George energy waffles; Oct 7)
    ("krono",          "https://krononutrition.com/en-ca",   "food"),
    ("innerself",      "https://innerselfrunning.com",       "gear"),   # Inner Self (Montréal running apparel; Oct 8)
    ("balmoral",       "https://balmoralrunning.com",        "gear"),   # Balmoral (Montréal, made-in-Canada running apparel; Oct 8)   # Krono Nutrition (Québec gels, bars, drink mixes; Oct 7)
    # running & trail brands
    ("altra",          "https://altrarunning.com",           "gear"),
    ("janji",          "https://runjanji.com",               "gear"),
    ("rabbit",         "https://www.runinrabbit.com",        "gear"),
    ("satisfy",        "https://satisfyrunning.com",         "gear"),
    ("saysky",         "https://saysky.com",                 "gear"),
    ("soar",           "https://www.soarrunning.com",        "gear"),
    ("raidlight",      "https://raidlight.com",              "gear"),
    ("districtvision", "https://www.districtvision.com",     "gear"),
    ("bandit",         "https://banditrunning.com",          "gear"),
    ("tenthousand",    "https://www.tenthousand.cc",         "gear"),
    ("oiselle",        "https://www.oiselle.com",            "gear"),
    ("2xu",            "https://ca.2xu.com",                 "gear"),   # Oct 9: 2xu.com is the Australian store (ships to AU only)
    ("2xuus",          "https://us.2xu.com",                 "gear"),
    # Canadian stores of US brands (Oct 9): their .com ships to the US only; the .com stays for the USA side
    ("feeturesca",     "https://feetures.ca",                "socks"),
    ("balegaca",       "https://balega.ca",                  "socks"),
    ("stanceca",       "https://stance.ca",                  "socks"),
    ("goodrca",        "https://goodr.ca",                   "eyewear"),
    ("nuunca",         "https://nuun.ca",                    "food"),
    ("humaca",         "https://humagel.ca",                 "food"),   # Podium Imports (Huma's Canadian distributor): nutrition only
    ("rnnr",           "https://rnnr.com",                   "gear"),
    ("smartwool",      "https://smartwool.com",              "gear"),
    ("nathan",         "https://www.nathansports.com",       "gear"),
    ("nakedsports",    "https://www.nakedsportsinnovations.com", "gear"),
    ("mounttocoast",   "https://mounttocoast.com",           "gear"),
    ("kogalla",        "https://kogalla.com",                "gear"),
    ("squirrels",      "https://squirrelsnutbutter.com",     "gear"),
    # added 2026-09-27
    ("endurance",      "https://www.boutiqueendurance.ca",   "gear"),   # Boutique Endurance (QC running)
    ("fitfirst",       "https://www.fitfirst.ca",            "gear"),   # Fit First Footwear (Calgary running)
    # added 2026-09-30
    ("capra",          "https://www.capra.run",              "gear"),   # Capra Running Co. (Squamish trail running)
    # added 2026-10-01
    ("lecoureur",      "https://www.lecoureur.com",          "gear"),   # Le Coureur (Montréal running)
    ("blacktoe",       "https://www.blacktoerunning.com",    "gear"),   # BlackToe Running (Toronto)
    # added 2026-10-02
    ("frontrunners",   "https://www.frontrunners.ca",        "gear"),   # Frontrunners (Victoria)
    ("forerunners",    "https://shop.forerunners.ca",        "gear"),
    ("rackets",        "https://racketsandrunners.ca",       "rackets"),   # Rackets & Runners (Vancouver, Oak St; tennis/pickleball left out; Oct 8)   # Forerunners (Vancouver; shop on its own address)
    # added 2026-10-07
    ("runuphill",      "https://runuphill.ca",               "gear"),   # Ski Uphill / Run Uphill (Canmore + Squamish; same shop as skiuphill.ca)
    # added 2026-10-08 (sorting check clean)
    ("trailrunner",    "https://trailrunnerstore.com",       "gear"),   # The Trail Runner Store (Toronto)
    ("cowichan",       "https://cowichanvalleyrunning.com",  "gear"),   # Cowichan Valley Running (Mill Bay, BC)
    # added 2026-10-03
    ("aerobicsfirst",  "https://www.aerobicsfirst.com",      "gear"),   # Aerobics First (Halifax)
    ("cityparkrunners", "https://www.cityparkrunners.com",   "gear"),   # City Park Runners (Winnipeg)
    ("runnersshop",    "https://www.therunnersshop.com",     "gear"),   # The Runners Shop (Toronto, since 1975)
    ("strides",        "https://www.stridesrunning.com",     "gear"),   # Strides Running Store (Calgary, Canmore)
    # added 2026-10-06
    ("brainsport",     "https://www.brainsport.ca",          "gear"),   # Brainsport (Saskatoon, SK)
    ("sail",           "https://www.sail.ca/en-ca",          "gear"),   # SAIL plein air (QC/ON chain): its running section only
    # US running shops (Oct 6, 2026): the USA side of the site only (they may not ship to Canada); read in their US market
    ("pacers",         "https://pacersrunning.com",          "gear"),   # Pacers Running (Washington DC area)
    ("portlandrun",    "https://portlandrunningcompany.com", "gear"),   # Portland Running Company (Oregon)
    ("heartbreak",     "https://heartbreakhillrunningcompany.com", "gear"),   # Heartbreak Hill Running Co. (Boston)
    ("runnersplus",    "https://runnersplus.com",            "gear"),   # Runners Plus (Chicago area)
    ("gazelle",        "https://gazellesports.com",          "gear"),   # Gazelle Sports (Michigan)
    ("sportsbasement", "https://sportsbasement.com",         "gear"),   # Sports Basement (California)
    # 2026 Best Running Stores (The Running Event) with a readable Shopify feed
    ("tortoisehare",   "https://www.tortoiseandharesports.com", "gear"),   # Tortoise & Hare Sports (Glendale, AZ)
    ("runflagstaff",   "https://www.runflagstaff.com",       "gear"),   # Run Flagstaff (AZ)
    ("runninglab",     "https://www.runninglabstore.com",    "gear"),   # Running Lab (Brighton, MI)
    ("playmakers",     "https://www.playmakers.com",         "gear"),   # Playmakers (Okemos, MI)
    ("millcity",       "https://www.millcityrunning.com",    "gear"),   # Mill City Running (Minneapolis, MN)
    ("runningwell",    "https://therunningwellstore.com",    "gear"),   # The Running Well Store (Kansas City, MO)
    ("mountainrun",    "https://www.mountainrunningcompany.com", "gear"),   # Mountain Running Company (Asheville, NC)
    ("confluence",     "https://www.confluencerunning.com",  "gear"),   # Confluence Running (Johnson City, NY)
    ("columbusrun",    "https://www.columbusrunning.com",    "gear"),   # Columbus Running Company (OH)
    ("scrantonrun",    "https://scrantonrunning.com",        "gear"),   # Scranton Running Company (PA)
    ("trailheadrun",   "https://www.trailheadrunningsupply.com", "gear"),   # Trailhead Running Supply (Flower Mound, TX)
    ("prrunwalk",      "https://www.prrunandwalk.com",       "gear"),   # =PR= Run & Walk (Northern VA)
    ("performancerun", "https://www.performancerunning.com", "gear"),   # Performance Running Outfitters (WI)
    # Best Running Stores past winners (Oct 6, 2026)
    ("fitnesssports",  "https://www.fitnesssports.com",      "gear"),   # Fitness Sports (Iowa)
    ("athleticannex",  "https://www.athleticannex.com",      "gear"),   # Athletic Annex (Indianapolis, IN)
    ("annarborrun",    "https://www.annarborrunningcompany.com", "gear"),   # Ann Arbor Running Company (MI)
    ("tworivers",      "https://tworiverstreads.com",        "gear"),   # Two Rivers Treads (Asheville, NC)
    ("xtramile",       "https://www.xtramilerunning.com",    "gear"),   # Xtra Mile Running (Tennessee)
    ("lukeslocker",    "https://www.lukeslocker.com",        "gear"),   # Luke's Locker (Texas)
    ("sfrunco",        "https://store.sfrunco.com",          "gear"),   # San Francisco Running Company (Mill Valley, San Anselmo CA)
    ("territory",      "https://territoryrun.co",            "gear"),   # Territory Run Co. (California trail apparel; Oct 8, USA side)
    ("pathprojects",   "https://pathprojects.com",           "gear"),   # Path Projects (Colorado running shorts/liners; Oct 8, USA side)
    # socks
    ("feetures",       "https://www.feetures.com",           "socks"),
    ("balega",         "https://www.balega.com",             "socks"),
    ("darntough",      "https://www.darntough.com",          "socks"),
    ("swiftwick",      "https://swiftwick.com",              "socks"),
    ("stance",         "https://stance.com",                 "socks"),
    ("wigwam",         "https://wigwam.com",                 "socks"),
    # sunglasses
    ("goodr",          "https://goodr.com",                  "eyewear"),
    ("roka",           "https://roka.com",                   "eyewear"),
    ("sunski",         "https://sunski.com",                 "eyewear"),
    ("ombraz",         "https://ombraz.com",                 "eyewear"),   # Ombraz armless sunglasses (California; Oct 8, USA side)
    ("tifosi",         "https://www.tifosioptics.com",       "eyewear"),
    # race fuel
    ("tailwind",       "https://www.tailwindnutrition.com",  "food"),
    ("skratch",        "https://www.skratchlabs.com",        "food"),
    ("nuun",           "https://nuun.com",                   "food"),
    # ("honeystinger",   "https://www.honeystinger.com",       "food"),   # off Oct 8: blocks GitHub's servers (0 products since Oct 1); its gels reach us through other stores
    ("gu",             "https://guenergy.com",               "food"),
    ("huma",           "https://www.humagel.com",            "food"),
]

NOT_RUNNING = re.compile(r"gift ?card|pannier|eyeglasses|optical|reading glass|blue light|prescription|e-?gift|\bbike\b|cycling|\bbib\b|swim|golf|\bski\b|snowboard|\bdog\b|\bpet\b|"
                         r"\btent\b|sleeping bag|stickers?|poster|\bmug\b|\bbundle builder\b|warranty|shipping protection|"
                         r"route protection|insurance|\bsample\b|donation|\bknitwear\b|\bsherpa\b|\bgym bag\b|tote bag|loops & loot|test clothing|"   # Balmoral's lifestyle pieces (Oct 8)
                         # ski touring (Ski Uphill, Oct 7); trail crampons and goodr "Donkey Goggles" sunglasses stay
                         r"\bskis\b|\bhelmets?\b|airbag|avalanche|(?<!donkey )\bgoggles?\b|\b(powder|pole) baskets?\b|climbing skins?|skinalp|"
                         r"\bbindings?\b|splitboard|glide wax|liquid wax|aenergy harness|footwear refresh", re.I)
FOOD = re.compile(r"\bgels?\b(?!-)|[ée]lectrolyte|boisson|\bbarres?\b|jujubes?|\bchews?\b|\bbars?\b|electrolyte|drink mix|hydration mix|energy|\bfuel\b|"
                  r"nutrition|recovery drink|protein|waffle|stroopwafel|salt tab|capsule", re.I)

def generic_size(label):
    """Common Shopify size labels -> the site's sizes: 'M10 / W11.5', "Men's 10", 'US 10', 'EU 36-38' socks."""
    t = re.sub(r"\s*\(.*?\)", "", (label or "")).strip()
    m = re.match(r"^\s*(?:M|Men'?s|US M|Mens)\s*(\d+(?:\.5)?)\b", t, re.I) or re.match(r"^\s*(\d+(?:\.5)?)\s*M\b", t)
    if m:
        return m.group(1)
    m = re.match(r"^\s*US\s*(\d+(?:\.5)?)\s*$", t, re.I)
    if m:
        return m.group(1)
    return sp_size(t)

RR_SKIP = re.compile(r"^(rackets|admin|run club)|court|walking|cross training|casual|kids|teamevent|sweatbands|underwear", re.I)
RR_TENNIS = re.compile(r"\b(babolat|head|wilson|yonex|tecnifibre|pickleball|tennis|nikecourt|rafa|court|squash|badminton)\b", re.I)


def generic_group(kind):
    def g(p):
        title = p.get("title") or ""
        ptype = p.get("product_type") or ""
        tags = re.sub(r"[_:>/-]+", " ", " ".join(p.get("tags") or []))
        if NOT_RUNNING.search(f"{title} {ptype}") or re.search(r"gift ?card|carte[- ]cadeau", title, re.I):
            return None
        if kind == "rackets":          # Rackets & Runners (Vancouver, Oct 8): half the shop is tennis and pickleball
            if RR_SKIP.search(ptype) or RR_TENNIS.search(title):
                return None
            if re.match(r"footwear\b", ptype, re.I):
                return "shoes" if re.search(r"\brunning\b", ptype, re.I) else None
        g = group_of(title)
        if kind == "food" and re.search(r"\b(soft ?cup|gobelet|bouteilles?|gourdes?|flasques?)\b", title, re.I):
            return "gear"                  # Brix (Oct 7): a race cup, a bottle, a soft flask
        if kind == "food" and re.search(r"\bcasquette\b", title, re.I):
            return "headwear"              # Upika's cap
        if kind == "food" and re.search(r"\bcache[- ]cou\b", title, re.I):
            return "headwear"              # neck gaiter
        if kind == "food":             # fuel brands: food, unless it's clearly merch/gear (a cap, a flask)
            return g if g and not FOOD.search(title) else "nutrition"
        if kind == "socks":            # sock brands: socks unless it's clearly a tee/hoodie/etc.
            return g if g and g != "tops" or re.search(r"\btee\b|shirt|tank|hoodie|jacket|pullover", title, re.I) else "socks"
        if kind == "eyewear":          # sunglasses brands: everything is eyewear except hats/apparel
            return g if g in ("headwear", "tops", "bottoms") else "gear"
        if FOOD.search(ptype) or (FOOD.search(title) and not g and not re.search(r"apparel|clothing|shoe|footwear|v[êe]tement", ptype, re.I)):
            return "nutrition"
        return g or group_of(ptype) or group_of(tags)
    return g

# RunFree stores (Oct 6, 2026): read at night by scraper/runfree.py into runfree.json (kept on the history branch);
# the refresh downloads it to RUNFREE_FILE and each store comes in like a saved page (a store not read in 36 h keeps its last offers)
import runfree as RF
RUNFREE = [x[0] for x in RF.RUNFREE_STORES]
RUNFREE_US = [st for st in RUNFREE if st not in RF.CANADIAN]     # Runner's Soul (Lethbridge) is on RunFree too: Canada side
RUNFREE_FILE = os.environ.get("RUNFREE_FILE", "/tmp/runfree.json")
_RF = {}

def scrape_runfree(st):
    if "data" not in _RF:
        try:
            _RF["data"] = json.loads(Path(RUNFREE_FILE).read_text())
        except Exception as e:
            _RF["data"] = {"stores": {}, "error": str(e)[:80]}
    entry = _RF["data"].get("stores", {}).get(st)
    if not entry:
        raise RuntimeError("no RunFree night read yet" + (f" ({_RF['data'].get('error')})" if _RF["data"].get("error") else ""))
    t = dt.datetime.fromisoformat(entry["updated"])
    if dt.datetime.now(dt.timezone.utc) - t > dt.timedelta(hours=36):
        raise RuntimeError(f"RunFree night job last read it {t:%b %d}")
    ca = st in RF.CANADIAN
    fx = 1.0 if ca else fx_to_cad("USD")
    out = []
    for o in entry["offers"]:
        o = dict(o, ca=ca, us=not ca, lp=round(o["lp"] * fx, 2), sz=[[k, round(p * fx, 2), round(r * fx, 2)] for k, p, r in o["sz"]])
        out.append(o)
    return out 
US_SHOPS = {"pacers", "portlandrun", "heartbreak", "runnersplus", "gazelle", "sportsbasement", "tortoisehare",
            "runflagstaff", "runninglab", "playmakers", "millcity", "runningwell", "mountainrun", "confluence", "columbusrun",
            "scrantonrun", "trailheadrun", "prrunwalk", "performancerun", "fitnesssports", "athleticannex", "annarborrun",
            "tworivers", "xtramile", "lukeslocker", "sfrunco", "backcountry", "rei",
            "territory", "pathprojects", "ombraz", "2xuus"} | set(RUNFREE_US)   # REI ships within the US only
US_COLLECTIONS = {"sportsbasement": ["running"], "sail": ["outdoor-gear-running"], "humaca": ["nutrition"]}   # (Canadian stores too: SAIL)   # general stores: their running section only (Sports Basement also sells
                                                   # snowboards, swimwear, tennis: those topped the US deals, Oct 6, 2026)
# Shoebacca was tried and dropped (Oct 6, 2026): mostly PUMA/adidas/Diadora budget and gym shoes, no Hoka/Brooks/ASICS/Nike
SHIPS_US = set()       # Canadian stores that ship to the US, shown on the USA side too. Empty: Altitude Sports doesn't ship
                       # there (Bastien, Oct 6, 2026) and most Canadian shops don't; add one only after checking its shipping page
       # Canadian stores that also ship to the US (shown on the USA side too)

def make_shopify_scraper(st, base, kind):
    def run():
        # quick probe so a dead / blocked / non-Shopify store costs one request, not minutes of retries
        r = S.get(f"{base}/products.json?limit=1", timeout=20)
        if r.status_code != 200 or not r.text.lstrip().startswith("{"):
            raise RuntimeError(f"no Shopify product feed (HTTP {r.status_code})")
        home, ships = None, []                         # the store's own currency (meta.json) = where it ships from
        try:
            meta = get(f"{base}/meta.json", tries=2).json()
            home = (meta.get("currency") or "").upper() or None
            ships = meta.get("ships_to_countries") or []   # Oct 9: 2xu.com (Australia only), Darn Tough, Balega, Nathan (US only)
        except Exception:
            pass
        # always ask for the store's Canadian market: the price and stock a Canadian visitor actually gets
        # (otherwise the store guesses from GitHub's server location: Chilean pesos, or "not available here")
        cookies = None if st in US_SHOPS else CA_COOKIES    # US shops: their own (US) market
        served = shopify_price_currency(base, cookies)   # the currency the prices actually come back in
        home = home or served
        if not home:
            print(f"  ! {st}: currency unknown, assuming CAD", file=sys.stderr)
            home = "CAD"
        cur = served or home
        if st in US_COLLECTIONS:
            seen, prods = set(), []
            for h in US_COLLECTIONS[st]:
                for p in shopify_products(f"{base}/collections/{h}", max_pages=24, cookies=cookies):
                    if p["id"] not in seen:
                        seen.add(p["id"])
                        prods.append(p)
        else:
            prods = shopify_products(base, max_pages=24, cookies=cookies)
        fx = fx_to_cad(cur)
        print(f"  {st}: {len(prods)} products, store {home}, prices in {cur}" + (f" x{fx}" if cur != "CAD" else ""), file=sys.stderr)
        items = shopify_items(st, base, prods, generic_group(kind), fx=fx, size_aware=True, collapse=True,
                              size_fn=(lambda _l: "OS") if kind == "eyewear" else generic_size)
        for o in items:
            o["ca"] = home == "CAD"         # a store based in CAD ships from Canada; USD/EUR/GBP stores are cross-border
            o["us"] = home == "USD"         # ships from the US (the USA side's "Ships from the US")
            if ships and "*" not in ships:  # the store's own shipping list ("*" = everywhere) leaves a country out: not shown on that side
                o["no_ca"], o["no_us"] = "CA" not in ships, "US" not in ships
        if ships and "*" not in ships and ("CA" not in ships or "US" not in ships):
            print(f"  {st}: ships to {', '.join(ships[:6])}{'…' if len(ships) > 6 else ''} only" , file=sys.stderr)
        return items
    return run

STORES = {
    "altitude": lambda: scrape_commercetools("altitude", "https://www.altitude-sports.com"),
    "lasthunt": lambda: scrape_commercetools("lasthunt", "https://www.thelasthunt.com"),
    "thefeed": scrape_thefeed,
    "sea2sky": scrape_sea2sky,
    "sportinglife": scrape_sportinglife,
    "stampeak": scrape_stampeak,
    "mec": scrape_mec_saved,       # from pages you save (their sites block automated access)
    "rei": lambda: scrape_catalog("REI") or scrape_rei_saved(),   # the catalog file (Oct 9: every size, with stock), else saved pages
    "sportchek": lambda: scrape_catalog("Sport Chek"),    # from the catalog file Bastien brings (blocks automated reads)
    "adidasca": lambda: scrape_catalog("Adidas"),
    # "svp": scrape_svp_saved,   # parked Oct 6, 2026 (Bastien: its sale page is mostly soccer and budget shoes); reader kept
    "decathlon": lambda: scrape_decathlon_saved(),    # read at night, slowly (runfree.yml): Decathlon blocked GitHub's daytime reads
    # "backcountry": off (Oct 6): its bot protection answers GitHub's servers "202, empty"; reader kept for a feed
    "footlocker": scrape_footlocker,
}
# Final sale (Oct 4, 2026; read from each store's return policy, recheck now and then): 1 = every item is final sale,
# 2 = every item bought on sale is final, N > 2 = final from N% off. Items a store tags "Final sale" count too (offer "fs").
# The site labels a deal "Final sale" when the store and price shown match; no label never means "returnable".
FINAL_SALE = {"lasthunt": 1,
              "strides": 2, "aerobicsfirst": 2, "blacktoe": 2, "runnersshop": 2, "vanrunco": 2, "districtvision": 2,
              "fitfirst": 2, "endurance": 2, "cityparkrunners": 2, "capra": 2, "forerunners": 2, "tifosi": 2, "naak": 2,
              "xact": 2, "squirrels": 2,
              "lecoureur": 40, "janji": 40}
FINAL_TAG = re.compile(r"final.?sale|vente.?finale", re.I)

for _st, _base, _kind in SHOPIFY_STORES:
    STORES[_st] = make_shopify_scraper(_st, _base, _kind)
for _st in RUNFREE:
    STORES[_st] = (lambda st: lambda: scrape_runfree(st))(_st)

# Casual footwear some running stores also sell; not what people come here for.
CASUAL_BRANDS = {"ambler", "birkenstock", "wolky", "teva", "crocs", "ugg", "blundstone", "dr. martens", "clarks", "oofos", "billy footwear"}   # Ambler (Oct 8): toques, and its only "shoe" is a wool slipper
CASUAL_SHOE = re.compile(r"\b(sandal|sandale|clog|sabot|slipper|pantoufle|mule|flip[- ]flop|loafer|slide|clearwater cnx|recovery (flip|slide)|ora recovery)s?\b", re.I)
# court and lifestyle shoes from running brands (ASICS tennis/pickleball lines, retro sneakers)
COURT_SHOE = re.compile(r"pick[el]+ball|\btennis\b|\bpadel\b|\bcourt\b|gel[- ]?(resolution|dedicate|game|challenger|1130|nyc|kahana)|solution speed", re.I)
# lifestyle lines stores file under running (brand + model; Foot Locker, Oct 4, 2026)
LIFESTYLE_SHOE = re.compile(r"^(new balance\s+(740|2002r?|9060|530|1906r?)|on\s+(cloud\s?6|cloudtilt|cloudzone|cloud\s?5|cloudnova|roger)"
                            r"|salomon\s+xt-?(6|pathway|whisper|4|quest)|asics\s+gel-?(kayano\s?(14|20)|k1011)"
                            r"|nike\s+(zoom\s+)?vomero\s?5|hoka\s+speedgoat\s?2|adidas\s+(originals\b|ultraboost\s+1\.0|.*\bdna\b|adizero\s+goukana))\b", re.I)
# soccer boots (Frontrunners sells them): ground codes FG/AG/MG/SG/TF, or the model lines
GOALIE = re.compile(r"goal ?keep|\b(copa|pred|predator) gl\b|\bvapor grip\b|\bgk (dynamic|match|vapor)", re.I)
SOCCER = re.compile(r"\b(FG|AG|MG|SG|TF)\b|(?i:\b(soccer|futsal|predator|f50|copa|tiempo|mercurial)\b)")

def shoe_width_from_name(n, sx):
    """Widths many stores put in the product name: "Bondi 9 (2E)", "880v15 (D)", "Clifton 10 Wide".
    Returns "wide", "narrow" or "". Women's D is wide; men's D is the regular width."""
    low = n.lower()
    if re.search(r"\(\s*(2e|4e|6e|ee|eee|x-?wide|wide|extra wide)\s*\)|\b(x-?wide|extra wide|wide)\b|\blarge\b(?=.*\b(pied|chaussure)\b)|-\s*large\s*$|\(\s*large\s*\)", low):   # Québec stores: "Clifton 11 (Homme) - Large"
        return "wide"
    if re.search(r"\(\s*(2a|aa|4a|narrow|n)\s*\)|\bnarrow\b|\b[ée]troit", low):
        return "narrow"
    if re.search(r"\(\s*d\s*\)", low):
        women = "women" in (sx or []) and "men" not in (sx or [])
        return "wide" if women or re.search(r"\bwom[ae]n|\bfemme", low) else ""
    if re.search(r"\(\s*b\s*\)", low) and (re.search(r"(?<!wo)\bmen'?s?\b|\bhomme", low)):
        return "narrow"
    return ""

# Nutrition shops also sell flasks, bottles, tees and odds and ends; sort them properly.
NUT_FOOD = re.compile(r"\b(gels?|chews?|bars?|mix|powder|tablets?|capsules?|servings?|sachets?|shots?|fuel|drink|coffee|brew|"
                      r"protein|electrolytes?|recovery|oat(meal)?s?|power cups|brownie|muffin|flapjack|pre-?workout|sampler|"
                      r"creatine|collagen|caffeine|\d+\s*mg|\d+\s*ct|pack of)\b|\+\s*(free\s*)?(\d+x\s*)?(race day\s*)?(bottles?|shirt|hat)", re.I)
NUT_GEAR = re.compile(r"\b(soft ?flasks?|flasks?|bottles?|shakers?|race cup|musette|tote|grocery bag|boulder bag)\b", re.I)
NUT_CAMP_BRANDS = {"msr", "jetboil", "primus", "snow peak", "soto", "optimus", "esbit"}   # stove fuel, not runner fuel
NUT_WEAR = re.compile(r"\b(tee|t-?shirt|shirt|hoodie|crew ?neck|socks?|hat|trucker|beanie|toque|tuque|visor)\b", re.I)
NUT_DROP = re.compile(r"\b(stove|fuel pump|cann?ister|cooler|rental|vip box|gift ?card|subscription)\b", re.I)
# bike parts some fuel shops also sell (handlebar tape, chain lube, tubes); not running gear either
NUT_BIKE = re.compile(r"handlebar|bar ?tape|\bbartape\b|\bgrips?\b|chain (lube|wax)|\blube\b|\bsaddles?\b|"
                      r"inner ?tubes?|\btubeless\b|\b(tires?|tyres?)\b|\bcleats?\b|\bderailleur|\bcassette\b|\bbike\b|cycling", re.I)

def tidy_nutrition(offers):
    out = []
    for o in offers:
        if o["g"] == "nutrition":
            n = o["n"]
            if NUT_DROP.search(n) or NUT_BIKE.search(n) or (o["b"] or "").lower() in NUT_CAMP_BRANDS:
                continue
            if not NUT_FOOD.search(n):
                if NUT_GEAR.search(n):
                    o["g"] = "gear"
                elif NUT_WEAR.search(n):
                    o["g"] = ("headwear" if re.search(r"\b(hat|trucker|beanie|toque|tuque|visor)\b", n, re.I)
                              else "socks" if re.search(r"\bsocks?\b", n, re.I) else "tops")
        out.append(o)
    return out

# Clothing that stores file next to headlamps and bottles: compression sleeves, warmers, recovery tights, caps.
GEAR_LEG = re.compile(r"\b(calf|leg|compression|booster)\b.*\b(sleeves?|warmers?)\b|\b(leg|knee) warmers?\b|\bcalf (guards?|tubes?)\b|"
                      r"^booster elite", re.I)
SHOE_BRANDS = {"asics", "adidas", "hoka", "brooks", "salomon", "saucony", "new balance", "nike", "on", "on running", "altra", "mizuno",
               "puma", "la sportiva", "merrell", "topo", "topo athletic", "norda", "nnormal", "under armour", "inov-8", "scarpa"}
GEAR_SHOE = re.compile(r"\b(aero|ultra) glide\b|\bgrvl\b|\brunning shoes?\b|\btrail shoes?\b|souliers? de course", re.I)   # shoes a store filed as gear
GEAR_ARM = re.compile(r"\barm\b.*\b(sleeves?|warmers?|coolers?)\b|\b(sleeves?|warmers?)\b.*\barm\b", re.I)
GEAR_TIGHTS = re.compile(r"\b(tights?|leggings?|shorts)\b", re.I)
GEAR_CAP = re.compile(r"\b(?:go|trl|trk|crw|fst|alz|ss|gt)cap\b|\b(caps?|hats?|visors?|beanies?|toques?|tuques?)\b", re.I)

SHOE_SIZES = lambda o: o.get("sz") and all(re.match(r"^([MW]:)?\d{1,2}([.,][05])?$", str(e[0]).strip()) for e in o["sz"])

# Not food (Oct 7 audit: ~200 gloves, socks, caps, lights filed as nutrition, mostly by stores' own product types:
# Brainsport types Stance socks "Nutrition"; The Feed sells gear). Only when the name has no food word.
NOT_FOOD = re.compile(r"headlamp|\blights?\b|luminator|reflective|\btape\b|\btowel|\bbag\b|\bspikes?\b|traction|massage|\bball\b|"
                      r"flasques?|bidon|gourde|\bcup\b|soft ?flask|sleeves?\b|\bcover\b|sling|bite valve|\btube\b|sheaths?|reservoir", re.I)
CAMP_BRANDS = {"big agnes", "esbit"}
NOT_SOCK = re.compile(r"t-?shirt|\btee\b|hood|jacket|sweat|pullover|\btank\b|shorts?\b|pants?\b|tights?\b|sleeve|jogger|"
                      r"boxer|brief|underwear|legging|\btop\b|shirt|bralette|\bbra\b", re.I)
STRONG_FOOD = re.compile(r"\bgels?\b(?!-| pockets?| force| heel| cups?)|\bchews?\b|drink mix|electrolyte|energy bar|protein|stroopwafel|(?<!wool )waffle|"
                         r"caffeine|hydration mix|\bfuel\b(?! belt|\W+n\W*\s*fly|\s*cell)|\bbars?\b(?=.*\b(\d+ ?g|pack|box|bar)\b)|nut butter|honey|\bmix\b|tablets|capsules", re.I)
EYEWEAR_BRANDS = {"ombraz", "goodr", "sunski", "tifosi", "roka", "district vision", "julbo", "suncloud", "moana sunnies", "alpinamente", "knockaround"}
SOCK_BRANDS = {"darn tough", "balega", "feetures", "injinji", "swiftwick", "wigwam", "drymax", "rockay"}
CLOTH_SOCK_SHAPE = re.compile(r"\bcrew\b|no[- ]show|\bquarter\b|\bmicro\b|\bmini\b|\btab\b|over[- ]the[- ]calf|\botc\b|\bboot\b", re.I)
BYOB = re.compile(r"build your own bundle|\bbundle\d{3,}", re.I)
def tidy_food(offers):
    for o in offers:
        for e in o.get("sz") or []:
            if len(e) > 2 and e[1] and e[2] and e[2] > e[1] * 7:
                e[2] = e[1]            # "93% off": a store's typo in the regular price (Feetures socks "was $312.97"), not a deal
        o["n"] = re.sub(r"\s*\(needs description\)", "", o["n"], flags=re.I)   # a store's note to itself (Run Uphill)
        if BYOB.search(o["n"]) or re.fullmatch(r"(?=.*\d)[A-Z0-9-]{6,}", o["n"].strip()):   # a code, not a name ("MRCXLB4")
            o["g"] = "_drop"           # other shoppers' saved bundles ("Build Your Own Bundle · Bundle20740_2026-09-14T17:33")
            continue
        b = tidy_brand(o["b"]).lower()        # "Darn Tough Vermont" -> "darn tough"
        if b in CAMP_BRANDS:
            o["g"] = "_drop"           # tents, dry bags, stove fuel (The Trail Runner Store sells camping too)
            continue
        if b in EYEWEAR_BRANDS and o["g"] in ("nutrition", "tops", "bottoms") and not GEAR_CAP.search(o["n"]):
            o["g"] = "gear"            # goodr "Race to the Open Bar", "Three Parts Tee": sunglasses with funny names
            continue
        if b in SOCK_BRANDS and o["g"] in ("tops", "bottoms") and CLOTH_SOCK_SHAPE.search(o["n"]) \
                and not re.search(r"t-?shirt|\btee\b|hood|jacket|sweat|pullover|\btank\b|shorts?\b|pants?\b|tights?\b|sleeve", o["n"], re.I):
            o["g"] = "socks"           # Darn Tough "Lifestyle | Crew": a sock, not a crew-neck
            continue
        if o["g"] != "nutrition":
            continue
        if FOOD.search(o["n"]):
            g = group_of(o["n"])
            if g in ("tops", "bottoms", "bras", "headwear"):   # REI: Mammut "Aenergy" jacket; Ciele "TRKCap … /Bar"
                o["g"] = g
            continue
        g = group_of(o["n"]) or group_of(o["b"] or "")   # brand too: Buff, Body Glide
        if g:
            o["g"] = g
        elif NOT_FOOD.search(o["n"]):
            o["g"] = "gear"
    return offers

def tidy_gear(offers):
    offers = tidy_food(offers)
    for o in offers:
        # a shoe brand in numbered sizes filed by a word in its name: "Gel Kayano 33" (food), Merrell "Trail Glove 8" (gloves)
        if o["g"] in ("nutrition", "gloves") and (o["b"] or "").lower() in SHOE_BRANDS and SHOE_SIZES(o):
            o["g"] = "_drop" if COURT_SHOE.search(o["n"]) or CASUAL_SHOE.search(o["n"]) else "shoes"
            continue
        if o["g"] != "gear":
            continue
        n = o["n"]
        shoe_brand = (o["b"] or "").lower() in SHOE_BRANDS
        if (GEAR_SHOE.search(n) or shoe_brand) and o.get("sz") and all(re.match(r"^([MW]:)?\d{1,2}([.,][05])?$", str(e[0]).strip()) for e in o["sz"]):
            o["g"] = "shoes"           # numbered sizes too: a real shoe, not "shoe bag" or laces
        elif GEAR_ARM.search(n):
            o["g"] = "tops"            # arm sleeves / warmers: with tops, in the clothing size
        elif GEAR_LEG.search(n):
            o["g"] = "socks"           # calf sleeves / leg warmers: with socks (CEP, BV Sport sell them together)
        elif GEAR_TIGHTS.search(n):
            o["g"] = "bottoms"
        elif GEAR_CAP.search(n):
            o["g"] = "headwear"
    return [o for o in offers if o["g"] != "_drop"]

# Clothing that landed in the wrong category, and the type of each top / bottom (the site's "Jackets & vests" etc. buttons)
CLOTH_BRA = re.compile(r"\bsports? bra\b|\bbra\b|brassi[èe]re|(?-i:[A-Z]{2,}Bra\b)", re.I)   # Ciele "FSTBra"
CLOTH_CAPRI = re.compile(r"\bcapri\b", re.I)
CLOTH_NOT = re.compile(r"bottom bracket|eyejacket", re.I)          # bike parts, Oakley sunglasses
TYPES = {
    "tops": [("jacket", r"jacket|veste\b|manteau|\bcoat\b|parka|\bshell|anorak|wind ?breaker|coupe-vent|\bvest\b|gilet|puffer|"
                        r"insulat|\bdown\b|duvet|\brain\b|softshell|hardshell|bomber"),
             ("layer", r"hood|houdi|kangourou|\bzip\b|half[- ]?zip|1/2 ?zip|quarter[- ]?zip|1/4 ?zip|pullover|fleece|polaire|sweat|"
                       r"crew ?neck|mid[- ]?layer|midlayer|base ?layer|long[- ]?sleeve|long tee|\bl/?s\b|manches longues|thermal|layer one"),
             ("tee", r"tank|singlet|camisole|\bcami\b|d[ée]bardeur|crop|t-?shirt|\btee\b|\btech t\b|\bt\b|short[- ]?sleeve|\bs/?s\b|\bss\b|"
                     r"manches courtes|\btop\b|jersey|shirt|polo|sleeveless|\bcrew\b|go time|tunic")],
    "bottoms": [("short", r"short|cuissard|brief|culotte|skort|jupe|skirt|\d(\.\d)?\s*(\"|''|”|in\b|inch)|buns|splitty|speedsters|shredsters"),
                ("tight", r"tight|legging|collant|capri|7/8|3/4|leggy|base ?layer bottom"),
                ("pant", r"pant|pantalon|jogger|trouser|sweats|cargo|jeans")],
}
# shoes and gear: matched on "brand name" (trail brands, sunglasses brands); first match wins, "." = everything else
# Shoe types, the way runners shop (checked on the live catalogue Oct 2, 2026):
#   spike  track and cross-country spikes (Zoom Rival, XC7, EvoSPEED, Avanti, Ja Fly…)
#   hike   built for walking, hiking, snow and cold: hikers, mids, boots, winter shoes
#   trail  running shoes for dirt, rock and mud (lugs, rock plates), waterproof trail runners included
#   race   road racing / tempo shoes with a carbon (or similar) plate and race foam
#   daily  everything else: road shoes for everyday and long runs (cushioned, stability)
# Order matters (first match wins). Colour names are cut off first ("GT-2000 — Winter Sea" is not a winter shoe).
TYPES["shoes"] = [
    ("race", r"phantasm|s/lab pulsar|aero blaze"),      # Salomon's road racers ("S/Lab" otherwise means trail)
    # winter trail shoes with ice studs ("Speedgoat GTX Spike", "Norda G+ Spike") and "Norvan LD" (long distance) are trail
    ("trail", r"norvan|speedgoat.*spike|norda|\bg\+|carbide|cross spike|mtn racer|\bice\b"),
    ("spike", r"spikes?\b(?<!cross spike)|\bpointes?\b|\bxc\d*\b|\bm?xcs\d|\bwxcs|zoom rival|\bavanti\b|sprintstar|evospeed|"
              r"\bja fly|maxfly|dragonfly|\bvictory\b|\b[LMS]D(-X)?\b|metaspeed (ld|md|sp)|ambition|\bdistance (nitro|11)\b"),
    ("hike", r"\bhik(e|er|ing)\b|\bboots?\b|\bbottes?\b|\bmid\b|chelsea|\bpolar\b|winter|hiver|snow ?boot|"
             r"approach(?!.*trail running)|toundra|\bkaha\b|\bmoab\b|targhee|x ultra|genesis mid|renegade|nabucco|sawtooth|"
             r"crosscut|\bbogs\b|cloudsoma|\btransport\b|\bax4\b|trailmaker|kopec|eastrail"),
    ("trail", r"trail runn|\btrail\b|sentier|speedgoat|mafate|tecton|challenger|torrent|zinal|stinson|cascadia|caldera|catamount|"
              r"divide|peregrine|xodus|endorphin edge|olympus|lone peak|timp|mont blanc|speedcross|\bsense\b|s/lab|ultra glide|"
              r"genesis|xa pro|alphacross|wildcross|agility peak|long ?sky|hierro|supercomp trail|fuji|trabuco|venture|wildhorse|"
              r"kiger|zegama|ultrafly|ultra fly|cloudultra|cloudvista|cloudventure|tomir|kjerag|mutant|jackal|bushido|akasha|"
              r"prodigio|cyklon|daichi|mujin|ibuki|xt-6|grvl|experience wild|nordlite|seek|\btr\d|amplux|madrix|fortux|katabatic|"
              r"\bla sportiva\b|nnormal|scarpa|inov-?8|\bvj\b|dynafit|norda|icebug|merrell|\blowa\b|\boboz\b|\bkeen\b|"
              r"agravic|vectiv|offtrail|thundercross|cloudsurfer ?trail|mountain racer|exp wild"),   # Oct 7 audit
    ("race", r"alphafly|vaporfly|adios pro|adizero pro|prime x|takumi|metaspeed|endorphin (pro|elite|speed)|rocket x|cielo x|"
             r"cielo rd|super ?comp (elite|pacer|trainer)|magic speed|\bsc (elite|pacer|trainer)\b|deviate nitro|fast-r|hyperion (elite|max)|"
             r"cloudboom|wave rebellion|carbon|metaracer|rc elite|streakfly|adizero boston|velociti elite|racing|racer|"
             r"zoomx|supercomp rebel"),
    ("daily", r"."),
]
TYPES["gear"] = [
    ("sun", r"sunglass|lunettes?|glasses|eyewear|\blens(es)?\b|goggle|nose pad|sunnies|\bgoodr\b|\broka\b|sunski|tifosi|oakley|"
            r"district vision|\bjulbo\b|\bsmith\b|pit viper|ombraz|knockaround|wildwood"),
    ("light", r"head ?lamp|frontale|\blamp|lampe|\blights?\b|beacon|torch|flashlight|lumens?"),
    ("pole", r"\bpoles?\b|bâtons?|\bbatons?\b|trekking|z-pole"),
    ("bottle", r"bottle|flask|gourde|bidon|reservoir|réservoir|bladder|hydration|hydratation|\bcup\b|filter|filtre|handheld|hydrapak"),
]
TYPES = {g: [(k, re.compile(rx, re.I)) for k, rx in v] for g, v in TYPES.items()}

CLOTH_SOCK = re.compile(r"\bsocks?\b|\bchaussettes?\b|mini crew|micro crew|mid crew|crew height|no[- ]show|over[- ]the[- ]calf|cushion\b.*\bcrew\b", re.I)

CLOTH_TOPW = re.compile(r"short[- ]?sleeve|long[- ]?sleeve|arm (sleeve|warmer)s?|t-?shirt|\btee\b|\bshirt|singlet|\btank\b|hood(ie|y)?\b|jacket|"
                        r"pullover|\bcrew\b|1/4 zip|half zip|quarter zip|\btop\b|\bvest\b", re.I)
CLOTH_BOTW = re.compile(r"\bshorts?\b(?![- ]?sleeve)|tights?\b|leggings?|\bpants?\b|joggers?|skirt|skort|capri|bottoms?\b|"
                        r"\bbriefs?\b|boxers?|\bset\b|half tight|split", re.I)
CLOTH_STRONG = re.compile(r"\bjacket|\bpants\b|singlet|\bt-?shirt|\btee\b|\bshorts\b|\btights\b|leggings|hoodie|\btank top", re.I)
CLOTH_GEAR_OK = re.compile(r"sunglass|lens|eye ?jacket|suture|bottle|flask|belt|\bpack\b|backpack|vest pack|holder|hanger|patch|"
                           r"\bwash|detergent|gift|bundle|strap|clip|towel", re.I)
def tidy_clothes(offers):
    out = []
    for o in offers:
        n = o["n"]
        if o["g"] in ("tops", "bottoms") and CLOTH_NOT.search(n):
            continue
        if o["g"] == "tops" and CLOTH_BRA.search(n) and not re.search(r"tank|cami|top\b", n, re.I):
            o["g"] = "bras"
        elif o["g"] == "tops" and CLOTH_CAPRI.search(n):
            o["g"] = "bottoms"
        if o["g"] in ("tops", "gear", "headwear") and CLOTH_SOCK.search(n):
            o["g"] = "socks"           # "Run Zero Cushion Mid Crew Height", "Chaussettes Hike…": a crew sock, not a crew-neck top
        if o["g"] in ("tops", "bottoms") and re.search(r"\blens(es)?\b|sunglass", n, re.I):
            o["g"] = "gear"            # MEC files spare sunglass lenses under clothing ("Equinox Lens")
        # tops and bottoms swapped by a store's category (Oct 7 audit: "Dash Short Sleeve" under bottoms at US shops,
        # "D4T Shorts" under tops at The Last Hunt): only when the name says one and not the other
        if o["g"] in ("packs", "gear", "nutrition") and CLOTH_STRONG.search(n) and not CLOTH_GEAR_OK.search(n):
            o["g"] = "bottoms" if CLOTH_BOTW.search(n) and not CLOTH_TOPW.search(n) else "tops"   # "Torrentshell 3L Jacket", Janji "Pinnacle Tee"
        if o["g"] == "socks" and re.search(r"\btights?\b|\bshorts?\b(?![- ]?sleeve)|leggings?|\bpants?\b", n, re.I) \
                and not re.search(r"\bsocks?\b|chaussettes", n, re.I):
            o["g"] = "bottoms"         # Bandit "Quarter Tights" read as quarter-height socks
        if o["g"] == "bottoms" and CLOTH_TOPW.search(n) and not CLOTH_BOTW.search(n):
            o["g"] = "tops"
        elif o["g"] == "tops" and CLOTH_BOTW.search(n) and not CLOTH_TOPW.search(n):
            o["g"] = "bottoms"
        out.append(o)
    return out

def garment_type(g, n):
    """tops: tee / layer / jacket; bottoms: short / tight / pant; shoes: hike / trail / race / daily;
    gear: sun / light / pole / bottle; None when the name doesn't say (shown under "All" only)."""
    if g == "shoes":
        n = re.split(r"\s+[—·]\s+", n)[0]       # "Women's GT-2000 14 — Winter Sea/White": the colour isn't the shoe
        if re.search(r"trail runn", n, re.I) and not re.search(r"\b(hik(e|er|ing)|mid|boots?|winter)\b", n, re.I):
            return "trail"                       # "Lowa Amplux Trail Running Shoes": a trail runner from a hiking brand
    for k, rx in TYPES.get(g, []):
        if rx.search(n):
            return k
    return None

# Kids' gear: a kids' 11 or "M" would match an adult's size. The site is for adults, so leave it out.
KIDS = re.compile(r"\b(kids?|kid'?s|kids'|juniors?'?|jr|youth|enfants?|gar[çc]ons?|filles?|boys?|girls?|toddlers?|infants?|"
                  r"b[ée]b[ée]s?|big kids?|little kids?|grade school|pre-?school|pr[ée]scolaire|jeunesse|children'?s?)\b", re.I)
KIDS_SHOE = re.compile(r"\b(GS|PS|TD)\b|\s(J|Y|K)$")      # grade school / preschool / toddler codes; "… FG J" (junior)
ADULT_STYLE = re.compile(r"\bboy ?shorts?\b|\bboyfriend\b", re.I)  # women's underwear and fits, not kids

def drop_kids(offers):
    out = []
    for o in offers:
        n = f"{o['b']} {o['n']}"
        if (KIDS.search(n) and not ADULT_STYLE.search(n)) or (o["g"] == "shoes" and KIDS_SHOE.search(o["n"])):
            continue
        out.append(o)
    return out

US_CASUAL_BRANDS = {"sorel", "olukai", "k-swiss", "smellwell", "dryshod", "vans", "converse", "sperry", "keen"}
US_LIFESTYLE_BRANDS = {"beyond yoga", "fp movement", "free people", "nux", "rvca", "roark", "travismathew", "sunsets", "forum snowboards"}
US_CASUAL = re.compile(r"\b(sneaker|leather|boot|slip-?on)s?\b", re.I)
US_CAPS_STORES = {"runningwell", "performancerun"} | set(RUNFREE_US)     # US shops that write everything in capitals
US_WIDTH = re.compile(r"\s+-\s+[^-]+?\s+-\s+(Regular|Medium|Standard|Wide|Extra Wide|X-?Wide|Narrow)\s*\(\s*[A-Z0-9]+\s*\)", re.I)
STYLE_CODE = re.compile(r"\s+((?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{7,}|\d{6,})(?=$|\s+-\s)")

def tidy_us_names(offers):
    """US running shops' ways of writing a shoe (Oct 6, 2026), brought to the usual "Model - Men's" so the same shoe at
    several shops becomes one card: "Hoka | Arahi 9 | Women's" (Confluence), "Clifton 10 Running Shoe - Black/White -
    Regular (D) - Men's" (Gazelle: one listing per colour and width), "Arahi 9 Women's Shoes" (Heartbreak Hill),
    "Ghost 17 (Extra Wide - 4E)", "MEN'S PEGASUS 41 XWIDE", "M Ghost Max 1104951D" (a style code)."""
    out = []
    for o in offers:
        if o["g"] == "shoes" and " | " not in o["n"]:   # any store: "Terrex Agravic 3 Men's", "Adistar 4 Men's shoes" -> "... - Men's"
            o["n"] = re.sub(r"(\s+-)?\s+(Men|Women)[’']?s(\s+(running\s+)?shoes?)?$", lambda m: f" - {m.group(2).capitalize()}'s", o["n"], flags=re.I)
        if o.get("st") not in US_SHOPS:
            out.append(o)
            continue
        n = o["n"]
        if o.get("st") in US_CAPS_STORES and n == n.upper():
            n = soften_caps(n)
            if re.fullmatch(r"[A-Z][A-Z .'&-]{2,}", o["b"] or ""):
                o["b"] = o["b"].title()
        if " | " in n:
            parts = [x.strip() for x in n.split("|") if x.strip()]
            gen = next((x for x in parts if re.fullmatch(r"(men|women|unisex)[’']?s?", x, re.I)), None)
            bnames = {(o["b"] or "").lower(), tidy_brand(o["b"]).lower(), ((o["b"] or "").split() or [""])[0].lower()}   # "Hoka" for "Hoka One One"
            rest = [x for x in parts if x is not gen and x.lower() not in bnames and "/" not in x]
            gw = (gen or "").lower()
            n = (rest[0] if rest else parts[0]) + (" - Women's" if gw.startswith("wom") else " - Men's" if gw.startswith("men") else "")
        n = n.replace(" – ", " - ")
        if (o["b"] or "").lower() in US_LIFESTYLE_BRANDS:
            continue                              # yoga and fashion labels general stores file under running (US shops)
        if re.sub(r"\s*-\s*(men|women)[’']?s$|\W", "", n.lower()) in ("", re.sub(r"\W", "", (o["b"] or "").lower())):
            continue                              # a listing named only after its brand ("Hoka | Hoka | Women's")
        if o["g"] == "shoes" and ((o["b"] or "").lower() in US_CASUAL_BRANDS or US_CASUAL.search(n)):
            continue                              # general shoe stores: boots, sneakers, leather (US shops only)
        if o["g"] == "shoes":
            n = re.sub(r"\s+-\s+Size\s+[\d.]+", "", n, flags=re.I)                    # one listing per size
            segs = n.split(" - ")
            keep = [segs[0]]
            for x in segs[1:]:                    # " - D -", " - X-Wide 2E -", " - WIDE 1162032 -", " - Black/White -"
                xl = re.sub(r"[()]", "", x).strip().lower()
                if re.fullmatch(r"(men|women)[’']?s|unisex", xl):
                    keep.append(x)
                elif re.fullmatch(r"(x-?wide|extra wide|wide)\s*(2e|4e|6e|ee|d|w)?(\s+\d{5,})?|(2e|4e|6e|ee)(\s+\d{5,})?", xl):
                    o["w"] = True
                elif re.fullmatch(r"(narrow|2a|aa|n)", xl):
                    keep = None
                    break
                elif re.fullmatch(r"(regular|medium|standard)?\s*(b|d|m)?(\s+\d{5,})?", xl) and xl or "/" in x:
                    pass
                else:
                    keep.append(x)
            if keep is None:
                continue
            n = " - ".join(keep)
            m = US_WIDTH.search(n)
            if m:
                w = m.group(1).lower()
                n = n[:m.start()] + n[m.end():]
                if w == "narrow":
                    continue
                if "wide" in w:
                    o["w"] = True
            m = re.search(r"\s*\((extra |x-?)?wide\b[^)]*\)|\s+(x-?wide|extra wide)$", n, re.I)
            if m:
                n = n[:m.start()] + n[m.end():]
                o["w"] = True
            n = re.sub(r"\b(Men|Women)[’']?s Shoes$", lambda x: f"- {x.group(1)}'s", n).replace("  ", " ")
            n = STYLE_CODE.sub("", n)
            if re.search(r"\b(x-?wide|extra wide)\b|\bwide\b", n, re.I) and not o.get("w"):
                o["w"] = True
                n = re.sub(r"\s*\b(x-?wide|extra wide|wide)\b", "", n, flags=re.I)
        o["n"] = re.sub(r"\s+-\s*-\s+", " - ", n).strip()
        out.append(o)
    return out

BIKE_SHOE_BRANDS = {"leatt", "five ten", "shimano", "giro", "fizik", "northwave", "sidi", "ride concepts", "crankbrothers"}   # clip-in/MTB shoes (Oct 7)
SHOE_CARE = re.compile(r"\blaces?\b|\blacets?\b|quicklace|cleaner|cleaning|repel|deodou?ri[sz]er|\bwipes\b|spike wrench|"
                       r"\bspray\b|\bpackage\b.*spikes|\bshoe ?(bag|tree|horn)\b|\binsoles?\b|quick-?clip|"
                       r"replacement spikes|\d+ count\b|roll-?on|foot shield|installation", re.I)
def tidy_shoes(offers):
    """Drop casual footwear and narrow-only shoes; mark wide ones from the product name."""
    out = []
    for o in offers:
        if o["g"] == "shoes" and SHOE_CARE.search(o["n"]) and not re.search(r"running shoes?|\bshoes?$", o["n"], re.I):
            o["g"] = "gear"            # laces, cleaners, sprays, spike wrenches: shoe things, not shoes (Oct 7 audit)
        if o["g"] == "shoes":
            if (o["b"] or "").lower() in CASUAL_BRANDS or (o["b"] or "").lower() in BIKE_SHOE_BRANDS or CASUAL_SHOE.search(o["n"]) or SOCCER.search(o["n"]) or COURT_SHOE.search(o["n"]) \
                    or LIFESTYLE_SHOE.search(f'{o["b"]} {o["n"]}'):
                continue
            w = shoe_width_from_name(o["n"], name_gender(o["n"]) or o.get("sx"))
            if w == "narrow":
                continue
            if w == "wide":
                o["w"] = True
                o["n"] = re.sub(r"\s*-\s*large\s*$|\s*\(\s*large\s*\)", "", o["n"], flags=re.I)   # the wide flag says it
        out.append(o)
    return out

# ---------------------------------------------------------------- tidy names and accessory sizes (site, email and alerts all use these)
BRAND_PREFER = {"ASICS", "GU", "On", "Topo Athletic", "Craft", "CEP", "Injinji", "LEKI", "adidas", "rabbit", "norda", "Arc'teryx", "The North Face", "Squirrel's Nut Butter", "New Balance", "Nathan", "Inov-8", "Ketone-IQ",
                "SaltStick", "Precision Fuel & Hydration", "Tailwind", "Xact Nutrition", "goodr", "Dæhlie", "Feetures", "Body Glide",
                "Naked", "Ciele", "SPIbelt", "Trigger Point", "Pro-Tec Athletics", "DexShell", "NiteVest", "Oboz"}
BRAND_CANON = {"hoka one one": "Hoka", "hoka": "Hoka", "asics": "ASICS", "satisfy": "Satisfy", "oiselle": "Oiselle",
               "nnormal": "NNormal", "new balance": "New Balance", "on running": "On", "the north face": "The North Face",
               "karitraa": "Kari Traa", "kari traa": "Kari Traa", "naak": "Näak", "näak": "Näak", "näak na": "Näak",
               "diadora": "Diadora"}

# US shops often list the parent company or distributor as the vendor (Oct 6, 2026: "Asics Corp." on all 480 US ASICS items,
# "Brooks Sports, Inc. #105856", "Ing Source, Inc" = Injinji, "Medi USA" = CEP): company words go, then this map
BRAND_ALIAS = {"balmoral sports": "Balmoral", "inner self": "Inner Self", "krono nutrition": "Krono", "kronobar": "Krono", "grynd food": "Grynd", "grynd food inc": "Grynd", "fast bundle": "Upika", "upika": "Upika", "brix rechargé par la nature": "Brix", "brix recharge par la nature": "Brix", "asics america": "ASICS", "asics": "ASICS", "brooks sports": "Brooks", "nike usa": "Nike", "nike team sale": "Nike",
               "on shoes": "On", "on footwear": "On", "on-running": "On", "gu energy": "GU", "gu energy labs": "GU", "gu sports": "GU",
               "gu nutrition": "GU", "gu energy gel": "GU", "ing source": "Injinji", "medi usa": "CEP", "medi": "CEP",
               "cep / medi usa": "CEP", "cep/medi usa": "CEP", "medi usa (cep)": "CEP", "medi/cep": "CEP", "medi usa - cep": "CEP", "craft sportswear": "Craft", "craft sportsware usa": "Craft",
               "craft sportsware": "Craft", "topo": "Topo Athletic", "drymax tech": "Drymax", "gofluo": "GoFluo", "handful": "Handful",
               "superfeet worldwide": "Superfeet", "anita international": "Anita", "surefoot": "Surefoot", "ifitness": "iFitness",
               "mizuno usa": "Mizuno", "leki usa": "LEKI", "buff usa": "Buff", "sidas usa": "Sidas", "haix usa": "HAIX",
               "tailwind nutrition": "Tailwind", "xact nutrition": "Xact Nutrition", "xact": "Xact Nutrition", "xact electrolytes": "Xact Nutrition", "krono nutrition": "Krono", "podium nutrition": "Podium",
               "neversecond nutrition": "Neversecond", "noogs nutrition": "Noogs", "spring sports nutrition": "Spring",
               "wigwam socks": "Wigwam", "strassburg sock": "Strassburg", "saucony socks": "Saucony", "feetures socks": "Feetures",
               "balega sports - socks": "Balega", "pillar performance": "Pillar", "trigger point performance": "Trigger Point",
               "junk brand": "JUNK", "blacktoe running": "BlackToe", "send it gear": "Send It Gear",
               "i-blu": "District Vision", "nakanishi optical products": "District Vision",
               # Oct 7 audit: one brand split across cards
               "precision": "Precision Fuel & Hydration", "precision fuel": "Precision Fuel & Hydration",
               "precision fuel and hydration": "Precision Fuel & Hydration", "precision fuel & hydratation": "Precision Fuel & Hydration",
               "precision fuel & hyrdration": "Precision Fuel & Hydration", "darn tough vermont": "Darn Tough",
               "daehlie": "Dæhlie", "dæhlie": "Dæhlie", "bjorn daehlie": "Dæhlie", "bjørn dæhlie": "Dæhlie", "b daehlie": "Dæhlie",
               "topo athletics": "Topo Athletic", "suncloud optics": "Suncloud", "tifosi optics": "Tifosi", "science in sport (sis)": "Science in Sport",
               "sis": "Science in Sport", "fjallraven": "Fjällräven", "norrona": "Norrøna", "hüma": "Huma", "huma gel": "Huma",
               "instinct": "Instinct Trail", "life sport": "Life Sports Gear", "life sports": "Life Sports Gear", "strassburg medical": "Strassburg",
               "columbia titanium": "Columbia", "stance us": "Stance", "balega us": "Balega", "2xu outlet": "2XU", "roka outlet": "ROKA",
               "roka custom": "ROKA", "goodr sunglasses": "goodr", "nb": "New Balance", "h.koumori": "Hermanos Koumori",
               "clif bar": "Clif", "nuun hydration": "Nuun", "currex insoles": "Currex", "cep compression": "CEP",
               "spenco medical products": "Spenco", "strides running store": "Strides", "glide + seek": "Glide and Seek",
               "raide": "Raide Research", "moana": "Moana Sunnies", "buffs": "Buff", "hammer": "Hammer Nutrition",
               "kinesys performance sunscreen": "Kinesys", "altra zero drop footwear": "Altra", "adidas terrex": "adidas",
               "puma north a": "Puma", "smith optics": "Smith", "lé bent": "Le Bent", "naak nutrition": "Näak", "smith sport optics": "Smith", "diadora us": "Diadora", "maurten us": "Maurten",
               "nathan hydration": "Nathan", "zym hydration": "ZYM", "puma north america": "Puma", "spenco medical": "Spenco", "precision fuel & hydration": "Precision Fuel & Hydration"}   # District Vision's makers

DISTRIBUTORS = {"back river sport", "back river group", "territory run co", "territory run co."}   # Territory resells Tailwind, Hydrapak
def tidy_brand(b):
    b = (b or "").strip()
    if b.lower() in BRAND_CANON:
        return BRAND_CANON[b.lower()]
    c = re.sub(r"\s*#\d+\s*$", "", b)                                                    # "#105856"
    c = re.sub(r"\s+-\s+((SS|FW)\d\d|archive|collab)$", "", c, flags=re.I)                 # "Janji - SS25", "SATISFY - Archive"
    c = re.sub(r",?\s*\b(inc|incorporated|corp|corporation|llc|ltd|l\.?\s?p)\b\.?", "", c, flags=re.I).strip(" ,.-")
    k = re.sub(r"\s+", " ", c.lower().replace(",", "")).strip()
    if k in BRAND_ALIAS:
        return BRAND_ALIAS[k]
    if k in BRAND_CANON:
        return BRAND_CANON[k]
    r = re.sub(r"(?<=\w)\s+(canada|ca|us|usa|united states)?(\s*outlet)?$", "", c, flags=re.I)   # a brand's regional store (Oct 9):
    if r and r != c:                                                                               # "2XU Canada Outlet", "Balega Ca"
        return tidy_brand(r)
    return c or b

CAPS_STORES = {"lecoureur", "runnerssoul"}
OWN_BRAND = {"rabbit": "rabbit", "bandit": "Bandit Running"}
GENDER_PREFIX_STORES = {"frontrunners",    # names start with "M " / "W " / "U " ("M Adidas Boston 13")
                        "aerobicsfirst",   # "Saucony Women's Endorphin Speed 5 - White/Black *SALE*"
                        "cityparkrunners", # "Women's Saucony Peregrine 14", "Mens Altra Outroad"
                        "sportinglife",    # "Men's Velociti 4 Running Shoe"
                        "runningwell", "performancerun", "scrantonrun"}   # US: "BROOKS WOMEN'S HYPERION MAX 4", "UNISEX SLOWCUSH - ORANGE/RED", "M Ghost Max"
GENDER_PREFIX = {"M": ["men"], "W": ["women"], "U": ["men", "women"]}    # stores that write brands and names in capitals ("ADIDAS ADIOS PRO 4 - FEMME")

# short words that read as words, not model codes, when an ALL-CAPS name is softened ("RUN", "MID" vs "GTX", "SP")
SOFT = {"and", "the", "for", "with", "de", "et", "en", "in", "mid", "low", "run", "pro", "one", "max", "air", "gel", "sky",
        "top", "tee", "bra", "hat", "cap", "sun", "day", "all", "new", "men", "fit", "pant", "les", "la", "le", "du", "sur"}

def soften_caps(n):
    """"ADIZERO ADIOS PRO 4 - FEMME" -> "Adizero Adios Pro 4 - Femme"; model codes (GTX, AX4, SP) stay in capitals."""
    def part(w):
        if not w.isalpha():
            return w
        return w.capitalize() if len(w) >= 4 or w.lower() in SOFT else w
    return " ".join("-".join(part(x) for x in word.split("-")) for word in n.split(" "))

def tidy_name(b, n):
    """"Hoka - Cielo X 2 LD - Unisexe" -> "Cielo X 2 LD - Unisex": no repeated brand, gender words in English."""
    n = re.sub(r"\s+", " ", n or "").strip()
    n = re.sub(r"\bHommes?\b", "Men's", n)
    n = re.sub(r"\bFemmes?\b", "Women's", n)
    n = re.sub(r"\bUnisexe\b", "Unisex", n)
    n = re.sub(r"\b(Wom|M)en[’`´]s\b", r"\1en's", n)                                  # curly apostrophe
    n = re.sub(r"\s*\((Men's|Women's|Unisex)\)\s*$", r" - \1", n)                  # "Neo Vista (Men's)" -> "Neo Vista - Men's"
    first = b.split(" ")[0] if b else ""
    toks = {b} | ({first} if len(first) >= 4 and first.lower() not in {"black", "blue", "north", "mountain", "outdoor"} else set())
    if b.lower() == "hoka":
        toks |= {"Hoka One One", "Hoka"}
    for tok in sorted(toks if b else set(), key=len, reverse=True):
        if not tok:
            continue
        m = re.match(re.escape(tok) + r"(?![A-Za-z0-9])\s*[®™]?\s*[-–:|·]?\s*", n, re.I)   # "Naked® Vest", "=PR= Short", "Rip van Wafel · Honey"
        if m and len(n) - m.end() >= 3:
            n = n[m.end():]
            break
    n = re.sub(r"^[®™·*,+\s]+", "", n)                     # "® Drink Tube Kit": a symbol left behind by the brand
    return n[:1].upper() + n[1:] if n else n

ACC_OS = {"", "OS", "OSFA", "OSFM", "ONE SIZE", "O/S", "STANDARD", "DEFAULT TITLE", "NA", "N/A", "UNIQUE", "TAILLE UNIQUE"}
ACC_WORD = [("EXTRA EXTRA LARGE", "2XL"), ("EXTRA EXTRA SMALL", "2XS"), ("EXTRA LARGE", "XL"), ("EXTRA SMALL", "XS"),
            ("XX-LARGE", "2XL"), ("X-LARGE", "XL"), ("X-SMALL", "XS"), ("SMALL", "S"), ("MEDIUM", "M"), ("LARGE", "L"),
            ("XXXL", "3XL"), ("XXL", "2XL"), ("XXS", "2XS")]
ACC_LETTERS = {"2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL"}

def acc_sizes(label):
    """Vests, belts, lights etc.: letter sizes -> ["M", "L"]; colours and volumes -> ["OS"]; anything else kept as is."""
    t = re.sub(r"\(.*?\)", "", str(label or "")).strip().upper()
    for a, b in ACC_WORD:
        t = re.sub(r"\b" + re.escape(a) + r"\b", b, t)
    if t in ACC_OS or re.match(r"^\d+(\.\d+)?\s*(OZ|ML|L|LITRE|LITER|LITRES|LITERS)\b", t):
        return ["OS"]
    parts = [x for x in re.split(r"\s*[/|]\s*|\s+-\s+|(?<=[SMLX])-(?=[SMLX2])|\s+", t) if x]
    if parts and all(x in ACC_LETTERS for x in parts):
        return list(dict.fromkeys(parts))
    if {"SM": ["S", "M"], "ML": ["M", "L"], "LXL": ["L", "XL"]}.get(t):
        return {"SM": ["S", "M"], "ML": ["M", "L"], "LXL": ["L", "XL"]}[t]
    if not re.search(r"\d", t):                     # "BLACK", "BLACK/REFLECTIVE SILVER": a colour, not a size
        return ["OS"]
    return [str(label).strip()]

def tag_gender(p):
    """A Shopify product's gender from the store's own tags/product type ("Gender: Womens", "mens", "Women's Apparel"),
    used when the name says nothing. Only when exactly one gender appears (many shops tag unisex items with both)."""
    txt = " ".join([t for t in p.get("tags") or [] if re.search(r"gender|wom[ae]n|\bmen|ladies|female|\bmale|femme|homme", t, re.I)]
                   + [p.get("product_type") or ""]).lower()
    if "unisex" in txt:
        return []
    w = bool(re.search(r"wom[ae]n|ladies|female|femme", txt))
    m = bool(re.search(r"(?<!wo)\bmen|\bmale|\bhomme", txt))
    return ["women"] if w and not m else ["men"] if m and not w else []

# Clothing whose name or brand only fits women, when neither the name nor the store says (Oct 6: a men's runner saw
# skirts, skorts, bras and high-rise leggings, 1 in 5 clothing items had no gender and showed to everyone).
WOMEN_ONLY = re.compile(r"\b(skirts?|skorts?|dress|sports? bra|bra|bralette|hi(gh)?[- ]rise|capris?|leggings?|prenatal|maternity|jupes?|soutien-gorge)\b", re.I)
WOMEN_BRANDS = {"oiselle", "girlfriend collective", "lululemon"}
MEN_BRANDS = {"ten thousand", "tenthousand"}

def clothing_gender(o):
    if o["g"] == "bras":
        return ["women"]
    if o["g"] not in ("tops", "bottoms"):
        return []
    b = (o.get("b") or "").lower()
    if re.search(r"\bunisex\b", o["n"], re.I):
        return []
    if b in WOMEN_BRANDS or WOMEN_ONLY.search(o["n"]):
        return ["women"]
    if b in MEN_BRANDS:
        return ["men"]
    return []

def name_gender(n):
    """Product names ("... - Women's", "Mens Pressio Tee") beat a store's gender tag, which is
    often "unisex" for women's-cut gear."""
    low = n.lower()
    w = bool(re.search(r"\bwom[ae]n'?s?\b|\bfemmes?\b", low))
    m = bool(re.search(r"(?<!wo)\bmen'?s?\b|\bhommes?\b", low))
    return ["women"] if w and not m else ["men"] if m and not w else None

# Stores that sell and ship from Canada (no border fees). Generic Shopify stores decide by their currency.
CA_STORES = {"altitude", "lasthunt", "sea2sky", "sportinglife", "stampeak", "mec", "decathlon", "svp", "footlocker", "sportchek", "adidasca"}

_TRAIL_MODELS = set()    # shoe keys that keep "trail"/"road" because a store names the model that way ("Ghost Trail - Men's")

def _shoe_name(o, keep_tr):
    g = re.search(r"\s-\s*(men's|women's|unisex)$", o["n"].lower())
    name = re.sub(r"[^a-z0-9]+", " ", (re.split(r"\s+[—·]\s+", o["n"])[0] + (" " + g.group(1) if g and " — " in o["n"] else "")).lower()).strip()
    # "Triumph 23 Running Shoe - Women's" (Sporting Life) = "Triumph 23 Running Shoes - Women's" (Last Hunt) =
    # "Speedgoat 7 GTX Trail Running [Wide]"; but "Ghost Trail Running Shoes" (Altitude) = "Ghost Trail" (a model, not
    # Brooks' road Ghost): the trail/road word stays when another store's name for the model has it (_TRAIL_MODELS)
    tr = r"\brunning( road| trail)?( shoes?)?\b|\bshoes?\b" if keep_tr else r"\b((trail|road) )?running( road| trail)?( shoes?)?\b|\bshoes?\b"
    name = re.sub(r"\bgore ?tex\b", "gtx", name)                     # "Ghost 18 Gore-Tex" = "Ghost 18 GTX"
    name = re.sub(r"\b(available in wide widths?|waterproof)\b", " ", name) if "gtx" in name or "available" in name else name
    name = re.sub(r"\b((trail|road) )?racing( shoes?)?\b", " ", name)    # "Zoom Fly 6 Racing Shoe" = "Zoom Fly 6 Road Racing Shoes"
    name = re.sub(tr, " ", name)
    name = re.sub(r"\bunisex\b", " ", name)                   # "Metaspeed Ray" = "Metaspeed Ray - Unisex" (no gender either way)
    if o["b"].lower().strip() == "nike":
        name = re.sub(r"^\s*(nike\s+)?air zoom\s+", "", name)       # "Air Zoom Pegasus 41" = "Pegasus 41"
    if o["b"].lower().strip() == "adidas":
        name = re.sub(r"^\s*adizero\s+", "", name)            # "Evo SL - Men's" (Endurance) = "Adizero EVO SL" (Altitude)
    name = re.sub(r"\s+", " ", name).strip()
    if o["w"]:   # width words go too ("(2E)", "Wide"): the wide flag already keeps wide and regular apart
        name = re.sub(r"\s+", " ", re.sub(r"\b(x ?wide|extra wide|wide|2e|4e|ee|d)\b", " ", name)).strip()
    return name

def mkey(o):
    name = re.sub(r"[^a-z0-9]+", " ", o["n"].lower()).strip()
    if o["g"] == "shoes":      # "GT-2000 15 — Black/White - Men's" (Fit First lists each colour) = "GT-2000 15 - Men's"
        keep = _shoe_name(o, True)
        name = keep if (o["b"].lower().strip(), keep) in _TRAIL_MODELS else _shoe_name(o, False)
    # Canadian and cross-border offers stay separate, so "Canadian stores only" never hides a cheaper US price inside a card
    return (o["b"].lower().strip(), name, o["w"], o["g"], bool(o.get("ca")))

def merge(offers):
    """Same product at several stores -> one item; each size keeps the cheapest store."""
    for o in offers:
        if (o["b"] or "").strip().lower() in ("not specified", "n/a", "none", "unknown", "default"):   # Brainsport leaves some blank
            m = re.match(r"^(?:(?:Men|Women|Kid)[’']?s\s+)?(\S+)", o["n"])
            o["b"] = m.group(1) if m else ""
        # Oct 6: "*FINAL SALE* Race Vest 6.0" (Mountain Running Co.), "(M) Saucony Velocity MP" (MoRunCo),
        # "=PR= Originals Tights - WRT-1001 - Women's" (PR Run & Walk's stock codes)
        n = o["n"] or ""
        if o["g"] in ("shoes", "gear") and re.search(r"\bshoe bag\b", n, re.I):
            o["g"] = "gear"
        if o["g"] in ("shoes", "gear"):   # "Bondi 9 Running Shoe- Galactic Grey/Stellar Grey - Men's" (Gazelle; some filed as gear), "Arahi 9 - Men's--Black/White"
            n = re.sub(r"\s*-{2,}\s*", " - ", n)                                          # (Tortoise & Hare): the colour goes
            n = re.sub(r"(\S)- (?=\S)", r"\1 - ", n)
            n = re.sub(r" -(?=[A-Za-z])", " - ", n)
            parts = n.split(" - ")
            n = " - ".join([parts[0]] + [x for x in parts[1:] if not ("/" in x and " x " not in x
                                                                       and re.fullmatch(r"[A-Za-z][A-Za-z '/]*", x.strip()))])
        if re.search(r"[*(\[]\s*final\s*sale\s*[*)\]]", n, re.I):
            o["fs"] = 1                # "*FINAL SALE*", "(FINAL SALE)" (The Trail Runner Store): the card's label says it
        n = re.sub(r"\s*[*(\[]\s*(?:final\s*sale|sale|clearance)\s*[*)\]]\s*", " ", n, flags=re.I).strip()
        m = re.match(r"^\(([MWU])\)\s+(.+)", n)
        if m:
            n = m.group(2) + ("" if re.search(r"\b(wom[ae]n|men)[’']?s\b", m.group(2), re.I)
                              else {"M": " - Men's", "W": " - Women's", "U": ""}[m.group(1)])
        if o.get("st") == "prrunwalk":
            n = re.sub(r"\s*=PR=\s*", " ", n).strip()
            n = re.sub(r"\s+-\s+(?=[A-Za-z0-9-]*[\d-])[A-Z][A-Za-z0-9-]{3,}(?=\s+-\s+(?:Men|Women)'s$|$)", "", n)
        o["n"] = n
        if o.get("st") == "brainsport" and o["g"] == "shoes":   # "Fresh Foam X 880v15 Smoked Violet": the colour goes
            o["n"] = re.sub(r"(\b\d{3,4}v\d+)\s+(?!(?:GTX|Gore|Wide|Trail|Boa|BOA|SL)\b)[A-Za-z][A-Za-z ]*$", r"\1", o["n"])
        if o.get("st") == "nordarun":   # norda's own store (Oct 9): "001A - M - Abyss", "000 - W - norda x Black Diamond/Kunzite"
            m = re.match(r"^(.*?)\s+-\s+([MWU])(?:\s+-\s+.*)?$", o["n"])
            if m:
                o["n"] = m.group(1) + {"M": " - Men's", "W": " - Women's", "U": ""}[m.group(2)]
                if m.group(2) in "MW":
                    o["sx"] = ["men" if m.group(2) == "M" else "women"]
        if o.get("st") == "rackets" and o["g"] == "shoes":   # Rackets & Runners (Oct 8): "Kayano 32 Running - Men's", "1080 V14 (D) Width"
            n, wom = o["n"], bool(re.search(r"women", o["n"], re.I))
            m = re.search(r"\s*\((2E|4E|EE|D|B)\)\s*Width", n, re.I)
            if m:
                if m.group(1).upper() in (("D", "2E", "EE", "4E") if wom else ("2E", "EE", "4E")):
                    o["w"] = True
                n = n[:m.start()] + n[m.end():]
            n = re.sub(r"\s+(Running|Stability)(?=\s+-\s+|$)", "", n)
            n = re.sub(r"\s+(Running|Stability)(?=\s+-\s+|$)", "", n)
            n = re.sub(r"\bV(\d+)\b", r"v\1", n)
            if re.match(r"asics", o["b"] or "", re.I):
                n = re.sub(r"^(Kayano|Nimbus|Cumulus|Excite|Contend|Pulse|Trabuco|Venture|Sonoma|Resolution)\b", r"GEL-\1", n)
            if re.match(r"brooks", o["b"] or "", re.I):
                n = re.sub(r"^Adrenaline (\d+)", r"Adrenaline GTS \1", n)
                n = re.sub(r"^(Ghost|Glycerin|Launch|Hyperion) GTX (\d+)", r"\1 \2 GTX", n)
            if re.match(r"new balance", o["b"] or "", re.I):
                n = re.sub(r"\b(\d{3,4}) v(\d+)\b", r"\1v\2", n)
                n = re.sub(r"\b(Balos|More|Hierro|Kaiha|Vongo|Arishi) v1\b", r"\1", n)
            o["n"] = n
    # soccer goalkeeper gloves come in numbered sizes, so tidy_gear would file them under shoes (Gazelle Sports, Oct 6)
    offers = [o for o in offers if not GOALIE.search(o["n"] or "")]
    # Rackets & Runners: walking shoes and Babolat's tennis line are not running gear
    offers = [o for o in offers if not (o.get("st") == "rackets" and (re.search(r"\bwalking\b", o["n"] or "", re.I)
                                                                    or re.match(r"babolat", o["b"] or "", re.I)
                                                                    or re.search(r"\btest\b", f'{o["b"]} {o["n"]}', re.I)))]
    offers = tidy_clothes(tidy_gear(tidy_nutrition(tidy_shoes(drop_kids(tidy_us_names(offers))))))
    items, tidied = {}, []
    for o in offers:
        if (o["b"] or "").strip() in ("", "0") and o.get("st") in OWN_BRAND:   # brand stores that leave the brand blank or "0"
            o["b"] = OWN_BRAND[o["st"]]
        if o.get("st") not in GENDER_PREFIX_STORES and o["g"] in ("shoes", "tops", "bottoms", "bras", "socks"):
            m = re.match(r"^(Men|Women)[’']?s\s+(.+)", tidy_name(o["b"] or "", o["n"]))   # any store, after the brand:
                                                                             # "Saucony Men’s Triumph 23" -> "Triumph 23 - Men's"
            if m and not re.search(r"\b(wom[ae]n|men)[’']?s?\b", m.group(2), re.I):
                o["n"] = m.group(2) + (" - Men's" if m.group(1) == "Men" else " - Women's")
        if o.get("st") in GENDER_PREFIX_STORES:
            o["n"] = re.sub(r"\s*\*[^*]{1,12}\*", "", o["n"]).strip()                 # "*SALE*"
            o["n"] = re.sub(r"\s+-\s*[^-]*/[^-]*$", "", o["n"]) if o["g"] == "shoes" else o["n"]   # " - White/Black" colour
            o["n"] = tidy_name(o["b"] or "", o["n"])                                  # brand first, then the gender
            m = re.match(r"^(M|W|U|Unisex|Men[’']?s|Women[’']?s)\s+(.+)", o["n"], re.I)
            if m:
                k = m.group(1)[0].upper()
                o["n"] = m.group(2)
                o["sx"] = GENDER_PREFIX[k]
                o["n"] += {"M": " - Men's", "W": " - Women's", "U": " - Unisex"}[k]
            if o["g"] == "shoes" and (o["b"] or "").lower() == "frontrunners footwear":
                o["g"] = "gear"            # the store's own accessories (toe spreaders, lights) filed under footwear
        if o.get("st") in CAPS_STORES:
            if (o["b"] or "").lower() not in BRAND_CANON and re.fullmatch(r"[A-Z][A-Z .'&-]{3,}", o["b"] or ""):
                o["b"] = o["b"].title()
            if o["n"] == o["n"].upper():
                o["n"] = soften_caps(o["n"])
        if o.get("st") == "rabbit":
            o["b"] = "rabbit"          # its own shop sometimes puts a product name in the brand ("EZ tee LS - women's")
        if (o["b"] or "").lower() == "precision" and o["n"].lower().startswith("fuel and hydration"):
            o["n"] = o["n"][18:].lstrip(" -") or o["n"]   # Capra: "Precision" + "Fuel and Hydration - PF30 Gels"
        o["b"] = tidy_brand(o["b"])
        o["n"] = tidy_name(o["b"], o["n"])
        if o["g"] in ("shoes", "tops", "bottoms", "bras", "socks"):
            # a gender word or code in front, any store (US shops: "M Ghost 18", "MEN'S GEL-KAYANO 33", "Unisex ASICS Megablast"):
            # it goes to the end like everywhere else, so one shoe gets one card and one price page (Oct 7 audit)
            m = re.match(r"^(M|W|U|Unisex|All[- ]Gender|Men[’']?s|Women[’']?s|Mens|Womens)\s+(.+)", o["n"], re.I)
            if m and not re.search(r"\b(wom[ae]n|men)[’']?s?\b|unisex", m.group(2), re.I):
                k = m.group(1)[0].upper()
                k = "U" if k == "A" else k
                rest = tidy_name(o["b"], m.group(2))
                if rest == rest.upper() and len(rest) > 4:
                    rest = soften_caps(rest)
                o["n"] = rest + {"M": " - Men's", "W": " - Women's", "U": " - Unisex"}[k]
                o["sx"] = GENDER_PREFIX[k]
        if o["g"] == "shoes":
            # "Ghost 17 Road", "GT-2000 15 Running Road", "Alphafly 3 Road Racing": filler, not the model;
            # "Speedgoat 7 GTX Trail Running" only when the model is a trail shoe anyway ("Pegasus Trail Running" keeps Trail)
            o["n"] = re.sub(r"\s+(running road|road racing|road running|road)(?=(?:\s*\[[^\]]+\])?(?:\s+-\s+(?:Men's|Women's|Unisex))?$)", "", o["n"], flags=re.I)
            m = re.match(r"^(.+?)\s+trail running((?:\s*\[[^\]]+\])?(?:\s+-\s+(?:Men's|Women's|Unisex))?)$", o["n"], re.I)
            if m and garment_type("shoes", m.group(1)) == "trail" and not re.search(r"\btrail\b", m.group(1), re.I):
                o["n"] = m.group(1) + (m.group(2) or "")
        o["sx"] = name_gender(o["n"]) or o["sx"] or clothing_gender(o)
        tidied.append(o)
    # one brand, one spelling, decided before cards are keyed ("Nathan Sports" = "Nathan", "ciele athletics" = "Ciele",
    # "SOAR Running" = "SOAR", "North Face" = "The North Face"): same letters once filler words and punctuation go;
    # the most common spelling wins, BRAND_PREFER first (Oct 5, 2026: ~30 brands were split across cards)
    def bkey(b):
        t = re.sub(r"[®™!]", "", (b or "").lower())
        t2 = re.sub(r"\b(sports?|running|innovations|inc|co|corp|company|ltd|athletics|apparel|footwear|the|optical products corp)\b", "", t)
        t2 = re.sub(r"[^a-z0-9]+", "", t2)
        return t2 if len(t2) >= 3 else re.sub(r"[^a-z0-9]+", "", t)
    bcount = collections.Counter(o["b"] for o in tidied)
    best = {}
    for b, n in bcount.items():
        k, cur = bkey(b), best.get(bkey(b))
        rank = lambda x: (x in BRAND_PREFER, x != x.upper() or len(x) <= 4, bcount[x])
        if cur is None or rank(b) > rank(cur):
            best[k] = b
    best.update({bkey(p): p for p in BRAND_PREFER})        # the official spelling wins even when no store uses it exactly
    for o in tidied:
        o["b"] = best.get(bkey(o["b"]), o["b"])
    # food from a brand that doesn't sell food (Oct 8 audit: Brainsport files Ciele caps, goodr sunglasses and Craft mittens
    # as "Nutrition"; US shops file ASICS Gel-Kayano there): the name's own category, else the brand's usual one,
    # unless the name is plainly food ("XACT Energy Chews" under a store's name stays food)
    per = collections.defaultdict(collections.Counter)
    for o in tidied:
        per[o["b"]][o["g"]] += 1
    for o in tidied:
        c = per[o["b"]]
        tot = sum(c.values())
        if o["g"] == "nutrition" and tot >= 8 and c["nutrition"] / tot < 0.08 and not STRONG_FOOD.search(o["n"]):
            o["g"] = ("bottoms" if re.search(r"\d(\.\d)?\s*(\"|''|”)", o["n"]) else group_of(o["n"])) \
                or next(g for g, _ in c.most_common() if g != "nutrition")      # rabbit "Fuel n' Fly 5"": shorts
        elif o["g"] in ("tops", "bottoms") and tot >= 8 and c["socks"] / tot >= 0.8 and not NOT_SOCK.search(o["n"]):
            o["g"] = "socks"           # a sock brand's "Franchise Crew" is a crew sock, not a crew-neck top (Stance, OS1st, Sockwell)
        elif o["g"] == "shoes" and tot >= 8 and c["shoes"] / tot < 0.08 and not SHOE_SIZES(o):
            # US shops file headlamps, flasks and spikes packs as footwear (Nathan, Amphipod, 2Toms): not a shoe without shoe sizes
            o["g"] = group_of(o["n"]) or next(g for g, _ in c.most_common() if g != "shoes")
    # distributors listed as the brand (Brainsport: "Back River Sport" for Feetures socks, Sprints hats, Tailwind):
    # the real brand from the start of the name when we know it (Oct 7 audit)
    known = {bkey(b): b for b in best.values()}
    for o in tidied:
        if (o["b"] or "").lower() in DISTRIBUTORS:
            ws = o["n"].split()
            for k in (3, 2, 1):
                b = known.get(bkey(" ".join(ws[:k]))) if len(ws) > k else None
                if b and b.lower() not in DISTRIBUTORS:
                    o["b"], o["n"] = b, " ".join(ws[k:])
                    break
    _TRAIL_MODELS.clear()
    for o in tidied:          # models a store names with Trail/Road but without "running" ("Ghost Trail - Men's")
        if o["g"] == "shoes" and re.search(r"\b(trail|road)\b", o["n"], re.I) and not re.search(r"\brunning\b", o["n"], re.I):
            _TRAIL_MODELS.add((o["b"].lower().strip(), _shoe_name(o, True)))
    for o in tidied:
        it = items.get(mkey(o))
        if not it:
            nm = o["n"].strip()
            if o["g"] == "shoes" and re.search(r"\s[—·]\s", nm):          # card name without the colour of the first store's listing
                gx = re.search(r"\s-\s*(Men's|Women's|Unisex)$", nm)
                nm = re.split(r"\s+[—·]\s+", nm)[0] + (f" - {gx.group(1)}" if gx else "")
            it = items[mkey(o)] = {"b": o["b"], "n": nm, "g": o["g"], "sx": list(o["sx"]), "w": o["w"],
                                   "img": o.get("img"), "lp": o["lp"], "bb": o.get("bb"), "sz": {}, "of": [], "_st": [],
                                   "_ca": [], "_fs": [], "ca": False}
            if o["g"] in TYPES:
                it["t"] = garment_type(o["g"], f'{o["b"]} {o["n"]}' if o["g"] in ("shoes", "gear") else o["n"])
        oi = len(it["of"])
        it["of"].append(o["u"]); it["_st"].append(o["st"]); it["_ca"].append(bool(o.get("ca")))
        it["_fs"].append(1 if o.get("fs") else FINAL_SALE.get(o["st"], 0))
        it["ca"] = it["ca"] or bool(o.get("ca"))     # sold by any Canadian store = ships from Canada
        it["lp"] = max(it["lp"], o["lp"])
        it["img"] = it["img"] or o.get("img")
        it["bb"] = it["bb"] or o.get("bb")
        it["sx"] = sorted(set(it["sx"]) | set(o["sx"]))
        for e in o["sz"]:
            size, price, reg = e[0], e[1], e[2]
            vid = e[3] if len(e) > 3 else None
            keys = canon_shoe(size) if o["g"] == "shoes" else acc_sizes(size) if o["g"] in ("packs", "gear") else [size]
            for k in keys:
                cur = it["sz"].get(k)
                # gear: a Canadian store's price wins over a cheaper one from abroad (no duties, easy returns);
                # nutrition shows US stores anyway, so there the cheapest wins
                pref = it["g"] != "nutrition"
                if cur is None or (pref and it["_ca"][oi], -price) > (pref and it["_ca"][cur[1]], -cur[0]):
                    it["sz"][k] = (price, oi, reg, vid)
    # one spelling per brand ("adidas"/"Adidas", "SmartWool"/"Smartwool"): the most common one, all-capitals last
    spell = collections.defaultdict(collections.Counter)
    for it in items.values():
        spell[it["b"].lower()][it["b"]] += 1
    best = {k: max(c, key=lambda b: (b != b.upper() or len(b) <= 4, c[b])) for k, c in spell.items()}   # GU, LEKI stay
    out = []
    for it in items.values():
        it["b"] = best[it["b"].lower()]
        # [size, price, offer, regular] plus the size's own variant id when the store has one
        it["sz"] = [[s, p, i, r] + ([v] if v else []) for s, (p, i, r, v) in it["sz"].items()]
        it.pop("_ca", None)
        fs = it.pop("_fs", [])
        if any(fs):
            it["fs"] = fs          # per offer, same order as "of" (FINAL_SALE codes)
        if it["sz"]:
            out.append(it)
    return out

def report_groups(items):
    """Log how many products each category has (and how many on sale), plus where the nutrition comes from."""
    on_sale = lambda i: any(e[1] < e[3] * 0.99 for e in i["sz"])
    groups = {}
    for i in items:
        n = groups.setdefault(i["g"], [0, 0])
        n[0] += 1
        n[1] += on_sale(i)
    print("categories: " + ", ".join(f"{g} {a} ({b} on sale)" for g, (a, b) in sorted(groups.items())), file=sys.stderr)
    by_store = {}
    for i in items:
        if i["g"] == "nutrition":
            for st in set(i["_st"]):
                n = by_store.setdefault(st, [0, 0])
                n[0] += 1
                n[1] += on_sale(i)
    print("nutrition by store: " + ", ".join(f"{st} {a} ({b} on sale)" for st, (a, b) in
                                             sorted(by_store.items(), key=lambda x: -x[1][0])), file=sys.stderr)

def main():
    def load(path):
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    prev = load(OUT)
    prev_offers = load(OUT.parent / "offers.json")   # yesterday's raw per-store listings, for fallback
    stamps, offers, failed, raw, why = dict(prev.get("stores", {})), [], [], {}, {}
    def run(st, fn):
        """One store: (listings, ok, log line). A store that fails or empties keeps yesterday's listings."""
        t = time.time()
        if REMERGE:
            return prev_offers.get(st, []), None, None
        try:
            got = fn()
            if not got and st not in dict((x[0], 1) for x in SHOPIFY_STORES) and st not in SAVED_STORES:
                raise RuntimeError("0 items")
            if not got and len(prev_offers.get(st, [])) >= 20 and st not in SAVED_STORES:   # a store rarely empties
                # overnight: keep yesterday's. Not for saved pages / the catalog file: when they expire, their deals go (Oct 9)
                raise RuntimeError(f"0 items today (had {len(prev_offers[st])})")
            n_sale = sum(1 for o in got if any(e[1] < e[2] * 0.99 for e in o["sz"]))
            return got, True, f"{st}: {len(got)} items ({n_sale} on sale) in {time.time()-t:.0f}s"
        except Exception as e:
            msg = str(e)
            m = re.search(r"(Tunnel connection failed: \d+ \w+|\d{3} Client Error: \w+|HTTP \d{3}|no [^;]{0,60})", msg)
            kept = prev_offers.get(st, [])
            return kept, False, f"{st}: FAILED ({m.group(1) if m else msg[:120]}); kept {len(kept)} from last run"
    # Lanes (Oct 5, 2026: one after another took ~35 min, this ~13): the Shopify stores one at a time in one lane
    # (Shopify counts requests from one machine across all its stores: 4 at once got "429 too many requests"),
    # every other reader in its own lane, 4 lanes at once, each keeping its polite pace. Results are used in STORES
    # order so the merge (first store names the card) never changes.
    shop = [st for st in STORES if st in dict((x[0], 1) for x in SHOPIFY_STORES)]
    lanes = [shop] + [[st] for st in STORES if st not in shop]
    lanes.sort(key=lambda l: -len(l))
    results = {}
    def lane(sts):
        for st in sts:
            results[st] = run(st, STORES[st])
    with ThreadPoolExecutor(1 if REMERGE else 4) as ex:
        list(ex.map(lane, lanes))
    # a store that said "too busy" (429/5xx) gets one more go at the end, after a pause, before it falls back to its
    # last read (Oct 8: The Feed's 2,370 products kept a half-day-old read after one 429)
    busy = [st for st in STORES if results[st][1] is False and re.search(r"\b(429|50[0234])\b", results[st][2] or "")]
    if busy and not REMERGE:
        print(f"trying again in 90 s: {', '.join(busy)}", file=sys.stderr)
        time.sleep(90)
        for st in busy:
            again = run(st, STORES[st])
            if again[1]:
                results[st] = (again[0], True, again[2] + " (second try)")
    for st in STORES:
        got, ok, line = results[st]
        for o in got:
            o.setdefault("ca", st in CA_STORES)
            o.setdefault("us", st in ("thefeed", "rei") or st in US_SHOPS)
        raw[st] = got
        if ok:
            stamps[st] = now()
        elif ok is False:
            failed.append(st)
            why[st] = line.split("FAILED (", 1)[-1].split("); kept")[0][:160]   # for the health email: why it failed
        if line:
            print(line, file=sys.stderr)
        offers += got
    # the USA side (Oct 6, 2026): stores that ship to the US, merged on their own (best US-shippable price per size);
    # "ca" there means "ships from the US". Copied before the Canadian merge, which tidies offers in place.
    us_offers = [dict(o, ca=bool(o.get("us")), sz=[list(e) for e in o["sz"]], sx=list(o.get("sx") or []))
                 for o in offers if (o.get("us") or o.get("st") in SHIPS_US or not o.get("ca")) and not o.get("no_us")]
    offers = [o for o in offers if o.get("st") not in US_SHOPS and not o.get("no_ca")]   # US shops may not ship to Canada
    items = merge(offers)
    report_groups(items)
    for it in items:
        it.pop("_st", None)
    items.sort(key=lambda i: (i["g"], i["b"].lower(), i["n"].lower()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        usd = round(fx_to_cad("USD"), 4)            # for the site's CAD/USD switch
    except Exception:
        usd = FX_FALLBACK["USD"]
    n_ca = n_us = len({o["st"] for o in offers} | {o["st"] for o in us_offers})   # "N stores checked daily": one total, both sides
    OUT.write_text(json.dumps({"v": 2, "updated": now(), "stores": stamps, "n_stores": n_ca, "failed": why, "fx": {"USD": usd}, "items": items},
                              separators=(",", ":"), ensure_ascii=False))
    # the site loads sale items first: same shape, only items with at least one size on sale
    sale = [i for i in items if any(e[1] < e[3] for e in i["sz"])]   # same test as the site's % off
    (OUT.parent / "sale.json").write_text(json.dumps({"v": 2, "updated": now(), "stores": stamps, "n_stores": n_ca, "fx": {"USD": usd}, "items": sale},
                                                     separators=(",", ":"), ensure_ascii=False))
    us_items = merge(us_offers)
    for it in us_items:
        it.pop("_st", None)
    us_items.sort(key=lambda i: (i["g"], i["b"].lower(), i["n"].lower()))
    (OUT.parent / "deals-us.json").write_text(json.dumps({"v": 2, "country": "us", "updated": now(), "stores": stamps, "n_stores": n_us,
                                                          "fx": {"USD": usd}, "items": us_items}, separators=(",", ":"), ensure_ascii=False))
    (OUT.parent / "sale-us.json").write_text(json.dumps({"v": 2, "country": "us", "updated": now(), "stores": stamps, "n_stores": n_us,
                                                         "fx": {"USD": usd}, "items": [i for i in us_items if any(e[1] < e[3] for e in i["sz"])]},
                                                        separators=(",", ":"), ensure_ascii=False))
    print(f"USA side: {len(us_items)} items ({sum(1 for i in us_items if i['g'] == 'shoes')} shoes) from {len(us_offers)} listings",
          file=sys.stderr)
    # raw offers go in a side file so a failed store can be restored tomorrow
    (OUT.parent / "offers.json").write_text(json.dumps(raw, separators=(",", ":"), ensure_ascii=False))
    ok = [st for st in STORES if st not in failed]
    print(f"stores OK ({len(ok)}): {', '.join(ok)}", file=sys.stderr)
    if failed:
        print(f"stores skipped ({len(failed)}): {', '.join(failed)}", file=sys.stderr)
    n_sale = sum(1 for i in items if any(e[1] < e[3] * 0.99 for e in i["sz"]))
    print(f"wrote {len(items)} items ({n_sale} on sale) from {len(offers)} store listings to {OUT}", file=sys.stderr)
    return 1 if len(failed) == len(STORES) else 0

def scrape_decathlon_saved():
    """Decathlon (Oct 6, 2026): read at night by `scrape.py --decathlon-night` (one page every 6 s; stops for the night on
    "429 too many requests") into decathlon.json on the history branch; the refresh downloads it to DECATHLON_FILE."""
    try:
        d = json.loads(Path(DECATHLON_FILE).read_text())
    except Exception:
        raise RuntimeError("no night read of Decathlon yet")
    t = dt.datetime.fromisoformat(d["updated"])
    if dt.datetime.now(dt.timezone.utc) - t > dt.timedelta(hours=36):
        raise RuntimeError(f"Decathlon night read last worked {t:%b %d}" + (f" ({d['failed']})" if d.get("failed") else ""))
    return d["offers"]


def decathlon_night(out):
    """The night read (Oct 8, 2026): Decathlon answers "429 too many requests" to GitHub's servers after ~50 product pages even
    at one page every 6 s, so a full read never finished and the site kept Oct 5 prices. Now: one page every 20 s, keep every
    product read, and pick up next night where this one stopped (a cursor through the product list). The list itself is
    refreshed once a week (or when the cursor has gone round). A product not re-read for 14 days drops off. We stop the
    moment Decathlon says no: polite reading, nothing that gets around its limit."""
    global DEC_PACE
    DEC_PACE = 20.0
    p = Path(out)
    try:
        prev = json.loads(p.read_text())
    except Exception:
        prev = {}
    t0, today = time.time(), now()
    links, cur = prev.get("links") or [], int(prev.get("cursor") or 0)
    offers = {o["u"]: o for o in prev.get("offers") or []}
    seen = dict(prev.get("seen") or {})                  # product link -> last night it was read
    for u in offers:
        seen.setdefault(u, prev.get("updated") or today)
    note, read, listed = "", 0, prev.get("listed")
    try:
        if not links or cur >= len(links) or not listed or \
                dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(listed) > dt.timedelta(days=7):
            links, cur, listed = dec_links(40 * 60), 0, today
        while cur < len(links) and time.time() - t0 < 85 * 60:
            u = links[cur]
            time.sleep(DEC_PACE)
            o = dec_offer(u)
            full = DEC_BASE + u
            if o:
                offers[full] = o
            else:
                offers.pop(full, None)                    # sold out or not ours any more
            seen[full] = today
            cur += 1
            read += 1
    except DecBusy as e:
        note = f"stopped for the night (429) at {cur} of {len(links)}"
    except Exception as e:
        note = f"stopped ({str(e)[:80]}) at {cur} of {len(links)}"
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)).isoformat()   # a full round takes about a week
    offers = {u: o for u, o in offers.items() if seen.get(u, today) >= cutoff}
    good = read >= 20 or (not note and cur >= len(links))
    d = {"updated": today if good else (prev.get("updated") or today), "offers": list(offers.values()), "links": links,
         "cursor": cur, "listed": listed, "seen": {u: t for u, t in seen.items() if t >= cutoff}}
    if note:
        d["failed"] = note
    p.write_text(json.dumps(d, separators=(",", ":"), ensure_ascii=False))
    print(f"decathlon night read: {read} product pages read tonight, {len(offers)} products kept, list position {cur}/{len(links)}"
          + (f"; {note}" if note else ""), file=sys.stderr)
    return 0


# ---------------------------------------------------------------- Backcountry (US)
# Oct 6, 2026: its robots rules block the JSON feeds (/*.json, /api/*) but allow category and product pages, which carry
# their data in the page (__NEXT_DATA__): each size and colour with list price, sale price and stock. One page every
# BC_PACE seconds (OFF since Oct 6: Backcountry's bot protection answers GitHub's servers "HTTP 202, empty page", and we
# don't get around bot protection; waits for an affiliate product feed) -> backcountry.json on the history branch; the refresh
# loads it (BACKCOUNTRY_FILE). US side only (ships within the US). `--sale-only` reads just the products with sizes on sale.
BC_BASE = "https://www.backcountry.com"
BC_LISTS = ["/cat/running-shoes", "/cat/running-clothing-accessories", "/cat/running-hydration"]
BC_PACE = 1.5
BACKCOUNTRY_FILE = os.environ.get("BACKCOUNTRY_FILE", "/tmp/backcountry.json")
BC_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def bc_data(path):
    for i in range(3):
        r = S.get(BC_BASE + path, timeout=45, headers={"User-Agent": BC_UA})
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(30 * (i + 1))
            continue
        r.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            t = re.search(r"<title[^>]*>([^<]{0,80})", r.text)
            raise RuntimeError(f"no page data on {path} (HTTP {r.status_code}, {len(r.text)} bytes, "
                               f"title: {t.group(1).strip() if t else 'none'})")
        return json.loads(m.group(1))["props"]["pageProps"]
    raise requests.HTTPError(f"{r.status_code} {path}")

def bc_list(sale_only=False):
    """Every product in the running section: (url, on sale?). Strollers/joggers skipped."""
    seen = {}
    for path in BC_LISTS:
        page, last = 1, 1
        while page <= last and page <= 80:
            pp = bc_data(f"{path}?page={page}" if page > 1 else path)
            cat = pp["plpData"]["data"]["category"]
            last = ((cat.get("pageInfo") or {}).get("lastPage") or {}).get("value") or 1
            for k, v in pp["__APOLLO_STATE__"].items():
                if k.startswith("Product:") and v.get("url"):
                    sale = ((v.get("aggregates") or {}).get("variationsOnSale") or 0) > 0
                    if not re.search(r"stroller|jogger stroller|kids'|\bkids\b|toddler", v.get("name") or "", re.I):
                        seen[v["url"]] = seen.get(v["url"]) or sale
            page += 1
            time.sleep(BC_PACE)
    return [(u, s) for u, s in seen.items() if s or not sale_only]

def bc_group(title, crumbs):
    c = " ".join(crumbs).lower()
    if re.search(r"footwear|shoes", c) and not re.search(r"sock|gaiter|insole|lace", title, re.I):
        return "shoes"
    g = group_of(title)
    if g == "packs" and "clothing" in c and "hydration" not in c:
        g = "tops"                                       # a running vest you wear
    return g or group_of(c)

def bc_product(url):
    p = bc_data(url)["product"]
    title = p.get("title") or ""
    crumbs = [b.get("name") or "" for b in p.get("breadcrumbs") or []]
    g = bc_group(title, crumbs)
    if not g:
        return None
    sx = name_gender(title) or []
    sizes, lp = {}, 0
    for k in p.get("skus") or []:
        a = k.get("availability") or {}
        if a.get("status") != "InStock" or (a.get("stockLevel") or 0) <= 0:
            continue
        size = k.get("size") or {}
        scale = size.get("scale") or ""
        if re.search(r"kid|youth|toddler|infant|little|big kid", scale, re.I):
            continue
        if g == "shoes" and not sx:                      # a unisex shoe sized on one scale
            sx = ["women"] if "women" in scale.lower() else ["men"] if "men" in scale.lower() else sx
        lab = norm_size(size.get("name") or "OS")
        if g == "shoes":                                 # "US 10.0/UK 8.5" (Salomon) -> "10.0"
            m = re.match(r"US\s*(\d+(?:\.\d)?)\s*/\s*UK", lab, re.I)
            lab = m.group(1) + (" Wide" if re.search(r"wide", lab, re.I) else "") if m else lab
        price, reg = float(k.get("salePrice") or k.get("listPrice") or 0), float(k.get("listPrice") or 0)
        if not price:
            continue
        reg = max(reg, price)
        lp = max(lp, reg)
        if lab not in sizes or price < sizes[lab][0]:
            sizes[lab] = (price, reg, f"{BC_BASE}{url}?skid={k['id']}")
    if g in ("shoes", "tops", "bottoms", "bras", "socks", "gloves") and len(sizes) > 1:
        sizes.pop("OS", None)
    if not sizes:
        return None
    img = (p.get("productMainImage") or {}).get("mediumImg")
    return {"st": "backcountry", "b": (p.get("brand") or {}).get("name") or "", "n": title, "u": BC_BASE + url, "g": g,
            "sx": sx, "w": bool(re.search(r"\bwide\b", title, re.I)),
            "img": "https://content.backcountry.com" + img if img else None, "lp": round(lp, 2), "bb": None,
            "sz": [[k, pr, rg, u] for k, (pr, rg, u) in sizes.items()]}

def backcountry_night(out, sale_only=False):
    """Read Backcountry's running section slowly (prices in USD); keeps the last good read if this one fails."""
    p, t0 = Path(out), time.time()
    try:
        prev = json.loads(p.read_text())
    except Exception:
        prev = {}
    try:
        links = bc_list(sale_only)
        print(f"backcountry: {len(links)} products to open ({sum(1 for _, s in links if s)} with sizes on sale)", file=sys.stderr)
        got, bad = [], 0
        for i, (u, _) in enumerate(sorted(links, key=lambda x: not x[1])):     # sale items first
            try:
                o = bc_product(u)
                if o:
                    got.append(o)
            except Exception as e:
                bad += 1
                if bad > 50 and bad > len(got):
                    raise RuntimeError(f"too many pages failed ({str(e)[:60]})")
            if i % 200 == 0:
                print(f"  {i}/{len(links)} pages, {len(got)} products, {time.time() - t0:.0f}s", file=sys.stderr)
            time.sleep(BC_PACE)
        if len(got) < 100:
            raise RuntimeError(f"only {len(got)} products")
        if sale_only and prev.get("offers"):                # keep yesterday's full-price items until the full read
            mine = {o["u"] for o in got}
            got += [o for o in prev["offers"] if o["u"] not in mine and not any(e[1] < e[2] * 0.99 for e in o["sz"])]
        p.write_text(json.dumps({"updated": now(), "offers": got}, separators=(",", ":"), ensure_ascii=False))
        print(f"backcountry read: {len(got)} products in {time.time() - t0:.0f}s", file=sys.stderr)
    except Exception as e:
        print(f"backcountry read failed ({str(e)[:120]}); kept the last good read", file=sys.stderr)
        if prev:
            prev["failed"] = str(e)[:120]
            p.write_text(json.dumps(prev, separators=(",", ":"), ensure_ascii=False))
    return 0

def scrape_backcountry_saved():
    try:
        d = json.loads(Path(BACKCOUNTRY_FILE).read_text())
    except Exception:
        raise RuntimeError("no night read of Backcountry yet")
    t = dt.datetime.fromisoformat(d["updated"])
    if dt.datetime.now(dt.timezone.utc) - t > dt.timedelta(hours=36):
        raise RuntimeError(f"Backcountry night read last worked {t:%b %d}")
    fx = fx_to_cad("USD")
    return [dict(o, ca=False, us=True, lp=round(o["lp"] * fx, 2), sz=[[k, round(pr * fx, 2), round(rg * fx, 2), u] for k, pr, rg, u in o["sz"]])
            for o in d["offers"]]


if __name__ == "__main__" and "--backcountry-night" in sys.argv:
    sys.exit(backcountry_night(sys.argv[sys.argv.index("--backcountry-night") + 1], "--sale-only" in sys.argv))

if __name__ == "__main__" and "--thefeed-night" in sys.argv:
    sys.exit(thefeed_night(sys.argv[sys.argv.index("--thefeed-night") + 1]))

if __name__ == "__main__" and "--decathlon-night" in sys.argv:
    sys.exit(decathlon_night(sys.argv[sys.argv.index("--decathlon-night") + 1]))

if __name__ == "__main__":
    sys.exit(main())
