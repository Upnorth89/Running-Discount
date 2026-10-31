#!/usr/bin/env python3
"""Trail gear list pages (Oct 25, 2026; Bastien's idea Oct 24, OK'd Oct 25: "tell us where they are going and for how long, then we
can show a list of the 10 essentials or more gear dependant on the area").

One page per hike in scraper/hikes.py: what to bring for that trail and that trip length (the 10 essentials, then what the trail adds:
bears, wet coast, snow early and late season, river fords, tides, permits), each line with today's hiking deals in the visitor's size,
an "I have it" tick and ♡ Watch, like the race gear lists (race_pages.py: same size box, script and sign-up box).
/hikes/<slug>/ + /randonnees/<slug>/ (Canadian stores) and /us/hikes/<slug>/ (US stores), hubs /hikes/ /randonnees/ /us/hikes/.

Rule (no claims we can't back up): a hike's distance and climb show only once `checked` (re-read on the park's own page); the
others are built for the preview but left out of the live site and the sitemap (ONLY_CHECKED).

Usage: python scraper/hike_pages.py SITE_DIR [--all]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hikes as HK                                                            # noqa: E402
import race_pages as RP                                                       # noqa: E402
from shoe_pages import T, US, _H, esc, page_head, page_foot, store_names, size_url, host   # noqa: E402

POOL, SHOW = 60, 10
MONTHS = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
          "fr": "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()}
REGION = {"BC": "British Columbia", "AB": "Alberta", "ON": "Ontario", "QC": "Québec", "YT": "Yukon", "NL": "Newfoundland and Labrador",
          "NS": "Nova Scotia", "NB": "New Brunswick", "PE": "Prince Edward Island", "MB": "Manitoba", "SK": "Saskatchewan", "NT": "Northwest Territories",
          "NU": "Nunavut", "CA": "California", "WA": "Washington", "OR": "Oregon", "UT": "Utah", "CO": "Colorado", "AZ": "Arizona", "WY": "Wyoming",
          "MT": "Montana", "ID": "Idaho", "NV": "Nevada", "NM": "New Mexico", "AK": "Alaska", "HI": "Hawaii", "TN": "Tennessee", "NC": "North Carolina",
          "VA": "Virginia", "NH": "New Hampshire", "VT": "Vermont", "ME": "Maine", "NY": "New York", "MN": "Minnesota", "MI": "Michigan", "WI": "Wisconsin",
          "GA": "Georgia", "PA": "Pennsylvania"}
REGION_FR = {"BC": "Colombie-Britannique", "NL": "Terre-Neuve-et-Labrador", "NS": "Nouvelle-Écosse", "NB": "Nouveau-Brunswick",
             "PE": "Île-du-Prince-Édouard", "NT": "Territoires du Nord-Ouest", "CA": "Californie", "OR": "Oregon", "NM": "Nouveau-Mexique",
             "NC": "Caroline du Nord", "VA": "Virginie", "PA": "Pennsylvanie", "GA": "Géorgie"}

S = {
    "en": dict(dir="hikes", title="{name} gear list: what to bring", h1="{name}: what to bring",
               desc="What to bring for {name} ({where}): the 10 essentials and what this trail adds, with today's best prices in your size at Canadian stores.",
               trip="Your trip", day="Day hike", nights="{n} nights", night1="1 night",
               Y="Essential", M="Required", R="Recommended",
               progress="You have {h} of {n} must-bring items. Tick what you already own.", progressAll="You have everything you must bring. Have a great hike.",
               facts_rt="{km} km round trip", facts_ow="{km} km one way", climb="{m} m climb", best="Best {m}", days1="Usually a day", daysN="Usually {n} days",
               bears={"grizzly": "Grizzly and black bear country", "black": "Black bear country", "none": ""},
               flag={"permit": "Permit or reservation needed", "canister": "Bear canister required overnight", "tide": "Tide-dependent sections",
                     "ford": "Unbridged river crossings", "snow": "Snow early and late in the season", "altitude": "High altitude",
                     "exposure": "Exposed sections", "scramble": "Scrambling", "lightning": "Afternoon thunderstorms",
                     "water-scarce": "Little water on the trail", "navigation": "Unmarked sections", "bugs": "Black flies and mosquitoes in early summer",
                     "heat": "Hot and exposed", "huts": "Huts or refuges", "cold-water": "Cold water", "oneway": ""},
               src="Distance from {park}'s page ({link}), checked {date}. Trails change: check the park's page and conditions before you go.",
               srcLink="park page", notAff="The Gear Fox isn't affiliated with the park.",
               boxH="Get hiking deals in your size every Friday", boxTxt="Free. One email on Friday mornings with the best hiking deals in your sizes. Unsubscribe in one tap.",
               qBring="What should I bring for {name}?", aBring="The 10 essentials ({ess}), plus for this trail: {adds}.",
               qPermit="Do I need a permit for {name}?", aPermit="Usually, yes: {park} manages permits or reservations for this area (dates, quotas or parking). Check its page for your dates before you go.",
               qBears="Are there bears on {name}?", aBears={"grizzly": "Yes, grizzly and black bears. Carry bear spray where you can reach it in seconds.",
                                                         "black": "Yes, black bears. Carry bear spray and store food away from your tent overnight."},
               aisle="Trail gear lists", bootH="Boot size",
               hubTitle="Trail gear lists: what to bring for {n} hikes", hubH1="Trail gear lists",
               hubDesc="What to bring for popular hikes in Canada and the US: the 10 essentials and what each trail adds, with today's best prices in your size.",
               hubIntro="Pick your trail: the 10 essentials and what that trail adds (bears, rain, snow, river crossings), with today's deals in your size.",
               hubGo="What to bring →", groups={"ca": "Canada", "us": "United States"},
               otherSide="Shopping in the US? This list with US stores →"),
    "fr": dict(dir="randonnees", title="{name} : quoi apporter", h1="{name} : quoi apporter",
               desc="Quoi apporter pour {name} ({where}) : les 10 essentiels et ce que ce sentier ajoute, avec les meilleurs prix du jour dans votre taille.",
               trip="Votre sortie", day="Randonnée d'un jour", nights="{n} nuits", night1="1 nuit",
               Y="Essentiel", M="Exigé", R="Recommandé",
               progress="Vous avez {h} des {n} articles à apporter. Cochez ce que vous avez déjà.", progressAll="Vous avez tout ce qu'il faut apporter. Bonne randonnée.",
               facts_rt="{km} km aller-retour", facts_ow="{km} km aller simple", climb="{m} m de dénivelé", best="Meilleurs mois : {m}", days1="Habituellement une journée",
               daysN="Habituellement {n} jours",
               bears={"grizzly": "Territoire du grizzli et de l'ours noir", "black": "Territoire de l'ours noir", "none": ""},
               flag={"permit": "Permis ou réservation requis", "canister": "Contenant anti-ours exigé la nuit", "tide": "Passages selon la marée",
                     "ford": "Rivières à traverser sans pont", "snow": "Neige en début et fin de saison", "altitude": "Haute altitude",
                     "exposure": "Passages exposés", "scramble": "Passages d'escalade facile", "lightning": "Orages d'après-midi",
                     "water-scarce": "Peu d'eau sur le sentier", "navigation": "Sections non balisées", "bugs": "Mouches noires et moustiques au début de l'été",
                     "heat": "Chaud et à découvert", "huts": "Refuges", "cold-water": "Eau froide", "oneway": ""},
               src="Distance selon la page de {park} ({link}), vérifiée le {date}. Les sentiers changent : vérifiez la page du parc et les conditions avant de partir.",
               srcLink="page du parc", notAff="The Gear Fox n'est pas affilié au parc.",
               boxH="Les aubaines de randonnée dans votre taille, chaque vendredi", boxTxt="Gratuit. Un courriel le vendredi matin avec les meilleures aubaines de randonnée dans vos tailles. Désabonnement en un clic.",
               qBring="Quoi apporter pour {name}?", aBring="Les 10 essentiels ({ess}), plus pour ce sentier : {adds}.",
               qPermit="Faut-il un permis pour {name}?", aPermit="Habituellement, oui : {park} gère les permis ou réservations de ce secteur (dates, quotas ou stationnement). Vérifiez sa page pour vos dates avant de partir.",
               qBears="Y a-t-il des ours sur {name}?", aBears={"grizzly": "Oui, des grizzlis et des ours noirs. Gardez le chasse-ours en aérosol à portée de main.",
                                                            "black": "Oui, des ours noirs. Apportez du chasse-ours en aérosol et rangez la nourriture loin de la tente la nuit."},
               aisle="Listes de matériel de randonnée", bootH="Pointure",
               hubTitle="Listes de matériel de randonnée : quoi apporter pour {n} randonnées", hubH1="Listes de matériel de randonnée",
               hubDesc="Quoi apporter pour les randonnées populaires au Canada et aux États-Unis : les 10 essentiels et ce que chaque sentier ajoute, avec les aubaines du jour dans votre taille.",
               hubIntro="Choisissez votre sentier : les 10 essentiels et ce que ce sentier ajoute (ours, pluie, neige, rivières), avec les aubaines du jour dans votre taille.",
               hubGo="Quoi apporter →", groups={"ca": "Canada", "us": "États-Unis"},
               otherSide="Vous magasinez aux États-Unis ? Cette liste avec les boutiques américaines →"),
}
S["us"] = dict(S["en"], dir="us/hikes", desc="What to bring for {name} ({where}): the 10 essentials and what this trail adds, with today's best prices in your size at US stores.",
               otherSide="Shopping in Canada? This list with Canadian stores →")
# Oct 26 (Bastien: "include formula for calories per day consumed depending on hours hiked and weight on back"): the food box.
# Oct 26 (Bastien: "switch to most accurate and up to date formula"): the US Army's Load Carriage Decision Aid (LCDA; Looney et al.,
# Med Sci Sports Exerc 2022;54(4):646, eq. 4), which beat Pandolf (1977) on the same data (bias 0.01 vs -0.44 W/kg):
#   W/kg = M_rest + [0.19 + n*1.78*S^0.58 + 0.27*S^4 + M_grade] * (1 + 1.96*(L/W)^1.36)
#   M_grade = 0.34*S*G*(1 - 1.05^(1 - 1.1^(G+32)))   (Looney 2019, MSSE 51(9):1954; G in %, works downhill too)
# S m/s, L pack kg, W body kg, n terrain (1.2 = trail); M_rest = Cunningham RMR (500 + 22*lean kg kcal/day, lean ~ 80% of weight).
# Half the walking time climbing at the trail's average grade (total climb over half the distance), half coming down at it; the rest
# of the day at 1.2 x resting (sleep + camp chores).
FUEL = {
    "en": dict(fu_fuelH="Calories and food for this trip", fu_fuelTxt="Your numbers stay on this device.", fu_body="Your weight", fu_pack="Pack weight",
               fu_hours="Hours of walking a day", fu_climb="Total climb", fu_kg="kg", fu_lb="lb", fu_m="m", fu_ft="ft", fu_units="Weight in",
               fu_trail="On the trail: about {k} kcal a day ({h} kcal an hour).",
               fu_day="Whole day, camp included: about {k} kcal.",
               fu_food="Food to carry: about {f} a day of dense trail food (about 4,400 kcal per kg), {t} for the trip.",
               fu_snack="Snacks for the day: {a}–{b} kcal (a common guideline: 200–300 kcal for each hour on the trail).",
               fu_fine="An estimate from the US Army's Load Carriage Decision Aid (Looney et al., 2022), on trail, with half the walking up and half down this trail's average grade, plus your resting burn for the rest of the day. Cold, snow, a fast pace or a heavier pack mean more.",
               fu_noclimb="This park doesn't publish the climb: add it for a better estimate.",
               fu_gpx="Hiking your own route? Load its GPX file (AllTrails, Gaia GPS, Strava and Garmin all export one)",
               fu_gpxOk="Your route: {km} km, {m} m of climb.", fu_gpxBad="We couldn't read that file. Try a GPX export."),
    "fr": dict(fu_fuelH="Calories et nourriture pour cette sortie", fu_fuelTxt="Vos chiffres restent sur cet appareil.", fu_body="Votre poids", fu_pack="Poids du sac",
               fu_hours="Heures de marche par jour", fu_climb="Dénivelé total", fu_kg="kg", fu_lb="lb", fu_m="m", fu_ft="pi", fu_units="Poids en",
               fu_trail="En sentier : environ {k} kcal par jour ({h} kcal à l'heure).",
               fu_day="Journée complète, camp compris : environ {k} kcal.",
               fu_food="Nourriture à apporter : environ {f} par jour d'aliments denses (environ 4 400 kcal par kg), {t} pour la sortie.",
               fu_snack="Collations pour la journée : {a} à {b} kcal (repère courant : 200 à 300 kcal par heure de marche).",
               fu_fine="Estimation tirée du modèle de l'armée américaine sur la marche avec charge (Load Carriage Decision Aid, Looney et coll., 2022), en sentier, la moitié de la marche en montée et l'autre en descente selon la pente moyenne du sentier, plus votre dépense au repos pour le reste de la journée. Le froid, la neige, un rythme rapide ou un sac plus lourd en demandent plus.",
               fu_noclimb="Ce parc ne publie pas le dénivelé : ajoutez-le pour une meilleure estimation.",
               fu_gpx="Votre propre itinéraire ? Chargez son fichier GPX (AllTrails, Gaia GPS, Strava et Garmin en exportent tous un)",
               fu_gpxOk="Votre itinéraire : {km} km, {m} m de dénivelé.", fu_gpxBad="Impossible de lire ce fichier. Essayez un export GPX."),
}
FUEL["us"] = FUEL["en"]
for L in S:   # the race pages' size box, watch and sign-up words
    S[L] = dict(RP.S[L], **FUEL[L], **S[L])


def where(h, L):
    r = (REGION_FR.get(h["region"]) if L == "fr" else None) or REGION.get(h["region"], h["region"])
    return f'{h["park"]}, {r}'


def trips(h):
    """The trip lengths offered: a day (when the trail fits in one), one night, and the usual length."""
    out = []
    if h["kind"] == "day" or h["km"] <= 30:
        out.append(1)
    if h["kind"] != "day":
        out.append(2 if h["kind"] == "overnight" else max(2, h["days"]))
        if h["kind"] in ("multi", "thru") and h["days"] > 3:
            out.append(2)
    return sorted(set(out))


def tlab(d, L):
    s = S[L]
    return s["day"] if d == 1 else s["night1"] if d == 2 else s["nights"].format(n=d - 1)


LEVEL = {"essential": "Y", "required": "M", "recommended": "R"}


def gear_rows(h):
    """Every line for any of the trip lengths, with its level per length (absent = not on that trip)."""
    ts, rows = trips(h), {}
    for t in ts:
        for x in HK.gear_for(h, t):
            r = rows.setdefault(x["key"], dict(x, lv={}))
            r["lv"][t] = LEVEL[x["level"]]
    return ts, list(rows.values())


_POOLS = {}
# what a pick's name must say for each line (a category alone isn't enough: Garmin watches are "safety" gear, Oct 25)
NEED = {"nav": r"\bmap\b|compass|\bgps\b|altimeter", "light": r"headlamp|head ?lamp|frontale|lantern|\blamp\b",
        "sun": r"sunglass|lunette|\bsun\b|sunscreen|\buv\b|brim|bucket|sahara|boonie|safari", "firstaid": r"first.?aid|medical|med kit|trousse|blister",
        "shelter": r"bivy|bivvy|bivi\b|space blanket|emergency (blanket|shelter|bag|tent|bivy)|survival (blanket|bag|shelter)|\btarp\b", "water": r"bottle|flask|filter|purif|reservoir|bladder|hydration|bouteille|gourde|filtre",
        "bearspray": r"bear (spray|deterrent|attack)|counter ?assault|\budap\b|frontiersman|chasse-ours", "messenger": r"inreach|messenger|\bspot\b|satellite|zoleo|beacon", "traction": r"spike|crampon|traction|yaktrax|microspike",
        "gaiters": r"gaiter|gu[êe]tre", "socks": r"wool|merino|laine", "poles": r"pole|b[âa]ton", "toque": r"toque|tuque|beanie|glove|mitt|\bgants?\b|bonnet",
        "gpsdevice": r"\bgps\b|inreach|etrex|\bmap\b", "water3": r"bottle|flask|filter|reservoir|bladder|hydration|bouteille|gourde"}
NOT = re.compile(r"\bwatch\b|montre|fenix|forerunner|epix|instinct|enduro|coros|suunto|\bpolar\b|\bbook|\bpress\b|\bpub\b|edition|guide|"
                 r"\bbell\b|\bbelt\b|whistle|golf|stool|chair|\bshorts?\b|\bpants?\b|\bjacket\b|\bshirt\b", re.I)
PACK_BITS = re.compile(r"\bcup\b|\d-pack|valve|sheath|rain ?cover|strap|bladder|reservoir|hip ?belt|pouch|organi[sz]er|\bcase\b", re.I)


def hike_pool(items, shop, stores, us, need=None):
    """Hiking deals for one line: its group (and type), full price too, a photo, sold on this side; most-carried + on sale first.
    The same line on 100 hikes asks for the same pool: built once per side and line."""
    key = (id(items), tuple(shop), need)
    if key not in _POOLS:
        _POOLS[key] = _pool(items, shop, stores, re.compile(need, re.I) if need else None)
    return _POOLS[key]


def _pool(items, shop, stores, need):
    g, t = shop
    out = []
    for d in items:
        if d["g"] != g or (t and d.get("t") != t) or not d.get("img") or (d.get("ca") is False):
            continue
        if (need and not need.search(d["n"])) or (g == "gear" and NOT.search(d["n"] + " " + d["b"])) or (g == "packs" and PACK_BITS.search(d["n"])):
            continue
        sz = [e for e in d["sz"] if e[1] and not str(e[0]).endswith("~N")]
        if not sz or (max(e[1] for e in sz) > 2.5 * min(e[1] for e in sz)):
            continue
        best = min(sz, key=lambda e: e[1])
        reg = max(best[3] or best[1], best[1]) if len(best) > 3 else best[1]
        pct = round(100 * (1 - best[1] / reg)) if reg > best[1] * 1.01 else 0
        u = size_url(d, best)
        nst = len({host(x) for x in d.get("of") or [] if x})
        out.append({"b": d["b"], "n": d["n"], "img": d["img"], "sx": d.get("sx") or [], "g": d["g"],
                    "k": f'{d["b"]}|{d["n"]}|{d["g"]}|{1 if d.get("w") else 0}'.lower(),
                    "s": [[e[0], e[1], max(e[3] or e[1], e[1]) if len(e) > 3 else e[1], size_url(d, e)] for e in sz],
                    "st": stores.get(host(u), [host(u)])[0], "h": host(u), "_s": min(nst, 5) * 6 + pct * 0.4 + min(len(sz), 6)})
    out.sort(key=lambda r: -r["_s"])
    for r in out:
        del r["_s"]
    return out[:POOL]


def months(h, L):
    m = h["months"]
    return f'{MONTHS[L][m[0] - 1]}–{MONTHS[L][m[-1] - 1]}' if len(m) > 1 else MONTHS[L][m[0] - 1]


def facts(h, L):
    s = S[L]
    km = f'{h["km"]:g}'.replace(".", "," if L == "fr" else ".")
    out = [(s["facts_ow"] if "oneway" in h["flags"] else s["facts_rt"]).format(km=km)]
    if h.get("gain_ok") or not h.get("checked"):      # a climb only when the park's page gives one (preview: our estimate)
        out.append(s["climb"].format(m=f'{h["gain_m"]:,}'.replace(",", " " if L == "fr" else ",")))
    out.append(s["days1"] if h["days"] <= 1 else s["daysN"].format(n=h["days"]))
    out.append(s["best"].format(m=months(h, L)))
    return " · ".join(out)



def HL(L):
    """Hiking strings for the page header/menu (boot prices + trail gear lists, hiking home), like the boot pages."""
    d = dict(US if L == "us" else T[L]); d.update(_H["en"] if L == "us" else {}); d.update(_H[L]); d["hike"] = True
    return d


def page(h, L, items, stores, checked_on):
    s, Tl = S[L], (US if L == "us" else T[L])
    slug, LL = h["slug"], ("en" if L == "us" else L)
    fmt = dict(name=h["name"], where=where(h, LL))
    own = f'/{s["dir"]}/{slug}/'
    if L == "us":
        head = page_head(HL("us"), s["title"].format(**fmt), s["desc"].format(**fmt), own, "", f"<style>{RP.CSS}{FUEL_CSS}</style>").replace('class="sw" href="/shoes/"', f'class="sw" href="/hikes/{slug}/"')
    else:
        head = page_head(HL(L), s["title"].format(**fmt), s["desc"].format(**fmt), f"/hikes/{slug}/", f"/randonnees/{slug}/", f"<style>{RP.CSS}{FUEL_CSS}</style>")
    BASE = "https://thegearfox.com"
    head = re.sub(r'(<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n?)+',
                  f'<link rel="alternate" hreflang="en-CA" href="{BASE}/hikes/{slug}/">\n<link rel="alternate" hreflang="fr-CA" href="{BASE}/randonnees/{slug}/">\n'
                  f'<link rel="alternate" hreflang="en-US" href="{BASE}/us/hikes/{slug}/">\n'
                  f'<link rel="alternate" hreflang="x-default" href="{BASE}{"/us" if h["side"] == "us" else ""}/hikes/{slug}/">\n', head, count=1)
    ts, rows = gear_rows(h)
    default = ts[-1] if h["kind"] != "day" else ts[0]
    pools, lis = {}, []
    for r in rows:
        title, why = r[LL], r["why_" + LL]
        p = hike_pool(items, r["shop"], stores, L == "us", NEED.get(r["key"])) if r.get("shop") else []
        if p:
            pools[r["key"]] = p
        lvs = "".join(f' data-l{t}="{r["lv"].get(t, "")}"' for t in ts)
        first = r["lv"].get(default, "")
        top = RP.picks(p, SHOW) if p else []
        deals = ((f'<ul class="dl"{"" if top else " hidden"}>{"".join(RP.deal_html(L, x) for x in top)}</ul>'
                  f'<p class="none"{" hidden" if top else ""}>{s["noDeals"]}</p>'
                  f'<p class="ft"><button type="button" class="mored" data-n="{s["moreN"]}"{"" if len(top) > 3 else " hidden"}>{s["moreN"].format(n=len(top))}</button></p>')
                 if r.get("shop") else "")
        lis.append(f'<li class="gi{"" if r.get("shop") else " mini"}" data-k="{r["key"]}"{lvs}{"" if first else " hidden"}><div class="hd">'
                   f'<input type="checkbox" class="have" aria-label="{esc(s["have"])}: {esc(title)}"><h3>{esc(title)}</h3>'
                   f'<span class="lv {first or "R"}">{s.get(first, "")}</span></div><p class="note">{esc(why)}</p>{deals}</li>')
    # what this trail is like, in plain words (only facts we hold for it)
    notes = [s["bears"][h["bears"]]] + [s["flag"][f] for f in h["flags"] if s["flag"].get(f)]
    ess = [x[LL] for x in HK.gear_for(h, default) if x["level"] == "essential"]
    adds = [x[LL] for x in HK.gear_for(h, default) if x["level"] != "essential"]
    faq = [(s["qBring"].format(**fmt), s["aBring"].format(ess=", ".join(e.split(":")[0].lower() for e in ess), adds=", ".join(a.lower() for a in adds)))]
    if "permit" in h["flags"]:
        faq.append((s["qPermit"].format(**fmt), s["aPermit"].format(park=h["park"])))
    if h["bears"] != "none":
        faq.append((s["qBears"].format(**fmt), s["aBears"][h["bears"]]))
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    by_rows = "".join(f'<div class="byrow"><b>{s["by"][g]}</b><div class="row">'
                      + "".join(f'<button type="button" data-bg="{g}" data-bs="{z}">{z}</button>' for z in ("XS", "S", "M", "L", "XL", "2XL")) + '</div></div>'
                      for g in ("tops", "bottoms", "socks", "gloves"))
    pj = json.dumps(pools, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    src = (s["src"].format(park=esc(h["park"]), link=f'<a href="{h["src"]}" rel="noopener">{s["srcLink"]}</a>', date=checked_on[LL])
           if h.get("checked") else f'<a href="{h["src"]}" rel="noopener">{s["srcLink"]}</a>')
    body = f"""<p class="crumbs"><a href="/{s['dir']}/">{s['aisle']}</a></p>
<h1>{esc(s['h1'].format(**fmt))}</h1>
<p class="sub">{esc(fmt['where'])} · {esc(facts(h, LL))}</p>
<p class="oside"><a href="{"/hikes/" if L == "us" else "/us/hikes/"}{slug}/">{esc(s['otherSide'])}</a></p>
{f'<p class="lnote">{esc(" · ".join(n for n in notes if n))}</p>' if any(notes) else ""}
<section class="rsize" id="rsize" data-men="{s['men']}" data-women="{s['women']}" data-change="{s['change']}"><p><b>{s['sizeH']}</b> · {s['sizeTxt']}</p>
<div class="row" data-f>{"".join(f'<button type="button" data-g="{g}">{s[g]}</button>' for g in ("men", "women"))}</div>
<p class="cur"><b>{s['sizeH']}:</b> <span></span> <button type="button" data-chg>{s['change']}</button></p>
<div class="row" data-s style="margin-top:6px">{"".join(f'<button type="button" data-s="{z}">{z}</button>' for z in ("XS", "S", "M", "L", "XL", "2XL"))}</div>
<div class="shrow"><label for="shoeSz" style="align-self:center;font-weight:600">{s['bootH']}</label><select id="shoeSz" aria-label="{esc(s['bootH'])}" data-ph="{esc(s['shSize'])}"></select></div>
<p class="bym"><button type="button" data-byopen>{s['byOpen']}</button></p><div class="byrows" hidden>{by_rows}</div></section>
{f'<p class="lbl">{s["trip"]}</p><div class="dists" role="group" aria-label="{s["trip"]}">' + "".join(f'<button type="button" data-d="{t}" aria-pressed="{str(t == default).lower()}">{tlab(t, LL)}</button>' for t in ts) + "</div>" if len(ts) > 1 else '<div class="dists" hidden></div>'}
<p class="prog" id="prog" data-t="{esc(s['progress'])}" data-all="{esc(s['progressAll'])}"></p>
<ul class="gl" id="gl" data-race="hike-{slug}" data-default="{default}" data-lm="{s['M']}" data-lr="{s['R']}" data-la="" data-lp="" data-ll=""
 data-home="{Tl['home']}{"&" if "?" in Tl['home'] else "?"}sport=hike" data-watch="{esc(s['watch'])}" data-won="{esc(s['watchOn'])}" data-wmember="{esc(s['wMember'])}" data-wnew="{esc(s['wNew'])}" data-wpending="{esc(s['wPending'])}" data-wadd="{esc(s['wAdd'])}" data-woff="{esc(s['wOff'])}" data-moren="{esc(s['moreN'])}" data-dh="{esc(s['deals'])}" data-dhs="{esc(s['dealsSize'])}" data-none="{esc(s['noDeals'])}" data-few="{esc(s['few'])}" data-off="{esc(s['off'])}" data-ly="{esc(s['Y'])}">{"".join(lis)}</ul>
<div hidden id="shoeBox" data-root="" data-dir="" data-pickfit="" data-from="" data-page="" data-none="" data-rm="" data-gone="" data-picksize=""><input id="shoeQ"><ul id="shoeSug"></ul><ul id="shoeMine"></ul></div>
{fuel(h, L)}
<p class="srcb">{src} {s['notAff']}</p>
<section class="alert" id="raceBox" data-ref="hike-{slug}" data-bad="{esc(Tl['alertBad'])}" data-ok="{esc(Tl['alertOk'])}" data-in="{esc(Tl['alertIn'])}" data-fail="{esc(Tl['alertFail'])}" data-pick="{esc(s['sizeTxt'])}">
<h2>{esc(s['boxH'])}</h2><p class="fine">{esc(s['boxTxt'])}</p><form novalidate><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(Tl['emailPh'])}" aria-label="Email" required><button type="submit">{esc(s['boxBtn'])}</button></form><p class="msg" aria-live="polite"></p></section>
<section class="faq"><h2>{s['faqH']}</h2>{"".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</section>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script id="pools" type="application/json">{pj}</script>
<script id="shoes" type="application/json">[]</script>
"""
    fx = getattr(page, "fx", 1.0) if L == "us" else 1.0
    kb = RP.S["en" if L == "us" else L]
    return (head + body + RP.KITB.replace("$BEST", RP.esc(kb["kbBest"])).replace("$BESTN", RP.esc(kb["kbBestN"])) + script(L, fx) + FUEL_JS + page_foot(Tl).replace('"shoe-page"', '"hike-page"').replace("|shoes||shoe-page", "|gear||hike-page"))


def fuel(h, L):
    """The food box: inputs prefilled from the trail (hours: 4 km/h + 1 h per 600 m climbed, Naismith's rule at a loaded hiker's
    pace; the visitor can change it), the maths in the page."""
    s, us = S[L], L == "us"
    gain = h["gain_m"] if h.get("gain_ok") else 0
    km = h["km"]
    nc = "" if gain else f'<p class="fine">{esc(s["fu_noclimb"])}</p>'
    num = lambda k, v, step, unit: (f'<label class="fu"><span>{s[k]}</span><span class="fi"><input type="number" inputmode="decimal" min="0" '
                                    f'step="{step}" data-f="{k}" value="{v}"><em{" data-w" if unit in (s["fu_kg"], s["fu_lb"]) else ""}>{unit}</em></span></label>')
    # Oct 27 (Bastien: "some people use both"): kg | lb for body + pack + food, whatever the side; climb stays m (Canada) / ft (USA)
    units = (f'<div class="fuu" role="group" aria-label="{esc(s["fu_units"])}">'
             + "".join(f'<button type="button" data-u="{u}" aria-pressed="{str((u == "lb") == us).lower()}">{s["fu_" + u]}</button>' for u in ("kg", "lb")) + '</div>')
    return (f'<section class="fuel" id="fuel" data-km="{km:g}" data-gain="{gain}" data-us="{1 if us else 0}" data-l="{"fr" if L == "fr" else "en"}"'
            f' data-trail="{esc(s["fu_trail"])}" data-day="{esc(s["fu_day"])}" data-food="{esc(s["fu_food"])}" data-snack="{esc(s["fu_snack"])}">'
            f'<h2>{esc(s["fu_fuelH"])}</h2><p class="fine">{esc(s["fu_fuelTxt"])}</p>{units}<div class="fus">'
            + num("fu_body", 165 if us else 75, 1, s["fu_lb"] if us else s["fu_kg"])
            + num("fu_pack", "", 0.5, s["fu_lb"] if us else s["fu_kg"])
            + num("fu_hours", "", 0.5, "h")
            + num("fu_climb", round(gain * 3.281) if us else gain, 10, s["fu_ft"] if us else s["fu_m"])
            + f'</div>{nc}<label class="gpx"><span>{esc(s["fu_gpx"])}</span><input type="file" accept=".gpx,application/gpx+xml" data-ok="{esc(s["fu_gpxOk"])}" data-bad="{esc(s["fu_gpxBad"])}"></label><p class="gpxm fine" aria-live="polite"></p>'
            f'<div class="fo" aria-live="polite"></div><p class="fine">{esc(s["fu_fine"])}</p></section>')


FUEL_CSS = """.fuel{background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px;margin:18px 0}
.fuel h2{margin:0 0 4px;font-size:18px}.fus{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}
.fu{display:flex;flex-direction:column;gap:3px;font-size:13px;font-weight:600}.fu input{font:inherit;font-weight:400;padding:8px;border:1.5px solid var(--line);border-radius:10px;width:100%;box-sizing:border-box}
.fi{display:flex;align-items:center;gap:6px}.fu em{font-style:normal;font-weight:400;color:var(--mute,#5c6660);font-size:12px}.gpx{display:flex;flex-direction:column;gap:4px;font-size:13px;margin:4px 0}.gpx input{font-size:13px;max-width:100%}.fo p{margin:6px 0}.fo b{font-size:17px}
.fuu{display:inline-flex;border:1.5px solid var(--line);border-radius:999px;overflow:hidden;margin:8px 0 0}.fuu button{font:600 13px/1 var(--body);padding:7px 14px;border:0;background:transparent;color:inherit;cursor:pointer}.fuu button[aria-pressed=true]{background:var(--ink,#17201c);color:#fff}"""

FUEL_JS = """<script>(function(){var b=document.getElementById("fuel");if(!b)return;
var us=b.dataset.us==="1",fr=b.dataset.l==="fr",km=+b.dataset.km,lb=us;
function days(){var x=document.querySelector(".dists button[aria-pressed=true]");return x?+x.dataset.d:1}
function inp(k){return b.querySelector('[data-f="'+k+'"]')}
function num(v,d){return (Math.round(v/d)*d).toLocaleString(fr?"fr-CA":"en-CA")}
function fill(){var d=days(),g=+inp("fu_climb").value*(us?0.3048:1),h=(km/4+g/600)/d;   // 4 km/h + 1 h per 600 m (Naismith at a loaded pace)
  if(!inp("fu_hours").dataset.own)inp("fu_hours").value=Math.max(1,Math.round(h*2)/2);
  if(!inp("fu_pack").dataset.own)inp("fu_pack").value=lb?(d>1?(d>3?31:24):13):(d>1?(d>3?14:11):6)}
function calc(){var d=days(),k=lb?0.4536:1,W=+inp("fu_body").value*k,L=+inp("fu_pack").value*k,H=+inp("fu_hours").value,
  g=+inp("fu_climb").value*(us?0.3048:1),o=b.querySelector(".fo");
  if(!(W>20&&H>0)){o.innerHTML="";return}
  var V=Math.max(0.3,Math.min(2,(km*1000/d)/(H*3600))),G=Math.min(40,g/(km*1000/2)*100)||0,n=1.2,
      R=(500+22*0.8*W)*4184/86400/W,   // Cunningham resting rate, W/kg
      P=function(G){var mg=0.34*V*G*(1-Math.pow(1.05,1-Math.pow(1.1,G+32)));   // LCDA (Looney 2022), W per kg of body weight
        return W*(R+Math.max(0,0.19+n*1.78*Math.pow(V,0.58)+0.27*Math.pow(V,4)+mg)*(1+1.96*Math.pow(L/W,1.36)))},
      kh=(P(G)+P(-G))/2*3600/4184,tr=kh*H,all=tr+Math.max(0,24-H)*R*1.2*W*3600/4184,t=function(s,o){return s.replace(/\{(\w)\}/g,function(_,x){return o[x]})},
      wt=function(kg){return lb?num(kg*2.2046,0.1)+" lb":num(kg,0.1)+" kg"};
  var out="<p><b>"+t(b.dataset.trail,{k:num(tr,10),h:num(kh,10)})+"</b></p>";
  if(d>1){var f=all/4400;out+="<p>"+t(b.dataset.day,{k:num(all,50)})+"</p><p>"+t(b.dataset.food,{f:wt(f),t:wt(f*d)})+"</p>"}
  else out+="<p>"+t(b.dataset.snack,{a:num(H*200,50),b:num(H*300,50)})+"</p>";
  o.innerHTML=out}
b.addEventListener("input",function(e){if(e.target.dataset.f)e.target.dataset.own=1;if(e.target.dataset.f==="fu_climb")fill();calc()});
document.querySelectorAll(".dists button").forEach(function(x){x.addEventListener("click",function(){setTimeout(function(){fill();calc()},0)})});
var gf=b.querySelector(".gpx input"),gm=b.querySelector(".gpxm");
gf.addEventListener("change",function(){var f=gf.files&&gf.files[0];if(!f)return;var r=new FileReader();
  r.onload=function(){try{var x=new DOMParser().parseFromString(r.result,"application/xml"),pts=x.querySelectorAll("trkpt,rtept"),d=0,up=0,pv=null,ev=null;
    if(pts.length<2)throw 0;
    pts.forEach(function(p){var la=+p.getAttribute("lat")*Math.PI/180,lo=+p.getAttribute("lon")*Math.PI/180,e=p.querySelector("ele");
      if(pv){var a=Math.sin((la-pv[0])/2),c=Math.sin((lo-pv[1])/2);d+=12742000*Math.asin(Math.sqrt(a*a+Math.cos(la)*Math.cos(pv[0])*c*c))}
      pv=[la,lo];if(e){var z=+e.textContent;if(ev===null)ev=z;else if(Math.abs(z-ev)>=5){if(z>ev)up+=z-ev;ev=z}}});   // 5 m steps: GPS noise doesn't count as climb
    km=Math.round(d/100)/10;inp("fu_climb").value=Math.round(us?up*3.281:up);inp("fu_climb").dataset.own=1;inp("fu_hours").dataset.own="";
    gm.textContent=gf.dataset.ok.replace("{km}",km.toLocaleString(fr?"fr-CA":"en-CA")).replace("{m}",Math.round(up).toLocaleString(fr?"fr-CA":"en-CA"));
    fill();calc()}catch(e){gm.textContent=gf.dataset.bad}};r.readAsText(f)});
function save(){try{localStorage.setItem("gf-fuel",JSON.stringify({b:inp("fu_body").value,u:lb?"lb":"kg"}))}catch(e){}}
function unit(u,conv){var to=u==="lb";if(conv&&to!==lb)["fu_body","fu_pack"].forEach(function(f){var x=inp(f);if(x.value!=="")x.value=Math.round(+x.value*(to?2.2046:0.4536)*(f==="fu_pack"?2:1))/(f==="fu_pack"?2:1)});
  lb=to;b.querySelectorAll(".fuu button").forEach(function(x){x.setAttribute("aria-pressed",String(x.dataset.u===u))});
  b.querySelectorAll("em[data-w]").forEach(function(x){x.textContent=u})}
b.querySelectorAll(".fuu button").forEach(function(x){x.addEventListener("click",function(){unit(x.dataset.u,true);save();calc()})});
try{var p=JSON.parse(localStorage.getItem("gf-fuel")||"null");if(p&&p.b){var pu=p.u||(us?"lb":"kg");unit(pu,false);inp("fu_body").value=p.b}}catch(e){}
inp("fu_body").addEventListener("change",save);
fill();calc()})();</script>"""


def script(L, fx):
    """The race pages' script, for hikes: essentials ("Y") count in "You have N of M" with what the park requires; boots follow the
    boot size (US, or the EU size from the homepage); events say "hike|<slug>|…"; a sign-up here is a hiking sign-up (Friday email)."""
    sc = RP.SCRIPT.replace("$LANG", "en" if L == "us" else L).replace("$CTRY", "us" if L == "us" else "ca").replace("$FX", str(fx))
    reps = [
        ('if(lv==="M"&&!li.dataset.kit){n++;if(got)h++}', 'if((lv==="M"||lv==="Y")&&!li.dataset.kit){n++;if(got)h++}'),
        ('return li.getAttribute("data-l"+dist)==="M"&&!li.closest(".kit")', 'var l=li.getAttribute("data-l"+dist);return (l==="M"||l==="Y")&&!li.closest(".kit")'),
        ('var s=SIZED[r.g]?r.s.filter(function(e){return fits(e[0],sizeFor(r.g))}):r.s;',
         'var bz=document.getElementById("shoeSz").value,eu=((prof&&prof.sizes&&prof.sizes.shoes&&prof.sizes.shoes.eu)||[]).map(String);'
         'var s=SIZED[r.g]?r.s.filter(function(e){return fits(e[0],sizeFor(r.g))}):r.g==="shoes"&&bz?r.s.filter(function(e){var z=String(e[0]);'
         'return z.indexOf("E:")===0?eu.indexOf(z.slice(2))>=0:z.replace(/^[MW]:/,"")===bz}):r.s;'),
        ('if(!p||!p.length||(!fit&&!size))return;', 'if(!p||!p.length||(!fit&&!size&&!document.getElementById("shoeSz").value))return;'),
        ('ana("filter",["race",race,what', 'ana("filter",["hike",race.replace(/^hike-/,""),what'),
        ('p.email=em;', 'p.email=em;if(!p.sport)p.sport="hike";'),
        ('terrain:"trail",', 'terrain:"trail",sport:"hike",'),
        ('ssel.addEventListener("change",function(){if(ssel.value){put("gf-shoe-size",{g:fit||"men",s:ssel.value});rt("shoesize",ssel.value)}shoeMine()});',
         'ssel.addEventListener("change",function(){if(ssel.value){put("gf-shoe-size",{g:fit||"men",s:ssel.value});rt("shoesize",ssel.value)}render()});'),
    ]
    for a, b in reps:
        assert a in sc, a
        sc = sc.replace(a, b)
    return sc


# Oct 29 (Bastien: "putting the hikes per province under country and state in the USA"): the hub groups trails by province / state
# under each country, most trails first, each one a line that opens ("British Columbia · 15 trails"); trails that cross states
# ("GA–ME") sit in "Multi-state trails" at the end; the visitor's own province/state (device time zone) opens by itself
HOME_TZ = {"America/Vancouver": "BC", "America/Edmonton": "AB", "America/Toronto": "ON", "America/Montreal": "QC", "America/Halifax": "NS",
           "America/Moncton": "NB", "America/St_Johns": "NL", "America/Whitehorse": "YT", "America/Winnipeg": "MB", "America/Regina": "SK",
           "America/Los_Angeles": "CA", "America/Phoenix": "AZ", "America/Denver": "CO", "America/Boise": "ID", "America/Anchorage": "AK"}
HUB_JS = """<script>(function(){var tz="";try{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||""}catch(e){}
var M=$TZ,r=M[tz];if(tz==="America/Toronto"&&document.documentElement.lang==="fr")r="QC";
var d=r&&document.querySelector('details.rg[data-r="'+r+'"]');if(d)d.open=true;
var q=document.getElementById("hubQ");if(!q)return;var keep=null;
q.addEventListener("input",function(){var on=!!q.value.trim(),D=[].slice.call(document.querySelectorAll("details.rg"));
  if(on&&!keep)keep=D.map(function(x){return x.open});
  setTimeout(function(){D.forEach(function(x,i){var any=[].some.call(x.querySelectorAll("li"),function(li){return !li.hidden});
      x.hidden=on&&!any;x.open=on?any:(keep?keep[i]:x.open)});if(!on)keep=null;
    document.querySelectorAll("h2.cty").forEach(function(h){var n=h.nextElementSibling,any=false;
      while(n&&n.tagName==="DETAILS"){if(!n.hidden)any=true;n=n.nextElementSibling}h.hidden=on&&!any})},0)});
document.querySelectorAll("details.rg").forEach(function(x){x.addEventListener("toggle",function(){if(x.open&&!q.value)try{ana("filter","hubregion|"+x.dataset.r)}catch(e){}})})})();</script>
<style>details.rg{border-bottom:1px solid var(--line)}details.rg>summary{list-style:none;display:flex;justify-content:space-between;align-items:center;gap:10px;
min-height:52px;padding:6px 2px;cursor:pointer;font:700 18px/1.2 var(--display)}details.rg>summary::-webkit-details-marker{display:none}
details.rg>summary small{font:500 14px var(--body);color:var(--muted);white-space:nowrap}details.rg>summary small::after{content:" +";font-weight:700;color:var(--moss)}
details.rg[open]>summary small::after{content:" −"}details.rg>ul.cards{margin:2px 0 14px}details.rg[hidden]{display:none!important}h2.cty{margin-top:22px}</style>"""


def hub(L, hikes):
    s, Tl, LL = S[L], (US if L == "us" else T[L]), ("en" if L == "us" else L)
    first = "us" if L == "us" else "ca"
    fr = L == "fr"
    multi = lambda h: "–" in h["region"]
    rows = ""
    for side in sorted({h["side"] for h in hikes}, key=lambda x: x != first):
        mine = [h for h in hikes if h["side"] == side]
        regs = {}
        for h in mine:
            regs.setdefault("MULTI" if multi(h) else h["region"], []).append(h)
        name = lambda r: ("Sentiers sur plusieurs États" if fr else "Multi-state trails") if r == "MULTI" else \
            ((REGION_FR.get(r) if fr else None) or REGION.get(r, r))
        rows += f'<h2 class="cty">{esc(s["groups"][side])}</h2>'
        for r in sorted(regs, key=lambda r: (r == "MULTI", -len(regs[r]), name(r))):
            n = len(regs[r])
            cnt = (f"{n} sentier" + ("s" if n > 1 else "")) if fr else (f"{n} trail" + ("s" if n > 1 else ""))
            rows += f'<details class="rg" data-r="{esc(r)}"><summary><span>{esc(name(r))}</span><small>{cnt}</small></summary><ul class="cards rh">'
            for h in sorted(regs[r], key=lambda h: h["name"]):
                rows += (f'<li><a href="/{s["dir"]}/{h["slug"]}/"><span class="nm"><b>{esc(h["name"])}</b>'
                         f'<small>{esc(where(h, LL))} · {esc(facts(h, LL))}</small></span><span class="pr">{s["hubGo"]}</span></a></li>')
            rows += "</ul></details>"
    rows += HUB_JS.replace("$TZ", json.dumps(HOME_TZ))
    t, d = s["hubTitle"].format(n=len(hikes)), s["hubDesc"]
    head = (page_head(HL("us"), t, d, "/us/hikes/", "", f"<style>{RP.HUB_CSS}</style>").replace('class="sw" href="/shoes/"', 'class="sw" href="/hikes/"') if L == "us"
            else page_head(HL(L), t, d, "/hikes/", "/randonnees/", f"<style>{RP.HUB_CSS}</style>"))
    find = RP.hub_find("Trouvez un sentier : nom, parc ou région" if fr else "Find a trail: name, park or region",
                       "Aucun sentier ne correspond à « {q} » pour l'instant." if fr else "No trail matches “{q}” yet.")
    return head + f'<h1 class="hubh">{esc(s["hubH1"])}</h1><p class="sub">{esc(s["hubIntro"])}</p>{find}{rows}' + page_foot(Tl)


LIVE = True       # Oct 25: Bastien OK'd ("Yes"); TRAIL_LIVE in index.html goes with it


def main():
    site = Path(sys.argv[1])
    every = "--all" in sys.argv                      # preview: unchecked hikes too
    if not LIVE and not every and "--force" not in sys.argv:
        print("hike pages: off (LIVE = False)")
        return
    stores = store_names((site / "index.html").read_text())
    hikes = [h for h in HK.HIKES if every or h.get("checked")]
    checked_on = {"en": "October 25, 2026", "fr": "25 octobre 2026"}
    urls = []
    for side, f in (("ca", "deals-hike.json"), ("us", "deals-hike-us.json")):
        p = site / f
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        langs = ("en", "fr") if side == "ca" else ("us",)
        if side == "us":
            fx = float((data.get("fx") or {}).get("USD") or 1.37)
            page.fx = fx
            S["us"]["money"] = lambda v, fx=fx: f"${v / fx:,.2f}"
            RP.S["us"]["money"] = S["us"]["money"]
        for h in hikes:
            for L in langs:
                out = site / S[L]["dir"] / h["slug"] / "index.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(page(h, L, data["items"], stores, checked_on))
                urls.append(f'/{S[L]["dir"]}/{h["slug"]}/')
        for L in langs:
            (site / S[L]["dir"] / "index.html").write_text(hub(L, hikes))
            urls.append(f'/{S[L]["dir"]}/')
    sm = site / "sitemap.xml"
    if sm.exists() and not every and urls:
        x = sm.read_text()
        day = __import__("datetime").date.today().isoformat()
        new = "".join(f"<url><loc>https://thegearfox.com{u}</loc><lastmod>{day}</lastmod></url>\n" for u in urls if f"https://thegearfox.com{u}<" not in x)
        sm.write_text(x.replace("</urlset>", new + "</urlset>"))
    print(f"hike pages: {len(hikes)} hikes, {len(urls)} pages")


if __name__ == "__main__":
    main()
