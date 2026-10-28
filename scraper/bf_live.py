"""Black Friday deal check, live (Oct 27; growth chat's spec, Bastien: "You think this is a good addition to the Black Friday
then yes ship it"): /black-friday/live/ + /vendredi-fou/direct/ (Canada side), rebuilt on every refresh after history.py has
annotated sale.json, so twice a day. Three lists from our own price history (hist/prices.jsonl), Canadian stores only, no spikes:
  1. Real drops this week: changed in the last 7 days AND lower than every price in the 30 days before, by 10% or $10 (>= $5).
  2. Not new: 30%+ off the tag, regular $60+, the same best price for 21+ days.
  3. Went up lately: +10% and +$10 vs 21 days ago (an old price under 60% of today's = a data glitch, left out).
A sale that ended is already gone: featured_check.py takes ended sales out of sale.json before this runs. Neutral wording: we
never say a store did anything wrong.

  python scraper/bf_live.py SITE      (HISTORY_FILE = the history file, default hist/prices.jsonl)
"""
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shoe_pages as SP  # noqa: E402

PATHS = {"en": ("black-friday/live", "Black Friday deal check, live"), "fr": ("vendredi-fou/direct", "Vendredi fou : vraies et fausses aubaines, en direct")}
S = {
    "en": dict(
        lead="Every morning and afternoon we compare each sale price at {n} stores with what the same item cost over the last 60 days. Here is what's really new, and what isn't.",
        upd="Updated {d}", st=("real drops this week", "of sale prices were already this low 2 weeks ago", "sale items checked today"),
        h1="Real drops this week", s1="Lower than any price in the 30 days before, by 10% or $10.",
        h2="Not new: same “sale” price for weeks", s2="30%+ off the tag, at the same price for at least 3 weeks. Not a bad price, just not a Black Friday price.",
        h3="Went up lately: watch for a “drop” back", s3="Up 10%+ in the last 3 weeks. If it “drops” on Black Friday, it may just be back where it was.",
        was="Was {p} before {d}", same="Same price since {d}", start="Same price since we started tracking ({d})", up="Was {p} on {d}",
        at="{p} CAD at {s}", sizes=lambda n, shoe: f"{n} sizes", none="Nothing in this list today.",
        jH="For journalists", j="Free to quote with a link to this page. Need a cut by store, brand or category for your Black Friday story? Email hello@thegearfox.com.",
        mH="How we check", m="We record the best price of every product at {n} stores twice a day since Oct. 2, size by size. A “real drop” must be lower than every price in the 30 days before it. We don't judge stores: a price that hasn't moved can still be a good one.",
        free="Free, no affiliate links, no store pays to be listed.", watch="♡ Watch any item on the site and we email you when it really drops.",
        watchA="See today's deals in your size", back="← Black Friday", g={"men": "Men's", "women": "Women's", "unisex": "Unisex"}),
    "fr": dict(
        lead="Chaque matin et chaque après-midi, on compare chaque prix en solde dans {n} boutiques avec ce que le même article coûtait dans les 60 derniers jours. Voici ce qui est vraiment nouveau, et ce qui ne l’est pas.",
        upd="Mis à jour le {d}", st=("vraies baisses cette semaine", "des prix en solde étaient déjà aussi bas il y a 2 semaines", "articles en solde vérifiés aujourd’hui"),
        h1="Vraies baisses cette semaine", s1="Plus bas que tous les prix des 30 jours précédents, d’au moins 10 % ou 10 $.",
        h2="Pas nouveau : le même prix « en solde » depuis des semaines", s2="30 % et plus de rabais sur l’étiquette, au même prix depuis au moins 3 semaines. Pas un mauvais prix, juste pas un prix du Vendredi fou.",
        h3="En hausse récemment : attention à une « baisse » de retour", s3="Plus de 10 % de hausse dans les 3 dernières semaines. S’il « baisse » au Vendredi fou, il revient peut-être juste à son prix d’avant.",
        was="Était à {p} avant le {d}", same="Même prix depuis le {d}", start="Même prix depuis le début de notre suivi ({d})", up="{p} le {d}",
        at="{p} CAD chez {s}", sizes=lambda n, shoe: f"{n} {'pointures' if shoe else 'tailles'}", none="Rien dans cette liste aujourd’hui.",
        jH="Pour les journalistes", j="Libre de citer avec un lien vers cette page. Besoin des chiffres par boutique, marque ou catégorie pour votre reportage? Écrivez à hello@thegearfox.com.",
        mH="Notre méthode", m="On note le meilleur prix de chaque produit dans {n} boutiques deux fois par jour depuis le 2 octobre, pointure par pointure. Une « vraie baisse » doit être plus basse que tous les prix des 30 jours précédents. On ne juge pas les boutiques : un prix qui ne bouge pas peut quand même être bon.",
        free="Gratuit, sans liens affiliés, aucune boutique ne paie pour y être.", watch="♡ Suivez n’importe quel article sur le site et on vous écrit quand il baisse vraiment.",
        watchA="Voir les aubaines du jour dans votre taille", back="← Vendredi fou", g={"men": "hommes", "women": "femmes", "unisex": "unisexe"}),
}
CSS = """<style>.bfl-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0 4px}.bfl-stats div{background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:10px}
.bfl-stats b{display:block;font:800 26px/1.1 var(--display)}.bfl-stats span{font-size:13px;color:var(--muted)}
.bfl{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.bfl a{display:flex;gap:10px;align-items:center;background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:8px 10px;color:var(--ink);text-decoration:none}
.bfl img{width:64px;height:64px;object-fit:contain;background:#fff;border-radius:8px;flex:none}.bfl .t{display:inline-block;font:800 13px var(--body);border-radius:6px;padding:2px 7px;margin-bottom:3px}
.bfl .dn{background:#2f6b3a;color:#fff}.bfl .fl{background:var(--mist);color:var(--ink);border:1px solid var(--line)}.bfl .upt{background:#8a2a12;color:#fff}
.bfl .nm{display:block;font-weight:700;line-height:1.25}.bfl small{display:block;color:var(--muted);font-size:13px;line-height:1.3}
.bfl-sub{color:var(--muted);margin:2px 0 0}@media (max-width:420px){.bfl-stats b{font-size:22px}}</style>"""


def d0(s):
    return date.fromisoformat(str(s)[:10])


def price_on(h, day):
    """The best price on a day = the last change on or before it."""
    p = None
    for e in h:
        if d0(e[0]) <= day:
            p = e[1]
        else:
            break
    return p


def item_key(d):
    return f"{d['b']}|{d['n']}|{d['g']}|{1 if d.get('w') else 0}".lower()


def show_name(d, lang):
    """"Rocket X Trail Running Shoes - Men's · Black" -> "Rocket X Trail (Men's)" (not base_model: it would cut "Trail")."""
    n = re.split(r"\s+·\s+", d["n"])[0]
    g = None
    m = re.search(r"\s*(?:-\s*|\()(Men's|Women's|Unisex)\)?\s*$", n)
    if m:
        g = {"Men's": "men", "Women's": "women", "Unisex": "unisex"}[m.group(1)]
        n = n[:m.start()]
    n = re.sub(r"\s+((Trail |Road )?Running Shoes?|Shoes?)$", "", n.strip(), flags=re.I) or n
    return f"{d['b']} {n}" + (f" ({S[lang]['g'][g]})" if g else "")


def build(site):
    sale = json.loads((site / "sale.json").read_text())
    upd = sale.get("updated")
    today = (datetime.fromisoformat(upd.replace("Z", "+00:00")) if upd else datetime.now(timezone.utc)).astimezone(SP.HOME_TZ).date()
    H = {}
    for line in Path(os.environ.get("HISTORY_FILE") or "hist/prices.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if "|" in r["k"] and not r["k"].startswith(("us|", "hike|", "hikeus|")):
                H[r["k"]] = r["h"]
    first_day = min((d0(h[0][0]) for h in H.values() if h), default=today)
    reg = {}
    try:
        reg = json.loads((site / "shoes" / "pages.json").read_text())
    except Exception:
        pass
    names = SP.store_names((site / "index.html").read_text()) if (site / "index.html").exists() else {}
    real, flat, up = [], [], []
    n_sale = n_old = n_flat = 0
    for d in sale["items"]:
        if not d.get("ca") or not d.get("sz") or not d.get("img") or d.get("t") == "spike":
            continue
        h = H.get(item_key(d))
        if not h:
            continue
        best = min(e[1] for e in d["sz"])
        regp = max((e[3] for e in d["sz"] if len(e) > 3 and e[3]), default=best)
        at = [e for e in d["sz"] if abs(e[1] - best) < 0.01]
        url = d["of"][at[0][2]] if at and at[0][2] < len(d["of"]) else d["of"][0]
        row = dict(d=d, best=best, reg=regp, n=len(at), url=url, store=(names.get(SP.host(url)) or [SP.host(url)])[0])
        onsale = best < regp * 0.97
        since = d0(h[-1][0])
        if onsale:
            n_sale += 1
            p14 = price_on(h, today - timedelta(days=14))
            if p14 is not None:
                n_old += 1
                n_flat += p14 <= best + 0.01
        wk = price_on(h, today - timedelta(days=7))
        prior = [e[1] for e in h if today - timedelta(days=37) <= d0(e[0]) < today - timedelta(days=7)] + ([wk] if wk else [])
        if wk and prior and since > today - timedelta(days=7) and best < min(prior) - 0.01 and len(at) >= 3:
            gap = min(prior) - best
            if gap >= 5 and (gap >= 10 or gap / min(prior) >= 0.10):
                real.append(dict(row, was=min(prior), gap=gap, day=since))
        if onsale and (today - since).days >= 21 and (regp - best) / regp >= 0.30 and len(at) >= 3 and regp >= 60:
            flat.append(dict(row, day=since, start=since <= first_day, off=round(100 * (regp - best) / regp)))
        p21 = price_on(h, today - timedelta(days=21))
        if p21 and best * 0.6 <= p21 and best >= p21 * 1.10 and best - p21 >= 10 and len(at) >= 3:
            up.append(dict(row, was=p21, gap=best - p21, day=today - timedelta(days=21)))

    def one_per_brand(rows, k):
        seen, out = set(), []
        for r in sorted(rows, key=k):
            if r["d"]["b"].lower() not in seen:
                seen.add(r["d"]["b"].lower())
                out.append(r)
        return out
    n_real = len(real)                        # the count line: every real drop this week, not just the 12 shown (one per brand)
    real = one_per_brand(real, lambda r: -r["gap"])[:12]
    flat = one_per_brand(flat, lambda r: (r["day"], -r["off"]))[:12]
    up = one_per_brand(up, lambda r: -r["gap"])[:8]
    return dict(today=today, upd=upd, real=real, flat=flat, up=up, n_real=n_real, n_sale=n_sale, n_old=n_old, n_flat=n_flat,
                n_stores=sale.get("n_stores") or len(names), reg=reg)


def link(r, lang):
    d = r["d"]
    if d["g"] == "shoes":
        sl = SP.slugify(f'{d["b"]} {SP.base_model(d["n"])}')
        m = r["reg"].get(sl) if isinstance(r.get("reg"), dict) else None
        if m and m.get("to"):
            sl, m = m["to"], r["reg"].get(m["to"])
        if m:
            return f'/{"chaussures" if lang == "fr" else "shoes"}/{sl}/?ref=bf-desk'
    return r["url"]


def page(lang, data):
    L = SP.T[lang]
    s = S[lang]
    path, title = PATHS[lang]
    money = L["money"]
    sd = lambda d: SP.short_date(d, L)

    def cards(rows, kind):
        if not rows:
            return f'<p class="bfl-sub">{s["none"]}</p>'
        out = []
        for r in rows:
            d = r["d"]
            r["reg"] = data["reg"]
            tag = (f'↓ {money(r["gap"]).replace(".00", "")} ' + ("cette semaine" if lang == "fr" else "this week") if kind == "real"
                   else f'−{r["off"]}{" %" if lang == "fr" else "%"}' if kind == "flat" else f'↑ {money(r["gap"]).replace(".00", "")}')
            line = (s["was"].format(p=money(r["was"]), d=sd(r["day"])) if kind == "real"
                    else (s["start"] if r["start"] else s["same"]).format(d=sd(r["day"])) if kind == "flat"
                    else s["up"].format(p=money(r["was"]), d=sd(r["day"])))
            href = link(r, lang)
            ext = "" if href.startswith("/") else ' target="_blank" rel="noopener nofollow"'
            out.append(f'<li><a href="{SP.esc(href)}"{ext} data-store="{SP.esc(SP.host(r["url"]))}"><img src="{SP.esc(d["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer">'
                       f'<span><span class="t {"dn" if kind == "real" else "fl" if kind == "flat" else "upt"}">{SP.esc(tag)}</span>'
                       f'<span class="nm">{SP.esc(show_name(d, lang))}</span>'
                       f'<small>{SP.esc(s["at"].format(p=money(r["best"]), s=r["store"]))}</small><small>{SP.esc(line)}</small>'
                       f'<small>{SP.esc(s["sizes"](r["n"], d["g"] == "shoes"))}</small></span></a></li>')
        return '<ul class="bfl">' + "".join(out) + "</ul>"
    pct = round(100 * data["n_flat"] / data["n_old"]) if data["n_old"] else 0
    num = (lambda n: f"{n:,}".replace(",", " ")) if lang == "fr" else (lambda n: f"{n:,}")
    lead = s["lead"].format(n=data["n_stores"])
    out = [SP.page_head(L, title, lead, "/" + PATHS["en"][0] + "/", "/" + PATHS["fr"][0] + "/", CSS)]
    bf_home = "/vendredi-fou/" if lang == "fr" else "/black-friday/"
    out.append(f'<p class="crumbs"><a href="{bf_home}">{SP.esc(s["back"])}</a></p><h1>{SP.esc(title)}</h1><p class="sub">{SP.esc(lead)}</p>'
               f'<p class="bfl-sub">{SP.esc(s["upd"].format(d=SP.fmt_date(data["upd"], L)))}</p>'
               f'<div class="bfl-stats"><div><b>{num(data["n_real"])}</b><span>{s["st"][0]}</span></div><div><b>{pct}{" %" if lang == "fr" else "%"}</b><span>{s["st"][1]}</span></div>'
               f'<div><b>{num(data["n_sale"])}</b><span>{s["st"][2]}</span></div></div>'
               f'<h2>{SP.esc(s["h1"])}</h2><p class="bfl-sub">{SP.esc(s["s1"])}</p>{cards(data["real"], "real")}'
               f'<h2>{SP.esc(s["h2"])}</h2><p class="bfl-sub">{SP.esc(s["s2"])}</p>{cards(data["flat"], "flat")}'
               f'<h2>{SP.esc(s["h3"])}</h2><p class="bfl-sub">{SP.esc(s["s3"])}</p>{cards(data["up"], "up")}'
               f'<p><a href="{L["home"]}{"&" if "?" in L["home"] else "?"}ref=bf-desk">{SP.esc(s["watchA"])} →</a> {SP.esc(s["watch"])}</p>'
               f'<h2>{SP.esc(s["mH"])}</h2><p>{SP.esc(s["m"].format(n=data["n_stores"]))}</p><p>{SP.esc(s["free"])}</p>'
               f'<h2>{SP.esc(s["jH"])}</h2><p>{SP.esc(s["j"])}</p>')
    out.append(SP.page_foot(L))
    return "".join(out)


def main():
    site = Path(sys.argv[1])
    data = build(site)
    for lang in ("en", "fr"):
        p = site / PATHS[lang][0] / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page(lang, data))
    sm = site / "sitemap.xml"
    if sm.exists():
        t = sm.read_text()
        add = "".join(f"<url><loc>{SP.BASE}/{PATHS[lang][0]}/</loc></url>" for lang in ("en", "fr") if f"/{PATHS[lang][0]}/<" not in t)
        if add:
            sm.write_text(t.replace("</urlset>", add + "</urlset>"))
    print(f"Black Friday deal check: {data['n_real']} real drops ({len(data['real'])} shown), {len(data['flat'])} not new, {len(data['up'])} went up; "
          f"{data['n_flat']} of {data['n_old']} sale prices already this low 2 weeks ago; {data['n_sale']} sale items")


if __name__ == "__main__":
    main()
