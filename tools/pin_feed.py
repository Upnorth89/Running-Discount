"""Pinterest feeds (Oct 26; growth chat + Bastien: a 6-week Pinterest test, stop if under 30 first visits with ?ref=pinterest by mid-Dec).

Pinterest's "auto-publish from RSS" (business account + claimed site, no API review) reads one feed per board:
  site/pins/ca.xml  Canadian shoe pages (/shoes/<slug>/)      site/pins/us.xml  US shoe pages (/us/shoes/<slug>/)
Each item = one REAL price drop, the same picks as the Bluesky posts (tools/social_post.py: best price a week ago in the price
history vs today, 10% or $10 and at least $5, 5+ sizes at that price, still on sale on the store's own page, one per brand),
each shoe once per 21 days, up to 5 new per side per day, the last 50 kept (guid stable, so Pinterest never pins one twice).
Pin image: 1000x1500 JPG at site/pins/img/<date>-<side>-<slug>.jpg (Playwright), facts only; images older than 45 days go.

  python tools/pin_feed.py site            # morning: yesterday's feeds + today's new drops (needs HISTORY_FILE or hist/prices.jsonl)
  python tools/pin_feed.py site --carry    # any other run: put yesterday's feeds and images back (a deploy replaces the whole site)
"""
import base64
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scraper"))
import social_post as SPOST        # noqa: E402  (picks, store check, history)

SITE = "https://thegearfox.com"
PER_DAY, KEEP, IMG_DAYS = 5, 50, 45
SIDES = {"ca": ("sale.json", "shoes/pages.json", "The Gear Fox: running shoe price drops in Canada", "CAD"),
         "us": ("sale-us.json", "us/shoes/pages.json", "The Gear Fox: running shoe price drops in the US", "USD")}
UA = {"User-Agent": "TheGearFoxBot/1.0 (+https://thegearfox.com/about.html)"}
MEDIA = "http://search.yahoo.com/mrss/"
ET.register_namespace("media", MEDIA)


def old_items(side, prev):
    """Yesterday's items: from PIN_PREV (a folder) or the live site."""
    try:
        if prev:
            txt = (Path(prev) / f"{side}.xml").read_text()
        else:
            r = requests.get(f"{SITE}/pins/{side}.xml", headers=UA, timeout=60)
            if r.status_code != 200:
                return []
            txt = r.text
        out = []
        for it in ET.fromstring(txt).iter("item"):
            g = lambda k: (it.findtext(k) or "").strip()
            enc = it.find("enclosure")
            out.append({"title": g("title"), "link": g("link"), "desc": g("description"), "guid": g("guid"), "date": g("pubDate"),
                        "img": enc.get("url") if enc is not None else ""})
        return out
    except Exception as e:
        print(f"{side}: yesterday's feed not read ({e})")
        return []


def keep_images(site, items):
    """A deploy replaces the whole site: put back the images yesterday's items use (from the live site)."""
    d = site / "pins" / "img"
    d.mkdir(parents=True, exist_ok=True)
    for it in items:
        name = it["img"].rsplit("/", 1)[-1]
        f = d / name
        if not name or f.exists():
            continue
        try:
            r = requests.get(it["img"], headers=UA, timeout=60)
            if r.ok and r.headers.get("content-type", "").startswith("image/"):
                f.write_bytes(r.content)
        except Exception:
            pass


def age_days(it, today):
    try:
        return (today - parsedate_to_datetime(it["date"]).date()).days
    except Exception:
        return 0


def money(v):
    return f"${v:,.2f}".replace(".00", "") if v >= 100 else f"${v:,.2f}"


def card_html(p, cur):
    """The pin: photo big on white, then the facts (price, drop, % off, store, sizes), fox + address."""
    logo = "data:image/svg+xml;base64," + base64.b64encode((ROOT / "site" / "logo.svg").read_bytes()).decode()
    img = re.sub(r"([?&])width=\d+", r"\1width=1000", p["img"])
    g = f' · {p["gender"]}' if p["gender"] else ""
    e = html.escape
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@500;700;800&display=swap');
*{{box-sizing:border-box;margin:0}}body{{width:1000px;height:1500px;background:#fff;font-family:Inter,Arial,sans-serif;color:#17201C;
display:flex;flex-direction:column;padding:56px 64px 48px}}
.ph{{height:700px;display:flex;align-items:center;justify-content:center;margin-bottom:28px}}.ph img{{max-width:100%;max-height:100%;object-fit:contain}}
.drop{{align-self:flex-start;background:#1F7A4D;color:#fff;font-weight:800;font-size:40px;padding:10px 22px;border-radius:14px}}
.b{{margin-top:26px;font-size:34px;font-weight:700;color:#5c6660;text-transform:uppercase;letter-spacing:.04em}}
.n{{font-family:'Archivo Black',Inter,sans-serif;font-size:62px;line-height:1.05;margin-top:6px;overflow-wrap:anywhere}}
.pr{{display:flex;align-items:baseline;gap:22px;margin-top:26px}}.now{{font-family:'Archivo Black',Inter,sans-serif;font-size:96px;color:#E8621A}}
.cur{{font-size:30px;font-weight:700;color:#5c6660}}.off{{font-size:44px;font-weight:800;background:#FDEBDD;color:#B4470E;padding:4px 16px;border-radius:12px}}
.was{{font-size:32px;color:#5c6660;margin-top:8px}}.st{{font-size:36px;font-weight:700;margin-top:22px}}.sz{{font-size:32px;color:#5c6660;margin-top:6px}}
.ft{{margin-top:auto;display:flex;align-items:center;justify-content:space-between;border-top:3px solid #EEF1EC;padding-top:26px}}
.ft img{{height:92px}}.u{{font-size:36px;font-weight:800}}
</style></head><body>
<div class="ph"><img src="{e(img)}"></div>
<div class="drop">↓ ${p["drop"]:,} this week</div>
<div class="b">{e(p["b"])}{e(g)}</div><div class="n">{e(p["name"][len(p["b"]):].strip())}</div>
<div class="pr"><span class="now">{money(p["now"])}</span><span class="cur">{cur}</span><span class="off">−{p["pct"]}%</span></div>
<div class="was">Regular {money(p["reg"])}</div>
<div class="st">at {e(p["store"])}</div><div class="sz">{p["sizes"]} sizes at this price</div>
<div class="ft"><img src="{logo}"><span class="u">thegearfox.com</span></div>
</body></html>'''


def render(jobs):
    """jobs = [(html, path)]: one browser for all; images and fonts fetched through our own requests (works behind proxies)."""
    if not jobs:
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or os.environ.get("CHROMIUM_PATH") or None)
        pg = b.new_page(viewport={"width": 1000, "height": 1500})

        def through(route):
            try:
                route.fulfill(response=route.fetch())
            except Exception:
                route.abort()
        pg.route("http*://**/*", through)
        for page_html, path in jobs:
            pg.set_content(page_html, wait_until="networkidle", timeout=60000)
            pg.wait_for_timeout(500)
            fits = pg.evaluate("() => document.body.scrollHeight <= 1500 && document.body.scrollWidth <= 1000 && [...document.images].every(i => i.complete && i.naturalWidth > 0)")
            if not fits:
                print(f"  {path.name}: something doesn't fit or a picture didn't load: left out")
                continue
            pg.screenshot(path=str(path), type="jpeg", quality=88)
        b.close()


def item_xml(it):
    e = html.escape
    img = it["img"]
    return (f'<item><title>{e(it["title"])}</title><link>{e(it["link"])}</link>'
            f'<description><![CDATA[{it["desc"].replace("]]>", "")}]]></description>'
            f'<guid isPermaLink="false">{e(it["guid"])}</guid><pubDate>{e(it["date"])}</pubDate>'
            f'<enclosure url="{e(img)}" type="image/jpeg" length="0"/><media:content url="{e(img)}" medium="image" type="image/jpeg"/></item>')


def write_feed(site, side, items):
    title, cur = SIDES[side][2], SIDES[side][3]
    link = f"{SITE}/{'us/shoes' if side == 'us' else 'shoes'}/"
    body = "".join(item_xml(it) for it in items)
    (site / "pins" / f"{side}.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:media="{MEDIA}"><channel><title>{html.escape(title)}</title>'
        f'<link>{link}</link><description>Real price drops on running shoes, checked on the store page every morning ({cur}).</description>'
        f'<language>en</language>{body}</channel></rss>\n')


def main():
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    carry = "--carry" in sys.argv
    prev = os.environ.get("PIN_PREV")
    today = date.today()
    (site / "pins" / "img").mkdir(parents=True, exist_ok=True)
    hist = None
    for side, (sale_f, pages_f, _, cur) in SIDES.items():
        old = [it for it in old_items(side, prev) if age_days(it, today) <= IMG_DAYS]
        keep_images(site, old)
        new = []
        if not carry:
            try:
                sale = json.loads((site / sale_f).read_text())
                pages = json.loads((site / pages_f).read_text())
                if hist is None:
                    hist = SPOST.history()
                state = {}
                for it in old:          # each shoe once per 21 days: the feed itself is the memory
                    m = re.search(r"/shoes/([^/?]+)/", it["link"])
                    if m and age_days(it, today) < SPOST.REPOST_DAYS:
                        state[m.group(1)] = today.isoformat()
                jobs = []
                for p in SPOST.picks(sale, pages, hist, state, today, side=side):
                    if len(new) >= PER_DAY:
                        break
                    if not SPOST.confirmed(p):
                        print(f"  {side}: not confirmed on the store page: {p['name']}")
                        continue
                    name = f"{today.isoformat()}-{side}-{p['slug']}.jpg"
                    g = f' ({p["gender"]})' if p["gender"] else ""
                    link = f'{p["page"]}?ref=pinterest'
                    img = f"{SITE}/pins/img/{name}"
                    title = f'{p["name"]}{g} dropped ${p["drop"]:,}: {money(p["now"])} at {p["store"]}, −{p["pct"]}%'
                    if len(title) > 100:
                        title = f'{p["name"]}{g}: {money(p["now"])} at {p["store"]}, −{p["pct"]}%'[:100]
                    text = (f'{p["name"]}{g} dropped ${p["drop"]:,} this week: {money(p["now"])} {cur} at {p["store"]} '
                            f'(regular {money(p["reg"])}, −{p["pct"]}%), {p["sizes"]} sizes at that price. Every size and store, checked daily.')
                    new.append({"title": title, "link": link, "guid": f"{side}-{p['slug']}-{today.isoformat()}",
                                "date": format_datetime(datetime.now(timezone.utc)), "img": img,
                                "desc": f'<p><img src="{html.escape(img)}" alt="{html.escape(p["name"])}"></p><p>{html.escape(text)}</p>', "_job": (card_html(p, cur), site / "pins" / "img" / name)})
                render([it["_job"] for it in new])
                new = [it for it in new if it.pop("_job")[1].exists()]
            except Exception as e:
                print(f"{side}: no new pins today ({e})")
        items = (new + old)[:KEEP]
        write_feed(site, side, items)
        print(f"{side}: {len(new)} new, {len(items)} in the feed")
    used = {Path(u).name for side in SIDES for u in re.findall(r'<enclosure url="([^"]+)"', (site / "pins" / f"{side}.xml").read_text())}
    for f in (site / "pins" / "img").glob("*.jpg"):
        if f.name not in used:
            f.unlink()


if __name__ == "__main__":
    main()
