#!/usr/bin/env python3
"""IndexNow (Oct 11, 2026): after the morning deploy, tell Bing (and Yandex, Seznam, Naver; Bing also feeds DuckDuckGo and
ChatGPT search) which pages changed today. Without it Bing finds them only when it happens to crawl. The key is public by
design: site/d5b591bd5a0f92826eeb50008110fb99.txt proves we own the site.

Oct 23 (Bastien OK'd): only pages that really changed. IndexNow asks sites not to resend unchanged pages, and we were sending all
~2,400 every morning (24,200 notices in 12 days). Each sitemap page is read from the live site, its visible text kept without the
day's date stamps ("checked Oct 23", "35 days to go"), and compared with yesterday's fingerprint (STATE, kept between runs by the
workflow's cache): new or different pages are sent. No fingerprints yet (first run, cache lost) = every page, like before.

  python tools/indexnow.py [STATE.json]      (refresh.yml job "indexnow", morning runs only)
"""
import concurrent.futures as cf
import hashlib
import json
import re
import sys
from html import unescape
from pathlib import Path

import requests

KEY = "d5b591bd5a0f92826eeb50008110fb99"
HOST = "thegearfox.com"
STATE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/indexnow-state.json")
UA = {"User-Agent": "TheGearFox-IndexNow/1.0 (+https://thegearfox.com/about.html)"}

MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
MOIS = r"(?:janv|févr|fevr|mars|avr|mai|juin|juil|août|aout|sept|oct|nov|déc|dec)[a-zéû]*\.?"
STAMPS = [re.compile(p, re.I) for p in (
    rf"\b{MON} \d{{1,2}}(?:, \d{{4}})?",            # Oct 23 / October 23, 2026 / Oct. 22
    rf"\b\d{{1,2}}(?:er)? {MOIS}(?: \d{{4}})?",      # 23 oct. / 1er novembre 2026
    r"\b\d{4}-\d{2}-\d{2}(?:T[\d:.+Z-]+)?",           # 2026-10-23
    r"\b\d+ days? to go|\bencore \d+ jours?",          # Black Friday / Boxing Day countdowns
    r"\b\d+ (?:h|hours?|heures?|min) ago|il y a \d+ ?(?:h|min)",
)]


def fingerprint(html):
    t = re.sub(r"(?is)<(script|style|noscript|template)\b.*?</\1>", " ", html)   # scripts carry dateModified etc.
    t = unescape(re.sub(r"<[^>]+>", " ", t))
    for p in STAMPS:
        t = p.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def read(url):
    for _ in range(2):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code == 200:
                return url, fingerprint(r.text)
            if r.status_code in (404, 410):
                return url, None
        except requests.RequestException:
            pass
    return url, ""          # couldn't read it: sent anyway, fingerprint kept as unknown


xml = requests.get(f"https://{HOST}/sitemap.xml", headers=UA, timeout=60).text
urls = [f"https://{HOST}/"] + [u for u in re.findall(r"<loc>([^<]+)</loc>", xml) if u.startswith(f"https://{HOST}/")]
urls = list(dict.fromkeys(urls))
try:
    old = json.loads(STATE.read_text())
except Exception:
    old = {}
with cf.ThreadPoolExecutor(8) as ex:
    now = dict(ex.map(read, urls))
send = [u for u in urls if now[u] is not None and (not now[u] or old.get(u) != now[u])]
new = sum(1 for u in send if u not in old)
print(f"{len(urls)} pages in the sitemap; {len(send)} to send ({new} new, {len(send) - new} changed"
      + (", no fingerprints from yesterday: all of them" if not old else "") + ")")
STATE.write_text(json.dumps({u: h for u, h in now.items() if h}, separators=(",", ":")))

ok = True
if not send or __import__("os").environ.get("INDEXNOW_DRY"):    # nothing changed / testing: send nothing
    sys.exit(0)
for i in range(0, len(send), 10000):                  # 10,000 URLs per call at most
    r = requests.post("https://api.indexnow.org/indexnow", timeout=60, json={
        "host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": send[i:i + 10000]})
    print(f"IndexNow: {len(send[i:i + 10000])} URLs -> HTTP {r.status_code} {r.text[:200]}")
    ok &= r.status_code in (200, 202)
sys.exit(0 if ok else 1)
