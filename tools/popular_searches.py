"""Popular searches (Oct 27, Bastien OK'd idea 4): what people searched most in the last 7 days, kept only when today's search
still finds 5+ deals on that side, so a tap never lands on "Nothing matches". Feeds the chips under the search box (test 'popq').

  python tools/popular_searches.py SITE_DIR      (needs SUPABASE_URL + SUPABASE_SECRET_KEY; without them it keeps what's there)
-> SITE/popular.json {"ca": ["Superblast", "Evo SL", ...], "us": [...]}
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import search_check as SC  # noqa: E402

SB = os.environ.get("SUPABASE_URL", "https://krwymmkauwqqxjxbvkyq.supabase.co")
KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
DAYS, MIN_SESSIONS, MIN_DEALS, KEEP = 7, 2, 5, 8


def searches():
    """Each search once per session (the site sends it after 1.5 s of no typing), like tools/funnel.py."""
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    since = (datetime.now(timezone.utc) - timedelta(days=DAYS)).isoformat()
    rows, step = [], 1000
    while True:
        r = requests.get(f"{SB}/rest/v1/ana_events", headers={**h, "Range": f"{len(rows)}-{len(rows) + step - 1}"}, timeout=60,
                         params={"select": "sid,detail", "kind": "eq.search", "at": f"gte.{since}", "order": "id"})
        r.raise_for_status()
        got = r.json()
        rows += got
        if len(got) < step:
            break
    seen = {}
    for e in rows:
        q = " ".join((e.get("detail") or "").lower().split())[:40]
        if q and ":" not in q[:14] and len(q) >= 3:            # "any-size: …", "did-you-mean: …" are follow-ups, not searches
            seen[(e["sid"], q[:3])] = q                          # the last word typed in that session wins
    return Counter(seen.values())


def label(q, items):
    """How the store/maker writes it ("evo sl" -> "Evo SL", "norda" -> "norda"): the spelling in today's names, else Title case."""
    out = []
    for w in q.split():
        best = Counter(t for d in items[:400] for t in f'{d["b"]} {d["n"]}'.split() if t.lower().strip("(),") == w).most_common(1)
        out.append(best[0][0].strip("(),") if best else w.capitalize())
    return " ".join(out)


def main():
    site = Path(sys.argv[1])
    if not KEY:
        print("popular searches: no SUPABASE_SECRET_KEY, kept yesterday's list")
        return
    counts = searches()
    res = {}
    for side, f in (("ca", "sale.json"), ("us", "sale-us.json")):
        p = site / f
        if not p.exists():
            continue
        items = json.loads(p.read_text())["items"]
        hays = [SC.hay(d) for d in items]
        keep = []
        for q, n in counts.most_common(80):
            if n < MIN_SESSIONS or len(keep) >= KEEP:
                break
            if any(q.startswith(k + " ") or k.startswith(q + " ") or k == q for k in keep):   # "evo" vs "evo sl": the more searched one
                continue
            w = SC.words(q)
            hits = [d for d, h in zip(items, hays) if all(SC.qhas(h, x) for x in w)]
            if len(hits) >= MIN_DEALS:
                keep.append(q)
        res[side] = [label(q, [d for d, h in zip(items, hays) if all(SC.qhas(h, x) for x in SC.words(q))]) for q in keep]
    (site / "popular.json").write_text(json.dumps(res, ensure_ascii=False))
    print("popular searches:", res)


if __name__ == "__main__":
    main()
