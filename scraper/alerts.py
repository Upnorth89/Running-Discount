#!/usr/bin/env python3
"""The Gear Fox watchlist alerts.

Runs once a day after the deals refresh. For every confirmed subscriber's watched product it works
out today's best price in their sizes (same rules as the site and the Saturday email), then sends
ONE email per person when something changed:
  * price drop: at least 10% or $10 below the last price we told them about
  * back in your size: out of stock in their sizes at the last check, in stock today
Rules that keep email volume low:
  * at most one alert every 3 days per person (changes in between wait and go out together)
  * no alerts on Saturdays: the Saturday deals email carries the watchlist news instead
It then saves today's price and stock on each watch so the next run only reports new changes.

Env: RESEND_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY, SITE_URL, FROM_EMAIL, MAILING_ADDRESS
Usage: python scraper/alerts.py site/deals.json [--dry-run]
"""
import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weekly_email as W  # noqa: E402  (shares match(), branding and settings)

FORCE = "--any-day" in sys.argv
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
COOLDOWN_H = 70           # "every 3 days" with a little slack for run times
TZ = "America/Vancouver"
E = W.E
ALL_GROUPS = list(W.GROUP_LABEL)


def item_key(d):
    """Stable id for a product across days; the site builds the same string."""
    return f"{d['b']}|{d['n']}|{d['g']}|{1 if d.get('w') else 0}".lower()


def sb(method, path, **kw):
    h = {"apikey": W.SB_KEY, "Content-Type": "application/json"}
    if W.SB_KEY.count(".") == 2:
        h["Authorization"] = f"Bearer {W.SB_KEY}"
    r = requests.request(method, f"{W.SB_URL}/rest/v1/{path}", headers=h, timeout=60, **kw)
    r.raise_for_status()
    return r.json() if r.text else None


def best_for(items_by_key, key, profile):
    """Today's best offer for this product in the person's sizes, or None if not in stock for them."""
    cands = items_by_key.get(key) or []
    p = {**profile, "groups": ALL_GROUPS}          # a watch counts even if they filtered that category out
    hits = W.match(cands, p)
    return min(hits, key=lambda d: d["best"]) if hits else None


A_STR = {
    "en": dict(drop="Price drop", back="Back in your size", was="was {} when we last told you",
               subj_drop=lambda b, n, m: f"Price drop: {b} {n} is now {m} in your size",
               subj_back=lambda b, n: f"Back in your size: {b} {n}",
               subj_many=lambda k: f"{k} items on your Gear Fox watchlist changed",
               watchlist="Your watchlist", title="Your watchlist moved",
               intro="Things you're watching changed today, in your sizes. Prices and stock move fast.",
               button="Open your watchlist",
               fine="You get this because you're watching these items on The Gear Fox. Remove an item from your watchlist to stop alerts about it."),
    "fr": dict(drop="Baisse de prix", back="De retour dans votre taille", was="était à {} à notre dernier avis",
               subj_drop=lambda b, n, m: f"Baisse de prix : {b} {n} maintenant à {m} dans votre taille",
               subj_back=lambda b, n: f"De retour dans votre taille : {b} {n}",
               subj_many=lambda k: f"{k} articles de vos favoris The Gear Fox ont changé",
               watchlist="Vos favoris", title="Vos favoris ont bougé",
               intro="Des articles de vos favoris ont changé aujourd'hui, dans vos tailles. Les prix et les stocks bougent vite.",
               button="Voir mes favoris",
               fine="Vous recevez ce courriel parce que ces articles sont dans vos favoris sur The Gear Fox. Retirez un article de vos favoris pour ne plus recevoir d'alertes à son sujet."),
}


def at(lang, key, *a):
    v = A_STR[lang][key]
    return v(*a) if callable(v) else (v.format(*a) if a else v)


def alert_row(kind, a, lang="en"):
    d = a["deal"]
    money = lambda v: W.money(v, lang)
    head = at(lang, "drop") if kind == "drop" else at(lang, "back")
    was = a.get("was")
    was_txt = (f'<span style="font-size:13px;color:#5C6660;margin-left:6px">{E(at(lang, "was", money(was)))}</span>'
               if kind == "drop" and was else "")
    reg = (f'<span style="font-size:13px;color:#5C6660;text-decoration:line-through;margin-left:6px">{money(d["reg"])}</span>'
           if d["pct"] else "")
    img = (f'<img src="{E(d["img"])}" width="84" height="84" alt="" '
           f'style="display:block;width:84px;height:84px;object-fit:contain;background:#fff;border-radius:8px">') if d.get("img") else ""
    return f'''<tr><td style="padding:12px 0;border-top:1px solid #E3E7E2">
<a href="{E(d["url"])}" style="text-decoration:none;color:#17201C;display:block">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="96" valign="top">{img}</td>
<td valign="top" style="font-family:Arial,Helvetica,sans-serif">
<div style="font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#B8470A">{E(head)}</div>
<div style="font-size:13px;font-weight:700;color:#17201C;margin-top:2px">{E(d["b"])}</div>
<div style="font-size:15px;line-height:1.3;margin:2px 0 4px">{E(d["n"])}</div>
<div><span style="font-size:20px;font-weight:800">{money(d["best"])}</span>{reg}{was_txt}</div>
<div style="font-size:12px;color:#5C6660;margin-top:3px">{E(W.sizes_label(d, lang))}</div>
</td></tr></table></a></td></tr>'''


def build(sub, drops, backs):
    lang = W.lang_of(sub.get("profile"))
    n = len(drops) + len(backs)
    if len(drops) == 1 and not backs:
        d = drops[0]["deal"]
        subject = at(lang, "subj_drop", d["b"], d["n"], W.money(d["best"], lang))
    elif len(backs) == 1 and not drops:
        d = backs[0]["deal"]
        subject = at(lang, "subj_back", d["b"], d["n"])
    else:
        subject = at(lang, "subj_many", n)
    shop = f"{W.SITE_URL}?k={sub['token']}"
    rows = "".join(alert_row("drop", a, lang) for a in drops) + "".join(alert_row("back", a, lang) for a in backs)
    footer = (f'<a href="{E(shop)}" style="color:#5C6660">{E(at(lang, "watchlist"))}</a> · '
              f'<a href="{E(W.SITE_URL)}?unsub={sub["token"]}" style="color:#5C6660">{E(W.tr(lang, "unsubscribe"))}</a> · '
              f'<a href="{E(W.SITE_URL)}privacy.html" style="color:#5C6660">{E(W.tr(lang, "privacy"))}</a>'
              + (f"<br>The Gear Fox · {E(W.ADDRESS)}" if W.ADDRESS else ""))
    body = f'''<!doctype html><html lang="{lang}"><body style="margin:0;background:#EEF1EC">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">
<tr><td style="padding:18px 20px 0;text-align:center"><a href="{E(shop)}"><img src="{E(W.SITE_URL)}{W.tr(lang, "logo")}" width="220" alt="The Gear Fox" style="display:inline-block;width:220px;max-width:70%;height:auto;border:0"></a></td></tr>
<tr><td style="padding:8px 20px 4px;text-align:center;font:800 26px Arial Narrow,Arial,sans-serif;color:#17201C">{E(at(lang, "title"))}</td></tr>
<tr><td style="padding:0 20px 8px;text-align:center;font:15px/1.45 Arial,sans-serif;color:#5C6660">{E(at(lang, "intro"))}</td></tr>
<tr><td style="padding:0 20px 16px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td style="padding:14px 20px 22px;text-align:center;border-top:2px dashed #CBD2CC">
<a href="{E(shop)}" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 20px;font:800 16px Arial,sans-serif;text-decoration:none">{E(at(lang, "button"))}</a>
<div style="font:12px/1.4 Arial,sans-serif;color:#5C6660;margin-top:14px">{E(at(lang, "fine"))}<br>{footer}</div></td></tr>
</table></td></tr></table></body></html>'''
    text = subject + "\n\n" + "\n".join(
        f"- {at(lang, 'drop') if a in drops else at(lang, 'back')}: {a['deal']['b']} {a['deal']['n']} {W.money(a['deal']['best'], lang)} {a['deal']['url']}"
        for a in drops + backs) + (f"\n\n{at(lang, 'watchlist')}: {shop}\n{W.tr(lang, 'unsubscribe')}: {W.SITE_URL}?unsub={sub['token']}\n")
    return subject, body, text


def fetch_rows():
    return sb("GET", "watches", params={
        "select": "id,item_key,meta,last_price,last_in_stock,notified_price,notified_at,"
                  "subscribers!inner(email,token,profile,confirmed_at,unsubscribed_at)",
        "subscribers.confirmed_at": "not.is.null", "subscribers.unsubscribed_at": "is.null"})


def is_drop(told, price):
    return told is not None and price is not None and (told - price >= 10 or price <= float(told) * 0.90)


def evaluate(rows, by_key, now, cooldown=True):
    """Per person: what to tell them and how to update their watches.
    Returns {token: {"sub", "drops", "backs", "updates": [(id, fields)], "held": bool}}."""
    people = {}
    for w in rows:
        s = w["subscribers"]
        people.setdefault(s["token"], {"sub": s, "rows": []})["rows"].append(w)
    iso = now.isoformat()
    for tok, p in people.items():
        last = max((datetime.fromisoformat(r["notified_at"]) for r in p["rows"] if r.get("notified_at")), default=None)
        p.update(drops=[], backs=[], updates=[], held=False)
        plain = []
        for w in p["rows"]:
            deal = best_for(by_key, w["item_key"], p["sub"]["profile"] or {})
            price = deal["best"] if deal else None
            upd = {"last_price": price if price is not None else w["last_price"], "last_in_stock": bool(deal)}
            if deal and w["last_in_stock"] is False:
                p["backs"].append({"deal": deal, "watch": w})
                upd.update(notified_price=price, notified_at=iso)
            elif deal and is_drop(w["notified_price"] and float(w["notified_price"]), price):
                p["drops"].append({"deal": deal, "watch": w, "was": float(w["notified_price"])})
                upd.update(notified_price=price, notified_at=iso)
            elif deal and w["notified_price"] is None:
                upd["notified_price"] = price
            plain.append((w["id"], upd))
        recent = last is not None and (now - last).total_seconds() < COOLDOWN_H * 3600
        if (p["drops"] or p["backs"]) and cooldown and recent:
            p.update(drops=[], backs=[], held=True)       # wait: nothing updated, so the changes keep
        else:
            p["updates"] = plain
        del p["rows"]
    return people


def main():
    src = next((a for a in sys.argv[1:] if not a.startswith("--")), "site/deals.json")
    items = json.loads(Path(src).read_text()).get("items", [])
    by_key = {}
    for d in items:
        by_key.setdefault(item_key(d), []).append(d)
    if not (W.SB_URL and W.SB_KEY):
        print("Supabase not configured, no alerts")
        return 0
    rows = fetch_rows()
    print(f"{len(rows)} watched items from confirmed subscribers, {len(items)} products today")

    now = datetime.now(timezone.utc)
    if not FORCE and now.astimezone(ZoneInfo(TZ)).weekday() == 5:
        print("Saturday: no alerts today, the Saturday email carries watchlist news")
        return 0
    people = evaluate(rows, by_key, now)
    updates = []
    for p in people.values():
        updates += p["updates"]
    sent = failed = 0
    for tok, p in people.items():
        if not (p["drops"] or p["backs"]):
            continue
        subject, body, text = build(p["sub"], p["drops"], p["backs"])
        who = p["sub"]["email"]
        if DRY:
            (W.ROOT / "email" / "alert-preview.html").write_text(body)
            print(f"{who}: DRY RUN {subject!r}")
            continue
        r = requests.post("https://api.resend.com/emails", timeout=60,
                          headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                          json={"from": W.FROM, "to": [who], "subject": subject, "html": body, "text": text,
                                "headers": {"List-Unsubscribe": f"<{W.SITE_URL}?unsub={tok}>"}})
        if r.ok:
            sent += 1
            print(f"{who}: sent {len(p['drops'])} drops, {len(p['backs'])} back in size")
        else:
            failed += 1
            print(f"{who}: FAILED {r.status_code} {r.text[:200]}")
            # keep their notified prices as they were so tomorrow retries
            ids = {i for i, _ in p["updates"]}
            updates = [(i, u) for i, u in updates if i not in ids]

    if not DRY:
        for wid, upd in updates:
            sb("PATCH", f"watches?id=eq.{wid}", json=upd)
    held = sum(1 for p in people.values() if p["held"])
    print(f"alerts: {sent} sent, {failed} failed, {held} waiting for their 3-day gap, {len(updates)} watches updated")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
