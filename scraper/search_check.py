#!/usr/bin/env python3
"""Searches that found nothing, sorted by why (Oct 10, 2026; Bastien, from the stats page: "arcteryx", "goretex" and
"a1080v15" found nothing, and he asked for this in the daily check).

Every "search-none" from the last 24 hours (analytics, only the words typed) is run again on today's data with the same
rules as the site's search (index.html hayOf/suggest), on both sides:
  - our search missed it   = a looser match finds products the site's search doesn't: a bug to fix (health email problem)
  - typo, the site offered = "Did you mean …?" showed a real word
  - store name             = the site offered that store's deals
  - not in their size      = the site has it, just not in the visitor's size (the "show all sizes" button showed)
  - other side only        = only on the USA (or Canada) side; side guessed from the device's time zone
  - not carried            = nothing like it anywhere: what people want that we don't have (stores/brands to add)

  python scraper/search_check.py SITE_DIR [query ...]     (no queries: reads the last 24 h from Supabase)
"""
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

CA_TZ = {"America/Toronto", "America/Montreal", "America/Vancouver", "America/Edmonton", "America/Winnipeg", "America/Halifax",
         "America/Regina", "America/St_Johns", "America/Moncton", "America/Whitehorse", "America/Yellowknife", "America/Iqaluit",
         "America/Glace_Bay", "America/Goose_Bay", "America/Swift_Current", "America/Dawson_Creek", "America/Fort_Nelson",
         "America/Creston", "America/Inuvik", "America/Rankin_Inlet", "America/Cambridge_Bay", "America/Atikokan",
         "America/Nipigon", "America/Thunder_Bay", "America/Rainy_River", "America/Dawson", "America/Blanc-Sablon"}


def fold(s):
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


def sq(s):
    return re.sub(r"v(?=\d)", "", re.sub(r"[^a-z0-9]", "", s))


def hay(d):
    """Same as hayOf() in index.html."""
    t = fold(d["b"] + " " + d["n"])
    w = [x for x in (sq(x) for x in t.split()) if x]
    pairs = [w[i] + x for i, x in enumerate(w[1:]) if re.search(r"\d", x + w[i])]
    return t + " " + " ".join(w) + " " + " ".join(pairs) + (" goretex gtx" if re.search(r"gore-?tex|\bgtx\b", t) else "")


def words(q):
    """Same as the site: plain words lose a "v" before digits ("v15" = "15"), others lose punctuation ("arc'teryx")."""
    return [x for x in (re.sub(r"v(?=\d)", "", w) if re.fullmatch(r"[a-z0-9]+", w) else sq(w) for w in fold(q.strip()).split()) if x]


def lev(a, b):
    if abs(len(a) - len(b)) > 2:
        return 9
    p = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        r = [i]
        for j in range(1, len(b) + 1):
            r.append(min(p[j] + 1, r[j - 1] + 1, p[j - 1] + (a[i - 1] != b[j - 1])))
        p = r
    return p[len(b)]


class Side:
    def __init__(self, items):
        self.items = items
        self.hays = [hay(d) for d in items]
        self.vocab = {}
        for d in items:
            for w in re.split(r"[^a-z0-9+]+", fold(d["b"] + " " + d["n"])):
                if len(w) >= 3 and not w.isdigit():
                    self.vocab[w] = self.vocab.get(w, 0) + 1
        self.squash = [sq(fold(d["b"] + " " + d["n"])) for d in items]

    def hits(self, q):
        return sum(1 for h in self.hays if all(w in h for w in q))

    def suggest(self, q):
        """Same as suggest() + the "longest part that exists" fallback in index.html."""
        changed, out = False, []
        for w in q:
            if any(w in k for k in self.vocab):
                out.append(w)
                continue
            m = re.fullmatch(r"([a-z]{3,})(\d+)", w)
            if m and m.group(1) in self.vocab:
                changed = True
                out.append(m.group(1) + " " + m.group(2))
                continue
            if len(w) < 4:
                out.append(w)
                continue
            best, bd, bn = None, (2 if len(w) >= 7 else 1) + 1, 0
            for k, n in self.vocab.items():
                dd = lev(w, k)
                if dd < bd or (dd == bd and n > bn):
                    best, bd, bn = k, dd, n
            if best:
                changed = True
                out.append(best)
            else:
                out.append(w)
        if changed:
            return " ".join(out)
        for k in range(len(q) - 1, 0, -1):
            if self.hits(q[:k]):
                return " ".join(q[:k])
        return None

    def loose(self, q):
        """A looser match than the site's: the whole query squashed, inside the whole name squashed."""
        s = sq("".join(q))
        return sum(1 for x in self.squash if len(s) >= 4 and s in x)


def store_names(site):
    try:
        html = (Path(site) / "index.html").read_text()
        return [fold(v[0]) for v in json.loads(re.search(r"const STORES=(\{.*?\});", html, re.S).group(1)).values()]
    except Exception:
        return []


def classify(queries, site):
    """queries: [(text, tz)] -> {group: [line, ...]}, [(problem key, message)]"""
    sides = {}
    for side, f in (("ca", "deals.json"), ("us", "deals-us.json")):
        try:
            sides[side] = Side(json.loads((Path(site) / f).read_text())["items"])
        except Exception:
            pass
    stores = store_names(site)
    out, probs, seen = {}, [], set()
    for text, tz in queries:
        q = words(text)
        key = " ".join(q)
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        side = "ca" if tz in CA_TZ else "us" if str(tz or "").startswith("America/") else "ca"
        other = "us" if side == "ca" else "ca"
        here, there = sides.get(side), sides.get(other)
        name = "Canada" if side == "ca" else "USA"
        qs = " ".join(fold(text).split())
        miss = (here.loose(q) - here.hits(q)) if here else 0
        if miss >= 3:              # the site's search finds fewer than a punctuation-blind look (Oct 10: "arcteryx" 5 of 156)
            out.setdefault("bug", []).append(f"{text} (the search finds {here.hits(q)}, {here.loose(q)} products have it)")
            probs.append((f"search:{key[:50]}", f"Search: '{text}' found nothing for a visitor; the site's search finds "
                                                f"{here.hits(q)} products in {name} but {here.loose(q)} have it in their name: "
                                                f"our search is missing them."))
        elif here and here.hits(q):
            out.setdefault("size", []).append(f"{text} ({here.hits(q)} in {name})")
        elif there and there.hits(q):
            out.setdefault("other", []).append(f"{text} (only on the {'USA' if other == 'us' else 'Canada'} side, "
                                               f"{there.hits(q)} products)")
        elif len(qs) >= 4 and any(s.startswith(qs) or s.replace(" ", "").startswith(qs.replace(" ", "")) for s in stores):
            out.setdefault("store", []).append(text)
        elif here and (sg := here.suggest(q)) and here.hits(words(sg)):
            out.setdefault("typo", []).append(f"{text} -> {sg}")
        else:
            out.setdefault("none", []).append(text)
    return out, probs


LABELS = [("bug", "Our search missed it (to fix)"), ("typo", "Typo: the site offered 'Did you mean'"),
          ("store", "A store's name: the site offered its deals"), ("size", "We have it, not in that visitor's size"),
          ("other", "Only on the other side"), ("none", "We don't carry it (ideas for stores/brands)")]


def lines(out, total):
    if not total:
        return ""
    s = f"\nSearches that found nothing (last 24 h): {total}\n"
    for k, label in LABELS:
        if out.get(k):
            s += f"- {label}: " + ", ".join(out[k][:12]) + (f" (+{len(out[k]) - 12} more)" if len(out[k]) > 12 else "") + "\n"
    return s


def recent(hours=24):
    sb, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SECRET_KEY", "")
    if not (sb and key):
        return []
    h = {"apikey": key}
    if key.count(".") == 2:
        h["Authorization"] = f"Bearer {key}"
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    r = requests.get(f"{sb}/rest/v1/ana_events", headers=h, timeout=30,
                     params={"select": "detail,tz", "kind": "eq.search-none", "at": f"gte.{since}", "order": "at.desc",
                             "limit": "500"})
    r.raise_for_status()
    return [(x["detail"] or "", x.get("tz")) for x in r.json() if x.get("detail")]


def run(site):
    """-> (email text, problems). Never raises: a failed check is one line in the email."""
    try:
        qs = recent()
        out, probs = classify(qs, site)
        return lines(out, len({" ".join(words(t)) for t, _ in qs})), probs
    except Exception as e:
        return f"\nSearches that found nothing: couldn't check ({str(e)[:80]})\n", []


if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else "site"
    qs = [(q, "America/Vancouver") for q in sys.argv[2:]] or recent()
    out, probs = classify(qs, site)
    print(lines(out, len(qs)) or "no searches that found nothing")
    for _, m in probs:
        print("PROBLEM:", m)
