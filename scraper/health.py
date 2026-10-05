#!/usr/bin/env python3
"""Daily health check for The Gear Fox: runs right after the morning refresh.

Compares today's data with yesterday's and emails the owner only when something NEW goes wrong
(plus a Monday reminder of anything still broken). Every run also writes site/health.json, which
is how tomorrow's run knows what was already reported.

What it catches
  - a store that failed to update (the site keeps yesterday's deals for it, so users can't tell)
  - a store whose product count suddenly halves or drops to zero
  - a store whose prices jump or fall across the board (usually a currency mix-up)
  - a store with an unusual pile of 70%+ discounts (usually bad "regular" prices)
  - the whole catalogue shrinking sharply
  - sign-ups getting close to the free email plan's limits
  - anything the site test found (tools/sitetest.py: clicks through the site like a visitor, searches, links)

Usage: python scraper/health.py YESTERDAY_DIR SITE_DIR
Env:   RESEND_API_KEY, HEALTH_EMAIL (default hello@thegearfox.com), FROM_EMAIL,
       SUPABASE_URL, SUPABASE_SECRET_KEY (optional, for the sign-up checks),
       SITETEST (default /tmp/sitetest.json, the site test's results),
       SEND_HEALTH=1 to email (the workflow sets it on the scheduled morning run only)
"""
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

PREV, SITE = Path(sys.argv[1]), Path(sys.argv[2])
NOW = datetime.now(timezone.utc)
TO = (os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com").strip()   # a GitHub secret can point it straight at your inbox
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")

# Free Resend plan: 100 emails a day, 3,000 a month. Weekly email = 1 per subscriber per Friday.
WEEKLY_SUBS_WARN = 500      # ~650 subscribers x 4.3 Fridays = the monthly cap
DAILY_SIGNUPS_WARN = 60     # confirmation emails + alerts share the 100/day cap
SAVED = {"mec", "rei", "svp"}      # stores read from pages you save by hand (their sites block automated access)


def load(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def when(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return None


def low_price(o):
    ps = [e[1] for e in o.get("sz", []) if len(e) > 2]
    return min(ps) if ps else None


def big_discounts(offers):
    """Share of listings with any size at 70%+ off."""
    if not offers:
        return 0.0
    n = sum(1 for o in offers if any(len(e) > 2 and e[2] > 0 and e[1] <= e[2] * 0.30 for e in o["sz"]))
    return n / len(offers)


def check():
    problems = []   # (key, message)
    deals, deals0 = load(SITE / "deals.json"), load(PREV / "deals.json")
    offers, offers0 = load(SITE / "offers.json"), load(PREV / "offers.json")
    stamps = deals.get("stores", {})

    for st in sorted(set(offers) | set(offers0)):
        today, before = offers.get(st, []), offers0.get(st, [])
        n, n0 = len(today), len(before)
        t = when(stamps.get(st, ""))
        stale = t is None or NOW - t > timedelta(hours=30)
        if stale:
            since = f"since {t:%b %-d}" if t else "for a while"
            problems.append((f"stale:{st}", f"{st}: hasn't updated {since}"
                             + (". The site is still showing its older deals." if n else " and has no products on the site.")))
        if st in SAVED and n == 0:
            problems.append((f"zero:{st}", f"{st}: no saved pages from the last 10 days, so its deals are hidden. "
                                           f"Save fresh pages to bring them back."))
        elif stale:
            pass
        elif n == 0 and n0 > 0:
            problems.append((f"zero:{st}", f"{st}: 0 products today (had {n0} yesterday)."))
        elif n == 0:
            problems.append((f"zero:{st}", f"{st}: 0 products."))
        elif n0 >= 30 and n < n0 * 0.5:
            problems.append((f"drop:{st}", f"{st}: {n} products today, down from {n0} yesterday."))
        # same product links, yesterday vs today: did every price move together?
        prev_p = {o["u"]: low_price(o) for o in before}
        ratios = [low_price(o) / prev_p[o["u"]] for o in today
                  if prev_p.get(o["u"]) and low_price(o)]
        if len(ratios) >= 20:
            m = statistics.median(ratios)
            if m > 1.2 or m < 0.8:
                problems.append((f"price:{st}", f"{st}: prices moved {round((m - 1) * 100):+d}% across the board overnight "
                                                f"(typical price check on {len(ratios)} products). Possibly a currency mix-up."))
        if n >= 20:
            share, share0 = big_discounts(today), big_discounts(before)
            if share > 0.25 and share > share0 + 0.10:
                problems.append((f"disc:{st}", f"{st}: {round(share * 100)}% of its products show 70%+ off "
                                               f"(yesterday {round(share0 * 100)}%). The regular prices may be wrong."))

    items, items0 = len(deals.get("items", [])), len(deals0.get("items", []))
    if items0 >= 500 and items < items0 * 0.75:
        problems.append(("total", f"The whole site shrank to {items} products from {items0} yesterday."))
    pages = len(list((SITE / "shoes").glob("*/index.html")))      # the Google shoe pages (shoe_pages.py may fail quietly)
    if pages < 100:
        problems.append(("shoepages", f"Only {pages} shoe price pages were built today (normally 350+): the shoe pages step "
                                      "failed, so Google and visitors get 'page not found'. Claude should look at the refresh log."))

    # the site test (tools/sitetest.py): a robot visitor clicked through today's site before it was published
    st = load(Path(os.environ.get("SITETEST", "/tmp/sitetest.json")))
    for c in st.get("checks", []):
        if not c.get("ok"):
            problems.append((f"site:{c['name']}", f"Site test, {c['name']}: {c.get('why', 'failed')}"
                                                  + (" (critical: yesterday's site stays up)" if c.get("critical") else "")))

    # sign-ups vs the free email plan
    sb, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
    subs = new = None
    if sb and key:
        try:
            h = {"apikey": key, "Prefer": "count=exact", "Range": "0-0"}
            if key.count(".") == 2:
                h["Authorization"] = f"Bearer {key}"
            def count(params):
                r = requests.get(f"{sb}/rest/v1/subscribers", params={"select": "email", **params}, headers=h, timeout=30)
                r.raise_for_status()
                return int(r.headers.get("content-range", "*/0").split("/")[-1])
            subs = count({"confirmed_at": "not.is.null", "unsubscribed_at": "is.null"})
            new = count({"created_at": f"gte.{(NOW - timedelta(hours=24)).isoformat()}"})
            if subs >= WEEKLY_SUBS_WARN:
                problems.append(("subs", f"{subs} subscribers: the free email plan (3,000 a month) covers about 650. "
                                         f"Time to upgrade Resend before a Friday send gets cut off."))
            if new >= DAILY_SIGNUPS_WARN:
                problems.append(("signups", f"{new} sign-ups in the last 24 hours: the free email plan allows 100 emails a day, "
                                            f"confirmations included. Upgrade Resend if this keeps up."))
        except Exception as e:
            print(f"sign-up check skipped: {e}")
    sale = lambda its: sum(1 for i in its if any(len(e) > 3 and e[1] < e[3] * 0.99 for e in i.get("sz", [])))
    fresh_stores = sum(1 for st in offers if (t := when(stamps.get(st, ""))) and NOW - t <= timedelta(hours=30))
    moves = sorted(((st, len(offers.get(st, [])), len(offers0.get(st, []))) for st in set(offers) | set(offers0)),
                   key=lambda x: -abs(x[1] - x[2]))
    return problems, {"items": items, "items0": items0, "sale": sale(deals.get("items", [])), "sale0": sale(deals0.get("items", [])),
                      "stores": {st: len(v) for st, v in offers.items()}, "stores_ok": fresh_stores, "stores_n": len(offers),
                      "moves": [m for m in moves if abs(m[1] - m[2]) >= 10][:5], "subscribers": subs, "signups_24h": new,
                      "sitetest": st}


def site_line(st):
    if not st.get("checks"):
        return "- Site test didn't run today (see the log)\n"
    n, ok = len(st["checks"]), st.get("passed", 0)
    ln = st.get("links", {})
    links = (f"; store links: {ln['ok']} of {ln['stores']} stores open" + (f", {len(ln['unsure'])} couldn't be checked "
             f"(they block robots: {', '.join(ln['unsure'])})" if ln.get("unsure") else "")) if "stores" in ln else ""
    return f"- Site test (a robot visitor clicked through the site): {ok} of {n} checks passed{links}\n"


def main():
    problems, stats = check()
    prev = load(PREV / "health.json")
    emailed = set(prev.get("emailed", []))        # problems already sent, still ongoing
    reported = prev.get("reported")                # Vancouver date of the last morning report (the backup run skips if it's today)
    keys = [k for k, _ in problems]
    fresh = [(k, m) for k, m in problems if k not in emailed]
    monday = NOW.astimezone(timezone(timedelta(hours=-7))).weekday() == 0
    send = os.environ.get("SEND_HEALTH") == "1" and os.environ.get("RESEND_API_KEY")      # a short report every morning

    lines = [f"- {m}" for _, m in problems] or ["- All good."]
    print("Health check\n" + "\n".join(lines))
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as f:
            f.write("## Health check\n" + "\n".join(lines) + "\n")

    if send:
        new_part = [m for _, m in fresh]
        old_part = [m for k, m in problems if k in emailed]
        if fresh:
            subject = f"Gear Fox daily check: {len(fresh)} new {'problem' if len(fresh) == 1 else 'problems'}"
        elif problems:
            subject = f"Gear Fox daily check: all running, {len(problems)} still to fix"
        else:
            subject = "Gear Fox daily check: all good"
        d = lambda a, b: f" ({a - b:+,} vs yesterday)" if b else ""
        text = ("All good. Every store updated and nothing looks off.\n\n" if not problems else "") + \
               ("New today:\n" + "\n".join(f"- {m}" for m in new_part) + "\n\n" if new_part else "") + \
               ("Still to fix:\n" + "\n".join(f"- {m}" for m in old_part) + "\n\n" if old_part else "") + \
               "Today on the site:\n" + \
               f"- {stats['items']:,} products{d(stats['items'], stats['items0'])}\n" + \
               f"- {stats['sale']:,} on sale{d(stats['sale'], stats['sale0'])}\n" + \
               f"- {stats['stores_ok']} of {stats['stores_n']} stores updated in the last day\n" + \
               site_line(stats["sitetest"]) + \
               (f"- {stats['subscribers']} subscribers, {stats['signups_24h']} new sign-ups in the last 24 hours\n"
                if stats["subscribers"] is not None else "") + \
               ("\nBiggest changes by store:\n" + "\n".join(f"- {st}: {a:,} products (was {b:,})" for st, a, b in stats["moves"]) + "\n"
                if stats["moves"] else "") + \
               "\nFull log: https://github.com/upnorth89/Running-Discount/actions\n"
        r = requests.post("https://api.resend.com/emails", timeout=60,
                          headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                          json={"from": FROM, "to": [TO], "subject": subject, "text": text})
        print(f"emailed {TO}: HTTP {r.status_code}")
        if r.ok:
            emailed = set(keys)
            reported = NOW.astimezone(ZoneInfo("America/Vancouver")).date().isoformat()
    # forget problems that are fixed, so they get reported again if they come back
    emailed &= set(keys)
    # this file is public (it's deployed with the site), so no subscriber numbers in it
    public = [m for k, m in problems if k not in ("subs", "signups")]
    (SITE / "health.json").write_text(json.dumps({"checked": NOW.isoformat(timespec="seconds"), "problems": public,
                                                   "emailed": sorted(emailed), "reported": reported, "items": stats["items"],
                                                   "stores": stats["stores"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
