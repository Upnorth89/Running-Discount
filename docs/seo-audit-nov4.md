# The Gear Fox: SEO audit, night of Nov 3-4, 2026 (seo-lead)

Evidence base: the live sitemap (2,811 URLs, fetched Nov 4 ~05:30 UTC), 95 live pages across every page type (1.5 s apart),
the live page registries (shoes/pages.json, us/shoes/pages.json, hiking-boots/pages.json, us/hiking-boots/pages.json), sale.json,
and the generators (scraper/shoe_pages.py, race_pages.py, hike_pages.py, gift_pages.py, bf_live.py). No Search Console export
tonight: Oct 19 snapshot only (about 98 clicks in 3 weeks, nearly all "the gear fox"; shoe queries at positions 30-70; on-cloudboom-max
pos 3, /shoes/ 4, /running-shoes-sale/ 6.5, /brands/asics 7). Bing Oct 23: 2.3K discovered, 5 indexed, no backlinks.
No search volumes are quoted anywhere below. Where I rank things by "expected impact", that ranking is my estimate.

## What the site looks like to Google today (the facts behind the specs)

- Sitemap: 2,811 URLs. /shoes 665 + /chaussures 665 + /us/shoes 662, hikes 85+85+86, hiking-boots 80+80+74, races 49+49+50,
  sale hubs + size pages 32+32+33, brands 23+23+19, BF/BF live/Boxing Day/gifts 13. Every lastmod = 2026-11-04 (all 2,806 that
  have one); 5 entries have no lastmod (BF live x2, gifts x3).
- Model pages: title "X Sale Canada: from $Y (−Z%)", unique description, self canonical, H1 = model name, Product + AggregateOffer
  (+ image since Oct 26), FAQPage, BreadcrumbList, WebPage dateModified. 450-850 words. About 55 KB of HTML. Solid template.
- Internal links on model pages (15 CA, 5 FR, 7 US sampled): links to same-brand models, brand page, /shoes/, /races/, the menu.
  **ZERO links to /black-friday/, /running-shoes-sale/ or any type/size hub, on every one of them.** Model pages are ~2,000 of
  our 2,811 sitemap pages. Today /black-friday/ is linked only from the ~160 list/brand/size pages and the homepage SEO block.
  /black-friday/live/ is linked only from the 2 BF pages.
- Hreflang is one-way between Canada and the US: a US model page says "en-CA twin = /shoes/x/", but /shoes/x/ never names
  /us/shoes/x/ (444 US model pages with a live Canadian twin). Same on the 19 US brand pages. US hubs, size pages, BF and gift
  pages never name their fr-CA twin, while the French pages name the US page. Google ignores annotations without a return link.
- Black Friday page (pre-week mode until Nov 19): title "Black Friday 2026 running shoe deals in Canada: what to expect",
  582 words, 6 deals, no structured data. On Nov 20 the title, H1 and list all switch: Google sees a new page right when it matters.
- French race titles have a grammar bug: "Matériel obligatoire de l'Rothrock by UTMB", "de l'Canyons…" (6 races, utmb_race() default de="de l'").
- Brand pages exist for hiking brands under "running shoes": "Keen Sale Canada: 3 running shoes on sale" (191 words, Keen Targhee
  is a hiking boot), Lowa (225 words). (Rossignol checked: its 4 models are trail runners, so its page is fine.)
- Forwarding pages (CA 82 slugs x 2 languages, US 372): noindex + canonical + 0-second meta refresh.
- Homepage: title "The Gear Fox | Running deals in your size", 2 H1s (one empty, #rdH1), 345 KB HTML, loads sale.json
  (1.30 MB sent, 8.05 MB unpacked, 9,691 items; CLAUDE.md lab: 2.6 s of phone CPU just to process it).

---

## 1. TOP 10 changes, ranked by expected search impact before Black Friday

### #1 Link every running page to Black Friday and the sale hubs (biggest gap, cheapest fix)
- Pages: every model page (/shoes/*, /chaussures/*, /us/shoes/*), plus the ☰ menu on every generated page and the homepage.
- Generator: scraper/shoe_pages.py `model_page()` (end, after the "More {brand} shoes" list) and `menu_links()`; site/index.html menu (like `giftMenu()`); `home_section()`.
- Rule:
  a) model_page(): append `browse_nav(L, [])` after the related-brand list (same row the list pages already have: 6 sale hubs,
     Black Friday, Boxing Day (CA only), All shoe models, Race gear lists). Boot pages already get the hiking version from browse_nav.
  b) menu_links(): a seasonal item right after "Race gear lists", running side only, from ship date to Dec 1 (Vancouver date), same
     pattern as `gift_season()`: EN "Black Friday 2026" -> /black-friday/, FR "Vendredi fou 2026" -> /vendredi-fou/,
     US "Black Friday 2026" -> /us/black-friday/. Dec 2 - Jan 3: swap for "Boxing Day" / "Boxing Day" -> /boxing-day/ + /soldes-apres-noel/
     (Canada only). Homepage menu: the same item (#mBF), same dates; add it to the site test "Homepage: every button does something".
  c) home_section() nav line: add the deal check link after Black Friday: EN "Black Friday deal check" -> /black-friday/live/,
     FR "Vérification Vendredi fou" -> /vendredi-fou/direct/ (Canada copies only).
- Why: Google Search Central (links, "SEO starter guide"): links are how Google finds pages and judges which ones matter. Our
  ~2,000 model pages send 0 links to the page we need to rank in 3 weeks. Sample: 27/27 model pages, 0 links to /black-friday/.
- Visible change (a link row + a menu item): needs Bastien's yes under the freeze. It's a links-only change, no new page or feature.
- Verify: night scan, every /shoes/* page contains href="/black-friday/" (CA), "/vendredi-fou/" (FR), "/us/black-friday/" (US);
  check.py "no noindex page in sitemap" still passes; menu item gone after Dec 1.
- Metric: Search Console > Links > Internal links for /black-friday/ (today ~160 pages -> 2,000+); Performance for /black-friday/ +
  /vendredi-fou/ impressions. Check Nov 18 and Dec 2.

### #2 Seasonal Black Friday wording on model + brand pages (Nov 10 - Dec 1)
- Pages: model pages on sale (sm["off"] >= 10) and brand pages, CA EN/FR + US.
- Generator: shoe_pages.py `T["en"]/T["fr"]/US` strings, `model_page()` title line, `brand_title()`; date window helper like gift_season(): `bf_season()` = Nov 10 - Dec 1 Vancouver date.
- Text (old -> new, only inside the window, only when on sale 10%+; otherwise today's title stays):
  - EN CA titleSale: "{name} Sale Canada: from {price} (−{p}%)" -> "{name} Black Friday price check, Canada: from {price} (−{p}%)"
  - FR titleSale: "{name} en solde au Canada : dès {price} (−{p} %)" -> "{name} : prix du Vendredi fou au Canada, dès {price} (−{p} %)"
  - US titleSale: "{name} Sale: from {price} (−{p}%)" -> "{name} Black Friday price check: from {price} (−{p}%)"
  - brandTitle EN: "{brand} Sale Canada: {n} running shoes on sale, up to {p}% off" -> "{brand} Black Friday Canada: {n} running shoes on sale, up to {p}% off";
    FR: "{brand} en solde au Canada : …" -> "{brand} au Vendredi fou : {n} chaussures de course en solde au Canada, jusqu'à {p} % de rabais";
    US: "{brand} Black Friday: {n} running shoes on sale, up to {p}% off".
  - One visible line under the hero facts on model pages (all pages, on sale or not), linking to the BF page:
    EN "Black Friday is November 27. We check this shoe's price twice a day: watch it and we'll email you if it drops in your size. Black Friday deals →"
    FR "Le Vendredi fou tombe le 27 novembre. On vérifie le prix de cette chaussure deux fois par jour : suivez-la et on vous écrit si elle baisse dans votre pointure. Aubaines du Vendredi fou →"
    US same as EN, link /us/black-friday/.
  - Dec 2: titles back to normal automatically (window ends). Optional Canada follow-up Dec 14 - Dec 31: "Boxing Day price check".
- Why: people search "<model> black friday" and "<brand> black friday canada" (no volume numbers: I'm saying the queries exist, not
  how big they are). The title is the strongest on-page relevance signal we control; our model pages already rank 30-70 for the plain
  model query and brand pages ~7 (asics). The wording says "price check", not "sale": we don't claim the store runs a Black Friday promo.
  Compliance must PASS the wording before it ships (team rule).
- Verify: on Nov 10, /shoes/<on-sale model>/ title contains "Black Friday"; a model at full price keeps "price in Canada"; Dec 2 rebuild reverts.
- Metric: Search Console queries containing "black friday" (EN) / "vendredi fou" (FR): impressions + clicks on /shoes/*, /chaussures/*,
  /brands/*; baseline = Oct 27 - Nov 9. Check Nov 20 (crawled? URL Inspection on 5 models) and Dec 3 (results).

### #3 One stable title + H1 for the seasonal pages, starting now
- Pages: /black-friday/, /vendredi-fou/, /us/black-friday/, /black-friday/live/, /vendredi-fou/direct/, /boxing-day/, /soldes-apres-noel/, gifts x3.
- Generator: shoe_pages.py strings bfTitlePre/bfTitle/bfH1Pre/bfH1, bdTitlePre/bdTitle; bf_live.py `PATHS` (title = H1); gift_pages.py `S[...]["title"]`.
- Text:
  - bfTitlePre AND bfTitle (EN): "…: what to expect" / "Black Friday 2026 running shoe deals in Canada" -> both "Black Friday 2026 Running Shoe Deals in Canada"
  - bfH1Pre EN: "Black Friday 2026 in Canada: November {date}" -> "Black Friday 2026 running shoe deals in Canada: November {date}"
  - bfH1 EN (BF week): "Black Friday 2026: running deals in Canada" -> "Black Friday & Cyber Monday 2026: running deals in Canada"
  - FR bfTitlePre AND bfTitle: -> "Vendredi fou (Black Friday) 2026 : aubaines de chaussures de course au Canada"
  - FR bfH1Pre: "Vendredi fou 2026 au Canada : le {date} novembre" -> "Vendredi fou 2026 : aubaines de chaussures de course au Canada, le {date} novembre"
  - FR bfH1 (week): -> "Vendredi fou et Cyberlundi 2026 : aubaines course au Canada"
  - US bfTitlePre AND bfTitle: -> "Black Friday 2026 Running Shoe Deals at US Running Stores"; US bfH1 (week) -> "Black Friday & Cyber Monday 2026: running shoe deals"
  - bf_live EN: "Black Friday deal check, live" -> "Black Friday 2026 deal check: are these running deals real? (Canada, live)"
  - bf_live FR: "Vendredi fou : vraies et fausses aubaines, en direct" -> "Vendredi fou (Black Friday) 2026 : vraies et fausses aubaines course, en direct"
  - bdTitlePre AND bdTitle EN: -> "Boxing Day {y} Running Shoe Deals in Canada"; FR: -> "Boxing Day {y} : soldes d'après-Noël en chaussures de course au Canada"
  - Gifts CA EN: "Gifts for runners: under $25, $50 and $100" -> "Gifts for Runners in Canada: Under $25, $50 and $100" (US keeps its title: today CA and US titles are identical);
    FR: -> "Cadeaux pour coureurs au Canada : moins de 25 $, 50 $ et 100 $".
  - BF intro/description: lead with the topic instead of the countdown. EN bfIntroPre: "{days} days to go. Black Friday deals aren't out yet. …" ->
    "Black Friday is Friday, November 27 ({days} days to go). Until then, here are today's real prices from {n} Canadian running stores, checked twice a day. During Black Friday week this page lists that week's deals in every size."
    FR: "Le Vendredi fou (Black Friday) tombe le vendredi 27 novembre (encore {days} jours). D'ici là, voici les vrais prix du jour de {n} boutiques de course canadiennes, vérifiés deux fois par jour. Pendant la semaine du Vendredi fou, cette page affiche les aubaines de la semaine dans chaque pointure."
  - Pre-week list: show 24 deals instead of 6 (`bf_rows[:6]` -> `bf_rows[:24]`), still under the "Not Black Friday yet: today's best…" heading (honest label stays).
- Why: the URL should collect signals for one stable topic for 3 weeks; today the title/H1 flip on Nov 20, exactly when Google must
  already trust the page. "What to expect" reads as an article, not deals. French Quebecers also type "black friday" (to confirm in SC:
  FR pages' queries), so the FR title carries both names. Gifts: CA + US titles are the same string today.
- Verify: titles on the 10 URLs match the new text today AND after the Nov 20 switch (check.py could assert bfTitlePre == bfTitle).
- Metric: Search Console Performance, page = /black-friday/, /vendredi-fou/, /black-friday/live/: impressions, avg position for queries containing
  "black friday" / "vendredi fou". Check Nov 18, Nov 30, Jan 5 (Boxing Day).

### #4 Fix hreflang so Canada and US pages point at each other (technical, invisible: ship as a bug fix)
- Pages: 444 CA model pages (EN+FR) whose US twin is live and indexable; 19 brand pairs; FR <-> US on hubs, size pages, BF, gifts.
- Generator: shoe_pages.py `alternates()` (and the callers in `main()` / `build_us()`, gift_pages.py, size_pages()).
- Rule: every page in a twin set lists ALL members, itself included: en-CA, fr-CA, en-US (when the US page exists and is not noindex),
  x-default = en-CA (keep today's choice). CA model page: add `<link rel="alternate" hreflang="en-US" href="/us/shoes/<slug>/">` when
  slug is live in us/shoes/pages.json and not in the US NOINDEX set. US pages: add fr-CA = the French twin (/chaussures/<slug>/,
  /marques/<b>/, /chaussures-course-solde/…, /vendredi-fou/, /cadeaux-coureurs/). Never point at a noindex or forwarded page
  (today a US page can name a Canadian page that is noindex). Needs the US registry read before the Canadian pages are written.
- Why: Google Search Central, "Localized versions of your page": "If two pages don't both point to each other, the tags will be ignored."
  Without it Google may treat /shoes/x/ and /us/shoes/x/ as duplicates and show the USD page to Canadians (or fold one into the other).
- Verify: check.py step: for every sitemap URL, each hreflang target lists the source back (reciprocity) and is in the sitemap.
- Metric: Search Console > Pages: "Duplicate, Google chose different canonical than user" count for /us/shoes/* and /shoes/* (watch it fall);
  Performance by country: share of Canadian clicks landing on /us/. Check Nov 25.

### #5 US Black Friday page: add the price-data section (it has 436 words vs 582 CA)
- Page: /us/black-friday/. Generator: shoe_pages.py `bf_stats()`/`bf_data()` (CA only today) + build_us().
- Rule: run the same compute on deals-us.json with the "us|" history keys (US history since Oct 6), US strings:
  "{pct}% of running shoe models at US running stores are on sale right now ({on} of {shoes}, at {shops} stores)." /
  "Your size is the catch: a women's size 8 can buy only {w8}% of those sale shoes, a men's size 9 only {m9}%." /
  "{same}% of the shoes on sale today were already at that price or lower two weeks ago ({back})." / brands line. No history = no section (same rule).
- Why: the US BF page has nothing Google can't find on 100 other pages; our own data is the only unique content we have (helpful content guidance: original information).
- Verify: section renders with sane numbers (check.py BF step for the US side). Metric: SC impressions for /us/black-friday/; check Dec 2.

### #6 Sitemap lastmod = the day the page really changed
- Generator: shoe_pages.py `main()` sitemap writer (+ race/hike/gift/bf_live appenders); tools/indexnow.py already fingerprints every page's visible text minus dates.
- Rule: keep per-URL `{fingerprint, changed}` (the IndexNow cache, or a small file on the history branch); lastmod = `changed`. Give the 5
  entries without lastmod one. Cache lost = today for all (as now).
- Why: Google (Build and submit a sitemap): lastmod is used only when "consistently and verifiably accurate". 2,806 of 2,806 say today, every day,
  so it carries no signal; Bing leans on lastmod more than Google. Real dates point crawlers at the pages that did change (prices moved).
- Verify: sitemap shows a spread of dates; a model whose price changed shows today. Metric: Bing Webmaster indexed count (5 on Oct 23); SC crawl stats. Check Nov 30.

### #7 Homepage title + description (our strongest page)
- File: site/index.html <title>, meta description, og:title (static; backend edit).
- Text: "The Gear Fox | Running deals in your size" -> "Running Shoes & Gear on Sale in Your Size | The Gear Fox".
  Description -> "Running shoes and gear on sale in your size from 150+ stores in Canada and the US, checked twice a day. Free price-drop alerts. Outfox full price."
  (150+ matches the Organization JSON-LD; sale.json n_stores = 170 today.) Remove the empty second H1 (#rdH1) or make it a div. Keep the brand in the title.
- Why: the homepage has the most links in (every page's logo + menu). Its title names no product. Brand queries still match ("The Gear Fox" stays in the title).
- Metric: SC homepage impressions for non-brand queries (query not containing "gear fox"). Check Nov 25.

### #8 French race title bug (trust bug: fix now)
- Generator: race_pages.py `utmb_race()` calls for canyons-endurance-runs, desert-rats, rothrock, speedgoat, snowbasin, grindstone (default de="de l'", le="l'").
- Rule: pass de="du ", le="le " for those 6 (Ultra-Trail Whistler and Ultra Trail Chattanooga keep "de l'"). Result: "Matériel obligatoire du Rothrock by UTMB".
  Guard in check.py: no FR title/H1 matches `de l'[^aeiouyhéèêAEIOUYHÉ]` or `l'[^aeiouyhéèêAEIOUYHÉ]`.
- Why: broken French in the title + H1 of 6 indexed FR pages (and on Google's result). Verify: grep the 6 /courses/ pages.

### #9 Forwarding pages: drop noindex, keep canonical + 0 s refresh; forward never-stocked US duplicates
- Generator: shoe_pages.py `forward_old()` (written HTML) + build_us().
- Rule: forwarding HTML = canonical + `<meta http-equiv="refresh" content="0; url=…">` + link, no `noindex`. Also forward_old: try the
  "gel-" form for ASICS ("asics-kayano-32" -> "asics-gel-kayano-32", cumulus/nimbus likewise) and "-men-s"/"-women-s" suffixes
  (us: on-cloudsurfer-max-men-s, mizuno-wave-rider-30-women-s): today these sit as noindex "never in stock" pages instead of forwarding.
- Why: Google treats an instant meta refresh like a permanent redirect (Search Central, "Redirects and Google Search"); a noindex on the same
  page is a contradictory signal, and links that point at old slugs are better passed on than dropped. 536 forwarding files today (CA 82 x2, US 372).
- Verify: forwarded pages have no robots meta; sitemap still excludes them. Metric: SC "Page with redirect"/"Excluded by noindex" counts; check Dec 1.

### #10 Running brand pages only for running brands; sale hubs lead with real sizes
- Generator: shoe_pages.py `main()` (`brands` list), `kinds` sort.
- Rule a: a brand gets a running brand page when 3+ of its live models are NOT t == "hike" (today Keen and Lowa pass on hiking
  shoes and get "N running shoes on sale" titles, 191-225 words). Existing pages for brands that drop out: keep the URL, noindex,follow
  + out of the sitemap (same as the stale rule), never delete.
- Rule b: on /running-shoes-sale/* hubs, models with 6+ sizes first (as the BF list already does), then the rest; today the first cards are
  "Brooks Hyperion, 3 sizes · 2 stores" style clearance.
- Why: Google helpful content: a page should satisfy the visitor who lands there; mislabeled thin pages and odd-size-first lists don't.
- Verify: /brands/keen/ noindex + gone from sitemap; hubs' first 10 cards all 6+ sizes. Metric: SC position for /running-shoes-sale/ (6.5 on Oct 19). Check Dec 1.

---

## 2. Black Friday SEO plan

Deadline: ship #1-#5 by **Mon Nov 9**. The morning run's IndexNow job sends every changed page to Bing the next morning. Bastien asks
Google to recrawl the key URLs on **Nov 10** (Search Console > URL Inspection > Request indexing, about 10 a day: /black-friday/,
/vendredi-fou/, /black-friday/live/, /vendredi-fou/direct/, /us/black-friday/, /gifts-for-runners/, /running-shoes-sale/, /brands/hoka/,
/brands/asics/, /shoes/). Check on **Nov 18-20** that Google shows the new titles (URL Inspection "crawled" date). Boxing Day: same by Dec 5.

| Query family (no volumes; winnability = my estimate) | Page | What it lacks today | Fix |
|---|---|---|---|
| "<model> black friday", "<model> sale canada" (long tail; best odds: many models, retailers' pages are the competition) | /shoes/<slug>/ (+ /chaussures/, /us/shoes/) | No mention of Black Friday anywhere; no link to the BF page | #2, #1 |
| "<brand> black friday canada", "hoka sale canada" (brand pages already ~pos 7 for asics) | /brands/<b>/ | No BF wording; FR brand pages same | #2 |
| "black friday running shoes canada", "black friday running deals canada" (hard: Sport Chek, brands, Canadian Running, BlackToe rank today) | /black-friday/ | "What to expect" title that flips Nov 20; 6 deals; ~160 internal links, 0 from model pages; no backlinks | #3, #1; backlinks (section 4) |
| "vendredi fou chaussures de course", "black friday chaussures de course" (French results looked thinner: Brooks fr_ca, Altra fr-ca, French .fr sites; my best guess for a head term we can win) | /vendredi-fou/ | Title lacks "Black Friday"; FR model/brand pages don't link it | #3, #1, #2 |
| "are black friday deals real", "fake black friday sales canada" (our unique data; the press angle) | /black-friday/live/ + /vendredi-fou/direct/ | Title has no searchable words; linked only from 2 pages | #3, #1c; pitch it to press as the link target |
| "cyber monday running shoes canada" | /black-friday/ (BF week mode runs to Cyber Monday) | Never says "Cyber Monday" | #3 (BF-week H1) |
| "boxing day running shoes canada", "soldes après Noël chaussures course" | /boxing-day/ + /soldes-apres-noel/ | "What to expect" title flips Dec 19; no menu link | #3, #1b (Dec 2 swap); by Dec 5 |
| "gifts for runners canada", "gifts for runners under 50" | /gifts-for-runners/, /cadeaux-coureurs/, /us/gifts-for-runners/ | CA title has no "Canada" and equals the US title; menu link only from Nov 15 | #3 |
| "black friday running shoes" (US; very hard vs US media) | /us/black-friday/ | No data section (436 words), no deal check | #5; aim at US model long tail instead |

Structured data: no new markup unlocks a rich result here. FAQPage rich results are limited to government/health sites since Aug 2023,
and ItemList carousels don't cover deal lists like ours. Keep Product/AggregateOffer on model pages (product snippets: price range);
adding BreadcrumbList to list/BF pages is harmless but low value. The levers before BF are titles, internal links and backlinks.

## 3. Indexation hygiene (counts from tonight)

- Sitemap: 2,811 URLs, no forwarding page and no noindex page in it (checked against the registries). All lastmod = today (#6); 5 without lastmod.
- Canadian model pages (shoes/pages.json): 753 slugs = 82 forwarded + 671 live: 658 in stock Nov 3-4, 7 out of stock 1-13 days (indexable,
  "Not in stock" text), 6 noindex (never seen in stock / 14+ days). The Oct 23 night scan's 114 "Not in stock" pages are now down to 7 indexable: the Oct 24 rule works.
- US model pages: 1,047 slugs = **372 forwarded** + 675 live: 641 in stock, 20 out 1-13 days, 14 noindex (incl. asics-kayano-32,
  asics-nimbus-28, asics-cumulus-27/28: name variants that should forward, #9).
- Boot pages: CA 80 / US 73, all in stock.
- Forwarding: 536 files with noindex + canonical + meta refresh (#9).
- Hreflang: 444 US model pages + 19 US brand pages one-way; FR <-> US missing on hubs/size/BF/gifts (#4). US hubs /us/hikes/, /us/hiking-boots/
  list only themselves (fine, but the CA hubs don't name them either: add en-US both ways when touching #4).
- Duplicate titles across sides: /races/ = /us/races/, /hikes/ = /us/hikes/, /gifts-for-runners/ = /us/gifts-for-runners/ (hreflang'd, but
  distinct titles are cleaner: add "(US stores)" on the US ones).
- Thin/mislabeled: Keen and Lowa running brand pages (#10).
- French grammar: 6 FR race pages "de l'Rothrock…" (#8).
- Size pages (32 CA EN + 32 FR + 33 US): useful, but neighbours overlap heavily (size 10 vs 10.5). Watch "Duplicate, Google chose different
  canonical" for /size-*/ in Search Console; no change without data (Oct 24 decision stands).
- Robots: fine. sale*.json open (Google renders the homepage with it), deals*/offers blocked, /?watch= links nofollow, ?show=/?ref= URLs canonical to /.
- Page speed red flags: homepage HTML 345 KB + sale.json 1.30 MB sent / 8.05 MB unpacked (9,691 items) before deals show; 2.6 s phone CPU (Oct 27 lab).
  Model/list pages are light (45-78 KB HTML) and readable without script, so this matters for homepage experience, much less for ranking
  the pages we need. Google Fonts CSS blocks rendering on every page (minor). No change before BF; Fox Pro/perf work later.
- Two H1s on the homepage (one empty) (#7).

## 4. Backlinks: 15 realistic targets

Already contacted (don't re-pitch, follow up only): Sinister Sports (Kirsti; call Oct 28; 8 races incl. Moose Mountain/Canmore referrals),
Fat Dog 120 (wrote back Nov 3 about errors: fixed; ask once trust is restored), Chic-Chocs, Harricana (follow-ups due Oct 30: check the tracker).
Press wave 1 being sent by Bastien: Canadian Running, Daily Hive Vancouver, Happiest Outdoors, MobileSyrup, iRunFar, Believe in the Run,
Distances+; wave 2 (week of Nov 16): CBC Marketplace, MoneySense, Narcity Québec, Protégez-vous. The 13 organizer drafts are in artifact 4tD4v4AWgXWrW6zohytTuN.

| # | Target | Page that would link | Our page | Why they'd want to | Status |
|---|---|---|---|---|---|
| 1 | Iron Legs / Racing Dusk 20 Miler (ironlegs.ca) | Racing Dusk race page or participant info (race Dec 19, 2026) | /races/racing-dusk/ + /races/iron-legs/ | Race in 6 weeks; our page lists their 7 mandatory items with prices in each runner's size | Not contacted. Most timely |
| 2 | Trail Whisperer (trailwhispererbc.ca), Frosty Mountain Ultra | Frosty gear checklist page | /races/frosty-mountain-ultra/ | Their PDF checklist turned into a tickable list | Not contacted |
| 3 | Lewiston Ultra Events (Moose Mountain) | Race info page | /races/moose-mountain/ | Referred by Sinister Sports: warm intro | Not contacted (built Nov 3) |
| 4 | 5 Peaks (5peaks.com), Canmore Ultra | Canmore Ultra page / series FAQ | /races/canmore-ultra/ | Series with many BC/AB races: one yes can lead to more lists | Not contacted (built Nov 3) |
| 5 | Ultra-Trail du Fjord du Saguenay | Matériel obligatoire page | /courses/ultra-trail-du-fjord-du-saguenay/ | French list, same race distances as theirs | Drafted Oct 23, not logged as sent |
| 6 | Québec Mega Trail (ultratrailcanada.com) | Gear / runner info | /courses/quebec-mega-trail/ | Same | Drafted, not logged as sent |
| 7 | Bromont Ultra | Matériel obligatoire | /courses/bromont-ultra/ | Same | Drafted, not logged as sent |
| 8 | La Chute du Diable, Ultra-Trail Sayam (Québec) | Their race guide pages | /courses/la-chute-du-diable/, /courses/ultra-trail-sayam/ | Same | Not contacted |
| 9 | Destination Trail (Tahoe 200, Bigfoot, Moab 240, Arizona Monster, El Jefe, Tahoe 100K) | Runner manual / race pages (one email, 6 races) | /us/races/tahoe-200/ etc. | Their manuals are Google Docs; a clean shoppable checklist per race | Not contacted |
| 10 | Aravaipa (Cocodona 250) | Runner info | /us/races/cocodona/ | Biggest-name US race we list; its required list is long | Not contacted |
| 11 | Mammoth 200, Massif Running (Twisted Fork) | Runner manual pages | /us/races/mammoth-200/, /us/races/twisted-fork/ | Massif sent us its doc (Oct 23): warm | Not contacted (check if Bastien replied to Massif) |
| 12 | Coast Mountain Trail Running (Run Ridge Run) | Sponsors/partners or race info | homepage /?ref=… or /races/ | Bastien ran Run Ridge Run 25K (his About photo): a runner asking his own race | Not contacted; no gear list page (no list exists to build) |
| 13 | Run Canada Podcast (Kirsten Parker) | Episode show notes | homepage + /black-friday/live/ | Black Friday price-data story: "71% of sale prices were already this low 2 weeks ago" (Oct 27 figure: refresh it from the live page before pitching) | Not contacted |
| 14 | Athletics Ontario Running Podcast | Episode show notes | homepage + /black-friday/live/ | Same story, Ontario angle (Running Free, BlackToe tracked) | Not contacted |
| 15 | The press wave (Canadian Running first) | BF roundup articles | /black-friday/live/ (not the homepage) | Unique Canadian data; give them the live page as the citation | Pitched: make sure the pitch links /black-friday/live/ |

Rule for every ask: one small yes first (correct list / add partners), the link asked after (Oct 26 decision). A link from a race's own gear page is
the strongest signal we can earn this month (topic match + real site); press links are the biggest prize for /black-friday/.

## 5. Nightly SEO routine (one agent run, ~150 fetches)

1. Fetch sitemap.xml: count URLs per type vs last night (file in scratchpad/night/seo-state.json); list new/removed URLs; flag any URL
   that is forwarded, noindex or non-200 (sample).
2. Fixed set every night (~20 pages): /, /running-shoes-sale/, the 4 BF pages, 2 BF live, 2 Boxing Day, 3 gift pages, /shoes/, /races/,
   on-cloudboom-max, /brands/asics/, /brands/hoka/. Rotating set (~100): 30 /shoes/, 10 /chaussures/, 20 /us/shoes/, 10 races, 10 hikes, 10 boots,
   10 hubs/size/brand pages (seeded by date so a week covers ~700 pages).
3. Per page: status, title (length, today's price matches the table, seasonal wording only in its window), description, canonical = self,
   robots, hreflang reciprocity (each target lists us back and is in the sitemap), H1 count, JSON-LD parses (Product has image + lowPrice),
   FR checks (elision regex, English words in FR titles), links to /black-friday/ present after #1 ships.
4. If Bastien uploaded Search Console/Bing exports (docs/ or saved-pages/seo/): positions for the tracked pages vs last week; pages 8-20 that
   could move with a title or link change; new queries containing black friday / vendredi fou / boxing day.
5. Output: one short note (max 10 lines) to the growth chat: "SEO night: N pages checked, N problems (list), 1 change worth doing (spec)".
   Bugs go to the backend as specs; nothing else. Monday: fold the week into the ranked list.
Steps 1-3 are deterministic: worth asking the backend for `tools/seo_check.py` run inside night-scan.yml (emails only on problems), so the
agent run is about reading Search Console and deciding, not fetching.
