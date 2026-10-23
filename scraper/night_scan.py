#!/usr/bin/env python3
"""Night scan (Oct 23, 2026; Bastien: "scan website as a user to find any glitches: this should be done nightly").

The refresh runs the robot visitor test on the main paths twice a day; this walks EVERY page Google sees, at night:
  1. every page in sitemap.xml: answers 200, has a title, no leftovers a visitor would see ("undefined", "NaN", "{name}",
     "[object Object]", a "$0.00" price), shoe/list/race pages show at least one price;
  2. every link and picture on our own site those pages point to: answers 200 (once per address);
  3. a phone (390 px wide) opens the hubs + 40 random pages: no script errors from our own code, nothing wider than the
     screen, no leftover words once the page's scripts have run.
It emails only when something is wrong (like the noon check), with the page addresses to look at.

  python scraper/night_scan.py [BASE_URL] [OUT.json]     env: RESEND_API_KEY, HEALTH_EMAIL; NIGHT_SAMPLE=40
"""
import concurrent.futures as cf
import json
import os
import random
import re
import sys
import time
from html import unescape
from urllib.parse import urljoin, urlparse

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://thegearfox.com/").rstrip("/") + "/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/night-scan.json"
SAMPLE = int(os.environ.get("NIGHT_SAMPLE", "40"))
TO = os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com"
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
UA = {"User-Agent": "TheGearFox-NightScan/1.0 (+https://thegearfox.com/about.html)"}
HOST = urlparse(BASE).netloc
# what a visitor should never read on a page
JUNK = re.compile(r"\bundefined\b|\bNaN\b|\[object Object\]|\{[a-z_]{2,20}\}|Traceback \(most recent|\$\s?0[.,]00\b|\b0[.,]00\s?\$")
PRICED = re.compile(r"/(shoes|chaussures|running-shoes-sale|chaussures-course-solde|brands|marques|races|courses)/[^/]+/")
S = requests.Session()
S.headers.update(UA)


def get(url, tries=2):
    for i in range(tries):
        try:
            r = S.get(url, timeout=40)
            if r.status_code < 500 or i == tries - 1:
                return r
        except requests.RequestException as e:
            if i == tries - 1:
                return e
        time.sleep(3)


def visible(html):
    t = re.sub(r"(?is)<(script|style|noscript|template)\b.*?</\1>", " ", html)
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", t)))


def ours(u):
    p = urlparse(u)
    return p.netloc in ("", HOST) and p.scheme in ("", "http", "https")


def page_check(url):
    r = get(url)
    if not isinstance(r, requests.Response):
        return url, [f"didn't answer ({type(r).__name__})"], set()
    if r.status_code != 200:
        return url, [f"HTTP {r.status_code}"], set()
    h, bad = r.text, []
    if not re.search(r"<title>[^<]{5,}</title>", h):
        bad.append("no page title")
    txt = visible(h)
    for m in sorted(set(JUNK.findall(txt)))[:3]:
        i = txt.find(m)
        bad.append(f"shows “{m}”: …{txt[max(0, i - 50):i + 40].strip()}…")
    if PRICED.search(urlparse(url).path) and not re.search(r"\$\s?\d|\d\s?\$|Not in stock at the stores|Pas en stock dans les boutiques", txt):
        bad.append("no price on the page")
    links = set()
    for a in re.findall(r'(?:href|src)="([^"#]+)"', re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", h)):   # not the scripts' own templates
        if a.startswith(("mailto:", "tel:", "javascript:", "data:", "{", "$")) or "${" in a:
            continue
        u = urljoin(url, unescape(a)).split("#")[0]
        if ours(u) and urlparse(u).netloc == HOST:
            links.add(u.split("?")[0])
    return url, bad, links


def phone_pass(urls):
    """A 390 px phone opens each page: script errors from our code, sideways scroll, leftovers after the scripts ran."""
    from playwright.sync_api import sync_playwright
    found = {}
    exe = os.environ.get("CHROMIUM")
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                            ignore_https_errors=bool(os.environ.get("SITETEST_INSECURE")), user_agent=UA["User-Agent"] + " Mobile")
        # analytics stay out of our own numbers
        ctx.route(re.compile(r"supabase\.co|umami|cloud\.umami|googletagmanager"), lambda r: r.fulfill(status=200, body="{}"))
        for url in urls:
            errs, pg = [], ctx.new_page()
            pg.on("pageerror", lambda e, errs=errs: errs.append(str(e).splitlines()[0][:160]))
            try:
                try:
                    pg.goto(url, wait_until="load", timeout=45000)
                except Exception:      # one blip isn't a glitch: a second try
                    pg.wait_for_timeout(5000)
                    pg.goto(url, wait_until="load", timeout=45000)
                pg.wait_for_timeout(2500)
                w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
                txt = pg.evaluate("document.body ? document.body.innerText : ''")
            except Exception as e:
                found[url] = [f"phone: didn't load ({str(e).splitlines()[0][:100]})"]
                pg.close()
                continue
            bad = [f"phone: script error: {e}" for e in errs[:2]]
            if w[0] > w[1] + 2:
                bad.append(f"phone: wider than the screen ({w[0]} px on a {w[1]} px phone)")
            for m in sorted(set(JUNK.findall(txt)))[:2]:
                i = txt.find(m)
                bad.append(f"phone: shows “{m}”: …{' '.join(txt[max(0, i - 50):i + 40].split())}…")
            if bad:
                found[url] = bad
            pg.close()
        b.close()
    return found


def main():
    t0 = time.time()
    sm = get(BASE + "sitemap.xml")
    if not isinstance(sm, requests.Response) or sm.status_code != 200:
        pages, problems = [], {BASE + "sitemap.xml": ["the sitemap didn't load"]}
    else:
        pages = [unescape(u).replace("https://thegearfox.com/", BASE) for u in re.findall(r"<loc>([^<]+)</loc>", sm.text)]
        problems = {}
    print(f"{len(pages)} pages in the sitemap")
    links = set()
    with cf.ThreadPoolExecutor(6) as ex:
        for url, bad, ls in ex.map(page_check, pages):
            if bad:
                problems[url] = bad
            links |= ls
    # links + pictures on our site that aren't sitemap pages themselves (each address once)
    todo = sorted(links - set(pages) - {BASE + "sitemap.xml"})
    todo = [u for u in todo if not re.search(r"/(grab|stats|catalog)\.html$", u)]
    print(f"{len(todo)} other addresses linked from them")

    def head(u):
        r = get(u)
        return u, (r.status_code if isinstance(r, requests.Response) else 0)
    broken = {}
    with cf.ThreadPoolExecutor(6) as ex:
        for u, code in ex.map(head, todo):
            if code != 200:
                broken[u] = code
    for u, code in broken.items():
        problems.setdefault(u, []).append(f"linked from our pages but answers HTTP {code or 'nothing'}")

    hubs = [BASE, BASE + "shoes/", BASE + "chaussures/", BASE + "races/", BASE + "courses/", BASE + "us/races/", BASE + "running-shoes-sale/",
            BASE + "black-friday/", BASE + "about.html", BASE + "privacy.html"]
    rest = [p for p in pages if p not in hubs]
    random.seed(time.strftime("%Y%m%d"))
    sample = hubs + random.sample(rest, min(SAMPLE, len(rest)))
    try:
        for u, bad in phone_pass(sample).items():
            problems.setdefault(u, []).extend(bad)
    except Exception as e:
        problems.setdefault("phone pass", []).append(f"couldn't run: {str(e).splitlines()[0][:160]}")

    n = sum(len(v) for v in problems.values())
    summary = (f"Night scan: {len(pages)} pages, {len(todo)} other links and pictures, {len(sample)} pages opened on a phone; "
               f"{n} {'problem' if n == 1 else 'problems'} on {len(problems)} {'page' if len(problems) == 1 else 'pages'} "
               f"({round((time.time() - t0) / 60)} min)")
    lines = [f"- {u.replace(BASE, '/')}: " + "; ".join(v) for u, v in sorted(problems.items())]
    print(summary + ("\n" + "\n".join(lines) if lines else "\nAll good: no email."))
    json.dump({"date": time.strftime("%Y-%m-%d"), "pages": len(pages), "links": len(todo), "phone": len(sample),
               "problems": problems}, open(OUT, "w"), indent=1, ensure_ascii=False)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("## Night scan\n" + summary + "\n" + "\n".join(lines[:200]) + "\n")
    if problems and os.environ.get("RESEND_API_KEY"):
        text = ("The night scan found things a visitor would trip on:\n\n" + "\n".join(lines[:60])
                + (f"\n…and {len(lines) - 60} more (full list in the log)" if len(lines) > 60 else "") + "\n\n" + summary
                + "\n\nFull log: https://github.com/upnorth89/Running-Discount/actions/workflows/night-scan.yml\n")
        r = requests.post("https://api.resend.com/emails", timeout=60, headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                          json={"from": FROM, "to": [TO], "subject": f"Gear Fox night scan: {len(problems)} "
                                f"{'page' if len(problems) == 1 else 'pages'} to look at", "text": text})
        print(f"emailed {TO}: HTTP {r.status_code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
