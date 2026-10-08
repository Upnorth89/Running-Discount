#!/usr/bin/env python3
"""Turn site/index.html into a self-contained, playable preview page (for a claude.ai artifact).

The preview is the real page with: today's deals embedded (no photos), logos inlined, a pretend
server (nothing is saved or emailed), and a test panel to jump between situations.

Usage: python tools/make_preview.py OUT.html [--new "SELECTOR::What changed::How to see it" ...]

--new (Oct 9, Bastien: "when you do previews can you highlight a change so it sticks out"): every element matching the CSS
selector gets a bright dashed outline, and the panel lists the change with a "Show me" button (scrolls to it, or says how to
get there). Always pass one --new per visible change.
"""
import base64
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
out = Path(sys.argv[1])
NEW = []                                          # (selector, what changed, how to see it)
for k, a in enumerate(sys.argv):
    if a == "--new" and k + 1 < len(sys.argv):
        sel, what, how = (sys.argv[k + 1].split("::") + ["", ""])[:3]
        NEW.append((sel.strip(), what.strip(), how.strip()))

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
    <span class="pvseg" id="pvFlow" role="group" aria-label="First-visit version"><button type="button" data-f="A">A</button><button type="button" data-f="B">B</button><button type="button" data-f="C">C</button><button type="button" data-f="D">D</button></span>
    <span class="pvseg" id="pvCards" role="group" aria-label="Deal cards on phones"><button type="button" data-c="compact">Cards: compact</button><button type="button" data-c="big">Cards: before</button></span>
    <button type="button" class="pvb" id="pvReset">Start as a new visitor</button>
    <button type="button" class="pvb" id="pvConfirm">Pretend I confirmed my email</button>
    <button type="button" class="pvb" id="pvDay">Pretend a day has passed</button>
  </div>
  <p id="pvMsg">A, B, C and D are the four first-visit versions: pick one to start over as a new visitor. Nothing here is saved or emailed, and product photos don't load in the preview. Everything else is the real page with today's deals.</p>
</div></div>
<header class="topbar">''')
rep("/* top bar */", '''/* preview panel (not part of the site) */
.pv{position:relative;z-index:60;background:var(--band);color:var(--band-ink);padding:10px 16px}
.pvin{max-width:680px;margin:0 auto}
.pvrow{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.pv b{font:700 18px var(--display);letter-spacing:.3px;margin-right:4px}
.pvb{font:600 14px var(--body);color:var(--band-ink);background:transparent;border:1.5px solid var(--band-muted);border-radius:8px;min-height:40px;padding:0 12px;cursor:pointer}
.pvb:hover{border-color:var(--hivis)}
.pvseg{display:inline-flex;gap:3px;background:rgba(255,255,255,.12);border-radius:9px;padding:3px}
.pvseg button{font:700 15px var(--body);color:var(--band-ink);background:transparent;border:0;border-radius:7px;min-width:40px;min-height:36px;cursor:pointer}
.pvseg button[aria-pressed="true"]{background:var(--hivis);color:#17201C}
.pv p{margin:6px 0 0;font-size:13px;color:var(--band-muted)}
.sheet .panel{max-height:calc(100vh - 300px)!important}
.pvg{width:100%;max-width:400px;min-height:44px;border:1.5px solid #DADCE0;border-radius:999px;background:#fff;color:#1F1F1F;font:500 15px Arial,sans-serif;cursor:pointer}
.pvg small{color:#777;font-weight:400}
/* top bar */''')

# what changed in this preview: outlined on the page + listed in the panel with "Show me"
new_js = json.dumps([[sel, w, h] for sel, w, h in NEW])
if NEW:
    import html as _h
    rows = "".join(f'<li><span class="pvnum">{n + 1}</span><span><b>{_h.escape(w)}</b>'
                   + (f'<small>{_h.escape(h)}</small>' if h else "")
                   + f'</span><button type="button" class="pvb pvshow" data-n="{n}">Show me</button></li>'
                   for n, (_, w, h) in enumerate(NEW))
    rep('<p id="pvMsg">', '<div class="pvnew"><div class="pvrow"><b class="pvnewh">What\'s new in this preview</b>'
        '<button type="button" class="pvb" id="pvHl" aria-pressed="true">Highlights on</button></div>'
        f'<ol>{rows}</ol></div>\n  <p id="pvMsg">')
    sels = ",".join(f"body.pvhl {sel}" for sel, _, _ in NEW)
    rep("/* top bar */", "/* preview: changed parts */\n" + sels + "{outline:3px dashed #FF5A1F!important;outline-offset:3px;"
        "box-shadow:0 0 0 6px rgba(255,90,31,.18)!important;border-radius:6px}\n"
        ".pvflash{animation:pvflash 1.6s ease 2}@keyframes pvflash{50%{box-shadow:0 0 0 14px rgba(255,90,31,.45)}}\n"
        ".pvnew{margin-top:8px;padding:8px 10px;border:1.5px solid #FF5A1F;border-radius:10px;background:rgba(255,90,31,.10)}\n"
        ".pvnew .pvnewh{font-size:15px;color:#FF8A5B}.pvnew ol{list-style:none;margin:6px 0 0;padding:0;display:grid;gap:6px}\n"
        ".pvnew li{display:flex;gap:10px;align-items:center}.pvnew li>span:nth-child(2){flex:1;display:grid;font-size:14px}\n"
        ".pvnew small{color:var(--band-muted);font-size:12.5px}.pvnum{flex:none;width:24px;height:24px;border-radius:50%;"
        "background:#FF5A1F;color:#17201C;font:700 13px/24px var(--body);text-align:center}\n/* top bar */")

# embedded data, pretend server
data = json.loads((SITE / "deals.json").read_text())


def on_sale(x):
    return any(len(z) > 3 and z[1] < z[3] * 0.99 for z in x["sz"])


def pretend_history(xs):
    """FAKE_HISTORY=1 (Oct 6, 2026): before 30 real days exist, show how "Lowest price in N days" badges look:
    about 1 deal in 6 (fixed by its name) gets 41 days of history with today's price as the lowest."""
    if os.environ.get("FAKE_HISTORY") != "1":
        return xs
    import zlib
    for x in xs:
        if on_sale(x) and zlib.crc32(f"{x['b']}|{x['n']}".encode()) % 6 == 0:
            x["hd"], x["lo"] = 41, min(z[1] for z in x["sz"])
            x["hi"] = round(x["lo"] * 1.2, 2)
    return xs


items = pretend_history([{k: v for k, v in x.items() if k != "img"} for x in data["items"] if x.get("ca") is not False or on_sale(x)])
blob = json.dumps({"updated": data["updated"], "stores": data.get("stores", {}), "n_stores": data.get("n_stores"), "fx": data.get("fx", {}), "items": items}, separators=(",", ":")).replace("</", "<\\/")
# shoe price pages list (links on shoe cards and in search): embedded too, when the site folder has one
sp_path = SITE / "shoes" / "pages.json"
if sp_path.exists():
    rep('fetch("shoes/pages.json").then(r=>r.ok?r.json():{})', 'Promise.resolve(' + sp_path.read_text().replace("</", "<\\/") + ')')
rep('const loadData=f=>fetch(f,{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error(f);return r.json()});',
    'const loadData=f=>Promise.resolve(JSON.parse(document.getElementById(/-us/.test(f)&&document.getElementById("gfdata-us")?"gfdata-us":"gfdata").textContent));')
# the USA side (Oct 6, 2026): its items on sale, when the site folder has deals-us.json (kept small: sale items, no photos)
us_path = SITE / "deals-us.json"
us_blob = ""
if us_path.exists():
    du = json.loads(us_path.read_text())
    us_blob = json.dumps({"updated": du["updated"], "stores": du.get("stores", {}), "n_stores": du.get("n_stores"), "fx": du.get("fx", {}),
                          "items": pretend_history([{k: v for k, v in x.items() if k != "img"} for x in du["items"] if on_sale(x)])},
                         separators=(",", ":")).replace("</", "<\\/")
a = s.index("async function rpc(fn,args,bearer){")
b = s.index("\n}\n", a) + 3
s = s[:a] + '''async function rpc(fn,args,bearer){   // preview: pretend server, nothing leaves the page
  await new Promise(r=>setTimeout(r,300));
  const fake={lang:LANG,gender:"men",ships:"ca",sizes:{shoes:{sizes:["10"],width:["Regular"]},tops:{sizes:["M"]},bottoms:{sizes:["M"]},socks:{sizes:["M"]}}};
  if(fn==="google_profile")return signinMode?{found:true,email:"you@gmail.com",key:"00000000-0000-0000-0000-000000000000",profile:fake,subscribed:true}:{found:false,email:"you@gmail.com"};
  if(fn==="google_subscribe")return {found:true,email:"you@gmail.com",key:"00000000-0000-0000-0000-000000000000",profile:args.p_profile,subscribed:true};
  return {subscribe:"sent",send_link:"sent",save_profile:true,unsubscribe:true,watch_add:true,watch_remove:true,watch_list:[]}[fn]??null;
}
''' + s[b:]

rep("/* ---------- start ---------- */", '''/* ---------- preview: stand-in for Google sign-in (the real one only runs on thegearfox.com) ---------- */
G.load=function(){G.ready=true};
G.exchange=async()=>"preview";
G.render=function(){["gBtnW","gBtnUp","gBtnIn"].forEach(id=>{const el=$(id);if(!el)return;
  el.innerHTML=`<button type="button" class="pvg">${LANG==="fr"?"Continuer avec Google":"Continue with Google"} <small>(stand-in)</small></button>`;
  el.firstChild.addEventListener("click",()=>onGoogle("preview"))})};

/* ---------- preview panel ---------- */
function pvMsg(t){$("pvMsg").textContent=t}
const PVNEW=__PVNEW__;   // what changed in this preview (--new)
if(PVNEW.length){document.body.classList.add("pvhl");
  $("pvHl").addEventListener("click",e=>{const on=document.body.classList.toggle("pvhl");e.target.setAttribute("aria-pressed",String(on));e.target.textContent=on?"Highlights on":"Highlights off"});
  document.querySelectorAll(".pvshow").forEach(b=>b.addEventListener("click",()=>{const [sel,what,how]=PVNEW[+b.dataset.n];
    const el=[...document.querySelectorAll(sel)].find(x=>x.getClientRects().length);
    if(!el){pvMsg(`"${what}" isn't on screen right now. ${how||""}`);return}
    el.scrollIntoView({behavior:"smooth",block:"center"});el.classList.remove("pvflash");void el.offsetWidth;el.classList.add("pvflash");pvMsg(`${what}: outlined in orange.`)}))}
function pvClear(){["rd-profile","gf-sub","gf-watch","gf-last","gf-base","gf-clicks","gf-peek"].forEach(k=>LS.set(k,null))}
document.querySelectorAll("#pvCards button").forEach(b=>{b.setAttribute("aria-pressed",String(b.dataset.c===CARDS));
  b.addEventListener("click",()=>{try{localStorage.setItem("gf-cards",JSON.stringify(b.dataset.c))}catch(e){}location.reload()})});
$("pvReset").addEventListener("click",()=>{pvClear();location.reload()});
document.querySelectorAll("#pvFlow button").forEach(b=>{b.setAttribute("aria-pressed",String(b.dataset.f===FLOW));
  b.addEventListener("click",()=>{try{localStorage.setItem("gf-flow",JSON.stringify(b.dataset.f))}catch(e){}pvClear();location.reload()})});
$("pvConfirm").addEventListener("click",()=>{
  if(gated()){pvMsg("Sign up first (sizes and an email), then tap this.");return}
  setSub({key:"00000000-0000-0000-0000-000000000000",email:state.email||"you@example.com",active:true});
  $("notice").classList.add("hidden");renderAll();pvMsg("You're now a confirmed subscriber. Hearts say you'll get alerts, and the sign-up card is gone.")});
$("pvDay").addEventListener("click",()=>{
  if(!hasSizes()){pvMsg("Pick your sizes first (Find my deals), then tap this.");return}
  const sale=matchItems(toProfile()).filter(d=>d.pct>0).sort((a,b)=>b.pct-a.pct);
  const keys=sale.map(itemKey);
  LS.set("gf-last",{at:Date.now()-26*3600e3,keys:keys.filter((_,i)=>i%8!==3)});LS.set("gf-base",null);
  if(!Object.keys(watches).length)sale.slice(0,3).forEach(d=>{const k=itemKey(d);watches[k]={b:d.b,n:d.n,g:d.g,url:d.url,price:d.best,low:d.best,seen:d.best,gone:false,saved:new Date(Date.now()-3*86400e3).toISOString()}});
  Object.entries(watches).forEach(([k,w],i)=>{
    if(i===1){w.gone=true;return}
    if(w.price!=null){const up=Math.round(w.price*1.18);w.price=up;w.seen=up;w.low=up}});
  LS.set("gf-watch",watches);
  const d=sale[0];if(d&&!Object.keys(clicks).length){clicks[itemKey(d)]={off:Math.round((d.reg-d.best)*100)/100,at:Date.now()-26*3600e3,p:Math.round(d.best*1.15)};LS.set("gf-clicks",clicks)}   // a deal "opened yesterday" at a higher price: "Since your last visit" shows a drop
  location.reload();
});

/* ---------- start ---------- */''')
s = s.replace("__PVNEW__", new_js)
s = s.rstrip() + '\n<script type="application/json" id="gfdata">' + blob + "</script>\n"
if us_blob:
    s += '<script type="application/json" id="gfdata-us">' + us_blob + "</script>\n"
m = s.index("<script>\n(function(){")
e = s.index("</script>", m) + len("</script>")
s = s[:m] + s[e:] + s[m:e] + "\n"
out.write_text(s)
print(f"wrote {out} ({len(s)//1024} KB, {len(items)} products)")
