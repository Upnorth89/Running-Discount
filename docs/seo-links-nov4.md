# SEO night, Wed Nov 4: INTERNAL LINKS (seo-lead)

This builds on docs/seo-audit-nov4.md and docs/seo-log.md and doesn't repeat them.
Evidence:
- the live sitemap (2,811 URLs, fetched Nov 4 ~08:00 UTC);
- 81 live pages fetched 1.5 s apart, covering every page type (raw HTML in scratchpad/night/links/html/, parsed links in links/parsed.json, parser in night/linkparse.py);
- the live registries shoes/pages.json and us/shoes/pages.json, used to simulate the "More {brand} shoes" rule over all 1,346 model pages;
- the generators: shoe_pages.py, race_pages.py, hike_pages.py, gift_pages.py, bf_live.py.

No new Search Console export, so the Oct 19 snapshot is still the only ranking data. No search volumes are quoted. Impact ranking is my estimate.

## 1. Link map by page type (live, Nov 4)

Unique internal links per page. Footer and menu are included. Store links, ?watch= and ?show= are not.

| Page type (sampled) | Links per page | Breadcrumb (visible / BreadcrumbList) | Links out to |
|---|---|---|---|
| Homepage (1) | 124 | no / no | 12 models + 12 brands per side (SEO block), /running-shoes-sale/, /black-friday/, /shoes/, hikes + boots hubs, race hub (menu, relative link) |
| /shoes/, /chaussures/, /us/shoes/ (3) | 686-689 | no / no | every model + browse row (6 sale hubs, BF, Boxing Day, races) |
| Model pages (19 CA/FR, 7 US) | **16 on every one** | yes / 17 of 19 (the 2 missing are out of stock) | /shoes/, brand page, up to 8 same-brand models, home, /races/ (menu). **0 to any sale hub, BF or size page** |
| Sale hubs + gender/type hubs (5) | 113-133 | no / no | top 80 models, browse row, 23 brands, size menu (men/women only) |
| Size pages (3) | 127-133 | no / no | up to 80 models, sibling sizes, browse row, brands |
| Brand pages (6) | 48-105 | no / no | all the brand's in-stock models, browse row, brand row |
| BF / Boxing Day (4) | 40-47 | no / no | 6 deals, deal check, gifts, other side, browse row |
| BF deal check (2) | 18 | yes / no | BF page, model pages (?ref=bf-desk) |
| Gift pages (3) | **8** | no / no | home, Boxing Day (CA) or US BF (US), menu. **The CA/FR gift pages don't link Black Friday; the US one does** |
| Race pages (6) | **7-8** | yes, 1 level / no | race hub, twin, /?cat= links, menu. Shoe-page links exist only in a script (after the visitor picks a shoe), so Google can't follow them |
| Trail hike pages (5) | **7-8** | yes, 1 level / no | hike hub, boots hub, twin, menu |
| Boot pages (5) | 13-15 | yes / yes | boots hub, same-brand boots, hike hub |
| About (1) | 3 (relative) | no / no | home, privacy, terms |

Who links to the pages we need before Black Friday (out of 79 sampled pages):
- /black-friday/: 14 pages (home, /shoes/, sale hubs, brand pages, size pages). **None of the 26 model pages.**
- /black-friday/live/ and /vendredi-fou/direct/: **2 pages each** (the two BF pages). Sitewide, that's exactly 2 pages plus the twin.
- /gifts-for-runners/: 3 (/black-friday/, its FR twin, the US gift page). The menu item only starts Nov 15.
- Size pages: only the men's/women's hub of their own gender + sibling size pages.
- /races/: 33 (the menu on every running page).

**Orphans:** none. Every sitemap URL is linked from at least one page. The size pages I didn't reach are linked from the men's/women's hubs by construction (size_nav).
/brands/ and /marques/ return 404: there is no brand index, and brands are only reached through rows and breadcrumbs. That's fine; adding one would be a new page, so not during the freeze.
Report pages: hidden by design, as intended.

**Near-orphans** (one linking page type only):
- race pages (147): their hub;
- hike pages (256): their hub;
- gift pages (3): the BF pages;
- BF deal check (2): the BF pages;
- size pages (96): one hub.

### The big finding: "More {brand} shoes" piles its links onto the same few pages
model_page()'s related list is `sorted(same_brand, key=(other kind, slug))[:8]`. That gives every page in a brand+kind the same alphabetically first 8 models. I simulated it on tonight's live registries:
- **Canada: 303 of 671 live model pages (45%) get zero links from any other model page. USA: 336 of 675 (50%).**
- Meanwhile asics-cumulus-27 gets 55 links, and asics-gel-excite-11, asics-dynablast-5 and asics-gel-cumulus-26 get 48 each. Several of these are old or duplicate models: asics-cumulus-27 and asics-gel-cumulus-27 are the same shoe, which is audit #9.
- These get 0 today: ASICS Novablast 5, ASICS Gel-Nimbus 27, Brooks Ghost 17, Brooks Glycerin 22, Hoka Mach 6, Saucony Ride 18, Saucony Kinvara 15, On Cloudmonster 2. Hoka Clifton 10 gets 8 and On Cloudboom Max (pos 3 on Oct 19) gets 3.
- So the current models people actually search for reach Google only through the 686-link /shoes/ index, their brand page and, when they're on sale, a hub.

## 2. Strongest pages and where their strength should go

- **Strongest by links in:**
  - homepage: every page's logo, about 2,800;
  - /shoes/ + /chaussures/: every model page's breadcrumb + menu, about 2,000;
  - /races/: the menu;
  - brand pages: model breadcrumbs + the brand row on ~160 list pages.
- **Strongest by Oct 19 ranking:** /shoes/ pos 4, /running-shoes-sale/ 6.5, /brands/asics/ 7, /shoes/on-cloudboom-max/ 3.
- **Money pages before Nov 27:** /black-friday/ + /vendredi-fou/ + /us/black-friday/, /black-friday/live/ + /vendredi-fou/direct/ (the press-pitch target), the 6 sale hubs, brand pages ("<brand> black friday"), gift pages (from Nov 15).
- **What each needs:**
  - /shoes/ and the brand pages already pass strength to BF and the hubs through the browse row. They pass nothing to the deal check or the gift pages.
  - Model pages (2,000 of 2,811 URLs) pass nothing to any money page.
  - Race pages are where organizer backlinks will land (the backlink plan), and they pass that strength nowhere except their hub.

## 3. Specs, ranked by expected impact

### L1. "More {brand} shoes": neighbours instead of the alphabet  [INVISIBLE: same block, heading and look; only which 8 models. Can ship as a bug-level fix]
- **Generator:** scraper/shoe_pages.py. There are three copies of the same rule:
  - `main()` line ~1667-1668 (Canada EN/FR);
  - `build_us()` line ~1866-1867;
  - `build_hike()` line ~2041-2042 (boot pages).
- **Rule:**
  1. Eligible = the brand's live slugs (`known_live` / `live`). Leave out the page itself, forwarded slugs, and pages that are noindex today (stale). Compute `stale()` once in a pre-pass and reuse the result in the write loop: it writes `meta["seen"]`, so don't call it twice per page.
  2. Ring A = eligible slugs of the same kind `t` plus this slug, sorted by slug. Take the nearest neighbours, alternating 1 before, 1 after, 2 before, 2 after and so on, wrapping around the ends, up to 8.
  3. If that gives fewer than 8, fill from ring B (the brand's other kinds) the same way.
  4. Display order stays as today: same kind first, then by slug.
- **Result, simulated on tonight's registries:**
  - Canada: 303 -> 3 pages with zero model-page links. The 3 left are brands with a single model, which already have /shoes/ and the hubs.
  - USA: 336 -> 9.
  - Median 8, max 16 (was 55).
  - Each of Novablast 5, Ghost 17, Mach 6 and Ride 18 goes 0 -> 8.
  - For people, neighbours are the previous and next versions (Novablast 4 <-> 5, Ghost 16 <-> 17), which is what someone comparing a shoe wants.
- **Why:** Google Search Central ("Links", SEO starter guide): Google finds pages and judges which ones matter through links. Every page you care about should be linked from other pages, and today half our model pages are reachable only through one 686-link index. Oct 19 Search Console showed 411 pages discovered but not yet indexed. I expect weakly linked pages to be crawled less often; that's my estimate, not a Google promise.
- **Verify:**
  - New check.py step "Model pages link to each other". After the build, count `href="/shoes/<slug>/"` in the other /shoes/*/index.html files (same for /chaussures/ and /us/shoes/).
  - Every indexable model page whose brand has 2+ eligible models gets at least min(3, n-1) links in, and no page gets more than 16.
  - No related link points at a noindex page or a forwarding page.
  - Spot check: /shoes/brooks-ghost-16/ lists Ghost 17.
- **Metric + dates:**
  - Search Console > Links > Internal links: /shoes/brooks-ghost-17/ and /shoes/asics-novablast-5/ go from about 3 linking pages to 10+.
  - Search Console > Pages: indexed count under /shoes/ and /us/shoes/. Baseline: ask Bastien for the Nov 9 number.
  - Impressions for the 8 models listed above.
  - Check Nov 25 and Dec 9.

### L2. Model pages: one "On sale now" row to the matching hubs + Black Friday  [VISIBLE: this is the concrete form of audit #1a; needs Bastien's OK]
- **Change vs audit #1a:** instead of appending the full 11-link browse row, add one short row with 3-5 links that match the shoe. It gives Google more relevant anchors (link text naming the topic), adds less clutter, and sends the same strength to BF.
- **Generator:** shoe_pages.py `model_page()`. Put it right after the "More {brand} shoes" list, and also on out-of-stock pages (they're dead ends today). Use the existing `<nav class="browse">` style; no new CSS.
- **Links, in order:**
  1. Kind hub from `its[0]["t"]`: daily -> road, trail -> trail, race -> racing, anything else -> all. Text = `L["hubs"][k][0]`.
     - EN: "Trail running shoes on sale in Canada" -> /running-shoes-sale/trail/
     - FR: "Chaussures de course en sentier en solde au Canada" -> /chaussures-course-solde/sentier/
     - US: "Trail running shoes on sale" -> /us/running-shoes-sale/trail/
  2. Gender hub(s) for the cuts that have a table on the page (men's and/or women's; unisex = both). Text = `L["hubs"]["men"/"women"][0]`, e.g. "Women's running shoes on sale in Canada" / « Chaussures de course pour femme en solde au Canada ».
  3. Seasonal, Vancouver date:
     - Nov 1 - Dec 1: EN "Black Friday 2026 running shoe deals" -> /black-friday/; FR "Aubaines du Vendredi fou 2026" -> /vendredi-fou/; US "Black Friday 2026 running shoe deals" -> /us/black-friday/.
     - Canada only, same window: EN "Black Friday deal check" -> /black-friday/live/; FR "Vérification Vendredi fou" -> /vendredi-fou/direct/.
     - Dec 2 - Jan 3, Canada only: EN "Boxing Day running shoe deals" -> /boxing-day/; FR "Aubaines du Boxing Day" -> /soldes-apres-noel/. The US shows no seasonal link then.
  4. Row label (aria-label + a small bold lead-in): EN/US "On sale now", FR "En solde maintenant".
  5. Boot pages: none (browse_nav's hiking branch already covers them).
- **Copy:** the copywriter + compliance pass the 4 new strings. The rest are existing titles.
- **Why:** 26 of 26 sampled model pages carry exactly 16 links and none goes to a hub or BF. /black-friday/ is linked from ~160 pages, none of them model pages, which make up ~2,000 of 2,811 URLs.
- **Verify:**
  - Night scan: every /shoes/* page has href="/black-friday/" and its kind hub; /chaussures/* has "/vendredi-fou/"; /us/shoes/* has "/us/black-friday/".
  - The BF links are gone on Dec 2 (Boxing Day replaces them in Canada).
- **Metric + dates:**
  - Search Console Links, internal links to /black-friday/: ~160 -> 2,000+; to /running-shoes-sale/trail/ and /running-shoes-sale/women/: + about 600 each.
  - Impressions and position for /running-shoes-sale/ (6.5 on Oct 19) and /black-friday/.
  - Check Nov 18 and Dec 2.

### L3. The strong hubs feed the deal check and the gift page; the CA gift page links BF  [VISIBLE: folds into audit #1c; needs Bastien's OK]
- **Generators:**
  - shoe_pages.py `browse_nav()` (line ~1466). It runs on /shoes/ + /chaussures/, the 12 sale hubs, 64 size pages, 46 brand pages, BF and Boxing Day: about 165 CA/FR pages + the US set.
  - `home_section()` nav (line ~1589).
  - gift_pages.py page body (line ~170).
- **Rule:**
  - a) browse_nav: right after the Black Friday link, Nov 1 - Dec 1, Canada only: EN "Black Friday deal check" -> /black-friday/live/, FR "Vérification Vendredi fou" -> /vendredi-fou/direct/. Then, while `gift_season()` is on (Nov 15 - Dec 26): EN "Gifts for runners" -> /gifts-for-runners/, FR "Cadeaux pour coureurs" -> /cadeaux-coureurs/, US "Gifts for runners" -> /us/gifts-for-runners/.
  - b) home_section(): the same two links in each copy's nav line (EN, FR, US; the US copy gets gifts only).
  - c) gift_pages.py, CA and FR only (the US page already links /us/black-friday/), one line before the "box" line:
    - EN: `<p class="gf-box">Shopping for yourself too? <a href="/black-friday/">Black Friday 2026 running shoe deals →</a></p>`
    - FR: `<p class="gf-box">Vous magasinez aussi pour vous? <a href="/vendredi-fou/">Aubaines de chaussures de course du Vendredi fou 2026 →</a></p>`
- **Why:**
  - The deal check is the page we pitch to press (audit backlink #13-15), and it has 2 internal links in.
  - The gift page has the BF pages and its twin, nothing else, until Nov 15.
  - /shoes/ (pos 4) and /brands/asics/ (pos 7) are our strongest pages, and they already carry the browse row, so it's the cheapest place to add these links.
  - Today the CA and US gift pages are inconsistent (US links BF, CA links only Boxing Day).
- **Verify:**
  - Night scan Nov 5 - Dec 1: /shoes/, /running-shoes-sale/ and /brands/asics/ contain href="/black-friday/live/".
  - From Nov 15 they also contain "/gifts-for-runners/".
  - /gifts-for-runners/ contains "/black-friday/".
  - All of these links are gone after their window.
- **Metric + dates:**
  - Search Console Links: /black-friday/live/ 2 -> ~165 linking pages; /gifts-for-runners/ 3 -> ~165.
  - Impressions for both. Check Nov 20 and Dec 3.
  - Gift page sessions (ref=gifts clicks) in the funnel: Dec 3.

### L4. Race pages pass their organizer links on  [VISIBLE: after Nov 15 or with Bastien's OK; small]
- **Generator:** race_pages.py `page()`. Put it in the "Trail running shoes" line's section, in plain HTML next to where the JS shoe pick renders (the body starts at line ~1862).
- **Link (static, always shown):**
  - CA EN: "Trail running shoes on sale in Canada →" -> /running-shoes-sale/trail/
  - FR: "Chaussures de course en sentier en solde au Canada →" -> /chaussures-course-solde/sentier/
  - US: "Trail running shoes on sale →" -> /us/running-shoes-sale/trail/
  - Suggested lists: same link.
  - Add `?ref=race-<slug>` only to homepage links. This one stays a clean URL (a ref on it would make a duplicate URL).
- **Why:** race pages have 7-8 static links. The shoe-page links there exist only inside a script and appear after a visitor picks a shoe, so Google can't follow them. The backlink plan (audit section 4, targets #1-11) points every organizer at a race page, so those will become our only pages with outside links, and today that strength stops at the race hub. For people: someone checking mandatory gear is shoe shopping, and this is one tap to every trail shoe on sale.
- **Verify:** night scan: every /races/*, /courses/* and /us/races/* page contains its side's trail hub link. The site test "Race gear page…" still passes.
- **Metric + dates:**
  - Search Console Links, internal links to /running-shoes-sale/trail/: + about 147 pages.
  - Funnel "RACE GEAR LISTS": "% that went on to another page" (move vs the Nov 2-8 baseline).
  - Check Dec 9.

### L5. Breadcrumb data where the breadcrumb is already visible  [INVISIBLE for a + b; c is VISIBLE]
- **a) Model pages that are out of stock lose BreadcrumbList.** `crumbs_ld` sits inside `if sm:` in model_page(), lines ~1388-1396. Seen live on /shoes/nike-zoom-superfly-elite-2/ and /chaussures/: visible crumb, no data. Fix: build and emit crumbs_ld outside the `if sm:` block. FAQ and WebPage stay inside it.
- **b) Race (147), trail hike (256) and BF deal check (2) pages** show a one-level visible crumb with no BreadcrumbList.
  - Add JSON-LD matching what's visible: The Gear Fox (/) › the hub (`s['aisle']`, /races/ | /courses/ | /us/races/ | /hikes/ | /randonnees/ | /us/hikes/; deal check: the BF page) › page H1.
  - Generators: race_pages.py `page()` ~1862, hike_pages.py ~283, bf_live.py ~210.
- **c) Visible crumbs where there are none:**
  - Size pages: "Men's running shoes on sale in Canada › Size 10" (FR « Chaussures de course pour homme en solde au Canada › Pointure 10 »; US "Men's running shoes on sale › Size 10"), linking the gender hub. Generator: size_pages().
  - Brand pages: "All shoe models › ASICS" (FR « Tous les modèles › ASICS »). Generator: list_page() via an extra argument from the brand loop.
  - Plus BreadcrumbList for both.
- **Why:** BreadcrumbList is the one rich-result type the audit kept (Google's breadcrumb structured data docs). Honest limit: since January 2025 Google no longer shows breadcrumbs in mobile results, only on desktop, so this is the lowest-impact item. a + b are pure data fixes that match what's already on the page.
- **Verify:** check.py: every page with `class="crumbs"` also has a BreadcrumbList whose names match the visible crumb. Rich Results Test on 1 race page, 1 hike page and 1 out-of-stock model page.
- **Metric + dates:** Search Console > Enhancements > Breadcrumbs: valid items go up by about 400 (races + hikes) with no new errors. Check Nov 25.

## Not recommended tonight
- **A /brands/ index page:** new page, freeze. Brands are reachable from every list page's brand row anyway.
- **"Other races nearby" rows on race pages:** a new feature. Backlog it after Nov 15 if race-page sessions grow.
- **Rotating related links daily:** churn. Stable links are better; the ring rule in L1 is stable unless a model is added.

## Bastien (2 lines)
Half our shoe pages (303 of 671 in Canada, 336 of 675 in the US) get no links from our other shoe pages. That includes Novablast 5, Ghost 17, Mach 6 and Ride 18. A small fix to how "More ASICS shoes" picks its 8 models fixes it with nothing new on screen.
Two link rows still need your yes: one on shoe pages to the sale lists and Black Friday, and one sending our strongest pages to the deal check and the gift page. Those are links only, no new pages.
