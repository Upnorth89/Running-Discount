# Super Shoe Sunday, Sun Nov 8, 2026: the 6 shoes (format 1, docs/social-formats.md)
Social producer, night of Nov 5. Draft: nothing posted. Bastien makes the video. Before he posts: designer check (frames), compliance
check (words), and **every price re-checked on the store's own page Sunday morning** (commands at the bottom).

## How they were picked (data read Nov 5)
- Live files: https://thegearfox.com/sale.json + sale-us.json (updated 2026-11-05 06:34 UTC, n_stores 150, USD fx 1.3961).
- Price history: `git show origin/history:prices.jsonl` (last write Nov 4 23:55 UTC).
- Rule (tools/social_post.py `picks()`, the Bluesky/Pinterest rule): best price a week ago vs today, 10% or $10 and >= $5, lower than 97%
  of the week-ago price, 5+ sizes at the shown price, has a shoe page; US prices in US$ against the "us|" history. Then by hand: well-known
  models, one per brand across all 6, no spikes, 3 Canada + 3 USA, 3 women's + 3 men's, road + trail + race.
- Checked Nov 5 (sandbox): every row passes tools/post_check.py on its live shoe page ("OK", price + regular + % + 5+ sizes) and
  livecheck.still_on_sale = True on the store's own page (CAD for Canada, USD for USA).

## The 6 rows (order = video order: Canada first, then USA)
| # | Side | Brand + model | Gender | Kind | Regular | Sale | % off | Sizes at that price | Store | History (date it dropped) | Shoe page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CA | On Cloudboom Strike | Women's | race | $359.99 | $180.00 | −50% | 5 (5.5, 6, 7, 9, 9.5) | La Boutique du Lac | $269.99 since Oct 3 -> $180.00 Nov 1 | https://thegearfox.com/shoes/on-cloudboom-strike/ |
| 2 | CA | New Balance FuelCell Rebel v5 | Men's | road | $180.00 | $70.00 | −61% | 5 (8, 8.5, 9, 10, 10.5) | JD Sports | $143.00 a week before -> $70.00 Oct 31 ($90 on Nov 1 only, $70 again since Nov 2) | https://thegearfox.com/shoes/new-balance-fuelcell-rebel-v5/ |
| 3 | CA | Saucony Xodus Ultra 4 | Men's | trail | $189.99 | $132.99 | −30% | 10 (7-10, 11, 11.5, 12) | SAIL | $157.50 Oct 28 -> $132.99 Nov 2 (lowest since Oct 2) | https://thegearfox.com/shoes/saucony-xodus-ultra-4/ |
| 4 | US | ASICS Gel-Nimbus 28 | Women's | road | US$169.95 | US$125.00 | −26% | 9 (7.5-12) | Scranton Running Company | $169.95 Oct 29 -> $136 Oct 30 -> $125.00 Nov 2 | https://thegearfox.com/us/shoes/asics-gel-nimbus-28/ |
| 5 | US | adidas Adizero Evo SL ATR | Women's | trail | US$160.00 | US$128.00 | −20% | 7 (7-10) | Heartbreak Hill Running Co. | $159.95 since Oct 17 -> $128.00 Nov 1 | https://thegearfox.com/us/shoes/adidas-adizero-evo-sl-atr/ |
| 6 | US | Salomon Genesis | Men's | trail | US$150.00 | US$89.95 | −40% | 8 (8-10, 12, 13, 14) | Mountain Running Company | $99.95 since Oct 6 -> $89.95 Nov 1 | https://thegearfox.com/us/shoes/salomon-genesis/ |

Store pages (for the product photo and Sunday's check; never commit store photos):
1. https://laboutiquedulac.com/products/on-cloudboom-strike-f-w?variant=41379889053742
2. https://www.jdsports.ca/products/new-balance-fuelcell-rebel-v5-white-grey?variant=44056788238518
3. https://www.sail.ca/en-ca/products/saucony-xodus-ultra-4-trail-running-shoes-men-s-1479153?variant=56879066349728
4. https://scrantonrunning.com/products/w-gel-nimbus-28-1012b899?variant=42808788516948
5. https://heartbreakhillrunningcompany.com/products/adidas-adizero-evo-sl-atr-mens-shoes-copy?variant=58951638614176
   (the address says "mens-shoes-copy" but the store's own product title is "Adidas Adizero Evo SL ATR Women's Shoes": checked)
6. https://www.mountainrunningcompany.com/products/salomon-genesis-mens?variant=44681122971876

Small grey line per row (video): "Women's · 5 sizes · La Boutique du Lac" / FR « Femme · 5 pointures · La Boutique du Lac ».
Size 11 (Bastien's size) is in rows 3 and 6 only: don't say "my size" in this video.

## Backups (use only if a row fails Sunday's check; keep one per brand)
| For | Side | Shoe | Regular | Sale | % | Sizes | Store | History | Shoe page |
|---|---|---|---|---|---|---|---|---|---|
| any CA row | CA | Nike Structure 26 (Men's, road) | $180.00 | $126.00 | −30% | 8 (8-12, incl. 11) | BlackToe Running | $179.95 Oct 29 -> $126.00 Nov 1 | https://thegearfox.com/shoes/nike-structure-26/ |
| any US row | US | Brooks Revel Max (Men's, road) | US$120.00 | US$99.95 | −17% | 15 (7-15) | Athletic Annex | $119.95 since Oct 6 -> $99.95 Nov 2 | https://thegearfox.com/us/shoes/brooks-revel-max/ |
| row 4 only (ASICS) | US | ASICS Trabuco Max 5 (Women's, trail) | US$170.00 | US$119.00 | −30% | 6 at Trailhead (7-9.5) | Trailhead Running Supply | $169.95 Oct 9 -> $119.00 Nov 3 | https://thegearfox.com/us/shoes/asics-trabuco-max-5/ |
Store pages: https://www.blacktoerunning.com/products/nike-mens-structure-26?variant=42946401009739 ·
https://www.athleticannex.com/products/m-revel-max-oyster-mushroom-poppy-seed?variant=51491477061919 ·
https://www.trailheadrunningsupply.com/products/womens-trabuco-max-5?variant=49020076818649

Left out on purpose (the rule passed them, the facts didn't hold up):
- Saucony Ride TR2 men's ($79.99 at SVP, −56%): its "week-ago" $180 was a 3-day blip; it sat at $79.99 from Oct 12. Not a new drop.
- Altra Escalante Racer 2 men's (Mountain Running Co.): the regular price jumped $128 -> $145 the same day as the "drop". Unclear.
- Brooks Ghost women's at Boréal ($143.95): the store item is the **Ghost Trail**, filed on the road Ghost page. Data bug -> data-auditor/backend.
- MEC, REI, Backcountry rows (Hoka Zinal 3, On Cloudhorizon 2, Arc'teryx Sylan 2...): their store pages can't be checked by our tools.
- On Cloudultra Pro / Cloudeclipse: On is already row 1.

## Words
**Hook (first second, over the ???):** EN "Guess what these running shoes cost right now." / FR « Devinez combien coûtent ces souliers de course en ce moment. »
**At each reveal (his voice):** the price + the store ("A hundred and eighty at La Boutique du Lac"). He stops before the logo.
Video sub line under the title: "Guess the price · Canada + USA" / FR « Devinez le prix · Canada + É.-U. »

**Caption EN**
Super Shoe Sunday: 6 running shoes whose price dropped between Oct 30 and Nov 2 (our price history). Canada + USA. How many did you guess?

Canada (CAD)
On Cloudboom Strike, women's: $180, regular $359.99 (−50%), 5 sizes, La Boutique du Lac
New Balance FuelCell Rebel v5, men's: $70, regular $180 (−61%), 5 sizes, JD Sports
Saucony Xodus Ultra 4, men's: $132.99, regular $189.99 (−30%), 10 sizes, SAIL

USA (USD)
ASICS Gel-Nimbus 28, women's: $125, regular $169.95 (−26%), 9 sizes, Scranton Running Company
adidas Adizero Evo SL ATR, women's: $128, regular $160 (−20%), 7 sizes, Heartbreak Hill Running Co.
Salomon Genesis, men's: $89.95, regular $150 (−40%), 8 sizes, Mountain Running Company

Prices checked Sunday morning on each store's site. Every size and every store: thegearfox.com
Prices can change: check the store before you buy.
Link in bio.

**Caption FR (Québec)**
Super Shoe Sunday : 6 souliers de course dont le prix a baissé entre le 30 octobre et le 2 novembre (notre historique de prix). Canada + États-Unis. Combien en avez-vous deviné?

Canada ($ CA)
On Cloudboom Strike, femme : 180 $, prix régulier 359,99 $ (−50 %), 5 pointures, La Boutique du Lac
New Balance FuelCell Rebel v5, homme : 70 $, prix régulier 180 $ (−61 %), 5 pointures, JD Sports
Saucony Xodus Ultra 4, homme : 132,99 $, prix régulier 189,99 $ (−30 %), 10 pointures, SAIL

États-Unis ($ US)
ASICS Gel-Nimbus 28, femme : 125 $ US, prix régulier 169,95 $ US (−26 %), 9 pointures, Scranton Running Company
adidas Adizero Evo SL ATR, femme : 128 $ US, prix régulier 160 $ US (−20 %), 7 pointures, Heartbreak Hill Running Co.
Salomon Genesis, homme : 89,95 $ US, prix régulier 150 $ US (−40 %), 8 pointures, Mountain Running Company

Prix vérifiés dimanche matin sur le site de chaque magasin. Toutes les pointures et tous les magasins : thegearfox.com
Les prix peuvent changer : vérifiez sur le site du magasin avant d'acheter.
Lien dans la bio.

If a backup replaces a row, change that line AND the "between Oct 30 and Nov 2" dates (Trabuco Max 5 = Nov 3).
Compliance note: "regular" = the store's own compare-at price as shown on its page; we don't claim the regular price was ever charged.

## Link + what to measure
- Link in bio Sun Nov 8 -> Mon Nov 9: **https://thegearfox.com/?ref=ig-sss-nov8** (the homepage picks Canada or USA by itself; the list pages
  don't link to their other-country twin, and 3 of the rows are US). If he adds a Story: one sticker per country,
  https://thegearfox.com/running-shoes-sale/?ref=ig-sss-nov8 and https://thegearfox.com/us/running-shoes-sale/?ref=ig-sss-nov8.
  Nov 10 the bio goes back to /black-friday/?ref=ig-bio (content calendar).
- Measure (funnel.yml / Monday check-in, ref ig-sss-nov8, Nov 8-15): first visits, % that pick sizes, % that click a store, sign-ups,
  shoe-page views of the 6 slugs. Compare with the last Super Shoe Sunday's ref if it had one (ask Bastien) and with ig-bio. Plus
  Instagram's own: views, 3-s hold, saves, shares, comments with guesses.

## Sunday morning check (before he posts; from GitHub's servers or the sandbox)
```
cd /home/user/Running-Discount && python3 - <<'PY'
import sys; sys.path.insert(0, "scraper"); import livecheck
rows = [("https://laboutiquedulac.com/products/on-cloudboom-strike-f-w?variant=41379889053742", 180.00, "41379889053742", False),
 ("https://www.jdsports.ca/products/new-balance-fuelcell-rebel-v5-white-grey?variant=44056788238518", 70.00, "44056788238518", False),
 ("https://www.sail.ca/en-ca/products/saucony-xodus-ultra-4-trail-running-shoes-men-s-1479153?variant=56879066349728", 132.99, "56879066349728", False),
 ("https://scrantonrunning.com/products/w-gel-nimbus-28-1012b899?variant=42808788516948", 125.00, "42808788516948", True),
 ("https://heartbreakhillrunningcompany.com/products/adidas-adizero-evo-sl-atr-mens-shoes-copy?variant=58951638614176", 128.00, "58951638614176", True),
 ("https://www.mountainrunningcompany.com/products/salomon-genesis-mens?variant=44681122971876", 89.95, "44681122971876", True)]
for u, p, v, us in rows: print(livecheck.still_on_sale(u, p, v, us=us), p, u)
PY
```
Then re-run tools/post_check.py on the 6 lines (the shoe page must still show 5+ sizes at that price) and recount the sizes for the grey lines.
Any False/None = swap in a backup (same day, same checks).
