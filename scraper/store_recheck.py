#!/usr/bin/env python3
"""Store recheck (Oct 16, 2026; Bastien: "Everyone that says no we should try every 2 weeks to make sure there's no other way in").

On the 1st and 15th (store-recheck.yml), from GitHub's servers, one polite visit per door for every store that said no: its
robots.txt (does it now let us, or ClaudeBot, in?), its running list page (a real page, or a 403 / "Just a moment" / empty
script page?) and, where it exists, its public product data (Shopify products.json). Never a disguised browser or a
workaround: a store that still says no is simply listed. Emails Bastien (HEALTH_EMAIL) the result: which stores now look open
(ask Claude to build their reader) and which still say no, with the door that refused.

  python scraper/store_recheck.py            (needs RESEND_API_KEY + HEALTH_EMAIL to email; prints either way)
"""
import os
import re
import time

import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; TheGearFoxBot/1.0; +https://thegearfox.com/about.html)",
      "Accept-Language": "en-CA,en;q=0.8"}

# store: (why it was a no, [doors to try]). Keep in step with STORES.md "Master list" (blocked rows).
STORES = {
    "MEC": ("blocks automated reading (Grab deals bookmark meanwhile)",
            ["https://www.mec.ca/robots.txt", "https://www.mec.ca/en/products/running/deals"]),
    "REI (USA)": ("blocks automated reading (Grab deals bookmark meanwhile)",
                  ["https://www.rei.com/robots.txt", "https://www.rei.com/c/running"]),
    "Backcountry (USA)": ("'HTTP 202, empty page' to our servers (Grab deals bookmark meanwhile)",
                          ["https://www.backcountry.com/robots.txt", "https://www.backcountry.com/cat/running-shoes"]),
    "Hoka": ("Cloudflare 403", ["https://www.hoka.com/robots.txt", "https://www.hoka.com/en/ca/mens-road/"]),
    "Brooks": ("Akamai 403", ["https://www.brooksrunning.com/robots.txt", "https://www.brooksrunning.com/en_ca/mens/shoes/"]),
    "New Balance": ("403", ["https://www.newbalance.ca/robots.txt", "https://www.newbalance.ca/en_ca/men/shoes/running/"]),
    "ASICS": ("Akamai 403", ["https://www.asics.com/robots.txt", "https://www.asics.com/ca/en-ca/mens-running-shoes/c/aa10201000/"]),
    "adidas.ca": ("connection dropped / blocked", ["https://www.adidas.ca/robots.txt", "https://www.adidas.ca/en/running-shoes"]),
    "Salomon": ("403 after an hour of reading (Oct 16)",
                ["https://www.salomon.com/robots.txt", "https://www.salomon.com/en-ca/shop/men/shoes/trail-running.html"]),
    "Patagonia": ("Akamai holding page 'Hang Tight! Routing to checkout' on every page (Oct 25)",
                  ["https://www.patagonia.ca/robots.txt", "https://www.patagonia.ca/shop/web-specials"]),
    "Latulippe": ("Cloudflare 403 challenge, robots.txt included (Oct 25)",
                  ["https://www.latulippe.com/robots.txt", "https://www.latulippe.com/products.json?limit=1"]),
    "Merrell": ("robots.txt blocks ClaudeBot and AI robots",
                ["https://www.merrell.com/robots.txt", "https://www.merrell.com/CA/en_CA/men-trail-running/"]),
    "On": ("the page is an empty shell filled by script", ["https://www.on.com/robots.txt", "https://www.on.com/en-ca/shop/mens/shoes/running"]),
    "The North Face": ("403", ["https://www.thenorthface.com/robots.txt", "https://www.thenorthface.com/en-ca/mens/mens-footwear-c211723"]),
    "Inov-8": ("403", ["https://www.inov-8.com/robots.txt", "https://www.inov-8.com/ca/"]),
    "Simons": ("Cloudflare 403 everywhere", ["https://www.simons.ca/robots.txt", "https://www.simons.ca/en"]),
    "Boutique Courir": ("blocks automated reading", ["https://boutiquecourir.com/robots.txt", "https://boutiquecourir.com/products.json"]),
    "Honey Stinger": ("blocks GitHub's servers", ["https://www.honeystinger.com/robots.txt", "https://www.honeystinger.com/products.json"]),
}
WALL = re.compile(r"Just a moment|cf-chl|captcha|Access Denied|Request unsuccessful|Pardon Our Interruption|px-captcha", re.I)


def robots_says(text):
    """'no' when the rules for everyone (*) or for ClaudeBot / AI robots block the whole site, else 'ok'."""
    groups, cur, rules = [], [], []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if rules:
                groups.append((cur, rules))
                cur, rules = [], []
            cur.append(v.lower())
        elif k in ("disallow", "allow"):
            rules.append((k, v))
    if cur or rules:
        groups.append((cur, rules))
    for agents, rules in groups:
        if any(a in ("*", "claudebot", "anthropic-ai", "claude-user") for a in agents):
            if ("disallow", "/") in rules and not any(k == "allow" and v in ("/", "") for k, v in rules):
                who = "ClaudeBot / AI robots" if "*" not in agents else "everyone"
                return f"no ({who}: Disallow /)"
    return "ok"


def visit(url):
    try:
        r = requests.get(url, headers=UA, timeout=40, allow_redirects=True)
    except requests.RequestException as e:
        return None, f"no answer ({type(e).__name__})"
    t = r.text or ""
    if url.endswith("robots.txt"):
        return (r.status_code == 200 and "User-agent" in t and robots_says(t) == "ok"), \
               f"robots.txt {r.status_code}" + ("" if r.status_code != 200 else f", {robots_says(t)}")
    if r.status_code != 200:
        return False, f"{r.status_code}"
    if WALL.search(t[:20000]):
        return False, "200 but a bot check page"
    if url.endswith("products.json"):
        n = len(re.findall(r'"handle"', t))
        return n > 0, f"products.json: {n} products"
    data = len(re.findall(r'application/ld\+json|__NEXT_DATA__|"price"', t))
    ok = len(t) > 50000 and data > 0
    return ok, f"200, {len(t) // 1000} KB, {'product data found' if data else 'no product data (script page?)'}"


def main():
    opened, still = [], []
    for name, (why, doors) in STORES.items():
        notes, page_ok, robots_ok = [], False, True
        for u in doors:
            ok, note = visit(u)
            notes.append(note)
            if u.endswith("robots.txt"):
                robots_ok = ok is not False
            elif ok:
                page_ok = True
            time.sleep(3)
        line = f"- {name}: " + "; ".join(notes) + f"  (was: {why})"
        print(line)
        (opened if page_ok and robots_ok else still).append(line)
    subject = (f"Store recheck: {len(opened)} store{'s' if len(opened) != 1 else ''} may let us in now" if opened
               else f"Store recheck: all {len(still)} still say no")
    text = ("Every two weeks we knock again, politely, on every store that said no (robots.txt, the running list page, public "
            "product data). Never a workaround.\n\n" +
            ("LOOKS OPEN NOW (ask Claude to build the reader and check every category first):\n" + "\n".join(opened) + "\n\n" if opened else "") +
            "STILL NO:\n" + "\n".join(still) + "\n\nThe list lives in scraper/store_recheck.py and STORES.md.\n")
    print(subject)
    key, to = os.environ.get("RESEND_API_KEY"), os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com"
    if key:
        r = requests.post("https://api.resend.com/emails", timeout=60, headers={"Authorization": f"Bearer {key}"},
                          json={"from": os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>"), "to": [to],
                                "subject": subject, "text": text})
        print(f"emailed: HTTP {r.status_code}")
    for line in opened:
        print(f"::warning title=store may be open::{line}")


if __name__ == "__main__":
    main()
