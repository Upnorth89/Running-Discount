#!/usr/bin/env python3
"""The weekly Reel video for Bastien (rides in the Wednesday Instagram brief).

Finds this week's real price drops in Bastien's sizes (men's shoe 11, clothing M) from the price history:
one running shoe and, when there is one, a piece of gear or clothing for variety. Puts both in a pretend
watchlist (saved at last week's price), records the site on a phone (the heart blinks, the watchlist opens,
each card says "Dropped $X since you saved it") and cuts a 1080x1920 Reel:
  - dark safe bands: 218 px on top (Instagram's title/camera), 400 px below (name, caption, buttons)
  - opens on the payoff: 2.5 s slow zoom on the first card, then the recording
One video in English, one in French. Honest numbers only: "saved" price = that item's best price a week ago
(any size), so the drop shown is never bigger than the real drop in his size.

Usage: python scraper/ig_reel.py OUT_DIR   (writes reel-en.mp4, reel-fr.mp4, picks.json)
Env:   SALE_URL, HISTORY_FILE (local prices.jsonl; else fetched from the history branch), CHROMIUM_PATH
"""
import asyncio
import base64
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

SALE_URL = os.environ.get("SALE_URL", "https://thegearfox.com/sale.json")
HISTORY_URL = "https://raw.githubusercontent.com/Upnorth89/Running-Discount/history/prices.jsonl"
SITE = "https://thegearfox.com/"
SHOE, LETTER = ("11", "M:11"), ("M", "OS")        # Bastien's sizes: the Reels say "my size"
SKIP = re.compile(r"spike|\b[LM]D(-X)?\b|\bXC\b|cross[- ]?country|\bsprint|boot|kids?|youth|junior", re.I)
TOP, BOTTOM = 218, 400                            # safe bands (px) on the 1080x1920 frame
VW, VH = 360, 434                                 # phone viewport = the space between the bands at 3x


def key(it):
    return f"{it['b']}|{it['n']}|{it['g']}|{1 if it.get('w') else 0}".lower()


def history():
    p = os.environ.get("HISTORY_FILE")
    text = Path(p).read_text() if p and Path(p).exists() else requests.get(HISTORY_URL, timeout=120).text
    out = {}
    for line in text.splitlines():
        try:
            r = json.loads(line)
            out[r["k"]] = r["h"]
        except Exception:
            pass
    return out


def week_ago(h, today):
    """Best price a week ago: the last point on or before that day, else the oldest we have."""
    cut = (today - timedelta(days=7)).isoformat()
    old = [p for p in h if p[0] <= cut]
    return (old[-1] if old else h[0])[1]


def in_my_size(it):
    want = SHOE if it["g"] == "shoes" else LETTER
    s = [e for e in it["sz"] if e[0] in want]
    return min(s, key=lambda e: e[1]) if s else None


def drops(items, hist, today):
    out = []
    for it in items:
        if not it.get("ca") or SKIP.search(it["n"]) or "women" in it["n"].lower():
            continue
        if it["g"] not in ("shoes", "tops", "bottoms", "packs", "gear"):
            continue
        h = hist.get(key(it))
        e = in_my_size(it)
        if not h or len(h) < 2 or not e:
            continue
        then, now = week_ago(h, today), e[1]
        if then < 60 or now > then - 20 or now > then * 0.85:   # a real drop: $20+ and 15%+
            continue
        out.append({"it": it, "then": then, "now": now, "drop": round(then - now, 2), "reg": e[3],
                    "url": (it["of"][e[2]] if e[2] < len(it["of"]) else it["of"][0])})
    return sorted(out, key=lambda d: -d["drop"])


def pick(cands):
    shoes = [d for d in cands if d["it"]["g"] == "shoes" and d["it"].get("t") in ("daily", "race", "trail", None)]
    other = [d for d in cands if d["it"]["g"] != "shoes"]
    chosen = shoes[:1] + other[:1]
    for d in shoes[1:]:                                 # no gear this week: a second shoe from another brand
        if len(chosen) >= 2:
            break
        if all(d["it"]["b"] != c["it"]["b"] for c in chosen):
            chosen.append(d)
    return sorted(chosen, key=lambda d: -d["drop"])     # the biggest drop opens the video


def watchlist(chosen):
    w = {}
    for d in chosen:
        it = d["it"]
        w[key(it)] = {"b": it["b"], "n": it["n"], "g": it["g"], "url": d["url"], "price": d["then"], "low": d["then"],
                      "seen": d["then"], "gone": False, "saved": (date.today() - timedelta(days=7)).isoformat() + "T15:00:00Z"}
    return w


SETUP = """(([w, lang]) => { if (sessionStorage.getItem('fx')) return; sessionStorage.setItem('fx', '1');
  localStorage.setItem('gf-sub', JSON.stringify({key: '00000000-0000-0000-0000-000000000000', email: 'demo@thegearfox.com', active: true}));
  localStorage.setItem('rd-profile', JSON.stringify({gender: 'men', terrain: 'both', ships: 'ca', groups: ['shoes','tops','bottoms','socks','packs','gear'],
    sizes: {shoes: {sizes: ['11'], width: ['Regular']}, tops: {sizes: ['M']}, bottoms: {sizes: ['M']}}, brands: [], lang}));
  localStorage.setItem('gf-watch', JSON.stringify(w)); localStorage.setItem('gf-lang', JSON.stringify(lang));
  addEventListener('DOMContentLoaded', () => { const s = document.createElement('style');
    s.textContent = '.fx-dot{position:fixed;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:rgba(242,106,27,.35);border:3px solid #F26A1B;pointer-events:none;z-index:99999;transition:transform .35s ease,opacity .45s ease}';
    document.head.appendChild(s) }) })"""

SCROLL = """([px, ms]) => new Promise(r => { const t = document.scrollingElement, y0 = t.scrollTop, t0 = performance.now();
  (function st(n) { const k = Math.min(1, (n - t0) / ms), e = k < .5 ? 2*k*k : 1 - Math.pow(-2*k + 2, 2) / 2;
    t.scrollTop = y0 + px * e; k < 1 ? requestAnimationFrame(st) : r() })(t0) })"""

CARD_TOP = """() => { const c = [...document.querySelectorAll('.dw')].filter(e => e.offsetParent)[1];
  return c ? Math.round(c.getBoundingClientRect().top - 80) : 0 }"""


async def record(w, lang, names, work):
    from playwright.async_api import async_playwright
    frames, stamps = work / f"frames-{lang}", []
    frames.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        ctx = await b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=3, is_mobile=True, has_touch=True,
                                  user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
                                             "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")

        async def through(route):
            u = route.request.url
            if "/rpc/" in u or "umami" in u:            # no sign-in calls, no visit counts from the recording
                return await route.abort()
            try:
                await route.fulfill(response=await route.fetch())
            except Exception:
                await route.abort()
        await ctx.route("**/*", through)
        await ctx.add_init_script(f"({SETUP})({json.dumps([w, lang])})")
        pg = await ctx.new_page()
        cdp = await ctx.new_cdp_session(pg)

        async def on_frame(f):
            i = len(stamps)
            stamps.append(f["metadata"]["timestamp"])
            (frames / f"{i:05d}.jpg").write_bytes(base64.b64decode(f["data"]))
            try:
                await cdp.send("Page.screencastFrameAck", {"sessionId": f["sessionId"]})
            except Exception:
                pass
        cdp.on("Page.screencastFrame", lambda f: asyncio.ensure_future(on_frame(f)))
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "everyNthFrame": 1})
        await pg.goto(SITE)
        await pg.wait_for_timeout(13500)                 # the heart blinks with its "2", the watchlist strip
        el = pg.locator("#openWatch")
        bx = await el.bounding_box()
        x, y = bx["x"] + bx["width"] / 2, bx["y"] + bx["height"] / 2
        await pg.evaluate("""([x, y]) => { const d = document.createElement('div'); d.className = 'fx-dot'; d.style.left = x + 'px';
          d.style.top = y + 'px'; document.body.appendChild(d); setTimeout(() => { d.style.transform = 'scale(1.5)'; d.style.opacity = '0' }, 350);
          setTimeout(() => d.remove(), 900) }""", [x, y])
        await pg.wait_for_timeout(250)
        await pg.mouse.click(x, y)
        await pg.wait_for_timeout(1500)
        await pg.evaluate(SCROLL, [175, 1500])           # the first card whole
        await pg.wait_for_timeout(600)
        await pg.screenshot(path=str(work / f"payoff-{lang}.png"))
        await pg.wait_for_timeout(3900)
        if len(names) > 1:                               # the second card
            px = await pg.evaluate(CARD_TOP)
            if px > 0:
                await pg.evaluate(SCROLL, [px, 2400])
            await pg.wait_for_timeout(4500)
        await pg.wait_for_timeout(1500)
        await cdp.send("Page.stopScreencast")
        await b.close()
    lines = []
    for i in range(len(stamps)):
        d = stamps[i + 1] - stamps[i] if i + 1 < len(stamps) else 1.0
        lines += [f"file '{frames / f'{i:05d}.jpg'}'", f"duration {max(d, 0.001):.4f}"]
    lines.append(f"file '{frames / f'{len(stamps) - 1:05d}.jpg'}'")
    (work / f"rec-{lang}.txt").write_text("\n".join(lines))


def cut(lang, work, out):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    h = 1920 - TOP - BOTTOM
    band = f"pad=1080:1920:0:{TOP}:color=0x17201C"
    body = work / f"body-{lang}.mp4"
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(work / f"rec-{lang}.txt"), "-ss", "3",
                    "-vf", f"scale=1080:{h}:flags=lanczos,{band},fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18",
                    "-preset", "slow", str(body)], check=True)
    zoom = (f"[0]scale=1080:{h},scale=2160:{2 * h},zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih*0.4/zoom)':"
            f"d=75:s=1080x{h}:fps=30,trim=end_frame=75,{band},setsar=1,format=yuv420p[a];"
            "[1]fps=30,setsar=1,format=yuv420p[b];[a][b]concat=n=2:v=1[v]")
    subprocess.run([ff, "-y", "-loglevel", "error", "-loop", "1", "-i", str(work / f"payoff-{lang}.png"), "-i", str(body),
                    "-filter_complex", zoom, "-map", "[v]", "-c:v", "libx264", "-crf", "20", "-preset", "slow",
                    "-movflags", "+faststart", str(out)], check=True)


def money(v, lang):
    return f"${v:,.2f}" if lang == "en" else f"{v:,.2f} $".replace(",", " ").replace(".", ",")


def short(it):
    return f"{it['b']} " + re.sub(r"\s+-\s+(Men's|Women's|Unisex)$", "", it["n"])


def store(url):
    h = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*", r"\1", url))
    return {"sportinglife.ca": "Sporting Life", "altitude-sports.com": "Altitude Sports", "thelasthunt.com": "The Last Hunt",
            "mec.ca": "MEC", "lecoureurnordique.ca": "Le Coureur Nordique", "lecoureur.com": "Le Coureur"}.get(h, h.split(".")[0].title())


def script(chosen):
    """Hook, lines to say over the video and the caption, EN and FR, with the real numbers."""
    a = chosen[0]
    b = chosen[1] if len(chosen) > 1 else None
    da, db = round(a["drop"]), round(b["drop"]) if b else 0
    en = {"hook": "Stop paying full price for your running gear",
          "open": f"{short(a['it'])}, down {da} bucks in my size, and I didn't check a single store.",
          "how": "Heart anything on The Gear Fox. When the price drops in your size, the heart lights up and you get an email.",
          "a": f"{short(a['it'])}: {money(a['now'], 'en')}, down ${da}, at {store(a['url'])}.",
          "b": f"And {short(b['it'])}: down ${db}." if b else "",
          "end": "It's free. Link in my bio.",
          "caption": f"{short(a['it'])} dropped ${da} this week and I didn't check a single store 👀 Heart anything on The Gear Fox "
                     "and we watch the price for you, in your size, at 60+ Canadian stores. Free. Link in bio 🦊\n\n"
                     "#runningshoes #runcanada #vancouverrunning #trailrunning #runningdeals"}
    fr = {"hook": "Arrête de payer ton stock de course plein prix",
          "open": f"{short(a['it'])} : {da} $ de rabais dans ma pointure, pis j'ai même pas eu à chercher.",
          "how": "Sur The Gear Fox, tu mets un cœur sur n'importe quel article. Quand le prix baisse dans ta pointure, le cœur s'allume pis tu reçois un courriel.",
          "a": f"{short(a['it'])} : {money(a['now'], 'fr')}, {da} $ de moins, chez {store(a['url'])}.",
          "b": f"Pis {short(b['it'])} : {db} $ de moins." if b else "",
          "end": "C'est gratuit. Lien dans ma bio.",
          "caption": f"{short(a['it'])} : {da} $ de rabais cette semaine pis j'ai même pas eu à chercher 👀 Mets un cœur sur n'importe quel "
                     "article sur The Gear Fox et on surveille le prix pour toi, dans ta pointure, dans plus de 60 boutiques canadiennes. "
                     "Gratuit. Lien dans la bio 🦊\n\n#course #courseapied #coureur #quebecrunning #aubaines"}
    return {"en": en, "fr": fr}


def make(out_dir, items=None):
    """Build both videos. Returns {"picks": [...], "script": {...}, "videos": {lang: path}} or None (no real drops)."""
    out = Path(out_dir)
    work = out / "reel-work"
    work.mkdir(parents=True, exist_ok=True)
    if items is None:
        items = requests.get(SALE_URL, timeout=60).json().get("items", [])
    chosen = pick(drops(items, history(), date.today()))
    if not chosen:
        return None
    w = watchlist(chosen)
    names = [d["it"]["n"] for d in chosen]
    videos = {}
    for lang in ("en", "fr"):
        asyncio.run(record(w, lang, names, work))
        videos[lang] = out / f"reel-{lang}.mp4"
        cut(lang, work, videos[lang])
    picks = [{"name": short(d["it"]), "then": d["then"], "now": d["now"], "drop": d["drop"], "store": store(d["url"]), "url": d["url"]}
             for d in chosen]
    (out / "picks.json").write_text(json.dumps(picks, indent=1, ensure_ascii=False))
    return {"picks": picks, "script": script(chosen), "videos": videos}


if __name__ == "__main__":
    r = make(sys.argv[1] if len(sys.argv) > 1 else "email")
    print(json.dumps(r and {"picks": r["picks"], "videos": {k: str(v) for k, v in r["videos"].items()}}, indent=1, ensure_ascii=False))
