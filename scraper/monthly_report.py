#!/usr/bin/env python3
"""The Gear Fox monthly report: visitors, sign-ups and the shoppers sent to each store.

For affiliate applications and emails to shops ("In October we sent 412 shoppers to Altitude Sports").
Reads our own counts in Supabase (supabase/clicks.sql: visits and deal clicks the site logs) and new confirmed
subscribers with the ?ref= link they came from, then emails a plain-text report. (Umami's free plan has no API.)

Env:   RESEND_API_KEY, HEALTH_EMAIL (default
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


def supabase():
    sb, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
    if not (sb and key):
        raise RuntimeError("SUPABASE_URL / SUPABASE_SECRET_KEY missing")
    h = {"apikey": key, "Content-Type": "application/json"}
    if key.count(".") == 2:
        h["Authorization"] = f"Bearer {key}"
    return sb, h


def counts(start, end):
    """Visits and deal clicks from our own table (supabase/clicks.sql), already grouped."""
    sb, h = supabase()
    r = requests.post(f"{sb}/rest/v1/rpc/click_report", headers=h, timeout=60,
                      json={"p_from": start.astimezone(timezone.utc).isoformat(), "p_to": end.astimezone(timezone.utc).isoformat()})
    r.raise_for_status()
    return r.json()


def new_subscribers(start, end):
    """Confirmed sign-ups in the month, by ?ref= link."""
    sb, h = supabase()
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
    c = counts(start, end)
    clicks, groups = Counter(c.get("by_store") or {}), Counter(c.get("by_group") or {})
    ref_visits, langs = Counter(c.get("visits_by_ref") or {}), Counter(c.get("visits_by_lang") or {})
    subs, subs_by_ref = new_subscribers(start, end)
    n_clicks = int(c.get("clicks") or 0)

    pitch = [f"- In {label.split(' (')[0]}, The Gear Fox sent {n:,} shopper{'s' if n != 1 else ''} to {STORE_NAMES.get(s, s)}."
             for s, n in clicks.most_common(15)]
    text = "\n".join([
        f"The Gear Fox, {label}",
        "",
        "Visitors",
        f"- {int(c.get('visits') or 0):,} visit{'s' if int(c.get('visits') or 0) != 1 else ''}",
        *[f"- in {'French' if k == 'fr' else 'English'}: {n:,}" for k, n in langs.most_common()],
        "- Countries and pages: https://cloud.umami.is",
        "",
        "Sign-ups",
        f"- {subs:,} new confirmed subscribers",
        *lines(subs_by_ref),
        "",
        f"Shoppers sent to stores: {n_clicks:,} click{'s' if n_clicks != 1 else ''} on deals",
        *lines(clicks, STORE_NAMES),
        "",
        "What they clicked",
        *lines(groups, GROUPS),
        "",
        "Where visitors came from (?ref= links)",
        *lines(ref_visits),
        "",
        "Ready to paste (affiliate applications, emails to shops)",
        *(pitch or ["- no clicks yet"]),
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
