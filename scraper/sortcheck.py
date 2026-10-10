#!/usr/bin/env python3
"""Sorting check (Oct 7, 2026; Bastien: "this seems to be the most common bug we find"): items in the wrong category,
the wrong gender or shoe type, junk names, one brand split in two. Runs in every health check (morning and afternoon)
and by hand on one store after adding it:

  python scraper/sortcheck.py site/deals.json                 everything, both sides if deals-us.json is beside it
  python scraper/sortcheck.py site/deals.json runuphill.ca    one store (its domain)

Heuristics: a hit is "look at this", not always a bug. Fix real ones in scrape.py (tidy_* rules), then rerun.
"""
import collections
import json
import re
import sys
from pathlib import Path

FOOD = re.compile(r"\bgels?\b|electrolyte|drink|\bmix\b|\bbars?\b|chews?|gumm|\btabs?\b|tablets|capsules?|caps\b.*\d+ ?c(oun)?t|powder|"
                  r"protein|energy|fuel|carb|recovery|hydration|salt|caffeine|waffle|wafel|stroop|cookie|nut butter|honey|jerky|coffee|"
                  r"\btea\b|vitamin|supplement|ketone|bicarb|creatine|collagen|\boats?\b|bites?\b|snack|syrup|juice|puree|shot\b|"
                  r"servings?|flavou?r|pre-?workout|beet|nitrate|mct|creamer|bundle|sampler|variety|tryout|pack\b|kit\b|box\b|lytes|\d+ ?caps\b|"
                  r"pouch|gaufre|boisson|jujube|barre|recharge|érable|erable|\d+ ?(g|ml|oz|ct)\b", re.I)
GEARISH = re.compile(r"\b(gloves?|mitts?|socks?|caps?|hats?|beanie|toque|headband|neckwear|buff|headlamp|lights?|vest|belt|"
                     r"bottle|flask|bag|towel|sleeves?|tape|massage|ball|spikes?|shirt|tee|tank|shorts?|tights?|jacket|"
                     r"sunglasses|poles?|insoles?)\b", re.I)
SHOE_NOT = re.compile(r"\b(laces?|lacets?|cleaner|cleaning|repel|spray|wipes|deodou?ri[sz]er|shoe ?horn|socks?|insoles?|"
                      r"t-?shirt|tee|shorts|tights|jacket|hat|cap|bottle)\b", re.I)
CLOTH_IN_GEAR = re.compile(r"\b(t-?shirt|tee|singlet|tank top|hoodie|jacket|shorts|tights|leggings|pants|joggers|bra)\b", re.I)
GEAR_OK = re.compile(r"sunglass|eye ?jacket|suture jacket|lens|bottle|flask|belt|band|strap|patch|wash|hanger|holder|clip|"
                     r"bundle|gift|box|pack of|wipes", re.I)
BOTTOM_W = re.compile(r"\b(shorts?(?! sleeve)|tights?|leggings?|joggers?|pants?|skirt|skort|capri)\b", re.I)
TOP_W = re.compile(r"\b(top|shirt|t-?shirt|tee|jacket|hood(ie|y)?|vest|bra|singlet|tank|crew|sleeve|jersey|layer|bundle|"
                   r"pullover|half[- ]zip|quarter[- ]zip|1/4 zip|anorak)\b", re.I)   # not "set": a top + bottom set can sit under either
TRAIL_ONLY = re.compile(r"speedgoat|peregrine|cascadia|mafate|tecton|kjerag|tomir|agravic|vectiv|offtrail|speedcross|"
                        r"thundercross|ultra glide|lone peak|olympus|mutant|bushido|jackal|akasha|prodigio|xodus|caldera|"
                        r"catamount|torrent|challenger|zinal|hierro|wildhorse|trabuco|norvan|sense ride|genesis|xa pro|"
                        r"\btrail\b", re.I)
JUNK = re.compile(r"(?i:build your own bundle|bundle\d{3,}|needs description|\btest product\b|do not (buy|use)|\bplaceholder\b)|"
                  r"^\W*$|^(?=.*\d)[A-Z0-9-]{6,}$")      # a code instead of a name: "221739588"
COMPANY = re.compile(r"\b(inc|corp|llc|ltd|usa|us|outlet|vermont|optics|nutrition|hydration|medical|international)\b\.?$", re.I)


# checked by hand and fine (brand + name start): a cap whose colour is "Leather Jacket", a bug jacket sold with mitts
OK = re.compile(r"^(SOAR Running Artefact Cap|Ben's InvisiNet|Aetrex L\d|Satisfy (TheRocker|Adizero)|rabbit (High Country|Dream Chaser)|"
                r"Tracksmith Eliot|Tortoise & Hare Trofeo|City Park Runners XACT|CEP Pro Run Optaspeed|.*Mystery Nutrition|"
                r"BlackToe Mix Pack|Craft (Nordlite|Xplor))", re.I)


def host(i):
    u = (i.get("of") or [i.get("lp") or ""])[0] or ""
    return re.sub(r"^https?://(www\.)?", "", str(u)).split("/")[0]


def bkey(b):
    t = (b or "").lower().replace("æ", "ae").replace("ø", "o").replace("ü", "u").replace("ä", "a").replace("é", "e")
    t = re.sub(r"\b(sports?|running|athletics?|apparel|footwear|the|inc|co|corp|company|ltd|usa|us|outlet|optics|"
               r"nutrition|hydration|medical|vermont|sunglasses)\b", "", t)
    return re.sub(r"[^a-z0-9]", "", t)


def check(items, store=None):
    """[(rule, plain-language label, [examples "Brand Name (category, store)"])], biggest first."""
    if store:
        items = [i for i in items if store in [host({"of": [u]}) for u in (i.get("of") or [])]]
    hits = collections.defaultdict(list)
    for i in items:
        b, n, g, sx, t = i.get("b") or "", i.get("n") or "", i.get("g"), i.get("sx") or [], i.get("t")
        ex = f"{b} {n} ({g}, {host(i)})"
        if OK.search(f"{b} {n}"):
            continue
        if JUNK.search(n):
            hits["junk"].append(ex)
        if g == "nutrition" and not FOOD.search(n) and GEARISH.search(n):
            hits["food"].append(ex)
        if g == "shoes" and SHOE_NOT.search(n) and not re.search(r"\bshoes?\b|running|trail|racer|spike", n, re.I):
            hits["shoes"].append(ex)
        if g in ("gear", "packs", "watches", "nutrition", "socks", "gloves", "headwear") and CLOTH_IN_GEAR.search(n) \
                and not GEAR_OK.search(n):
            hits["cloth"].append(ex)
        if g == "tops" and BOTTOM_W.search(n) and not TOP_W.search(n):
            hits["tops"].append(ex)
        if g == "bottoms" and TOP_W.search(n) and not BOTTOM_W.search(n) and not re.search(r"bottoms?|brief|boxer", n, re.I):
            hits["bottoms"].append(ex)
        if re.search(r"\bwomen'?s\b|\bfemme\b", n, re.I) and sx == ["men"] and not re.search(r"\bmen'?s\b", n, re.I):
            hits["gender"].append(ex)
        if re.search(r"(?<!wo)\bmen'?s\b|\bhomme\b", n, re.I) and not re.search(r"women", n, re.I) and sx == ["women"]:
            hits["gender"].append(ex)
        if g == "shoes" and t in ("daily", "race") and TRAIL_ONLY.search(n) and not re.search(r"road", n, re.I):
            hits["type"].append(f"{ex} typed {t}")
        if re.search(r" - .* - | - (men|women)'s$", b, re.I):
            hits["brandname"].append(ex)
    # the odd one out for its brand (Oct 8: a Ciele cap and goodr sunglasses under Nutrition because of the word "Bar"):
    # a brand that is mostly something else, with one item filed as food or as a shoe
    per = collections.defaultdict(collections.Counter)
    for i in items:
        per[i.get("b") or ""][i.get("g")] += 1
    for i in items:
        b, g = i.get("b") or "", i.get("g")
        tot = sum(per[b].values())
        if b and g in ("nutrition", "shoes") and tot >= 8 and per[b][g] / tot < 0.08 and not OK.search(f"{b} {i.get('n')}") \
                and not (g == "shoes" and re.search(r"shoe|running|trail", i.get("n") or "", re.I)):
            hits["odd"].append(f"{b} {i.get('n')} ({g}, {host(i)}; {b} is mostly {per[b].most_common(1)[0][0]})")
    for i in items:   # a sock brand's crew sock under Tops ("Darn Tough Lifestyle | Crew")
        b, g = i.get("b") or "", i.get("g")
        tot = sum(per[b].values())
        if b and g in ("tops", "bottoms") and tot >= 8 and per[b]["socks"] / tot >= 0.8 \
                and not re.search(r"t-?shirt|\btee\b|hood|jacket|sweat|pullover|\btank\b|shorts?\b|pants?\b|tights?\b|sleeve|"
                                  r"boxer|brief|underwear|legging|\btop\b|shirt|bralette|bra\b|jogger", i.get("n") or "", re.I):
            hits["odd"].append(f"{b} {i.get('n')} ({g}, {host(i)}; {b} is mostly socks)")
    # one brand under two spellings
    c = collections.Counter(i.get("b") or "" for i in items)
    groups = collections.defaultdict(list)
    for b in c:
        groups[bkey(b)].append(b)
    for k, bs in groups.items():
        if len(bs) > 1 and len(k) >= 3:
            hits["brands"].append(" = ".join(f"{b} ({c[b]})" for b in sorted(bs, key=lambda x: -c[x])))
    LABEL = {"junk": "junk listings (saved bundles, placeholders)", "food": "non-food under Nutrition",
             "shoes": "non-shoes under Shoes (laces, sprays, socks…)", "cloth": "clothing under gear/accessories",
             "tops": "bottoms under Tops", "bottoms": "tops under Bottoms", "gender": "name and gender disagree",
             "type": "trail shoes typed road/race", "brandname": "a product name in the brand field",
             "brands": "one brand under two spellings", "odd": "food or shoes from a brand that sells neither"}
    return sorted(((k, LABEL[k], v) for k, v in hits.items()), key=lambda x: -len(x[2]))


def report(items, store=None, side=""):
    out = []
    for k, label, ex in check(items, store):
        out.append((k, f"Sorting check{side}, {label}: {len(ex)} (e.g. {'; '.join(ex[:3])})"))
    return out


if __name__ == "__main__":
    p = Path(sys.argv[1] if len(sys.argv) > 1 else "site/deals.json")
    store = sys.argv[2] if len(sys.argv) > 2 else None
    for f, side in ((p, "Canada"), (p.parent / "deals-us.json", "USA")):
        if not f.exists():
            continue
        items = json.loads(f.read_text())["items"]
        res = check(items, store)
        print(f"\n=== {side}{' / ' + store if store else ''}: {len(items) if not store else ''} {sum(len(x[2]) for x in res)} to look at")
        for k, label, ex in res:
            print(f"\n## {label}: {len(ex)}")
            for e in ex[:40]:
                print("   ", e)
