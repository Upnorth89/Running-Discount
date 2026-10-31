"""Every line of a post, checked on its live shoe page before Bastien sees it (Oct 28; Bastien: "The novablast % discount is off ...
I need you to double check your work before I push stuff").

A line "[Name (men's)](shoe page link): $X (was $Y, −Z%)" passes when: Z is what $X and $Y work out to, the shoe page has a row at
exactly $X with regular $Y, and 5+ sizes of that cut cost $X or less there today. Lines linking elsewhere (?q= searches) are skipped.

  python tools/post_check.py post.md        -> prints OK/BAD per line, exits 1 if any line is BAD
  from post_check import check; bad = check(markdown_text)   (list of the BAD lines' names)
"""
import html
import re
import sys
import urllib.request

LINE = re.compile(r"\[([^\]]+)\]\((https://thegearfox\.com/(?:us/)?shoes/[^)]+)\): \$([\d.,]+) \(was \$([\d.,]+), −(\d+)%\)")
ROW = re.compile(r"(\d+(?:\.5)?(?: \(wide\))?|[MW] \d+(?:\.5)?) \$([\d,]+\.\d\d) \$([\d,]+\.\d\d) −(\d+)%")


def rows(page_html):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page_html, flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    parts = re.split(r"(Men's|Women's|Unisex[^♡]*) ♡ Watch the price Size Price Store", t)
    out = []
    for i in range(1, len(parts), 2):
        for r in ROW.finditer(parts[i + 1]):
            out.append((parts[i], r.group(1), float(r.group(2).replace(",", "")), float(r.group(3).replace(",", ""))))
    return out


def check(md, log=print):
    bad = []
    for m in LINE.finditer(md):
        name, url, p, w, pc = m.groups()
        p, w = float(p.replace(",", "")), float(w.replace(",", ""))
        sex = "women" if "(women's)" in name else "men" if "(men's)" in name else None
        try:
            page = urllib.request.urlopen(url.split("?")[0] + "?check=post", timeout=30).read().decode()
        except Exception as e:
            log(f"BAD {name}: shoe page didn't open ({e})")
            bad.append(name)
            continue
        rel = [r for r in rows(page) if not sex or r[0].lower().startswith(sex) or r[0].startswith("Unisex")]
        n = len({(r[0], r[1]) for r in rel if r[2] <= p + 0.01 and "wide" not in r[1]})
        exact = any(abs(r[2] - p) < 0.01 and abs(r[3] - w) < 0.6 for r in rel)
        why = [] if round(100 * (1 - p / w)) == int(pc) else [f"${p:g} off ${w:g} is −{round(100 * (1 - p / w))}%, not −{pc}%"]
        if not exact:
            why.append(f"no size at ${p:g} (was ${w:g}) on the page")
        if n < 5:
            why.append(f"only {n} sizes at ${p:g} or less")
        log(("OK  " if not why else "BAD ") + f"{name}: ${p:g} (was ${w:g}, −{pc}%)" + (f" | {'; '.join(why)}" if why else f" | {n} sizes"))
        if why:
            bad.append(name)
    return bad


if __name__ == "__main__":
    b = check(open(sys.argv[1]).read())
    print(f"{'ALL LINES MATCH' if not b else f'{len(b)} LINE(S) WRONG: ' + ', '.join(b)}")
    sys.exit(1 if b else 0)
