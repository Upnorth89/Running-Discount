#!/usr/bin/env python3
"""Run before every push to main: rebuilds what the morning update builds, from today's live data, in a scratch
folder, and stops at the first thing that crashes or comes out empty. Nothing ships unless this says ALL GOOD.

  python tools/check.py            (about 3 minutes; needs internet for today's live offers.json)

Checks: every Python file compiles · every script in the site pages parses (node --check) · deals merge from today's
offers · shoe pages, list pages, Black Friday and sitemap get built (350+ models) · the Friday email matches and draws
cards for a sample runner · the preview builds · the site test clicks through it like a visitor
(tools/sitetest.py; set CHROMIUM=/path/to/chromium if Playwright's own browser isn't installed). Added Oct 4, 2026 after the shoe pages broke silently for 3 hours.
"""
import json
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = "https://thegearfox.com/"
fails = []


def step(name, fn):
    try:
        note = fn()
        print(f"  ok   {name}" + (f" ({note})" if note else ""))
    except Exception as e:
        fails.append(name)
        print(f"  FAIL {name}: {e}")


def compile_all():
    files = list((ROOT / "scraper").glob("*.py")) + list((ROOT / "tools").glob("*.py"))
    for f in files:
        py_compile.compile(str(f), doraise=True)
    return f"{len(files)} files"


def scripts_parse():
    n = 0
    with tempfile.TemporaryDirectory() as t:
        for page in ["index.html", "about.html", "privacy.html", "stats.html", "grab.html"]:
            p = ROOT / "site" / page
            if not p.exists():
                continue
            for i, (attrs, js) in enumerate(re.findall(r"<script([^>]*)>(.*?)</script>", p.read_text(), re.S)):
                if not js.strip() or "src=" in attrs or "json" in attrs:
                    continue
                f = Path(t) / f"{page}.{i}.js"
                f.write_text(js)
                r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
                if r.returncode:
                    raise RuntimeError(f"{page} script {i}: {r.stderr.strip().splitlines()[-1]}")
                n += 1
        for js in (ROOT / "site").glob("*.js"):
            r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(f"{js.name}: {r.stderr.strip().splitlines()[-1]}")
            n += 1
    return f"{n} scripts"


def main():
    work = Path(tempfile.mkdtemp(prefix="gf-check-"))
    site = work / "site"
    shutil.copytree(ROOT / "site", site, ignore=shutil.ignore_patterns("deals.json", "sale.json", "offers.json"))
    print("Checking against today's live data…")
    step("Python files compile", compile_all)
    step("Site scripts parse", scripts_parse)

    def ana_kinds():   # Oct 8: events the database didn't list were dropped silently for days (store bar, Canadian filter)
        sql = (ROOT / "supabase" / "analytics.sql").read_text()
        allowed = set(re.findall(r"'([a-z-]+)'", sql[sql.index("ana_kinds()"):sql.index("$$;", sql.index("ana_kinds()"))]))
        sent = set()
        for f in [ROOT / "site" / "index.html", ROOT / "scraper" / "shoe_pages.py"]:
            t = f.read_text()
            sent |= set(re.findall(r'\bana\("([a-z-]+)"', t))
            if f.name == "index.html":
                sent |= set(re.findall(r'\btrack\("([a-z-]+)"', t)) - {"ref-visit"}
        missing = sorted(sent - allowed)
        if missing:
            raise RuntimeError(f"the site sends events the database drops: {', '.join(missing)} (add them to ana_kinds in supabase/analytics.sql "
                               "and have Bastien run it)")
        return f"{len(sent)} kinds, all accepted"
    step("Analytics events are all recorded", ana_kinds)

    def fetch():
        for f in ("offers.json", "deals.json"):
            urllib.request.urlretrieve(LIVE + f, site / f)
        return "offers.json + deals.json"
    step("Download today's live data", fetch)

    def merge():
        r = subprocess.run([sys.executable, str(ROOT / "scraper" / "scrape.py"), str(site / "deals.json"), "--remerge"],
                           capture_output=True, text=True, timeout=900)
        if r.returncode:
            raise RuntimeError(r.stderr.strip().splitlines()[-1])
        n = len(json.loads((site / "deals.json").read_text())["items"])
        if n < 5000:
            raise RuntimeError(f"only {n} items")
        return f"{n} items"
    step("Deals merge", merge)

    def pages():
        r = subprocess.run([sys.executable, str(ROOT / "scraper" / "shoe_pages.py"), str(site)],
                           capture_output=True, text=True, timeout=1200)
        if r.returncode:
            raise RuntimeError(r.stderr.strip().splitlines()[-1])
        n = len(list((site / "shoes").glob("*/index.html")))
        for must in ["sitemap.xml", "black-friday/index.html", "vendredi-fou/index.html", "running-shoes-sale/index.html",
                     "chaussures/index.html", "shoes/index.html"]:
            if not (site / must).exists():
                raise RuntimeError(f"{must} missing")
        if n < 300:
            raise RuntimeError(f"only {n} shoe pages")
        return f"{n} shoe pages"
    step("Shoe pages, list pages, sitemap", pages)

    def same_names():   # the site links cards to shoe pages with a JS copy of base_model + slugify: they must agree (Oct 7)
        sys.path.insert(0, str(ROOT / "scraper"))
        import shoe_pages as SP
        names = [[d["b"], d["n"]] for f in ("deals.json", "deals-us.json") if (site / f).exists()
                 for d in json.loads((site / f).read_text())["items"] if d["g"] == "shoes"]
        html = (ROOT / "site" / "index.html").read_text()
        js = re.search(r"function baseModel\(n\)\{.*?\n\}", html, re.S).group(0) + "\n" + \
            re.search(r"function slugify\(t\)\{.*?\}\n", html, re.S).group(0)
        (work / "n.json").write_text(json.dumps(names))
        (work / "t.js").write_text(js + f"\nconsole.log(JSON.stringify(require({json.dumps(str(work / 'n.json'))}).map(([b,n])=>slugify(b+' '+baseModel(n)))));")
        got = json.loads(subprocess.run(["node", str(work / "t.js")], capture_output=True, text=True).stdout)
        diff = [n for n, g in zip(names, got) if SP.slugify(f"{n[0]} {SP.base_model(n[1])}") != g]
        if diff:
            raise RuntimeError(f"{len(diff)} shoes get a different page address on the site (e.g. {diff[0]})")
        return f"{len(names)} shoes"
    step("Shoe page links match (site vs pages)", same_names)

    def email():
        sys.path.insert(0, str(ROOT / "scraper"))
        import weekly_email as W
        items = json.loads((site / "deals.json").read_text())["items"]
        prof = {"lang": "en", "gender": "men", "terrain": "both", "ships": "ca", "groups": ["shoes", "tops", "bottoms"],
                "sizes": {"shoes": {"sizes": ["11"], "width": []}, "tops": {"sizes": ["M"]}, "bottoms": {"sizes": ["M"]}}}
        got = [d for d in W.match(items, prof) if d["pct"] > 0]
        if len(got) < 50:
            raise RuntimeError(f"only {len(got)} deals for a size-11 runner")
        html = "".join(W.card(d, lang) for d in got[:8] for lang in ("en", "fr"))
        if len(html) < 2000:
            raise RuntimeError("cards came out empty")
        return f"{len(got)} deals for a size-11 runner"
    step("Friday email matching + cards", email)

    def preview():
        dst = ROOT / "site" / "deals.json"
        had = dst.exists()
        if not had:
            shutil.copy(site / "deals.json", dst)
        try:
            r = subprocess.run([sys.executable, str(ROOT / "tools" / "make_preview.py"), str(work / "preview.html")],
                               capture_output=True, text=True, timeout=600)
        finally:
            if not had:
                dst.unlink()
        if r.returncode:
            raise RuntimeError(r.stderr.strip().splitlines()[-1])
        return r.stdout.strip().splitlines()[-1][:80]
    step("Preview builds", preview)

    def sitetest():
        out = work / "sitetest.json"
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "sitetest.py"), str(site), str(out)],
                           capture_output=True, text=True, timeout=900)
        if not out.exists():
            raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1])
        st = json.loads(out.read_text())
        bad = [f"{c['name']}: {c['why']}" for c in st["checks"] if not c["ok"]]
        if bad:
            raise RuntimeError("; ".join(bad[:3]) + (f" (+{len(bad) - 3} more)" if len(bad) > 3 else ""))
        return f"{st['passed']} checks, clicked through like a visitor"
    step("Site test (tools/sitetest.py)", sitetest)

    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(ROOT / "scraper" / "__pycache__", ignore_errors=True)
    if fails:
        print(f"\nNOT READY: {len(fails)} problem(s): {', '.join(fails)}. Don't push.")
        sys.exit(1)
    print("\nALL GOOD: safe to push.")


if __name__ == "__main__":
    main()
