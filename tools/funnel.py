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
                     params={"select": "sid,kind,detail,num,page,dev,ref,nv,at", "at": f"gte.{since}", "order": "id"})
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
ret = [s for s in S.values() if (s["nv"] or 0) > 1]
out.append(f"Returning visits {len(ret)}: clicked a deal {pct(sum(1 for s in ret if 'deal-click' in s['kinds']), len(ret))}")

text = "\n".join(out)
print(text)
if os.environ.get("GITHUB_ACTIONS"):
    print("::notice title=Funnel::" + text.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
