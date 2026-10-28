"""Deal check index: one small file per store host, so the page fetches only the pasted link's store.
check/<host>.json = {"k": {pathkey: item index}, "i": [item, ...]}; item = brand, name, photo, group, lo/hd/hi (60-day history
of the best price), this store's sizes [size, price, regular], other stores [[name, ca, [[size, price], ...]], ...]."""
import json, sys, os, collections
from urllib.parse import urlparse
deals, offers, out = sys.argv[1:4]
D = json.load(open(deals)); O = json.load(open(offers))
names = D.get("stores", {})
def key(u):
    p = urlparse(u); h = p.netloc.lower().removeprefix("www."); path = p.path.lower().rstrip("/")
    if "/products/" in path: path = "products/" + path.split("/products/")[-1]
    return h, path
off = {}
for st, lst in O.items():
    if not isinstance(lst, list): continue
    for o in lst:
        if isinstance(o, dict) and o.get("u") and not o.get("no_ca"): off.setdefault(key(o["u"]), o)
shards = collections.defaultdict(lambda: {"k": {}, "i": []})
miss = hit = 0
for it in D["items"]:
    ofs = it.get("of", [])
    per = []
    for u in ofs:
        o = off.get(key(u))
        if not o: per.append(None); continue
        per.append([[s[0], s[1], s[2] if len(s) > 2 and isinstance(s[2], (int, float)) else None] for s in o.get("sz", []) if isinstance(s[1], (int, float))])
    for i, u in enumerate(ofs):
        h, k = key(u)
        if per[i] is None: miss += 1; continue
        hit += 1
        sh = shards[h]
        if k in sh["k"]: continue
        others = [[urlparse(ofs[j]).netloc.lower().removeprefix("www."), [[s[0], s[1]] for s in per[j]]] for j in range(len(ofs)) if j != i and per[j]]
        sh["k"][k] = len(sh["i"])
        sh["i"].append({"b": it["b"], "n": it["n"], "img": it.get("img"), "g": it["g"], "sx": it.get("sx"), "lo": it.get("lo"), "hd": it.get("hd"),
                        "hi": it.get("hi"), "lp": it.get("lp"), "me": per[i], "ot": others})
os.makedirs(out, exist_ok=True)
tot = 0
for h, sh in shards.items():
    p = os.path.join(out, h + ".json"); json.dump(sh, open(p, "w"), separators=(",", ":")); tot += os.path.getsize(p)
json.dump({"hosts": sorted(shards), "updated": D.get("updated")}, open(os.path.join(out, "hosts.json"), "w"))
print("stores", len(shards), "links", hit, "unmatched", miss, "MB", round(tot / 1e6, 1),
      "biggest", max((os.path.getsize(os.path.join(out, h + ".json")), h) for h in shards))
