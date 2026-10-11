#!/usr/bin/env python3
"""IndexNow (Oct 11, 2026): after the morning deploy, tell Bing (and Yandex, Seznam, Naver; Bing also feeds DuckDuckGo and
ChatGPT search) that every page in our sitemap changed today: shoe pages carry today's prices. Without it Bing finds them
only when it happens to crawl. The key is public by design: site/d5b591bd5a0f92826eeb50008110fb99.txt proves we own the site.

  python tools/indexnow.py            (refresh.yml job "indexnow", morning runs only)
"""
import re
import sys

import requests

KEY = "d5b591bd5a0f92826eeb50008110fb99"
HOST = "thegearfox.com"

xml = requests.get(f"https://{HOST}/sitemap.xml", timeout=60).text
urls = re.findall(r"<loc>([^<]+)</loc>", xml)
urls = [f"https://{HOST}/"] + [u for u in urls if u.startswith(f"https://{HOST}/")]
ok = True
for i in range(0, len(urls), 10000):                  # 10,000 URLs per call at most
    r = requests.post("https://api.indexnow.org/indexnow", timeout=60, json={
        "host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls[i:i + 10000]})
    print(f"IndexNow: {len(urls[i:i + 10000])} URLs -> HTTP {r.status_code} {r.text[:200]}")
    ok &= r.status_code in (200, 202)
sys.exit(0 if ok else 1)
