#!/usr/bin/env python3
"""Running Discount scraper.

Pulls the full running catalogue (full price and on sale) from Altitude Sports, The Last Hunt,
The Feed and Sea2Sky Nutrition, merges the same product sold by several stores, and writes
site/deals.json in the compact format the page reads:

  {v:2, updated, stores:{id: iso}, items:[{b,n,g,sx,w,img,lp,bb,sz:[[size,price,offer]],of:[url,...]}]}

  sz = in-stock sizes: [size, today's lowest price, index of the offer (store link) that has it,
  that size's regular price]. A size is on sale when its price is below its regular price.
  lp = highest regular price across sizes (for display only).

If one store fails, its items from the previous run are kept so the site never goes blank.
Usage:  python scraper/scrape.py [out_path] [--remerge]
"""
import json, re, sys, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
import requests

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
REMERGE = "--remerge" in sys.argv   # rebuild deals.json from offers.json without scraping (for testing)
OUT = Path(ARGS[0] if ARGS else Path(__file__).resolve().parents[1] / "site" / "deals.json")
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128 Safari/537.36", "Accept-Language": "en-CA,en;q=0.9"})

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def get(url, tries=4):
    for i in range(tries):
        try:
            r = S.get(url, timeout=45)
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
    ("shoes",     r"\bshoes?\b|\bspikes\b"),
    ("bras",      r"\bbras?\b"),
    ("socks",     r"\bsocks?\b"),
    ("gloves",    r"\bgloves?\b|\bmitts?\b|mittens"),
    ("watches",   r"\bwatch(es)?\b"),
    ("headwear",  r"\bhats?\b|\bcaps?\b|gocap|trlcap|beanie|toque|tuque|headband|\bbuffs?\b|neck ?gaiter|visor"),
    ("packs",     r"hydration (vest|pack)|race vest|running vest|backpack|\bbelts?\b|waist ?pack|\bpinnacle\b|\bvest \d|\d+ ?l\b"),
    ("bottoms",   r"(?<!short sleeve )\bshorts\b|\bshort\b(?! sleeve)|tights?\b|\bpants?\b|leggings?|joggers?|skirts?|skorts?|boxers?|briefs?"),
    ("tops",      r"t-?shirts?|\btees?\b|\bshirts?|\btops?\b|tanks?|singlets?|jackets?|hood(ie|y)|\bvests?\b|gilets?|jersey|sweaters?|base ?layer|pullovers?|fleece|anorak|windbreaker|\bcrew\b|half zip|quarter zip|1/2 zip|1/4 zip"),
    ("gear",      r"poles?\b|headlamp|bottles?|flasks?|sunglass|sleeves?\b|gaiters|roller|massage|insoles?"),
]
def group_of(*texts):
    t = " ".join(x for x in texts if x).lower()
    for g, rx in RULES:
        if re.search(rx, t):
            return g
    return None

WORD = {"ONE SIZE": "OS", "O/S": "OS", "NA": "OS", "": "OS", "X-SMALL": "XS", "SMALL": "S", "MEDIUM": "M",
        "LARGE": "L", "X-LARGE": "XL", "XX-LARGE": "2XL", "XXL": "2XL", "XXXL": "3XL", "XXS": "2XS"}
def norm_size(s):
    s = str(s or "").strip()
    return WORD.get(s.upper(), s)

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
        sz = norm_size(attr(v["attributesRaw"], "size_1") or attr(v["attributesRaw"], "size"))
        price = round((disc if disc is not None else reg * 100) / 100, 2)
        if sz not in sizes or price < sizes[sz][0]:
            sizes[sz] = (price, reg)
    if not sizes:
        return None                      # nothing in stock
    if not img:
        a = (mv.get("assets") or [{}])[0].get("sources") or [{}]
        img = a[0].get("uri")
    return {"st": st, "b": attr(A, "brand_name") or "", "n": name, "u": f"{base}/p/{slug}", "g": g,
            "sx": sx, "w": wide, "img": img, "lp": lp, "bb": None, "sz": [[k, pr, rg] for k, (pr, rg) in sizes.items()]}

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

BB = re.compile(r"\s*\(?\s*best\s*by:?\s*([0-9/.-]+)\s*\)?", re.I)

def shopify_products(base):
    prods, page = [], 1
    while True:
        batch = get(f"{base}/products.json?limit=250&page={page}").json()["products"]
        if not batch:
            break
        prods += batch
        page += 1
    return prods

def shopify_items(st, base, prods, group_fn, fx=1.0):
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
            rest = " / ".join(x for x in (v.get("option2"), v.get("option3")) if x)
            key = o1 if len(opts) > 1 else ""
            label = rest if len(opts) > 1 else o1
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
            if lab not in b["sz"] or cad < b["sz"][lab][0]:
                b["sz"][lab] = (cad, reg)
            b["bb"] = b["bb"] or bb
        for key, b in buckets.items():
            out.append({"st": st, "b": p.get("vendor") or "", "n": p["title"] + (f" · {key}" if key else ""),
                        "u": f"{base}/products/{p['handle']}?variant={b['vid']}", "g": g, "sx": [], "w": False,
                        "img": img, "lp": round(b["lp"] * fx, 2), "bb": b["bb"],
                        "sz": [[k, pr, rg] for k, (pr, rg) in b["sz"].items()]})
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
    fx = usd_cad()                   # The Feed is a US store; show CAD
    print(f"  thefeed: USD->CAD {fx}", file=sys.stderr)
    return shopify_items("thefeed", "https://thefeed.com", shopify_products("https://thefeed.com"), feed_group, fx)

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
    return shopify_items("sea2sky", base, shopify_products(base), s2s_group)

# ---------------------------------------------------------------- merge + main
STORES = {
    "altitude": lambda: scrape_commercetools("altitude", "https://www.altitude-sports.com"),
    "lasthunt": lambda: scrape_commercetools("lasthunt", "https://www.thelasthunt.com"),
    "thefeed": scrape_thefeed,
    "sea2sky": scrape_sea2sky,
}

def name_gender(n):
    """Product names ("... - Women's", "Mens Pressio Tee") beat a store's gender tag, which is
    often "unisex" for women's-cut gear."""
    low = n.lower()
    w = bool(re.search(r"\bwom[ae]n'?s?\b", low))
    m = bool(re.search(r"(?<!wo)\bmen'?s?\b", low))
    return ["women"] if w and not m else ["men"] if m and not w else None

def mkey(o):
    name = re.sub(r"[^a-z0-9]+", " ", o["n"].lower()).strip()
    return (o["b"].lower().strip(), name, o["w"], o["g"])

def merge(offers):
    """Same product at several stores -> one item; each size keeps the cheapest store."""
    items = {}
    for o in offers:
        o["sx"] = name_gender(o["n"]) or o["sx"]
        it = items.get(mkey(o))
        if not it:
            it = items[mkey(o)] = {"b": o["b"], "n": o["n"].strip(), "g": o["g"], "sx": list(o["sx"]), "w": o["w"],
                                   "img": o.get("img"), "lp": o["lp"], "bb": o.get("bb"), "sz": {}, "of": [], "_st": []}
        oi = len(it["of"])
        it["of"].append(o["u"]); it["_st"].append(o["st"])
        it["lp"] = max(it["lp"], o["lp"])
        it["img"] = it["img"] or o.get("img")
        it["bb"] = it["bb"] or o.get("bb")
        it["sx"] = sorted(set(it["sx"]) | set(o["sx"]))
        for size, price, reg in o["sz"]:
            cur = it["sz"].get(size)
            if cur is None or price < cur[0]:
                it["sz"][size] = (price, oi, reg)
    out = []
    for it in items.values():
        it["sz"] = [[s, p, i, r] for s, (p, i, r) in it["sz"].items()]
        out.append(it)
    return out

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
            offers += raw[st]
            continue
        try:
            got = fn()
            if not got:
                raise RuntimeError("0 items")
            raw[st] = got
            stamps[st] = now()
            n_sale = sum(1 for o in got if any(p < r * 0.99 for _, p, r in o["sz"]))
            print(f"{st}: {len(got)} items ({n_sale} on sale) in {time.time()-t:.0f}s", file=sys.stderr)
        except Exception as e:
            failed.append(st)
            raw[st] = prev_offers.get(st, [])
            print(f"{st}: FAILED ({e}); kept {len(raw[st])} from last run", file=sys.stderr)
        offers += raw[st]
    items = merge(offers)
    for it in items:
        it.pop("_st", None)
    items.sort(key=lambda i: (i["g"], i["b"].lower(), i["n"].lower()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"v": 2, "updated": now(), "stores": stamps, "items": items},
                              separators=(",", ":"), ensure_ascii=False))
    # raw offers go in a side file so a failed store can be restored tomorrow
    (OUT.parent / "offers.json").write_text(json.dumps(raw, separators=(",", ":"), ensure_ascii=False))
    n_sale = sum(1 for i in items if any(p < r * 0.99 for _, p, _, r in i["sz"]))
    print(f"wrote {len(items)} items ({n_sale} on sale) from {len(offers)} store listings to {OUT}", file=sys.stderr)
    return 1 if len(failed) == len(STORES) else 0

if __name__ == "__main__":
    sys.exit(main())
