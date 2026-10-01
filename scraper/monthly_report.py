#!/usr/bin/env python3
"""The Gear Fox monthly report: visitors, sign-ups and the shoppers sent to each store.

For affiliate applications and emails to shops ("In October we sent 412 shoppers to Altitude Sports").
Reads Umami Cloud (visits, the deal-click / signup / ref-visit events the site sends) and Supabase
(new confirmed subscribers and the ?ref= link they came from), then emails a plain-text report.

Env:   UMAMI_API_KEY (Umami Cloud > Settings > API keys), RESEND_API_KEY, HEALTH_EMAIL (default
       hello@thegearfox.com), FROM_EMAIL, SUPABASE_URL, SUPABASE_SECRET_KEY
       REPORT_MONTH  "2026-10" for that month; empty = last month on the 1st-3rd, else this month so far
Usage: python scraper/monthly_report.py [--dry-run]   (--dry-run prints instead of emailing)
"""
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

WEBSITE_ID = "d73c30be-171d-40d8-8101-278c2a536699"         # same as UMAMI_ID in site/index.html
BASES = ["https://api.umami.is/v1", "https://api.umami.is/v1/us", "https://api.umami.is/v1/eu"]
TZ = ZoneInfo("America/Vancouver")
TO = (os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com").strip()
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")

# store web address -> name (same names as the cards on the site)
STORE_NAMES = {
    "altitude-sports.com": "Altitude Sports", "thelasthunt.com": "The Last Hunt", "thefeed.com": "The Feed",
    "sea2skynutrition.ca": "Sea2Sky Nutrition", "sportinglife.ca": "Sporting Life", "stampeak.com": "Stampeak",
    "mec.ca": "MEC", "rei.com": "REI", "decathlon.ca": "Decathlon", "vanrunco.com": "Vancouver Running Co.",
    "lecoureurnordique.ca": "Le Coureur Nordique", "bushtukah.com": "Bushtukah", "nordarun.com": "Nordarun",
    "ca.cieleathletics.com": "Ciele", "xactnutrition.com": "Xact Nutrition", "naak.com": "Näak",
    "boutiqueendurance.ca": "Boutique Endurance", "fitfirst.ca": "Fit First", "capra.run": "Capra Running Co.",
    "altrarunning.com": "Altra", "runjanji.com": "Janji", "runinrabbit.com": "rabbit", "satisfyrunning.com": "Satisfy",
    "saysky.com": "SAYSKY", "soarrunning.com": "Soar", "raidlight.com": "Raidlight", "districtvision.com": "District Vision",
    "banditrunning.com": "Bandit", "tenthousand.cc": "Ten Thousand", "oiselle.com": "Oiselle", "2xu.com": "2XU",
    "rnnr.com": "rnnr", "smartwool.com": "Smartwool", "nathansports.com": "Nathan", "nakedsportsinnovations.com": "Naked",
    "mounttocoast.com": "Mount to Coast", "kogalla.com": "Kogalla", "squirrelsnutbutter.com": "Squirrel's Nut Butter",
    "feetures.com": "Feetures", "balega.com": "Balega", "darntough.com": "Darn Tough", "swiftwick.com": "Swiftwick",
    "stance.com": "Stance", "wigwam.com": "Wigwam", "goodr.com": "goodr", "roka.com": "Roka", "sunski.com": "Sunski",
    "tifosioptics.com": "Tifosi", "tailwindnutrition.com": "Tailwind", "skratchlabs.com": "Skratch Labs",
    "nuun.com": "Nuun", "honeystinger.com": "Honey Stinger", "guenergy.com": "GU", "humagel.com": "Huma",
}
COUNTRIES = {"CA": "Canada", "US": "United States", "FR": "France", "GB": "United Kingdom", "AU": "Australia",
             "DE": "Germany", "MX": "Mexico"}
GROUPS = {"shoes": "Shoes", "tops": "Tops & jackets", "bottoms": "Shorts & tights", "bras": "Sports bras",
          "socks": "Socks", "gloves": "Gloves", "headwear": "Hats", "packs": "Vests & packs",
          "gear": "Lights, poles & bottles", "watches": "Watches", "nutrition": "Nutrition"}


def month_range():
    """Start and end (Vancouver time) of the month to report, and a label."""
    now = datetime.now(TZ)
    m = os.environ.get("REPORT_MONTH", "").strip()
    if m:
        y, mo = map(int, m.split("-"))
        start = datetime(y, mo, 1, tzinfo=TZ)
    elif now.day <= 3:                          # the scheduled run on the 1st: last month
        start = (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:                                       # a manual run mid-month: this month so far
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=32)).replace(day=1)
    partial = end > now
    end = min(end, now)
    label = start.strftime("%B %Y") + (f" (1–{end.day}, so far)" if partial else "")
    return start, end, label


class Umami:
    def __init__(self, key, start, end):
        self.h = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        self.p = {"startAt": int(start.timestamp() * 1000), "endAt": int(end.timestamp() * 1000)}
        self.base = None
        for b in BASES:                         # the account's region decides which address answers
            r = requests.get(f"{b}/websites/{WEBSITE_ID}/stats", params=self.p, headers=self.h, timeout=30)
            if r.ok:
                self.base, self._stats = b, r.json()
                break
        if not self.base:
            raise RuntimeError(f"Umami API: HTTP {r.status_code} {r.text[:200]}")

    def get(self, path, **extra):
        r = requests.get(f"{self.base}/websites/{WEBSITE_ID}/{path}", params={**self.p, **extra}, headers=self.h, timeout=30)
        r.raise_for_status()
        return r.json()

    def stats(self):
        def v(k):                               # newer API: plain numbers; older: {"value": n}
            x = self._stats.get(k, 0)
            return int(x.get("value", 0) if isinstance(x, dict) else x or 0)
        return {k: v(k) for k in ("visitors", "visits", "pageviews")}

    def values(self, event, prop):
        """Counter of an event property, e.g. deal-click -> store."""
        try:
            rows = self.get("event-data/values", eventName=event, propertyName=prop)
        except requests.HTTPError:
            return Counter()
        return Counter({str(r.get("value")): int(r.get("total", 0)) for r in rows or []})

    def metric(self, type_, limit=10):
        try:
            rows = self.get("metrics", type=type_, limit=limit)
        except requests.HTTPError:
            return Counter()
        return Counter({str(r.get("x")): int(r.get("y", 0)) for r in rows or []})


def new_subscribers(start, end):
    """Confirmed sign-ups in the month, by ?ref= link (Supabase)."""
    sb, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
    if not (sb and key):
        return None, Counter()
    h = {"apikey": key}
    if key.count(".") == 2:
        h["Authorization"] = f"Bearer {key}"
    r = requests.get(f"{sb}/rest/v1/subscribers", headers=h, timeout=30, params={
        "select": "ref:profile->>ref",
        "and": f"(confirmed_at.gte.{start.astimezone(timezone.utc).isoformat()},confirmed_at.lt.{end.astimezone(timezone.utc).isoformat()})"})
    r.raise_for_status()
    rows = r.json()
    return len(rows), Counter((x.get("ref") or "no link") for x in rows)


def lines(counter, names=None, top=None):
    total = sum(counter.values()) or 1
    out = []
    for k, n in counter.most_common(top):
        out.append(f"- {(names or {}).get(k, k)}: {n:,} ({round(100 * n / total)}%)")
    return out or ["- none yet"]


def main():
    start, end, label = month_range()
    key = os.environ.get("UMAMI_API_KEY", "")
    if not key:
        print("No UMAMI_API_KEY: add it in GitHub > Settings > Secrets (Umami Cloud > Settings > API keys).")
        return 1
    u = Umami(key, start, end)
    st = u.stats()
    clicks = u.values("deal-click", "store")
    groups = u.values("deal-click", "group")
    ref_visits = u.values("ref-visit", "ref")
    signup_refs = Counter({("no link" if k == "none" else k): n for k, n in u.values("signup", "ref").items()})
    events = u.metric("event", 20)
    countries = u.metric("country", 6)
    subs, subs_by_ref = new_subscribers(start, end)
    n_clicks = sum(clicks.values())

    pitch = [f"- In {label.split(' (')[0]}, The Gear Fox sent {n:,} shoppers to {STORE_NAMES.get(s, s)}."
             for s, n in clicks.most_common(15)]
    text = "\n".join([
        f"The Gear Fox, {label}",
        "",
        "Visitors",
        f"- {st['visitors']:,} people, {st['visits']:,} visits, {st['pageviews']:,} page views",
        *[f"- {COUNTRIES.get(c, c)}: {n:,}" for c, n in countries.most_common(5)],
        "",
        "Sign-ups",
        f"- {events.get('signup', 0):,} sign-ups started, {events.get('signup-confirmed', 0):,} confirmed on the site",
        *([f"- {subs:,} new confirmed subscribers this month (Supabase)"] if subs is not None else []),
        "",
        f"Shoppers sent to stores: {n_clicks:,} clicks on deals",
        *lines(clicks, STORE_NAMES),
        "",
        "What they clicked",
        *lines(groups, GROUPS),
        "",
        "Where visitors came from (?ref= links)",
        *lines(ref_visits),
        "Sign-ups by link",
        *(lines(subs_by_ref) if subs is not None else lines(signup_refs)),
        "",
        "Ready to paste (affiliate applications, emails to shops)",
        *(pitch or ["- no clicks yet"]),
        "",
        f"Shares: {events.get('share', 0):,} · Hearts: {events.get('watch-add', 0):,} · "
        f"Language switches: {events.get('language', 0):,}",
        "Full dashboard: https://cloud.umami.is",
    ])
    print(text)
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as f:
            f.write("```\n" + text + "\n```\n")
    if DRY:
        return 0
    r = requests.post("https://api.resend.com/emails", timeout=60,
                      headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                      json={"from": FROM, "to": [TO], "subject": f"Gear Fox monthly report: {label}", "text": text})
    print(f"emailed {TO}: HTTP {r.status_code}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
