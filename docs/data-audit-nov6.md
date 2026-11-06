# Data audit, night of Nov 5-6, 2026 (live site, sale.json + sale-us.json updated 05:19 UTC Nov 6; last store read 23:41 UTC Nov 5)

RESULT: PROBLEMS. Every price checked was right (15 of 15). 4 of the 15 had a size, category or name problem. The whole-file scans found 6 more problems. Worst first under "Bugs for backend".

## How I checked
- Files: sale.json (9,444 items, Canada), sale-us.json (10,945, USA). deals*.json not read (robots-disallowed).
- Stores: only ones not sampled on Nov 4 or Nov 5: Boréal Running, Bushtukah, Le Coureur, The Trail Runner Store, Gord's, 33-off, BlackToe, Foveo, The Last Hunt, The Runner's Shop (CA); Sports Basement, Runners Plus, Performance Running, The Running Well Store, Playmakers (US). Categories: shoes 8, tops 1, bottoms 2, headwear 1, gear 2, packs 1.
- How: user agent "TheGearFoxBot/1.0 (+https://thegearfox.com/about.html)", robots.txt read first (TheGearFoxBot and ClaudeBot rules), 3 s between requests, at most 2 product pages per store. Shopify: the product's .js (Canadian cookies for CA shops, none for US shops). Last Hunt: the product page's JSON-LD + stock data. Gord's (WooCommerce): the page's variation data. Playmakers: the product page's JSON-LD (its .js answers 404, see bug 8).
- US prices: sale-us.json stores CAD; compared as CAD / 1.3989 (the file's fx).
- No 403, 429 or captcha anywhere. Nothing skipped.

| # | Item | Store | Ours | Store page | Verdict |
|---|---|---|---|---|---|
| 1 | Nike Zoomx Vaporfly NEXT% 3 OLY - Women's, 9 | lecoureur.com | $218.97, was $364.95, size key "9~N" (narrow, hidden on the site) | "900 / 9.0 / B" $218.97 / $364.95, in stock. Women's B = regular width | Price right. SIZE WRONG: a regular women's shoe is filed as narrow, so nobody sees it (bug 1) |
| 2 | Black Diamond Circuit 2 Shoes - Women's - FINAL SALE, 6.5 | foveo.run | $39.97, was $149.95, shoes/daily | $39.97 / $149.95, in stock; store's product type "Lifestyle", tags "lifestyle" | Price right. CATEGORY WRONG (lifestyle shoe as a running shoe) + "FINAL SALE" in the name (bug 4) |
| 3 | Merrell Accentor Sport 3 - Men's, 7 | 33-off.com | $113.90, was $170 | "Men's Merrell Accentor Sport 3 GORE-TEX® Black" 7: $113.90 / $170, in stock | Price right. NAME WRONG: GORE-TEX dropped (bug 5) |
| 4 | NB 880 V15 - C15 Pearl Grey - Women's (wide card), 7.5 | performancerunning.com | US$114.99, was US$150 | "WOMEN'S 880 V15 - WIDE D - C15 PEARL GREY" 7.5: $114.99 / $150 | Price + width right. NAME: colour code in the name (bug 3) |
| 5 | Brooks Shield Hybrid Jacket 3.0 - Men's, S | therunnersshop.com | $149, was $180 | "Brooks Men's Shield Hybrid Jacket 3.0" Small: $149 / $180, in stock (the web address says "womens", the product is men's: we are right) | right |
| 6 | Mizuno Alpha Eco 7" 2-in-1 Shorts - Men's, XL | borealrunning.com | $39.95, was $79.95, final sale | XL $39.95 / $79.95, in stock, tagged final-sale | right |
| 7 | Arc'teryx Gamma 5 Panel Cap, Small-Medium | bushtukah.com | $39, was $59.99 | same, in stock | right |
| 8 | Saucony Triumph Tight - Women's, XS | blacktoerunning.com | $100, was $170 | Black / Extra Small $100 / $170, in stock | right |
| 9 | goodr The OGs - These Shades Are Still Trash | trailrunnerstore.com | $35, was $45 | same, in stock | right |
| 10 | Nathan Pinnacle Breeze Hydration Race Vest 4L, 2XL | thelasthunt.com | $94.39, was $159.99 | Electric Blue XXL $94.39 CAD, InStock, list $159.99 | right |
| 11 | Hoka Skyward X - Men's, 10 | gordsrunningstore.com | $169.95, was $279.95 | cosmic-grey-silver / 10 / D: $169.95 / $279.95, in stock | right |
| 12 | ASICS GEL-Nimbus 28 - Men's, 7 | sportsbasement.com | US$129.95, was US$170 | "Men's Gel Nimbus 28" 7: $129.95 / $170, in stock (web address says nimbus-29; title is 28: we are right) | right |
| 13 | Puma Velocity Nitro 3 - Men's, 9 | runnersplus.com | US$101.25, was US$135 | "Men's Puma Velocity Nitro 3" 9: $101.25 / $135 (address says nitro-4; title is 3) | right |
| 14 | Hoka Clifton 10 - Women's (wide card), 6.5 | therunningwellstore.com | US$123.95, was US$154.95 | "HOKA WOMEN'S CLIFTON 10 WIDE" 6.5: $123.95 / $154.95, in stock | right (card is w=true, so the plain 6.5 counts as wide) |
| 15 | Amphipod Versa-Light Max Headlamp | playmakers.com | US$35.99, was US$45 | JSON-LD price 35.99 USD, list 45.0, InStock | right |

Count: 15 checked, 15 prices right, 11 fully right, 4 with a size/category/name problem, 0 skipped.

## Whole-file scans
- Duplicate cards (same brand + name + gender + ships-from + wide + group): 0 on both sides. Same name, regular vs wide: 7 CA / 61 US pairs (by design). Same name in two groups: 3 US (Confluence, see bug 6).
  Near-duplicates the exact check misses: Frontrunners' colourway names (bug 2), PR Run & Walk style codes and Performance Running colour codes (bug 3).
- Discounts over 70%: 394 CA (SVP 286, Running Room 31, Boréal 25, Last Hunt 13), 170 US (REI 85, Fit2Run 35, Stance 15). SVP's were checked on Nov 4/5 and matched. One looks wrong (bug 7).
- sortcheck.py on both files: 4 hits, all fine (Smartwool "Snowed In Sweater" crew = a sock; REI "Short Coat" / "Short Cardigan" / "Capris" are where they belong).
- Nov 5 follow-up: Stance PEAKS SS is now under tops (fixed). REI swimwear down from 109 to 4 rashguards (one, Free Fly "Pinnacle Rashguard", is under packs). REI ski/snow and bike clothing still on the US running side (bug 6).

## Bugs for backend (worst first)

1. Le Coureur: every women's shoe in regular width (B) is filed as NARROW, so the site hides it.
   - Where: sale.json, lecoureur.com: 436 women's sale sizes keyed "~N"; 15 women's cards have ONLY narrow sizes, so they never show to anyone. Example: Nike Zoomx Vaporfly NEXT% 3 OLY - Women's (https://www.lecoureur.com/products/nike-w-zoomx-vaporfly-next-3-oly), Adizero Adios 9 Running Shoes - Women's (6, 7, 7.5, 8.5, 9 all "~N").
   - Evidence: store options Couleur / Taille / Largeur, variant "900 / 9.0 / B", title "NIKE ZOOMX VAPORFLY NEXT% 3 OLY - FEMME", tag "largeur-b". Ours: "9~N".
   - Cause: scraper/scrape.py `width_word(w, title)` decides women's vs men's with `\bwom[ae]n` on the title only. Le Coureur's titles say "FEMME", so B is read as men's B = Narrow.
   - Fix: in `width_word`, treat the product as women's when the title, product_type or tags say women/womens/femme/femmes/W prefix (or pass in the gender the reader already worked out). Re-check after the fix: 0 women's "~N" sizes at lecoureur.com except real 2A/AA. Also look at Brainsport (16 women's ~N) and the US: Fit2Run 455 "~N" sizes on cards with no gender, Athletic Annex 77 women's.

2. Frontrunners: Brooks shoes keep the colourway in the name, so every colour is its own card, apart from the other stores' card.
   - Where: sale.json, frontrunners.ca, 26 shoe cards. Example: "Ghost Trail Atlantic Deep/Black/Green - Men's", "Ghost Trail Ebony/Black/Clove - Men's", "Ghost Trail Gray/Gray/Blackened Pearl - Men's" = 3 cards for one shoe; "Ghost Max 3 Navy/Peacoat/Clearwater - Women's" sits beside the real "Ghost Max 3 - Women's" card.
   - Evidence: store title "W Brooks Adrenaline GTS 24 Alloy/White/Zephyr" (options Width / Size only, no colour option). Prices are right (checked: 2A / 7.5 $143.96 / $179.95).
   - Cause: `drop_colour` needs a colour option; the " - Colour/Colour" rule needs a dash. Neither fires.
   - Fix: for Frontrunners (or any GENDER_PREFIX_STORES shoe), cut a trailing run of words joined by "/" after the model number. Check: 0 Frontrunners shoe names with "/".

3. Store codes and colour codes in names (each colour its own card).
   - PR Run & Walk (US): 40 names with Brooks style codes, e.g. "Journey 5\" Short - 211542-001 - Men's" and "Journey 5\" Short - 211542-068 - Men's" (two cards, one product line).
   - Performance Running (US): 9 with "Clearance" and 11 with colour codes: "880 V15 - C15 Pearl Grey - Women's", "GO High Rise 7/8 Tight - 509 DAYBREAK/BLACK - Clearance - Women's", "Drifit ADV Aeroswift 4\" Short - 010 Black - Men's", "Solar Glide 5 Clearance - Men's".
   - Others: La Boutique du Lac "Aero Glide 4 F/W - Solde" (3; the F/W should also become "- Women's"), Farm to Feet "… Warehouse Sale" (3, both sides), Foveo "… - FINAL SALE", Running Room "- RN2387", "- RACE#ATTACH", "- 7710" (6, still there from Nov 5), District Vision "Layered Trail Shorts, Black/Dove" (5 per side).
   - Fix: a name rule after the store tidies: drop " - \d{6}-\d{3}", " - [A-Z]?\d{2,3} <Colour words>", "Clearance", "Solde", "Warehouse Sale", "FINAL SALE" (keep the final-sale flag `fs`), ", Colour/Colour" at the end; "F/W" / "H/M" -> gender. Check: none of the patterns left in either file.

4. Lifestyle shoes on the running side: Foveo's Black Diamond "Circuit 2 Shoes - Women's - FINAL SALE" (73% off) is filed shoes/daily; the store calls it "Lifestyle". Same family: Merrell "Jungle Moc", "Antora 3 Thermo Moc", "Speedarc Matis Mid GORE-TEX Hiking Sneakers" (REI, shoes), "Wrapt Sneaker Women" (distancerunwear.com), Roll Recovery slides under gear.
   - Fix: drop shoes whose Shopify product_type/tags say lifestyle/casual (Foveo), and names with moc/moccasin/sneaker(s) unless "Trail Running Sneaker" (Merrell Morphaxis is a trail runner).

5. 33-off drops GORE-TEX and Mid from shoe names, so waterproof/mid shoes look like the plain ones.
   - Evidence: "Men's Merrell Accentor Sport 3 GORE-TEX® Black" -> ours "Accentor Sport 3 - Men's"; "womens-salomon-x-ultra-4-mid-gtx" -> ours "X Ultra 4 - Women's". Price right ($113.90 / $170).
   - Cause: scrape.py 33off branch (~line 3837): `ws[k].upper().strip(",") in OFF33_KEEP`: "GORE-TEX®" keeps its ® so it misses; "MID" isn't in OFF33_KEEP, so the cut stops before "Mid GTX".
   - Fix: strip ®/™ before the lookup; add MID, LOW, GTX variants to OFF33_KEEP. Altitude has 3 similar (Vomero 18, Aero Blaze 3 GTX addresses, names without GTX): worth a look.

6. US running side still carries REI ski/snow and bike clothing, and Confluence's lifestyle clothes in odd groups.
   - REI: 148 snow/ski pants and bibs under bottoms (e.g. Arc'teryx "Fissile Insulated Snow Pants - Men's", 686 "Smarty 3-in-1 Cargo Snow Pants"), 5 tops, 2 gloves; 266 bike items (137 tops, 100 bottoms, 14 gloves, 9 socks: Canari "Arrow Bike Shorts"); Klymit "Horizon Backpacking Blanket" (packs), Rumpl "The Fleece Puffy Blanket" (tops), Free Fly "Pinnacle Rashguard" (packs).
   - Confluence: dresses and a cardigan under bras/bottoms: Tribal "Cable Knit Collared Cardigan - Women's" (bras), Ivko "Retro Motif Printed Viscose Dress" (bottoms), Krimson Klover "Piper Dress" (bottoms); same-name cards in two groups: CEP "Ultralight - Women's" (tops + bottoms), Tribal "Flatten It - Women's" (bottoms + bras), Sno Skins "Viscose Prints - Women's" (bras + tops). Gazelle: The Normal Brand "Lucia Knit Midi Dress" (bottoms, 2 colour cards).
   - Fix: running side drops snow/ski pants/bibs, bike/cycling clothing (keep running "bike shorts" = short tights? decide: Hoka "Elaro 5 in Bike Shorts" is running), blankets, dresses, cardigans, in every source (REI/Backcountry grab saves included). Confluence: use the product_type for the group; when the name has no garment word, leave it out.

7. A price that looks wrong, not checkable: The North Face "Snoga Pants - Women's", REI (US), US$163.83, "was" US$750 (CAD $229.18 / $1,049.17). A $750 regular for a pant is far above that brand's pants elsewhere in the file. REI blocks robots, so not opened. Fix: the gift page's rule (regular price over 1.8x the brand's median for that kind = out) applied to sale cards, or check the REI save for this row.

8. (low) Playmakers moved to a headless Shopify front: every product .js answers 404 while the page is fine. livecheck `_shopify` then returns None (can't tell), so Playmakers deals can never be confirmed for posts/featured checks. The page carries JSON-LD offers (price, ListPrice, availability): read those when .js 404s (same for The Feed).

## Notes (not bugs)
- Several US Shopify handles don't match the product (sportsbasement "nimbus-29" = Nimbus 28, runnersplus "velocity-nitro-4" = Nitro 3, therunnersshop "brooks-womens-shield…-copy" = men's). We follow the title, which is right: keep it that way (url_gender must not override a title that names the gender).
- RunFree stores still listed in "stores" with Oct 31 dates, but none of their items are in either file (KEEP_HOURS works).

# Nov 6 morning (live sale.json + sale-us.json updated 11:42 UTC Nov 6)

RESULT: PROBLEMS. 18 products checked: 18 prices right (price, regular, size in stock, currency), 4 with a size or category problem, all at the new store The Run House. 0 skipped (no 403/429/captcha). Race list Iron Legs: 2 problems (wording). Yesterday's 8 bugs not repeated here.

## How I checked
- Same method as last night: TheGearFoxBot UA, robots.txt first (TheGearFoxBot + ClaudeBot), 3 s between requests, Shopify .js (Canadian cookies for CA shops). US: sale-us.json CAD / 1.3989. Run House: 7 product pages (cap 20).
- Featured = top-scoring shoes (featured_check.py score, 5+ sale sizes). Deepest = highest % off.
- New stores since Nov 4 (git log): Speedland (runspeedland.com), The Run House (therunhouse.com), Hettas (hettas.com). Speedland and Hettas have 0 sale items today (nothing to check on sale.json; deals*.json not read). Speedland shoes at Pacers checked instead.

| # | Item | Store | Ours | Store page | Verdict |
|---|---|---|---|---|---|
| 1 | NB FuelCell SuperComp LD-X - Unisex, M:6 (featured #1 CA) | lecoureurnordique.ca | $50, was $229.99 | "6.0 H / 7.5 F / Régulière" $50 / $229.99, in stock | right |
| 2 | Saucony Endorphin Elite - Women's, 5 | borealrunning.com | $99.95, was $349.95 | ViziBlue / 5 / B $99.95 / $349.95, in stock | right |
| 3 | adidas Megaride - Women's, 5 | svpsports.ca | $59.99, was $229.99 | Blk/Slv / W5 $59.99 / $229.99, in stock | right |
| 4 | Naked T/R Trail - Unisex, M:6 | trailrunnerstore.com | $76, was $247 | M6 / W7 $76 / $247, in stock | right |
| 5 | Naked T/r Trail, M:6 (featured #1 US) | nakedsportsinnovations.com (USD shop) | US$45, was US$180 | Men's6/Women's7 $45 / $180, in stock | right |
| 6 | Nike Alphafly 3 - Women's, M:3.5/W:5 | gazellesports.com | US$134.99, was US$285 | M3.5/W5 $134.99 / $285, in stock | right |
| 7 | ASICS Studio Luxe Headband (deepest CA, 85%) | ca.shop.runningroom.com | $3, was $19.99 | $3.00 / $19.99 CAD, InStock | right |
| 8 | ASICS Wild Camo Sprinter Tights - Women's, XS (85%) | svpsports.ca | $9.99, was $64.99 | Pur/Wht / XS $9.99 / $64.99, in stock | right |
| 9 | Stance PEAKS SS, XL (deepest US, 84%) | stance.com | US$4.70, was US$29 | SEA BLUE / XL $4.70 / $29, in stock | right |
| 10 | Falke RU3 Comfort Invisible Socks, 35-36 (83%) | fit2run.com | US$2.98, was US$18 | White - Mix / 35 - 36 $2.98 / $18, in stock | right |
| 11 | Speedland GL:PDX - Unisex, M:5 | pacersrunning.com | US$99.95, was US$250 | M5/W6.5 / D $99.95 / $250, in stock | right (typed daily; store tags Trail Running: low) |
| 12 | Saucony Endorphin Trainer - Men's, 8.5 | therunhouse.com | US$134.95, was US$180 | "Men's Endorphin Trainer" 8.5 $134.95 / $180 (handle says endorphin-pro-4: title wins, right) | right |
| 13 | Saucony Endorphin Trainer - Women's, 6 | therunhouse.com | US$134.95, was US$180 | "Women's Endorphin Trainer" 6 (handle says mens) | right |
| 14 | Root'd Essential Prenatal Nutrition + Electrolytes, 30 Pack | therunhouse.com | US$54.99, was US$59.99 | $54.99 / $59.99 | price right (a prenatal vitamin under Nutrition: low, see bug 4) |
| 15 | Hoka Clifton 10 - Women's, 11 | therunhouse.com | US$103.95, was US$155, REGULAR width | "HOKA Women's Clifton 10 - WHITE / CIELO BLUE (Wide)" 11 $103.95 / $155 | price right, SIZE WRONG (wide shown as regular, bug 1) |
| 16 | NB Fresh Foam X 880 v15 GTX - Men's, 7 | therunhouse.com | US$174.99, regular width | "New Balance Mens 880v15 Gore-tex® - BLACK (Wide)", tag "wide" | SIZE WRONG (bug 1) |
| 17 | Merrell Moab 3 Hiking Shoes - Men's, 7 | therunhouse.com | US$145, regular width | "Men's Merrell Moab 3 - Walnut Wide" | SIZE WRONG (bug 1) |
| 18 | Diadora Troffeo 2 AF PKL - (101.179105-C9453) - Women's, 7.5 | therunhouse.com | US$60, was US$105, shoes/daily | $60 / $105; tags "pickleball", "tennis" | price right, CATEGORY WRONG (bug 2) |

## Race list: Iron Legs Mountain Races (/races/iron-legs/), vs ironlegs.ca /100km, /50mile, /partners (60 km), /20km (25 km), /relay, home (read Nov 6)
- Date August 7, 2027: matches. Mandatory per distance (headlamp, jacket M except 25K = R, water, bear spray M except relay = L, bib = P): matches. Suggested lines and the 25K's missing sunglasses/sunscreen: match.
- PROBLEM A (wording): "Quick answers" says the 25 km night race needs "Hydration pack or bottles: 1.5 L or more". The race's /20km page: "Hydration pack or water bottles - min. 1L". The note on the line says 1 L, but the FAQ answer (race_pages.py `qList`/`aList`) uses the line's name only.
- PROBLEM B (added line): "Reusable cup" shown as Recommended on every distance + FAQ "No. The aid stations have no cups". None of the 6 pages read today mention cups (our RACES comment says "Every aid station is cupless", source not on the current site; maybe the 2026 Racer Guide).

## Bugs for backend (worst first)
1. The Run House (US): shoes whose width is only in the TITLE ("(Wide)", "Walnut Wide") are filed as regular width, so regular-width shoppers see a wide shoe at that price. 7 cards today: Hoka Clifton 10 W (2 colours), Merrell Moab 3 M/W (3), NB 880v15 GTX M/W (2). Evidence: titles above, tags "wide" / "cw-group:...--wide"; ours: size keys without "~W", card w=false. Products with a width word the reader catches (ASICS "wide" items) are fine. Cause: Shopify reader width comes from the option (`width_word`, scrape.py ~2154) and these products have only a Size option. Fix: in the Shopify reader, a title with "Wide"/"(Wide)"/"Extra Wide" (or tag "wide", cw-group ending "--wide") = every size "~W"; then move "Wide" out of the name so it merges with the wide card. Check: 0 therunhouse offers whose URL or title says wide without "~W".
2. The Run House: Diadora "Troffeo 2 AF PKL" (2 cards, women's) = pickleball/tennis shoes on the running side, with the style code in the name. Store tags "pickleball", "tennis". Fix: COURT_SHOE also catches "PKL", "pickleball", and Shopify tags pickleball/tennis/court; the code "(101.179105-C9453)" falls under yesterday's bug 3 rule.
3. Iron Legs FAQ (Problem A): FAQ answers should use the distance's own amount when a line has a per-distance note (25 km: "1 L or more"); simplest: an `faq` text per distance in RACES for the water line. Fix wording only after re-reading /20km.
4. Iron Legs cup line (Problem B): keep "aid stations are cupless" only if the race's own current material says it (name the source); otherwise drop the "Reusable cup" R line and the cup FAQ. If it comes from the 2026 guide, show it as a note, not "Recommended by the race".
5. (low) The Run House carries Root'd prenatal/daily vitamins ("Essential Prenatal Nutrition", "Advanced Daily Nutrition formulated for her", 6 cards) with pack sizes and "Mom & Dad Bundle" as sizes. Prices right; not running fuel. Fix: drop "prenatal"/"daily nutrition"/multivitamin names, or keep the gels collection only.
