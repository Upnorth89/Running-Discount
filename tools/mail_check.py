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
# Bastien's own address comes from the HEALTH_EMAIL secret (the repo is public: no personal address in the code)
OWN_USER = re.sub(r"\+.*", "", (os.environ.get("OWN_EMAIL") or "").partition("@")[0]).lower()
OWN = re.compile("^" + re.escape(OWN_USER) if OWN_USER else r"^(?!)", re.I)


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
        "select": "email,confirmed_at,unsubscribed_at,last_mail_at", "email": f"like.{OWN_USER}*"}) if OWN_USER else None
    for x in (r.json() if r is not None else []):
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

# 3. Oct 31 (Bastien: "Hotmail users aren't getting emails, a person signed up 3 times with no emails"): every Microsoft
#    address (hotmail/outlook/live/msn) in the last 30 days, in the database and in Resend's log (what Microsoft answered)
MS = re.compile(r"@(hotmail|outlook|live|msn|windowslive|passport)\.", re.I)
try:
    since30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    rows = []
    for col in ("created_at", "last_mail_at"):
        r = requests.get(f"{sb}/rest/v1/subscribers", headers=SH, timeout=30, params={
            "select": "*", col: f"gte.{since30}", "order": f"{col}.desc", "limit": "1000"})
        r.raise_for_status()
        rows += r.json()
    seen, ms = set(), []
    for x in rows:
        if MS.search(x.get("email") or "") and x["email"] not in seen:
            seen.add(x["email"])
            ms.append(x)
    out.append(f"MICROSOFT ADDRESSES (hotmail/outlook/live/msn), last 30 days in the database: {len(ms)}")
    # every new row of the last 30 days by week and by mail provider (is one provider missing since a date?)
    byw = {}
    for x in {x["email"]: x for x in rows}.values():
        if not x.get("created_at") or x["created_at"] < since30:
            continue
        d = (x["email"].partition("@")[2] or "?").lower()
        prov = "microsoft" if MS.search(x["email"]) else "gmail" if d in ("gmail.com", "googlemail.com") else \
               "yahoo" if d.startswith(("yahoo.", "ymail.", "rocketmail.")) else "apple" if d in ("icloud.com", "me.com", "mac.com") else \
               "proton" if "proton" in d else "videotron/bell/rogers/shaw/telus" if re.search(r"videotron|bell|sympatico|rogers|shaw|telus|cogeco", d) else "other"
        wk = datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")).strftime("%m-%d")
        wk = (datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) - timedelta(days=datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")).weekday())).strftime("week of %b %d")
        byw.setdefault(wk, {}).setdefault(prov, 0)
        byw[wk][prov] += 1
    others = sorted({(x["email"].partition("@")[2], str(x.get("created_at"))[:10], "member" if x.get("confirmed_at") else "not member")
                     for x in rows if x.get("created_at", "") >= since30 and not re.search(r"@(gmail|googlemail)\.com$", x["email"] or "")}, key=lambda z: z[1])
    out.append("  non-Gmail new rows (domain, day): " + "; ".join(f"{d} {day} {m}" for d, day, m in others))
    for wk in sorted(byw):
        out.append(f"  new rows {wk}: " + ", ".join(f"{k} {v}" for k, v in sorted(byw[wk].items(), key=lambda kv: -kv[1])))
    for x in ms:
        out.append("  " + mask(x["email"]) + "  " + "  ".join(f"{k}={str(x.get(k))[:16]}" for k in
                   ("created_at", "confirmed_at", "welcomed_at", "last_mail_at", "bounced_at", "complained_at", "unsubscribed_at", "consent_via") if k in x))
    seen_ids, n_ms, events, got = None, 0, {}, set()
    for page in range(10):                                  # Resend's log, newest first, 100 at a time
        r = requests.get("https://api.resend.com/emails", headers=H, params={"limit": 100, **({"after": seen_ids} if seen_ids else {})}, timeout=30)
        if not r.ok:
            out.append(f"Resend log page {page}: HTTP {r.status_code} {r.text[:120]}")
            break
        js = r.json()
        data = [m for m in (js.get("data") or []) if m.get("id") not in got]     # a page seen twice = no paging: stop
        got |= {m.get("id") for m in data}
        for m in data:
            to = (m.get("to") or [""])[0]
            if MS.search(to):
                n_ms += 1
                events[m.get("last_event", "?")] = events.get(m.get("last_event", "?"), 0) + 1
                if n_ms <= 25:
                    out.append(f"  Resend {m.get('created_at', '')[:16]}  {m.get('last_event', '?'):>10}  to {mask(to)}  '{(m.get('subject') or '')[:45]}'")
        if not js.get("has_more") or not data:
            break
        seen_ids = data[-1].get("id")
    out.append(f"Resend: {n_ms} emails to Microsoft addresses in the pages read; last status: " + (", ".join(f"{k} {v}" for k, v in events.items()) or "none"))
except Exception as e:
    out.append(f"Microsoft check: failed ({str(e)[:160]})")

# 4. Oct 31: one person, found by the sha256 of their address (or of the part before @), so the address never appears here
FIND = (os.environ.get("FIND") or "").strip().lower()
if FIND:
    import hashlib
    hx = lambda s: hashlib.sha256(s.encode()).hexdigest()
    try:
        allrows, step = [], 1000
        while True:
            r = requests.get(f"{sb}/rest/v1/subscribers", headers={**SH, "Range": f"{len(allrows)}-{len(allrows) + step - 1}"}, timeout=30,
                             params={"select": "*", "order": "created_at"})
            r.raise_for_status()
            b = r.json()
            allrows += b
            if len(b) < step:
                break
        hit = [x for x in allrows if FIND in (hx((x.get("email") or "").lower()), hx((x.get("email") or "").lower().partition("@")[0]))]
        out.append(f"LOOK-UP: {len(hit)} of {len(allrows)} database rows match")
        for x in hit:
            out.append("  " + mask(x["email"]) + "  " + "  ".join(f"{k}={str(x.get(k))[:19]}" for k in
                       ("created_at", "confirmed_at", "welcomed_at", "last_mail_at", "confirm_reminded_at", "weekly_sent_at", "bounced_at",
                        "complained_at", "unsubscribed_at", "consent_via") if k in x)
                       + f"  profile lang={(x.get('profile') or {}).get('lang')} pending_profile={'yes' if x.get('pending_profile') else 'no'}")
        n, after, got2 = 0, None, set()
        for page in range(20):
            r = requests.get("https://api.resend.com/emails", headers=H, params={"limit": 100, **({"after": after} if after else {})}, timeout=30)
            if not r.ok:
                break
            js = r.json()
            data = [m for m in (js.get("data") or []) if m.get("id") not in got2]
            got2 |= {m.get("id") for m in data}
            for m in data:
                to = ((m.get("to") or [""])[0] or "").lower()
                if FIND in (hx(to), hx(to.partition("@")[0])):
                    n += 1
                    out.append(f"  Resend {m.get('created_at', '')[:16]}  {m.get('last_event', '?'):>10}  to {mask(to)}  '{(m.get('subject') or '')[:50]}'")
            if not js.get("has_more") or not data:
                break
            after = data[-1].get("id")
        out.append(f"LOOK-UP in Resend's log ({len(got2)} emails read): {n} to this person")
    except Exception as e:
        out.append(f"LOOK-UP: failed ({str(e)[:160]})")

text = "\n".join(out)
print(text)
if os.environ.get("GITHUB_ACTIONS"):
    print("::notice title=Mail check::" + text.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
