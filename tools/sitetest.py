#!/usr/bin/env python3
"""Site test: uses the site like a real visitor, every morning and afternoon, before it's published (Oct 5, 2026).

Bastien: "these little glitches are being caught by users and not our own health check". So a robot phone opens the
freshly built site (today's data, served from this machine), and:
  - first visit: welcome screen, sizes (men's 11, clothing M), deals appear, sign-up card + "No thanks"
  - "Ships from Canada" on: no card from a store abroad (Nutrition too); "Show US stores too" adds them
  - every category chip shows only that category (and has deals), "Show more" and the shoe type buttons work
  - one search per category (a brand that category shows today): every result matches, and stays in the category
  - "Wrong price or size?" on a card opens three reasons and thanks the visitor
  - a typo ("saucny") offers "Did you mean saucony?" and the tap finds deals
  - an accent-free search finds accented brands ("naak" = Näak), a nonsense search shows the "nothing matches" note
  - filters (Include full price, Sort by price), a heart opens the email step, the ☰ menu, the French version
  - shoe pages (a model page with its price table, the list pages EN/FR, Black Friday), About, privacy
  - every link on those pages that points inside the site opens (no "page not found")
  - store links: two deals per store are opened; "page not found" on both = broken (blocked/busy = couldn't check)
Nothing is sent anywhere: sign-up, analytics and Google calls are answered by a stand-in.

  python tools/sitetest.py SITE_DIR [OUT.json]     (needs: pip install playwright; python -m playwright install chromium)

Writes OUT.json (default /tmp/sitetest.json) for scraper/health.py: each check with ok/critical/why. Critical = the
site would be useless today (no deals after the sizes step, the page crashes, shoe pages empty): refresh.yml then keeps
yesterday's site up. Screenshots of failures go next to OUT.json (sitetest-*.png).
"""
import functools
import os
import http.server
import json
import random
import re
import socketserver
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visual_check import collisions, NO_KEEPALIVE   # noqa: E402  (Oct 28: letters touching things)
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

LIVE = sys.argv[1].startswith("http")            # Oct 8: the noon check tests thegearfox.com itself (nothing is built)
SITE = None if LIVE else Path(sys.argv[1]).resolve()
_cache = {}
INSECURE = os.environ.get("SITETEST_INSECURE") == "1"   # only for a machine whose network proxy re-signs HTTPS (Claude's sandbox)


def site_get(rel):
    """A file of the site under test: from the folder, or (live) from the web. None when it isn't there."""
    rel = rel.lstrip("/")
    if not LIVE:
        f = SITE / rel
        if f.is_dir():
            f = f / "index.html"
        return f.read_text(errors="ignore") if f.exists() else None
    if rel not in _cache:
        try:
            r = requests.get(sys.argv[1].rstrip("/") + "/" + rel, timeout=60, headers={"Cache-Control": "no-cache"})
            _cache[rel] = r.text if r.status_code == 200 else None
        except Exception:
            _cache[rel] = None
    return _cache[rel]


def site_json(rel):
    return json.loads(site_get(rel) or "null")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/sitetest.json")
ORDER = ["shoes", "tops", "bottoms", "bras", "socks", "gloves", "headwear", "packs", "gear", "watches", "nutrition"]
NAMES = {"shoes": "Shoes", "tops": "Tops & jackets", "bottoms": "Shorts & tights", "bras": "Sports bras", "socks": "Socks",
         "gloves": "Gloves", "headwear": "Hats", "packs": "Packs & vests", "gear": "Gear", "watches": "Watches",
         "nutrition": "Nutrition"}
results = []
shots = OUT.parent


def sec(ids):
    return ", ".join(NAMES.get(i.removeprefix("grp-"), i.removeprefix("grp-")) for i in sorted(ids))


def fold(s):
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


def check(name, critical=False):
    """check(name)(fn, page): runs fn, records ok / why. fn returns a short note, or raises AssertionError(why)."""
    def run(fn, page=None):
        # SITETEST_ONLY="word|word" (Oct 28): run only the checks whose name has one of the words (+ the critical ones the rest needs)
        only = os.environ.get("SITETEST_ONLY")
        if only and not critical and not any(w.lower() in name.lower() for w in only.split("|")):
            return True
        t = time.time()
        try:
            note = fn()
            results.append({"name": name, "ok": True, "critical": critical, "note": note or ""})
            print(f"  ok   {name}" + (f" ({note})" if note else "") + f"  [{time.time() - t:.1f}s]")
            return True
        except Exception as e:
            why = str(e).strip().splitlines()[0][:400] if str(e).strip() else type(e).__name__
            results.append({"name": name, "ok": False, "critical": critical, "why": why})
            print(f"  FAIL {name}: {why}")
            if page is not None:
                try:
                    page.screenshot(path=str(shots / f"sitetest-{re.sub(r'[^a-z0-9]+', '-', name.lower())}.png"))
                except Exception:
                    pass
                try:                                       # close whatever was left open, so one glitch isn't reported twice
                    page.evaluate("""() => { const m = document.getElementById('menu'); if (m && !m.hidden) document.getElementById('menuBtn').click();
                        const c = document.getElementById('closeSheet'); if (c && c.offsetParent) c.click(); }""")
                    page.wait_for_timeout(300)
                except Exception:
                    pass
            return False
    return run


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=str(SITE))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), h)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/"


def stub(ctx):
    # sign-up/analytics functions answer "null" (nothing reaches Supabase); trackers and Google stay out; photos skipped (speed)
    ctx.add_init_script(NO_KEEPALIVE)      # a keepalive send skips the routes below and reached the real database (Oct 28)
    ctx.route("**/rest/v1/rpc/**", lambda r: r.fulfill(status=200, content_type="application/json", body="null"))
    ctx.route(re.compile(r"umami|googletagmanager|accounts\.google|gstatic"), lambda r: r.abort())
    ctx.route(re.compile(r"^https?://(?!127\.0\.0\.1).*\.(jpe?g|png|webp|gif|avif)(\?.*)?$", re.I), lambda r: r.abort())
    # A/B tests (Oct 18): the robot is group A unless a check asks otherwise (test "welcome" B skips the welcome screen)
    ctx.add_init_script("try{if(!localStorage.getItem('gf-exp'))localStorage.setItem('gf-exp',JSON.stringify({welcome:'A',layout:'A',short:'A',namecard:'A',watchsheet:'A'}))}catch(e){}")


# ---------- what today's data says we should see ----------
def expected():
    sale = site_json("sale.json")["items"]
    per = Counter(d["g"] for d in sale)
    plain = lambda b: re.sub("[\u0300-\u036f]", "", unicodedata.normalize("NFD", b)).lower()   # same as the site's fold()
    accented = Counter(d["b"] for d in sale if plain(d["b"]) != d["b"].lower() and plain(d["b"]).isascii())
    return per, [b for b, _ in accented.most_common(5)]


def cards(page):
    """Visible deal cards in the deal list (not the watchlist strip or new-deals row): brand, name, section id, price."""
    return page.evaluate("""() => [...document.querySelectorAll('section.grp .deal')].map(a => {
        const s = a.closest('section.grp');
        return {b: ((a.querySelector('.brand')||{}).textContent||'').replace('🍁','').trim(), n: (a.querySelector('.name')||{}).textContent||'',
                sec: s ? s.id : '', price: (a.querySelector('.price b')||{}).textContent||'', href: a.getAttribute('href')||''};
    })""")


def settle(page, ms=350):
    page.wait_for_timeout(ms)


def site_flow(base, per, accented):
    errors = []
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)   # CHROMIUM: a local browser, if any
        ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA",
                             user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
                                        "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1 GearFoxSiteTest")
        stub(ctx)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_default_timeout(15000)

        def welcome():
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("#wDeals .wdeal", state="visible", timeout=30000)
            n = page.locator("#wDeals .wdeal").count()
            assert n >= 2, f"the welcome screen shows {n} sample deals (should be 3)"
            assert page.locator("#saveSizes").is_visible(), "the welcome button is missing"
            return f"{n} sample deals"
        if not check("Welcome screen opens", critical=True)(welcome, page):
            br.close()
            return errors

        def sizes():
            page.click("#saveSizes")                       # "Find my deals" -> sizes step
            page.wait_for_selector("#shoeSizes button", state="visible")
            page.click('#fit button[data-v="men"]')
            page.locator("#shoeSizes button", has_text=re.compile(r"^11$")).first.click()
            if page.locator("#moreSizes").is_visible():      # first visit: the short sizes step hides clothing behind a link
                page.click("#moreSizes")
            page.locator("#clothSizes button", has_text=re.compile(r"^M$")).first.click()
            page.click("#saveSizes")
            page.wait_for_selector("#sheet", state="hidden")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            n = len(cards(page))
            assert n >= 20, f"only {n} deals showed after picking men's 11 / M"
            bad = [c for c in cards(page) if not re.search(r"\d", c["price"])]
            assert not bad, f"{len(bad)} cards without a price (e.g. {bad[0]['b']} {bad[0]['n']})"
            return f"{n} deals on the page"
        if not check("Sizes step shows deals (men's 11, M)", critical=True)(sizes, page):
            br.close()
            return errors

        def signup_card():
            assert page.locator(".signup").count(), "the 'Free with your email' card isn't on the page"
            page.click("#suNo")
            settle(page)
            assert not page.locator(".signup").count(), "'No thanks' didn't hide the sign-up card"
            assert len(cards(page)) >= 20, "deals disappeared after 'No thanks'"
        check("Sign-up card + No thanks")(signup_card, page)

        def email_rules():           # Oct 6: "mailto:name@gmail.com" was accepted, Resend refused it, the person got nothing
            got = page.evaluate("""() => [['mailto:Name@Gmail.com',1],['runner.name+test5@gmail.com',1],['jo@sub.domain.co.uk',1],
                ['a:b@gmail.com',0],['a..b@gmail.com',0],['name@gmail',0],['name @gmail.com',1]]
                .filter(([v,ok]) => gfMail.okMail(gfMail.cleanMail(v)) !== !!ok).map(([v]) => v)""")
            assert not got, f"the sign-up form judges these emails wrong: {got}"
        check("Sign-up email check")(email_rules, page)

        def low_badge_rule():        # Oct 6: "Lowest price in N days" only for a real drop, with 30+ days of history, never > 60
            got = page.evaluate("""() => [
                [{hd:41,lo:100,hi:130,best:100,pct:30},41], [{hd:90,lo:100,hi:130,best:100,pct:30},60],
                [{hd:20,lo:100,hi:130,best:100,pct:30},0],  [{hd:41,lo:100,hi:101,best:100,pct:30},0],
                [{hd:41,lo:95,hi:130,best:100,pct:30},0],   [{hd:41,lo:100,hi:130,best:100,pct:0},0],
                [{pct:30,best:100},0]].filter(([d,want]) => gfLow(d) !== want).map(([d]) => JSON.stringify(d))""")
            assert not got, f"the lowest-price badge rule is wrong for: {got}"
            shown = page.locator(".badge.lo30").count()
            return f"rule ok; {shown} badges on the page today"
        check("Lowest-price badge rule")(low_badge_rule, page)

        def chip(v):     # Oct 22: the redesign hides the chip row (circles + the Filters panel instead); the chips still drive the
            # categories, so the checks press them directly
            page.evaluate("v => document.querySelector(`#cats .chip[data-v=\"${v}\"]`).click()", v)
            settle(page)

        def all_gear():
            chip("__all")
            page.fill("#dSearch", "")
            settle(page)

        # every category on its own
        brands = {}
        for g in ORDER:
            if not page.locator(f'#cats .chip[data-v="{g}"]').count():
                continue                                  # not offered for this runner (sports bras for men): tested below

            def one(g=g):
                all_gear()
                chip(g)
                cs = cards(page)
                other = sorted({c["sec"] for c in cs} - {f"grp-{g}"})
                assert not other, f"tapping {NAMES[g]} also shows {sec(other)}"
                if per.get(g, 0) >= 30:
                    assert cs, f"tapping {NAMES[g]} shows no deals (today's data has {per[g]} on sale)"
                if g in ("tops", "bottoms"):                  # Oct 6: a men's runner saw skirts, bras and high-rise leggings
                    wom = [c for c in cs if re.search(r"women|\bskirts?\b|\bskorts?\b|\bbras?\b|\bdress\b|hi(gh)?[- ]rise",
                                                      c["n"], re.I)]
                    assert not wom, f"{NAMES[g]} for a men's runner shows women's items (e.g. {wom[0]['b']} {wom[0]['n']})"
                messy = [c for c in cs if re.search(r"^\s*[®™·]|\*\s*(final\s*)?sale\s*\*|^\([MWU]\)\s", c["n"], re.I)]
                assert not messy, f"messy product names in {NAMES[g]} (e.g. '{messy[0]['n']}')"   # Oct 6: "® T/r Trail Racing Shoe"
                common = Counter(c["b"].replace(" ★", "").strip() for c in cs).most_common(1)
                if common:
                    brands[g] = (common[0][0], cs)
                more = page.locator(f"#grp-{g} button.more")
                if more.count():
                    n0 = len(cs)
                    more.first.click()
                    settle(page)
                    assert len(cards(page)) > n0, f"'Show more' in {NAMES[g]} didn't add deals"
                return f"{len(cs)} deals"
            check(f"Category {NAMES[g]}")(one, page)

        def shoe_types():
            all_gear()
            chip("shoes")
            seen = []
            for ty in ["daily", "trail", "race"]:
                page.click(f'#grp-shoes .chip[data-type="shoes:{ty}"]')
                settle(page)
                n = len(cards(page))
                assert n, f"the shoe type button '{ty}' shows no shoes"
                seen.append(f"{ty} {n}")
            page.click('#grp-shoes .chip[data-type="shoes:"]')
            return ", ".join(seen)
        check("Shoe type buttons (road, trail, race)")(shoe_types, page)

        # one search per category: a brand that category shows today, with the chip on
        for g in ORDER:
            if g not in brands:
                continue
            brand, before = brands[g]

            def srch(g=g, brand=brand, before=before):
                all_gear()
                chip(g)
                q = brand if len(brand) > 2 else brand + " " + before[0]["n"].split()[0]
                page.fill("#dSearch", q)
                settle(page, 900)                         # search may load the full-price list first
                cs = cards(page)
                assert cs, f"searching '{q}' in {NAMES[g]} found nothing, but {NAMES[g]} shows {brand} deals"
                words = fold(q).split()
                miss = [c for c in cs if not all(w in fold(c["b"] + " " + c["n"]) for w in words)]
                assert not miss, f"searching '{q}' in {NAMES[g]} shows unrelated items ({miss[0]['b']} {miss[0]['n']})"
                other = sorted({c["sec"] for c in cs} - {f"grp-{g}"})
                assert not other, f"searching '{q}' with {NAMES[g]} picked also shows {sec(other)}"
                return f"'{q}': {len(cs)} results"
            check(f"Search in {NAMES[g]}")(srch, page)

        def model_search():
            all_gear()
            chip("shoes")
            c = brands.get("shoes", (None, []))[1]
            assert c, "no shoes to search"
            q = f"{c[0]['b']} {c[0]['n'].split()[0]}".replace(" ★", "")
            page.fill("#dSearch", q)
            settle(page, 900)
            cs = cards(page)
            assert cs, f"searching the shoe on top of the list ('{q}') finds nothing"
            return f"'{q}': {len(cs)}"
        check("Search a shoe model")(model_search, page)

        def search_help():   # Oct 8: a typo gets "Did you mean", a store name offers its deals
            all_gear()
            page.fill("#dSearch", "saucny")
            settle(page, 1200)
            h = page.locator(".searchhelp")
            assert h.count() and "saucony" in h.inner_text().lower(), "the typo 'saucny' doesn't offer 'Did you mean saucony?'"
            page.click(".searchhelp [data-sq]")
            settle(page, 1200)
            n = len(cards(page))
            assert n, "tapping 'saucony' finds nothing"
            page.fill("#dSearch", "")
            settle(page)
            return f"'saucny' -> saucony: {n} deals"
        check("Search: did you mean")(search_help, page)

        def search_closest():   # Oct 26 (Bastien OK'd): a search whose words don't all match offers the closest models, never a dead end
            all_gear()
            page.fill("#dSearch", "saucony zzqxv")
            settle(page, 1200)
            h = page.locator(".searchhelp")
            assert h.count() and h.locator("[data-sq]").count(), "'saucony zzqxv' leaves a dead end (no closest matches)"
            first = h.locator("[data-sq]").first.inner_text()
            assert "saucony" in first.lower(), f"closest match for 'saucony zzqxv' isn't a Saucony: {first!r}"
            h.locator("[data-sq]").first.click()
            settle(page, 1200)
            n = len(cards(page))
            page.fill("#dSearch", "")
            settle(page)
            assert n, f"tapping '{first}' finds nothing"
            return f"'saucony zzqxv' -> {first}: {n} deals"
        check("Search: closest matches, never a dead end")(search_closest, page)

        def report_link():   # Oct 8: "Wrong price or size?" on a card -> three reasons -> thanks
            all_gear()
            page.locator("#dealList .dw .rep").first.click()
            page.wait_for_selector("#dealList .repbox [data-repwhy]", timeout=3000)
            page.locator("#dealList .repbox [data-repwhy='price']").first.click()
            settle(page, 300)
            txt = page.locator("#dealList .repbox").first.inner_text()
            assert "Thanks" in txt, f"after picking a reason the box says '{txt[:60]}'"
            return "report sent, thanks shown"
        check("Wrong price or size? link")(report_link, page)

        def accents():
            # an accented brand as written finds N deals; typed without the accent must find the same N
            for brand in accented:
                all_gear()
                page.fill("#dSearch", brand)
                settle(page, 900)
                n = len(cards(page))
                if not n:
                    continue
                q = fold(brand)
                page.fill("#dSearch", q)
                settle(page, 900)
                m = len(cards(page))
                assert m == n, f"searching '{q}' finds {m} deals, '{brand}' finds {n}"
                page.fill("#dSearch", "")
                return f"'{q}' = '{brand}': {n}"
            return "no accented brand in these sizes today"
        check("Search without accents")(accents, page)

        def punctuation():   # Oct 10 (stats: "arcteryx" and "goretex" found nothing): punctuation and spaces don't matter
            out = []
            for written, typed in (("arc'teryx", "arcteryx"), ("gore-tex", "goretex"), ("zoom fly", "zoomfly")):   # Oct 29: "nike zoomfly" found nothing
                all_gear()
                page.fill("#dSearch", written)
                settle(page, 900)
                n = len(cards(page))
                if not n:
                    continue
                page.fill("#dSearch", typed)
                settle(page, 900)
                m = len(cards(page))
                # "zoom fly" as two words also finds names where they sit apart ("Zoom … Flyknit"): "zoomfly" only has to find the Zoom Flys
                assert (m > 0) if typed == "zoomfly" else (m >= n), f"searching '{typed}' finds {m} deals, '{written}' finds {n}"
                out.append(f"'{typed}' {m} (>= '{written}' {n})")
            page.fill("#dSearch", "")
            settle(page)
            return "; ".join(out) or "neither in these sizes today"
        check("Search without punctuation")(punctuation, page)

        def plural():   # Oct 24 (searches that found nothing: "saucony endorphins speed", "glycerine"): a trailing s or e is forgiven
            out = []
            # Oct 27: filler words ("running vest for women" found nothing because of "for")
            for written, typed in (("endorphin speed", "endorphins speed"), ("glycerin", "glycerine"), ("running shorts men", "running shorts for men")):
                all_gear()
                page.fill("#dSearch", written)
                settle(page, 900)
                n = len(cards(page))
                if not n:
                    continue
                page.fill("#dSearch", typed)
                settle(page, 900)
                m = len(cards(page))
                assert m >= n, f"searching '{typed}' finds {m} deals, '{written}' finds {n}"
                out.append(f"'{typed}' {m} (>= '{written}' {n})")
            page.fill("#dSearch", "")
            settle(page)
            return "; ".join(out) or "neither in these sizes today"
        check("Search forgives a plural, an extra e or a filler word")(plural, page)

        def nonsense():
            all_gear()
            page.fill("#dSearch", "zzqxw")
            settle(page, 600)
            assert not cards(page), "a nonsense search still shows deals"
            txt = page.inner_text("main")
            assert "Nothing matches" in txt or "don't have “zzqxw” yet" in txt, "a search with no results says nothing"   # Oct 18: "We don't have X yet" once the full list is in
            page.fill("#dSearch", "")
            settle(page)
            assert cards(page), "deals didn't come back after clearing the search"
        check("Search with no results")(nonsense, page)

        def filters():
            all_gear()
            chip("shoes")
            n0 = int(page.inner_text("#grp-shoes h2 small").replace(",", "").replace(" ", "").replace(" ", "") or 0)
            def open_f():   # Oct 22: the redesign keeps these in its Filters panel (header button on phones)
                if page.locator('#toggles .chip[data-t="sale"]').is_visible():
                    return
                for b in ("#hFilt", "#rdQF", "#rdBarF", "#filtBtn"):
                    if page.locator(b).is_visible():
                        page.click(b)
                        break
                page.wait_for_selector('#toggles .chip[data-t="sale"]', state="visible", timeout=5000)
            def close_f():
                if page.locator("#rdFs:not([hidden])").count():
                    page.click("#rdFsGo")
                    settle(page)
            open_f()
            page.click('#toggles .chip[data-t="sale"]')
            page.wait_for_timeout(2500)                   # loads the full-price list
            n1 = int(page.inner_text("#grp-shoes h2 small").replace(",", "").replace(" ", "").replace(" ", "") or 0)
            assert n1 > n0, f"'Include full price' didn't add shoes ({n0} -> {n1})"
            open_f()
            page.click('#toggles .chip[data-t="sale"]')
            settle(page)
            open_f()
            page.select_option("#sort", "price")
            settle(page)
            close_f()
            ps = [float(re.sub(r"[^\d.]", "", c["price"].replace(",", ".") if "," in c["price"] and "." not in c["price"] else c["price"].replace(",", "")) or 0)
                  for c in cards(page)[:12]]
            assert ps == sorted(ps), f"'Lowest price' isn't in price order ({ps[:6]})"
            open_f()
            page.select_option("#sort", "match")
            settle(page)
            close_f()
            return f"full price {n0} -> {n1} shoes"
        check("Filters (full price, sort)")(filters, page)

        def heart():
            all_gear()
            page.locator("section.grp .heart").first.click()
            page.wait_for_selector("#sheet", state="visible")
            assert page.locator("#gateEmail").is_visible(), "a heart didn't ask for the email"
            assert not page.locator("#toast").is_visible(), "a message sits on top of the email sheet"   # Oct 18 spy-shopper pass
            page.click("#closeSheet")
            page.wait_for_selector("#sheet", state="hidden")
        check("Heart asks for the email")(heart, page)

        def menu():
            page.click("#menuBtn")
            page.wait_for_selector("#menu", state="visible")
            gos = page.eval_on_selector_all("#menu [data-go]:not([hidden])", "e => e.map(x => x.dataset.go)")
            for need in ["deals", "shoes", "races", "sizes", "about"]:
                assert need in gos, f"the menu has no '{need}' item"
            page.click('#menu [data-go="sizes"]')
            page.wait_for_selector("#sheet", state="visible")
            assert page.locator("#shoeSizes button").first.is_visible(), "Menu > My sizes didn't open the sizes"
            page.click("#closeSheet")
            page.wait_for_selector("#sheet", state="hidden")
            return ", ".join(gos)
        check("Menu")(menu, page)

        def french():
            page.click("#menuBtn")
            langs = page.eval_on_selector_all("#langPick [data-lang]", "e => e.map(x => x.dataset.lang + (x.getAttribute('aria-pressed') === 'true' ? '*' : ''))")
            assert langs == ["en*", "fr"], f"the menu's language list is {langs} (want English picked, Français to pick)"   # Oct 23: a choice, not a toggle
            page.click('#langPick [data-lang="fr"]')
            settle(page, 600)
            assert page.evaluate("document.documentElement.lang") == "fr", "the page didn't switch to French"
            t = page.inner_text("#pageTitle")
            assert t and "On sale" not in t, f"the headline stayed in English ({t})"
            assert len(cards(page)) >= 20, "deals disappeared in French"
            page.fill("#dSearch", "chaussette")    # French words aren't in names: it's fine to find none, but nothing may break
            settle(page, 600)
            page.fill("#dSearch", "")
            if page.locator("#menu").is_visible():
                page.click("#menuBtn")
            page.click("#menuBtn")
            page.click('#langPick [data-lang="fr"]')   # picking the language already on stays put
            settle(page, 300)
            assert page.evaluate("document.documentElement.lang") == "fr", "picking Français again switched the language"
            if not page.locator("#menu").is_visible():
                page.click("#menuBtn")
            page.click('#langPick [data-lang="en"]')
            settle(page, 600)
            return t
        check("French version")(french, page)

        def comeback():
            # tap a deal (the store opens in another tab; here the click is kept on the page), come back: the bar offers
            # that store's other deals; Show = only that store; "× All stores" = everything again
            all_gear()
            n0 = len(cards(page))
            tap = """() => { const a = [...document.querySelectorAll('section.grp a.deal')]
                .find(a => /altitude|lasthunt|sportinglife|thefeed|bushtukah/.test(a.dataset.store)) || document.querySelector('section.grp a.deal');
                a.addEventListener('click', e => e.preventDefault(), {once: true}); a.click(); return a.parentNode.querySelector('.heart').dataset.key; }"""
            page.evaluate(tap)
            # Oct 22: the "Didn't buy it?" card is gone (382 shown, 0 sign-ups): the first return offers that store's other deals
            page.wait_for_selector("#backBar", timeout=6000)
            assert not page.locator("#backBar.bwbar,#backBar.subar").count(), "a removed bar ('Didn't buy it?' / sign-up) came back"
            bar = page.inner_text("#backBar")
            page.evaluate("scrollTo(0, document.body.scrollHeight * 0.6)")   # Oct 25: from far down the page, Show must bring the store's
            settle(page, 300)                                                     # deals into view (they opened out of sight)
            page.click("#backBar .go")
            page.wait_for_selector(".storebar")
            settle(page, 1200)
            top = page.evaluate("document.querySelector('.storebar').getBoundingClientRect().top")
            assert 0 <= top < page.evaluate("innerHeight"), f"Show opened the store's deals out of sight (box at {round(top)} px)"
            name = page.inner_text(".storebar b").strip()
            cs = cards(page)
            assert cs, f"the come-back bar opened {name} with no deals"
            stores = page.eval_on_selector_all("section.grp .deal .store", "e => e.map(x => x.textContent)")
            other = [x for x in stores if name not in x]
            assert not other, f"{name}'s page also shows another store's deal ({other[0].strip()})"
            page.click(".storebar button")
            settle(page, 300)
            # the iPhone back button can bring back a reloaded page: the bar must still remember the store
            page.evaluate("sessionStorage.removeItem('gf-offered')")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("#backBar", timeout=8000)
            page.click("#backBar .x")
            settle(page, 600)
            assert not page.locator(".storebar").count() and len(cards(page)) >= min(n0, 20), "'× All stores' didn't bring every deal back"
            return f"{name}: {len(cs)} deals ({' '.join(bar.split()[:6])}…)"
        check("Come-back bar after a deal click")(comeback, page)

        def watch_label():   # Oct 11: cards say "Watch price" (the small heart alone was used by 5 people in 3 weeks)
            labels = page.eval_on_selector_all("section.grp .heart .hl", "e => e.map(x => x.textContent)")
            ok = ("Watch price", "Watching") + (("Watch",) if page.evaluate("document.documentElement.classList.contains('cards2')") else ())   # test cards2 B: "Watch" (Bastien OK'd, Oct 25)
            assert labels and all(x in ok for x in labels), f"cards' watch buttons say {set(labels)}"
            return f"{len(labels)} cards"
        check("Cards have a 'Watch price' button")(watch_label, page)

        def drops_gone():   # test 'drops' ended Oct 20 (A won): nobody gets the "Dropped today in your size" row, even an old group B
            page.goto(base + "?exp=drops:B", wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            n = page.locator(".grp.drops").count()
            page.evaluate("() => localStorage.removeItem('gf-exp')")
            assert n == 0, "the 'Dropped today' row still shows"
            return "no 'Dropped today' row"
        check("Test 'drops' ended: no 'Dropped today' row")(drops_gone, page)

        def r100_test():   # Oct 18, A/B test 'r100' (Rule of 100): group B's badge is "−$X" when the regular price is $100+, "−N%" below
            def at(group):
                page.goto(base + f"?exp=r100:{group}", wait_until="domcontentloaded")
                page.wait_for_selector("section.grp .deal", timeout=20000)
                return page.eval_on_selector_all("section.grp .deal", """e => e.filter(x => x.querySelector('.pct') && x.querySelector('.price s'))
                    .map(x => [x.querySelector('.pct').textContent, parseFloat(x.querySelector('.price s').textContent.replace(/[^0-9.,]/g, '').replace(',', '.'))])""")
            b, a = at("B"), at("A")
            page.evaluate("() => localStorage.removeItem('gf-exp')")
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            assert a and all(t.endswith("%") for t, _ in a), "group A shows a dollar badge"
            bad = [f"{t} on ${r}" for t, r in b if ("$" in t) != (r >= 100)]
            assert b and not bad, f"group B: {bad[:3]}"
            n = sum("$" in t for t, _ in b)
            return f"group B: {n} dollar badges ($100+), {len(b) - n} percent; group A: all percent"
        check("Test 'r100': dollars off at $100+ for group B")(r100_test, page)

        def layout_test():   # test 'layout' (Oct 18; for everyone Oct 19; 50/50 again Oct 20): B = the swipe row under search + categories
            page.goto(base + "?exp=layout:A", wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            ya = page.evaluate("() => {const r = document.querySelector('#newBox section.grp'), f = document.querySelector('#filtersBox'); return r && f ? r.getBoundingClientRect().top < f.getBoundingClientRect().top : null}")
            assert ya in (True, None), "group A: the swipe row isn't above the categories"
            page.goto(base + "?exp=layout:B", wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            r = page.evaluate("""() => {const y = s => {const e = document.querySelector(s); return e ? e.getBoundingClientRect().top : null};
                return {search: y('#dSearch'), row: y('#newBox section.grp'), tiles: document.querySelectorAll('#newBox .tw').length,
                        cards: document.querySelectorAll('#newBox .dw:not(.tw)').length}}""")
            page.evaluate("() => localStorage.removeItem('gf-exp')")
            if r["row"] is None:
                return "no swipe row today (nothing dropped / new in men's 11 / M)"
            assert r["tiles"] and not r["cards"], f"row: {r['tiles']} tiles, {r['cards']} full cards"
            assert r["search"] < r["row"], "search is not above the row"
            more = ""
            if r["tiles"] >= 24:      # Oct 19: swiping to the end of the row loads the next tiles (no "See all" button)
                n2 = page.evaluate("""async () => {const g = document.querySelector('#newBox .grp.new .grid');
                    g.scrollLeft = g.scrollWidth; await new Promise(r => setTimeout(r, 600)); return g.querySelectorAll('.tw').length}""")
                assert n2 > r["tiles"], f"swiping to the end of the row didn't load more tiles ({n2})"
                more = f"; swiping to the end loads more ({r['tiles']} -> {n2})"
            return f"search on top, {r['tiles']} tiles in the row{more}"
        check("Test 'layout': B = swipe row under the categories, small tiles that keep loading")(layout_test, page)

        # Oct 23: the "Top drop" link was removed (Bastien), its check with it

        def top_overlap():   # Oct 19 (Bastien: "I shouldn't have to ask will the filter button cover the other buttons"): at 320/390/768/1280px
            out = []       # nothing in the header and the lines above the deals sits on top of something else, nothing wider than the screen
            try:
                for w in (320, 390, 768, 900, 1280):
                    page.set_viewport_size({"width": w, "height": 800})
                    settle(page, 400)
                    r = page.evaluate("""() => {const box = e => e.getBoundingClientRect();
                        const els = [...document.querySelectorAll('.topbar a,.topbar button,.topbar input,#subhead,#hook a,#filtBtn,#pageTitle,#cats')].filter(e => e.offsetParent);
                        const ov = [];
                        for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
                            const a = box(els[i]), b = box(els[j]);
                            if (a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1 && !els[i].contains(els[j]) && !els[j].contains(els[i])
                                && !([els[i].id, els[j].id].includes('hFilt') && [els[i].id, els[j].id].includes('dSearch')))   // the Filters button sits inside the search box on purpose
                                ov.push((els[i].id || els[i].className) + ' / ' + (els[j].id || els[j].className))}
                        return {ov, wide: document.documentElement.scrollWidth}}""")
                    assert not r["ov"], f"{w}px: {', '.join(r['ov'][:3])} overlap"
                    assert r["wide"] <= w + 1, f"{w}px: the page is {r['wide'] - w}px too wide"
                    hit = page.evaluate("""() => [...document.querySelectorAll('.dw')].filter(d => {const a = d.querySelector('.rep'), h = d.querySelector('.heart');
                        if (!a || !h || !a.offsetParent) return false; const ra = a.getBoundingClientRect(), rh = h.getBoundingClientRect();
                        return ra.left < rh.right + 2 && rh.left < ra.right + 2 && ra.bottom > rh.top && ra.top < rh.bottom}).length""")   # Oct 20: "Wrong price or size?" ran into "Watch price"
                    assert not hit, f"{w}px: on {hit} cards 'Wrong price or size?' runs into 'Watch price'"
                    out.append(f"{w}px ok")
            finally:
                page.set_viewport_size({"width": 390, "height": 844})
                settle(page, 300)
            return ", ".join(out)
        check("Top of the page and cards: nothing overlaps (phone to computer)")(top_overlap, page)

        def laptop_top():   # Oct 23 (Bastien: the hero "cuts off the categories"; "when you click more filters on a laptop, you don't see what it changes")
            try:
                page.set_viewport_size({"width": 1366, "height": 650})   # a 1366x768 laptop minus the browser bars
                page.evaluate("scrollTo(0,0)")
                settle(page, 500)
                r = page.evaluate("""() => {const t = document.getElementById('rdTiles'), f = document.getElementById('filtersBox'), b = document.getElementById('filtBtn');
                    return {tiles: t && t.offsetParent ? Math.round(t.getBoundingClientRect().bottom) : null, btn: !!(b && b.offsetParent), open: !!(f && f.classList.contains('open'))}}""")
                if r["tiles"] is not None:
                    assert r["tiles"] <= 650, f"the category circles end at {r['tiles']}px, below a laptop screen (650px tall in the browser)"
                gap = page.evaluate("""() => {const h = document.querySelector('.rdhero h1'), f = document.getElementById('rdSearch');
                    return h && f && h.offsetParent && f.offsetParent ? Math.round(f.getBoundingClientRect().top - h.getBoundingClientRect().bottom) : null}""")
                if gap is not None:   # Oct 28 (Bastien: "the Y bleeds into the search bar"): the headline's y/g hung into the search box
                    assert gap >= 10, f"the headline sits {gap}px above the search box (its y touches the box)"
                if r["btn"] and not r["open"]:
                    page.click("#filtBtn")
                    settle(page, 900)
                    top = page.evaluate("Math.round(document.getElementById('filtersBox').getBoundingClientRect().top)")
                    page.click("#filtBtn")   # close it again
                    assert 0 <= top <= 650 - 160, f"after More filters the filter row is at {top}px, off a laptop screen"
                return f"circles end at {r['tiles']}px; More filters shows its row" if r["btn"] else f"circles end at {r['tiles']}px"
            finally:
                page.set_viewport_size({"width": 390, "height": 844})
                page.evaluate("scrollTo(0,0)")
                settle(page, 300)
        check("Laptop (1366x650 in the browser): categories on screen, More filters in view")(laptop_top, page)

        def menu_computer():   # Oct 23 (Bastien: "the drop down menu gives us all the duplicates of the header menu")
            try:
                page.set_viewport_size({"width": 1440, "height": 900})
                settle(page, 400)
                page.click("#menuBtn")
                page.wait_for_selector("#menu", state="visible")
                shown = page.eval_on_selector_all("#menu [data-go]", "e => e.filter(x => x.offsetParent).map(x => x.dataset.go)")
                head = page.eval_on_selector_all(".rdnav [data-rdgo], .rdnav a, #rdMy", "e => e.filter(x => x.offsetParent).length")
                if head:
                    for dup in ("deals", "races", "sizes", "shoes"):
                        assert dup not in shown, f"the ☰ menu repeats '{dup}', already in the header on a computer"
                assert "about" in shown, "the ☰ menu lost About on a computer"
                assert page.locator("#langPick [data-lang]").count() >= 2 and page.locator("#menu [data-ctry]").count() == 2, "language or country choice missing from the menu"
                page.click("#menuBtn")
                return "menu: " + ", ".join(shown) + " + country, language, currency"
            finally:
                page.set_viewport_size({"width": 390, "height": 844})
                settle(page, 300)
        check("Computer: the ☰ menu doesn't repeat the header")(menu_computer, page)

        def brand_full():   # Oct 23 (Bastien: "it shows only 1 norda even though I clicked full price"): brand counts counted sale items only
            if not page.locator("#ddSale").count():
                return "no sale switch on this page"
            cnt = """() => {const o = {}; [...document.querySelectorAll('#ddBrand option')].forEach(x => {const m = x.textContent.match(/^(.*) \\(([\\d,\\s]+)\\)$/); if (m) o[m[1]] = +m[2].replace(/\\D/g, '')}); return o}"""
            before = page.evaluate(cnt)
            page.evaluate("() => {const c = document.getElementById('ddSale'); c.checked = false; c.dispatchEvent(new Event('change'))}")
            try:
                after, t0 = {}, time.time()
                while time.time() - t0 < 45:          # the full catalogue is a bigger file: wait until the counts move
                    settle(page, 1000)
                    after = page.evaluate(cnt)
                    if any(after[b] > before.get(b, 0) for b in after):
                        break
                cards = page.evaluate("document.querySelectorAll('#dealList .dw').length")
                grew = [b for b in after if after[b] > before.get(b, 0)]
                assert grew, f"with full price on, no brand count went up ({len(after)} brands in the Brand menu)"
                top = max(after, key=after.get)
                return f"{len(grew)} brands count full-price items too (e.g. {top} {before.get(top, 0)} -> {after[top]}); {cards} cards"
            finally:
                page.evaluate("() => {const c = document.getElementById('ddSale'); c.checked = true; c.dispatchEvent(new Event('change'))}")
                settle(page, 500)
        check("Include full price: brand counts include full-price items")(brand_full, page)

        def whole_page():   # Oct 18 (Bastien: "nothing should ever be silo"): two tests each added a swipe row and nobody saw them
            # together. Every live test on at once (all B), then all off (all A): the top of the page on a phone stays tidy.
            names = re.findall(r'"([a-z0-9]+)"', (re.search(r"const TESTS=\[([^\]]*)\]", site_get("index.html") or "") or [None, ""])[1])
            assert names, "couldn't read the live tests (TESTS) from index.html"
            res = {}
            for arm in "BA":
                page.goto(base + "?exp=" + ",".join(f"{n}:{arm}" for n in names), wait_until="domcontentloaded")
                page.wait_for_selector("section.grp .deal", timeout=20000)
                page.wait_for_timeout(800)
                res[arm] = page.evaluate("""() => {const top = e => e ? e.getBoundingClientRect().top + scrollY : null;
                    const firstDeal = [...document.querySelectorAll('#dealList section.grp .deal')][0];
                    return {rows: document.querySelectorAll('#newBox section.grp').length, deal: top(firstDeal), h: innerHeight,
                            wide: document.documentElement.scrollWidth > innerWidth + 1}}""")
            page.evaluate("() => localStorage.removeItem('gf-exp')")
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            for arm, r in res.items():
                assert r["rows"] <= 1, f"all tests {arm}: {r['rows']} swipe rows at the top (one at most)"
                assert not r["wide"], f"all tests {arm}: the page is wider than the phone"
                assert r["deal"] is not None and r["deal"] < 2.2 * r["h"], f"all tests {arm}: the first deal starts {r['deal']:.0f}px down (over 2 screens)"
            return (f"{len(names)} tests ({', '.join(names)}); all on: {res['B']['rows']} row, first deal at {res['B']['deal'] / res['B']['h']:.1f} screens; "
                    f"all off: {res['A']['rows']} row, {res['A']['deal'] / res['A']['h']:.1f} screens")
        check("Whole page: every live test on at once stays tidy")(whole_page, page)

        def runcard_test():   # Oct 18, A/B test 'runcard': the sign-up card asks "What do you run in?" with suggestions as you type
            page.goto(base + "?exp=runcard:B", wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            if not page.locator(".runcard").count():
                page.evaluate("() => localStorage.removeItem('gf-exp')")
                return "no sign-up card on this visit (signed up or 'No thanks' earlier): skipped"
            page.click("#rcShoe")
            page.keyboard.type("peg")
            page.wait_for_timeout(500)
            sug = page.eval_on_selector_all("#rcSug button", "e => e.map(x => x.textContent)")
            page.evaluate("() => localStorage.removeItem('gf-exp')")
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            assert sug, "typing 'peg' suggests nothing"
            assert len(sug) <= 6 and all("peg" in x.lower() for x in sug), f"odd suggestions: {sug}"
            return f"'peg' -> {', '.join(sug[:3])}…"
        # Oct 22: test 'runcard' ended (Bastien); its check is off

        def pro_card():   # Oct 25 (Bastien: "yes run the Pro price test from Nov 2"): the waitlist card, $3/$29 (A) vs $5/$49 (B)
            seen = {}
            for arm in ("B", "A"):
                page.goto(base + f"?pro=1&exp=pro:{arm}", wait_until="domcontentloaded")
                page.wait_for_selector("section.grp .deal", timeout=20000)
                if not page.locator(".procard").count():
                    page.evaluate("() => localStorage.removeItem('gf-exp')")
                    return "no card slot on this visit (waiting for an email confirmation): skipped"
                seen[arm] = page.inner_text(".procard .proprice")
            assert "$5/month or $49/year" in seen["B"], f"group B shows {seen['B']!r}"
            assert "$3/month or $29/year" in seen["A"], f"group A shows {seen['A']!r}"
            assert page.locator("#proForm, #proJoin").count(), "no way to join the waitlist"
            page.click("#proNo")
            page.wait_for_timeout(400)
            gone = not page.locator(".procard").count()
            page.evaluate("() => {localStorage.removeItem('gf-nopro'); localStorage.removeItem('gf-exp')}")
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            assert gone, "'No thanks' didn't hide the card"
            import datetime as _dt
            if not ("2026-11-02" <= _dt.date.today().isoformat() <= "2026-11-16"):
                assert not page.locator(".procard").count(), "the card shows outside the test window (Nov 2-16) without ?pro=1"
            return "B $5/$49, A $3/$29, 'No thanks' hides it, nothing outside the test window"
        check("Fox Pro waitlist card (price test)")(pro_card, page)

        def pro_poll():   # Oct 28 (Bastien: "put all 6 together"): after joining the waitlist, "What would you use most?" with 6 Pro ideas
            page.goto(base + "?propoll=1", wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            if not page.locator(".propoll").count():
                return "no card slot on this visit: skipped"
            n = page.locator(".propoll .ppo").count()
            assert n == 6, f"{n} choices instead of 6"
            page.locator(".propoll .ppo").nth(0).click(); page.locator(".propoll .ppo").nth(4).click()
            pressed = page.locator('.propoll .ppo[aria-pressed="true"]').count()
            assert pressed == 2, f"{pressed} choices ticked after 2 taps"
            page.click("#ppGo"); page.wait_for_timeout(400)
            saved = page.evaluate("() => JSON.parse(localStorage.getItem('gf-prowant') || 'null')")
            gone = not page.locator(".propoll").count()
            page.evaluate("() => localStorage.removeItem('gf-prowant')")
            assert saved == ["codes", "passport"], f"saved {saved!r}"
            assert gone, "the question stayed after Send"
            return "6 choices, 2 ticked and saved, card closes after Send"
        check("Fox Pro waitlist: what would you use most?")(pro_poll, page)

        def compact_cards():   # Oct 25 (Bastien: "more items would be better on a screen"): test 'cards2' B = slimmer two-per-row phone cards,
            # last line = your size / "S/M/L" on the left + "♡ Watch" on the right, 6 top deals; A = as before
            out = {}
            for arm in ("B", "A"):
                page.goto(base + f"?exp=cards2:{arm}", wait_until="domcontentloaded")
                page.wait_for_selector("section.grp .deal", timeout=20000)
                page.wait_for_timeout(600)
                out[arm] = page.evaluate("""() => {const cs = [...document.querySelectorAll('#dealList section.grp:not(.new) .rdc')].slice(0, 12);
                  const hit = (a, b) => { if (!a || !b) return false; const x = a.getBoundingClientRect(), y = b.getBoundingClientRect();
                    return x.left < y.right - 1 && y.left < x.right - 1 && x.top < y.bottom - 1 && y.top < x.bottom - 1 };
                  return {on: document.documentElement.classList.contains('cards2'), top: document.querySelectorAll('#grp-__sale .rdc').length,
                    h: Math.round(cs.reduce((t, c) => t + c.getBoundingClientRect().height, 0) / Math.max(1, cs.length)),
                    labels: [...new Set(cs.map(c => (c.querySelector('.heart .hl') || {}).textContent))],
                    over: cs.filter(c => [...c.querySelectorAll('.yoursz,.sztxt,.cmp,.rdrep,.store,.price')].some(e => hit(e, c.querySelector('.heart')))).length,
                    boxes: cs.filter(c => c.querySelector('.szrow')).length, wide: document.documentElement.scrollWidth > innerWidth}}""")
            page.evaluate("() => {const o = JSON.parse(localStorage.getItem('gf-exp') || '{}'); delete o.cards2; localStorage.setItem('gf-exp', JSON.stringify(o))}")
            b, a = out["B"], out["A"]
            assert b["on"] and not a["on"], f"group switch didn't apply: {out}"
            assert b["top"] == 6 and a["top"] == 4, f"top deals shown: B {b['top']}, A {a['top']} (should be 6 and 4)"
            assert set(b["labels"]) <= {"Watch", "Watching"} and set(a["labels"]) <= {"Watch price", "Watching"}, f"watch labels B {b['labels']}, A {a['labels']}"
            assert not b["over"], f"B: on {b['over']} cards the last line runs into 'Watch'"
            assert not b["boxes"], f"B: {b['boxes']} cards still show size boxes"
            assert not b["wide"], "B: the page is wider than the phone"
            assert b["h"] < a["h"] * 0.85, f"B cards aren't slimmer: {b['h']}px vs {a['h']}px"
            return f"B {b['h']}px a card (A {a['h']}px), 6 top deals, size + Watch on one line, no overlaps"
        check("Compact phone cards (test cards2)")(compact_cards, page)

        def your_size_line():   # Oct 23 (Bastien OK'd): cards say "✓ Size 11 in stock" instead of a row of size chips
            lines = page.eval_on_selector_all("section.grp:not(.new) .deal .yoursz", "e => e.map(x => x.textContent)")
            rows = page.eval_on_selector_all("section.grp:not(.new) .deal .szrow", "e => e.length")
            assert lines, "no 'Size … in stock' line on the cards"
            assert not rows, f"{rows} cards still show the size chips row"
            bad = [x for x in lines if not re.search(r"\b(11|M)\b", x)]
            assert len(bad) <= len(lines) // 10, f"{len(bad)} of {len(lines)} lines don't name the visitor's size (e.g. {bad[:2]})"
            return f"{len(lines)} cards, e.g. '{lines[0]}'"
        check("Cards: one 'Size … in stock' line (no size chips)")(your_size_line, page)

        def nonmember_search():   # Oct 18: a visitor who never tapped "No thanks" searched "lululemon" and saw only the sign-up card
            prev = page.evaluate("() => localStorage.getItem('gf-nosignup')")
            page.evaluate("() => localStorage.removeItem('gf-nosignup')")
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            out = {}
            for q in ("zzqxv", "running"):
                page.fill("#dSearch", q)
                page.wait_for_timeout(1500)
                out[q] = page.evaluate("""() => {const kids = [...document.querySelectorAll('#dealList > *')];
                    const card = kids.findIndex(x => x.classList.contains('signup')), grp = kids.findIndex(x => x.matches('section.grp'));
                    const nh = document.querySelector('#dealList .nohave');
                    return {empty: !!document.querySelector('#dealList .empty'), card, grp, nohave: nh ? nh.textContent : ''}}""")
                if q == "zzqxv":   # Oct 18: "We don't have “zzqxv” yet" + a button back to today's deals
                    assert "zzqxv" in out[q]["nohave"], f"no 'we don't have it yet' message: {out[q]}"
                    page.click("#dealList [data-sclear]")
                    page.wait_for_timeout(800)
                    left = page.evaluate("() => [document.querySelector('#dSearch').value, document.querySelectorAll('#dealList section.grp').length]")
                    assert left[0] == "" and left[1] > 0, f"'See today's deals' didn't clear the search: {left}"
            page.fill("#dSearch", "")
            page.evaluate("p => p === null ? localStorage.removeItem('gf-nosignup') : localStorage.setItem('gf-nosignup', p)", prev)
            assert out["zzqxv"]["empty"] and out["zzqxv"]["card"] < 0, f"no-result search: {out['zzqxv']}"
            r = out["running"]
            assert r["card"] < 0 or (r["grp"] >= 0 and r["card"] > r["grp"]), f"sign-up card above the results: {r}"
            return "no results -> 'We don't have it yet' + a way back, no card; with results the card comes after the first deals"
        check("Search as a non-member: message when nothing matches, card after the deals")(nonmember_search, page)

        def small_phone():   # Oct 11: at 320px "$100.00 CAD $229.99" made the page 24px too wide (bottom bars cut off)
            page.set_viewport_size({"width": 320, "height": 700})
            settle(page, 500)
            try:
                w = page.evaluate("() => document.documentElement.scrollWidth")    # a phone widens innerWidth to the page: compare with 320
                assert w <= 321, f"the page is {w - 320}px too wide on a 320px phone"
            finally:
                page.set_viewport_size({"width": 390, "height": 844})
                settle(page, 300)
            return "no sideways scroll at 320px"
        check("Fits a small phone (320px)")(small_phone, page)

        def returning():
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            assert page.locator("#sheet").is_hidden(), "a returning visitor gets the welcome screen again"
            return f"{len(cards(page))} deals, sizes remembered"
        check("Returning visit remembers sizes", critical=True)(returning, page)

        def women():
            page.click("#menuBtn")
            page.click('#menu [data-go="sizes"]')
            page.wait_for_selector("#shoeSizes button", state="visible")
            page.click('#fit button[data-v="women"]')
            page.locator("#shoeSizes button[aria-pressed=true]").evaluate_all("e => e.forEach(b => b.click())")
            page.locator("#shoeSizes button", has_text=re.compile(r"^8$")).first.click()
            page.locator("#clothSizes button[aria-pressed=true]").evaluate_all("e => e.forEach(b => b.click())")
            page.locator("#clothSizes button", has_text=re.compile(r"^S$")).first.click()
            page.click("#saveSizes")
            page.wait_for_selector("#sheet", state="hidden")
            settle(page, 600)
            assert "8" in page.inner_text("#sizeSummary") or "8" in page.inner_text("main"), "the new sizes didn't show"
            all_gear()
            n = len(cards(page))
            assert n >= 20, f"only {n} deals after switching to women's 8 / S"
            if not page.locator('#cats .chip[data-v="bras"]').count():
                raise AssertionError("no Sports bras category for a women's profile")
            chip("bras")
            cs = cards(page)
            other = sorted({c["sec"] for c in cs} - {"grp-bras"})
            assert not other, f"tapping Sports bras also shows {sec(other)}"
            if per.get("bras", 0) >= 30:
                assert cs, f"Sports bras shows no deals (today's data has {per['bras']} on sale)"
            if cs:
                q = Counter(c["b"].replace(" ★", "").strip() for c in cs).most_common(1)[0][0]
                page.fill("#dSearch", q)
                settle(page, 900)
                got = cards(page)
                assert got and all(fold(q) in fold(c["b"] + " " + c["n"]) and c["sec"] == "grp-bras" for c in got), \
                    f"searching '{q}' in Sports bras doesn't show only {q} bras"
                page.fill("#dSearch", "")
                return f"{n} deals; bras {len(cs)}, search '{q}' {len(got)}"
            return f"{n} deals; no bras on sale in S"
        check("Change sizes to women's 8 / S, Sports bras + search")(women, page)

        def cloth_by():         # Oct 21: a different size per category (a visitor: "medium in shorts, L in socks, small in t-shirts")
            page.click("#menuBtn")
            page.click('#menu [data-go="sizes"]')
            page.wait_for_selector("#clothSizes button", state="visible")
            if page.locator("#clothMore").is_visible():
                page.click("#clothMore")
            page.wait_for_selector('#clothBy [data-g="socks"] button', state="visible")
            socks = page.locator('#clothBy [data-g="socks"]')
            socks.locator("button[aria-pressed=true]").evaluate_all("e => e.forEach(b => b.click())")
            socks.locator("button", has_text=re.compile(r"^L$")).first.click()
            page.click("#saveSizes")
            page.wait_for_selector("#sheet", state="hidden")
            settle(page, 600)
            p = page.evaluate("JSON.parse(localStorage.getItem('rd-profile'))")["sizes"]
            assert p["socks"]["sizes"] == ["L"], f"socks size not saved on its own ({p['socks']})"
            assert p["tops"]["sizes"] == ["S"], f"changing socks changed tops too ({p['tops']})"
            all_gear()
            if page.locator('#cats .chip[data-v="socks"]').count():
                chip("socks")
                labels = page.eval_on_selector_all("section.grp:not(.new) .deal .sizes strong", "e => e.map(x => x.textContent)")
                bad = [x for x in labels if x and not re.search(r"(^|[ ,/|])L($|[ ,/|])|OS", x)]
                assert not bad, f"socks cards show sizes other than L: {bad[:3]}"
                chip("socks")
            page.reload(wait_until="domcontentloaded")
            settle(page, 1200)
            page.click("#menuBtn")
            page.click('#menu [data-go="sizes"]')
            page.wait_for_selector('#clothBy [data-g="socks"] button[aria-pressed=true]', state="visible")
            on = page.eval_on_selector_all('#clothBy [data-g="socks"] button[aria-pressed=true]', "e => e.map(x => x.textContent)")
            assert on == ["L"], f"after a reload the socks size is {on}"
            page.click("#closeSheet")
            page.wait_for_selector("#sheet", state="hidden")
            return "tops S, socks L: saved apart, socks cards in L, kept after a reload"
        check("Clothing: a different size per category (socks L, tops S)")(cloth_by, page)

        # shoe pages
        def shoe_page():
            all_gear()
            chip("shoes")
            href = page.locator("section.grp a.cmp").first.get_attribute("href")
            page.goto(base + href.lstrip("/"), wait_until="domcontentloaded")
            rows = page.locator("table tr").count()
            assert rows >= 2, f"the shoe page {href} has no price table"
            assert re.search(r"\$\s?\d", page.inner_text("body")), f"the shoe page {href} shows no price"
            # Oct 8: the 4:17pm update printed tomorrow's (UTC) date, "checked Oct. 9" on Oct 8: never later than today in Vancouver
            m = re.search(r"checked ([A-Z][a-z]+)\.? (\d+)", page.inner_text("body"))
            if m:
                from zoneinfo import ZoneInfo
                today = datetime.now(ZoneInfo("America/Vancouver")).date()
                mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(m.group(1)[:3]) + 1
                shown = today.replace(month=mon, day=int(m.group(2))) if (mon, int(m.group(2))) <= (12, 31) else today
                assert not (shown > today and (shown - today).days < 300), f"the shoe page says 'checked {m.group(1)} {m.group(2)}', later than today in Vancouver ({today:%b %-d})"
            return f"{href}: {rows - 1} rows"
        check("Shoe page from a card", critical=True)(shoe_page, page)

        def pages():
            out = []
            for path, needs in [("shoes/", r"−\d+\s?%"), ("chaussures/", r"−\d+\s?%"), ("running-shoes-sale/", r"\$\s?\d"),
                                ("black-friday/", r"Black Friday"), ("vendredi-fou/", r"Vendredi fou"), ("about.html", r"Bastien"),
                                ("privacy.html", r"[Pp]rivacy")]:
                r = page.goto(base + path, wait_until="domcontentloaded")
                assert r and r.status == 200, f"{path} doesn't open (status {r.status if r else '?'})"
                assert re.search(needs, page.inner_text("body")), f"{path} opens but looks empty"
                out.append(path)
            page.goto(base + "shoes/", wait_until="domcontentloaded")
            box = page.locator(".find input")   # the list's own box (the header has a search box too, test 'hdr')
            if box.count():
                box.first.fill("clifton")
                settle(page, 500)
                vis = page.evaluate("[...document.querySelectorAll('a[href*=\"clifton\"]')].filter(a=>a.offsetParent).length")
                assert vis, "searching 'clifton' on the shoe list shows no Clifton"
            return f"{len(out)} pages"
        check("Shoe lists, Black Friday, About, privacy", critical=False)(pages, page)

        def size_pages():     # Oct 14: one page per shoe size (SEO: "men's size 11 running shoes on sale")
            got = []
            for rel, word in (("running-shoes-sale/men/size-11/", "Size 11"), ("chaussures-course-solde/femme/pointure-8/", "pointure 8"),
                              ("us/running-shoes-sale/women/size-8/", "Size 8")):
                h = site_get(rel) or ""
                assert word in h, f"{rel} is missing or has the wrong title"
                n = h.count('<li><a href="/')
                assert n >= 5, f"{rel} lists only {n} shoes"
                got.append(n)
            return f"size pages list {got} shoes"
        check("Size pages")(size_pages, page)

        def price_watch():    # Oct 15: price history line on shoe pages ("lowest in N days" / "it was $X: email me when it drops")
            reg = site_json("shoes/pages.json") or {}
            pages_ = [site_get(f"shoes/{k}/") or "" for k in list(reg)[:40]]
            n = sum('class="pws"' in h for h in pages_)
            if not n:
                return "no price history in this build (skipped)"
            bad = [h for h in pages_ if 'class="pw was"' in h and 'id="alertBox"' not in h]
            assert not bad, "'Email me when it drops' points to an email box the page doesn't have"
            return f"{n} of {len(pages_)} shoe pages show a price-history line"
        check("Shoe page price history line")(price_watch, page)

        def shoe_cut_first():   # Oct 18 (spy-shopper pass): a women's visitor had to scroll past the Men's table
            reg = site_json("shoes/pages.json") or {}
            slug = next((k for k in list(reg)[:200] if 'class="gt" data-g="women"' in (site_get(f"shoes/{k}/") or "")
                         and 'class="gt" data-g="men"' in (site_get(f"shoes/{k}/") or "")), None)
            if not slug:
                return "no shoe page with both men's and women's tables (skipped)"
            prev = page.evaluate("() => localStorage.getItem('rd-profile')")
            page.evaluate("() => localStorage.setItem('rd-profile', JSON.stringify({gender:'women',sizes:{shoes:{sizes:['8']}},groups:['shoes']}))")
            page.goto(base + f"shoes/{slug}/", wait_until="domcontentloaded")
            first = page.evaluate("() => [...document.querySelectorAll('.gt')].sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0].dataset.g")
            page.evaluate("p => p === null ? localStorage.removeItem('rd-profile') : localStorage.setItem('rd-profile', p)", prev)
            page.goto(base, wait_until="domcontentloaded")
            page.wait_for_selector("section.grp .deal", timeout=20000)
            assert first == "women", f"{slug}: a women's visitor sees the {first} table first"
            return f"{slug}: women's table first for a women's visitor"
        check("Shoe page: your own cut's table first")(shoe_cut_first, page)

        def inside_links():
            seen, bad = set(), []
            for path in ["", "shoes/", "about.html", "black-friday/", page_any_model()]:
                page.goto(base + path, wait_until="domcontentloaded")
                page.wait_for_timeout(600 if path == "" else 100)
                for h in page.eval_on_selector_all("a[href]", "e => e.map(a => a.href)"):
                    u = urlparse(h)
                    if u.netloc != urlparse(base).netloc or u.path in seen:
                        continue
                    seen.add(u.path)
            for pth in sorted(seen):
                if site_get(pth) is None:
                    bad.append(pth)
            assert not bad, f"{len(bad)} links inside the site lead to 'page not found': {', '.join(bad[:5])}"
            return f"{len(seen)} links"

        def page_any_model():
            reg = site_json("shoes/pages.json")
            live = [k for k, v in (reg.items() if isinstance(reg, dict) else []) if not (isinstance(v, dict) and v.get("to"))]
            return f"shoes/{live[0]}/" if live else "shoes/"
        check("Links inside the site")(inside_links, page)

        # a second visitor: "just show me today's deals" from the welcome screen, sizes later
        ctx2 = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
        stub(ctx2)
        pg = ctx2.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.set_default_timeout(15000)

        def browse():
            pg.goto(base, wait_until="domcontentloaded")
            pg.wait_for_selector("#wDeals .wdeal", state="visible", timeout=30000)
            pg.click("#wBrowseB")
            pg.wait_for_selector("#sheet", state="hidden")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            n = len(cards(pg))
            assert n >= 20, f"'just show me today's deals' shows only {n} deals"
            assert pg.locator(".browsebar").count(), "browsing without sizes doesn't offer to pick a size"
            assert "Sizes on sale" in pg.inner_text("section.grp:not(.new)") or "every size" in pg.inner_text(".browsebar").lower(), \
                "nothing says the deals show every size"   # Oct 22: the redesign says it once, in the bar above the deals
            # Oct 29 (two "wrong size" reports): with every size showing, a price that isn't the same in every size says "From"
            froms = pg.locator("section.grp .deal .price .from").count()
            assert froms, "no card says 'From' while browsing every size (prices differ by size on many shoes)"
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            assert pg.locator("#sheet").is_hidden(), "a browsing visitor gets the welcome screen again on reload"
            pg.click(".browsebar [data-picksize]")
            pg.wait_for_selector("#shoeSizes button", state="visible")
            # Oct 22 (Bastien): fit, shoe size and the general clothing size show right away; road/trail + brands stay behind "+ Road or trail"
            assert pg.locator("#moreSizes").is_visible() and pg.locator("#clothSizes").is_visible() and pg.locator("#terrain").is_hidden(), \
                "the sizes step should show fit, shoe and clothing size, with road/trail behind '+ Road or trail'"
            pg.click('#fit button[data-v="men"]')
            pg.locator("#shoeSizes button", has_text=re.compile(r"^10$")).first.click()
            pg.click("#saveSizes")
            pg.wait_for_selector("#sheet", state="hidden")
            settle(pg, 500)
            assert not pg.locator(".browsebar").count(), "the 'pick your size' note stays after picking sizes"
            pg.evaluate("() => document.querySelector('#cats .chip[data-v=\"tops\"]').click()")
            settle(pg)
            assert "Pick your clothing size" in pg.inner_text("main"), "clothing doesn't offer to pick a clothing size"
            return f"{n} deals in every size, then men's 10"
        check("Just show me deals, sizes later")(browse, pg)

        def welcome_back():   # test 'welcome' ended Oct 20 (A won): an old group B gets the welcome screen like everyone
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("try{localStorage.setItem('gf-exp',JSON.stringify({welcome:'B'}))}catch(e){}")
            q = c.new_page()
            q.on("pageerror", lambda e: errors.append(str(e)))
            q.goto(base, wait_until="domcontentloaded")
            q.wait_for_selector("#wDeals .wdeal", state="visible", timeout=30000)
            c.close()
            return "welcome screen shows"
        check("Test 'welcome' ended: everyone gets the welcome screen")(welcome_back, pg)

        def look_welcome():   # Oct 21, test 'look' (B): store names + 4 category photos on the welcome screen; a tap opens the sizes
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("try{localStorage.setItem('gf-exp',JSON.stringify({look:'B'}))}catch(e){}")
            q = c.new_page()
            q.on("pageerror", lambda e: errors.append(str(e)))
            q.goto(base, wait_until="domcontentloaded")
            q.wait_for_selector("#wStats .wcat", state="visible", timeout=30000)
            tiles = q.eval_on_selector_all("#wStats .wcat", "e => e.map(x => [x.querySelector('b').textContent, !!x.dataset.img])")   # photos are blocked here: check the address
            line = q.inner_text("#wStats .wfrom") if q.locator("#wStats .wfrom").count() else ""
            q.locator("#wStats .wcat").first.click()
            q.wait_for_selector("#sizesPart", state="visible", timeout=10000)
            c.close()
            assert len(tiles) >= 3, f"only {len(tiles)} category tiles"
            assert all(p for _, p in tiles), f"a category tile has no photo: {tiles}"
            assert re.search(r"Prices from .+ and \d+ more stores", line), f"store names line looks wrong: '{line}'"
            return f"{len(tiles)} tiles; '{line[:60]}…'; a tap opens the sizes"
        check("Test 'look': welcome screen, store names + category photos")(look_welcome, pg)

        def look_mobile():   # Oct 21 (Bastien: "make it more user friendly for mobile"): the redesign on a small phone. One deal per row, the
            # bar that stays at the top once the search scrolls away, its Filters panel (a brand picked there filters the deals), and the
            # closed panel never covering the page (first try had it invisible on top of everything, blocking every tap)
            c = br.new_context(viewport={"width": 320, "height": 640}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-exp',JSON.stringify({look:'B'}));localStorage.setItem('gf-peek','1');localStorage.setItem('gf-nosignup','1');
              localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms'],sizes:{shoes:{sizes:['11'],width:[]},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}))}catch(e){}""")
            q = c.new_page()
            q.on("pageerror", lambda e: errors.append(str(e)))
            q.goto(base, wait_until="domcontentloaded")
            q.wait_for_selector("#dealList .rdc", timeout=30000)
            q.wait_for_timeout(600)
            cols = q.evaluate("() => {const c=[...document.querySelectorAll('#dealList .grp.sale .rdc')].slice(0,2).map(x=>x.getBoundingClientRect());return c.length<2?0:(c[1].top>=c[0].bottom-1?1:2)}")
            hit = q.evaluate("() => {const e=document.elementFromPoint(160,320);return e&&e.closest('#rdFs')?'panel':'page'}")
            q.evaluate("() => scrollTo(0, 1400)")
            q.wait_for_timeout(400)
            # Oct 22 (Bastien OK'd): no bar following the scroll on phones; Filters is in the header search box, on screen anywhere
            bar = q.evaluate("() => getComputedStyle(document.getElementById('rdBar')).display === 'none' && (r => r.width > 0 && r.top >= 0 && r.bottom < 80)(document.getElementById('hFilt').getBoundingClientRect())")
            q.click("#hFilt")
            q.wait_for_selector("#rdFs:not([hidden]) #ddBrand", timeout=5000)
            brand = q.evaluate("() => {const s=document.getElementById('ddBrand');return s.options.length>1?s.options[1].value:''}")
            q.select_option("#ddBrand", brand)
            q.wait_for_timeout(700)
            q.click("#rdFsGo")
            q.wait_for_timeout(800)
            after = q.evaluate("""() => ({closed: document.getElementById('rdFs').hidden, back: !!document.querySelector('#rdHero #rdFilters'),
                brands: [...new Set([...document.querySelectorAll('#dealList .grp:not(.new) .rdc .brand')].map(x=>x.textContent))],
                wide: document.documentElement.scrollWidth > innerWidth + 1})""")
            # Oct 22: a category circle shows only that category with a "× All categories" bar; the bar brings everything back
            q.goto(base, wait_until="domcontentloaded")
            q.wait_for_selector("#dealList .rdc", timeout=30000)
            q.click('[data-rdtile="shoes"]')
            q.wait_for_timeout(800)
            cat = q.evaluate("() => [!!document.querySelector('.rdcatbar'), [...new Set([...document.querySelectorAll('#dealList section.grp:not(.new)')].map(x=>x.id))]]")
            q.click(".rdcatbar button")
            q.wait_for_timeout(800)
            back = q.evaluate("() => [!!document.querySelector('.rdcatbar'), document.querySelectorAll('#dealList section.grp:not(.new)').length]")
            c.close()
            assert cat[0] and cat[1] == ["grp-shoes"], f"Shoes circle: bar {cat[0]}, sections {cat[1]}"
            assert not back[0] and back[1] >= 4, f"'× All categories' didn't bring every category back: {back}"
            assert hit == "page", "the closed filter panel covers the page (taps don't reach it)"
            assert cols == 1, f"small phone: {cols} deals per row (want 1)"
            assert bar, "after scrolling: the old bar still shows, or the header's Filters button isn't on screen"
            assert after["closed"] and after["back"], f"the filter panel didn't close or the filters didn't go back to the top: {after}"
            assert brand and after["brands"] == [brand], f"brand '{brand}' picked in the panel, deals show {after['brands'][:5]}"
            assert not after["wide"], "page wider than a 320px phone"
            return f"1 deal per row; bar stays on top; Filters panel: brand '{brand}' -> only {brand} deals; Shoes circle -> Shoes only, '× All' back"
        check("Test 'look': small phone, sticky bar + Filters panel")(look_mobile, pg)

        def core_things():   # Oct 22 (Bastien: "don't remove core things"): every agreed, brand-defining piece is on the page, in the
            # current design and in the new one ('look' B). CLAUDE.md lists them; a missing one = tell Bastien before shipping
            missing = {}
            for arm in ("B",):   # Oct 22: the redesign is the site for everyone
                c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                stub(c)
                c.add_init_script(f"""try{{localStorage.setItem('gf-exp',JSON.stringify({{look:'{arm}'}}));localStorage.setItem('gf-peek','1');localStorage.removeItem('gf-nosignup');
                  localStorage.setItem('rd-profile',JSON.stringify({{gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms','socks','gloves','headwear','packs','gear','watches','nutrition'],sizes:{{shoes:{{sizes:['11'],width:[]}},tops:{{sizes:['M']}},bottoms:{{sizes:['M']}}}},brands:[],lang:'en'}}))}}catch(e){{}}""")
                q = c.new_page()
                q.goto(base, wait_until="domcontentloaded")
                q.wait_for_selector("#dealList .deal", timeout=30000)
                q.wait_for_timeout(1200)
                got = q.evaluate("""() => {const vis = el => !!el && el.getClientRects().length > 0, txt = s => [...document.querySelectorAll(s)].filter(vis).map(x => x.textContent).join(' ');
                  const cards = [...document.querySelectorAll('#dealList section.grp:not(.new) .dw')].slice(0, 6);
                  return {
                    '"Watch price" in words on cards': cards.length > 0 && cards.every(w => /watch price|watching/i.test(w.querySelector('.heart')?.innerText || '') || (document.documentElement.classList.contains('cards2') && /^\W*watch$/i.test((w.querySelector('.heart')?.innerText || '').trim()))),
                    'your sizes shown': /11/.test(txt('#subhead,#sizeSummary,#ddSize,#rdQS,#rdBarZ')),
                    'sign-up card': !!document.querySelector('#dealList .signup'),
                    'search box': vis(document.getElementById('dSearch')),
                    '"Wrong price or size?" on cards': cards.every(w => !!w.querySelector('.rep')),
                    'store on cards': cards.every(w => !!w.querySelector('.store')),
                    'currency after prices': cards.every(w => /CAD|USD/.test(w.querySelector('.price')?.innerText || '')),
                    'footer links': ['shoes/','about.html','privacy.html','instagram'].every(h => [...document.querySelectorAll('.foot a')].some(a => a.href.includes(h)))}}""")
                c.close()
                bad = [k for k, ok in got.items() if not ok]
                if bad:
                    missing[arm] = bad
            assert not missing, f"core things missing: {missing}"
            return "Watch price, sizes, sign-up card, search, Wrong price, store, currency, footer: all there (A and B)"
        check("Core things are on the page")(core_things, pg)

        def canadian():   # Oct 7: Canadian brands filter (Canada side): only maple-leaf brands, a box saying so, × turns it off
            pg.goto(base + "?canadian", wait_until="domcontentloaded")
            pg.wait_for_selector(".cdnbar", timeout=20000)
            settle(pg)
            if pg.evaluate("() => !!document.querySelector('.rdcatbar')"):     # an earlier check left one category picked: all of them
                pg.click(".rdcatbar button")
                settle(pg)
            brands = pg.eval_on_selector_all("#dealList .deal .brand", "e => e.map(x => [x.textContent, !!x.closest('.deal').querySelector('.leaf')])")
            assert len(brands) >= 5, f"only {len(brands)} Canadian-brand deals"
            bad = sorted({b for b, leaf in brands if not leaf})
            assert not bad, f"non-Canadian brands in the Canadian view: {', '.join(bad[:5])}"
            assert "not always made in Canada" in pg.inner_text(".cdnbar"), "the box doesn't say 'not always made in Canada'"
            pg.click("[data-cdnoff]")
            settle(pg)
            assert not pg.locator(".cdnbar").count(), "× All brands doesn't turn it off"
            return f"{len(brands)} cards, all Canadian brands"
        check("Canadian brands filter")(canadian, pg)

        def ships_ca():   # Oct 7 (Bastien): "Ships from Canada" showed US stores under Nutrition (fuel skipped the filter)
            pg.goto(base, wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            pg.evaluate("() => document.querySelector('#cats .chip[data-v=\"nutrition\"]').click()")
            settle(pg)
            for _ in range(8):
                more = pg.locator("#grp-nutrition .btn.more")
                if not more.count():
                    break
                more.first.click()
                settle(pg, 300)
            n = pg.locator("#dealList .deal").count()
            abroad = pg.eval_on_selector_all("#dealList .deal .abroad", "e => e.map(x => x.closest('.deal').innerText.split('\\n')[0])")
            assert not abroad, f"{len(abroad)} deals from outside Canada with Ships from Canada on, e.g. {abroad[0][:80]}"
            btn = pg.locator("[data-usfuel]")
            assert btn.count(), "no 'Show US stores too' under Nutrition"
            btn.first.click()
            settle(pg)
            m = pg.locator("#dealList .deal").count()
            pg.evaluate("() => document.querySelector('#toggles .chip[data-t=\"ca\"]').click()")   # back to Canada only for the next checks
            settle(pg)
            pg.evaluate("() => document.querySelector('#cats .chip[data-v=\"nutrition\"]').click()")                                  # and every category again
            settle(pg)
            return f"Nutrition: {n} deals from Canada, {m} with US stores"
        check("Ships from Canada means Canada")(ships_ca, pg)

        def backbar_none():   # Oct 22: the come-back sign-up bar was removed (612 shown, 264 closed, 0 sign-ups); a non-member coming
            # back from a store gets the store's other deals or nothing, never the email bar
            pg.goto(base, wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            pg.evaluate("localStorage.removeItem('gf-sub');sessionStorage.removeItem('gf-offered');sessionStorage.setItem('gf-lastshop',JSON.stringify({h:'sportinglife.ca',t:Date.now()}))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            settle(pg, 3000)
            assert not pg.locator("#backBar.subar,#backBar.bwbar").count(), "the removed sign-up bar still shows after a deal click"
            pg.evaluate("sessionStorage.removeItem('gf-lastshop')")
            return "no sign-up bar; the store offer only"
        check("Back from a store: no sign-up bar (removed Oct 22)")(backbar_none, pg)

        def any_size_link():   # Oct 25 (Bastien: "clicked a salomon shoe and its showing me size 6.5 when I have 11 selected"): a view of
            # every size (?q= post links, "Show all sizes") opened the cheapest size at the store; with the visitor's size in stock, the
            # link must open on their size
            items = site_json("sale.json")["items"]
            pick = None
            for x in items:
                if x["g"] != "shoes" or x.get("sx") != ["men"] or x.get("w"):
                    continue
                e11 = [e for e in x["sz"] if e[0] == "11" and len(e) > 4 and isinstance(e[4], int)]
                if e11 and any(e[1] < e11[0][1] and len(e) > 4 and e[4] != e11[0][4] for e in x["sz"]):
                    pick = (x, e11[0])
                    break
            if not pick:
                return "no shoe today with a cheaper size than 11 (nothing to check)"
            x, e = pick
            q = " ".join(re.sub(r"\s+-\s+Men's$", "", x["n"]).split()[:4])
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');
              localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'all',country:'ca',groups:['shoes'],sizes:{shoes:{sizes:['11'],width:[]}},brands:[],lang:'en'}))}catch(e){}""")
            q2 = c.new_page()
            try:
                q2.goto(base + "?q=" + q.replace(" ", "+"), wait_until="domcontentloaded")
                q2.wait_for_selector("#dealList a[href*='variant='], #dealList a.deal", timeout=20000)
                settle(q2, 800)
                hrefs = q2.eval_on_selector_all("#dealList a[href^='http']", "e => e.map(a => a.href)")
                mine = [h for h in hrefs if h.split("?")[0] == x["of"][e[2]].split("?")[0]]
                assert mine, f"'{q}': the card for {x['b']} {x['n']} isn't on the page"
                assert any(f"variant={e[4]}" in h for h in mine), f"'{q}': the card opens {mine[0][-40:]}, not size 11 (variant {e[4]})"
            finally:
                c.close()
            return f"{x['b']} {q}: opens size 11"
        check("All-sizes view: the store link opens on your size")(any_size_link, pg)

        def hiking_tab():   # Oct 25 (Bastien: hiking "identical to the running page", launch today): the switch beside the size,
            # hiking deals and words, the six hiking circles, hiking type buttons, and back to running
            if not site_json("sale-hike.json"):
                return "no hiking file in this build (skipped)"
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');localStorage.removeItem('gf-sport');
              localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms','socks','gloves','headwear','packs','gear'],sizes:{shoes:{sizes:['11'],width:[]},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}))}catch(e){}""")
            q2 = c.new_page()
            errs = []
            q2.on("pageerror", lambda e: errs.append(str(e)))
            try:
                q2.goto(base, wait_until="domcontentloaded")
                q2.wait_for_selector("#dealList .rdc", timeout=30000)
                sw = [b for b in q2.query_selector_all(".sportsw button[data-sport=hike]") if b.is_visible()]
                assert sw, "no visible Hiking button beside the size"
                sw[0].click()
                q2.wait_for_function("document.documentElement.classList.contains('hike') && document.querySelectorAll('#dealList .rdc').length > 3", timeout=30000)
                settle(q2, 800)
                h1 = q2.inner_text("#rdH1")
                assert "hiking" in h1.lower(), f"headline on the hiking side: {h1!r}"
                tiles = q2.eval_on_selector_all("#rdTiles .rdtile b", "e => e.map(x => x.textContent)")
                assert tiles[:3] == ["Boots & Shoes", "Jackets & Tops", "Pants & Shorts"], f"hiking circles: {tiles}"
                q2.locator("#rdTiles .rdtile").nth(1).click()
                settle(q2, 1000)
                chips = q2.eval_on_selector_all(".types .chip", "e => e.map(x => x.textContent)")
                assert "Rain shells" in chips, f"no hiking type buttons under Jackets & Tops: {chips}"
                wide = q2.evaluate("document.documentElement.scrollWidth - innerWidth")
                assert wide <= 1, f"the hiking page is {wide}px wider than the phone"
                [b for b in q2.query_selector_all(".sportsw button[data-sport=run]") if b.is_visible()][0].click()
                q2.wait_for_function("!document.documentElement.classList.contains('hike')", timeout=20000)
                settle(q2, 1500)
                assert "hiking" not in q2.inner_text("#rdH1").lower(), "back on Running, the headline still says hiking"
                assert not errs, f"script error: {errs[0][:120]}"
            finally:
                c.close()
            return f"{h1.splitlines()[0][:40]}; circles {', '.join(tiles[:3])}…"
        check("Hiking tab: switch, hiking deals and words, circles, types, back to running")(hiking_tab, pg)

        def hiking_intake():   # Oct 25 (Bastien OK'd the hiking intake mockup: "similar drop down as running. Different choices for socks
            # pants shirts"): a new visitor landing on ?sport=hike gets hiking words, the EU boot line matched from the US size,
            # "What kind of hiking?" and a hiking per-category size link; all of it saved in the profile
            if not site_json("sale-hike.json"):
                return "no hiking file in this build (skipped)"
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            q2 = c.new_page()
            errs = []
            q2.on("pageerror", lambda e: errs.append(str(e)))
            try:
                q2.goto(base + "?sport=hike", wait_until="domcontentloaded")
                q2.wait_for_selector("#saveSizes", state="visible", timeout=30000)
                settle(q2, 800)
                assert q2.get_attribute("#wSport [data-sport=hike]", "aria-pressed") == "true", "welcome: Hiking not shown as picked"
                q2.click("#saveSizes")
                q2.wait_for_selector("#shoeSizes .chip", state="visible")
                q2.click("#fit button[data-v=men]")
                q2.click("#shoeSizes .chip[data-v='11']")
                q2.click("#clothSizes .chip[data-v=M]")
                settle(q2, 400)
                eu = q2.inner_text("#euLine")
                assert "EU 44.5" in eu, f"EU line for a men's US 11: {eu!r}"
                if q2.locator("#moreSizes").is_visible():
                    q2.click("#moreSizes")
                cm = q2.inner_text("#clothMore")
                assert "pants" in cm.lower(), f"per-category size link isn't worded for hiking: {cm!r}"
                q2.click("#hkind button[data-v=overnight]")
                q2.click("#saveSizes")
                q2.wait_for_selector("#sheet", state="hidden", timeout=20000)
                settle(q2, 1500)
                p = q2.evaluate("JSON.parse(localStorage.getItem('rd-profile'))")
                assert p.get("hike_kind") == "overnight", f"kind of hiking not saved: {p.get('hike_kind')}"
                assert p["sizes"]["shoes"].get("eu") == ["44.5"], f"EU size not saved: {p['sizes']['shoes']}"
                h1 = q2.inner_text("#rdH1")
                assert "running" not in h1.lower(), f"hiking headline says running: {h1!r}"
                assert not errs, f"script error: {errs[0][:120]}"
            finally:
                c.close()
            return f"EU 44.5 matched, overnight saved; {h1.splitlines()[0][:40]}"
        check("Hiking intake: EU boot size, kind of hiking, hiking words")(hiking_intake, pg)

        def short_sizes():   # Oct 25 test 'short' (Bastien OK'd): B's first sizes screen asks only fit + shoe size; clothing,
            # the EU line and the rest sit behind one link; Show my deals works with just a shoe size (clothing in every size)
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("try{localStorage.setItem('gf-exp',JSON.stringify({welcome:'A',layout:'A',short:'B'}))}catch(e){}")
            q2 = c.new_page()
            errs = []
            q2.on("pageerror", lambda e: errs.append(str(e)))
            try:
                q2.goto(base, wait_until="domcontentloaded")
                q2.wait_for_selector("#saveSizes", state="visible", timeout=30000)
                settle(q2, 600)
                q2.click("#saveSizes")
                q2.wait_for_selector("#shoeSizes .chip", state="visible")
                settle(q2, 400)
                assert not q2.locator("#clothSizes").is_visible(), "B: clothing sizes still on the first screen"
                more = q2.inner_text("#moreSizes")
                assert "Clothing size" in more, f"B: the link doesn't offer the clothing size: {more!r}"
                q2.click("#fit button[data-v=men]")
                q2.click("#shoeSizes .chip[data-v='11']")
                q2.click("#saveSizes")
                q2.wait_for_selector("#sheet", state="hidden", timeout=20000)
                q2.wait_for_selector("#dealList .rdc", timeout=30000)
                n = q2.locator("#dealList .rdc").count()
                assert n > 3, f"only {n} deals after fit + shoe size"
                q2.click("#menuBtn")
                q2.click('#menu [data-go="sizes"]')
                q2.wait_for_selector("#clothSizes button", state="visible", timeout=10000)
                assert not errs, f"script error: {errs[0][:120]}"
            finally:
                c.close()
            return f"fit + shoe size only, {n} deals; clothing size there under My sizes"
        check("Short sizes screen (test short B)")(short_sizes, pg)

        def boot_pages():   # Oct 25 (Bastien: boot price pages "doing the same as the shoe page"): list -> a model page with sizes,
            # its French twin, and a hiking card's "All sizes & stores" link lands on a boot page
            if not site_get("hiking-boots/pages.json"):
                return "no boot pages in this build (skipped)"
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            q2 = c.new_page()
            errs = []
            q2.on("pageerror", lambda e: errs.append(str(e)))
            try:
                q2.goto(base + "hiking-boots/", wait_until="domcontentloaded")
                links = q2.eval_on_selector_all(".links a", "e => e.map(a => a.getAttribute('href'))")
                assert len(links) >= 10, f"only {len(links)} models on the boot list page"
                q2.goto(base + links[0].lstrip("/"), wait_until="domcontentloaded")
                h1 = q2.inner_text("h1")
                rows = q2.locator("table tr").count()
                assert rows > 2 or q2.locator("text=Not in stock").count(), f"{links[0]}: no size table"
                assert "running" not in q2.title().lower(), f"boot page title says running: {q2.title()!r}"
                q2.goto(base + links[0].lstrip("/").replace("hiking-boots/", "bottes-randonnee/"), wait_until="domcontentloaded")
                assert q2.evaluate("document.documentElement.lang").startswith("fr"), "French boot page missing"
                c.add_init_script("""try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');
                  localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes'],sizes:{shoes:{sizes:['11'],width:[]}},brands:[],lang:'en'}))}catch(e){}""")
                q3 = c.new_page()
                q3.on("pageerror", lambda e: errs.append(str(e)))
                q3.goto(base + "?sport=hike", wait_until="domcontentloaded")
                q3.wait_for_function("document.documentElement.classList.contains('hike') && document.querySelectorAll('#dealList .rdc').length > 3", timeout=30000)
                q3.wait_for_timeout(1500)
                hrefs = q3.eval_on_selector_all("a.cmp", "e => e.map(a => a.getAttribute('href'))")
                bad = [h for h in hrefs if "hiking-boots/" not in h]
                assert not bad, f"hiking cards link to running shoe pages: {bad[:2]}"
                assert not errs, f"script error: {errs[0][:120]}"
            finally:
                c.close()
            return f"{len(links)} models; {h1[:40]}; {len(hrefs)} hiking cards link to boot pages"
        check("Boot price pages + hiking cards link to them")(boot_pages, pg)

        def hike_lists():   # Oct 25 (Bastien: trail gear lists): hub -> a trail, sizes picked -> deals in each line, a tick counts
            if not site_get("hikes/index.html") and not site_get("hikes/"):
                return "no trail gear lists in this build (skipped)"
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("try{var o=JSON.parse(localStorage.getItem('gf-exp')||'{}')||{};if(!o.kit){o.kit='A';localStorage.setItem('gf-exp',JSON.stringify(o))}}catch(e){}")   # test 'kit': unfolded list
            q2 = c.new_page()
            errs = []
            q2.on("pageerror", lambda e: errs.append(str(e)))
            try:
                q2.goto(base + "hikes/", wait_until="domcontentloaded")
                links = q2.eval_on_selector_all(".cards a", "e => e.map(a => a.getAttribute('href'))")
                assert links, "no trails on the hub"
                q2.goto(base + links[0].lstrip("/"), wait_until="domcontentloaded")
                q2.click('#rsize [data-g="men"]')
                q2.click('#rsize button[data-s="M"]')
                q2.select_option("#shoeSz", "11")
                settle(q2, 500)
                deals = q2.locator(".gi:not([hidden]) .dl li").count()
                assert deals >= 5, f"{links[0]}: only {deals} deals after men's M / 11"
                before = q2.inner_text("#prog")
                q2.locator(".gi:not([hidden]) input.have").first.check()
                settle(q2, 300)
                assert q2.inner_text("#prog") != before, "ticking an essential didn't change 'You have N of M'"
                assert "running" not in q2.title().lower(), f"trail page title says running: {q2.title()!r}"
                # Oct 26 (Bastien: "the trail list still links to races"): the menu is the hiking one
                menu = q2.eval_on_selector_all("details.menu nav a", "e => e.map(a => a.getAttribute('href'))")
                assert not [u for u in menu if "/races/" in u or "/courses/" in u or "/shoes/" in u], f"trail page menu goes to running pages: {menu}"
                assert any("/hikes/" in u for u in menu), f"trail page menu has no trail gear lists link: {menu}"
                # Oct 26 (Bastien: calories by hours hiked and pack weight): the food box answers, and a heavier pack means more
                fo = q2.inner_text("#fuel .fo")
                assert "kcal" in fo, f"the food box shows no calories: {fo[:80]!r}"
                k1 = int(re.search(r"([\d,]+) kcal", fo).group(1).replace(",", ""))
                q2.fill('#fuel [data-f="fu_pack"]', "25")
                settle(q2, 200)
                k2 = int(re.search(r"([\d,]+) kcal", q2.inner_text("#fuel .fo")).group(1).replace(",", ""))
                assert k2 > k1, f"a 25 kg pack didn't raise the calories ({k1} -> {k2})"
                # Oct 27 (Bastien: "some people use both"): kg | lb converts the weights, same answer
                body = float(q2.input_value('#fuel [data-f="fu_body"]'))
                q2.click('#fuel .fuu button[data-u="lb"]')
                settle(q2, 200)
                lbv = float(q2.input_value('#fuel [data-f="fu_body"]'))
                assert abs(lbv - body * 2.2046) <= 1, f"kg -> lb: body weight {body} became {lbv}"
                k3 = int(re.search(r"([\d,]+) kcal", q2.inner_text("#fuel .fo")).group(1).replace(",", ""))
                assert abs(k3 - k2) <= 0.03 * k2, f"switching to lb changed the calories ({k2} -> {k3})"
                q2.click('#fuel .fuu button[data-u="kg"]')
                assert not errs, f"script error: {errs[0][:120]}"
            finally:
                c.close()
            return f"{len(links)} trails; {links[0]}: {deals} deals in men's M / 11; food box {k1} -> {k2} kcal with a 25 kg pack"
        check("Trail gear list: sizes, deals, ticks, food box")(hike_lists, pg)

        def hike_bottom():   # Oct 25 (Bastien: "The hiking page shows running deal links at the bottom"): hiking side = boot block + boot footer link
            if not (site_get("index.html") or "").count('class="seo-today seo-hike"'):
                return "no hiking bottom block in this build (skipped)"
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');
              localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes'],sizes:{shoes:{sizes:['11'],width:[]}},brands:[],lang:'en'}))}catch(e){}""")
            q2 = c.new_page()
            try:
                q2.goto(base + "?sport=hike", wait_until="domcontentloaded")
                q2.wait_for_function("document.documentElement.classList.contains('hike') && document.querySelectorAll('#dealList .rdc').length > 3", timeout=30000)
                run_vis = q2.evaluate("[...document.querySelectorAll('.seo-today:not(.seo-hike)')].some(e => e.offsetParent)")
                hike_vis = q2.evaluate("[...document.querySelectorAll('.seo-hike .seo-en')].some(e => e.offsetParent)")
                assert not run_vis, "the running deals block still shows on the hiking side"
                assert hike_vis, "the hiking bottom block doesn't show on the hiking side"
                foot = q2.inner_text('p.foot[data-i18n="footer"]')
                assert "Boot prices" in foot and "Shoe prices" not in foot, f"hiking footer link: {foot!r}"
            finally:
                c.close()
            return "boot block + 'Boot prices by model' on the hiking side"
        check("Hiking side: bottom block and footer are hiking")(hike_bottom, pg)

        def menu_short_phone():   # Oct 25 (Bastien: "is there no more button to go from Canada to USA in the menu?"): on a short phone
            # the menu ran past the screen; Canada/USA and Prices in must be reachable
            c = br.new_context(viewport={"width": 320, "height": 568}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes'],sizes:{shoes:{sizes:['11'],width:[]}},brands:[],lang:'en'}))}catch(e){}""")
            q2 = c.new_page()
            try:
                q2.goto(base + "?gifts=1", wait_until="domcontentloaded")    # Oct 28: with the seasonal gift item in the menu too
                q2.wait_for_selector("#dealList .rdc", timeout=30000)
                q2.click("#menuBtn")
                settle(q2, 500)
                assert q2.locator("#mGifts").is_visible(), "the gift item isn't in the menu with ?gifts=1"
                q2.locator("#menu [data-ctry=us]").scroll_into_view_if_needed(timeout=3000)
                r = q2.evaluate("document.querySelector('#menu [data-ctry=us]').getBoundingClientRect().bottom")
                assert r <= q2.evaluate("innerHeight"), f"USA button below the screen ({round(r)}px) and can't be reached"
                q2.click("#menu [data-ctry=us]")
                settle(q2, 800)
                assert q2.evaluate("document.documentElement.classList.contains('us')"), "tapping USA in the menu didn't switch"
            finally:
                c.close()
            return "Canada/USA reachable and working on a 320x568 phone"
        check("Menu on a short phone: Canada/USA reachable")(menu_short_phone, pg)

        def gift_menu():          # Oct 28 (growth chat, Bastien OK'd): "Gifts for runners" in the ☰ menu Nov 15 - Dec 26, Canada running side only
            import datetime as _dt
            from zoneinfo import ZoneInfo
            d = _dt.datetime.now(ZoneInfo("America/Vancouver")).strftime("%m-%d")
            season = "11-15" <= d <= "12-26"
            out = []
            for q, lang, want in (("", "en", season), ("?gifts=1", "en", True), ("?gifts=1&lang=fr", "fr", True), ("?gifts=1&c=us", "en", False)):
                c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                stub(c)
                c.add_init_script("""try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes'],sizes:{shoes:{sizes:['11'],width:[]}},brands:[],lang:'""" + lang + """'}))}catch(e){}""")
                q2 = c.new_page()
                try:
                    q2.goto(base + q, wait_until="domcontentloaded")
                    q2.wait_for_selector("#dealList .rdc", timeout=30000)
                    q2.click("#menuBtn")
                    settle(q2, 400)
                    vis = q2.locator("#mGifts").is_visible()
                    # Oct 28 (Bastien): Instagram left the menu ("it's at the bottom of the page"); the footer keeps it
                    assert not q2.locator('#menu a[href*="instagram.com"]').count(), "Instagram is back in the ☰ menu"
                    assert q2.locator('footer a[href*="instagram.com"], .foot a[href*="instagram.com"]').count(), "the footer lost its Instagram link"
                    assert vis == want, f"{q or 'no switch'}: gift item {'missing' if want else 'showing'} (today {d})"
                    if vis:
                        href, txt = q2.get_attribute("#mGifts", "href"), q2.inner_text("#mGifts")
                        assert href == ("cadeaux-coureurs/" if lang == "fr" else "gifts-for-runners/"), f"gift item goes to {href}"
                        assert ("Cadeaux" if lang == "fr" else "Gifts for runners") in txt, f"gift item reads {txt!r}"
                        after = q2.evaluate("document.getElementById('mRaces').nextElementSibling.id")
                        assert after == "mGifts", "the gift item isn't right after the race gear lists"
                    out.append(f"{q or 'today'} {'on' if vis else 'off'}")
                finally:
                    c.close()
            return "; ".join(out)
        check("Menu: seasonal 'Gifts for runners' (Nov 15 - Dec 26, Canada)")(gift_menu, pg)

        def open_mail():     # Oct 11 (52% confirmed): "Check your inbox" opens their mail app
            pg.evaluate("localStorage.setItem('gf-sub',JSON.stringify({pending:'robot@gmail.com'}))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector(".signup .mailbtn", timeout=8000)
            href = pg.get_attribute(".signup .mailbtn", "href")
            assert "mail.google.com" in href, f"Gmail address, button goes to {href}"
            pg.evaluate("localStorage.setItem('gf-sub',JSON.stringify({pending:'robot@hotmail.com'}))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector(".signup .mailbtn", timeout=8000)
            assert "outlook" in pg.get_attribute(".signup .mailbtn", "href"), "Hotmail address doesn't open Outlook"
            pg.evaluate("localStorage.removeItem('gf-sub')")
            return "Gmail, Outlook"
        check("Check your inbox: open my mail")(open_mail, pg)

        def q_landing():     # Oct 11: a ?q= link from a post: the deal first, then one short sign-up line
            nm = pg.evaluate("() => { const a = document.querySelector('section.grp:not(.new) a.deal'); return a.querySelector('.brand').textContent.replace('🍁','').trim() + ' ' + a.querySelector('.name').textContent }")
            q = " ".join(nm.split()[:3])
            pg.evaluate("localStorage.removeItem('gf-nosignup')")
            pg.goto(base + "?q=" + q.replace(" ", "+") + "&ref=sitetest", wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            pg.wait_for_selector(".signup.qsline #suForm", timeout=8000)
            first = pg.evaluate("() => { const l = document.querySelector('.qsline'), g = document.querySelector('section.grp'); return !!(g.compareDocumentPosition(l) & 4) }")
            assert first, "the sign-up line shows above the deal"
            assert pg.locator(".signup").count() == 1, "two sign-up asks on the page"
            return q
        check("Post link (?q=): deal, then a sign-up line")(q_landing, pg)

        def shoe_alert():       # Oct 8: "Email me when it drops in my size" on shoe pages (Google visitors)
            reg = site_json("shoes/pages.json")
            slug = next((k for k, v in list(reg.items())[:40] if not (isinstance(v, dict) and v.get("to"))
                         and 'id="alertBox"' in (site_get(f"shoes/{k}/") or "")), None)
            assert slug, "no shoe page has the 'email me when it drops' box"
            pg.goto(base + f"shoes/{slug}/", wait_until="domcontentloaded")
            pg.wait_for_selector("#alertBox form", timeout=8000)
            pg.fill("#alertBox input", "robot@example.com")
            pg.click("#alertBox button")
            settle(pg, 700)
            msg = pg.inner_text("#alertBox .msg")
            assert "robot@example.com" in msg or "size" in msg.lower(), f"the box gave no answer ({msg!r})"
            return f"{slug}: {msg[:60]}"
        check("Shoe page: email me when it drops")(shoe_alert, pg)

        def shoe_back():        # Oct 27: pages with nothing in stock: "Email me when it's back in my size" watches the whole page
            reg = site_json("shoes/pages.json") or {}
            slug = next((k for k, v in reg.items() if isinstance(v, dict) and not v.get("to")
                         and 'id="backBox"' in (site_get(f"shoes/{k}/") or "")), None)
            if not slug:
                return "every shoe page has something in stock today"
            pg.goto(base + f"shoes/{slug}/", wait_until="domcontentloaded")
            pg.wait_for_selector("#backBox form", timeout=8000)
            prev = pg.evaluate("() => localStorage.getItem('gf-watch')")
            # Oct 30 (morning email: select_option timed out): a size saved by an earlier check shows "Men's 11 · Change" and hides
            # the two menus, as it should for a visitor; tap Change first
            if pg.locator("#backBox .bok button").count():
                pg.click("#backBox .bok button")
            # the page's own choices (a women's-only shoe has no men's fit; Oct 28 a fixed "men" timed out)
            fits = pg.eval_on_selector_all("#backBox [data-fit] option", "os => os.map(o => o.value).filter(Boolean)")
            if fits:
                pg.select_option("#backBox [data-fit]", "men" if "men" in fits else fits[0])
                pg.wait_for_timeout(200)
            sizes = pg.eval_on_selector_all("#backBox [data-size] option", "os => os.map(o => o.value).filter(Boolean)")
            assert sizes, "the box offers no sizes to pick"
            pg.select_option("#backBox [data-size]", "10.5" if "10.5" in sizes else sizes[len(sizes) // 2])
            pg.fill("#backBox input", "robot@example.com")
            pg.click("#backBox button")
            settle(pg, 900)
            msg = pg.inner_text("#backBox .msg")
            w = json.loads(pg.evaluate("() => localStorage.getItem('gf-watch')") or "{}")
            pg.evaluate("p => p === null ? localStorage.removeItem('gf-watch') : localStorage.setItem('gf-watch', p)", prev)
            assert "robot@example.com" in msg, f"the box gave no answer ({msg!r})"
            assert f"page|{slug}" in w, f"the page wasn't put on the watchlist: {list(w)[:3]}"
            return f"{slug}: watched as page|{slug}"
        check("Shoe page with nothing in stock: email me when it's back")(shoe_back, pg)

        def shoe_alts():        # Oct 22, test 'alts': B shows other shoes of the same kind on sale in your size under the size tables
            alts = site_json("shoes/alts.json") or {}
            assert alts and all(len(v) >= 3 for k, v in alts.items() if k != "hike"), f"shoes/alts.json is empty or thin: { {k: len(v) for k, v in alts.items()} }"
            reg = site_json("shoes/pages.json") or {}
            slug = next((k for k, v in reg.items() if isinstance(v, dict) and not v.get("to") and v.get("t") == "race"
                         and 'id="alts"' in (site_get(f"shoes/{k}/") or "")), None)
            assert slug, "no race shoe page has the 'other shoes' section"
            prev = pg.evaluate("() => localStorage.getItem('rd-profile')")
            pg.evaluate("() => localStorage.setItem('rd-profile', JSON.stringify({gender:'men',sizes:{shoes:{sizes:['10']}},groups:['shoes']}))")
            got = {}
            for arm in ("A", "B"):
                pg.goto(base + f"shoes/{slug}/?exp=alts:{arm}", wait_until="domcontentloaded")
                settle(pg, 1200)
                got[arm] = pg.evaluate("""() => {const a = document.getElementById('alts'); return {hidden: a.hidden,
                    cards: [...a.querySelectorAll('.altrow a')].map(x => [x.getAttribute('href'), x.querySelector('.az').textContent])}}""")
            pg.evaluate("p => p === null ? localStorage.removeItem('rd-profile') : localStorage.setItem('rd-profile', p)", prev)
            pg.evaluate("() => { const o = JSON.parse(localStorage.getItem('gf-exp') || '{}'); delete o.alts; localStorage.setItem('gf-exp', JSON.stringify(o)) }")
            assert got["A"]["hidden"], "group A (as before) shows the 'other shoes' row"
            b = got["B"]
            assert not b["hidden"] and len(b["cards"]) >= 3, f"{slug}: group B shows {len(b['cards'])} other shoes"
            assert all(h != f"/shoes/{slug}/" for h, _ in b["cards"]), "the row shows the page's own shoe"
            assert all("10" in z for _, z in b["cards"]), f"cards not in the visitor's size: {[z for _, z in b['cards']]}"
            return f"{slug}: A hidden, B shows {len(b['cards'])} race shoes in size 10"
        check("Shoe page: other shoes on sale in your size (test 'alts')")(shoe_alts, pg)

        def shoe_hdr():     # Oct 23 (Bastien: "you get lost scrolling"): the header comes back on scroll-up + search, every shoe/list/race page
            reg = site_json("shoes/pages.json") or {}
            slug = next((k for k, v in reg.items() if isinstance(v, dict) and not v.get("to")), None)
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            q = c.new_page()
            try:
                q.goto(base + f"shoes/{slug}/", wait_until="load")
                q.wait_for_timeout(500)
                assert q.locator("#hsb").is_visible(), "no search icon in the header"
                q.evaluate("scrollTo(0, 1600)")
                q.wait_for_timeout(200)
                q.mouse.wheel(0, 300)
                q.wait_for_timeout(500)
                down = q.evaluate("Math.round(document.querySelector('header.top').getBoundingClientRect().bottom)")
                q.mouse.wheel(0, -250)
                q.wait_for_timeout(600)
                up = q.evaluate("Math.round(document.querySelector('header.top').getBoundingClientRect().top)")
                assert down <= 1, f"the header didn't slide away while scrolling down (bottom at {down}px)"
                assert up == 0, f"the header didn't come back on scroll-up (top at {up}px)"
                q.click("#hsb")
                q.fill("#hsf input", "pegasus")
                with q.expect_navigation():
                    q.press("#hsf input", "Enter")
                assert "q=pegasus" in q.url, f"search went to {q.url}"
                return "hides on scroll down, back on scroll up, search opens the deals"
            finally:
                c.close()
        check("Shoe page: header comes back on scroll-up + search")(shoe_hdr, pg)

        def hearts_two_devices():   # Oct 23 (Bastien: "I keep taking 2 items off the list and it inputs them back"): one account, two
            # devices (phone browser + home-screen app keep separate storage); removing on one must not come back from the other
            srv = {}

            def rpc(route):
                name = route.request.url.split("/rpc/")[-1].split("?")[0]
                try:
                    body = json.loads(route.request.post_data or "{}")
                except Exception:
                    body = {}
                res = None
                if name == "watch_list":
                    res = [{"key": k, "meta": m} for k, m in srv.items()]
                elif name == "watch_add":
                    srv[body["p_key"].lower()] = body["p_meta"]
                    res = True
                elif name == "watch_remove":
                    res = srv.pop(body["p_key"].lower(), None) is not None
                route.fulfill(status=200, content_type="application/json", body=json.dumps(res))
            init = ("try{if(!localStorage.getItem('rd-profile')){localStorage.setItem('gf-peek','1');localStorage.setItem('gf-nosignup','1');"
                    "localStorage.setItem('gf-sub',JSON.stringify({key:'11111111-1111-4111-8111-111111111111',email:'t@example.com',active:true}));"
                    "localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms'],"
                    "sizes:{shoes:{sizes:['11'],width:[]},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}))}}catch(e){}")
            ctxs = []

            def device():
                c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                stub(c)
                c.route("**/rest/v1/rpc/watch_*", rpc)
                c.add_init_script(init)
                ctxs.append(c)
                q = c.new_page()
                q.goto(base, wait_until="domcontentloaded")
                q.wait_for_selector("#dealList .heart", state="attached", timeout=30000)
                q.wait_for_timeout(1500)
                return q
            local = lambda q: set(json.loads(q.evaluate("localStorage.getItem('gf-watch')") or "{}"))
            try:
                a = device()
                hs = a.locator("#dealList .heart")
                for i in range(3):
                    hs.nth(i * 2).evaluate("e => e.click()")
                    a.wait_for_timeout(300)
                assert len(srv) == 3, f"3 hearts, but the account has {len(srv)}"
                b = device()
                keys = sorted(local(b))[:2]
                assert len(keys) == 2, "the second device didn't get the hearts"
                b.evaluate("document.getElementById('openWatch').click()")
                b.wait_for_timeout(1500)
                for k in keys:
                    b.locator(f'#dealList .heart[data-key="{k}"]').first.evaluate("e => e.click()")
                    b.wait_for_timeout(500)
                a.reload(wait_until="domcontentloaded")
                a.wait_for_selector("#dealList .heart", state="attached", timeout=30000)
                a.wait_for_timeout(2000)
                back = [k for k in keys if k in srv or k in local(a)]
                assert not back, f"removed on one device, back after the other opened: {back}"
                return "removed on one device stays removed on the other (1 left of 3)"
            finally:
                for c in ctxs:
                    c.close()
        check("Watchlist: removed on one device stays removed on the other")(hearts_two_devices, pg)

        def store_offer():           # Oct 27: a store's own site-wide code (promos.json): a line on top, a note on its full-price cards
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            offers = [{"store": "ca.shop.runningroom.com", "side": "ca", "en": "Test offer", "fr": "Offre test", "code": "TESTCODE", "until": "2099-12-31"},
                      {"store": "sportchek.ca", "side": "ca", "en": "Old offer", "code": "OLD", "until": "2099-01-01", "from": "2098-01-01"},
                      {"store": "sportinglife.ca", "side": "ca", "en": "Up to 40% off sale", "fr": "Up to 40% off sale", "auto": True, "sale": True,
                       "cards": False, "until": "2099-12-31", "chk": {"n": 400, "on": 120, "med": 30}},   # Oct 27: read off a homepage bar
                      {"store": "us.2xu.com", "side": "us", "en": "US only", "until": "2099-12-31"}]
            c.route("**/promos.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(offers)))
            c.add_init_script("try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',"
                              "ships:'ca',country:'ca',groups:['shoes','tops','bottoms'],sizes:{shoes:{sizes:['11'],width:[]},tops:{sizes:['M']},"
                              "bottoms:{sizes:['M']}},brands:[],lang:'en'}))}catch(e){}")
            try:
                q = c.new_page()
                q.goto(base, wait_until="domcontentloaded")
                q.wait_for_selector("#dealList .promobar", state="attached", timeout=30000)
                bars = q.locator("#dealList .promobar")
                assert bars.count() == 1, f"{bars.count()} store offer lines on a phone (1: not one that hasn't started, nor the USA side's)"
                assert "TESTCODE" in bars.first.inner_text(), "the offer line doesn't show the code"
                q.set_viewport_size({"width": 1280, "height": 900})          # computers show two
                q.evaluate("renderAll()") if q.evaluate("typeof renderAll") == "function" else q.reload()
                q.wait_for_timeout(800)
                if bars.count() < 2:
                    q.reload(wait_until="domcontentloaded")
                    q.wait_for_selector("#dealList .promobar", state="attached", timeout=30000)
                    q.wait_for_timeout(1500)
                assert bars.count() == 2, f"{bars.count()} store offer lines on a computer (2 expected)"
                auto = bars.nth(1).inner_text()
                q.set_viewport_size({"width": 390, "height": 844})
                q.reload(wait_until="domcontentloaded")
                q.wait_for_selector("#dealList .promobar", state="attached", timeout=30000)
                assert "homepage today" in auto and "Our check: 120 of the 400" in auto, f"a banner read off a homepage doesn't quote it + our check: {auto[:120]!r}"
                bars.first.locator("[data-promo]").evaluate("e => e.click()")
                q.wait_for_selector("#dealList .storebar", state="attached", timeout=20000)
                for _ in range(12):            # full-price cards come after the store's sale ones: open "Show more" until one shows
                    q.wait_for_timeout(2500)
                    if q.locator("#dealList .deal .promo").count():
                        break
                    for m in q.locator("#dealList button.more").all():
                        m.evaluate("e => e.click()")
                assert q.locator("#dealList .deal .promo").count(), "no full-price card at that store shows the offer note"
                stores = q.eval_on_selector_all("#dealList .deal .store", "els => els.map(e => e.textContent)")
                other = [s for s in stores if "Running Room" not in s]
                assert stores and not other, f"the store's view shows other stores: {other[:2]}"
                n = q.locator("#dealList .deal .promo").count()
                return f"offer line + {n} full-price cards with the note, {len(stores)} Running Room cards"
            finally:
                c.close()
        check("Store offer: line on top + note on that store's full-price cards")(store_offer, pg)

        def pop_searches():      # Oct 27, test 'popq': B = popular searches when you tap the empty search box
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.route("**/popular.json*", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps({"ca": ["Hoka", "Salomon"], "us": []})))
            c.add_init_script("try{localStorage.setItem('gf-nosignup','1');localStorage.setItem('gf-peek','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',"
                              "ships:'ca',country:'ca',groups:['shoes','tops','bottoms'],sizes:{shoes:{sizes:['11'],width:[]},tops:{sizes:['M']},"
                              "bottoms:{sizes:['M']}},brands:[],lang:'en'}))}catch(e){}")
            try:
                q = c.new_page()
                out = {}
                for arm in ("A", "B"):
                    q.goto(base + f"?exp=popq:{arm}", wait_until="domcontentloaded")
                    q.wait_for_selector("section.grp .deal", timeout=30000)
                    q.wait_for_timeout(800)
                    q.focus("#dSearch")
                    q.wait_for_timeout(400)
                    out[arm] = q.evaluate("(()=>{const b=document.getElementById('popq');return b&&!b.hidden?b.querySelectorAll('button').length:0})()")
                assert out["A"] == 0, "group A sees popular searches"
                assert out["B"] == 2, f"group B: {out['B']} popular searches (2 expected)"
                q.locator("#popq button", has_text="Hoka").click()
                q.wait_for_timeout(1200)
                assert q.input_value("#dSearch") == "Hoka", "tapping a popular search didn't search for it"
                assert q.evaluate("document.getElementById('popq').hidden"), "the popular box stayed open after a tap"
                names = q.eval_on_selector_all("#dealList .deal .name", "els => els.slice(0,6).map(e => e.textContent)")
                assert names and all("hoka" in n.lower() for n in names), f"tapping 'Hoka' shows other brands: {names[:2]}"
                return f"A none, B 2 chips; tapping 'Hoka' shows {len(names)}+ Hoka deals"
            finally:
                c.close()
        check("Popular searches under the search box (test popq)")(pop_searches, pg)

        def race_tracking():   # Oct 23 (Bastien: "a tracker to see how and if people are using the gear checklist")
            got = []

            def grab(route):
                try:
                    got.extend(e.get("d") or "" for e in json.loads(route.request.post_data or "{}").get("p_events", []))
                except Exception:
                    pass
                route.fulfill(status=200, content_type="application/json", body="null")
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.route("**/rest/v1/rpc/ana_track", grab)
            q = c.new_page()
            try:
                q.goto(base + "races/ultra-trail-harricana/?exp=kit:A", wait_until="load")
                q.wait_for_timeout(600)
                q.locator(".dists button").nth(1).click()
                q.locator(".gi:not([hidden]) input.have").first.check()
                q.wait_for_timeout(300)
                q.evaluate("document.dispatchEvent(new Event('visibilitychange'))")   # not enough on its own: wait for the 6 s send
                q.wait_for_timeout(7000)
                race = [d for d in got if d.startswith("race|")]
                for w in ("open", "dist", "have"):
                    assert any(d.split("|")[2] == w for d in race), f"the race page didn't send '{w}' ({race[:4]})"
                kit = [d for d in got if d.startswith("exp|kit|")]
                assert kit, "the race page didn't say its 'kit' test group"
                return f"{len(race)} race events sent ({', '.join(sorted({d.split('|')[2] for d in race}))}), {kit[0]}"
            finally:
                c.close()
        check("Race gear page: what visitors do is recorded")(race_tracking, pg)

        def letters():       # Oct 28 (Bastien: "I shouldn't have to see the y bleeding over. These details matter and should be caught in our scan"):
            # every kind of page at phone, tablet, laptop and wide-screen widths, every live test off (A) and on (B): no line of text
            # touching a box it doesn't belong to, no words cut off, nothing wider than the screen (tools/visual_check.py)
            prof = ("localStorage.setItem('gf-peek','1');localStorage.setItem('gf-nosignup','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',"
                    "terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms'],sizes:{shoes:{sizes:['11'],width:[]},tops:{sizes:['M']},"
                    "bottoms:{sizes:['M']}},brands:[],lang:'en'}))")
            allb = "localStorage.setItem('gf-exp',JSON.stringify({r100:'B',run1st:'B',cards2:'B',short:'B',popq:'B',kit:'B',alts:'B',namecard:'B',watchsheet:'B',welcome:'A',layout:'A'}))"
            paths = ["", "?lang=fr", "shoes/", "black-friday/", "running-shoes-sale/", "races/", "races/ultra-trail-harricana/", "about.html", "gifts-for-runners/"]
            if site_get("hikes/"):
                paths.append("hikes/")
            bad, seen, skipped = [], 0, 0
            for arm, extra in (("A", ""), ("B", allb)):
                for w, h in ((320, 640), (390, 844), (768, 1024), (1024, 768), (1366, 768), (1920, 1080)):
                    mob = w < 700
                    c = br.new_context(viewport={"width": w, "height": h}, is_mobile=mob, has_touch=mob, ignore_https_errors=INSECURE, locale="en-CA")
                    stub(c)
                    c.add_init_script("try{" + prof + ";" + extra + "}catch(e){}")
                    q = c.new_page()
                    try:
                        # the homepage at every width; other pages at a phone and a laptop (the night scan opens every page type nightly)
                        for path in ([""] + ([p_ for p_ in paths if p_] if w in (390, 1366) and arm == "A" else [])):
                            q.goto(base + path, wait_until="load")
                            q.wait_for_timeout(900 if path else 1800)
                            r = collisions(q)
                            if r and r[0].startswith("STYLES-MISSING"):
                                q.reload(wait_until="load")
                                q.wait_for_timeout(900)
                                r = collisions(q)
                            if r and r[0].startswith("STYLES-MISSING"):
                                skipped += 1
                                continue
                            seen += 1
                            bad += [f"{w}px /{path} ({arm}): {x}" for x in r]
                    finally:
                        c.close()
            assert not bad, f"{len(bad)} found: " + " | ".join(bad[:4])
            assert seen >= 2 * skipped, f"only {seen} page views measured, {skipped} had no stylesheet"
            return f"{seen} page views measured (6 widths, tests off and on; {skipped} skipped, stylesheet didn't load): no text touching anything, nothing cut off"
        check("Letters touch nothing: every page, phone to wide screen (headline vs search box, cut-off words)")(letters, pg)

        def name_card():       # Oct 28 (Bastien OK'd the preview): test 'namecard' B = the sign-up card names a real deal in your size
            out = []
            for a in ("B", "A"):
                c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                stub(c)
                q = c.new_page()
                try:
                    q.goto(base + f"?exp=namecard:{a}", wait_until="load")
                    q.wait_for_selector("#saveSizes", state="visible", timeout=30000)
                    q.click("#saveSizes")                       # a new visitor: welcome -> men's 11 / M
                    q.wait_for_selector("#shoeSizes button", state="visible")
                    q.click('#fit button[data-v="men"]')
                    q.locator("#shoeSizes button", has_text=re.compile(r"^11$")).first.click()
                    if q.locator("#moreSizes").is_visible():
                        q.click("#moreSizes")
                    q.locator("#clothSizes button", has_text=re.compile(r"^M$")).first.click()
                    q.click("#saveSizes")
                    q.wait_for_selector("section.grp .deal", timeout=20000)
                    q.wait_for_timeout(800)
                    if a == "A":
                        assert not q.locator(".namecard").count() and q.locator(".signup .perks").count(), "group A lost the usual 'Free with your email' card"
                        out.append("A: the usual card")
                        continue
                    nc = q.locator(".namecard")
                    assert nc.count(), "group B shows no named-deal card"
                    h = nc.locator("h3").inner_text()
                    k = q.get_attribute("#suForm", "data-nc") or ""
                    assert k and k.split("|")[0] in h.lower(), f"the card names '{h}' but would watch '{k}'"
                    names = [x.inner_text().lower() for x in q.locator("section.grp").first.locator(".rdc .name, .deal .name").all()]
                    assert any(k.split("|")[1][:12] in n_ for n_ in names), f"'{h}' isn't one of the Top deals on the page"
                    q.fill("#suEmail", "robot@example.com")
                    q.click(".namecard .primary")
                    q.wait_for_timeout(1200)
                    w = q.evaluate("Object.keys(JSON.parse(localStorage.getItem('gf-watch')||'{}'))")
                    assert k in w, "signing up on the card didn't watch the deal it names"
                    out.append(f"B: '{h}', watched on sign-up")
                finally:
                    c.close()
            return "; ".join(out)
        check("Sign-up card that names a deal (test namecard)")(name_card, pg)

        def watch_sheet():     # Oct 29 (Bastien: "ship both and test"): 'watchsheet' B = the email step after a Watch tap names the item;
            # and a watchlist with no email asks for one (it used to say "Confirm your email" to people who never gave one)
            out = []
            for a in ("B", "A"):
                c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                stub(c)
                q = c.new_page()
                try:
                    q.goto(base + f"?exp=watchsheet:{a}", wait_until="load")
                    q.wait_for_selector("#saveSizes", state="visible", timeout=30000)
                    q.click("#saveSizes")
                    q.wait_for_selector("#shoeSizes button", state="visible")
                    q.click('#fit button[data-v="men"]')
                    q.locator("#shoeSizes button", has_text=re.compile(r"^11$")).first.click()
                    q.click("#saveSizes")
                    q.wait_for_selector("section.grp .deal", timeout=20000)
                    q.wait_for_timeout(600)
                    h = q.locator("section.grp .heart").first
                    brand = h.locator("xpath=ancestor::*[contains(@class,'dw')][1]").locator(".brand").first.inner_text().replace("🍁", "").strip()
                    h.click()
                    q.wait_for_selector("#sheet", state="visible", timeout=5000)
                    title, btn = q.inner_text("#sheetTitle"), q.inner_text("#saveSizes")
                    if a == "B":
                        assert brand.lower() in title.lower() and "drops" in title.lower(), f"group B's email step says '{title}' after watching a {brand} item"
                        assert "show my deals" not in btn.lower(), f"group B's button still says '{btn}'"
                    else:
                        assert "where should we send" in title.lower(), f"group A's email step changed: '{title}'"
                    q.click("#closeSheet")
                    q.wait_for_timeout(400)
                    q.click("#openWatch")
                    q.wait_for_timeout(800)
                    lede = q.inner_text("#lede")
                    assert "confirm your email" not in lede.lower(), f"the watchlist tells someone who never gave an email: '{lede}'"
                    assert q.locator("#watchEmail").is_visible(), "the watchlist has no button to add an email"
                    q.click("#watchEmail")
                    q.wait_for_selector("#sheet", state="visible", timeout=5000)
                    out.append(f"{a}: '{title}'")
                finally:
                    c.close()
            return "; ".join(out) + "; watchlist asks for the email"
        check("Email step after a Watch tap (test watchsheet) + watchlist email ask")(watch_sheet, pg)

        def instant_member():  # Oct 29 (Bastien: "Yes on each"): single opt-in = a sign-up is a member at once; Google first on the card
            KEY = "11111111-2222-4333-8444-555555555555"
            fake_gsi = ("window.google={accounts:{id:{initialize:function(){},prompt:function(){},"
                        "renderButton:function(el){el.innerHTML='<div role=\"button\" class=\"fakeg\">Continue with Google</div>'}}}};")
            out = []
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.route("**/gsi/client*", lambda r: r.fulfill(status=200, content_type="application/javascript", body=fake_gsi))   # last route wins
            c.route("**/rest/v1/rpc/subscribe", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps("k:" + KEY)))
            q = c.new_page()
            try:
                q.goto(base, wait_until="load")
                q.wait_for_selector("#saveSizes", state="visible", timeout=30000)
                q.click("#saveSizes")
                q.wait_for_selector("#shoeSizes button", state="visible")
                q.click('#fit button[data-v="men"]')
                q.locator("#shoeSizes button", has_text=re.compile(r"^11$")).first.click()
                q.click("#saveSizes")
                q.wait_for_selector("section.grp .deal", timeout=20000)
                q.wait_for_selector(".signup #suForm", timeout=8000)
                q.wait_for_timeout(600)
                order = q.evaluate("""() => {const c = document.querySelector('.signup'), g = c && c.querySelector('.gcard'), f = c && c.querySelector('#suForm');
                    return g && f ? [!!(g.compareDocumentPosition(f) & Node.DOCUMENT_POSITION_FOLLOWING), (g.querySelector('.fakeg') || {}).textContent || ''] : null}""")
                assert order, "the sign-up card has no Google button"
                assert order[0], "the Google button isn't above the email box"
                assert "google" in order[1].lower(), "the Google button wasn't drawn on the card"
                out.append("Google first on the card")
                q.fill("#suEmail", "robot@example.com")
                q.locator(".signup #suForm button").first.click()
                q.wait_for_timeout(1200)
                sub = q.evaluate("JSON.parse(localStorage.getItem('gf-sub')||'null')")
                assert sub and sub.get("active") and sub.get("key") == KEY, f"the sign-up didn't make this device a member: {sub}"
                note = q.inner_text("#notice") if q.locator("#notice").is_visible() else ""
                assert "you're in" in note.lower(), f"no 'You're in' after signing up (notice: {note[:80]!r})"
                assert not q.locator(".signup #suForm").count(), "the sign-up card still asks for an email after joining"
                out.append("card sign-up = member at once")
                reg = site_json("shoes/pages.json")
                slug = next((k for k, v in list(reg.items())[:40] if not (isinstance(v, dict) and v.get("to"))
                             and 'id="alertBox"' in (site_get(f"shoes/{k}/") or "")), None)
                if slug:
                    q.evaluate("localStorage.removeItem('gf-sub')")
                    q.goto(base + f"shoes/{slug}/", wait_until="domcontentloaded")
                    q.wait_for_selector("#alertBox form", timeout=8000)
                    q.fill("#alertBox input", "robot@example.com")
                    q.click("#alertBox button")
                    q.wait_for_timeout(1000)
                    msg = q.inner_text("#alertBox .msg")
                    sub = q.evaluate("JSON.parse(localStorage.getItem('gf-sub')||'null')")
                    if "pick" not in msg.lower() and "size" not in msg.lower()[:12]:
                        assert "you're in" in msg.lower(), f"the shoe page box says {msg!r} after an instant sign-up"
                        assert sub and sub.get("active"), "the shoe page sign-up didn't make this device a member"
                        out.append("shoe page box too")
            finally:
                c.close()
            return "; ".join(out)
        check("Sign-up = member at once (single opt-in) + Google first")(instant_member, pg)

        def visit_resend():    # Oct 27 (Bastien: "Are we tracking numbers correctly?"): 28% of first visits had lost their first batch
            got, n = [], [0]

            def grab(route):
                n[0] += 1
                if n[0] == 1:
                    return route.abort()          # the first send fails, like on those phones
                try:
                    got.extend(e.get("k") for e in json.loads(route.request.post_data or "{}").get("p_events", []))
                except Exception:
                    pass
                route.fulfill(status=200, content_type="application/json", body="null")
            out = []
            hide = "Object.defineProperty(document,'visibilityState',{get:()=>'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'))"
            for path, poke in (("", hide), ("shoes/", hide)):   # leaving the tab sends the next batch
                got.clear()
                n[0] = 0
                c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                stub(c)
                c.route("**/rest/v1/rpc/ana_track", grab)
                q = c.new_page()
                try:
                    q.goto(base + path, wait_until="load")
                    q.wait_for_timeout(7000)
                    q.evaluate(poke)
                    q.wait_for_timeout(7000)
                    assert n[0] >= 2, f"/{path}: no second send ({n[0]})"
                    assert "visit" in got, f"/{path}: the visit was lost with the first send ({got[:6]})"
                    assert got.count("visit") == 1, f"/{path}: the visit was sent {got.count('visit')} times"
                    out.append(f"/{path} ok")
                finally:
                    c.close()
            return "; ".join(out)
        check("Analytics: a first visit lost in the first send is sent again")(visit_resend, pg)

        def kit_test():        # Oct 27 (Bastien: "Yes race kit"): test 'kit' B = every gear line folded to one row; A = as before
            out = []
            for path in ("races/ultra-trail-harricana/", "races/sinister-7/"):   # trail gear lists share the same layout code (RP.KITB)
                for a in ("A", "B"):
                    c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
                    stub(c)
                    q = c.new_page()
                    try:
                        q.goto(base + path + f"?exp=kit:{a}", wait_until="load")
                        q.wait_for_timeout(700)
                        on = q.evaluate("document.documentElement.classList.contains('kitb')")
                        assert on == (a == "B"), f"{path} group {a}: folded layout {'missing' if a == 'B' else 'showing'}"
                        if a == "B":
                            li = q.locator(".gi:not(.shoe):not(.mini):not([hidden])").first
                            assert not li.locator(".dl").first.is_visible(), f"{path}: a folded line still shows its picks"
                            assert li.locator(".kb").count(), f"{path}: no 'From $X' line on a folded row"
                            li.locator(".hd h3").click()
                            q.wait_for_timeout(200)
                            assert "kopen" in (li.get_attribute("class") or ""), f"{path}: tapping a row doesn't open it"
                            h = q.evaluate("document.documentElement.scrollHeight")
                            out.append(f"{path} B {h}px")
                        else:
                            out.append(f"{path} A {q.evaluate('document.documentElement.scrollHeight')}px")
                    finally:
                        c.close()
            return "; ".join(out)
        check("Race kit layout test (kit): A as before, B folded rows")(kit_test, pg)

        def one_look():         # Oct 22 (Bastien: "Only the homepage is formatted in the way we want. All others are dark and still the
            # same"): on a phone set to dark mode, every page is light with the charcoal header, like the homepage, and fits the phone
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE,
                               locale="en-CA", color_scheme="dark")
            stub(c)
            q = c.new_page()
            reg = site_json("shoes/pages.json") or {}
            slug = next((k for k, v in reg.items() if isinstance(v, dict) and not v.get("to")), None)
            bad = []
            for u in [f"shoes/{slug}/", f"chaussures/{slug}/", "running-shoes-sale/", "races/", "black-friday/", "about.html", "privacy.html"]:
                q.goto(base + u, wait_until="domcontentloaded")
                q.wait_for_timeout(400)
                r = q.evaluate("""() => {const lum = c => {const m = c.match(/\\d+(\\.\\d+)?/g); return m ? (+m[0] + +m[1] + +m[2]) / 3 : 0};
                    const top = document.querySelector('.top');
                    return {page: lum(getComputedStyle(document.body).backgroundColor), head: top ? lum(getComputedStyle(top).backgroundColor) : null,
                            wide: document.documentElement.scrollWidth}}""")
                if r["page"] < 200:
                    bad.append(f"{u} has a dark page")
                if r["head"] is not None and r["head"] > 80:
                    bad.append(f"{u} has a light header")
                if r["wide"] > 391:
                    bad.append(f"{u} is {r['wide'] - 390}px wider than the phone")
            # Oct 23 (Bastien's screenshot): a page-wide rule squeezed the pick names inside the TOR bag fold to a few letters a line;
            # every race page with a weather/bag fold: open it, each pick's name keeps a readable width
            for slug, kit in (("tor-des-geants", "bag"), ("borealys-mont-tremblant", "bad"), ("ultra-trail-australia", "bad")):
                q.goto(base + f"races/{slug}/", wait_until="domcontentloaded")
                q.wait_for_timeout(400)
                w = q.evaluate("""() => {document.querySelectorAll('li.kit details').forEach(d => d.open = true);
                    const n = [...document.querySelectorAll('li.kit .dl .nm, .gl > li .dl .nm')].filter(x => x.offsetParent).map(x => x.getBoundingClientRect().width);
                    return n.length ? Math.round(Math.min(...n)) : null}""")
                if w is not None and w < 90:
                    bad.append(f"races/{slug}/: product names squeezed to {w}px")
            c.close()
            assert not bad, "; ".join(bad)
            return "shoe (EN/FR), sale list, races, Black Friday, About, Privacy: light pages, charcoal header, fit the phone"
        check("Every page has the homepage's look (phone in dark mode)")(one_look, pg)

        def run1st():           # Oct 22, test 'run1st' (B): running gear leads Today's top deals; one store fills at most 2 of the first 12
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)   # its own window: the next checks expect the shared page to stay where it was
            c.add_init_script("""try{localStorage.setItem('gf-peek','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'women',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms','bras','socks','gloves','headwear','packs','gear','watches','nutrition'],sizes:{shoes:{sizes:['8'],width:[]},tops:{sizes:['S']},bottoms:{sizes:['S']}},brands:[],lang:'en'}))}catch(e){}""")
            q = c.new_page()
            q.goto(base + "?exp=run1st:B", wait_until="domcontentloaded")
            q.wait_for_selector("#grp-__sale .deal", timeout=20000)
            q.wait_for_timeout(600)
            rows = q.evaluate("""() => [...document.querySelectorAll('#grp-__sale .dw')].slice(0, 12).map(w =>
                [w.querySelector('.store') ? w.querySelector('.store').textContent.trim() : '', (w.querySelector('.name') || {}).textContent || ''])""")
            c.close()
            per = Counter(r[0] for r in rows)
            assert rows, "no Top deals with test 'run1st' on"
            assert max(per.values()) <= 2, f"one store fills {max(per.values())} of the first {len(rows)} top deals: {per.most_common(1)}"
            gym = [n for _, n in rows[:6] if re.search(r"\b(training|hiit|studio|yoga|pilates|lounge)\b", n, re.I)]
            assert not gym, f"gym/lifestyle in the first 6 with running gear first on: {gym}"
            return f"{len(rows)} top deals from {len(per)} stores, max {max(per.values())} per store"
        check("Test 'run1st': running gear first, max 2 per store")(run1st, pg)

        def every_button():     # Oct 22 (Bastien: "The view all brands button doesn't lead anywhere. How did you miss this"): every button and
            # link on the homepage's own sections is pressed once on a phone, and each must give ITS result (a first version only checked that
            # "something changed" and passed the broken button, because the page changes on its own as it loads)
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-peek','1');localStorage.setItem('gf-nosignup','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms','socks','gloves','headwear','packs','gear','watches','nutrition'],sizes:{shoes:{sizes:['10'],width:[]},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}))}catch(e){}""")
            q = c.new_page()
            q.route(re.compile(r"^https?://(?!127\.0\.0\.1|localhost)"), lambda r: r.abort() if r.request.resource_type == "document" else r.continue_())
            first_more = "section.grp:not(#grp-__sale):not(.new) button.more"
            targets = [   # (name, what to press, what must be true after, a number that must grow)
                ("View all brands", "[data-rdbrands]", "() => document.querySelectorAll('.rdball .ba').length > 8", None),
                ("a brand tile", ".rdbrands .bt", "() => new Set([...document.querySelectorAll('#dealList .rdc .brand')].map(x => x.textContent)).size === 1", None),
                ("a category circle", ".rdtile", "() => !!document.querySelector('.rdcatbar')", None),
                ("the size button", "#rdQS", "() => { const s = document.getElementById('sheet'); return !!s && !s.classList.contains('hidden') }", None),
                ("Filters", "#hFilt", "() => !document.getElementById('rdFs').hidden", None),
                ("the menu", "#menuBtn", "() => { const m = document.getElementById('menu'); return !!m && !m.hidden }", None),
                ("View all deals", "#grp-__sale .rdmore", None, "() => document.querySelectorAll('#grp-__sale .rdc').length"),
                ("Show more", first_more, None, "() => document.querySelectorAll('section.grp:not(#grp-__sale):not(.new) .rdc').length")]
            dead, done = [], []
            for name, sel, want, grow in targets:
                q.goto(base, wait_until="domcontentloaded")
                q.wait_for_selector("#dealList .rdc", timeout=30000)
                q.wait_for_timeout(600)
                el = q.locator(sel).first
                if not el.count() or not el.is_visible():
                    continue
                el.scroll_into_view_if_needed()
                n0 = q.evaluate(grow) if grow else 0
                if want == "TAB":   # a link out: it must point to a real page and open in a new tab (a click can land on the sticky header)
                    ok = el.evaluate("a => /^https?:/.test(a.href) && !/^https?:\\/\\/[^\\/]+\\/?#?$/.test(a.href) && a.target === '_blank'")
                    (done if ok else dead).append(name)
                    continue
                el.click()
                q.wait_for_timeout(900)
                ok = q.evaluate(want) if want else q.evaluate(grow) > n0
                (done if ok else dead).append(name)
            # Oct 23: the computer header's buttons too (the country button opened the menu and the same click closed it)
            q.set_viewport_size({"width": 1366, "height": 768})
            for name, sel, want in [("the header's country button", "#rdCtry", "() => !document.getElementById('menu').hidden"),
                                    ("the header's My sizes", "#rdMy", "() => { const s = document.getElementById('sheet'); return !!s && !s.classList.contains('hidden') }")]:
                q.goto(base, wait_until="domcontentloaded")
                q.wait_for_selector("#dealList .rdc", timeout=30000)
                q.wait_for_timeout(600)
                el = q.locator(sel).first
                if not el.count() or not el.is_visible():
                    continue
                el.click()
                q.wait_for_timeout(700)
                (done if q.evaluate(want) else dead).append(name)
            c.close()
            assert not dead, f"pressing these doesn't do what it says: {', '.join(dead)}"
            return f"{len(done)} buttons each do their job: {', '.join(done)}"
        check("Homepage: every button does something")(every_button, pg)

        def brands_all():       # Oct 22: "View all brands" opens an A-Z list; finding and tapping a brand shows only its deals
            c = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c)
            c.add_init_script("""try{localStorage.setItem('gf-peek','1');localStorage.setItem('gf-nosignup','1');localStorage.setItem('rd-profile',JSON.stringify({gender:'men',terrain:'both',ships:'ca',country:'ca',groups:['shoes','tops','bottoms','socks','gloves','headwear','packs','gear','watches','nutrition'],sizes:{shoes:{sizes:['10'],width:[]},tops:{sizes:['M']},bottoms:{sizes:['M']}},brands:[],lang:'en'}))}catch(e){}""")
            q = c.new_page()
            q.goto(base, wait_until="domcontentloaded")
            q.wait_for_selector(".rdbrands", timeout=30000)
            q.click("[data-rdbrands]")
            q.wait_for_selector(".rdball .ba", timeout=5000)
            names = q.eval_on_selector_all(".rdball .ba span", "e => e.map(x => x.textContent)")
            pick = names[len(names) // 2]
            q.fill("#rdBQ", pick)
            q.wait_for_timeout(300)
            shown = q.eval_on_selector_all(".rdball .ba:not([hidden]) span", "e => e.map(x => x.textContent)")
            q.locator(".rdball .ba:not([hidden])").first.click()
            q.wait_for_timeout(1200)
            got = q.eval_on_selector_all("#dealList .rdc .brand", "e => [...new Set(e.map(x => x.textContent))]")
            c.close()
            assert len(names) > 8 and all(n.strip() for n in names), f"the brand list has {len(names)} names (or an empty one)"
            assert pick in shown, f"finding '{pick}' doesn't show it"
            assert got and all(g == shown[0] for g in got), f"tapping {shown[0]} shows deals from {got[:4]}"
            return f"{len(names)} brands A-Z; '{pick}' found and tapped: only its deals"
        check("Shop by brand: View all brands, find, tap")(brands_all, pg)

        def shoe_backbar():     # Oct 11: back on a shoe page from a store, a non-member gets "Didn't buy it?" + email
            pg.evaluate("localStorage.removeItem('gf-sub');localStorage.removeItem('gf-backno');sessionStorage.removeItem('gf-backshown')")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector("a[data-store]", timeout=8000)
            pg.evaluate("var a=document.querySelector('a[data-store]');a.addEventListener('click',function(e){e.preventDefault()},{once:true});a.click()")
            pg.wait_for_selector(".backbar form", timeout=9000)
            if pg.locator(".backbar .bsel").count():
                opts = pg.eval_on_selector_all(".backbar .bsel option", "e=>e.map(o=>o.value).filter(Boolean)")
                pg.select_option(".backbar .bsel", opts[0])
            pg.fill(".backbar input", "robot@example.com")
            pg.click(".backbar form button")
            settle(pg, 900)
            msg = pg.inner_text("#alertBox .msg")
            assert "robot@example.com" in msg, f"the come-back bar didn't sign up ({msg!r})"
            pg.evaluate("localStorage.removeItem('gf-sub')")
            return "shown after a store click, signed up"
        check("Shoe page: 'Didn't buy it?' bar")(shoe_backbar, pg)

        def bf_quick():         # Oct 11: Black Friday page: fit + shoe size + email, right on the page
            pg.evaluate("localStorage.removeItem('gf-sub')")
            keep = pg.evaluate("() => [localStorage.getItem('rd-profile'), localStorage.getItem('gf-shoe-size')]")   # starts with no size saved
            pg.evaluate("() => {localStorage.removeItem('rd-profile'); localStorage.removeItem('gf-shoe-size')}")
            pg.goto(base + "black-friday/", wait_until="domcontentloaded")
            pg.wait_for_selector("#qsBox form", timeout=8000)
            pg.fill("#qsBox input", "robot@example.com")
            pg.click("#qsBox button")
            settle(pg, 300)
            assert pg.inner_text("#qsBox .msg").strip(), "no size picked: the box says nothing"
            pg.select_option("#qsBox .qsg", "men")     # an earlier check may have left a women's size picked
            pg.select_option("#qsBox .qss", "10")
            pg.click("#qsBox button")
            settle(pg, 900)
            msg = pg.inner_text("#qsBox .msg")
            assert "robot@example.com" in msg, f"the Black Friday box didn't sign up ({msg!r})"
            pg.evaluate("localStorage.removeItem('gf-sub')")
            pg.evaluate("k => {if (k[0]) localStorage.setItem('rd-profile', k[0]); if (k[1]) localStorage.setItem('gf-shoe-size', k[1])}", keep)
            return "asked for a size, then signed up"
        check("Black Friday page: sign up right here")(bf_quick, pg)

        def race_page():        # Oct 21: race gear lists: hub, size, 10 picks per item, Watch hearts in place, shoe + size picker, French
            pg.evaluate("(function(){var o={};try{o=JSON.parse(localStorage.getItem('gf-exp')||'{}')||{}}catch(e){}o.kit='A';localStorage.setItem('gf-exp',JSON.stringify(o))})()")   # test 'kit': this check reads the unfolded list
            pg.evaluate("['gf-watch','gf-race-size','gf-shoe-size','gf-sub'].forEach(function(k){localStorage.removeItem(k)})")
            pg.goto(base + "races/", wait_until="domcontentloaded")
            pg.wait_for_selector("ul.cards a", timeout=8000)
            pg.click("ul.cards a")
            pg.wait_for_selector("#gl .gi", timeout=8000)
            pg.click('#rsize [data-g="men"]')
            pg.click('#rsize button[data-s="M"]')
            settle(pg, 300)
            n = pg.evaluate("[...document.querySelectorAll('#gl .gi:not(.mini):not(.shoe):not([hidden])')].map(l=>l.querySelectorAll('.dl li').length)")
            assert n and sum(1 for x in n if x >= 3) >= len(n) - 2, f"items with fewer than 3 picks in men's M: {n}"
            b = "#gl .gi:not(.mini):not(.shoe):not([hidden]) .dl li:first-child .wt"
            pg.click(b)
            settle(pg, 200)
            assert pg.get_attribute(b, "aria-pressed") == "true", "Watch didn't heart the pick"
            assert pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('gf-watch')||'{}')).length") == 1, "the heart isn't in the watchlist"
            assert "/races/" in pg.url and "watch=" not in pg.url, f"Watch left the race page ({pg.url})"
            pg.click(b)
            settle(pg, 200)
            assert pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('gf-watch')||'{}')).length") == 0, "a second tap didn't remove it"
            # Oct 28 (Bastien: "when a race item is expanded to the 10 items there's no way to shrink it back"): See all, then Show fewer
            li = pg.locator("#gl .gi:not(.mini):not(.shoe):not([hidden])").filter(has=pg.locator(".mored:not([hidden])")).first
            if li.count():
                li.locator(".mored").click()
                settle(pg, 200)
                shown = li.evaluate("l => [...l.querySelectorAll('.dl li')].filter(x => x.offsetParent).length")
                assert shown > 3, f"'See all' shows only {shown} picks"
                li.locator(".lessd").click()
                settle(pg, 200)
                back = li.evaluate("l => [...l.querySelectorAll('.dl li')].filter(x => x.offsetParent).length")
                assert back == 3, f"'Show fewer' left {back} picks showing"
                assert li.locator(".mored").is_visible(), "'See all' didn't come back after 'Show fewer'"
            # Oct 29 (Bastien): each item links to its whole category on the homepage ("See more jackets on sale →")
            cl = pg.locator("#gl .gi:not([hidden]) .catall a").first
            assert cl.count(), "no 'See more … on sale' link on any race item"
            href = cl.get_attribute("href")
            assert "cat=" in href, f"category link without a category: {href}"
            race_url = pg.url
            c2 = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-CA")
            stub(c2)
            q2 = c2.new_page()
            try:
                q2.goto(base + href.lstrip("/"), wait_until="domcontentloaded")
                q2.wait_for_selector("section.grp .deal", timeout=30000)
                q2.wait_for_timeout(800)
                g = re.search(r"cat=(\w+)", href).group(1)
                secs = q2.evaluate("[...document.querySelectorAll('#dealList section.grp')].map(x => x.id || x.dataset.g || '')")
                shown = q2.evaluate("(() => { try { return (JSON.parse(localStorage.getItem('rd-profile')||'{}').groups)||null } catch(e) { return null } })()")
                cats = q2.evaluate("[...document.querySelectorAll('#dealList section.grp h2')].map(h => h.innerText.split('\\n')[0])")
                assert len(cats) >= 1 and not q2.locator("#welcome:not(.hidden), .sheet:not(.hidden) #saveSizes:visible").count(), f"the category link didn't open the deals ({cats[:3]})"
                assert len(cats) <= 2, f"the category link shows several categories: {cats[:4]} (wanted only {g})"
            finally:
                c2.close()
            pg.goto(race_url, wait_until="domcontentloaded")
            pg.wait_for_selector("#gl .gi", timeout=8000)
            pg.select_option("#shoeSz", "10")
            pg.fill("#shoeQ", "speedgoat")
            settle(pg, 200)
            sug = pg.eval_on_selector_all("#shoeSug button", "e=>e.map(x=>x.textContent)")
            assert sug, "the shoe box suggested nothing for 'speedgoat'"
            pg.click("#shoeSug button")
            settle(pg, 200)
            mine = pg.inner_text("#shoeMine")
            assert "10" in mine, f"the picked shoe doesn't say its size-10 price ({mine[:80]!r})"
            pg.goto(base + "courses/", wait_until="domcontentloaded")
            pg.click("ul.cards a")
            pg.wait_for_selector("#gl .gi", timeout=8000)
            assert "Matériel obligatoire" in pg.inner_text("h1"), "the French race page isn't in French"
            pg.evaluate("['gf-watch','gf-race-size','gf-shoe-size'].forEach(function(k){localStorage.removeItem(k)})")
            return f"{len(n)} items with picks, heart + shoe picker work, FR ok"
        check("Race gear page: picks in your size, Watch hearts in place, shoe + size")(race_page, pg)

        def hub_search():       # Oct 27 (Bastien: "a search function for the race kits and the hiking planner")
            out = []
            for path in ("races/", "hikes/"):
                if not site_get(path):
                    continue
                pg.goto(base + path, wait_until="domcontentloaded")
                pg.wait_for_selector("#hubQ", timeout=8000)
                first = pg.eval_on_selector("ul.cards li b", "e => e.textContent")
                word = max(first.split(), key=len)
                pg.fill("#hubQ", word.lower())
                settle(pg, 300)
                shown = pg.eval_on_selector_all("ul.cards li", "els => els.filter(l => l.offsetParent).map(l => l.querySelector('b').textContent)")
                assert first in shown and len(shown) < pg.eval_on_selector_all("ul.cards li", "e => e.length"), f"{path}: searching '{word}' shows {shown[:3]}"
                if path == "hikes/":   # Oct 29: trails grouped by province/state, folded; a search opens the groups it finds
                    groups = pg.eval_on_selector_all("details.rg", "e => e.length")
                    assert groups >= 3, f"hikes/: only {groups} province/state groups"
                    assert pg.evaluate("[...document.querySelectorAll('details.rg')].every(d => d.hidden || d.open)"), "hikes/: a group with a match stayed closed"
                pg.fill("#hubQ", "zzqx")
                settle(pg, 300)
                assert pg.evaluate("!document.querySelector('.hnone').hidden"), f"{path}: no 'nothing matches' line"
                out.append(f"{path} '{word}' -> {len(shown)}")
            return "; ".join(out)
        check("Race and trail hubs: search")(hub_search, pg)

        def bf_live():          # Oct 27: Black Friday deal check, live (scraper/bf_live.py); its own check in check.py reads the history
            h = site_get("black-friday/live/")
            if not h:
                return "not built here (needs the price history)"
            pg.goto(base + "black-friday/live/", wait_until="domcontentloaded")
            n = pg.eval_on_selector_all(".bfl li", "e => e.length")
            assert n >= 3, f"only {n} items on the deal check"
            w = pg.evaluate("document.documentElement.scrollWidth")
            assert w <= 400, f"the deal check is wider than the phone ({w}px)"
            pg.goto(base + "black-friday/", wait_until="domcontentloaded")
            assert pg.locator('a[href="/black-friday/live/"]').count(), "the Black Friday page doesn't link the deal check"
            return f"{n} items, linked from /black-friday/"
        check("Black Friday deal check page")(bf_live, pg)

        def gifts():            # Oct 28: gifts for runners (scraper/gift_pages.py): three budgets, sale + full-price picks, Watch goes to the homepage
            if not site_get("gifts-for-runners/"):
                return "not built here"
            pg.goto(base + "gifts-for-runners/", wait_until="domcontentloaded")
            n = pg.eval_on_selector_all(".gf", "e => e.length")
            assert n >= 18, f"only {n} gifts on the page"
            prices = pg.eval_on_selector_all(".gf .pr", "e => e.map(x => parseFloat(x.textContent.replace(/[^0-9.]/g, ' ').trim().split(' ')[0]))")
            assert all(p <= 100 for p in prices if p == p), f"a gift over $100: {max(prices)}"
            w = pg.locator(".gf a.wt").first
            href = w.get_attribute("href") or ""
            assert "watch=" in href, f"'Watch the price' doesn't watch: {href}"
            wide = pg.evaluate("document.documentElement.scrollWidth")
            assert wide <= 400, f"the gift page is wider than the phone ({wide}px)"
            pg.goto(base + "cadeaux-coureurs/", wait_until="domcontentloaded")
            assert "Cadeaux pour coureurs" in pg.inner_text("h1"), "the French gift page isn't in French"
            pg.goto(base + "black-friday/", wait_until="domcontentloaded")
            assert pg.locator('a[href="/gifts-for-runners/"]').count(), "the Black Friday page doesn't link the gift page"
            us = ""
            if site_get("us/gifts-for-runners/"):   # Oct 30: USA side (US stores, US$), linked from /us/black-friday/
                pg.goto(base + "us/gifts-for-runners/", wait_until="domcontentloaded")
                nu = pg.eval_on_selector_all(".gf", "e => e.length")
                assert nu >= 18, f"only {nu} gifts on the US page"
                assert "c=us" in (pg.locator(".gf a.wt").first.get_attribute("href") or ""), "the US page's Watch link doesn't open the USA side"
                wide = pg.evaluate("document.documentElement.scrollWidth")
                assert wide <= 400, f"the US gift page is wider than the phone ({wide}px)"
                pg.goto(base + "us/black-friday/", wait_until="domcontentloaded")
                assert pg.locator('a[href="/us/gifts-for-runners/"]').count(), "the US Black Friday page doesn't link the US gift page"
                us = f", USA {nu} gifts"
            return f"{n} gifts, Watch links work, FR ok, linked from /black-friday/{us}"
        check("Gift page: three budgets, Watch the price, French, USA")(gifts, pg)
        ctx2.close()

        # an American visitor (Oct 6, 2026): a US time zone opens the USA side; the switch goes back to Canada
        us_ready = site_get("sale-us.json") is not None and sum(
            1 for d in site_json("sale-us.json")["items"] if d["g"] == "shoes") >= 300   # USA side has real data
        if us_ready:
            ctx3 = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, ignore_https_errors=INSECURE, locale="en-US",
                                  timezone_id="America/Chicago")
            stub(ctx3)
            pu = ctx3.new_page()
            pu.on("pageerror", lambda e: errors.append(str(e)))
            pu.set_default_timeout(15000)

            def usa():
                pu.goto(base, wait_until="domcontentloaded")
                pu.wait_for_selector("#wDeals .wdeal", state="visible", timeout=30000)
                assert pu.get_attribute('#welcomePart [data-ctry="us"]', "aria-pressed") == "true", "a US time zone didn't pick USA"
                assert "across the US" in pu.inner_text("#sheet"), "the welcome text still says Canada"
                pu.click("#wBrowseB")
                pu.wait_for_selector("section.grp .deal", timeout=20000)
                cs = cards(pu)
                assert len(cs) >= 20, f"the USA side shows only {len(cs)} deals"
                lines = pu.eval_on_selector_all("section.grp .deal .store", "e => e.map(x => x.textContent)")
                bad = [x for x in lines if "ships from the US" in x]
                assert not bad, f"US stores are labelled as shipping from abroad ({bad[0]})"
                assert "USD" in pu.inner_text("section.grp:not(.new)"), "prices on the USA side aren't in US dollars"
                if pu.locator(".seo-today:not(.seo-hike) .seo-us").count():          # the bottom block: the US copy, not "...in Canada"
                    assert pu.locator(".seo-today:not(.seo-hike) .seo-us").is_visible() and not pu.locator(".seo-today:not(.seo-hike) .seo-en").is_visible(), \
                        "the bottom of the page still shows Canadian shoe prices on the USA side"
                if site_get("us/shoes/pages.json") is not None:          # a US card's "All sizes & stores" opens the US shoe page
                    lk = pu.locator("section.grp a.cmp")
                    if lk.count():
                        href = lk.first.get_attribute("href")
                        assert href.startswith("us/shoes/"), f"a US card links to the Canadian shoe page ({href})"
                n_us = pu.inner_text("#lede")
                pu.click("#menuBtn")
                pu.click('#menu [data-ctry="ca"]')
                pu.wait_for_function("document.querySelector('#lede') && document.querySelector('#lede').textContent !== " + json.dumps(n_us), timeout=20000)
                pu.wait_for_selector("section.grp .deal", timeout=20000)
                assert "CAD" in pu.inner_text("section.grp:not(.new)"), "switching to Canada didn't switch to Canadian dollars"
                return f"{len(cs)} deals in USD, then Canada"
            check("USA side (US time zone) and back to Canada")(usa, pu)

            def us_pages():
                out = []
                for path, needs in [("us/shoes/", r"\$\s?\d|−\d+\s?%"), ("us/running-shoes-sale/", r"\$\s?\d"), ("us/black-friday/", r"Black Friday")]:
                    r = pu.goto(base + path, wait_until="domcontentloaded")
                    assert r and r.status == 200, f"{path} doesn't open"
                    body = pu.inner_text("body")
                    assert re.search(needs, body), f"{path} opens but looks empty"
                    assert "Canada" not in pu.title(), f"{path} still says Canada in its title"
                    out.append(path)
                return f"{len(out)} pages"
            if len(site_json("us/shoes/pages.json") or {}) >= 20:
                check("US shoe pages")(us_pages, pu)
            ctx3.close()

        br.close()
    return errors


# ---------- store links ----------
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-CA,en;q=0.9"}


def store_links():
    """Two of today's sale items per store, opened once each (an ordinary page view, like a shopper's click)."""
    items = site_json("sale.json")["items"]
    by = defaultdict(list)
    for d in items:
        for o in d.get("of", []):
            u = o.get("u") if isinstance(o, dict) else (o[0] if isinstance(o, list) else o)
            if isinstance(u, str) and u.startswith("http"):
                by[urlparse(u).netloc.removeprefix("www.")].append(u)
    random.seed(datetime.now().strftime("%Y%m%d"))
    picks = {st: random.sample(us, min(2, len(us))) for st, us in by.items()}

    def get(u):
        try:
            r = requests.get(u, headers=UA, timeout=25, allow_redirects=True, stream=True)
            r.close()
            return r.status_code
        except Exception:
            return None
    flat = [(st, u) for st, us in picks.items() for u in us]
    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda x: get(x[1]), flat))
    res = defaultdict(list)
    for (st, u), c in zip(flat, codes):
        res[st].append((u, c))
    broken = {st: [u for u, c in v] for st, v in res.items() if all(c in (404, 410) for _, c in v)}
    unsure = sorted(st for st, v in res.items() if st not in broken and not any(c and c < 400 for _, c in v))
    ok = len(res) - len(broken) - len(unsure)
    return broken, unsure, ok, len(res)


def main():
    t0 = time.time()
    per, accented = expected()
    base = sys.argv[1].rstrip("/") + "/" if LIVE else serve()
    print(f"Site test on {base}" + ("" if LIVE else f" ({SITE})"))
    errors = site_flow(base, per, accented)
    real = [e for e in errors if "ResizeObserver" not in e]
    results.append({"name": "No script errors", "ok": not real, "critical": False,
                    **({"why": f"{len(real)} script error(s) while clicking around, first: {real[0][:300]}"} if real else {})})
    print(("  ok   " if not real else "  FAIL ") + "No script errors" + (f": {real[0][:200]}" if real else ""))

    broken = unsure = []
    try:
        broken, unsure, ok, n = store_links()
        for st, us in sorted(broken.items()):
            results.append({"name": f"Store links: {st}", "ok": False, "critical": False,
                            "why": f"deal links to {st} lead to 'page not found' (e.g. {us[0]})"})
        print(f"  store links: {ok} of {n} stores open, {len(broken)} broken, {len(unsure)} couldn't be checked "
              f"(blocked or busy: {', '.join(unsure) or 'none'})")
        links = {"stores": n, "ok": ok, "broken": sorted(broken), "unsure": unsure}
    except Exception as e:
        links = {"error": str(e)[:200]}
        print(f"  store links skipped: {e}")

    fails = [r for r in results if not r["ok"]]
    OUT.write_text(json.dumps({"ran": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seconds": round(time.time() - t0),
                               "passed": sum(r["ok"] for r in results), "failed": len(fails),
                               "critical": [r["name"] for r in fails if r["critical"]], "checks": results, "links": links}, indent=1))
    print(f"\n{sum(r['ok'] for r in results)} passed, {len(fails)} failed"
          + (f" ({len([r for r in fails if r['critical']])} critical)" if fails else "") + f" in {time.time() - t0:.0f}s -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
