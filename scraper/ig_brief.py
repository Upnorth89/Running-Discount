#!/usr/bin/env python3
"""The Gear Fox Wednesday Instagram brief (for Bastien, not subscribers).

Picks this week's best running-shoe deals from the live sale.json and emails:
  - 3 picks for his Reel, with the facts that make each one good
  - a short script to say (EN and FR) and on-screen text
  - the "Top 5" graphic for his Story (EN + FR PNGs, 1080x1350), drawn with Chromium

Picks: shoes at 30-70% off, normally $130+, in 6+ sizes, ship from Canada, no spikes or boots, one per brand,
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

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "email"
TO = (os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com").strip()
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
SALE_URL = os.environ.get("SALE_URL", "https://thegearfox.com/sale.json")
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
E = html.escape

SKIP = re.compile(r"spike|\b[LM]D(-X)?\b|\bXC\b|cross[- ]?country|\bsprint|dragonfly|maxfly|ja fly|\bvictory\b|\bpointes?\b|"
                  r"avanti|evospeed|hiking|\bhike\b|boot", re.I)
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
    return re.sub(r"\s+(Trail )?Running Shoes?(?= - |$)", lambda m: " Trail" if m.group(1) else "", n)


def picks(items, stores, n=5):
    out = []
    for i in items:
        if i["g"] != "shoes" or not i.get("img") or not i.get("ca") or SKIP.search(i["n"]):
            continue
        sale = [e for e in i["sz"] if e[1] < e[3]]
        if not sale:
            continue
        e = min(sale, key=lambda e: e[1])
        pct = round(100 * (1 - e[1] / e[3]))
        if not 30 <= pct <= 70 or e[3] < 130:
            continue
        # only the sizes at this exact price and store, each size once: a unisex shoe is stored as both
        # "M:8" and "W:9.5" (the same shoe), so count the men's numbers, or the women's when there are none
        same = [x[0] for x in i["sz"] if x[2] == e[2] and abs(x[1] - e[1]) < 0.01 and not x[0].endswith("~N")]
        men = [k[2:] for k in same if k.startswith("M:")]
        women = [k[2:] for k in same if k.startswith("W:")]
        plain = [k for k in same if not k[:2] in ("M:", "W:")]
        nums, who = (men, "men's") if men else (women, "women's") if women else (plain, "")
        sizes = sorted({float(k.split("~")[0]) for k in nums if re.match(r"^\d+(\.\d)?(~W)?$", k)})
        if len(sizes) < 4:
            continue
        host = urlparse(i["of"][e[2]]).hostname.replace("www.", "")
        out.append(dict(score=pct + len(sale) * 0.5 + (15 if i["b"].lower() in POPULAR else 0), b=i["b"], n=clean(i["n"]),
                        pct=pct, price=e[1], reg=e[3], store=stores.get(host, host), img=i["img"], sizes=sizes, who=who,
                        url=i["of"][e[2]]))
    out.sort(key=lambda x: -x["score"])
    chosen, brands = [], set()
    for x in out:
        if x["b"].lower() in brands:
            continue
        chosen.append(x)
        brands.add(x["b"].lower())
        if len(chosen) == n:
            break
    return chosen


def money(v, lang):
    return f"{v:,.2f} $".replace(",", " ").replace(".", ",") if lang == "fr" else f"${v:,.2f}"


def size_range(s):
    """A short list ("6, 6.5, 8, 10.5") when there are few sizes, else a range ("7–12, 9 sizes")."""
    f = lambda v: str(int(v)) if v == int(v) else str(v)
    return ", ".join(f(v) for v in s) if len(s) <= 6 else f"{f(s[0])}–{f(s[-1])} ({len(s)})"


T = {
    "en": dict(kicker="This week's", title="Top 5 deals", sub="Sale running shoes, found across {n} stores", at="at",
               sizes="sizes", who={"men's": "men's", "women's": "women's"}, cta1="Your size?", cta3="Every deal, filtered to your size. Free.", gender={}),
    "fr": dict(kicker="Cette semaine", title="Top 5 aubaines", sub="Souliers de course en solde, dans {n} boutiques", at="chez",
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
<div class="s">{t['at']} {E(x['store'])} · {sizes_label(x, lang)} {size_range(x['sizes'])}</div></div></div>''' for x in chosen)
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


def brief(chosen, when):
    top = chosen[:3]
    ord_en, ord_fr = ["First", "Then", "And"], ["D'abord", "Ensuite", "Et enfin"]
    script_en = " ".join(["Three running deals I'd actually buy this week."] +
                         [f"{ord_en[k]} the {short(x)}, {spoken_pct(x['pct'], 'en')} at {x['store']}." for k, x in enumerate(top)] +
                         ["Want deals like these in your size every Friday? Link in bio."])
    script_fr = " ".join(["Trois aubaines de course que j'achèterais cette semaine."] +
                         [f"{ord_fr[k]}, les {short(x)}, {spoken_pct(x['pct'], 'fr')} chez {x['store']}." for k, x in enumerate(top)] +
                         ["Tu veux des aubaines comme ça dans ta taille chaque vendredi? Lien dans la bio."])
    who = lambda x: {"Men's": "men's", "Women's": "women's"}.get(x["n"].split(" - ")[-1], "unisex")
    li = "".join(f'''<li style="margin:0 0 12px"><b>{E(short(x))}</b> ({who(x)}):
<b>{money(x['price'], 'en')}</b> instead of {money(x['reg'], 'en')}, −{x['pct']}% at {E(x['store'])}, in {x['who'] + ' ' if x['who'] else ''}sizes {size_range(x['sizes'])} (as of this morning).
<a href="{E(x['url'])}">Check it</a></li>''' for x in top)
    rest = "".join(f"<li>{E(short(x))}: {money(x['price'], 'en')} (−{x['pct']}%) at {E(x['store'])}</li>" for x in chosen[3:])
    p = 'style="font:15px/1.5 Arial,sans-serif;color:#17201C;margin:0 0 14px"'
    h = 'style="font:800 18px Arial,sans-serif;color:#B8470A;margin:22px 0 8px"'
    body = f'''<div style="max-width:620px;margin:0 auto;padding:18px">
<p {p}>Hi Bastien, here's this week's Instagram kit, picked from this morning's deals ({when}).
Post the Reel today (Wednesday) and the Top 5 graphic as a Story.</p>
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
    body, *_ = brief(chosen, when)
    for x in chosen:
        print(f"- {x['pct']}% {short(x)} {x['price']} at {x['store']}")
    if DRY:
        (OUT / "ig-brief.html").write_text(body)
        print(f"DRY RUN: wrote {OUT / 'ig-brief.html'} and the PNGs")
        return 0
    r = requests.post("https://api.resend.com/emails", timeout=60,
                      headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                      json={"from": FROM, "to": [TO], "subject": f"Instagram kit for {when}: 3 picks + Top 5 graphic",
                            "html": body,
                            "attachments": [{"filename": f"top5-{l}.png", "content": base64.b64encode(p.read_bytes()).decode()}
                                            for l, p in pngs.items()]})
    print(f"emailed {TO}: HTTP {r.status_code} {r.text[:200]}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
