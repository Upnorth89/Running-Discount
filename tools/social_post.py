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


def picks(sale, pages, hist, state, today):
    names = store_names()
    cut = (today - timedelta(days=7)).isoformat()
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
        reg = max((e[3] or 0) for e in at)
        if len(at) < 5 or not reg or best >= reg * 0.9:
            continue
        k = f'{d["b"]}|{d["n"]}|{d["g"]}|{1 if d.get("w") else 0}'.lower()
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
        nm_ = re.sub(r"\b[A-Z]{5,}\b", lambda w: w.group(0).capitalize(), SP.base_model(d["n"]))   # "ENDORPHIN EDGE" -> "Endorphin Edge"
        out.append({"slug": slug, "b": d["b"], "name": f'{d["b"]} {nm_}', "gender": gender, "now": best,
                    "was": then, "reg": reg, "pct": round(100 * (1 - best / reg)), "drop": round(off), "store": names.get(host(u), host(u)),
                    "url": u, "variant": e[4] if len(e) > 4 else None, "sizes": len(at), "img": d.get("img") or "",
                    "page": f"{SITE}/shoes/{slug}/"})
    out.sort(key=lambda x: (-x["drop"], -x["pct"]))
    seen, keep = set(), []
    for p in out:                       # one per brand and per model a day
        if p["b"].lower() in seen or any(q["slug"] == p["slug"] for q in keep):
            continue
        seen.add(p["b"].lower())
        keep.append(p)
    return keep


def confirmed(p):
    """Still on sale on the store's own page right now (the Instagram kit's rule: blocked or unsure = left out)."""
    try:
        import livecheck
        return livecheck.still_on_sale(p["url"], p["now"], p.get("variant")) is True
    except Exception:
        return False


def text(p, ref):
    g = f' ({p["gender"]})' if p["gender"] else ""
    link = f'{p["page"]}?ref={ref}'
    return (f'{p["name"]}{g} dropped ${p["drop"]} this week: ${p["now"]:.2f} at {p["store"]} '
            f'(regular ${p["reg"]:.0f}, −{p["pct"]}%), {p["sizes"]} sizes at that price.\n'
            f'Every size and store, checked daily: {link}'), link


def bluesky(p, body, link):
    """Bluesky's own API (app password, no review needed): a post with a link card (title, line, photo)."""
    s = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession", timeout=30,
                      json={"identifier": os.environ["BLUESKY_HANDLE"], "password": os.environ["BLUESKY_APP_PASSWORD"]}).json()
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
    i = body.find(link)
    rec = {"$type": "app.bsky.feed.post", "text": body, "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
           "langs": ["en"], "embed": {"$type": "app.bsky.embed.external", "external": card},
           "facets": [{"index": {"byteStart": len(body[:i].encode()), "byteEnd": len(body[:i + len(link)].encode())},
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
    cands = picks(sale, pages, history(), state, today)
    posts, live = [], os.environ.get("SOCIAL_LIVE") == "1"
    for p in cands:
        if len([q for q in posts if q["ok"]]) >= PER_DAY:
            break
        p["ok"] = confirmed(p)
        p["text"], link = text(p, "bluesky")
        if p["ok"] and live and os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_APP_PASSWORD"):
            try:
                p["posted"] = {"bluesky": bluesky(p, p["text"], link)}
                state[p["slug"]] = today.isoformat()
            except Exception as e:
                p["error"] = str(e)[:200]
        posts.append(p)
        print(("OK  " if p["ok"] else "SKIP") + " " + p["text"].replace("\n", " | "))
    (out / "posts.json").write_text(json.dumps(posts, indent=1, ensure_ascii=False))
    sf.write_text(json.dumps(state, indent=1))
    preview(posts, out)
    print(f"{len(cands)} real drops today, {sum(p['ok'] for p in posts)} confirmed; live={live}")


if __name__ == "__main__":
    main()
