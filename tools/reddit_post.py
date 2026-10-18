#!/usr/bin/env python3
"""Reddit / Facebook post maker (Oct 11, 2026; Bastien: "post every 3 days on running gear", and the format he settled on:
"6 shoes 4 gear Canada and 6 shoes 4 gear USA, that's it", names as links).

Picks today's best deals from the live site, opens every one on the store's own page (livecheck: a deal that ended or can't be
confirmed is skipped and the next one taken), and writes the post two ways:
  - Markdown: the name is the link (paste at old.reddit.com, or the app's Markdown mode)
  - plain:    the address on its own line under each deal (works anywhere, phone app included)
  - --html:   a page with the post already showing clickable names and a "Copy post" button (Oct 17; Bastien: "the shoe
              name should be a clickable link"): it copies the links as rich text, so they stay clickable when pasted in
              Reddit's normal editor (no Markdown mode needed)

Shoes: famous models first (the ones people search for), biggest discount first, 7+ sizes at the shown price, no spikes.
Gear: vests, tights, jackets, watches, lights from known brands, 3+ sizes (or one-size gear), $30+ (US$ on the USA side).
One per model (men's and women's of the same shoe count once). Links: the shoe price page when it exists, else a ?q= search
that finds that item (checked against today's data).

  python tools/reddit_post.py --ref reddit-runningshoes            # both countries
  python tools/reddit_post.py --ref fb-trail --side ca --out post.md
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
import livecheck  # noqa: E402

SITE = "https://thegearfox.com"
fold = lambda s: unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()

HYPE = ["vaporfly", "alphafly", "pegasus", "vomero", "invincible", "zoom fly", "superblast", "novablast", "megablast", "metaspeed",
        "kayano", "nimbus", "cumulus", "clifton", "bondi", "mach", "speedgoat", "rocket x", "cielo", "skyward", "ghost", "glycerin",
        "hyperion", "adrenaline", "endorphin", "triumph", "kinvara", "ride 1", "guide 1", "peregrine", "xodus", "adios pro", "boston",
        "evo sl", "prime x", "1080", "rebel", "more v", "supercomp", "cloudmonster", "cloudsurfer", "cloudboom", "cloudeclipse",
        "neo vista", "rebellion pro", "hyperwarp", "wave rider", "torrent", "ultrafly", "norvan", "sylan", "genesis", "s/lab",
        "pulsar", "aero glide", "lone peak", "olympus", "tecton", "zinal", "mafate", "catamount", "norda 00"]
SHOE_BR = {"nike", "adidas", "hoka", "brooks", "saucony", "asics", "new balance", "on", "altra", "salomon", "mizuno", "puma",
           "la sportiva", "merrell", "the north face", "topo athletic", "norda", "arc'teryx", "craft", "inov-8", "scarpa", "karhu"}
GEAR_BR = {"nathan", "salomon", "patagonia", "arc'teryx", "the north face", "ciele", "janji", "rabbit", "tracksmith", "satisfy",
           "garmin", "coros", "suunto", "black diamond", "petzl", "brooks", "hoka", "on", "nike", "adidas", "smartwool", "oakley",
           "ultimate direction", "craft", "icebreaker", "saucony", "new balance", "asics", "2xu", "gorewear", "sugoi", "garneau",
           "odlo", "life sports gear", "kogalla", "raidlight", "osprey", "camelbak", "mec"}
FAMOUS_CDN = ["arc'teryx", "norda", "ciele", "saxx", "mec", "lole", "tentree", "reigning champ", "knix", "kombi", "naak", "sugoi"]
GEAR_GROUPS = {"packs", "gear", "watches", "tops", "bottoms", "gloves", "headwear"}


def base(n):
    n = re.sub(r"\s*\((also )?available in [^)]*\)", "", n, flags=re.I)       # "(Available in Wide Widths)"
    n = re.sub(r"\s*-\s*(men|women)'?s.*$|\s*-\s*unisex.*$|\s*\((men|women)'?s\)", "", n, flags=re.I)
    return re.sub(r"[\s-]*(road|trail)?[\s-]*(running|race|racing)?[\s-]*shoes?$", "", n, flags=re.I).strip(" -").removesuffix(" Road")


def noun(n):
    """What kind of thing it is, from the last word of the name: Knee Warmer / Leg Warmers / Leg Cooler = one kind."""
    w = re.sub(r"[^a-z ]", "", fold(base(n))).split() or [""]
    w = w[-1].rstrip("s")
    if "vest" in fold(n) or "vesta" in fold(n):
        return "vest"                       # Race Vesta, Hydration Race Vest 4L: one kind
    return "warmer" if w in ("warmer", "cooler", "warm", "sleeve") else w


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", fold(s))).strip("-")


def best_band(it, need):
    """The deepest discount that still has `need` sizes (within 3 points of it), wides not counted."""
    sale = sorted([s for s in it["sz"] if len(s) > 3 and s[3] and s[1] < s[3]], key=lambda s: s[1] / s[3])
    for s0 in sale:
        pct = 1 - s0[1] / s0[3]
        at = [s for s in sale if 1 - s[1] / s[3] >= pct - 0.03 and not str(s[0]).endswith(("~W", "~N"))]
        if len({s[0] for s in at}) >= need:
            return pct, at
    return None, None


def confirm(it, at, fx, us):
    for s in sorted(at, key=lambda s: s[1])[:3]:
        u = it["of"][s[2]]
        shop = "/products/" in u
        if livecheck.still_on_sale(u, round(s[1] / fx, 2), s[4] if len(s) > 4 else None, us=us and shop) is True:
            return True
    return False


def cdn_brands():
    """The site's Canadian-brands list (index.html CDN_BRANDS, checked by hand), so posts and the 🍁 filter agree."""
    html = (ROOT / "site" / "index.html").read_text()
    m = re.search(r"const CDN_BRANDS=new Set\(\[(.*?)\]\)", html, re.S)
    return set(re.findall(r'"([^"]+)"', m.group(1)))


# Oct 17 (Bastien, r/runTO: "Put best deals around Toronto"): stores with shops in Toronto / the GTA
TORONTO = ["runningfree.com", "runningroom.com", "blacktoerunning.com", "sportinglife.ca", "mec.ca", "sportchek.ca",
           "decathlon.ca", "footlocker.ca", "arcteryx.com"]
# Stores per place (--city): Toronto = shops in the city; Québec and BC = based in the province
CITIES = {"toronto": TORONTO,
          # Oct 18 (Bastien: "local means Quebec province", the Montréal-Québec City corridor): Québec-based stores and brands, + MEC (stores in Montréal and Québec City)
          "quebec": ["svpsports.ca", "sportsexperts.ca", "boutiqueendurance.ca", "lecoureur.com", "lecoureurnordique.ca", "sail.ca",
                     "altitude-sports.com", "thelasthunt.com", "innerselfrunning.com", "balmoralrunning.com",
                     "krononutrition.com", "brixrechargeparlanature.com", "upika.ca", "mec.ca"],
          # and the same for BC (Vancouver posts): BC-based shops and brands only
          "bc": ["vanrunco.com", "shop.forerunners.ca", "racketsandrunners.ca", "frontrunners.ca", "capra.run", "runuphill.ca",
                 "cowichanvalleyrunning.com", "sea2skynutrition.ca", "arcteryx.com", "mec.ca"]}


def store_names():
    html = (ROOT / "site" / "index.html").read_text()
    return {d: n for d, n in re.findall(r'"([a-z0-9.-]+\.[a-z]+)":\["([^"]+)"', html)}


def host(u):
    return re.sub(r"^https?://(www\.)?", "", u).split("/")[0].lower()


def side_picks(side, ref, n_shoes=6, n_gear=4, log=print, kind=None, sex=None, under=None, canadian=False, direct=False, stores=None, exclude=(), hand=()):
    d = requests.get(f"{SITE}/{'sale.json' if side == 'ca' else 'sale-us.json'}", timeout=200).json()
    fx = d["fx"]["USD"] if side == "us" else 1.0
    pre = "shoes" if side == "ca" else "us/shoes"
    pages = requests.get(f"{SITE}/{pre}/pages.json", timeout=60).json()
    items = [dict(i, n=re.sub(r"(?i)\bendorphine\b", "Endorphin", i["n"])) for i in d["items"] if i.get("ca")]   # Running Room typo
    everything = list(items)    # search links must find only this item on the whole site, not just among the Toronto picks
    if stores:           # only the sizes whose best price is at one of these stores (r/runTO: shops you can walk into)
        keep = []
        for i in items:
            sz = [x for x in i["sz"] if any(host(i["of"][x[2]]).endswith(st) for st in stores)]
            if sz:
                keep.append(dict(i, sz=sz))
        items = keep
    if canadian:         # Canadian brands only (r/BuyCanadian, Canada pages): any of their shoes, gear, clothing or fuel
        cb = cdn_brands()
        items = [i for i in items if fold(i["b"]) in cb]
    if sex:              # a women's or men's post (r/xxrunning…): that cut, or unisex
        items = [i for i in items if not i.get("sx") or sex in i["sx"]]
    hay = [(i, fold(i["b"] + " " + i["n"])) for i in everything]
    shoes, gear = [], []
    for it in items:
        if it.get("t") == "spike":
            continue
        b, n = it["b"].lower(), fold(it["n"])
        if re.search(r"cumulus 16|kayano 14|gt-?2160|gel-?nyc|gel-?1130|1906|2002r|990v|530|9060", n):   # retro lifestyle reissues
            continue
        if it["g"] == "shoes" and b in SHOE_BR:
            rank = next((k for k, h in enumerate(HYPE) if h in n), None)
            if re.search(r"spike|track|terminal vt|velocity mp|\bkids?\b|youth|junior|grade school|\bgs\b", n):
                continue                          # Oct 14: a track spike and a kids' shoe made a beginner list
            if not re.search(r"[a-z]{3}", fold(base(it["n"])).replace(b, "")):
                continue                          # a name that is only the brand ("New Balance New Balance")
            if rank is None and (kind != "daily" or under) and not canadian:   # daily lists (C25K) still want known models          # themed posts take any known-brand shoe of that kind
                continue
            if kind and it.get("t") != kind:
                continue
            pct, at = best_band(it, 5 if canadian else 7)
            if pct and pct >= 0.30 and (not under or min(s[1] for s in at) / fx <= under):
                shoes.append((pct, it, at))
        elif ((it["g"] in GEAR_GROUPS and b in GEAR_BR) or (canadian and it["g"] != "shoes")) \
                and not (kind == "daily" and (it["g"] == "packs" or re.search(r"vest|onesie", n))):   # beginners: no race vests
            pct, at = best_band(it, 1 if it["g"] in ("gear", "watches", "nutrition", "packs") else 3)
            if pct and pct >= (0.25 if canadian else 0.35) and min(s[1] for s in at) / fx >= (10 if canadian else 30) and (not under or min(s[1] for s in at) / fx <= under) \
                    and (kind != "trail" or re.search(r"trail|vest|pole|headlamp|light|wind|rain|jacket", fold(it["n"]))):
                gear.append((pct, it, at))
    out = {}
    brands, nouns = {}, {}
    for kind, pool, k in (("shoes", shoes, n_shoes), ("gear", gear, n_gear)):
        if kind == "gear" and canadian:          # fewer Canadian shoes than asked: gear fills the list
            k += n_shoes - len(out.get("shoes", []))
        # Canadian posts: the brands people know first (Bastien, Oct 11: "you haven't found Canadian items like Arc'teryx")
        fame = lambda it: FAMOUS_CDN.index(fold(it["b"])) if canadian and fold(it["b"]) in FAMOUS_CDN else len(FAMOUS_CDN)
        pool.sort(key=lambda r: (fame(r[1]), -r[0]))
        got, seen, groups = [], set(), {}
        brands = {}
        for pct, it, at in pool:
            if len(got) >= k:
                break
            key = fold(it["b"] + " " + base(it["n"]))
            if any(x in key for x in exclude):     # Oct 18: same sub two days in a row gets fresh items (--exclude)
                continue
            fam = re.sub(r"\s*(v?\d+(\.\d)?)$", "", key)          # Neo Vista 2 and Neo Vista: one model family per post
            if key in seen or fam in seen or (kind == "gear" and groups.get(it["g"], 0) >= 2) \
                    or ((canadian or kind) and brands.get(fold(it["b"]), 0) >= 2) \
                    or (kind == "gear" and nouns.get(noun(it["n"]), 0) >= 1):     # a mix of brands and of kinds of thing     # gear: a mix, at most 2 of a kind
                continue
            if not confirm(it, at, fx, side == "us"):
                u0 = it["of"][min(at, key=lambda s: s[1])[2]]
                if any(d in u0 for d in hand):     # Oct 18 (Bastien: "add MEC ones and I'll manually check them"): kept, flagged
                    log(f"  CHECK BY HAND (store blocks our check): {it['b']} {it['n']} -> {u0}")
                else:
                    log(f"  skipped (not confirmed on the store's page): {it['b']} {it['n']}")
                    continue
            name = re.sub(r"[®™]", "", f"{it['b']} {base(it['n'])}")
            m = re.search(r"(men|women)'?s", it["n"], re.I)
            label = name + (f" ({m.group(1).lower()}'s)" if m and not re.search(r"(men|women)'?s", name, re.I) else "")
            sl = slug(name)
            if kind == "shoes" and sl in pages and not (pages[sl] or {}).get("to"):
                link = f"{SITE}/{pre}/{sl}/?ref={ref}"
            else:          # a search that finds this item: the shortest run of name words that matches nothing else
                words = re.sub(r"[^a-z0-9' ]+", " ", fold(name)).split()
                q = None
                for j in range(2, len(words) + 1):
                    cand = words[:j]
                    hits = [i for i, h in hay if all(w in h for w in cand)]
                    if hits and all(fold(i["b"] + " " + base(i["n"])) == key for i in hits):
                        q = " ".join(cand)
                        break
                if q is None:      # Oct 17: "On Cloudsurfer" also finds Cloudsurfer 2 / Max / Next: no precise link, next item
                    log(f"  skipped (no link that finds only this item): {it['b']} {it['n']}")
                    continue
                link = f"{SITE}/?{'c=us&' if side == 'us' else ''}q={quote(q)}&ref={ref}"
            seen |= {key, fam}
            groups[it["g"]] = groups.get(it["g"], 0) + 1
            brands[fold(it["b"])] = brands.get(fold(it["b"]), 0) + 1
            if kind == "gear":
                nouns[noun(it["n"])] = nouns.get(noun(it["n"]), 0) + 1
            if direct:       # Oct 12: Reddit's spam filter removed a post with 20 thegearfox.com links: link the store itself
                link = it["of"][min(at, key=lambda s: s[1])[2]]
            lo, was = min(s[1] for s in at) / fx, max(s[3] for s in at) / fx
            at_host = host(it["of"][min(at, key=lambda s: s[1])[2]])
            names = store_names()
            shop = next((n for d_, n in names.items() if at_host.endswith(d_)), at_host) if stores else None
            got.append({"label": label, "price": lo, "was": was, "pct": round(pct * 100), "link": link,
                        "sizes": len({s[0] for s in at}), "store": shop})
        out[kind] = got
    return out


def money(v):
    return f"${v:,.2f}".replace(".00", "") if v >= 100 else f"${v:,.2f}"


FOOT = ""


def write(picks, sides):
    md, plain = [], []
    for side in sides:
        title = "Canada" if side == "ca" else "USA"
        md.append(f"**{title}**\n")
        plain.append(f"{title}\n")
        n = 0
        for kind in ("shoes", "gear"):
            for x in picks[side][kind]:
                n += 1
                line = f"{money(x['price'])} (was {money(x['was'])}, −{x['pct']}%)" + (f" at {x['store']}" if x.get("store") else "")
                md.append(f"{n}. [{x['label']}]({x['link']}): {line}")
                plain.append(f"{n}. {x['label']}: {line}\n{x['link']}\n")
        md.append("")
    if FOOT:
        md.append(FOOT)
        plain.append(FOOT)
    return "\n".join(md), "\n".join(plain)


def write_html(picks, sides, ref):
    """The copy page: names are links; the button copies the list as rich text (+ the Markdown as plain text)."""
    import html as H
    import json
    md, _ = write(picks, sides)
    body = []
    for side in sides:
        if len(sides) > 1:
            body.append(f"<p><strong>{'Canada' if side == 'ca' else 'USA'}</strong></p>")
        body.append("<ol>")
        for kind in ("shoes", "gear"):
            for x in picks[side][kind]:
                line = f"{money(x['price'])} (was {money(x['was'])}, −{x['pct']}%)" + (f" at {x['store']}" if x.get("store") else "")
                body.append(f'<li><a href="{H.escape(x["link"])}">{H.escape(x["label"])}</a>: {H.escape(line)}</li>')
        body.append("</ol>")
    if FOOT:
        body.append("<p>" + re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', H.escape(FOOT).strip("*")) + "</p>")
    post = "\n".join(body)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reddit Post Copy</title><style>
:root{{--bg:#fff;--ink:#17201C;--mute:#5b6660;--line:#dfe5e1;--acc:#e8692c;--link:#1a5fb4}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#151a18;--ink:#eef2ef;--mute:#a3ada7;--line:#2c3430;--link:#8cb8ff}}}}
:root[data-theme="dark"]{{--bg:#151a18;--ink:#eef2ef;--mute:#a3ada7;--line:#2c3430;--link:#8cb8ff}}
body{{background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:720px;margin-inline:auto}}
a{{color:var(--link)}} button{{font:600 17px system-ui;background:var(--acc);color:#fff;border:0;border-radius:10px;padding:12px 18px;width:100%}}
#post{{border:1px solid var(--line);border-radius:10px;padding:4px 14px;margin:14px 0}} li{{margin:6px 0}} .m{{color:var(--mute);font-size:14px}}
</style></head><body>
<button id="copy">Copy post</button>
<p class="m" id="msg">Tap Copy post, then paste in Reddit's normal editor: the names stay clickable. ({H.escape(ref)})</p>
<div id="post">{post}</div>
<script>
const MD={json.dumps(md)};
document.getElementById('copy').onclick=async()=>{{
  const el=document.getElementById('post'),msg=document.getElementById('msg');
  try{{await navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([el.innerHTML],{{type:'text/html'}}),'text/plain':new Blob([MD],{{type:'text/plain'}})}})]);
    msg.textContent='Copied. Paste it in the post body on Reddit.';}}
  catch(e){{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);
    msg.textContent=document.execCommand('copy')?'Copied. Paste it in the post body on Reddit.':'Selected: tap Copy in the menu.';}}
}};
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="tracking tag, one per place: reddit-runningshoes, fb-trail-bc…")
    ap.add_argument("--side", choices=["ca", "us", "both"], default="both")
    ap.add_argument("--out", help="write the Markdown here (the plain version goes beside it, .txt)")
    ap.add_argument("--kind", choices=["daily", "race", "trail"], help="themed post: only this kind of shoe")
    ap.add_argument("--sex", choices=["men", "women"], help="themed post: men's or women's (unisex included)")
    ap.add_argument("--direct", action="store_true", help="link each item to the store (one Gear Fox line at the bottom)")
    ap.add_argument("--canadian", action="store_true", help="Canadian brands only (the site's 🍁 list): 4 shoes + 6 others")
    ap.add_argument("--under", type=float, help="themed post: nothing over this price (C25K: --under 100)")
    ap.add_argument("--shoes", type=int, help="shoes per country (default 6, --canadian 4)")
    ap.add_argument("--gear", type=int, help="other items per country (default 4, --canadian 6)")
    ap.add_argument("--exclude", default="", help="comma-separated words: skip items whose brand+model contains any (items posted there recently)")
    ap.add_argument("--html", help="also write a copy page here (names as links, 'Copy post' button keeps them clickable)")
    ap.add_argument("--toronto", action="store_true", help="only deals at stores with Toronto shops (r/runTO), store named on each line")
    ap.add_argument("--hand-check", default="", help="comma-separated store domains whose deals stay in even when our check is blocked (mec.ca); listed as CHECK BY HAND")
    ap.add_argument("--city", choices=sorted(CITIES) + ["montreal", "vancouver"], help="only deals at stores with shops in that city, store named on each line")
    a = ap.parse_args()
    if a.toronto:
        a.city = "toronto"
    a.city = {"montreal": "quebec", "vancouver": "bc"}.get(a.city, a.city)
    sides = ["ca", "us"] if a.side == "both" else [a.side]
    n = (4, 6) if a.canadian else (6, 4)
    n = (n[0] if a.shoes is None else a.shoes, n[1] if a.gear is None else a.gear)
    picks = {s: side_picks(s, a.ref, n[0], n[1], log=lambda m: print(m, file=sys.stderr), kind=a.kind, sex=a.sex, under=a.under,
                           canadian=a.canadian, direct=a.direct, stores=CITIES[a.city] if a.city else None,
                           exclude=[fold(x.strip()) for x in a.exclude.split(",") if x.strip()],
                           hand=[x.strip() for x in a.hand_check.split(",") if x.strip()]) for s in sides}
    global FOOT
    if a.direct:
        FOOT = (f"*Found with [thegearfox.com](https://thegearfox.com/?ref={a.ref}), a free site I made that shows running deals "
                "in your size. No affiliate links, I don't make anything from these.*")
    md, plain = write(picks, sides)
    print(md)
    if a.out:
        Path(a.out).write_text(md)
        Path(a.out).with_suffix(".txt").write_text(plain)
    if a.html:
        Path(a.html).write_text(write_html(picks, sides, a.ref))


if __name__ == "__main__":
    main()
