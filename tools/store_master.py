#!/usr/bin/env python3
"""Store master list page (Oct 8, 2026; Bastien: "I need a master list pinned for companies we have or haven't checked
and the reason we can't get the items"). Builds one HTML page from the code (every store we read) and STORES.md
("Master list" table: every company we can't read, why, what would unlock it). Published as the pinned
"Gear Fox Store List" artifact; rebuild and republish after adding or checking a store.

  python tools/store_master.py OUT.html
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))
sys.argv = [sys.argv[0], "/dev/null", "--remerge"] + sys.argv[1:]
import scrape  # noqa: E402
import runfree as RF  # noqa: E402

E = html.escape
out = Path(sys.argv[3] if len(sys.argv) > 3 else "store-list.html")

names = json.loads(re.search(r"const STORES=(\{.*?\});", (ROOT / "site" / "index.html").read_text(), re.S).group(1))
host = lambda u: re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
KIND = {"food": "Nutrition brand", "socks": "Sock brand", "eyewear": "Sunglasses brand", "gear": ""}
CUSTOM = {"altitude": ("Altitude Sports", "altitude-sports.com"), "lasthunt": ("The Last Hunt", "thelasthunt.com"),
          "thefeed": ("The Feed", "thefeed.com"), "sea2sky": ("Sea2Sky Nutrition", "sea2skynutrition.ca"),
          "sportinglife": ("Sporting Life", "sportinglife.ca"), "stampeak": ("Stampeak", "stampeak.com"),
          "mec": ("MEC (your saved pages)", "mec.ca"), "rei": ("REI (your saved pages)", "rei.com"),
          "decathlon": ("Decathlon (night read)", "decathlon.ca"), "footlocker": ("Foot Locker", "footlocker.ca")}

rows = []   # (side, name, domain, how)
for st, base, kind in scrape.SHOPIFY_STORES:
    d = host(base)
    nm = (names.get(d) or [st])[0]
    abroad = (names.get(d) or [None, None])[1:2]
    side = "USA" if st in scrape.US_SHOPS else "Canada" if not abroad or abroad[0] is None else f"Canada (ships from {abroad[0]})"
    rows.append((side, nm, d, KIND.get(kind, "") or "Shopify"))
for st, (nm, d) in CUSTOM.items():
    if st in scrape.STORES:
        rows.append(("USA" if st in scrape.US_SHOPS else "Canada", nm, d, "Own reader"))
for st, base, nm, state in RF.RUNFREE_STORES:
    rows.append(("Canada" if st in RF.CANADIAN else "USA", f"{nm} ({state})", host(base), "RunFree (night read)"))
rows.sort(key=lambda r: (0 if r[0] == "Canada" else 1 if r[0].startswith("Canada") else 2, r[1].lower()))

# the "can't read" table from STORES.md
md = (ROOT / "STORES.md").read_text()
sec = md.split("## Master list", 1)[1].split("\n## ", 1)[0]
blocked, group = [], ""
for line in sec.splitlines():
    if not line.startswith("|") or line.startswith("|---") or line.startswith("| Company"):
        continue
    cells = [c.strip() for c in line.strip("|").split("|")]
    if cells[0].startswith("**") and not any(cells[1:]):
        group = cells[0].strip("*")
        continue
    blocked.append((group, *cells[:5]))

md_b = lambda s: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", E(s))
n_ca = sum(1 for r in rows if r[0].startswith("Canada"))
n_us = len(rows) - n_ca

read_html = "".join(
    f'<tr data-q="{E((r[1] + " " + r[2]).lower())}"><td>{E(r[1])}</td><td class="dom">{E(r[2])}</td>'
    f'<td><span class="pill {"us" if r[0] == "USA" else "ca"}">{E(r[0])}</span></td><td class="how">{E(r[3])}</td></tr>'
    for r in rows)
groups = []
for g in dict.fromkeys(b[0] for b in blocked):
    items = [b for b in blocked if b[0] == g]
    tag = {"Blocked (the store says no)": "no", "No online catalogue we can read": "none",
           "Readable, needs its own reader (not built yet)": "build", "No answer from my machine or GitHub": "retry",
           "Readable, waiting on purpose": "wait", "Checked and skipped (not a fit)": "skip"}.get(g, "none")
    groups.append(f'<h3><span class="dot {tag}"></span>{E(g)} <small>{len(items)}</small></h3><div class="scroll"><table>'
                  '<thead><tr><th>Company</th><th>Where</th><th>Why not</th><th>Tried</th><th>What would unlock it</th></tr></thead><tbody>'
                  + "".join(f'<tr data-q="{E((b[1] + " " + b[3]).lower())}"><td><b>{md_b(b[1])}</b></td><td>{md_b(b[2])}</td>'
                            f'<td>{md_b(b[3])}</td><td>{md_b(b[4])}</td><td>{md_b(b[5])}</td></tr>' for b in items)
                  + "</tbody></table></div>")

page = f"""<title>Gear Fox Store List</title>
<style>
/* layout: one column, a search bar, then two plain tables; colours from The Gear Fox (forest green ink, fox orange) */
:root{{--bg:#F6F7F4;--card:#FFFFFF;--ink:#17201C;--muted:#5C6660;--line:#DDE2DC;--accent:#D9661F;--ca:#1F6B45;--us:#2B5B8A;
  --no:#B3261E;--wait:#B7791F;--build:#2B5B8A;--skip:#7A837D;--display:"Bricolage Grotesque",system-ui,sans-serif;--body:"Atkinson Hyperlegible",system-ui,sans-serif}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#121815;--card:#1A221E;--ink:#E7ECE8;--muted:#9AA59E;--line:#2C3631;
  --accent:#F08A45;--ca:#5CC08A;--us:#7FAEDB;--no:#F2857C;--wait:#E8B45A;--build:#7FAEDB;--skip:#9AA59E;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#121815;--card:#1A221E;--ink:#E7ECE8;--muted:#9AA59E;--line:#2C3631;--accent:#F08A45;--ca:#5CC08A;--us:#7FAEDB;
  --no:#F2857C;--wait:#E8B45A;--build:#7FAEDB;--skip:#9AA59E;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 var(--body);padding-inline:16px;padding-block:24px 48px}}
main{{max-width:1100px;margin:0 auto;display:grid;gap:28px}}
h1{{font:700 clamp(26px,4vw,36px)/1.1 var(--display);margin:0;text-wrap:balance}}
h2{{font:700 22px/1.2 var(--display);margin:0 0 10px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}}
h2 small,h3 small{{font:600 13px var(--body);color:var(--muted)}}
h3{{font:700 16px var(--display);margin:22px 0 8px;display:flex;gap:8px;align-items:center}}
.sub{{color:var(--muted);margin:6px 0 0;max-width:68ch}}
.stats{{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-variant-numeric:tabular-nums}}
.stats b{{color:var(--ink);font-size:18px}}
input{{width:100%;box-sizing:border-box;font:inherit;padding:11px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink)}}
input:focus-visible{{outline:2px solid var(--accent);outline-offset:1px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;min-width:0}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:14px;min-width:640px}}
th{{text-align:left;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:6px 10px;border-bottom:1px solid var(--line)}}
td{{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:last-child td{{border-bottom:0}}
.dom,.how{{color:var(--muted)}}
.pill{{display:inline-block;font-size:12px;font-weight:700;padding:1px 8px;border-radius:99px;border:1px solid currentColor;white-space:nowrap}}
.pill.ca{{color:var(--ca)}}.pill.us{{color:var(--us)}}
.dot{{width:10px;height:10px;border-radius:50%;background:var(--skip);flex:none}}
.dot.no{{background:var(--no)}}.dot.wait{{background:var(--wait)}}.dot.build{{background:var(--build)}}.dot.retry{{background:var(--accent)}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--muted);font-size:13px}}.legend span{{display:flex;gap:6px;align-items:center}}
.none{{color:var(--muted);display:none}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Bricolage+Grotesque:wght@700&display=swap">
<main>
<header><h1>Gear Fox Store List</h1>
<p class="sub">Every store and brand we read every day, and every one we checked and can't read yet, with the reason and what would change that. Updated {date.today():%B %-d, %Y}.</p></header>
<div class="stats"><span><b>{len(rows)}</b> stores and brands read</span><span><b>{n_ca}</b> Canada side</span><span><b>{n_us}</b> USA side</span><span><b>{len(blocked)}</b> checked, not read</span></div>
<label for="q" class="sub" style="margin:0">Search a store or brand</label>
<input id="q" type="search" placeholder="e.g. Injinji, Sport Chek, Darn Tough" autocomplete="off">
<p id="nores" class="none">Not on either list yet: we haven't checked it. Ask Claude to check it.</p>
<section id="no"><h2>Can't read yet <small>{len(blocked)} companies</small></h2>
<div class="legend"><span><i class="dot no"></i>blocked by the store</span><span><i class="dot build"></i>readable, needs its own reader</span><span><i class="dot wait"></i>readable, waiting on purpose</span><span><i class="dot retry"></i>no answer, retry</span><span><i class="dot"></i>no catalogue / not a fit</span></div>
{''.join(groups)}</section>
<section id="yes"><h2>Read every day <small>{len(rows)} stores and brands</small></h2>
<div class="scroll"><table><thead><tr><th>Store or brand</th><th>Website</th><th>Side</th><th>How we read it</th></tr></thead><tbody>{read_html}</tbody></table></div></section>
</main>
<script>
const q=document.getElementById("q"),rows=[...document.querySelectorAll("tr[data-q]")],nores=document.getElementById("nores");
q.addEventListener("input",()=>{{const v=q.value.trim().toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"");let n=0;
  for(const r of rows){{const hit=!v||r.dataset.q.normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").includes(v);r.hidden=!hit;n+=hit}}
  nores.style.display=v&&!n?"block":"none"}});
</script>
"""
out.write_text(page)
print(f"wrote {out}: {len(rows)} read, {len(blocked)} not read")
