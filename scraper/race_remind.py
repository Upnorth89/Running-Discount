#!/usr/bin/env python3
"""Race gear list reminders (Oct 31, 2026; Bastien: "lets build it now").

On a race gear list page, a visitor ticks what they already have and taps "Remind me" (race_pages.py, #raceBox). 30 days before
the race (the date standing in RACES on that day, Vancouver time) this sends ONE email per person and race: what is still
unticked for their distance (mandatory, recommended, "ask the race"; never what the race provides, never the weather kits),
each line with the page's first pick in their fit + size today, its price, the store and a Watch link. Everything ticked = no email.
Each send is recorded in race_reminders, so nobody gets the same race twice. A missed day catches up for 6 days.

Env: RESEND_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY, SITE_URL, FROM_EMAIL, MAILING_ADDRESS
Usage: python scraper/race_remind.py SITE_DIR [--dry-run]
       python scraper/race_remind.py SITE_DIR --sample SLUG [--dist D] [--fr|--us] OUT.html   (a pretend member's email, nothing sent)
       python scraper/race_remind.py SITE_DIR --send-test SLUG   (the sample to HEALTH_EMAIL: the robot end-to-end test)
Writes /tmp/race-remind.json (due / sent / failed / all ticked) for the health email.
"""
import json
import os
import re
import sys
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import race_pages as RP            # noqa: E402
import weekly_email as W           # noqa: E402

E = W.E
DRY = "--dry-run" in sys.argv or not os.environ.get("RESEND_API_KEY")
CATCH_UP = 6                       # a run missed on the day still sends during the next 6 days
LEVELS = ("M", "L", "R")           # what the email lists, in this order; P (provided) and A (allowed) never

R_STR = {
    "en": dict(
        subj=lambda race, n: f"{race} is in 30 days: {n} thing{'s' if n != 1 else ''} left on your list",
        title=lambda race: f"{race} is in 30 days",
        intro=lambda short, dist, n: f"Here's what's still unticked on your {short} list ({dist}): {n} thing{'s' if n != 1 else ''}. "
                                     "Each with the best pick in your size at the stores we check this morning.",
        M="Mandatory", R="Recommended", L="Ask the race", S="Suggested by the race",
        none="Not in stock in your size today. We check every morning: the list shows it when it's back.",
        none0="None in stock at the stores we check today. We check every morning.",
        notsold="The stores we check don't sell this one.",
        buy="See it at {store}", watch="♡ Watch", size="Size {z}",
        button="Open my list", tick="Already have something? Tick it on your list and it won't come up again.",
        why=lambda race: f"You get this because you asked us on thegearfox.com to remind you 30 days before {race}. It's the only reminder for this race.",
        src="The list is the race's own ({link}). Rules can change: check it before race day.", link="official list",
        notaff="The Gear Fox isn't affiliated with the race."),
    "fr": dict(
        subj=lambda race, n: f"{race} dans 30 jours : il vous manque {n} article{'s' if n != 1 else ''}",
        title=lambda race: f"{race} dans 30 jours",
        intro=lambda short, dist, n: f"Voici ce qui n'est pas encore coché sur votre liste {short} ({dist}) : {n} article{'s' if n != 1 else ''}. "
                                     "Chacun avec le meilleur choix dans votre taille dans les boutiques que nous suivons, ce matin.",
        M="Obligatoire", R="Recommandé", L="À confirmer", S="Suggéré par la course",
        none="Pas en stock dans votre taille aujourd'hui. On vérifie chaque matin : la liste l'affiche dès son retour.",
        none0="Rien en stock dans les boutiques que nous suivons aujourd'hui. On vérifie chaque matin.",
        notsold="Les boutiques que nous suivons ne vendent pas cet article.",
        buy="Voir chez {store}", watch="♡ Suivre", size="Taille {z}",
        button="Ouvrir ma liste", tick="Vous avez déjà quelque chose ? Cochez-le sur votre liste et il ne reviendra plus.",
        why=lambda race: f"Vous recevez ce courriel parce que vous nous avez demandé sur thegearfox.com un rappel 30 jours avant {race}. C'est le seul rappel pour cette course.",
        src="La liste est celle de la course ({link}). Les règles peuvent changer : vérifiez-la avant la course.", link="liste officielle",
        notaff="The Gear Fox n'est pas affilié à la course."),
}


def mask(e):
    u, _, d = (e or "").partition("@")
    return (u[:2] + "…@" + d) if d else "?"


def sb(method, path, headers=None, **kw):
    h = {"apikey": W.SB_KEY, "Content-Type": "application/json", **(headers or {})}
    if W.SB_KEY.count(".") == 2:
        h["Authorization"] = f"Bearer {W.SB_KEY}"
    r = requests.request(method, f"{W.SB_URL}/rest/v1/{path}", headers=h, timeout=60, **kw)
    r.raise_for_status()
    return r.json() if r.text else None


def due(race, today):
    """The race date when today is its reminder day (or within the catch-up days after it), else None."""
    d = RP.race_date(race)
    if not d:
        return None
    r = d - timedelta(days=RP.REMIND_DAYS)
    return d if r <= today <= r + timedelta(days=CATCH_UP) and today < d else None


def fits(lab, z):
    """Same as the race page's fits(): one size, or one of "S/M"."""
    if not z:
        return True
    l = RP.norm(lab)
    if l in ("OS", "OSFA", "OSZ"):
        return True
    return RP.norm(z) in [RP.norm(x) for x in re.split(r"\s*[/|]\s*", l)]


def size_for(profile, g):
    sizes = (profile or {}).get("sizes") or {}
    g = "tops" if g == "bras" else g
    z = ((sizes.get(g) or {}).get("sizes") or [])
    if not z:     # the main clothing size: the one most groups share (the race page does the same)
        votes = {}
        for k in ("tops", "bottoms", "socks", "gloves", "headwear"):
            v = ((sizes.get(k) or {}).get("sizes") or [None])[0]
            if v:
                votes[str(v).upper()] = votes.get(str(v).upper(), 0) + 1
        return max(votes, key=votes.get) if votes else ""
    return str(z[0]).upper()


def best_pick(pool, profile):
    """The race page's first pick in this person's fit + size: (row, size entry) or None."""
    fit = (profile or {}).get("gender")
    ok = []
    for r in pool:
        if fit in ("men", "women") and r["sx"] and fit not in r["sx"]:
            continue
        s = [e for e in r["s"] if fits(e[0], size_for(profile, r["g"]))] if r["g"] in RP.SIZED_G else r["s"]
        if s:
            ok.append(dict(r, s=s))
    top = RP.picks(ok)
    if not top:
        return None
    sale = lambda r: any(e[2] > e[1] * 1.01 for e in r["s"])
    r = next((x for x in top[:RP.FIRST] if sale(x)), top[0])   # the first deal the page shows on sale ("the best price"), else its first pick
    return r, min(r["s"], key=lambda e: e[1])


def page_url(slug, side, lang):
    path = f"us/races/{slug}/" if side == "us" else (f"courses/{slug}/" if lang == "fr" else f"races/{slug}/")
    return f"{W.SITE_URL}{path}?ref=race-remind"


def lines(slug, race, dist, ticks, items, stores):
    """What's left: [(kind, level, (title, note), pick or None, sold)] for this distance, mandatory first."""
    inkit = {k for ks in (race.get("kits") or {}).values() for k in ks}
    i = race["dists"].index(dist) if dist in race["dists"] else race["dists"].index(race["default"])
    out = []
    for kind, lv, txt, _spec in race["items"]:
        level = lv[i].strip()
        if level not in LEVELS or kind in inkit or kind in ticks:
            continue
        out.append((kind, level, txt))
    out.sort(key=lambda x: LEVELS.index(x[1]))
    return out


def row_html(level, title, note, pick, sold, lang, S, sub_token, suggested):
    tag = S["S"] if suggested and level == "R" else S[level]
    head = (f'<div style="font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#B8470A">{E(tag)}</div>'
            f'<div style="font-size:16px;font-weight:800;color:#17201C;margin:2px 0">{E(title)}</div>')
    if not sold:
        body = f'<div style="font-size:13px;color:#5C6660">{E(S["notsold"])}</div>'
    elif not pick:
        body = f'<div style="font-size:13px;color:#5C6660">{E(S["none" if sold == "sized" else "none0"])}</div>'
    else:
        r, e = pick
        money = lambda v: W.money(v, lang)
        reg = (f' <span style="font-size:13px;color:#5C6660;text-decoration:line-through">{money(e[2])}</span>'
               f' <span style="font-size:13px;font-weight:800;color:#1E7A46">{W.pct_txt(round(100 * (1 - e[1] / e[2])), lang)}</span>'
               if e[2] > e[1] * 1.01 else "")
        z = f' · {E(S["size"].format(z=e[0]))}' if r["g"] in RP.SIZED_G and RP.norm(e[0]) != "OS" else ""
        watch = f'{W.SITE_URL}?k={sub_token}&watch={quote(r["k"])}&ref=race-remind'
        body = f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:6px"><tr>
<td width="84" valign="top"><a href="{E(e[3])}"><img src="{E(r["img"])}" width="72" height="72" alt="" style="display:block;width:72px;height:72px;object-fit:contain;background:#fff;border-radius:8px;border:1px solid #E3E7E2"></a></td>
<td valign="top" style="font-family:Arial,Helvetica,sans-serif">
<div style="font-size:13px;font-weight:700;color:#17201C">{E(r["b"])}</div>
<div style="font-size:14px;line-height:1.3;color:#17201C">{E(W.nm(r["n"], lang))}</div>
<div style="margin-top:2px"><span style="font-size:18px;font-weight:800;color:#17201C">{money(e[1])}</span>{reg}</div>
<div style="font-size:12px;color:#5C6660;margin-top:2px">{E(r["st"])}{z}</div>
<div style="font-size:13px;margin-top:6px"><a href="{E(e[3])}" style="color:#B8470A;font-weight:700">{E(S["buy"].format(store=r["st"]))}</a>
 &nbsp;·&nbsp; <a href="{E(watch)}" style="color:#17201C">{E(S["watch"])}</a></div>
</td></tr></table>'''
    nt = f'<div style="font-size:12px;color:#5C6660;margin-top:3px">{E(note)}</div>' if note and not pick else ""
    return f'<tr><td style="padding:12px 0;border-top:1px solid #E3E7E2;font-family:Arial,Helvetica,sans-serif">{head}{nt}{body}</td></tr>'


def build(sub, slug, race, entry, items, stores, pools):
    """(subject, html, text, n) for one person and race; n = 0 when everything is ticked."""
    side = entry.get("side") or "ca"
    prof = sub.get("profile") or {}
    lang = "en" if side == "us" else W.lang_of(prof)
    L = "us" if side == "us" else lang
    S = R_STR[lang]
    dist = entry.get("dist") if entry.get("dist") in race["dists"] else race["default"]
    left = lines(slug, race, dist, set(entry.get("ticks") or []), items, stores)
    if not left:
        return None, None, None, 0
    rows, text = [], []
    for kind, level, txt in left:
        title, note = txt["en" if L == "us" else L]
        sold = RP.kbase(kind) in RP.KINDS
        if sold and kind not in pools:
            pools[kind] = RP.pool(items, kind, stores)
        pick = best_pick(pools[kind], prof) if sold else None
        if sold and not pick and any(r["g"] in RP.SIZED_G or r["sx"] for r in pools[kind]):
            sold = "sized"                   # in stock, not in their fit or size
        rows.append(row_html(level, title, note, pick, sold, lang, S, sub["token"], race.get("suggested")))
        text.append(f"- {title}" + (f": {pick[0]['b']} {pick[0]['n']} {W.money(pick[1][1], lang)} at {pick[0]['st']} {pick[1][3]}" if pick else ""))
    name, short = race["name"], race["short"]
    dl = RP.dlab(race, dist, L)
    subject = S["subj"](name, len(left))
    url = page_url(slug, side, lang)
    src = race.get("src_fr") if lang == "fr" and race.get("src_fr") else race.get("src")
    footer = (f'{E(S["why"](name))}<br>' + S["src"].format(link=f'<a href="{E(src or url)}" style="color:#5C6660">{E(S["link"])}</a>')
              + f' {E(S["notaff"])}<br><a href="{E(W.SITE_URL)}?unsub={sub["token"]}" style="color:#5C6660">{E(W.tr(lang, "unsubscribe"))}</a> · '
              f'<a href="{E(W.SITE_URL)}privacy.html" style="color:#5C6660">{E(W.tr(lang, "privacy"))}</a>'
              + (f"<br>The Gear Fox · {E(W.ADDRESS)}" if W.ADDRESS else ""))
    html = f'''<!doctype html><html lang="{lang}"><body style="margin:0;background:#EEF1EC">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">
<tr><td style="padding:18px 20px 0;text-align:center"><a href="{E(url)}"><img src="{E(W.SITE_URL)}{W.tr(lang, "logo")}" width="220" alt="The Gear Fox" style="display:inline-block;width:220px;max-width:70%;height:auto;border:0"></a></td></tr>
<tr><td style="padding:8px 20px 4px;text-align:center;font:800 26px Arial Narrow,Arial,sans-serif;color:#17201C">{E(S["title"](name))}</td></tr>
<tr><td style="padding:0 20px 8px;text-align:center;font:15px/1.45 Arial,sans-serif;color:#5C6660">{E(S["intro"](short, dl, len(left)))}</td></tr>
<tr><td style="padding:0 20px 8px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table></td></tr>
<tr><td style="padding:14px 20px 22px;text-align:center;border-top:2px dashed #CBD2CC">
<div style="font:14px/1.4 Arial,sans-serif;color:#17201C;margin-bottom:12px">{E(S["tick"])}</div>
<a href="{E(url)}" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 20px;font:800 16px Arial,sans-serif;text-decoration:none">{E(S["button"])}</a>
<div style="font:12px/1.4 Arial,sans-serif;color:#5C6660;margin-top:14px">{footer}</div></td></tr>
</table></td></tr></table></body></html>'''
    plain = f"{S['title'](name)}\n\n{S['intro'](short, dl, len(left))}\n\n" + "\n".join(text) + \
        f"\n\n{S['button']}: {url}\n{W.tr(lang, 'unsubscribe')}: {W.SITE_URL}?unsub={sub['token']}\n"
    return subject, html, plain, len(left)


def load(site):
    """Both sides' catalogues (full price too, like the race pages) and the store names."""
    stores = RP.store_names((site / "index.html").read_text())
    ca = json.loads((site / "deals.json").read_text())["items"] if (site / "deals.json").exists() else \
        json.loads((site / "sale.json").read_text())["items"]
    us, fx = [], 1.37
    f = site / "deals-us.json"
    if not f.exists():
        f = site / "sale-us.json"
    if f.exists():
        data = json.loads(f.read_text())
        us, fx = data["items"], float((data.get("fx") or {}).get("USD") or 1.37)
    return {"ca": ca, "us": us}, fx, stores


def side_set(side, fx):
    W.SIDE.update(us=side == "us", fx=fx if side == "us" else 1.0)


def send(to, subject, html, text, token):
    r = requests.post("https://api.resend.com/emails", timeout=60,
                      headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
                      json={"from": W.FROM, "to": [to], "subject": subject, "html": html, "text": text,
                            "headers": {"List-Unsubscribe": f"<{W.SITE_URL}?unsub={token}>"}})
    return r


SAMPLE_PROFILE = {"lang": "en", "gender": "men", "sizes": {"shoes": {"sizes": ["11"]}, "tops": {"sizes": ["M"]}, "bottoms": {"sizes": ["M"]},
                                                          "socks": {"sizes": ["M"]}, "gloves": {"sizes": ["M"]}, "headwear": {"sizes": ["M"]}}}


def sample(site, slug, out=None, to=None):
    data, fx, stores = load(site)
    race = RP.RACES[slug]
    side = "us" if "--us" in sys.argv else "ca"
    dist = sys.argv[sys.argv.index("--dist") + 1] if "--dist" in sys.argv else race["default"]
    prof = dict(SAMPLE_PROFILE, lang="fr" if "--fr" in sys.argv else "en")
    sub = {"email": to or "sample@example.com", "token": "00000000-0000-0000-0000-000000000000", "profile": prof}
    side_set(side, fx)
    subject, html, text, n = build(sub, slug, race, {"dist": dist, "side": side, "ticks": ["headlamp"]}, data[side], stores, {})
    print(f"sample: {subject!r} ({n} lines)")
    if out:
        Path(out).write_text(html)
    if to:
        if DRY:
            print("no RESEND_API_KEY: not sent")
            return 1
        r = send(to, "[TEST] " + subject, html, text, sub["token"])
        print("test send:", r.status_code, r.text[:200])
        return 0 if r.ok else 1
    return 0


def main():
    site = Path(next(a for a in sys.argv[1:] if not a.startswith("--")))
    if "--sample" in sys.argv:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        slug = sys.argv[sys.argv.index("--sample") + 1]
        out = next((a for a in args if a.endswith(".html")), None)
        return sample(site, slug, out)
    if "--send-test" in sys.argv:
        to = os.environ.get("HEALTH_EMAIL") or "hello@thegearfox.com"
        return sample(site, sys.argv[sys.argv.index("--send-test") + 1], None, to)
    today = RP.today()
    races = {slug: d for slug, r in RP.RACES.items() if (d := due(r, today))}
    report = {"date": today.isoformat(), "races": sorted(races), "due": 0, "sent": 0, "failed": 0, "ticked": 0, "dry": DRY}
    print(f"{today}: races at their 30-day mark: {', '.join(sorted(races)) or 'none'}")
    if races and W.SB_URL and W.SB_KEY:
        rows = sb("GET", "race_lists", params={
            "select": "slug,dist,side,ticks,subscriber_id,subscribers!inner(email,token,profile,confirmed_at,unsubscribed_at)",
            "slug": f"in.({','.join(races)})", "subscribers.confirmed_at": "not.is.null", "subscribers.unsubscribed_at": "is.null"})
        done = {(x["subscriber_id"], x["slug"]) for x in sb("GET", "race_reminders", params={
            "select": "subscriber_id,slug", "slug": f"in.({','.join(races)})"}) or []}
        data, fx, stores = load(site)
        pools = {"ca": {}, "us": {}}
        for x in rows:
            if (x["subscriber_id"], x["slug"]) in done:
                continue
            report["due"] += 1
            side = "us" if x.get("side") == "us" else "ca"
            side_set(side, fx)
            sub = x["subscribers"]
            subject, html, text, n = build(sub, x["slug"], RP.RACES[x["slug"]], x, data[side], stores, pools[side])
            rec = {"subscriber_id": x["subscriber_id"], "slug": x["slug"], "race_date": races[x["slug"]].isoformat()}
            if not n:
                report["ticked"] += 1
                print(f"{mask(sub['email'])} {x['slug']}: everything ticked, no email")
                if not DRY:
                    sb("POST", "race_reminders", json=rec, headers={"Prefer": "resolution=ignore-duplicates"})
                continue
            if DRY:
                print(f"{mask(sub['email'])} {x['slug']}: DRY RUN {subject!r}")
                continue
            r = send(sub["email"], subject, html, text, sub["token"])
            if r.ok:
                report["sent"] += 1
                sb("POST", "race_reminders", json=rec, headers={"Prefer": "resolution=ignore-duplicates"})
                print(f"{mask(sub['email'])} {x['slug']}: sent ({n} lines)")
            else:
                report["failed"] += 1
                print(f"{mask(sub['email'])} {x['slug']}: FAILED {r.status_code} {r.text[:200]}")
            time.sleep(0.7)       # Resend takes 2 a second
    elif races:
        print("Supabase not configured: nothing sent")
    Path("/tmp/race-remind.json").write_text(json.dumps(report))
    print(f"race reminders: {report['due']} due, {report['sent']} sent, {report['failed']} failed, {report['ticked']} with everything ticked")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
