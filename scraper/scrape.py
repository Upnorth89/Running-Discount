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
import json, re, sys, time, datetime as dt
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
        try:
            r = S.get(url, timeout=45, cookies=cookies)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code} {url}")
            r.raise_for_status()
            return r
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))

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
    ("socks",     r"\bsocks?\b|mini crew|no[- ]show|over[- ]the[- ]calf|\bquarter\b(?![- ]?zip)"),
    ("gloves",    r"\bgloves?\b|\bmitts?\b|mittens"),
    ("watches",   r"\bwatch(es)?\b"),
    ("headwear",  r"\bhats?\b|\bcaps?\b|\b(?:go|trl|crw|fst|alz|ss|gt)cap\b|beanie|toque|tuque|headband|\bbuffs?\b|neck ?gaiter|visor"),
    ("packs",     r"hydration (vest|pack)|race vest|running vest|backpack|\bbelts?\b|waist ?pack|\bpinnacle\b|\bvest \d|\d+ ?l\b"),
    ("bottoms",   r"\bbottoms?\b|(?<!short sleeve )\bshorts\b|\bshort\b(?! sleeve)|tights?\b|\bpants?\b|leggings?|joggers?|skirts?|skorts?|boxers?|briefs?"),
    ("tops",      r"t-?shirts?|\btees?\b|\bshirts?|\btops?\b|tanks?|singlets?|jackets?|\bcoats?\b|raincoats?|hood(ie|y)|\bvests?\b|gilets?|jersey|sweaters?|base ?layer|pullovers?|fleece|anorak|windbreaker|\bcrew\b|half zip|quarter zip|1/2 zip|1/4 zip|long sleeve|short sleeve|\bcrop\b"),
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
        "EXTRA SMALL": "XS", "EXTRA LARGE": "XL", "EXTRA EXTRA LARGE": "2XL", "EXTRA EXTRA SMALL": "2XS"}
def norm_size(s):
    s = str(s or "").strip()
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
DEC_LISTS = ["/en/clearance/running-clearance"]
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

def scrape_decathlon():
    links = []
    for path in DEC_LISTS:
        start = 0
        while start < 2000:
            html = get(f"{DEC_BASE}{path}?from={start}&size=40").text
            new = [u for u in dict.fromkeys(re.findall(r'href="(/en/p/[^"]+)"', html)) if u not in links]
            if not new:
                break
            links += new
            start += 40
            time.sleep(1)
    out, seen = [], set()
    for u in links:
        m = re.search(r"/p/[^/]+/(\d+)/", u)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        time.sleep(0.7)                                   # relaxed pace
        try:
            skus = [x for x in dec_skus(get(DEC_BASE + u).text) if x.get("isAvailable")]
        except Exception:
            continue
        if not skus:
            continue
        x0 = skus[0]
        title = x0.get("title") or ""
        if re.search(r"\b(kids?|children|boys?|girls?|junior|baby)'?s?\b", title, re.I):
            continue
        g = dec_group(x0)
        if not g:
            continue
        gs = {(y.get("name") or "").lower() for y in x0.get("genders") or []}
        sx = (["men"] if "men" in gs else []) + (["women"] if "women" in gs else [])
        if g == "shoes" and len(sx) != 1:
            continue                                      # unisex US sizes are ambiguous without a gender
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
            sizes.pop("OS", None)                         # an unlabelled size must not match everyone
        if not sizes:
            continue
        brand = ((x0.get("brand") or {}).get("name") or "Decathlon").title()
        img = (x0.get("mainImage") or {}).get("url")
        out.append({"st": "decathlon", "b": brand, "n": title, "u": DEC_BASE + u, "g": g, "sx": sx,
                    "w": bool(re.search(r"\bwide\b", title, re.I)), "img": img + "?format=auto&f=500x0" if img else None,
                    "lp": round(lp, 2), "bb": None, "sz": [[k, p, r] for k, (p, r) in sizes.items()], "ca": True})
    print(f"  decathlon: {len(links)} listings, {len(out)} products in stock", file=sys.stderr)
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
    prods, page = [], 1
    while page <= max_pages:
        batch = get(f"{base}/products.json?limit=250&page={page}", cookies=cookies).json()["products"]
        if not batch:
            break
        prods += batch
        page += 1
    return prods

SIZE_OPT = re.compile(r"^(size|taille|pointure|shoe size)$", re.I)

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
            price = float(v["price"])
            if price <= 0:
                continue
            cmp_ = max(price, float(v.get("compare_at_price") or 0))
            o1 = v.get("option1") or ""
            vals = [v.get(f"option{i}") or "" for i in (1, 2, 3)][:len(opts)]
            si = next((i for i, n in enumerate(opts) if SIZE_OPT.match(n)), None) if size_aware else None
            if si is not None:            # apparel: one card per colour, sizes as the "sizes"
                key = " / ".join(x for i, x in enumerate(vals) if i != si and x)
                label = vals[si]
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
                        "u": f"{base}/products/{p['handle']}?variant={b['vid']}", "g": g, "sx": [], "w": False,
                        "img": img, "lp": round(b["lp"] * fx, 2), "bb": b["bb"],
                        "sz": [[k, pr, rg, vid] for k, (pr, rg, vid) in b["sz"].items()]})
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

def scrape_thefeed():
    # Read The Feed as a Canadian visitor: it then lists only what it ships to Canada (about 500 products fewer)
    # with its own CAD prices. Its site is custom-built (no cart.js), so check the currency against a page of
    # US prices: CAD prices run ~1.4x the USD ones; if they don't, the Canadian view was ignored -> convert.
    base = "https://thefeed.com"
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
            if key in seen:
                continue
            seen.add(key)
            it = mec_item(h)
            if it:
                out.append(it)
    print(f"  mec: {used} saved page(s)", file=sys.stderr)
    return out                      # no fresh pages -> no MEC items (never keep stale prices)

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
    ("2xu",            "https://www.2xu.com",                "gear"),
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
    ("forerunners",    "https://shop.forerunners.ca",        "gear"),   # Forerunners (Vancouver; shop on its own address)
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
    ("tifosi",         "https://www.tifosioptics.com",       "eyewear"),
    # race fuel
    ("tailwind",       "https://www.tailwindnutrition.com",  "food"),
    ("skratch",        "https://www.skratchlabs.com",        "food"),
    ("nuun",           "https://nuun.com",                   "food"),
    ("honeystinger",   "https://www.honeystinger.com",       "food"),
    ("gu",             "https://guenergy.com",               "food"),
    ("huma",           "https://www.humagel.com",            "food"),
]

NOT_RUNNING = re.compile(r"gift ?card|pannier|eyeglasses|optical|reading glass|blue light|prescription|e-?gift|\bbike\b|cycling|\bbib\b|swim|golf|\bski\b|snowboard|\bdog\b|\bpet\b|"
                         r"\btent\b|sleeping bag|stickers?|poster|\bmug\b|\bbundle builder\b|warranty|shipping protection|"
                         r"route protection|insurance|\bsample\b|donation", re.I)
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

def generic_group(kind):
    def g(p):
        title = p.get("title") or ""
        ptype = p.get("product_type") or ""
        tags = re.sub(r"[_:>/-]+", " ", " ".join(p.get("tags") or []))
        if NOT_RUNNING.search(f"{title} {ptype}"):
            return None
        g = group_of(title)
        if kind == "food":             # fuel brands: food, unless it's clearly merch/gear (a cap, a flask)
            return g if g and not FOOD.search(title) else "nutrition"
        if kind == "socks":            # sock brands: socks unless it's clearly a tee/hoodie/etc.
            return g if g and g != "tops" or re.search(r"\btee\b|shirt|tank|hoodie|jacket|pullover", title, re.I) else "socks"
        if kind == "eyewear":          # sunglasses brands: everything is eyewear except hats/apparel
            return g if g in ("headwear", "tops", "bottoms") else "gear"
        if FOOD.search(ptype) or (FOOD.search(title) and not g):
            return "nutrition"
        return g or group_of(ptype) or group_of(tags)
    return g

def make_shopify_scraper(st, base, kind):
    def run():
        # quick probe so a dead / blocked / non-Shopify store costs one request, not minutes of retries
        r = S.get(f"{base}/products.json?limit=1", timeout=20)
        if r.status_code != 200 or not r.text.lstrip().startswith("{"):
            raise RuntimeError(f"no Shopify product feed (HTTP {r.status_code})")
        home = None                                    # the store's own currency (meta.json) = where it ships from
        try:
            home = (get(f"{base}/meta.json", tries=2).json().get("currency") or "").upper() or None
        except Exception:
            pass
        # always ask for the store's Canadian market: the price and stock a Canadian visitor actually gets
        # (otherwise the store guesses from GitHub's server location: Chilean pesos, or "not available here")
        cookies = CA_COOKIES
        served = shopify_price_currency(base, cookies)   # the currency the prices actually come back in
        home = home or served
        if not home:
            print(f"  ! {st}: currency unknown, assuming CAD", file=sys.stderr)
            home = "CAD"
        cur = served or home
        prods = shopify_products(base, max_pages=24, cookies=cookies)
        fx = fx_to_cad(cur)
        print(f"  {st}: {len(prods)} products, store {home}, prices in {cur}" + (f" x{fx}" if cur != "CAD" else ""), file=sys.stderr)
        items = shopify_items(st, base, prods, generic_group(kind), fx=fx, size_aware=True, collapse=True,
                              size_fn=(lambda _l: "OS") if kind == "eyewear" else generic_size)
        for o in items:
            o["ca"] = home == "CAD"         # a store based in CAD ships from Canada; USD/EUR/GBP stores are cross-border
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
    "rei": scrape_rei_saved,
    "decathlon": scrape_decathlon,
}
for _st, _base, _kind in SHOPIFY_STORES:
    STORES[_st] = make_shopify_scraper(_st, _base, _kind)

# Casual footwear some running stores also sell; not what people come here for.
CASUAL_BRANDS = {"birkenstock", "wolky", "teva", "crocs", "ugg", "blundstone", "dr. martens", "clarks"}
CASUAL_SHOE = re.compile(r"\b(sandal|sandale|clog|sabot|slipper|pantoufle|mule|flip[- ]flop|loafer)s?\b", re.I)
# soccer boots (Frontrunners sells them): ground codes FG/AG/MG/SG/TF, or the model lines
SOCCER = re.compile(r"\b(FG|AG|MG|SG|TF)\b|(?i:\b(soccer|futsal|predator|f50|copa|tiempo|mercurial)\b)")

def shoe_width_from_name(n, sx):
    """Widths many stores put in the product name: "Bondi 9 (2E)", "880v15 (D)", "Clifton 10 Wide".
    Returns "wide", "narrow" or "". Women's D is wide; men's D is the regular width."""
    low = n.lower()
    if re.search(r"\(\s*(2e|4e|6e|ee|eee|x-?wide|wide|extra wide)\s*\)|\b(x-?wide|extra wide|wide)\b|\blarge\b(?=.*\b(pied|chaussure)\b)", low):
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
NUT_CAMP_BRANDS = {"msr", "jetboil", "primus", "snow peak", "soto", "optimus"}   # stove fuel, not runner fuel
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
GEAR_LEG = re.compile(r"\b(calf|leg|compression|booster)\b.*\b(sleeves?|warmers?)\b|\b(leg|knee) warmers?\b|\bcalf (guards?|tubes?)\b", re.I)
GEAR_ARM = re.compile(r"\barm\b.*\b(sleeves?|warmers?|coolers?)\b|\b(sleeves?|warmers?)\b.*\barm\b", re.I)
GEAR_TIGHTS = re.compile(r"\b(tights?|leggings?|shorts)\b", re.I)
GEAR_CAP = re.compile(r"\b(?:go|trl|crw|fst|alz|ss|gt)cap\b|\b(caps?|hats?|visors?|beanies?|toques?|tuques?)\b", re.I)

def tidy_gear(offers):
    for o in offers:
        if o["g"] != "gear":
            continue
        n = o["n"]
        if GEAR_ARM.search(n):
            o["g"] = "tops"            # arm sleeves / warmers: with tops, in the clothing size
        elif GEAR_LEG.search(n):
            o["g"] = "socks"           # calf sleeves / leg warmers: with socks (CEP, BV Sport sell them together)
        elif GEAR_TIGHTS.search(n):
            o["g"] = "bottoms"
        elif GEAR_CAP.search(n):
            o["g"] = "headwear"
    return offers

# Clothing that landed in the wrong category, and the type of each top / bottom (the site's "Jackets & vests" etc. buttons)
CLOTH_BRA = re.compile(r"\bsports? bra\b|\bbra\b|brassi[èe]re", re.I)
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
TYPES = {g: [(k, re.compile(rx, re.I)) for k, rx in v] for g, v in TYPES.items()}

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
        out.append(o)
    return out

def garment_type(g, n):
    """tops: tee / layer / jacket; bottoms: short / tight / pant; None when the name doesn't say (shown under "All" only)."""
    for k, rx in TYPES.get(g, []):
        if rx.search(n):
            return k
    return None

# Kids' gear: a kids' 11 or "M" would match an adult's size. The site is for adults, so leave it out.
KIDS = re.compile(r"\b(kids?|kid'?s|kids'|juniors?'?|jr|youth|enfants?|gar[çc]ons?|filles?|boys?|girls?|toddlers?|infants?|"
                  r"b[ée]b[ée]s?|big kids?|little kids?|grade school|pre-?school|pr[ée]scolaire|jeunesse)\b", re.I)
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

def tidy_shoes(offers):
    """Drop casual footwear and narrow-only shoes; mark wide ones from the product name."""
    out = []
    for o in offers:
        if o["g"] == "shoes":
            if (o["b"] or "").lower() in CASUAL_BRANDS or CASUAL_SHOE.search(o["n"]) or SOCCER.search(o["n"]):
                continue
            w = shoe_width_from_name(o["n"], name_gender(o["n"]) or o.get("sx"))
            if w == "narrow":
                continue
            if w == "wide":
                o["w"] = True
        out.append(o)
    return out

# ---------------------------------------------------------------- tidy names and accessory sizes (site, email and alerts all use these)
BRAND_CANON = {"hoka one one": "Hoka", "hoka": "Hoka", "asics": "ASICS", "satisfy": "Satisfy", "oiselle": "Oiselle",
               "nnormal": "NNormal", "new balance": "New Balance", "on running": "On", "the north face": "The North Face",
               "karitraa": "Kari Traa", "kari traa": "Kari Traa"}

def tidy_brand(b):
    b = (b or "").strip()
    if b.lower() in BRAND_CANON:
        return BRAND_CANON[b.lower()]
    return b

CAPS_STORES = {"lecoureur"}
OWN_BRAND = {"rabbit": "rabbit", "bandit": "Bandit Running"}
GENDER_PREFIX_STORES = {"frontrunners"}   # names start with "M " / "W " / "U " ("M Adidas Boston 13")
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
    first = b.split(" ")[0] if b else ""
    toks = {b} | ({first} if len(first) >= 4 and first.lower() not in {"black", "blue", "north", "mountain", "outdoor"} else set())
    if b.lower() == "hoka":
        toks |= {"Hoka One One", "Hoka"}
    for tok in sorted(toks if b else set(), key=len, reverse=True):
        if not tok:
            continue
        m = re.match(re.escape(tok) + r"\b\s*[-–:|]?\s*", n, re.I)
        if m and len(n) - m.end() >= 3:
            n = n[m.end():]
            break
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

def name_gender(n):
    """Product names ("... - Women's", "Mens Pressio Tee") beat a store's gender tag, which is
    often "unisex" for women's-cut gear."""
    low = n.lower()
    w = bool(re.search(r"\bwom[ae]n'?s?\b|\bfemmes?\b", low))
    m = bool(re.search(r"(?<!wo)\bmen'?s?\b|\bhommes?\b", low))
    return ["women"] if w and not m else ["men"] if m and not w else None

# Stores that sell and ship from Canada (no border fees). Generic Shopify stores decide by their currency.
CA_STORES = {"altitude", "lasthunt", "sea2sky", "sportinglife", "stampeak", "mec", "decathlon"}

def mkey(o):
    name = re.sub(r"[^a-z0-9]+", " ", o["n"].lower()).strip()
    # Canadian and cross-border offers stay separate, so "Canadian stores only" never hides a cheaper US price inside a card
    return (o["b"].lower().strip(), name, o["w"], o["g"], bool(o.get("ca")))

def merge(offers):
    """Same product at several stores -> one item; each size keeps the cheapest store."""
    offers = tidy_clothes(tidy_gear(tidy_nutrition(tidy_shoes(drop_kids(offers)))))
    items = {}
    for o in offers:
        if (o["b"] or "").strip() in ("", "0") and o.get("st") in OWN_BRAND:   # brand stores that leave the brand blank or "0"
            o["b"] = OWN_BRAND[o["st"]]
        if o.get("st") in GENDER_PREFIX_STORES:
            m = re.match(r"^(M|W|U|Unisex)\s+(.+)", o["n"])
            if m:
                k = m.group(1)[0]
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
        o["b"] = tidy_brand(o["b"])
        o["n"] = tidy_name(o["b"], o["n"])
        o["sx"] = name_gender(o["n"]) or o["sx"]
        it = items.get(mkey(o))
        if not it:
            it = items[mkey(o)] = {"b": o["b"], "n": o["n"].strip(), "g": o["g"], "sx": list(o["sx"]), "w": o["w"],
                                   "img": o.get("img"), "lp": o["lp"], "bb": o.get("bb"), "sz": {}, "of": [], "_st": [],
                                   "_ca": [], "ca": False}
            if o["g"] in TYPES:
                it["t"] = garment_type(o["g"], o["n"])
        oi = len(it["of"])
        it["of"].append(o["u"]); it["_st"].append(o["st"]); it["_ca"].append(bool(o.get("ca")))
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
    out = []
    for it in items.values():
        # [size, price, offer, regular] plus the size's own variant id when the store has one
        it["sz"] = [[s, p, i, r] + ([v] if v else []) for s, (p, i, r, v) in it["sz"].items()]
        it.pop("_ca", None)
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
    stamps, offers, failed, raw = dict(prev.get("stores", {})), [], [], {}
    for st, fn in STORES.items():
        t = time.time()
        if REMERGE:
            raw[st] = prev_offers.get(st, [])
            for o in raw[st]:
                o.setdefault("ca", st in CA_STORES)
            offers += raw[st]
            continue
        try:
            got = fn()
            if not got and st not in dict((x[0], 1) for x in SHOPIFY_STORES) and st not in ("mec", "rei"):
                raise RuntimeError("0 items")
            if not got and len(prev_offers.get(st, [])) >= 20:     # a store rarely empties overnight: keep yesterday's
                raise RuntimeError(f"0 items today (had {len(prev_offers[st])})")
            for o in got:
                o.setdefault("ca", st in CA_STORES)
            raw[st] = got
            stamps[st] = now()
            n_sale = sum(1 for o in got if any(e[1] < e[2] * 0.99 for e in o["sz"]))
            print(f"{st}: {len(got)} items ({n_sale} on sale) in {time.time()-t:.0f}s", file=sys.stderr)
        except Exception as e:
            failed.append(st)
            raw[st] = prev_offers.get(st, [])
            for o in raw[st]:
                o.setdefault("ca", st in CA_STORES)
            msg = str(e)
            m = re.search(r"(Tunnel connection failed: \d+ \w+|\d{3} Client Error: \w+|HTTP \d{3}|no [^;]{0,60})", msg)
            print(f"{st}: FAILED ({m.group(1) if m else msg[:120]}); kept {len(raw[st])} from last run", file=sys.stderr)
        offers += raw[st]
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
    OUT.write_text(json.dumps({"v": 2, "updated": now(), "stores": stamps, "fx": {"USD": usd}, "items": items},
                              separators=(",", ":"), ensure_ascii=False))
    # the site loads sale items first: same shape, only items with at least one size on sale
    sale = [i for i in items if any(e[1] < e[3] for e in i["sz"])]   # same test as the site's % off
    (OUT.parent / "sale.json").write_text(json.dumps({"v": 2, "updated": now(), "stores": stamps, "fx": {"USD": usd}, "items": sale},
                                                     separators=(",", ":"), ensure_ascii=False))
    # raw offers go in a side file so a failed store can be restored tomorrow
    (OUT.parent / "offers.json").write_text(json.dumps(raw, separators=(",", ":"), ensure_ascii=False))
    ok = [st for st in STORES if st not in failed]
    print(f"stores OK ({len(ok)}): {', '.join(ok)}", file=sys.stderr)
    if failed:
        print(f"stores skipped ({len(failed)}): {', '.join(failed)}", file=sys.stderr)
    n_sale = sum(1 for i in items if any(e[1] < e[3] * 0.99 for e in i["sz"]))
    print(f"wrote {len(items)} items ({n_sale} on sale) from {len(offers)} store listings to {OUT}", file=sys.stderr)
    return 1 if len(failed) == len(STORES) else 0

if __name__ == "__main__":
    sys.exit(main())
