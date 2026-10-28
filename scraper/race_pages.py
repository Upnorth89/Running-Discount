#!/usr/bin/env python3
"""Race gear list pages (Oct 20, Bastien's idea): "<race> mandatory gear list", one page per race, EN + FR.

Each item on the race's own mandatory list gets a line: mandatory / recommended for each distance (as the race publishes it),
the race's note, an "I have it" tick (kept in this browser) and today's best deals for it in the visitor's size. Deals come
from sale.json (Canadian side, on sale, with a photo); the page carries a small pool per item and the script picks the ones
in the visitor's fit and clothing size. Items no store we check sells (whistle, blanket, phone) are a plain checklist line.

Rules: only what the race's own page says (dated, linked); specs we can't check from store data say "check the spec";
not affiliated with the race. A test: judged on Search Console clicks + sign-ups from these pages (plan doc).

Usage: python scraper/race_pages.py SITE_DIR [SALE_JSON]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoe_pages import base_model, slugify
from shoe_pages import T, US, esc, page_head, page_foot, store_names, size_url, host  # noqa: E402

POOL = 60        # picks per gear item carried in the page (the script picks the best 10 in your size)
SHOW = 10        # Oct 20 (Bastien): 10 choices per item, a few on sale; 3 show, "See all 10" opens the rest
FIRST = 3
MIN_SALE = 3

WATERPROOF = r"waterproof|\brain|gore|gtx|h2no|shell|storm|hydro|2\.5l|3l\b|futurelight|pertex shield|dryvent|membrane|imperm"
# Oct 20 (Bastien: "2x 6oz bottles for a 125 km"; "tuques are mostly city tuques"): race gear, not anything with the word in it.
# need = must match; good = trail/running words; an item needs a good word OR a trail brand; x = never.
TRAIL = {"salomon", "hoka", "arc'teryx", "ciele", "buff", "smartwool", "icebreaker", "patagonia", "outdoor research", "black diamond", "petzl",
         "nathan", "ultraspire", "hydrapak", "inov-8", "la sportiva", "dynafit", "montane", "norrøna", "raidlight", "rab", "craft", "odlo",
         "kari traa", "janji", "rabbit", "tracksmith", "saysky", "the north face", "mammut", "haglöfs", "brooks", "saucony", "on", "2xu",
         "nnormal", "norda", "leki", "compressport", "scott", "kiprun", "mec", "life sports gear", "fenix", "ledlenser", "silva", "biolite",
         "karpos", "gore wear", "naak", "näak", "maurten", "spring energy", "precision fuel & hydration", "neversecond", "boco", "satisfy", "district vision"}
# Oct 20 (Bastien): the brands runners buy for each item. MAYBE brands come in only for running items ("if it's running stuff").
BRANDS = {
    "water": "salomon|hydrapak|nathan|ultraspire|norda|montane|life sports gear|nnormal|naked|kiprun",
    "jacket": "salomon|arc'teryx|nnormal|patagonia|the north face|inov-8|montane|karpos|black diamond|outdoor research|mammut|brooks|craft|kiprun|scott|dynafit|la sportiva|raidlight|norrøna",
    "tuque": "ciele|smartwool|buff|salomon|icebreaker|kari traa|arc'teryx|outdoor research|nathan|saucony|brooks|craft|patagonia|on",
    "headlamp": "petzl|black diamond|nathan|biolite|silva|fenix|ledlenser|raidlight",
    "gloves": "black diamond|outdoor research|smartwool|craft|salomon|brooks|nathan|arc'teryx|icebreaker|montane|the north face|saucony",
    "midlayer": "salomon|smartwool|icebreaker|brooks|craft|patagonia|arc'teryx|outdoor research|kari traa|hoka|on|saucony|the north face|mons royale|odlo|ciele",
    "cap": "buff|ciele|salomon|satisfy|fractel|boco|patagonia|arc'teryx|on|nnormal|nathan|smartwool",
    "pants": "salomon|patagonia|montane|outdoor research|rab|black diamond|mammut|dynafit|scott|kiprun|brooks|craft",
    "poles": "black diamond|leki|salomon|dynafit|norda|raidlight|ultraspire|la sportiva|scott|kiprun|komperdell",
    "food": "maurten|näak|naak|precision fuel & hydration|gu|spring energy|neversecond|xact nutrition|skratch labs|skratch|huma|science in sport|honey stinger|clif|krono|brix|lecka",
    "cup": "hydrapak|salomon|nathan|brix|xact nutrition|foveo running",
}
BRANDS.update({   # Oct 21: same idea for the new items (the brands trail runners buy for each)
    "vest": "salomon|nathan|ultraspire|raidlight|inov-8|the north face|arc'teryx|black diamond|naked|nnormal|patagonia|brooks|montane|kiprun|la sportiva|compressport|hoka|hydrapak|mec",
    "filter": "salomon|hydrapak|katadyn|lifestraw|sawyer|platypus|grayl|aquatabs|life sports gear",
    "longpants": "salomon|patagonia|arc'teryx|craft|brooks|saucony|the north face|kari traa|odlo|smartwool|icebreaker|outdoor research|montane|kiprun|hoka|on|ciele|janji|rabbit|tracksmith|mec",
    "warmjacket": "arc'teryx|patagonia|salomon|the north face|montane|black diamond|outdoor research|rab|mammut|kari traa|smartwool|icebreaker|craft|norrøna|mec",
    "socks": "injinji|darn tough|smartwool|balega|feetures|swiftwick|icebreaker|salomon|drymax|compressport|rabbit|ciele|stance|mec|saucony|brooks",
    "sun": "goodr|oakley|julbo|smith|roka|tifosi|district vision|sunski|ombraz|knockaround|ciele|bolle|100%|rudy project|scott",
    "wind": "salomon|arc'teryx|patagonia|the north face|inov-8|montane|black diamond|outdoor research|brooks|craft|kiprun|ciele|janji|rabbit|tracksmith|saucony|hoka|on|nnormal|raidlight|norrøna|mec",
})
BRANDS = {k: set(v.split("|")) for k, v in BRANDS.items()}
MAYBE = {"2xu", "balmoral", "nike", "under armour", "bula", "camelbak", "osprey"}
RUN = re.compile(r"\brun|running|trail|race|racing|ultra|marathon", re.I)
KINDS = {
    # "gloves2" (Oct 21): the UTMB cold kit's "warm and waterproof gloves"; any other "<kind>2" uses its kind's rules
    "water":    dict(g={"gear", "packs"}, need=r"soft ?flask|handheld|hand held|skyflask|ultraflask|pocketflask|speedflask", good=r".",
                     x=r"\b(150|250) ?ml|\b[5-9] ?oz|\b1[0-3] ?oz|holder|cap only|lid|valve only|bite valve|kit\b"),   # 1 L = two 500 ml flasks
    "food":     dict(g={"nutrition"}, need=r"gel|bar\b|bars\b|chew|waffle|blok|stinger|gummies|jelly|bites", good=r".", x=r"drink mix|electrolyte|hydration mix|capsule|tablet|protein"),
    "cup":      dict(g={"gear", "packs"}, need=r"\bcup\b|speedcup|tasse|gobelet", good=r".", x=r"holder"),
    "jacket":   dict(g={"tops"}, t={"jacket"}, need=WATERPROOF, good=r"\brun|trail|race|ultra|light|pack|stretch|speed|active",
                     x=r"vest|windbreaker|wind jacket|wind shell|insulat|down\b|puffer|softshell|soft shell|t-?shirt|\btee\b|\bski\b|snow|3-in-1|parka|\bbib\b"),
    "tuque":    dict(g={"headwear"}, need=r"beanie|tuque|toque", good=r"\brun|thermal|merino|\blight|lite\b|dryflx|tech|race|trail|reflective|grid|active|fleece|wool blend",
                     x=r"\bpom|bobble|cuff|chunky|cable|\brib\b|cashmere|cotton|cursive|bird|word head|logo|heritage|fold|slouch|fur\b|pompom|sherpa|lined knit"),
    "headlamp": dict(g={"gear"}, need=r"headlamp|head lamp|frontale|lampe", good=r"\brun|trail|lumens|recharge|-r\b|ultra|\bswift|nao|actik|iko|spot|storm|distance",
                     x=r"bike|tail|clip light|band only|strap only|case|pouch|kids?\b"),
    "gloves":   dict(g={"gloves"}, need=r".", good=r"\brun|trail|merino|liner|touch|light|thermal|windstopper|fleece|tech|race|wind",
                     x=r"arm sleeve|warmers?\b|cycling|bike|fingerless|half[- ]finger|gel\b|\bski\b|snowboard|work glove|lifting|gym"),
    "midlayer": dict(g={"tops"}, t={"layer", "tee"}, need=r"long sleeve|long-sleeve|\bl/s\b|\bls\b|half[- ]zip|quarter[- ]zip|1/4|1/2 zip|mid-?layer|fleece|hoodie|thermal|manches longues",
                     good=r"\brun|trail|merino|thermal|grid|tech|race|ultra|wool|zip|baselayer|base layer",
                     x=r"vest|sleeveless|short sleeve|tank|singlet|arm sleeve|crop|tie dye|stella mccartney|bra\b|polo|cotton|plus size|graphic|logo"),
    "cap":      dict(g={"headwear"}, need=r"\bcap\b|buff|bandana|gaiter|casquette|visor|neckwear|tube", good=r"\brun|trail|race|ultra|tech|light|panel|neck|cool|air",
                     x=r"beanie|tuque|toque|trucker|snapback|dad hat|corduroy|cotton"),
    "pants":    dict(g={"bottoms"}, t={"pant"}, need=WATERPROOF, good=r"\brun|trail|light|pack|stretch|race|ultra|active", x=r"short|\bski\b|snow|insulat|\bbib\b"),
    "poles":    dict(g={"gear"}, need=r"\bpoles?\b|bâtons?|z-pole", good=r"\brun|trail|ultra|distance|\bz\b|z-pole|carbon|fold|compact|race|\bfl\b",
                     x=r"basket|tip|strap|nordic|touring|\bft-?\d|\bski\b"),
    # Oct 21: the other Québec races' lists
    "vest":     dict(g={"packs"}, need=r"hydration|race vest|trail vest|run(ning)? vest|\d+(\.\d)? ?l\b|flasks?|adv skin|skin \d|pinnacle|vapor|race pack",
                     good=r"\brun|trail|race|ultra|adv skin|skin|speed|hydration",
                     x=r"belt|waist|hip|bladder|reservoir|tube|replacement|strap|daypack|\b[3-9]\d ?l\b|\bski\b|bike|ride|wind|insulat|hybrid|shield|fleece|puffer|down\b|primaloft|therma"),   # Oct 22: a Nike PrimaLoft Therma-FIT vest (clothing) showed
    "filter":   dict(g={"gear", "packs"}, need=r"filter|purif|befree|lifestraw|sawyer|aquatab|katadyn|xa filter", good=r".",
                     x=r"adapter|replacement|cartridge|inline|\bkit\b|\bcap\b"),
    "longpants": dict(g={"bottoms"}, t={"pant", "tight"}, need=r"\bpants?\b|tights?\b|legging|jogger", good=r"\brun|trail|thermal|warm|merino|tech|race|ultra|light",
                     x=r"short|capri|3/4|7/8|crop|bra\b|\bski\b|snow|insulat|\bbib\b|cotton|yoga"),
    "warmjacket": dict(g={"tops"}, t={"jacket"}, need=r"insulat|\bdown\b|puffer|primaloft|synthetic|thermal|hybrid|alpha|octa|atom|nano|fill",
                     good=r"\brun|trail|light|hood|hoody|packable", x=r"vest|\bski\b|snow|parka|3-in-1|t-?shirt|\btee\b"),
    "socks":    dict(g={"socks"}, need=r".", good=r"\brun|trail|merino|toe|wool|ultra|crew|cushion", x=r"no show|liner only|compression sleeve|kids?|dress|casual|lifestyle"),
    "blanket":  dict(g={"gear", "packs"}, need=r"blanket|bivv?y|couverture de survie", good=r".", x=r"puffer|festival|picnic|stadium|throw|fleece|wool|down"),
    "sun":      dict(g={"gear"}, t={"sun"}, need=r"sunglass|glasses|lunettes|\bshades\b|goodr|og\b|\bvrg\b|bfg|lens", good=r".", x=r"case|strap|cord|retainer|cleaning|cleaner|cloth|spray|lens only|replacement|^lens(es)?\b|\blens(es)?$", min=15),   # Oct 21: a $5 spare lens + a lens cleaner showed
    "wind":     dict(g={"tops"}, t={"jacket"}, need=r"wind|breaker|shell|anorak|light ?jacket|run jacket", good=r"\brun|trail|race|light|ultra|pack|dwr",
                     x=r"insulat|\bdown\b|puffer|nano|atom|alpha|primaloft|thermal|\bski\b|snow|parka|3-in-1|t-?shirt|\btee\b|vest"),
}
KINDS["gloves2"] = dict(KINDS["gloves"], need=WATERPROOF)
KINDS["gloves3"] = KINDS["gloves2"]


def kbase(kind):
    """A list can name the same kind twice (a second headlamp, the weather kit's gloves): "cap3" uses the "cap" rules."""
    return kind if kind in KINDS else re.sub(r"\d+$", "", kind)

# The Ultra-Trail Harricana list as the race published it (ultratrailharricana.com, "Mandatory and Suggested Gear",
# last update 2024-08-01; read Oct 20, 2026). M = mandatory, R = recommended, A = allowed, "" = not listed.
RACES = {
    "ultra-trail-harricana": {
        "name": "Ultra-Trail Harricana", "short": "UTHC",
        "where": {"en": "Charlevoix, Québec", "fr": "Charlevoix, Québec"},
        "when": {"en": "September 10–12, 2027", "fr": "10 au 12 septembre 2027"},
        "dists": ["125", "80", "65", "42"], "default": "125",
        "src": "https://ultratrailharricana.com/en/mandatory-and-suggested-equipment/",
        "rules": "https://ultratrailharricana.com/en/official-rules/",
        "updated": {"en": "August 1, 2024", "fr": "1er août 2024"}, "faq_jacket": True, "cupless": True,
        "items": [
            ("jacket", "MMMR", {"en": ("Waterproof jacket with a hood", "Waterproof and breathable membrane, hood attached. Windbreakers aren't accepted."),
                                "fr": ("Manteau imperméable avec capuchon", "Membrane imperméable et respirante, capuchon attaché. Les coupe-vent ne sont pas acceptés.")}, True),
            ("headlamp", "MMMR", {"en": ("Headlamp + spare batteries", "Race tip: 200 lumens or more for the main light."),
                                  "fr": ("Lampe frontale + piles de rechange", "Conseil de la course : 200 lumens ou plus pour la lampe principale.")}, True),
            ("tuque", "MMMR", {"en": ("Warm hat (tuque)", ""), "fr": ("Tuque", "")}, False),
            ("gloves", "MRRR", {"en": ("Warm gloves", ""), "fr": ("Gants chauds", "")}, False),
            ("midlayer", "MR  ", {"en": ("Long-sleeve mid-layer", "Arm warmers don't count."),
                                  "fr": ("Couche intermédiaire à manches longues", "Les manchons ne comptent pas.")}, False),
            ("headlamp2", "MR  ", {"en": ("Second light or power bank", "Extra batteries, a second working headlamp or a charger."),
                                   "fr": ("Deuxième lampe ou batterie externe", "Piles de rechange, une deuxième lampe frontale ou un chargeur.")}, False),
            ("water", "MMMM", {"en": ("Water: 1 litre or more", "Two 500 ml soft flasks = 1 L."),
                               "fr": ("Eau : 1 litre ou plus", "Deux flasques de 500 ml = 1 L.")}, False),
            ("food", "MMMM", {"en": ("Food supply", "Energy bars, gels, other."), "fr": ("Réserve de nourriture", "Barres, gels, autres.")}, False),
            ("cup", "MMMM", {"en": ("Reusable cup (15 cl or more)", "Aid stations have no cups, dishes or cutlery."),
                             "fr": ("Gobelet réutilisable (15 cl ou plus)", "Les ravitaillements n'ont ni verres, ni vaisselle, ni ustensiles.")}, False),
            ("blanket", "MMMM", {"en": ("Survival blanket (1.40 m × 2 m or more)", ""), "fr": ("Couverture de survie (1,40 m × 2 m ou plus)", "")}, False),
            ("whistle", "MMMM", {"en": ("Whistle", "Many race vests have one on the chest strap: check yours."),
                                 "fr": ("Sifflet", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre.")}, False),
            ("phone", "MMMM", {"en": ("Cell phone", "With the race's emergency number saved. Reception is patchy on the course."),
                               "fr": ("Téléphone cellulaire", "Avec le numéro d'urgence de la course enregistré. Peu de réseau sur le parcours.")}, False),
            ("map", "MMMM", {"en": ("Course map", "Ondago or another GPX app on your phone."), "fr": ("Carte du parcours", "Ondago ou une autre appli GPX sur votre téléphone.")}, False),
            ("epipen", "MMMM", {"en": ("EpiPen, if you have allergies", "For insect or food allergies."),
                                "fr": ("Épipen, si vous avez des allergies", "Pour les allergies aux insectes ou alimentaires.")}, False),
            ("firstaid", "RRRR", {"en": ("Basic first aid kit", "Blister plasters, tape, pain relief, a small knife…"),
                                  "fr": ("Trousse de premiers soins", "Pansements pour ampoules, bandage, analgésique, petit couteau…")}, False),
            ("cap", "RRRR", {"en": ("Cap, bandana or Buff", ""), "fr": ("Casquette, bandana ou Buff", "")}, False),
            ("pants", "RR  ", {"en": ("Waterproof or windproof pants", ""), "fr": ("Pantalon imperméable ou coupe-vent", "")}, True),
            ("bell", "RRRR", {"en": ("Bear bell", ""), "fr": ("Clochette à ours", "")}, False),
            ("poles", "AAAA", {"en": ("Trekking poles", "Allowed, not required."), "fr": ("Bâtons de marche", "Permis, pas obligatoires.")}, False),
        ],
    },
    # Oct 21 (Bastien: "Yes build these"): every list read on the race's own site; M/R per distance as published
    "quebec-mega-trail": {
        "name": "Québec Mega Trail", "short": "QMT", "de": "du ", "le": "le ",
        "where": {"en": "Côte-de-Beaupré & Charlevoix, Québec", "fr": "Côte-de-Beaupré et Charlevoix, Québec"},
        "when": {"en": "July 1–4, 2027 (to be confirmed by the race)", "fr": "1er au 4 juillet 2027 (à confirmer par la course)"},
        "dists": ["135", "80", "50"], "default": "135",
        "src": "https://ultratrailcanada.com/courses-ultra-trail/qmt-135/",
        "read": {"en": "October 20, 2026", "fr": "20 octobre 2026"},
        "items": [
            ("jacket", "M  ", {"en": ("Waterproof windbreaker", "135 km only."), "fr": ("Coupe-vent imperméable", "135 km seulement.")}, True),
            ("headlamp", "MM ", {"en": ("Headlamp", "On the 80 km: from the Saint-Tite-des-Caps aid station on."),
                                 "fr": ("Lampe frontale", "Au 80 km : à partir du ravito de Saint-Tite-des-Caps.")}, True),
            ("battery", "MM ", {"en": ("Spare battery for the headlamp", ""), "fr": ("Pile de rechange pour la lampe frontale", "")}, False),
            ("water", "MMM", {"en": ("Water: 1.5 L on the 135 km, 1 L on the 80 and 50 km", "Three 500 ml soft flasks = 1.5 L."),
                              "fr": ("Eau : 1,5 L au 135 km, 1 L aux 80 et 50 km", "Trois flasques de 500 ml = 1,5 L.")}, False),
            ("food", "MMM", {"en": ("Food and energy supplements", ""), "fr": ("Suppléments énergétiques et nourriture", "")}, False),
            ("cap", "MMM", {"en": ("Cap or bandana for the sun", ""), "fr": ("Casquette ou foulard pour le soleil", "")}, False),
            ("blanket", "MMM", {"en": ("Survival blanket (1.4 m × 2 m)", ""), "fr": ("Couverture de survie (1,4 m × 2 m)", "")}, False),
            ("phone", "MMM", {"en": ("Cell phone", ""), "fr": ("Téléphone cellulaire", "")}, False),
            ("bandage", "MMM", {"en": ("Self-adhesive compression bandage (3 in × 48 in)", ""), "fr": ("Bandage de compression auto-adhésif (3 po × 48 po)", "")}, False),
            ("epipen", "MMM", {"en": ("EpiPen, if you have allergies", "For wasp stings or food allergies."),
                               "fr": ("Épipen, si vous avez des allergies", "Pour les piqûres de guêpes ou les allergies alimentaires.")}, False),
        ],
    },
    "borealys-mont-tremblant": {
        "name": "Boréalys Mont-Tremblant by UTMB", "short": "Boréalys", "de": "du ", "le": "le ",
        "where": {"en": "Mont-Tremblant, Québec", "fr": "Mont-Tremblant, Québec"},
        "when": {"en": "August 2027 (date to come)", "fr": "Août 2027 (date à venir)"},
        "dists": ["81", "46"], "default": "81",
        "kits": {"bad": ["jacket", "longpants", "midlayer", "tuque", "gloves", "pants"], "hot": ["sunscreen", "water2", "sun", "cap"]},
        "src": "https://borealys.utmb.world/runners/equipment",
        "read": {"en": "October 20, 2026", "fr": "20 octobre 2026"},
        "items": [
            ("vest", "MM", {"en": ("Race vest or pack", "To carry the mandatory gear the whole race."), "fr": ("Veste ou sac de course", "Pour porter le matériel obligatoire toute la course.")}, False),
            ("water", "MM", {"en": ("Water: 1 litre", "Sealed containers, no plastic bags. Two 500 ml soft flasks = 1 L."),
                             "fr": ("Eau : 1 litre", "Contenants étanches, pas de sacs de plastique. Deux flasques de 500 ml = 1 L.")}, False),
            ("cup", "MM", {"en": ("Collapsible cup (150 ml or more)", "Bottles and flasks with a lid don't count."), "fr": ("Gobelet pliable (150 ml ou plus)", "Les bouteilles et flasques avec bouchon ne comptent pas.")}, False),
            ("wind", "MM", {"en": ("Windbreaker (water-repellent)", "With durable water-repellent (DWR) protection."), "fr": ("Coupe-vent déperlant", "Avec un traitement déperlant durable (DWR).")}, True),
            ("headlamp", "M ", {"en": ("Headlamp", "200 lumens or more recommended. Phones and watches don't count."), "fr": ("Lampe frontale", "200 lumens ou plus recommandés. Téléphones et montres ne comptent pas.")}, True),
            ("blanket", "MM", {"en": ("Survival blanket (1.40 m × 2 m)", ""), "fr": ("Couverture de survie (1,40 m × 2 m)", "")}, False),
            ("whistle", "MM", {"en": ("Whistle", "Many race vests have one on the chest strap: check yours."), "fr": ("Sifflet", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre.")}, False),
            ("phone", "MM", {"en": ("Smartphone with the LiveTrail app", "On, with airplane mode off."), "fr": ("Téléphone avec l'appli LiveTrail", "Allumé, mode avion désactivé.")}, False),
            ("id", "MM", {"en": ("ID document", ""), "fr": ("Pièce d'identité", "")}, False),
            ("bandage", "MR", {"en": ("Self-adhesive elastic bandage (100 × 6 cm)", ""), "fr": ("Bandage élastique adhésif (100 × 6 cm)", "")}, False),
            ("food", "RR", {"en": ("Food reserve", "Recommended: about 800 kcal (e.g. 2 gels + 2 bars)."), "fr": ("Réserve de nourriture", "Recommandé : environ 800 kcal (ex. 2 gels + 2 barres).")}, False),
            ("jacket", "MM", {"en": ("Waterproof jacket with a hood", "Sealed seams, the jacket's own hood."),
                              "fr": ("Manteau imperméable avec capuchon", "Coutures scellées, capuchon d'origine.")}, True),
            ("longpants", "MM", {"en": ("Pants or tights that cover the legs", "Tights + socks that cover the legs also count."),
                                 "fr": ("Pantalon ou collant couvrant les jambes", "Un collant + des bas qui couvrent les jambes comptent aussi.")}, False),
            ("midlayer", "MR", {"en": ("Warm long-sleeve mid-layer", "No cotton, 180 g or more in size M."), "fr": ("Couche intermédiaire chaude à manches longues", "Pas de coton, 180 g ou plus en taille M.")}, False),
            ("tuque", "MR", {"en": ("Beanie or neck gaiter", ""), "fr": ("Tuque ou cache-cou", "")}, False),
            ("gloves", "MR", {"en": ("Warm, waterproof gloves", ""), "fr": ("Gants chauds et imperméables", "")}, False),
            ("pants", "R ", {"en": ("Waterproof overpants", ""), "fr": ("Surpantalon imperméable", "")}, True),
            ("poles", "RR", {"en": ("Hiking poles", "If you use them, carry them the whole race."), "fr": ("Bâtons de marche", "Si vous les utilisez, portez-les toute la course.")}, False),
            ("sunscreen", "MM", {"en": ("Sunscreen, 15 ml or more", "In its original container. SPF 50 recommended."),
                                 "fr": ("Crème solaire, 15 ml ou plus", "Dans son contenant d'origine. FPS 50 recommandé.")}, False),
            ("water2", "MM", {"en": ("Water: 2 L instead of 1 L", "Four 500 ml soft flasks = 2 L."), "fr": ("Eau : 2 L au lieu de 1 L", "Quatre flasques de 500 ml = 2 L.")}, False),
            ("sun", "RR", {"en": ("Sunglasses", ""), "fr": ("Lunettes de soleil", "")}, False),
            ("cap", "RR", {"en": ("Cooling bandana", "To carry ice."), "fr": ("Bandana rafraîchissant", "Pour transporter de la glace.")}, False),
        ],
    },
    "bromont-ultra": {
        "name": "Bromont Ultra", "short": "BU", "de": "du ", "le": "le ",
        "where": {"en": "Bromont, Québec", "fr": "Bromont, Québec"},
        "when": {"en": "October 2027 (date to come)", "fr": "Octobre 2027 (date à venir)"},
        "dists": ["160", "80", "55"], "default": "80", "cupless": True,
        "src": "https://www.bromontultra.com/details",
        "read": {"en": "October 21, 2026 (2026 list)", "fr": "21 octobre 2026 (liste 2026)"},
        "items": [
            ("jacket", "MMM", {"en": ("Waterproof windbreaker", ""), "fr": ("Coupe-vent imperméable", "")}, True),
            ("headlamp", "MM ", {"en": ("Headlamp", ""), "fr": ("Lampe frontale", "")}, True),
            ("headlamp2", "MM ", {"en": ("Spare battery or a second headlamp", ""), "fr": ("Pile de rechange ou 2e lampe frontale", "")}, False),
            ("water", "MMM", {"en": ("Water: 1 litre or more", "Two 500 ml soft flasks = 1 L."), "fr": ("Eau : 1 litre ou plus", "Deux flasques de 500 ml = 1 L.")}, False),
            ("food", "MMM", {"en": ("Food and energy supplements", ""), "fr": ("Suppléments énergétiques et nourriture", "")}, False),
            ("cup", "MMM", {"en": ("Reusable cup", "No cups at the aid stations."), "fr": ("Contenant à liquide réutilisable", "Aucun verre aux ravitaillements.")}, False),
            ("cap", "MMM", {"en": ("Cap, tuque or bandana", ""), "fr": ("Casquette, tuque ou foulard", "")}, False),
            ("blanket", "MMM", {"en": ("Survival blanket (1.4 m × 2 m)", ""), "fr": ("Couverture de survie (1,4 m × 2 m)", "")}, False),
            ("phone", "MMM", {"en": ("Cell phone", "With the race's emergency number saved."), "fr": ("Téléphone cellulaire", "Avec le numéro d'urgence de la course enregistré.")}, False),
            ("epipen", "MMM", {"en": ("EpiPen, if you have allergies", ""), "fr": ("Épipen, si vous avez des allergies", "")}, False),
        ],
    },
    "ultra-trail-des-chic-chocs": {
        "name": "Ultra-Trail des Chic-Chocs", "short": "UTCC",
        "where": {"en": "Sainte-Anne-des-Monts, Gaspésie, Québec", "fr": "Sainte-Anne-des-Monts, Gaspésie, Québec"},
        "when": {"en": "August 20–22, 2027", "fr": "20 au 22 août 2027"},
        "dists": ["170", "88", "45"], "default": "88",
        "src": "https://www.utchicchocs.com/88km",
        "read": {"en": "October 21, 2026", "fr": "21 octobre 2026"},
        "items": [
            ("jacket", "MMM", {"en": ("Waterproof jacket", ""), "fr": ("Veste imperméable", "")}, True),
            ("midlayer", "MM ", {"en": ("Mid-layer", ""), "fr": ("Couche intermédiaire", "")}, False),
            ("longpants", "MM ", {"en": ("Long pants", ""), "fr": ("Pantalon long", "")}, False),
            ("tuque", "MMM", {"en": ("Tuque", ""), "fr": ("Tuque", "")}, False),
            ("gloves", "MMM", {"en": ("Gloves", ""), "fr": ("Gants", "")}, False),
            ("headlamp", "MM ", {"en": ("Headlamp + spare battery", ""), "fr": ("Lampe frontale + batterie de rechange", "")}, True),
            ("water", "MMM", {"en": ("Water: 1.5 L (1 L on the 45 km)", "Three 500 ml soft flasks = 1.5 L."), "fr": ("Eau : 1,5 L (1 L au 45 km)", "Trois flasques de 500 ml = 1,5 L.")}, False),
            ("filter", "MMM", {"en": ("Purification tablets or a filter flask", ""), "fr": ("Pastilles de purification ou gourde avec filtre", "")}, False),
            ("food", "MMM", {"en": ("Energy supplements", ""), "fr": ("Suppléments énergétiques", "")}, False),
            ("cup", "MMM", {"en": ("Collapsible cup", ""), "fr": ("Verre ou gobelet rétractable", "")}, False),
            ("cap", "MMM", {"en": ("Cap or Buff", ""), "fr": ("Casquette ou Buff", "")}, False),
            ("blanket", "MMM", {"en": ("Survival blanket (140 × 200 cm)", ""), "fr": ("Couverture de survie (140 × 200 cm)", "")}, False),
            ("whistle", "MMM", {"en": ("Whistle", "Many race vests have one on the chest strap: check yours."), "fr": ("Sifflet", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre.")}, False),
            ("phone", "MMM", {"en": ("Cell phone in a waterproof bag", ""), "fr": ("Téléphone cellulaire dans un sac imperméable", "")}, False),
            ("firstaid", "MMM", {"en": ("Basic first aid kit", ""), "fr": ("Trousse de premiers soins de base", "")}, False),
            ("spoon", "MM ", {"en": ("Spoon and/or fork", ""), "fr": ("Cuillère et/ou fourchette", "")}, False),
            ("socks", "RR ", {"en": ("Spare shoes and socks", ""), "fr": ("Chaussures et bas de rechange", "")}, False),
            ("poles", "RR ", {"en": ("Hiking poles and/or crampons", ""), "fr": ("Bâtons de randonnée et/ou crampons", "")}, False),
            ("headlamp2", "RR ", {"en": ("Second headlamp", ""), "fr": ("2e lampe frontale", "")}, False),
            ("warmjacket", "RR ", {"en": ("Warm jacket for any weather", ""), "fr": ("Manteau chaud pour toutes conditions", "")}, False),
        ],
    },
    "ultra-trail-du-fjord-du-saguenay": {
        "name": "Ultra-Trail du Fjord-du-Saguenay", "short": "UTFS",
        "where": {"en": "Bas-Saguenay, Québec", "fr": "Bas-Saguenay, Québec"},
        "when": {"en": "August 6–8, 2027", "fr": "6 au 8 août 2027"},
        "dists": ["135", "100", "90", "55"], "default": "100", "cupless": True,
        "src": "https://www.ultratrailfjord.com/",
        "read": {"en": "October 21, 2026", "fr": "21 octobre 2026"},
        "items": [
            ("jacket", "MMMM", {"en": ("Waterproof windbreaker", ""), "fr": ("Coupe-vent imperméable", "")}, True),
            ("headlamp", "MMM ", {"en": ("Headlamp + spare batteries", ""), "fr": ("Lampe frontale + batteries de rechange", "")}, True),
            ("water", "MMMM", {"en": ("Water: 1.5 L on the 135 and 90 km, 1 L on the 100 and 55 km", "Three 500 ml soft flasks = 1.5 L."),
                               "fr": ("Eau : 1,5 L aux 135 et 90 km, 1 L aux 100 et 55 km", "Trois flasques de 500 ml = 1,5 L.")}, False),
            ("filter", "MMMM", {"en": ("Purification tablets or a filter flask", ""), "fr": ("Comprimés de purification ou gourde avec filtre", "")}, False),
            ("food", "MMMM", {"en": ("Food and energy food", ""), "fr": ("Nourriture et aliments énergétiques", "")}, False),
            ("cup", "MMMM", {"en": ("Reusable cup", "No cups at the aid stations."), "fr": ("Verre réutilisable", "Aucun verre fourni aux ravitaillements.")}, False),
            ("cap", "MMMM", {"en": ("Cap or bandana for the sun", ""), "fr": ("Casquette ou foulard pour le soleil", "")}, False),
            ("blanket", "MMMM", {"en": ("Survival blanket", ""), "fr": ("Couverture de survie", "")}, False),
            ("whistle", "MMMM", {"en": ("Whistle", "Many race vests have one on the chest strap: check yours."), "fr": ("Sifflet", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre.")}, False),
            ("phone", "MMMM", {"en": ("Cell phone", ""), "fr": ("Téléphone cellulaire", "")}, False),
            ("epipen", "MMMM", {"en": ("EpiPen, if you have allergies", ""), "fr": ("Épipen, si vous avez des allergies", "")}, False),
        ],
    },
}

# Oct 21 (Bastien: "10 more iconic races in Canada and 10 major races in the USA"): only races that publish a real mandatory list.
# UTMB North America (2026-2027 "Mandatory and Recommended Equipment" PDF, the same file on every event's regulation page, checked
# Oct 21, 2026): one list per category (100M, 100K, 50K, 20K = 21/25/28K), plus the hot/cold kits the race may call days before.
UTMB_NA = "https://pdf.utmb.world/image/upload/v1786553479/whistler/PDFS/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_3375f06592.pdf.pdf"
UTMB_CAT = {"100M": 0, "100K": 1, "50K": 2, "20K": 3}
UTMB_ITEMS = [   # kind, levels for 100M/100K/50K/20K, en, fr, spec
    ("vest", "MMRR", ("Running pack", "A vest, backpack or waist pack: it has to fit all the mandatory gear."),
     ("Sac de course", "Une veste, un sac à dos ou une ceinture : tout le matériel obligatoire doit y entrer."), False),
    ("phone", "MMMM", ("Cell phone", "With the race's safety numbers saved."), ("Téléphone cellulaire", "Avec les numéros de sécurité de la course enregistrés."), False),
    ("cup", "MMMM", ("Collapsible cup (150 ml / 5 oz or more)", "No disposable cups at the aid stations."),
     ("Gobelet pliable (150 ml ou plus)", "Aucun verre jetable aux ravitaillements."), False),
    ("water", "MMMM", ("Water: 1 litre (½ litre on the {short20})", "Two 500 ml soft flasks = 1 L."),
     ("Eau : 1 litre (½ litre au {short20})", "Deux flasques de 500 ml = 1 L."), False),
    ("headlamp", "MMR ", ("Headlamp + spare batteries", "200 lumens or more recommended for the main light."),
     ("Lampe frontale + piles de rechange", "200 lumens ou plus recommandés pour la lampe principale."), True),
    ("headlamp2", "M   ", ("Second headlamp + spare batteries", "100 miles only: two working headlamps."),
     ("2e lampe frontale + piles de rechange", "100 milles seulement : deux lampes frontales fonctionnelles."), False),
    ("food", "MMMR", ("Food reserve", "Recommended: about 800 kcal (2 gels + 2 bars)."), ("Réserve de nourriture", "Recommandé : environ 800 kcal (2 gels + 2 barres)."), False),
    ("jacket", "MMRR", ("Jacket with a hood for bad weather", "The hood is built in or attached the way the maker designed it."),
     ("Manteau avec capuchon pour le mauvais temps", "Capuchon intégré ou attaché par le système d'origine du fabricant."), True),
    ("cap", "MMRR", ("Hat: beanie, cap, bandana or Buff", ""), ("Chapeau : tuque, casquette, bandana ou Buff", ""), False),
    ("blanket", "MMMM", ("Survival blanket", ""), ("Couverture de survie", ""), False),
    ("whistle", "MMMM", ("Whistle", "Many race vests have one on the chest strap: check yours."),
     ("Sifflet", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre."), False),
    ("gloves", "RRRR", ("Gloves", ""), ("Gants", ""), False),
    ("id", "RRRR", ("ID card or passport", ""), ("Pièce d'identité ou passeport", ""), False),
    ("midlayer", "RRRR", ("Spare warm layer", "For cold rain, or if you get hurt and have to wait."), ("Couche chaude de rechange", "Pour la pluie froide, ou si vous êtes blessé et devez attendre."), False),
    ("poles", "RRRR", ("Trekking poles", "If you start with them, carry them the whole race."), ("Bâtons de marche", "Si vous partez avec, portez-les toute la course."), False),
    # the cold-weather kit (all distances), only if the race calls it
    ("sun", "MMMM", ("Protective eyewear", "Photochromic sunglasses can count for both kits."), ("Lunettes de protection", "Des lunettes photochromiques peuvent servir aux deux kits."), False),
    ("midlayer2", "MMMM", ("Second warm layer", "On top of the jacket."), ("Deuxième couche chaude", "En plus du manteau."), False),
    ("tuque", "MMMM", ("Warm hat", ""), ("Tuque chaude", ""), False),
    ("gloves2", "MMMM", ("Warm, waterproof gloves", ""), ("Gants chauds et imperméables", ""), True),
    ("pants", "MMMM", ("Waterproof overpants", ""), ("Surpantalon imperméable", ""), True),
    ("blanket2", "MMMM", ("Survival blanket, 1.40 × 2 m (55 × 80 in) or more", ""), ("Couverture de survie de 1,40 × 2 m ou plus", ""), False),
    # the hot-weather kit
    ("sun2", "MMMM", ("Sunglasses", ""), ("Lunettes de soleil", ""), False),
    ("sunscreen", "MMMM", ("Sunscreen", "SPF 50 recommended."), ("Crème solaire", "FPS 50 recommandé."), False),
    ("water2", "MMMM", ("Water: 2 litres instead of 1", "Four 500 ml soft flasks = 2 L."), ("Eau : 2 litres au lieu de 1", "Quatre flasques de 500 ml = 2 L."), False),
]
UTMB_KITS = {"bad": ["sun", "midlayer2", "tuque", "gloves2", "pants", "blanket2"], "hot": ["sun2", "sunscreen", "water2"]}


def utmb_na(cats):
    """The UTMB North America list for one event: cats = the UTMB category of each distance, in the race's order."""
    short20 = [d for d, c in cats if c == "20K"]
    out = []
    for kind, lv, en, fr, spec in UTMB_ITEMS:
        levels = "".join(lv[UTMB_CAT[c]] for _, c in cats)
        if not levels.strip():
            continue
        if kind == "water" and not short20:
            en, fr = ("Water: 1 litre", en[1]), ("Eau : 1 litre", fr[1])
        sh = " and ".join(short20)
        out.append((kind, levels, {"en": (en[0].format(short20=sh), en[1]), "fr": (fr[0].format(short20=sh.replace(" and ", " et ")), fr[1])}, spec))
    return out


def utmb_race(name, short, where, when, cats, src, side="ca", de="de l'", le="l'", default=None):
    return {"name": name, "short": short, "de": de, "le": le, "where": where, "when": when, "side": side,
            "dists": [d for d, _ in cats], "default": default or cats[0][0], "unit": "label", "src": src, "cupless": True,
            "read": {"en": "October 21, 2026 (2026–2027 list)", "fr": "21 octobre 2026 (liste 2026-2027)"},
            "kits": UTMB_KITS, "items": utmb_na(cats)}


RACES.update({
    "ultra-trail-whistler": utmb_race("Ultra-Trail Whistler by UTMB", "Whistler", {"en": "Whistler, BC", "fr": "Whistler, C.-B."},
                                      {"en": "June 25–27, 2027", "fr": "25 au 27 juin 2027"}, [("100K", "100K"), ("50K", "50K"), ("25K", "20K")], UTMB_NA),
    # Fat Dog 120 (2026 Racer Guide, linked from fatdog120.ca/about/race-guide.html, read Oct 21, 2026): every distance, same list
    "fat-dog-120": {
        "name": "Fat Dog 120", "short": "Fat Dog", "de": "du ", "le": "le ", "unit": "label",
        "where": {"en": "Cathedral & Manning Parks, BC", "fr": "Parcs Cathedral et Manning, C.-B."},
        "when": {"en": "August 2027 (date to come)", "fr": "Août 2027 (date à venir)"},
        "dists": ["120M", "100K", "40M"], "default": "120M", "cupless": True,
        "src": "https://fatdog120.ca/about/race-guide.html",
        "read": {"en": "October 21, 2026 (2026 Racer Guide)", "fr": "21 octobre 2026 (guide du coureur 2026)"},
        "items": [
            ("jacket", "MMM", {"en": ("Waterproof jacket with taped seams and a hood", ""), "fr": ("Manteau imperméable à coutures scellées avec capuchon", "")}, True),
            ("headlamp", "MMM", {"en": ("Two light sources + spare batteries", "A headlamp and a small flashlight, for example. Spare batteries don't count as the second light."),
                                 "fr": ("Deux sources de lumière + piles de rechange", "Par exemple une frontale et une petite lampe de poche. Les piles ne comptent pas comme 2e lumière.")}, True),
            ("water", "MMM", {"en": ("Fluid capacity: 2 litres or more", "A 3 L bladder is recommended: up to 25 km between water stops."),
                              "fr": ("Capacité de 2 litres ou plus", "Un sac d'hydratation de 3 L est recommandé : jusqu'à 25 km entre les points d'eau.")}, False),
            ("food", "MMM", {"en": ("Food reserve: 400 calories or more", "Only for an emergency."), "fr": ("Réserve de nourriture : 400 calories ou plus", "Seulement en cas d'urgence.")}, False),
            ("longpants", "MMM", {"en": ("Long pants or tights that cover the legs", "Tights + long socks also count. Waterproof pants are optional."),
                                  "fr": ("Pantalon ou collant couvrant les jambes", "Un collant + des bas longs comptent aussi. Le pantalon imperméable est facultatif.")}, False),
            ("midlayer", "MMM", {"en": ("Insulating long-sleeve layer", "Merino or light fleece recommended. A sun shirt or arm sleeves don't count."),
                                 "fr": ("Couche isolante à manches longues", "Mérinos ou laine polaire légère recommandés. Un chandail solaire ou des manchons ne comptent pas.")}, False),
            ("tuque", "MMM", {"en": ("Insulating hat or Buff", ""), "fr": ("Tuque ou Buff isolant", "")}, False),
            ("gloves", "MMM", {"en": ("Gloves", ""), "fr": ("Gants", "")}, False),
            ("cup", "MMM", {"en": ("Collapsible cup", "A cupless race: for drinks and food at every aid station."), "fr": ("Gobelet pliable", "Course sans verres : pour boire et manger à chaque ravito.")}, False),
            ("blanket", "MMM", {"en": ("Two survival blankets or one bivy", ""), "fr": ("Deux couvertures de survie ou un sac bivouac", "")}, False),
            ("whistle", "MMM", {"en": ("Whistle on the outside of your pack", "Many race vests have one on the chest strap: check yours."),
                                "fr": ("Sifflet à l'extérieur du sac", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre.")}, False),
            ("spoon", "MMM", {"en": ("Spoon or spork", "For the backcountry aid stations."), "fr": ("Cuillère ou cuillère-fourchette", "Pour les ravitos en arrière-pays.")}, False),
            ("gps", "MMM", {"en": ("GPS with the course loaded", "A phone or GPS watch works, charged for the whole race."),
                            "fr": ("GPS avec le parcours chargé", "Un téléphone ou une montre GPS, chargé pour toute la course.")}, False),
            ("tracker", "M  ", {"en": ("Race tracker on your pack", "Given by the race, 120 miles only."), "fr": ("Balise de la course sur le sac", "Fournie par la course, 120 milles seulement.")}, False),
            ("filter", "RRR", {"en": ("Filter flask or water treatment tablets", "If you drink from streams."), "fr": ("Gourde filtrante ou pastilles", "Si vous buvez dans les ruisseaux.")}, False),
            ("socks", "RRR", {"en": ("Extra pair of socks", ""), "fr": ("Bas de rechange", "")}, False),
            ("sunscreen", "RRR", {"en": ("Sunscreen and lip balm", ""), "fr": ("Crème solaire et baume à lèvres", "")}, False),
            ("bandage", "RRR", {"en": ("Compression bandage", ""), "fr": ("Bandage de compression", "")}, False),
            ("firstaid", "RRR", {"en": ("Small first aid and foot care kit", ""), "fr": ("Petite trousse de premiers soins et soins des pieds", "")}, False),
        ],
    },
})

# Oct 22 (Bastien: "Sinister SOO 200 and divide 200"): Sinister Sports' 200s. Their lists mix three things, labelled as the race does:
# P = mandatory but the race hands it out (inReach, bivvy, bib), M = mandatory you bring, R = recommended, L = listed by the race as
# "a mix of mandatory and recommended" without saying which (Divide 200): never shown as mandatory, never as optional
_SIN = lambda t, en, fr, enn="", frn="": (t, {"en": (en, enn), "fr": (fr, frn)})
RACES.update({
    # sinistersports.ca/soo200/rules_gear, "Mandatory (Provided by Sinister Sports)" + "Recommended" (read Oct 22, 2026); one list for every distance
    "soo-200": {
        "name": "SOO 200", "short": "SOO", "de": "du ", "le": "le ", "unit": "label", "suggested": True,
        "where": {"en": "Sault Ste. Marie, ON", "fr": "Sault-Sainte-Marie, Ont."},
        "when": {"en": "September 2027 (date to come; 2026: Sept. 11–15)", "fr": "Septembre 2027 (date à venir; 2026 : 11 au 15 sept.)"},
        "dists": ["200M", "100K", "50K"], "default": "200M", "cupless": True,
        "src": "https://www.sinistersports.ca/soo200/rules_gear",
        "read": {"en": "October 25, 2026 (confirmed with the race)", "fr": "25 octobre 2026 (confirmé avec la course)"},
        "items": [(k, lv, t, sp) for (k, t), lv, sp in [
            (_SIN("inreach", "Garmin inReach", "Garmin inReach", "Provided by the race.", "Fourni par la course."), "PPP", False),
            (_SIN("battery", "Battery backup", "Batterie de secours", "Provided at Stokely; the race swaps it at major aid stations.",
                  "Fournie à Stokely; la course l'échange aux gros ravitos."), "PPP", False),
            (_SIN("bib", "Race bib and timing chip", "Dossard et puce", "Provided by the race.", "Fournis par la course."), "PPP", False),
            (_SIN("bivy", "Emergency bivvy", "Sac bivouac d'urgence", "Provided by the race.", "Fourni par la course."), "PPP", False),
            (_SIN("headlamp", "Headlamp", "Lampe frontale"), "RRR", True),
            (_SIN("water", "2 L of fluid: bottles or a hydration pack", "2 L de liquide : gourdes ou sac d'hydratation",
                  "Checkpoints can be 20 to 42 km apart. No cups at aid stations: bring something to drink from.",
                  "Les points de contrôle peuvent être à 20-42 km. Pas de verres aux ravitos : apportez de quoi boire."), "RRR", False),
            (_SIN("filter", "Water filter", "Filtre à eau"), "RRR", False),
            (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant"), "RRR", True),
            (_SIN("tuque", "Toque or warm hat", "Tuque ou chapeau chaud"), "RRR", False),
            (_SIN("cap", "Sun hat", "Chapeau de soleil"), "RRR", False),
            (_SIN("gloves", "Full-finger gloves", "Gants à doigts complets"), "RRR", False),
            (_SIN("poles", "Running or trekking poles", "Bâtons de course ou de randonnée"), "RRR", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "RRR", False),
            (_SIN("bear", "Bear spray or bear banger", "Chasse-ours en aérosol ou pétard", "Only if you know how to use it.",
                  "Seulement si vous savez vous en servir."), "RRR", False),
        ]],
    },
    # sinistersports.ca/divide200/racer_information_package (read Oct 22, 2026). Oct 25, Kirsti (Sinister Sports) to Bastien: "We don't have
    # any mandatory gear. Other than ones bib and timing chip. And at the divide and SOO 200 the InReach": everything else = recommended
    "divide-200": {
        "name": "Divide 200", "short": "Divide", "de": "de la ", "le": "la ", "unit": "label", "suggested": True,
        "where": {"en": "Crowsnest Pass, AB", "fr": "Crowsnest Pass, Alb."},
        "when": {"en": "August 16–20, 2027", "fr": "16 au 20 août 2027"},
        "dists": ["200M", "100K"], "default": "200M", "cupless": True,
        "src": "https://www.sinistersports.ca/divide200/racer_information_package",
        "read": {"en": "October 25, 2026 (confirmed with the race)", "fr": "25 octobre 2026 (confirmé avec la course)"},
        "items": [(k, lv, t, sp) for (k, t), lv, sp in [
            (_SIN("headlamp", "Headlamp", "Lampe frontale", "You'll be out after dark.", "Vous serez dehors à la nuit tombée."), "RR", True),
            (_SIN("inreach", "Garmin inReach + Spotwalla tracking", "Garmin inReach + suivi Spotwalla",
                  "Provided by the race, returned at the end.", "Fourni par la course, rendu à la fin."), "PP", False),
            (_SIN("battery", "Battery backup", "Batterie de secours", "Provided; more at major aid stations.", "Fournie; d'autres aux gros ravitos."), "PP", False),
            (_SIN("bib", "Race bib and timing chip", "Dossard et puce", "Provided by the race.", "Fournis par la course."), "PP", False),
            (_SIN("bivy", "Emergency bivvy", "Sac bivouac d'urgence", "Provided by the race.", "Fourni par la course."), "PP", False),
            (_SIN("orange", "Blaze orange clothing item", "Vêtement orange vif", "The race gives a neck gaiter (hunting season). Extra bright clothing welcome.",
                  "La course donne un cache-cou (saison de chasse). Des vêtements voyants en plus sont bienvenus."), "PP", False),
            (_SIN("water", "2 L of fluid: bottles or a hydration pack", "2 L de liquide : gourdes ou sac d'hydratation",
                  "No cups at aid stations: bring something to drink from.", "Pas de verres aux ravitos : apportez de quoi boire."), "RR", False),
            (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant"), "RR", True),
            (_SIN("tuque", "Toque or warm hat", "Tuque ou chapeau chaud"), "RR", False),
            (_SIN("cap", "Sun hat", "Chapeau de soleil"), "RR", False),
            (_SIN("gloves", "Full-finger gloves", "Gants à doigts complets"), "RR", False),
            (_SIN("poles", "Running or trekking poles", "Bâtons de course ou de randonnée"), "RR", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "RR", False),
            (_SIN("bear", "Bear spray or bear banger", "Chasse-ours en aérosol ou pétard", "Only if you know how to use it.",
                  "Seulement si vous savez vous en servir."), "RR", False),
        ]],
    },
})

# Oct 27 (Bastien, via the growth chat, for his Sinister Sports call): the series' other races. Each one's own "Recommended Gear" list
# (rules_gear pages, read Oct 27, 2026); no gear is mandatory but the bib + timing chip (+ the Death Race coin) the race hands out (P).
# "suggested": every R reads "Suggested by the race", titles say "suggested gear list", a line on top says nothing is required.
_SBIB = [(_SIN("bib", "Race bib and timing chip", "Dossard et puce", "Handed out by the race; wear them the whole race.",
               "Remis par la course; portez-les toute la course."), "P", False)]
_SBASE = lambda dark="after 8 pm", dfr="après 20 h": [
    (_SIN("headlamp", "Headlamp", "Lampe frontale", f"Carry it {dark}.", f"À traîner {dfr}."), "R", True),
    (_SIN("water", "2 L of fluid: bottles or a hydration pack", "2 L de liquide : gourdes ou sac d'hydratation",
          "No cups at aid stations: bring something to drink from.", "Pas de verres aux ravitos : apportez de quoi boire."), "R", False),
    (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant"), "R", True),
    (_SIN("tuque", "Toque or warm hat", "Tuque ou chapeau chaud"), "R", False),
    (_SIN("cap", "Sun hat", "Chapeau de soleil"), "R", False),
    (_SIN("whistle", "Whistle", "Sifflet"), "R", False),
    (_SIN("blanket", "Space blanket", "Couverture de survie"), "R", False),
    (_SIN("bear", "Bear spray or bear banger", "Chasse-ours en aérosol ou pétard", "Only if you know how to use it.",
          "Seulement si vous savez vous en servir."), "R", False),
]
_sin = lambda rows, n: [(k, lv * n, tx, sp) for (k, tx), lv, sp in rows]
_SREAD = {"en": "October 27, 2026", "fr": "27 octobre 2026"}
RACES.update({
    "sinister-7": {
        "name": "Sinister 7 Ultra", "short": "Sinister 7", "de": "du ", "le": "le ", "unit": "label", "suggested": True, "cupless": True,
        "where": {"en": "Crowsnest Pass, AB", "fr": "Crowsnest Pass, Alb."}, "when": {"en": "July 10–11, 2027", "fr": "10 et 11 juillet 2027"},
        "dists": ["100M", "50M", "50K", "HALF"], "default": "100M", "labels": {"HALF": {"en": "Half marathon", "fr": "Demi-marathon"}},
        "src": "https://www.sinistersports.ca/sinister7/rules_gear", "read": _SREAD,
        "items": _sin(_SBASE() + _SBIB, 4),
    },
    "canadian-death-race": {
        "name": "Canadian Death Race", "short": "Death Race", "de": "de la ", "le": "la ", "unit": "label", "suggested": True,
        "where": {"en": "Grande Cache, AB", "fr": "Grande Cache, Alb."}, "when": {"en": "July 31–August 1, 2027", "fr": "31 juillet et 1er août 2027"},
        "dists": ["118K", "42K"], "default": "118K",
        "src": "https://www.sinistersports.ca/deathrace/rules_gear", "read": _SREAD,
        "items": _sin([
            (_SIN("headlamp", "Headlamp with new batteries", "Lampe frontale avec piles neuves", "Carry it after 6 pm.", "À traîner après 18 h."), "R", True),
            (_SIN("water", "Full water bottle or hydration pack", "Gourde pleine ou sac d'hydratation"), "R", False),
            (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant"), "R", True),
            (_SIN("tuque", "Toque or warm hat", "Tuque ou chapeau chaud"), "R", False),
            (_SIN("cap", "Sun hat", "Chapeau de soleil"), "R", False),
            (_SIN("sun", "Sunglasses", "Lunettes de soleil"), "R", False),
            (_SIN("eyes", "Clear eye protection", "Lunettes à verres clairs", "For Leg 5's dense forest.", "Pour la forêt dense de l'étape 5."), "R", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "R", False),
            (_SIN("blanket", "Space blanket", "Couverture de survie"), "R", False),
            (_SIN("bear", "Bear spray or bear banger", "Chasse-ours en aérosol ou pétard", "Only if you know how to use it.",
                  "Seulement si vous savez vous en servir."), "R", False),
        ] + _SBIB + [(_SIN("coin", "Death Race coin", "Pièce de la Death Race", "Handed out at check-in; pay the ferryman with it at the river. Lose it and you can't finish.",
                           "Remise à l'inscription; elle paie le passeur à la rivière. Perdue, vous ne pouvez pas finir."), "P", False)], 2),
    },
    "black-spur-ultra": {
        "name": "Black Spur Ultra", "short": "Black Spur", "de": "du ", "le": "le ", "unit": "label", "suggested": True, "cupless": True,
        "where": {"en": "Kimberley, BC", "fr": "Kimberley, C.-B."}, "when": {"en": "August 28–29, 2027", "fr": "28 et 29 août 2027"},
        "dists": ["108K", "54K", "HALF"], "default": "108K", "labels": {"HALF": {"en": "Half marathon", "fr": "Demi-marathon"}},
        "src": "https://www.sinistersports.ca/blackspur/rules_gear", "read": _SREAD,
        "items": _sin(_SBASE() + _SBIB, 3),
    },
    "castle-alpine": {
        "name": "Castle Alpine Trail", "short": "Castle Alpine", "de": "du ", "le": "le ", "unit": "label", "suggested": True, "cupless": True,
        "where": {"en": "Castle Mountain Resort, AB", "fr": "Castle Mountain Resort, Alb."},
        "when": {"en": "September (2027 date to come; 2026: Sept. 19)", "fr": "Septembre (date 2027 à venir; 2026 : 19 sept.)"},
        "dists": ["28K"], "default": "28K",
        "src": "https://www.sinistersports.ca/castlealpine/rules_gear", "read": _SREAD,
        "items": _sin(_SBASE() + _SBIB, 1),
    },
    "vertical-vendetta": {
        "name": "Vertical Vendetta", "short": "Vendetta", "de": "du ", "le": "le ", "unit": "label", "suggested": True,
        "where": {"en": "Crowsnest Pass, AB (9.75 km, 1,000 m up)", "fr": "Crowsnest Pass, Alb. (9,75 km, 1 000 m D+)"}, "when": {"en": "May 29, 2027", "fr": "29 mai 2027"},
        "dists": ["VK"], "default": "VK", "labels": {"VK": {"en": "Vertical K", "fr": "Kilomètre vertical"}},
        "src": "https://www.sinistersports.ca/verticalvendetta/rules_gear", "read": _SREAD,
        "items": _sin([
            (_SIN("water", "1 to 2 L of fluid: bottles or a hydration pack", "1 à 2 L de liquide : gourdes ou sac d'hydratation"), "R", False),
            (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant"), "R", True),
            (_SIN("tuque", "Toque or warm hat", "Tuque ou chapeau chaud"), "R", False),
            (_SIN("cap", "Sun hat", "Chapeau de soleil"), "R", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "R", False),
            (_SIN("blanket", "Space blanket", "Couverture de survie"), "R", False),
        ] + _SBIB, 1),
    },
    "the-dark-24": {
        "name": "The Dark 24", "short": "The Dark", "de": "de ", "le": "", "unit": "label", "suggested": True,
        "where": {"en": "Bellevue Underground Mine, Crowsnest Pass, AB", "fr": "Mine souterraine de Bellevue, Crowsnest Pass, Alb."},
        "when": {"en": "Oct. 31–Nov. 1 (2027 date to come)", "fr": "31 oct. et 1er nov. (date 2027 à venir)"},
        "dists": ["24h", "12h", "6h"], "default": "24h", "labels": {d: {"en": f"{d[:-1]}-hour", "fr": f"{d[:-1]} h"} for d in ("24h", "12h", "6h")},
        "src": "https://www.sinistersports.ca/thedark/rules_gear", "read": _SREAD,
        "items": _sin([
            (_SIN("waistlight", "Waist light (optional)", "Lampe de ceinture (facultative)", "500 m loops in a mine shaft.", "Boucles de 500 m dans un puits de mine."), "R", False),
            (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant"), "R", True),
            (_SIN("tuque", "Toque or warm hat", "Tuque ou chapeau chaud"), "R", False),
            (_SIN("blanket", "Space blanket", "Couverture de survie"), "R", False),
            (_SIN("warmjacket", "Warm blanket and clothes for your breaks", "Couverture et vêtements chauds pour les pauses",
                  "For the aid station when you stop.", "Pour le ravito quand vous arrêtez."), "R", False),
        ] + _SBIB, 3),
    },
})

# USA side (Oct 21): /us/races/, English, prices in US$ from deals-us.json
US_EV = {
    "canyons": "v1787099482/canyons/2027%20PDFs/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_e562161c6e.pdf.pdf",
    "desertrats": "v1787099336/desertrats/2027%20PDFs/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_6e26582fe1.pdf.pdf",
    "rothrock": "v1787145639/rothrock/Race%20Regs%20and%20Man.%20Gear%20Fall%202026/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_3375f06592_pdf_83b85beef5.pdf.pdf",
    "chattanooga": "v1785433896/chattanooga/Race%20Regs%20and%20Gear/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_d208f605bf.pdf.pdf",
    "speedgoat": "v1787100011/speedgoat/2027%20PDFs/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_a09e12053b.pdf.pdf",
    "snowbasin": "v1786541690/snowbasin/Race%20Regs%20and%20Gear/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_f772a1224d.pdf.pdf",
    "grindstone": "v1787683381/grindstone/Race%20Regs%20and%20Man.%20Gear%20Fall%202026/2026_and_2027_UTMB_MANDATORY_and_RECOMMENDED_EQUIPMENT_North_America_1_3375f06592_pdf_b283634717.pdf.pdf",
}
_us = lambda ev: "https://pdf.utmb.world/image/upload/" + US_EV[ev]
_w = lambda en, fr: {"en": en, "fr": fr}
RACES.update({
    "canyons-endurance-runs": utmb_race("Canyons Endurance Runs by UTMB", "Canyons", _w("Auburn, California", "Auburn, Californie"), _w("April 22–25, 2027", "22 au 25 avril 2027"),
                                        [("100M", "100M"), ("100K", "100K"), ("50K", "50K"), ("25K", "20K")], _us("canyons"), "us"),
    "desert-rats": utmb_race("Desert RATS Trail Running Festival by UTMB", "Desert RATS", _w("Fruita, Colorado", "Fruita, Colorado"), _w("April 8–11, 2027", "8 au 11 avril 2027"),
                             [("100K", "100K"), ("50K", "50K"), ("21K", "20K")], _us("desertrats"), "us"),
    "rothrock": utmb_race("Rothrock by UTMB", "Rothrock", _w("Tussey Mountain, Pennsylvania", "Tussey Mountain, Pennsylvanie"), _w("May 14–16, 2027", "14 au 16 mai 2027"),
                          [("50K", "50K"), ("25K", "20K")], _us("rothrock"), "us"),
    "ultra-trail-chattanooga": utmb_race("Ultra Trail Chattanooga by UTMB", "Chattanooga", _w("Chattanooga, Tennessee", "Chattanooga, Tennessee"), _w("June 4–6, 2027", "4 au 6 juin 2027"),
                                         [("100K", "100K"), ("50K", "50K"), ("20K", "20K")], _us("chattanooga"), "us"),
    "speedgoat": utmb_race("Speedgoat Mountain Races by UTMB", "Speedgoat", _w("Snowbird, Utah", "Snowbird, Utah"), _w("July 22–24, 2027", "22 au 24 juillet 2027"),
                           [("50K", "50K")], _us("speedgoat"), "us"),
    "snowbasin": utmb_race("Snowbasin by UTMB", "Snowbasin", _w("Snowbasin Resort, Utah", "Snowbasin Resort, Utah"), _w("September 16–18, 2027", "16 au 18 septembre 2027"),
                           [("58K", "50K"), ("28K", "20K")], _us("snowbasin"), "us"),
    "grindstone": utmb_race("Grindstone Trail Running Festival by UTMB", "Grindstone", _w("Natural Chimneys Park, Virginia", "Natural Chimneys Park, Virginie"), _w("September 23–26, 2027", "23 au 26 septembre 2027"),
                            [("100M", "100M"), ("100K", "100K"), ("50K", "50K"), ("21K", "20K")], _us("grindstone"), "us"),
})

# Oct 22 (Bastien: "Add cocodona races, and mammoth ultras"). Cocodona (Aravaipa): the 2027 Runner Guide's "Gear Requirements (Applies
# to ALL DISTANCES)": Required Gear the whole course, Cold Weather Gear carried on some sections (checked at set aid stations), the
# hooded jacket only in rain or snow, then "Additional Recommended Gear". The guide is a Google Doc: race_check reads its text
# export (`check`). Mammoth Trailfest's 50K says "No gear requirements" (recommended only): left out, like Hardrock.
_C = lambda en, fr: {"en": en, "fr": fr}
_COLD = ("Cold-weather gear: carried on some sections, checked at set aid stations (80 mi: if you leave Fain Ranch after 11 am; "
         "40 mi: if you leave Woody Mountain after 2:30 pm).",
         "Matériel pour le froid : à porter sur certaines sections, vérifié à des ravitos précis (80 mi : si vous quittez Fain Ranch "
         "après 11 h; 40 mi : si vous quittez Woody Mountain après 14 h 30).")
_CC = ("Cold-weather gear (see gloves).", "Matériel pour le froid (voir les gants).")
RACES.update({
    "cocodona": {
        "name": "Cocodona", "short": "Cocodona", "de": "de la ", "le": "la ", "unit": "label", "side": "us", "cupless": True,
        "where": _C("Black Canyon City to Flagstaff, Arizona", "De Black Canyon City à Flagstaff, Arizona"),
        "when": _C("May 2–7, 2027", "2 au 7 mai 2027"),
        "dists": ["250M", "125M", "100M", "80M", "40M"], "default": "250M",
        "src": "https://docs.google.com/document/d/1mG-qAY3yvHnL9oUCd5c1-ZEWwxvkgfpYxHcU9ppfjlQ/edit",
        "check": "https://docs.google.com/document/d/1mG-qAY3yvHnL9oUCd5c1-ZEWwxvkgfpYxHcU9ppfjlQ/export?format=txt",
        "read": _C("October 22, 2026 (2027 Runner Guide)", "22 octobre 2026 (guide du coureur 2027)"),
        "kits": {"bad": ["jacket"]},
        "items": [(k, lv, t, sp) for (k, t), lv, sp in [
            (_SIN("phone", "Cell phone", "Téléphone cellulaire", "Runners and pacers alike.", "Coureurs et accompagnateurs."), "MMMMM", False),
            (_SIN("gps", "GPS device with the course file loaded", "Appareil GPS avec le tracé chargé",
                  "Watch, handheld GPS or a phone in airplane mode, plus a way to charge it.",
                  "Montre, GPS de poche ou téléphone en mode avion, et de quoi le recharger."), "MMMMM", False),
            (_SIN("headlamp", "Headlamp + spare batteries or a way to charge it", "Lampe frontale + piles de rechange ou de quoi la recharger"), "MMMMM", True),
            (_SIN("cup", "Collapsible cup", "Gobelet pliable", "No cups for cold drinks at aid stations (they have cups for hot ones).",
                  "Pas de verres pour les boissons froides aux ravitos (il y en a pour les boissons chaudes)."), "MMMMM", False),
            (_SIN("blanket", "Space blanket", "Couverture de survie"), "MMMMM", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "MMMMM", False),
            (_SIN("vest", "Room for 4 L of water", "De quoi porter 4 L d'eau",
                  "250 and 100 mi: checked at the start, and you must leave Cottonwood Creek with 4 L (25 hot miles to the next aid).",
                  "250 et 100 mi : vérifié au départ, et il faut quitter Cottonwood Creek avec 4 L (40 km chauds jusqu'au prochain ravito)."), "M M  ", False),
            (_SIN("gloves", "Gloves", "Gants", *_COLD), "MMMMM", False),
            (_SIN("tuque", "Warm hat (a neck gaiter counts)", "Tuque (un cache-cou compte)", *_CC), "MMMMM", False),
            (_SIN("midlayer", "Long-sleeve top", "Haut à manches longues", *_CC), "MMMMM", False),
            (_SIN("warmjacket", "Insulating layer: fleece, puffy or mid-weight", "Couche isolante : polaire, doudoune ou mi-saison", *_CC), "MMMMM", False),
            (_SIN("jacket", "Waterproof jacket with a hood", "Manteau imperméable avec capuchon",
                  "Only required in rain or snow.", "Obligatoire seulement en cas de pluie ou de neige."), "MMMMM", True),
            (_SIN("socks", "Plenty of sock changes + wipes", "Plusieurs paires de bas + lingettes",
                  "Every 20 to 30 miles, from your crew or drop bags.", "Aux 30 à 50 km, par votre équipe ou vos sacs de ravito."), "RRRRR", False),
            (_SIN("poles", "Trekking poles", "Bâtons de marche"), "RRRRR", False),
            (_SIN("wind", "Lightweight jacket", "Manteau léger"), "RRRRR", False),
            (_SIN("longpants", "Long pants", "Pantalon long"), "RRRRR", False),
            (_SIN("sunscreen", "Sunscreen", "Crème solaire"), "RRRRR", False),
            (_SIN("cap", "Sun hat", "Chapeau de soleil"), "RRRRR", False),
            (_SIN("midlayer2", "Long-sleeve sun layer", "Haut à manches longues contre le soleil"), "RRRRR", False),
            (_SIN("sun", "Sunglasses", "Lunettes de soleil"), "RRRRR", False),
            (_SIN("gloves4", "Sun gloves", "Gants contre le soleil"), "RRRRR", False),
            (_SIN("gaiters", "Gaiters", "Guêtres"), "RRRRR", False),
        ]],
    },
    # themammoth200.com/runnersmanual -> runners manual PDF ("updated 9/29/26"), "Gear Requirements": Mandatory at All Times,
    # Mandatory Night Gear (the puffy only if the race activates cold-weather gear), "Recommended, but not Required"
    "mammoth-200": {
        "name": "Mammoth 200", "short": "Mammoth", "de": "du ", "le": "le ", "unit": "label", "side": "us",
        "where": _C("Mammoth Lakes, California", "Mammoth Lakes, Californie"),
        "when": _C("Early October 2027 (date to come; 2026: Oct. 2–6)", "Début octobre 2027 (date à venir; 2026 : 2 au 6 oct.)"),
        "dists": ["200M"], "default": "200M",
        "src": "https://www.themammoth200.com/s/theMAMMOTH-runners-manual-2.pdf",
        "read": _C("October 22, 2026 (manual updated Sept. 29, 2026)", "22 octobre 2026 (guide mis à jour le 29 sept. 2026)"),
        "kits": {"bad": ["warmjacket"]},
        "items": [(k, lv, t, sp) for (k, t), lv, sp in [
            (_SIN("jacket", "Waterproof jacket with taped seams", "Manteau imperméable à coutures scellées", "Mandatory at all times.", "Obligatoire en tout temps."), "M", True),
            (_SIN("headlamp", "Headlamp + spare batteries or battery pack", "Lampe frontale + piles de rechange ou batterie"), "M", True),
            (_SIN("headlamp2", "Second headlamp", "Deuxième lampe frontale", "Required at night.", "Obligatoire la nuit."), "M", True),
            (_SIN("vest", "Room for 3 L of water", "De quoi porter 3 L d'eau", "It doesn't have to be full all the time.",
                  "Pas besoin d'être plein en tout temps."), "M", False),
            (_SIN("gloves", "Gloves (light or liner is fine)", "Gants (légers ou sous-gants, ça va)"), "M", False),
            (_SIN("tuque", "Warm hat or Buff", "Tuque ou Buff"), "M", False),
            (_SIN("pants", "Waterproof pants", "Pantalon imperméable", "Night gear, checked leaving the early-evening aid station. In the day too if weather is forecast.",
                  "Matériel de nuit, vérifié en quittant le ravito de début de soirée. Le jour aussi si la météo l'annonce."), "M", True),
            (_SIN("midlayer", "Spare long-sleeve layer", "Haut à manches longues de rechange", "Night gear: a dry base layer to change into.",
                  "Matériel de nuit : une couche de base sèche pour se changer."), "M", False),
            (_SIN("warmjacket", "Insulated or puffy layer", "Couche isolante ou doudoune", "At night, only if the race activates cold-weather gear (said at the briefing).",
                  "La nuit, seulement si la course l'exige (annoncé au briefing)."), "M", False),
            (_SIN("phone", "Cell phone", "Téléphone cellulaire"), "M", False),
            (_SIN("battery", "Power bank (10,000 mAh or more)", "Batterie externe (10 000 mAh ou plus)"), "M", False),
            (_SIN("gps", "GPS device with the course map, and a way to recharge it", "Appareil GPS avec le tracé, et de quoi le recharger",
                  "Phone or watch; the battery has to last 50 to 110 hours.", "Téléphone ou montre; la pile doit tenir de 50 à 110 heures."), "M", False),
            (_SIN("cup", "Collapsible cup", "Gobelet pliable"), "M", False),
            (_SIN("blanket", "Emergency bivvy", "Sac bivouac d'urgence"), "M", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "M", False),
            (_SIN("food", "Extra food: what you plan to eat + 400 calories", "Nourriture : ce que vous prévoyez + 400 calories"), "M", False),
            (_SIN("electrolytes", "Electrolytes", "Électrolytes"), "M", False),
            (_SIN("tp", "Toilet paper + 2 ziplock bags", "Papier de toilette + 2 sacs ziplock", "To pack used paper out.", "Pour rapporter le papier utilisé."), "M", False),
            (_SIN("inreach", "Satellite messenger (inReach)", "Communicateur satellite (inReach)", "Many sections have no cell service.",
                  "Plusieurs sections n'ont pas de réseau."), "R", False),
            (_SIN("filter", "Water filter for a bottle", "Filtre à eau pour gourde"), "R", False),
            (_SIN("longpants", "Tights or pants", "Collant ou pantalon"), "R", False),
            (_SIN("poles", "Trekking poles", "Bâtons de marche"), "R", False),
            (_SIN("gaiters", "Gaiters", "Guêtres", "For the eastern Sierra pumice.", "Pour la pierre ponce de la Sierra Est."), "R", False),
            (_SIN("cap", "Sun hat or Buff", "Chapeau de soleil ou Buff"), "R", False),
            (_SIN("sun", "Sunglasses", "Lunettes de soleil"), "R", False),
            (_SIN("sunscreen", "Sunscreen + lip balm", "Crème solaire + baume à lèvres"), "R", False),
            (_SIN("xshoes", "Extra shoes (a different model helps)", "Souliers de rechange (un autre modèle aide)"), "R", False),
            (_SIN("firstaid", "Anti-chafe, KT tape, bandages, duct tape, wipes", "Anti-frottement, ruban KT, pansements, ruban adhésif, lingettes"), "R", False),
            (_SIN("sleep", "Earplugs + eye mask", "Bouchons + masque pour dormir"), "R", False),
            (_SIN("card", "Credit card", "Carte de crédit"), "R", False),
            (_SIN("meds", "Medications, toiletries, contact lenses", "Médicaments, articles de toilette, verres de contact"), "R", False),
        ]],
    },
})

# Oct 22 (Bastien: "add other Quebec races and more like Tahoe 200 and destination races. Also look into races in salt lake area").
# Destination Trail: each race's 2027 Runner Manual (a Google Doc linked from destinationtrailrun.com/<race>), "Required (Mandatory)
# Gear ... to Carry at ALL Times" + "Recommended Gear ... at ALL Times". The SPOT tracker, the bivy/blanket and one wag bag come in the
# runner bag = P. Bigfoot 20M ("There is no mandatory gear") left out. Salt Lake area: Speedgoat + Snowbasin are already in; Wasatch 100,
# Bear 100 (its site answers 403), Kat'cina Mosa, Goat Rattler and Salt and Sulfur publish no gear list: left out.
_gdoc = lambda d: {"src": f"https://docs.google.com/document/d/{d}/edit", "check": f"https://docs.google.com/document/d/{d}/export?format=txt"}
_DT_READ = _C("October 22, 2026 (2027 Runner Manual)", "22 octobre 2026 (guide du coureur 2027)")
_PROV = ("In your runner bag; pacers bring their own.", "Dans votre sac de coureur; les accompagnateurs apportent le leur.")
_DTM = {   # mandatory lines shared by the 200s, by key
    "spot": _SIN("tracker", "SPOT tracker", "Balise SPOT", "Provided by the race.", "Fournie par la course."),
    "bivy": _SIN("bivy", "Emergency bivy", "Sac bivouac d'urgence", *_PROV),
    "blanket": _SIN("bivy", "Emergency blanket", "Couverture de survie", *_PROV),
    "wag": _SIN("wag", "Wag bag (packing out human waste)", "Sac hygiénique (wag bag)", "One in your runner bag; bring spares in drop bags.",
                "Un dans votre sac de coureur; mettez-en d'autres dans vos sacs de ravito."),
    "jacket": _SIN("jacket", "Jacket with a hood", "Manteau avec capuchon"),
    "wjacket": _SIN("jacket", "Waterproof jacket with a hood", "Manteau imperméable avec capuchon"),
    "gloves": _SIN("gloves", "Gloves", "Gants"),
    "hat": _SIN("tuque", "Hat or Buff", "Tuque ou Buff"),
    "pants": _SIN("longpants", "Pants or tights covering the whole leg", "Pantalon ou collant qui couvre toute la jambe"),
    "layer": _SIN("midlayer", "Long-sleeve insulating layer", "Couche isolante à manches longues"),
    "lamp": _SIN("headlamp", "Headlamp or waist light", "Lampe frontale ou lampe de taille"),
    "batt": _SIN("battery", "Extra batteries", "Piles de rechange"),
    "phone": _SIN("phone", "Cell phone", "Téléphone cellulaire"),
    "gps": _SIN("gps", "Device with the course GPX", "Appareil avec le tracé GPX du parcours"),
    "food": _SIN("food", "500 extra calories, for emergencies only", "500 calories de plus, pour les urgences seulement"),
    "whistle": _SIN("whistle", "Whistle", "Sifflet"),
    "filter": _SIN("filter", "Water filter", "Filtre à eau"),
    "vest3": _SIN("vest", "Room for 3 L of water", "De quoi porter 3 L d'eau"),
}
_DTR = [   # "Recommended Gear ... to Carry at ALL Times", same on every 200
    _SIN("gaiters", "Gaiters", "Guêtres"),
    _SIN("headlamp2", "Extra headlamp", "Deuxième lampe frontale"),
    _SIN("vest", "Room for 3 L of water", "De quoi porter 3 L d'eau"),
    _SIN("cap", "Sun hat", "Chapeau de soleil"),
    _SIN("filter", "Water filter", "Filtre à eau"),
    _SIN("warmjacket", "Puffy jacket with a hood", "Doudoune avec capuchon"),
    _SIN("battery2", "Battery pack", "Batterie externe"),
    _SIN("cap2", "Neck gaiter", "Cache-cou"),
    _SIN("firstaid", "First aid kit", "Trousse de premiers soins"),
    _SIN("sunscreen", "Sunscreen", "Crème solaire"),
    _SIN("tp", "Toilet paper, wipes, zip locks", "Papier de toilette, lingettes, sacs ziplock"),
    _SIN("id", "ID, emergency contacts, allergies and meds card", "Pièce d'identité, contacts d'urgence, fiche allergies et médicaments"),
]
def _dt(name, short, where, when, dist, doc, mand, rec_skip=(), rec_add=(), le="le "):
    """A Destination Trail 200: P for what the race hands out, M for the rest of its mandatory table, R for its recommended table."""
    prov = {"spot", "bivy", "blanket", "wag"}
    items = [(t, "P" if k in prov else "M", False) for k, t in ((k, _DTM[k]) for k in mand)]
    items += [(t, "R", False) for t in _DTR if t[0] not in rec_skip] + [(t, "R", False) for t in rec_add]
    return dict(name=name, short=short, de="du " if le == "le " else "de la ", le=le, unit="label", side="us", where=where, when=when,
                dists=[dist], default=dist, read=_DT_READ, cupless=False,
                items=[(k, lv, t, sp) for (k, t), lv, sp in items], **_gdoc(doc))
_200 = ["spot", "jacket", "gloves", "hat", "pants", "layer", "lamp", "batt", "phone", "gps", "food", "whistle"]
RACES.update({
    "tahoe-200": _dt("Tahoe 200", "Tahoe", _C("Lake Tahoe loop, Stateline, Nevada", "Tour du lac Tahoe, Stateline, Nevada"),
                     _C("June 21–25, 2027", "21 au 25 juin 2027"), "200M", "1fPMytqObJhMBSZwAqsCoFgySWXIA5BMzQnfwLsqof6E", _200 + ["blanket", "wag"]),
    "bigfoot-200": _dt("Bigfoot 200", "Bigfoot", _C("Mount St. Helens to Randle, Washington", "Du mont St. Helens à Randle, Washington"),
                       _C("August 13–17, 2027", "13 au 17 août 2027"), "200M", "1BsbZPVf0kX86cAcaPgjOLOGV5OXOZB9b6RX0969x9ew",
                       _200 + ["filter", "bivy", "wag"], rec_skip={"filter"}),
    "moab-240": _dt("Moab 240", "Moab", _C("Moab, Utah", "Moab, Utah"), _C("October 8–12, 2027", "8 au 12 octobre 2027"), "240M",
                    "1fyxqaoYl-PRDkYE9OGvRt6JHHDx0npV58nEuS1cY4X8", _200 + ["bivy", "wag"]),
    "arizona-monster-300": _dt("Arizona Monster 300", "AZ Monster", _C("Patagonia to Superior, Arizona", "De Patagonia à Superior, Arizona"),
                               _C("March 29 – April 4, 2027", "29 mars au 4 avril 2027"), "300M", "1atspiqj84qFRVoZFN7M4PqIGheark3LQI9dOBh_3EM0",
                               ["wjacket" if k == "jacket" else k for k in _200] + ["bivy"]),
    "el-jefe-100": _dt("El Jefe 100", "El Jefe", _C("Superior, Arizona", "Superior, Arizona"), _C("April 3–4, 2027", "3 et 4 avril 2027"), "100M",
                       "12zIokTrSctB1pSTCOOWJWvK8gw_wJ7lwsqJuY6tdRUY",
                       ["spot", "wjacket", "lamp", "batt", "phone", "gps", "food", "whistle", "vest3", "filter", "bivy"],
                       rec_skip={"vest", "filter"},
                       rec_add=[_SIN("vest2", "Room for 5 L if you drink a lot", "De quoi porter 5 L si vous buvez beaucoup",
                                     "From Gila to Picketpost.", "De Gila à Picketpost.")]),
    # destinationtrailrun.com/tahoe-100k -> 2027 Runner Manual, "Required Gear to Carry at ALL Times" + "Recommended Gear"
    "tahoe-100k": dict(name="Tahoe 100K", short="Tahoe 100K", de="du ", le="le ", unit="label", side="us",
                       where=_C("Heavenly Stagecoach Lodge, Stateline, Nevada", "Heavenly Stagecoach Lodge, Stateline, Nevada"),
                       when=_C("June 19–20, 2027", "19 et 20 juin 2027"), dists=["100K"], default="100K", read=_DT_READ,
                       items=[(k, lv, t, sp) for (k, t), lv, sp in [
                           (_DTM["spot"], "P", False),
                           (_SIN("headlamp", "Headlamp + spare batteries", "Lampe frontale + piles de rechange"), "M", True),
                           (_SIN("jacket", "Jacket", "Manteau", "The race may add or change gear with the forecast.",
                                 "La course peut ajouter ou changer du matériel selon la météo."), "M", False),
                           (_DTM["gloves"], "M", False), (_DTM["hat"], "M", False),
                           (_SIN("blanket", "Emergency blanket", "Couverture de survie"), "M", False),
                           (_SIN("food", "500 extra calories", "500 calories de plus"), "M", False),
                           (_SIN("wag", "Wag bag", "Sac hygiénique (wag bag)"), "M", False),
                           (_SIN("longpants", "Light pants or tights", "Pantalon léger ou collant"), "R", False),
                           (_SIN("midlayer", "Insulating layer", "Couche isolante"), "R", False),
                           (_SIN("inreach", "SPOT or emergency beacon", "SPOT ou balise d'urgence"), "R", False),
                           (_SIN("headlamp2", "Second light", "Deuxième lampe"), "R", False),
                       ]], **_gdoc("1HbRW1yDNXnqX7JFrYoR7PQet5RK5a3wXBLAdrJP88PY")),
    # Québec. ultratrailsayam.com -> "Guide du coureur 2026" (PDF), "Matériel obligatoire" per distance (5 km left out)
    "ultra-trail-sayam": {
        "name": "Ultra-Trail Sayam", "short": "Sayam", "de": "de l'", "le": "l'",
        "where": _C("Val-Brillant (Matapédia), Québec", "Val-Brillant (Matapédia), Québec"),
        "when": _C("June 2027 (date to come; 2026: June 26–28)", "Juin 2027 (date à venir; 2026 : 26 au 28 juin)"),
        "dists": ["100", "50", "25", "15"], "default": "100", "cupless": True,
        "src": "https://cdn.shopify.com/s/files/1/0781/5774/2321/files/Guide_du_coureur_2026_8f36215b-4f31-42be-a353-9727fea44462.pdf",
        "read": _C("October 22, 2026 (2026 runner guide)", "22 octobre 2026 (guide du coureur 2026)"),
        "items": [(k, lv, t, sp) for (k, t), lv, sp in [
            (_SIN("headlamp", "Headlamp + spare batteries or power bank", "Lampe frontale + piles ou batterie de rechange"), "M   ", True),
            (_SIN("jacket", "Waterproof jacket", "Veste imperméable"), "M   ", True),
            (_SIN("water", "Water: 1.5 L on the 100 km, 1 L on the others", "Eau : 1,5 L au 100 km, 1 L aux autres",
                  "Three 500 ml soft flasks = 1.5 L.", "Trois flasques de 500 ml = 1,5 L."), "MMMM", False),
            (_SIN("blanket", "Survival blanket", "Couverture de survie"), "MMM ", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "MMM ", False),
            (_SIN("cap", "Buff or cap", "Buff ou casquette"), "MMMM", False),
            (_SIN("phone", "Charged cell phone", "Téléphone cellulaire chargé"), "MMMM", False),
            (_SIN("food", "Energy food", "Nourriture énergétique"), "MMMM", False),
            (_SIN("cup", "Your own cup", "Gobelet personnel", "No cups at aid stations.", "Aucun gobelet aux ravitos."), "MMMM", False),
            (_SIN("firstaid", "Basic first aid kit (gloves, compress, bandage…)", "Trousse de premiers soins de base (gants, compresse, bandage…)"), "MM  ", False),
        ]],
    },
    # lachutedudiable.ca/guide.html, "Matériel obligatoire" (2026 guide; the 1 km has none)
    "la-chute-du-diable": {
        "name": "La Chute du Diable", "short": "Chute du Diable", "de": "de la ", "le": "la ",
        "where": _C("Saint-Alexis-des-Monts (Mauricie), Québec", "Saint-Alexis-des-Monts (Mauricie), Québec"),
        "when": _C("September 2027 (date to come; 2026: Sept. 5)", "Septembre 2027 (date à venir; 2026 : 5 sept.)"),
        "dists": ["75", "50", "35", "22", "10"], "default": "75", "cupless": True,
        "src": "https://www.lachutedudiable.ca/guide.html",
        "read": _C("October 22, 2026 (2026 runner guide)", "22 octobre 2026 (guide des coureurs 2026)"),
        "items": [(k, lv, t, sp) for (k, t), lv, sp in [
            (_SIN("headlamp", "Headlamp (not your phone)", "Lampe frontale (pas votre cellulaire)",
                  "After 4 pm you can't leave the Lac en Croix aid station without one (random checks).",
                  "Après 16 h, pas de sortie du ravito du Lac en Croix sans lampe (vérifications aléatoires)."), "MMM  ", True),
            (_SIN("water", "1 L of liquid", "1 litre de liquide", "Water or another drink.", "Eau ou autre boisson."), "MMM  ", False),
            (_SIN("cup", "Something to drink from: bottle, flask, hydration pack or folding cup", "De quoi boire : bouteille, flasque, sac d'hydratation ou gobelet pliable",
                  "No cups at aid stations.", "Pas de gobelets aux ravitos."), "MMMMM", False),
            (_SIN("phone", "Charged cell phone", "Téléphone cellulaire chargé"), "MMM  ", False),
            (_SIN("whistle", "Whistle", "Sifflet"), "MMMMM", False),
            (_SIN("blanket", "Survival blanket", "Couverture de survie"), "MMMMM", False),
            (_SIN("poles", "Poles", "Bâtons", "Allowed on the 35, 50 and 75 km only (any distance at 70+).",
                  "Permis aux 35, 50 et 75 km seulement (toutes distances à 70 ans et plus)."), "AAA  ", False),
        ]],
    },
})

# Oct 23 (Bastien sent the guide: "this is for twisted forks"): Massif Running's Twisted Fork 2026 Runners Guide (Google Doc), "Gear
# Requirements/Weather", shown at check-in. Its change log says "Removed Ice carrying capacity from required gear" (May 27) but the 68K
# list still names it: L (ask the race), never M.
RACES["twisted-fork"] = {
    "name": "Twisted Fork", "short": "Twisted Fork", "de": "de la ", "le": "la ", "unit": "label", "side": "us", "cupless": True,
    "where": _C("Park City, Utah", "Park City, Utah"),
    "when": _C("Late May 2027 (date to come; 2026: May 30)", "Fin mai 2027 (date à venir; 2026 : 30 mai)"),
    "dists": ["68K", "30K", "15K"], "default": "68K",
    "read": _C("October 23, 2026 (2026 runners guide, updated May 27, 2026)", "23 octobre 2026 (guide 2026, mis à jour le 27 mai 2026)"),
    "items": [(k, lv, t, sp) for (k, t), lv, sp in [
        (_SIN("water", "Water: 2 L on the 68K, 1.5 L on the 30K and 15K", "Eau : 2 L au 68K, 1,5 L aux 30K et 15K",
              "Three 500 ml soft flasks = 1.5 L. 68K: 2 to 3 L leaving Jeremy Ranch the first time is strongly encouraged.",
              "Trois flasques de 500 ml = 1,5 L. 68K : de 2 à 3 L en quittant Jeremy Ranch la première fois, fortement conseillé."), "MMM", False),
        (_SIN("cup", "Bottle, flask or reusable cup", "Gourde, flasque ou gobelet réutilisable", "No cups for cold drinks at aid stations.",
              "Pas de verres pour les boissons froides aux ravitos."), "MMM", False),
        (_SIN("food", "600 calories or more of food", "Au moins 600 calories de nourriture"), "MMM", False),
        (_SIN("gps", "GPS device or phone with the course downloaded", "Appareil GPS ou téléphone avec le tracé téléchargé",
              "People sometimes remove course markings on these busy trails.", "Des gens enlèvent parfois le balisage sur ces sentiers achalandés."), "MMM", False),
        (_SIN("whistle", "Whistle", "Sifflet"), "M  ", False),
        (_SIN("cap", "A way to carry ice: ice bandana, sun sleeves or a hat with room for ice",
              "De quoi porter de la glace : bandana à glace, manchons solaires ou casquette qui en contient",
              "Strongly recommended on the 30K and 15K. The 68K list names it, but the guide's May 27 update says it was removed: ask the race.",
              "Fortement conseillé aux 30K et 15K. La liste du 68K le nomme, mais la mise à jour du 27 mai dit qu'il a été retiré : demandez à la course."), "LRR", False),
    ]],
    **_gdoc("1TTP2WVIHe9VGxwYtOJrBZM5_UspsdDklFuLI_Tn5wFk"),
}

# Oct 23 (Bastien sent "ENG-REGULATIONS-TORX-2026.pdf"; torxtrail.com answers robots with a Cloudflare challenge, so race_check can't
# reread it: `nocheck`, recheck by hand each spring). Article 14: "MANDATORY EQUIPMENT - 1" (carried the whole race; TOR450 adds a GPS
# navigator, route maps, altimeter + compass) and "MANDATORY EQUIPMENT - 2" (compulsory, may stay in the TORX bag; the Race Direction can
# require it) = kit "bag". Article 12: TOR450's GPS tracker is provided (EUR 100 deposit); TOR330's is an optional rental.
_TORX = "https://torxtrail.com/en/"
_TREAD = _C("October 23, 2026 (2026 regulations)", "23 octobre 2026 (règlement 2026)")
_T1 = [
    (_SIN("cup", "A cup or other container to drink at aid stations", "Un gobelet ou autre contenant pour boire aux ravitos"), "M", False),
    (_SIN("phone", "Mobile phone, always on with the ringer on", "Téléphone cellulaire, toujours allumé avec la sonnerie",
          "Save the race's emergency number, don't hide your number, start fully charged.",
          "Enregistrez le numéro d'urgence de la course, ne masquez pas votre numéro, partez avec la pile pleine."), "M", False),
    (_SIN("id", "ID or health insurance card", "Pièce d'identité ou carte d'assurance maladie",
          "Medical care in Italy isn't free: from outside Europe, carry your insurer's guarantee of payment letter.",
          "Les soins en Italie ne sont pas gratuits : hors Europe, apportez la lettre de garantie de paiement de votre assureur."), "M", False),
    (_SIN("blanket", "Two survival blankets", "Deux couvertures de survie"), "M", False),
    (_SIN("food", "Food supply", "Réserve de nourriture"), "M", False),
    (_SIN("water", "Water supply", "Réserve d'eau"), "M", False),
    (_SIN("headlamp", "Two working headlamps + spare batteries", "Deux lampes frontales fonctionnelles + piles de rechange"), "M", True),
]
_T450 = [
    (_SIN("gps", "Handheld GPS navigator with the course track", "GPS de poche avec le tracé du parcours",
          "A smartphone is accepted but not recommended; a smartwatch alone isn't enough.",
          "Un téléphone est accepté mais déconseillé; une montre seule ne suffit pas."), "M", False),
    (_SIN("map", "Route maps", "Cartes du parcours", "Downloadable from torxtrail.com.", "À télécharger sur torxtrail.com."), "M", False),
    (_SIN("alti", "Altimeter and compass", "Altimètre et boussole", "Phone apps are accepted.", "Les applis de téléphone sont acceptées."), "M", False),
    (_SIN("tracker", "GPS tracker", "Balise GPS", "Provided by the race (EUR 100 deposit, returned with the tracker).",
          "Fournie par la course (dépôt de 100 €, remis au retour de la balise)."), "P", False),
]
def _tbag(full):
    b = [
        (_SIN("a5", "Trail running shoes (category A5) or trekking shoes", "Chaussures de trail (catégorie A5) ou de randonnée", "For rough, uneven ground.", "Pour terrain accidenté."), "M", False),
        (_SIN("spikes", "Crampons with 8 mm spikes or more (front and heel)", "Crampons à pointes de 8 mm ou plus (avant et talon)"), "M", False),
        (_SIN("warmjacket", "Hooded thermal jacket for freezing temperatures", "Manteau thermique avec capuchon pour le gel",
              "Temperatures can drop several degrees below zero.", "Il peut faire plusieurs degrés sous zéro."), "M", False),
        (_SIN("jacket", "Hooded waterproof jacket, breathable, taped seams", "Manteau imperméable avec capuchon, respirant, coutures scellées"), "M", True),
        (_SIN("longpants", "Running leggings or pants", "Collant ou pantalon de course"), "M", False),
        (_SIN("pants", "Long waterproof over-trousers", "Surpantalon imperméable long"), "M", True),
        (_SIN("midlayer", "Warm layer: long-sleeved technical top and long trousers", "Couche chaude : haut technique à manches longues et pantalon long"), "M", False),
        (_SIN("tuque", "Hat that covers the ears", "Tuque qui couvre les oreilles"), "M", False),
        (_SIN("gloves2", "Warm, waterproof gloves", "Gants chauds et imperméables"), "M", False),
        (_SIN("spare", "Change of clothes", "Vêtements de rechange"), "M", False),
        (_SIN("whistle", "Whistle", "Sifflet"), "M", False),
        (_SIN("firstaid", "First aid kit for treating yourself", "Trousse de premiers soins pour vous soigner"), "M", False),
        (_SIN("battery", "Power bank for your phone and devices", "Batterie externe pour le téléphone et les appareils"), "M", False),
        (_SIN("knife", "Knife", "Couteau"), "M", False),
    ]
    if not full:    # already carried the whole race on the TOR450
        b[13:13] = [(_SIN("alti2", "Altimeter", "Altimètre"), "M", False),
                    (_SIN("gps2", "GPS device with the race route loaded", "Appareil GPS avec le tracé de la course"), "M", False)]
    return b
def _tor(name, short, dist, km, items):
    return {"name": name, "short": short, "de": "du ", "le": "le ", "unit": "label", "side": "it", "nocheck": True, "cupless": True,
            "where": _C("Courmayeur, Aosta Valley, Italy", "Courmayeur, Vallée d'Aoste, Italie"),
            "when": _C("September 2027 (dates to come)", "Septembre 2027 (dates à venir)"),
            "dists": [dist], "default": dist, "km": {dist: km}, "src": _TORX, "read": _TREAD,
            "kits": {"bag": [k for (k, _), _, _ in _tbag(dist == "TOR450")]},
            "items": [(k, lv, t, sp) for (k, t), lv, sp in items]}
RACES["tor-des-geants"] = _tor("Tor des Géants", "Courmayeur", "TOR330", 330, _T1 + _tbag(False))
RACES["tor-des-glaciers"] = _tor("Tor des Glaciers", "Courmayeur", "TOR450", 450, _T1 + _T450 + _tbag(True))

# UTMB Mont-Blanc (Oct 21, Bastien: "UTMB 160 the big race and all other distances in Chamonix"): the 2026 list, published as an
# image on montblanc.utmb.world (read Oct 21, 2026). One button per race; PTL left out (a team race with its own rules).
MB = ["UTMB", "TDS", "CCC", "OCC", "MCC", "ETC", "YCC"]
RACES["utmb-mont-blanc"] = {
    "name": "UTMB Mont-Blanc", "short": "Chamonix", "side": "fr", "unit": "label", "cupless": True,
    "where": {"en": "Chamonix, France", "fr": "Chamonix, France"},
    "when": {"en": "August 2027 (dates to come)", "fr": "Août 2027 (dates à venir)"},
    "km": {"UTMB": 177, "TDS": 151, "CCC": 101, "OCC": 61, "MCC": 39, "ETC": 15, "YCC": 15},
    "dists": MB, "default": "UTMB",
    "src": "https://montblanc.utmb.world/races-runners/runners/mandatory-equipment",
    "read": {"en": "October 21, 2026 (2026 list)", "fr": "21 octobre 2026 (liste 2026)"},
    "kits": {"bad": ["longpants", "jacket2", "midlayer2", "sun", "cap3", "gloves3", "warmjacket", "spare"], "hot": ["sun2", "cap2", "sunscreen"]},
    "items": [
        ("id", "MMMMMMM", {"en": ("ID: passport or ID card", ""), "fr": ("Pièce d'identité : passeport ou carte", "")}, False),
        ("phone", "MMMMMMM", {"en": ("Smartphone with the LiveTrail app", "With roaming for France, Italy and Switzerland. Keep it on: airplane mode isn't allowed."),
                              "fr": ("Téléphone avec l'appli LiveTrail", "Avec l'itinérance pour la France, l'Italie et la Suisse. Toujours allumé : le mode avion est interdit.")}, False),
        ("water", "MMMMMMM", {"en": ("Water: 1 litre or more", "1.5 L recommended on the UTMB, TDS and CCC. Sealed containers, no plastic bags."),
                              "fr": ("Eau : 1 litre ou plus", "1,5 L recommandé sur l'UTMB, la TDS et la CCC. Contenants étanches, pas de sacs de plastique.")}, False),
        ("cup", "MMMMMMM", {"en": ("Personal cup (150 ml or more)", "Bottles or flasks with a lid don't count."), "fr": ("Gobelet personnel (150 ml ou plus)", "Les bouteilles ou flasques avec bouchon ne comptent pas.")}, False),
        ("blanket", "MMMMMMM", {"en": ("Survival blanket (1.40 m × 2 m or more)", ""), "fr": ("Couverture de survie (1,40 m × 2 m ou plus)", "")}, False),
        ("whistle", "MMMMMMM", {"en": ("Whistle", "Many race vests have one on the chest strap: check yours."), "fr": ("Sifflet", "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre.")}, False),
        ("food", "MMMMMRR", {"en": ("Food reserve", "Recommended: about 800 kcal (2 gels + 2 bars)."), "fr": ("Réserve de nourriture", "Recommandé : environ 800 kcal (2 gels + 2 barres).")}, False),
        ("jacket", "MMMMM  ", {"en": ("Waterproof jacket with a hood", "Breathable membrane (20,000 mm recommended), sealed seams, the jacket's own hood. No non-waterproof panels."),
                               "fr": ("Manteau imperméable avec capuchon", "Membrane respirante (20 000 Schmerber recommandé), coutures scellées, capuchon d'origine. Aucun panneau non imperméable.")}, True),
        ("vest", "MMMMM  ", {"en": ("Running pack", "Worn the whole race; it carries the timing chip."), "fr": ("Sac de course", "Porté toute la course; il porte la puce de chronométrage.")}, False),
        ("headlamp", "MMMM   ", {"en": ("Headlamp + spare batteries", "200 lumens recommended. Phones and watches don't count. The OCC needs one."),
                                 "fr": ("Lampe frontale + piles de rechange", "200 lumens recommandés. Téléphones et montres ne comptent pas. L'OCC en demande une.")}, True),
        ("headlamp2", "MMM    ", {"en": ("Second headlamp", "UTMB, TDS, CCC: two working lamps, spare batteries for each (or a 5,000 mAh power bank). UTMB: one needs a forward red light."),
                                  "fr": ("2e lampe frontale", "UTMB, TDS, CCC : deux lampes, des piles pour chacune (ou une batterie externe de 5 000 mAh). UTMB : une doit avoir une lumière rouge vers l'avant.")}, False),
        ("bandage", "MMMMM  ", {"en": ("Self-adhesive elastic bandage (100 × 6 cm or more)", ""), "fr": ("Bandage élastique adhésif (100 × 6 cm ou plus)", "")}, False),
        ("cap", "MMMMM  ", {"en": ("Cap, bandana or neck gaiter for the sun", ""), "fr": ("Casquette, bandana ou cache-cou pour le soleil", "")}, False),
        ("pants", "MMMMM  ", {"en": ("Waterproof overpants", ""), "fr": ("Surpantalon imperméable", "")}, True),
        ("midlayer", "MMM    ", {"en": ("Warm long-sleeve second layer", "No cotton, 180 g or more in men's M (or a 110 g base layer + a water-repellent windproof jacket)."),
                                 "fr": ("Deuxième couche chaude à manches longues", "Pas de coton, 180 g ou plus en M homme (ou une couche de 110 g + un coupe-vent déperlant).")}, False),
        ("tuque", "MMM    ", {"en": ("Beanie or neck gaiter", ""), "fr": ("Tuque ou cache-cou", "")}, False),
        ("gloves2", "MMM    ", {"en": ("Warm, waterproof gloves", ""), "fr": ("Gants chauds et imperméables", "")}, True),
        ("poles", "RRRRRRR", {"en": ("Trail running poles", "If you start with them, carry them the whole race."), "fr": ("Bâtons de trail", "Si vous partez avec, portez-les toute la course.")}, False),
        ("battery", "RRRRRRR", {"en": ("Power bank", ""), "fr": ("Batterie externe", "")}, False),
        ("bowl", "RRRRRRR", {"en": ("Reusable bowl", "No disposable dishes at the aid stations."), "fr": ("Bol réutilisable", "Aucune vaisselle jetable aux ravitaillements.")}, False),
        # the additional list: any item can be called by the race, at the latest 24 h before the start
        ("longpants", "MMMMMMM", {"en": ("Long running tights or pants", "Down to the ankle, opaque, technical fabric. They don't replace the waterproof overpants."),
                                  "fr": ("Collant long ou pantalon de course", "Jusqu'à la cheville, opaque, tissu technique. Ne remplace pas le surpantalon imperméable.")}, False),
        ("jacket2", "MMMMMMM", {"en": ("Waterproof jacket with a hood", "For the ETC and YCC, when the race calls it."), "fr": ("Manteau imperméable avec capuchon", "Pour l'ETC et la YCC, quand la course l'annonce.")}, True),
        ("midlayer2", "MMMMMMM", {"en": ("Warm long-sleeve second layer", "For the races that don't already require it."), "fr": ("Deuxième couche chaude à manches longues", "Pour les courses qui ne l'exigent pas déjà.")}, False),
        ("sun", "MMMMMMM", {"en": ("Protective eyewear", "Photochromic sunglasses can count for both."), "fr": ("Lunettes de protection", "Des lunettes photochromiques peuvent compter pour les deux.")}, False),
        ("cap3", "MMMMMMM", {"en": ("A second neck gaiter", ""), "fr": ("Un deuxième cache-cou", "")}, False),
        ("gloves3", "MMMMMMM", {"en": ("Warm, waterproof gloves", "For the races that don't already require them."), "fr": ("Gants chauds et imperméables", "Pour les courses qui ne les exigent pas déjà.")}, True),
        ("warmjacket", "MMMMMMM", {"en": ("Third warm layer", "A softshell, down jacket or thick fleece."), "fr": ("Troisième couche chaude", "Softshell, doudoune ou laine polaire épaisse.")}, False),
        ("spare", "MMMMMMM", {"en": ("Spare warm clothing", ""), "fr": ("Vêtements chauds de rechange", "")}, False),
        ("sun2", "MMMMMMM", {"en": ("Sunglasses", ""), "fr": ("Lunettes de soleil", "")}, False),
        ("cap2", "MMMMMMM", {"en": ("Sahara cap (covers the head and neck)", ""), "fr": ("Casquette saharienne (couvre la tête et la nuque)", "")}, False),
        ("sunscreen", "MMMMMMM", {"en": ("Sunscreen, 15 ml or more", "In its original container. SPF 50 or higher recommended."), "fr": ("Crème solaire, 15 ml ou plus", "Dans son contenant d'origine. FPS 50 ou plus recommandé.")}, False),
    ],
}


# Oct 23 (Bastien: "you can expand to international races as well. all around the world"): UTMB World Series events abroad,
# each list read on the event's own mandatory gear page (read Oct 23, 2026). Shoes are the page's first line, so not repeated here.
_READ23 = _C("October 23, 2026", "23 octobre 2026")
def _intl(name, short, de, le, side, where, when, dists, src, items, kits=None):
    r = {"name": name, "short": short, "de": de, "le": le, "side": side, "unit": "label", "cupless": True,
         "where": where, "when": when, "dists": dists, "default": dists[0], "src": src, "read": _READ23,
         "items": [(k, lv, t, sp) for (k, t), lv, sp in items]}
    if kits:
        r["kits"] = kits
    return r
_WX = ("Weather item on the {d}: the race confirms a few days before.", "Selon la météo sur le {d} : la course confirme quelques jours avant.")
RACES.update({
    "lavaredo": _intl("Lavaredo Ultra Trail by UTMB", "Lavaredo", "du ", "le ", "it", _C("Cortina d'Ampezzo, Italy", "Cortina d'Ampezzo, Italie"),
        _C("June 23–27, 2027", "23 au 27 juin 2027"), ["120K", "80K", "50K", "20K", "10K"],
        "https://lavaredo.utmb.world/races-runners/info/mandatory-equipment", [
        (_SIN("vest", "Race pack for the mandatory gear", "Sac de course pour le matériel obligatoire"), "MMM  ", False),
        (_SIN("phone", "Phone, on, with the emergency numbers saved", "Téléphone allumé, numéros d'urgence enregistrés"), "MMMMM", False),
        (_SIN("jacket", "Waterproof jacket with a built-in hood", "Manteau imperméable avec capuchon intégré",
              "A Gore-Tex-type membrane, 10,000 mm or more (not asked on the 20K). The race's judges decide if yours passes.",
              "Membrane de type Gore-Tex, 10 000 mm ou plus (pas exigé sur le 20K). Les juges de la course décident si le vôtre passe."), "MMMM ", True),
        (_SIN("headlamp", "Headlamp + spare batteries (or two headlamps)", "Lampe frontale + piles de rechange (ou deux frontales)"), "MM   ", True),
        (_SIN("midlayer", "Long-sleeve top", "Chandail à manches longues", "Recommended on the 10K.", "Recommandé sur le 10K."), "MMM R", False),
        (_SIN("longpants", "Long pants or tights", "Pantalon long ou collant"), "MMM  ", False),
        (_SIN("cap", "Hat or bandana", "Chapeau ou bandana"), "MMM  ", False),
        (_SIN("gloves2", "Warm, waterproof gloves", "Gants chauds et imperméables"), "MMM  ", False),
        (_SIN("water", "Water: 1 litre or more", "Eau : 1 litre ou plus", "½ litre on the 20K; ½ litre recommended on the 10K (no aid station on the way).",
              "½ litre sur le 20K; ½ litre recommandé sur le 10K (aucun ravito en chemin)."), "MMMMR", False),
        (_SIN("cup", "Cup, 15 cl or more", "Gobelet de 15 cl ou plus", "No cups at the aid stations.", "Aucun verre aux ravitos."), "MMMM ", False),
        (_SIN("blanket", "Survival blanket (2 m × 1.40 m or more)", "Couverture de survie (2 m × 1,40 m ou plus)"), "MMMMR", False),
        (_SIN("whistle", "Whistle", "Sifflet"), "MMMMR", False),
        (_SIN("food", "Energy bars or solid food", "Barres énergétiques ou nourriture solide"), "MMM  ", False),
        (_SIN("spoon", "Your own cutlery and container", "Vos ustensiles et un contenant",
              "No disposable dishes at the aid stations or life bases, for hot or cold food.", "Aucune vaisselle jetable aux ravitos ni aux bases de vie."), "MMM  ", False),
        (_SIN("cash", "€20 or more in cash", "20 € ou plus en argent comptant", "To buy food in the mountain huts if needed.", "Pour acheter à manger dans les refuges au besoin."), "MMM  ", False),
        (_SIN("bandage", "Elastic bandage", "Bandage élastique"), "MMM  ", False),
        (_SIN("pants", "Waterproof pants", "Pantalon imperméable"), "RRR  ", True),
        (_SIN("warmjacket", "Third layer (fleece or puffy) for very cold weather", "Troisième couche (polaire ou doudoune) par grand froid"), "RRR  ", False),
        (_SIN("sun", "Sunglasses", "Lunettes de soleil"), "RRR  ", False),
        (_SIN("sunscreen", "Sunscreen", "Crème solaire"), "RRR  ", False),
        (_SIN("salts", "Mineral salts", "Sels minéraux"), "RRR  ", False),
        (_SIN("poles", "Trekking poles", "Bâtons de marche", "Allowed on the 120K, 80K and 50K. Not allowed on the 20K.",
              "Permis sur le 120K, le 80K et le 50K. Interdits sur le 20K."), "AAA  ", False),
    ]),
    "zugspitz": _intl("Zugspitz Ultratrail by UTMB", "Zugspitz", "du ", "le ", "de", _C("Garmisch-Partenkirchen, Germany", "Garmisch-Partenkirchen, Allemagne"),
        _C("June 17–20, 2027", "17 au 20 juin 2027"), ["ZUT100", "Ultratrail", "Ehrwald", "Leutasch", "Mittenwald", "Garmisch", "Grainau"],
        "https://zugspitz.utmb.world/runners/mandatory-gear", [
        (_SIN("vest", "Running pack or running belt", "Sac ou ceinture de course"), "MMMMMMM", False),
        (_SIN("jacket", "Waterproof jacket, taped seams, 10,000 mm or more", "Manteau imperméable, coutures scellées, 10 000 mm ou plus"), "MMMMMMM", True),
        (_SIN("midlayer", "Warm long-sleeve top (or a shirt + arm warmers)", "Haut chaud à manches longues (ou chandail + manchons)",
              "The rule: no skin may show.", "La règle : aucune peau visible."), "MMMM M ", False),
        (_SIN("longpants", "Running pants or leg warmers", "Pantalon de course ou jambières", "No skin may show.", "Aucune peau visible."), "MMMMMM ", False),
        (_SIN("gloves", "Gloves", "Gants"), "MMMMMM ", False),
        (_SIN("tuque", "Beanie or Buff that covers head and ears", "Tuque ou Buff qui couvre la tête et les oreilles"), "MMMMMM ", False),
        (_SIN("headlamp", "Headlamp + spare batteries (or a spare lamp)", "Lampe frontale + piles de rechange (ou une 2e lampe)",
              "ZUT100: two working headlamps. Grainau: recommended if you'll be out more than 3 hours.",
              "ZUT100 : deux frontales fonctionnelles. Grainau : recommandée si vous prévoyez plus de 3 heures."), "MMMM  R", True),
        (_SIN("water", "Sealable bottles: 1.5 litres or more", "Gourdes fermées : 1,5 litre ou plus", "1 litre on the Mittenwald, Garmisch and Grainau trails.",
              "1 litre sur Mittenwald, Garmisch et Grainau."), "MMMMMMM", False),
        (_SIN("cup", "Cup for drinks at the aid stations", "Gobelet pour boire aux ravitos"), "MMMMMMM", False),
        (_SIN("firstaid", "Emergency kit: a 10 × 10 cm compress, 2 bandage packs, 2 pairs of sterile gloves", "Trousse d'urgence : une compresse 10 × 10 cm, 2 bandages, 2 paires de gants stériles"), "MMMMMMM", False),
        (_SIN("whistle", "Whistle", "Sifflet"), "MMMMMMM", False),
        (_SIN("blanket", "Rescue blanket", "Couverture de survie"), "MMMMMMM", False),
        (_SIN("gps", "GPS watch with the route saved (or the route in a phone map app)", "Montre GPS avec le tracé (ou le tracé dans une appli de cartes)"), "MMMMMMM", False),
        (_SIN("phone", "Phone with the Alpine Medics number saved", "Téléphone avec le numéro des secours alpins enregistré",
              "+49 8324 933 550. It must also make calls from Austria.", "+49 8324 933 550. Il doit aussi pouvoir appeler depuis l'Autriche."), "MMMMMMM", False),
        (_SIN("helmet", "Helmet", "Casque", "Leave it in your Biberwier drop bag: worn on a 2 km section after it, handed back at Pestkapelle. Any helmet works.",
              "Dans votre sac de dépôt à Biberwier : porté sur 2 km après ce ravito, rendu à Pestkapelle. N'importe quel casque."), "M      ", False),
        (_SIN("poles", "Poles", "Bâtons", "Recommended.", "Recommandés."), "RRRRRRR", False),
    ]),
    "eiger": _intl("Eiger Ultra Trail by UTMB", "Eiger", "de l'", "l'", "ch", _C("Grindelwald, Switzerland", "Grindelwald, Suisse"),
        _C("July 14–18, 2027", "14 au 18 juillet 2027"), ["E250", "E101", "E51", "E35", "E16"],
        "https://eiger.utmb.world/races-runners/runners/mandatory-equipment", [
        (_SIN("vest", "Running pack for the mandatory gear", "Sac de course pour le matériel obligatoire"), "MMMM ", False),
        (_SIN("phone", "Smartphone, on the whole race", "Téléphone intelligent, allumé toute la course",
              "Roaming for Switzerland, the LiveRun app, the race's safety numbers saved. Airplane mode isn't allowed.",
              "Itinérance pour la Suisse, appli LiveRun, numéros de sécurité de la course enregistrés. Mode avion interdit."), "MMMMM", False),
        (_SIN("cup", "Collapsible cup (15 cl or more)", "Gobelet pliable (15 cl ou plus)", "Bottles or flasks with a lid don't count. E250: tableware and cutlery too.",
              "Les bouteilles et flasques avec bouchon ne comptent pas. E250 : vaisselle et ustensiles aussi."), "MMMMM", False),
        (_SIN("water", "Water: 1 litre or more", "Eau : 1 litre ou plus", "E250: 1.5 L. E16: 0.5 L.", "E250 : 1,5 L. E16 : 0,5 L."), "MMMMM", False),
        (_SIN("headlamp", "Two headlamps + spare batteries", "Deux lampes frontales + piles de rechange",
              "200 lumens or more recommended for the main one. A power bank can replace the spare battery.",
              "200 lumens ou plus recommandés pour la principale. Une batterie externe peut remplacer les piles."), "MM   ", True),
        (_SIN("jacket", "Waterproof jacket with a hood, taped seams", "Manteau imperméable avec capuchon, coutures scellées",
              "20,000 mm recommended (E250: 10,000 mm or more). The hood is built in or attached by the maker's system.",
              "20 000 mm recommandés (E250 : 10 000 mm ou plus). Capuchon intégré ou attaché par le système du fabricant."), "MMMM ", True),
        (_SIN("midlayer", "Warm long-sleeve top (180 g or more, no cotton)", "Haut chaud à manches longues (180 g ou plus, pas de coton)",
              "Or a lighter long-sleeve (110 g+) + a windproof jacket. A t-shirt + arm warmers don't count.",
              "Ou un manches longues plus léger (110 g+) + un coupe-vent. Un t-shirt + manchons ne comptent pas."), "MM   ", False),
        (_SIN("longpants", "Long pants, or tights that cover the legs fully", "Pantalon long, ou collant qui couvre toute la jambe"), "MMMM ", False),
        (_SIN("cap", "Cap, bandana or Buff", "Casquette, bandana ou Buff"), "MMMM ", False),
        (_SIN("sun", "Sunglasses", "Lunettes de soleil"), "MMMM ", False),
        (_SIN("blanket", "Survival blanket (1.40 m × 2 m or more)", "Couverture de survie (1,40 m × 2 m ou plus)"), "MMMM ", False),
        (_SIN("whistle", "Whistle", "Sifflet"), "MMMMM", False),
        (_SIN("bandage", "Self-adhesive elastic bandage (100 × 6 cm or more)", "Bandage élastique adhésif (100 × 6 cm ou plus)"), "MMMM ", False),
        (_SIN("food", "Food reserve", "Réserve de nourriture", "About 800 kcal recommended (2 gels + 2 bars).", "Environ 800 kcal recommandés (2 gels + 2 barres)."), "MMMM ", False),
        (_SIN("pants", "Waterproof overpants", "Surpantalon imperméable", "E101: the cold kit.", "E101 : le kit froid."), "MM   ", True),
        (_SIN("warmjacket", "Insulated jacket (down or PrimaLoft)", "Manteau isolé (duvet ou PrimaLoft)", "E101: the cold kit.", "E101 : le kit froid."), "MM   ", False),
        (_SIN("gloves", "Gloves", "Gants"), "M    ", False),
        (_SIN("spare", "Spare t-shirt", "T-shirt de rechange"), "M    ", False),
        (_SIN("liner", "Silk sleeping bag liner", "Sac à viande en soie", "For the overnight stops at the life bases.", "Pour dormir aux bases de vie."), "M    ", False),
        (_SIN("reflect", "Reflective band", "Bande réfléchissante", "Worn from 9 pm. A reflector on the pack or clothes counts.",
              "Portée dès 21 h. Un réflecteur sur le sac ou les vêtements compte."), "M    ", False),
        (_SIN("gps", "GPS device with the route (one per team)", "Appareil GPS avec le tracé (un par équipe)", "A phone works; a GPS watch alone doesn't.",
              "Un téléphone fonctionne; une montre GPS seule, non."), "M    ", False),
        (_SIN("battery", "Power bank + phone charger (per team)", "Batterie externe + chargeur (par équipe)"), "M    ", False),
        (_SIN("firstaid", "First aid kit (per team)", "Trousse de premiers soins (par équipe)",
              "Elastic bandage 200 × 4 cm, 2 sterile compresses, 2 gloves, 5 alcohol wipes, plasters.",
              "Bandage élastique 200 × 4 cm, 2 compresses stériles, 2 gants, 5 lingettes d'alcool, pansements."), "M    ", False),
        (_SIN("cash", "Swiss francs in cash", "Francs suisses en argent comptant", "Not every hut takes cards.", "Les refuges ne prennent pas tous les cartes."), "M    ", False),
        (_SIN("tracker", "GPS tracker", "Balise GPS", "Provided by the race.", "Fournie par la course."), "P    ", False),
    ]),
    "tarawera": _intl("Tarawera Ultramarathon by UTMB", "Tarawera", "du ", "le ", "nz", _C("Rotorua, New Zealand", "Rotorua, Nouvelle-Zélande"),
        _C("February 13–14, 2027", "13 et 14 février 2027"), ["TMiler", "T102", "T50", "T21", "T14"],
        "https://tarawera.utmb.world/runners/mandatory-gear", [
        (_SIN("midlayer", "Long-sleeve thermal top (polypropylene or wool)", "Haut thermique à manches longues (polypropylène ou laine)",
              "No cotton, compression or Coolmax tops. " + _WX[0].format(d="T102, T50 and T21"), "Pas de coton, de compression ni de Coolmax. " + _WX[1].format(d="T102, le T50 et le T21")), "MMMMR", False),
        (_SIN("jacket", "Waterproof, breathable jacket with a hood", "Manteau imperméable et respirant avec capuchon",
              "Fully taped seams. " + _WX[0].format(d="T102, T50 and T21"), "Coutures entièrement scellées. " + _WX[1].format(d="T102, le T50 et le T21")), "MMMMR", True),
        (_SIN("tuque", "Beanie, balaclava or Buff", "Tuque, cagoule ou Buff", _WX[0].format(d="T102, T50 and T21"), _WX[1].format(d="T102, le T50 et le T21")), "MMMMR", False),
        (_SIN("longpants", "Long thermal pants (polypropylene or wool)", "Pantalon thermique long (polypropylène ou laine)", _WX[0].format(d="T102, T50 and T21"), _WX[1].format(d="T102, le T50 et le T21")), "MMMMR", False),
        (_SIN("gloves", "Full-finger light thermal gloves", "Gants thermiques légers à doigts complets", _WX[0].format(d="T102, T50 and T21"), _WX[1].format(d="T102, le T50 et le T21")), "MMMMR", False),
        (_SIN("headlamp", "Headlamp", "Lampe frontale"), "MMM  ", True),
        (_SIN("headlamp2", "Spare batteries, a second headlamp or a USB power bank", "Piles de rechange, 2e frontale ou batterie USB"), "MMM  ", False),
        (_SIN("phone", "Phone that can call in New Zealand, fully charged", "Téléphone qui peut appeler en Nouvelle-Zélande, chargé"), "MMMRR", False),
        (_SIN("water", "Bottle, collapsible cup or hydration vest", "Gourde, gobelet pliable ou veste d'hydratation", "A cupless race: no cups at the aid stations.",
              "Course sans verres : aucun verre aux ravitos."), "MMMRR", False),
        (_SIN("bivy", "Emergency survival bag (not a blanket)", "Sac de survie d'urgence (pas une couverture)",
              "Sealed except the top, big enough to climb into; a single-use foil bag must be new.",
              "Fermé sauf en haut, assez grand pour y entrer; un sac d'aluminium à usage unique doit être neuf."), "MMMM ", False),
        (_SIN("hivis", "High-visibility safety vest (AS/NZS 4602, day/night)", "Dossard haute visibilité (norme AS/NZS 4602, jour/nuit)",
              "Worn on Tarawera Road. " + _WX[0].format(d="T102"), "Porté sur Tarawera Road. " + _WX[1].format(d="T102")), "MM   ", False),
        (_SIN("bandage", "Self-adhesive bandage (40 mm × 2 m or more)", "Bandage auto-adhésif (40 mm × 2 m ou plus)"), "MRRRR", False),
        (_SIN("drybag", "Light dry sack or zip-lock bags", "Sac étanche léger ou sacs à glissière", "To keep your gear dry.", "Pour garder le matériel au sec."), "MMMMR", False),
    ]),
    "ultra-trail-australia": _intl("Ultra-Trail Australia by UTMB", "UTA", "de l'", "l'", "au", _C("Katoomba, Blue Mountains, Australia", "Katoomba, Montagnes Bleues, Australie"),
        _C("May 13–16, 2027", "13 au 16 mai 2027"), ["UTAMiler", "UTA100", "UTA50", "UTA22", "UTA11"],
        "https://uta.utmb.world/runners/mandatory-gear", [
        (_SIN("midlayer", "Long-sleeve thermal top (polypropylene or wool)", "Haut thermique à manches longues (polypropylène ou laine)",
              "No cotton, compression or Coolmax tops. " + _WX[0].format(d="UTA22 and UTA11"), "Pas de coton, de compression ni de Coolmax. " + _WX[1].format(d="UTA22 et le UTA11")), "MMMMM", False),
        (_SIN("jacket", "Waterproof, breathable jacket with a hood", "Manteau imperméable et respirant avec capuchon",
              "Fully taped seams. " + _WX[0].format(d="UTA22 and UTA11"), "Coutures entièrement scellées. " + _WX[1].format(d="UTA22 et le UTA11")), "MMMMM", True),
        (_SIN("tuque", "Beanie, balaclava or Buff", "Tuque, cagoule ou Buff"), "MMMMM", False),
        (_SIN("phone", "Phone, fully charged, with a working SIM", "Téléphone chargé avec une carte SIM qui fonctionne"), "MMMMM", False),
        (_SIN("whistle", "Whistle", "Sifflet"), "MMMMM", False),
        (_SIN("blanket", "Space blanket or light bivvy sack", "Couverture de survie ou sac bivouac léger"), "MMMMM", False),
        (_SIN("bandage", "Compression bandage (7.5 cm × 2.3 m or more)", "Bandage de compression (7,5 cm × 2,3 m ou plus)"), "MMMMM", False),
        (_SIN("water", "Bottles or bladder for 2 litres of water", "Gourdes ou réservoir pour 2 litres d'eau", "1 litre on the UTA11. A cupless race.",
              "1 litre sur le UTA11. Course sans verres."), "MMMMM", False),
        (_SIN("food", "2 food bars or portions", "2 barres ou portions de nourriture", "Leave every checkpoint with 2. Gels count.",
              "Quittez chaque point de contrôle avec 2. Les gels comptent."), "MMMMM", False),
        (_SIN("trash", "Zip-lock bag for your rubbish", "Sac à glissière pour vos déchets"), "MMMMM", False),
        (_SIN("drybag", "Light dry sack or zip-lock bags", "Sac étanche léger ou sacs à glissière", "To keep your gear dry. " + _WX[0].format(d="UTA22 and UTA11"),
              "Pour garder le matériel au sec. " + _WX[1].format(d="UTA22 et le UTA11")), "MMMMM", False),
        (_SIN("hivis", "High-visibility safety vest (AS/NZS 4602, day/night)", "Dossard haute visibilité (norme AS/NZS 4602, jour/nuit)",
              "Worn at night, 8 pm to 6 am.", "Porté la nuit, de 20 h à 6 h."), "MMM  ", False),
        (_SIN("headlamp", "Headlamp", "Lampe frontale"), "MMM  ", True),
        (_SIN("headlamp2", "Small backup light", "Petite lampe de secours"), "MM   ", False),
        (_SIN("longpants", "Long thermal pants (polypropylene or wool)", "Pantalon thermique long (polypropylène ou laine)"), "MM   ", False),
        (_SIN("gloves", "Full-finger light thermal gloves", "Gants thermiques légers à doigts complets"), "MM   ", False),
        (_SIN("pants", "Long waterproof pants", "Pantalon imperméable long"), "MM   ", True),
        (_SIN("midlayer2", "Long-sleeve fleece top (100-weight or more)", "Polaire à manches longues (100 ou plus)"), "MM   ", False),
    ], kits={"bad": ["pants", "midlayer2"]}),
    "mozart-100": _intl("mozart 100 by UTMB", "mozart", "du ", "le ", "at", _C("Salzburg, Austria", "Salzbourg, Autriche"),
        _C("June 5, 2027", "5 juin 2027"), ["100", "Ultra", "Marathon", "Half"],
        "https://mozart.utmb.world/races-runners/runners/equipment", [
        (_SIN("vest", "Running pack for the mandatory gear", "Sac de course pour le matériel obligatoire", "A running belt is allowed on the Marathon and Half.",
              "Une ceinture de course est permise sur le Marathon et le Demi."), "MMMM", False),
        (_SIN("phone", "Smartphone with the LiveTrail app", "Téléphone avec l'appli LiveTrail",
              "Roaming for Austria, emergency numbers saved, always on: airplane mode isn't allowed.",
              "Itinérance pour l'Autriche, numéros d'urgence enregistrés, toujours allumé : mode avion interdit."), "MMMM", False),
        (_SIN("water", "Water: 0.5 litre or more, in sealed containers", "Eau : 0,5 litre ou plus, contenants fermés", "No plastic bags.", "Pas de sacs de plastique."), "MMMM", False),
        (_SIN("headlamp", "Two headlamps, or one + a spare battery", "Deux frontales, ou une + une pile de rechange",
              "200 lumens recommended. Phones and watches don't count.", "200 lumens recommandés. Téléphones et montres ne comptent pas."), "MM  ", True),
        (_SIN("jacket", "Waterproof, breathable jacket with a hood, taped seams", "Manteau imperméable et respirant avec capuchon, coutures scellées",
              "20,000 mm recommended.", "20 000 mm recommandés."), "MMMM", True),
        (_SIN("whistle", "Whistle", "Sifflet"), "MMMM", False),
        (_SIN("blanket", "Survival blanket (1.40 m × 2 m or more)", "Couverture de survie (1,40 m × 2 m ou plus)"), "MMM ", False),
        (_SIN("bandage", "Self-adhesive elastic bandage (100 × 6 cm or more)", "Bandage élastique adhésif (100 × 6 cm ou plus)"), "MMM ", False),
        (_SIN("food", "Food reserve", "Réserve de nourriture", "About 400 kcal recommended (2 gels or 2 bars).", "Environ 400 kcal recommandés (2 gels ou 2 barres)."), "MM  ", False),
        (_SIN("cap", "Cap, bandana or neck gaiter for the sun", "Casquette, bandana ou cache-cou pour le soleil"), "MMM ", False),
        (_SIN("gloves", "Warm gloves", "Gants chauds"), "MM  ", False),
        (_SIN("sun", "Sunglasses", "Lunettes de soleil", "Photochromic lenses work for sun and bad weather.", "Des verres photochromiques servent au soleil comme au mauvais temps."), "MM  ", False),
        (_SIN("sunscreen", "Sunscreen, 15 ml or more", "Crème solaire, 15 ml ou plus", "In its original container. SPF 50 or higher recommended.",
              "Dans son contenant d'origine. FPS 50 ou plus recommandé."), "MM  ", False),
        (_SIN("longpants", "Long pants or tights (knees can show)", "Pantalon long ou collant (genoux à découvert permis)"), "MM  ", False),
        (_SIN("midlayer", "Warm long-sleeve second layer (no cotton)", "Deuxième couche chaude à manches longues (pas de coton)",
              "Or a long-sleeve base layer + a windproof jacket.", "Ou un haut de base à manches longues + un coupe-vent."), "MM  ", False),
        (_SIN("warmjacket", "Third layer (fleece or puffy)", "Troisième couche (polaire ou doudoune)"), "MM  ", False),
        (_SIN("tuque", "Beanie (or neck gaiter)", "Tuque (ou cache-cou)"), "MM  ", False),
        (_SIN("pants", "Waterproof overpants", "Surpantalon imperméable"), "MM  ", True),
    ], kits={"hot": ["sun", "sunscreen"], "bad": ["longpants", "midlayer", "warmjacket", "tuque", "pants"]}),
    "julian-alps": _intl("Julian Alps Trail Run by UTMB", "Julian Alps", "du ", "le ", "si", _C("Kranjska Gora, Slovenia", "Kranjska Gora, Slovénie"),
        _C("September 17–19, 2027", "17 au 19 septembre 2027"), ["120K", "80K", "50K", "25K", "15K", "10K"],
        "https://julianalps.utmb.world/races-runners/runners/equipment", [
        (_SIN("vest", "Running pack for the mandatory gear", "Sac de course pour le matériel obligatoire"), "MMMM  ", False),
        (_SIN("phone", "Smartphone with the LiveTrail app", "Téléphone avec l'appli LiveTrail",
              "Roaming for Slovenia, the race's safety numbers saved, always on: airplane mode isn't allowed.",
              "Itinérance pour la Slovénie, numéros de sécurité de la course enregistrés, toujours allumé : mode avion interdit."), "MMMMMM", False),
        (_SIN("cup", "Collapsible cup (15 cl or more)", "Gobelet pliable (15 cl ou plus)", "Bottles or flasks with a lid don't count.",
              "Les bouteilles et flasques avec bouchon ne comptent pas."), "MMMMMM", False),
        (_SIN("water", "Water: 1 litre or more", "Eau : 1 litre ou plus", "0.5 L on the 25K.", "0,5 L sur le 25K."), "MMMM  ", False),
        (_SIN("headlamp", "Two headlamps + spare batteries", "Deux lampes frontales + piles de rechange",
              "50K: one headlamp + spare batteries. 200 lumens or more recommended for the main one.",
              "50K : une frontale + piles de rechange. 200 lumens ou plus recommandés pour la principale."), "MMM   ", True),
        (_SIN("whistle", "Whistle", "Sifflet"), "MMMMM ", False),
        (_SIN("blanket", "Survival blanket or bag (1.40 m × 2 m or more)", "Couverture ou sac de survie (1,40 m × 2 m ou plus)"), "MMMMM ", False),
        (_SIN("food", "Food reserve", "Réserve de nourriture", "About 800 kcal recommended (2 gels + 2 bars).", "Environ 800 kcal recommandés (2 gels + 2 barres)."), "MMM   ", False),
        (_SIN("jacket", "Waterproof jacket with a hood, taped seams", "Manteau imperméable avec capuchon, coutures scellées",
              "10,000 mm or more recommended; hood built in or attached by the maker.", "10 000 mm ou plus recommandés; capuchon intégré ou attaché par le fabricant."), "MMM   ", True),
        (_SIN("bandage", "Self-adhesive elastic bandage (100 × 6 cm or more)", "Bandage élastique adhésif (100 × 6 cm ou plus)"), "MMM   ", False),
        (_SIN("longpants", "Long pants, or tights that cover the legs fully", "Pantalon long, ou collant qui couvre toute la jambe"), "MMM   ", False),
        (_SIN("cap", "Cap, bandana or neck gaiter", "Casquette, bandana ou cache-cou"), "MMM   ", False),
        (_SIN("midlayer", "Warm long-sleeve top (180 g or more, no cotton)", "Haut chaud à manches longues (180 g ou plus, pas de coton)",
              "Or a lighter long-sleeve (110 g+) + a windproof jacket.", "Ou un manches longues plus léger (110 g+) + un coupe-vent."), "MM    ", False),
        (_SIN("gloves", "Warm gloves", "Gants chauds"), "MM    ", False),
        (_SIN("tracker", "GPS tracker", "Balise GPS", "Provided by the race.", "Fournie par la course."), "PP    ", False),
        (_SIN("jacket2", "Waterproof jacket with a hood", "Manteau imperméable avec capuchon"), "   MMM", True),
        (_SIN("cap2", "Cap or bandana", "Casquette ou bandana"), "   MMM", False),
        (_SIN("gloves2", "Warm, waterproof gloves", "Gants chauds et imperméables"), "MMMMMM", False),
        (_SIN("wind", "Windproof jacket (water-repellent)", "Coupe-vent (déperlant)"), "MMM   ", False),
        (_SIN("tuque", "Hat", "Tuque"), "MMM   ", False),
        (_SIN("pants", "Waterproof overpants", "Surpantalon imperméable"), "MMM   ", True),
        (_SIN("warmjacket", "Third warm layer (under the waterproof jacket)", "Troisième couche chaude (sous le manteau imperméable)"), "MMM   ", False),
        (_SIN("midlayer2", "Warm long-sleeve top (180 g or more, no cotton)", "Haut chaud à manches longues (180 g ou plus, pas de coton)"), "  M   ", False),
        (_SIN("gaiters", "Light running gaiters", "Guêtres de course légères"), "MMM   ", False),
    ], kits={"bad": ["jacket2", "cap2", "gloves2", "wind", "tuque", "pants", "warmjacket", "midlayer2", "gaiters"]}),
})

# Oct 28 (growth chat, Bastien OK'd; each list re-read on the race's own site Oct 28, 2026)
_r = lambda rows: [(k, lv, tx, sp) for (k, tx), lv, sp in rows]
RACES.update({
    # Trail Whisperer's "MANDATORY CHECKLIST for 50K and 27K events" (PDF made Aug 6, 2026, linked from the race page): gear check
    # before check-in; the 13K has no gear check. Cup-less event; poles allowed.
    "frosty-mountain-ultra": {
        "name": "Frosty Mountain Ultra", "short": "Frosty", "de": "du ", "le": "le ", "unit": "label", "cupless": True,
        "where": {"en": "Manning Park, BC", "fr": "Parc Manning, C.-B."},
        "when": {"en": "September (2027 date to come; 2026: Sept. 12)", "fr": "Septembre (date 2027 à venir; 2026 : 12 sept.)"},
        "dists": ["50K", "27K", "13K"], "default": "50K",
        "src": "https://trailwhispererbc.ca/r-frosty-mtn-ultra/",
        "read": {"en": "October 28, 2026 (2026 checklist)", "fr": "28 octobre 2026 (liste 2026)"},
        "items": _r([
            (_SIN("headlamp", "Headlamp in working condition", "Lampe frontale fonctionnelle"), "MM ", True),
            (_SIN("blanket", "Emergency survival blanket", "Couverture de survie"), "MM ", False),
            (_SIN("whistle", "Whistle", "Sifflet", "Many race vests have one on the chest strap: check yours.",
                  "Plusieurs vestes de course en ont un sur la sangle de poitrine : vérifiez la vôtre."), "MM ", False),
            (_SIN("food", "400 calories of extra food", "400 calories de nourriture en plus", "Not to be eaten except in an emergency.",
                  "À ne manger qu'en cas d'urgence."), "MM ", False),
            (_SIN("jacket", "Waterproof jacket", "Manteau imperméable"), "MM ", True),
            (_SIN("midlayer", "Insulating long-sleeve layer", "Couche isolante à manches longues"), "MM ", False),
            (_SIN("gloves", "Gloves", "Gants"), "MM ", False),
            (_SIN("cap", "Hat", "Chapeau"), "RR ", False),
            (_SIN("water", "Bottles, soft flasks or a bladder: 2 L of fluid", "Gourdes, flasques ou réservoir : 2 L de liquide",
                  "Four 500 ml soft flasks = 2 L.", "Quatre flasques de 500 ml = 2 L."), "RR ", False),
            (_SIN("cup", "Collapsible cup", "Gobelet pliable", "A cup-less event: for drinks and food at every aid station.",
                  "Course sans verres : pour boire et manger à chaque ravito."), "RRR", False),
            (_SIN("headlamp2", "Spare batteries for your lights", "Piles de rechange pour vos lampes"), "RR ", False),
            (_SIN("gps", "GPS or phone with the race route loaded", "GPS ou téléphone avec le tracé de la course", "Charged for the whole race.",
                  "Chargé pour toute la course."), "RR ", False),
            (_SIN("longpants", "Long running pants or waterproof pants", "Pantalon de course long ou imperméable"), "RR ", False),
            (_SIN("filter", "Filter bottle or water treatment tablets", "Gourde filtrante ou pastilles de purification", "If you plan to drink from streams.",
                  "Si vous comptez boire aux ruisseaux."), "RR ", False),
            (_SIN("socks", "Extra pair of socks", "Paire de bas de rechange"), "RR ", False),
            (_SIN("firstaid", "Compact first-aid and foot-care kit + a compression bandage", "Trousse de premiers soins et de soins des pieds + bandage compressif"), "RR ", False),
            (_SIN("sunscreen", "Sunscreen and lip balm", "Crème solaire et baume à lèvres"), "RR ", False),
            (_SIN("chafe", "Anti-chafe (Vaseline or similar)", "Anti-frottement (vaseline ou autre)"), "RR ", False),
            (_SIN("bugs", "Bug spray", "Chasse-moustiques"), "RR ", False),
            (_SIN("bear", "Bear spray or an air horn", "Chasse-ours en aérosol ou corne de brume", "If you are concerned about bears.",
                  "Si les ours vous inquiètent."), "RR ", False),
            (_SIN("dropbag", "Warm clothes for the finish, in a waterproof drop bag", "Vêtements chauds pour l'arrivée, dans un sac imperméable"), "RRR", False),
        ]),
    },
    # ironlegs.ca/100km, /50mile, /partners (60 km), /20km (25 km night race), /relay "Mandatory Gear" + "Suggested Gear" (read Oct 28, 2026).
    # Relay: bear spray is "suggested" on its page but mandatory in the 2026 Racer Guide -> L (ask the race). Every aid station is cupless.
    "iron-legs": {
        "name": "Iron Legs Mountain Races", "short": "Iron Legs", "de": "de l'", "le": "l'", "unit": "label", "cupless": True,
        "where": {"en": "Kananaskis (Elbow Valley), AB", "fr": "Kananaskis (vallée de l'Elbow), Alb."},
        "when": {"en": "August 7, 2027", "fr": "7 août 2027"},
        "dists": ["100K", "50M", "60K", "25K", "RELAY"], "default": "100K",
        "labels": {"25K": {"en": "25 km night race", "fr": "25 km de nuit"}, "RELAY": {"en": "50 mile relay", "fr": "Relais 50 milles"}},
        "src": "https://www.ironlegs.ca/100km",
        "read": {"en": "October 28, 2026", "fr": "28 octobre 2026"},
        "items": _r([
            (_SIN("headlamp", "Headlamp", "Lampe frontale", "Required after Powderface (aid station 4); the night race carries it from the start.",
                  "Exigée après Powderface (ravito 4); dès le départ pour la course de nuit."), "MMMMM", True),
            (_SIN("jacket", "Wind and water resistant jacket", "Manteau coupe-vent et déperlant", "Needed for the mountain ascents (relay: after aid station 4).",
                  "Pour les montées en montagne (relais : après le ravito 4)."), "MMMRM", True),
            (_SIN("water", "Hydration pack or bottles: 1.5 L or more", "Sac d'hydratation ou gourdes : 1,5 L ou plus", "1 L on the 25 km night race.",
                  "1 L pour le 25 km de nuit."), "MMMMM", False),
            (_SIN("bear", "Bear spray", "Chasse-ours en aérosol"), "MMMML", False),
            (_SIN("bib", "Race bib", "Dossard", "Handed out by the race.", "Remis par la course."), "PPPPP", False),
            (_SIN("cup", "Reusable cup", "Gobelet réutilisable", "The aid stations are cupless.", "Les ravitos n'ont pas de verres."), "RRRRR", False),
            (_SIN("longpants", "Tights or pants", "Collant ou pantalon"), "RRRRR", False),
            (_SIN("food", "Food", "Nourriture"), "RRRRR", False),
            (_SIN("gloves", "Gloves", "Gants"), "RRRRR", False),
            (_SIN("cap", "Hat", "Chapeau"), "RRRRR", False),
            (_SIN("watch", "Watch", "Montre"), "RRRRR", False),
            (_SIN("sun", "Sunglasses", "Lunettes de soleil"), "RRR R", False),
            (_SIN("sunscreen", "Sunscreen", "Crème solaire"), "RRR R", False),
            (_SIN("headlamp2", "Spare batteries or a spare headlamp", "Piles de rechange ou 2e lampe frontale"), "RRRRR", False),
        ]),
    },
})

S = {
    "en": {
        "dir": "races", "title": "{name} mandatory gear list ({short} {dists})",
        "desc": "The {name} mandatory gear list for the {dists}, item by item, with today's best prices on each in your size at Canadian stores.",
        "h1": "{name} mandatory gear list", "sub": "{short} {dists} · {where} · {when}",
        "dist": "Your distance", "km": "{d} km",
        "M": "Mandatory", "R": "Recommended", "A": "Allowed", "P": "Provided", "L": "Ask the race",
        "lNote": "The race lists these as \"a mix of mandatory and recommended\" without saying which. Ask the race before you count on skipping one.", "aProv": "The race provides: {items}.",
        "have": "I have it", "progress": "You have {h} of {n} mandatory items. Tick what you already own.", "progressAll": "You have every mandatory item. See you at the start.",
        "deals": "On sale now", "dealsSize": "On sale now in your size", "noDeals": "None in stock in your size today. We check every morning.", "few": "Only {n} in {fit} {size} today. We check every morning.",
        "notSold": "The stores we check don't sell this.", "spec": "Check the spec before you buy.",
        "more": "See more on sale →", "moreN": "See all {n}", "shH": "Trail running shoes", "shTag": "Your pick", "shPh": "What do you race in?", "shSize": "Size", "shGone": "Not in stock in size {s} today. We'll tell you when it's back.", "shPickSize": "Pick your size too.", "shPickFit": "Pick Men's or Women's above first.", "shFrom": "{p} in size {s} today", "shPage": "Every size & store", "shNone": "Not in our trail shoe list. Try the brand name.", "shRm": "Remove", "watch": "Watch", "watchOn": "Watching", "watchL": "Watch the price", "wMember": "Watching. We'll email you when it drops in your size.", "wNew": "Watching, on this phone. Add your email and we'll tell you when it drops.", "wPending": "Watching. Confirm your email (check your inbox) to get the drop emails.", "wAdd": "Add my email", "wOff": "Removed from your watchlist.", "sizeH": "Your size", "sizeTxt": "Pick it once to see deals that fit you.",
        "men": "Men's", "women": "Women's", "change": "Change", "off": "off",
        "kit_bad": "Bad-weather kit", "kit_hot": "Hot-weather kit", "kitWhen": "Only if the race calls it, usually a few days before the start.",
        "kit_bag": "Compulsory, can stay in your TORX bag", "kitWhen_bag": "You may leave these in your TORX bag at the Life Bases, but the race can make you carry or wear them when conditions get tough (bad weather, snow, ice). Pack for the time between Life Bases, the altitude and the forecast.",
        "byOpen": "Different size in shorts, socks or gloves?", "by": {"tops": "Tops", "bottoms": "Shorts & tights", "socks": "Socks", "gloves": "Gloves"},
        "src": "From the race's official list (last updated by the race {date}). Rules can change: check the {link} before race day.",
        "srcLink": "official list", "srcRead": "From the race's official list (as published when we read it, {date}). Rules can change: check the {link} before race day.", "notAff": "The Gear Fox isn't affiliated with the race.",
        "boxH": "Get gear deals in your size every Friday until race day", "boxTxt": "Free. One email on Friday mornings with the best deals in your sizes. Unsubscribe in one tap.",
        "boxBtn": "Send me the deals", "faqH": "Quick answers",
        "qList": "What is the mandatory gear for the {short} {d}?", "aList": "{items}.",
        "qJacket": "Is a windbreaker enough for the {name}?", "aJacket": "No. The race asks for a jacket with an attached hood and a waterproof, breathable membrane (on the {dists}). Windbreakers aren't accepted.",
        "qCup": "Do the {name} aid stations have cups?", "aCup": "No. The aid stations have no cups: bring your own reusable cup.",
        "kbBest": "From {p} · {n} picks", "kbBestN": "Not in your size today", "aisle": "Race gear lists", "money": T["en"]["money"], "otherSide": "Shopping in the US? This list with US stores →",
    },
    "fr": {
        "dir": "courses", "title": "Matériel obligatoire {de}{name} ({short} {dists})",
        "desc": "Le matériel obligatoire {de}{name} pour le {dists}, article par article, avec les meilleurs prix du jour dans votre taille dans les boutiques canadiennes.",
        "h1": "Matériel obligatoire {de}{name}", "sub": "{short} {dists} · {where} · {when}",
        "dist": "Votre distance", "km": "{d} km",
        "M": "Obligatoire", "R": "Recommandé", "A": "Permis", "P": "Fourni", "L": "À confirmer",
        "lNote": "La course présente ces articles comme « un mélange d'obligatoire et de recommandé » sans préciser lesquels. Vérifiez auprès de la course avant d'en laisser un.", "aProv": "La course fournit : {items}.",
        "have": "Je l'ai", "progress": "Vous avez {h} des {n} articles obligatoires. Cochez ce que vous avez déjà.", "progressAll": "Vous avez tout le matériel obligatoire. On se voit au départ.",
        "deals": "En solde maintenant", "dealsSize": "En solde dans votre taille", "noDeals": "Rien en stock dans votre taille aujourd'hui. On vérifie chaque matin.", "few": "Seulement {n} en {size} {fit} aujourd'hui. On vérifie chaque matin.",
        "notSold": "Les boutiques que nous suivons n'en vendent pas.", "spec": "Vérifiez les caractéristiques avant d'acheter.",
        "more": "Voir plus d'aubaines →", "moreN": "Voir les {n}", "shH": "Chaussures de course en sentier", "shTag": "Votre choix", "shPh": "Vos chaussures de course ?", "shSize": "Pointure", "shGone": "Pas en stock en pointure {s} aujourd'hui. On vous avertit dès son retour.", "shPickSize": "Choisissez aussi votre pointure.", "shPickFit": "Choisissez d'abord Homme ou Femme plus haut.", "shFrom": "{p} en pointure {s} aujourd'hui", "shPage": "Toutes les pointures et boutiques", "shNone": "Pas dans notre liste de chaussures de sentier. Essayez le nom de la marque.", "shRm": "Retirer", "watch": "Suivre", "watchOn": "Suivi", "watchL": "Suivre le prix", "wMember": "Suivi. On vous écrit quand il baisse dans votre taille.", "wNew": "Suivi, sur ce téléphone. Ajoutez votre courriel et on vous avertira quand il baisse.", "wPending": "Suivi. Confirmez votre courriel (voyez votre boîte de réception) pour recevoir les alertes.", "wAdd": "Ajouter mon courriel", "wOff": "Retiré de vos favoris.", "sizeH": "Votre taille", "sizeTxt": "Choisissez-la une fois pour voir les aubaines à votre taille.",
        "men": "Homme", "women": "Femme", "change": "Modifier", "off": "de rabais",
        "kit_bad": "Kit mauvais temps", "kit_hot": "Kit chaleur", "kitWhen": "Seulement si la course l'annonce, habituellement quelques jours avant le départ.",
        "kit_bag": "Obligatoire, peut rester dans votre sac TORX", "kitWhen_bag": "Vous pouvez les laisser dans votre sac TORX aux bases de vie, mais la course peut vous obliger à les porter ou les transporter quand les conditions se corsent (mauvais temps, neige, glace). Prévoyez selon le temps entre les bases de vie, l'altitude et la météo.",
        "byOpen": "Une autre taille en shorts, bas ou gants ?", "by": {"tops": "Hauts", "bottoms": "Shorts et collants", "socks": "Bas", "gloves": "Gants"},
        "src": "Selon la liste officielle de la course (mise à jour par la course le {date}). Les règles peuvent changer : vérifiez la {link} avant la course.",
        "srcLink": "liste officielle", "srcRead": "Selon la liste officielle de la course (telle que publiée quand nous l'avons lue, le {date}). Les règles peuvent changer : vérifiez la {link} avant la course.", "notAff": "The Gear Fox n'est pas affilié à la course.",
        "boxH": "Les aubaines de matériel dans votre taille, chaque vendredi jusqu'à la course", "boxTxt": "Gratuit. Un courriel le vendredi matin avec les meilleures aubaines dans vos tailles. Désabonnement en un clic.",
        "boxBtn": "Envoyez-moi les aubaines", "faqH": "Réponses rapides",
        "qList": "Quel est le matériel obligatoire du {short} {d}?", "aList": "{items}.",
        "qJacket": "Un coupe-vent suffit-il pour {le}{name}?", "aJacket": "Non. La course demande un manteau avec capuchon attaché et une membrane imperméable et respirante (sur le {dists}). Les coupe-vent ne sont pas acceptés.",
        "qCup": "Y a-t-il des verres aux ravitaillements {de}{name}?", "aCup": "Non. Les ravitaillements n'ont pas de verres : apportez votre gobelet réutilisable.",
        "kbBest": "Dès {p} · {n} choix", "kbBestN": "Rien dans votre taille aujourd'hui", "aisle": "Listes de matériel de course", "money": T["fr"]["money"], "otherSide": "Vous magasinez aux États-Unis ? Cette liste avec les boutiques américaines →",
    },
}

S["us"] = dict(S["en"], dir="us/races", desc="The {name} mandatory gear list for the {dists}, item by item, with today's best prices on each in your size at US stores.",
               otherSide="Shopping in Canada? This list with Canadian stores →")

# Oct 27: races whose whole list is suggested (Sinister Sports: "no mandatory gear" but the bib and chip it hands out)
SUG = {
    "en": {"title": "{name} gear list: what the race suggests ({short} {dists})",
           "desc": "The gear the {name} suggests for the {dists}, item by item (none of it required), with today's best prices on each in your size at Canadian stores.",
           "h1": "{name} suggested gear list", "R": "Suggested by the race",
           "sNote": "The race suggests this gear; none of it is required. The only must-haves are what the race hands out (marked Provided).",
           "qList": "Is any gear mandatory for the {short} {d}?", "aList": "No. The race suggests: {items}."},
    "fr": {"title": "Matériel suggéré {de}{name} ({short} {dists})",
           "desc": "Le matériel que suggère {le}{name} pour le {dists}, article par article (rien d'obligatoire), avec les meilleurs prix du jour dans votre taille dans les boutiques canadiennes.",
           "h1": "Matériel suggéré {de}{name}", "R": "Suggéré par la course",
           "sNote": "La course suggère ce matériel; rien n'y est obligatoire. Seul ce que la course remet (marqué Fourni) est exigé.",
           "qList": "Y a-t-il du matériel obligatoire pour {le}{short} {d}?", "aList": "Non. La course suggère : {items}."},
}
SUG["us"] = dict(SUG["en"], desc="The gear the {name} suggests for the {dists}, item by item (none of it required), with today's best prices on each in your size at US stores.")


def twins(head, slug, race):
    """Oct 21 (Bastien: "people travel to races ... people need their gear locally even if the race is abroad"): every race has a
    Canadian (EN/FR) and a US page, same list, local stores. Tell search engines they're the same page for three audiences."""
    BASE = "https://thegearfox.com"
    alt = (f'<link rel="alternate" hreflang="en-CA" href="{BASE}/races/{slug}/">\n<link rel="alternate" hreflang="fr-CA" href="{BASE}/courses/{slug}/">\n'
           f'<link rel="alternate" hreflang="en-US" href="{BASE}/us/races/{slug}/">\n'
           f'<link rel="alternate" hreflang="x-default" href="{BASE}{"/us" if race.get("side") == "us" else ""}/races/{slug}/">')
    return re.sub(r'(<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n?)+', alt + "\n", head, count=1)


def dlab(race, d, L):
    """A distance as people say it: "125 km" for Québec races, "100K" / "100 mi" for races named that way (UTMB, Fat Dog)."""
    if d in race.get("labels", {}):   # Oct 27: "Half marathon", "24 hours", "Vertical K"
        return race["labels"][d]["fr" if L == "fr" else "en"]
    if race.get("unit") != "label":
        return S[L]["km"].format(d=d)
    return f'{d[:-1]} {"milles" if L == "fr" else "mi"}' if d.endswith("M") else d


def dlabs(race, L, ds=None):
    ds = ds or race["dists"]
    return "/".join(dlab(race, d, L) for d in ds) if race.get("unit") == "label" else "/".join(ds) + " km"


def tl(L):
    return US if L == "us" else T[L]


CSS = """
p.sub{overflow-wrap:anywhere}   /* Oct 23: only the subtitle (".gl.sub" is the kit list: it squeezed the pick names) */
.dists{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 12px}
.dists button{font:700 15px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:8px 12px;min-height:44px;cursor:pointer;white-space:nowrap}
.dists button[aria-pressed="true"]{background:var(--ink);color:var(--card);border-color:var(--ink)}
.lbl{font:600 13px var(--body);color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin:14px 0 0}
.prog{font-weight:600;margin:4px 0 10px}
.gl{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:10px}
.gi{background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:12px 14px}
.gi[hidden]{display:none}
.gi .hd{display:flex;align-items:center;gap:10px}
.gi .hd h3{flex:1;min-width:0;margin:0;font:700 19px/1.2 var(--display)}
.gi .note{margin:4px 0 0 34px;font-size:14px;color:var(--muted)}
.gi .lv{flex:none;font:700 11px var(--body);text-transform:uppercase;letter-spacing:.05em;border-radius:6px;padding:3px 7px;margin-top:2px}
.lv.M{background:var(--hivis);color:var(--hivis-ink)}.lv.R{background:var(--mist);color:var(--ink);border:1px solid var(--line)}.lv.A,.lv.P{color:var(--muted);border:1px solid var(--line)}.lv.L{background:var(--mist);color:var(--ink);border:1px dashed var(--ink)}.lnote{font-size:14px;color:var(--muted);margin:0 0 10px}
.gi .have{flex:none;width:24px;height:24px;margin:0;accent-color:var(--hivis);cursor:pointer}
.gi.got{opacity:.6}.gi.got .dl,.gi.got .ft,.gi.got .note,.gi.got .none{display:none}
.gi.got h3{text-decoration:line-through}
.dl{display:grid;gap:6px;margin:8px 0 0;padding:0;list-style:none}
.dl a.dg{display:flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:10px;padding:6px 10px 6px 6px;color:var(--ink);text-decoration:none}
.dl img{width:56px;height:56px;object-fit:contain;background:#fff;border-radius:8px;flex:none}
.dl .nm{flex:1;min-width:0;font-size:14px;line-height:1.25}.dl .nm b{display:block;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.dl .nm small{display:block;color:var(--muted);font-size:12px}
.dl .pr{text-align:right;white-space:nowrap}.dl .pr b{display:block;font:800 18px var(--display)}.dl .pr s{color:var(--muted);font-size:12px}
.dlh{font:600 13px var(--body);color:var(--muted);margin:10px 0 0}
.ft{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;margin:4px 0 0}.ft:empty{display:none}.spec{font-size:13px;color:var(--muted)}
.more{display:inline-block;margin-top:6px;font:600 14px var(--body)}
.none{font-size:14px;color:var(--muted);margin:6px 0 0}.few{font-size:13px;color:var(--muted)}
.faq details{border-bottom:1px solid var(--line);padding:10px 0}.faq summary{font:700 16px/1.3 var(--body);cursor:pointer}.faq details p{margin:6px 0 0}
.rsize{background:var(--card);border:1.5px solid var(--hivis);border-radius:12px;padding:12px 14px;margin:10px 0}
.rsize p{margin:0 0 8px;font-size:15px}.rsize .row{display:flex;gap:6px;flex-wrap:wrap}
.rsize button{font:600 15px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:7px 13px;min-height:40px;cursor:pointer}
.rsize button[aria-pressed="true"]{background:var(--ink);color:var(--card);border-color:var(--ink)}
.rsize .mine{border:0;padding:0;margin:0;background:none}
.oside{margin:-4px 0 10px;font-size:14px;background:none;padding:0;color:var(--ink)}.side~.oside{display:none}.srcb{font-size:14px;color:var(--muted);margin:16px 0 0}
.kit{order:20;background:var(--card);border:1.5px dashed var(--line);border-radius:14px;padding:10px 14px}.kit[hidden]{display:none}
.kit summary{font:700 18px/1.3 var(--display);cursor:pointer;min-height:32px;display:flex;align-items:center}.kit .kitwhen{margin:4px 0 10px}
.gl.sub{gap:8px}.gl.sub .gi{border-color:var(--line)}
.kit .dl .wl{display:none}.kit .dl .wt{font-size:18px;padding:0 9px}.kit .dl .pr s{display:block}.kit .dl img{width:46px;height:46px}.kit .dl a.dg{gap:8px}   /* Oct 23: the fold is narrower (inner border): small-phone layout so names stay readable */
.gi.shoe{border-color:var(--hivis)}.gi.shoe .shi{flex:none;width:24px;display:flex;justify-content:center;color:var(--muted)}.lv.Y{background:var(--ink);color:var(--card)}
.shrow{display:flex;gap:8px;margin-top:10px}.shrow select{flex:none;width:104px;font:600 16px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:0 8px}
.gi.shoe input{flex:1;min-width:0;font:400 16px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:11px 13px}
.sugg,.mine2{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:4px}.sugg:empty,.mine2:empty{display:none}
.sugg button{width:100%;text-align:left;font:500 15px var(--body);color:var(--ink);background:var(--mist);border:0;border-radius:10px;padding:10px 12px;cursor:pointer}
.sugg .no{font-size:14px;color:var(--muted);padding:4px 2px}
.mine2 li{display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:rgba(242,106,27,.12);border-radius:10px;padding:8px 10px;font-size:15px}
.mine2 b{flex:1 1 auto;min-width:0}.mine2 small{color:var(--muted)}.mine2 a{font:600 14px var(--body)}
.mine2 button{font:600 14px var(--body);color:var(--muted);background:none;border:0;padding:4px;cursor:pointer;text-decoration:underline}
.dl li{display:flex;align-items:stretch;gap:6px}.gi .dl li:nth-child(n+4){display:none}.gi.open .dl li{display:flex}
.dl .dg{flex:1;min-width:0}.dl .wt{flex:none;display:flex;align-items:center;font:600 13px var(--body);color:var(--moss);background:var(--card);text-decoration:none;border:1px solid var(--line);border-radius:10px;padding:0 10px;white-space:nowrap;cursor:pointer}
.dl .wt[aria-pressed="true"]{background:var(--hivis);color:var(--hivis-ink);border-color:var(--hivis)}
.wtoast{position:fixed;left:12px;right:12px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:60;max-width:520px;margin:0 auto;background:var(--card);color:var(--ink);border:1.5px solid var(--line);border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.2);padding:12px 14px;font-size:15px}
.wtoast button{font:700 15px var(--body);background:var(--hivis);color:var(--hivis-ink);border:0;border-radius:999px;padding:8px 14px;margin-top:8px;cursor:pointer}
.wtoast[hidden]{display:none}
@media (max-width:400px){.dl .wl{display:none}.dl .wt{font-size:18px;padding:0 9px}.dl .nm{font-size:13px;overflow-wrap:anywhere}.dl .pr s{display:block}.dl img{width:46px;height:46px}.dl a.dg{gap:8px}}
.mored{font:600 14px var(--body);color:var(--moss);background:none;border:0;padding:4px 0;cursor:pointer;text-decoration:underline}
.gi.open .mored{display:none}.gi.got .mored{display:none}
.gi.mini{padding:9px 14px}.gi.mini .hd h3{font:600 16px/1.3 var(--body)}.gi.mini .note{font-size:13px;margin:2px 0 0 34px}
.rsize.set .row,.rsize.set>p{display:none}.rsize .cur{display:none;margin:0;font-size:16px}.rsize.set .cur{display:block}
.rsize .bym{margin:8px 0 0}.rsize .bym button{border:0;background:none;padding:0;min-height:0;color:var(--moss);text-decoration:underline;font:600 14px var(--body);cursor:pointer}
.rsize .byrow{margin:8px 0 0}.rsize .byrow b{display:block;font:600 13px var(--body);margin:0 0 4px}.rsize.set .bym,.rsize.set .byrows{display:none}
.rsize .cur button{border:0;background:none;padding:0 4px;min-height:0;color:var(--moss);text-decoration:underline;font:600 15px var(--body)}
"""


BAD = re.compile(r"seat ?mast|seat ?post|\bbiogel\b", re.I)   # bike parts still in today's data (scrape.py NOT_RUNNING drops them from Oct 21)


def pool(items, kind, stores):
    """Race gear for one line of the list, full price too (people watch it for a drop): trail gear first, then how many stores
    carry it (the best popularity signal we have), then a sale."""
    k = KINDS[kbase(kind)]
    need, good = re.compile(k["need"], re.I), re.compile(k["good"], re.I)
    xx = re.compile(k["x"], re.I) if k.get("x") else None
    out = []
    for d in items:
        if d.get("ca") is False or not d.get("img") or d["g"] not in k["g"]:
            continue
        n = d["n"]
        if (k.get("t") and d.get("t") not in k["t"]) or not need.search(n) or (xx and xx.search(n)) or BAD.search(n):
            continue
        b = d["b"].lower()
        kb = re.sub(r"\d+$", "", kind)
        if not (kb not in BRANDS or b in BRANDS[kb] or (b in MAYBE and (kb in ("water", "cup", "food") or RUN.search(n)))):
            continue
        fit = bool(good.search(n))
        sz = [e for e in d["sz"] if e[1]]
        if not sz or (d["g"] != "nutrition" and max(e[1] for e in sz) > 2.5 * min(e[1] for e in sz)):
            continue                                       # sizes 2.5x apart in price: another product's sizes mixed in (Decathlon, Oct 20)
        best = min(sz, key=lambda e: e[1])
        if best[1] < k.get("min", 0):
            continue
        reg = max(best[3] or best[1], best[1]) if len(best) > 3 else best[1]
        pct = round(100 * (1 - best[1] / reg)) if reg > best[1] * 1.01 else 0
        u = size_url(d, best)
        nst = len({host(x) for x in d.get("of") or [] if x})
        out.append({"b": d["b"], "n": n, "img": d["img"], "sx": d.get("sx") or [], "g": d["g"],
                    "k": f'{d["b"]}|{n}|{d["g"]}|{1 if d.get("w") else 0}'.lower(),          # the site's itemKey(): /?watch=<k>
                    "s": [[e[0], e[1], max(e[3] or e[1], e[1]) if len(e) > 3 else e[1], size_url(d, e)] for e in sz],
                    "st": stores.get(host(u), [host(u)])[0], "h": host(u),
                    "_score": 30 * fit + min(nst, 5) * 6 + pct * 0.3 + min(len(sz), 6)})
    out.sort(key=lambda r: -r["_score"])
    for r in out:
        del r["_score"]
    # Oct 20 (Bastien: "always give 10 options"): past the top POOL, keep whatever a fit + size still needs to reach 10
    # (XS and 2XL ran short: men's 2XL gloves had 1)
    keep, need = out[:POOL], {}
    def buckets(r):
        fits = r["sx"] or ["men", "women"]
        if r["g"] not in SIZED_G:
            return [(f, "") for f in fits]
        return [(f, norm(e[0])) for f in fits for e in r["s"]]
    for r in keep:
        for b in set(buckets(r)):
            need[b] = need.get(b, 0) + 1
    for r in out[POOL:]:
        bs = set(buckets(r))
        if any(need.get(b, 0) < SHOW + 2 and (b[1] in CORE or b[1] == "") for b in bs):
            keep.append(r)
            for b in bs:
                need[b] = need.get(b, 0) + 1
    return keep


SIZED_G = {"tops", "bottoms", "gloves", "headwear", "socks"}
CORE = {"XS", "S", "M", "L", "XL", "2XL", "OS"}
ALIAS = {"XXS": "2XS", "XXL": "2XL", "X-SMALL": "XS", "SMALL": "S", "MEDIUM": "M", "LARGE": "L", "X-LARGE": "XL", "EXTRA LARGE": "XL", "XX-SMALL": "2XS"}


def norm(z):
    """Same as the page script's norm(); "S/M" counts for both S and M there, so it's a bucket of its own here (rare)."""
    z = str(z).upper().strip()
    return ALIAS.get(z, z)


def spread(p):
    """The best deals, one per brand first (11 tuques from one store's own brand look like a store ad)."""
    seen, first, rest = set(), [], []
    for r in p:
        (rest if r["b"].lower() in seen else first).append(r)
        seen.add(r["b"].lower())
    return first + rest


def picks(p, n=SHOW):
    """10 choices: one per brand first; at least MIN_SALE on sale when there are that many, one of them in the first 3 shown."""
    sale = lambda r: any(e[2] > e[1] * 1.01 for e in r["s"])
    top = spread(p)[:n]
    more = [r for r in spread(p)[n:] if sale(r)]
    while sum(map(sale, top)) < MIN_SALE and more:
        i = max(i for i, r in enumerate(top) if not sale(r)) if any(not sale(r) for r in top) else None
        if i is None:
            break
        top[i] = more.pop(0)
    if top and not any(map(sale, top[:FIRST])) and any(map(sale, top)):
        j = next(i for i, r in enumerate(top) if sale(r))
        top.insert(FIRST - 1, top.pop(j))
    return top


def fit_sizes(d, f):
    """Regular-width sizes of a shoe in one fit -> today's price: "10" on a one-gender shoe (or a unisex one, men's sizes),
    "M:10"/"W:11" from unisex labels; wide/narrow left out (Oct 20: the price shown is the one in the visitor's size)."""
    out = {}
    one = d.get("sx") or []
    for e in d["sz"]:
        m = re.match(r"^(?:([MW]):)?(\d+(?:\.5)?)(~[WN])?$", str(e[0]))
        if not m or m.group(3) or not e[1]:
            continue
        g, n = m.group(1), m.group(2)
        if g:
            ok = (g == "M") == (f == "men")
        else:
            ok = (len(one) == 1 and one[0] == f) or (len(one) != 1 and f == "men")
        if ok and (n not in out or e[1] < out[n]):
            out[n] = e[1]
    return out


def trail_shoes(items, pages):
    """Oct 20 (Bastien: "ask what they run in so we start tracking their favourite shoe"): every trail shoe model we carry in
    Canada, one entry per model with the men's and women's item (its watch key, today's lowest price, a store link) and its
    shoe page when there is one. Most-carried first (what people type most is what most stores sell)."""
    by = {}
    for d in items:
        if d["g"] != "shoes" or d.get("t") != "trail" or d.get("ca") is False or not d["sz"]:
            continue
        m = re.sub(r"\s*(-\s*Large|\(Large\)|-\s*Wide)\s*$", "", base_model(d["n"]), flags=re.I)   # Québec stores' wide = same model
        e = by.setdefault((d["b"], m), {"b": d["b"], "m": m, "n": 0})
        nst = len({host(x) for x in d.get("of") or [] if x})
        e["n"] = max(e["n"], nst)
        lo = min(z[1] for z in d["sz"] if z[1])
        for f in (d.get("sx") or ["men", "women"]):
            old = e.get(f)
            if d.get("w") and old:                 # the regular width is the one to watch
                continue
            if not old or (not d.get("w") and old.get("w")) or nst > old["c"]:
                e[f] = {"k": f'{d["b"]}|{d["n"]}|{d["g"]}|{1 if d.get("w") else 0}'.lower(), "p": lo, "u": (d.get("of") or [""])[0], "n": d["n"],
                        "c": nst, "w": bool(d.get("w")), "z": fit_sizes(d, f)}
    out = []
    for e in sorted(by.values(), key=lambda e: -e["n"]):
        sl = slugify(e["b"] + " " + e["m"])
        pg = (pages or {}).get(sl)
        if pg and pg.get("to"):
            sl, pg = pg["to"], pages.get(pg["to"])
        r = {"b": e["b"], "m": e["m"], "s": sl if pg else ""}
        for f in ("men", "women"):
            if e.get(f):
                r[f] = [e[f]["k"], e[f]["p"], e[f]["u"], e[f]["n"], e[f]["z"]]
        out.append(r)
    return out


def money(L, v):
    return S[L]["money"](v)


def nm(L, n):
    """The French pages say the fit in French, like the site."""
    return re.sub(r"Women[’']s\b", "Femme", re.sub(r"Men[’']s\b", "Homme", re.sub(r"\bUnisex\b", "Unisexe", n))) if L == "fr" else n


def price_html(L, e):
    sale = e[2] > e[1] * 1.01
    return (f'<b>{money(L, e[1])}</b>' + (f'<s>{money(L, e[2])}</s> <span class="off">−{round(100 * (1 - e[1] / e[2]))}%</span>' if sale else ""))


def deal_html(L, r):
    e = min(r["s"], key=lambda e: e[1])
    return (f'<li><a class="dg" href="{esc(e[3])}" data-store="{esc(r["h"])}" target="_blank" rel="noopener"><img src="{esc(r["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer">'
            f'<span class="nm"><b>{esc(r["b"])}</b>{esc(nm(L, r["n"]))}<small>{esc(r["st"])}</small></span>'
            f'<span class="pr">{price_html(L, e)}</span></a>'
            f'<button type="button" class="wt" data-k="{esc(r["k"])}" data-p="{e[1]}" data-u="{esc(e[3])}" aria-pressed="false" aria-label="{esc(S[L]["watchL"])}: {esc(r["b"])} {esc(r["n"])}">'
            f'<span class="hh">♡</span><span class="wl"> {S[L]["watch"]}</span></button></li>')


def page(slug, race, L, items, stores, pages=None, fx=1.0):
    s, Tl = (dict(S[L], **SUG[L]) if race.get("suggested") else S[L]), tl(L)
    fmt = dict(name=race["name"], short=race["short"], dists=dlabs(race, L), where=race["where"][L if L != "us" else "en"],
               when=race["when"][L if L != "us" else "en"], de=race.get("de", "de l'"), le=race.get("le", "l'"))
    if L == "us":   # English, US stores; the "Canadian stores" switch goes to the same race with Canadian stores
        head = page_head(US, s["title"].format(**fmt), s["desc"].format(**fmt), f"/us/races/{slug}/", "", f"<style>{CSS}</style>").replace('class="sw" href="/shoes/"', f'class="sw" href="/races/{slug}/"')
    else:
        head = page_head(T[L], s["title"].format(**fmt), s["desc"].format(**fmt), f"/races/{slug}/", f"/courses/{slug}/", f"<style>{CSS}</style>")
    head = twins(head, slug, race)
    pools, rows, shown, kits = {}, [], set(), {}
    for kind, lv, txt, spec in race["items"]:
        title, note = txt["en" if L == "us" else L]
        sold = kbase(kind) in KINDS
        p = pool(items, kind, stores) if sold else []
        if sold:
            pools[kind] = p
        lvs = "".join(f' data-l{d}="{lv[i].strip()}"' for i, d in enumerate(race["dists"]))
        first = lv[race["dists"].index(race["default"])].strip()
        top = picks([r for r in p if not (kind == "headlamp2" and r["n"] in shown)])
        if kind == "headlamp":
            shown = {r["n"] for r in top[:FIRST]}
        if sold:   # one deal shows, the others behind "N more deals"; the tick sits by the name (Oct 20: 7,800 px on a phone was too long)
            deals = (f'<ul class="dl"{"" if top else " hidden"}>{"".join(deal_html(L, r) for r in top)}</ul>'
                     f'<p class="none"{" hidden" if top else ""}>{s["noDeals"]}</p>'
                     f'<p class="ft"><button type="button" class="mored" data-n="{s["moreN"]}" {"" if len(top) > FIRST else " hidden"}>{s["moreN"].format(n=len(top))}</button>'
                     + (f'<span class="spec">{s["spec"]}</span>' if spec else "") + "</p>")
        else:
            deals = ""
        kit = next((k for k, ks in (race.get("kits") or {}).items() if kind in ks), "")
        (kits.setdefault(kit, []) if kit else rows).append(
                    f'<li class="gi{"" if sold else " mini"}" data-k="{kind}"{" data-kit=" + chr(34) + kit + chr(34) if kit else ""}{lvs}{"" if first else " hidden"}><div class="hd">'
                    f'<input type="checkbox" class="have" aria-label="{esc(s["have"])}: {esc(title)}"><h3>{esc(title)}</h3>'
                    f'<span class="lv {first or "R"}">{s.get(first, "")}</span></div>'
                    + (f'<p class="note">{esc(note)}</p>' if note else "") + f'{deals}</li>')
    # Oct 21 (Bastien: "the hot weather should be another drop down... it only gets activated a couple days before the race"):
    # kits the race calls only in bad or hot weather fold under the list, out of the mandatory count
    for kit, krows in kits.items():
        rows.append(f'<li class="kit" data-kit="{kit}"><details><summary>{s["kit_" + kit]}</summary><p class="note kitwhen">{s.get("kitWhen_" + kit, s["kitWhen"])}</p>'
                    f'<ul class="gl sub">{"".join(krows)}</ul></details></li>')
    # quick answers from the race's own table
    faq = []
    for i, d in enumerate(race["dists"]):
        inkit = {k for ks in (race.get("kits") or {}).values() for k in ks}
        must = [txt["en" if L == "us" else L][0] for kind, lv, txt, _ in race["items"] if lv[i] == ("R" if race.get("suggested") else "M") and kind not in inkit]
        prov = [txt["en" if L == "us" else L][0] for kind, lv, txt, _ in race["items"] if lv[i] == "P"]
        ans = (s["aList"].format(items=", ".join(must)) if must else "") + (" " if must and prov else "") + (s["aProv"].format(items=", ".join(prov)) if prov else "")
        faq.append((s["qList"].format(d=dlab(race, d, L), **fmt), ans))
    if race.get("faq_jacket"):        # Harricana: "windbreakers will not be accepted"
        faq.append((s["qJacket"].format(**fmt), s["aJacket"].format(**{**fmt, "dists": dlabs(race, L, [d for i, d in enumerate(race["dists"]) if dict((k, lv) for k, lv, *_ in race["items"])["jacket"][i] == "M"])})))
    if race.get("cupless"):           # the race says its aid stations have no cups
        faq.append((s["qCup"].format(**fmt), s["aCup"]))
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    src = race.get("src_fr") if L == "fr" and race.get("src_fr") else race["src"]
    # Oct 20 (Bastien: "put it in the checklist as trail runners, choose your shoe"): the first line of the list, every distance
    every = "".join(f' data-l{d}="Y"' for d in race["dists"])
    shoe_row = (f'<li class="gi shoe" id="shoeBox" data-k="shoes"{every} data-root="" data-dir="{Tl["dir"]}" '
                f'data-pickfit="{esc(s["shPickFit"])}" data-from="{esc(s["shFrom"])}" data-page="{esc(s["shPage"])}" data-none="{esc(s["shNone"])}" data-rm="{esc(s["shRm"])}" data-gone="{esc(s["shGone"])}" data-picksize="{esc(s["shPickSize"])}">'
                f'<div class="hd"><span class="shi" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 17v-6l3.5-3 3 2.5 2.5-2.5 4.5 4.5h3a2.5 2.5 0 0 1 2.5 2.5V17z"/><path d="M2.5 20.5h19"/></svg></span><h3>{s["shH"]}</h3><span class="lv Y">{s["shTag"]}</span></div>'
                f'<div class="shrow"><input type="search" id="shoeQ" autocomplete="off" enterkeyhint="search" placeholder="{esc(s["shPh"])}" aria-label="{esc(s["shH"])}">'
                f'<select id="shoeSz" aria-label="{esc(s["shSize"])}" data-ph="{esc(s["shSize"])}"></select></div>'
                f'<ul class="sugg" id="shoeSug" role="listbox"></ul><ul class="mine2" id="shoeMine"></ul></li>')
    by_rows = "".join(f'<div class="byrow"><b>{s["by"][g]}</b><div class="row">'
                      + "".join(f'<button type="button" data-bg="{g}" data-bs="{z}">{z}</button>' for z in ("XS", "S", "M", "L", "XL", "2XL")) + '</div></div>'
                      for g in ("tops", "bottoms", "socks", "gloves"))
    same = {}                         # Oct 21: a kit line with the same picks as a list line (gloves, layers) points to it
    for k in list(pools):
        sig = json.dumps(pools[k], sort_keys=True)
        if sig in same and pools[k]:
            pools[k] = same[sig]
        else:
            same.setdefault(sig, k)
    pj = json.dumps(pools, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    sj = json.dumps(trail_shoes(items, pages), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = f"""<p class="crumbs"><a href="/{s['dir']}/">{s['aisle']}</a></p>
<h1>{esc(s['h1'].format(**fmt))}</h1>
<p class="sub">{esc(" · ".join([f"{d} {race['km'][d]} km" for d in race["dists"]] + [fmt["where"], fmt["when"]]) if race.get("km") else s['sub'].format(**fmt))}</p>
<p class="oside"><a href="{"/races/" if L == "us" else "/us/races/"}{slug}/">{esc(s['otherSide'])}</a></p>
<section class="rsize" id="rsize" data-men="{s['men']}" data-women="{s['women']}" data-change="{s['change']}"><p><b>{s['sizeH']}</b> · {s['sizeTxt']}</p>
<div class="row" data-f>{"".join(f'<button type="button" data-g="{g}">{s[g]}</button>' for g in ("men", "women"))}</div>
<p class="cur"><b>{s['sizeH']}:</b> <span></span> <button type="button" data-chg>{s['change']}</button></p>
<div class="row" data-s style="margin-top:6px">{"".join(f'<button type="button" data-s="{z}">{z}</button>' for z in ("XS", "S", "M", "L", "XL", "2XL"))}</div>
<p class="bym"><button type="button" data-byopen>{s['byOpen']}</button></p><div class="byrows" hidden>{by_rows}</div></section>
<p class="lbl">{s['dist']}</p>
<div class="dists" role="group" aria-label="{s['dist']}">{"".join(f'<button type="button" data-d="{d}" aria-pressed="{str(d == race["default"]).lower()}">{dlab(race, d, L)}</button>' for d in race["dists"])}</div>
<p class="prog" id="prog" data-t="{esc(s['progress'])}" data-all="{esc(s['progressAll'])}"></p>{f'<p class="lnote">{esc(s["lNote"])}</p>' if any("L" in lv for _, lv, *_ in race["items"]) else ""}{f'<p class="lnote">{esc(s["sNote"])}</p>' if race.get("suggested") else ""}
<ul class="gl" id="gl" data-race="{slug}" data-default="{race['default']}" data-lm="{s['M']}" data-lr="{s['R']}" data-la="{s['A']}" data-lp="{s['P']}" data-ll="{s['L']}"
 data-home="{Tl['home']}" data-watch="{esc(s['watch'])}" data-won="{esc(s['watchOn'])}" data-wmember="{esc(s['wMember'])}" data-wnew="{esc(s['wNew'])}" data-wpending="{esc(s['wPending'])}" data-wadd="{esc(s['wAdd'])}" data-woff="{esc(s['wOff'])}" data-moren="{esc(s['moreN'])}" data-dh="{esc(s['deals'])}" data-dhs="{esc(s['dealsSize'])}" data-none="{esc(s['noDeals'])}" data-few="{esc(s['few'])}" data-off="{esc(s['off'])}" data-ly="{esc(s['shTag'])}">{shoe_row}{"".join(rows)}</ul>
<p class="srcb">{(s['src'] if race.get('updated') else s['srcRead']).format(date=(race.get('updated') or race['read'])["en" if L == "us" else L], link=f'<a href="{src}" rel="noopener">{s["srcLink"]}</a>')} {s['notAff']}</p>
<section class="alert" id="raceBox" data-ref="race-{slug}" data-bad="{esc(Tl['alertBad'])}" data-ok="{esc(Tl['alertOk'])}" data-fail="{esc(Tl['alertFail'])}" data-pick="{esc(s['sizeTxt'])}">
<h2>{esc(s['boxH'])}</h2><p class="fine">{esc(s['boxTxt'])}</p><form novalidate><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(Tl['emailPh'])}" aria-label="Email" required><button type="submit">{esc(s['boxBtn'])}</button></form><p class="msg" aria-live="polite"></p></section>
<section class="faq"><h2>{s['faqH']}</h2>{"".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</section>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script id="pools" type="application/json">{pj}</script>
<script id="shoes" type="application/json">{sj}</script>
"""
    return head + body + KITB.replace("$BEST", esc(s["kbBest"])).replace("$BESTN", esc(s["kbBestN"])) + SCRIPT.replace("$LANG", "en" if L == "us" else L).replace("$CTRY", "us" if L == "us" else "ca").replace("$FX", str(fx)) + page_foot(Tl).replace('"shoe-page"', '"race-page"').replace("|shoes||shoe-page", "|gear||race-page")


# Oct 27 (Bastien: "the kit page is very long to scroll ... we can't have deals fall below the screen"): layout B. A/B test 'kit'
# (Bastien: "Yes race kit", Oct 27): same coin as the homepage (device id + "kit"), "exp|kit|A/B" once per session; ?exp=kit:B or ?kit=b forces B: a compact top (size + distance in two short rows, the US link moved under the list) and every gear
# line folded to ONE row: tick, name, level and "From $50 · 10 picks"; a tap opens its picks. Sinister 7 went 4.6 -> ~2 phone screens.
KITB = r"""<style>
html.kitb .oside{display:none}html.kitb .rsize{padding:10px 12px;margin:8px 0}html.kitb .rsize p{font-size:14px;margin:0 0 6px}
html.kitb .rsize button{min-height:34px;padding:5px 11px;font-size:14px}html.kitb .rsize .row{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
html.kitb .lbl{margin:8px 0 0}html.kitb .dists{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;margin:4px 0 8px}html.kitb .dists button{min-height:38px;padding:6px 12px;font-size:14px}
html.kitb .lnote,html.kitb .prog{font-size:13px;margin:2px 0 8px}
html.kitb .gl{gap:6px}html.kitb .gi{padding:10px 12px}
html.kitb .gi:not(.shoe) .hd{display:grid;grid-template-columns:24px 1fr 18px;column-gap:10px;row-gap:2px;cursor:pointer}
html.kitb .gi:not(.shoe) .hd h3{grid-column:2;font-size:17px}html.kitb .gi:not(.shoe) .hd .have{grid-row:1/3;align-self:center}
html.kitb .gi:not(.shoe) .hd .lv{grid-column:2;grid-row:2;justify-self:start;font-size:10px;padding:1px 6px;margin:0}
html.kitb .gi:not(.shoe) .hd::after{content:"";grid-column:3;grid-row:1/3;align-self:center;width:8px;height:8px;border-right:2px solid var(--muted);border-bottom:2px solid var(--muted);transform:rotate(45deg);transition:transform .15s}
html.kitb .gi.kopen .hd::after{transform:rotate(-135deg)}
html.kitb .gi .kb{grid-column:2;grid-row:3;font:600 14px var(--body);color:var(--moss,#2f6b3a)}html.kitb .gi .kb.no{color:var(--muted);font-weight:400}
html.kitb .gi.mini .hd::after,html.kitb .gi.mini .kb{display:none}
html.kitb .gi:not(.kopen):not(.shoe) .dl,html.kitb .gi:not(.kopen):not(.shoe) .ft,html.kitb .gi:not(.kopen):not(.shoe) .none,html.kitb .gi:not(.kopen):not(.shoe) .note{display:none}
html.kitb .gi.got .kb{display:none}
</style><script>
(function(){var over={};try{over=JSON.parse(localStorage.getItem("gf-exp")||"{}")||{};var q=new URLSearchParams(location.search).get("exp");
  if(q){q.split(",").forEach(function(x){var a=x.split(":");if(a[0]&&/^[AB]$/.test(a[1]))over[a[0]]=a[1]});localStorage.setItem("gf-exp",JSON.stringify(over))}}catch(e){}
var did="";try{did=localStorage.getItem("gf-did")||"";if(!did){did=(function(){try{return crypto.randomUUID()}catch(e){return "10000000-1000-4000-8000-100000000000".replace(/[018]/g,function(c){return (c^Math.random()*16>>c/4).toString(16)})}})();localStorage.setItem("gf-did",did)}}catch(e){}
var arm=/[?&]kit=b\b/.test(location.search)?"B":over.kit||(function(){var h=2166136261,s=did+"|kit";for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0)%2?"B":"A"})();
addEventListener("DOMContentLoaded",function(){try{if(!sessionStorage.getItem("gf-exp-kit")){sessionStorage.setItem("gf-exp-kit","1");ana("signup-step","exp|kit|"+arm)}}catch(e){}});
if(arm!=="B")return;document.documentElement.classList.add("kitb");
var gl=document.getElementById("gl"),os=document.querySelector(".oside");if(os&&gl){gl.parentNode.insertBefore(os,gl.nextSibling);os.style.cssText="display:block;margin:12px 0 0"}
var best=function(){gl.querySelectorAll(".gi:not(.shoe):not(.mini)").forEach(function(li){var hd=li.querySelector(".hd");if(!hd)return;
  var k=hd.querySelector(".kb");if(!k){k=document.createElement("span");k.className="kb";hd.appendChild(k)}
  var ps=[].slice.call(li.querySelectorAll(".dl .pr b")).map(function(b){return parseFloat(b.textContent.replace(/[^0-9.,]/g,"").replace(",","."))}).filter(function(x){return x>0}),
      shown=li.querySelector(".dl:not([hidden])");
  if(ps.length&&shown){var m=Math.min.apply(null,ps),b0=[].slice.call(li.querySelectorAll(".dl .pr b")).filter(function(b){return parseFloat(b.textContent.replace(/[^0-9.,]/g,"").replace(",","."))===m})[0];
    k.className="kb";k.textContent="$BEST".replace("{p}",b0?b0.textContent:m).replace("{n}",ps.length)}else{k.className="kb no";k.textContent="$BESTN"}})};
gl.addEventListener("click",function(e){var hd=e.target.closest(".gi:not(.shoe):not(.mini) .hd");if(!hd||e.target.closest("input,button,a"))return;hd.parentNode.classList.toggle("kopen")});
new MutationObserver(function(){clearTimeout(best.t);best.t=setTimeout(best,60)}).observe(gl,{childList:true,subtree:true});setTimeout(best,300)})();
</script>"""


# picks the deals in the visitor's fit and clothing size, remembers the distance and the ticks (this browser only)
SCRIPT = r"""<script>
(function(){var gl=document.getElementById("gl"),race=gl.dataset.race,fr="$LANG"==="fr";
var get=function(k){try{return JSON.parse(localStorage.getItem(k)||"null")}catch(e){return null}},put=function(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
var pools={};try{pools=JSON.parse(document.getElementById("pools").textContent)}catch(e){}
Object.keys(pools).forEach(function(k){if(typeof pools[k]==="string")pools[k]=pools[pools[k]]});   // a line sharing another line's picks
var st=get("gf-race-"+race)||{},have=st.have||{},dist=st.d||gl.dataset.default;
var prof=get("rd-profile"),rs=get("gf-race-size");
var fit=(rs&&rs.g)||(prof&&prof.gender!=="any"&&prof.gender)||"",size=(rs&&rs.s)||"",by=(rs&&rs.by)||{};
/* Oct 21: a size per category (a visitor: "medium in shorts, L in socks, small in t-shirts"), like the homepage's sizes screen */
if(!rs&&prof&&prof.sizes){var per={},votes={};["tops","bottoms","socks","gloves","headwear"].forEach(function(g){var z=((prof.sizes[g]||{}).sizes||[])[0];if(z){per[g]=String(z).toUpperCase();votes[per[g]]=(votes[per[g]]||0)+1}});
  size=Object.keys(votes).sort(function(a,b){return votes[b]-votes[a]})[0]||"";["tops","bottoms","socks","gloves"].forEach(function(g){if(per[g]&&per[g]!==size)by[g]=per[g]})}
var sizeFor=function(g){return (g==="bras"?by.tops:by[g])||size};
var nm=function(n){return fr?n.replace(/Women[’']s\b/g,"Femme").replace(/Men[’']s\b/g,"Homme").replace(/\bUnisex\b/g,"Unisexe"):n};
var FX=$FX,money=function(v){v=v/FX;return fr?v.toFixed(2).replace(".",",")+" $":"$"+v.toFixed(2)};   // US pages: the data is in CAD, shown in US$
var esc=function(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
var ALIAS={"XXS":"2XS","XXL":"2XL","X-SMALL":"XS","SMALL":"S","MEDIUM":"M","LARGE":"L","X-LARGE":"XL","EXTRA LARGE":"XL","XX-SMALL":"2XS"};
var norm=function(z){z=String(z).toUpperCase().trim();return ALIAS[z]||z};
var fits=function(lab,z){if(!z)return true;var l=norm(lab);if(l==="OS"||l==="OSFA"||l==="OSZ")return true;
  return l.split(/\s*[\/|]\s*/).map(norm).indexOf(norm(z))>=0};
var SIZED={tops:1,bottoms:1,gloves:1,headwear:1,socks:1},SHOWN={};
function render(){
  [].forEach.call(document.querySelectorAll(".dists button"),function(b){b.setAttribute("aria-pressed",String(b.dataset.d===dist))});
  var n=0,h=0;
  var R={Y:-1,M:0,L:1,R:2,A:3,P:4};
  [].forEach.call(gl.querySelectorAll(".kit"),function(kb){kb.hidden=![].some.call(kb.querySelectorAll(".gi"),function(x){return x.getAttribute("data-l"+dist)})});
  [].forEach.call(gl.querySelectorAll(".gi"),function(li){var lv=li.getAttribute("data-l"+dist)||"",k=li.dataset.k;li.hidden=!lv;
    li.style.order=2*(R[lv]||0)+(li.classList.contains("mini")?1:0);   // what's mandatory for this distance first; the small stuff after
    var tag=li.querySelector(".lv");tag.className="lv "+lv;tag.textContent=lv==="Y"?gl.dataset.ly:lv==="M"?gl.dataset.lm:lv==="R"?gl.dataset.lr:lv==="A"?gl.dataset.la:lv==="P"?gl.dataset.lp:lv==="L"?gl.dataset.ll:"";
    if(k==="shoes")return;   // the shoe line: no tick, not counted
    var got=!!have[k]&&lv!=="P";li.classList.toggle("got",got);li.querySelector("input.have").checked=got;li.querySelector("input.have").hidden=lv==="P";   // provided by the race: nothing to tick
    if(lv==="M"&&!li.dataset.kit){n++;if(got)h++}
    var p=pools[k];if(!p||!p.length||(!fit&&!size))return;   // an item no store has today (blankets, Oct 21) keeps its "none" line
    var ok=[];for(var i=0;i<p.length;i++){var r=p[i];
      if(fit&&r.sx.length&&r.sx.indexOf(fit)<0)continue;
      var s=SIZED[r.g]?r.s.filter(function(e){return fits(e[0],sizeFor(r.g))}):r.s;if(!s.length)continue;
      ok.push([r,s.reduce(function(a,b){return b[1]<a[1]?b:a})])}
    if(k==="headlamp2"){var up=(SHOWN.headlamp||[]);ok=ok.filter(function(x){return up.indexOf(x[0].n)<0})}
    var seen={},all=ok.filter(function(x){var b=x[0].b.toLowerCase(),n=!seen[b];seen[b]=1;return n}).concat(ok).filter(function(x,i,a){return a.indexOf(x)===i});   // one per brand first
    var sale=function(x){return x[1][2]>x[1][1]*1.01},picks=all.slice(0,10),more=all.slice(10).filter(sale);   // same rule as picks() in race_pages.py
    while(picks.filter(sale).length<3&&more.length){var i=-1;picks.forEach(function(x,j){if(!sale(x))i=j});if(i<0)break;picks[i]=more.shift()}
    if(!picks.slice(0,3).some(sale)&&picks.some(sale)){var j=picks.findIndex(sale);picks.splice(2,0,picks.splice(j,1)[0])}
    var ul=li.querySelector(".dl"),none=li.querySelector(".none"),mb=li.querySelector(".mored");
    ul.hidden=!picks.length;none.hidden=!!picks.length;mb.hidden=picks.length<=3;mb.textContent=mb.dataset.n.replace("{n}",picks.length);
    var few=li.querySelector(".few");if(!few){few=document.createElement("span");few.className="few";mb.after(few)}   // Oct 20: fewer than 10 in this size = say so
    few.hidden=!(picks.length&&picks.length<10&&SIZED[p[0].g]&&sizeFor(p[0].g));few.textContent=gl.dataset.few.replace("{n}",picks.length).replace("{fit}",(fit?document.getElementById("rsize").dataset[fit]:"")).replace("{size}",sizeFor(p[0].g));
    SHOWN[k]=picks.slice(0,3).map(function(x){return x[0].n});if(!picks.length)return;
    ul.innerHTML=picks.map(function(x){var r=x[0],e=x[1];
      var pr=e[2]>e[1]*1.01?'<b>'+money(e[1])+'</b><s>'+money(e[2])+'</s> <span class="off">−'+Math.round(100*(1-e[1]/e[2]))+'%</span>':'<b>'+money(e[1])+'</b>',h=gl.dataset.home;
      return '<li><a class="dg" href="'+esc(e[3])+'" data-store="'+esc(r.h)+'" target="_blank" rel="noopener"><img src="'+esc(r.img)+'" alt="" loading="lazy" referrerpolicy="no-referrer"><span class="nm"><b>'+esc(r.b)+'</b>'+esc(nm(r.n))+'<small>'+esc(r.st)+(SIZED[r.g]&&size?" · "+esc(e[0]):"")+'</small></span><span class="pr">'+pr+'</span></a><button type="button" class="wt" data-k="'+esc(r.k)+'" data-p="'+e[1]+'" data-u="'+esc(e[3])+'" aria-pressed="false" aria-label="'+esc(gl.dataset.watch)+': '+esc(r.b+" "+r.n)+'"><span class="hh">♡</span><span class="wl"> '+esc(gl.dataset.watch)+'</span></button></li>'}).join("")});
  var pg=document.getElementById("prog");pg.hidden=!n;pg.textContent=n&&h>=n?pg.dataset.all:pg.dataset.t.replace("{h}",h).replace("{n}",n);
  var box=document.getElementById("rsize");box.classList.toggle("set",!!(fit&&size)&&!box.dataset.open);
  box.querySelector(".cur span").textContent=(fit?box.dataset[fit]:"")+" · "+size+Object.keys(by).map(function(g){var b0=box.querySelector('[data-bg="'+g+'"]');return " ("+b0.closest(".byrow").querySelector("b").textContent.toLowerCase()+" "+by[g]+")"}).join("");
  if(Object.keys(by).length)box.querySelector(".byrows").hidden=false;box.querySelector(".bym").hidden=!box.querySelector(".byrows").hidden;
  [].forEach.call(box.querySelectorAll("button[data-bg]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.bs===sizeFor(b.dataset.bg)))});[].forEach.call(box.querySelectorAll("[data-g]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.g===fit))});
  [].forEach.call(box.querySelectorAll("button[data-s]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.s===size))});
}
/* Oct 23 (Bastien: "add a tracker to see how and if people are using the gear checklist"): what people do on a race list, as
   "filter" events "race|<race>|<what>|<detail>" (a kind the database already takes; funnel.yml "RACE GEAR LISTS" reads them) */
var rt=function(what,x){try{ana("filter",["race",race,what,x==null?"":x].join("|"))}catch(e){}};
var doneSent=false,checkDone=function(){if(doneSent)return;var m=[].filter.call(gl.querySelectorAll(".gi:not([hidden])"),function(li){return li.getAttribute("data-l"+dist)==="M"&&!li.closest(".kit")});   // the "You have N of M" items (kits apart)
  if(m.length&&m.every(function(li){return have[li.dataset.k]})){doneSent=true;rt("complete",dist+"|"+m.length)}};
document.addEventListener("DOMContentLoaded",function(){rt("open",dist)});   // ana() is defined further down the page
document.querySelector(".dists").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;dist=b.dataset.d;st.d=dist;put("gf-race-"+race,st);render();rt("dist",dist)});
gl.addEventListener("change",function(e){var li=e.target.closest(".gi");if(!li||!e.target.classList.contains("have"))return;have[li.dataset.k]=e.target.checked;st.have=have;put("gf-race-"+race,st);render();
  rt(e.target.checked?"have":"unhave",li.dataset.k);if(e.target.checked)checkDone()});
gl.addEventListener("click",function(e){var b=e.target.closest(".mored");if(b){b.closest(".gi").classList.add("open");rt("seeall",b.closest(".gi").dataset.k)}});
document.getElementById("rsize").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;
  if(b.hasAttribute("data-chg")){this.dataset.open="1";render();return}if(b.dataset.s&&fit)delete this.dataset.open;
  if(b.hasAttribute("data-byopen")){this.querySelector(".byrows").hidden=false;render();return}
  if(b.dataset.bg){if(b.dataset.bs===size)delete by[b.dataset.bg];else by[b.dataset.bg]=b.dataset.bs}
  if(b.dataset.g)fit=b.dataset.g;if(b.dataset.s)size=b.dataset.s;put("gf-race-size",{g:fit,s:size,by:by});render();
  if(b.dataset.s||b.dataset.bg)rt("size",(fit||"")+"|"+(b.dataset.bs||b.dataset.s))});
/* Oct 20 (Bastien: "I thought it would just heart it there"): Watch hearts right here, in the same watchlist as the homepage
   (gf-watch); members' hearts go to their account too (watch_add, like the homepage), others are asked for an email */
var SB="https://krwymmkauwqqxjxbvkyq.supabase.co/rest/v1/rpc/",KEY="sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2";
var rpc=function(fn,body){return fetch(SB+fn,{method:"POST",headers:{apikey:KEY,"Content-Type":"application/json"},body:JSON.stringify(body)})};
var byK={};Object.keys(pools).forEach(function(k){pools[k].forEach(function(r){byK[r.k]=r})});
function hearts(){var w=get("gf-watch")||{};[].forEach.call(document.querySelectorAll(".wt"),function(b){var on=!!w[b.dataset.k];
  b.setAttribute("aria-pressed",String(on));b.querySelector(".hh").textContent=on?"♥":"♡";b.querySelector(".wl").textContent=" "+(on?gl.dataset.won:gl.dataset.watch)})}
var toastT=null;function say(txt,add){var t=document.getElementById("wtoast");if(!t){t=document.createElement("div");t.id="wtoast";t.className="wtoast";t.setAttribute("role","status");document.body.appendChild(t)}
  t.innerHTML="";var p=document.createElement("div");p.textContent=txt;t.appendChild(p);
  if(add){var b=document.createElement("button");b.type="button";b.textContent=gl.dataset.wadd;b.onclick=function(){t.hidden=true;var bx=document.getElementById("raceBox");bx.scrollIntoView({block:"center"});var i=bx.querySelector("input");if(i)i.focus()};t.appendChild(b)}
  t.hidden=false;clearTimeout(toastT);toastT=setTimeout(function(){t.hidden=true},add?7000:3500)}
gl.addEventListener("click",function(e){var b=e.target.closest(".wt");if(!b)return;e.preventDefault();
  var k=b.dataset.k,w=get("gf-watch")||{},sub=get("gf-sub")||{},r=byK[k]||{};
  if(w[k]){delete w[k];put("gf-watch",w);if(sub.key)rpc("watch_remove",{p_token:sub.key,p_key:k}).catch(function(){});hearts();say(gl.dataset.woff);
    try{ana("watch-remove",r.g)}catch(x){}return}
  var pr=parseFloat(b.dataset.p)||null;
  w[k]={b:r.b,n:r.n,g:r.g,url:b.dataset.u,price:pr,low:pr,seen:pr,gone:false,saved:new Date().toISOString()};put("gf-watch",w);hearts();
  try{ana("watch-add",r.g)}catch(x){}try{window.umami&&umami.track("watch-add",{brand:r.b,group:r.g,from:"race-page"})}catch(x){}
  if(sub.key&&sub.active){rpc("watch_add",{p_token:sub.key,p_key:k,p_meta:w[k]}).catch(function(){});say(gl.dataset.wmember)}
  else if(sub.pending)say(gl.dataset.wpending);else say(gl.dataset.wnew,!!document.getElementById("raceBox"))});
/* "What do you run in?" (Oct 20): type -> up to 6 trail shoe models (every typed word starts a word of the model, like the
   homepage's rcSuggest); a pick goes on the watchlist in the visitor's fit, same as any heart above */
var SH=[];try{SH=JSON.parse(document.getElementById("shoes").textContent)}catch(e){}
var sbox=document.getElementById("shoeBox"),sq=document.getElementById("shoeQ"),ssel=document.getElementById("shoeSz"),sug=document.getElementById("shoeSug"),mine=document.getElementById("shoeMine");
var fold=function(t){return String(t).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim()};
SH.forEach(function(x){x.f=fold(x.b+" "+x.m).split(" ")});
/* the shoe size: remembered from the profile or the shoe pages (gf-shoe-size), saved back there when picked here */
function shoeSize(){var ss=get("gf-shoe-size");if(ss&&ss.s&&(!fit||ss.g===fit||ss.g==="any"))return String(ss.s);
  var z=prof&&prof.sizes&&prof.sizes.shoes&&(prof.sizes.shoes.sizes||[])[0];return z&&(!fit||prof.gender===fit||prof.gender==="any")?String(z):""}
function sizeMenu(){var v=ssel.value||shoeSize(),lo=fit==="women"?5:6,hi=fit==="women"?12:15,o='<option value="">'+esc(ssel.dataset.ph)+'</option>';
  for(var n=lo;n<=hi;n+=0.5)o+='<option>'+n+'</option>';ssel.innerHTML=o;ssel.value=v}
ssel.addEventListener("change",function(){if(ssel.value){put("gf-shoe-size",{g:fit||"men",s:ssel.value});rt("shoesize",ssel.value)}shoeMine()});
function shoeMine(){var z=ssel.value;var w=get("gf-watch")||{},out=[];SH.forEach(function(x){["men","women"].forEach(function(f){if(x[f]&&w[x[f][0]])out.push([x,f])})});
  mine.innerHTML="";out.forEach(function(o){var x=o[0],f=o[1],li=document.createElement("li");
    li.innerHTML='<b>♥ '+esc(x.b+" "+x.m)+'</b><small>'+esc(z?(x[f][4]&&x[f][4][z]!=null?sbox.dataset.from.replace("{p}",money(x[f][4][z])).replace("{s}",z):sbox.dataset.gone.replace("{s}",z)):"")+'</small>'+(x.s?'<a href="'+sbox.dataset.root+'/'+sbox.dataset.dir+'/'+esc(x.s)+'/">'+esc(sbox.dataset.page)+' →</a>':'')+'<button type="button" data-rm="'+esc(x[f][0])+'">'+esc(sbox.dataset.rm)+'</button>';
    mine.appendChild(li)})}
sq.addEventListener("input",function(){var q=fold(sq.value).split(" ").filter(Boolean);sug.innerHTML="";if(!q.length)return;
  var hits=SH.filter(function(x){return (x.men||x.women)&&q.every(function(t){return x.f.some(function(w){return w.indexOf(t)===0})})}).slice(0,6);
  if(!hits.length){sug.innerHTML='<li class="no">'+esc(sbox.dataset.none)+'</li>';return}
  hits.forEach(function(x,i){var li=document.createElement("li"),b=document.createElement("button");b.type="button";b.textContent=x.b+" "+x.m;b.dataset.i=SH.indexOf(x);li.appendChild(b);sug.appendChild(li)})});
sug.addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;var x=SH[+b.dataset.i];
  if(!fit){sug.innerHTML='<li class="no">'+esc(sbox.dataset.pickfit)+'</li>';document.getElementById("rsize").scrollIntoView({block:"center"});return}
  if(!ssel.value){sug.innerHTML='<li class="no">'+esc(sbox.dataset.picksize)+'</li>';ssel.focus();return}
  put("gf-shoe-size",{g:fit,s:ssel.value});
  var it=x[fit]||x.men||x.women,k=it[0],w=get("gf-watch")||{},sub=get("gf-sub")||{},pz=(it[4]||{})[ssel.value];pz=pz==null?null:pz;
  w[k]={b:x.b,n:it[3]||x.m,g:"shoes",url:it[2],price:pz,low:pz,seen:pz,gone:pz==null,saved:new Date().toISOString()};put("gf-watch",w);
  try{ana("watch-add","shoes")}catch(z){}try{window.umami&&umami.track("watch-add",{brand:x.b,group:"shoes",from:"race-page-shoe"})}catch(z){}
  if(sub.key&&sub.active){rpc("watch_add",{p_token:sub.key,p_key:k,p_meta:w[k]}).catch(function(){});say(gl.dataset.wmember)}
  else if(sub.pending)say(gl.dataset.wpending);else say(gl.dataset.wnew,!!document.getElementById("raceBox"));
  sq.value="";sug.innerHTML="";shoeMine()});
mine.addEventListener("click",function(e){var b=e.target.closest("button[data-rm]");if(!b)return;var w=get("gf-watch")||{},sub=get("gf-sub")||{};
  delete w[b.dataset.rm];put("gf-watch",w);if(sub.key)rpc("watch_remove",{p_token:sub.key,p_key:b.dataset.rm}).catch(function(){});shoeMine();say(gl.dataset.woff)});
var render0=render;render=function(){render0();hearts();sizeMenu();shoeMine()};
render();
(function(){var box=document.getElementById("raceBox"),f=box.querySelector("form"),msg=box.querySelector(".msg");
var sub=get("gf-sub");if(sub&&(sub.active||sub.key)){box.remove();return}
f.addEventListener("submit",function(e){e.preventDefault();
  var em=f.querySelector("input").value.trim().replace(/^mailto:/i,"").replace(/^.*<([^>]+)>.*$/,"$1").replace(/\s+/g,"").replace(/\.+$/,"");
  if(!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/.test(em)||/\.\./.test(em)){msg.textContent=box.dataset.bad;return}
  if(!fit||!size){msg.textContent=box.dataset.pick;document.getElementById("rsize").scrollIntoView({block:"center"});return}
  var tz=null;try{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||null}catch(x){}
  var G=["shoes","tops","bottoms","bras","socks","gloves","headwear","packs","gear","watches","nutrition"],p;
  if(prof&&prof.sizes)p=JSON.parse(JSON.stringify(prof));
  else{var sz={shoes:{sizes:[],width:[]}};G.slice(1).forEach(function(k){sz[k]={sizes:[]}});
    p={lang:fr?"fr":"en",country:"$CTRY",tz:tz,name:"",gender:fit,terrain:"trail",ships:"$CTRY",groups:G,sizes:sz,brands:[],activities:[]}}
  ["tops","bottoms","bras","socks","gloves","headwear"].forEach(function(k){if(!(p.sizes[k]&&(p.sizes[k].sizes||[]).length))p.sizes[k]={sizes:[sizeFor(k)]}});
  if(ssel.value&&!(p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length))p.sizes.shoes={sizes:[ssel.value],width:[]};
  p.email=em;if(!p.ref)p.ref=get("gf-ref")||box.dataset.ref;var btn=f.querySelector("button");btn.disabled=true;
  fetch("https://krwymmkauwqqxjxbvkyq.supabase.co/rest/v1/rpc/subscribe",{method:"POST",headers:{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"},
    body:JSON.stringify({p_email:em,p_profile:Object.assign({},p,{watch_new:get("gf-watch")||{}})})}).then(function(r){if(!r.ok)throw 0;
    put("gf-sub",{pending:em});if(!prof)put("rd-profile",p);f.remove();msg.textContent=box.dataset.ok.replace("{email}",em);
    try{ana("signup",box.dataset.ref)}catch(x){}try{window.umami&&umami.track("signup",{method:"email",where:box.dataset.ref,lang:fr?"fr":"en"})}catch(x){}})
  .catch(function(){btn.disabled=false;msg.textContent=box.dataset.fail})})})();
})();
</script>
"""


HUB = {
    "en": {"title": "Race gear lists: mandatory gear, item by item", "h1": "Race gear lists",
           "desc": "Mandatory gear lists for trail and ultra races, item by item, with today's best prices in your size at Canadian stores.",
           "intro": "The mandatory gear for each race, as the race publishes it, with today's best prices in your size. More races coming soon.",
           "go": "Mandatory gear list →", "goS": "Suggested gear list →", "dists": "{d} km",
           "find": "Find your race: name, place or country", "findNone": "No race matches “{q}” yet. Tell us which one: hello@thegearfox.com"},
    "fr": {"title": "Listes de matériel de course : le matériel obligatoire, article par article", "h1": "Listes de matériel de course",
           "desc": "Le matériel obligatoire des courses en sentier et des ultras, article par article, avec les meilleurs prix du jour dans votre taille.",
           "intro": "Le matériel obligatoire de chaque course, tel que publié par la course, avec les meilleurs prix du jour dans votre taille. D'autres courses s'en viennent.",
           "go": "Liste du matériel obligatoire →", "goS": "Liste du matériel suggéré →", "dists": "{d} km",
           "find": "Trouvez votre course : nom, lieu ou pays", "findNone": "Aucune course ne correspond à « {q} » pour l'instant. Dites-nous laquelle : hello@thegearfox.com"},
}
HUB["us"] = dict(HUB["en"], desc="Mandatory gear lists for trail and ultra races, item by item, with today's best prices in your size at US stores.")
HUB["en"]["groups"] = HUB["us"]["groups"] = {"ca": "Canada", "us": "United States", "fr": "France", "it": "Italy", "ch": "Switzerland",
                                             "de": "Germany", "at": "Austria", "si": "Slovenia", "au": "Australia", "nz": "New Zealand"}
HUB["fr"]["groups"] = {"ca": "Canada", "us": "États-Unis", "fr": "France", "it": "Italie", "ch": "Suisse", "de": "Allemagne", "at": "Autriche", "si": "Slovénie",
                       "au": "Australie", "nz": "Nouvelle-Zélande"}
HUB["en"]["note"] = "Every list shows today's prices at Canadian stores, wherever the race is."
HUB["fr"]["note"] = "Chaque liste montre les prix du jour dans les boutiques canadiennes, peu importe où a lieu la course."
HUB["us"]["note"] = "Every list shows today's prices at US stores, wherever the race is."
OTHER = {"en": ("Shopping in the US?", "Same lists with US stores →", "/us/races/"), "fr": ("Vous magasinez aux États-Unis ?", "Les mêmes listes avec les boutiques américaines →", "/us/races/"),
         "us": ("Shopping in Canada?", "Same lists with Canadian stores →", "/races/")}


def side(L):
    """Oct 21 (Bastien: "races should be available on both sides regardless"): every race on every side, the visitor's country first."""
    first = "us" if L == "us" else "ca"
    order = {first: 0, "ca": 1, "us": 2, "fr": 3, "it": 4, "ch": 5, "de": 6, "at": 7, "si": 8, "au": 9, "nz": 10}
    return sorted(RACES.items(), key=lambda kv: order.get(kv[1].get("side", "ca"), 11))


# Oct 21: the shoe list pages' cards put the link in a right-hand column, which squeezed race names to 2-3 words a line on phones
HUB_CSS = (".hubh{margin-top:26px}.cards.rh .nm{min-width:0;max-width:100%}.cards.rh small{overflow-wrap:anywhere}"   # Oct 23: Zugspitz's 7 distance names in one word overflowed a phone
           ".cards.rh a{flex-direction:column;align-items:flex-start;gap:4px;padding:12px 14px}.cards.rh .nm b{font-size:20px}"
           ".cards.rh .pr{text-align:left;white-space:normal;font:600 15px var(--body);color:var(--moss)}")


# Oct 27 (Bastien: "add a search function for the race kits and the hiking planner"): a box on the hubs that filters the cards as
# you type (name, place, country, distance; accents and capitals ignored); groups with no match fold away
def hub_find(ph, none):
    return (f'<div class="hfind"><input type="search" id="hubQ" placeholder="{esc(ph)}" aria-label="{esc(ph)}" autocomplete="off" enterkeyhint="search">'
            f'<p class="hnone" hidden data-t="{esc(none)}"></p></div>'
            '<style>.hfind{position:sticky;top:var(--hh,0px);z-index:5;background:var(--bg,#faf8f3);padding:8px 0 10px}'
            '.hfind input{width:100%;box-sizing:border-box;font:16px var(--body);border:1.5px solid var(--line);border-radius:999px;padding:11px 16px;background:var(--card)}'
            '.hnone{color:var(--muted);margin:8px 2px 0}ul.cards li[hidden],ul.cards[hidden],h2[hidden]{display:none!important}</style>'
            '<script>(function(){var q=document.getElementById("hubQ"),no=document.querySelector(".hnone");if(!q)return;'
            'var f=function(s){return (s||"").normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").toLowerCase()};'
            'var cards=null;'   # the cards come after this box in the page: read them on the first keystroke
            'var run=function(){if(!cards){cards=[].slice.call(document.querySelectorAll("ul.cards li"));cards.forEach(function(li){li.dataset.h=f(li.textContent+" "+((li.closest("ul.cards").previousElementSibling||{}).textContent||""))})}var w=f(q.value).split(/\\s+/).filter(Boolean),n=0;cards.forEach(function(li){var ok=w.every(function(x){return li.dataset.h.indexOf(x)>=0});li.hidden=!ok;if(ok)n++});'
            'document.querySelectorAll("ul.cards").forEach(function(u){var any=[].some.call(u.children,function(li){return !li.hidden});u.hidden=!any;var h=u.previousElementSibling;if(h&&/^H[23]$/.test(h.tagName))h.hidden=!any});'
            'no.hidden=!!n||!w.length;no.textContent=no.dataset.t.replace("{q}",q.value.trim());'
            'clearTimeout(run.t);run.t=setTimeout(function(){try{ana("filter","hubsearch|"+location.pathname.split("/")[1]+"|"+q.value.trim().toLowerCase().slice(0,40))}catch(e){}},1500)};'
            'q.addEventListener("input",run)})();</script>')


def hub(L):
    """/races/ + /courses/ (Oct 21, Bastien: a ☰ menu item "even if it's one; we will add more soon"); /us/races/ for the USA side."""
    h, Tl, LL = HUB[L], tl(L), "en" if L == "us" else L
    rows, grp = "", None
    for slug, r in side(L):
        if r.get("side", "ca") != grp:
            grp = r.get("side", "ca")
            rows += f'{"</ul>" if rows else ""}<h2>{esc(h["groups"][grp])}</h2><ul class="cards rh">'
        rows += (f'<li><a href="/{S[L]["dir"]}/{slug}/"><span class="nm"><b>{esc(r["name"])}</b>'
                 f'<small>{esc(r["where"][LL])} · {esc(r["when"][LL])} · {esc(dlabs(r, L))}</small></span>'
                 f'<span class="pr">{h["goS"] if r.get("suggested") else h["go"]}</span></a></li>')
    o = OTHER[L]
    head = page_head(US, h["title"], h["desc"], "/us/races/", "", f"<style>{HUB_CSS}</style>").replace('class="sw" href="/shoes/"', 'class="sw" href="/races/"') if L == "us" else page_head(T[L], h["title"], h["desc"], "/races/", "/courses/", f"<style>{HUB_CSS}</style>")
    BASE = "https://thegearfox.com"
    head = re.sub(r'(<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n?)+',
                  f'<link rel="alternate" hreflang="en-CA" href="{BASE}/races/">\n<link rel="alternate" hreflang="fr-CA" href="{BASE}/courses/">\n'
                  f'<link rel="alternate" hreflang="en-US" href="{BASE}/us/races/">\n<link rel="alternate" hreflang="x-default" href="{BASE}/races/">\n', head, count=1)
    return (head + f'<h1 class="hubh">{esc(h["h1"])}</h1><p class="sub">{esc(h["intro"])}</p>'
            + f'<p class="fine">{esc(h["note"])} {esc(o[0])} <a href="{o[2]}">{esc(o[1])}</a></p>' + hub_find(h["find"], h["findNone"]) + f'{rows}</ul>' + page_foot(Tl))


def add_to_sitemap(site):
    """shoe_pages.py writes sitemap.xml earlier in the refresh; the race pages join it (never twice)."""
    p = site / "sitemap.xml"
    if not p.exists():
        return
    x = p.read_text()
    urls = ["/races/", "/courses/", "/us/races/"] + [f"/{S[L]['dir']}/{slug}/" for L in ("en", "fr", "us") for slug in RACES]
    today = __import__("datetime").date.today().isoformat()
    new = "".join(f"<url><loc>https://thegearfox.com{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls if f"https://thegearfox.com{u}<" not in x)
    if new and "</urlset>" in x:
        p.write_text(x.replace("</urlset>", new + "</urlset>"))


def main():
    site = Path(sys.argv[1])
    sale = json.loads(Path(sys.argv[2] if len(sys.argv) > 2 else site / "deals.json").read_text())   # full price too
    stores = store_names((site / "index.html").read_text())
    try:
        pages = json.loads((site / "shoes" / "pages.json").read_text())       # written by shoe_pages.py earlier in the refresh
    except Exception:
        pages = {}
    for slug, race in RACES.items():
        for L in ("en", "fr"):
            out = site / S[L]["dir"] / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(slug, race, L, sale["items"], stores, pages))
            print("wrote", out)
    us = site / "deals-us.json"         # USA side (Oct 21): the same races from the US data, prices in US$
    if us.exists():
        data = json.loads(us.read_text())
        fx = float((data.get("fx") or {}).get("USD") or 1.37)
        S["us"]["money"] = lambda v: f"${v / fx:,.2f}"
        try:
            us_pages = json.loads((site / "us" / "shoes" / "pages.json").read_text())
        except Exception:
            us_pages = {}
        for slug, race in RACES.items():
            out = site / S["us"]["dir"] / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(slug, race, "us", data["items"], stores, us_pages, fx))
            print("wrote", out)
    for L in ("en", "fr", "us"):
        (site / S[L]["dir"]).mkdir(parents=True, exist_ok=True)
        (site / S[L]["dir"] / "index.html").write_text(hub(L))
    add_to_sitemap(site)


if __name__ == "__main__":
    main()
