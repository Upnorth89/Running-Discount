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
from shoe_pages import T, esc, page_head, page_foot, store_names, size_url, host  # noqa: E402

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
    "wind": "salomon|arc'teryx|patagonia|the north face|inov-8|montane|black diamond|outdoor research|brooks|craft|kiprun|ciele|janji|rabbit|tracksmith|saucony|hoka|on|nnormal|raidlight|norrøna|mec",
})
BRANDS = {k: set(v.split("|")) for k, v in BRANDS.items()}
MAYBE = {"2xu", "balmoral", "nike", "under armour", "bula", "camelbak", "osprey"}
RUN = re.compile(r"\brun|running|trail|race|racing|ultra|marathon", re.I)
KINDS = {
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
                     x=r"belt|waist|hip|bladder|reservoir|tube|replacement|strap|daypack|\b[3-9]\d ?l\b|\bski\b|bike|ride|wind|insulat|hybrid|shield|fleece|puffer|down\b"),
    "filter":   dict(g={"gear", "packs"}, need=r"filter|purif|befree|lifestraw|sawyer|aquatab|katadyn|xa filter", good=r".",
                     x=r"adapter|replacement|cartridge|inline|\bkit\b|\bcap\b"),
    "longpants": dict(g={"bottoms"}, t={"pant", "tight"}, need=r"\bpants?\b|tights?\b|legging|jogger", good=r"\brun|trail|thermal|warm|merino|tech|race|ultra|light",
                     x=r"short|capri|3/4|7/8|crop|bra\b|\bski\b|snow|insulat|\bbib\b|cotton|yoga"),
    "warmjacket": dict(g={"tops"}, t={"jacket"}, need=r"insulat|\bdown\b|puffer|primaloft|synthetic|thermal|hybrid|alpha|octa|atom|nano|fill",
                     good=r"\brun|trail|light|hood|hoody|packable", x=r"vest|\bski\b|snow|parka|3-in-1|t-?shirt|\btee\b"),
    "socks":    dict(g={"socks"}, need=r".", good=r"\brun|trail|merino|toe|wool|ultra|crew|cushion", x=r"no show|liner only|compression sleeve|kids?|dress|casual|lifestyle"),
    "wind":     dict(g={"tops"}, t={"jacket"}, need=r"wind|breaker|shell|anorak|light ?jacket|run jacket", good=r"\brun|trail|race|light|ultra|pack|dwr",
                     x=r"insulat|\bdown\b|puffer|nano|atom|alpha|primaloft|thermal|\bski\b|snow|parka|3-in-1|t-?shirt|\btee\b|vest"),
}

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
            ("jacket", "MM", {"en": ("Waterproof jacket with a hood (bad-weather kit)", "When the race calls the bad-weather kit. Sealed seams, the jacket's own hood."),
                              "fr": ("Manteau imperméable avec capuchon (kit mauvais temps)", "Quand la course annonce le kit mauvais temps. Coutures scellées, capuchon d'origine.")}, True),
            ("longpants", "MM", {"en": ("Pants or tights that cover the legs (bad-weather kit)", "Tights + socks that cover the legs also count."),
                                 "fr": ("Pantalon ou collant couvrant les jambes (kit mauvais temps)", "Un collant + des bas qui couvrent les jambes comptent aussi.")}, False),
            ("midlayer", "MR", {"en": ("Warm long-sleeve mid-layer (bad-weather kit)", "No cotton, 180 g or more in size M."), "fr": ("Couche intermédiaire chaude à manches longues (kit mauvais temps)", "Pas de coton, 180 g ou plus en taille M.")}, False),
            ("tuque", "MR", {"en": ("Beanie or neck gaiter (bad-weather kit)", ""), "fr": ("Tuque ou cache-cou (kit mauvais temps)", "")}, False),
            ("gloves", "MR", {"en": ("Warm, waterproof gloves (bad-weather kit)", ""), "fr": ("Gants chauds et imperméables (kit mauvais temps)", "")}, False),
            ("pants", "R ", {"en": ("Waterproof overpants (bad-weather kit)", ""), "fr": ("Surpantalon imperméable (kit mauvais temps)", "")}, True),
            ("poles", "RR", {"en": ("Hiking poles", "If you use them, carry them the whole race."), "fr": ("Bâtons de marche", "Si vous les utilisez, portez-les toute la course.")}, False),
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

S = {
    "en": {
        "dir": "races", "title": "{name} mandatory gear list ({short} {dists} km)",
        "desc": "The {name} mandatory gear list for the {dists} km, item by item, with today's best prices on each in your size at Canadian stores.",
        "h1": "{name} mandatory gear list", "sub": "{short} {dists} km · {where} · {when}",
        "dist": "Your distance", "km": "{d} km",
        "M": "Mandatory", "R": "Recommended", "A": "Allowed",
        "have": "I have it", "progress": "You have {h} of {n} mandatory items. Tick what you already own.", "progressAll": "You have every mandatory item. See you at the start.",
        "deals": "On sale now", "dealsSize": "On sale now in your size", "noDeals": "None in stock in your size today. We check every morning.", "few": "Only {n} in {fit} {size} today. We check every morning.",
        "notSold": "The stores we check don't sell this.", "spec": "Check the spec before you buy.",
        "more": "See more on sale →", "moreN": "See all {n}", "shH": "Trail running shoes", "shTag": "Your pick", "shPh": "What do you race in?", "shSize": "Size", "shGone": "Not in stock in size {s} today. We'll tell you when it's back.", "shPickSize": "Pick your size too.", "shPickFit": "Pick Men's or Women's above first.", "shFrom": "{p} in size {s} today", "shPage": "Every size & store", "shNone": "Not in our trail shoe list. Try the brand name.", "shRm": "Remove", "watch": "Watch", "watchOn": "Watching", "watchL": "Watch the price", "wMember": "Watching. We'll email you when it drops in your size.", "wNew": "Watching, on this phone. Add your email and we'll tell you when it drops.", "wPending": "Watching. Confirm your email (check your inbox) to get the drop emails.", "wAdd": "Add my email", "wOff": "Removed from your watchlist.", "sizeH": "Your size", "sizeTxt": "Pick it once to see deals that fit you.",
        "men": "Men's", "women": "Women's", "change": "Change", "off": "off",
        "src": "From the race's official list (last updated by the race {date}). Rules can change: check the {link} before race day.",
        "srcLink": "official list", "srcRead": "From the race's official list (as published when we read it, {date}). Rules can change: check the {link} before race day.", "notAff": "The Gear Fox isn't affiliated with the race.",
        "boxH": "Get gear deals in your size every Friday until race day", "boxTxt": "Free. One email on Friday mornings with the best deals in your sizes. Unsubscribe in one tap.",
        "boxBtn": "Send me the deals", "faqH": "Quick answers",
        "qList": "What is the mandatory gear for the {short} {d} km?", "aList": "{items}.",
        "qJacket": "Is a windbreaker enough for the {name}?", "aJacket": "No. The race asks for a jacket with an attached hood and a waterproof, breathable membrane (on the {dists} km). Windbreakers aren't accepted.",
        "qCup": "Do the {name} aid stations have cups?", "aCup": "No. The aid stations have no cups: bring your own reusable cup.",
        "aisle": "Race gear lists", "money": T["en"]["money"],
    },
    "fr": {
        "dir": "courses", "title": "Matériel obligatoire {de}{name} ({short} {dists} km)",
        "desc": "Le matériel obligatoire {de}{name} pour le {dists} km, article par article, avec les meilleurs prix du jour dans votre taille dans les boutiques canadiennes.",
        "h1": "Matériel obligatoire {de}{name}", "sub": "{short} {dists} km · {where} · {when}",
        "dist": "Votre distance", "km": "{d} km",
        "M": "Obligatoire", "R": "Recommandé", "A": "Permis",
        "have": "Je l'ai", "progress": "Vous avez {h} des {n} articles obligatoires. Cochez ce que vous avez déjà.", "progressAll": "Vous avez tout le matériel obligatoire. On se voit au départ.",
        "deals": "En solde maintenant", "dealsSize": "En solde dans votre taille", "noDeals": "Rien en stock dans votre taille aujourd'hui. On vérifie chaque matin.", "few": "Seulement {n} en {size} {fit} aujourd'hui. On vérifie chaque matin.",
        "notSold": "Les boutiques que nous suivons n'en vendent pas.", "spec": "Vérifiez les caractéristiques avant d'acheter.",
        "more": "Voir plus d'aubaines →", "moreN": "Voir les {n}", "shH": "Chaussures de course en sentier", "shTag": "Votre choix", "shPh": "Vos chaussures de course ?", "shSize": "Pointure", "shGone": "Pas en stock en pointure {s} aujourd'hui. On vous avertit dès son retour.", "shPickSize": "Choisissez aussi votre pointure.", "shPickFit": "Choisissez d'abord Homme ou Femme plus haut.", "shFrom": "{p} en pointure {s} aujourd'hui", "shPage": "Toutes les pointures et boutiques", "shNone": "Pas dans notre liste de chaussures de sentier. Essayez le nom de la marque.", "shRm": "Retirer", "watch": "Suivre", "watchOn": "Suivi", "watchL": "Suivre le prix", "wMember": "Suivi. On vous écrit quand il baisse dans votre taille.", "wNew": "Suivi, sur ce téléphone. Ajoutez votre courriel et on vous avertira quand il baisse.", "wPending": "Suivi. Confirmez votre courriel (voyez votre boîte de réception) pour recevoir les alertes.", "wAdd": "Ajouter mon courriel", "wOff": "Retiré de vos favoris.", "sizeH": "Votre taille", "sizeTxt": "Choisissez-la une fois pour voir les aubaines à votre taille.",
        "men": "Homme", "women": "Femme", "change": "Modifier", "off": "de rabais",
        "src": "Selon la liste officielle de la course (mise à jour par la course le {date}). Les règles peuvent changer : vérifiez la {link} avant la course.",
        "srcLink": "liste officielle", "srcRead": "Selon la liste officielle de la course (telle que publiée quand nous l'avons lue, le {date}). Les règles peuvent changer : vérifiez la {link} avant la course.", "notAff": "The Gear Fox n'est pas affilié à la course.",
        "boxH": "Les aubaines de matériel dans votre taille, chaque vendredi jusqu'à la course", "boxTxt": "Gratuit. Un courriel le vendredi matin avec les meilleures aubaines dans vos tailles. Désabonnement en un clic.",
        "boxBtn": "Envoyez-moi les aubaines", "faqH": "Réponses rapides",
        "qList": "Quel est le matériel obligatoire du {short} {d} km?", "aList": "{items}.",
        "qJacket": "Un coupe-vent suffit-il pour {le}{name}?", "aJacket": "Non. La course demande un manteau avec capuchon attaché et une membrane imperméable et respirante (sur le {dists} km). Les coupe-vent ne sont pas acceptés.",
        "qCup": "Y a-t-il des verres aux ravitaillements {de}{name}?", "aCup": "Non. Les ravitaillements n'ont pas de verres : apportez votre gobelet réutilisable.",
        "aisle": "Listes de matériel de course", "money": T["fr"]["money"],
    },
}

CSS = """
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
.lv.M{background:var(--hivis);color:var(--hivis-ink)}.lv.R{background:var(--mist);color:var(--ink);border:1px solid var(--line)}.lv.A{color:var(--muted);border:1px solid var(--line)}
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
.srcb{font-size:14px;color:var(--muted);margin:16px 0 0}
.gi.shoe{border-color:var(--hivis)}.gi.shoe .shi{flex:none;width:24px;text-align:center;font-size:18px}.lv.Y{background:var(--ink);color:var(--card)}
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
.rsize .cur button{border:0;background:none;padding:0 4px;min-height:0;color:var(--moss);text-decoration:underline;font:600 15px var(--body)}
"""


BAD = re.compile(r"seat ?mast|seat ?post|\bbiogel\b", re.I)   # bike parts still in today's data (scrape.py NOT_RUNNING drops them from Oct 21)


def pool(items, kind, stores):
    """Race gear for one line of the list, full price too (people watch it for a drop): trail gear first, then how many stores
    carry it (the best popularity signal we have), then a sale."""
    k = KINDS[kind.rstrip("2")]
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
        if not (b in BRANDS[kind.rstrip("2")] or (b in MAYBE and (kind in ("water", "cup", "food") or RUN.search(n)))):
            continue
        fit = bool(good.search(n))
        sz = [e for e in d["sz"] if e[1]]
        if not sz or (d["g"] != "nutrition" and max(e[1] for e in sz) > 2.5 * min(e[1] for e in sz)):
            continue                                       # sizes 2.5x apart in price: another product's sizes mixed in (Decathlon, Oct 20)
        best = min(sz, key=lambda e: e[1])
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


SIZED_G = {"tops", "bottoms", "gloves", "headwear"}
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


def page(slug, race, L, items, stores, pages=None):
    s, other = S[L], "fr" if L == "en" else "en"
    dists = "/".join(race["dists"])
    fmt = dict(name=race["name"], short=race["short"], dists=dists, where=race["where"][L], when=race["when"][L],
               de=race.get("de", "de l'"), le=race.get("le", "l'"))
    path = {"en": f"/races/{slug}/", "fr": f"/courses/{slug}/"}
    head = page_head(T[L], s["title"].format(**fmt), s["desc"].format(**fmt), path["en"], path["fr"], f"<style>{CSS}</style>")
    pools, rows, shown = {}, [], set()
    for kind, lv, txt, spec in race["items"]:
        title, note = txt[L]
        sold = kind.rstrip("2") in KINDS
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
        rows.append(f'<li class="gi{"" if sold else " mini"}" data-k="{kind}"{lvs}{"" if first else " hidden"}><div class="hd">'
                    f'<input type="checkbox" class="have" aria-label="{esc(s["have"])}: {esc(title)}"><h3>{esc(title)}</h3>'
                    f'<span class="lv {first or "R"}">{s.get(first, "")}</span></div>'
                    + (f'<p class="note">{esc(note)}</p>' if note else "") + f'{deals}</li>')
    # quick answers from the race's own table
    faq = []
    for i, d in enumerate(race["dists"]):
        must = [txt[L][0] for kind, lv, txt, _ in race["items"] if lv[i] == "M"]
        faq.append((s["qList"].format(d=d, **fmt), s["aList"].format(items=", ".join(must))))
    if race.get("faq_jacket"):        # Harricana: "windbreakers will not be accepted"
        faq.append((s["qJacket"].format(**fmt), s["aJacket"].format(**{**fmt, "dists": "/".join(d for i, d in enumerate(race["dists"]) if dict((k, lv) for k, lv, *_ in race["items"])["jacket"][i] == "M")})))
    if race.get("cupless"):           # the race says its aid stations have no cups
        faq.append((s["qCup"].format(**fmt), s["aCup"]))
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    src = race.get("src_fr") if L == "fr" and race.get("src_fr") else race["src"]
    # Oct 20 (Bastien: "put it in the checklist as trail runners, choose your shoe"): the first line of the list, every distance
    every = "".join(f' data-l{d}="Y"' for d in race["dists"])
    shoe_row = (f'<li class="gi shoe" id="shoeBox" data-k="shoes"{every} data-root="" data-dir="{T[L]["dir"]}" '
                f'data-pickfit="{esc(s["shPickFit"])}" data-from="{esc(s["shFrom"])}" data-page="{esc(s["shPage"])}" data-none="{esc(s["shNone"])}" data-rm="{esc(s["shRm"])}" data-gone="{esc(s["shGone"])}" data-picksize="{esc(s["shPickSize"])}">'
                f'<div class="hd"><span class="shi" aria-hidden="true">👟</span><h3>{s["shH"]}</h3><span class="lv Y">{s["shTag"]}</span></div>'
                f'<div class="shrow"><input type="search" id="shoeQ" autocomplete="off" enterkeyhint="search" placeholder="{esc(s["shPh"])}" aria-label="{esc(s["shH"])}">'
                f'<select id="shoeSz" aria-label="{esc(s["shSize"])}" data-ph="{esc(s["shSize"])}"></select></div>'
                f'<ul class="sugg" id="shoeSug" role="listbox"></ul><ul class="mine2" id="shoeMine"></ul></li>')
    pj = json.dumps(pools, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    sj = json.dumps(trail_shoes(items, pages), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = f"""<p class="crumbs"><a href="{T[L]['home']}">The Gear Fox</a> › {s['aisle']}</p>
<h1>{esc(s['h1'].format(**fmt))}</h1>
<p class="sub">{esc(s['sub'].format(**fmt))}</p>
<section class="rsize" id="rsize" data-men="{s['men']}" data-women="{s['women']}" data-change="{s['change']}"><p><b>{s['sizeH']}</b> · {s['sizeTxt']}</p>
<div class="row" data-f>{"".join(f'<button type="button" data-g="{g}">{s[g]}</button>' for g in ("men", "women"))}</div>
<p class="cur"><b>{s['sizeH']}:</b> <span></span> <button type="button" data-chg>{s['change']}</button></p>
<div class="row" data-s style="margin-top:6px">{"".join(f'<button type="button" data-s="{z}">{z}</button>' for z in ("XS", "S", "M", "L", "XL", "2XL"))}</div></section>
<p class="lbl">{s['dist']}</p>
<div class="dists" role="group" aria-label="{s['dist']}">{"".join(f'<button type="button" data-d="{d}" aria-pressed="{str(d == race["default"]).lower()}">{s["km"].format(d=d)}</button>' for d in race["dists"])}</div>
<p class="prog" id="prog" data-t="{esc(s['progress'])}" data-all="{esc(s['progressAll'])}"></p>
<ul class="gl" id="gl" data-race="{slug}" data-default="{race['default']}" data-lm="{s['M']}" data-lr="{s['R']}" data-la="{s['A']}"
 data-home="{T[L]['home']}" data-watch="{esc(s['watch'])}" data-won="{esc(s['watchOn'])}" data-wmember="{esc(s['wMember'])}" data-wnew="{esc(s['wNew'])}" data-wpending="{esc(s['wPending'])}" data-wadd="{esc(s['wAdd'])}" data-woff="{esc(s['wOff'])}" data-moren="{esc(s['moreN'])}" data-dh="{esc(s['deals'])}" data-dhs="{esc(s['dealsSize'])}" data-none="{esc(s['noDeals'])}" data-few="{esc(s['few'])}" data-off="{esc(s['off'])}" data-ly="{esc(s['shTag'])}">{shoe_row}{"".join(rows)}</ul>
<p class="srcb">{(s['src'] if race.get('updated') else s['srcRead']).format(date=(race.get('updated') or race['read'])[L], link=f'<a href="{src}" rel="noopener">{s["srcLink"]}</a>')} {s['notAff']}</p>
<section class="alert" id="raceBox" data-ref="race-{slug}" data-bad="{esc(T[L]['alertBad'])}" data-ok="{esc(T[L]['alertOk'])}" data-fail="{esc(T[L]['alertFail'])}" data-pick="{esc(s['sizeTxt'])}">
<h2>{esc(s['boxH'])}</h2><p class="fine">{esc(s['boxTxt'])}</p><form novalidate><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(T[L]['emailPh'])}" aria-label="Email" required><button type="submit">{esc(s['boxBtn'])}</button></form><p class="msg" aria-live="polite"></p></section>
<section class="faq"><h2>{s['faqH']}</h2>{"".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</section>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script id="pools" type="application/json">{pj}</script>
<script id="shoes" type="application/json">{sj}</script>
"""
    return head + body + SCRIPT.replace("$LANG", L).replace("$CUR", "CAD") + page_foot(T[L]).replace('"shoe-page"', '"race-page"').replace("|shoes||shoe-page", "|gear||race-page")


# picks the deals in the visitor's fit and clothing size, remembers the distance and the ticks (this browser only)
SCRIPT = r"""<script>
(function(){var gl=document.getElementById("gl"),race=gl.dataset.race,fr="$LANG"==="fr";
var get=function(k){try{return JSON.parse(localStorage.getItem(k)||"null")}catch(e){return null}},put=function(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
var pools={};try{pools=JSON.parse(document.getElementById("pools").textContent)}catch(e){}
var st=get("gf-race-"+race)||{},have=st.have||{},dist=st.d||gl.dataset.default;
var prof=get("rd-profile"),rs=get("gf-race-size");
var fit=(rs&&rs.g)||(prof&&prof.gender!=="any"&&prof.gender)||"",size=(rs&&rs.s)||(prof&&prof.sizes&&prof.sizes.tops&&(prof.sizes.tops.sizes||[])[0])||"";
var nm=function(n){return fr?n.replace(/Women[’']s\b/g,"Femme").replace(/Men[’']s\b/g,"Homme").replace(/\bUnisex\b/g,"Unisexe"):n};
var money=function(v){return fr?v.toFixed(2).replace(".",",")+" $":"$"+v.toFixed(2)};
var esc=function(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})};
var ALIAS={"XXS":"2XS","XXL":"2XL","X-SMALL":"XS","SMALL":"S","MEDIUM":"M","LARGE":"L","X-LARGE":"XL","EXTRA LARGE":"XL","XX-SMALL":"2XS"};
var norm=function(z){z=String(z).toUpperCase().trim();return ALIAS[z]||z};
var fits=function(lab){if(!size)return true;var l=norm(lab);if(l==="OS"||l==="OSFA"||l==="OSZ")return true;
  return l.split(/\s*[\/|]\s*/).map(norm).indexOf(size)>=0};
var SIZED={tops:1,bottoms:1,gloves:1,headwear:1},SHOWN={};
function render(){
  [].forEach.call(document.querySelectorAll(".dists button"),function(b){b.setAttribute("aria-pressed",String(b.dataset.d===dist))});
  var n=0,h=0;
  var R={Y:-1,M:0,R:1,A:2};
  [].forEach.call(gl.children,function(li){var lv=li.getAttribute("data-l"+dist)||"",k=li.dataset.k;li.hidden=!lv;
    li.style.order=2*(R[lv]||0)+(li.classList.contains("mini")?1:0);   // what's mandatory for this distance first; the small stuff after
    var tag=li.querySelector(".lv");tag.className="lv "+lv;tag.textContent=lv==="Y"?gl.dataset.ly:lv==="M"?gl.dataset.lm:lv==="R"?gl.dataset.lr:lv==="A"?gl.dataset.la:"";
    if(k==="shoes")return;   // the shoe line: no tick, not counted
    var got=!!have[k];li.classList.toggle("got",got);li.querySelector("input.have").checked=got;
    if(lv==="M"){n++;if(got)h++}
    var p=pools[k];if(!p||(!fit&&!size))return;
    var ok=[];for(var i=0;i<p.length;i++){var r=p[i];
      if(fit&&r.sx.length&&r.sx.indexOf(fit)<0)continue;
      var s=SIZED[r.g]?r.s.filter(function(e){return fits(e[0])}):r.s;if(!s.length)continue;
      ok.push([r,s.reduce(function(a,b){return b[1]<a[1]?b:a})])}
    if(k==="headlamp2"){var up=(SHOWN.headlamp||[]);ok=ok.filter(function(x){return up.indexOf(x[0].n)<0})}
    var seen={},all=ok.filter(function(x){var b=x[0].b.toLowerCase(),n=!seen[b];seen[b]=1;return n}).concat(ok).filter(function(x,i,a){return a.indexOf(x)===i});   // one per brand first
    var sale=function(x){return x[1][2]>x[1][1]*1.01},picks=all.slice(0,10),more=all.slice(10).filter(sale);   // same rule as picks() in race_pages.py
    while(picks.filter(sale).length<3&&more.length){var i=-1;picks.forEach(function(x,j){if(!sale(x))i=j});if(i<0)break;picks[i]=more.shift()}
    if(!picks.slice(0,3).some(sale)&&picks.some(sale)){var j=picks.findIndex(sale);picks.splice(2,0,picks.splice(j,1)[0])}
    var ul=li.querySelector(".dl"),none=li.querySelector(".none"),mb=li.querySelector(".mored");
    ul.hidden=!picks.length;none.hidden=!!picks.length;mb.hidden=picks.length<=3;mb.textContent=mb.dataset.n.replace("{n}",picks.length);
    var few=li.querySelector(".few");if(!few){few=document.createElement("span");few.className="few";mb.after(few)}   // Oct 20: fewer than 10 in this size = say so
    few.hidden=!(picks.length&&picks.length<10&&SIZED[p[0].g]&&size);few.textContent=gl.dataset.few.replace("{n}",picks.length).replace("{fit}",(fit?document.getElementById("rsize").dataset[fit]:"")).replace("{size}",size);
    SHOWN[k]=picks.slice(0,3).map(function(x){return x[0].n});if(!picks.length)return;
    ul.innerHTML=picks.map(function(x){var r=x[0],e=x[1];
      var pr=e[2]>e[1]*1.01?'<b>'+money(e[1])+'</b><s>'+money(e[2])+'</s> <span class="off">−'+Math.round(100*(1-e[1]/e[2]))+'%</span>':'<b>'+money(e[1])+'</b>',h=gl.dataset.home;
      return '<li><a class="dg" href="'+esc(e[3])+'" data-store="'+esc(r.h)+'" target="_blank" rel="noopener"><img src="'+esc(r.img)+'" alt="" loading="lazy" referrerpolicy="no-referrer"><span class="nm"><b>'+esc(r.b)+'</b>'+esc(nm(r.n))+'<small>'+esc(r.st)+(SIZED[r.g]&&size?" · "+esc(e[0]):"")+'</small></span><span class="pr">'+pr+'</span></a><button type="button" class="wt" data-k="'+esc(r.k)+'" data-p="'+e[1]+'" data-u="'+esc(e[3])+'" aria-pressed="false" aria-label="'+esc(gl.dataset.watch)+': '+esc(r.b+" "+r.n)+'"><span class="hh">♡</span><span class="wl"> '+esc(gl.dataset.watch)+'</span></button></li>'}).join("")});
  var pg=document.getElementById("prog");pg.textContent=n&&h>=n?pg.dataset.all:pg.dataset.t.replace("{h}",h).replace("{n}",n);
  var box=document.getElementById("rsize");box.classList.toggle("set",!!(fit&&size)&&!box.dataset.open);
  box.querySelector(".cur span").textContent=(fit?box.dataset[fit]:"")+" · "+size;[].forEach.call(box.querySelectorAll("[data-g]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.g===fit))});
  [].forEach.call(box.querySelectorAll("button[data-s]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.s===size))});
}
document.querySelector(".dists").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;dist=b.dataset.d;st.d=dist;put("gf-race-"+race,st);render()});
gl.addEventListener("change",function(e){var li=e.target.closest(".gi");if(!li||!e.target.classList.contains("have"))return;have[li.dataset.k]=e.target.checked;st.have=have;put("gf-race-"+race,st);render()});
gl.addEventListener("click",function(e){var b=e.target.closest(".mored");if(b)b.closest(".gi").classList.add("open")});
document.getElementById("rsize").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;
  if(b.hasAttribute("data-chg")){this.dataset.open="1";render();return}if(b.dataset.s&&fit)delete this.dataset.open;
  if(b.dataset.g)fit=b.dataset.g;if(b.dataset.s)size=b.dataset.s;put("gf-race-size",{g:fit,s:size});render()});
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
ssel.addEventListener("change",function(){if(ssel.value)put("gf-shoe-size",{g:fit||"men",s:ssel.value});shoeMine()});
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
    p={lang:fr?"fr":"en",country:"ca",tz:tz,name:"",gender:fit,terrain:"trail",ships:"ca",groups:G,sizes:sz,brands:[],activities:[]}}
  ["tops","bottoms"].forEach(function(k){if(!(p.sizes[k]&&(p.sizes[k].sizes||[]).length))p.sizes[k]={sizes:[size]}});
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
           "go": "Mandatory gear list →", "dists": "{d} km"},
    "fr": {"title": "Listes de matériel de course : le matériel obligatoire, article par article", "h1": "Listes de matériel de course",
           "desc": "Le matériel obligatoire des courses en sentier et des ultras, article par article, avec les meilleurs prix du jour dans votre taille.",
           "intro": "Le matériel obligatoire de chaque course, tel que publié par la course, avec les meilleurs prix du jour dans votre taille. D'autres courses s'en viennent.",
           "go": "Liste du matériel obligatoire →", "dists": "{d} km"},
}


def hub(L):
    """/races/ + /courses/ (Oct 21, Bastien: a ☰ menu item "even if it's one; we will add more soon")."""
    h = HUB[L]
    rows = "".join(f'<li><a href="/{S[L]["dir"]}/{slug}/"><span class="nm"><b>{esc(r["name"])}</b>'
                   f'<small>{esc(r["where"][L])} · {esc(r["when"][L])} · {h["dists"].format(d="/".join(r["dists"]))}</small></span>'
                   f'<span class="pr">{h["go"]}</span></a></li>' for slug, r in RACES.items())
    return (page_head(T[L], h["title"], h["desc"], "/races/", "/courses/")
            + f'<p class="crumbs"><a href="{T[L]["home"]}">The Gear Fox</a></p><h1>{esc(h["h1"])}</h1><p class="sub">{esc(h["intro"])}</p>'
            + f'<ul class="cards">{rows}</ul>' + page_foot(T[L]))


def add_to_sitemap(site):
    """shoe_pages.py writes sitemap.xml earlier in the refresh; the race pages join it (never twice)."""
    p = site / "sitemap.xml"
    if not p.exists():
        return
    x = p.read_text()
    urls = ["/races/", "/courses/"] + [f"/{S[L]['dir']}/{slug}/" for slug in RACES for L in ("en", "fr")]
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
    for L in ("en", "fr"):
        (site / S[L]["dir"]).mkdir(parents=True, exist_ok=True)
        (site / S[L]["dir"] / "index.html").write_text(hub(L))
    add_to_sitemap(site)


if __name__ == "__main__":
    main()
