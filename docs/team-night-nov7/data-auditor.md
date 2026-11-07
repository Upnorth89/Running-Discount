# Data audit, night of Nov 6-7, 2026: Black Friday deal check (live) + "Lowest price we've seen" badges

Checked: /black-friday/live/ and /vendredi-fou/direct/ ("Updated Nov. 6"; sale.json updated 01:10 UTC Nov 7), history branch
prices.jsonl (commit 372ae61, "prices 2026-11-06"), each listed item's store page (TheGearFoxBot UA via scraper/polite.py, robots
obeyed, 4-5 s apart, max 4 pages per store, no 403/429/captcha met). I re-ran bf_live.py's rule on sale.json + history: my count
matches the page (379 real drops), so the numbers below describe exactly what the page does.

## Verdict: PROBLEMS (2 trust bugs in the "Real drops this week" rule, 1 smaller badge bug)

### 1. A price that went UP this week is listed as a "real drop" (worst: it is the exact thing the page promises to catch)
- New Balance FuelCell Rebel v5 (Men's), JD Sports, "↓ $53 this week ... $90.00 CAD ... Was $143.00 before Nov 6".
  Store page (jdsports.ca new-balance-rebel-v5-alkaline-green.js): $90.00, reg $180, sizes 8/9/10/10.5/13 in stock = ours.
  Our own history: Oct 31 $70, Nov 1 $90, Nov 2 $70, Nov 4 $70, Nov 6 $90. So today's $90 is a $20 RISE vs Nov 4, and it was
  never "$143 before Nov 6" (it was $70-90 all week). Same page, both languages.
- 12 of the 379 counted real drops are like this (cheaper earlier this week than today), e.g. Nike Pegasus Premium men's
  ($145.79 Nov 5 -> $190 Nov 6, counted as a drop from the 30-day price), Salomon Aero Blaze 3 men's ($79.94 Nov 4 -> $89.94),
  Ultimate Direction Mountain Vest men's, Brooks Momentum Thermal pants/hoodie/vest, Brooks Cascadia belt.
- Cause: scraper/bf_live.py build(): `prior` only holds prices from today-37 to today-7 (+ the price 7 days ago); changes INSIDE the
  last 7 days are never compared, and `day = since` is the LAST change date (often a small bounce), shown as "Was $X before <day>".
- Spec: a real drop must also be the lowest price of the whole 37 days including this week (today <= every price since today-37,
  i.e. best <= min of all h entries in the window, - 0.01). "Was" = the lowest price before the drop (keep min(prior)), and the date =
  the FIRST day this week the price went under min(prior), not h[-1]. Add a check.py case with the Rebel v5 history above.

### 2. "Lower than any price in the 30 days before" shown for items we have tracked for only 7-8 days
- Outdoor Research Aspire GORE-TEX Pants (Women's), The Last Hunt: "↓ $57.60, Was $203.96 before Nov 6". History starts Oct 29
  (one price, $203.96), then $151.16 Oct 31, $146.36 Nov 4, $148.76 Nov 5, $146.36 Nov 6. The store page shows $146.36 / reg $239.95
  (3 sizes) = ours, but "was $203.96 before Nov 6" is false and we have no 30 days to compare.
- Ultimate Direction Xodus vest (Women's), The Last Hunt: history starts Oct 30 ($212.49), $177.49 Nov 4, $162.49 Nov 6; page says
  "Was $212.49 before Nov 6". Store: $162.49 / reg $249.99 = ours.
- 90 of the 379 counted real drops have under 30 days of history (first seen Oct 20-30).
- Cause: bf_live.py build() has no minimum history length. Spec: require h[0] date <= today-30 (30+ days tracked, same as the
  badge rule `hd >= 30`), else not a real drop (and not in the count).
  Note: the stat "379 real drops this week" goes down once 1 + 2 are fixed; that's the honest number.

### 3. Sale-list cards: "Lowest price we've seen in N days" while another version of the same shoe was cheaper inside N days
- /running-shoes-sale/ list, 54 cards with the badge; 4 have a cheaper version of the same model inside N days:
  Puma Magmax Nitro "35 days, $79.99" (men's was $69.99 14 days ago); New Balance 1080v14 "35 days, $99.99" (men's $93.94 on Nov 4;
  its own shoe page even says "It was $93.94 on Nov 4"); Saucony Cohesion 18 "35 days, $59.99" (women's wide $54.99 yesterday);
  Saucony Endorphin Elite 2 "$148.00" (unisex $147.99 25 days ago: 1 cent).
- Cause: scraper/shoe_pages.py summary() `lowd` = low_days() on the versions AT today's best price only; the card names the model.
  The shoe-page hero badge already caps N with CHEAPER_AGO (Nov 6 fix); the list cards don't. Spec: cap lowd with the same
  all-versions check (every version on that page, both genders/widths on the card, since the card shows no gender), or show nothing.
- The other 50 cards and the 10 shoe pages I opened (Saucony Endorphin Elite, NB SuperComp Trainer v3, Puma Deviate Nitro 3, NNormal
  Kjerag, Hoka Cielo X1 2.0, adidas Adios Pro 4, ASICS Novablast 5, Saucony Guide 18, Salomon S/Lab Pulsar 3, Mizuno Wave Rider 29):
  N matches the history, no cheaper day inside N for the version named.

## Smaller (fix when convenient)
- Hoka Clifton 10 (Women's), Running Room, "Was $189.00 before Nov 4": Running Room's own page shows regular $179.99 (sale $110, both B
  and 2E pages). The $189 is the card's earlier best from another store; the drop is real but $69.99, not $79, vs the store's own tag.
  2 of its "3 sizes" are 2E wide (10~W, 11~W) on the regular-width card. Wording risk only: "Was $X" next to "at <store>" reads as that
  store's old price. Spec idea: "Best price before Nov 4: $189 (any store)".
- Same for "Went up lately": "$159.99 CAD at Vancouver Running Co. / Was $118.97 on Oct 16" (Hoka Bondi 9): the Oct 16 low may have
  been another store (history keeps no store). Reads as if VRC raised its price; our rule says neutral wording. Same fix: "(any store)".
- Running page shows hiking/winter items: AKU Tribute II LTR (Bushtukah product type "Boots"), Merrell Moab Speed 2 GTX, Merrell SpeedARC
  Matis hiking shoes, Keen Voyageur, Kombi leather mittens, Castelli Tri Shorts, under "are these running deals real?". Sorting
  (running sale.json) issue, not bf_live. Name not tidied: "Moab Speed 2 Gore-Tex (Available in Wide Widths)".
- Cents: Gord's Cloudultra Pro reg is $329.95 on its page, we show "Was $329.99"; VRC Bondi 9 is $160.00 on its page, we say $159.99
  at VRC (Altitude has $159.99). Mizuno Rebellion Pro (Strides): we list 6 sizes, 8.5 sold out since (5 now).

## Store checks (store page vs ours) - all prices match unless noted above
| Item | Store | Store page | Ours |
|---|---|---|---|
| AKU Tribute II LTR M | Bushtukah | $144.97/289.95, 8,9,10,10.5,11,11.5 | same, 6 sizes |
| Merrell Moab Speed 2 GTX M | Bushtukah | $125.97/209.95, 6 regular + 8 wide | same, 14 |
| Kombi Patrol mittens M | Bushtukah | $149.96/199.95, M/L/XL | same |
| Ciele VLVHalfzip W | Bushtukah | $149.96/199.95, title "Women's" (handle says mens-copy: store's) | same |
| Saucony Endorphin Speed 5 Marathon W | BlackToe | $160/230, 8.5/9/10 | same |
| NB Rebel v5 M | JD Sports | $90/180, 8/9/10/10.5/13 | same price; drop claim wrong (#1) |
| Puma Deviate Nitro 3 W | SVP | $79.99/219.99, 6.5-10.5 | same, 9 |
| Mizuno Wave Horizon 7 W | Strides | $150/200, 7.5/8/9.5/10 | same |
| On Cloudultra Pro W | Gord's | $229.95/329.95, 7-9 | $229.95, 5 sizes |
| Hoka Clifton 10 W | Running Room | $110/179.99 | $110 (was $189, see above) |
| OR Aspire pants W | The Last Hunt | $146.36/239.95 | same; "was" wrong (#2) |
| UD Xodus vest W | The Last Hunt | $162.49/249.99 | same; "was" wrong (#2) |
| Reebok FloatZig 2 M (went up) | The Last Hunt | $141.74 / $150.49, title Men's | same |
| On Cloudflow 5 M (went up) | Brainsport | $179.99/230, 8/8.5/10/10.5/11 (handle m-cloudflow-6) | same |
| Saucony ProGrid Paramount W (went up) | Saucony | C$172.95/230 | same |
| Nike Pegasus Premium W (went up) | Endurance | $202.50/270, 8.5/9/9.5 | same |
| Mizuno Rebellion Pro W (went up) | Strides | $200/290 | same |
| Hoka Bondi 9 M (went up) | VRC | $160.00 | $159.99 (Altitude's) |
Not checked: MEC items (blocks robots; saved pages), Stampeak, Le Coureur ("not new" list, single history point since Oct 2 = rule holds).
