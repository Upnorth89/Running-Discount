#!/usr/bin/env python3
"""Probe (Oct 10, 2026): can GitHub's servers read a store? One plain visit per address, 2 s apart, results as run
annotations (Claude reads those; the logs aren't reachable). Says what came back: status, size, server, robots.txt lines,
product data (JSON-LD offers, __NEXT_DATA__, Shopify). Never retries around a block.

  URLS="https://a/robots.txt https://a/p/1" python tools/probe.py      (workflow: .github/workflows/probe.yml)
"""
import os
import re
import time

import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

for u in os.environ.get("URLS", "").split():
    try:
        r = requests.get(u, headers=H, timeout=30)
        t = r.text
        bits = [f"{r.status_code}", f"{len(t)} chars", r.headers.get("server") or "", (r.headers.get("content-type") or "")[:30]]
        if u.endswith("robots.txt") and r.status_code == 200:
            rules = [l.strip() for l in t.splitlines() if re.match(r"(?i)(user-agent|disallow|allow|crawl-delay|sitemap)", l.strip())]
            bits.append(" ; ".join(rules[:40]))
        else:
            offers = t.count(chr(34) + "offers" + chr(34))
            title = re.search(r"<title>(.*?)</title>", t, re.S)
            prices = sorted(set(re.findall(r"\$\s?\d+\.\d\d", t)))[:6]
            bits.append(f"ld+json offers: {offers}, __NEXT_DATA__: {'__NEXT_DATA__' in t}, prices: {prices}, "
                        f"title: {title.group(1).strip()[:80] if title else ''}")
        print(f"::warning title=probe {u[:100]}::" + " | ".join(bits)[:3500].replace("\n", " "))
    except Exception as e:
        print(f"::warning title=probe {u[:100]}::failed: {type(e).__name__} {str(e)[:200]}")
    time.sleep(2)
