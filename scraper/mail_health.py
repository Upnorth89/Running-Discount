#!/usr/bin/env python3
"""Bounces and complaints (Oct 29, 2026; single opt-in, Bastien: "Yes on each").

With single opt-in a typo'd or made-up address becomes a member at once, so every morning we read Resend's own record of the
emails it sent (GET /emails, newest first, last 7 days) and:
  * stop all email to an address that hard-bounced or marked us as spam (unsubscribed_at + bounced_at / complained_at);
  * report the week's numbers: health email (morning) and the Monday usage report, flagged at a bounce rate over 4% or any
    complaint (Resend and Gmail start filtering senders well before 5% bounces / 0.3% complaints).

  python scraper/mail_health.py            print the week's numbers (and mark bad addresses when the keys are there)

Needs RESEND_API_KEY; SUPABASE_URL + SUPABASE_SECRET_KEY to mark addresses. Never prints a whole address.
"""
import os
from datetime import datetime, timedelta, timezone

import requests

BOUNCE_WARN = 0.04
DAYS = 7


def mask(e):
    u, _, d = (e or "").partition("@")
    return (u[:2] + "…@" + d) if d else "?"


def read(days=DAYS):
    """Resend's emails of the last `days` days: (sent, bounced [(email, at)], complained [(email, at)])."""
    key = os.environ.get("RESEND_API_KEY", "")
    if not key:
        return None
    since = datetime.now(timezone.utc) - timedelta(days=days)
    sent, bounced, complained, after = 0, [], [], None
    for _ in range(40):                                   # 40 pages x 100 = 4,000 emails, more than a week's worth today
        params = {"limit": 100, **({"after": after} if after else {})}
        r = requests.get("https://api.resend.com/emails", headers={"Authorization": f"Bearer {key}"}, params=params, timeout=30)
        r.raise_for_status()
        js = r.json()
        rows = js.get("data") or []
        old = False
        for m in rows:
            try:
                at = datetime.fromisoformat((m.get("created_at") or "").replace(" ", "T").replace("Z", "+00:00"))
            except ValueError:
                continue
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            if at < since:
                old = True
                break
            sent += 1
            ev = (m.get("last_event") or "").lower()
            to = (m.get("to") or [""])[0].lower()
            if ev == "bounced":
                bounced.append((to, at))
            elif ev == "complained":
                complained.append((to, at))
        if old or not rows or not js.get("has_more"):
            break
        after = rows[-1].get("id")
    return sent, bounced, complained


def suppress(bounced, complained):
    """Mark the addresses in Supabase so no email goes to them again. Returns how many rows changed."""
    sb, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
    if not (sb and key):
        return 0
    h = {"apikey": key, "Content-Type": "application/json", "Prefer": "return=representation"}
    if key.count(".") == 2:
        h["Authorization"] = f"Bearer {key}"
    n = 0
    for (e, at), kind in [(x, "bounced") for x in bounced] + [(x, "complained") for x in complained]:
        if not e:
            continue
        # unsubscribed_at stops the Friday email and alerts with no change to those jobs; bounced_at/complained_at say why
        body = {f"{kind}_at": at.isoformat(), "unsubscribed_at": at.isoformat()}
        r = requests.patch(f"{sb}/rest/v1/subscribers", headers=h, timeout=30, json=body,
                           params={"email": f"eq.{e}", f"{kind}_at": "is.null"})
        if r.ok:
            n += len(r.json() or [])
    return n


def summary():
    """(line for the reports, [problems as (key, text)]) or (None, []) without a Resend key."""
    try:
        got = read()
    except Exception as e:
        return f"- Email bounces: couldn't read Resend ({str(e)[:80]})\n", []
    if got is None:
        return None, []
    sent, bounced, complained = got
    try:
        marked = suppress(bounced, complained)
    except Exception as e:
        print(f"suppress failed: {e}")
        marked = 0
    rate = len(bounced) / sent if sent else 0
    line = (f"- Email, last {DAYS} days: {sent} sent, {len(bounced)} bounced ({rate:.1%}), {len(complained)} marked as spam"
            + (f"; {marked} addresses newly stopped" if marked else "") + "\n")
    probs = []
    if sent >= 20 and rate > BOUNCE_WARN:
        probs.append(("bounce", f"{rate:.0%} of our emails bounced in the last {DAYS} days ({len(bounced)} of {sent}): typo'd "
                                f"or made-up sign-ups. Those addresses are stopped; if it keeps climbing, we go back to confirming emails."))
    for e, at in complained:
        probs.append((f"complaint:{mask(e)}", f"Someone ({mask(e)}) marked our email as spam on {at:%b %d}: they're unsubscribed."))
    return line, probs


if __name__ == "__main__":
    line, probs = summary()
    print(line or "no RESEND_API_KEY")
    for _, p in probs:
        print("!", p)
