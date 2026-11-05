"""Store risk list (Nov 5, 2026; growth chat after the lockout talk with Bastien): which stores could lock us out, and what it would cost.

    python tools/store_risk.py [SCRAPE_LOG ...] > docs/store-risk.md

For every store we read: how we read it, requests per read (from the scrape logs' "polite:" lines when given; the logs list the top
25 sites, the rest are small), the last failure we know of and its kind (locked out = the store said no: 403/429/robots/country
page; our reader broke = we misread a page; the store's own problem = its server or file was broken), and its share of today's sale
cards: how many cards it gives the best price on in at least one size, and how many cards ONLY it has (lost if it locks us out).
Reads the live sale.json + sale-us.json + deals.json "stores"/"failed"/"fails" (scrape.py keeps the last failure per store since Nov 5).
"""
import collections, datetime as dt, json, re, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import scrape as SC                                    # noqa: E402  (store tables only; nothing is read from the stores)

LIVE = "https://thegearfox.com/"
UA = {"User-Agent": "TheGearFoxBot/1.0 (+https://thegearfox.com/about.html)"}

# How each non-Shopify store is read. kind: open = a public file or page the store publishes for everyone (products.json, feed,
# listing pages); service = the data service the store's own pages call (public key, no login, but the store can close it any time);
# night = a slow copy made at night from GitHub; saved = pages Bastien saves by hand; file = the catalog file (parked).
METHOD = {
    "altitude": ("service", "its catalogue service + product pages (commercetools), ~2,100 requests a read"),
    "lasthunt": ("service", "its catalogue service + product pages (commercetools), ~1,400 requests a read"),
    "sportinglife": ("open", "listing + product pages"),
    "footlocker": ("open", "listing + product pages"),
    "sea2sky": ("open", "listing pages"),
    "stampeak": ("open", "listing pages"),
    "runningroom": ("open", "its own public product feed (22 files, listed in robots.txt)"),
    "thefeed": ("night", "products.json, slowly at night (it rate-limits GitHub by day)"),
    "decathlon": ("night", "listing + product pages, one every 20 s at night (429 by day since Oct 5)"),
    "runningfree": ("night", "listing + size pages, one every 30 s at night (its Crawl-delay)"),
    "fleetfeet": ("night", "product pages, one every 2 s at night (~3,000 a night)"),
    "saucony": ("night", "brand site pages + its size service, one every 3 s at night"),
    "arcteryx": ("night", "brand site sitemap + product pages at night"),
    "mec": ("saved", "Bastien's saved pages (Grab deals bookmark)"),
    "rei": ("saved", "Bastien's saved pages (Grab deals bookmark)"),
    "backcountry": ("saved", "Bastien's saved pages (Grab deals bookmark)"),
    "catalog": ("file", "catalog file (parked Oct 30)"),
    "adidasca": ("file", "catalog file (parked Oct 30)"),
}
# Failures before deals.json kept them (from the health emails and CLAUDE.md), newest first. kind: locked / broke / store
KNOWN = {
    "runningroom": [("2026-11-05", "store", "one of its 22 feed files was a picture (19 KB); also Oct 12 + Oct 18")],
    "runningfree": [("2026-11-05", "locked", "country page 'only available to visitors in Canada' to GitHub's US computers (was 'Canada or the United States')")],
    "sportchek": [("2026-11-04", "locked", "HTTP 403 at both reads: OFF since Nov 5")],
    "sportsexperts": [("2026-11-02", "locked", "robots.txt AI block (ClaudeBot Disallow /): OFF")],
    "runfree": [("2026-10-30", "locked", "robots.txt Disallow /api/ on all 27 RunFree shops: OFF")],
    "thefeed": [("2026-10-08", "locked", "429 local_rate_limited by day: moved to a slow night read")],
    "decathlon": [("2026-10-08", "locked", "429 after ~50 pages even at night: one page every 20 s")],
    "backcountry": [("2026-10-06", "locked", "HTTP 202 empty page to GitHub: saved pages only")],
    "salomon": [("2026-10-16", "locked", "403 after ~1 h of pages: never read")],
    "hoka": [("2026-10-16", "locked", "403 most visits: never read")],
}
# What would lower each store's risk (the top 5 print it). Never: disguised browsers, other computers' addresses, captcha solvers.
LOWER = {
    "runningfree": "Its country page now says Canada only, and GitHub's computers are in the US. Ask Running Free (they're friendly to links: "
                   "we send them clicks) for permission or a product file; until then it leaves the site 48 h after its last copy. Never read it "
                   "through a Canadian address to get past the page.",
    "thefeed": "Already slow (a page every 10 s at night). Lower: read only products changed since last night (products.json updated_at), "
               "and apply to its CJ affiliate product feed (the real fix).",
    "lasthunt": "~1,400 requests a read, twice a day, through its catalogue service. Lower: re-read a product page only when its listing "
                "changed or it's on sale (already), move the second daily read to night, and ask Rakuten/FlexOffers for its product feed.",
    "altitude": "~2,100 requests a read, twice a day, same service as The Last Hunt (same company). Same steps: fewer re-reads, one read a "
                "day at night, product feed via Rakuten/FlexOffers or Sovrn in January.",
    "borealrunning": "Public products.json, ~15 requests a read: low risk per read, but 894 cards only here. Nothing to slow down; a short "
                     "hello email (we link to them, here are the clicks) makes a lockout less likely.",
    "runningroom": "Its own feed for AI tools (robots.txt lists it): the lowest-risk door. Its files sometimes come back broken (handled since Nov 5).",
    "decathlon": "Already one page every 20 s at night after 429s. Lower: fewer pages (only lists that changed). Affiliate feed declined Oct 6; reapply December.",
    "fleetfeet": "~3,000 product pages a night at one every 2 s. Lower: sale products nightly, the rest every 3 nights (already a cursor); "
                 "a 403/429 = stop.",
}
OFF = {"sportchek": "Sport Chek", "sportsexperts": "Sports Experts", "runfree": "27 RunFree shops"}


def get(path):
    with urllib.request.urlopen(urllib.request.Request(LIVE + path, headers=UA), timeout=120) as r:
        return json.loads(r.read())


def host(u):
    return re.sub(r"^www\.", "", u.split("/")[2]) if u and "//" in u else ""


def store_hosts():
    m = {}
    for st, base, *_ in SC.SHOPIFY_STORES + SC.WOO_SITES + SC.LIGHTSPEED_SITES:
        m[host(base)] = st
    m.update({"altitude-sports.com": "altitude", "thelasthunt.com": "lasthunt", "sportinglife.ca": "sportinglife", "footlocker.ca": "footlocker",
              "ca.shop.runningroom.com": "runningroom", "thefeed.com": "thefeed", "decathlon.ca": "decathlon", "runningfree.com": "runningfree",
              "fleetfeet.com": "fleetfeet", "saucony.com": "saucony", "arcteryx.com": "arcteryx", "mec.ca": "mec", "rei.com": "rei",
              "backcountry.com": "backcountry", "sea2sky.ca": "sea2sky", "stampeak.com": "stampeak"})
    return m


def shares():
    """Per store: cards where it has the best price in at least one size, and cards only it carries (both sides)."""
    hm, best, only, total = store_hosts(), collections.Counter(), collections.Counter(), 0
    for f in ("sale.json", "sale-us.json"):
        for it in get(f)["items"]:
            sts = []
            for u in it.get("of") or []:
                h = host(u)
                sts.append(hm.get(h) or next((v for k, v in hm.items() if h.endswith(k)), h))
            win = {sts[e[2]] for e in it["sz"] if len(e) > 2 and isinstance(e[2], int) and e[2] < len(sts) and e[1] < e[3] * 0.99}
            total += bool(win)
            for s in win:
                best[s] += 1
            if len(set(sts)) == 1 and sts and win:
                only[sts[0]] += 1
    return best, only, total


def requests_from_logs(paths):
    n = collections.Counter()
    for p in paths:
        for line in Path(p).read_text(errors="ignore").splitlines():
            m = re.search(r"^\S*\s+([a-z0-9.-]+\.[a-z]{2,}): (\d+)", line)
            if m:
                n[host("https://" + m.group(1))] += int(m.group(2))
    return n


def main():
    deals = get("deals.json")
    stamps, failed, fails = deals.get("stores", {}), deals.get("failed", {}), deals.get("fails", {})
    best, only, total = shares()
    reqs = requests_from_logs(sys.argv[1:])
    hm = store_hosts()
    rq = collections.Counter()
    for h, n in reqs.items():
        rq[hm.get(h) or h] += n
    shop = {x[0] for x in SC.SHOPIFY_STORES}
    woo = {x[0] for x in SC.WOO_SITES + SC.LIGHTSPEED_SITES}
    rows = []
    for st in SC.STORES:
        kind, how = METHOD.get(st) or (("open", "public products.json (Shopify)") if st in shop else
                                        ("open", "public shop data (WooCommerce / Lightspeed)") if st in woo else ("open", "?"))
        last = None
        if st in fails:
            f = fails[st]
            last = (f.get("at", "")[:10], f.get("kind", "?"), f.get("why", ""))
        elif st in failed:
            last = (deals.get("updated", "")[:10], SC.fail_kind(failed[st]) if hasattr(SC, "fail_kind") else "?", failed[st])
        elif st in KNOWN:
            last = KNOWN[st][0]
        # risk: what we'd lose (cards only they have count 3x) x how fragile the door is
        door = {"service": 3, "night": 2.5, "saved": 0.2, "file": 0.2, "open": 1}[kind]   # saved pages can't lock us out (Bastien's own visits): their risk is going stale
        if last and last[1] == "locked" and kind not in ("saved", "file"):
            door += 2
        loss = only[st] * 3 + best[st]
        rows.append((loss * door, st, kind, how, rq.get(st), last, best[st], only[st], stamps.get(st, "")[:16]))
    rows.sort(reverse=True)
    today = dt.date.today().isoformat()
    print(f"# Store risk list ({today})\n")
    print("Built by `tools/store_risk.py` from the live site's files and the morning read's log. **Cards** = today's sale cards (Canada + USA) "
          f"where the store has the best price in at least one size; **only here** = cards no other store carries (gone if it locks us out). "
          f"{total:,} sale cards in all.\n")
    print("Kinds of failure: **locked out** = the store said no (403/429, robots.txt, a country page): we stop and never work around it. "
          "**Reader broke** = we misread a page (our fix). **Store's own problem** = its server or file was broken (it comes back by itself).\n")
    print("## Top 5 at risk\n")
    for score, st, kind, how, n, last, b, o, at in [r for r in rows if r[2] not in ("saved", "file")][:5]:
        print(f"- **{st}** ({how}): {b:,} cards, {o:,} only here" + (f"; last failure {last[0]} ({last[1]}: {last[2]})" if last else ""))
        if st in LOWER:
            print(f"  - What lowers it: {LOWER[st]}")
    sv = [r for r in rows if r[2] == "saved"]
    if sv:
        print("\nSaved pages can't lock us out (they're Bastien's own visits); their risk is going stale after 5 days without a save: "
              + ", ".join(f"{r[1]} ({r[6]:,} cards, {r[7]:,} only here)" for r in sv) + ".")
    print("\n## Every store\n")
    print("| Store | How we read it | Requests a read | Cards | Only here | Last good read | Last failure |")
    print("|---|---|---|---|---|---|---|")
    for score, st, kind, how, n, last, b, o, at in rows:
        if not (b or o or last or kind != "open"):
            continue
        print(f"| {st} | {how} | {n if n else '-'} | {b:,} | {o:,} | {at.replace('T', ' ') or '-'} | "
              + (f"{last[0]} {last[1]}: {last[2][:90]}" if last else "-") + " |")
    small = [st for _, st, kind, _, _, last, b, o, _ in rows if not (b or o or last or kind != "open")]
    print(f"\n{len(small)} more stores (public products.json, no sale card and no failure today): {', '.join(sorted(small))}.\n")
    print("Off on purpose: " + ", ".join(f"{v} ({KNOWN[k][0][2]})" for k, v in OFF.items()) + ".")


if __name__ == "__main__":
    main()
