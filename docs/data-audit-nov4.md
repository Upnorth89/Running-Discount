# Data audit, night of Nov 3-4, 2026 (live site, files updated 04:45 UTC Nov 4; last store read 23:42 UTC Nov 3)

RESULT: PROBLEMS (6 data problems, 1 race-list wording problem). Worst first.

## How I checked
- Files: sale.json (9,691 items), sale-us.json (12,561), sale-hike.json (5,497). deals*.json not read (robots-disallowed).
- Sample: 171 deals = top 30 by featured_check score + 20 deepest discounts + 10 random, for each side.
- Checked on the store's own page (TheGearFoxBot UA, robots.txt obeyed, 3 s apart, at most ~20 product pages per store):
  - 85 Shopify products (.js with Canadian cookies for CAD shops, .json for base price and tags): 78 match exactly (price, regular, in stock, size, colour, gender).
  - 5 Running Room / Last Hunt deals checked with livecheck.still_on_sale: all confirmed.
  - Not checked: 1 Sport Chek (livecheck can't tell), 17 REI/Backcountry (bot protection, not tried), 62 skipped by the per-store cap (SVP, Gazelle, Fit2Run, Geartrade).
  - No 403/429/captcha anywhere. FYI: altrarunning.com robots.txt now has `Disallow: /products/` for every bot (products.json is still allowed, so the reader is fine).
- Listing junk, categories and sizes: scans of all three files. Races: 5 lists compared line by line with each race's own page.

## 1. Hiking: used gear from Gear Trade shown as "80% off" sales (worst)
- Where: sale-hike.json, store geartrade.com. 906 items. Gear Trade holds all of the top 100 hiking deals by score, and 278 of the hiking 70%+ discounts.
- Evidence:
  - Timberland Premium 6-Inch Waterproof Boot, Men's 15: we show $55.42, was $277.08 (-80%). The store page says "This UnNew Timberland Premium 6-Inch Waterproof Boot - Men's is in Good condition. Products in Good condition have been well loved ... Minor outsole stains from typical wear". Tags include `consignment-items-over-80`.
  - Hanwag Banks Lady GTX, Women's 6.5: $83.96, was $419.82. Store: "This UnNew ... is in Good condition". This one has NO consignment tag.
  - AKU Minima Low, Women's 5.5: store says "is in New condition". So the store sells new and used side by side.
  - Stio "Rivet Twill Short - Women's (SAMPLE)": $24.91, was $124.55.
- Likely cause: scraper/hike.py line ~406 keeps products tagged `RetailVendorPartner` and assumes that means new stock. Used items carry that tag too.
- Spec: for geartrade, keep a product only when body_html says "is in New condition". Drop "UnNew", "Excellent/Good/Fair condition", any `consignment*` tag, and "(SAMPLE)" in the title. Until that ships, leave Gear Trade off the hiking side.
- Same kind of problem at other stores:
  - Sea to Summit "Ultra-Sil Pack Cover (Like New)" (handle ...-used).
  - wildrock.net "Mountain Hardwear Ghost Lite Windbreaker" (handle ...-xl-used).
  - Feathered Friends "Down Comforter - Washed and Returned or Factory Second" at $1,353.50 and $849.72, filed as tops/insulated (it's bedding).
  - Spec: a generic used/returned rule (handle or title "-used", "like new", "washed and returned", "factory second", "(sample)") in the hiking and running Shopify readers.

## 2. LMNT wholesale prices: still live, should go after the next store read
- Where: sale.json AND sale-us.json, 3 cards:
  - "Zero-Sugar Electrolytes": $31.49 CAD, was $62.97 (-50%). Offers include lmnt-electrolytes-wholesale-pro and lmnt-recharge-wholesale.
  - "Variety Pack": $15.39, was $27.99. Offers include lmnt-recharge-wholesale-variety-pack.
  - "INSIDER MVP Bundle": $36.73, was $62.97. A members-only product.
- Evidence: all 6 products checked on drinklmnt.com carry the tag `Hidden` (plus `Wholesale Product` / `Bulk Buyer` / `Insider MVP Product`). Example: lmnt-recharge-wholesale shows US$22.50 against a US$45.00 regular, which is the price a visitor reported.
- Status: commit 7ec78fe (00:01 UTC Nov 4) skips all of these, but the last store read was 23:42 UTC Nov 3. Push runs only remerge, so they stay up until the 11:17 UTC read. Re-check sale.json after the morning run: 0 offers with "wholesale" in the URL, and no "INSIDER MVP Bundle".

## 3. Canada's #1 deal is gone, and Top deals are full of SVP lifestyle sneakers
- adidas NMD S1 - Women's, SVP: $39.99, was $229.99. It is the highest-scored Canada sale item. Both the product page and the .js now return 404 (product removed).
  - featured_check.py should catch this on the next refresh. Spec: run featured_check on push/remerge runs too, or confirm it already does.
- 17 of the top 30 Canada deals by score are SVP adidas clearance pairs, many of them lifestyle shoes.
  - The store's own tags say so: Oztral = `Casual`, `Originals`. X_PLRBoost = `Casual`.
  - Others in sale.json: NMD R1, Ozweego, Run 70s, Swift Run, Kaptir, Lite Racer, Cloudfoam Pure.
  - Prices themselves are right (9 SVP products + 6 of its 85%-off items match the store exactly).
- Likely cause: scrape.py `tidy_svp` / SVP reader. Only /collections/running-collection is read, but SVP files casual shoes there.
- Spec: drop SVP products tagged `Casual` or `Originals`.

## 4. Non-running and non-hiking products on the site
- Gazelle Sports (USA):
  - ~56 soccer jerseys and hoodies (store tags `Activity:Soccer`, `Apparel Type:Soccer Apparel`): Man Utd, Brazil, AC Milan, adidas Campeon/Squadra, Admiral "Cult Pullover Hoodie".
  - Soccer cleats filed as tops/tee: Nike Mercurial Vapor 16 Pro FG ($125.90), Mercurial Zoom Superfly 10 Elite FG ($223.86), Puma King Top FG/AG.
  - Cause: `SOCCER` / `GOALIE` only act on items read as shoes. Spec: drop Shopify products with soccer activity/apparel tags, plus FG/AG/"Soccer Cleat" names in any group.
- Confluence Running (USA): "Spring Training Programs", size "16-week Bridge Run half-marathon program" (a coaching plan), filed as a top at -72% (US$130 vs US$471). It is on the store as a product (tags "apparel, shirt collection").
- Fit2Run (USA): Tyrol "Drive V" and "Striker Pro V" (pickleball shoes) shown as daily running shoes at -67%. Spec: add Tyrol to COURT_SHOE / brand drop.
- REI (USA):
  - Under gear: crankbrothers Mallet / Stamp bike shoes, evolv Elektra climbing shoes, Birkenstock Utti.
  - Under packs: Black Diamond JetForce Pro avalanche airbag packs ($1,343).
  - Dakine Low Roller Snowboard Bag.
  - Under nutrition: Gear Aid "Snap Bar Repair Buckle".
  - Under bottoms: Patagonia "Bottom Turn Swimsuit Top".
- Run Uphill (Canada): Patagonia Powslayer ski pants ($405, was $809) and jacket ($500, was $999). NOT_RUNNING ski words miss "Powslayer".
- Rollga (both sides): "OHM - Experience Sound's Healing Power", $427, was $711, under gear.
- PR Run & Walk (USA): NB 900v4 / 700v5 XC Spikes filed under packs.
- Heartbreak Hill (USA): adidas "BAA 2026 Superlite Trainer" (a hat) is right under headwear. Fine.
- wildrock.net (hiking): Wilderness Systems "Silent Traction - Large Bow Hood Cover For Thresher & Atak" (kayak part) under gear/traction at -82%.
- Gear Trade (hiking): Timberland composite/alloy-toe WORK boots and work sneakers (Hypercharge, Switchback, Radius, TiTAN) under hiking boots/shoes. Paramount wading boot. La Sportiva Olympus Mons Cube (8000 m boot) and Scarpa Phantom Tech HD under hike/boot.

## 5. Wrong category or type (clothing)
- Socks group:
  - Smartwool "Active Mesh Polo - Men's" (both sides).
  - Stance "AURA SWEATPANT".
  - Stance "SHELTER WOMENS CREW" (US$80 regular, likely a crewneck sweatshirt) at -73%.
  - Cause: probably the sock-brand "Crew" rule in the merge. NOT_SOCK should keep polo/sweatpant/sweatshirt.
- Bottoms/short: Helly Hansen "Emiko Short Shell Jacket" (REI), Marmot "Chelsea Short Coat" (Backcountry), Columbia "Watertight II Jacket" (bottoms/tight, already in sortcheck), Backcountry "BGA Tahoe Sun Golf Polo", Tribal "Split Neck Striped Sweater".
  - Cause: "Short" read as shorts. Jacket/coat/polo/sweater should win.
- Packs (should be clothing tops): Brooks "Shield Hybrid Vest 3.0" (Boreal, Le Coureur, REI, Portland, Sports Basement), Brooks "Run Visible Insulated Vest 2.0" (REI), Craft "SubZ Vest 4" (Pacers).
- Tops: Smartwool "Second Cut Fleece Slipper(s)" (REI, Playmakers).
- Gender: name vs `sx` mismatches = 0 on all three files. Good.

## 6. Broken names, duplicate cards, unreadable sizes
- PR Run & Walk (USA): 32 cards with broken names, e.g. "ASCIS GT-2000 14 ( - Women's", "GEL-Nimbus 26 ( - 1012B602.400 - Women's", "GT - 2000 13 ( - 1012B667.022 - Women's". Unclosed "(", style codes and a misspelt brand, all left in. Spec: tidy_us_names should cut from "(" when it isn't closed, plus ASICS style codes \d{4}[AB]\d{3}(\.\d{3})?.
- Running Room (Canada): 9 cards with the SKU in the name, e.g. "Bedlam 3 Running Shoe (BRK-120330 1B 46432F0 12 (117) JET/ATLANTIS/A) - Women's".
- Duplicate cards: Saucony Hurricane 25 men's shows as 3 cards on the USA side: "Hurricane 25 - Men's" + "Hurricane 25 S21026 - Men's" (Scranton Running) + "Hurricane 25, 205 - Men's" (Columbus Running). Style/colour codes are not stripped. The health email also flags ACG Pegasus Trail GTX twins.
- Performance Running (USA): one Shopify product per size, so 8 shoe cards with size "OS" that show in every size ("Carbon Rocket X - 10.0", "Cumulus 27 - Taupe Grey", "860 V11"). Distance Run Wear: 2 Inov-8 shoes "OS".
- Visitor report "size · Saucony Hurricane 25 - Men's · prrunandwalk.com · USD $99.95": I couldn't reproduce it. The store now shows 8/9/10 Flint/Navy and 13 Black/White in stock at US$99.95 (was $170), and other sizes at the second product. That matches ours.

## 7. Small price drifts (low)
- Black Diamond (hiking): the store got cheaper after our read.
  - Session Suede Men's 7: ours US$123.45 (CAD 172.75), store US$63.98.
  - Crop Pullover Hoody Women's L: ours US$44.38, store US$36.00.
- Smartwool Hike Classic Second Cut Ankle Socks, L (hiking, smartwool.com): sold out now.

## Race lists (5 compared with the race's own current page)
- Sinister 7 (sinistersports.ca/sinister7/rules_gear + race page): PASS.
  - 8 suggested lines, headlamp after 8 pm, bib + chip.
  - The race calls the bib and chip "(mandatory)". We show them as "Provided", and the top note says the must-haves are what the race hands out. OK.
  - Distances (100M/50M/50K/Half) and date July 10-11, 2027 match.
- Moose Mountain (lewistonultraevents.com): PASS.
  - Jacket mandatory 29/42/50 km, the 10 highly-recommended lines, cupless, Aug 21, 2027.
  - Optional: the page says "Poles are permitted" (rules section). Not on our list, while Canmore shows poles as Allowed.
- Canmore 25K & Ultra (5peaks.com/canmoreultra): PASS.
  - Bear spray + 1 L = M, pockets/belt/vest = suggested, poles = optional, June 5, 2027.
  - Note: the page also puts "Bear Spray" under "Optional Gear" (the race contradicts itself). Our M follows its "Mandatory Gear" block.
- Lavaredo (lavaredo.utmb.world): PASS. Every line, level and distance matches, including no headlamp on the 50K, no poles on the 20K, and the 10K's recommended items.
- UTMB Mont-Blanc: PROBLEM (wording/structure).
  - The page still shows the 2026 image (MATERIEL_OBLIGATIORE_2026_EN). All basic-kit lines, levels and the 7 races match, including OCC "1 torch" and ETC/YCC food "recommended".
  - (a) The race publishes ONE "Additional list (may be activated depending on weather conditions)" of 12 items. We split it into a "Bad-weather kit" and a "Hot-weather kit": that grouping and those names are ours, not theirs. Spec: one kit named like the race's list.
  - (b) "Other recommended elements" has 8 lines. We list 3 (poles, power bank, bowl). Missing: Vaseline or anti-heat cream; knife or scissors; sewing kit / spare laces / repair kits; GPS watch; at least €20 cash.
  - (c) Additional item 11 "Sturdy, closed trail running shoes" is not shown as part of that list.
  - Where: scraper/race_pages.py RACES["utmb-mont-blanc"] `kits` + items.
