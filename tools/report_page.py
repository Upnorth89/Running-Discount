"""Monthly report page (Oct 19, 2026; Bastien: links from running sites are the Google lever): "Running shoe sales in Canada"
from our own data, a page journalists and bloggers can cite. One frozen page per month, EN + FR:
  python tools/report_page.py DEALS.json PRICES.jsonl SITE_DIR 2026-10 [compare-date]
writes SITE_DIR/report/2026-10/index.html and SITE_DIR/rapport/2026-10/index.html (commit them; they never change after).
Counts only shoe sizes whose best price is at a Canadian store; spikes left out; a size is "on sale" 1%+ under its regular price."""
import collections, json, re, statistics, sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import shoe_pages as SP  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MONTH = {"en": "January February March April May June July August September October November December".split(),
         "fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()}


def stores_map():
    html = (ROOT / "site/index.html").read_text()
    return json.loads(re.search(r"const STORES=(\{.*?\});", html, re.S).group(1))


def compute(deals, prices, back):
    S = stores_map()

    def store(u):
        h = urlparse(u).netloc.lower()
        for k in (h, h.replace("www.", ""), ".".join(h.split(".")[-2:])):
            if k in S:
                return S[k]
        return None

    D = json.load(open(deals))
    rows = []
    for i in D["items"]:
        if i["g"] != "shoes" or i.get("t") == "spike":
            continue
        zs = [z for z in i["sz"] if (store(i["of"][z[2]]) or ["", "?"])[1:] == []]   # best price at a Canadian store
        if not zs:
            continue
        sale = [z for z in zs if z[3] and z[1] < z[3] * 0.99]
        rows.append((i, zs, sale, max((1 - z[1] / z[3]) for z in sale) if sale else 0))
    on = [r for r in rows if r[2]]
    shops = {store(r[0]["of"][z[2]])[0] for r in rows for z in r[1]}

    by = collections.defaultdict(list)
    for r in rows:
        by[r[0]["b"]].append(r)
    brands = []
    for b, rs in by.items():
        if len(rs) >= 25:
            o = [r for r in rs if r[2]]
            brands.append((b, len(rs), round(100 * len(o) / len(rs)), round(100 * statistics.median([r[3] for r in o])) if o else 0))
    brands.sort(key=lambda x: (-x[2], x[0]))

    sizes = {}
    for g, rng in (("men", [x / 2 for x in range(14, 27)]), ("women", [x / 2 for x in range(10, 23)])):
        sg = [r for r in on if r[0].get("sx") == [g]]
        sizes[g] = (len(sg), [(f"{s:g}", round(100 * sum(1 for r in sg if any(z[0] == f"{s:g}" for z in r[2])) / len(sg))) for s in rng])

    per = collections.defaultdict(set)
    for r in on:
        for z in r[2]:
            per[store(r[0]["of"][z[2]])[0]].add(itemkey(r[0]))
    shops_top = sorted(((s, len(v)) for s, v in per.items()), key=lambda x: (-x[1], x[0]))[:10]

    H = {}
    for line in open(prices):
        o = json.loads(line)
        H[o["k"]] = o["h"]
    tot = same = 0
    for r in on:
        h = H.get(itemkey(r[0]))
        if not h or h[0][0] > back:
            continue
        then = [e for e in h if e[0] <= back][-1][1]
        tot += 1
        same += then <= h[-1][1] * 1.005
    return {"day": D["updated"][:10], "shoes": len(rows), "on": len(on), "shops": len(shops), "brands": brands, "sizes": sizes,
            "top": shops_top, "hist": tot, "same": same, "back": back}


def itemkey(d):
    return f"{d['b']}|{d['n']}|{d['g']}|{1 if d.get('w') else 0}".lower()


def fmt(n, lang):
    s = f"{n:,}"
    return s.replace(",", " ") if lang == "fr" else s


def date(iso, lang):
    y, m, d = iso.split("-")
    return f"{MONTH[lang][int(m) - 1]} {int(d)}, {y}" if lang == "en" else f"{int(d)} {MONTH[lang][int(m) - 1]} {y}"


TXT = {
    "en": {
        "title": "Running shoe sales in Canada: {month} report",
        "desc": "Our own numbers from {shops} Canadian running stores: how many shoes are on sale, which brands discount most, and how few sale shoes are left in your size.",
        "h1": "Running shoe sales in Canada", "kicker": "{month} report",
        "lead": "Every day The Gear Fox reads the prices and sizes of every running shoe at {shops} Canadian stores. On {day}, {on} of {shoes} running shoe models ({p}%) were on sale in at least one size. Here's what the numbers say.",
        "find": "Key findings",
        "f1": "Half of all running shoes were on sale ({p}%).",
        "f2": "Your size is the catch: a women's size 8 could buy only {w8}% of the shoes on sale, a men's size 9 only {m9}%.",
        "f3": "The most common sizes go first: men's 8 to 9 are left on fewer sale shoes than men's 11 to 12.",
        "f4": "{same}% of the shoes on sale were already at that price or lower on {back}: a 'sale' is often not new.",
        "f5": "Among the big brands (100+ models), {b1} had the most shoes on sale ({p1}% of its models) and {bl} the fewest ({pl}%).",
        "sizesH": "Your size is the catch",
        "sizesP": "Share of sale shoes still on sale in each size. A shoe counts as 'on sale' when at least one of its sizes is discounted.",
        "men": "Men's ({n} shoes on sale)", "women": "Women's ({n} shoes on sale)", "size": "Size",
        "sizesN": "Sizes at the edges (men's 7 and 12.5, women's 5 and 10.5) are rare in any store, on sale or not.",
        "brandsH": "Brands: how much is on sale",
        "brandsP": "Brands with 25 or more running shoe models at Canadian stores.",
        "thB": "Brand", "thN": "Models", "thP": "On sale", "thD": "Typical discount",
        "brandsN": "Typical discount = the median of each sale shoe's deepest discount.",
        "histH": "Is the sale new?",
        "histP": "We record every shoe's best price each day. Of the {hist} shoes on sale on {day} that we tracked since {back}, {same}% ({n}) were already at that price or lower on {back}. Before Black Friday, a price that has been sitting there for weeks isn't a reason to rush.",
        "shopsH": "Stores with the most shoes on sale",
        "shopsP": "Shoe models whose best sale price, in at least one size, was at that store.",
        "thS": "Store", "thC": "Shoes on sale",
        "howH": "How we counted",
        "how": ["Data from {day}: every running shoe at {shops} Canadian stores (store sites read directly, twice a day). Track spikes left out.",
                "One model = one shoe in one fit (men's, women's, wide), all colours together, best price per size across stores.",
                "Only sizes whose best price is at a Canadian store count. 'On sale' = at least 1% under the store's regular price.",
                "Price history started October 2, 2026."],
        "useH": "Use these numbers", "use": "Free to quote or chart with a link to this page. Questions or another cut of the data (a brand, a size, a city): hello@thegearfox.com.",
        "cta": "See the deals in your size", "ctaTxt": "The Gear Fox shows only the running gear on sale in your size, from {shops}+ Canadian stores. Free.", "ctaBtn": "Find my deals",
    },
    "fr": {
        "title": "Soldes de chaussures de course au Canada : rapport de {month}",
        "desc": "Nos propres chiffres, tirés de {shops} boutiques de course canadiennes : combien de chaussures sont en solde, quelles marques baissent le plus leurs prix, et combien il en reste dans votre pointure.",
        "h1": "Soldes de chaussures de course au Canada", "kicker": "Rapport de {month}",
        "lead": "Chaque jour, The Gear Fox lit les prix et les pointures de toutes les chaussures de course de {shops} boutiques canadiennes. Le {day}, {on} des {shoes} modèles ({p} %) étaient en solde dans au moins une pointure. Voici ce que disent les chiffres.",
        "find": "En bref",
        "f1": "La moitié des chaussures de course étaient en solde ({p} %).",
        "f2": "Le hic, c'est la pointure : une femme qui chausse du 8 ne pouvait acheter que {w8} % des chaussures en solde, un homme qui chausse du 9, seulement {m9} %.",
        "f3": "Les pointures les plus courantes partent en premier : il reste moins de soldes en 8 à 9 homme qu'en 11 à 12.",
        "f4": "{same} % des chaussures en solde étaient déjà à ce prix ou moins le {back} : un « solde » n'est souvent pas nouveau.",
        "f5": "Parmi les grandes marques (100 modèles et plus), {b1} avait le plus de chaussures en solde ({p1} % de ses modèles) et {bl}, le moins ({pl} %).",
        "sizesH": "Le hic : votre pointure",
        "sizesP": "Part des chaussures en solde encore offertes en solde dans chaque pointure. Une chaussure compte « en solde » dès qu'une de ses pointures l'est.",
        "men": "Hommes ({n} chaussures en solde)", "women": "Femmes ({n} chaussures en solde)", "size": "Pointure",
        "sizesN": "Les pointures aux extrémités (7 et 12,5 homme, 5 et 10,5 femme) sont rares en boutique, en solde ou non.",
        "brandsH": "Marques : combien en solde",
        "brandsP": "Marques ayant 25 modèles de chaussures de course ou plus dans les boutiques canadiennes.",
        "thB": "Marque", "thN": "Modèles", "thP": "En solde", "thD": "Rabais typique",
        "brandsN": "Rabais typique = la médiane du plus gros rabais de chaque chaussure en solde.",
        "histH": "Le solde est-il nouveau?",
        "histP": "Nous notons chaque jour le meilleur prix de chaque chaussure. Des {hist} chaussures en solde le {day} suivies depuis le {back}, {same} % ({n}) étaient déjà à ce prix ou moins le {back}. Avant le Vendredi fou, un prix affiché depuis des semaines n'est pas une raison de se presser.",
        "shopsH": "Les boutiques avec le plus de chaussures en solde",
        "shopsP": "Modèles dont le meilleur prix soldé, dans au moins une pointure, était dans cette boutique.",
        "thS": "Boutique", "thC": "Chaussures en solde",
        "howH": "Notre méthode",
        "how": ["Données du {day} : toutes les chaussures de course de {shops} boutiques canadiennes (sites lus directement, deux fois par jour). Chaussures à crampons exclues.",
                "Un modèle = une chaussure dans une coupe (homme, femme, large), toutes couleurs confondues, meilleur prix par pointure entre les boutiques.",
                "Seules les pointures dont le meilleur prix est dans une boutique canadienne comptent. « En solde » = au moins 1 % sous le prix courant de la boutique.",
                "Historique des prix depuis le 2 octobre 2026."],
        "useH": "Utilisez ces chiffres", "use": "Libres de citer ou de mettre en graphique avec un lien vers cette page. Questions ou autre découpage (une marque, une pointure, une ville) : hello@thegearfox.com.",
        "cta": "Voyez les aubaines dans votre pointure", "ctaTxt": "The Gear Fox montre seulement l'équipement de course en solde dans votre pointure, de {shops}+ boutiques canadiennes. Gratuit.", "ctaBtn": "Trouver mes aubaines",
    },
}

CSS = """<style>
.kick{font:700 14px var(--body);letter-spacing:.08em;text-transform:uppercase;color:var(--moss);margin:14px 0 2px}
.find{background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:6px 16px 6px 34px;margin:14px 0}
.find li{margin:8px 0}
.charts{display:grid;gap:14px}@media(min-width:680px){.charts{grid-template-columns:1fr 1fr}}
.chart{background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:12px 14px;margin:0}
.chart figcaption{font:700 17px var(--display);margin:0 0 8px}
.bar{display:grid;grid-template-columns:34px 1fr 38px;align-items:center;gap:8px;font-size:14px;margin:3px 0}
.bar .k{color:var(--muted);text-align:right}.bar .v{text-align:right;font-variant-numeric:tabular-nums}
.bar .t{display:block;height:12px;background:var(--mist);border-radius:4px;overflow:hidden}
.bar .f{display:block;height:100%;background:var(--hivis);border-radius:0 4px 4px 0}
.note{font-size:14px;color:var(--muted);margin:8px 0 0}
td.n{text-align:right;font-variant-numeric:tabular-nums}th.n{text-align:right}
@media(max-width:520px){.rep th,.rep td{padding:8px 6px;font-size:14px}.rep th{font-size:11px;letter-spacing:.02em}}
</style>"""


def page(lang, R, ym, paths):
    L, X = SP.T[lang], TXT[lang]
    y, m = ym.split("-")
    month = f"{MONTH[lang][int(m) - 1]} {y}" if lang == "en" else f"{MONTH[lang][int(m) - 1]} {y}"
    day, back = date(R["day"], lang), date(R["back"], lang)
    pc = lambda n: f"{n} %" if lang == "fr" else f"{n}%"
    p = round(100 * R["on"] / R["shoes"])
    sz = {g: dict(v[1]) for g, v in R["sizes"].items()}
    big = [b for b in R["brands"] if b[1] >= 100]
    b1, bl = big[0], big[-1]
    same = round(100 * R["same"] / R["hist"])
    title = X["title"].format(month=month)
    out = [SP.page_head(L, title, X["desc"].format(shops=R["shops"]), paths[0], paths[1], CSS)]
    out.append(f'<p class="kick">{SP.esc(X["kicker"].format(month=month))}</p><h1>{SP.esc(X["h1"])}</h1>'
               f'<p class="sub">{SP.esc(X["lead"].format(shops=R["shops"], day=day, on=fmt(R["on"], lang), shoes=fmt(R["shoes"], lang), p=p))}</p>')
    out.append(f'<h2>{X["find"]}</h2><ul class="find">' + "".join(f"<li>{SP.esc(s)}</li>" for s in (
        X["f1"].format(p=p), X["f2"].format(w8=sz["women"]["8"], m9=sz["men"]["9"]), X["f3"],
        X["f4"].format(same=same, back=back), X["f5"].format(b1=SP.bname(b1[0]), p1=b1[2], bl=SP.bname(bl[0]), pl=bl[2]))) + "</ul>")
    out.append(f'<h2>{X["sizesH"]}</h2><p>{SP.esc(X["sizesP"])}</p><div class="charts">')
    for g in ("men", "women"):
        n, vals = R["sizes"][g]
        bars = "".join(f'<div class="bar"><span class="k">{k.replace(".", ",") if lang == "fr" else k}</span><span class="t"><span class="f" style="width:{v}%"></span></span>'
                       f'<span class="v">{pc(v)}</span></div>' for k, v in vals)
        out.append(f'<figure class="chart" role="group" aria-label="{SP.esc(X[g].format(n=fmt(n, lang)))}"><figcaption>{SP.esc(X[g].format(n=fmt(n, lang)))}</figcaption>{bars}</figure>')
    out.append(f'</div><p class="note">{SP.esc(X["sizesN"])}</p>')
    out.append(f'<h2>{X["brandsH"]}</h2><p>{SP.esc(X["brandsP"])}</p><table class="rep"><thead><tr><th>{X["thB"]}</th><th class="n">{X["thN"]}</th>'
               f'<th class="n">{X["thP"]}</th><th class="n">{X["thD"]}</th></tr></thead><tbody>'
               + "".join(f'<tr><td>{SP.esc(SP.bname(b))}</td><td class="n">{n}</td><td class="n">{pc(on)}</td><td class="n">{"−" + pc(d) if d else "–"}</td></tr>'
                         for b, n, on, d in R["brands"]) + f'</tbody></table><p class="note">{SP.esc(X["brandsN"])}</p>')
    out.append(f'<h2>{X["histH"]}</h2><p>{SP.esc(X["histP"].format(hist=fmt(R["hist"], lang), day=day, back=back, same=same, n=fmt(R["same"], lang)))}</p>')
    out.append(f'<h2>{X["shopsH"]}</h2><p>{SP.esc(X["shopsP"])}</p><table class="rep"><thead><tr><th>{X["thS"]}</th><th class="n">{X["thC"]}</th></tr></thead><tbody>'
               + "".join(f'<tr><td>{SP.esc(s)}</td><td class="n">{n}</td></tr>' for s, n in R["top"]) + "</tbody></table>")
    out.append(f'<h2>{X["howH"]}</h2><ul>' + "".join(f"<li>{SP.esc(s.format(day=day, shops=R['shops']))}</li>" for s in X["how"]) + "</ul>")
    out.append(f'<h2>{X["useH"]}</h2><p>{SP.esc(X["use"])}</p>')
    home = L["home"] + ("&" if "?" in L["home"] else "?") + f"ref=report-{ym}"
    out.append(f'<section class="cta"><h2>{X["cta"]}</h2><p>{SP.esc(X["ctaTxt"].format(shops=R["shops"]))}</p><a class="btn" href="{home}">{X["ctaBtn"]}</a></section>')
    out.append(SP.page_foot(L))
    return "".join(out)


def main():
    deals, prices, site, ym = sys.argv[1:5]
    back = sys.argv[5] if len(sys.argv) > 5 else "2026-10-05"
    R = compute(deals, prices, back)
    paths = (f"/report/{ym}/", f"/rapport/{ym}/")
    for lang, pth in (("en", paths[0]), ("fr", paths[1])):
        f = Path(site) / pth.strip("/") / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(page(lang, R, ym, paths))
        print("wrote", f)
    print(json.dumps({k: v for k, v in R.items() if k != "brands"}, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
