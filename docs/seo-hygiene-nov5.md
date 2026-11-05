# SEO night, Thu Nov 5: INDEXATION HYGIENE (seo-lead)

Builds on docs/seo-audit-nov4.md and docs/seo-links-nov4.md; specs already sent there are not repeated, only their status.
Evidence (all live, Nov 5 07:40-09:15 UTC, honest UA "TheGearFox-SEOcheck", 1 request/second):
- sitemap.xml (2,826 URLs), robots.txt, the 4 live registries (shoes/pages.json, us/shoes/pages.json, hiking-boots/pages.json, us/hiking-boots/pages.json);
- a HEAD request to EVERY sitemap URL (2,826);
- 195 full pages parsed: 170 sampled across every page type (incl. all 42 indexable "Not in stock" pages and 12 noindex pages) + 25 duplicate/boot checks;
- the IndexNow job logs of the last two morning runs (gh run view), tools/lastmod.py + tools/indexnow.py, shoe_pages.py base_model()/model_page().
No Search Console export tonight. No search volumes anywhere below.

## Did the Nov 4 specs land? (checked on the live pages)

| Spec | Live? | Evidence |
|---|---|---|
| #8 FR race articles (du/le) | YES | 0 elisions before a consonant in the sampled FR titles |
| #4 hreflang reciprocity (hreflang_sync) | YES | 463 return-link checks on the sample, 0 failures |
| #6 sitemap lastmod = last real change | YES | 2,826/2,826 dated: 79 Nov 3, 1,981 Nov 4, 766 Nov 5; /shoes/* and /chaussures/* both 284 changed today (consistent) |
| #9a forwarding pages without noindex | YES | 8/8 sampled forwards: canonical + 0 s refresh, no robots meta |
| #9b US "kayano-32" style duplicates | NO | backend parked it (base_model change); grown into finding 2 below |
| #3 stable BF/Boxing Day/gift titles | YES | /black-friday/, /vendredi-fou/, /us/black-friday/, both deal checks, /boxing-day/, CA gift page carry the new titles |
| #5 US BF price-data section | YES | present on /us/black-friday/ |
| #7 homepage title + description | YES | "Running Shoes & Gear on Sale in Your Size \| The Gear Fox"; still 2 H1s (backend's choice, explained Nov 4) |
| #2/#11 BF price-tracker titles | SCHEDULED | switch on by themselves Nov 10 (bf_titles()); verify Nov 10 |
| L2 "On sale now" row | YES | 78/78 sampled sitemap model pages have it + their side's BF link |
| L3 deal check/gift links in browse rows, CA gift -> BF | YES | /shoes/, /running-shoes-sale/, /brands/asics/ link /black-friday/live/; both CA gift pages link BF |
| L1 related-shoes ring rule | NO | /shoes/asics-gt-2000-14/ "More ASICS shoes" is still alphabetical (cumulus-27, cumulus-27-gtx, dynablast-5, gel-cumulus-26...) and links the duplicate asics-cumulus-27 |
| L5a BreadcrumbList on out-of-stock model pages | NO | 0 of 42 indexable "Not in stock" pages have it (in-stock: 36/36) |
| L5b BreadcrumbList on race/hike pages | NO | 0 of 18 sampled race/hike pages (they carry FAQPage only) |
| #10 Keen/Lowa running brand pages | NO (needs Bastien) | still in the sitemap: "Keen Sale Canada: 3 running shoes on sale", "Lowa Sale Canada: 2 running shoes on sale" |

## Findings tonight (counts)

### 1. Sitemap: clean
- 2,826 URLs, 0 repeated. HEAD on all 2,826: **2,826 x 200** (one connection reset, 200 on retry). 0 redirects.
- Sizes match the registries exactly: /shoes 666 = /chaussures 666 = 672 live CA slugs - 6 stale; /us/shoes 665 = 679 - 14 stale; boots 82/82/73 = registries.
- **0 forwarded slugs and 0 stale (noindex) pages in the sitemap.** 0 noindex pages among the 158 sampled sitemap pages.
- lastmod: all dates <= today, none missing (the 5 undated entries of Nov 4 are dated now).
- Report pages (/report/2026-10/) not in the sitemap, as decided.

### 2. Duplicates: the same shoe on two LIVE pages (biggest problem tonight)
A slug-normalising pass over the live registries (drop New Balance "Fresh Foam X"/"FuelCell", ASICS "Gel", width words Large/D/2E/Extra/Wide,
a trailing gender word, a repeated "Trail") finds **Canada 21 groups = 43 live pages, USA 32 groups = 66 live pages**, all in the sitemap
except the stale ones. A few are real twins (Brooks Ghost vs Ghost Trail = road vs trail, kept apart on purpose Oct 30). I opened 11 pairs live:

| Pair (live, both in sitemap unless noted) | What a visitor sees |
|---|---|
| /shoes/new-balance-880v15/ vs /shoes/new-balance-fresh-foam-x-880v15/ | same title price "from $151.95 (−20%)", 7 stores each, DIFFERENT stores (Endurance, City Park... vs BlackToe, Running Room, Fit First...) |
| /shoes/new-balance-860v15/ vs /shoes/new-balance-fresh-foam-x-860v15/ | 4 stores vs 6 stores, same low price $189.95 |
| /shoes/new-balance-rebel-v5/ vs /shoes/new-balance-fuelcell-rebel-v5/ | "from $143.98" (3 stores) vs "from $70.00 (−61%)" (10 stores): someone landing on the first misses a $70 price |
| /shoes/asics-cumulus-27/ vs /shoes/asics-gel-cumulus-27/ | women's only, 4 stores vs men's + wide, 10 stores |
| /shoes/asics-gt-2000-14-large/ vs /shoes/asics-gt-2000-14/ | women's WIDE lives only on the "- Large" page; the main page has no women's wide table |
| /shoes/asics-gel-nimbus-27-large/, /shoes/mizuno-wave-rider-29-d/ | same: women's wide split off ("- Large", "D") |
| /us/shoes/new-balance-1080v15/ vs /us/shoes/new-balance-fresh-foam-x-1080v15/ | 8 stores, 110 rows vs 1 store (Pacers), 24 rows |
| /us/shoes/new-balance-supercomp-elite-v5/ vs /us/shoes/new-balance-fuelcell-supercomp-elite-v5/ | "from $174.99" vs "from $159.95" |
| /us/shoes/asics-cumulus-26/ vs /us/shoes/asics-gel-cumulus-26/ | 1 store each, different stores |
| **/us/shoes/new-balance-men-s/ and /us/shoes/new-balance-women-s/** | titled "New Balance Men's price": the table mixes a 1080v15 (Luke's Locker) and an MD500 v8 (Athletic Annex): two different shoes on one page |

Other groups: CA 860v14 (3 slugs), 880v15-gtx, hierro-v9, hierro-v9-gtx, hierro-mid-gtx, md500-v9 (both out of stock), supercomp pairs, trabuco-14(-gtx) gel/no-gel,
gel-kayano-32-large, brooks-addiction-walker-2-men-s; US gel/no-gel cumulus 27/28, nimbus-28, kayano 31/32/33, glycerin-22-extra, 860v15-2e,
fuel-cell-rebel-v5 (3 slugs), more-v6, vongo-v6, 880v14, 880v15-gtx, clifton-pro-wide, mach-7-wide, wave-rider-29-wide, wave-rider-30-women-s,
cloudsurfer-max-men-s, cloudsurfer-trail-2-trail, sd100-v5, topo-athletic-connect(-trail).
Why it matters: two pages compete for one query (Google picks one, often the thinner one), each page's title says "every size, every store" while
missing the twin's stores, and wide/women's sizes vanish from the main page. CLAUDE.md lists duplicate cards as "clearly broken". This is the
base_model gap backend named on Nov 4 (#9b): `base_model()` only strips "(Large)" in brackets, not "- Large", a bare "D"/"2E"/"Extra", NB tech prefixes
or a missing "Gel".

### 3. Forwarding: 8 chains, 4 dead ends
- CA 83 forwarded slugs: 81 land on a live page, **2 chains** (nike-pegasus-trail-5-gore-tex-trail -> ...-gtx-trail -> nike-pegasus-trail-5-gtx; same for nike-acg-pegasus-trail-gore-tex-waterproof).
- US 374 forwarded: 364 ok, **6 chains** (nike-acg-pegasus-trail, nike-zegama-trail-2, asics-corp-men-s-novablast-5, brooks-ghost-17-gore-tex-road, new-balance-m-1080-v15,
  salomon-speedcross-6-gore-tex-trail) and **4 forwards that land on a noindex never-stocked page** (asics-corp-cumulus-27 -> asics-cumulus-27, same for cumulus-28,
  kayano-32, nimbus-28) while the live page is the gel- one.
- Two meta-refresh hops still work for people, but Google may stop following after a chain and a forward onto a noindex page passes nothing.

### 4. Canonicals: clean
- 159 of 167 sampled 200 pages: canonical = itself. The other 8 are forwarding pages: canonical = forward target, all 8 targets live and in the sitemap.
- 0 pages without a canonical, 0 pointing at a 404 or a redirect.

### 5. hreflang: clean where it exists, 2 gaps
- 145 sampled sitemap pages carry hreflang (480 annotations): **0 non-reciprocal, 0 targets outside the sitemap, 0 pointing at noindex/forwarded pages.**
  x-default on 123; the 22 without are US-only pages listing only en-US (no twin: correct). Homepage + About: none (one URL for EN/FR via script: fine).
- Gap a: **22 boot slugs exist on both sides** (e.g. /hiking-boots/keen-hightrail-waterproof/ and /us/hiking-boots/keen-hightrail-waterproof/) and are not
  twinned: the CA pair lists en-CA/fr-CA/x-default only, the US page lists only itself. Model pages, races, hikes, hubs, BF and gifts ARE twinned across sides.
- Gap b: hubs /hikes/ <-> /us/hikes/ and /hiking-boots/ <-> /us/hiking-boots/ don't name each other (/races/ <-> /us/races/ do).
- Same titles on both sides of twinned pages: every race page (49 pairs, e.g. "Iron Legs Mountain Races mandatory gear list (...)") and hike page (85 pairs),
  plus /hikes/ = /us/hikes/. Hreflang tells Google which is which, so low risk; the US gift page title is now distinct.

### 6. Thin "Not in stock" pages: the Oct 24 rule works
- Indexable "Not in stock" pages in the sitemap: **42** (CA 10 slugs x EN/FR = 20, US 22), all out 1-13 days; I fetched all 42. Median 238 words vs 615 on
  in-stock pages, no Product data, no BreadcrumbList (L5a).
- Stale (14+ days or never stocked): CA 6, US 14: **all noindex,follow and out of the sitemap** (12 fetched: 12/12 correct).
- 18 of the 42 are duplicates from finding 2 (md500/sd100 pairs, speedgoat-6-large, kayano-33, glycerin-22-extra, 860v15-2e, fuel-cell-rebel-v5,
  cloudsurfer-trail-2-trail, lone-peak-9-gtx-trail, akasha-ii-trail...). Fixing finding 2 removes most of the thin set; no change to HIDE_DAYS needed.
- Internal links to noindex pages: 10 sampled pages link 39 noindex URLs (the /shoes/ indexes and ASICS "More ASICS shoes" lists). L1 already says related
  lists skip noindex pages; the /shoes/ index listing them is fine (follow).

### 7. robots.txt: fine
- Blocks only /grab.html, /stats.html, offers/hike-offers and deals*.json. sale*.json, /shoes/alts.json, CSS/JS and every page type are open.
- catalog.html, grab-save.html, stats.html carry noindex. Nothing money-critical is blocked.

### 8. Size pages
- Men's 10 vs 10.5 share 54% of their model links (nav rows included); men's 10 vs the main hub 16%. Different enough; titles + counts differ
  ("232 deals" vs "243 deals"). No change (Oct 24 decision stands); watch "Duplicate, Google chose different canonical" for /size-*/ in Search Console.

### 9. IndexNow (logs, not run)
- Nov 3 morning: 2,808 sitemap pages, **2,478 sent** (30 new, 2,448 changed), HTTP 200. Nov 4 (12:50 run): 2,821 pages, **2,170 sent** (14 new, 2,156 changed), HTTP 200.
  Today's morning job hasn't run yet (the 03:30 schedule run skipped build + indexnow).
- So the "changed pages only" filter still sends 77-88% of the site each morning. Prices and sizes really do move on most model pages between two
  morning reads (lastmod saw 284 of 666 model pages change between Nov 4's last build and Nov 5's), so this may be honest; I can't tell without a diff.
  Not a spec tonight: if Bing's indexed count stays at ~5 after the backlinks, ask backend to log 5 random "changed" diffs so we know what moves.

## Specs (ranked by expected impact; specs only, backend writes the code)

### S1. One shoe = one page: close the base_model gaps and forward the twins  [BUG: duplicate pages, wrong "every store" claim, wide sizes missing]
- Page type: model pages /shoes/, /chaussures/, /us/shoes/ (boots: same rule, none found tonight).
- Generator: scraper/shoe_pages.py `base_model()` (line ~325) + its JS twin `baseModel()` in site/index.html (line ~1481) (check.py "Shoe page links match"
  keeps them identical), `forward_old()` (registry `to`), `main()` / `build_us()`.
- Rule (add to base_model, in this order, after the existing width line):
  1. Width at the end without brackets: `\s*-?\s*\b(Large|Extra Wide|Extra|X-?Wide|Wide|2E|4E)\s*$` -> removed; a bare `D` or `B` only when it follows a number
     (`(\d)\s+[DB]\s*$`, "Wave Rider 29 D"). The item keeps its `w` flag, so the sizes land in the "· wide" table of the main page.
  2. A trailing gender word without a dash: `\s+(Men|Women)['’]?s\s*$` -> removed ("Addiction Walker 2 men's", "Cloudsurfer Max Men's").
  3. New Balance (brand == "New Balance"): drop a leading `Fresh Foam X `, `Fresh Foam `, `FuelCell `, `Fuel Cell ` before a model word
     ("Fresh Foam X 880v15" -> "880v15", "FuelCell Rebel v5" -> "Rebel v5", "FuelCell SuperComp Elite v5" -> "SuperComp Elite v5"). base_model needs the brand:
     pass it (`base_model(n, brand)`), same in baseModel.
  4. ASICS: a missing "Gel" on its Gel lines becomes "Gel-": `^(Cumulus|Kayano|Nimbus|Trabuco(?! Max)|Excite|Contend|Venture|Sonoma|Kinsei|Pulse)\b` ->
     "Gel-\1" (ASICS's own product names; Novablast, GT-2000, Superblast, Trabuco Max have no Gel).
  5. "Trail" twice in a name keeps one ("Cloudsurfer Trail 2 Trail" -> "Cloudsurfer Trail 2"). A trailing " Trail" on a slug whose base without it is a live page of the
     same kind `t` == "trail" forwards to that page ("Lone Peak 9 GTX Trail", "Akasha II Trail", "Topo Connect Trail" if both trail), never for OK_TWINS
     (Rocket X Trail, Ghost Trail).
  6. A name that is ONLY brand + gender after base_model ("New Balance Men's") gets NO page: a registered one becomes noindex,follow + out of the sitemap today
     (not after 14 days). Its items stay on the site's cards. Upstream: the store titles behind it (Luke's Locker "1080v15-4", Athletic Annex "mmd500v8")
     need their model back in the name; flag for the data side.
- Which slug survives: whatever base_model now produces; the old slugs get `to` through forward_old (the Oct 24 GTX and Oct 30 "Available in Widths" path:
  pages never disappear, card merge keeps the registered wording). Note the parked duplicate-card branch a5424a7 worried about moving ~40 slugs: here every
  move is a forward, so links and Google signals pass on.
- Expected (tonight's registries; backend recounts): CA ~19 groups, US ~30 groups collapse; about 45 CA + 60 US sitemap URLs leave the sitemap as forwards.
- Verify: check.py new step "One shoe, one page": over each live registry, no two live slugs share slugify(base_model) after the rule, and no live page is named
  only brand + gender. Spot checks: /shoes/new-balance-fresh-foam-x-880v15/ forwards to /shoes/new-balance-880v15/ which lists the stores of both (BlackToe, Running Room,
  Endurance, City Park...); /shoes/asics-gt-2000-14/ has a "Women's · wide" table; /shoes/new-balance-rebel-v5/ shows "from $70.00"; sitemap /shoes/* count drops by the forwards.
- Metric + date: Search Console > Pages "Duplicate, Google chose different canonical than user" + "Alternate page with proper canonical" counts for /shoes/ and /us/shoes/
  (baseline: Bastien's Nov 9 screenshot); impressions on the surviving NB/ASICS pages. Check Nov 25 and Dec 9.

### S2. Flatten forwarding chains and never forward onto a noindex page  [BUG: redirect chains, dead-end forwards]
- Generator: shoe_pages.py `forward_old()` (CA + US), after all `to` are set; S1 will create more forwards, so run this after S1.
- Rule: resolve every `to` to its final live slug (follow `to` until a slug without `to`; stop on a loop and log it). If the final slug is stale/noindex
  (never seen or 14+ days) AND a live slug has the same slugify(base_model) after S1, point to that live slug instead. Written forward HTML (canonical + refresh)
  uses the resolved target.
- Tonight: CA 2 chains, US 6 chains, US 4 forwards onto noindex pages (asics-corp-cumulus-27/-28, -kayano-32, -nimbus-28 -> the asics-gel-* live pages).
- Verify: check.py step "Forwards land on a live page": every `to` in both registries is a slug with no `to` whose URL is in the sitemap. 0 hops of 2.
- Metric + date: Search Console > Pages "Page with redirect" stays flat while "Redirect error" stays 0. Check Dec 1.

### S3. Twin the hiking boots and hiking hubs across Canada and the US  [BUG (invisible, head tags only)]
- Generator: shoe_pages.py `hreflang_sync()` (runs after every builder) + `build_hike()` / `hike_main()` and hike_pages.py hubs.
- Rule: a boot slug live and indexable in BOTH hiking-boots/pages.json and us/hiking-boots/pages.json = one twin set {en-CA /hiking-boots/x/, fr-CA /bottes-randonnee/x/,
  en-US /us/hiking-boots/x/, x-default = en-CA}, same as running model pages. Hubs: /hiking-boots/ + /bottes-randonnee/ + /us/hiking-boots/, and /hikes/ + /randonnees/
  + /us/hikes/ become twin sets (like /races/ + /courses/ + /us/races/ today). Never name a noindex page.
- Tonight: 22 boot slugs on both sides, 0 twinned; the 2 hub trios not twinned.
- Verify: the existing guard "Language twins name each other back" covers it; add: every slug in both boot registries has an en-US link on its CA page.
- Metric + date: Search Console Performance by country: share of US clicks landing on /hiking-boots/ (CA) pages should fall. Check Dec 9.

### S4. Distinct titles on the US race + hike pages  [NEEDS-OK: visible title text]
- Generator: race_pages.py title builder (US side `/us/races/`), hike_pages.py (US side `/us/hikes/` + hub).
- Text (US side only; CA/FR unchanged):
  - Race: "{race} mandatory gear list ({distances})" -> "{race} mandatory gear list ({distances}), US stores"; suggested lists:
    "{race} gear list: what the race suggests ({distances})" -> "{race} gear list: what the race suggests ({distances}), US stores".
  - Hike: "{hike} gear list: what to bring" -> "{hike} gear list: what to bring (US stores)".
  - Hubs: "Race gear lists: mandatory gear, item by item" -> "Race gear lists: mandatory gear, item by item (US stores)";
    "Trail gear lists: what to bring for {n} hikes" -> "Trail gear lists: what to bring for {n} hikes (US stores)".
  - H1 unchanged. No French (US side is English only).
- Why: 134 page pairs have word-for-word identical titles on both sides; hreflang separates them, but a distinct title tells both Google and the searcher which
  stores and currency they'll see (Search Central, "Influencing title links": unique, descriptive titles per page).
- Verify: no title in the sitemap is shared by two URLs except EN pages that are not twins (check.py: count duplicate <title> across sitemap pages = 0 for twin sets).
- Metric + date: Search Console impressions + CTR for /us/races/* (baseline Nov 9). Check Dec 9.

### Not a spec: L1 + L5a/b (Nov 4) are still open
They're unchanged since Nov 4. After S1 lands, L1's ring also stops sending "More ASICS shoes" links to duplicates and noindex pages. Ask backend for L1 + L5a/b in
the same push as S1/S2: all are invisible.

## Bastien (2 lines)
Indexing is clean: all 2,826 pages in the map answer, none is hidden from Google by mistake, and the language links all point at each other.
The real problem: about 50 shoes have two pages each (New Balance "880v15" and "Fresh Foam X 880v15", ASICS "Cumulus" and "Gel-Cumulus", women's wide split onto "- Large" pages), so each page shows only part of the stores. Fixing that is a bug fix, no new pages.
