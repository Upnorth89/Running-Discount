#!/usr/bin/env python3
"""The Gear Fox watchlist alerts.

Runs once a day after the deals refresh. For every confirmed subscriber's watched product it works
out today's best price in their sizes (same rules as the site and the Saturday email), then sends
ONE email per person when something changed:
  * price drop: cheaper than the last price we told them about (at least 1% and $1 lower)
  * back in your size: out of stock in their sizes at the last check, in stock today
It then saves today's price and stock on each watch so the next run only reports new changes.

Env: RESEND_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY, SITE_URL, FROM_EMAIL, MAILING_ADDRESS
Usage: python scraper/alerts.py site/deals.json [--dry-run]
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weekly_email as W  # noqa: E402  (shares match(), branding and settings)

DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
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


def alert_row(kind, a):
    d, w = a["deal"], a["watch"]
    head = "Price drop" if kind == "drop" else "Back in your size"
    was = a.get("was")
    was_txt = (f'<span style="font-size:13px;color:#5C6660;margin-left:6px">was ${was:.2f} when we last told you</span>'
               if kind == "drop" and was else "")
    reg = (f'<span style="font-size:13px;color:#5C6660;text-decoration:line-through;margin-left:6px">${d["reg"]:.2f}</span>'
           if d["pct"] else "")
    img = (f'<img src="{E(d["img"])}" width="84" height="84" alt="" '
           f'style="display:block;width:84px;height:84px;object-fit:contain;background:#fff;border-radius:8px">') if d.get("img") else ""
    return f'''<tr><td style="padding:12px 0;border-top:1px solid #E3E7E2">
<a href="{E(d["url"])}" style="text-decoration:none;color:#17201C;display:block">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="96" valign="top">{img}</td>
<td valign="top" style="font-family:Arial,Helvetica,sans-serif">
<div style="font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#B8470A">{head}</div>
<div style="font-size:13px;font-weight:700;color:#17201C;margin-top:2px">{E(d["b"])}</div>
<div style="font-size:15px;line-height:1.3;margin:2px 0 4px">{E(d["n"])}</div>
<div><span style="font-size:20px;font-weight:800">${d["best"]:.2f}</span>{reg}{was_txt}</div>
<div style="font-size:12px;color:#5C6660;margin-top:3px">{E(W.sizes_label(d))}</div>
</td></tr></table></a></td></tr>'''


def build(sub, drops, backs):
    n = len(drops) + len(backs)
    if len(drops) == 1 and not backs:
        d = drops[0]["deal"]
        subject = f"Price drop: {d['b']} {d['n']} is now ${d['best']:.2f} in your size"
    elif len(backs) == 1 and not drops:
        d = backs[0]["deal"]
        subject = f"Back in your size: {d['b']} {d['n']}"
    else:
        subject = f"{n} items on your Gear Fox watchlist changed"
    shop = f"{W.SITE_URL}?k={sub['token']}"
    rows = "".join(alert_row("drop", a) for a in drops) + "".join(alert_row("back", a) for a in backs)
    footer = (f'<a href="{E(shop)}" style="color:#5C6660">Your watchlist</a> · '
              f'<a href="{E(W.SITE_URL)}?unsub={sub["token"]}" style="color:#5C6660">Unsubscribe</a> · '
              f'<a href="{E(W.SITE_URL)}privacy.html" style="color:#5C6660">Privacy</a>'
              + (f"<br>The Gear Fox · {E(W.ADDRESS)}" if W.ADDRESS else ""))
    body = f'''<!doctype html><html><body style="margin:0;background:#EEF1EC">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">
<tr><td style="padding:18px 20px 0;text-align:center"><a href="{E(shop)}"><img src="{E(W.SITE_URL)}logo-email.png" width="220" alt="The Gear Fox" style="display:inline-block;width:220px;max-width:70%;height:auto;border:0"></a></td></tr>
<tr><td style="padding:8px 20px 4px;text-align:center;font:800 26px Arial Narrow,Arial,sans-serif;color:#17201C">Your watchlist moved</td></tr>
<tr><td style="padding:0 20px 8px;text-align:center;font:15px/1.45 Arial,sans-serif;color:#5C6660">Things you're watching changed today, in your sizes. Prices and stock move fast.</td></tr>
<tr><td style="padding:0 20px 16px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td style="padding:14px 20px 22px;text-align:center;border-top:2px dashed #CBD2CC">
<a href="{E(shop)}" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 20px;font:800 16px Arial,sans-serif;text-decoration:none">Open your watchlist</a>
<div style="font:12px/1.4 Arial,sans-serif;color:#5C6660;margin-top:14px">You get this because you're watching these items on The Gear Fox. Remove an item from your watchlist to stop alerts about it.<br>{footer}</div></td></tr>
</table></td></tr></table></body></html>'''
    text = subject + "\n\n" + "\n".join(
        f"- {'Price drop' if a in drops else 'Back in your size'}: {a['deal']['b']} {a['deal']['n']} ${a['deal']['best']:.2f} {a['deal']['url']}"
        for a in drops + backs) + f"\n\nYour watchlist: {shop}\nUnsubscribe: {W.SITE_URL}?unsub={sub['token']}\n"
    return subject, body, text


def main():
    src = next((a for a in sys.argv[1:] if not a.startswith("--")), "site/deals.json")
    items = json.loads(Path(src).read_text()).get("items", [])
    by_key = {}
    for d in items:
        by_key.setdefault(item_key(d), []).append(d)
    if not (W.SB_URL and W.SB_KEY):
        print("Supabase not configured, no alerts")
        return 0
    rows = sb("GET", "watches", params={
        "select": "id,item_key,meta,last_price,last_in_stock,notified_price,"
                  "subscribers!inner(email,token,profile,confirmed_at,unsubscribed_at)",
        "subscribers.confirmed_at": "not.is.null", "subscribers.unsubscribed_at": "is.null"})
    print(f"{len(rows)} watched items from confirmed subscribers, {len(items)} products today")

    people, updates = {}, []
    now = datetime.now(timezone.utc).isoformat()
    for w in rows:
        s = w["subscribers"]
        deal = best_for(by_key, w["item_key"], s["profile"] or {})
        price = deal["best"] if deal else None
        upd = {"last_price": price if price is not None else w["last_price"], "last_in_stock": bool(deal)}
        p = people.setdefault(s["token"], {"sub": s, "drops": [], "backs": []})
        if deal:
            told = w["notified_price"]
            if w["last_in_stock"] is False:
                p["backs"].append({"deal": deal, "watch": w})
                upd.update(notified_price=price, notified_at=now)
            elif told is not None and price < told * 0.99 and told - price >= 1:
                p["drops"].append({"deal": deal, "watch": w, "was": float(told)})
                upd.update(notified_price=price, notified_at=now)
            elif told is None:
                upd["notified_price"] = price
        updates.append((w["id"], upd))

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
            ids = {a["watch"]["id"] for a in p["drops"] + p["backs"]}
            updates = [(i, {k: v for k, v in u.items() if k not in ("notified_price", "notified_at")}) if i in ids else (i, u)
                       for i, u in updates]

    if not DRY:
        for wid, upd in updates:
            sb("PATCH", f"watches?id=eq.{wid}", json=upd)
    print(f"alerts: {sent} sent, {failed} failed, {len(updates)} watches updated")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
