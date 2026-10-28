"""Gift guide prototype: 'Gifts for runners on sale' by budget, from today's sale.json (Canada)."""
import json,re,collections,sys,html
d=json.load(open(sys.argv[1]));its=d['items'];LANG=sys.argv[2] if len(sys.argv)>2 else 'en'
bc=collections.Counter(i['b'] for i in its)
NOT=re.compile(r"\b(l/s|s/s|long sleeve|short sleeve|half-?zip|1/4 zip|quarter zip|tee|shirt|jacket|hoodie|tight|short|pant|race number|attachment|replacement|refill|lens only|strap only|insole|lace)\b",re.I)
HYD=re.compile(r"hydration|race vest|\d+ ?l\b(?!/)|belt|flask|bottle",re.I)
ONE={'OS','O/S','ONE SIZE','ONESIZE','TU','UNI','1','ONE'}
KIND={'headwear':('Hats & headbands','Tuques et bandeaux'),'gloves':('Gloves & mitts','Gants et mitaines'),'socks':('Socks','Bas'),
      'light':('Lights & headlamps','Lampes frontales'),'bottle':('Bottles & flasks','Bouteilles et flasques'),'sun':('Sunglasses','Lunettes de soleil'),
      'packs':('Vests & belts','Vestes d\'hydratation et ceintures'),'watches':('Watches','Montres')}
def kind(i):
    if i['g'] in ('headwear','gloves','socks','watches'):return i['g']
    if i['g']=='packs':return 'packs' if HYD.search(i['n']) else None
    if i['g']=='gear' and i.get('t') in ('light','bottle','sun'):return i['t']
    return None
picks={25:[],50:[],100:[]}
for i in its:
    k=kind(i)
    if not k or not i.get('img') or not i.get('ca') or NOT.search(i['n']) and k!='packs':continue
    ps=[s[1] for s in i['sz']];regs=[s[3] for s in i['sz'] if s[3]]
    if not ps or not regs:continue
    p=min(ps);r=max(regs);off=1-p/r
    sale=off>=0.2 and r<=7*p
    if p<10 or (off>0.02 and not sale):continue
    sz={str(s[0]).upper() for s in i['sz']}
    if k in('headwear','gloves','socks') and not (sz&ONE or {'S','M','L'}<=sz or {'M','L'}<=sz):continue
    cap=25 if p<=25 else 50 if p<=50 else 100 if p<=100 else None
    if not cap:continue
    store=min(i['sz'],key=lambda s:s[1])[2]
    picks[cap].append(dict(sale=sale,score=(off*100 if sale else 0)+min(bc[i['b']],80)/4,b=i['b'],n=i['n'],k=k,p=p,r=r,img=i['img'],u=i['of'][store]))
out={}
for cap,l in picks.items():
    l.sort(key=lambda x:-x['score']);res={'s':[],'f':[]}
    for part,n in (('s',8),('f',4)):
        seenb={x['b'] for x in res['s']};seenk=collections.Counter()
        for x in l:
            if (part=='s')!=x['sale'] or x['b'] in seenb or seenk[x['k']]>=(3 if part=='s' else 1):continue
            seenb.add(x['b']);seenk[x['k']]+=1;res[part].append(x)
            if len(res[part])==n:break
    out[cap]=res
fr=LANG=='fr'
C=(lambda v:f"{v:.2f}".replace('.',',')+" $") if fr else (lambda v:f"${v:.2f}")
T=dict(title="Cadeaux pour coureurs : moins de 25 $, 50 $ et 100 $" if fr else "Gifts for runners: under $25, $50 and $100",
 sub=("Des idées sans souci de taille (taille unique, ou petit/moyen/grand en stock) dans des boutiques canadiennes : les soldes du jour d'abord, puis des classiques à prix régulier à suivre. Mis à jour chaque matin." if fr else
      "Ideas you can buy without knowing their size (one size, or small/medium/large in stock) at Canadian stores: today's sales first, then full-price favourites worth watching. Updated every morning."),
 under=(lambda c:f"Moins de {c} $") if fr else (lambda c:f"Under ${c}"),off="de rabais" if fr else "off",
 note=("Les prix changent chaque jour : vérifiez sur le site de la boutique. Rien ici ne nous rapporte d'argent." if fr else "Prices change daily: check on the store's site. Nothing here earns us money."),
 more="Vous courez aussi ? Voyez les aubaines dans votre taille →" if fr else "Run yourself? See deals in your size →",
 onsale="En solde aujourd'hui" if fr else "On sale today",full="Prix régulier : on vous écrit s'il baisse" if fr else "Full price: we'll email you if it drops",
 watch="♡ Suivre le prix" if fr else "♡ Watch the price",fp="Prix régulier" if fr else "Full price",
 box=("Le 26 décembre (Boxing Day), bien des prix baissent encore. Suivez un article : on vous écrit s'il baisse." if fr else "Prices often drop again on Boxing Day. Watch an item and we'll email you if it drops."))
cards=lambda l:''.join(f'''<a class="g" href="{html.escape(x["u"])}" rel="nofollow"><span class="ph"><img src="{html.escape(x["img"])}" alt=""></span><span class="k">{KIND[x["k"]][1 if fr else 0]}</span><b>{html.escape(x["b"])}</b><span class="n">{html.escape(x["n"])}</span><span class="pr">{C(x["p"])}{(f' <s>{C(x["r"])}</s> <em>−{round((1-x["p"]/x["r"])*100)}%</em>' if x["sale"] else f' <span class="fpl">{T["fp"]}</span>')}</span>{'' if x["sale"] else f'<span class="wt">{T["watch"]}</span>'}</a>''' for x in l)
page=f'''<!doctype html><html lang="{LANG}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{T["title"]} | The Gear Fox</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet"><style>
*{{box-sizing:border-box}}body{{margin:0;background:#F5F6F2;color:#14201C;font:16px/1.5 Inter,system-ui,sans-serif}}header{{background:#17201C;color:#fff;padding:12px 16px;display:flex;align-items:center;gap:10px}}header img{{width:34px;height:34px;border-radius:50%}}
main{{max-width:1100px;margin:0 auto;padding:22px 16px 40px}}h1{{font:800 32px/1.08 Inter;letter-spacing:-.03em;margin:0 0 8px}}.sub{{color:#3A4542;margin:0 0 8px;max-width:40em}}
h2{{font:800 22px/1.2 Inter;margin:26px 0 10px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}@media(min-width:720px){{.grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}}}@media(min-width:1000px){{.grid{{grid-template-columns:repeat(4,minmax(0,1fr))}}}}
.g{{background:#fff;border:1px solid #DDE0D8;border-radius:14px;padding:10px;text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:2px}}.ph{{aspect-ratio:1;background:#F2F2EE;border-radius:10px;display:grid;place-items:center;overflow:hidden;margin-bottom:6px}}.ph img{{width:100%;height:100%;object-fit:contain}}
.k{{font-size:11.5px;color:#2E6B4F;font-weight:600;text-transform:uppercase;letter-spacing:.04em}}.g b{{font-size:14px}}.n{{font-size:13.5px;color:#3A4542;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.pr{{margin-top:auto;padding-top:6px;font-weight:700}}.pr s{{color:#8A918E;font-weight:400;font-size:13px}}.pr em{{font-style:normal;color:#1D6B45;font-size:13px}}h3{{font:600 13px/1.3 Inter;text-transform:uppercase;letter-spacing:.06em;color:#55605C;margin:14px 0 8px}}.fpl{{font-weight:500;font-size:12.5px;color:#6B7572}}.wt{{font-size:13px;font-weight:600;color:#1D3A30;margin-top:4px}}.bx{{background:#E7EFE9;border-radius:12px;padding:12px 14px;margin-top:22px;color:#1F3A2E}}.note{{font-size:13px;color:#6B7572;margin-top:24px}}.more{{display:inline-block;margin-top:14px;font-weight:700;color:#1D3A30}}
</style></head><body><header><img src="fox-face.webp" alt=""><b>The Gear Fox</b></header><main><h1>{T["title"]}</h1><p class="sub">{T["sub"]}</p>
{''.join(f'<h2>{T["under"](c)}</h2><h3>{T["onsale"]}</h3><div class="grid">{cards(out[c]["s"])}</div>'+(f'<h3>{T["full"]}</h3><div class="grid">{cards(out[c]["f"])}</div>' if out[c]["f"] else '') for c in (25,50,100))}
<p class="bx">{T["box"]}</p>
<a class="more" href="/">{T["more"]}</a><p class="note">{T["note"]}</p></main></body></html>'''
open(f'gifts-{LANG}.html','w').write(page)
print({c:{k:[(x['b'],x['n'],x['p']) for x in v] for k,v in out[c].items()} for c in out})
