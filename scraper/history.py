#!/usr/bin/env python3
"""Price history: the base for "Is this deal real?" (lowest price in 60 days vs. a price raised before a sale).

Keeps one line per product in a JSON-lines file that lives on the `history` branch (not on the site, so a failed
download can never wipe it). Each line is {"k": product id, "h": [[day, best price, regular price], ...]} with a
new entry only when the best price changes (several runs on one day keep that day's lowest). Entries older than
KEEP_DAYS are dropped, except the last one before the window, which says what the price was going into it.

It also writes two fields into deals.json and sale.json (and the USA side's deals-us.json / sale-us.json, tracked in USD
under "us|" keys) for every product it has seen:
  lo  lowest best price over the last WINDOW days (today included)
  hd  how many days of history we have for it (the site waits for enough history before showing a badge)
  hi  highest best price over the same window (the badge needs a real drop, not a price that never moved)

Usage: python scraper/history.py HISTORY_FILE SITE_DIR [--no-save]
       (--no-save: annotate the site files without recording today, e.g. on upload runs)
"""
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

WINDOW = 60
KEEP_DAYS = 120


def item_key(d):
    """Same id as alerts.py and the site's itemKey()."""
    return f"{d['b']}|{d['n']}|{d['g']}|{1 if d.get('w') else 0}".lower()


def load(path):
    hist = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                hist[row["k"]] = row["h"]
    return hist


def save(path, hist):
    lines = [json.dumps({"k": k, "h": h}, separators=(",", ":"), ensure_ascii=False) for k, h in sorted(hist.items())]
    path.write_text("\n".join(lines) + "\n")


US = "us|"     # USA side (Oct 6, 2026): its own lines, in US dollars, so a moving exchange rate never fakes a "lowest price"


def today_prices(items, prefix="", fx=1.0):
    """Best (lowest) and regular price per product today; a product listed twice (Canada and abroad) keeps the lowest.
    The site files keep every price in CAD; the USA side is recorded in USD (prefix US, fx = CAD per USD)."""
    out = {}
    for d in items:
        if not d.get("sz"):
            continue
        best = min(e[1] for e in d["sz"]) / fx
        reg = max((e[3] for e in d["sz"] if len(e) > 3), default=best * fx) / fx
        k = prefix + item_key(d)
        if k not in out or best < out[k][0]:
            out[k] = (round(best, 2), round(reg, 2))
    return out


def record(hist, prices, day):
    for k, (best, reg) in prices.items():
        h = hist.setdefault(k, [])
        if h and h[-1][0] == day:
            if best < h[-1][1]:
                h[-1] = [day, best, reg]
        elif not h or h[-1][1] != best:
            h.append([day, best, reg])


def prune(hist, day):
    cut = (date.fromisoformat(day) - timedelta(days=KEEP_DAYS)).isoformat()
    for k, h in hist.items():
        older = [e for e in h if e[0] < cut]
        hist[k] = (older[-1:] if older else []) + [e for e in h if e[0] >= cut]


def lowest(h, day, today_best=None):
    """Lowest price in the WINDOW days up to `day`, how many days of history there are, and the highest price in the window
    (the badge needs a real drop: a price that sat still for a month isn't news)."""
    start = (date.fromisoformat(day) - timedelta(days=WINDOW)).isoformat()
    before = [e for e in h if e[0] < start]
    inside = [e[1] for e in h if e[0] >= start]
    prices = inside + ([before[-1][1]] if before else []) + ([today_best] if today_best is not None else [])
    first = h[0][0] if h else day
    return (min(prices) if prices else None), (date.fromisoformat(day) - date.fromisoformat(first)).days, (max(prices) if prices else None)


def annotate(site, hist, prices, day, names=("deals.json", "sale.json"), prefix="", fx=1.0):
    for name in names:
        p = site / name
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        for d in data.get("items", []):
            k = prefix + item_key(d)
            if k not in hist and k not in prices:
                continue
            lo, hd, hi = lowest(hist.get(k, []), day, prices.get(k, (None,))[0])
            if lo is not None:
                d["lo"], d["hd"], d["hi"] = round(lo * fx, 2), hd, round(hi * fx, 2)   # back in CAD, like every price in the site files
        p.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path, site = Path(args[0]), Path(args[1])
    day = datetime.now(ZoneInfo("America/Vancouver")).date().isoformat()
    hist = load(path)
    items = json.loads((site / "deals.json").read_text())["items"]
    prices = today_prices(items)
    us_prices, fx = {}, 1.0
    if (site / "deals-us.json").exists():
        us = json.loads((site / "deals-us.json").read_text())
        fx = float((us.get("fx") or {}).get("USD") or 0) or 1.0
        us_prices = today_prices(us["items"], US, fx)
    if "--no-save" not in sys.argv:
        record(hist, {**prices, **us_prices}, day)
        prune(hist, day)
        save(path, hist)
    annotate(site, hist, prices, day)
    if us_prices:
        annotate(site, hist, us_prices, day, ("deals-us.json", "sale-us.json"), US, fx)
    days = sorted({e[0] for h in hist.values() for e in h})
    print(f"price history: {len(hist)} products, {len(days)} days with changes "
          f"(since {days[0] if days else 'today'}), {sum(len(h) for h in hist.values())} price points")


if __name__ == "__main__":
    main()
