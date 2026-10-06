#!/usr/bin/env python3
"""RunFree night job (Oct 6, 2026): local US running stores whose online shop runs on RunFree (runfreeproject.com), a shop
system built for running stores. Their shops publish every product in sitemap.xml and answer two questions the shop page
itself asks: /api/product (name, brand, gender, category, photo) and /api/options (every size in stock, its price and
regular price, per store location). robots.txt allows everything but /admin.

Polite: one request per second per store (like a person clicking), all stores at once (different websites). Product
details rarely change, so they're kept for 7 days (RUNFREE_CACHE); sizes and prices are read every night. ~20-35 min.

  python scraper/runfree.py DATA_DIR          writes DATA_DIR/runfree.json (+ runfree-cache.json); the morning refresh reads it
  python scraper/runfree.py DATA_DIR charmcity     one store only (testing)
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# id, shop address, name (site STORES map has the same names), state
RUNFREE_STORES = [
    ("charlotterun", "https://shop.charlotterunning.com", "Charlotte Running Company", "NC"),
    ("terrarun", "https://shop.terrarunning.com", "Terra Running Company", "TN"),
    ("johnsrunwalk", "https://shop.johnsrunwalkshop.com", "John's Run/Walk Shop", "KY"),
    ("palmettorun", "https://shop.palmettorunningcompany.com", "Palmetto Running Company", "SC"),
    ("rushrun", "https://shop.rushrunning.com", "Rush Running", "AR"),
    ("iruntexas", "https://shop.iruntexas.net", "iRun Texas", "TX"),
    ("weststride", "https://shop.weststride.com", "West Stride", "GA"),
    ("millennium", "https://shop.millenniumrunning.com", "Millennium Running", "NH"),
    ("runningniche", "https://shop.runningniche.com", "Running Niche", "MO"),
    ("goodtimes", "https://shop.goodtimesrunningco.com", "Good Times Running Co.", "TX"),
    ("bullcity", "https://shop.bullcityrunning.com", "Bull City Running Co.", "NC"),
    ("redcoyote", "https://shop.redcoyoterunning.com", "Red Coyote Running and Fitness", "OK"),
    ("run605", "https://shop.run605.com", "605 Running Company", "SD"),
    ("point2", "https://shop.runpoint2.com", "Point 2 Running Company", "VA"),
    ("bigpeach", "https://shop.bigpeachrunningco.com", "Big Peach Running Co.", "GA"),
    ("runningzone", "https://shop.runningzone.com", "Running Zone", "FL"),
    ("manhattanrun", "https://shop.manhattanrunningco.com", "Manhattan Running Company", "KS"),
    ("charmcity", "https://shop.charmcityrun.com", "Charm City Run", "MD"),
    ("paceyourself", "https://shop.pyrunco.com", "Pace Yourself Run Co.", "NC"),
    ("runnersroost", "https://shop.runnersroost.com", "Runner's Roost", "CO"),
    ("missourirun", "https://shop.moruncocape.com", "Missouri Running Company", "MO"),
    ("trackshack", "https://shop.trackshack.com", "Track Shack", "FL"),
    ("aardvark", "https://shop.aardvarksportsshop.com", "Aardvark Sports Shop", "PA"),
    ("phillyrunner", "https://shop.philadelphiarunner.com", "Philadelphia Runner", "PA"),
]
LETTER = {"XSM": "XS", "XSMALL": "XS", "X-SMALL": "XS", "SM": "S", "SML": "S", "SMALL": "S", "MED": "M", "MD": "M", "MEDIUM": "M",
          "LG": "L", "LRG": "L", "LARGE": "L", "XLG": "XL", "XLARGE": "XL", "X-LARGE": "XL", "2XL": "XXL", "XXLARGE": "XXL"}
PACE = 1.0              # seconds between requests to one store
DETAILS_DAYS = 7        # product details re-read weekly
H = {"Content-Type": "application/json", "Accept": "application/json",
     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

# brands that sell through a parent company's name ("Deckers Outdoor Corp" = Hoka): the brand comes from the product name
BRANDS = ["Hoka", "Brooks", "Saucony", "ASICS", "New Balance", "Nike", "adidas", "On", "Altra", "Mizuno", "Salomon", "Merrell",
          "Topo Athletic", "La Sportiva", "PUMA", "Under Armour", "Diadora", "Karhu", "Newton", "inov-8", "norda", "Craft", "Scott",
          "The North Face", "Vivobarefoot", "Xero", "Mount to Coast", "NNormal", "Arc'teryx", "Teva", "OOFOS", "Hylo", "Kiprun"]


CORP = {"asics tiger corp": "ASICS", "asics america": "ASICS", "brooks sports": "Brooks", "deckers outdoor corp": "Hoka",
        "deckers": "Hoka", "on running": "On", "on inc": "On", "new balance athletics": "New Balance", "nike usa": "Nike", "nike inc": "Nike",
        "adidas america": "adidas", "amer sports": "Salomon", "mizuno usa": "Mizuno", "altra running": "Altra", "wolverine": "Saucony",
        "saucony inc": "Saucony", "puma north america": "PUMA", "under armour inc": "Under Armour"}


def brand_of(name, brand_name):
    low = f" {name.lower()} "
    for b in BRANDS:
        if re.search(rf"(?<![a-z]){re.escape(b.lower())}(?![a-z])", low) and not (b == "On" and not re.search(r"\bOn\b", name)):
            return b
    b = (brand_name or "").strip()
    k = re.sub(r"[.,]", "", b.lower())
    if k in CORP:
        return CORP[k]
    k = re.sub(r"\b(corp|corporation|inc|llc|usa|america|north america|company|co)\b", "", k).strip()
    return CORP.get(k, b.title() if b.isupper() and len(b) > 4 else b)


def name_tags(name):
    """Track Shack style: "GT-2000 15 (W-D)", "GEL-KAYANO 33 (M-4E)", "CLOUDRUNNER 3 (M)" -> (name, genders, wide, narrow)."""
    m = re.search(r"\s*\((M|W|U|MENS|WOMENS)(?:\s*-\s*([0-9A-Z]+))?\)\s*$", name, re.I)
    if not m:
        return name, None, False, False
    g = m.group(1).upper()[0]
    sx = {"M": ["men"], "W": ["women"]}.get(g, [])
    w = (m.group(2) or "").upper()
    wide = w in ("2E", "4E", "6E", "EE", "W", "WIDE") or (g == "W" and w == "D")
    narrow = w in ("2A", "AA", "N") or (g == "M" and w == "B")
    gender = {"M": " - Men's", "W": " - Women's"}.get(g, "")
    return name[:m.start()].strip() + gender, sx, wide, narrow


def group_of_cats(cats, name):
    c = " ".join(cats).lower()
    n = name.lower()
    if "footwear" in c or "shoe" in c:
        return "shoes"
    if re.search(r"\bbra\b|sports bra", n):
        return "bras"
    if re.search(r"\bsocks?\b", n) or "sock" in c:
        return "socks"
    if re.search(r"glove|mitten", n):
        return "gloves"
    if re.search(r"\b(hat|cap|visor|beanie|headband|buff|neck gaiter|trucker)\b", n):
        return "headwear"
    if re.search(r"\b(short|tight|pant|capri|skirt|skort|jogger|bottom|half tight)s?\b", n):
        return "bottoms"
    if re.search(r"\b(tee|shirt|tank|singlet|top|jacket|vest|hoodie|pullover|quarter zip|1/4 zip|half zip|long sleeve|crew|bra top)\b", n):
        return "tops" if "vest" not in n or "hydration" not in n else "packs"
    if re.search(r"hydration|pack\b|vest|belt|flask|bottle", n):
        return "packs"
    if re.search(r"\b(gel|chew|bar|drink mix|electrolyte|hydration mix|waffle|fuel)s?\b", n) or "nutrition" in c:
        return "nutrition"
    if re.search(r"light|headlamp|pole|sunglass|watch|insole|roller|massage|anti-chafe|bodyglide|body glide", n) or "accessor" in c:
        return "gear"
    return None


def width_word(w, name):
    w = (w or "").strip().lower()
    women = re.search(r"\bwom[ae]n", name, re.I)
    if re.search(r"wide|\b[246]e\b|\bee+\b|extra", w) or (women and w == "d"):
        return " Wide"
    if re.search(r"narrow|\b2a\b|\baa\b", w) or (not women and w == "b"):
        return " Narrow"
    return ""


class Store:
    def __init__(self, st, base):
        self.st, self.base, self.s, self.last = st, base, requests.Session(), 0.0

    def call(self, kind, payload):
        wait = PACE - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        for i in range(3):
            self.last = time.time()
            try:
                r = self.s.post(f"{self.base}/api/{kind}", json=payload, headers=H, timeout=30)
                if r.status_code == 429:
                    time.sleep(30 * (i + 1))
                    continue
                r.raise_for_status()
                return r.json()
            except Exception:
                if i == 2:
                    raise
                time.sleep(5 * (i + 1))

    def sitemap(self):
        r = self.s.get(f"{self.base}/sitemap.xml", headers={"User-Agent": H["User-Agent"]}, timeout=60)
        r.raise_for_status()
        return re.findall(r"<loc>(https?://[^<]+/product/(\d+)/[^<]*)</loc>", r.text)


def read_store(st, base, name, cache, now, budget):
    """Every product in the shop's sitemap -> offers in the scraper's shape (prices in USD, converted later)."""
    t0 = time.time()
    s = Store(st, base)
    urls = s.sitemap()
    c = cache.setdefault(st, {})
    offers, fresh_details, skipped = [], 0, 0
    for url, pid in urls:
        if time.time() - t0 > budget:
            print(f"  {st}: out of time after {len(offers)} products", file=sys.stderr)
            break
        d = c.get(pid)
        if not d or datetime.fromisoformat(d["t"]) < now - timedelta(days=DETAILS_DAYS):
            try:
                p = s.call("product", {"id": int(pid)})
            except Exception:
                continue
            if p.get("error"):
                continue
            d = c[pid] = {"t": now.isoformat(timespec="seconds"), "n": p.get("name") or "", "bn": p.get("brandName") or "",
                          "g": p.get("gender") or "", "cats": [x.get("name") or "" for x in p.get("categories") or []],
                          "img": p.get("imageUrl") or "", "sku": p.get("sku") or "", "live": bool(p.get("isLive")) and not p.get("dateDeleted"),
                          "instore": bool(p.get("isInStorePurchaseOnly") or p.get("inStorePurchaseOnly"))}
            fresh_details += 1
        if not d["live"] or d["instore"]:
            skipped += 1
            continue
        try:
            o = s.call("options", {"id": int(pid), "sku": d["sku"], "relay": ""})
        except Exception:
            continue
        sizes = {}
        for loc in o.get("data") or []:
            if loc.get("allowOnline") is False:
                continue
            for i in loc.get("inventory") or []:
                if i.get("allowOnline") is False or not i.get("isLive", True):
                    continue
                if (i.get("quantity") or 0) - (i.get("heldQuantity") or 0) <= 0:
                    continue
                price = float(i.get("realCost") or i.get("cost") or 0)
                reg = max(float(i.get("retail") or 0), price)
                if price <= 0:
                    continue
                size = re.sub(r"^0+(?=\d)", "", str(i.get("size") or "OS").strip())       # "06.5" -> "6.5"
                size = LETTER.get(size.upper().replace(" ", ""), size)                           # "MED" -> "M"
                lab = size + (width_word(i.get("sizeAppend"), d["n"]) if i.get("sizeAppend") else "")
                if lab not in sizes or price < sizes[lab][0]:
                    sizes[lab] = (price, reg)
        if not sizes:
            continue
        nm, tag_sx, wide, narrow = name_tags(d["n"])
        if narrow:
            continue
        g = group_of_cats(d["cats"], nm)
        if not g or re.search(r"lifestyle", " ".join(d["cats"]), re.I) and g != "shoes":
            continue
        sx = tag_sx if tag_sx is not None else {"M": ["men"], "W": ["women"]}.get(d["g"], [])
        img = d["img"]
        if img and not img.startswith("http"):
            img = base + img
        offers.append({"st": st, "b": brand_of(nm, d["bn"]), "n": nm, "u": url, "g": g, "sx": sx, "w": wide, "img": img or None,
                       "lp": max(r for _, r in sizes.values()), "bb": None, "sz": [[k, p, r] for k, (p, r) in sizes.items()]})
    print(f"  {st}: {len(urls)} in sitemap, {len(offers)} in stock online, {fresh_details} details refreshed, "
          f"{skipped} in-store only or off, {time.time() - t0:.0f}s", file=sys.stderr)
    return offers


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    now = datetime.now(timezone.utc)
    cache_f, out_f = out_dir / "runfree-cache.json", out_dir / "runfree.json"
    try:
        cache = json.loads(cache_f.read_text())
    except Exception:
        cache = {}
    try:
        prev = json.loads(out_f.read_text())
    except Exception:
        prev = {"stores": {}}
    stores = [x for x in RUNFREE_STORES if not only or x[0] in only]
    budget = float(os.environ.get("RUNFREE_BUDGET") or 75 * 60)   # per store: at most 75 minutes (the job has 2 hours)

    def one(x):
        st, base, name, state = x
        try:
            return st, read_store(st, base, name, cache, now, budget), None
        except Exception as e:
            return st, None, str(e)[:160]
    with ThreadPoolExecutor(len(stores) or 1) as ex:
        results = list(ex.map(one, stores))
    data = {"updated": now.isoformat(timespec="seconds"), "stores": dict(prev.get("stores", {}))}
    for st, offers, err in results:
        if offers:
            data["stores"][st] = {"updated": now.isoformat(timespec="seconds"), "offers": offers}
        else:
            print(f"  {st}: FAILED ({err or 'nothing in stock online'}); kept the last good read", file=sys.stderr)
            if st in data["stores"]:
                data["stores"][st]["failed"] = err or "nothing in stock online"
    out_f.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    cache_f.write_text(json.dumps(cache, separators=(",", ":"), ensure_ascii=False))
    ok = sum(1 for _, o, _ in results if o)
    print(f"RunFree: {ok} of {len(stores)} stores read, {sum(len(o or []) for _, o, _ in results)} products", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
