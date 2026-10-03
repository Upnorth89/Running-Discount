#!/usr/bin/env python3
"""One page per popular shoe model, for Google: "Saucony Endorphin Speed 5 on sale in Canada".

Each page lists every size in stock with the best price, the store (linked straight to that size) and the % off,
in English (/shoes/<slug>/) and French (/chaussures/<slug>/). Rebuilt every morning from deals.json, after the
price history step (so "lowest price we've seen" can show; good news only, never "it was cheaper before").

A model gets a page once 3+ stores that ship from Canada carry it. Pages never disappear: a model that drops out
keeps its page (listed in shoes/pages.json, fetched from the live site each run) with "not in stock right now",
so Google never finds a dead link.

Also writes shoes/index.html + chaussures/index.html (all models by brand) and sitemap.xml.

Usage: python scraper/shoe_pages.py SITE_DIR
"""
import html
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

BASE = "https://thegearfox.com"
MIN_STORES = 3          # Canadian stores carrying the model before it gets a page
HISTORY_DAYS = 30       # days of price history before "lowest price we've seen" can show

T = {
    "en": {
        "dir": "shoes", "lang": "en-CA", "other": "fr",
        "title": "{name} on sale in Canada: prices by size",
        "h1sub": "On sale in Canada: every size, every store",
        "desc": "{name}: today's best price in every size at {n} Canadian running stores{off}. Checked every morning by The Gear Fox.",
        "descOff": ", up to {p}% off",
        "from": "From <b>{price}</b> <s>{reg}</s> ({p}% off)",
        "fromFull": "From <b>{price}</b>",
        "facts": "{sizes} sizes in stock · {stores} stores · checked {date}",
        "none": "Not in stock at the stores we check right now. Prices change every day: we'll show it here as soon as it's back.",
        "low": "Lowest price we've seen in {d} days",
        "size": "Size", "price": "Price", "store": "Store", "was": "was",
        "men": "Men's", "women": "Women's", "unisex": "Unisex (men's sizes)", "wide": "wide",
        "us": "ships from the US",
        "cta": "Get it in your size", "ctaTxt": "Pick your sizes once. Every Friday we email the best deals in them, and you can get a price-drop alert on this shoe.",
        "ctaBtn": "See deals in my size",
        "more": "More {brand} shoes", "all": "All shoe models",
        "types": {"daily": "Road running shoe", "race": "Racing shoe (plated)", "trail": "Trail running shoe", "hike": "Hiking & winter shoe"},
        "idxTitle": "Running shoe prices by model in Canada",
        "idxH1": "Shoe prices by model",
        "idxIntro": "Every popular running shoe we track, with today's best price in each size at Canadian stores. Updated every morning.",
        "idxDesc": "Today's best price in every size for {n} running shoe models at Canadian stores. Updated every morning by The Gear Fox.",
        "onSale": "on sale", "home": "The Gear Fox", "switch": "Français",
        "find": "Search a model (e.g. Clifton)", "noMatch": "No model matches. Try the brand name, or a shorter word.",
        "foot": "The Gear Fox · Outfox full price · Prices change often: the store's price at checkout is the one that counts.",
        "privacy": "Privacy",
        "months": ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."],
        "date": lambda d, m: f"{m} {d}",
        "money": lambda v: f"${v:,.2f}",
    },
    "fr": {
        "dir": "chaussures", "lang": "fr-CA", "other": "en",
        "title": "{name} en solde au Canada : prix par pointure",
        "h1sub": "En solde au Canada : chaque pointure, chaque boutique",
        "desc": "{name} : le meilleur prix du jour dans chaque pointure dans {n} boutiques de course canadiennes{off}. Vérifié chaque matin par The Gear Fox.",
        "descOff": ", jusqu'à {p} % de rabais",
        "from": "À partir de <b>{price}</b> <s>{reg}</s> ({p} % de rabais)",
        "fromFull": "À partir de <b>{price}</b>",
        "facts": "{sizes} pointures en stock · {stores} boutiques · vérifié le {date}",
        "none": "Pas en stock dans les boutiques que nous suivons en ce moment. Les prix changent chaque jour : on l'affichera ici dès son retour.",
        "low": "Le plus bas prix vu en {d} jours",
        "size": "Pointure", "price": "Prix", "store": "Boutique", "was": "avant",
        "men": "Homme", "women": "Femme", "unisex": "Unisexe (pointures homme)", "wide": "large",
        "us": "expédié des États-Unis",
        "cta": "Trouvez-la dans votre pointure", "ctaTxt": "Choisissez vos tailles une fois. Chaque vendredi, on vous envoie les meilleures aubaines dans vos tailles, et vous pouvez suivre le prix de cette chaussure.",
        "ctaBtn": "Voir les aubaines à ma taille",
        "more": "Autres chaussures {brand}", "all": "Tous les modèles",
        "types": {"daily": "Chaussure de course sur route", "race": "Chaussure de compétition (plaque)", "trail": "Chaussure de course en sentier", "hike": "Chaussure de randonnée et d'hiver"},
        "idxTitle": "Prix des chaussures de course par modèle au Canada",
        "idxH1": "Prix par modèle",
        "idxIntro": "Toutes les chaussures de course populaires que nous suivons, avec le meilleur prix du jour dans chaque pointure dans les boutiques canadiennes. Mis à jour chaque matin.",
        "idxDesc": "Le meilleur prix du jour dans chaque pointure pour {n} modèles de chaussures de course dans les boutiques canadiennes. Mis à jour chaque matin par The Gear Fox.",
        "onSale": "en solde", "home": "The Gear Fox", "switch": "English",
        "find": "Chercher un modèle (ex. Clifton)", "noMatch": "Aucun modèle trouvé. Essayez le nom de la marque ou un mot plus court.",
        "foot": "The Gear Fox · Flairez les aubaines · Les prix changent souvent : le prix de la boutique au paiement est celui qui compte.",
        "privacy": "Confidentialité",
        "months": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "date": lambda d, m: f"{d} {m}",
        "money": lambda v: f"{v:,.2f} $".replace(",", " ").replace(".", ","),
    },
}
UMAMI_ID = "d73c30be-171d-40d8-8101-278c2a536699"
SB_URL = "https://krwymmkauwqqxjxbvkyq.supabase.co"


def esc(s):
    return html.escape(str(s), quote=True)


def base_model(n):
    """"Triumph 23 Running Shoes [Wide] - Women's" -> "Triumph 23"."""
    n = re.sub(r"\s*(-\s*|\()(Men|Women)[’']s\)?$|\s*(-\s*|\()Unisex\)?$", "", n)
    n = re.split(r"\s+[—·]\s+", n)[0]                                    # "Clifton 10 — White/White"
    n = re.sub(r"\s*[\[(](x-?wide|extra wide|wide|2e|4e|d|ee|large)[\])]\s*|\s+\b(extra wide|x-?wide|wide)\b", " ", n, flags=re.I)
    n = re.sub(r"\b((trail|road) )?running shoes?\b|\bhiking shoes?\b|\bshoes?\b", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip(" -")


def slugify(s):
    s = s.lower().replace("+", " plus").replace("&", " and ")
    s = re.sub(r"[àâä]", "a", re.sub(r"[éèêë]", "e", re.sub(r"[öô]", "o", re.sub(r"[üû]", "u", s))))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def store_names(index_html):
    """The STORES map in index.html: {"altitude-sports.com": ["Altitude Sports"], "thefeed.com": ["The Feed", "US"], ...}."""
    m = re.search(r"const STORES=(\{.*?\});", index_html, re.S)
    try:
        return json.loads(m.group(1)) if m else {}
    except Exception:
        return {}


def host(u):
    return urlparse(u).hostname.replace("www.", "") if u else ""


def size_url(item, e):
    """Same as the site's sizeUrl(): the store's own link for this size, else ?variant=."""
    u = item["of"][e[2]] if e[2] < len(item["of"]) else item["of"][0]
    if len(e) < 5 or not u:
        return u
    if isinstance(e[4], str) and e[4].startswith("https://"):
        return e[4]
    p = urlparse(u)
    q = dict(parse_qsl(p.query))
    q["variant"] = e[4]
    return urlunparse(p._replace(query=urlencode(q)))


def size_sort(s):
    m = re.match(r"(\d+(?:\.\d)?)", s)
    return (float(m.group(1)) if m else 99, s)


def build_models(items):
    models = defaultdict(list)
    for d in items:
        if d["g"] != "shoes" or d.get("t") == "spike":
            continue
        name = base_model(d["n"])
        if not name:
            continue
        models[slugify(f'{d["b"]} {name}')].append(d)
    return models


def canadian_stores(its, stores):
    return {host(u) for d in its for u in d["of"] if len(stores.get(host(u), [""])) < 2}


def variant_label(d, L):
    sx = d.get("sx") or []
    lab = L["men"] if sx == ["men"] else L["women"] if sx == ["women"] else L["unisex"]
    if any(str(e[0]).startswith(("M:", "W:")) for e in d["sz"]):
        lab = L["unisex"]
    return lab + (f" · {L['wide']}" if d.get("w") else "")


def rows_for(d, stores, L):
    out = {}
    for e in d["sz"]:
        s = str(e[0])
        if s.endswith("~N") or s == "OS":
            continue
        wide = s.endswith("~W")
        s = s.replace("~W", "").replace("M:", "").replace("W:", "W ")
        key = s + (f" ({L['wide']})" if wide and not d.get("w") else "")
        if key not in out or e[1] < out[key][0]:
            u = size_url(d, e)
            out[key] = (e[1], e[3] if len(e) > 3 else e[1], host(u), u)
    return sorted(out.items(), key=lambda kv: size_sort(kv[0]))


def fmt_date(iso, L):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")) if iso else datetime.now(timezone.utc)
    return L["date"](dt.day, L["months"][dt.month - 1])


HEAD_CSS = """
:root{--ink:#17201C;--muted:#5C6660;--mist:#EEF1EC;--card:#FFFFFF;--line:#CBD2CC;--moss:#B8470A;--hivis:#F26A1B;--hivis-ink:#17201C;
--band:#17201C;--band-ink:#FFFFFF;--body:"Barlow",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--display:"Barlow Condensed","Arial Narrow",Impact,system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#E7ECE8;--muted:#9BA6A0;--mist:#121815;--card:#1B2320;--line:#34403A;--moss:#FF9A5C;--hivis-ink:#121815;--band:#26312C;--band-ink:#E7ECE8}}
:root[data-theme="dark"]{--ink:#E7ECE8;--muted:#9BA6A0;--mist:#121815;--card:#1B2320;--line:#34403A;--moss:#FF9A5C;--hivis-ink:#121815;--band:#26312C;--band-ink:#E7ECE8}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--mist);color:var(--ink);font:400 17px/1.5 var(--body);-webkit-font-smoothing:antialiased}
a{color:var(--moss)}
.top{background:var(--card);border-bottom:1.5px solid var(--line)}
.top .in,.wrap{max-width:720px;margin:0 auto;padding:12px 16px}
.top .in{display:flex;align-items:center;justify-content:space-between;gap:12px}
.top img{height:40px;width:auto;display:block}
.lang{font:600 14px var(--body);border:1.5px solid var(--line);border-radius:999px;padding:6px 12px;text-decoration:none;color:var(--ink)}
.crumbs{font-size:14px;color:var(--muted);margin:14px 0 0}
h1{font:800 clamp(30px,7vw,44px)/1.05 var(--display);margin:6px 0 4px;letter-spacing:-.01em}
.sub{margin:0 0 14px;color:var(--muted);font-size:16px}
.hero{display:flex;gap:16px;align-items:center;background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px;margin:0 0 18px}
.hero img{width:120px;height:90px;object-fit:contain;background:#fff;border-radius:10px;flex:none}
.hero p{margin:2px 0}
.hero b{font:800 26px/1 var(--display)}
.hero s{color:var(--muted)}
.tag{display:inline-block;font:700 12px var(--body);letter-spacing:.04em;text-transform:uppercase;color:var(--moss)}
.badge{display:inline-block;background:var(--hivis);color:var(--hivis-ink);border:1.5px solid var(--ink);border-radius:6px;font:700 13px var(--body);padding:2px 8px;margin-top:6px}
.facts{font-size:14px;color:var(--muted)}
h2{font:700 24px/1.1 var(--display);margin:22px 0 8px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1.5px solid var(--line);border-radius:12px;overflow:hidden;font-size:15px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line)}
th{font:600 13px var(--body);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
td.p{white-space:nowrap}
td.p b{font:800 18px var(--display)}
td.p s{color:var(--muted);font-size:13px;margin-left:4px}
.off{display:inline-block;background:var(--hivis);color:var(--hivis-ink);border-radius:5px;font:700 12px var(--body);padding:1px 5px;margin-left:6px}
.us{display:block;font-size:12px;color:var(--muted)}
.cta{background:var(--band);color:var(--band-ink);border-radius:14px;padding:18px;margin:26px 0}
.cta h2{margin:0 0 6px;color:var(--band-ink)}
.cta p{margin:0 0 12px;color:var(--band-ink);opacity:.85}
.btn{display:inline-block;background:var(--hivis);color:#17201C;border:2px solid #17201C;border-radius:10px;font:700 18px var(--display);padding:10px 18px;text-decoration:none}
.links{display:flex;flex-wrap:wrap;gap:8px;padding:0;list-style:none;margin:0}
.links a{display:inline-block;background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:6px 12px;text-decoration:none;color:var(--ink);font-size:15px}
.links small{color:var(--moss);font-weight:600}
.brand{margin:18px 0 6px;font:700 20px var(--display);scroll-margin-top:120px}
.find{position:sticky;top:0;z-index:5;background:var(--mist);padding:10px 0 8px;margin:0 -2px}
.find input{width:100%;font:400 17px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:12px 14px}
.find input:focus{outline:3px solid var(--moss);outline-offset:1px}
.jump{display:flex;gap:6px;overflow-x:auto;padding:2px 0 4px;scrollbar-width:none}
.jump a{flex:none;font:600 13px var(--body);color:var(--ink);text-decoration:none;border:1.5px solid var(--line);border-radius:999px;padding:4px 10px;background:var(--card)}
.nomatch{color:var(--muted);margin:16px 0}
.foot{font-size:13px;color:var(--muted);margin:30px 0 10px}
"""


def page_head(L, title, desc, path_en, path_fr, extra=""):
    lang_path = path_en if L["lang"] == "en-CA" else path_fr
    return f"""<!DOCTYPE html>
<html lang="{L['lang'][:2]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | The Gear Fox</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{lang_path}">
<link rel="alternate" hreflang="en-CA" href="{BASE}{path_en}">
<link rel="alternate" hreflang="fr-CA" href="{BASE}{path_fr}">
<link rel="alternate" hreflang="x-default" href="{BASE}{path_en}">
<meta name="theme-color" content="#F26A1B">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Gear Fox">
<meta property="og:url" content="{BASE}{lang_path}">
<meta property="og:image" content="{BASE}/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/shoe-pages.css">
{extra}
<script defer src="https://cloud.umami.is/script.js" data-website-id="{UMAMI_ID}" data-domains="thegearfox.com,www.thegearfox.com"></script>
</head>
<body>
<header class="top"><div class="in"><a href="/{'' if L['lang'] == 'en-CA' else '?lang=fr'}" aria-label="The Gear Fox"><img src="/logo.svg" alt="The Gear Fox" width="185" height="80"></a>
<a class="lang" href="{path_fr if L['lang'] == 'en-CA' else path_en}" hreflang="{L['other']}">{L['switch']}</a></div></header>
<main class="wrap">
"""


def page_foot(L):
    priv = "/privacy.html" + ("" if L["lang"] == "en-CA" else "?lang=fr")
    # deal clicks count toward the monthly report (same anonymous counter as the site: store + category, nothing personal)
    return f"""<p class="foot">{esc(L['foot'])} · <a href="https://www.instagram.com/thegearfox/" rel="noopener">@thegearfox</a> · <a href="{priv}">{L['privacy']}</a></p>
</main>
<script>
document.addEventListener("click",function(e){{var a=e.target.closest("a[data-store]");if(!a)return;
try{{fetch("{SB_URL}/rest/v1/rpc/log_event",{{method:"POST",keepalive:true,headers:{{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"}},
body:JSON.stringify({{p_kind:"click",p_store:a.dataset.store,p_group:"shoes",p_ref:"shoe-page",p_lang:"{L['lang'][:2]}"}})}})}}catch(x){{}}
try{{window.umami&&umami.track("deal-click",{{store:a.dataset.store,from:"shoe-page"}})}}catch(x){{}}}});
</script>
</body>
</html>
"""


def model_page(slug, its, stores, L, updated, related, brand_models):
    first = its[0]
    brand = first["b"]
    name = f"{brand} {base_model(first['n'])}"
    path_en, path_fr = f"/shoes/{slug}/", f"/chaussures/{slug}/"
    money = L["money"]
    # every variant (men's, women's, wide…) with its sizes
    groups = []
    for d in sorted(its, key=lambda d: ({"men": 0, "women": 1}.get((d.get("sx") or ["u"])[0], 2) if len(d.get("sx") or []) == 1 else 2, bool(d.get("w")))):
        rows = rows_for(d, stores, L)
        if rows:
            groups.append((variant_label(d, L), rows))
    merged = defaultdict(list)            # two items with the same label (e.g. GTX folded in elsewhere) share one table
    for lab, rows in groups:
        merged[lab].extend(rows)
    allrows = [r for _, rows in merged.items() for r in rows]
    sale = [r for _, r in allrows if r[0] < r[1] * 0.99]
    best = min(allrows, key=lambda kv: kv[1][0])[1] if allrows else None
    top = max((round(100 * (1 - p / r)) for p, r, _, _ in sale), default=0)
    n_stores = len({host(u) for d in its for u in d["of"]})          # every store that carries it, not just the cheapest
    title = L["title"].format(name=name)
    desc = L["desc"].format(name=name, n=n_stores, off=L["descOff"].format(p=top) if top >= 10 else "")
    ld = ""
    if best:
        lo_p, hi_p = min(r[0] for _, r in allrows), max(r[0] for _, r in allrows)
        ld = json.dumps({"@context": "https://schema.org", "@type": "Product", "name": name, "brand": {"@type": "Brand", "name": brand},
                         **({"image": first["img"]} if first.get("img") else {}),
                         "offers": {"@type": "AggregateOffer", "priceCurrency": "CAD", "lowPrice": f"{lo_p:.2f}", "highPrice": f"{hi_p:.2f}",
                                    "offerCount": len(allrows), "availability": "https://schema.org/InStock"}}, ensure_ascii=False)
        ld = f'<script type="application/ld+json">{ld}</script>'
    out = [page_head(L, title, desc, path_en, path_fr, ld)]
    out.append(f'<p class="crumbs"><a href="/{L["dir"]}/">{L["all"]}</a> › {esc(brand)}</p>')
    out.append(f'<h1>{esc(name)}</h1><p class="sub">{L["h1sub"]}</p>')
    t = L["types"].get(first.get("t") or "", "")
    if best:
        p, reg = best[0], best[1]
        off = round(100 * (1 - p / reg)) if reg and p < reg * 0.99 else 0
        line = L["from"].format(price=money(p), reg=money(reg), p=off) if off else L["fromFull"].format(price=money(p))
        # "Is this deal real?": good news only (Bastien's call): the best price today is the lowest in 30+ days of history
        lows = [d for d in its if d.get("hd", 0) >= HISTORY_DAYS and d.get("lo") is not None and min(e[1] for e in d["sz"]) <= d["lo"] + 0.01]
        badge = f'<span class="badge">{L["low"].format(d=max(d["hd"] for d in lows))}</span>' if lows and off else ""
        img = f'<img src="{esc(first["img"])}" alt="{esc(name)}" loading="lazy" referrerpolicy="no-referrer">' if first.get("img") else ""
        out.append(f'<div class="hero">{img}<div>{f"<span class=tag>{esc(t)}</span>" if t else ""}<p>{line}</p>{badge}'
                   f'<p class="facts">{L["facts"].format(sizes=len(allrows), stores=n_stores, date=fmt_date(updated, L))}</p></div></div>')
    else:
        out.append(f'<div class="hero"><div>{f"<span class=tag>{esc(t)}</span>" if t else ""}<p>{L["none"]}</p></div></div>')
    for lab, rows in merged.items():
        rows = sorted({k: v for k, v in rows}.items(), key=lambda kv: size_sort(kv[0]))
        out.append(f'<h2>{esc(lab)}</h2><table><thead><tr><th>{L["size"]}</th><th>{L["price"]}</th><th>{L["store"]}</th></tr></thead><tbody>')
        for size, (p, reg, h, u) in rows:
            off = round(100 * (1 - p / reg)) if reg and p < reg * 0.99 else 0
            st = stores.get(h, [h])
            us = f'<span class="us">{L["us"]}</span>' if len(st) > 1 else ""
            price = f'<b>{money(p)}</b>' + (f'<s>{money(reg)}</s><span class="off">−{off}%</span>' if off else "")
            out.append(f'<tr><td>{esc(size)}</td><td class="p">{price}</td><td><a href="{esc(u)}" rel="nofollow noopener" target="_blank" data-store="{esc(h)}">{esc(st[0])}</a>{us}</td></tr>')
        out.append("</tbody></table>")
    home = "/?ref=shoe-page" + ("&lang=fr" if L["lang"] == "fr-CA" else "")
    out.append(f'<section class="cta"><h2>{L["cta"]}</h2><p>{L["ctaTxt"]}</p><a class="btn" href="{home}">{L["ctaBtn"]}</a></section>')
    if related:
        out.append(f'<h2>{L["more"].format(brand=esc(brand))}</h2><ul class="links">' +
                   "".join(f'<li><a href="/{L["dir"]}/{s}/">{esc(brand_models[s])}</a></li>' for s in related) + "</ul>")
    out.append(page_foot(L))
    return "".join(out)


def index_page(L, entries, updated):
    """entries: [(brand, slug, model name, best % off or 0)]"""
    path_en, path_fr = "/shoes/", "/chaussures/"
    out = [page_head(L, L["idxTitle"], L["idxDesc"].format(n=len(entries)), path_en, path_fr)]
    out.append(f'<h1>{L["idxH1"]}</h1><p class="sub">{L["idxIntro"]}</p>')
    by = defaultdict(list)
    for b, s, n, off in entries:
        by[b].append((n, s, off))
    brands = sorted(by, key=str.lower)
    # search as you type + brand shortcuts (for people; Google reads the plain links below either way)
    out.append(f'<div class="find"><input id="find" type="search" placeholder="{esc(L["find"])}" aria-label="{esc(L["find"])}" autocomplete="off">'
               f'<nav class="jump">' + "".join(f'<a href="#b-{slugify(b)}">{esc(b)}</a>' for b in brands) + '</nav></div>')
    for b in brands:
        out.append(f'<section class="bgrp"><p class="brand" id="b-{slugify(b)}">{esc(b)}</p><ul class="links">' + "".join(
            f'<li data-n="{esc((b + " " + n).lower())}"><a href="/{L["dir"]}/{s}/">{esc(n[len(b):].strip() if n.lower().startswith(b.lower() + " ") else n)}{f" <small>−{off}%</small>" if off >= 10 else ""}</a></li>'
            for n, s, off in sorted(by[b], key=lambda x: x[0].lower())) + "</ul></section>")
    out.append(f'<p class="nomatch" id="nomatch" hidden>{esc(L["noMatch"])}</p>')
    out.append("""<script>(function(){var f=document.getElementById("find"),nm=document.getElementById("nomatch");
var norm=function(t){return t.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/[^a-z0-9+ ]/g," ")};
f.addEventListener("input",function(){var w=norm(f.value).split(/\\s+/).filter(Boolean),any=false;
document.querySelectorAll(".bgrp").forEach(function(g){var n=0;g.querySelectorAll("li").forEach(function(li){var t=norm(li.dataset.n).replace(/ /g,"")+" "+norm(li.dataset.n);
var ok=w.every(function(x){return t.indexOf(x)>=0});li.hidden=!ok;if(ok)n++});g.hidden=!n;if(n)any=true});
nm.hidden=any||!w.length;document.querySelector(".jump").hidden=!!w.length})})();</script>""")
    out.append(page_foot(L))
    return "".join(out)


def main():
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    data = json.loads((site / "deals.json").read_text())
    items, updated = data["items"], data.get("updated")
    stores = store_names((site / "index.html").read_text())
    models = build_models(items)
    reg_path = site / "shoes" / "pages.json"          # every model that ever had a page (fetched from the live site)
    try:
        known = json.loads(reg_path.read_text())
    except Exception:
        known = {}
    for slug, its in models.items():
        if slug not in known and len(canadian_stores(its, stores)) >= MIN_STORES:
            known[slug] = {"b": its[0]["b"], "n": f'{its[0]["b"]} {base_model(its[0]["n"])}', "t": its[0].get("t") or ""}
    # an old page whose name now tidies into another model ("Neo Vista (Men's)" -> "Neo Vista") forwards to it
    for slug, meta in known.items():
        if meta.get("to") or slug in models:
            continue
        b = meta["b"]
        to = slugify(f'{b} {base_model(meta["n"][len(b) + 1:] if meta["n"].lower().startswith(b.lower() + " ") else meta["n"])}')
        if to != slug and to in known and not known[to].get("to"):
            meta["to"] = to
    moved = {s: v["to"] for s, v in known.items() if v.get("to")}
    for slug, to in moved.items():
        for L in T.values():
            p = site / L["dir"] / slug / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            u = f"/{L['dir']}/{to}/"
            p.write_text(f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{esc(known[to]["n"])}</title><link rel="canonical" href="{BASE}{u}">'
                         f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={u}"></head><body><a href="{u}">{esc(known[to]["n"])}</a></body></html>')
    known_live = {s: v for s, v in known.items() if not v.get("to")}
    names = {s: v["n"] for s, v in known_live.items()}
    by_brand = defaultdict(list)
    for s, v in known_live.items():
        by_brand[v["b"].lower()].append(s)
    entries, n_live = [], 0
    for slug, meta in known_live.items():
        its = models.get(slug) or [{"b": meta["b"], "n": meta["n"][len(meta["b"]) + 1:], "g": "shoes", "t": meta.get("t"), "sz": [], "of": []}]
        n_live += bool(models.get(slug))
        same = [s for s in by_brand[meta["b"].lower()] if s != slug]
        related = sorted(same, key=lambda s: (known[s].get("t") != meta.get("t"), s))[:8]
        offs = [round(100 * (1 - e[1] / e[3])) for d in its for e in d["sz"] if len(e) > 3 and e[1] < e[3] * 0.99]
        entries.append((meta["b"], slug, meta["n"], max(offs, default=0)))
        for L in T.values():
            p = site / L["dir"] / slug / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(model_page(slug, its, stores, L, updated, related, names))
    (site / "shoe-pages.css").write_text(HEAD_CSS.strip() + "\n")
    for L in T.values():
        (site / L["dir"]).mkdir(parents=True, exist_ok=True)
        (site / L["dir"] / "index.html").write_text(index_page(L, entries, updated))
    reg_path.write_text(json.dumps(known, ensure_ascii=False, separators=(",", ":")))
    day = (updated or datetime.now(timezone.utc).isoformat())[:10]
    urls = ["/", "/shoes/", "/chaussures/", "/privacy.html"]
    urls += [f"/{d}/{s}/" for s in known_live for d in ("shoes", "chaussures")]
    (site / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{day}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    print(f"shoe pages: {len(known_live)} models ({n_live} in stock today), {2 * len(known_live)} pages EN/FR, "
          f"{len(moved)} old addresses forwarded, sitemap {len(urls)} links")


if __name__ == "__main__":
    main()
