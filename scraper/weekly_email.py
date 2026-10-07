#!/usr/bin/env python3
"""The Gear Fox weekly sale email.

Reads today's deals.json (the live site's copy) and each profile in email/profiles.json, finds
the gear on sale in that person's sizes (same matching rules as the Shop page), and emails it
through Resend (https://resend.com, free tier).

Env:
  RESEND_API_KEY   required to send (without it the email is only written to email/preview.html)
  DEALS_URL        where to read deals.json (default: the site's own copy)
  SITE_URL         link to the site in the email
  FROM_EMAIL       sender, default "The Gear Fox <deals@thegearfox.com>"
  SUPABASE_URL, SUPABASE_SECRET_KEY
                   where subscribers who signed up on the site live (confirmed and not unsubscribed)
  MAILING_ADDRESS  postal address for the footer (required by Canada's anti-spam law, CASL)
  SEND_TO          test sends: only these subscribers get it (comma-separated emails), or "everyone".
                   "due" = a normal Friday run (people for whom it's 7am+, each once): Supabase's timer uses it.
                   A manual run from the Actions tab must set it, so a test never reaches everybody by accident.

Subscribers come from Supabase plus email/profiles.json (the database wins if an address is in both).

Usage: python scraper/weekly_email.py [--dry-run]
"""
import html
import json
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/") + "/"
DEALS_URL = os.environ.get("DEALS_URL") or (SITE_URL + "deals.json" if SITE_URL != "/" else "")
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
SB_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
ADDRESS = os.environ.get("MAILING_ADDRESS", "").strip()
SEND_TO = os.environ.get("SEND_TO", "").strip().lower()
if SEND_TO == "due":     # Supabase's Friday timer (or a manual catch-up): exactly like a scheduled run
    SEND_TO = ""
MANUAL = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and os.environ.get("SEND_TO", "").strip().lower() != "due"

GROUP_LABEL = {"shoes": "Shoes", "tops": "Tops & jackets", "bottoms": "Shorts & tights", "bras": "Sports bras",
               "socks": "Socks", "gloves": "Gloves", "headwear": "Hats & buffs", "packs": "Vests & packs",
               "gear": "Lights, poles & bottles", "watches": "Watches", "nutrition": "Nutrition"}
SIZED = {"shoes", "tops", "bottoms", "bras", "socks", "gloves", "headwear"}
PER_GROUP, TOTAL = 6, 36

WORD = {"ONE SIZE": "OS", "O/S": "OS", "X-SMALL": "XS", "XSMALL": "XS", "SMALL": "S", "MEDIUM": "M",
        "LARGE": "L", "X-LARGE": "XL", "XLARGE": "XL"}
def norm(s):
    s = str(s).strip().upper()
    s = WORD.get(s, s)
    return s.replace("XXXL", "3XL").replace("XXL", "2XL").replace("XXS", "2XS")

LETTERS = {"2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL"}

def acc_letters(d):
    """Vests, belts, lights in letter sizes follow the clothing size (same rule as the site)."""
    return d["g"] in ("packs", "gear") and any(e[0] in LETTERS for e in d["sz"]) and all(e[0] == "OS" or e[0] in LETTERS for e in d["sz"])

GROUP_BONUS = {"shoes": 15, "tops": 8, "bottoms": 8, "bras": 8, "packs": 6, "watches": 6}

def score(d):
    """% off plus dollars saved and what it is, so a $200 shoe at 60% beats a $15 belt at 74% (same as the site)."""
    return d["pct"] + GROUP_BONUS.get(d["g"], 0) + min(15, (d["reg"] - d["best"]) / 10)

def nm(n, lang="en"):
    if lang != "fr":
        return n
    n = re.sub(r"^(Men's|Women's|Unisex)\s+(.+)$", r"\2 - \1", n)    # "Women's Trail Tee" -> "Trail Tee - Femme"
    return re.sub(r"\bUnisex\b", "Unisexe", re.sub(r"\bWomen's\b", "Femme", re.sub(r"\bMen's\b", "Homme", n)))

SHOE_KEY = re.compile(r"^(?:([MW]):)?(\d+(?:\.5)?)(?:~([WN]))?$")

def size_url(d, e):
    """The product page with this size already selected, when the store gives each size its own link."""
    u = d["of"][e[2]] if len(d["of"]) > e[2] else d["of"][0]
    if len(e) > 4 and isinstance(e[4], str) and e[4].startswith("https://"):
        return e[4]                     # the store's own link for this size (Sporting Life)
    if len(e) > 4 and e[4]:
        from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
        sp = urlsplit(u)
        q = [(k, v) for k, v in parse_qsl(sp.query) if k != "variant"] + [("variant", str(e[4]))]
        u = urlunsplit(sp._replace(query=urlencode(q)))
    return u

def final_sale(d, e):
    """Same as the site's finalSale(): the store's rule (scrape.py FINAL_SALE, per offer in "fs") for the price shown."""
    fs = d.get("fs") or []
    c = fs[e[2]] if e[2] < len(fs) else 0
    if not c:
        return False
    reg = e[3] if len(e) > 3 and e[3] else e[1]
    return True if c == 1 else e[1] < reg * 0.99 if c == 2 else reg > 0 and 100 * (1 - e[1] / reg) >= c - 0.5

TERRAIN = {"road": {"daily", "race"}, "trail": {"trail", "hike"}}

def terrain_ok(d, p):
    """Road or trail runner (sign-up "Where do you run?"): only their kind of shoes; untyped shoes and
    everything else stay. "both" or no answer: everything."""
    want = TERRAIN.get(p.get("terrain"))
    return not want or d["g"] != "shoes" or not d.get("t") or d["t"] in want

def match(items, p):
    """Mirror of matchItems() on the site: items in stock in the profile's sizes, with best price."""
    favs = {b.lower() for b in p.get("brands") or []}
    groups, gender = set(p.get("groups") or []), p.get("gender")
    ca_only = (p.get("ships") or "ca") != "all"
    out = []
    for d in items:
        if d["g"] not in groups:
            continue
        if ca_only and d.get("ca") is False:   # Oct 7: fuel from US shops too (it used to skip "Ships from Canada")
            continue
        if gender and gender != "any" and d["sx"] and gender not in d["sx"]:
            continue
        ok = d["sz"]
        if d["g"] in SIZED:
            spec = (p.get("sizes") or {}).get(d["g"]) or {}
            want = {norm(x) for x in spec.get("sizes") or []}
            if d["g"] == "shoes":
                w = spec.get("width") or []
                want_wide, want_reg = "Wide" in w, (not w or "Regular" in w)
                G = {"men": "M", "women": "W"}.get(gender or "", "")
                # "Both" with its own women's sizes (site: men's + 1.5 until changed): women's sizes use that list
                want_w = {str(x) for x in spec.get("women") or []} if gender == "any" else set()
                def fits(e):
                    if e[0] == "OS":
                        return True
                    k = SHOE_KEY.match(str(e[0]))
                    if not k or k.group(3) == "N":
                        return False
                    if k.group(1) and G and k.group(1) != G:
                        return False
                    wide = k.group(3) == "W" or (not k.group(3) and d["w"])
                    if (wide and not want_wide) or (not wide and not want_reg):
                        return False
                    if want_w:
                        is_w = k.group(1) == "W" or (not k.group(1) and d["sx"] == ["women"])
                        return k.group(2) in (want_w if is_w else want)
                    return k.group(2) in want
                ok = [e for e in d["sz"] if fits(e)]
            else:
                ok = [e for e in d["sz"] if e[0] == "OS" or norm(e[0]) in want]
        elif acc_letters(d):
            want = {norm(x) for x in ((p.get("sizes") or {}).get("tops") or {}).get("sizes") or []}
            ok = [e for e in d["sz"] if e[0] == "OS" or e[0] in want]
        if not ok:
            continue
        pick = min(ok, key=lambda e: (e[1], -(e[3] if len(e) > 3 else e[1])))
        best = pick[1]
        reg = max(pick[3] if len(pick) > 3 else best, best)
        if p.get("max_price") and best > p["max_price"]:
            continue
        pct = round(100 * (1 - best / reg)) if reg > best else 0
        out.append({**d, "best": best, "reg": reg, "pct": pct, "ok": ok,
                    "url": size_url(d, pick), "fin": final_sale(d, pick),
                    "fav": d["b"].lower() in favs})
    return out

IG_URL = "https://www.instagram.com/thegearfox/"

# ---------- English / French (the subscriber's site language is saved in their profile as "lang") ----------
GROUP_FR = {"shoes": "Chaussures", "tops": "Hauts et manteaux", "bottoms": "Shorts et collants", "bras": "Soutiens-gorge de sport",
            "socks": "Bas", "gloves": "Gants", "headwear": "Casquettes et cache-cous", "packs": "Vestes et sacs d'hydratation",
            "gear": "Frontales, bâtons et gourdes", "watches": "Montres", "nutrition": "Nutrition"}
STR = {
    "en": dict(your_size="Your size: ", best_by="Best by {}", all_sizes="All sizes & stores →", abroad="Ships from outside Canada · converted to CAD, duties may apply",
               abroad_us="Ships from outside the US, duties may apply", final="Final sale: no returns",
               see_all="See all {} on sale →", watch_head="Your watchlist",
               changes=lambda n: f"{n} {'change' if n == 1 else 'changes'} this week",
               change_sizes="Change your sizes", unsubscribe="Unsubscribe", privacy="Privacy", follow="Follow us on Instagram",
               subject=lambda n, top: f"The Gear Fox: {n} deals in your size this week, up to {top}% off",
               subject_watch=lambda n: f"The Gear Fox: your watchlist moved, plus {n} deals in your size",
               hi="Hi", intro="{}, here are this week's sales on gear in your sizes, every price drop, big or small. Best deals first.",
               title="Your weekly deals", open_shop="Open your shop",
               first_gmail="<b>Your first Friday email!</b> Gmail sometimes files us under Promotions: drag this email to your "
                           "<b>Primary</b> tab and the next ones will land there.",
               first_other="<b>Your first Friday email!</b> Add deals@thegearfox.com to your contacts so the next ones "
                           "don't end up in junk.",
               fine="Prices and stock change daily; the product page has the final price.<br>"
                    "You get this because you signed up for Friday deals on The Gear Fox. Outfox full price.",
               was="was", all_deals="All deals", logo="logo-email.png"),
    "fr": dict(your_size="Votre taille : ", best_by="Meilleur avant le {}", all_sizes="Toutes les pointures et boutiques →",
               abroad="Expédié de l'extérieur du Canada · converti en $ CA, des droits peuvent s'appliquer",
               abroad_us="Expédié de l'extérieur des États-Unis, des droits peuvent s'appliquer", final="Vente finale : aucun retour",
               see_all="Voir les {} articles en solde →", watch_head="Vos favoris",
               changes=lambda n: f"{n} {'changement' if n == 1 else 'changements'} cette semaine",
               change_sizes="Modifier vos tailles", unsubscribe="Se désabonner", privacy="Confidentialité", follow="Suivez-nous sur Instagram",
               subject=lambda n, top: f"The Gear Fox : {n} aubaines à votre taille cette semaine, jusqu'à {top} % de rabais",
               subject_watch=lambda n: f"The Gear Fox : vos favoris ont bougé, et {n} aubaines à votre taille",
               hi="Bonjour", intro="{}, voici les soldes de la semaine dans vos tailles, chaque baisse de prix, petite ou grande. "
                                   "Les meilleures aubaines d'abord.",
               title="Vos aubaines de la semaine", open_shop="Voir ma boutique",
               first_gmail="<b>Votre premier courriel du vendredi!</b> Gmail nous classe parfois dans Promotions : glissez ce "
                           "courriel dans l'onglet <b>Principal</b> et les prochains arriveront au bon endroit.",
               first_other="<b>Votre premier courriel du vendredi!</b> Ajoutez deals@thegearfox.com à vos contacts pour que "
                           "les prochains n'aboutissent pas dans les indésirables.",
               fine="Les prix et les stocks changent chaque jour; le prix final est sur la page du produit.<br>"
                    "Vous recevez ce courriel parce que vous êtes abonné aux aubaines du vendredi de The Gear Fox. Flairez les aubaines.",
               was="avant", all_deals="Toutes les aubaines", logo="logo-email-fr.png"),
}


def lang_of(p):
    return "fr" if (p or {}).get("lang") == "fr" else "en"


def tr(lang, key, *a):
    v = STR[lang][key]
    return v(*a) if callable(v) else (v.format(*a) if a else v)


SIDE = {"us": False, "fx": 1.0}      # set per person in main(): the USA side shows US dollars and US wording (Oct 6, 2026)


def money(v, lang="en"):
    if SIDE["us"]:
        v = v / SIDE["fx"]
        return f"{v:.2f}".replace(".", ",") + " $ US" if lang == "fr" else f"US${v:.2f}"
    return f"{v:.2f}".replace(".", ",") + " $" if lang == "fr" else f"${v:.2f}"


def pct_txt(n, lang="en"):
    return f"−{n} %" if lang == "fr" else f"−{n}%"


def group_label(g, lang="en"):
    return GROUP_FR.get(g, GROUP_LABEL[g]) if lang == "fr" else GROUP_LABEL[g]


def shoe_label(s, lang="en"):
    k = SHOE_KEY.match(str(s))
    if not k:
        return str(s)
    return (k.group(1) or "") + k.group(2) + ((" large" if lang == "fr" else " wide") if k.group(3) == "W" else "")

def sizes_label(d, lang="en"):
    both = d["g"] == "shoes" and len({str(e[0])[:2] for e in d["ok"] if str(e[0])[:2] in ("M:", "W:")}) > 1
    labels = list(dict.fromkeys((shoe_label(e[0], lang) if both else re.sub(r"^[MW](?=\d)", "", shoe_label(e[0], lang)))
                                if d["g"] == "shoes" else e[0] for e in d["ok"]))
    if d["g"] in SIZED or acc_letters(d):
        labels = [x for x in labels if x != "OS"]
        if not labels:
            return ""
        order = ["2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL"]
        def k(v):
            try:
                return (0, float(re.sub(r"^[MW]|\s.*$", "", v)))
            except ValueError:
                return (1, order.index(norm(v)) if norm(v) in order else 99)
        labels.sort(key=k)
        return tr(lang, "your_size") + ", ".join(labels)
    return ""                     # odd labels ("T2", "115cm"): the store page explains them

E = html.escape
SHOE_PAGES = {}     # shoes/pages.json from the site: models with a price page (see scraper/shoe_pages.py)

def shoe_page_url(d, lang):
    """Link to the shoe's price page (every size, every store), when it has one."""
    if d.get("g") != "shoes" or not SHOE_PAGES or SITE_URL == "/" or SIDE["us"]:     # the shoe pages list Canadian stores
        return ""
    import shoe_pages as SP
    slug = SP.slugify(f'{d["b"]} {SP.base_model(d["n"])}')
    m = SHOE_PAGES.get(slug)
    if m and m.get("to"):
        slug, m = m["to"], SHOE_PAGES.get(m["to"])
    return f'{SITE_URL}{"chaussures" if lang == "fr" else "shoes"}/{slug}/?em=friday' if m else ""

def card(d, lang="en"):
    img = (f'<img src="{E(d["img"])}" width="84" height="84" alt="" '
           f'style="display:block;width:84px;height:84px;object-fit:contain;background:#fff;border-radius:8px">') if d.get("img") else ""
    fav = " ★" if d["fav"] else ""
    sz = sizes_label(d, lang)
    bb = f'<div style="font-size:12px;color:#B3261E;font-weight:600">{E(tr(lang, "best_by", d["bb"]))}</div>' if d.get("bb") else ""
    if d.get("ca") is False:
        bb += f'<div style="font-size:12px;color:#5C6660">{E(tr(lang, "abroad_us" if SIDE["us"] else "abroad"))}</div>'
    if d.get("fin"):
        bb += f'<div style="font-size:12px;color:#17201C;font-weight:600">{E(tr(lang, "final"))}</div>'
    sp = shoe_page_url(d, lang)
    cmp = (f'<div style="margin:4px 0 0 96px;font-family:Arial,Helvetica,sans-serif;font-size:12px">'
           f'<a href="{E(sp)}" style="color:#B8470A;font-weight:700">{E(tr(lang, "all_sizes"))}</a></div>') if sp else ""

    return f'''<tr><td style="padding:10px 0;border-top:1px solid #E3E7E2">
<a href="{E(d["url"])}" style="text-decoration:none;color:#17201C;display:block">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="96" valign="top">{img}</td>
<td valign="top" style="font-family:Arial,Helvetica,sans-serif">
<div style="font-size:13px;font-weight:700;color:#B8470A">{E(d["b"])}{fav}</div>
<div style="font-size:15px;line-height:1.3;margin:2px 0 4px">{E(nm(d["n"], lang))}</div>
<div><span style="font-size:20px;font-weight:800">{money(d["best"], lang)}</span>
<span style="font-size:13px;color:#5C6660;text-decoration:line-through;margin-left:6px">{money(d["reg"], lang)}</span>
<span style="font-size:13px;font-weight:800;background:#F26A1B;border:1px solid #17201C;border-radius:4px;padding:1px 5px;margin-left:6px">{pct_txt(d["pct"], lang)}</span></div>
<div style="font-size:12px;color:#5C6660;margin-top:3px">{E(sz)}</div>{bb}
</td></tr></table></a>{cmp}</td></tr>'''

def shop_link(p):
    """Site link that opens this person's tailored shop on any device."""
    import base64
    if p.get("token"):
        return f"{SITE_URL}?k={p['token']}"      # private key: loads their saved profile from the database
    keep = {k: p.get(k) for k in ("name", "gender", "ships", "activities", "groups", "sizes", "brands", "max_price", "lang")}
    b = base64.urlsafe_b64encode(json.dumps(keep, separators=(",", ":")).encode()).decode().rstrip("=")
    return f"{SITE_URL}?p={b}"          # query string survives email link-wrappers better than #

def build(p, sale, watch=None):
    lang = lang_of(p)
    shop = shop_link(p) + "&em=friday"      # Oct 8: visits from the Friday email show as "email-friday" in our analytics
    first = (p.get("name") or "").split(" ")[0] or tr(lang, "hi")
    sale.sort(key=lambda d: (-d["fav"], -score(d), d["best"]))
    sections, shown = [], 0
    order = [g for g in GROUP_LABEL if g in set(p.get("groups") or [])]
    for g in order:
        ds = [d for d in sale if d["g"] == g]
        if not ds or shown >= TOTAL:
            continue
        take = ds[:min(PER_GROUP, TOTAL - shown)]
        shown += len(take)
        more = (f'<tr><td style="padding:6px 0 0;font:13px Arial,sans-serif"><a href="{E(shop)}" style="color:#B8470A">'
                f'{E(tr(lang, "see_all", len(ds)))}</a></td></tr>') if len(ds) > len(take) else ""
        sections.append(f'''<tr><td style="padding:22px 0 4px;font:800 20px Arial,Helvetica,sans-serif;color:#17201C">
{E(group_label(g, lang))} <span style="font:400 14px Arial,sans-serif;color:#5C6660">{len(ds)}</span></td></tr>
{"".join(card(d, lang) for d in take)}{more}''')
    has_watch = bool(watch and (watch["drops"] or watch["backs"]))
    if has_watch:
        import alerts as A
        rows = ("".join(A.alert_row("drop", a, lang) for a in watch["drops"])
                + "".join(A.alert_row("back", a, lang) for a in watch["backs"]))
        n = len(watch["drops"]) + len(watch["backs"])
        sections.insert(0, f'''<tr><td style="padding:22px 0 4px;font:800 20px Arial,Helvetica,sans-serif;color:#17201C">
{E(tr(lang, "watch_head"))} <span style="font:400 14px Arial,sans-serif;color:#5C6660">{E(tr(lang, "changes", n))}</span></td></tr>{rows}''')
    top = max([d["pct"] for d in sale] or [0])
    links = [f'<a href="{E(shop)}" style="color:#5C6660">{E(tr(lang, "change_sizes"))}</a>']
    if p.get("token"):
        links.append(f'<a href="{E(SITE_URL)}?unsub={p["token"]}" style="color:#5C6660">{E(tr(lang, "unsubscribe"))}</a>')
    links.append(f'<a href="{E(SITE_URL)}privacy.html" style="color:#5C6660">{E(tr(lang, "privacy"))}</a>')
    links.append(f'<a href="{IG_URL}" style="color:#5C6660">{E(tr(lang, "follow"))} @thegearfox</a>')
    footer_links = " · ".join(links) + (f"<br>The Gear Fox · {E(ADDRESS)}" if ADDRESS else "")
    subject = tr(lang, "subject_watch", len(sale)) if has_watch else tr(lang, "subject", len(sale), top)
    intro = E(tr(lang, "intro", first))
    first_note = ""                       # only in someone's first Friday email (nothing recorded in weekly_sent_at yet)
    if not p.get("_sent"):
        gmail = re.search(r"@(gmail|googlemail)\.com$", (p.get("email") or "").lower())
        first_note = (f'<tr><td style="padding:4px 20px 14px"><div style="background:#FFF4EC;border:1.5px solid #F26A1B;border-radius:10px;'
                      f'padding:10px 14px;font:14px/1.45 Arial,sans-serif;color:#17201C">{tr(lang, "first_gmail" if gmail else "first_other")}</div></td></tr>')
    body = f'''<!doctype html><html lang="{lang}"><body style="margin:0;background:#EEF1EC">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">
<tr><td style="padding:18px 20px 0;text-align:center"><a href="{E(shop)}"><img src="{E(SITE_URL)}{tr(lang, "logo")}" width="260" alt="The Gear Fox" style="display:inline-block;width:260px;max-width:80%;height:auto;border:0"></a></td></tr>
<tr><td style="padding:8px 20px 6px;text-align:center;font:800 28px Arial Narrow,Arial,sans-serif;color:#17201C">{E(tr(lang, "title"))}</td></tr>
<tr><td style="padding:0 20px 8px;text-align:center;font:15px/1.45 Arial,sans-serif;color:#5C6660">{intro}</td></tr>
{first_note}<tr><td style="padding:0 20px 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(sections)}</table></td></tr>
<tr><td style="padding:14px 20px 22px;text-align:center;border-top:2px dashed #CBD2CC">
<a href="{E(shop)}" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 20px;font:800 16px Arial,sans-serif;text-decoration:none">{E(tr(lang, "open_shop"))}</a>
<div style="font:12px/1.4 Arial,sans-serif;color:#5C6660;margin-top:14px">{tr(lang, "fine")}<br>
{footer_links}</div></td></tr>
</table></td></tr></table></body></html>'''
    text = f"{subject}\n\n" + "\n".join(
        f"- {d['b']} {d['n']}: {money(d['best'], lang)} ({tr(lang, 'was')} {money(d['reg'], lang)}, {pct_txt(d['pct'], lang)}) {d['url']}"
        for d in sale[:TOTAL]) + f"\n\n{tr(lang, 'all_deals')}: {shop}\n" + (
        f"{tr(lang, 'unsubscribe')}: {SITE_URL}?unsub={p['token']}\n" if p.get("token") else "") + (
        f"The Gear Fox, {ADDRESS}\n" if ADDRESS else "")
    return subject, body, text


def subscribers():
    """Confirmed, still-subscribed people from Supabase, as profile dicts with email + token."""
    if not (SB_URL and SB_KEY):
        print("Supabase not configured, using email/profiles.json only")
        return []
    r = requests.get(f"{SB_URL}/rest/v1/subscribers", timeout=60,
                     params={"select": "email,profile,token,weekly_sent_at", "confirmed_at": "not.is.null", "unsubscribed_at": "is.null"},
                     headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"} if SB_KEY.count(".") == 2
                     else {"apikey": SB_KEY})
    r.raise_for_status()
    out = [{**(row["profile"] or {}), "email": row["email"], "token": row["token"], "_sent": row.get("weekly_sent_at")}
           for row in r.json()]
    print(f"{len(out)} subscribers in Supabase")
    return out

# ---------- 7am in each subscriber's own time zone ----------
# The workflow runs every hour on Friday morning (UTC). Each run sends to the people for whom it is now
# Friday, 7am or later, and who haven't had this week's email (weekly_sent_at, saved after each send).
# The time zone comes from the browser at sign-up (profile "tz"); without one: French -> Eastern, else Pacific.
SEND_HOUR, SEND_DAY = 7, 4          # 7am, Friday (Monday = 0)
def local_now(p, now=None):
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    tz = p.get("tz") or ("America/Toronto" if lang_of(p) == "fr" else "America/Vancouver")
    try:
        z = ZoneInfo(tz)
    except Exception:
        z = ZoneInfo("America/Vancouver")
    return (now or datetime.now(timezone.utc)).astimezone(z)

def due(p, now=None):
    from datetime import datetime, timezone, timedelta
    now = now or datetime.now(timezone.utc)
    t = local_now(p, now)
    if t.weekday() != SEND_DAY or t.hour < SEND_HOUR:
        return False
    if not p.get("token"):                   # old file-based profiles: no record of sends, so only in the 7am hour
        return t.hour == SEND_HOUR
    sent = p.get("_sent")
    if sent:
        try:
            if now - datetime.fromisoformat(sent.replace("Z", "+00:00")) < timedelta(days=3):
                return False                 # already had this week's email
        except Exception:
            pass
    return True

def mark_sent(p):
    from datetime import datetime, timezone
    if not p.get("token"):
        return
    try:
        import alerts as A
        A.sb("PATCH", f"subscribers?token=eq.{p['token']}", json={"weekly_sent_at": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        print(f"  could not record the send for {p['email']}: {e}")

def main():
    profiles = []
    f = ROOT / "email" / "profiles.json"
    if f.exists():
        profiles = json.loads(f.read_text())
        if isinstance(profiles, dict):
            profiles = [profiles]
    db = subscribers()
    seen = {p["email"].lower() for p in db}
    profiles = db + [p for p in profiles if (p.get("email") or "").lower() not in seen]
    if MANUAL and not SEND_TO:
        print("Manual run with no 'send to' address: nothing sent. Type your email in the box (or 'everyone').")
        return 1
    if SEND_TO and SEND_TO != "everyone":
        want = {e.strip() for e in SEND_TO.split(",") if e.strip()}
        profiles = [p for p in profiles if (p.get("email") or "").lower() in want]
        missing = want - {p["email"].lower() for p in profiles}
        for e in sorted(missing):
            print(f"{e}: not a confirmed subscriber, so no email. Sign up on the site and confirm first.")
        print(f"TEST SEND to {len(profiles)} of the subscribers only")
        if not profiles:
            return 1
    if not SEND_TO:                          # the scheduled runs: only people for whom it's 7am (or later) now
        before = len(profiles)
        profiles = [p for p in profiles if due(p)]
        print(f"{len(profiles)} of {before} subscribers are due now (Friday, 7am or later where they live)")
    if not ADDRESS:
        print("WARNING: MAILING_ADDRESS is not set; CASL requires a postal address in the footer")
    if DEALS_URL:
        data = requests.get(DEALS_URL, timeout=60).json()
    else:
        data = json.loads((ROOT / "site" / "deals.json").read_text())
    items = data.get("items", [])
    print(f"{len(items)} items in deals.json (updated {data.get('updated')})")
    us_items = []                          # the USA side (Oct 6, 2026): people who shop from the US get US stores
    if any(p.get("country") == "us" for p in profiles):
        try:
            us_items = (requests.get(DEALS_URL.replace("deals.json", "deals-us.json"), timeout=60).json() if DEALS_URL
                        else json.loads((ROOT / "site" / "deals-us.json").read_text())).get("items", [])
            print(f"{len(us_items)} items on the USA side")
            SIDE["fx"] = float((data.get("fx") or {}).get("USD") or 1.37)
        except Exception as e:
            print(f"  (no USA deals: {e}; US subscribers get the Canadian list)")
    try:                                   # shoe price pages, for the "All sizes & stores" links
        SHOE_PAGES.update(requests.get(SITE_URL + "shoes/pages.json", timeout=30).json() if DEALS_URL
                          else json.loads((ROOT / "site" / "shoes" / "pages.json").read_text()))
    except Exception as e:
        print(f"  (no shoe pages list: {e})")
    watch_news = {}
    if SB_URL and SB_KEY and any(p.get("token") for p in profiles):
        try:
            import alerts as A
            from datetime import datetime, timezone
            by_key, by_us = {}, {}
            for d in items:
                by_key.setdefault(A.item_key(d), []).append(d)
            for d in us_items:
                by_us.setdefault(A.item_key(d), []).append(d)
            watch_news = A.evaluate_sides(A.fetch_rows(), by_key, by_us, datetime.now(timezone.utc), cooldown=False)
            print(f"watchlist news for {sum(1 for w in watch_news.values() if w['drops'] or w['backs'])} people")
        except Exception as e:                      # the deals email still goes out without it
            print(f"watchlist news skipped: {e}")
    failed = 0
    for p in profiles:
        if not p.get("email"):
            continue
        SIDE["us"] = p.get("country") == "us" and bool(us_items)
        side = us_items if SIDE["us"] else items
        sale = [d for d in match(side, p) if d["pct"] >= 1 and terrain_ok(d, p)]      # anything below full price
        who = p["email"]
        watch = watch_news.get(p.get("token"))
        has_watch = bool(watch and (watch["drops"] or watch["backs"]))
        if not sale and not has_watch:
            print(f"{who}: nothing on sale in their sizes this week, no email sent")
            continue
        subject, body, text = build(p, sale, watch)
        if DRY:
            out = ROOT / "email" / "preview.html"
            out.write_text(body)
            print(f"{who}: DRY RUN, {len(sale)} deals, subject: {subject!r}, wrote {out}")
            continue
        r = requests.post("https://api.resend.com/emails", timeout=60,
                          headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                          json={"from": FROM, "to": [who], "subject": subject, "html": body, "text": text,
                                **({"headers": {"List-Unsubscribe": f"<{SITE_URL}?unsub={p['token']}>"}} if p.get("token") else {})})
        if r.ok:
            print(f"{who}: sent {len(sale)} deals" + (" + watchlist news" if has_watch else ""))
            if not SEND_TO:
                mark_sent(p)
            if watch:
                import alerts as A
                for wid, upd in watch["updates"]:
                    try:
                        A.sb("PATCH", f"watches?id=eq.{wid}", json=upd)
                    except Exception as e:
                        print(f"  could not update watch {wid}: {e}")
        else:
            failed += 1
            print(f"{who}: FAILED {r.status_code} {r.text[:300]}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
