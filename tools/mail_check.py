#!/usr/bin/env python3
"""Why didn't a sign-up email arrive? (Oct 6, 2026) Read-only: asks Resend what happened to the latest emails and the
database for recent sign-up attempts. Prints as a GitHub notice; email addresses are masked (the repo and its run notes are public).

  RESEND_API_KEY=... SUPABASE_URL=... SUPABASE_SECRET_KEY=... python tools/mail_check.py   (workflow: mail-check.yml)
"""
import os
import re
from datetime import datetime, timedelta, timezone

import requests

out = []
OWN = re.compile(r"^bastien\.hammond", re.I)


def mask(e):
    e = e or ""
    u, _, d = e.partition("@")
    if OWN.match(e):
        return u + "@…"                      # the repo is public: never the full address, even Bastien's
    return (u[:2] + "…@" + d) if d else "?"


# 2. The database: sign-up attempts (each one stamps last_mail_at) and Bastien's own test rows
sb, key = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_SECRET_KEY"]
SH = {"apikey": key}
if key.count(".") == 2:
    SH["Authorization"] = f"Bearer {key}"
since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
try:
    r = requests.get(f"{sb}/rest/v1/subscribers", headers=SH, timeout=30, params={
        "select": "email,confirmed_at,unsubscribed_at,last_mail_at", "last_mail_at": f"gte.{since}", "order": "last_mail_at.desc"})
    r.raise_for_status()
    rows = r.json()
    out.append(f"Database: {len(rows)} sign-up/sign-in emails asked for in the last 2 days "
               f"({sum(1 for x in rows if x['confirmed_at'])} of those people are confirmed):")
    for x in rows[:12]:
        e = x["email"] or ""
        odd = sorted({c for c in e if not re.match(r"[a-z0-9._%+\-@]", c, re.I)})       # what Resend may refuse ("Invalid `to`")
        flags = ([f"odd characters {odd!r}"] if odd else []) + (["two dots"] if ".." in e else []) + \
                (["starts/ends with a dot"] if re.search(r"(^\.|\.@|@\.|\.$)", e) else []) + (["not ASCII"] if not e.isascii() else [])
        out.append(f"  {str(x['last_mail_at'])[:19]}  {mask(e)}  confirmed={'yes' if x['confirmed_at'] else 'no'}"
                   + (f"  <- {', '.join(flags)}" if flags else ""))
    r = requests.get(f"{sb}/rest/v1/subscribers", headers=SH, timeout=30, params={
        "select": "email,confirmed_at,unsubscribed_at,last_mail_at", "email": "like.bastien.hammond*"})
    for x in r.json():
        out.append(f"Your address {mask(x['email'])}: confirmed={x['confirmed_at']}, unsubscribed={x['unsubscribed_at']}, last email asked {x['last_mail_at']}")
except Exception as e:
    out.append(f"Database: failed ({e})")

# 1. Resend: the domain and the latest emails it was asked to send
rk = os.environ.get("RESEND_API_KEY", "")
H = {"Authorization": f"Bearer {rk}"}
try:
    r = requests.get("https://api.resend.com/domains", headers=H, timeout=30)
    out.append(f"Resend domains: HTTP {r.status_code} " + "; ".join(
        f"{d.get('name')} {d.get('status')}" for d in (r.json().get("data") or [])) if r.ok else f"Resend domains: HTTP {r.status_code} {r.text[:160]}")
except Exception as e:
    out.append(f"Resend domains: failed ({e})")
try:
    r = requests.get("https://api.resend.com/emails", headers=H, params={"limit": 6}, timeout=30)
    if r.ok:
        rows = r.json().get("data") or []
        out.append(f"Resend: last {len(rows)} emails (newest first):")
        for m in rows:
            to = m.get("to") or []
            out.append(f"  {m.get('created_at', '')[:19]}  {m.get('last_event', '?'):>10}  to {mask(to[0] if to else '')}  "
                       f"from {m.get('from', '')[:40]}  '{(m.get('subject') or '')[:50]}'")
    else:
        out.append(f"Resend email list: HTTP {r.status_code} {r.text[:200]}")
except Exception as e:
    out.append(f"Resend email list: failed ({e})")

text = "\n".join(out)
print(text)
if os.environ.get("GITHUB_ACTIONS"):
    print("::notice title=Mail check::" + text.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
