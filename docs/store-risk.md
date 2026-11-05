# Store risk list (2026-11-05)

Built by `tools/store_risk.py` from the live site's files and the morning read's log. **Cards** = today's sale cards (Canada + USA) where the store has the best price in at least one size; **only here** = cards no other store carries (gone if it locks us out). 20,368 sale cards in all.

Kinds of failure: **locked out** = the store said no (403/429, robots.txt, a country page): we stop and never work around it. **Reader broke** = we misread a page (our fix). **Store's own problem** = its server or file was broken (it comes back by itself).

## Top 5 at risk

- **thefeed** (products.json, slowly at night (it rate-limits GitHub by day)): 842 cards, 824 only here; last failure 2026-10-08 (locked: 429 local_rate_limited by day: moved to a slow night read)
  - What lowers it: Already slow (a page every 10 s at night). Lower: read only products changed since last night (products.json updated_at), and apply to its CJ affiliate product feed (the real fix).
- **lasthunt** (its catalogue service + product pages (commercetools), ~1,400 requests a read): 1,227 cards, 734 only here
  - What lowers it: ~1,400 requests a read, twice a day, through its catalogue service. Lower: re-read a product page only when its listing changed or it's on sale (already), move the second daily read to night, and ask Rakuten/FlexOffers for its product feed.
- **runningfree** (listing + size pages, one every 30 s at night (its Crawl-delay)): 558 cards, 377 only here; last failure 2026-11-05 (locked: country page 'only available to visitors in Canada' to GitHub's US computers (was 'Canada or the United States'))
  - What lowers it: Its country page now says Canada only, and GitHub's computers are in the US. Ask Running Free (they're friendly to links: we send them clicks) for permission or a product file; until then it leaves the site 48 h after its last copy. Never read it through a Canadian address to get past the page.
- **borealrunning** (public products.json (Shopify)): 1,081 cards, 894 only here
  - What lowers it: Public products.json, ~15 requests a read: low risk per read, but 894 cards only here. Nothing to slow down; a short hello email (we link to them, here are the clicks) makes a lockout less likely.
- **altitude** (its catalogue service + product pages (commercetools), ~2,100 requests a read): 362 cards, 228 only here
  - What lowers it: ~2,100 requests a read, twice a day, same service as The Last Hunt (same company). Same steps: fewer re-reads, one read a day at night, product feed via Rakuten/FlexOffers or Sovrn in January.

Saved pages can't lock us out (they're Bastien's own visits); their risk is going stale after 5 days without a save: rei (4,779 cards, 4,432 only here), backcountry (1,074 cards, 926 only here), mec (146 cards, 86 only here).

## Every store

| Store | How we read it | Requests a read | Cards | Only here | Last good read | Last failure |
|---|---|---|---|---|---|---|
| thefeed | products.json, slowly at night (it rate-limits GitHub by day) | - | 842 | 824 | 2026-11-05 11:48 | 2026-10-08 locked: 429 local_rate_limited by day: moved to a slow night read |
| lasthunt | its catalogue service + product pages (commercetools), ~1,400 requests a read | 1405 | 1,227 | 734 | 2026-11-05 11:48 | - |
| runningfree | listing + size pages, one every 30 s at night (its Crawl-delay) | - | 558 | 377 | 2026-11-05 11:48 | 2026-11-05 locked: country page 'only available to visitors in Canada' to GitHub's US computers (was 'Canada  |
| borealrunning | public products.json (Shopify) | 15 | 1,081 | 894 | 2026-11-05 11:48 | - |
| rei | Bastien's saved pages (Grab deals bookmark) | - | 4,779 | 4,432 | 2026-11-05 11:48 | - |
| altitude | its catalogue service + product pages (commercetools), ~2,100 requests a read | 2132 | 362 | 228 | 2026-11-05 11:48 | - |
| svp | public products.json (Shopify) | - | 664 | 599 | 2026-11-05 11:48 | - |
| runningroom | its own public product feed (22 files, listed in robots.txt) | 25 | 726 | 526 | 2026-11-04 23:41 | 2026-11-05 store: one of its 22 feed files was a picture (19 KB); also Oct 12 + Oct 18 |
| confluence | public products.json (Shopify) | 18 | 607 | 389 | 2026-11-05 11:48 | - |
| stance | public products.json (Shopify) | 15 | 443 | 442 | 2026-11-05 11:48 | - |
| rabbit | public products.json (Shopify) | - | 451 | 398 | 2026-11-05 11:48 | - |
| fleetfeet | product pages, one every 2 s at night (~3,000 a night) | - | 296 | 87 | 2026-11-05 11:48 | - |
| coureurnordique | public products.json (Shopify) | 16 | 511 | 244 | 2026-11-05 11:48 | - |
| bushtukah | public products.json (Shopify) | 23 | 355 | 288 | 2026-11-05 11:48 | - |
| prrunwalk | public products.json (Shopify) | 29 | 438 | 258 | 2026-11-05 11:48 | - |
| sportsbasement | public products.json (Shopify) | 12 | 386 | 214 | 2026-11-05 11:48 | - |
| decathlon | listing + product pages, one every 20 s at night (429 by day since Oct 5) | - | 56 | 56 | 2026-11-05 11:48 | 2026-10-08 locked: 429 after ~50 pages even at night: one page every 20 s |
| trailrunner | public products.json (Shopify) | 11 | 274 | 216 | 2026-11-05 11:48 | - |
| fit2run | public products.json (Shopify) | 83 | 293 | 205 | 2026-11-05 11:48 | - |
| smartwool | public products.json (Shopify) | - | 257 | 209 | 2026-11-05 11:48 | - |
| playmakers | public products.json (Shopify) | 19 | 244 | 208 | 2026-11-05 11:48 | - |
| lecoureur | public products.json (Shopify) | 15 | 322 | 174 | 2026-11-05 11:48 | - |
| stanceca | public products.json (Shopify) | - | 211 | 195 | 2026-11-05 11:48 | - |
| gazelle | public products.json (Shopify) | 23 | 313 | 158 | 2026-11-05 11:48 | - |
| backcountry | Bastien's saved pages (Grab deals bookmark) | - | 1,074 | 926 | 2026-11-05 11:48 | 2026-10-06 locked: HTTP 202 empty page to GitHub: saved pages only |
| performancerun | public products.json (Shopify) | 15 | 224 | 170 | 2026-11-05 11:48 | - |
| stampeak | listing pages | - | 164 | 160 | 2026-11-05 11:48 | - |
| brainsport | public products.json (Shopify) | 13 | 300 | 111 | 2026-11-05 11:48 | - |
| runnersplus | public products.json (Shopify) | 17 | 255 | 123 | 2026-11-05 11:48 | - |
| sail | public products.json (Shopify) | - | 179 | 136 | 2026-11-05 11:48 | - |
| frontrunners | public products.json (Shopify) | 16 | 213 | 124 | 2026-11-05 11:48 | - |
| blacktoe | public products.json (Shopify) | 12 | 210 | 114 | 2026-11-05 11:48 | - |
| sportinglife | listing + product pages | 1220 | 222 | 108 | 2026-11-05 11:48 | - |
| runuphill | public products.json (Shopify) | 13 | 184 | 118 | 2026-11-05 11:48 | - |
| districtvision | public products.json (Shopify) | - | 134 | 134 | 2026-11-05 11:48 | - |
| gords | public shop data (WooCommerce / Lightspeed) | 137 | 207 | 102 | 2026-11-05 11:48 | - |
| saucony | brand site pages + its size service, one every 3 s at night | - | 58 | 46 | 2026-11-05 11:48 | - |
| headsweats | public products.json (Shopify) | - | 122 | 122 | 2026-11-05 11:48 | - |
| 33off | public products.json (Shopify) | - | 170 | 100 | 2026-11-05 11:48 | - |
| aerobicsfirst | public products.json (Shopify) | 20 | 159 | 88 | 2026-11-05 11:48 | - |
| feetures | public products.json (Shopify) | - | 103 | 103 | 2026-11-05 11:48 | - |
| runnersshop | public products.json (Shopify) | - | 159 | 80 | 2026-11-05 11:48 | - |
| pacers | public products.json (Shopify) | 37 | 163 | 73 | 2026-11-05 11:48 | - |
| tortoisehare | public products.json (Shopify) | - | 109 | 84 | 2026-11-05 11:48 | - |
| 2xuus | public products.json (Shopify) | - | 86 | 86 | 2026-11-05 11:48 | - |
| 2xu | public products.json (Shopify) | 9 | 92 | 82 | 2026-11-05 11:48 | - |
| saysky | public products.json (Shopify) | 10 | 83 | 83 | 2026-11-05 11:48 | - |
| runningwell | public products.json (Shopify) | 13 | 134 | 65 | 2026-11-05 11:48 | - |
| foveo | public products.json (Shopify) | 10 | 113 | 69 | 2026-11-05 11:48 | - |
| aupiedsportif | public products.json (Shopify) | 11 | 101 | 69 | 2026-11-05 11:48 | - |
| vanrunco | public products.json (Shopify) | 10 | 124 | 59 | 2026-11-05 11:48 | - |
| heartbreak | public products.json (Shopify) | - | 104 | 65 | 2026-11-05 11:48 | - |
| mountainrun | public products.json (Shopify) | - | 126 | 43 | 2026-11-05 11:48 | - |
| athleticannex | public products.json (Shopify) | 32 | 128 | 38 | 2026-11-05 11:48 | - |
| orangemud | public products.json (Shopify) | - | 50 | 50 | 2026-11-05 11:48 | - |
| daves | public products.json (Shopify) | - | 110 | 26 | 2026-11-05 11:48 | - |
| swiftwick | public products.json (Shopify) | - | 46 | 46 | 2026-11-05 11:48 | - |
| millcity | public products.json (Shopify) | - | 65 | 38 | 2026-11-05 11:48 | - |
| theloop | public products.json (Shopify) | - | 61 | 36 | 2026-11-05 11:48 | - |
| altra | public products.json (Shopify) | - | 60 | 35 | 2026-11-05 11:48 | - |
| praise | public products.json (Shopify) | - | 41 | 41 | 2026-11-05 11:48 | - |
| strides | public products.json (Shopify) | 17 | 77 | 28 | 2026-11-05 11:48 | - |
| karhuus | public products.json (Shopify) | - | 45 | 38 | 2026-11-05 11:48 | - |
| skratch | public products.json (Shopify) | - | 36 | 36 | 2026-11-05 11:48 | - |
| trailheadrun | public products.json (Shopify) | - | 54 | 29 | 2026-11-05 11:48 | - |
| rnnr | public products.json (Shopify) | - | 28 | 28 | 2026-11-05 11:48 | - |
| cityparkrunners | public products.json (Shopify) | 9 | 60 | 15 | 2026-11-05 11:48 | - |
| boutiquedulac | public products.json (Shopify) | 10 | 65 | 13 | 2026-11-05 11:48 | - |
| wigwam | public products.json (Shopify) | - | 24 | 24 | 2026-11-05 11:48 | - |
| fitnesssports | public products.json (Shopify) | - | 42 | 17 | 2026-11-05 11:48 | - |
| tworivers | public products.json (Shopify) | - | 38 | 17 | 2026-11-05 11:48 | - |
| capra | public products.json (Shopify) | 9 | 26 | 21 | 2026-11-05 11:48 | - |
| portlandrun | public products.json (Shopify) | - | 41 | 15 | 2026-11-05 11:48 | - |
| mec | Bastien's saved pages (Grab deals bookmark) | - | 146 | 86 | 2026-11-05 11:48 | - |
| raidlight | public products.json (Shopify) | - | 20 | 20 | 2026-11-05 11:48 | - |
| footlocker | listing + product pages | 479 | 33 | 15 | 2026-11-05 11:48 | - |
| columbusrun | public products.json (Shopify) | 12 | 33 | 14 | 2026-11-05 11:48 | - |
| runderwear | public products.json (Shopify) | - | 18 | 18 | 2026-11-05 11:48 | - |
| rollga | public products.json (Shopify) | - | 18 | 18 | 2026-11-05 11:48 | - |
| roka | public products.json (Shopify) | - | 18 | 18 | 2026-11-05 11:48 | - |
| farmtofeet | public products.json (Shopify) | - | 18 | 18 | 2026-11-05 11:48 | - |
| runninglab | public products.json (Shopify) | 18 | 50 | 7 | 2026-11-05 11:48 | - |
| ciele | public products.json (Shopify) | 9 | 30 | 13 | 2026-11-05 11:48 | - |
| ombraz | public products.json (Shopify) | - | 17 | 17 | 2026-11-05 11:48 | - |
| sunski | public products.json (Shopify) | - | 16 | 16 | 2026-11-05 11:48 | - |
| skirack | public products.json (Shopify) | - | 30 | 11 | 2026-11-05 11:48 | - |
| distance | public shop data (WooCommerce / Lightspeed) | 568 | 17 | 15 | 2026-11-05 11:48 | - |
| xtramile | public products.json (Shopify) | - | 25 | 11 | 2026-11-05 11:48 | - |
| rackets | public products.json (Shopify) | 14 | 55 | 1 | 2026-11-05 11:48 | - |
| sfrunco | public products.json (Shopify) | - | 18 | 13 | 2026-11-05 11:48 | - |
| lukeslocker | public products.json (Shopify) | - | 32 | 7 | 2026-11-05 11:48 | - |
| flipbelt | public products.json (Shopify) | - | 13 | 13 | 2026-11-05 11:48 | - |
| endurance | public products.json (Shopify) | 9 | 31 | 7 | 2026-11-05 11:48 | - |
| squirrels | public products.json (Shopify) | - | 12 | 12 | 2026-11-05 11:48 | - |
| nathan | public products.json (Shopify) | - | 24 | 8 | 2026-11-05 11:48 | - |
| fitletic | public products.json (Shopify) | - | 12 | 12 | 2026-11-05 11:48 | - |
| thorlo | public products.json (Shopify) | - | 11 | 11 | 2026-11-05 11:48 | - |
| styrkr | public products.json (Shopify) | - | 11 | 11 | 2026-11-05 11:48 | - |
| fitfirst | public products.json (Shopify) | 11 | 29 | 5 | 2026-11-05 11:48 | - |
| feeturesca | public products.json (Shopify) | - | 11 | 11 | 2026-11-05 11:48 | - |
| veloforte | public products.json (Shopify) | - | 10 | 10 | 2026-11-05 11:48 | - |
| territory | public products.json (Shopify) | - | 10 | 10 | 2026-11-05 11:48 | - |
| runinn | public products.json (Shopify) | - | 19 | 7 | 2026-11-05 11:48 | - |
| pathprojects | public products.json (Shopify) | - | 10 | 10 | 2026-11-05 11:48 | - |
| tifosi | public products.json (Shopify) | - | 12 | 9 | 2026-11-05 11:48 | - |
| cowichan | public products.json (Shopify) | 9 | 14 | 5 | 2026-11-05 11:48 | - |
| nuun | public products.json (Shopify) | 11 | 7 | 7 | 2026-11-05 11:48 | - |
| balega | public products.json (Shopify) | - | 7 | 7 | 2026-11-05 11:48 | - |
| nuunca | public products.json (Shopify) | 11 | 6 | 6 | 2026-11-05 11:48 | - |
| nakedsports | public products.json (Shopify) | - | 6 | 6 | 2026-11-05 11:48 | - |
| runnersden | public products.json (Shopify) | 11 | 17 | 2 | 2026-11-05 11:48 | - |
| forerunners | public products.json (Shopify) | - | 11 | 4 | 2026-11-05 11:48 | - |
| newton | public products.json (Shopify) | - | 5 | 5 | 2026-11-05 11:48 | - |
| runflagstaff | public products.json (Shopify) | - | 8 | 2 | 2026-11-05 11:48 | - |
| jdsports | public products.json (Shopify) | - | 14 | 0 | 2026-11-05 11:48 | - |
| spibelt | public products.json (Shopify) | - | 2 | 2 | 2026-11-05 11:48 | - |
| soar | public products.json (Shopify) | - | 2 | 2 | 2026-11-05 11:48 | - |
| nordarun | public products.json (Shopify) | - | 2 | 2 | 2026-11-05 11:48 | - |
| muir | public products.json (Shopify) | - | 2 | 2 | 2026-11-05 11:48 | - |
| darntough | public products.json (Shopify) | - | 2 | 2 | 2026-11-05 11:48 | - |
| brix | public products.json (Shopify) | - | 2 | 2 | 2026-11-05 11:48 | - |
| xero | public products.json (Shopify) | - | 2 | 1 | 2026-11-05 11:48 | - |
| scrantonrun | public products.json (Shopify) | - | 5 | 0 | 2026-11-05 11:48 | - |
| upika | public products.json (Shopify) | - | 1 | 1 | 2026-11-05 11:48 | - |
| huma | public products.json (Shopify) | - | 1 | 1 | 2026-11-05 11:48 | - |
| paragon | public products.json (Shopify) | 12 | 2 | 0 | 2026-11-05 11:48 | - |
| naak | public products.json (Shopify) | - | 1 | 0 | 2026-11-05 11:48 | - |
| catalog | catalog file (parked Oct 30) | - | 0 | 0 | 2026-11-05 11:48 | - |
| arcteryx | brand site sitemap + product pages at night | - | 0 | 0 | 2026-11-05 11:48 | - |
| adidasca | catalog file (parked Oct 30) | - | 0 | 0 | 2026-11-05 11:48 | - |

23 more stores (public products.json, no sale card and no failure today): annarborrun, balegaca, balmoral, bandit, fauxmouvement, goodr, goodrca, grynd, gu, hettas, humaca, innerself, janji, kogalla, krono, lmnt, mounttocoast, oiselle, satisfy, sea2sky, tailwind, tenthousand, xact.

Off on purpose: Sport Chek (HTTP 403 at both reads: OFF since Nov 5), Sports Experts (robots.txt AI block (ClaudeBot Disallow /): OFF), 27 RunFree shops (robots.txt Disallow /api/ on all 27 RunFree shops: OFF).
