#!/usr/bin/env python3
"""Reddit / Facebook post maker (Oct 11, 2026; Bastien: "post every 3 days on running gear", and the format he settled on:
"6 shoes 4 gear Canada and 6 shoes 4 gear USA, that's it", names as links).

Picks today's best deals from the live site, opens every one on the store's own page (livecheck: a deal that ended or can't be
confirmed is skipped and the next one taken), and writes the post two ways:
  - Markdown: the name is the link (paste at old.reddit.com, or the app's Markdown mode)
  - plain:    the address on its own line under each deal (works anywhere, phone app included)

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
GEAR_GROUPS = {"packs", "gear", "watches", "tops", "bottoms", "gloves", "headwear"}


def base(n):
    n = re.sub(r"\s*-\s*(men|women)'?s.*$|\s*-\s*unisex.*$|\s*\((men|women)'?s\)", "", n, flags=re.I)
    return re.sub(r"[\s-]*(road|trail)?[\s-]*(running|race|racing)?[\s-]*shoes?$", "", n, flags=re.I).strip(" -").removesuffix(" Road")


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


def side_picks(side, ref, n_shoes=6, n_gear=4, log=print, kind=None, sex=None, under=None):
    d = requests.get(f"{SITE}/{'sale.json' if side == 'ca' else 'sale-us.json'}", timeout=200).json()
    fx = d["fx"]["USD"] if side == "us" else 1.0
    pre = "shoes" if side == "ca" else "us/shoes"
    pages = requests.get(f"{SITE}/{pre}/pages.json", timeout=60).json()
    items = [i for i in d["items"] if i.get("ca")]
    if sex:              # a women's or men's post (r/xxrunning…): that cut, or unisex
        items = [i for i in items if not i.get("sx") or sex in i["sx"]]
    hay = [(i, fold(i["b"] + " " + i["n"])) for i in items]
    shoes, gear = [], []
    for it in items:
        if it.get("t") == "spike":
            continue
        b, n = it["b"].lower(), fold(it["n"])
        if it["g"] == "shoes" and b in SHOE_BR:
            rank = next((k for k, h in enumerate(HYPE) if h in n), None)
            if rank is None and not kind:          # themed posts take any known-brand shoe of that kind
                continue
            if kind and it.get("t") != kind:
                continue
            pct, at = best_band(it, 7)
            if pct and pct >= 0.30 and (not under or min(s[1] for s in at) / fx <= under):
                shoes.append((pct, it, at))
        elif it["g"] in GEAR_GROUPS and b in GEAR_BR:
            pct, at = best_band(it, 1 if it["g"] in ("gear", "watches") else 3)
            if pct and pct >= 0.35 and min(s[1] for s in at) / fx >= 30 and (not under or min(s[1] for s in at) / fx <= under) \
                    and (kind != "trail" or re.search(r"trail|vest|pole|headlamp|light|wind|rain|jacket", fold(it["n"]))):
                gear.append((pct, it, at))
    out = {}
    for kind, pool, k in (("shoes", shoes, n_shoes), ("gear", gear, n_gear)):
        pool.sort(key=lambda r: -r[0])
        got, seen, groups = [], set(), {}
        for pct, it, at in pool:
            if len(got) >= k:
                break
            key = fold(it["b"] + " " + base(it["n"]))
            fam = re.sub(r"\s*(v?\d+(\.\d)?)$", "", key)          # Neo Vista 2 and Neo Vista: one model family per post
            if key in seen or fam in seen or (kind == "gear" and groups.get(it["g"], 0) >= 2):     # gear: a mix, at most 2 of a kind
                continue
            if not confirm(it, at, fx, side == "us"):
                log(f"  skipped (not confirmed on the store's page): {it['b']} {it['n']}")
                continue
            seen |= {key, fam}
            groups[it["g"]] = groups.get(it["g"], 0) + 1
            name = f"{it['b']} {base(it['n'])}"
            m = re.search(r"(men|women)'?s", it["n"], re.I)
            label = name + (f" ({m.group(1).lower()}'s)" if m and not re.search(r"(men|women)'?s", name, re.I) else "")
            sl = slug(name)
            if kind == "shoes" and sl in pages and not (pages[sl] or {}).get("to"):
                link = f"{SITE}/{pre}/{sl}/?ref={ref}"
            else:          # a search that finds this item: the shortest run of name words that matches nothing else
                words = fold(name).replace("-", " ").split()
                q = " ".join(words)
                for j in range(2, len(words) + 1):
                    cand = words[:j]
                    hits = [i for i, h in hay if all(w in h for w in cand)]
                    if hits and all(fold(i["b"] + " " + base(i["n"])) == key for i in hits):
                        q = " ".join(cand)
                        break
                link = f"{SITE}/?{'c=us&' if side == 'us' else ''}q={quote(q)}&ref={ref}"
            lo, was = min(s[1] for s in at) / fx, max(s[3] for s in at) / fx
            got.append({"label": label, "price": lo, "was": was, "pct": round(pct * 100), "link": link,
                        "sizes": len({s[0] for s in at})})
        out[kind] = got
    return out


def money(v):
    return f"${v:,.2f}".replace(".00", "") if v >= 100 else f"${v:,.2f}"


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
                line = f"{money(x['price'])} (was {money(x['was'])}, −{x['pct']}%)"
                md.append(f"{n}. [{x['label']}]({x['link']}): {line}")
                plain.append(f"{n}. {x['label']}: {line}\n{x['link']}\n")
        md.append("")
    return "\n".join(md), "\n".join(plain)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="tracking tag, one per place: reddit-runningshoes, fb-trail-bc…")
    ap.add_argument("--side", choices=["ca", "us", "both"], default="both")
    ap.add_argument("--out", help="write the Markdown here (the plain version goes beside it, .txt)")
    ap.add_argument("--kind", choices=["daily", "race", "trail"], help="themed post: only this kind of shoe")
    ap.add_argument("--sex", choices=["men", "women"], help="themed post: men's or women's (unisex included)")
    ap.add_argument("--under", type=float, help="themed post: nothing over this price (C25K: --under 100)")
    a = ap.parse_args()
    sides = ["ca", "us"] if a.side == "both" else [a.side]
    picks = {s: side_picks(s, a.ref, log=lambda m: print(m, file=sys.stderr), kind=a.kind, sex=a.sex, under=a.under) for s in sides}
    md, plain = write(picks, sides)
    print(md)
    if a.out:
        Path(a.out).write_text(md)
        Path(a.out).with_suffix(".txt").write_text(plain)


if __name__ == "__main__":
    main()
