#!/usr/bin/env python3
"""The Gear Fox weekly usage report: what people did on the site last week, so we can see where they drop off,
what they look for and whether they come back. From our own analytics (supabase/analytics.sql, ana_report):
behaviour only, never who anyone is.

Env:   RESEND_API_KEY, HEALTH_EMAIL (default hello@thegearfox.com), FROM_EMAIL, SUPABASE_URL, SUPABASE_SECRET_KEY
       REPORT_DAYS (default 7)
Usage: python scraper/usage_report.py [--dry-run]   (--dry-run writes email/usage-report.html instead of emailing)
"""
import html
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monthly_report import STORE_NAMES, supabase  # same store names and database access as the monthly report

TZ = ZoneInfo("America/Vancouver")
TO = (os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com").strip()
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
E = html.escape
P = 'style="font:15px/1.5 Arial,sans-serif;color:#17201C;margin:0 0 12px"'
H = 'style="font:800 18px Arial,sans-serif;color:#B8470A;margin:26px 0 8px"'
TD = 'style="padding:5px 10px;border-bottom:1px solid #E3E7E3;font:14px Arial,sans-serif;text-align:{a}"'


def report(start, end):
    sb, h = supabase()
    r = requests.post(f"{sb}/rest/v1/rpc/ana_report", headers=h, timeout=60,
                      json={"p_from": start.astimezone(timezone.utc).isoformat(), "p_to": end.astimezone(timezone.utc).isoformat()})
    r.raise_for_status()
    return r.json()


def pct(a, b):
    return f"{round(100 * a / b)}%" if b else "–"


def table(head, rows, align=None):
    align = align or ["left"] + ["right"] * (len(head) - 1)
    th = "".join(f'<th {TD.format(a=a)}><b>{E(str(x))}</b></th>' for x, a in zip(head, align))
    tr = "".join("<tr>" + "".join(f'<td {TD.format(a=a)}>{x}</td>' for x, a in zip(row, align)) + "</tr>" for row in rows)
    return f'<table style="border-collapse:collapse;margin:0 0 12px">{"<tr>" + th + "</tr>"}{tr}</table>' if rows else f"<p {P}>Nothing yet.</p>"


def store(d):
    return STORE_NAMES.get(d, d)


def build(d, start, end):
    out, insights = [], []
    f = d.get("funnel_new") or {}
    ret = d.get("returning") or {}
    n_new = f.get("sessions", 0)
    # 1. the week in numbers
    dev = d.get("by_dev") or {}
    lang = d.get("by_lang") or {}
    secs = d.get("median_secs")
    out.append(f'<div {H}>The week in numbers</div><p {P}><b>{d.get("devices", 0)}</b> people (devices), '
               f'<b>{d.get("new_devices", 0)}</b> of them new · <b>{d.get("sessions", 0)}</b> visits · '
               f'phone {dev.get("phone", 0)}, computer {dev.get("computer", 0)}, tablet {dev.get("tablet", 0)} · '
               f'English {lang.get("en", 0)}, French {lang.get("fr", 0)}'
               + (f' · typical visit <b>{round(secs)} s</b>' if secs else "") + "</p>")
    # 2. new visitors: where they drop off
    steps = [("Arrived", n_new), ("Saw the welcome", f.get("welcome", 0)), ("Picked their sizes", f.get("sizes", 0)),
             ("Saw their deals", f.get("peek", 0)), ("Signed up", f.get("signup", 0))]
    rows, worst = [], None
    for i, (name, n) in enumerate(steps):
        prev = steps[i - 1][1] if i else n
        lost = prev - n if i else 0
        if i and prev and (worst is None or lost / prev > worst[2]):
            worst = (steps[i - 1][0], name, lost / prev)
        rows.append([E(name), str(n), pct(n, n_new), f"−{lost}" if i and lost else ""])
    out.append(f'<div {H}>New visitors: where they drop off</div>' + table(["Step", "Visits", "of arrivals", "lost"], rows) +
               f'<p {P}>Clicked at least one deal: <b>{f.get("clicked", 0)}</b> ({pct(f.get("clicked", 0), n_new)}).</p>')
    if worst and n_new >= 10:
        insights.append(f"The biggest drop is between <b>{E(worst[0].lower())}</b> and <b>{E(worst[1].lower())}</b> "
                        f"({round(100 * worst[2])}% stop there). That's the step to make easier.")
    # 3. returning visitors
    rs = ret.get("sessions", 0)
    out.append(f'<div {H}>People who came back</div><p {P}><b>{rs}</b> return visits · clicked a deal in {pct(ret.get("clicked", 0), rs)} · '
               f'hearted something in {pct(ret.get("hearted", 0), rs)} · searched in {pct(ret.get("searched", 0), rs)}</p>')
    coh = d.get("cohorts") or []
    out.append(table(["First visit (week of)", "New devices", "Came back", "Back after 7+ days", "3+ days active", "Signed up"],
                     [[c["week"], str(c["devices"]), pct(c["came_back"], c["devices"]), pct(c["back_after_7d"], c["devices"]),
                       pct(c["active_3_days"], c["devices"]), pct(c["signed_up"], c["devices"])] for c in coh]))
    # 4. where they come from
    refs = d.get("by_ref") or []
    out.append(f'<div {H}>Where they came from</div>' + table(
        ["Link", "Visits", "Picked sizes", "Signed up", "Clicked a deal"],
        [[E(r["ref"]), str(r["sessions"]), pct(r["sizes"], r["sessions"]), pct(r["signups"], r["sessions"]), pct(r["clicked"], r["sessions"])]
         for r in refs[:12]]))
    best = max((r for r in refs if r["sessions"] >= 10), key=lambda r: r["signups"] / r["sessions"], default=None)
    if best and best["signups"]:
        insights.append(f"Best source for sign-ups: <b>{E(best['ref'])}</b> ({pct(best['signups'], best['sessions'])} of its visits signed up).")
    ent = d.get("entry") or []
    out.append(f'<p {P}><b>First page they landed on</b></p>' + table(["Page", "Visits", "Clicked a deal"],
               [[E(e["page"]), str(e["sessions"]), pct(e["clicked"], e["sessions"])] for e in ent[:10]]))
    # 5. what they look for
    top = d.get("top") or {}
    none = top.get("search-none") or []
    out.append(f'<div {H}>What they searched for</div>' + table(["Search", "Times", "Results"],
               [[E(x["d"] or ""), str(x["n"]), "found"] for x in (top.get("search") or [])[:12]] +
               [[E(x["d"] or ""), str(x["n"]), "<b>nothing</b>"] for x in none[:12]]))
    if none:
        insights.append(f"Searched with no result: <b>{E(', '.join(x['d'] or '' for x in none[:5]))}</b>. Brands or stores to add?")
    # 6. what they click
    pos = d.get("click_positions") or {}
    clicks = top.get("deal-click") or []
    by_store, by_group = {}, {}
    for x in clicks:
        parts = (x["d"] or "").split("|")
        by_store[parts[0]] = by_store.get(parts[0], 0) + x["n"]
        if len(parts) > 1 and parts[1]:
            by_group[parts[1]] = by_group.get(parts[1], 0) + x["n"]
    out.append(f'<div {H}>What they clicked</div><p {P}>Deal clicks by card position: ' +
               " · ".join(f"{k}: <b>{pos.get(k, 0)}</b>" for k in ("1-6", "7-12", "13-24", "25+")) + "</p>" +
               table(["Store", "Clicks"], [[E(store(k)), str(v)] for k, v in sorted(by_store.items(), key=lambda kv: -kv[1])[:10]]) +
               f'<p {P}>By category: ' + " · ".join(f"{E(k)} {v}" for k, v in sorted(by_group.items(), key=lambda kv: -kv[1])) + "</p>")
    for kind, label in (("category", "Category buttons"), ("filter", "Filters"), ("sort", "Sort"), ("menu", "☰ menu"),
                        ("shoe-page-view", "Shoe pages viewed"), ("shoe-page-size", "Sizes picked on shoe pages"),
                        ("watch-add", "Hearted"), ("share", "Shared")):
        items = top.get(kind) or []
        if items:
            out.append(f'<p {P}><b>{label}:</b> ' + " · ".join(f"{E(x['d'] or '–')} ({x['n']})" for x in items[:10]) + "</p>")
    sc = d.get("scroll") or {}
    if sc:
        out.append(f'<p {P}><b>How far down they scrolled:</b> ' + " · ".join(f"{k}%: {sc.get(k, 0)}" for k in ("25", "50", "75", "100")) + "</p>")
    errs = top.get("error") or []
    if errs:
        out.append(f'<div {H}>Errors seen on visitors\' screens</div><p {P}>Claude should look at these.</p>' +
                   table(["Error", "Times", "Devices"], [[E(x["d"] or ""), str(x["n"]), str(x["devices"])] for x in errs[:8]]))
    head = (f'<p {P}>Hi Bastien, here\'s how people used thegearfox.com from {start:%b %-d} to {(end - timedelta(seconds=1)):%b %-d}. '
            "Behaviour only: no names or emails are ever recorded.</p>")
    if insights:
        head += f'<div {H}>What this tells us</div><ul style="font:15px/1.5 Arial,sans-serif;padding-left:20px">' + "".join(f"<li>{x}</li>" for x in insights) + "</ul>"
    return f'<div style="max-width:680px;margin:0 auto;padding:18px">{head}{"".join(out)}' \
           f'<p style="font:12px Arial,sans-serif;color:#5C6660;margin-top:24px">Sent every Monday (scraper/usage_report.py). Only to you.</p></div>'


def main():
    days = int(os.environ.get("REPORT_DAYS") or 7)
    end = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    body = build(report(start, end), start, end)
    if DRY:
        out = Path(__file__).resolve().parent.parent / "email" / "usage-report.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(body)
        print(f"DRY RUN: wrote {out}")
        return 0
    r = requests.post("https://api.resend.com/emails", timeout=60, headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                      json={"from": FROM, "to": [TO], "subject": f"How people used The Gear Fox ({start:%b %-d}–{(end - timedelta(days=1)):%b %-d})",
                            "html": body})
    print(f"emailed {TO}: HTTP {r.status_code} {r.text[:200]}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
