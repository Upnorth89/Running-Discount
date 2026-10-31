#!/usr/bin/env python3
"""Send the welcome email to catch-up members who never got it (Oct 29, 2026).

The single opt-in catch-up (supabase/single-optin-oct29.sql) asked for 54 welcome emails in the same second; pg_net sends a
transaction's requests together and Resend's free plan takes 2 a second, so 41 came back 429 and were never sent. This finds the
catch-up members (consent_via = 'form-before-oct29') whose address isn't among the welcome emails Resend actually created in the
last 12 hours, and sends them the same email (same words and design as public._gf_welcome), one every 0.7 s.

  python tools/welcome_resend.py          dry run: how many would get it (masked list)
  SEND=1 python tools/welcome_resend.py   send

Needs RESEND_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY; MAILING_ADDRESS (CASL footer) when set. Never prints a whole address.
"""
import html
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

RK = os.environ.get("RESEND_API_KEY", "")
SB, SK = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
ADDR = (os.environ.get("MAILING_ADDRESS") or "").strip()
SEND = os.environ.get("SEND") == "1"
SUBJ = {"en": "Welcome to The Gear Fox", "fr": "Bienvenue sur The Gear Fox"}


def mask(e):
    u, _, d = (e or "").partition("@")
    return (u[:2] + "…@" + d) if d else "?"


def sb_headers():
    h = {"apikey": SK}
    if SK.count(".") == 2:
        h["Authorization"] = f"Bearer {SK}"
    return h


def sent_welcomes(hours=12):
    """Addresses Resend created a welcome email for in the last `hours` hours (a 429 never gets created)."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    got, after = set(), None
    for _ in range(40):
        r = requests.get("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RK}"}, timeout=30,
                         params={"limit": 100, **({"after": after} if after else {})})
        r.raise_for_status()
        js = r.json()
        rows = js.get("data") or []
        old = False
        for m in rows:
            at = datetime.fromisoformat((m.get("created_at") or "").replace(" ", "T").replace("Z", "+00:00"))
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            if at < since:
                old = True
                break
            if (m.get("subject") or "") in SUBJ.values():
                got.update(x.lower() for x in (m.get("to") or []))
        if old or not rows or not js.get("has_more"):
            break
        after = rows[-1].get("id")
        time.sleep(0.6)
    return got


def sizes_line(p, fr):
    """Same as public._gf_sizes_line."""
    out = []
    shoes = ((p.get("sizes") or {}).get("shoes") or {}).get("sizes") or []
    if shoes:
        g = p.get("gender") or ""
        lead = {"men": ("Pointure homme " if fr else "Men's shoe "), "women": ("Pointure femme " if fr else "Women's shoe ")}.get(
            g, "Pointure " if fr else "Shoe ")
        out.append(lead + ", ".join(map(str, shoes)))
    tops = ((p.get("sizes") or {}).get("tops") or {}).get("sizes") or []
    if tops:
        out.append(("vêtements " if fr else "clothing ") + ", ".join(map(str, tops)))
    return " · ".join(out) or None


def letter(title, body, button, url, fr, token):
    """Same design as public._gf_letter, with the welcome's footer (as public._gf_welcome makes it)."""
    unsub = f"https://thegearfox.com/?unsub={token}"
    foot = ((f'Ce n\'était pas vous? <a href="{unsub}" style="color:#5C6660">Se désabonner</a> en un clic.<br>'
             f'The Gear Fox · Flairez les aubaines · hello@thegearfox.com') if fr else
            (f'Not you? <a href="{unsub}" style="color:#5C6660">Unsubscribe</a> in one tap.<br>'
             f'The Gear Fox · Outfox full price · hello@thegearfox.com')) + (f"<br>{html.escape(ADDR)}" if ADDR else "")
    return ('<!doctype html><html lang="' + ("fr" if fr else "en") + '"><body style="margin:0;background:#EEF1EC">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:24px 12px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">'
            '<tr><td style="padding:22px 24px 0;text-align:center"><img src="https://thegearfox.com/' + ("logo-email-fr.png" if fr else "logo-email.png")
            + '" width="220" alt="The Gear Fox" style="width:220px;max-width:80%;height:auto;border:0"></td></tr>'
            '<tr><td style="padding:14px 24px 4px;text-align:center;font:800 24px Arial,Helvetica,sans-serif;color:#17201C">' + title + '</td></tr>'
            '<tr><td style="padding:0 24px 18px;text-align:center;font:15px/1.5 Arial,Helvetica,sans-serif;color:#5C6660">' + body + '</td></tr>'
            '<tr><td style="padding:0 24px 24px;text-align:center"><a href="' + url + '" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 22px;font:800 16px Arial,Helvetica,sans-serif;text-decoration:none">' + button + '</a></td></tr>'
            '<tr><td style="padding:14px 24px 20px;text-align:center;border-top:2px dashed #CBD2CC;font:12px/1.5 Arial,Helvetica,sans-serif;color:#5C6660">'
            + foot + '</td></tr></table></td></tr></table></body></html>')


def welcome(row):
    p = row.get("profile") or {}
    fr = p.get("lang") == "fr"
    hike = p.get("sport") == "hike"
    sz = sizes_line(p, fr)
    base = f"https://thegearfox.com/?k={row['token']}"
    if fr:
        body = (f"Chaque semaine, on vous envoie {'l’équipement de randonnée' if hike else 'l’équipement de course'} en solde dans vos tailles. "
                "Et quand un article que vous suivez baisse de prix, on vous le dit.")
        if sz:
            body += f'<br><br><b style="color:#17201C">Vos tailles :</b> {html.escape(sz)} · <a href="{base}&show=sizes" style="color:#C2410C">Modifier</a>'
        doc = letter("C'est fait!", body, "Voir mes aubaines", base, True, row["token"])
        text = f"C'est fait! Chaque semaine, vos aubaines dans vos tailles. Voir mes aubaines : {base}\nSe désabonner : https://thegearfox.com/?unsub={row['token']}"
    else:
        body = (f"Every week, we'll send you the {'hiking' if hike else 'running'} gear on sale in your sizes. "
                "And when something you watch drops in price, we'll tell you.")
        if sz:
            body += f'<br><br><b style="color:#17201C">Your sizes:</b> {html.escape(sz)} · <a href="{base}&show=sizes" style="color:#C2410C">Change</a>'
        doc = letter("You're in", body, "See my deals", base, False, row["token"])
        text = f"You're in. Every week, the gear on sale in your sizes. See my deals: {base}\nUnsubscribe: https://thegearfox.com/?unsub={row['token']}"
    return SUBJ["fr" if fr else "en"], doc, text


def main():
    if not (RK and SB and SK):
        print("needs RESEND_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY")
        return 1
    r = requests.get(f"{SB}/rest/v1/subscribers", headers=sb_headers(), timeout=30,
                     params={"select": "id,email,token,profile", "consent_via": "eq.form-before-oct29", "unsubscribed_at": "is.null"})
    r.raise_for_status()
    rows = r.json()
    got = sent_welcomes()
    todo = [x for x in rows if x["email"].lower() not in got]
    print(f"catch-up members: {len(rows)}; welcome already created by Resend: {len(rows) - len(todo)}; to send: {len(todo)}")
    ok = 0
    for x in todo:
        subj, doc, text = welcome(x)
        if not SEND:
            print(f"  would send '{subj}' to {mask(x['email'])}")
            continue
        for attempt in range(4):
            s = requests.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RK}"}, timeout=30,
                              json={"from": "Bastien from The Gear Fox <bastien@thegearfox.com>", "to": [x["email"]],
                                    "subject": subj, "html": doc, "text": text})
            if s.status_code != 429:
                break
            time.sleep(2 * (attempt + 1))
        print(f"  {mask(x['email'])}: HTTP {s.status_code}")
        if s.ok:
            ok += 1
            requests.patch(f"{SB}/rest/v1/subscribers", headers={**sb_headers(), "Content-Type": "application/json"}, timeout=30,
                           params={"id": f"eq.{x['id']}"}, json={"welcomed_at": datetime.now(timezone.utc).isoformat()})
        time.sleep(0.7)
    if SEND:
        print(f"sent {ok} of {len(todo)}")
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice title=Welcome resend::catch-up {len(rows)}, already had it {len(rows) - len(todo)}, "
              + (f"sent {ok} of {len(todo)}" if SEND else f"would send {len(todo)} (dry run)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
