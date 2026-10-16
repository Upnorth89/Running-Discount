/* The Gear Fox — "Grab deals" bookmark.
   Run it on any MEC, REI or SVP Sports product list in your own browser: the running deals, or a regular list (all running
   gear, running shoes, clothing...; Oct 16, Bastien: "both options for all websites... all running gear and on sale items"). It reads the page you're on,
   then opens the next pages one at a time (a relaxed ~2 s apart, like clicking "next"), and
   downloads one file to upload to saved-pages/ on GitHub. */
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const box = document.createElement("div");
  box.style.cssText = "position:fixed;z-index:2147483647;top:16px;right:16px;background:#17201C;color:#fff;font:600 15px/1.4 system-ui;padding:14px 18px;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.3);max-width:320px";
  document.body.appendChild(box);
  const say = t => { box.textContent = t; };
  const download = (name, obj) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(obj)], { type: "application/json" }));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
  };
  // Oct 8: a phone can't upload a file to GitHub easily, so the list goes straight to thegearfox.com/grab-save.html
  // (one tap: a new tab can only open from a tap). The file download stays as a backup for computers.
  let keep = false;
  const save = (name, obj) => {
    keep = true;
    const n = (obj.hits || obj.results || obj.products || []).length;
    box.textContent = "";
    const t = document.createElement("div"); t.textContent = `${n} products read.`;
    const b = document.createElement("button"); b.textContent = "Send to The Gear Fox";
    b.style.cssText = "display:block;margin:10px 0 8px;font:800 16px system-ui;background:#D7F23A;color:#17201C;border:0;border-radius:10px;padding:11px 16px;cursor:pointer";
    const d = document.createElement("a"); d.textContent = "or download the file";
    d.href = URL.createObjectURL(new Blob([JSON.stringify(obj)], { type: "application/json" })); d.download = name;
    d.style.cssText = "color:#fff;font-size:13px;text-decoration:underline";
    box.append(t, b, d);
    b.onclick = () => {
      const w = window.open("https://thegearfox.com/grab-save.html", "gfgrab");
      if (!w) { t.textContent = "Pop-up blocked: allow pop-ups for this site, or download the file."; return; }
      let tries = 0;
      const iv = setInterval(() => {
        if (++tries > 60) return clearInterval(iv);
        try { w.postMessage({ gf: "save", payload: obj }, "https://thegearfox.com"); } catch (e) {}
      }, 500);
      addEventListener("message", e => {
        if (e.origin === "https://thegearfox.com" && e.data && e.data.gf === "got") {
          clearInterval(iv); t.textContent = "Sent ✓ The new tab says when it's saved."; b.remove();
        }
      });
    };
  };
  const fetchDoc = async url => new DOMParser().parseFromString(await (await fetch(url, { credentials: "include" })).text(), "text/html");
  const host = location.hostname;
  try {
    if (/mec\.ca$/.test(host)) {
      // the product list in the page's data: any object with "hits" + "nbPages" (deals and regular lists name it differently)
      const find = (o, depth = 0) => {
        if (!o || typeof o !== "object" || depth > 12) return null;
        if (Array.isArray(o.hits) && "nbPages" in o) return o;
        for (const v of Object.values(o)) { const r = find(v, depth + 1); if (r) return r; }
        return null;
      };
      const results = d => { const r = find(d.props); if (!r) throw new Error("no product list on this page: open a list like Running shoes or the running deals"); return r; };
      const DROP = ["_highlightResult", "_rankingInfo", "_collections", "styleCategoryPageId", "categoryPageId", "facets",
                    "imageTransparent", "swatch", "analytics", "storeInventory", "promotions", "stylePromotions", "priceBuckets"];
      const slim = h => { const o = { ...h }; DROP.forEach(k => delete o[k]); return o; };   // ~23 KB -> ~5 KB a product
      const nd = doc => JSON.parse(doc.getElementById("__NEXT_DATA__").textContent);
      say("MEC: reading page 1…");
      const first = results(nd(await fetchDoc(location.href)));   // fresh copy: the open tab may be stale after filtering
      let hits = first.hits.map(slim); const pages = Math.min(first.nbPages || 1, 80);
      let offset = null;
      for (let n = 1; n < pages; n++) {
        say(`MEC: page ${n + 1} of ${pages}…`); await sleep(2000);
        for (const cand of offset === null ? [n + 1, n] : [n + offset]) {
          const u = new URL(location.href); u.searchParams.set("page", cand);
          const doc = await fetchDoc(u);
          const r = results(nd(doc));
          if (r.page === n) { offset = cand - n; hits = hits.concat(r.hits.map(slim)); break; }
        }
      }
      save(`mec-${new Date().toISOString().slice(0, 10)}.json`, { store: "mec", saved: new Date().toISOString(), hits });
    } else if (/rei\.com$/.test(host)) {
      const results = doc => JSON.parse(doc.getElementById("initial-props").textContent).ProductSearch.products.searchResults;
      say("REI: reading page 1…");
      const first = results(await fetchDoc(location.href));      // fresh copy: reflects your current sort/filter
      const m = ((first.pagination || {}).lastPage || {}).queryString?.match(/[?&]page=(\d+)/);
      const pages = Math.min(m ? +m[1] : 1, 150);          // 30 per page: all running gear is ~100 pages (deals ~30)
      const KEEP = ["prodId", "title", "cleanTitle", "brand", "link", "thumbnailImageLink", "sizeDetails", "regularPrice",
                    "displayPrice", "sale", "clearance", "gender", "available", "percentageOff", "skus", "skuSizes"];
      const slim = r => Object.fromEntries(KEEP.filter(k => k in r).map(k => [k, r[k]]));   // ~5 KB -> ~1.5 KB a product
      let items = first.results.map(slim);
      const start = +(new URL(location.href).searchParams.get("page") || 1);
      for (let n = start + 1; n <= pages; n++) {
        say(`REI: page ${n} of ${pages}…`); await sleep(2000);
        const u = new URL(location.href); u.searchParams.set("page", n);
        items = items.concat((results(await fetchDoc(u)).results || []).map(slim));
      }
      save(`rei-${new Date().toISOString().slice(0, 10)}.json`, { store: "rei", saved: new Date().toISOString(), results: items });
    } else if (/svpsports\.ca$/.test(host)) {
      // SVP is a Shopify store: read the collection you're on (e.g. running shoes on sale) page by page
      const m = location.pathname.match(/^((?:\/[a-z]{2})?\/collections\/[^/]+)/);
      if (!m) throw new Error("open a product list (a collection), like running shoes on sale");
      let products = [];
      for (let n = 1; n <= 12; n++) {
        say(`SVP: page ${n}…`); if (n > 1) await sleep(2000);
        const r = await fetch(`${location.origin}${m[1]}/products.json?limit=250&page=${n}`, { credentials: "include" });
        const batch = (await r.json()).products || [];
        if (!batch.length) break;
        products = products.concat(batch);
        if (batch.length < 250) break;
      }
      save(`svp-${new Date().toISOString().slice(0, 10)}.json`, { store: "svp", saved: new Date().toISOString(), url: location.href, products });
    } else if (/hoka\.com$/.test(host)) {
      // Hoka (test, Oct 5): saves only what this tab already shows (no extra requests at all), like "Save page as".
      // Scroll to the bottom first so every shoe on the page has loaded.
      const ld = [...document.querySelectorAll('script[type="application/ld+json"]')].map(x => x.textContent);
      const data = [...document.querySelectorAll("script:not([src])")].map(x => x.textContent)
        .filter(t => /price|pid|productId/i.test(t)).map(t => t.slice(0, 300000)).slice(0, 20);
      const tiles = [...document.querySelectorAll("[data-pid], .product-tile, .product")].slice(0, 400).map(x => x.outerHTML.slice(0, 6000));
      download(`hoka-${new Date().toISOString().slice(0, 10)}.json`, { store: "hoka", saved: new Date().toISOString(), url: location.href, ld, data, tiles });
      say(`Hoka: ${tiles.length} shoes on this page saved. File saved.`);
    } else {
      say("Open a running product list on MEC, REI or SVP Sports first (the deals or all running gear), then tap the bookmark.");
    }
  } catch (e) {
    say("Couldn't read this page (" + e.message + "). Open a product list (running deals, Running shoes, Running clothing...), then try again.");
  }
  if (!keep) setTimeout(() => box.remove(), 12000);
})();
