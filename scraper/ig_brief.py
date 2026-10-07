#!/usr/bin/env python3
"""The Gear Fox Wednesday Instagram brief (for Bastien, not subscribers).

Picks this week's best running-shoe deals from the live sale.json and emails:
  - 3 picks for his Reel, with the facts that make each one good
  - a short script to say (EN and FR) and on-screen text
  - the "Top 5" graphic for his Story (EN + FR PNGs, 1080x1350), drawn with Chromium
  - a ready-made Reel video, EN + FR (scraper/ig_reel.py: this week's real price drops in his sizes)

Picks: 3 shoes (30-70% off, normally $130+, 7+ sizes at that price, 3+ of the common ones) and 2 clothing\n(a top and a bottom: $60+, S, M and L in stock at that price), ship from Canada, no spikes or boots, one per brand,
well-known running brands first.

Env:   RESEND_API_KEY, HEALTH_EMAIL (where it goes; default hello@thegearfox.com), FROM_EMAIL, SALE_URL
Usage: python scraper/ig_brief.py [--dry-run]   (--dry-run writes email/ig-brief.html and the PNGs, sends nothing)
"""
import base64
import html
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests

import livecheck

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "email"
TO = (os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com").strip()
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
SALE_URL = os.environ.get("SALE_URL", "https://thegearfox.com/sale.json")
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
E = html.escape

SKIP = re.compile(r"spike|\b[LM]D(-X)?\b|\bXC\b|cross[- ]?country|\bsprint|dragonfly|maxfly|ja fly|\bvictory\b|\bpointes?\b|"
                  r"avanti|evospeed|hiking|\bhike\b|boot", re.I)
MIN_SIZES = 7
COMMON = {"men's": [9, 9.5, 10, 10.5, 11], "women's": [7, 7.5, 8, 8.5, 9]}   # the sizes most runners wear
GEAR_BRANDS = {"salomon", "garmin", "coros", "suunto", "petzl", "black diamond", "nathan", "ultimate direction", "leki",
               "naked", "kogalla", "ledlenser", "osprey", "camelbak", "patagonia", "arc'teryx", "polar", "raidlight", "inov8"}
POPULAR = {"hoka", "brooks", "asics", "nike", "saucony", "new balance", "on", "salomon", "adidas", "altra", "mizuno", "puma"}


def store_names():
    s = (ROOT / "site" / "index.html").read_text()
    block = re.search(r"const STORES=(\{.*?\});", s, re.S).group(1)
    return dict(re.findall(r'"([^"]+)":\["([^"]+)"', block))


def clean(n):
    """"Men's Olympus 6 Trail Running Shoe" -> "Olympus 6 Trail - Men's"."""
    g = re.match(r"^(Men's|Women's)\s+(.*)", n)
    if g:
        n = g.group(2) + " - " + g.group(1)
    n = re.sub(r"\s+with\s+[^-]+(?= - |$)", "", n)          # "Vest with 1.5L Bladder - 6L" -> "Vest - 6L"
    return re.sub(r"\s+(Trail )?Running Shoes?(?= - |$)", lambda m: " Trail" if m.group(1) else "", n)


CLOTH_SKIP = re.compile(r"\b(boxer|brief|underwear|bra|hipkini|thong|swim|bikini|jeans|denim)\b", re.I)
LETTERS = ["2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL"]


def sex_of(who, i):
    return ("women" if who == "women's" or (not who and i.get("sx") == ["women"]) else
            "men" if who == "men's" or i.get("sx") == ["men"] else "unisex")


def candidate(i, stores):
    """One deal (best price), with only the sizes at that price and store, or None if it doesn't qualify."""
    g = i["g"]
    if g not in ("shoes", "tops", "bottoms", "packs", "gear", "watches") or not i.get("img") or not i.get("ca"):
        return None
    if (g == "shoes" and (SKIP.search(i["n"]) or i.get("t") in ("spike", "hike"))) or (g != "shoes" and CLOTH_SKIP.search(i["n"])):
        return None
    sale = [e for e in i["sz"] if e[1] < e[3]]
    if not sale:
        return None
    e = min(sale, key=lambda e: e[1])
    pct = round(100 * (1 - e[1] / e[3]))
    if not 30 <= pct <= 70 or e[3] < {"shoes": 130, "tops": 60, "bottoms": 60}.get(g, 80):
        return None
    same = [x[0] for x in i["sz"] if x[2] == e[2] and abs(x[1] - e[1]) < 0.01 and not x[0].endswith("~N")]
    if g == "shoes":
        # each size once: a unisex shoe is stored as both "M:8" and "W:9.5" (the same shoe), so count the
        # men's numbers, or the women's when there are none
        men = [k[2:] for k in same if k.startswith("M:")]
        women = [k[2:] for k in same if k.startswith("W:")]
        plain = [k for k in same if not k[:2] in ("M:", "W:")]
        nums, who = (men, "men's") if men else (women, "women's") if women else (plain, "")
        sizes = sorted({float(k.split("~")[0]) for k in nums if re.match(r"^\d+(\.\d)?(~W)?$", k)})
        common = COMMON["women's" if sex_of(who, i) == "women" else "men's"]
        if len(sizes) < MIN_SIZES or sum(1 for v in common if v in sizes) < 3:
            return None                  # featured shoes must fit most runners: 7+ sizes, 3+ of the common ones
    elif g in ("tops", "bottoms"):
        who = ""
        sizes = [k for k in LETTERS if k in same]
        if len(sizes) < 4 or not {"S", "M", "L"} <= set(sizes):
            return None                  # clothing: 4+ letter sizes including S, M and L
    else:
        who = ""                         # gear and accessories: one size fits all, or S, M and L for vests
        sizes = [k for k in LETTERS if k in same]
        if "OS" in same:
            sizes = []
        elif not {"S", "M", "L"} <= set(sizes):
            return None
    host = urlparse(i["of"][e[2]]).hostname.replace("www.", "")
    known = i["b"].lower() in (POPULAR if g in ("shoes", "tops", "bottoms") else GEAR_BRANDS | POPULAR)
    return dict(score=pct + len(sale) * 0.5 + (15 if known else 0) + (min(e[3], 300) / 20 if g not in ("shoes", "tops", "bottoms") else 0), g=g, t=i.get("t"), b=i["b"],
                n=clean(i["n"]), pct=pct, price=e[1], reg=e[3], store=stores.get(host, host), img=i["img"], sizes=sizes,
                who=who, sex=sex_of(who, i), url=i["of"][e[2]], vid=e[4] if len(e) > 4 else None)


DROPPED = []                             # picks the store's own page no longer shows on sale (listed in the email)


def live(x):
    ok = livecheck.still_on_sale(x["url"], x["price"], x.get("vid"))
    if not ok:
        DROPPED.append(f"{x['b']} {x['n']} ({x['store']}: " + ("couldn't check" if ok is None else "not at that price any more") + ")")
    return ok


def picks(items, stores):
    """2 shoes + 2 clothing (a top and a bottom) + 1 piece of gear (vest, watch, light, poles…), one per brand,
    a mix of men's and women's."""
    cands = sorted(filter(None, (candidate(i, stores) for i in items)), key=lambda x: -x["score"])
    brands, per_sex = set(), {}

    def take(pool, k, cap=3):
        got = []
        for x in pool:
            if len(got) == k:
                break
            if x["b"].lower() in brands or per_sex.get(x["sex"], 0) >= 3 or sum(1 for y in got if y["sex"] == x["sex"]) >= cap:
                continue
            if not live(x):              # Oct 7: a store ended its sale after the morning read; feature only what's on sale now
                continue
            got.append(x)
            brands.add(x["b"].lower())
            per_sex[x["sex"]] = per_sex.get(x["sex"], 0) + 1
        return got

    shoes = take([x for x in cands if x["g"] == "shoes"], 2, cap=1)     # one men's (or unisex) and one women's
    top = take([x for x in cands if x["g"] == "tops"], 1)
    bottom = take([x for x in cands if x["g"] == "bottoms"], 1)
    clothes = top + bottom
    if len(clothes) < 2:                 # no good top or bottom this week: take another of either
        clothes += take([x for x in cands if x["g"] in ("tops", "bottoms") and x not in clothes], 2 - len(clothes))
    gear = take([x for x in cands if x["g"] in ("packs", "gear", "watches")], 1)
    # shoe, clothing, gear, shoe, clothing: the Reel's 3 are a shoe, a piece of clothing and an accessory
    order = shoes[:1] + clothes[:1] + gear + shoes[1:] + clothes[1:]
    reel = order[:3]
    if len(reel) == 3 and len({x["sex"] for x in reel}) == 1:     # the Reel's 3 shouldn't all be men's or all women's
        other = next((x for x in order[3:] if x["sex"] != reel[0]["sex"] and x["g"] == reel[2]["g"]), None)
        if other:
            i, j = order.index(reel[2]), order.index(other)
            order[i], order[j] = order[j], order[i]
    chosen = order
    return chosen


def money(v, lang):
    return f"{v:,.2f} $".replace(",", " ").replace(".", ",") if lang == "fr" else f"${v:,.2f}"


def size_range(s):
    """A short list ("6, 6.5, 8, 10.5") when there are few sizes, else a range ("7–12")."""
    f = lambda v: v if isinstance(v, str) else str(int(v)) if v == int(v) else str(v)
    return ", ".join(f(v) for v in s) if len(s) <= 6 else f"{f(s[0])}–{f(s[-1])}"


T = {
    "en": dict(kicker="This week's", title="Top 5 deals", sub="Running gear on sale, found across {n} stores", at="at",
               sizes="sizes", who={"men's": "men's", "women's": "women's"}, cta1="Your size?", cta3="Every deal, filtered to your size. Free.", gender={}),
    "fr": dict(kicker="Cette semaine", title="Top 5 aubaines", sub="Équipement de course en solde, dans {n} boutiques", at="chez",
               sizes="tailles", who={"men's": "homme", "women's": "femme"}, cta1="Ta taille?", cta3="Chaque aubaine, filtrée à ta taille. Gratuit.",
               gender={"Men's": "Homme", "Women's": "Femme", "Unisex": "Unisexe"}),
}


def name(n, lang):
    for a, b in T[lang]["gender"].items():
        n = n.replace(a, b)
    return n


def sizes_label(x, lang):
    """"men's sizes" / "tailles homme"; plain "sizes" when the shoe has one gender."""
    t, w = T[lang], x.get("who")
    if not w:
        return t["sizes"]
    return f"{t['who'][w]} {t['sizes']}" if lang == "en" else f"{t['sizes']} {t['who'][w]}"


def graphic(chosen, lang, n_stores):
    t = T[lang]
    pct = lambda p: f"−{p}&nbsp;%" if lang == "fr" else f"−{p}%"
    rows = "".join(f'''<div class="row"><div class="pic"><img src="{E(x['img'])}"></div><div class="info">
<div class="b">{E(x['b'])}</div><div class="n">{E(name(x['n'], lang))}</div>
<div class="p"><b>{money(x['price'], lang)}</b><s>{money(x['reg'], lang)}</s><span class="pct">{pct(x['pct'])}</span></div>
<div class="s">{t['at']} {E(x['store'])}{(' · ' + sizes_label(x, lang) + ' ' + size_range(x['sizes'])) if x['sizes'] else ''}</div></div></div>''' for x in chosen)
    logo = "data:image/png;base64," + base64.b64encode((ROOT / "site" / "logo.png").read_bytes()).decode()
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;800&display=swap');
*{{box-sizing:border-box;margin:0}}body{{width:1080px;height:1350px;background:#EEF1EC;font-family:Inter,Arial,sans-serif;color:#17201C;padding:48px 60px 52px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;align-items:flex-start}}.logo{{height:92px}}
.k{{font:800 30px Inter;color:#B8470A;text-transform:uppercase;letter-spacing:2px}}.t{{font:64px/1 'Archivo Black',Arial Black;margin-top:6px}}.sub{{font:500 26px Inter;color:#5C6660;margin-top:12px}}
.list{{margin-top:26px;display:flex;flex-direction:column;gap:14px}}
.row{{display:flex;gap:26px;background:#fff;border:3px solid #17201C;border-radius:22px;padding:12px 20px;align-items:center}}
.pic{{width:170px;height:128px;flex:none;display:flex;align-items:center;justify-content:center;background:#F6F7F4;border-radius:14px;overflow:hidden}}.pic img{{max-width:100%;max-height:100%;object-fit:contain}}
.b{{font:800 24px Inter;color:#B8470A}}.n{{font:600 27px/1.15 Inter;margin:2px 0 6px}}
.p b{{font:800 36px Inter}}.p s{{font:500 24px Inter;color:#5C6660;margin-left:12px}}.pct{{font:800 26px Inter;background:#F26A1B;border:2px solid #17201C;border-radius:8px;padding:2px 10px;margin-left:14px;vertical-align:6px}}
.s{{font:500 22px Inter;color:#5C6660;margin-top:6px}}
.cta{{margin-top:22px;background:#17201C;color:#fff;border-radius:22px;padding:24px 30px;display:flex;justify-content:space-between;align-items:center}}
.cta .a{{font:800 34px Inter}}.cta .u{{font:42px 'Archivo Black';color:#F26A1B}}.cta .c{{font:500 22px Inter;color:#CBD2CC;margin-top:4px}}
</style></head><body>
<div class="top"><div><div class="k">{t['kicker']}</div><div class="t">{t['title']}</div><div class="sub">{t['sub'].format(n=n_stores)}</div></div><img class="logo" src="{logo}"></div>
<div class="list">{rows}</div>
<div class="cta"><div><div class="a">{t['cta1']}</div><div class="c">{t['cta3']}</div></div><div class="u">thegearfox.com</div></div>
</body></html>'''


def render_png(page_html, path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        pg = b.new_page(viewport={"width": 1080, "height": 1350})

        def through(route):            # fetch images and fonts ourselves (works behind proxies too)
            try:
                route.fulfill(response=route.fetch())
            except Exception:
                route.abort()
        pg.route("**/*", through)
        pg.set_content(page_html, wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(1500)
        pg.screenshot(path=str(path))
        b.close()


def short(x):
    """Spoken shoe name: "Saucony Endorphin Elite 2"."""
    return f"{x['b']} " + re.sub(r"\s+-\s+(Men's|Women's|Unisex)$", "", x["n"])


def spoken_pct(p, lang):
    if 48 <= p <= 52:
        return "half price" if lang == "en" else "à moitié prix"
    return f"{p}% off" if lang == "en" else f"{p} % de rabais"


def reel_section(reel, p, h):
    """This week's ready-made Reel (scraper/ig_reel.py): the two videos are attached; what to say over them."""
    rows = "".join(f"<li>{E(x['name'])}: <b>{money(x['now'], 'en')}</b> in your size, was {money(x['then'], 'en')} a week ago "
                   f"(down ${x['drop']:.0f}) at {E(x['store'])}. <a href=\"{E(x['url'])}\">Check it</a></li>" for x in reel["picks"])
    out = [f'<div {h}>0. This week\'s Reel video (attached: reel-en.mp4, reel-fr.mp4)</div>',
           f'<p {p}>Real price drops from the last 7 days, in your sizes (11 / M), recorded on the site with the safe bands. '
           'Film yourself over it (bottom-left corner, captions on the site part, never on the bottom band).</p>',
           f'<ul style="font:15px/1.5 Arial,sans-serif">{rows}</ul>']
    for lang, label in (("en", "English"), ("fr", "Français")):
        t = reel["script"][lang]
        out.append(f'<p {p}><b>{label}</b><br>Big text, first second: <b>{E(t["hook"])}</b><br>'
                   f'0–2.5 s (the first card): {E(t["open"])}<br>Heart blinking: {E(t["how"])}<br>'
                   f'Watchlist: {E(t["a"])} {E(t["b"])}<br>End: {E(t["end"])}</p>'
                   f'<p {p}>Caption:<br>{E(t["caption"]).replace(chr(10), "<br>")}</p>')
    out.append(f'<p {p}>Post the English one first, the French one 2–3 days later.</p>')
    return "".join(out)


def brief(chosen, when, reel=None):
    top = chosen[:3]
    ord_en, ord_fr = ["First", "Then", "And"], ["D'abord", "Ensuite", "Et enfin"]
    script_en = " ".join(["Three deals I'd actually buy this week."] +
                         [f"{ord_en[k]} the {short(x)}, {spoken_pct(x['pct'], 'en')} at {x['store']}." for k, x in enumerate(top)] +
                         ["Want deals like these in your size every Friday? Link in bio."])
    script_fr = " ".join(["Trois aubaines que j'achèterais cette semaine."] +
                         [f"{ord_fr[k]}, {short(x)}, {spoken_pct(x['pct'], 'fr')} chez {x['store']}." for k, x in enumerate(top)] +
                         ["Tu veux des aubaines comme ça dans ta taille chaque vendredi? Lien dans la bio."])
    who = lambda x: {"Men's": "men's", "Women's": "women's"}.get(x["n"].split(" - ")[-1], "unisex")
    li = "".join(f'''<li style="margin:0 0 12px"><b>{E(short(x))}</b> ({who(x)}):
<b>{money(x['price'], 'en')}</b> instead of {money(x['reg'], 'en')}, −{x['pct']}% at {E(x['store'])}{(', in ' + (x['who'] + ' ' if x['who'] else '') + 'sizes ' + size_range(x['sizes'])) if x['sizes'] else ', one size'} (as of this morning).
<a href="{E(x['url'])}">Check it</a></li>''' for x in top)
    rest = "".join(f"<li>{E(short(x))}: {money(x['price'], 'en')} (−{x['pct']}%) at {E(x['store'])}</li>" for x in chosen[3:])
    p = 'style="font:15px/1.5 Arial,sans-serif;color:#17201C;margin:0 0 14px"'
    h = 'style="font:800 18px Arial,sans-serif;color:#B8470A;margin:22px 0 8px"'
    reel_html = reel_section(reel, p, h) if reel else ""
    checked = datetime.now(ZoneInfo("America/Vancouver")).strftime("%-I:%M%p").lower() + " Vancouver"
    body = f'''<div style="max-width:620px;margin:0 auto;padding:18px">
<p {p}>Hi Bastien, here's this week's Instagram kit, picked from this morning's deals ({when}).
Post the Reel today (Wednesday) and the Top 5 graphic as a Story.</p>
<p {p}>✓ Every price below was checked on the store's own page at {checked} (sales end without warning: post today).
{f"Left out, no longer on sale: {E('; '.join(DROPPED[:6]))}." if DROPPED else ""}</p>
{reel_html}
<div {h}>1. Your 3 picks for the Reel</div><ol style="font:15px/1.5 Arial,sans-serif;padding-left:20px">{li}</ol>
<p {p}>Add one line of your own on each (fit, what you'd use it for): your opinion is what people follow.</p>
<div {h}>2. What to say (15–25 seconds)</div>
<p {p}><b>EN:</b> {E(script_en)}</p><p {p}><b>FR :</b> {E(script_fr)}</p>
<div {h}>3. On-screen text</div>
<p {p}>Opening (first 2–3 s): <b>3 deals I'd buy this week 🦊</b> / <b>3 aubaines que j'achèterais 🦊</b><br>
On each shoe: the shoe name and price, e.g. <b>{E(short(top[0]))} · {money(top[0]['price'], 'en')}</b><br>
End: <b>Your size → link in bio</b> / <b>Ta taille → lien dans la bio</b></p>
<div {h}>4. Caption</div>
<p {p}>3 running deals I'd actually buy this week 👟 Every deal on The Gear Fox is filtered to YOUR size, from 50+ stores. Free. Link in bio.<br>
Trois aubaines de course que j'achèterais cette semaine 👟 Chaque aubaine filtrée à TA taille, dans plus de 50 boutiques. Gratuit. Lien dans la bio.<br>
#runningcanada #trailrunning #courseapied #runninggear</p>
<div {h}>5. Story: Top 5 graphic</div>
<p {p}>Attached: <b>top5-en.png</b> and <b>top5-fr.png</b>. Post one or both as Stories and add them to a "Deals" highlight.
No link sticker for now (Instagram held back the last one); "link in bio" works.</p>
{f'<p {p}>The other two in the graphic:</p><ul style="font:15px/1.5 Arial,sans-serif">{rest}</ul>' if rest else ''}
<p style="font:12px/1.4 Arial,sans-serif;color:#5C6660;margin-top:24px">Sent every Wednesday by The Gear Fox (scraper/ig_brief.py). Only to you.</p></div>'''
    return body, script_en, script_fr


def main():
    when = datetime.now(ZoneInfo("America/Vancouver")).strftime("%A %b %-d")
    data = requests.get(SALE_URL, timeout=60).json()
    items = data.get("items", [])
    stores = store_names()
    n_stores = len(stores)
    chosen = picks(items, stores)
    if len(chosen) < 3:
        print(f"only {len(chosen)} picks this week; nothing sent")
        return 1
    OUT.mkdir(exist_ok=True)
    pngs = {}
    for lang in ("en", "fr"):
        path = OUT / f"top5-{lang}.png"
        render_png(graphic(chosen, lang, n_stores), path)
        pngs[lang] = path
    reel = None
    try:                                         # the ready-made Reel; the rest of the kit goes out even if it fails
        import ig_reel
        reel = ig_reel.make(OUT, items)
    except Exception as e:
        print(f"reel video skipped: {e}")
    body, *_ = brief(chosen, when, reel)
    for x in chosen:
        print(f"- {x['pct']}% {short(x)} {x['price']} at {x['store']}")
    if DRY:
        (OUT / "ig-brief.html").write_text(body)
        print(f"DRY RUN: wrote {OUT / 'ig-brief.html'} and the PNGs")
        return 0
    r = requests.post("https://api.resend.com/emails", timeout=60,
                      headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                      json={"from": FROM, "to": [TO], "subject": f"Instagram kit for {when}: " + ("Reel video + " if reel else "") + "3 picks + Top 5 graphic",
                            "html": body,
                            "attachments": [{"filename": f"top5-{l}.png", "content": base64.b64encode(p.read_bytes()).decode()}
                                            for l, p in pngs.items()] +
                                           [{"filename": f"reel-{l}.mp4", "content": base64.b64encode(p.read_bytes()).decode()}
                                            for l, p in (reel["videos"].items() if reel else [])]})
    print(f"emailed {TO}: HTTP {r.status_code} {r.text[:200]}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
