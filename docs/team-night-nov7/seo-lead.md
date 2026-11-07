# SEO lead, night of Nov 7: Black Friday + gift pages readiness

Checked live (Nov 7, 02:00 UTC): /black-friday/, /vendredi-fou/, /black-friday/live/, /vendredi-fou/direct/, /us/black-friday/,
/gifts-for-runners/, /cadeaux-coureurs/, /us/gifts-for-runners/, plus homepage, /shoes/, /running-shoes-sale/, /brands/hoka/,
/shoes/hoka-clifton-10/, sitemap.xml (2,797 URLs). Code: scraper/shoe_pages.py (season_links, browse_nav, bf strings, bf_titles),
scraper/gift_pages.py (S strings, h2), scraper/bf_live.py. No search volumes below: query wording is a judgment, checked later in Search Console.

## What is already right (don't redo)
- All 8 pages: 200, self-canonical, no noindex, in the sitemap with lastmod 2026-11-06; hreflang en-CA/fr-CA/en-US/x-default reciprocal
  (deal check has no US twin: correct, none exists).
- Nov 4 audit #3 is live: BF titles/H1s/intros, deal check title, CA gift title "Gifts for Runners in Canada…", 24 deals pre-week.
- L2/L3 live: homepage, /shoes/, hubs, brand and model pages link /black-friday/ + the deal check (Clifton 10: 1 + 1).
- BF pages link 23 brand pages (20 US) and 24 model pages. Brand pages get "Black Friday" titles by themselves on Nov 10 (bf_titles()),
  which is the page that should answer "black friday hoka canada". Verify Nov 10 (below), no new work.
- Structured data: DON'T add any to these pages. FAQ rich results are limited to government/health sites since Aug 2023 (Google Search
  Central blog); ItemList carousels only exist for recipes/courses/movies/restaurants; Product snippets need a single-product page
  (our model pages already carry Product + AggregateOffer). Breadcrumbs no longer show in mobile results (Jan 2025). Nothing to unlock.

## Specs, ranked

### 1. Gift pages: start their internal links now, not Nov 15  [visible link in an existing row: needs Bastien's yes]
- Evidence: the 3 gift pages get links from only 3 places (the two BF pages + each other). Homepage (our strongest page: 671 clicks
  Oct 27-Nov 2), /shoes/, the sale hubs and brand pages: 0 links to them today, because season_links() only adds gifts while
  gift_season() is on (Nov 15 - Dec 26). Search Console (Oct 22 report): 718 URLs "Discovered, not indexed" = Google hasn't
  got to them; weakly linked new pages wait longest. Nov 15 leaves 12 days before Black Friday for Google to crawl, index and rank them.
- Generator: scraper/shoe_pages.py. Add `gift_links(today=None)` = Nov 8 - Dec 26 (Vancouver date, GIFT_MENU=1 forces it);
  `season_links()` line `if gifts and gift_season(d):` -> `if gifts and gift_links(d):`. Leave `gift_season()` and the ☰ menu item at Nov 15 (Bastien's Oct 28 call).
- Text (unchanged, already in season_links): EN "Gifts for runners" -> /gifts-for-runners/; FR "Cadeaux pour coureurs" -> /cadeaux-coureurs/;
  US "Gifts for runners" -> /us/gifts-for-runners/. Model pages stay without it (gifts=False there).
- Verify: next morning build, `curl -s https://thegearfox.com/ | grep -c 'href="/gifts-for-runners/"'` >= 1, same on /shoes/, /chaussures/
  (/cadeaux-coureurs/), /us/shoes/ (/us/gifts-for-runners/), /brands/hoka/. Night scan: no 404.
- Know it worked: Search Console URL Inspection on the 3 gift URLs = "Indexed" by Nov 18; Links report internal links to
  /gifts-for-runners/ 3 -> 150+ by Nov 18; Performance, pages = gift URLs, impressions + queries containing "gift"/"cadeau" on Dec 1 and Dec 22.

### 2. Gift pages: headings that say what's under them (EN/FR/US)  [wording only, same layout: bucket-1-ish, still show Bastien]
- Evidence: the gift pages' only H2s are "Under $25" / "Under $50" / "Under $100" (FR "Moins de 25 $"…): no word about gifts or runners
  below the H1. The under-$25 section is literally stocking stuffers (hats, socks, lights). The US title is the old lowercase string,
  and differs from the CA one only by "in Canada" missing (Search Central: unique, descriptive titles per page; same reason as S4, Nov 5).
- Generator: scraper/gift_pages.py `S` dict + the h2 line (~167): replace `under` by a per-budget key.
  - EN `under25` "Stocking stuffers for runners under $25"; `under50` "Running gifts under $50"; `under100` "Running gifts under $100".
  - FR `under25` "Idées pour le bas de Noël d'un coureur, moins de 25 $"; `under50` "Cadeaux de course à moins de 50 $"; `under100` "Cadeaux de course à moins de 100 $".
  - US: same as EN (US$ already in the amount). US title: "Gifts for runners: under $25, $50 and $100" -> "Gifts for Runners: Under $25, $50 and $100 at US Stores" (H1 too).
- Verify: `curl` the 3 pages, grep the new <h2> strings; designer check at 390px (the longer H2 wraps to 2 lines max).
- Know it worked: SC queries for the gift pages: count of distinct queries containing "stocking"/"bas de Noël"/"gift" Dec 1 vs Nov 18.

### 3. French Black Friday page: use the Québec word "souliers de course" once  [text only]
- Evidence: 0 occurrences of "souliers" or "espadrilles" on /vendredi-fou/, /cadeaux-coureurs/ or the FR deal check; every FR page says
  "chaussures de course". Québec runners commonly say "souliers de course" (everyday Québec usage; I have no volume number: check SC FR
  queries after). One natural mention, not repeated.
- Generator: scraper/shoe_pages.py FR strings.
  - `bfIntroPre` FR: "… D'ici là, voici les vrais prix du jour de {n} boutiques de course canadiennes, …" ->
    "… D'ici là, voici les vrais prix du jour des souliers de course dans {n} boutiques canadiennes, …" (rest unchanged).
  - `bfIntro` FR: "Voici les plus gros rabais du jour; …" -> "Voici les plus gros rabais du jour sur les souliers de course; …".
  - The meta description is built from the intro, so it carries the word too. Title/H1 unchanged.
- Verify: `curl -s https://thegearfox.com/vendredi-fou/ | grep -c souliers` = 2 (body + meta); copywriter OKs the sentence.
- Know it worked: SC, page /vendredi-fou/, queries containing "souliers": any impressions by Nov 30 (today none expected).

### 4. Deal check: a shorter <title> (H1 unchanged)  [new fact vs my Nov 4 spec: measured length]
- Evidence: live <title> is 89 characters EN ("Black Friday 2026 deal check: are these running deals real? (Canada, live) | The Gear Fox")
  and 99 FR. Google cuts titles at ~600 px (~55-60 characters) and often rewrites long ones; the question ("are they real?") is the hook
  and sits past the cut. This is the press-pitch page, so the result line matters.
- Generator: scraper/bf_live.py `PATHS` titles: give a separate `title` (today title = H1):
  - EN: "Real or Fake Black Friday Running Deals? Live Check, Canada"
  - FR: "Vendredi fou 2026 : vraies ou fausses aubaines? En direct"
  - H1s stay as today.
- Verify: curl both URLs, <title> matches; check.py BF live step still passes.
- Know it worked: SC page /black-friday/live/: CTR at similar position, Nov 23-29 vs Nov 16-22.

## Checks with dates (no work, just look)
- Nov 10 morning: /shoes/hoka-clifton-10/ title contains "Black Friday price check", /brands/hoka/ title ends with the brandBF text,
  a full-price model keeps its normal title (bf_titles()).
- Nov 20: BF pages switch to week mode; titles must stay identical (bfTitle == bfTitlePre).
- Dec 2: BF links leave model pages, Boxing Day links arrive (season_links); gift links stay until Dec 26.
