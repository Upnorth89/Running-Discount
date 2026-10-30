"""Daily "real price drop" posts (Oct 26, Bastien: "How can you make growth into an automatic feature?").

Every morning after the refresh: today's biggest REAL drops on shoes that have a shoe page (best price a week ago in the
price history vs today, 10% or $10 and at least $5, the Friday email's rule), 5+ sizes at today's price, still on sale on
the store's own page (livecheck). One post each, facts only (price, was, % off, store, sizes), linking to the shoe page
with ?ref=<network> so the Monday check-in counts visits and sign-ups per network.

  python tools/social_post.py OUT_DIR            # dry run: writes OUT_DIR/posts.json + posts.html (a preview), posts nothing
  SOCIAL_LIVE=1 python tools/social_post.py OUT  # posts to every network whose keys are set (GitHub secrets only):
      Bluesky: BLUESKY_HANDLE + BLUESKY_APP_PASSWORD (an app password made in Bluesky's settings, never the real password)

Bastien said yes (Oct 26): social.yml sets SOCIAL_LIVE=1 unless the repo variable SOCIAL_LIVE is 0 (pause); a network
posts only once its keys are in GitHub secrets. Each item is posted once per 21 days
(OUT_DIR/social-state.json, kept on the history branch by social.yml).
"""
import html
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
import shoe_pages as SP            # noqa: E402  (base_model + slugify: the same page address the site uses)

SITE = os.environ.get("SITE", "https://thegearfox.com").rstrip("/")
HISTORY_URL = "https://raw.githubusercontent.com/Upnorth89/Running-Discount/history/prices.jsonl"
PER_DAY = int(os.environ.get("SOCIAL_PER_DAY", "3"))
REPOST_DAYS = 21
UA = {"User-Agent": "TheGearFoxBot/1.0 (+https://thegearfox.com/about.html)"}


def store_names():
    t = (ROOT / "site" / "index.html").read_text()
    return {d: n for d, n in re.findall(r'"([a-z0-9.-]+\.[a-z]+)":\["([^"]+)"', t)}


def host(u):
    return re.sub(r"^https?://(www\.)?", "", u).split("/")[0].lower()


def history():
    p = os.environ.get("HISTORY_FILE")
    text = Path(p).read_text() if p and Path(p).exists() else requests.get(HISTORY_URL, timeout=180).text
    h = {}
    for line in text.splitlines():
        try:
            r = json.loads(line)
            h[r["k"]] = r["h"]
        except Exception:
            pass
    return h


def picks(sale, pages, hist, state, today, side="ca"):
    """side "us" (Oct 26, Pinterest's USA board): US stores, prices in US$ (the history's "us|" lines are in US$; the site files
    keep CAD, so today's price is divided by the file's fx), links to /us/shoes/."""
    names = store_names()
    cut = (today - timedelta(days=7)).isoformat()
    us = side == "us"
    fx = float((sale.get("fx") or {}).get("USD") or 1.37) if us else 1.0
    out = []
    for d in sale["items"]:
        if d.get("g") != "shoes" or not d.get("ca") or not d.get("sz"):
            continue
        slug = SP.slugify(f'{d["b"]} {SP.base_model(d["n"])}')
        m = pages.get(slug)
        if m and m.get("to"):
            slug, m = m["to"], pages.get(m["to"])
        if not m:
            continue
        best = min(e[1] for e in d["sz"])
        at = [e for e in d["sz"] if e[1] <= best + 0.01]
        reg = max((e[3] or 0) for e in at) / fx
        best = round(best / fx, 2)
        if len(at) < 5 or not reg or best >= reg * 0.9:
            continue
        k = ("us|" if us else "") + f'{d["b"]}|{d["n"]}|{d["g"]}|{1 if d.get("w") else 0}'.lower()
        h = hist.get(k) or []
        old = [x for x in h if x[0] <= cut]
        if not old:
            continue
        then = old[-1][1]
        off = then - best
        if not (off >= 5 and (off >= 10 or off / then >= 0.10) and best < then * 0.97):
            continue
        if state.get(slug, "") >= (today - timedelta(days=REPOST_DAYS)).isoformat():
            continue
        e = at[0]
        u = d["of"][e[2]]
        gender = "Women's" if d.get("sx") == ["women"] else "Men's" if d.get("sx") == ["men"] else ""
        nm_ = re.sub(r"\b(?!GTX\b|BOA\b)[A-Z]{4,}\b", lambda w: w.group(0).capitalize(), SP.base_model(d["n"]))   # "Endorphin EDGE" -> "Endorphin Edge"
        out.append({"slug": slug, "b": d["b"], "name": f'{d["b"]} {nm_}', "gender": gender, "now": best,
                    "was": then, "reg": reg, "pct": round(100 * (1 - best / reg)), "drop": round(off), "store": names.get(host(u), host(u)),
                    "url": u, "variant": e[4] if len(e) > 4 else None, "sizes": len(at), "img": d.get("img") or "",
                    "page": f"{SITE}/{'us/shoes' if us else 'shoes'}/{slug}/", "side": side})
    out.sort(key=lambda x: (-x["drop"], -x["pct"]))
    seen, keep = set(), []
    for p in out:                       # one per brand and per model a day
        if p["b"].lower() in seen or any(q["slug"] == p["slug"] for q in keep):
            continue
        seen.add(p["b"].lower())
        keep.append(p)
    return keep


# Oct 26 (Bastien OK'd, growth chat's spec): shoes every day (shoe pages bring the sign-ups) + ONE rotating category a day, by date:
# most popular (the non-shoe category visitors clicked most in the last 7 days; clicks don't record the item), coats/jackets,
# pants/tights, shirts/tops. Same honesty rules: real drop this week, confirmed on the store page, S, M AND L at the shown price
# (one-size gear: in stock), one per brand, each item once per 21 days. Running side only: the price history doesn't cover hiking yet.
# Link = a homepage search that finds only that item (?q=), ref "<network>-<category>" so the Nov 17 check splits shoes vs the rest.
ROTATION = ("popular", "coats", "pants", "tops")
JACKETY = re.compile(r"\b(jackets?|anorak|shell|parka|windbreaker|wind ?shell|softshell|hardshell)\b", re.I)
CLOTHES = {"tops", "bottoms", "bras"}
SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL"]


def rotation(today):
    return ROTATION[today.toordinal() % len(ROTATION)]


def popular_group():
    """The non-shoe, non-food category with the most store clicks on our site in the last 7 days (own analytics)."""
    key = os.environ.get("SUPABASE_SECRET_KEY")
    if not key:
        return None
    sb = os.environ.get("SUPABASE_URL", "https://krwymmkauwqqxjxbvkyq.supabase.co").rstrip("/")
    h = {"apikey": key, **({"Authorization": f"Bearer {key}"} if key.count(".") == 2 else {})}
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    count, got = {}, 0
    try:
        while True:
            r = requests.get(f"{sb}/rest/v1/ana_events", timeout=60, headers={**h, "Range": f"{got}-{got + 999}"},
                             params={"select": "detail", "kind": "eq.deal-click", "at": f"gte.{since}"})
            r.raise_for_status()
            rows = r.json()
            for x in rows:
                g = ((x.get("detail") or "").split("|") + ["", ""])[1]
                if g and g not in ("shoes", "nutrition"):
                    count[g] = count.get(g, 0) + 1
            got += len(rows)
            if len(rows) < 1000:
                break
    except Exception as e:
        print(f"popular category: clicks not read ({e})")
        return None
    return max(count, key=count.get) if count else None


def fits(d, cat, pop):
    g, t, n = d.get("g"), d.get("t") or "", d.get("n") or ""
    if cat == "coats":
        return g == "tops" and (t == "jacket" or bool(JACKETY.search(n)))
    if cat == "pants":
        return g == "bottoms" and t in ("pant", "tight")
    if cat == "tops":
        return g == "tops" and t in ("tee", "layer") and not JACKETY.search(n)
    return g not in ("shoes", "nutrition") and (g == pop if pop else True)


def _fold(s):
    import unicodedata
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


def _base(n):
    n = re.sub(r"\s*\((also )?available in [^)]*\)", "", n, flags=re.I)
    return re.sub(r"\s*-\s*(men|women)'?s.*$|\s*-\s*unisex.*$|\s*\((men|women)'?s\)", "", n, flags=re.I).strip(" -")


def unique_q(it, hay):
    """The shortest run of the item's own name words that the SITE's search (search_check.py = hayOf/qhas in index.html) answers
    with this item only (its colours count as one); never ending on a little word ("with", "and"). None = no precise link: skip it."""
    import search_check as SC
    name = re.sub(r"[®™]", "", f"{it['b']} {_base(it['n'])}")
    key = _fold(name)
    toks = [w for w in _fold(name).split() if SC.words(w)]
    for j in range(2, len(toks) + 1):
        if toks[j - 1] in ("with", "and", "for", "the", "de", "et", "-", "&"):
            continue
        q = SC.words(" ".join(toks[:j]))
        hits = [i for i, h in hay if all(SC.qhas(h, w) for w in q)]
        if hits and all(_fold(i["b"] + " " + _base(i["n"])) == key for i in hits):
            return " ".join(toks[:j])
    return None


def picks_cat(sale, hist, state, today, cat, side="ca", pop=None, everything=None):
    """Today's real drops in the rotating category, same rules as the shoes; each gets a search link that finds only it."""
    from urllib.parse import quote
    names = store_names()
    cut = (today - timedelta(days=7)).isoformat()
    us = side == "us"
    fx = float((sale.get("fx") or {}).get("USD") or 1.37) if us else 1.0
    import search_check as SC
    # a ?q= landing shows full-price items too (Oct 26: "2xu core compression long" also found a full-price "Long Sleeve Top"),
    # so the link must be unique in the WHOLE catalogue (deals.json), as tools/reddit_post.py does
    hay = [(i, SC.hay(i)) for i in (everything or sale)["items"]]
    out = []
    for d in sale["items"]:
        if not d.get("ca") or not d.get("sz") or not fits(d, cat, pop):
            continue
        best = min(e[1] for e in d["sz"])
        at = [e for e in d["sz"] if e[1] <= best + 0.01]
        keys = {str(e[0]).upper() for e in at}
        if d["g"] in CLOTHES or keys - {"OS"}:
            if not {"S", "M", "L"} <= keys:
                continue
        elif "OS" not in keys:
            continue
        reg = max((e[3] or 0) for e in at) / fx
        best = round(best / fx, 2)
        if not reg or best >= reg * 0.9:
            continue
        k = ("us|" if us else "") + f'{d["b"]}|{d["n"]}|{d["g"]}|{1 if d.get("w") else 0}'.lower()
        old = [x for x in hist.get(k) or [] if x[0] <= cut]
        if not old:
            continue
        then = old[-1][1]
        off = then - best
        if not (off >= 5 and (off >= 10 or off / then >= 0.10) and best < then * 0.97):
            continue
        sid = "q:" + _fold(d["b"] + " " + _base(d["n"]))
        if state.get(sid, "") >= (today - timedelta(days=REPOST_DAYS)).isoformat():
            continue
        q = unique_q(d, hay)
        if not q:
            continue
        e = at[0]
        u = d["of"][e[2]]
        gender = "Women's" if d.get("sx") == ["women"] else "Men's" if d.get("sx") == ["men"] else ""
        letters = [s for s in SIZE_ORDER if s in keys]
        out.append({"slug": sid, "b": d["b"], "name": f'{d["b"]} {_base(d["n"])}', "gender": gender, "now": best, "was": then, "reg": reg,
                    "pct": round(100 * (1 - best / reg)), "drop": round(off), "store": names.get(host(u), host(u)), "url": u,
                    "variant": e[4] if len(e) > 4 else None, "sizes": len(at), "img": d.get("img") or "", "side": side, "cat": cat,
                    "sizes_label": " · ".join(letters) if letters else "One size",
                    "page": f"{SITE}/?{'c=us&' if us else ''}q={quote(q, safe='')}"})
    out.sort(key=lambda x: (-x["drop"], -x["pct"]))
    seen, keep = set(), []
    for p in out:
        if p["b"].lower() not in seen:
            seen.add(p["b"].lower())
            keep.append(p)
    return keep


def with_ref(page, ref):
    return page + ("&" if "?" in page else "?") + f"ref={ref}"


def confirmed(p):
    """Still on sale on the store's own page right now (the Instagram kit's rule: blocked or unsure = left out)."""
    try:
        import livecheck
        return livecheck.still_on_sale(p["url"], p["now"], p.get("variant"), us=p.get("side") == "us") is True
    except Exception:
        return False


def text(p, ref):
    g = f' ({p["gender"]})' if p["gender"] else ""
    link = with_ref(p["page"], ref)
    sizes = f'{p["sizes_label"]} at that price' if p.get("sizes_label") else f'{p["sizes"]} sizes at that price'
    return (f'{p["name"]}{g} dropped ${p["drop"]} this week: ${p["now"]:.2f} at {p["store"]} '
            f'(regular ${p["reg"]:.0f}, −{p["pct"]}%), {sizes}.\n'
            f'Every size and store, checked daily: {link}'), link


def bluesky(p, body, link):
    """Bluesky's own API (app password, no review needed): a post with a link card (title, line, photo)."""
    s = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession", timeout=30,
                      json={"identifier": os.environ["BLUESKY_HANDLE"].strip().lstrip("@"), "password": os.environ["BLUESKY_APP_PASSWORD"].strip()}).json()
    if "accessJwt" not in s:     # Oct 26: a failed login showed up only as 'accessJwt'; say what Bluesky said (never the secrets)
        raise RuntimeError(f'Bluesky login failed: {s.get("error")}: {s.get("message")} (handle like thegearfox.bsky.social, app password from Settings > App passwords)')
    H = {"Authorization": f'Bearer {s["accessJwt"]}'}
    card = {"uri": link, "title": f'{p["name"]}: ${p["now"]:.2f} (−{p["pct"]}%)', "description": "Every size and store in Canada, checked daily."}
    if p["img"]:
        try:
            im = requests.get(p["img"], headers=UA, timeout=30)
            if im.ok and len(im.content) < 950_000:
                b = requests.post("https://bsky.social/xrpc/com.atproto.repo.uploadBlob", timeout=60,
                                  headers={**H, "Content-Type": im.headers.get("content-type", "image/jpeg")}, data=im.content).json()
                card["thumb"] = b["blob"]
        except Exception:
            pass
    # Oct 29: a 327-character post (a long ?q= search link) got "400 Bad Request": Bluesky takes 300. The text shows a short
    # label for the link (thegearfox.com/shoes/<slug>/ or thegearfox.com/?q=…) and the tap still opens the full tracked link.
    from urllib.parse import unquote
    short = unquote(re.sub(r"^https?://", "", link).split("&ref=")[0].split("?ref=")[0])
    if len(short) > 56:
        short = short[:54] + "…"
    body = body.replace(link, short)
    if len(body) > 300:                        # still too long: shorten the first line, keep the link line whole
        head, _, tail = body.partition("\n")
        body = head[:300 - len(tail) - 2].rstrip() + "…\n" + tail
    link_text = short
    i = body.find(link_text)
    rec = {"$type": "app.bsky.feed.post", "text": body, "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
           "langs": ["en"], "embed": {"$type": "app.bsky.embed.external", "external": card},
           "facets": [{"index": {"byteStart": len(body[:i].encode()), "byteEnd": len(body[:i + len(link_text)].encode())},
                       "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link}]}]}
    r = requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord", headers=H, timeout=30,
                      json={"repo": s["did"], "collection": "app.bsky.feed.post", "record": rec})
    r.raise_for_status()
    return r.json().get("uri")


def preview(posts, out):
    rows = "".join(f'<article><img src="{html.escape(p["img"])}" alt=""><div><b>{html.escape(p["name"])}</b>'
                   f'<p>{html.escape(p["text"]).replace(chr(10), "<br>")}</p><small>{"confirmed on the store page" if p["ok"] else "NOT confirmed: would be skipped"}</small></div></article>'
                   for p in posts) or "<p>No real drops today (that's allowed: no post beats a fake one).</p>"
    (out / "posts.html").write_text(f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Daily drop posts</title>'
                                    f'<style>body{{font:15px system-ui;max-width:640px;margin:16px auto;padding:0 16px}}article{{display:flex;gap:12px;border:1px solid #ddd;'
                                    f'border-radius:12px;padding:12px;margin:12px 0}}img{{width:96px;height:96px;object-fit:contain}}small{{color:#5c6660}}</style>'
                                    f'<h1>Daily drop posts ({date.today():%b %d})</h1>{rows}')


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/social")
    out.mkdir(parents=True, exist_ok=True)
    sf = out / "social-state.json"
    state = json.loads(sf.read_text()) if sf.exists() else {}
    sale = requests.get(f"{SITE}/sale.json", timeout=200).json()
    pages = requests.get(f"{SITE}/shoes/pages.json", timeout=60).json()
    today = date.today()
    hist = history()
    cat = rotation(today)
    shoes = picks(sale, pages, hist, state, today)
    try:
        everything = requests.get(f"{SITE}/deals.json", timeout=300).json()
    except Exception as e:
        print(f"deals.json not read ({e}): no rotating item today (its search link can't be checked)")
        everything = None
    rot = picks_cat(sale, hist, state, today, cat, pop=popular_group() if cat == "popular" else None, everything=everything) if everything else []
    print(f"today's rotating category: {cat} ({len(rot)} real drops)")
    posts, live = [], os.environ.get("SOCIAL_LIVE") == "1"
    # 1 rotating item (tried first) + shoes for the rest: 2 shoes, or 3 when no rotating item qualifies today
    for kind, p in [(cat, p) for p in rot] + [("shoes", p) for p in shoes]:
        ok = [q for q in posts if q["ok"]]
        if len(ok) >= PER_DAY:
            break
        if kind == cat and any(q["kind"] == cat for q in ok):
            continue
        p["kind"] = kind
        p["ok"] = confirmed(p)
        p["text"], link = text(p, f"bluesky-{kind}")
        if p["ok"] and live and os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_APP_PASSWORD"):
            try:
                p["posted"] = {"bluesky": bluesky(p, p["text"], link)}
                state[p["slug"]] = today.isoformat()
            except Exception as e:
                p["error"] = str(e)[:200]
        posts.append(p)
        print(("OK  " if p["ok"] else "SKIP") + " " + p["text"].replace("\n", " | "))   # OK = confirmed on the store page; posting result on the next line
        if p.get("posted") or p.get("error"):
            print("     -> " + (f'posted {p["posted"]["bluesky"]}' if p.get("posted") else f'NOT posted: {p["error"]}'))
    (out / "posts.json").write_text(json.dumps(posts, indent=1, ensure_ascii=False))
    sf.write_text(json.dumps(state, indent=1))
    preview(posts, out)
    print(f"{len(shoes)} shoe + {len(rot)} {cat} real drops today, {sum(p['ok'] for p in posts)} confirmed; live={live}")
    failed = [p for p in posts if p.get("error")]
    if failed:      # the run goes red so a failed login is never a quiet green run
        sys.exit(f"{len(failed)} post(s) failed: {failed[0]['error']}")


if __name__ == "__main__":
    main()
