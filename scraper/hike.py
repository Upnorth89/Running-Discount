#!/usr/bin/env python3
"""Hiking catalogue (Oct 25, 2026; Bastien: "focus our energy on gathering as many hiking stores and hiking gear we can find ...
continue cataloging it all so it is clean"; "we always input both [sale and full price] so people can track").

Reads the hiking (and camping) sections of outdoor stores and brands, sorts every product into the hiking categories, and merges
them with the running site's own merge (same sizes, brands, genders, card shape). Hidden until the Hiking tab launches (~Nov 17):

  python scraper/hike.py OUTDIR            read every store -> OUTDIR/hike-offers.json (raw, per store) + the merged files
  python scraper/hike.py OUTDIR --remerge  merge OUTDIR/hike-offers.json again (no store visits)

Merged files: deals-hike.json / sale-hike.json (Canada), deals-hike-us.json / sale-hike-us.json (USA), camp.json + camp-us.json
(camping: tents, sleeping bags, mats, stoves; Bastien Oct 25: "read the camping stuff but not publish it").

Hiking categories (the running site's groups, so cards, sizes and filters work the same; types = the buttons under each):
  shoes   hike (low hiking shoes), boot (mid/high, mountaineering), approach
  tops    shell (rain), insulated (down/synthetic), fleece, wind (softshell/wind), base (base layers), shirt (tees, sun shirts)
  bottoms pant, rain, short, base
  packs   day (under 35 L), overnight (35 L+)
  gear    pole, light, water, traction, safety, nav, gaiter, sun
  socks, gloves, headwear
Trail running shoes stay on the running side; ski, bike, paddling, hunting, climbing hardware, kids and casual lines are left out.
Polite: one page every 1.5 s per store, robots.txt checked for each store (STORES.md "Hiking"); a 403/429 wall = stop.
"""
import collections
import os
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib import robotparser
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
import scrape as s  # noqa: E402

UA = "TheGearFoxBot/1.0 (+https://thegearfox.com)"
PAUSE = 1.5

# ---------------------------------------------------------------- what is (and isn't) hiking
SKIP = re.compile(
    r"\b(ski|skis|skiing|snowboard\w*|splitboard|bindings?|skins?|avalanche|beacon|probe|shovel|freeride|backcountry ski|nordic|"
    r"cross[- ]country|xc ski|bike|biking|cycling|mtb|bibs?|chamois|swim\w*|bikini|paddl\w*|kayak\w*|canoe|pfd|life ?jacket|"
    r"wetsuit|neoprene|surf|wader|fishing|hunting|hunter|camo|blaze orange|golf|yoga|pickleball|tennis|kids?|youth|junior|"
    r"jr|toddler|baby|infant|boys?|girls?|dog|pet|leash|gift ?card|e-?gift|book|guide ?book|maps?|sticker|decal|poster|"
    r"calendar|slippers?|booties|sandals?|flip[- ]flops?|clogs?|slides?|winter boots?|snow boots?|rain boots?|apres|pac boots?|"
    r"jeans?|denim|chinos?|dress|blazer|suit|underwear|briefs?|boxers?|bras?|bralette|lingerie|pajamas?|robe|harness|"
    r"carabiner|quickdraw|belay|rope|chalk|climbing shoes?|crash ?pad|ice axe|ice screw|helmet|umbrella|luggage|duffel|"
    r"suitcase|wallet|tote|purse|laptop|coffee|beans|food|meal|snack|bar|candy|gum|knife|knives|multi-?tool|axe|saw|"
    r"hatchet|gift set|mask|scrunchie|keychain|key ?chain|sweatpants|joggers?|sweatshirt|cardigan|flannel|"
    r"scarf|socks? liner|run(ning)?\b|trail run\w*|race|racing|track|spikes?|insoles?|laces?|shoe ?care|wax|spray|"
    r"cleaner|repair|patch|warranty|rental|demo|sample sale|replacement|spare|parts?|buckle|strap only|lid)\b", re.I)
# Allowed even when a SKIP word appears: "Running Shorts" are skipped, but these names are hiking gear
KEEP = re.compile(r"\b(trekking|hiking|backpacking|approach|bear (spray|canister|bell)|first[- ]aid|emergency|water (filter|bottle)|"
                  r"purif|microspikes?|nanospikes?|crampons?|traction)\b", re.I)
# fashion, ski, work and city-coat labels some outdoor stores also carry: not hiking gear, whatever the item
NOT_HIKE_BRANDS = {"barbour", "bogner", "bogner fire + ice", "duer", "krimson klover", "moose knuckles", "mackage", "moncler", "nobis",
                   "woolrich", "levi's", "carhartt", "herschel", "herschel supply", "roots", "lululemon", "vuori", "on", "on running",
                   "spyder", "goldwin", "perfect moment", "obermeyer", "halfdays", "rossignol", "picture", "picture organic clothing",
                   "orage", "karbon", "686", "burton", "volcom", "sorel", "kamik", "baffin", "blundstone", "ugg", "pajar", "quartz co",
                   "quartz co.", "canada goose", "rudsak", "soia & kyo", "tentree", "toad&co", "toad & co", "faherty", "birkenstock",
                   "teva", "crocs", "hey dude", "chaco", "olukai", "reef", "rainbow", "dakine", "armada", "faction", "volkl", "atomic",
                   "fischer", "salomon snow", "helly hansen ski", "sweaty betty", "beyond yoga", "alo", "free people", "varley"}
CASUAL = re.compile(r"\b(cotton|teddy|corduroy|cord|denim|shacket|shirt[- ]jacket|work jacket|bomber|trench|wool coat|overcoat|"
                    r"peacoat|sweater|cardigan|knit|chore|canvas|moleskin|overalls?|dungarees?|blazer|loungewear|lounge|sleep)\b", re.I)
CASUAL_TOP = re.compile(r"\b(logo|graphic|tee shirt|t-shirt|tee|tank|polo|henley|button[- ]?(up|down)|crew ?neck sweatshirt)\b", re.I)

CAMP = [("tent", r"\btents?\b|\bshelters?\b|\btarps?\b|\bbivy\b|\bbivvy\b|\bhammocks?\b|\bmid\s?\d|\bpyramid\b|tent (stakes?|poles?|footprint)"),
        ("bag", r"sleeping ?bags?|\bquilts?\b|\bunder ?quilts?\b|sac de couchage|bag liner|sleep(ing)? liner"),
        ("mat", r"sleeping (pads?|mats?)|\b(air|foam|camp) (pads?|mats?|mattress)|\bpads?\b(?=.*\b(r[- ]?value|sleep|inflat))|\bpillows?\b|matelas"),
        ("kitchen", r"\bstoves?\b|\bcook(set|ware|ing)?\b|\bpots?\b|\bpans?\b|\bkettle\b|\butensils?\b|\bsporks?\b|\bcups?\b|\bbowls?\b|"
                    r"fuel( canister)?|\bisobutane\b|\bwindscreen\b|\bjetboil\b|\bpocket ?rocket\b"),
        ("other", r"\blanterns?\b|\bchairs?\b|\bcots?\b|\bcoolers?\b|\btables?\b|bear (canister|vault|bag)|ursack|food bag|"
                  r"\bdry ?bags?\b|stuff ?sacks?|compression sacks?|\btowels?\b|camp shoes?")]
CAMP = [(t, re.compile(rx, re.I)) for t, rx in CAMP]

SHOE = re.compile(r"\b(boots?|shoes?|footwear|chaussures?|bottes?|souliers?|approach|hikers?|mids?|gtx|gore-?tex|waterproof)\b", re.I)
PACK_L = re.compile(r"(?<![\d.])(\d{2,3})\s?(?:\+\s?\d+\s?)?(?:l|liters?|litres?)\b", re.I)

RULES = [  # (group, type, pattern); first match wins, tested on the product name (store's type/collection only as a hint)
    ("socks", None, r"\bsocks?\b|\bchaussettes?\b|\bbas\b"),
    ("gloves", None, r"\bgloves?\b|\bmitts?\b|\bmittens?\b|\bgants?\b|\bmitaines?\b"),
    ("gear", "gaiter", r"\bgaiters?\b(?!.*\bneck\b)|\bgu[êe]tres?\b"),
    ("headwear", None, r"\bhats?\b|\bcaps?\b(?![- ]sleeve)|\bbeanies?\b|\btoques?\b|\btuques?\b|\bbuffs?\b|neck ?gaiter|"
                       r"\bbalaclavas?\b|\bheadbands?\b|\bvisors?\b|\bsun ?hats?\b|\bbucket\b|\bchapeau\b|\bcasquettes?\b"),
    ("gear", "pole", r"\b(trekking|hiking|walking|z|carbon|distance|trail) poles?\b|\bpoles?\b|\bb[âa]tons?\b"),
    ("gear", "light", r"\bheadlamps?\b|\bflashlights?\b|\bfrontales?\b|\blampes? frontales?\b|\btorch\b"),
    ("gear", "water", r"water (filters?|bottles?|treatment|purif\w*)|\bfilters?\b|\bpurifiers?\b|\bsteripen\b|\bsqueeze\b|"
                      r"\breservoirs?\b|\bbladders?\b|\bhydration (system|bladder|reservoir)\b|\bbottles?\b|\bgourdes?\b|"
                      r"\bsoft ?flasks?\b|aquatabs|purification tablets?"),
    ("gear", "traction", r"microspikes?|nanospikes?|crampons?|\btraction\b|ice cleats?|yaktrax|trail crampons?|kahtoola|\bspikes\b"),
    ("gear", "safety", r"bear (spray|bangers?|bells?)|first[- ]aid|\bemergency\b|\bsurvival\b|\bwhistles?\b|space blanket|"
                       r"\bbivvy\b|blister|moleskin|\bsos\b|\binreach\b|satellite (messenger|communicator)|\bplb\b"),
    ("gear", "nav", r"\bgps\b|\bcompass\w*\b|\baltimeter\b|\bboussoles?\b"),
    ("gear", "sun", r"sunglass\w*|\blunettes\b|\bgoggles?\b"),
    ("packs", None, r"\bbackpacks?\b|\bday ?packs?\b|\brucksacks?\b|\bpacks?\b(?! of)(?!able)|\bsac(s)? [àa] dos\b|"
                    r"\bhip ?packs?\b|\bwaist ?packs?\b|\bfanny ?packs?\b|\blumbar\b|\bvest pack\b"),
    ("bottoms", "rain", r"\b(rain|waterproof|hard ?shell|shell|storm|gtx|gore-?tex|h2no|precip)\b.*\b(pants?|trousers?|bottoms?|bibs?)\b|"
                        r"\b(pants?|trousers?)\b.*\b(rain|waterproof|shell)\b|\bpantalons? imper"),
    ("bottoms", "base", r"\b(base ?layer|baselayer|thermal|long ?(johns|underwear)|merino)\b.*\b(bottoms?|pants?|tights?|leggings?)\b|"
                        r"\b(bottoms?|tights?|leggings?)\b"),
    ("bottoms", "short", r"(?<!short sleeve )\bshorts\b|\bshort\b(?![- ]sleeve)|\bskorts?\b|\bbermudas?\b"),
    ("bottoms", "pant", r"\bpants?\b|\btrousers?\b|\bpantalons?\b|\bzip[- ]off\b|\bconvertible\b(?!.*jacket)|\bknickers?\b"),
    ("tops", "shell", r"\b(rain|waterproof|hard ?shell|storm|gtx|gore-?tex|h2no|futurelight|precip|torrentshell|beta|zeta|alpha|"
                      r"microlight|aspire|helium|foray|interstellar|stretch ozonic|minimalist)\b.*\b(jackets?|anoraks?|shells?|parkas?|ponchos?)\b|"
                      r"\b(shell|rain) (jackets?|coats?)\b|\bponchos?\b|\bmanteaux? (de pluie|imper)"),
    ("tops", "insulated", r"\b(down|puff\w*|insulat\w*|synthetic|primaloft|thermoball|nano puff|nano-?air|atom|cerium|ghost ?whisperer|downwool|"
                          r"proton|kor airshield|thermawool|thermal ?wool|"
                          r"micro puff|parka|belay|duvet|plumes?|isol[ée]s?)\b"),
    ("tops", "fleece", r"\bfleece\b|\bpolaire\b|\bpolartec\b|\bgrid\b|\bR1\b|\bthermal pro\b|\bmicro ?fleece\b|\bsherpa\b"),
    ("tops", "wind", r"\bsoft ?shell\b|\bwind\w*\b|\bcoupe[- ]vent\b|\bgamma\b|\bsquamish\b|\bhoudini\b"),
    ("tops", "base", r"\b(base ?layer|baselayer|thermal|first ?layer|merino \d{3}|\d{3} merino)\b|\b(crew|zip[- ]?neck|1/4 zip|half[- ]zip)\b.*\bmerino\b"),
    ("tops", "insulated", r"\bvests?\b|\bgilets?\b"),
    ("tops", "@", r"\bjackets?\b|\banoraks?\b|\bmanteaux?\b|\bvestes?\b|\bcoats?\b|\bponcho\b|\bhalf[- ]zip\b|\b1/2 zip\b"),
    ("tops", "shirt", r"\bshirts?\b|\btees?\b|\bt-shirts?\b|\b(tank|crop|base ?layer) tops?\b|\btanks?\b|\bhood(y|ie)\b|\bsun hood\b|\blong sleeve\b|"
                      r"\bshort sleeve\b|\bcrew\b|\bpullovers?\b|\bquarter[- ]zip\b|\b1/4 zip\b|\bpolo\b|\bchandails?\b"),
]
RULES = [(g, t, re.compile(rx, re.I)) for g, t, rx in RULES]
# a jacket whose name doesn't say what it is: brand codes (Mammut HS/IN/SO/ML), then the store's own section
JACKET_CODE = [("shell", re.compile(r"\bHS\b|\bhard ?shell\b", re.I)), ("insulated", re.compile(r"\bIN\b|\bpadded\b|\bwinter\b|\bthermo\b", re.I)),
               ("wind", re.compile(r"\bSO\b")), ("fleece", re.compile(r"\bML\b|\bmid-?layer\b|\bpile\b|\bhalf[- ]zip\b|\b1/2 zip\b|\bquarter[- ]zip\b"))]
JACKET_HINT = [("shell", r"hard[-_ ]?shell|technical-shells|rain|waterproof"), ("insulated", r"insulat|down|synthetic|parka|winter|puff"),
               ("fleece", r"fleece|mid-?layer"), ("wind", r"soft[-_ ]?shell|wind"), ("base", r"base[-_ ]?layer"), ("shirt", r"shirt|tee|tops?$")]


def jacket_type(n, hint):
    for t, rx in JACKET_CODE:
        if rx.search(n):
            return t
    for t, rx in JACKET_HINT:
        if re.search(rx, hint or "", re.I):
            return t
    return None
# a store's own section names that say what a product is when its name doesn't ("Moab 3 Mid": a boot)
HINT = [("shoes", r"boot|shoe|footwear|chaussure|soulier|approach"), ("socks", r"sock"), ("gloves", r"glove|mitt"),
        ("headwear", r"hat|cap|headwear|beanie|tuque|toque"), ("packs", r"pack|sac-a-dos|sacs-a-dos"),
        ("bottoms", r"pant|short|bottom|tight"), ("tops", r"jacket|fleece|shell|insulat|base-?layer|top|shirt|manteau|veste"),
        ("gear", r"pole|headlamp|lighting|water|filter|first-aid|traction|crampon|navigation|gps|gaiter")]
HINT = [(g, re.compile(rx, re.I)) for g, rx in HINT]
CAMP_HINT = re.compile(r"camp|tent|sleeping|shelter|stove|kitchen|cook", re.I)


def shoe_type(n):
    if re.search(r"\bapproach\b", n, re.I):
        return "approach"
    if re.search(r"\bboots?\b|\bmid\b|\bhigh\b|\bhi\b|mountaineering|\bbottes?\b|\bmontantes?\b", n, re.I):
        return "boot"
    return "hike"


def pack_type(n):
    m = PACK_L.search(n)
    if m:
        return "overnight" if int(m.group(1)) >= 35 else "day"
    return "overnight" if re.search(r"backpacking|expedition|thru|overnight|trekking pack", n, re.I) else "day"


def classify(name, ptype="", hint="", brand=""):
    """-> (group, type) or None. Group 'camp' = camping (read, not published)."""
    n = re.sub(r"\s+", " ", name or "").strip()
    both = f"{n} {ptype}"
    if not n or (SKIP.search(both) and not KEEP.search(n)) or (brand or "").strip().lower() in NOT_HIKE_BRANDS or CASUAL.search(n):
        return None
    for t, rx in CAMP:
        if rx.search(n) and not re.search(r"\bquilted\b|\bjackets?\b|\bvests?\b|\bpants\b|\bsocks?\b", n, re.I):
            if t == "tent" and re.search(r"\bmid\b", n, re.I) and SHOE.search(f"{n} {hint}") and not re.search(r"\bmid\s?\d", n, re.I):
                break                                            # "Moab 3 Mid": a boot, not a pyramid tent
            return "camp", t
    hint_g = next((g for g, rx in HINT if rx.search(hint or "")), None)
    if re.search(r"\b(boots?|shoes?|footwear|chaussures?|bottes?|souliers?)\b", n, re.I) and not re.search(
            r"\b(socks?|gaiters?|traction|microspikes?|nanospikes?|crampons?|cleats?|poles?|cubes?|bags?|boot[- ]?(length|cut))\b", n, re.I):
        return "shoes", shoe_type(n)
    for g, t, rx in RULES:
        if rx.search(n):
            if g == "packs":
                return "packs", pack_type(n)
            if t == "@":
                return "tops", jacket_type(n, hint)
            if g == "tops" and t == "shirt" and hint_g not in ("tops",) and CASUAL_TOP.search(n) and not re.search(
                    r"\b(merino|sun|uv|upf|tech|technical|trail|hik\w*|quick[- ]dry|wool|capilene|performance)\b", n, re.I):
                return None                                     # a logo tee from a whole-store read: not hiking gear
            return g, t
    if hint_g == "shoes":                  # no rule matched the name ("Moab 3 Mid Waterproof") and the store files it as footwear
        return "shoes", shoe_type(n)
    if hint_g == "packs":
        return "packs", pack_type(n)
    h = (hint or "").lower()               # camping sections: names like "Hubba Hubba 2" say nothing
    for t, rx in (("tent", r"tent|shelter"), ("bag", r"sleeping[-_ ]?bag|quilt"), ("mat", r"\bmats?\b|pads?|mats_|-mats"),
                  ("kitchen", r"stove|kitchen|cook")):
        if re.search(rx, h):
            return "camp", t
    return None


# ---------------------------------------------------------------- stores
# (key, base, collections or None = whole store, side) side: "ca" ships to Canada (USD stores are cross-border on the Canada side
# and US stores on the USA side, like running), "us" = USA side only (doesn't ship to Canada)
_g = lambda *xs: [f"{p}{x}" for x in xs for p in ("mens-", "womens-")]
SHOPIFY = [
    # Canadian outdoor stores (sections that are hiking; camping sections read for camp.json)
    ("vpo", "https://www.vpo.ca", ["mens-jackets-hard_shell", "womens-jackets-hard_shell", "mens-jackets-insulated", "womens-jackets-insulated",
                                   "mens-bottoms-pants-quick_dry", "womens-bottoms-pants-quick_dry", "mens-bottoms-pants-hard_shell",
                                   "womens-bottoms-pants-hard_shell", "mens-bottoms-pants-soft_shell", "womens-bottoms-pants-soft_shell",
                                   "mens-bottoms-shorts-quick_dry", "womens-bottoms-shorts-quick_dry", "mens-baselayers", "womens-baselayers",
                                   "mens-footwear-hiking_boots", "womens-footwear-hiking_boots", "mens-footwear-hiking_shoes",
                                   "womens-footwear-hiking_shoes", "mens-footwear-socks-hiking", "womens-footwear-socks-hiking",
                                   "mens-accessories-gloves_mitts-gloves", "womens-accessories-gloves_mitts-gloves",
                                   "mens-accessories-headwear-toques_beanies", "womens-accessories-headwear-toques_beanies",
                                   "mens-accessories-headwear-sun_hats_fedoras", "womens-accessories-headwear-sun_hats_fedoras",
                                   "gear-hiking", "gear-packs_travel-daypacks", "gear-hiking-hiking_poles", "backpacking-tents",
                                   "gear-camping-tents_shelters", "gear-camping-sleeping_bags_liners", "gear-camping-mats_pillows"], "ca"),
    ("sail", "https://www.sail.ca/en-ca", ["outdoor-gear-hiking", "layering-essentials-rain-jackets", "layering-essentials-fleeces-softshells",
                                          "men-outdoor-pants", "women-outdoor-pants", "footwear-accessories-socks-hiking-socks",
                                          "camping-tents", "camping-sleeping-gear"], "ca"),
    ("monod", "https://www.monodsports.com", ["hiking-footwear", "approach-shoes", "mountaineering-boots", *_g("insulated-jackets", "rain-jackets",
              "windbreakers-and-softshells", "fleeces", "base-layer-tops", "base-layer-bottoms", "hiking-pants", "rain-pants", "shorts",
              "socks", "gloves-and-mitts"), "hiking-and-backpacking-packs", "hiking-gear", "hiking-accessories", "headlamps",
              "trekking-poles", "crampons", "first-aid-and-medical-kits", "tents-and-shelters", "sleeping-bags", "sleeping-pads",
              "camping-stoves-and-fuel"], "ca"),
    ("bushtukah", "https://www.bushtukah.com", ["hike-clothing", "hike-footwear", "category-hike-and-travel"], "ca"),
    ("trailhead", "https://www.trailheadpaddleshack.ca", ["camp-and-hike", *_g("jackets", "pants", "shorts", "hiking-socks", "fleeces",
                  "hiking-shoes", "hiking-boots", "lightweight-insulated-jackets", "rain-jackets"), "womens-baselayers",
                  "mens-baselayers-and-underwear", "hiking-packs-backpacks", "hiking-day-packs", "headlamps", "hiking-poles",
                  "water-treatment-and-filters", "first-aid-and-survival", "hiking-accessories", "ski-and-outdoor-gloves"], "ca"),
    ("geartrade", "https://geartrade.com", ["womens-hiking-climbing-pants", "mens-hiking-and-climbing-pants", "womens-hiking-and-climbing-shorts",
                  "mens-hiking-and-climbing-shorts", *_g("softshell-jackets", "rain-jackets", "technical-shells", "down-jackets",
                  "synthetic-insulation-jackets", "fleece-jackets", "baselayers", "hiking-boots", "hiking-shoes"), "backpacks", "daypacks",
                  "water-treatment", "gaiters", "socks", "gloves", "sun-hats-rain-hats-safari-hats", "hiking-and-camping", "tents"], "ca"),
    # Canadian brands
    ("taiga", "https://www.taigaworks.com", None, "ca"),
    ("hillsound", "https://www.hillsound.ca", None, "ca"),
    ("jbfields", "https://www.greatsox.com", None, "ca"),
    ("tilley", "https://ca.tilley.com", None, "ca"),
    ("primus", "https://www.primusequipment.ca", None, "ca"),
    ("zamberlan", "https://www.zamberlancanada.ca", None, "ca"),
    # brands and stores abroad that ship to Canada (cross-border on the Canada side, home side for the USA)
    ("featheredfriends", "https://www.featheredfriends.com", None, "ca"),
    ("seatosummit", "https://www.seatosummit.com", None, "ca"),
    ("lasportiva", "https://www.lasportivausa.com", None, "ca"),
    ("scarpa", "https://us.scarpa.com", None, "ca"),
    ("outdoorresearch", "https://www.outdoorresearch.com", None, "ca"),
    ("smartwool", "https://www.smartwool.com", None, "ca"),
    ("ridgemerino", "https://www.ridgemerino.com", None, "ca"),
    ("minus33", "https://www.minus33.com", None, "ca"),
    ("blackdiamond", "https://www.blackdiamondequipment.com", None, "ca"),
    ("msr", "https://www.msrgear.com", None, "ca"),
    ("thermarest", "https://www.thermarest.com", None, "ca"),
    ("nemo", "https://www.nemoequipment.com", None, "ca"),
    ("bigsky", "https://www.bigskyinternational.com", None, "ca"),
    ("katabatic", "https://www.katabaticgear.com", None, "ca"),
    ("snowpeak", "https://snowpeak.com", None, "ca"),
    ("cnoc", "https://www.cnocoutdoors.com", None, "ca"),
    ("vargo", "https://www.vargooutdoors.com", None, "ca"),
    ("nitecore", "https://www.nitecorestore.com", None, "ca"),
    ("sierradesigns", "https://www.sierradesigns.com", None, "ca"),
    ("teton", "https://www.tetonsports.com", None, "ca"),
    ("outdoorvitals", "https://www.outdoorvitals.com", None, "ca"),
    ("paria", "https://www.pariaoutdoorproducts.com", None, "ca"),
    ("naturehike", "https://www.naturehike.com", None, "ca"),
    ("gossamer", "https://www.gossamergear.com", None, "ca"),
    ("sixmoon", "https://www.sixmoondesigns.com", None, "ca"),
    ("zpacks", "https://www.zpacks.com", None, "ca"),
    ("durston", "https://www.durstongear.com", None, "ca"),
    ("hyperlite", "https://www.hyperlitemountaingear.com", None, "ca"),
    ("palante", "https://www.palantepacks.com", None, "ca"),
    ("gryphon", "https://www.gryphongear.com", None, "ca"),
    ("garagegrown", "https://garagegrowngear.com", None, "ca"),
    ("neptune", "https://www.neptunemountaineering.com", ["camp-hike", "clothing-footwear", "backpacks", "daypacks", "backpacking-packs",
                  "trekking-poles", "crampons", "traction-gaiters", "gps-navigation", "microfilters", "boots", "approach-shoes",
                  "mountaineering-boots", "tents-shelters", "down-sleeping-bags", "synthetic-sleeping-bags", "sleeping-pads", "stoves"], "ca"),
    ("outdoorplay", "https://www.outdoorplay.com", ["camp-hike", "mens-outdoor-apparel", "womens-outdoor-apparel", "hiking-boots-shoes",
                  "backpacks"], "ca"),
    # more outdoor stores (Oct 25 night, probed + robots.txt read): shipping to Canada
    ("nextadventure", "https://www.nextadventure.net", None, "ca"),
    ("gearhead", "https://www.gearheadoutfitters.com", None, "ca"),
    ("mountainhigh", "https://www.mountainhighoutfitters.com", None, "ca"),
    ("outdoorsinc", "https://www.outdoorsinc.com", None, "ca"),
    # USA side only (their own shipping list leaves Canada out)
    ("appoutdoors", "https://www.appoutdoors.com", None, "us"),
    ("greatoutdoor", "https://www.greatoutdoorprovision.com", None, "us"),
    ("halfmoon", "https://www.halfmoonoutfitters.com", None, "us"),
    ("mastgeneral", "https://www.mastgeneralstore.com", None, "us"),
    ("mtnchalet", "https://www.mtnchalet.com", None, "us"),
    ("ramsey", "https://www.ramseyoutdoor.com", None, "us"),
    ("secondascent", "https://www.secondascent.com", None, "us"),
    ("ascent", "https://www.ascentoutdoors.com", ["backpacking-camping", "apparel", "mens-hiking-backpacking-shoes",
                  "womens-hiking-backpacking-footwear", "socks", "hand-gloves", "crampons-traction", "hiking-poles", "day-packs"], "us"),
    ("ems", "https://www.ems.com", None, "us"),
    ("bigagnes", "https://www.bigagnes.com", None, "us"),
    ("oboz", "https://www.obozfootwear.com", None, "us"),
    ("lowa", "https://www.lowaboots.com", None, "us"),
    ("keen", "https://www.keenfootwear.com", None, "us"),
    ("darntough", "https://www.darntough.com", None, "us"),
    ("kelty", "https://www.kelty.com", None, "us"),
    ("cascade", "https://www.cascademountaintech.com", None, "us"),
]
NAMES = {"vpo": "Valhalla Pure Outfitters", "sail": "SAIL", "monod": "Monod Sports", "bushtukah": "Bushtukah", "trailhead": "Trailhead",
         "geartrade": "Gear Trade", "taiga": "Taiga Works", "hillsound": "Hillsound", "jbfields": "J.B. Field's", "tilley": "Tilley",
         "primus": "Primus Canada", "zamberlan": "Zamberlan Canada", "featheredfriends": "Feathered Friends", "seatosummit": "Sea to Summit",
         "lasportiva": "La Sportiva", "scarpa": "Scarpa", "outdoorresearch": "Outdoor Research", "smartwool": "Smartwool",
         "ridgemerino": "Ridge Merino", "minus33": "Minus33", "blackdiamond": "Black Diamond", "msr": "MSR", "thermarest": "Therm-a-Rest",
         "nemo": "NEMO", "bigsky": "Big Sky International", "katabatic": "Katabatic Gear", "snowpeak": "Snow Peak", "cnoc": "CNOC Outdoors",
         "vargo": "Vargo", "nitecore": "Nitecore Store", "sierradesigns": "Sierra Designs", "teton": "TETON Sports",
         "outdoorvitals": "Outdoor Vitals", "paria": "Paria Outdoor Products", "naturehike": "Naturehike", "gossamer": "Gossamer Gear",
         "sixmoon": "Six Moon Designs", "zpacks": "Zpacks", "durston": "Durston Gear", "hyperlite": "Hyperlite Mountain Gear",
         "palante": "Pa'lante Packs", "gryphon": "Gryphon Gear", "garagegrown": "Garage Grown Gear", "neptune": "Neptune Mountaineering",
         "outdoorplay": "Outdoorplay", "ascent": "Ascent Outdoors", "ems": "Eastern Mountain Sports", "bigagnes": "Big Agnes",
         "oboz": "Oboz", "lowa": "LOWA", "keen": "KEEN", "darntough": "Darn Tough", "kelty": "Kelty", "cascade": "Cascade Mountain Tech",
         "altitude": "Altitude Sports", "lasthunt": "The Last Hunt", "nextadventure": "Next Adventure", "gearhead": "Gearhead Outfitters",
         "mountainhigh": "Mountain High Outfitters", "outdoorsinc": "Outdoors Inc.", "appoutdoors": "Appalachian Outdoors",
         "greatoutdoor": "Great Outdoor Provision Co.", "halfmoon": "Half-Moon Outfitters", "mastgeneral": "Mast General Store",
         "mtnchalet": "Mountain Chalet", "ramsey": "Ramsey Outdoor", "secondascent": "Second Ascent"}
# brands whose own store lists them blank or under a store name
OWN = {"taiga": "Taiga Works", "hillsound": "Hillsound", "jbfields": "J.B. Field's", "tilley": "Tilley", "featheredfriends": "Feathered Friends",
       "gossamer": "Gossamer Gear", "sixmoon": "Six Moon Designs", "zpacks": "Zpacks", "durston": "Durston Gear",
       "hyperlite": "Hyperlite Mountain Gear", "palante": "Pa'lante", "gryphon": "Gryphon Gear", "cnoc": "CNOC", "vargo": "Vargo",
       "katabatic": "Katabatic Gear", "bigsky": "Big Sky International", "paria": "Paria", "naturehike": "Naturehike",
       "outdoorvitals": "Outdoor Vitals", "ridgemerino": "Ridge Merino", "minus33": "Minus33"}
# ultralight / fastpack makers (the "Fastpack" filter); items with "ultralight" in the name count too
UL_BRANDS = {"gossamer gear", "six moon designs", "zpacks", "durston gear", "hyperlite mountain gear", "pa'lante", "pa'lante packs",
             "gryphon gear", "cnoc", "vargo", "katabatic gear", "big sky international", "feathered friends", "enlightened equipment",
             "mountain laurel designs", "ula", "ula equipment", "superior wilderness designs", "nemo", "sea to summit", "toaks",
             "senchi designs", "farpointe", "timmermade", "liteaf", "waymark", "kakwa", "northern ultralight", "taiga works"}

# Altitude Sports / The Last Hunt: product types in /c/camping-and-hiking (the running reader's commercetools pages)
CT_HIKE = {"Hiking Shoes": "shoes", "Hiking and Mountaineering Boots": "shoes", "Approach Shoes": "shoes", "Backpacking Packs": "packs",
           "Day Packs": "packs", "Technical Pants": "bottoms", "Hardshell and Rain Pants": "bottoms", "Shorts": "bottoms",
           "Fleeces": "tops", "Lightweight Insulated Jackets": "tops", "Hardshells and Rain Jackets": "tops",
           "Softshells and Windbreakers": "tops", "Vests": "tops", "T-Shirts and Polos": "tops", "Long Sleeve T-Shirts": "tops",
           "Shirts": "tops", "Base Layer Tops": "tops", "Base Layer Bottoms": "bottoms", "Socks": "socks", "Gloves": "gloves",
           "Caps and Sun Hats": "headwear", "Beanies and Winter Hats": "headwear", "Water Treatment and Filters": "gear",
           "Poles": "gear", "Headlamps": "gear", "Gaiters": "gear", "Bottles": "gear", "Crampons and Traction": "gear",
           "First Aid": "gear", "GPS and Navigation": "gear",
           "Tents": "camp", "Sleeping Bags": "camp", "Sleeping Mats and Pads": "camp", "Pillows": "camp", "Stoves": "camp",
           "Cookware": "camp", "Lanterns": "camp", "Camping Furniture": "camp"}


def robots_ok(base):
    try:
        root = re.match(r"https?://[^/]+", base).group(0)
        rp = robotparser.RobotFileParser()
        rp.parse(s.S.get(root + "/robots.txt", timeout=20, headers={"User-Agent": UA}).text.splitlines())
        return all(rp.can_fetch(a, base + "/products.json") for a in ("ClaudeBot", "anthropic-ai", UA, "*"))
    except Exception:
        return True


def shopify_store(st, base, cols, side):
    if not robots_ok(base):
        raise RuntimeError("robots.txt says no")
    r = s.S.get(f"{base}/products.json?limit=1", timeout=25)
    if r.status_code != 200 or not r.text.lstrip().startswith("{"):
        raise RuntimeError(f"no Shopify product feed (HTTP {r.status_code})")
    home, ships = None, []
    try:
        meta = s.get(re.match(r"https?://[^/]+", base).group(0) + "/meta.json", tries=2).json()
        home, ships = (meta.get("currency") or "").upper() or None, meta.get("ships_to_countries") or []
    except Exception:
        pass
    cookies = s.CA_COOKIES if side == "ca" else None
    root = re.match(r"https?://[^/]+", base).group(0)
    served = s.shopify_price_currency(root, cookies)
    if home == "CAD" and served and served != "CAD":     # Oct 25: Taiga (a CAD store) once answered USD; ask again before converting
        served = s.shopify_price_currency(root, cookies)
        if served != "CAD":
            raise RuntimeError(f"CAD store served {served}: prices unsure, left out today")
    cur = served or home or "CAD"
    home = home or cur
    prods, seen = [], {}
    for c in (cols or [None]):
        url = f"{base}/collections/{c}" if c else base
        try:
            got = s.shopify_products(url, max_pages=100 if not c else 40, cookies=cookies)
        except Exception as e:
            print(f"  ! {st}/{c}: {str(e)[:80]}", file=sys.stderr)
            continue
        for p in got:
            if p["id"] in seen:
                continue
            seen[p["id"]] = 1
            p["_col"] = c or ""
            prods.append(p)
        time.sleep(PAUSE)
    if st == "geartrade":            # new stock only (consignment = used one-offs, a later idea)
        prods = [p for p in prods if "RetailVendorPartner" in (p.get("tags") or [])]
    fx = s.fx_to_cad(cur)
    kinds = {}

    def group(p):
        c = classify(p.get("title") or "", p.get("product_type") or "", f'{p.get("_col", "")} {p.get("product_type") or ""}', p.get("vendor") or "")
        if c:
            kinds[p["id"]] = c
            return c[0]
        return None
    items = s.shopify_items(st, base, prods, group, fx=fx, size_aware=True, collapse=True, size_fn=s.generic_size)
    byurl = {f"{base}/products/{p['handle']}": p for p in prods}
    for o in items:
        p = byurl.get(o["u"].split("?")[0])
        g, t = kinds.get(p["id"]) if p else (o["g"], None)
        o["_t"] = t
        if st in OWN and not (o["b"] or "").strip() or (o["b"] or "").strip().lower() in ("default", "default vendor", st):
            o["b"] = OWN.get(st, o["b"])
        hg = gender_hint(p.get("_col", "") if p else "")
        if hg and o["g"] in ("shoes", "tops", "bottoms", "socks", "gloves") and not re.search(r"\b(wom[ae]n|men|unisex)[’']?s?\b", o["n"], re.I):
            o["n"] += " - Women's" if hg == "women" else " - Men's"
        o["ca"] = home == "CAD"
        o["us"] = home == "USD"
        if side == "us":
            o["no_ca"] = True
        if ships and "*" not in ships:
            o["no_ca"], o["no_us"] = o.get("no_ca") or "CA" not in ships, "US" not in ships
    print(f"  {st}: {len(prods)} products read, {len(items)} hiking/camping listings, prices in {cur}"
          + (f" x{fx}" if cur != "CAD" else ""), file=sys.stderr)
    return items


def gender_hint(col):
    col = (col or "").lower()
    if re.search(r"(^|-)wom[ae]ns?(-|$)|^women|-w-|femmes?", col):
        return "women"
    if re.search(r"(^|-)mens?(-|$)|^men-|hommes?", col):
        return "men"
    return None


def ct_store(st, base):
    from urllib.parse import quote as q
    types = s.plp(f"{base}/c/camping-and-hiking")["facets"].get("attributes.product_type_name", {})
    found = {}
    for t, n in types.items():
        g = CT_HIKE.get(t)
        if not g:
            continue
        url = f"{base}/c/camping-and-hiking?product_type_name={q(t)}"
        for u in ([url] if n <= 1000 else [f"{url}&gender={x}" for x in ("Men", "Women", "NA")]):
            _, hits = s.list_all(u)
            for h in hits:
                found.setdefault(h["slug"], (g, h.get("image_url"), t))
    out = []

    def one(kv):
        slug, (g, img, t) = kv
        try:
            return s.product(base, slug, st, "gear" if g == "camp" else g, img), t
        except Exception as e:
            return e, t
    with ThreadPoolExecutor(6) as ex:
        for r, t in ex.map(one, found.items()):
            if not r or isinstance(r, Exception):
                continue
            c = classify(r["n"], t, t, r["b"])
            if not c:
                continue
            r["g"], r["_t"] = c
            if (CT_HIKE.get(t) == "camp") != (c[0] == "camp"):
                continue                                         # the store's section and the name disagree: leave it out
            r["ca"] = True
            r["no_us"] = st == "altitude"
            out.append(r)
    print(f"  {st}: {len(found)} listings, {len(out)} hiking/camping in stock", file=sys.stderr)
    return out


# ---------------------------------------------------------------- merge
HTYPES = {"shoes": ["hike", "boot", "approach"], "tops": ["shell", "insulated", "fleece", "wind", "base", "shirt"],
          "bottoms": ["pant", "rain", "short", "base"], "packs": ["day", "overnight"],
          "gear": ["pole", "light", "water", "traction", "safety", "nav", "gaiter", "sun"]}


def tidy(items):
    """After the running merge: hiking types, the fastpack flag, the store's display names."""
    run = running_shoes()
    out = []
    for it in items:
        if it["b"].lower() in NOT_HIKE_BRANDS or CASUAL.search(it["n"]):
            continue
        c = classify(it["n"], brand=it["b"])
        if c and c[0] != "camp":
            if c[0] != it["g"] or c[1]:          # the running merge's tidy-ups are tuned for running gear: our own sorting wins
                it["g"], it["t"] = c[0], c[1] or (it.get("t") if c[0] == it["g"] else None)
        elif it.get("t") not in HTYPES.get(it["g"], [None]):
            it["t"] = next((t for g, t, rx in RULES if g == it["g"] and rx.search(it["n"])), None)
        if it["g"] == "shoes":
            if not any(re.search(r"\d", str(e[0])) for e in it["sz"]) or (it["b"].lower(), base(it["n"])) in run:
                continue                         # a "shoe" without shoe sizes (a shoe bag), or a trail runner (running side)
            if it.get("t") not in HTYPES["shoes"]:
                it["t"] = shoe_type(it["n"])
        if it["g"] == "packs":
            it["t"] = pack_type(it["n"])
        if it["g"] in ("socks", "gloves", "headwear"):
            it.pop("t", None)
        out.append(it)
    items = out
    for it in items:
        if it["b"].lower() in UL_BRANDS or re.search(r"\bultra ?light\b|\bUL\b", it["n"]):
            it["ul"] = 1
    return items


RUNNING_DEALS = Path(os.environ.get("RUNNING_DEALS") or Path(__file__).parent.parent / "site" / "deals.json")
_RUN = {}


def base(n):
    n = re.sub(r"\s*(-\s*|\()(Men|Women)[’']s\)?$|\s*(-\s*|\()Unisex\)?$", "", n or "")
    n = re.sub(r"\b(wide|gtx|gore-?tex|trail running shoes?|running shoes?|shoes?)\b", "", n, flags=re.I)
    return re.sub(r"[^a-z0-9]+", " ", n.lower()).strip()


def running_shoes():
    """Trail running shoes that hiking stores file under footwear ("Lone Peak 9", "Speedgoat 6") belong to the running side:
    any shoe model the running site carries as a road/trail/race shoe is left out here."""
    if "s" not in _RUN:
        try:
            d = json.loads(RUNNING_DEALS.read_text())
            _RUN["s"] = {(i["b"].lower(), base(i["n"])) for i in d["items"] if i["g"] == "shoes" and i.get("t") in ("daily", "race", "trail", "spike")}
        except Exception as e:
            print(f"  ! running shoes list not read ({e}); trail runners may show as hiking shoes", file=sys.stderr)
            _RUN["s"] = set()
    return _RUN["s"]


# EU -> US boot sizes from each maker's OWN size chart (Oct 25, Bastien: "We might have to have some EU sizes in hiking. lots of boots
# are european models"). Only official charts, read on the brand's site (no guessing: third-party charts disagree by half a size).
# A brand without one here: its EU sizes convert only from today's labels that carry both (the running merge's eu_us), else stay EU.
EU_CHART = {
    # us.lowa.com/pages/size-chart (read Oct 25, 2026); women's = standard soles (the "injected soles" column is half a size up)
    "lowa": {"men": {"39.5": "7", "40": "7.5", "41": "8", "41.5": "8.5", "42": "9", "42.5": "9.5", "43.5": "10", "44": "10.5", "44.5": "11",
                     "45": "11.5", "46": "12", "46.5": "12.5", "47": "13", "48": "13.5", "48.5": "14", "49": "14.5", "49.5": "15"},
             "women": {"35": "4", "36": "4.5", "36.5": "5", "37": "5.5", "37.5": "6", "38": "6.5", "39": "7", "39.5": "7.5", "40": "8",
                       "41": "8.5", "41.5": "9", "42": "9.5", "42.5": "10", "43.5": "10.5", "44": "11"}},
}


def eu_to_us(brand, label, women):
    m = re.fullmatch(r"(?i)(?:eu\s*)?(\d{2}(?:[.,]5)?)\s*(?:eu)?(\s+wide)?", str(label or "").strip())
    ch = EU_CHART.get((brand or "").strip().lower())
    if not m or not ch:
        return None
    us = ch["women" if women else "men"].get(m.group(1).replace(",", "."))
    return us + (" Wide" if m.group(2) else "") if us else None


def shoe_label(label, women):
    """Hiking stores' shoe size labels -> what canon_shoe() reads. "8.5 US" -> "8.5"; "9 US Wide" -> "9 Wide"; "7 UK" -> US: men's
    UK + 1, women's UK + 2 (the standard UK-US chart every boot maker prints). EU sizes stay as they are: the running merge
    converts them only from today's labels that carry both EU and US for the same brand (no guessing)."""
    t = str(label or "").strip()
    m = re.fullmatch(r"(?i)(?:us\s*)?(\d{1,2}(?:\.5)?)\s*us(\s+wide)?", t)
    if m:
        return m.group(1) + (" Wide" if m.group(2) else "")
    m = re.fullmatch(r"(?i)(?:uk\s*)?(\d{1,2}(?:\.5)?)\s*uk(\s+wide)?", t)
    if m:
        v = float(m.group(1)) + (2 if women else 1)
        return (str(int(v)) if v == int(v) else str(v)) + (" Wide" if m.group(2) else "")
    return t


def merged(offers, side):
    offs = []
    for o in offers:
        if side == "ca" and o.get("no_ca"):
            continue
        if side == "us" and (o.get("no_us") or (o.get("ca") and not o.get("us"))):
            continue                                          # USA side: US stores + others that ship there, not Canadian ones
        o = dict(o, sz=[list(e) for e in o["sz"]], sx=list(o.get("sx") or []))
        if side == "us":
            o["ca"] = bool(o.get("us"))
        if o["g"] == "shoes":
            women = bool(re.search(r"\bwom[ae]n", o["n"], re.I)) or o["sx"] == ["women"]
            for e in o["sz"]:
                e[0] = eu_to_us(o["b"], e[0], women) or shoe_label(e[0], women)
        offs.append(o)
    camp = [o for o in offs if o["g"] == "camp"]
    hike = [o for o in offs if o["g"] != "camp"]
    for o in camp:
        o["g"] = "gear"                                     # the running merge knows "gear"; camp files say what each one is in "t"
    hi = s.merge(hike)
    ca = s.merge(camp)
    for it in ca:
        it["g"] = "camp"
    for it in hi + ca:
        it.pop("_st", None)
    hi.sort(key=lambda i: (i["g"], i["b"].lower(), i["n"].lower()))
    ca.sort(key=lambda i: (i.get("t") or "", i["b"].lower(), i["n"].lower()))
    return tidy(hi), ca


def write(out, offers, stamps):
    n_st = len({o["st"] for o in offers})
    try:
        usd = round(s.fx_to_cad("USD"), 4)
    except Exception:
        usd = s.FX_FALLBACK["USD"]
    for side, suf in (("ca", ""), ("us", "-us")):
        hi, ca = merged(offers, side)
        head = {"v": 2, "sport": "hike", "updated": s.now(), "stores": stamps, "n_stores": n_st, "fx": {"USD": usd}}
        if side == "us":
            head["country"] = "us"
        dump = lambda p, its: (out / p).write_text(json.dumps(dict(head, items=its), separators=(",", ":"), ensure_ascii=False))
        dump(f"deals-hike{suf}.json", hi)
        dump(f"sale-hike{suf}.json", [i for i in hi if any(e[1] < e[3] for e in i["sz"])])
        dump(f"camp{suf}.json", ca)
        c = collections.Counter((i["g"], i.get("t")) for i in hi)
        sale = sum(1 for i in hi if any(e[1] < e[3] * 0.99 for e in i["sz"]))
        print(f"{side}: {len(hi)} hiking items ({sale} on sale), {len(ca)} camping; " +
              ", ".join(f"{g}/{t} {n}" for (g, t), n in sorted(c.items(), key=lambda x: (x[0][0], str(x[0][1])))), file=sys.stderr)


def main():
    s.S.headers["User-Agent"] = UA          # our own name, no disguise
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / "hike-offers.json"
    if "--remerge" in sys.argv:
        raw = json.loads(raw_path.read_text())
    else:
        prev = json.loads(raw_path.read_text()) if raw_path.exists() else {}
        only = [a for a in sys.argv[2:] if not a.startswith("--")]
        raw = dict(prev)
        jobs = [(st, (lambda st=st, b=b: ct_store(st, b))) for st, b in (("altitude", "https://www.altitude-sports.com"),
                                                                           ("lasthunt", "https://www.thelasthunt.com"))]
        jobs += [(st, (lambda st=st, b=b, c=c, sd=sd: shopify_store(st, b, c, sd))) for st, b, c, sd in SHOPIFY]
        jobs = [j for j in jobs if not only or j[0] in only]

        def run(job):
            st, fn = job
            t0 = time.time()
            try:
                got = fn()
                if not got and len(prev.get(st, {}).get("o", [])) >= 20:
                    raise RuntimeError(f"0 items today (had {len(prev[st]['o'])})")
                return st, {"o": got, "at": s.now()}, f"{st}: {len(got)} in {time.time() - t0:.0f}s"
            except Exception as e:
                return st, prev.get(st), f"{st}: FAILED ({str(e)[:100]}); kept the last read"
        # the commercetools pair in their own lanes, Shopify stores one after another (Shopify counts one machine's requests)
        lanes = [[j] for j in jobs if j[0] in ("altitude", "lasthunt")] + [[j for j in jobs if j[0] not in ("altitude", "lasthunt")]]
        res = []
        with ThreadPoolExecutor(3) as ex:
            for got in ex.map(lambda l: [run(j) for j in l], lanes):
                res += got
        for st, data, line in res:
            print(line, file=sys.stderr)
            if data:
                raw[st] = data
        raw_path.write_text(json.dumps(raw, separators=(",", ":"), ensure_ascii=False))
    offers = [o for v in raw.values() for o in (v.get("o") or [])]
    write(out, offers, {st: v.get("at") for st, v in raw.items()})


if __name__ == "__main__":
    main()
