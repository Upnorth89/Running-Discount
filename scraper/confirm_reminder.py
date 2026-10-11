#!/usr/bin/env python3
"""One reminder to confirm the email (Oct 11, 2026). In 21 days 90 people signed up and only 47 (52%) tapped the confirm link;
stores usually see 65-80%. Each morning, a sign-up that is 20-72 hours old, still not confirmed and not reminded yet gets ONE
short email (their language) with the same confirm link as the first one. Never a second reminder (confirm_reminded_at).

Needs the column from supabase/confirm-reminder-oct11.sql; until it exists this does nothing (and says so).
Env: SUPABASE_URL, SUPABASE_SECRET_KEY, RESEND_API_KEY.   Usage: python scraper/confirm_reminder.py [--dry-run]
"""
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

SB, KEY = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
RESEND = os.environ.get("RESEND_API_KEY", "")
DRY = "--dry-run" in sys.argv or not RESEND
FROM = "Bastien from The Gear Fox <bastien@thegearfox.com>"

T = {
    "en": dict(subject="One tap to start your deals", title="One tap and you're in",
               body="You asked for the running deals in your size, but your email isn't confirmed yet, so nothing can reach you. "
                    "Tap the button and your first Friday email is on its way.", button="Confirm my email",
               foot="If you didn't ask for this, ignore this email: we won't write again.<br>The Gear Fox · Outfox full price"),
    "fr": dict(subject="Un clic pour recevoir vos aubaines", title="Un clic et c'est parti",
               body="Vous avez demandé les aubaines de course dans votre pointure, mais votre courriel n'est pas encore confirmé, "
                    "donc rien ne peut vous arriver. Touchez le bouton et votre premier courriel du vendredi est en route.",
               button="Confirmer mon courriel",
               foot="Si vous n'avez rien demandé, ignorez ce courriel : on ne vous écrira plus.<br>The Gear Fox · Flairez les aubaines"),
}


def letter(lang, url):
    t = T[lang]
    logo = "logo-email-fr.png" if lang == "fr" else "logo-email.png"
    return (f'<!doctype html><html lang="{lang}"><body style="margin:0;background:#EEF1EC">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:24px 12px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">'
            f'<tr><td style="padding:22px 24px 0;text-align:center"><img src="https://thegearfox.com/{logo}" width="220" alt="The Gear Fox" style="width:220px;max-width:80%;height:auto;border:0"></td></tr>'
            f'<tr><td style="padding:14px 24px 4px;text-align:center;font:800 24px Arial,Helvetica,sans-serif;color:#17201C">{t["title"]}</td></tr>'
            f'<tr><td style="padding:0 24px 18px;text-align:center;font:15px/1.5 Arial,Helvetica,sans-serif;color:#5C6660">{t["body"]}</td></tr>'
            f'<tr><td style="padding:0 24px 24px;text-align:center"><a href="{url}" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 22px;font:800 16px Arial,Helvetica,sans-serif;text-decoration:none">{t["button"]}</a></td></tr>'
            f'<tr><td style="padding:14px 24px 20px;text-align:center;border-top:2px dashed #CBD2CC;font:12px/1.5 Arial,Helvetica,sans-serif;color:#5C6660">{t["foot"]}</td></tr>'
            '</table></td></tr></table></body></html>')


def main():
    if not (SB and KEY):
        print("confirm reminders: no Supabase key, skipped")
        return 0
    h = {"apikey": KEY, "Content-Type": "application/json"}
    if KEY.count(".") == 2:
        h["Authorization"] = f"Bearer {KEY}"
    now = datetime.now(timezone.utc)
    r = requests.get(f"{SB}/rest/v1/subscribers", headers=h, timeout=30, params=[
        ("select", "email,token,profile,pending_profile,created_at"), ("confirmed_at", "is.null"), ("unsubscribed_at", "is.null"),
        ("confirm_reminded_at", "is.null"), ("created_at", f"gte.{(now - timedelta(hours=72)).isoformat()}"),
        ("created_at", f"lte.{(now - timedelta(hours=20)).isoformat()}")])
    if r.status_code >= 400:
        print(f"confirm reminders: can't read sign-ups yet (HTTP {r.status_code}: {r.text[:120]}); paste supabase/confirm-reminder-oct11.sql")
        return 0
    rows = r.json()
    sent = 0
    for x in rows:
        prof = x.get("pending_profile") or x.get("profile") or {}
        lang = "fr" if (prof.get("lang") == "fr") else "en"
        url = f"https://thegearfox.com/?confirm={x['token']}" + ("&lang=fr" if lang == "fr" else "")
        if DRY:
            print(f"would remind ({lang}): {x['email'][:3]}…")
            continue
        m = requests.post("https://api.resend.com/emails", timeout=30, headers={"Authorization": f"Bearer {RESEND}"},
                          json={"from": FROM, "to": [x["email"]], "reply_to": "hello@thegearfox.com", "subject": T[lang]["subject"],
                                "html": letter(lang, url)})
        if m.ok:
            sent += 1
            requests.patch(f"{SB}/rest/v1/subscribers", headers={**h, "Prefer": "return=minimal"}, timeout=30,
                           params={"email": f"eq.{x['email']}"}, json={"confirm_reminded_at": now.isoformat()})
        else:
            print(f"confirm reminder not sent: HTTP {m.status_code} {m.text[:120]}")
        time.sleep(0.6)            # Resend allows 2 a second
    print(f"confirm reminders: {len(rows)} waiting, {sent} sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
