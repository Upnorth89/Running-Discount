#!/usr/bin/env python3
"""Noon check (Oct 8, 2026; Bastien: "2 health runs a day and a midday lite check").

No store is re-read. Around noon Vancouver it:
  1. runs the robot visitor test (tools/sitetest.py) on the LIVE site, twice when something fails (a network blip on one try
     isn't a problem), and
  2. re-checks today's featured deals on the stores' own pages (scraper/featured_check.py on the live data).
It emails only when something is wrong: a check that failed twice, or a featured sale that ended since the morning. In that
last case it also starts a site update (refresh.yml), which re-reads the stores and takes the ended sale off.

  python scraper/noon_check.py WORKDIR      env: RESEND_API_KEY, HEALTH_EMAIL, GITHUB_TOKEN (to start the update)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/noon")
SITE = "https://thegearfox.com/"
TO = os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com"
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")


def sitetest(n):
    out = WORK / f"sitetest-{n}.json"
    subprocess.run([sys.executable, str(ROOT / "tools" / "sitetest.py"), SITE, str(out)], check=False)
    try:
        return json.loads(out.read_text())
    except Exception:
        return {"checks": [], "error": "the site test didn't run"}


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    problems = []

    # 1. the robot visitor, on the live site
    first = sitetest(1)
    failed = {c["name"]: c.get("why", "") for c in first.get("checks", []) if not c["ok"]}
    if failed or not first.get("checks"):
        second = sitetest(2)
        again = {c["name"]: c.get("why", "") for c in second.get("checks", []) if not c["ok"]}
        failed = {k: v for k, v in again.items() if k in failed} if first.get("checks") else again
        if not second.get("checks"):
            problems.append("The robot visitor test couldn't run on the live site (see the log).")
    for name, why in failed.items():
        problems.append(f"Site test, {name}: {why}")
    passed = sum(c["ok"] for c in first.get("checks", []))

    # 2. today's featured deals, on the stores' own pages (on a copy of the live data)
    data = WORK / "site"
    data.mkdir(exist_ok=True)
    for f in ("sale.json", "deals.json", "sale-us.json", "deals-us.json"):
        r = requests.get(SITE + f, timeout=120)
        if r.ok:
            (data / f).write_bytes(r.content)
    env = dict(os.environ, FEATURED=str(WORK / "featured.json"))
    subprocess.run([sys.executable, str(ROOT / "scraper" / "featured_check.py"), str(data)], check=False, env=env)
    fc = json.loads((WORK / "featured.json").read_text()) if (WORK / "featured.json").exists() else {}
    ended = fc.get("removed") or []
    for e in ended:
        problems.append(f"Sale ended since this morning: {e}")
    if ended and os.environ.get("GITHUB_TOKEN"):        # a full update takes them off the site
        r = requests.post("https://api.github.com/repos/upnorth89/Running-Discount/actions/workflows/refresh.yml/dispatches",
                          headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"},
                          json={"ref": "main"}, timeout=30)
        print(f"site update started: HTTP {r.status_code}")

    summary = (f"Noon check: robot visitor {passed} of {len(first.get('checks', []))} checks passed on the live site; "
               f"featured deals {fc.get('ok', 0)} of {fc.get('checked', 0)} confirmed on the stores' pages"
               + (f", {len(ended)} ended" if ended else ""))
    print(summary + ("\n" + "\n".join(f"- {p}" for p in problems) if problems else "\nAll good: no email."))
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as f:
            f.write("## Noon check\n" + summary + "\n" + "\n".join(f"- {p}" for p in problems) + "\n")

    if problems and os.environ.get("RESEND_API_KEY"):     # quiet when all is well
        text = ("Something needs a look before the evening shoppers:\n\n" + "\n".join(f"- {p}" for p in problems) + "\n\n"
                + summary + "\n" + ("A site update was started to take the ended sales off (about 20 minutes).\n" if ended else "")
                + "\nFull log: https://github.com/upnorth89/Running-Discount/actions/workflows/noon-check.yml\n")
        r = requests.post("https://api.resend.com/emails", timeout=60,
                          headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                          json={"from": FROM, "to": [TO], "subject": f"Gear Fox noon check: {len(problems)} "
                                f"{'thing' if len(problems) == 1 else 'things'} to look at", "text": text})
        print(f"emailed {TO}: HTTP {r.status_code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
