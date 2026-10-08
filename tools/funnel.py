#!/usr/bin/env python3
"""First-visit funnel, split by where people land (Oct 5, 2026). Read-only: totals only, nothing personal.

The dashboard's "Arrived" counts every first visit, including people landing on a shoe page from Google, who never see
the welcome screen. This splits the funnel by landing page and shows how fast people leave, so the drop is measured
on the homepage only. Prints the result, and as a GitHub notice (readable from the run's annotations).

  SUPABASE_URL=... SUPABASE_SECRET_KEY=... python tools/funnel.py [DAYS]     (workflow: .github/workflows/funnel.yml)
"""
import os
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
                         "steps": set(), "n": 0})
for e in rows:
    s = S[e["sid"]]
    s["n"] += 1
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

new = [s for s in S.values() if s["nv"] == 1]
out = [f"Last {DAYS} days: {len(rows)} events, {len(S)} sessions, {len(new)} first visits"]


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
               f"went on to the homepage {pct(sum(1 for s in shoe if 'welcome-view' in s['kinds'] or 'sizes-saved' in s['kinds']), len(shoe))}")
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

text = "\n".join(out)
print(text)
if os.environ.get("GITHUB_ACTIONS"):
    print("::notice title=Funnel::" + text.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
