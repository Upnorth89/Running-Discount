#!/usr/bin/env python3
"""First-visit funnel, split by where people land (Oct 5, 2026). Read-only: totals only, nothing personal.

The dashboard's "Arrived" counts every first visit, including people landing on a shoe page from Google, who never see
the welcome screen. This splits the funnel by landing page and shows how fast people leave, so the drop is measured
on the homepage only. Prints the result, and as a GitHub notice (readable from the run's annotations).

  SUPABASE_URL=... SUPABASE_SECRET_KEY=... python tools/funnel.py [DAYS]     (workflow: .github/workflows/funnel.yml)
"""
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import requests

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 14
SB, KEY = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_SECRET_KEY"]
H = {"apikey": KEY}
if KEY.count(".") == 2:
    H["Authorization"] = f"Bearer {KEY}"
since = (datetime.now(timezone.utc) - timedelta(days=DAYS)).isoformat()

rows, step = [], 1000
while True:
    r = requests.get(f"{SB}/rest/v1/ana_events", headers={**H, "Range": f"{len(rows)}-{len(rows) + step - 1}"}, timeout=60,
                     params={"select": "sid,kind,detail,num,page,dev,ref,nv,at,tz", "at": f"gte.{since}", "order": "id"})
    r.raise_for_status()
    batch = r.json()
    rows += batch
    if len(batch) < step:
        break

S = defaultdict(lambda: {"kinds": set(), "entry": None, "nv": None, "dev": None, "ref": None, "secs": None, "scroll": None,
                         "steps": set(), "n": 0, "pages": set(), "race": [], "dclick": [], "hike": [], "sport": None})
for e in rows:
    s = S[e["sid"]]
    s["n"] += 1
    s["d"] = s.get("d") or e["at"][:10]          # the session's day (events come in time order)
    s["kinds"].add(e["kind"])
    s["nv"] = s["nv"] or e["nv"]
    s["dev"] = s["dev"] or e["dev"]
    s["ref"] = s["ref"] or e["ref"]
    if e["kind"] == "visit" and not s["entry"]:
        s["entry"] = e["page"] or "?"
        s["src"] = e["detail"] or "(none)"          # the site that sent them (referrer host), "email-friday", "home-screen app"
    if e["kind"] == "leave" and e["num"] is not None:
        s["secs"] = max(s["secs"] or 0, e["num"])
    if e["kind"] == "scroll" and e["num"] is not None:
        s["scroll"] = max(s["scroll"] or 0, e["num"])
    if e["kind"] == "signup-step":
        s["steps"].add(e["detail"])
    if e["kind"] == "shoe-page-view":
        s["pages"].add(e["detail"])
    if e["kind"] == "filter" and (e["detail"] or "").startswith("race|"):   # race gear lists (Oct 23): race|<race>|<what>|<detail>
        s["race"].append(e["detail"].split("|", 3)[1:])
    if e["kind"] == "filter" and (e["detail"] or "").startswith("hike|"):   # trail gear lists (Oct 25): hike|<slug>|<what>|<detail>
        s["hike"].append(e["detail"].split("|", 3)[1:])
    if e["kind"] == "filter" and (e["detail"] or "").startswith("sport|"):  # Running | Hiking switch: sport|<run|hike>|<from>
        s["sport"] = e["detail"].split("|")[1]
    if e["kind"] == "deal-click":
        s["dclick"].append(e["detail"] or "")
    if e["kind"] in ("welcome-view", "sizes-saved", "load"):
        s["pages"].add("/")             # the homepage

new = [s for s in S.values() if s["nv"] == 1]
out = [f"Last {DAYS} days: {len(rows)} events, {len(S)} sessions, {len(new)} first visits"]
SC = {}       # the scorecard's numbers, filled as each section computes them (printed second, after this line)


def land(s):
    p = s["entry"] or "?"
    if p.startswith("/us/"):
        p = p[3:]                                  # the USA side's pages count with their Canadian twins
    return "homepage" if p in ("/", "/index.html") else "shoe pages" if p.startswith(("/shoes", "/chaussures", "/running-shoes",
           "/chaussures-course", "/brands", "/marques", "/black-friday", "/vendredi-fou")) else "other " + p[:30]


out.append("First visits by landing page: " + ", ".join(f"{k} {v}" for k, v in Counter(land(s) for s in new).most_common(8)))
home = [s for s in new if land(s) == "homepage"]
pct = lambda a, b: f"{a} ({round(100 * a / b)}%)" if b else str(a)
w = [s for s in home if "welcome-view" in s["kinds"]]
z = [s for s in home if "sizes-saved" in s["kinds"]]
c = [s for s in home if "deal-click" in s["kinds"]]
su = [s for s in home if "signup" in s["kinds"]]
out.append(f"HOMEPAGE first visits {len(home)} -> saw welcome {pct(len(w), len(home))} -> picked sizes {pct(len(z), len(home))}"
           f" -> clicked a deal {pct(len(c), len(home))} -> signed up {pct(len(su), len(home))}")
# Oct 22 redesign (light look for everyone, no test): watch the homepage first visits before vs after until Nov 5
RD = "2026-10-22"
for nm, g in (("before Oct 22", [s for s in home if s.get("d", "") < RD]), ("from Oct 22", [s for s in home if s.get("d", "") >= RD])):
    if g:
        SC["redesign " + nm] = (f"redesign watch, homepage first visits {nm}: {len(g)} -> sizes {pct(sum(1 for s in g if 'sizes-saved' in s['kinds']), len(g))}, "
                                f"store {pct(sum(1 for s in g if 'deal-click' in s['kinds']), len(g))}")
SC["home"] = f"homepage first visits {len(home)}: sizes {pct(len(z), len(home))}, store {pct(len(c), len(home))}, sign-up {pct(len(su), len(home))}"
only = [s for s in home if s["kinds"] <= {"visit", "ref-visit"}]
out.append(f"Homepage first visits with nothing but the visit (no welcome, no leave/scroll: bots, link previews or gone at once): "
           f"{pct(len(only), len(home))}")
# of those who saw the welcome but didn't pick sizes: how long they stayed, and how far they got
drop = [s for s in w if "sizes-saved" not in s["kinds"]]
secs = sorted(s["secs"] for s in drop if s["secs"] is not None)
if secs:
    b = Counter("<5s" if x < 5 else "5-15s" if x < 15 else "15-60s" if x < 60 else "60s+" for x in secs)
    out.append(f"Saw welcome, no sizes ({len(drop)}): time on site {', '.join(f'{k} {b[k]}' for k in ['<5s', '5-15s', '15-60s', '60s+'])}"
               f" (known for {len(secs)}); median {secs[len(secs) // 2]:.0f}s")
went = Counter()
for s in drop:
    if "shoe-page-link" in s["kinds"]:
        went["went to shoe pages"] += 1
    if s["steps"]:
        went["started the sizes step"] += 1
    if "language" in s["kinds"]:
        went["switched language"] += 1
out.append("  of them: " + (", ".join(f"{k} {v}" for k, v in went.items()) or "nothing else recorded"))
out.append("Homepage first visits by device: " + ", ".join(
    f"{d}: {sum(1 for s in home if s['dev'] == d)} visits, {pct(sum(1 for s in z if s['dev'] == d), sum(1 for s in home if s['dev'] == d))} picked sizes"
    for d in ("phone", "computer", "tablet")))
refs = Counter(s["ref"] or "(direct)" for s in home)
out.append("Homepage first visits by link: " + ", ".join(
    f"{r}: {n} -> {sum(1 for s in z if (s['ref'] or '(direct)') == r)} sizes" for r, n in refs.most_common(8)))
shoe = [s for s in new if land(s) == "shoe pages"]
if shoe:
    out.append(f"SHOE PAGE first visits {len(shoe)}: picked a size {pct(sum(1 for s in shoe if 'shoe-page-size' in s['kinds']), len(shoe))}, "
               f"clicked a store {pct(sum(1 for s in shoe if 'deal-click' in s['kinds']), len(shoe))}, "
               f"went on to the homepage {pct(sum(1 for s in shoe if 'welcome-view' in s['kinds'] or 'sizes-saved' in s['kinds']), len(shoe))}, "
               f"went on to another of our pages {pct(sum(1 for s in shoe if len(s['pages']) >= 2), len(shoe))}")   # Oct 22: test 'alts' metric
    SC["shoe"] = (f"shoe-page first visits {len(shoe)}: size {pct(sum(1 for s in shoe if 'shoe-page-size' in s['kinds']), len(shoe))}, "
                  f"store {pct(sum(1 for s in shoe if 'deal-click' in s['kinds']), len(shoe))}, another page {pct(sum(1 for s in shoe if len(s['pages']) >= 2), len(shoe))}")
# come-back bar (Oct 5) and where sign-ups happen (Oct 8): is the store offer used, and does a sign-up follow a deal click?
alls = list(S.values())
off = [s for s in alls if "store-offer" in s["kinds"]]
used = [s for s in off if "store-view" in s["kinds"]]
off_clicks = [s for s in used if "deal-click" in s["kinds"]]
out.append(f"Come-back store bar: offered in {len(off)} sessions, Show tapped in {pct(len(used), len(off))}, "
           f"of those also clicked a deal {len(off_clicks)}")
clk = [s for s in alls if "deal-click" in s["kinds"]]
member_like = [s for s in clk if "signup" in s["kinds"]]
out.append(f"Sessions with a deal click: {len(clk)} (first visits {sum(1 for s in clk if s['nv'] == 1)}); signed up in the same session {len(member_like)}")
wh = Counter()
for e in rows:
    if e["kind"] == "signup":
        wh[(e["detail"] or "?")[:30]] += 1
out.append("Sign-ups by where (detail): " + (", ".join(f"{k} {v}" for k, v in wh.most_common(6)) or "none recorded"))
# load time (Oct 8): ms until the deals are on screen, first visits on the homepage; and who left the welcome within 5 s
loads = {}
for e in rows:
    if e["kind"] == "load" and e["num"] is not None and e["sid"] not in loads:
        loads[e["sid"]] = (e["num"], (e["detail"] or "").split("|"))
hl = sorted((loads[sid][0], sid) for sid, s in S.items() if sid in loads and s["nv"] == 1 and land(s) == "homepage")
if hl:
    ms = [m for m, _ in hl]
    q = lambda f: ms[min(len(ms) - 1, int(len(ms) * f))]
    out.append(f"Load time, homepage first visits ({len(ms)}): median {q(.5) / 1000:.1f}s, 3 in 4 under {q(.75) / 1000:.1f}s, "
               f"slowest 1 in 10 over {q(.9) / 1000:.1f}s")
    for lo, hi, lab in ((0, 2000, "<2s"), (2000, 4000, "2-4s"), (4000, 10 ** 9, "4s+")):
        grp = [S[sid] for m, sid in hl if lo <= m < hi]
        if grp:
            out.append(f"  loaded in {lab}: {len(grp)} visits, picked sizes {pct(sum(1 for s in grp if 'sizes-saved' in s['kinds']), len(grp))}")
    con = Counter(loads[sid][1][1] if len(loads[sid][1]) > 1 else "?" for _, sid in hl)
    out.append("  connection: " + ", ".join(f"{k} {v}" for k, v in con.most_common(5)))
ret = [s for s in S.values() if (s["nv"] or 0) > 1]
out.append(f"Returning visits {len(ret)}: clicked a deal {pct(sum(1 for s in ret if 'deal-click' in s['kinds']), len(ret))}")

# when (Oct 8, Bastien: post and notify when shoppers are around): visits, deal clicks and sign-ups by the visitor's own
# local hour and weekday (each event carries the device's time zone; Pacific when unknown)
from zoneinfo import ZoneInfo
def local(e):
    try:
        z = ZoneInfo(e.get("tz") or "America/Vancouver")
    except Exception:
        z = ZoneInfo("America/Vancouver")
    return datetime.fromisoformat(e["at"].replace("Z", "+00:00")).astimezone(z)
hv, hc, wv, wc, hs = Counter(), Counter(), Counter(), Counter(), Counter()
for e in rows:
    if e["kind"] in ("visit", "deal-click", "signup"):
        t = local(e)
        if e["kind"] == "visit":
            hv[t.hour] += 1; wv[t.strftime("%a")] += 1
        elif e["kind"] == "deal-click":
            hc[t.hour] += 1; wc[t.strftime("%a")] += 1
        else:
            hs[t.hour] += 1
if hv:
    bands = [(5, 9, "5-9am"), (9, 12, "9-noon"), (12, 14, "noon-2pm"), (14, 17, "2-5pm"), (17, 20, "5-8pm"), (20, 23, "8-11pm"), (23, 29, "11pm-5am")]
    inb = lambda c, lo, hi: sum(v for h, v in c.items() if lo <= h < hi or lo <= h + 24 < hi)
    out.append("BY LOCAL TIME (visits / deal clicks / sign-ups): " + ", ".join(
        f"{lab} {inb(hv, lo, hi)}/{inb(hc, lo, hi)}/{inb(hs, lo, hi)}" for lo, hi, lab in bands))
    out.append("  busiest hours (visits): " + ", ".join(f"{h}:00 {v}" for h, v in hv.most_common(5)) +
               " | deal clicks: " + ", ".join(f"{h}:00 {v}" for h, v in hc.most_common(5)))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    out.append("  by weekday (visits/clicks): " + ", ".join(f"{d} {wv[d]}/{wc[d]}" for d in days))
# visits from our emails (Oct 8: links carry ?em=friday / ?em=alert)
emv = Counter((e["detail"] or "") for e in rows if e["kind"] == "visit" and (e["detail"] or "").startswith("email-"))
out.append("Visits from our emails: " + (", ".join(f"{k[6:]} {v}" for k, v in emv.most_common()) or "none yet"))
# Oct 27, test 'emailday' (weekly email Friday for A, Saturday for B, Oct 31 - Nov 21): sessions and devices that came from each
# day's email. Per send: divide by the subscribers in each group (the email workflow log prints "A n, B n" each run)
try:
    ed = {k: [e for e in rows if e["kind"] == "visit" and (e["detail"] or "") == f"email-{k}"] for k in ("friday", "saturday")}
    out.append("EMAIL DAY TEST (Fri = A, Sat = B, from Oct 31): " + ", ".join(
        f"{k} {len({e['sid'] for e in v})} sessions / {len({e.get('did') or e['sid'] for e in v})} devices" for k, v in ed.items()))
except Exception as e:
    out.append(f"EMAIL DAY TEST: couldn't read ({str(e)[:60]})")
# coming back (Oct 8): devices by the day they first came, how many came back on a later day, by where they first came from
try:
    dv, step = [], 1000
    while True:
        r = requests.get(f"{SB}/rest/v1/ana_devices", headers={**H, "Range": f"{len(dv)}-{len(dv) + step - 1}"}, timeout=60,
                         params={"select": "first_day,last_day,days,signed_up,ref,dev", "order": "first_day"})
        r.raise_for_status()
        b = r.json()
        dv += b
        if len(b) < step:
            break
    today = datetime.now(timezone.utc).date()
    age = 7 if any((today - datetime.fromisoformat(d["first_day"]).date()).days >= 14 for d in dv) else 2   # analytics began Oct 4
    old = [d for d in dv if (today - datetime.fromisoformat(d["first_day"]).date()).days >= age]   # had time to come back
    back = lambda g: sum(1 for d in g if (d["days"] or 1) > 1)
    if not old:
        out.append(f"Coming back: no device is {age}+ days old yet ({len(dv)} devices)")
    if old:
        out.append(f"COMING BACK (devices first seen {age}+ days ago: {len(old)}): came back on another day {pct(back(old), len(old))}, "
                   f"3+ days {pct(sum(1 for d in old if (d['days'] or 1) >= 3), len(old))}")
        su = [d for d in old if d["signed_up"]]
        out.append(f"  signed up {len(su)}: came back {pct(back(su), len(su))} | not signed up {len(old) - len(su)}: came back "
                   f"{pct(back([d for d in old if not d['signed_up']]), len(old) - len(su))}")
        refs = Counter((d["ref"] or "(direct)") for d in old)
        out.append("  by first link: " + ", ".join(f"{k} {pct(back([d for d in old if (d['ref'] or '(direct)') == k]), n)}"
                                                  for k, n in refs.most_common(7)))
        out.append("  by device: " + ", ".join(f"{k} {pct(back([d for d in old if d['dev'] == k]), n)}"
                                              for k, n in Counter(d["dev"] for d in old).most_common(3)))
except Exception as e:
    out.append(f"Coming back: couldn't read devices ({str(e)[:80]})")

# where first visits came from (Oct 8: the r/RunningShoeGeeks post had no ?ref= link, the subreddit doesn't allow them)
def src(s):
    v = (s.get("src") or "(none)").lower()
    return "reddit" if "reddit" in v else "google" if "google" in v else "instagram" if "instagram" in v else \
        "facebook" if "facebook" in v else v if v.startswith(("email-", "home-screen", "(none)")) else "other site"


# TRACKING CHECK (Oct 27, Bastien: "Are we tracking numbers correctly?"): first visits whose session has no "visit" event have no
# source or landing page (they count as "(none)" / "other ?"). Which kinds and pages they do send tells where the visit event is lost.
try:
    nov = [s for s in new if not s["entry"]]
    if nov:
        out.append(f"TRACKING CHECK: {pct(len(nov), len(new))} first visits have no 'visit' event (no source, no landing page); "
                   f"their events: " + ", ".join(f"{k} {v}" for k, v in Counter(k for s in nov for k in s["kinds"]).most_common(10)))
        out.append("  their pages: " + ", ".join(f"{k} {v}" for k, v in Counter(pg_ for s in nov for pg_ in (s["pages"] or {"(none)"})).most_common(8))
                   + " | devices: " + ", ".join(f"{k} {v}" for k, v in Counter(s["dev"] for s in nov).most_common(3))
                   + " | first event day: " + ", ".join(f"{k} {v}" for k, v in Counter(s.get("d") for s in nov).most_common(3)))
        # Oct 31: every day, oldest first, with that day's share of first visits: the Oct 27 fix should show as a drop to ~0
        allday = Counter(s.get("d") for s in new)
        out.append("  by day (missing / first visits): " + ", ".join(
            f"{str(k)[5:]} {v}/{allday[k]}" for k, v in sorted(Counter(s.get("d") for s in nov).items(), key=lambda x: str(x[0]))))
        # was their visit event simply before this window (a phone tab left open and reopened days later keeps its session)?
        ids = [sid for sid, s in S.items() if s in nov]
        before = {}
        for i in range(0, len(ids), 40):
            rr = requests.get(f"{SB}/rest/v1/ana_events", headers=H, timeout=60,
                              params={"select": "sid,at", "kind": "eq.visit", "sid": f"in.({','.join(ids[i:i + 40])})"})
            rr.raise_for_status()
            for x in rr.json():
                before[x["sid"]] = min(before.get(x["sid"], x["at"]), x["at"])
        out.append(f"  visit event found earlier (session started before this window, tab reopened later): {len(before)} of {len(ids)}; "
                   f"started: " + ", ".join(f"{k} {v}" for k, v in Counter(a[:10] for a in before.values()).most_common(6)))
except Exception as e:
    out.append(f"Tracking check: couldn't compute ({str(e)[:80]})")
# RIGHT NOW (Oct 27, Bastien: "umami shows 6 currently online, our tracker over 100"): the stats page's "Right now" = devices with any
# event in the last 30 minutes (Umami: the last 5). Who they are: new or returning, what they sent, which pages, how long ago.
try:
    nowu = datetime.now(timezone.utc)
    for mins in (30, 5):
        cut = (nowu - timedelta(minutes=mins)).isoformat()
        rr = requests.get(f"{SB}/rest/v1/ana_events", headers=H, timeout=60,
                          params={"select": "did,sid,kind,page,dev,nv,at", "at": f"gte.{cut}", "order": "id", "limit": "5000"})
        rr.raise_for_status()
        ev = rr.json()
        dids = {e["did"] for e in ev}
        only_leave = {d for d in dids if {e["kind"] for e in ev if e["did"] == d} <= {"leave", "scroll"}}
        out.append(f"RIGHT NOW (last {mins} min): {len(dids)} devices, {len({e['sid'] for e in ev})} sessions, {len(ev)} events; "
                   f"devices that only sent 'left the tab' (a tab closed or switched away, not someone reading): {len(only_leave)}; "
                   f"kinds: " + ", ".join(f"{k} {v}" for k, v in Counter(e["kind"] for e in ev).most_common(8))
                   + " | devices: " + ", ".join(f"{k} {v}" for k, v in Counter(e["dev"] for e in {e["did"]: e for e in ev}.values()).most_common(3)))
except Exception as e:
    out.append(f"Right now: couldn't compute ({str(e)[:80]})")
# TODAY (Vancouver time, since midnight): where first visits came from and where they landed
try:
    from zoneinfo import ZoneInfo
    t0 = datetime.now(ZoneInfo("America/Vancouver")).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()
    first_at = {}
    for e in rows:
        first_at.setdefault(e["sid"], e["at"])
    tn = [s for sid, s in S.items() if s["nv"] == 1 and first_at.get(sid, "") >= t0]
    tall = [sid for sid in S if first_at.get(sid, "") >= t0]
    out.append(f"TODAY (since midnight Vancouver): {len(tall)} sessions, {len(tn)} first visits; from: "
               + ", ".join(f"{k} {v}" for k, v in Counter(src(s) if s["entry"] else "(no visit event)" for s in tn).most_common(8)))
    out.append("  sites that sent them: " + ", ".join(f"{k} {v}" for k, v in Counter(s.get("src") for s in tn if s["entry"] and s.get("src") != "(none)").most_common(10)))
    out.append("  landed on: " + ", ".join(f"{k} {v}" for k, v in Counter(land(s) for s in tn).most_common(8))
               + " | ?ref=: " + ", ".join(f"{k} {v}" for k, v in Counter(s["ref"] for s in tn if s["ref"]).most_common(8)))
except Exception as e:
    out.append(f"Today: couldn't compute ({str(e)[:80]})")
out.append("FIRST VISITS BY SOURCE (picked a size / clicked a store / signed up / median seconds):")
for k, n in Counter(src(s) for s in new).most_common(8):
    g = [s for s in new if src(s) == k]
    sized = sum(1 for s in g if {"sizes-saved", "shoe-page-size"} & s["kinds"])
    secs = sorted(s["secs"] for s in g if s["secs"] is not None)
    out.append(f"  {k}: {n} -> sizes {pct(sized, n)}, store {pct(sum(1 for s in g if 'deal-click' in s['kinds']), n)}, "
               f"signed up {pct(sum(1 for s in g if 'signup' in s['kinds']), n)}, {secs[len(secs) // 2] if secs else '?'} s")
    if k == "reddit":
        out.append("    landed on: " + ", ".join(f"{p} {c}" for p, c in Counter(s["entry"] for s in g).most_common(8)))
        out.append("    devices: " + ", ".join(f"{d} {c}" for d, c in Counter(s["dev"] for s in g).most_common(3))
                   + "; went on to the homepage " + str(sum(1 for s in g if land(s) != "homepage"
                                                           and {"welcome-view", "sizes-saved"} & s["kinds"])))

# Oct 26: campaigns by ?ref= prefix (press-<outlet>, bluesky-<shoes|cat>, pinterest-<shoes|cat>): first visits and what they did,
# then each tag; the Nov 17 rotation check compares bluesky-shoes / pinterest-shoes with the rotating categories
def camp(r):
    r = (r or "").lower()
    return next((p for p in ("press", "bluesky", "pinterest", "reddit", "ig", "race", "hike") if r == p or r.startswith(p + "-")), None)


def campaigns():
  out.append("LINKS BY CAMPAIGN (first visits -> picked a size / clicked a store / signed up; sign-ups also count later visits):")
  for c in ("press", "bluesky", "pinterest", "reddit", "ig", "race", "hike"):
      g = [s for s in new if camp(s["ref"]) == c]
      ups = sum(1 for s in alls if camp(s["ref"]) == c and "signup" in s["kinds"])
      if not g and not ups:
          continue
      n = len(g)
      out.append(f"  {c}: {n} -> sizes {pct(sum(1 for s in g if {'sizes-saved', 'shoe-page-size'} & s['kinds']), n)}, "
                 f"store {pct(sum(1 for s in g if 'deal-click' in s['kinds']), n)}, sign-ups {ups}")
      tags = Counter(s["ref"] for s in new if camp(s["ref"]) == c)
      out.append("    " + ", ".join(f"{k} {v} ({sum(1 for s in alls if s['ref'] == k and 'signup' in s['kinds'])} sign-ups)"
                                    for k, v in tags.most_common(10)))


try:
    campaigns()
except Exception as e:          # never let this section stop the weekly report
    out.append(f"LINKS BY CAMPAIGN: not computed ({e})")

# sign-up card (Oct 11, Bastien deciding "a sign-up card on every page"): how often it's waved off, and where sign-ups come from
st = Counter()
for e in rows:
    if e["kind"] == "signup-step" and e["detail"] in ("no-thanks", "backbar-view", "backbar-close", "drop-ask"):
        st[e["detail"]] += 1
saw_deals = [s for s in alls if {"sizes-saved", "deal-click"} & s["kinds"] or "browse" in s["steps"]]
out.append(f"SIGN-UP CARD: sessions that saw deals {len(saw_deals)}; 'No thanks' taps {st['no-thanks']}; come-back sign-up bar shown "
           f"{st['backbar-view']}, closed {st['backbar-close']}; watchlist 'email me' asks {st['drop-ask']}; "
           f"sign-ups total {sum(wh.values())}, by where: " + (", ".join(f"{k} {v}" for k, v in wh.most_common(8)) or "none"))
shoe_signup = sum(1 for s in alls if "signup" in s["kinds"] and (s["entry"] or "").startswith(("/shoes", "/us/shoes", "/chaussures")))
out.append(f"  sessions that landed on a shoe page and signed up: {shoe_signup}")

# deal clicks per store (Oct 11: the affiliate pitch quotes each store's clicks): this window from analytics, and this month
# so far from our own click table (the monthly report's numbers)
dc = Counter((e["detail"] or "?").split("|")[0] for e in rows if e["kind"] == "deal-click")
out.append(f"DEAL CLICKS BY STORE (last {DAYS} days, {sum(dc.values())} clicks): " + ", ".join(f"{k} {v}" for k, v in dc.most_common(20)))
# Oct 23 (Bastien: "maybe the top drop can be removed"): clicks by the spot on the page they came from ("hook" = the Top drop link,
# "hero" = the big shoe photo), and how many sessions used each spot
spot = lambda e: ((e["detail"] or "").split("|") + [""] * 4)[3] or "card"
sc = Counter(spot(e) for e in rows if e["kind"] == "deal-click")
ss = Counter(sp for sid, sp in {(e["sid"], spot(e)) for e in rows if e["kind"] == "deal-click"})
out.append(f"DEAL CLICKS BY SPOT (clicks / sessions): " + ", ".join(f"{k} {v}/{ss[k]}" for k, v in sc.most_common(12))
           + f"; homepage sessions with sizes {sum(1 for x in S.values() if 'sizes-saved' in x['kinds'] or 'load' in x['kinds'])}")
try:
    now = datetime.now(timezone.utc)
    m0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    r = requests.post(f"{SB}/rest/v1/rpc/click_report", headers=H, timeout=60, json={"p_from": m0.isoformat(), "p_to": now.isoformat()})
    r.raise_for_status()
    c = r.json()
    bs = Counter(c.get("by_store") or {})
    SC["clicks"] = (int(c.get("clicks") or 0), now.day)
    out.append(f"THIS MONTH SO FAR (own click table): {int(c.get('visits') or 0)} visits, {int(c.get('clicks') or 0)} clicks; by store: "
               + ", ".join(f"{k} {v}" for k, v in bs.most_common(20)))
except Exception as e:
    out.append(f"This month's click table: couldn't read ({str(e)[:80]})")

# RETENTION DRIVERS (Oct 11, Bastien: "use our analytics to pinpoint exactly what we need to do"): for each device first seen in this
# window (2+ days ago, so it had time to come back), what it did on its first visit vs whether it came back on another day
try:
    from datetime import date as _d
    day = lambda e: e["at"][:10]
    dev = defaultdict(lambda: {"first": None, "days": set(), "k": set(), "entry": None, "src": None, "dev": None, "ref": None})
    for e in rows:
        if not e.get("sid"):
            continue
    # device id isn't in the selected columns: re-read did per session from a light query
    r2, ds = [], 0
    while True:
        rr = requests.get(f"{SB}/rest/v1/ana_events", headers={**H, "Range": f"{len(r2)}-{len(r2) + step - 1}"}, timeout=60,
                          params={"select": "did,sid,at,nv", "at": f"gte.{since}", "kind": "eq.visit", "order": "id"})
        rr.raise_for_status()
        bb = rr.json()
        r2 += bb
        if len(bb) < step:
            break
    sid_did = {x["sid"]: x["did"] for x in r2}
    first_sid, days_of = {}, defaultdict(set)
    for x in r2:
        days_of[x["did"]].add(x["at"][:10])
        if x["nv"] == 1 and x["did"] not in first_sid:
            first_sid[x["did"]] = (x["sid"], x["at"][:10])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    D = []
    for did, (sid, d0) in first_sid.items():
        if d0 > cutoff or sid not in S:
            continue
        ss = S[sid]
        back = any(dd > d0 for dd in days_of[did])
        D.append((ss, back))
    if D:
        base = sum(b for _, b in D) / len(D)
        out.append(f"RETENTION DRIVERS: {len(D)} devices first seen 2+ days ago; {round(100 * base)}% came back on another day. "
                   "Came back, by what they did on the first visit (did it / didn't):")
        feats = [("picked sizes", lambda s: "sizes-saved" in s["kinds"] or "shoe-page-size" in s["kinds"]),
                 ("hearted a deal", lambda s: "watch-add" in s["kinds"]), ("signed up", lambda s: "signup" in s["kinds"]),
                 ("clicked a store", lambda s: "deal-click" in s["kinds"]), ("searched", lambda s: "search" in s["kinds"] or "search-none" in s["kinds"]),
                 ("landed on homepage", lambda s: land(s) == "homepage"), ("landed on a shoe page", lambda s: land(s) == "shoe pages"),
                 ("came from reddit", lambda s: src(s) == "reddit"), ("came from google", lambda s: src(s) == "google"),
                 ("on a phone", lambda s: s["dev"] == "phone"), ("stayed 60s+", lambda s: (s["secs"] or 0) >= 60),
                 ("saw the come-back bar", lambda s: "store-offer" in s["kinds"] or "backbar-view" in s["steps"])]
        for name, f in feats:
            yes = [b for s_, b in D if f(s_)]
            no = [b for s_, b in D if not f(s_)]
            if yes:
                out.append(f"  {name}: {len(yes)} devices -> {round(100 * sum(yes) / len(yes))}% came back | didn't: "
                           f"{round(100 * sum(no) / max(1, len(no)))}% ({len(no)})")
except Exception as e:
    out.append(f"Retention drivers: couldn't compute ({str(e)[:80]})")

# EXPERIMENTS (Oct 17, Bastien: "data driven and proven methods ... no guessing"): devices first seen in this window (2+ days ago)
# split by their test group (the site sends "exp|<test>|A/B" once per session). A = as before, B = the new thing. A difference
# counts only when p < 0.05 (two-proportion z-test); until then it's "not proven yet".
try:
    import math
    def ztest(y1, n1, y2, n2):
        if not n1 or not n2:
            return 1.0
        p = (y1 + y2) / (n1 + n2)
        se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) or 1
        return math.erfc(abs(y1 / n1 - y2 / n2) / se / math.sqrt(2))
    tests = sorted({x.split("|")[1] for s_, _ in D for x in s_["steps"] if x and x.startswith("exp|")})
    for tname in tests:
        g = {"A": [], "B": []}
        for s_, b in D:
            a_ = next((x.split("|")[2] for x in s_["steps"] if x and x.startswith(f"exp|{tname}|")), None)
            if a_ in g:
                g[a_].append((s_, b))
        out.append(f"EXPERIMENT '{tname}' (A = as before, B = new): A {len(g['A'])} devices, B {len(g['B'])} devices")
        for mname, f in (("came back on another day", lambda s_, b: b),
                         ("went on to another of our pages", lambda s_, b: len(s_["pages"]) >= 2), ("signed up", lambda s_, b: "signup" in s_["kinds"]),
                         ("picked sizes", lambda s_, b: "sizes-saved" in s_["kinds"]),
                         ("clicked a store or picked sizes", lambda s_, b: "deal-click" in s_["kinds"] or "sizes-saved" in s_["kinds"]),
                         ("clicked a store", lambda s_, b: "deal-click" in s_["kinds"])):
            for who, keep in (("everyone", lambda s_: True), ("picked sizes", lambda s_: "sizes-saved" in s_["kinds"])):
                A = [f(s_, b) for s_, b in g["A"] if keep(s_)]
                B = [f(s_, b) for s_, b in g["B"] if keep(s_)]
                if A and B:
                    pv = ztest(sum(B), len(B), sum(A), len(A))
                    verdict = ("B WINS" if sum(B) / len(B) > sum(A) / len(A) else "A WINS") if pv < 0.05 else "not proven yet"
                    out.append(f"  {mname} ({who}): A {round(100 * sum(A) / len(A), 1)}% of {len(A)} | B {round(100 * sum(B) / len(B), 1)}% "
                               f"of {len(B)} | p={pv:.3f} -> {verdict}")
except Exception as e:
    out.append(f"Experiments: couldn't compute ({str(e)[:80]})")
# card parts (Oct 18, Bastien: shoe cards are "super crammed"): what people actually use on a card, in sessions
try:
    ss = lambda f: len({e["sid"] for e in rows if f(e)})
    dc = ss(lambda e: e["kind"] == "deal-click")
    out.append(f"CARD PARTS (sessions, last {DAYS} days): clicked a deal {dc} | 'All sizes & stores' "
               f"{ss(lambda e: e['kind'] == 'shoe-page-link' and (e['detail'] or '') == 'card')} | Watch price "
               f"{ss(lambda e: e['kind'] == 'watch-add')} | 'Wrong price or size?' sent "
               f"{ss(lambda e: e['kind'] == 'error' and (e['detail'] or '').startswith('report|'))} | shoe-page links from anywhere "
               f"{ss(lambda e: e['kind'] == 'shoe-page-link')}")
except Exception as e:
    out.append(f"Card parts: couldn't compute ({str(e)[:80]})")
# week vs week (Oct 18, plan Week 3 retention check): the last two full 7-day weeks before today, side by side
try:
    today = datetime.now(timezone.utc).date()
    weeks = [(today - timedelta(days=14), today - timedelta(days=8)), (today - timedelta(days=7), today - timedelta(days=1))]
    D = lambda x: datetime.fromisoformat(x).date()
    hh = {**H, "Prefer": "count=exact", "Range": "0-0"}
    def cnt2(params):
        rr = requests.get(f"{SB}/rest/v1/subscribers", headers=hh, params={"select": "email", **params}, timeout=30)
        rr.raise_for_status()
        return int(rr.headers.get("content-range", "*/0").split("/")[-1])
    out.append("WEEK VS WEEK (new devices that week; came back = visited again on a later day, so far):")
    for a0, a1 in weeks:
        g = [d for d in dv if a0 <= D(d["first_day"]) <= a1]
        b7 = sum(1 for d in g if (d["days"] or 1) > 1 and (D(d["last_day"]) - D(d["first_day"])).days <= 7)
        ev = [e for e in rows if a0 <= D(e["at"][:10]) <= a1]
        sess = lambda f: len({e["sid"] for e in ev if f(e)})
        made = cnt2({"and": f"(created_at.gte.{a0},created_at.lt.{a1 + timedelta(days=1)})"})
        conf = cnt2({"and": f"(created_at.gte.{a0},created_at.lt.{a1 + timedelta(days=1)})", "confirmed_at": "not.is.null"})
        SC["week"] = f"{a0:%b %d}-{a1:%b %d}: {len(g)} new devices, came back within 7 days {pct(b7, len(g))}, sign-ups {made}"
        out.append(f"  {a0:%b %d}-{a1:%b %d}: {len(g)} new devices, came back {pct(sum(1 for d in g if (d['days'] or 1) > 1), len(g))} (within 7 days: {pct(b7, len(g))}); "
                   f"sign-ups {made}, confirmed {conf} ({round(100 * conf / max(1, made))}%)")
        out.append(f"    Watch price taps {sess(lambda e: e['kind'] == 'watch-add')} sessions | 'Didn't buy it?' card shown "
                   f"{sess(lambda e: e['kind'] == 'signup-step' and (e['detail'] or '') == 'watch-offer')}, watched from it "
                   f"{sess(lambda e: e['kind'] == 'signup-step' and (e['detail'] or '') == 'watch-offer-yes')}, signed up from it "
                   f"{sess(lambda e: e['kind'] == 'signup' and 'watchoffer' in (e['detail'] or ''))} | shoe-page 'Didn't buy it?' bar shown "
                   f"{sess(lambda e: e['kind'] == 'signup-step' and (e['detail'] or '') == 'watchbar-view')} | Open my mail taps "
                   f"{sess(lambda e: e['kind'] == 'signup-step' and (e['detail'] or '').startswith('open-mail'))}")
except Exception as e:
    out.append(f"Week vs week: couldn't compute ({str(e)[:80]})")
# watchlist size (Oct 31, Bastien: should the free watchlist be 3 or 5 items? "yes pull the numbers"): members' watched items on the
# server (watches table, test addresses left out) + every device's Watch taps in this window (non-members' lists live only on their device)
try:
    ws, step = [], 1000
    while True:
        rr = requests.get(f"{SB}/rest/v1/watches", headers={**H, "Range": f"{len(ws)}-{len(ws) + step - 1}"}, timeout=60,
                          params={"select": "subscriber_id,item_key"})
        rr.raise_for_status()
        part = rr.json()
        ws += part
        if len(part) < step:
            break
    rr = requests.get(f"{SB}/rest/v1/subscribers", headers=H, timeout=30, params={"select": "id,email", "confirmed_at": "not.is.null", "unsubscribed_at": "is.null"})
    rr.raise_for_status()
    subs = rr.json()
    low = lambda e: (e or "").lower()
    pb = {re.sub(r"\+[^@]*@", "@", low(x["email"])) for x in subs if re.search(r"\+[^@]*@", low(x["email"]))}
    tst = lambda e: low(e).endswith(("@thegearfox.com", "@example.com")) or bool(re.search(r"\+[^@]*@", low(e))) or low(e) in pb
    real = {x["id"] for x in subs if not tst(x["email"])}
    per = Counter(w["subscriber_id"] for w in ws if w["subscriber_id"] in real and not (w["item_key"] or "").startswith("page|"))
    n = [per.get(i, 0) for i in real]
    band = lambda xs: (f"0: {sum(1 for x in xs if x == 0)}, 1: {sum(1 for x in xs if x == 1)}, 2: {sum(1 for x in xs if x == 2)}, "
                       f"3: {sum(1 for x in xs if x == 3)}, 4-5: {sum(1 for x in xs if 4 <= x <= 5)}, 6-10: {sum(1 for x in xs if 6 <= x <= 10)}, "
                       f"11+: {sum(1 for x in xs if x > 10)}")
    srt = sorted(n)
    out.append(f"WATCHLIST SIZE (members now, {len(real)} real members): {band(n)} | over 3: {sum(1 for x in n if x > 3)}, over 5: "
               f"{sum(1 for x in n if x > 5)}, over 10: {sum(1 for x in n if x > 10)}; most watched by one member: {max(n) if n else 0}")
    dev = Counter(e["sid"] for e in rows if e["kind"] == "watch-add")
    d = list(dev.values())
    out.append(f"  Watch taps per visit (last {DAYS} days, every visitor, adds only): {len(d)} visits tapped Watch; {band(d)}")
except Exception as e:
    out.append(f"Watchlist size: couldn't compute ({str(e)[:80]})")
# confirmations: of the sign-ups in this window, how many confirmed the email (double opt-in)
try:
    hh = {**H, "Prefer": "count=exact", "Range": "0-0"}
    def cnt(params):
        rr = requests.get(f"{SB}/rest/v1/subscribers", headers=hh, params={"select": "email", **params}, timeout=30)
        rr.raise_for_status()
        return int(rr.headers.get("content-range", "*/0").split("/")[-1])
    made = cnt({"created_at": f"gte.{since}"})
    conf = cnt({"created_at": f"gte.{since}", "confirmed_at": "not.is.null"})
    live = cnt({"confirmed_at": "not.is.null", "unsubscribed_at": "is.null"})
    unsub = cnt({"unsubscribed_at": "not.is.null"})
    # Oct 30 (Bastien: "I don't see 154 subscribers"): the list includes test addresses and the Oct 29 catch-up. Same rule as the
    # stats page (supabase/ana-members-oct30.sql): a test = @thegearfox.com / @example.com, any "+tag" address, and the plain
    # address those +tags belong to. No address in the code (public repo).
    rr = requests.get(f"{SB}/rest/v1/subscribers", headers=H, timeout=30,
                      params={"select": "email,consent_via", "confirmed_at": "not.is.null", "unsubscribed_at": "is.null"})
    rr.raise_for_status()
    act = rr.json()
    low = lambda e: (e or "").lower()
    plus_bases = {re.sub(r"\+[^@]*@", "@", low(x["email"])) for x in act if re.search(r"\+[^@]*@", low(x["email"]))}
    test = lambda e: low(e).endswith(("@thegearfox.com", "@example.com")) or bool(re.search(r"\+[^@]*@", low(e))) or low(e) in plus_bases
    tests = sum(1 for x in act if test(x["email"]))
    catch = sum(1 for x in act if not test(x["email"]) and x.get("consent_via") == "form-before-oct29")
    real = len(act) - tests
    SC["members"] = real
    out.append(f"EMAIL: sign-ups in this window {made}, confirmed {conf} ({round(100 * conf / max(1, made))}%); "
               f"REAL SUBSCRIBERS NOW {real} (list {live} = {real} real + {tests} test addresses; {catch} of the real ones joined "
               f"through the Oct 29 catch-up); unsubscribed ever {unsub}")
except Exception as e:
    out.append(f"Email numbers: couldn't read ({str(e)[:80]})")

# SEARCHES (Oct 24, Bastien: "the Google of the outdoor space"): what people look for, and what found nothing. A search counts
# once per session (the site sends it after 1.5 s of no typing; the last word typed is the one kept)
try:
    norm = lambda q: " ".join((q or "").lower().split())[:40]
    last = {}
    for e in rows:
        if e["kind"] in ("search", "search-none") and e["detail"] and ":" not in (e["detail"] or "")[:14]:
            last[(e["sid"], norm(e["detail"])[:3])] = (e["kind"], norm(e["detail"]))
    found = Counter(q for k, q in last.values() if k == "search")
    none = Counter(q for k, q in last.values() if k == "search-none")
    nses = len({sid for sid, _ in last})
    if last:
        out.append(f"SEARCHES: {nses} sessions searched, {sum(found.values()) + sum(none.values())} searches, "
                   f"{sum(none.values())} found nothing ({round(100 * sum(none.values()) / max(1, sum(found.values()) + sum(none.values())))}%)")
        out.append("  top searches: " + ", ".join(f"{q} {n}" for q, n in found.most_common(20)))
        if none:
            out.append("  found nothing: " + ", ".join(f"{q} {n}" for q, n in none.most_common(25)))
        dym = Counter((e["detail"] or "")[14:] for e in rows if e["kind"] == "search" and (e["detail"] or "").startswith("did-you-mean: "))
        if dym:
            out.append("  'Did you mean' taps: " + ", ".join(f"{q} {n}" for q, n in dym.most_common(10)))
except Exception as e:
    out.append(f"Searches: couldn't read ({str(e)[:80]})")

# FOX PRO PRICE TEST (Nov 2-16, agreed Oct 25): returning visitors see a waitlist card, A = $3/month or $29/year, B = $5/month or
# $49/year. Per device (a device that saw it in several sessions counts once). Rule: build Pro if 5%+ of viewers join at a price;
# both pass -> the higher price unless the lower one gets clearly more people (p < 0.05)
try:
    import math as _m
    view, join, no = {"A": set(), "B": set()}, {"A": set(), "B": set()}, {"A": set(), "B": set()}
    did = {}
    for e in rows:
        d_ = e.get("detail") or ""
        # before Nov 2 only robots saw the card (site test ?pro=1; their keepalive sends leaked past the stand-in until Oct 28)
        if e["kind"] == "signup-step" and d_.startswith(("pro-view|", "pro-join|", "pro-no|")) and str(e["at"])[:10] >= "2026-11-02":
            k, a_ = d_.split("|")[:2]
            dev_ = e["sid"]            # one session = one device here (sessions don't carry the device id)
            {"pro-view": view, "pro-join": join, "pro-no": no}[k].setdefault(a_, set()).add(dev_)
    if view["A"] or view["B"]:
        def zt(y1, n1, y2, n2):
            if not n1 or not n2:
                return 1.0
            p_ = (y1 + y2) / (n1 + n2)
            se = _m.sqrt(p_ * (1 - p_) * (1 / n1 + 1 / n2)) or 1
            return _m.erfc(abs(y1 / n1 - y2 / n2) / se / _m.sqrt(2))
        nA, nB, jA, jB = len(view["A"]), len(view["B"]), len(join["A"] & view["A"]), len(join["B"] & view["B"])
        out.append(f"FOX PRO PRICE TEST (sessions that saw the card): $3/$29 (A) {pct(jA, nA)} joined of {nA}, 'No thanks' {len(no['A'])} | "
                   f"$5/$49 (B) {pct(jB, nB)} joined of {nB}, 'No thanks' {len(no['B'])} | difference p={zt(jA, nA, jB, nB):.3f} "
                   f"| rule: build at a price where 5%+ join")
except Exception as e:
    out.append(f"Fox Pro test: couldn't read ({str(e)[:80]})")

# Race gear lists (Oct 23, Bastien: "a tracker to see how and if people are using the gear checklist")
try:
    RP = ("/races/", "/courses/", "/us/races/")
    isrp = lambda pth: any(pth.startswith(x) for x in RP)
    rs = [s for s in S.values() if any(isrp(pth or "") for pth in s["pages"])]
    rland = [s for s in new if isrp(s["entry"] or "")]
    if rs:
        did = lambda s, w: any(x[1] == w for x in s["race"])
        rclick = [s for s in rs if any("||race|" in d for d in s["dclick"])]
        other = [s for s in rs if any(not isrp(pth or "") for pth in s["pages"])]
        n = len(rs)
        out.append(f"RACE GEAR LISTS: {n} sessions opened one ({len(rland)} first visits landed on one); of the {n}: "
                   f"changed distance {pct(sum(did(s, 'dist') for s in rs), n)}, ticked an item {pct(sum(did(s, 'have') for s in rs), n)}, "
                   f"ticked every mandatory item {pct(sum(did(s, 'complete') for s in rs), n)}, 'See all' {pct(sum(did(s, 'seeall') for s in rs), n)}, "
                   f"picked a size {pct(sum(did(s, 'size') or did(s, 'shoesize') for s in rs), n)}, clicked a store {pct(len(rclick), n)}, "
                   f"watched an item {pct(sum('watch-add' in s['kinds'] for s in rs), n)}, signed up {pct(sum('signup' in s['kinds'] for s in rs), n)}, "
                   f"went on to another of our pages {pct(len(other), n)}")
        rm = Counter(x[2] for s in rs for x in s["race"] if x[1] == "remind")   # Oct 31: "Remind me 30 days before" (new / member / pending)
        out.append(f"  race reminders asked: {sum(rm.values())} ({', '.join(f'{k} {v}' for k, v in rm.most_common()) or 'none yet'}), "
                   f"in {pct(sum(did(s, 'remind') for s in rs), n)} of the sessions")
        per = Counter(pth.strip("/").split("/")[-1] for s in rs for pth in s["pages"] if isrp(pth or ""))
        out.append("  by race (sessions): " + ", ".join(f"{k} {v}" for k, v in per.most_common(12)))
        refs = Counter(s["ref"] for s in rs if s["ref"])
        if refs:
            out.append("  by link (?ref=): " + ", ".join(f"{k} {v}" for k, v in refs.most_common(8)))
        ticks = Counter(x[2] for s in rs for x in s["race"] if x[1] == "have")
        if ticks:
            out.append("  items ticked 'I have it': " + ", ".join(f"{k} {v}" for k, v in ticks.most_common(10)))
        clicks = Counter(d.split("|")[1] or "?" for s in rs for d in s["dclick"] if "||race|" in d)
        if clicks:
            out.append("  store clicks by item: " + ", ".join(f"{k} {v}" for k, v in clicks.most_common(10)))
except Exception as e:
    out.append(f"Race gear lists: couldn't read ({str(e)[:80]})")

# HIKING (Oct 26: live since Oct 25): the Running | Hiking switch, boot price pages, trail gear lists
try:
    HP = ("/hikes/", "/randonnees/", "/us/hikes/")
    BP = ("/hiking-boots/", "/bottes-randonnee/", "/us/hiking-boots/")
    on = lambda s, P: any(any((pth or "").startswith(x) for x in P) for pth in s["pages"])
    hs = [s for s in S.values() if s["sport"] == "hike"]
    hn = [s for s in new if s["sport"] == "hike"]
    homen = [s for s in new if "/" in s["pages"]]
    tl = [s for s in S.values() if on(s, HP) or s["hike"]]
    bp = [s for s in S.values() if on(s, BP)]
    out.append(f"HIKING: {len(hs)} sessions switched to Hiking ({pct(len(hn), len(homen))} of homepage first visits); of those "
               f"sessions: picked sizes {pct(sum('sizes-saved' in s['kinds'] for s in hs), len(hs))}, clicked a store "
               f"{pct(sum('deal-click' in s['kinds'] for s in hs), len(hs))}, signed up {pct(sum('signup' in s['kinds'] for s in hs), len(hs))}")
    out.append(f"  boot price pages: {len(bp)} sessions ({sum(1 for s in new if any((s['entry'] or '').startswith(x) for x in BP))} first visits landed), "
               f"clicked a store {pct(sum('deal-click' in s['kinds'] for s in bp), len(bp))} | trail gear lists: {len(tl)} sessions "
               f"({sum(1 for s in new if any((s['entry'] or '').startswith(x) for x in HP))} landed), ticked an item "
               f"{pct(sum(any(x[1] == 'have' for x in s['hike']) for s in tl), len(tl))}, changed trip length "
               f"{pct(sum(any(x[1] in ('trip', 'dist') for x in s['hike']) for s in tl), len(tl))}, clicked a store "
               f"{pct(sum('deal-click' in s['kinds'] for s in tl), len(tl))}, signed up {pct(sum('signup' in s['kinds'] for s in tl), len(tl))}")
    per = Counter(x[0] for s in tl for x in s["hike"][:1])
    if per:
        out.append("  trails opened (sessions): " + ", ".join(f"{k} {v}" for k, v in per.most_common(12)))
except Exception as e:
    out.append(f"Hiking: couldn't read ({str(e)[:80]})")

# KIT LAYOUT TEST (Oct 27, Bastien: "Yes race kit"): race + trail gear list sessions by test 'kit' group (B = every line folded to one
# row). Metric: sessions that ticked an item or clicked a store (baseline ~4%); keep B only at p < 0.05.
try:
    LP = ("/races/", "/courses/", "/us/races/", "/hikes/", "/randonnees/", "/us/hikes/")
    kg = {"A": [], "B": []}
    for s in S.values():
        if any(any((pth or "").startswith(x) for x in LP) for pth in s["pages"]):
            a_ = next((x.split("|")[2] for x in s["steps"] if x and x.startswith("exp|kit|")), None)
            if a_ in kg:
                kg[a_].append(s)
    if kg["A"] or kg["B"]:
        import math as _mk
        used = lambda s: any(x[1] == "have" for x in s["race"] + s["hike"]) or "deal-click" in s["kinds"]
        yA, yB, nA, nB = sum(map(used, kg["A"])), sum(map(used, kg["B"])), len(kg["A"]), len(kg["B"])
        pp = (yA + yB) / max(1, nA + nB)
        se = _mk.sqrt(pp * (1 - pp) * (1 / max(1, nA) + 1 / max(1, nB))) or 1
        pv = _mk.erfc(abs(yA / max(1, nA) - yB / max(1, nB)) / se / _mk.sqrt(2)) if nA and nB else 1.0
        out.append(f"KIT LAYOUT TEST (race + trail list sessions that ticked an item or clicked a store): A {pct(yA, nA)} of {nA} | "
                   f"B {pct(yB, nB)} of {nB} | p={pv:.3f} -> " + (("B WINS" if yB / nB > yA / nA else "A WINS") if pv < 0.05 else "not proven yet")
                   + f" | clicked a store: A {pct(sum('deal-click' in s['kinds'] for s in kg['A']), nA)}, B {pct(sum('deal-click' in s['kinds'] for s in kg['B']), nB)}")
        # Oct 30 (growth chat: 18 A vs 4 B sessions looked like a broken coin): the coin is per DEVICE, the counts above are sessions,
        # so one device opening the list 10 times tilts them. Devices per group, and the busiest device's share of its group:
        sd = globals().get("sid_did") or {}
        sid_of = {id(s_): k_ for k_, s_ in S.items()}
        for g_ in ("A", "B"):
            ds = Counter(sd.get(sid_of[id(s_)]) for s_ in kg[g_])
            ds.pop(None, None)
            if ds:
                out.append(f"  kit {g_}: {len(ds)} devices; busiest device {ds.most_common(1)[0][1]} of {len(kg[g_])} sessions")
except Exception as e:
    out.append(f"Kit layout test: couldn't read ({str(e)[:80]})")

# SCORECARD (Oct 24, Bastien: "weekly checkins ... to ensure we are optimizing the data we collect and where people drop off"):
# the few numbers the Monday check-in starts from, against the Path to $300K milestones (plan doc). The store-commission line
# is an estimate: $0.05-0.15 a click (Sovrn's quoted earnings per click ranged $0.04-0.33), and only stores in a program earn.
try:
    srcs = Counter(src(s) for s in new)
    sc = ["SCORECARD (milestone Mar 2027: 2,000 members, $1,000/month)",
          f"  first visits {len(new)}: " + ", ".join(f"{k} {v}" for k, v in srcs.most_common(5))]
    sc += [f"  {SC[k]}" for k in ("home", "redesign before Oct 22", "redesign from Oct 22", "shoe", "week") if k in SC]
    if "members" in SC:
        sc.append(f"  active subscribers {SC['members']} (milestone 2,000)")
    if "clicks" in SC:
        n, d = SC["clicks"]
        pace = round(n * 30 / max(1, d))
        sc.append(f"  store clicks this month {n} (pace ~{pace:,}/month); if every store paid: ~${round(pace * 0.05):,}-{round(pace * 0.15):,}/month (estimate)")
    out[1:1] = sc
except Exception as e:
    out.insert(1, f"Scorecard: couldn't build ({str(e)[:80]})")

text = "\n".join(out)
print(text)
if os.environ.get("GITHUB_ACTIONS"):
    parts, cur = [], ""
    for ln in out:                      # GitHub cuts a notice at ~4 KB (Oct 11: the end was lost): several notices, in order
        if len(cur) + len(ln) > 3500:
            parts.append(cur)
            cur = ""
        cur += ln + "\n"
    parts.append(cur)
    for i, ptxt in enumerate(parts, 1):
        print(f"::notice title=Funnel {i}/{len(parts)}::" + ptxt.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
