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
from shoe_pages import T, US, esc, page_head, page_foot, store_names, size_url, host   # noqa: E402

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
               progress="You have {h} of {n} essentials. Tick what you already own.", progressAll="You have every essential. Have a great hike.",
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
               progress="Vous avez {h} des {n} essentiels. Cochez ce que vous avez déjà.", progressAll="Vous avez tous les essentiels. Bonne randonnée.",
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
for L in S:   # the race pages' size box, watch and sign-up words
    S[L] = dict(RP.S[L], **S[L])


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


def page(h, L, items, stores, checked_on):
    s, Tl = S[L], (US if L == "us" else T[L])
    slug, LL = h["slug"], ("en" if L == "us" else L)
    fmt = dict(name=h["name"], where=where(h, LL))
    own = f'/{s["dir"]}/{slug}/'
    if L == "us":
        head = page_head(US, s["title"].format(**fmt), s["desc"].format(**fmt), own, "", f"<style>{RP.CSS}</style>")
    else:
        head = page_head(T[L], s["title"].format(**fmt), s["desc"].format(**fmt), f"/hikes/{slug}/", f"/randonnees/{slug}/", f"<style>{RP.CSS}</style>")
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
<p class="srcb">{src} {s['notAff']}</p>
<section class="alert" id="raceBox" data-ref="hike-{slug}" data-bad="{esc(Tl['alertBad'])}" data-ok="{esc(Tl['alertOk'])}" data-fail="{esc(Tl['alertFail'])}" data-pick="{esc(s['sizeTxt'])}">
<h2>{esc(s['boxH'])}</h2><p class="fine">{esc(s['boxTxt'])}</p><form novalidate><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(Tl['emailPh'])}" aria-label="Email" required><button type="submit">{esc(s['boxBtn'])}</button></form><p class="msg" aria-live="polite"></p></section>
<section class="faq"><h2>{s['faqH']}</h2>{"".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</section>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script id="pools" type="application/json">{pj}</script>
<script id="shoes" type="application/json">[]</script>
"""
    fx = getattr(page, "fx", 1.0) if L == "us" else 1.0
    return (head + body + script(L, fx) + page_foot(Tl).replace('"shoe-page"', '"hike-page"').replace("|shoes||shoe-page", "|gear||hike-page"))


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


def hub(L, hikes):
    s, Tl, LL = S[L], (US if L == "us" else T[L]), ("en" if L == "us" else L)
    first = "us" if L == "us" else "ca"
    rows, grp = "", None
    for h in sorted(hikes, key=lambda h: (h["side"] != first, h["region"], h["name"])):
        if h["side"] != grp:
            grp = h["side"]
            rows += f'{"</ul>" if rows else ""}<h2>{esc(s["groups"][grp])}</h2><ul class="cards rh">'
        rows += (f'<li><a href="/{s["dir"]}/{h["slug"]}/"><span class="nm"><b>{esc(h["name"])}</b>'
                 f'<small>{esc(where(h, LL))} · {esc(facts(h, LL))}</small></span><span class="pr">{s["hubGo"]}</span></a></li>')
    t, d = s["hubTitle"].format(n=len(hikes)), s["hubDesc"]
    head = (page_head(US, t, d, "/us/hikes/", "", f"<style>{RP.HUB_CSS}</style>") if L == "us"
            else page_head(T[L], t, d, "/hikes/", "/randonnees/", f"<style>{RP.HUB_CSS}</style>"))
    return head + f'<h1 class="hubh">{esc(s["hubH1"])}</h1><p class="sub">{esc(s["hubIntro"])}</p>{rows}</ul>' + page_foot(Tl)


LIVE = False      # Oct 25: built and previewed; on the live site after Bastien's OK (then also TRAIL_LIVE in index.html)


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
