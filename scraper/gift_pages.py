"""Gifts for runners (Oct 28; growth chat's prototype, Bastien: "Ship it all except the fox pro"): /gifts-for-runners/ +
/cadeaux-coureurs/ (Canada side) + /us/gifts-for-runners/ (USA side, US stores, US$; Oct 30), rebuilt on every refresh from deals.json. Gifts you can buy without knowing someone's size: one
size, or small/medium/large all in stock. Three budgets (under $25 / $50 / $100), each with up to 8 on sale (20%+ off) and 4
full-price picks people can watch ("Full price · ♡ Watch the price" -> /?watch=<item key>, the homepage's watch link). One brand
once per budget, no more than 3 of a kind among the sale picks, Canadian stores only, photos only.
A card whose photo doesn't load removes itself (Oct 30: REI's photos came up as empty boxes for our robot).
Odd prices are left out: a pack or bundle, or a price far above the brand's usual for that kind (a goodr at $100 = a multi-pack).

USA: deals-us.json (where `ca` = ships from the US), US English, no Boxing Day box (a link to the US Black Friday page instead).

  python scraper/gift_pages.py SITE
"""
import collections
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shoe_pages as SP  # noqa: E402

PATHS = {"en": "gifts-for-runners", "fr": "cadeaux-coureurs", "us": "us/gifts-for-runners"}
NOT = re.compile(r"\b(l/s|s/s|long sleeve|short sleeve|half-?zip|1/4 zip|quarter zip|tee|shirt|jacket|hoodie|tights?|shorts?|pants?|race number|"
                 r"attachment|replacement|refill|lens only|strap only|insoles?|laces?|kids?|junior)\b", re.I)
PACK = re.compile(r"\b(\d+[- ]?(pack|pk)|pack of|bundle|set of|multi-?pack|kit|gift set|\d+ pairs?)\b", re.I)
HYD = re.compile(r"hydration|race vest|\d+ ?l\b(?!/)|belt|flask|bottle", re.I)
ONE = {"OS", "O/S", "ONE SIZE", "ONESIZE", "TU", "UNI", "1", "ONE", "NS"}
KIND = {"headwear": ("Hats & headbands", "Tuques et bandeaux"), "gloves": ("Gloves & mitts", "Gants et mitaines"), "socks": ("Socks", "Bas"),
        "light": ("Lights & headlamps", "Lampes frontales"), "bottle": ("Bottles & flasks", "Bouteilles et flasques"),
        "sun": ("Sunglasses", "Lunettes de soleil"), "packs": ("Vests & belts", "Vestes d'hydratation et ceintures"), "watches": ("Watches", "Montres")}
BUDGETS = (25, 50, 100)
S = {
    "en": dict(title="Gifts for runners: under $25, $50 and $100",
               sub="Ideas you can buy without knowing their size (one size, or small/medium/large in stock) at Canadian stores: today's sales first, then full-price favourites worth watching. Updated every morning.",
               under="Under ${c}", onsale="On sale today", full="Full price: we'll email you if it drops", fp="Full price", watch="♡ Watch the price",
               box="Prices often drop again on Boxing Day. Watch an item and we'll email you if it drops.", boxing="Boxing Day: get ready →",
               more="Run yourself? See deals in your size →", note="Prices change daily: check on the store's site. Nothing here earns us money.",
               upd="Updated {d}", none="Nothing in this budget today."),
    "fr": dict(title="Cadeaux pour coureurs : moins de 25 $, 50 $ et 100 $",
               sub="Des idées sans souci de taille (taille unique, ou petit/moyen/grand en stock) dans des boutiques canadiennes : les soldes du jour d'abord, puis des classiques à prix régulier à suivre. Mis à jour chaque matin.",
               under="Moins de {c} $", onsale="En solde aujourd'hui", full="Prix régulier : on vous écrit s'il baisse", fp="Prix régulier", watch="♡ Suivre le prix",
               box="Le 26 décembre (Boxing Day), bien des prix baissent encore. Suivez un article : on vous écrit s'il baisse.", boxing="Boxing Day : préparez-vous →",
               more="Vous courez aussi ? Voyez les aubaines dans votre taille →", note="Les prix changent chaque jour : vérifiez sur le site de la boutique. Rien ici ne nous rapporte d'argent.",
               upd="Mis à jour le {d}", none="Rien dans ce budget aujourd'hui."),
}
S["us"] = dict(S["en"], sub="Ideas you can buy without knowing their size (one size, or small/medium/large in stock) at US stores: today's sales first, then full-price favorites worth watching. Updated every morning.",
               box="Black Friday is November 27. Watch an item and we'll email you if it drops.", boxing="Black Friday deals →")
CSS = """<style>.gf-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:6px 0 4px}
@media(min-width:720px){.gf-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(min-width:1000px){.gf-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
.gf{background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:10px;display:flex;flex-direction:column;gap:2px;min-width:0}
.gf a.go{color:var(--ink);text-decoration:none;display:flex;flex-direction:column;gap:2px;flex:1}
.gf .ph{aspect-ratio:1;background:#fff;border-radius:10px;display:grid;place-items:center;overflow:hidden;margin-bottom:6px}.gf .ph img{width:100%;height:100%;object-fit:contain}
.gf .k{font-size:11.5px;color:var(--moss,#2f6b3a);font-weight:700;text-transform:uppercase;letter-spacing:.04em}.gf b{font-size:14px}
.gf .n{font-size:13.5px;color:var(--muted);line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.gf .pr{margin-top:auto;padding-top:6px;font-weight:700}.gf .pr s{color:var(--muted);font-weight:400;font-size:13px}.gf .pr em{font-style:normal;color:#1D6B45;font-size:13px}
.gf .st{font-size:12.5px;color:var(--muted);overflow-wrap:anywhere}.gf .fpl{display:block;font-weight:500;font-size:12.5px;color:var(--muted);white-space:nowrap}
.gf .wt{display:inline-block;margin-top:6px;font:700 13px var(--body);color:var(--ink);border:1.5px solid var(--line);border-radius:999px;padding:6px 10px;text-decoration:none;text-align:center}
.gf-h3{font:700 13px/1.3 var(--body);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:14px 0 6px}
.gf-box{background:var(--mist);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:22px}.gf-sub{color:var(--muted);margin:2px 0 0}</style>"""


def kind(d):
    if d["g"] in ("headwear", "gloves", "socks", "watches"):
        return d["g"]
    if d["g"] == "packs":
        return "packs" if HYD.search(d["n"]) else None
    if d["g"] == "gear" and d.get("t") in ("light", "bottle", "sun"):
        return d["t"]
    return None


def build(site, side="ca"):
    data = json.loads((site / ("deals-us.json" if side == "us" else "deals.json")).read_text())
    items = data["items"]
    fx = float((data.get("fx") or {}).get("USD") or 1.37) if side == "us" else 1.0   # deals-us.json prices are in CAD: shown in US$
    brands = collections.Counter(d["b"] for d in items)
    cand = []
    for d in items:
        k = kind(d)
        if not k or not d.get("img") or not d.get("ca") or (NOT.search(d["n"]) and k != "packs") or PACK.search(d["n"]):
            continue
        ps = [s[1] for s in d["sz"]]
        regs = [s[3] for s in d["sz"] if len(s) > 3 and s[3]]
        if not ps:
            continue
        p = min(ps) / fx
        r = (max(regs) if regs else min(ps)) / fx
        off = 1 - p / r if r else 0
        sale = off >= 0.2 and r <= 7 * p
        if p < 10 or (off > 0.02 and not sale):      # a few cents off isn't a sale; nothing under $10 (a lone gel, a sticker)
            continue
        sz = {str(s[0]).upper() for s in d["sz"]}
        if k in ("headwear", "gloves", "socks") and not (sz & ONE or {"S", "M", "L"} <= sz or {"M", "L"} <= sz):
            continue
        cap = next((c for c in BUDGETS if p <= c), None)
        if not cap:
            continue
        best = min(d["sz"], key=lambda s: s[1])
        cand.append(dict(d=d, k=k, p=p, r=r, off=off, sale=sale, cap=cap, url=d["of"][best[2]],
                         score=(off * 100 if sale else 0) + min(brands[d["b"]], 80) / 4))
    # a price far above what the brand usually asks for that kind = a bundle or a pack (goodr "Abominable Snow Icon" at $100)
    usual = collections.defaultdict(list)
    for d in items:                       # every item of that brand and kind today (both sides of the border, photo or not)
        k = kind(d)
        regs = [z[3] for z in d["sz"] if len(z) > 3 and z[3]] or [z[1] for z in d["sz"]]
        if k and regs:
            usual[(d["b"], k)].append(max(regs))
    cand = [c for c in cand if len(usual[(c["d"]["b"], c["k"])]) < 4 or c["r"] * fx <= 1.8 * statistics.median(usual[(c["d"]["b"], c["k"])])]
    out = {}
    for cap in BUDGETS:
        rows = sorted((c for c in cand if c["cap"] == cap), key=lambda c: -c["score"])
        res = {"s": [], "f": []}
        seen_b = set()
        for part, n in (("s", 8), ("f", 4)):
            seen_k = collections.Counter()
            for c in rows:
                if (part == "s") != c["sale"] or c["d"]["b"] in seen_b or seen_k[c["k"]] >= (3 if part == "s" else 1):
                    continue
                seen_b.add(c["d"]["b"])
                seen_k[c["k"]] += 1
                res[part].append(c)
                if len(res[part]) == n:
                    break
        out[cap] = res
    ix = site / "index.html"
    names = SP.store_names(ix.read_text()) if ix.exists() else {}
    return {"out": out, "upd": data.get("updated"), "names": names}


def item_key(d):
    return f"{d['b']}|{d['n']}|{d['g']}|{1 if d.get('w') else 0}".lower()


def page(lang, data):
    L = SP.US if lang == "us" else SP.T[lang]
    s = S[lang]
    money = L["money"]
    from urllib.parse import quote

    def cards(rows):
        if not rows:
            return f'<p class="gf-sub">{s["none"]}</p>'
        html = []
        for c in rows:
            d = c["d"]
            name = re.sub(r"\s*-\s*Unisex$", "", d["n"])
            pr = (f'{money(c["p"])} <s>{money(c["r"])}</s> <em>−{round(c["off"] * 100)}{" %" if lang == "fr" else "%"}</em>' if c["sale"]
                  else f'{money(c["p"])} <span class="fpl">{SP.esc(s["fp"])}</span>')
            watch = "" if c["sale"] else (f'<a class="wt" href="{L["home"]}{"&" if "?" in L["home"] else "?"}watch={quote(item_key(d))}&amp;ref=gifts">'
                                          f'{SP.esc(s["watch"])}</a>')
            html.append(f'<div class="gf"><a class="go" href="{SP.esc(c["url"])}" target="_blank" rel="noopener nofollow" data-store="{SP.esc(SP.host(c["url"]))}">'
                        f'<span class="ph"><img src="{SP.esc(d["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="var g=this.closest(`.gf`);if(g)g.remove()"></span>'
                        f'<span class="k">{SP.esc(KIND[c["k"]][1 if lang == "fr" else 0])}</span><b>{SP.esc(d["b"])}</b><span class="n">{SP.esc(name)}</span>'
                        f'<span class="pr">{pr}</span><span class="st">{SP.esc((data.get("names", {}).get(SP.host(c["url"])) or [SP.host(c["url"]).replace("www.", "")])[0])}</span></a>{watch}</div>')
        return '<div class="gf-grid">' + "".join(html) + "</div>"
    out = [SP.page_head(L, s["title"], s["sub"], f'/{PATHS["us"]}/', f'/{PATHS["en"]}/', CSS) if lang == "us"
           else SP.page_head(L, s["title"], s["sub"], f'/{PATHS["en"]}/', f'/{PATHS["fr"]}/', CSS)]
    body = [f'<h1>{SP.esc(s["title"])}</h1><p class="sub">{SP.esc(s["sub"])}</p>']
    if data.get("upd"):
        body.append(f'<p class="gf-sub">{SP.esc(s["upd"].format(d=SP.fmt_date(data["upd"], L)))}</p>')
    for cap in BUDGETS:
        r = data["out"][cap]
        body.append(f'<h2>{SP.esc(s["under"].format(c=cap))}</h2><p class="gf-h3">{SP.esc(s["onsale"])}</p>{cards(r["s"])}')
        if r["f"]:
            body.append(f'<p class="gf-h3">{SP.esc(s["full"])}</p>{cards(r["f"])}')
    boxing = "/us/black-friday/" if lang == "us" else "/soldes-apres-noel/" if lang == "fr" else "/boxing-day/"
    body.append(f'<p class="gf-box">{SP.esc(s["box"])} <a href="{boxing}">{SP.esc(s["boxing"])}</a></p>'
                f'<p><a href="{L["home"]}{"&" if "?" in L["home"] else "?"}ref=gifts"><strong>{SP.esc(s["more"])}</strong></a></p>'
                f'<p class="gf-sub">{SP.esc(s["note"])}</p>')
    out.append("".join(body))
    out.append(SP.page_foot(L))
    return "".join(out)


def main():
    site = Path(sys.argv[1])
    data = build(site)
    pages = [("en", data), ("fr", data)]
    us = None
    if (site / "deals-us.json").exists():
        us = build(site, "us")
        pages.append(("us", us))
    for lang, d in pages:
        p = site / PATHS[lang] / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page(lang, d))
    sm = site / "sitemap.xml"
    if sm.exists():
        t = sm.read_text()
        add = "".join(f"<url><loc>{SP.BASE}/{PATHS[lang]}/</loc></url>" for lang, _ in pages if f"/{PATHS[lang]}/<" not in t)
        if add:
            sm.write_text(t.replace("</urlset>", add + "</urlset>"))
    print("Gift page: " + ", ".join(f"under ${c}: {len(data['out'][c]['s'])} on sale + {len(data['out'][c]['f'])} full price" for c in BUDGETS))
    if us:
        print("Gift page (USA): " + ", ".join(f"under ${c}: {len(us['out'][c]['s'])} on sale + {len(us['out'][c]['f'])} full price" for c in BUDGETS))


if __name__ == "__main__":
    main()
