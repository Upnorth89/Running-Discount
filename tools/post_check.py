"""Every line of a post, checked on its live shoe page before Bastien sees it (Oct 28; Bastien: "The novablast % discount is off ...
I need you to double check your work before I push stuff").

A line "[Name (men's)](shoe page link): $X (was $Y, −Z%)[ at Store]" passes when: Z is what $X and $Y work out to, the shoe page has a row at
exactly $X with regular $Y, and 5+ sizes of that cut cost $X or less there today (at that store, when the line names one). Lines linking elsewhere (?q= searches) are skipped.

  python tools/post_check.py post.md        -> prints OK/BAD per line, exits 1 if any line is BAD
  from post_check import check; bad = check(markdown_text)   (list of the BAD lines' names)
"""
import html
import re
import sys
import urllib.request

SHORT = re.compile(r"^- \[([^\]]+)\]\((https://thegearfox\.com/(?:us/)?shoes/[^)]+)\) \$([\d.,]+), (\d+)% off", re.M)  # Nov 5 format
LINE = re.compile(r"\[([^\]]+)\]\((https://thegearfox\.com/(?:us/)?shoes/[^)]+)\): \$([\d.,]+) \(was \$([\d.,]+), −(\d+)%\)(?: at ([^\n]+))?")
ROW = re.compile(r"(\d+(?:\.5)?(?: \(wide\))?|[MW] \d+(?:\.5)?) \$([\d,]+\.\d\d) \$([\d,]+\.\d\d) −(\d+)%")


def rows(page_html):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page_html, flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    parts = re.split(r"(Men's|Women's|Unisex[^♡]*) ♡ Watch the price Size Price Store", t)
    out = []
    for i in range(1, len(parts), 2):
        for r in ROW.finditer(parts[i + 1]):
            out.append((parts[i], r.group(1), float(r.group(2).replace(",", "")), float(r.group(3).replace(",", "")),
                        parts[i + 1][r.end():r.end() + 60].strip()))      # the text after the row = its store
    return out


COMMON = {"men": {x / 2 for x in range(16, 24)}, "women": {x / 2 for x in range(13, 19)}}


def page_common(rel, p, sex):
    """Common sizes (men's 8-11.5, women's 6.5-9) at $p or less on the shoe page, as labels."""
    out = set()
    for cut, size, price, _, _ in rel:
        m = re.fullmatch(r"(?:([MW]) )?(\d+(?:\.5)?)", size)
        if not m or price > p + 0.01:
            continue
        c = {"M": "men", "W": "women"}.get(m.group(1)) or ("women" if cut.startswith("Women") else "men")
        if float(m.group(2)) in COMMON[c]:
            out.add((c, float(m.group(2))))
    return [f"{'W ' if c == 'women' and sex != 'women' else ''}{v:g}" for c, v in sorted(out)]


def check(md, log=print, common=None):
    """common: {line name: live common sizes} from reddit_post (opened on the store's pages); else read from the shoe page."""
    bad = []
    lines = [(m.group(1), m.group(2), m.group(3), None, m.group(4), None) for m in SHORT.finditer(md)] + \
            [m.groups() for m in LINE.finditer(md)]
    for name, url, p, w, pc, store in lines:
        p = float(p.replace(",", ""))
        w = float(w.replace(",", "")) if w else None
        sex = "women" if re.search(r"\(women's\)|\(W\)", name) else "men" if re.search(r"\(men's\)|\(M\)", name) else None
        try:
            page = urllib.request.urlopen(url.split("?")[0] + "?check=post", timeout=30).read().decode()
        except Exception as e:
            log(f"BAD {name}: shoe page didn't open ({e})")
            bad.append(name)
            continue
        rel = [r for r in rows(page) if not sex or r[0].lower().startswith(sex) or r[0].startswith("Unisex")]
        if store:      # Oct 31: a line naming a store ("at BlackToe Running") must be that store's own price and sizes
            rel = [r for r in rel if r[4].startswith(store.strip())]
        n = len({(r[0], r[1]) for r in rel if r[2] <= p + 0.01 and "wide" not in r[1]})
        if w is None:      # short line: the % must match a row at this price ("was" stays in this check's output only)
            hit = [r for r in rel if abs(r[2] - p) < 0.01 and round(100 * (1 - p / r[3])) == int(pc)]
            w = hit[0][3] if hit else max((r[3] for r in rel if abs(r[2] - p) < 0.01), default=p)
            exact = bool(hit)
            why = [] if exact else [f"no size at ${p:g} that is {pc}% off on the page"]
        else:
            exact = any(abs(r[2] - p) < 0.01 and abs(r[3] - w) < 0.6 for r in rel)
            why = [] if round(100 * (1 - p / w)) == int(pc) else [f"${p:g} off ${w:g} is −{round(100 * (1 - p / w))}%, not −{pc}%"]
            if not exact:
                why.append(f"no size at ${p:g} (was ${w:g}) on the page")
        if n < 5:
            why.append(f"only {n} sizes at ${p:g} or less")
        com = (common or {}).get(name)
        if com is None:
            com = page_common(rel, p, sex)
        if len(com) < 3:
            why.append(f"only {len(com)} common sizes")
        log(("OK  " if not why else "BAD ") + f"{name}: ${p:g} (was ${w:g}, −{pc}%)"
            + (f" | {'; '.join(why)}" if why else f" | {n} sizes") + f" | common: {', '.join(com) or 'none'}")
        if why:
            bad.append(name)
    return bad


if __name__ == "__main__":
    b = check(open(sys.argv[1]).read())
    print(f"{'ALL LINES MATCH' if not b else f'{len(b)} LINE(S) WRONG: ' + ', '.join(b)}")
    sys.exit(1 if b else 0)
