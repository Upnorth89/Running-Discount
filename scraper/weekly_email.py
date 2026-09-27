#!/usr/bin/env python3
"""The Gear Fox weekly sale email.

Reads today's deals.json (the live site's copy) and each profile in email/profiles.json, finds
the gear on sale in that person's sizes (same matching rules as the Shop page), and emails it
through Resend (https://resend.com, free tier).

Env:
  RESEND_API_KEY   required to send (without it the email is only written to email/preview.html)
  DEALS_URL        where to read deals.json (default: the site's own copy)
  SITE_URL         link to the site in the email
  FROM_EMAIL       sender, default "The Gear Fox <deals@thegearfox.com>"
  SUPABASE_URL, SUPABASE_SECRET_KEY
                   where subscribers who signed up on the site live (confirmed and not unsubscribed)
  MAILING_ADDRESS  postal address for the footer (required by Canada's anti-spam law, CASL)

Subscribers come from Supabase plus email/profiles.json (the database wins if an address is in both).

Usage: python scraper/weekly_email.py [--dry-run]
"""
import html
import json
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/") + "/"
DEALS_URL = os.environ.get("DEALS_URL") or (SITE_URL + "deals.json" if SITE_URL != "/" else "")
FROM = os.environ.get("FROM_EMAIL", "The Gear Fox <deals@thegearfox.com>")
SB_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
ADDRESS = os.environ.get("MAILING_ADDRESS", "").strip()

GROUP_LABEL = {"shoes": "Shoes", "tops": "Tops & jackets", "bottoms": "Shorts & tights", "bras": "Sports bras",
               "socks": "Socks", "gloves": "Gloves", "headwear": "Hats & buffs", "packs": "Vests & packs",
               "gear": "Lights, poles & bottles", "watches": "Watches", "nutrition": "Nutrition"}
SIZED = {"shoes", "tops", "bottoms", "bras", "socks", "gloves", "headwear"}
PER_GROUP, TOTAL = 6, 36

WORD = {"ONE SIZE": "OS", "O/S": "OS", "X-SMALL": "XS", "XSMALL": "XS", "SMALL": "S", "MEDIUM": "M",
        "LARGE": "L", "X-LARGE": "XL", "XLARGE": "XL"}
def norm(s):
    s = str(s).strip().upper()
    s = WORD.get(s, s)
    return s.replace("XXXL", "3XL").replace("XXL", "2XL").replace("XXS", "2XS")

def match(items, p):
    """Mirror of matchItems() on the site: items in stock in the profile's sizes, with best price."""
    favs = {b.lower() for b in p.get("brands") or []}
    groups, gender = set(p.get("groups") or []), p.get("gender")
    ca_only = (p.get("ships") or "ca") != "all"
    out = []
    for d in items:
        if d["g"] not in groups:
            continue
        if ca_only and d.get("ca") is False:
            continue
        if gender and gender != "any" and d["sx"] and gender not in d["sx"]:
            continue
        ok = d["sz"]
        if d["g"] in SIZED:
            spec = (p.get("sizes") or {}).get(d["g"]) or {}
            want = {norm(x) for x in spec.get("sizes") or []}
            if d["g"] == "shoes":
                w = spec.get("width") or []
                wide, reg = "Wide" in w, (not w or "Regular" in w)
                if (d["w"] and not wide) or (not d["w"] and not reg):
                    continue
            ok = [e for e in d["sz"] if e[0] == "OS" or norm(e[0]) in want]
        if not ok:
            continue
        pick = min(ok, key=lambda e: (e[1], -(e[3] if len(e) > 3 else e[1])))
        best = pick[1]
        reg = max(pick[3] if len(pick) > 3 else best, best)
        if p.get("max_price") and best > p["max_price"]:
            continue
        pct = round(100 * (1 - best / reg)) if reg > best else 0
        out.append({**d, "best": best, "reg": reg, "pct": pct, "ok": ok,
                    "url": d["of"][pick[2]] if len(d["of"]) > pick[2] else d["of"][0],
                    "fav": d["b"].lower() in favs})
    return out

def sizes_label(d):
    labels = list(dict.fromkeys(e[0] for e in d["ok"]))
    if d["g"] in SIZED:
        order = ["2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL"]
        def k(v):
            try:
                return (0, float(v))
            except ValueError:
                return (1, order.index(norm(v)) if norm(v) in order else 99)
        labels.sort(key=k)
        return "Your size: " + ", ".join(labels)
    if labels and labels[0] != "OS":
        return " · ".join(labels[:3]) + (" · …" if len(labels) > 3 else "")
    return ""

E = html.escape
def card(d):
    img = (f'<img src="{E(d["img"])}" width="84" height="84" alt="" '
           f'style="display:block;width:84px;height:84px;object-fit:contain;background:#fff;border-radius:8px">') if d.get("img") else ""
    fav = " ★" if d["fav"] else ""
    sz = sizes_label(d)
    bb = f'<div style="font-size:12px;color:#B3261E;font-weight:600">Best by {E(d["bb"])}</div>' if d.get("bb") else ""
    if d.get("ca") is False:
        bb += '<div style="font-size:12px;color:#5C6660">Ships from outside Canada · converted to CAD, duties may apply</div>'

    return f'''<tr><td style="padding:10px 0;border-top:1px solid #E3E7E2">
<a href="{E(d["url"])}" style="text-decoration:none;color:#17201C;display:block">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="96" valign="top">{img}</td>
<td valign="top" style="font-family:Arial,Helvetica,sans-serif">
<div style="font-size:13px;font-weight:700;color:#B8470A">{E(d["b"])}{fav}</div>
<div style="font-size:15px;line-height:1.3;margin:2px 0 4px">{E(d["n"])}</div>
<div><span style="font-size:20px;font-weight:800">${d["best"]:.2f}</span>
<span style="font-size:13px;color:#5C6660;text-decoration:line-through;margin-left:6px">${d["reg"]:.2f}</span>
<span style="font-size:13px;font-weight:800;background:#F26A1B;border:1px solid #17201C;border-radius:4px;padding:1px 5px;margin-left:6px">−{d["pct"]}%</span></div>
<div style="font-size:12px;color:#5C6660;margin-top:3px">{E(sz)}</div>{bb}
</td></tr></table></a></td></tr>'''

def shop_link(p):
    """Site link that opens this person's tailored shop on any device."""
    import base64
    if p.get("token"):
        return f"{SITE_URL}?k={p['token']}"      # private key: loads their saved profile from the database
    keep = {k: p.get(k) for k in ("name", "gender", "ships", "activities", "groups", "sizes", "brands", "max_price")}
    b = base64.urlsafe_b64encode(json.dumps(keep, separators=(",", ":")).encode()).decode().rstrip("=")
    return f"{SITE_URL}?p={b}"          # query string survives email link-wrappers better than #

def build(p, sale, watch=None):
    shop = shop_link(p)
    first = (p.get("name") or "").split(" ")[0] or "Hi"
    sale.sort(key=lambda d: (-d["fav"], -d["pct"], d["best"]))
    sections, shown = [], 0
    order = [g for g in GROUP_LABEL if g in set(p.get("groups") or [])]
    for g in order:
        ds = [d for d in sale if d["g"] == g]
        if not ds or shown >= TOTAL:
            continue
        take = ds[:min(PER_GROUP, TOTAL - shown)]
        shown += len(take)
        more = (f'<tr><td style="padding:6px 0 0;font:13px Arial,sans-serif"><a href="{E(shop)}" style="color:#B8470A">'
                f'See all {len(ds)} on sale →</a></td></tr>') if len(ds) > len(take) else ""
        sections.append(f'''<tr><td style="padding:22px 0 4px;font:800 20px Arial,Helvetica,sans-serif;color:#17201C">
{E(GROUP_LABEL[g])} <span style="font:400 14px Arial,sans-serif;color:#5C6660">{len(ds)}</span></td></tr>
{"".join(card(d) for d in take)}{more}''')
    if watch and (watch["drops"] or watch["backs"]):
        import alerts as A
        rows = "".join(A.alert_row("drop", a) for a in watch["drops"]) + "".join(A.alert_row("back", a) for a in watch["backs"])
        n = len(watch["drops"]) + len(watch["backs"])
        sections.insert(0, f'''<tr><td style="padding:22px 0 4px;font:800 20px Arial,Helvetica,sans-serif;color:#17201C">
Your watchlist <span style="font:400 14px Arial,sans-serif;color:#5C6660">{n} {"change" if n == 1 else "changes"} this week</span></td></tr>{rows}''')
    top = max([d["pct"] for d in sale] or [0])
    links = [f'<a href="{E(shop)}" style="color:#5C6660">Change your sizes</a>']
    if p.get("token"):
        links.append(f'<a href="{E(SITE_URL)}?unsub={p["token"]}" style="color:#5C6660">Unsubscribe</a>')
    links.append(f'<a href="{E(SITE_URL)}privacy.html" style="color:#5C6660">Privacy</a>')
    footer_links = " · ".join(links) + (f"<br>The Gear Fox · {E(ADDRESS)}" if ADDRESS else "")
    subject = f"The Gear Fox: {len(sale)} deals in your size this week, up to {top}% off"
    if watch and (watch["drops"] or watch["backs"]):
        subject = f"The Gear Fox: your watchlist moved, plus {len(sale)} deals in your size"
    intro = (f"{E(first)}, here are this week's sales on gear in your sizes, "
             f"every price drop, big or small. Biggest discounts first.")
    body = f'''<!doctype html><html><body style="margin:0;background:#EEF1EC">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">
<tr><td style="padding:18px 20px 0;text-align:center"><a href="{E(shop)}"><img src="{E(SITE_URL)}logo-email.png" width="260" alt="The Gear Fox" style="display:inline-block;width:260px;max-width:80%;height:auto;border:0"></a></td></tr>
<tr><td style="padding:8px 20px 6px;text-align:center;font:800 28px Arial Narrow,Arial,sans-serif;color:#17201C">Your weekly deals</td></tr>
<tr><td style="padding:0 20px 8px;text-align:center;font:15px/1.45 Arial,sans-serif;color:#5C6660">{intro}</td></tr>
<tr><td style="padding:0 20px 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(sections)}</table></td></tr>
<tr><td style="padding:14px 20px 22px;text-align:center;border-top:2px dashed #CBD2CC">
<a href="{E(shop)}" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 20px;font:800 16px Arial,sans-serif;text-decoration:none">Open your shop</a>
<div style="font:12px/1.4 Arial,sans-serif;color:#5C6660;margin-top:14px">Prices and stock change daily; the product page has the final price.<br>
You get this because you signed up for Saturday deals on The Gear Fox. Outfox full price.<br>
{footer_links}</div></td></tr>
</table></td></tr></table></body></html>'''
    text = f"{subject}\n\n" + "\n".join(f"- {d['b']} {d['n']}: ${d['best']:.2f} (was ${d['reg']:.2f}, -{d['pct']}%) {d['url']}"
                                         for d in sale[:TOTAL]) + f"\n\nAll deals: {shop}\n" + (
        f"Unsubscribe: {SITE_URL}?unsub={p['token']}\n" if p.get("token") else "") + (f"The Gear Fox, {ADDRESS}\n" if ADDRESS else "")
    return subject, body, text

def subscribers():
    """Confirmed, still-subscribed people from Supabase, as profile dicts with email + token."""
    if not (SB_URL and SB_KEY):
        print("Supabase not configured, using email/profiles.json only")
        return []
    r = requests.get(f"{SB_URL}/rest/v1/subscribers", timeout=60,
                     params={"select": "email,profile,token", "confirmed_at": "not.is.null", "unsubscribed_at": "is.null"},
                     headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"} if SB_KEY.count(".") == 2
                     else {"apikey": SB_KEY})
    r.raise_for_status()
    out = [{**(row["profile"] or {}), "email": row["email"], "token": row["token"]} for row in r.json()]
    print(f"{len(out)} subscribers in Supabase")
    return out

def main():
    profiles = []
    f = ROOT / "email" / "profiles.json"
    if f.exists():
        profiles = json.loads(f.read_text())
        if isinstance(profiles, dict):
            profiles = [profiles]
    db = subscribers()
    seen = {p["email"].lower() for p in db}
    profiles = db + [p for p in profiles if (p.get("email") or "").lower() not in seen]
    if not ADDRESS:
        print("WARNING: MAILING_ADDRESS is not set; CASL requires a postal address in the footer")
    if DEALS_URL:
        data = requests.get(DEALS_URL, timeout=60).json()
    else:
        data = json.loads((ROOT / "site" / "deals.json").read_text())
    items = data.get("items", [])
    print(f"{len(items)} items in deals.json (updated {data.get('updated')})")
    watch_news = {}
    if SB_URL and SB_KEY and any(p.get("token") for p in profiles):
        try:
            import alerts as A
            from datetime import datetime, timezone
            by_key = {}
            for d in items:
                by_key.setdefault(A.item_key(d), []).append(d)
            watch_news = A.evaluate(A.fetch_rows(), by_key, datetime.now(timezone.utc), cooldown=False)
            print(f"watchlist news for {sum(1 for w in watch_news.values() if w['drops'] or w['backs'])} people")
        except Exception as e:                      # the deals email still goes out without it
            print(f"watchlist news skipped: {e}")
    failed = 0
    for p in profiles:
        if not p.get("email"):
            continue
        sale = [d for d in match(items, p) if d["pct"] >= 1]      # anything below full price
        who = p["email"]
        watch = watch_news.get(p.get("token"))
        has_watch = bool(watch and (watch["drops"] or watch["backs"]))
        if not sale and not has_watch:
            print(f"{who}: nothing on sale in their sizes this week, no email sent")
            continue
        subject, body, text = build(p, sale, watch)
        if DRY:
            out = ROOT / "email" / "preview.html"
            out.write_text(body)
            print(f"{who}: DRY RUN, {len(sale)} deals, subject: {subject!r}, wrote {out}")
            continue
        r = requests.post("https://api.resend.com/emails", timeout=60,
                          headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                          json={"from": FROM, "to": [who], "subject": subject, "html": body, "text": text,
                                **({"headers": {"List-Unsubscribe": f"<{SITE_URL}?unsub={p['token']}>"}} if p.get("token") else {})})
        if r.ok:
            print(f"{who}: sent {len(sale)} deals" + (" + watchlist news" if has_watch else ""))
            if watch:
                import alerts as A
                for wid, upd in watch["updates"]:
                    try:
                        A.sb("PATCH", f"watches?id=eq.{wid}", json=upd)
                    except Exception as e:
                        print(f"  could not update watch {wid}: {e}")
        else:
            failed += 1
            print(f"{who}: FAILED {r.status_code} {r.text[:300]}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
