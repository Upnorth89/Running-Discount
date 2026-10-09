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
    ctx.route("**/rest/v1/rpc/**", lambda r: r.fulfill(status=200, content_type="application/json", body="null"))
    ctx.route(re.compile(r"umami|googletagmanager|accounts\.google|gstatic"), lambda r: r.abort())
    ctx.route(re.compile(r"^https?://(?!127\.0\.0\.1).*\.(jpe?g|png|webp|gif|avif)(\?.*)?$", re.I), lambda r: r.abort())


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
            got = page.evaluate("""() => [['mailto:Name@Gmail.com',1],['bastien.hammond+test5@gmail.com',1],['jo@sub.domain.co.uk',1],
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

        def chip(v):
            page.click(f'#cats .chip[data-v="{v}"]')
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

        def nonsense():
            all_gear()
            page.fill("#dSearch", "zzqxw")
            settle(page, 600)
            assert not cards(page), "a nonsense search still shows deals"
            txt = page.inner_text("main")
            assert "Nothing matches" in txt, "a search with no results doesn't say 'Nothing matches'"
            page.fill("#dSearch", "")
            settle(page)
            assert cards(page), "deals didn't come back after clearing the search"
        check("Search with no results")(nonsense, page)

        def filters():
            all_gear()
            chip("shoes")
            n0 = int(page.inner_text("#grp-shoes h2 small").replace(",", "").replace(" ", "").replace(" ", "") or 0)
            if not page.locator('#toggles .chip[data-t="sale"]').is_visible():
                page.click("#filtBtn")
                settle(page)
            page.click('#toggles .chip[data-t="sale"]')
            page.wait_for_timeout(2500)                   # loads the full-price list
            n1 = int(page.inner_text("#grp-shoes h2 small").replace(",", "").replace(" ", "").replace(" ", "") or 0)
            assert n1 > n0, f"'Include full price' didn't add shoes ({n0} -> {n1})"
            page.click('#toggles .chip[data-t="sale"]')
            settle(page)
            page.select_option("#sort", "price")
            settle(page)
            ps = [float(re.sub(r"[^\d.]", "", c["price"].replace(",", ".") if "," in c["price"] and "." not in c["price"] else c["price"].replace(",", "")) or 0)
                  for c in cards(page)[:12]]
            assert ps == sorted(ps), f"'Lowest price' isn't in price order ({ps[:6]})"
            page.select_option("#sort", "match")
            settle(page)
            return f"full price {n0} -> {n1} shoes"
        check("Filters (full price, sort)")(filters, page)

        def heart():
            all_gear()
            page.locator("section.grp .heart").first.click()
            page.wait_for_selector("#sheet", state="visible")
            assert page.locator("#gateEmail").is_visible(), "a heart didn't ask for the email"
            page.click("#closeSheet")
            page.wait_for_selector("#sheet", state="hidden")
        check("Heart asks for the email")(heart, page)

        def menu():
            page.click("#menuBtn")
            page.wait_for_selector("#menu", state="visible")
            gos = page.eval_on_selector_all("#menu [data-go]:not([hidden])", "e => e.map(x => x.dataset.go)")
            for need in ["deals", "shoes", "sizes", "about"]:
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
            page.click("#langBtn")
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
            page.click("#langBtn")
            settle(page, 600)
            return t
        check("French version")(french, page)

        def comeback():
            # tap a deal (the store opens in another tab; here the click is kept on the page), come back: the bar offers
            # that store's other deals; Show = only that store; "× All stores" = everything again
            all_gear()
            n0 = len(cards(page))
            page.evaluate("""() => { const a = [...document.querySelectorAll('section.grp a.deal')]
                .find(a => /altitude|lasthunt|sportinglife|thefeed|bushtukah/.test(a.dataset.store)) || document.querySelector('section.grp a.deal');
                a.addEventListener('click', e => e.preventDefault(), {once: true}); a.click(); }""")
            page.wait_for_selector("#backBar", timeout=6000)
            bar = page.inner_text("#backBar")
            page.click("#backBar .go")
            page.wait_for_selector(".storebar")
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

        # shoe pages
        def shoe_page():
            all_gear()
            chip("shoes")
            href = page.locator("section.grp a.cmp").first.get_attribute("href")
            page.goto(base + href.lstrip("/"), wait_until="domcontentloaded")
            rows = page.locator("table tr").count()
            assert rows >= 2, f"the shoe page {href} has no price table"
            assert re.search(r"\$\s?\d", page.inner_text("body")), f"the shoe page {href} shows no price"
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
            box = page.locator("input[type=search]")
            if box.count():
                box.first.fill("clifton")
                settle(page, 500)
                vis = page.evaluate("[...document.querySelectorAll('a[href*=\"clifton\"]')].filter(a=>a.offsetParent).length")
                assert vis, "searching 'clifton' on the shoe list shows no Clifton"
            return f"{len(out)} pages"
        check("Shoe lists, Black Friday, About, privacy", critical=False)(pages, page)

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
            assert "Sizes on sale" in pg.inner_text("section.grp"), "cards don't say they show every size"
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            assert pg.locator("#sheet").is_hidden(), "a browsing visitor gets the welcome screen again on reload"
            pg.click(".browsebar [data-picksize]")
            pg.wait_for_selector("#shoeSizes button", state="visible")
            assert pg.locator("#moreSizes").is_visible() and pg.locator("#clothSizes").is_hidden(), "the short sizes step isn't short"
            pg.click('#fit button[data-v="men"]')
            pg.locator("#shoeSizes button", has_text=re.compile(r"^10$")).first.click()
            pg.click("#saveSizes")
            pg.wait_for_selector("#sheet", state="hidden")
            settle(pg, 500)
            assert not pg.locator(".browsebar").count(), "the 'pick your size' note stays after picking sizes"
            chip_tops = pg.locator('#cats .chip[data-v="tops"]')
            chip_tops.click()
            settle(pg)
            assert "Pick your clothing size" in pg.inner_text("main"), "clothing doesn't offer to pick a clothing size"
            return f"{n} deals in every size, then men's 10"
        check("Just show me deals, sizes later")(browse, pg)

        def canadian():   # Oct 7: Canadian brands filter (Canada side): only maple-leaf brands, a box saying so, × turns it off
            pg.goto(base + "?canadian", wait_until="domcontentloaded")
            pg.wait_for_selector(".cdnbar", timeout=20000)
            settle(pg)
            brands = pg.eval_on_selector_all("#dealList .deal .brand", "e => e.map(x => [x.textContent, !!x.querySelector('.leaf')])")
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
            pg.locator('#cats .chip[data-v="nutrition"]').click()
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
            pg.locator('#cats .chip[data-v="nutrition"]').click()                                  # and every category again
            settle(pg)
            return f"Nutrition: {n} deals from Canada, {m} with US stores"
        check("Ships from Canada means Canada")(ships_ca, pg)

        def backbar_signup():   # Oct 8: back from a store, a visitor who isn't a member is offered the Friday email
            pg.goto(base, wait_until="domcontentloaded")
            pg.wait_for_selector("section.grp .deal", timeout=20000)
            pg.evaluate("sessionStorage.removeItem('gf-bsu');sessionStorage.setItem('gf-lastshop',JSON.stringify({h:'sportinglife.ca',t:Date.now()}))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector("#backBar.subar", timeout=8000)
            pg.fill("#backBar input", "not-an-email")
            pg.click("#backBar button.go")
            settle(pg)
            assert pg.inner_text("#backBar .msg").strip(), "a bad email gives no message in the come-back bar"
            pg.fill("#backBar input", "robot@example.com")
            pg.click("#backBar button.go")
            settle(pg, 600)
            assert "robot@example.com" in pg.inner_text("#backBar"), "the come-back bar doesn't confirm the sign-up"
            pg.evaluate("localStorage.removeItem('gf-sub')")
            return "offered, refused a bad email, signed up"
        check("Sign-up bar after a deal click")(backbar_signup, pg)

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
                assert "USD" in pu.inner_text("section.grp"), "prices on the USA side aren't in US dollars"
                if pu.locator(".seo-us").count():          # the bottom block: the US copy, not "...in Canada"
                    assert pu.locator(".seo-us").is_visible() and not pu.locator(".seo-en").is_visible(), \
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
                assert "CAD" in pu.inner_text("section.grp"), "switching to Canada didn't switch to Canadian dollars"
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
