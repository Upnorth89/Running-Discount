# Data audit, Thu Nov 5, 2026 (live site, files updated 11:48 UTC Nov 5)

RESULT: PROBLEMS (prices all right; 2 category/junk problems, 1 small race-list wording change). Worst first.

## How I checked
- Files: sale.json (9,510 items), sale-us.json (11,034), sale-hike.json (4,702, only to follow up yesterday's hiking items). deals*.json not read.
- Read politely: UA "TheGearFoxBot/1.0 (+https://thegearfox.com/about.html)", robots.txt read first, 2-3 s between requests, at most 3 pages per store.
- Sample: 15 deals = 6 top featured (featured_check score, 3 CA + 3 US), 4 deepest discounts, 2 Running Room (their Nov 4 23:41 read is what's live), 3 from night copies (Saucony, Fleet Feet, Running Free).
- Result: 14 checked on the store's own page, 14 right (price, regular, size in stock, currency, colour/gender). 1 not checked: runningfree.com answers "only available to visitors in Canada" to this sandbox's IP (a country wall, not a bot block; nothing tried around it).
- No 403/429/captcha anywhere.

| # | Item | Store | Ours | Store page | OK |
|---|---|---|---|---|---|
| 1 | Icebug Pace3 BUGrip GTX M, size 15 (CA #1 featured) | brainsport.ca | $49.99, was $260 | Black / 15: $49.99, compare $260, available (variant 45785149767724; the card link uses it) | yes (see note) |
| 2 | NB FuelCell SuperComp LD-X, M6 | lecoureurnordique.ca | $50, was $229.99 | "6.0 H / 7.5 F": $50 / $229.99, in stock | yes |
| 3 | adidas Equipment Takumi Sen, M4.5 | svpsports.ca | $59.99, was $239.99 | M4.5: $59.99 / $239.99 | yes |
| 4 | NB LD5Kv8 spike W10 (US #1) | gazellesports.com | US$19.99, was US$119.95 | same | yes |
| 5 | Naked T/r, M6 | nakedsportsinnovations.com | US$45, was US$180 | Men's6/Women's7: $45 / $180 (final sale) | yes |
| 6 | ASICS Gun Lap 2, M11.5 | fit2run.com | US$19.95, was US$99.95 | "11.5 M / 13 W": same | yes |
| 7 | 2XU Form Soft Touch Hi-Rise 4" Shorts, 2XL | ca.2xu.com | $10, was $70 | XXL: $10 / $70 | yes |
| 8 | ASICS Road Balance Tight W, S | svpsports.ca | $14.99, was $99.99 | same | yes |
| 9 | Stance PEAKS SS, XL | stance.com | US$4.70, was US$29 | same | price yes, CATEGORY no (problem 2) |
| 10 | NB Accelerate 5" Short M, L | fit2run.com | US$4.98, was US$30 | same | yes |
| 11 | Fuel Belt Race Number Attachment | ca.shop.runningroom.com | $1, was $6.99 | finalPrice 1 / oldPrice 6.99, In stock | yes |
| 12 | ASICS Studio Luxe Headband | ca.shop.runningroom.com | $3, was $19.99 | finalPrice 3 / oldPrice 19.99, In stock | yes |
| 13 | Saucony Cohesion 18 M, 12.5/13/14 | saucony.com/CA | $65.95, was $110 | C$65.95 / C$110; 12.5, 13, 14 IN_STOCK | yes |
| 14 | On Cloud X 4 M, 10/10.5/11.5/13 | fleetfeet.com | US$120, was US$160 | Black/Eclipse + Shadow/Apollo $120 / $160, those sizes in stock | yes |
| 15 | Salomon Speedcross 6 W 10 Wide | runningfree.com | $134.88, was $179.99 | not readable (Canada-only wall) | n/a |

Running Room: both deals still right on the Nov 4 afternoon data.

## 1. US running side: 109 REI swimsuits, plus yesterday's REI non-running items, still on the site
- Where: sale-us.json, rei.com. 109 swim items: 58 under bottoms, 51 under tops ("Wavebound Bikini Swimsuit Bottoms - Women's", "La Jolla Tankini Swimsuit Top", "Newport Trunk 4.5\" Swimsuit Bottoms - Men's", "Bottom Turn Swimsuit Top").
- Also still there (yesterday's item 4, REI part, not fixed): crankbrothers "Mallet Trail Speed Lace Clip-In Shoes" (gear), evolv "Elektra Lace Climbing Shoes", Black Diamond "JetForce Pro 25 L Avalanche Airbag Pack" (packs), Dakine "Low Roller Snowboard Bag", Gear Aid "Snap Bar Repair Buckle", Klymit "Homestead Cabin Fleece Comforter" (tops/layer).
- Evidence: names in sale-us.json; offers e.g. https://www.rei.com/product/245028/crankbrothers-mallet-trail-speed-lace-clip-in-shoes-mens , https://www.rei.com/product/224614/black-diamond-jetforce-pro-25-l-avalanche-airbag-pack
- Likely cause: REI arrives through the catalog/saved-page path; there is no swimwear rule anywhere, and the Nov 4 drops (76b499c, in `tidy_shoes`) don't reach these. BIKE_SHOE_BRANDS only acts on items filed as shoes.
- Spec: drop names matching swimsuit|swim trunk|bikini|tankini|rash guard|boardshort in every group and side; drop clip-in/climbing shoes, avalanche/airbag packs, snowboard bags, comforters/blankets (not space/emergency blankets) in every group, for every source (catalog, saved pages, grab saves included).

## 2. Nov 4 category fixes did not take effect for these items
- Socks: Smartwool "Active Mesh Polo - Men's" (both sides, smartwool.com); Stance "PEAKS SS" (US): stance.com tags it "Tshirts", "Graphic Tees & Hoodies", "Mens Shirts & Tees" (https://stance.com/products/peaks-ss-sea-blue). Shown under Socks at -84% (the US side's deepest discount).
- Bottoms: Marmot "Chelsea Down Short Coat - Women's" (REI), "BGA Tahoe Sun Golf Polo" (Backcountry), Tribal "Split Neck Striped Sweater - Women's" (confluencerunning.com).
- Tops: Smartwool "Second Cut Fleece Slipper(s)" (REI, Playmakers).
- Packs: New Balance 900v4 / 700v5 XC Spikes (prrunandwalk.com).
- Likely cause: 76b499c's rules (`generic_group` socks regex has polo but not "SS"/"tee" tags; the jacket/coat -> tops rule sits in `tidy_shoes`) are not reaching REI/Backcountry grab offers, and a later merge step (sock-brand "odd one out" rule) probably re-files the Smartwool polo. Spec: for sock brands use the Shopify product_type/tags (Tshirts, Apparel, Tops) before the sock default; run the coat/jacket/polo/sweater/slipper/spike rules after the merge on every offer source.

## 3. Race list: Racing Dusk 20 Miler, wording (low)
- Compared every line with https://www.ironlegs.ca/racing-dusk (read Nov 5): all 8 lines, levels and the date (19 December 2026, 10am start, headlamp only if the last loop starts after 2pm) match. Bib = Provided (the race lists it under mandatory; same treatment as Sinister 7).
- Wording we changed: the race says "Toque"; our EN line says "Tuque". Spec: EN "Toque" (FR "Tuque" is fine). Where: scraper/race_pages.py RACES["racing-dusk"] item "tuque".
- Side note: the race page still carries 2025 prices/deadlines (theirs, not ours).

## Small notes
- Icebug Pace3 BUGrip GTX (CA #1 featured): the $49.99 is one size (15) in colour Black; the card photo is the Black/Petroleum colour ($199.99). Price and link are right; the photo isn't the colour on sale.
- Running Room names still carry short codes: "Race Number Attachment - RACE#ATTACH", "Studio Luxe Headband - RN2387".
- Hiking: wildrock.net "Silent Traction - Large Bow Hood Cover For Thresher & Atak 140" (kayak part) still under gear.

## Yesterday's problems (docs/data-audit-nov4.md)
- FIXED: LMNT wholesale (0 "wholesale" offers, no INSIDER bundle); adidas NMD S1 gone and SVP's Casual/Originals sneakers out (Kaptir 4.0 / Lite Racer Adapt 7.0 remain but SVP tags them Running: fine); Gear Trade 906 -> 29 hiking items, no used/like-new/sample names on any side; Gazelle soccer kit 0; Tyrol 0; Powslayer 0; OHM 0; coaching plans 0; PR Run & Walk broken names 0; "OS"-only shoes 0; Hurricane 25 duplicates gone (only regular + wide); Brooks/Craft clothing vests out of packs; UTMB Mont-Blanc now one "Additional list" + all 8 recommended lines (live page checked).
- NOT FIXED: REI non-running items (problem 1); socks/bottoms/tops/packs miscategories (problem 2); wildrock kayak part.
