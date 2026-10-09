# Stores: what we read, what we checked

Check this list before looking at a new store, so nobody tests the same shop twice.
Update it whenever a store is added, rejected or changes. Counts are from Oct 2, 2026.

## Master list: stores and brands we can't read (yet)

Every company we checked and couldn't (or chose not to) read, why, what was tried, and what would unlock it. Update it after
every check (rule in CLAUDE.md: try every allowed way first; a store that says no stays no).

| Company | Where | Why not | Tried | What would unlock it |
|---|---|---|---|---|
| **Blocked (the store says no)** | | | | |
| Sport Chek, Atmosphere, Sports Experts (Canadian Tire) | Canada | "Access Denied" to automated reading; saved pages have no sizes (Oct 2) | site, saved pages | Canadian Tire affiliate feed (Impact.com), December |
| Running Room | Canada | blocks automated reading | site | partnership or affiliate feed |
| MEC | Canada | blocks automated reading | site; **saved pages work** (Grab deals) | MEC product feed via AvantLink/Sovrn |
| REI | USA | blocks automated reading | **saved pages work** (US side) | affiliate feed |
| Boutique Courir | Montréal | blocks automated reading (Oct 1) | site | ask the store |
| SVP Sports | Québec | Cloudflare check (Oct 4) | **saved pages work**; parked Oct 6 (soccer/budget shoes) | none needed |
| Brooks, New Balance, ASICS, Hoka, Salomon, adidas, Inov-8, The North Face | brands | 403/406 "Access denied" (rechecked Oct 5) | brand sites | their shoes reach us through the stores |
| Nike | brand | robots.txt disallows product pages (sizes) | listings | through the stores |
| On | brand | script-only page, robots disallows /api | site | through the stores |
| Backcountry / Steep & Cheap | USA | bot protection: "HTTP 202, empty page" (Oct 6) | site from GitHub; reader built | affiliate product feed |
| Seattle Running Company, Road Runner Sports | WA, CA | HTTP 403 (Oct 8, store finder) | sandbox + GitHub | affiliate feed (Road Runner has one) |
| Running Warehouse, Zappos, Dick's, Eastbay | USA | blocked or not readable (Oct 6) | site | affiliate feeds |
| Honey Stinger | brand | blocks GitHub's servers (works elsewhere) | site | its gels come through other stores |
| **No online catalogue we can read** | | | | |
| Kintec | BC | no product feed (Oct 1) | site | ask them |
| Running Free | Ontario | own shop system, no feed (Oct 1) | site | own reader if worth it |
| ENROUTE | Richmond, BC | Astro site, no product list (Oct 8) | products.json, homepage | own reader (sitemap + pages) if worth it |
| The Right Shoe | Vancouver | no online shop | site | none |
| Super Jock 'n Jill, Run Hub NW, Foot Zone (Bend), A Snail's Pace, Fleet Feet | US West | sell in store only / no readable catalogue (Oct 8) | products.json, homepage | none |
| Squarespace/WooCommerce shops without a catalogue | USA | nothing online to read | | none |
| **Readable, needs its own reader (not built yet)** | | | | |
| Injinji | brand (US) | Magento shop, no products.json (Oct 8) | products.json, cart.js | sitemap + product pages (JSON-LD), robots allows |
| Distance Runwear | Vancouver | Lightspeed; ~730 products, mostly barefoot/lifestyle (Oct 8) | **?format=json works** | build a Lightspeed reader |
| Gord's Running Store | Calgary | WooCommerce, Store API open (Oct 6) | | build a WooCommerce reader |
| Saucony, Puma, Salomon (salomon.com/en-ca) | brands | readable pages, need their own reader | | one at a time |
| **No answer from my machine or GitHub** | | | | |
| Bivo, Spring Energy, Fit Right NW | US West | no connection (Oct 8: sandbox + store finder; domains may differ) | bivo.co/.com, springenergy.co/.com | find the right address, retry |
| Fast Trax, Mile One Running, The Trail Store | AB / BC | site didn't answer (Oct 1) | | retry with the store finder |
| **Readable, waiting on purpose** | | | | |
| Valhalla Pure (vpo.ca) | BC | readable, 19,750 products, mostly hiking/camping | full read Oct 8 | December hiking launch |
| Outdoor Research | Seattle | readable, mostly hiking/climbing | first page | December hiking launch |
| Comor, Oberson, Kunstadt, Skiis & Biikes, Boardroom | snow | readable snow shops | | January ski launch |
| Running Factory | Windsor | readable, ~37 on sale, mostly CEP sleeves (Oct 3) | | recheck later |
| **Checked and skipped (not a fit)** | | | | |
| Picky Bars | Bend, OR | all bars sold out (now Laird Superfood) (Oct 8) | full read | recheck if bars return |
| Comor Sports (for running) | Vancouver | 7,250 products, zero running | full read | ski launch |
| The Trail Shop | Halifax | general outdoor (Yeti, tents) | full read | hiking launch maybe |
| Deadstock | Calgary/Vancouver | sneakers/streetwear (Oct 7) | | none |
| Shoebacca | USA | budget/gym shoes (Oct 6) | | none |
| Onion River Sports, Potomac River Running | USA | 2 shoes / same as PR Run & Walk | | none |
| La Cordée | Québec | insolvency (Oct 2026) | | recheck if it restructures |
| Amazon | | no scraping; Associates API needs 3 sales | | affiliate links first |

## Stores we read (63)

### Canadian stores (26)
| Store | Website | Products | On sale |
|---|---|---:|---:|
| Aerobics First (Halifax; added Oct 3) | aerobicsfirst.com | 1,847 | 249 |
| Altitude Sports | altitude-sports.com | 2,319 | 39 |
| BlackToe Running | blacktoerunning.com | 1,339 | 232 |
| Boutique Endurance | boutiqueendurance.ca | 539 | 67 |
| Bushtukah | bushtukah.com | 1,462 | 156 |
| Capra Running Co. | capra.run | 409 | 33 |
| Run Uphill / Ski Uphill (Canmore + Squamish; added Oct 7; skiuphill.ca = same shop; ski touring gear filtered out) | runuphill.ca | 935 | 208 |
| City Park Runners (Winnipeg; added Oct 3) | cityparkrunners.com | 649 | 70 |
| Ciele | ca.cieleathletics.com | 134 | 0 |
| Decathlon | decathlon.ca | 17 | 13 |
| Fit First | fitfirst.ca | 754 | 88 |
| Foot Locker (national; added Oct 4: running sale shoes only, own reader) | footlocker.ca | 48 | 48 |
| Forerunners | shop.forerunners.ca | 70 | 11 |
| Frontrunners | frontrunners.ca | 1,206 | 277 |
| Le Coureur | lecoureur.com | 1,233 | 480 |
| Le Coureur Nordique | lecoureurnordique.ca | 1,593 | 642 |
| MEC | mec.ca | 213 | 207 |
| Nordarun | nordarun.com | 128 | 2 |
| Näak | naak.com | 62 | 5 |
| Brix (Québec maple fuel) | brixrechargeparlanature.com | 11 | 2 |
| Upika (Québec drink mixes, bars) | upika.ca | 26 | 1 |
| Grynd (Calgary/Prince George energy waffles) | grynd.ca | 16 | 1 |
| Krono Nutrition (Québec gels, bars, drink mixes, Kronobar) | krononutrition.com | 97 | 0 |
| Inner Self (Montréal running apparel) | innerselfrunning.com | 41 | 0 |
| Balmoral (Montréal, made-in-Canada running apparel; knitwear/sherpa/gym bag filtered) | balmoralrunning.com | 35 | 0 |
| Sea2Sky Nutrition | sea2skynutrition.ca | 251 | 14 |
| Sporting Life | sportinglife.ca | 659 | 292 |
| Strides Running (Calgary/Canmore; added Oct 3) | stridesrunning.com | 1,344 | 136 |
| Stampeak | stampeak.com | 253 | 141 |
| The Runners Shop (Toronto; added Oct 3) | therunnersshop.com | 688 | 198 |
| The Last Hunt | thelasthunt.com | 1,281 | 1,274 |
| Vancouver Running Co. | vanrunco.com | 644 | 117 |
| Rackets & Runners (Vancouver, Oak St; tennis/pickleball, walking and court shoes left out; added Oct 8) | racketsandrunners.ca | 294 | 72 |
| Xact Nutrition | xactnutrition.com | 25 | 0 |

### Brands and stores abroad (37) (ship to Canada; prices converted to CAD)

**Oct 8, 2026 shipping check** (each Shopify store's own shipping list, `ships_to_countries` in meta.json, now read every day:
a store that leaves Canada out is kept off the Canada side, one that leaves the US out off the USA side). 2xu.com turned out
to be the Australian store (AU only): Canada side now reads **ca.2xu.com**, USA side **us.2xu.com**. US-only .com stores, so
USA side only: Darn Tough, Nathan, Balega, Feetures, Stance, goodr, Nuun, GU, Huma, Tifosi, Mount to Coast (Darn Tough,
Balega and Nathan say so on their shipping pages). Their Canadian stores, read for the Canada side: **feetures.ca, balega.ca,
stance.ca, goodr.ca, nuun.ca, humagel.ca** (Podium Imports, Huma's Canadian distributor: its nutrition section only; it also
carries Tifosi, SaltStick, Wrightsock, Currex). Saysky (EU) leaves the US out: Canada side only. Still to look for: a Canadian
way to buy Darn Tough, Nathan, GU, Tifosi (humagel.ca collection "tifosi-optics"), Mount to Coast.

| Store | Website | Products | On sale |
|---|---|---:|---:|
| 2XU (Canada; Oct 8: was 2xu.com, the Australian store, ships to AU only) | ca.2xu.com | 250+ | 71 |
| Altra (US) | altrarunning.com | 131 | 44 |
| Balega (US) | balega.com | 151 | 7 |
| Bandit (US) | banditrunning.com | 530 | 0 |
| Darn Tough (US) | darntough.com | 280 | 2 |
| District Vision (US) | districtvision.com | 462 | 121 |
| Feetures (US) | feetures.com | 163 | 103 |
| goodr (US) | goodr.com | 381 | 0 |
| GU (US) | guenergy.com | 14 | 0 |
| Huma (US) | humagel.com | 7 | 1 |
| Janji (US) | runjanji.com | 94 | 0 |
| Kogalla (US) | kogalla.com | 1 | 0 |
| Mount to Coast (US) | mounttocoast.com | 22 | 0 |
| Naked (US) | nakedsportsinnovations.com | 9 | 3 |
| Nathan (US) | nathansports.com | 92 | 29 |
| Nuun (US) | nuun.com | 17 | 9 |
| Oiselle (US) | oiselle.com | 95 | 0 |
| rabbit (US) | runinrabbit.com | 324 | 165 |
| Raidlight (FR) | raidlight.com | 83 | 12 |
| REI (US) | rei.com | 0 | 0 |
| rnnr (US) | rnnr.com | 75 | 16 |
| Roka (US) | roka.com | 218 | 10 |
| Satisfy (FR) | satisfyrunning.com | 447 | 1 |
| SAYSKY (DK) | saysky.com | 259 | 74 |
| Skratch Labs (US) | skratchlabs.com | 63 | 52 |
| Smartwool (US) | smartwool.com | 404 | 153 |
| Soar (UK) | soarrunning.com | 328 | 1 |
| Squirrel's Nut Butter (US) | squirrelsnutbutter.com | 36 | 6 |
| Stance (US) | stance.com | 872 | 405 |
| Sunski (US) | sunski.com | 114 | 0 |
| Swiftwick (US) | swiftwick.com | 64 | 24 |
| Tailwind (US) | tailwindnutrition.com | 89 | 0 |
| Ten Thousand (US) | tenthousand.cc | 70 | 0 |
| The Feed (US) | thefeed.com | 2,370 | 538 |
| Tifosi (US) | tifosioptics.com | 152 | 18 |
| Wigwam (US) | wigwam.com | 126 | 13 |

Honey Stinger was taken off Oct 8: it blocks GitHub's servers (0 products since Oct 1); its gels come through other stores. REI only shows when Bastien saves
fresh pages with the Grab deals bookmark (US only). MEC also comes from saved pages.

## Checked and not added

| Store | City | Why not (date checked) |
|---|---|---|
| Sport Chek | national | blocks automated reading; saved sale pages (Oct 2, 2026) have no sizes, even filtered to running clearance (74 shoes, 2 pages): wait for the affiliate feed (Canadian Tire) |
| Running Room | national | blocks automated reading |
| Atmosphere | national | blocks automated reading |
| Sports Experts | QC | blocks automated reading |
| Boutique Courir (boutiquecourir.com) | Montréal | blocks automated reading (Oct 1, 2026) |
| SVP Sports (svpsports.ca) | Québec chain | Shopify behind a Cloudflare "verify your connection" check on products.json and collections (Oct 4, 2026). Its Shopify shopping-agent catalog (UCP/MCP) exists but is meant for buyer assistants and needs an agent profile; not used. Read from the Grab deals bookmark (Oct 4): Bastien saved SVP's running sale collection (svp-DATE.json). **Parked Oct 6, 2026**: the sale page is mostly soccer and budget shoes, not worth a weekly save; reader kept |
| Kintec (kintec.net) | BC | no readable product feed (Oct 1, 2026) |
| Running Free (runningfree.com) | Ontario | no readable product feed (Oct 1, 2026) |
| Gord's Running Store | Calgary | no readable product feed (Oct 1, 2026) |
| Fast Trax, Mile One Running, The Trail Store | AB / BC | site didn't answer (Oct 1, 2026); try again later |

## Brand stores (checked Oct 1, 2026)

| Brand | Status |
|---|---|
| Brooks, New Balance, ASICS, Hoka, adidas, Inov-8, The North Face | block automated reading: skip (their shoes reach us through the stores) |
| Rechecked Oct 5, 2026 | Hoka (406 Access Denied), New Balance, Brooks, ASICS, Salomon (403), adidas.ca (connection dropped): still blocked. Nike: listings readable but robots.txt disallows product pages (*/p/), where sizes live: not usable. On: page is a script shell, robots disallows /api: not usable. Saucony (saucony.ca → saucony.com/CA, Salesforce) and Puma (ca.puma.com, robots allows /pd/ product pages; price + colour stock in the page, per-size stock loads separately): candidates, need their own reader |
| Norda, Altra, Ciele, rabbit, Janji, … | already read (Shopify) |
| Saucony (saucony.com/CA), Salomon (salomon.com/en-ca), On (on.com/en-ca), Nike (nike.com/ca) | readable pages, need their own reader: planned, one at a time (Saucony, Salomon first) |
| Arc'teryx, Craft, Topo, Dynafit | readable, less running-focused or US-only: low priority |
| Karhu, VJ, Scarpa | Shopify but in euros from Europe (duties): low priority |
| Mizuno (mizuno.ca) | domain parked |

## Readable, waiting (add when they have sales)

| Store | City | Note (date checked) |
|---|---|---|
| (none right now: Aerobics First and City Park Runners were added Oct 3) | | |

## Checked Oct 8, 2026 (overnight)

| Store | City | Result |
|---|---|---|
| The Trail Runner Store (trailrunnerstore.com) | Toronto | Shopify, CAD, 1,140 products, ~330 on sale, 173 shoe models, trail focus. Sorting check clean (Big Agnes camping dropped). **Added Oct 8** |
| Cowichan Valley Running (cowichanvalleyrunning.com) | Mill Bay, BC | Shopify, CAD, 660 products, few on sale (5 deals in a men's 11). **Added Oct 8** |
| The Trail Shop (trailshop.com) | Halifax | Shopify, CAD, 3,100 products but general outdoor (Yeti, tents, Blundstone), 60 on sale: skipped |
| Decathlon (night read) | | Oct 8: answers 429 after ~50 product pages even at night; now read a slice each night (cursor, one page / 20 s), products kept 14 days |
| Deadstock (deadstock.ca) | Calgary/Vancouver | sneaker/streetwear, ~24 running shoes: skipped (Oct 7) |
| R&R Rackets and Runners, Escarpment Running, Maison de la Course, Mile One, The Trail Store, Fast Trax | | site didn't answer from my sandbox or no shop found: try with the store finder (GitHub) |

## Ideas not checked yet

The Run Company, Le Coin des Coureurs.

Checked Oct 3: Running Factory (Windsor, runningfactory.com): readable, only ~37 on sale, mostly CEP sleeves; recheck later.
"Runner's Choice" (Toronto) not found; The Runners Shop is the Toronto store (added).

## Snow (researched Oct 2, 2026; parked until mid-November)

Readable snow shops (Shopify): Comor Sports (comorsports.com, Vancouver), Oberson (oberson.com, Québec: alpine + big
nordic range), Kunstadt Sports (kunstadt.com, Toronto: alpine, ski boots, nordic), Skiis & Biikes (skiisandbiikes.com,
Toronto), Boardroom (boardroomshop.com, Vancouver: snowboard). evo.com readable but US. Blocked: Sports Experts, Sporting Life.
Altitude / The Last Hunt (already read): categories /c/snowboarding (Altitude 1,894, Last Hunt 1,074 listings: goggles,
helmets, snow jackets and pants, snowboards, boots), /c/cross-country-skiing (220 / 164), /c/backcountry-skiing (470 / 143:
skins, avalanche gear). Plan if built: groups skis (alpine/nordic/touring), ski boots (mondo from shoe size), snowboards
(length from height), snowboard boots, helmets & goggles, snow jackets & pants, backcountry gear.

## USA side (Oct 6, 2026)

US running shops read for the USA side only (they may not ship to Canada). Shopify: Pacers Running (DC/VA), Portland Running Co. (OR),
Heartbreak Hill (MA), Runners Plus (IL), Gazelle Sports (MI), Sports Basement (CA; running collection only), Tortoise & Hare (AZ),
Run Flagstaff (AZ), Running Lab (MI), Playmakers (MI), Mill City Running (MN), The Running Well Store (MO), Mountain Running Co. (NC),
Confluence Running (NY), Columbus Running Co. (OH), Scranton Running Co. (PA), Trailhead Running Supply (TX), PR Run & Walk (VA),
Performance Running Outfitters (WI), Fitness Sports (IA), Athletic Annex (IN), Ann Arbor Running Co. (MI), Two Rivers Treads (NC),
Xtra Mile Running (TN), Luke's Locker (TX), San Francisco Running Co. (CA, store.sfrunco.com).
Brands (Oct 8, USA side): Territory Run Co. (CA, trail apparel; resold Tailwind/Hydrapak get their own brand), Path Projects (CO, shorts/liners),
Ombraz (CA, armless sunglasses).
RunFree (night job, scraper/runfree.py): Charlotte Running Co., Terra, John's Run/Walk, Palmetto, Rush, iRun Texas, West Stride,
Millennium, Running Niche, Good Times, Bull City, Red Coyote, 605 Running, Point 2, Big Peach, Running Zone, Manhattan Running Co.,
Charm City Run, Pace Yourself, Runner's Roost, Missouri Running Co., Track Shack, Aardvark, Philadelphia Runner.
Backcountry (checked Oct 6): pages readable and allowed by robots, but its bot protection answers GitHub's servers "HTTP 202,
empty page", so it's off. Reader kept in scrape.py (`bc_product`) for an affiliate product feed (Backcountry has an affiliate
program). Sister site Steep & Cheap: same catalogue.

Checked, not used: Shoebacca (mostly PUMA/adidas/Diadora budget shoes), Potomac River Running (same shop as PR Run & Walk),
Onion River Sports (VT, 2 shoes), Runner's Den (serves CAD; check which store it is), Running Warehouse, Road Runner Sports, Zappos,
Dick's, REI (saved pages only), Brooks, Eastbay (blocked or not readable). Squarespace/WooCommerce sites without an online catalogue:
skipped. Candidate list: tools/us_candidates.txt (store finder).

## Added Oct 6, 2026 (Canada)
- Brainsport (Saskatoon, SK) brainsport.ca: Shopify, ~1,500 listings (926 shoes). Colours in some New Balance names are cut off; "Not specified" brands taken from the name.
- SAIL plein air (QC/ON chain) sail.ca/en-ca: Shopify, running collection only (outdoor-gear-running).
- Runner's Soul (Lethbridge, AB) shop.runnersoul.com: RunFree (night job), Canada side, prices in CAD.
- Checked, skipped: La Cordée (insolvency, Oct 2026: recheck if it restructures and keeps selling online).
- Next to check: Gord's Running Store (Calgary, WooCommerce Store API open), Running Free (Ontario chain, own shop system).
  More candidates: Canadian Running Magazine's list of independent running shops (runningmagazine.ca).
