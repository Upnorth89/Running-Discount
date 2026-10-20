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
from shoe_pages import T, esc, page_head, page_foot, store_names, size_url, host  # noqa: E402

POOL = 40        # deals per gear item carried in the page (the script shows the best 3 in your size)
SHOW = 3

WATERPROOF = r"waterproof|\brain|gore|gtx|h2no|shell|storm|hydro|2\.5l|3l\b|futurelight|pertex shield|dryvent|membrane|imperm"
# what each kind of gear matches in our data (group, type, name pattern, name pattern to leave out)
KINDS = {
    "water":    dict(g={"gear", "packs"}, n=r"flask|bottle|bladder|reservoir|bidon|gourde", x=r"\bcup\b|holder|cage|brush|cleaning|cap only|lid|roller|stella mccartney|cooler|jug|tumbler|stainless|insulated|thermos|\b\d{3}\s?oz|\bride\b|classic light|shaker|\bbike\b"),
    "food":     dict(g={"nutrition"}, n=r"gel|bar\b|bars\b|chew|waffle|blok|stinger|gummies|jelly|bites", x=r"drink mix|electrolyte|hydration mix|capsule|tablet"),
    "cup":      dict(g={"gear", "packs"}, n=r"\bcup\b|speedcup|tasse|gobelet", x=r"holder"),
    "jacket":   dict(g={"tops"}, t={"jacket"}, n=WATERPROOF, x=r"vest|windbreaker|wind jacket|wind shell|insulat|down\b|puffer|softshell|soft shell|t-?shirt|\btee\b"),
    "tuque":    dict(g={"headwear"}, n=r"beanie|tuque|toque"),
    "headlamp": dict(g={"gear"}, n=r"headlamp|head lamp|frontale|lampe", x=r"bike|tail|clip light|band only|strap only|case|pouch"),
    "gloves":   dict(g={"gloves"}, x=r"arm sleeve|warmers?\b|cycling|bike|fingerless|half[- ]finger|gel\b"),
    "midlayer": dict(g={"tops"}, t={"layer", "tee"}, n=r"long sleeve|long-sleeve|\bl/s\b|\bls\b|half[- ]zip|quarter[- ]zip|1/4|1/2 zip|mid-?layer|fleece|hoodie|thermal|manches longues",
                     x=r"vest|sleeveless|short sleeve|tank|singlet|arm sleeve|crop|tie dye|stella mccartney|bra\b|polo"),
    "cap":      dict(g={"headwear"}, n=r"\bcap\b|buff|bandana|gaiter|casquette|visor", x=r"beanie|tuque|toque"),
    "pants":    dict(g={"bottoms"}, t={"pant"}, n=WATERPROOF, x=r"short"),
    "poles":    dict(g={"gear"}, n=r"\bpoles?\b|bâtons?|z-pole|trekking", x=r"basket|tip|strap|nordic|touring|\bft-?\d"),
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
        "updated": {"en": "August 1, 2024", "fr": "1er août 2024"},
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
            ("water", "MMMM", {"en": ("Water: 1 litre or more", "Soft flasks, bottles or a bladder, 1 L in all."),
                               "fr": ("Eau : 1 litre ou plus", "Flasques, bouteilles ou réservoir, 1 L en tout.")}, False),
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
}

S = {
    "en": {
        "dir": "races", "title": "{name} mandatory gear list ({short} {dists} km)",
        "desc": "The {name} mandatory gear list for the {dists} km, item by item, with today's best deals on each in your size at Canadian stores.",
        "h1": "{name} mandatory gear list", "sub": "{short} {dists} km · {where} · {when}",
        "dist": "Your distance", "km": "{d} km",
        "M": "Mandatory", "R": "Recommended", "A": "Allowed",
        "have": "I have it", "progress": "You have {h} of {n} mandatory items. Tick what you already own.", "progressAll": "You have every mandatory item. See you at the start.",
        "deals": "On sale now", "dealsSize": "On sale now in your size", "noDeals": "Nothing on sale in your size today. We check every morning.",
        "notSold": "The stores we check don't sell this.", "spec": "Check the spec before you buy.",
        "more": "See more on sale →", "moreN": "{n} more deals", "moreOne": "1 more deal", "sizeH": "Your size", "sizeTxt": "Pick it once to see deals that fit you.",
        "men": "Men's", "women": "Women's", "change": "Change", "off": "off",
        "src": "From the race's official list (last updated by the race {date}). Rules can change: check the {link} before race day.",
        "srcLink": "official list", "notAff": "The Gear Fox isn't affiliated with the race.",
        "boxH": "Get gear deals in your size every Friday until race day", "boxTxt": "Free. One email on Friday mornings with the best deals in your sizes. Unsubscribe in one tap.",
        "boxBtn": "Send me the deals", "faqH": "Quick answers",
        "qList": "What is the mandatory gear for the {short} {d} km?", "aList": "{items}.",
        "qJacket": "Is a windbreaker enough for the {name}?", "aJacket": "No. The race asks for a jacket with an attached hood and a waterproof, breathable membrane (on the {dists} km). Windbreakers aren't accepted.",
        "qCup": "Do the {name} aid stations have cups?", "aCup": "No. Aid stations have no cups, dishes or cutlery: every distance must carry a reusable cup of 15 cl or more.",
        "aisle": "Race gear lists", "money": T["en"]["money"],
    },
    "fr": {
        "dir": "courses", "title": "Matériel obligatoire de l'{name} ({short} {dists} km)",
        "desc": "Le matériel obligatoire de l'{name} pour le {dists} km, article par article, avec les meilleures aubaines du jour dans votre taille dans les boutiques canadiennes.",
        "h1": "Matériel obligatoire de l'{name}", "sub": "{short} {dists} km · {where} · {when}",
        "dist": "Votre distance", "km": "{d} km",
        "M": "Obligatoire", "R": "Recommandé", "A": "Permis",
        "have": "Je l'ai", "progress": "Vous avez {h} des {n} articles obligatoires. Cochez ce que vous avez déjà.", "progressAll": "Vous avez tout le matériel obligatoire. On se voit au départ.",
        "deals": "En solde maintenant", "dealsSize": "En solde dans votre taille", "noDeals": "Rien en solde dans votre taille aujourd'hui. On vérifie chaque matin.",
        "notSold": "Les boutiques que nous suivons n'en vendent pas.", "spec": "Vérifiez les caractéristiques avant d'acheter.",
        "more": "Voir plus d'aubaines →", "moreN": "{n} autres aubaines", "moreOne": "1 autre aubaine", "sizeH": "Votre taille", "sizeTxt": "Choisissez-la une fois pour voir les aubaines à votre taille.",
        "men": "Homme", "women": "Femme", "change": "Modifier", "off": "de rabais",
        "src": "Selon la liste officielle de la course (mise à jour par la course le {date}). Les règles peuvent changer : vérifiez la {link} avant la course.",
        "srcLink": "liste officielle", "notAff": "The Gear Fox n'est pas affilié à la course.",
        "boxH": "Les aubaines de matériel dans votre taille, chaque vendredi jusqu'à la course", "boxTxt": "Gratuit. Un courriel le vendredi matin avec les meilleures aubaines dans vos tailles. Désabonnement en un clic.",
        "boxBtn": "Envoyez-moi les aubaines", "faqH": "Réponses rapides",
        "qList": "Quel est le matériel obligatoire du {short} {d} km?", "aList": "{items}.",
        "qJacket": "Un coupe-vent suffit-il pour l'{name}?", "aJacket": "Non. La course demande un manteau avec capuchon attaché et une membrane imperméable et respirante (sur le {dists} km). Les coupe-vent ne sont pas acceptés.",
        "qCup": "Y a-t-il des verres aux ravitaillements de l'{name}?", "aCup": "Non. Les ravitaillements n'ont ni verres, ni vaisselle, ni ustensiles : chaque distance doit porter un gobelet réutilisable de 15 cl ou plus.",
        "aisle": "Listes de matériel de course", "money": T["fr"]["money"],
    },
}

CSS = """
.dists{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 12px}
.dists button{font:700 16px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:8px 16px;min-height:44px;cursor:pointer}
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
.dl a{display:flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:10px;padding:6px 10px 6px 6px;color:var(--ink);text-decoration:none}
.dl img{width:56px;height:56px;object-fit:contain;background:#fff;border-radius:8px;flex:none}
.dl .nm{flex:1;min-width:0;font-size:14px;line-height:1.25}.dl .nm b{display:block;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.dl .nm small{display:block;color:var(--muted);font-size:12px}
.dl .pr{text-align:right;white-space:nowrap}.dl .pr b{display:block;font:800 18px var(--display)}.dl .pr s{color:var(--muted);font-size:12px}
.dlh{font:600 13px var(--body);color:var(--muted);margin:10px 0 0}
.ft{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;margin:4px 0 0}.ft:empty{display:none}.spec{font-size:13px;color:var(--muted)}
.more{display:inline-block;margin-top:6px;font:600 14px var(--body)}
.none{font-size:14px;color:var(--muted);margin:6px 0 0}
.faq details{border-bottom:1px solid var(--line);padding:10px 0}.faq summary{font:700 16px/1.3 var(--body);cursor:pointer}.faq details p{margin:6px 0 0}
.rsize{background:var(--card);border:1.5px solid var(--hivis);border-radius:12px;padding:12px 14px;margin:10px 0}
.rsize p{margin:0 0 8px;font-size:15px}.rsize .row{display:flex;gap:6px;flex-wrap:wrap}
.rsize button{font:600 15px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:7px 13px;min-height:40px;cursor:pointer}
.rsize button[aria-pressed="true"]{background:var(--ink);color:var(--card);border-color:var(--ink)}
.rsize .mine{border:0;padding:0;margin:0;background:none}
.srcb{font-size:14px;color:var(--muted);margin:16px 0 0}
.gi .dl li:nth-child(n+2){display:none}.gi.open .dl li{display:block}
.mored{font:600 14px var(--body);color:var(--moss);background:none;border:0;padding:4px 0;cursor:pointer;text-decoration:underline}
.gi.open .mored{display:none}.gi.got .mored{display:none}
.gi.mini{padding:9px 14px}.gi.mini .hd h3{font:600 16px/1.3 var(--body)}.gi.mini .note{font-size:13px;margin:2px 0 0 34px}
.rsize.set .row,.rsize.set>p{display:none}.rsize .cur{display:none;margin:0;font-size:16px}.rsize.set .cur{display:block}
.rsize .cur button{border:0;background:none;padding:0 4px;min-height:0;color:var(--moss);text-decoration:underline;font:600 15px var(--body)}
"""


BAD = re.compile(r"seat ?mast|seat ?post|\bbiogel\b", re.I)   # bike parts still in today's data (scrape.py NOT_RUNNING drops them from Oct 21)


def pool(items, kind, stores):
    k = KINDS[kind.rstrip("2")]
    rx, xx = re.compile(k.get("n", "."), re.I), re.compile(k["x"], re.I) if k.get("x") else None
    out = []
    for d in items:
        if d.get("ca") is False or not d.get("img") or d["g"] not in k["g"]:
            continue
        if k.get("t") and d.get("t") not in k["t"]:
            continue
        if not rx.search(d["n"]) or (xx and xx.search(d["n"])) or BAD.search(d["n"]):
            continue
        sz = [e for e in d["sz"] if len(e) > 3 and e[3] and e[3] > e[1] * 1.1]       # 10%+ off
        if not sz:
            continue
        best = min(sz, key=lambda e: e[1])
        pct = round(100 * (1 - best[1] / best[3]))
        u = size_url(d, best)
        nm = stores.get(host(u), [host(u)])[0]
        out.append({"b": d["b"], "n": d["n"], "img": d["img"], "sx": d.get("sx") or [], "g": d["g"],
                    "s": [[e[0], e[1], e[3], size_url(d, e)] for e in sz], "st": nm, "h": host(u),
                    "_score": pct + min(best[3] - best[1], 150) / 5})
    out.sort(key=lambda r: -r["_score"])
    for r in out:
        del r["_score"]
    return out[:POOL]


def spread(p):
    """The best deals, one per brand first (11 tuques from one store's own brand look like a store ad)."""
    seen, first, rest = set(), [], []
    for r in p:
        (rest if r["b"].lower() in seen else first).append(r)
        seen.add(r["b"].lower())
    return first + rest


def money(L, v):
    return S[L]["money"](v)


def nm(L, n):
    """The French pages say the fit in French, like the site."""
    return re.sub(r"Women[’']s\b", "Femme", re.sub(r"Men[’']s\b", "Homme", re.sub(r"\bUnisex\b", "Unisexe", n))) if L == "fr" else n


def deal_html(L, r):
    e = min(r["s"], key=lambda e: e[1])
    pct = round(100 * (1 - e[1] / e[2]))
    return (f'<li><a href="{esc(e[3])}" data-store="{esc(r["h"])}" target="_blank" rel="noopener"><img src="{esc(r["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer">'
            f'<span class="nm"><b>{esc(r["b"])}</b>{esc(nm(L, r["n"]))}<small>{esc(r["st"])}</small></span>'
            f'<span class="pr"><b>{money(L, e[1])}</b><s>{money(L, e[2])}</s> <span class="off">−{pct}%</span></span></a></li>')


def page(slug, race, L, items, stores):
    s, other = S[L], "fr" if L == "en" else "en"
    dists = "/".join(race["dists"])
    fmt = dict(name=race["name"], short=race["short"], dists=dists, where=race["where"][L], when=race["when"][L])
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
        top = [r for r in spread(p) if not (kind == "headlamp2" and r["n"] in shown)][:SHOW]
        if kind == "headlamp":
            shown = {r["n"] for r in top}
        if sold:   # one deal shows, the others behind "N more deals"; the tick sits by the name (Oct 20: 7,800 px on a phone was too long)
            deals = (f'<ul class="dl"{"" if top else " hidden"}>{"".join(deal_html(L, r) for r in top)}</ul>'
                     f'<p class="none"{" hidden" if top else ""}>{s["noDeals"]}</p>'
                     f'<p class="ft"><button type="button" class="mored" data-n="{s["moreN"]}" data-one="{s["moreOne"]}"{"" if len(top) > 1 else " hidden"}>{s["moreOne"] if len(top) == 2 else s["moreN"].format(n=len(top) - 1)}</button>'
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
    faq.append((s["qJacket"].format(**fmt), s["aJacket"].format(**{**fmt, "dists": "/".join(d for i, d in enumerate(race["dists"]) if dict((k, lv) for k, lv, *_ in race["items"])["jacket"][i] == "M")})))
    faq.append((s["qCup"].format(**fmt), s["aCup"]))
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    src = race.get("src_fr") if L == "fr" and race.get("src_fr") else race["src"]
    pj = json.dumps(pools, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
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
 data-moren="{esc(s['moreN'])}" data-dh="{esc(s['deals'])}" data-dhs="{esc(s['dealsSize'])}" data-none="{esc(s['noDeals'])}" data-off="{esc(s['off'])}">{"".join(rows)}</ul>
<p class="srcb">{s['src'].format(date=race['updated'][L], link=f'<a href="{src}" rel="noopener">{s["srcLink"]}</a>')} {s['notAff']}</p>
<section class="alert" id="raceBox" data-ref="race-{slug}" data-bad="{esc(T[L]['alertBad'])}" data-ok="{esc(T[L]['alertOk'])}" data-fail="{esc(T[L]['alertFail'])}" data-pick="{esc(s['sizeTxt'])}">
<h2>{esc(s['boxH'])}</h2><p class="fine">{esc(s['boxTxt'])}</p><form novalidate><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(T[L]['emailPh'])}" aria-label="Email" required><button type="submit">{esc(s['boxBtn'])}</button></form><p class="msg" aria-live="polite"></p></section>
<section class="faq"><h2>{s['faqH']}</h2>{"".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</section>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script id="pools" type="application/json">{pj}</script>
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
  var R={M:0,R:1,A:2};
  [].forEach.call(gl.children,function(li){var lv=li.getAttribute("data-l"+dist)||"",k=li.dataset.k;li.hidden=!lv;
    li.style.order=2*(R[lv]||0)+(li.classList.contains("mini")?1:0);   // what's mandatory for this distance first; the small stuff after
    var tag=li.querySelector(".lv");tag.className="lv "+lv;tag.textContent=lv==="M"?gl.dataset.lm:lv==="R"?gl.dataset.lr:lv==="A"?gl.dataset.la:"";
    var got=!!have[k];li.classList.toggle("got",got);li.querySelector("input.have").checked=got;
    if(lv==="M"){n++;if(got)h++}
    var p=pools[k];if(!p||(!fit&&!size))return;
    var ok=[];for(var i=0;i<p.length;i++){var r=p[i];
      if(fit&&r.sx.length&&r.sx.indexOf(fit)<0)continue;
      var s=SIZED[r.g]?r.s.filter(function(e){return fits(e[0])}):r.s;if(!s.length)continue;
      ok.push([r,s.reduce(function(a,b){return b[1]<a[1]?b:a})])}
    if(k==="headlamp2"){var up=(SHOWN.headlamp||[]);ok=ok.filter(function(x){return up.indexOf(x[0].n)<0})}
    var seen={},picks=ok.filter(function(x){var b=x[0].b.toLowerCase(),n=!seen[b];seen[b]=1;return n}).concat(ok).filter(function(x,i,a){return a.indexOf(x)===i}).slice(0,3);   // one per brand first
    var ul=li.querySelector(".dl"),none=li.querySelector(".none"),mb=li.querySelector(".mored");
    ul.hidden=!picks.length;none.hidden=!!picks.length;mb.hidden=picks.length<2;mb.textContent=picks.length===2?mb.dataset.one:mb.dataset.n.replace("{n}",picks.length-1);
    SHOWN[k]=picks.map(function(x){return x[0].n});if(!picks.length)return;
    ul.innerHTML=picks.map(function(x){var r=x[0],e=x[1],pc=Math.round(100*(1-e[1]/e[2]));
      return '<li><a href="'+esc(e[3])+'" data-store="'+esc(r.h)+'" target="_blank" rel="noopener"><img src="'+esc(r.img)+'" alt="" loading="lazy" referrerpolicy="no-referrer"><span class="nm"><b>'+esc(r.b)+'</b>'+esc(nm(r.n))+'<small>'+esc(r.st)+(SIZED[r.g]&&size?" · "+esc(e[0]):"")+'</small></span><span class="pr"><b>'+money(e[1])+'</b><s>'+money(e[2])+'</s> <span class="off">−'+pc+'%</span></span></a></li>'}).join("")});
  var pg=document.getElementById("prog");pg.textContent=n&&h>=n?pg.dataset.all:pg.dataset.t.replace("{h}",h).replace("{n}",n);
  var box=document.getElementById("rsize");box.classList.toggle("set",!!(fit&&size)&&!box.dataset.open);
  box.querySelector(".cur span").textContent=(fit?box.dataset[fit]:"")+" · "+size;[].forEach.call(box.querySelectorAll("[data-g]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.g===fit))});
  [].forEach.call(box.querySelectorAll("button[data-s]"),function(b){b.setAttribute("aria-pressed",String(b.dataset.s===size))});
}
document.querySelector(".dists").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;dist=b.dataset.d;st.d=dist;put("gf-race-"+race,st);render()});
gl.addEventListener("change",function(e){var li=e.target.closest(".gi");if(!li)return;have[li.dataset.k]=e.target.checked;st.have=have;put("gf-race-"+race,st);render()});
gl.addEventListener("click",function(e){var b=e.target.closest(".mored");if(b)b.closest(".gi").classList.add("open")});
document.getElementById("rsize").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;
  if(b.hasAttribute("data-chg")){this.dataset.open="1";render();return}if(b.dataset.s&&fit)delete this.dataset.open;
  if(b.dataset.g)fit=b.dataset.g;if(b.dataset.s)size=b.dataset.s;put("gf-race-size",{g:fit,s:size});render()});
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
  p.email=em;if(!p.ref)p.ref=get("gf-ref")||box.dataset.ref;var btn=f.querySelector("button");btn.disabled=true;
  fetch("https://krwymmkauwqqxjxbvkyq.supabase.co/rest/v1/rpc/subscribe",{method:"POST",headers:{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"},
    body:JSON.stringify({p_email:em,p_profile:p})}).then(function(r){if(!r.ok)throw 0;
    put("gf-sub",{pending:em});if(!prof)put("rd-profile",p);f.remove();msg.textContent=box.dataset.ok.replace("{email}",em);
    try{ana("signup",box.dataset.ref)}catch(x){}try{window.umami&&umami.track("signup",{method:"email",where:box.dataset.ref,lang:fr?"fr":"en"})}catch(x){}})
  .catch(function(){btn.disabled=false;msg.textContent=box.dataset.fail})})})();
})();
</script>
"""


def main():
    site = Path(sys.argv[1])
    sale = json.loads(Path(sys.argv[2] if len(sys.argv) > 2 else site / "sale.json").read_text())
    stores = store_names((site / "index.html").read_text())
    for slug, race in RACES.items():
        for L in ("en", "fr"):
            out = site / S[L]["dir"] / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(slug, race, L, sale["items"], stores))
            print("wrote", out)


if __name__ == "__main__":
    main()
