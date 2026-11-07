# Data audit, Sat Nov 7 2026 (live sale.json / sale-us.json, updated 11:42 UTC)

Read with TheGearFoxBot (scraper/polite.py), robots.txt obeyed, 3-4 s between store pages. No 403/429/captcha met.
Verdict: **PROBLEMS** (1 trust problem, 2 sorting problems, 2 small). Every price checked matched the store's own page.

## Problems, worst first

### 1. Unisex shoes: men's sizes shown to women as their own size (trust, "a women's shoe in men's sizes")
- What: on unisex race shoes, sizes stored with no cut (plain "7.5") are men's US sizes, but the site matches them to a
  woman's size. A women's 8 visitor sees a men's 8 (= women's 9-9.5), often as the card's best price.
- Where: 45 Canadian cards (sizes from The Last Hunt 145, Boréal 39, Aerobics First 34, Frontrunners 30, Altitude 26, Run Uphill 12...)
  and 81 US cards (PR Run & Walk 202, Gazelle 104...). Examples: Hoka Cielo X1 2.0 - Unisex, Mizuno Hyperwarp Pro - Unisex,
  Brooks Hyperion Elite 5 - Unisex, adidas Adizero Prime X3 Strung - Unisex, Mizuno Wave Rebellion Pro 3 - Unisex.
- Evidence: Hoka Cielo X1 2.0, The Last Hunt (https://www.thelasthunt.com/p/hoka-cielo-x1-20-road-running-shoes-mens-hoo-1162053):
  the store's sizes are "8 / 9", "9 / 10"... (men's / women's), $204.74 / $324.99. Ours: plain "8", "9"... on a card with
  sx = men + women, so a women's 8 matches the store's men's 8 / women's 9. Same card already has correct "M:9.5"/"W:10.5" keys from
  Gord's. Mizuno Hyperwarp Pro: plain "9.5" $185.95 (men's, Altitude) beats the real "W:9.5" $188.88 for a women's 9.5.
  Boréal's Wave Rebellion Pro 3: store variant "7.5 / D" (men's D width), ours plain "7.5" on a men+women card.
- Cause: site/index.html `matchItems()` shoe branch: `if(k.g&&G&&k.g!==G)return false;` lets a key with no cut through for
  either gender. The CT reader (Last Hunt/Altitude) reduces "8 / 9" to "8" before canon_shoe (canon_shoe("8 / 9") already
  returns ["M:8","W:9"]).
- Smallest fix: in the merge (scraper/scrape.py, where canon_shoe keys are made, ~line 5261), a shoe offer whose sx is men+women
  turns a plain numeric key into "M:<n>" (unisex shoes are sold on the men's scale); and keep the CT size label whole ("8 / 9")
  so canon_shoe adds the W: key. Same rule in index.html matchItems (plain key + d.sx.length>1 = "M"), weekly_email.py match()
  and shoe_pages.py size tables. Check: no both-gender shoe card left with a plain numeric sale size.

### 2. Long tights, leggings and joggers typed as Shorts
- What: any name with an inch number ("28\"", "27 in") is typed `short` before the tight/pant rules are tried.
- Where: 39 Canadian + 35 US cards with an inseam of 15"+ under Shorts. Examples: Hoka ColdSnap Run Tight 28" - Women's
  (Culture Athletics, new today), New Balance NB Sleek Pocket High Rise Legging 27" (Culture), Ciele FST Tight 29" (4 stores),
  Hoka Elaro Knit Tights 27 in, MPG Vital HR PKT Jogger 28", New Balance Athletics Standard Tapered Pant 30" - Men's,
  US: lululemon Align High-Rise Pant 25", The North Face Dune Sky 28in Legging, Patagonia Utility Pant (30" Inseam).
- Cause: scraper/scrape.py TYPES["bottoms"] "short" regex `\d(\.\d)?\s*(\"|''|”|in\b|inch)`.
- Smallest fix: only inseams up to 12 count as a short: `\b(?:[1-9]|1[0-2])(?:\.\d)?\s*(\"|''|”|in\b|inch)`
  (then "legging/tight" -> tight, "pant/jogger" -> pant; 5-9" half tights stay shorts as today).

### 3. Last night's boxer fix also took running shorts out of Shorts (side effect)
- What: 8 Canadian running shorts with a brief liner now have no type (shown only under "All"):
  Nike Tempo Brief-Lined Running Shorts (W), Nike Tempo Brief-Lined Shorts (W), Nike Tempo Flow Swoosh Brief-Lined Short (W),
  Nike One Dri-Fit High Waisted Brief-Lined 3 Inch Shorts (W), Nike One Dri-Fit Mid-Rise Brief-Lined Shorts (W),
  adidas Run Fast Inner Briefs Running Shorts (W), Ciele DLYShort 5 Inch Long Brief 2 (M), Ciele ICNShort 3 Inch Brief (M) (Culture).
- Cause: scraper/scrape.py type function (~line 4465): the exemption `brief(?:s)?\s+(?:lined|liner)` misses the hyphen
  ("Brief-Lined"), and the inch exemption has no re.I ("3 Inch" with a capital I).
- Smallest fix: `brief(?:s)?[\s-]+(?:lined|liner)`, add re.I to the inch test, and exempt names that say "short(s)" unless they
  also say boxer/underwear/trunk.
- The boxer fix itself is live: 58 CA / 78 US boxer/underwear/trunk bottoms, none typed short.

### 4. Colour-only products get colour names as sizes (small)
- Culture Athletics: "Unisex Hoka Run Hat" sizes "White", "Mineral Blue"; Vuori "Unisex Dad Hat" size "Lilac Breeze" (store option
  is only "Color"). A sized visitor never sees them; the card would list colours as sizes.
- Fix: Shopify reader (make_shopify_scraper / shopify_items): a product whose only option is Color/Colour -> size "OS".

### 5. Culture Athletics: lifestyle/novelty items on a running site (small, judgment call)
- Stance "Christmas Vacation x Stance Griswold Crew Socks", "The Grinch Mean One Crew Socks", "The Grinch x Stance Down In Whovile
  Crew Socks"; Vuori Halo Essential Wideleg Pant, Halo Modern Pullover Hoodie, Unisex Dad Hat; Balmoral Athleisure T-Shirt /
  Campus Crop Tank. The same brands already come from other stores (Vuori at Running Room 28, Strides 15...; stance.ca Grinch), so
  not new to Culture. Also 26 separate Ciele cap cards (colour stays in un-gendered names: "GOCap - Classic - Athletics - Quarry").
- Fix if wanted: NOT_RUNNING words for novelty licence lines (Grinch, Christmas Vacation) + Vuori "Halo/Lux/Dad Hat"; Culture colour
  cut also for "GOCap/FSTCap/TRLCap ... - <colour>" (last segment).

## 1. Featured / top-scored + deepest Canadian deals vs the store's page (all MATCH)
| Item | Store | Store page (price / regular, size, stock) | Ours |
|---|---|---|---|
| NB FuelCell SuperComp Trainer v3 W | SVP | $99.99 / $329.99, W10, in stock | same |
| Saucony Endorphin Elite 2 Unisex | Le Coureur Nordique | $148 / $369.99, "6.0 H / 7.5 F" | same, M:6 |
| Naked T/R Trail Unisex | Trail Runner Store | $76 / $247, M6/W7 (title says FINAL SALE) | same |
| adidas Adizero Prime X3 Strung | BlackToe | $200 / $400, M8/W9 | same |
| Mizuno Wave Rebellion Pro 3 Unisex | Boréal | $129.95 / $309.95, "7.5 / D" | price same; size cut wrong (#1) |
| ASICS MetaRide M | 33-Off | $125 / $299.99, 8 D | same |
| NNormal Kjerag Unisex | Run Uphill | $99 / $259.95, 4.5 | same |
| On Cloudboom Strike M | La Boutique du Lac | $180 / $359.99, 8 | same |
| Patagonia Nano-Air Light Hybrid Hoody W | Bushtukah | $187.50 / $375, XS | same |
| Craft Kype Pro M | The Last Hunt | $207.99 / $399.99 | same |
| NB SuperComp Elite v4 Wide W | Gord's | $164.95 / $329.95, 8 D (only size in stock) | same, 8~W |
| Saucony Endorphin Elite 2 M | Saucony CA | C$199.95 / C$370 | same |
| 2XU Form Soft Touch 4" Shorts W (86%) | 2XU CA | $10 / $70, XXL | same, 2XL |
| ASICS Road Balance Tight W (85%) | SVP | $14.99 / $99.99, S | same |
| ASICS Wild Camo Sprinter Tights W (85%) | SVP | $9.99 / $64.99, XS | same |
| adidas Blakelock Tigers Tank W (85%) | SVP | $9.99 / $64.99, XS | same |
| Fuel Belt Race Number Attachment (86%) | Running Room | $1.00 / $6.99 | same |
| ASICS Studio Luxe Headband (85%) | Running Room | $3.00 / $19.99 | same |
All in CAD, gender and colour as named. Deep ones are real clearance (SVP, Running Room, 2XU), not wholesale/bundle prices.

## 2. Culture Athletics (new today)
- Live: stamp 11:42 UTC, currency CAD (homepage Shopify.currency active CAD), 172 sale.json cards carry it, 170 sizes priced at
  Culture. **All 170 match its products.json: price, compare-at, in stock, size label (per-size variant id).**
- Categories: shoes 53 (daily 32, race 19, trail 2), tops 40, headwear 32, bottoms 26, socks 11, bras 8, gear 1, packs 1.
  Gender read right on every gendered name (Mens/Womens/Unisex). Problems: #2, #3, #4, #5 above.
- Shop sale items not on the site (36): spot-checked 3 shoes; each is cheaper at another store in those sizes (e.g. Endorphin
  Speed 5 M $179.95 vs SVP $119.99), so the merge is right.

## 3. Last night's fixes
- Boxer briefs under bottoms/short: **fixed** (0 left, both sides); side effect = #3.
- Store count: **consistent by definition**. Homepage "We check 154 stores in Canada and the USA" (n_stores = stores with products
  today, both sides); About "more than 150 running shops, most of them Canadian"; FR BF « 99 boutiques de course canadiennes »,
  EN BF "99 Canadian running stores", BF deal check EN/FR "99 stores" (n_side Canada). US n_side = 88. One note: the welcome stat
  tile shows 154 on the Canada side next to BF pages' 99; the sentences say which side, so no fix needed.
- /us/shoes/jason-markk-quick-clean-kit/: **gone** from sitemap.xml (2,799 URLs, no clean/blister kit) and the page answers 404.
