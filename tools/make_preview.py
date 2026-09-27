#!/usr/bin/env python3
"""Turn site/index.html into a self-contained, playable preview page (for a claude.ai artifact).

The preview is the real page with: today's deals embedded (no photos), logos inlined, a pretend
server (nothing is saved or emailed), and a test panel to jump between situations.

Usage: python tools/make_preview.py OUT.html
"""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
out = Path(sys.argv[1])

s = (SITE / "index.html").read_text()


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:70], s.count(a))
    s = s.replace(a, b)


# document shell -> artifact body (the host adds doctype/head/body)
s = re.sub(r'<!DOCTYPE html>\s*<html lang="en">\s*<head>\s*', "", s)
s = re.sub(r"<meta[^>]*>\s*", "", s)
s = re.sub(r'<link rel="(icon|preconnect)"[^>]*>\s*', "", s)
s = re.sub(r"<title>.*?</title>", "<title>Gear Fox Preview</title>", s)
rep("</head>\n<body>\n", "")
rep("</body>\n</html>", "")
s = s.replace("--band-muted:#AEB8B2;\n  }\n}", "--band-muted:#AEB8B2; color-scheme:dark;\n  }\n}")
rep(':root[data-theme="dark"]{', ':root[data-theme="dark"]{color-scheme:dark;')

light = base64.b64encode((SITE / "logo-mark.svg").read_bytes()).decode()
dark = base64.b64encode((SITE / "logo-mark-dark.svg").read_bytes()).decode()
rep('<source srcset="logo-mark-dark.svg"', f'<source srcset="data:image/svg+xml;base64,{dark}"')
rep('<img src="logo-mark.svg"', f'<img src="data:image/svg+xml;base64,{light}"')
s = s.replace('href="privacy.html"', 'href="https://thegearfox.com/privacy.html" target="_blank" rel="noopener"')

# test panel
rep('<header class="topbar">', '''<div class="pv"><div class="pvin">
  <div class="pvrow"><b>Preview</b>
    <button type="button" class="pvb" id="pvReset">Start as a new visitor</button>
    <button type="button" class="pvb" id="pvConfirm">Pretend I confirmed my email</button>
    <button type="button" class="pvb" id="pvDay">Pretend a day has passed</button>
  </div>
  <p id="pvMsg">Nothing here is saved or emailed, and product photos don't load in the preview. Everything else is the real page with today's deals.</p>
</div></div>
<header class="topbar">''')
rep("/* top bar */", '''/* preview panel (not part of the site) */
.pv{position:relative;z-index:60;background:var(--band);color:var(--band-ink);padding:10px 16px}
.pvin{max-width:680px;margin:0 auto}
.pvrow{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.pv b{font:700 18px var(--display);letter-spacing:.3px;margin-right:4px}
.pvb{font:600 14px var(--body);color:var(--band-ink);background:transparent;border:1.5px solid var(--band-muted);border-radius:8px;min-height:40px;padding:0 12px;cursor:pointer}
.pvb:hover{border-color:var(--hivis)}
.pv p{margin:6px 0 0;font-size:13px;color:var(--band-muted)}
.sheet .panel{max-height:calc(100vh - 150px)!important}
/* top bar */''')

# embedded data, pretend server
data = json.loads((SITE / "deals.json").read_text())


def on_sale(x):
    return any(len(z) > 3 and z[1] < z[3] * 0.99 for z in x["sz"])


items = [{k: v for k, v in x.items() if k != "img"} for x in data["items"] if x.get("ca") is not False or on_sale(x)]
blob = json.dumps({"updated": data["updated"], "items": items}, separators=(",", ":")).replace("</", "<\\/")
rep('fetch("deals.json",{cache:"no-store"}).then(r=>r.json()).then(',
    'Promise.resolve(JSON.parse(document.getElementById("gfdata").textContent)).then(')
a = s.index("async function rpc(fn,args){")
b = s.index("\n}\n", a) + 3
s = s[:a] + '''async function rpc(fn,args){   // preview: pretend server, nothing leaves the page
  await new Promise(r=>setTimeout(r,300));
  return {subscribe:"sent",save_profile:true,unsubscribe:true,watch_add:true,watch_remove:true,watch_list:[]}[fn]??null;
}
''' + s[b:]

rep("/* ---------- start ---------- */", '''/* ---------- preview panel ---------- */
function pvMsg(t){$("pvMsg").textContent=t}
function pvClear(){["rd-profile","gf-sub","gf-watch","gf-last","gf-base","gf-clicks"].forEach(k=>LS.set(k,null))}
$("pvReset").addEventListener("click",()=>{pvClear();location.reload()});
$("pvConfirm").addEventListener("click",()=>{
  if(gated()){pvMsg("Sign up first (sizes and an email), then tap this.");return}
  setSub({key:"00000000-0000-0000-0000-000000000000",email:state.email||"you@example.com",active:true});
  $("notice").classList.add("hidden");renderAll();pvMsg("You're now a confirmed subscriber. Hearts say you'll get alerts, and the sign-up card is gone.")});
$("pvDay").addEventListener("click",()=>{
  if(gated()){pvMsg("Sign up first (sizes and an email), then tap this.");return}
  const sale=matchItems(toProfile()).filter(d=>d.pct>0).sort((a,b)=>b.pct-a.pct);
  const keys=sale.map(itemKey);
  LS.set("gf-last",{at:Date.now()-26*3600e3,keys:keys.filter((_,i)=>i%8!==3)});LS.set("gf-base",null);
  if(!Object.keys(watches).length)sale.slice(0,3).forEach(d=>{const k=itemKey(d);watches[k]={b:d.b,n:d.n,g:d.g,url:d.url,price:d.best,low:d.best,seen:d.best,gone:false,saved:new Date(Date.now()-3*86400e3).toISOString()}});
  Object.entries(watches).forEach(([k,w],i)=>{
    if(i===1){w.gone=true;return}
    if(w.price!=null){const up=Math.round(w.price*1.18);w.price=up;w.seen=up;w.low=up}});
  LS.set("gf-watch",watches);
  const d=sale[0];if(d&&!Object.keys(clicks).length){clicks[itemKey(d)]=Math.round((d.reg-d.best)*100)/100;LS.set("gf-clicks",clicks)}
  location.reload();
});

/* ---------- start ---------- */''')
s = s.rstrip() + '\n<script type="application/json" id="gfdata">' + blob + "</script>\n"
m = s.index("<script>\n(function(){")
e = s.index("</script>", m) + len("</script>")
s = s[:m] + s[e:] + s[m:e] + "\n"
out.write_text(s)
print(f"wrote {out} ({len(s)//1024} KB, {len(items)} products)")
