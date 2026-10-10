# The Gear Fox: handoff notes for Claude

The Gear Fox (thegearfox.com, tagline "Outfox full price"; French: « Flairez les aubaines ») is a free site
that shows running and outdoor gear **on sale in your size** from 50+ stores, mostly Canadian. Owner:
Bastien (Montréal / Vancouver, ultrarunner; "runner from Montréal and Vancouver" = coast to coast). Visitors pick their sizes, add an email, and get a Friday deals email
plus price-drop alerts on items they heart. Goal: $500–1,000/month by March 2027 from affiliate links,
then a paid tier (Fox Pro). The 6-month plan with weekly tasks:
https://claude.ai/code/artifact/36e1d545-7390-44fe-b080-80f03465af61
That plan (a Claude Docs doc) also holds the Fox Pro free/paid table, the Press pitch (EN/FR + outlets) and the
**Ideas backlog** (Now / Next / Later / Parked): add every new idea there and move rows as decisions change.
**Keep the plan current (Bastien, Oct 8: "always update the 6 month goal as we move forward")**: after anything ships or a
decision is made, tick it in the weekly goals (B = Bastien, C = Claude), rewrite weeks that no longer match reality, and
move backlog rows. When he asks "what's on the to-do list", answer from the current week there.

## How to work with Bastien

- **Preview first, always.** Show every change to the site in the playable preview artifact before it goes
  live (see Preview below). He approves, then it ships.
- He is not a developer. Plain language, short steps, no jargon; explain the why in a sentence.
- **Everything is bilingual (EN/FR).** Any new text needs both. French is Québec French ("courriel",
  "aubaines", "bas" for socks).
- Be willing to push back; he asks for honest opinions.
- **Request filter (Oct 4, Bastien: "make sure I'm not blowing in the wind with every demand").** Before building any
  idea (his, a user's, a Reddit comment), sort it: (1) bug or trust problem (wrong info, broken, misleading, a wall that
  contradicts the ladder) -> fix now; (2) helps the one goal before Black Friday (more visitors who come back and sign up)
  AND asked by 2+ people or backed by the stats -> next 2-week batch; (3) everything else -> the Ideas backlog, no build.
  One user asking is a signal, not a mandate. Say which bucket out loud and push back when he wants to build a bucket-3 idea now.
- **Bugs I find: fix, check in the preview, ship** (Oct 3: "no reason to wait for my approval"). New features still wait for his OK.
- **Push straight to `main`.** No pull requests or side branches (the site deploys from `main`).
- **Never ask him to paste secret keys into chat.** Secrets live only in GitHub secrets, Supabase or Vault.
- After every change, verify it landed: the right file in the right folder, the site updated, nothing broken.
- **Before every push to main: `python tools/check.py` must say ALL GOOD** (Oct 4: the shoe pages broke silently for 3 hours
  after a change that wasn't run through the shoe page builder; Bastien: "this should not be happening"). It rebuilds deals,
  shoe pages, the Friday email cards and the preview from today's live data, then runs the site test (~3 min). The refresh workflow also refuses to
  publish when the shoe pages are missing (yesterday's site stays up) and the health email flags it.
- Don't touch `email/profiles.json` (old sign-up list; kept out of commits). Subscribers live in Supabase.
- Don't circumvent bot protection. Stores that block automated access (Sport Chek, Running Room, Atmosphere,
  Sports Experts, MEC, REI…) are either skipped, read from pages Bastien saves himself, or wait for
  affiliate product feeds.

## Repo map (github.com/upnorth89/Running-Discount, branch main)

```
site/index.html          the whole site (one file: HTML, CSS, JS, EN/FR dictionary I18N)
site/privacy.html        bilingual privacy page
site/about.html          bilingual About page (Oct 3): Bastien's story + photo (bastien.jpg, Run Ridge Run 25K), what it does,
                         "How we make money" (affiliate disclosure), contact hello@thegearfox.com. Footer + privacy link to it.
site/grab.html, grab.js  "Grab deals" bookmark for MEC/REI (Bastien saves their sale pages weekly)
                         Phone version (Oct 8): after reading, the bookmark shows "Send to The Gear Fox" -> opens site/grab-save.html,
                         which takes the list by postMessage (only from mec.ca/rei.com/svpsports.ca) and calls Supabase grab_save()
                         (supabase/grab.sql; same private key as stats.html, gf-stats-key) -> table grab_saves + starts a refresh.
                         scrape.py grab_saves() reads the last 10 days like saved-pages files. After editing grab.js: python tools/make_grab.py
site/deals.json          generated daily (merged items); sale.json = only items on sale (the site loads it first;
                         deals.json only for "Include full price" or the watchlist); offers.json = raw per-store data;
                         health.json
scraper/scrape.py        all store readers + merge -> site/deals.json and site/offers.json
scraper/weekly_email.py  the Friday email (also the size-matching rules shared with alerts)
scraper/alerts.py        daily price-drop / back-in-your-size emails
scraper/health.py        daily health check + morning report email
scraper/shoe_pages.py    Google pages: one per popular shoe model (3+ Canadian stores), /shoes/<slug>/ and /chaussures/<slug>/,
                         list pages, sitemap.xml (robots.txt is static). Pages never disappear (shoes/pages.json registry)
                         List page: search-as-you-type + brand shortcuts. A registered slug that now tidies into another
                         model gets `to` in pages.json and becomes a forwarding page (noindex, canonical), out of the sitemap.
                         Model pages read the visitor's saved sizes (rd-profile in localStorage): "Your size 10: $X at Store"
                         + highlighted rows; no saved sizes (Oct 4) -> a "Your size: [Pick your size]" picker (gf-shoe-size in localStorage,
                         remembered across shoe pages; the homepage pre-fills it in the sizes step, nothing saved until confirmed); "♡ Watch the price" per table -> /?watch=<itemKey> (works at full price too).
                         The site links to them: "All sizes & stores →" on shoe cards (shoePage(): JS copy of base_model +
                         slugify, checked identical on all shoes), search cards for model names, "or look up a specific
                         shoe →" on the welcome screen (the second door), and the Friday email. Umami: shoe-page-link {from}.
                         SEO (Oct 4): titles carry today's price ("X Sale Canada: from $Y (−Z%)"); each model page has
                         "About this shoe" + "Quick answers" from today's numbers; list pages /running-shoes-sale/{,road,
                         trail,racing,women,men}/ (FR /chaussures-course-solde/{,route,sentier,competition,femme,homme}/),
                         brand pages /brands/<b>/ + /marques/<b>/ (brands with 3+ models), /black-friday/ + /vendredi-fou/;
                         it also fills the homepage block between <!--SEO-TODAY--> markers (keep them EMPTY in git: the
                         morning build writes today's top 12 + links there; one EN and one FR copy, CSS shows the one matching html[lang]).
supabase/setup.sql       database: tables, sign-up/confirm/profile/Google functions, email templates
supabase/watchlist.sql   watchlist table + functions
supabase/friday-switch.sql  latest change (Friday wording + weekly_sent_at column); already applied
supabase/morning-timer.sql  pg_cron at 11:17 UTC starts refresh.yml (morning=true) via GitHub API; key in Vault
                         as github_dispatch_token (fine-grained, Actions read/write; EXPIRES 2027-09-29: renew before)
supabase/friday-timer.sql  pg_cron Fridays :07 9-18 UTC starts weekly-email.yml with send_to=due (same Vault key)
supabase/clicks.sql      own visit/click counts for the monthly report (log_event, click_report); applied
supabase/analytics.sql   own product analytics (Oct 4): ana_events (raw, 45 days, pg_cron cleanup) + ana_devices (random device id
                         gf-did in localStorage: first/last day, visits, signed_up; no email/IP) + ana_track (site sends batches) +
                         ana_report (weekly report). Site: ANA module beside track() in index.html (forwards every Umami event,
                         plus search/search-none with result count, category, filter, sort, deal-click with card position, scroll,
                         leave seconds, errors); shoe pages send visit/shoe-page-view/shoe-page-size/deal-click. Privacy page says so.
                         scraper/usage_report.py + usage-report.yml: Monday 8:13am Vancouver email "How people used The Gear Fox".
                         Dashboard: site/stats.html (noindex, robots-disallowed; Chart.js) reads ana_dashboard(p_key, p_days):
                         ana_daily = nightly per-day totals (ana_rollup via pg_cron 9:13 UTC, kept forever) + today live; key
                         in ana_settings.dashboard_key (Bastien copies it from Supabase Table Editor; stored in his browser).
                         Region = the device's time zone (ana_events.tz, p_tz), mapped to provinces/US/Europe in stats.html (Québec
                         mostly reports America/Toronto: "Ontario & Québec"). No IP, so no country from the network.
supabase/personal-emails.sql  confirmation/sign-in emails from "Bastien from The Gear Fox" <bastien@>, branded design
                         (applied). Keep Resend open/click tracking OFF: with it on, Gmail files them in Promotions
tools/make_preview.py    builds the playable preview artifact from site/index.html
saved-pages/             MEC/REI files from the Grab deals bookmark (ignored after 10 days)
```

## Daily and weekly jobs (GitHub Actions)

- **Refresh deals** (`refresh.yml`): daily at 11:17 UTC (4:17am Vancouver) and on every push. Fetches
  yesterday's live data, scrapes all stores (a failed store keeps yesterday's data), runs watchlist alerts
  (not on push runs), runs the health check, deploys `site/` to GitHub Pages.
  - Backup time 14:47 UTC (7:47am Vancouver): GitHub often starts schedules late (Sep 30, 2026 ran ~5.5 h
    late) or skips them. A small `check` job skips any scheduled run once today's morning report went out
    (`reported` date in health.json), so there's never a second health email.
  - Afternoon run (Oct 5, Bastien; moved Oct 6 to 23:17 UTC = 4:17pm Vancouver, 12 h after the morning run, for after-work
    browsing; two scans a day keeps us polite with the shops): fresh prices/stock, site test, and a "Gear Fox afternoon
    check" email (HEALTH_WHEN=midday: compared with this morning, doesn't touch `reported`); no watchlist alerts; the check job never skips it.
  - Supabase timers (`supabase/timers.sql`, Oct 6; GitHub ran the 1:17pm schedule 5 h late): 23:17 UTC refresh.yml afternoon=true
    and 08:23 UTC runfree.yml night=true. Dedupe: health.json `midday` date (afternoon) and runfree.json `updated` < 12 h (night).
  - Supabase timer (`supabase/morning-timer.sql`) starts it on time with `morning=true`; GitHub's schedules are
    the backup. Morning runs (schedule or morning=true) send the health email; the `check` job dedupes.
  - The scrape log ends with product counts per category (and on sale) and nutrition by store.
  - Price history (`scraper/history.py`, started Oct 2, 2026): one line per product on the `history` branch (data only,
    not code: the one exception to "no side branches"), a point when the best price changes; adds `lo` (lowest in 60 days)
    and `hd` (days of history) to deals.json/sale.json. For "Is this deal real?" badges before Black Friday (Nov 27).
    Badge rule (Bastien, Oct 3): good news only ("Lowest price we've seen in N days", 30+ days of history), never "was cheaper before".
    Badges (Oct 6; Bastien chose it from pill/stamp/burst/tag/ribbon/line/check trials, "a bit smaller"): a small tilted green stamp
    "LOWEST PRICE / N DAYS" on the product photo (`.lostamp` inside `.pic`); no photo or it fails to load = green line "✓ Lowest price in
    N days" / « ✓ Plus bas prix en N jours » under the price (`.badge.lo30`, kept for screen readers when the stamp shows). Rule in `lowDays()`
    (site test "Lowest-price badge rule"): today's price in your size <= `lo`, `hd` >= 30, and `hi` (highest in the 60-day window) 2%+ above today: a real drop,
    not a price that never moved (Oct 6: 76% of sale items were "at their lowest", 15% with the drop rule). N is capped at 60.
    Shoe pages use the same rule. USA side: its own history lines ("us|" keys) in USD, so exchange rates never fake a low;
    US badges can start ~Nov 5. Preview: FAKE_HISTORY=1 python tools/make_preview.py OUT gives ~1 deal in 6 pretend history.
- **Site test** (`tools/sitetest.py`, Oct 5; Bastien: "these little glitches are being caught by users and not our own health
  check"): every refresh, after the shoe pages, a robot phone (Playwright) opens the freshly built site served locally (sign-up,
  analytics and Google calls answered by a stand-in, nothing reaches Supabase/Umami) and clicks through like a visitor: welcome ->
  men's 11/M -> deals, sign-up card + No thanks, every category chip shows only its category (+ Show more, shoe types), one search
  per category (the brand that category shows most today: all results match and stay in the category), a shoe model search,
  "naak" = "Näak", nonsense search -> "Nothing matches", Include full price + sort by price, heart -> email step, ☰ menu,
  French, returning visit, Menu > My sizes -> women's 8/S + Sports bras search, a shoe page from a card, list/BF/About/privacy
  pages, every internal link on them, script errors; then 2 deal links per store (404/410 on both = broken; 403/429 = couldn't
  check: Decathlon, MEC, Sporting Life block robots). Results -> /tmp/sitetest.json -> health email ("Site test, <check>: why"
  + a summary line); screenshots of failures are the "sitetest" artifact on the run. Critical checks (welcome, deals after
  sizes, returning visit, shoe page) are retried once, then stop publishing (yesterday's site stays up). `tools/check.py` runs
  it too (locally: CHROMIUM=/opt/pw-browsers/chromium). When adding a feature, add its check to sitetest.py.
  First catch (Oct 5): after a heart, "My sizes"/Edit opened the email step instead of the sizes (`editSizes()`).
- **Noon check** (`noon-check.yml`, `scraper/noon_check.py`, Oct 8; Bastien: "2 health runs a day and a midday lite check"): 18:53 UTC
  (11:53am Vancouver), no store re-read: tools/sitetest.py in live mode (`sitetest.py https://thegearfox.com/ OUT`; files fetched over
  the web; failures re-run once, only twice-failed checks count) + featured_check.py on the live JSON. Emails ONLY when something is
  wrong ("Gear Fox noon check: N things to look at"); an ended featured sale also starts refresh.yml. SITETEST_INSECURE=1 = Claude's sandbox only.
- **Weekly deals email** (`weekly-email.yml`): every hour on Friday 9:07–18:07 UTC. Each run sends to
  subscribers for whom it is now Friday 7am or later in their own time zone (profile `tz` from the browser;
  default: French = Eastern, English = Pacific) and records `weekly_sent_at` so nobody gets two.
  Manual "Run workflow" requires a `send_to` address (or `everyone`) and sends immediately; `due` = a normal Friday
  run (7am+ local, once each). GitHub skipped all scheduled Friday runs on Oct 2: Supabase timer (friday-timer.sql).
  Profile `terrain` (road/trail/both, sign-up "Where do you run?"): the email keeps only that kind of shoes
  (road = daily+race, trail = trail+hike); the site ranks them first (`terrainFit`), spikes excluded.
  No nutrition deals in the Friday email (Oct 9, Bastien); hearted nutrition still gets watchlist news.
  First Friday email (no `weekly_sent_at` yet) shows a note: Gmail → drag to Primary; others → add us to contacts.
- **Alerts**: at most one email per person every 3 days, only real drops (10% or $10), none on Fridays
  (the Friday email carries watchlist news).
- **Health check**: emails a daily report (subject says "all good", "all running, N still to fix" or
  "N new problems") to the `HEALTH_EMAIL` secret, else hello@thegearfox.com. Flags stale or empty stores,
  halved product counts, price jumps (currency mix-ups), piles of 70%+ discounts, and subscriber counts
  near the free email limits. Only the scheduled run emails.

- **Instagram brief** (`ig-brief.yml`, `scraper/ig_brief.py`): Wednesdays 13:03 UTC emails Bastien (HEALTH_EMAIL) 3 Reel
  picks + EN/FR script + caption and the Top 5 graphic PNGs (Chromium via Playwright). He posts a Reel of himself (feed)
  and the graphic as a Story; Friday stays the subscriber email. Manual run = send now.
  Mix: 2 shoes (7+ sizes at the shown price, 3+ common ones, one men's one women's), a top and a bottom (S/M/L in stock),
  1 piece of gear ($80+, one size or S/M/L, known brands first). Unisex sizes counted once.
  Ready-made Reel (Oct 4, `scraper/ig_reel.py`): the email also attaches reel-en.mp4 + reel-fr.mp4: this week's real drops
  (price history: best a week ago vs today's price in size 11 / M, $20+ and 15%+), one shoe + one gear/clothing, recorded as a
  watchlist on the live site (Python Playwright screencast) with safe bands + payoff first; script/hook/caption EN+FR in the email.
  Workflow fetches the history branch to /tmp/prices.jsonl (HISTORY_FILE). If it fails, the rest of the kit still goes out.
  Live check (Oct 7; Bushtukah ended a 25% sale after the morning read and the kit featured a full-price Arc'teryx jacket;
  Bastien: "double checked before sending ... so I don't post fake stuff", "checked the morning of"): `scraper/livecheck.py`
  `still_on_sale(url, price, variant)` looks at the store's own page (Shopify .js variant price/compare/stock; other stores: the
  price on the page) just before sending; brief and Reel feature only True (blocked = left out), the email lists what was left
  out. Timing: the Wednesday morning refresh starts ig-brief.yml after its deploy (refresh.yml `igbrief`); the 17:33 UTC
  schedule is the backup and skips when today's kit already went out.
- **Instagram Reels (Bastien's rule, Oct 3): always with safe bands.** Screen recordings of the site sit in the middle of a
  1080x1920 frame: dark (#17201C) band 218px on top (Instagram's Reels title/camera cover it) and 400px below (name, caption,
  like/comment buttons). Recorder + example in `tools/reels/` (rec.js records a 360x434 phone; ffmpeg line in its header).
  Open on the payoff (Oct 3): 2.5 s slow zoom on the result frame (e.g. "Dropped $41"), zooming only the site part
  (crop 1080x1302 at y218, zoompan, pad back), then the normal flow.
  Demo profile = Bastien's own sizes (Reels say "my size"): men's shoe 11 (clothing M).
  Tell him: captions go on the site part, never in the bottom band; a big hook line in the first second; cover image 1080x1920
  with the key content in the middle 4:5 (the profile grid crops to it).
- **Monthly report** (`monthly-report.yml`, `scraper/monthly_report.py`): the 1st of each month emails last
  month's visitors, sign-ups (by `?ref=` link), clicks sent to each store and paste-ready lines for affiliate
  applications ("we sent N shoppers to X"). Manual run = this month so far. Reads our own counts in Supabase
  (`supabase/clicks.sql`: the site logs one visit per session and each deal click via `log_event`; nothing
  personal), since Umami's free plan has no API. Countries/pages stay in the Umami dashboard.
- **Tracking links**: `?ref=name` (kept per device, sent with visits/sign-ups, saved in the profile), `?lang=fr`.

GitHub secrets (names only): `SUPABASE_SECRET_KEY`, `RESEND_API_KEY`, `MAILING_ADDRESS` (CASL footer),
`HEALTH_EMAIL`.

## Affiliate plan (Oct 1, 2026: none live yet; networks want 60–90 days of traffic)

- Oct 4: AvantLink network application DENIED (site too new). Reapply early December with the Dec 1 click report,
  Search Console traffic and Black Friday results, (About page, contact email and affiliate disclosure: live Oct 3).
  Meanwhile: Sovrn Commerce, Shopify Collabs (brand programs), small shops directly.
- Oct 6: Decathlon affiliate application DECLINED (same reason expected: site too new). Reapply early December with AvantLink,
  with Decathlon's Nov click count from the Dec 1 monthly report. Decathlon deals stay on the site (ranking never favours paying stores).

- AvantLink covers MEC and 9 of our brands (rabbit 10%, Sunski 8%, Oiselle 6% but no coupon/deal sites,
  Swiftwick, Ciele, Janji, Nathan, Tailwind, Skratch via Shopify Collabs). The Feed and Stance: CJ (Stance
  refuses deal sites). Altitude and The Last Hunt: Rakuten/FlexOffers. Sporting Life: Partnerize.
  Mount to Coast: Impact. Sovrn Commerce/Skimlinks as a catch-all.
- Small Canadian shops (Coureur Nordique, Endurance, VanRunCo, Capra, Fit First): no program, email directly
  with the monthly click numbers.
- Oct 7 (Bastien: subreddits refuse sites with affiliate links): NO affiliate links live. `AFF` is empty; About + privacy say "Right now, no
  link on this site earns us anything" (EN/FR) and "we'll say so here first". When a network approves: add links to `AFF` AND update
  About (How we make money) + privacy (partner cookie) the same day.
- Sovrn Commerce (Oct 3): first link was the Norvan LD 4 at Sporting Life -> https://sovrn.co/jfmu34u (removed Oct 7). `AFF` map in index.html
  (store product URL without query -> affiliate link, applied in the card href by `affUrl`; `data-store` keeps click counts on the store).
  Disclosure: About page "How we make money" + privacy page (Sovrn may set a cookie).
  Sovrn rates seen Oct 3 (application pending; clicks before approval don't earn; $25 payout minimum): Altitude Sports 10%
  (EPC $0.33), MEC 7.5% + CPC (EPC $0.17, AOV $139: keep MEC saves fresh; ask Sovrn for an MEC product feed), The Last Hunt
  1% (EPC $0.04), per click: Sporting Life, The Feed, Stance, 2XU. adidas 2-10.5% but only adidas.com (not a store of ours).
  After approval: Bastien sends Sovrn's install code -> all links to those stores earn; ranking never favours paying stores.

## Stores and data

- Speed (Oct 5): stores are read in 4 lanes at once (`run(st,fn)` + ThreadPoolExecutor(4)); all Shopify stores share one
  sequential lane (4 at once got 429s). The full scrape takes ~13 min instead of ~35.
- Shopify stores: listed in `SHOPIFY_STORES` in scrape.py (~44). Read via `/products.json`, prices checked
  in CAD with Canadian cookies (cart.js tells the served currency; USD is converted).
- Altitude Sports and The Last Hunt: commercetools readers (running category types in `CT_TYPES`).
  Each size links to `?color=…&size=…` (opens on that size). Sporting Life, MEC, Decathlon can't preselect a size
  (tested Oct 1); every size shown is in stock, so no note on cards (Bastien's call).
- Sporting Life, Stampeak, Sea2Sky, The Feed: custom readers. Decathlon: the full running section (Oct 5: all running subcategories in `DEC_LISTS`, full price included; server-rendered
  JSON, robots allow). It answered GitHub's daytime reads "429 too many requests" from Oct 5, so since Oct 6 it's read at night by
  runfree.yml (job "decathlon": `scrape.py --decathlon-night hist/decathlon.json`, one page every 6 s, stops for the night on 429,
  keeps the last good read) and the refresh loads /tmp/decathlon.json (`scrape_decathlon_saved`). Oct 8: even at night it says 429 after ~50
  pages, so the night read goes slice by slice (one page / 20 s, `cursor` + `links` in decathlon.json, list refreshed weekly,
  a product not re-read for 14 days drops); "updated" moves when 20+ pages were read. Honey Stinger off (blocks GitHub). MEC/REI: from saved pages only.
  The Feed (Oct 8; its products.json answers "429 local_rate_limited", a per-address limit that GitHub's shared addresses hit;
  morning reads failed twice in 2 days): read at night by runfree.yml job "thefeed" (`scrape.py --thefeed-night hist/thefeed.json`:
  a page every 10 s, waits Retry-After up to 15 times per page, slim copy of each product); the refresh downloads it to
  /tmp/thefeed.json (`THEFEED_FILE`) and uses it when under 36 h old, else reads live. Long term: The Feed's CJ affiliate product feed.
  SVP Sports (Oct 4, Québec chain, Shopify behind Cloudflare): saved pages too: the Grab deals bookmark on any SVP collection
  saves its products.json (svp-DATE.json, `scrape_svp_saved`); expires after 10 days like MEC/REI. PARKED Oct 6 (mostly soccer/budget shoes): out of STORES, no reminders.
- Running Free (Oct 9; Ontario chain, own shop system, no feed): `runningfree_night` in scrape.py, runfree.yml job "runningfree"
  (~2 h, one page every 30 s = its robots.txt Crawl-delay). Listing pages (96 a page) of the men's/women's sections give name,
  "Mens Black" gender+colour, photo, regular + sale price; size filter pages ("10-Regular-66612", "Medium-45397") list only what's
  in stock in that size (checked against product pages). Saved to runningfree.json on the history branch; the refresh downloads it
  (`RUNNINGFREE_FILE`, fresh = under 36 h). While fresh, the catalog file's Running Free rows are skipped. Short brands `RF_SHORT`
  (NB, SW, TNF, PI). Waist sizes (Size-28…) and shoe-drop filters (4mm…) are not read.
- Running Room (Oct 10; Canada's biggest running chain, Magento at ca.shop.runningroom.com): `scrape_runningroom` reads its own public
  product feed (robots.txt sitemap media/sitemap/ai_feed_sitemap.xml -> media/ai/products_N.json, ~22 files, rebuilt ~5am daily, 2 s
  apart): one record per size with price/final_price, stock qty, photo, a link that opens that colour+size. Tax class code -> group
  (`RR_GROUP`; 9xx "WR" = Walking Room, sandals, kids, swim, books left out); width from the name ("D Width") into the size. Oct 10:
  2,974 products, 1,262 on sale; sorting check clean; 4 of 4 sale prices matched on the store's page.
- Shoe sizes (Oct 9, Bastien: "we aren't pulling shoes that have European sizing?"): 2,476 shoe listings had no readable size.
  Fixed: Shopify option "US Size" (The Trail Runner Store, ~1,100), width first "D / 9.0" (Frontrunners; `canon_shoe(label, women)`),
  US+EU labels ("10.0 (43)", "EU 43 (US 10)", "42.5 (9.5US)"), "9 M / 10.5 W". EU-only sizes ("42", "38.5 EU": La Sportiva,
  Vibram) take the US size from today's labels that carry both for the same brand and gender (`eu_size`, `eu_only`, table in
  merge); when stores disagree (La Sportiva women's 39-41.5) the size stays unread. No guessing.
- Run Uphill / Ski Uphill (Oct 7; runuphill.ca = skiuphill.ca, Canmore + Squamish): half ski touring, filtered by NOT_RUNNING ski words
  (skis, bindings, skins, helmets, goggles except goodr "Donkey Goggles", glide wax, airbags). Its "Size (US M)" options count as sizes (SIZE_OPT).
  Checked and skipped Oct 7: Deadstock (sneaker/streetwear, ~24 running shoes). Amazon: no scraping; only via Associates + API (needs 3 sales
  and affiliate links): parked.
- Known: Honey Stinger is blocked from GitHub's servers (works elsewhere); REI needs fresh saved pages.
- **Checking a store or brand: try every allowed way before calling it unreadable** (Bastien, Oct 8: "always try multiple
  approaches. Fast, slow (Decathlon) and any work around to read their webpage"). In order: (1) Shopify `/products.json`
  (+ `/collections/<x>/products.json`, `/en-ca`, `www.`/no-`www.`, Canadian cookies; `.js` for one product); (2) the shop system's
  own public JSON: Lightspeed `?format=json`, WooCommerce Store API `/wp-json/wc/store/products`, BigCommerce, commercetools,
  RunFree `/api/product`, Next.js `__NEXT_DATA__`; (3) `sitemap.xml` + product pages' JSON-LD (`"offers"` price/availability):
  slow but allowed (Injinji, Puma); (4) slow mode: one page every 6-20 s at night, slice by slice with a cursor (Decathlon);
  (5) from GitHub's servers (store-finder.yml), since my sandbox can't reach some hosts; (6) Bastien's saved pages (Grab deals
  bookmark: MEC, REI); (7) an affiliate product feed. Always read robots.txt first and respect Disallow and Crawl-delay.
  **The line we never cross:** a 403/406/"Access denied", a Cloudflare/captcha check or "HTTP 202 empty page" means the store
  said no: no disguised browsers, rotating IPs, captcha solvers or hidden APIs behind a login. Write it in the master list
  (STORES.md "Master list") with what was tried and what would unlock it (affiliate feed, partnership, saved pages).
, ones checked and rejected (blocked, no feed) and ones waiting:
  check it before testing a shop, update it after.
- **Every store reader reads the full running catalogue, full price included, never only the sale section** (Bastien, Oct 4:
  "this should always be our default"). Full-price items are what people watch for a drop, and the "Include full price" filter needs them.
- **Sorting check** (`scraper/sortcheck.py`, Oct 7; Bastien: wrong categories are "the most common bug we find"): flags non-food
  under Nutrition, laces/sprays/insoles under Shoes, clothing under gear/packs, tops/bottoms swapped, name vs gender, trail shoes
  typed road, junk listings (saved bundles, SKU codes), one brand under two spellings, product names in the brand field. Runs in
  every health check (morning + afternoon emails: "Sorting check, …"). Known-fine items go in its `OK` list. Fixes live in scrape.py:
  `tidy_food` (+ NOT_FOOD, BYOB), SHOE_CARE in `tidy_shoes`, CLOTH_TOPW/BOTW/STRONG in `tidy_clothes`, BRAND_ALIAS, DISTRIBUTORS
  (Back River = a distributor: real brand taken from the name). Oct 7 audit: ~800 suspects -> ~1.
  Oct 8: brand-based rules in the merge (`per` brand counts): food from a brand that's <8% food goes to the name's category or the
  brand's usual one (STRONG_FOOD keeps real food); a "shoe" without shoe sizes from a non-shoe brand likewise; a sock brand's (80%+
  socks) "Crew" under tops/bottoms -> socks (NOT_SOCK keeps tees/joggers/boxers). CAMP_BRANDS (Big Agnes, Esbit) dropped;
  EYEWEAR_BRANDS (goodr…) never food/clothing. sortcheck has the same "odd one out for its brand" rule (it found these).
- Shoe names (Oct 7 audit): a gender word/code in front ("M Ghost 18", "MEN'S GEL-KAYANO 33", "Unisex ASICS Megablast") moves to the
  end for any store; filler "Road", "Running Road", "Road Racing" goes; "X Trail Running" -> "X" only when X is a trail model.
  base_model (shoe_pages.py) and baseModel (index.html) strip the same; `tools/check.py` step "Shoe page links match" compares
  them on every shoe. `forward_old()` (Canada and USA) forwards old pages to the tidy name, also across old brand spellings
  ("Asics Corp.", "Topo"); registered non-shoes (cleaning kits) lose their page. Bike shoes (BIKE_SHOE_BRANDS: Leatt…) dropped.
  A regular price 7x+ the sale price is a store typo: ignored (no "93% off").
- **Rule (Bastien, Oct 7): after adding a store, check every category before it goes live**: remerge with the new store, then
  `python scraper/sortcheck.py <deals.json> <store domain>` must come back clean (or each hit explained), and look at the store's
  items per category in the preview (`?store=<domain>`).
- **Adding a store** (Bastien aims for steady growth, 1–3 a week): check readability, currency, size labels
  (share readable), categories, sale share; add to `SHOPIFY_STORES`; remerge locally
  (`python scraper/scrape.py site/deals.json --remerge` with a fresh `offers.json`) and preview.
- Item shape in deals.json: `b` brand, `n` name, `g` group, `sx` genders, `w` wide, `img`, `lp`, `of` store
  links, `ca` ships from Canada, `sz` = `[size, price, offerIndex, regular, variantId?]`.
- Groups: shoes, tops, bottoms, bras, socks, gloves, headwear, packs, gear, watches, nutrition.
- Types (`t`, from the name, `TYPES` in scrape.py; buttons under each category on the site, untyped show under "All"):
  shoes daily/race/trail/hike/spike (definitions in scrape.py above TYPES["shoes"]; colour names cut off; "Trail Running"
  beats hiking brands; race = carbon/plated or racing flats; winter studded trail shoes are trail, not spikes), tops tee/layer/jacket, bottoms
  short/tight/pant, gear light/pole/bottle/sun. `tidy_clothes` moves bras/capris, drops bike parts; `tidy_gear` moves
  shoes filed as gear (shoe brand + numbered sizes) to shoes. One category chip picked = no Top deals (`NARROW`).
- `COURT_SHOE` drops tennis/pickleball/lifestyle lines (ASICS Gel Resolution/Dedicate/Game, Gel 1130). Shoe brands in numbered
  sizes filed under nutrition/gloves ("Gel-Kayano" read as a gel, Merrell "Trail Glove") move to shoes (`tidy_gear`); a store
  product type saying apparel/shoes never becomes food.
- `SOCCER` drops soccer boots (FG/AG… codes); `GENDER_PREFIX_STORES` move a leading gender to the end ("M Adidas Boston 13",
  "Women's Saucony Peregrine 14", "Men's Velociti 4 Running Shoe": Frontrunners, Aerobics First, City Park Runners, Sporting Life;
  also drops "*SALE*" and " - Colour/Colour"). Any store's "Men's …"/"Women's …" shoes and clothing get the same. Shoe merge keys
  ignore "(trail/road) running shoe(s)", so stores' differently worded names merge. One spelling per brand (most common wins).
  Merge keys for shoes also ignore the colour after " — " (Fit First lists each colour) and width words on wide items;
  "(Men's)"/"Men’s" become " - Men's"; Québec stores' "- Large"/"(Large)" = wide. Hoka Ora Recovery = casual (dropped).
- Clothing gender (Oct 6, a men's runner saw skirts/bras/high-rise leggings: 1 in 5 clothing items had no gender and showed to
  everyone): name first (`name_gender`), then the Shopify store's own tags/product type (`tag_gender`, clothing only, one gender
  only), then `clothing_gender` (bras group, WOMEN_ONLY words skirt/skort/dress/bra/high-rise/legging/capri/prenatal, WOMEN_BRANDS
  Oiselle, MEN_BRANDS Ten Thousand; a name saying Unisex stays unisex). Site test checks men's Tops/Bottoms for women's items.
  Oct 9 (a subscriber got women's tanks in the Friday email): `url_gender` reads the product address when the name has no gender
  (rabbit "tempo-tank-womens", Ciele "w-dlysinglet", Saysky "m-…", Brooks "/mens/") and adds " - Women's"/" - Men's" so the two
  cuts never merge into one card; WOMEN_BRANDS + Kari Traa, Athleta, Title Nine, Tahari, Huha, Sweaty Betty.
- Brand names (Oct 6): US shops often list the parent company ("Asics Corp.", "Brooks Sports, Inc. #105856", "Ing Source" = Injinji,
  "Medi USA" = CEP): `tidy_brand` drops company words (Inc/Corp/LLC/L.P/#123) then maps `BRAND_ALIAS`; BRAND_PREFER keeps the official
  spelling (the rank otherwise prefers non-capitals: "Asics Corp." beat "ASICS"). Shoe names lose a " - Colour/Colour" segment
  (Gazelle "Shoe- Black/White", Tortoise & Hare "Men's--Black/White"); `GOALIE` drops soccer goalkeeper gloves/jerseys (numbered
  sizes made tidy_gear file them as shoes). Shoe pages remember `?ref=` in gf-ref like the homepage (first link wins).
- `CAPS_STORES` (Le Coureur writes in capitals: softened), `OWN_BRAND` (rabbit/Bandit leave the brand "0").
- Shoe size keys: `"10"`, `"M:10"`/`"W:11"` (from unisex labels), suffix `~W` wide, `~N` narrow (hidden).
- Accessories (packs, gear) in letter sizes follow the clothing size; odd labels are hidden on cards.
- Merge tidies names (no repeated brand, French gender words to English; the FR site shows them in French),
  canonical brands (e.g. "Hoka One One" → "Hoka"), drops casual footwear and kids' gear (`KIDS`), sorts non-food
  out of Nutrition and clothing out of gear (`tidy_gear`).
- Ranking ("Best match"): favourites, then a deal score = % off + category bonus + dollars saved; track/XC spikes
  rank lower (`SPIKE` in index.html).
  `shoesFirst()`: with a shoe size picked and Best match, the first 6 (Top deals and the peek) alternate shoe / non-shoe
  (their road/trail kind, no spikes or hiking boots), so clothing's deeper % off doesn't push every shoe out.
- `ca`: true when any Canadian store sells the item. For gear, a Canadian store's price wins per size even if a
  store abroad is cheaper; for nutrition the cheapest wins. "Ships from Canada" hides stores abroad in every category, Nutrition
  too (Oct 7, Bastien saw US stores with it on: fuel used to skip the filter; site + Friday email). Nutrition then shows a note +
  "Show US stores too" (`data-usfuel`, turns the filter off). Site test "Ships from Canada means Canada". Cards name the store and where it ships from (`STORES` map in index.html:
  add new stores there too).

## USA side (Oct 6, 2026; Bastien: "we need a USA page" before posting on the big US subreddits)

- Site: Canada | USA switch on the welcome screen and in ☰ (`COUNTRY`, gf-country; `?c=us` links; else profile.country, French = Canada,
  else the device time zone `US_TZ`). USA = `sale-us.json`/`deals-us.json`, USD by default, "Ships from the US", other-country stores
  labelled. No Canadian store on the USA side (`SHIPS_US` empty: Altitude doesn't ship to the US; add one only after checking). One store total on both sides (`n_stores`, "87 stores checked daily").
  Profile `country`; the Friday email (`SIDE` in weekly_email.py: US$, US stores) and alerts (`evaluate_sides`) follow it.
- Data: scrape.py merges twice: Canada (no `US_SHOPS`, which may not ship north) and USA (`us` offers + `SHIPS_US` Canadian stores (none) +
  other cross-border; there `ca` means "ships from the US"). `tidy_us_names` brings US shops' names to "Model - Men's" (pipes
  "Hoka | Arahi 9 | Women's", " - Colour - Regular (D)", "(Extra Wide - 4E)", style codes, capitals); US-only filters: boots/sneakers
  (`US_CASUAL`), yoga/fashion labels (`US_LIFESTYLE_BRANDS`). General stores read from their running collection (`US_COLLECTIONS`:
  Sports Basement "running"). Shoebacca tried and dropped (PUMA/adidas/Diadora budget shoes).
- US shops (Shopify, `US_SHOPS`): Best Running Stores winners etc., ~26 (list in scrape.py and STORES.md). Finder: tools/find_stores.py
  + store-finder.yml (tests tools/us_candidates.txt from GitHub's network; my sandbox can't reach some hosts). Only ~1 in 4 US
  independents is on Shopify; many sell in store only.
- RunFree (runfreeproject.com, a shop system for running stores; 25 stores in `RF.RUNFREE_STORES`; Runner's Soul (AB) is Canadian:
  `RF.CANADIAN`, CAD, Canada side; the rest `RUNFREE_US`): scraper/runfree.py, nightly
  runfree.yml 08:23 UTC: sitemap.xml lists every product; POST /api/product (details, kept 7 days in runfree-cache.json) and
  /api/options (sizes, stock per location, cost = price, retail = regular); 1 request/second per store, all stores in parallel;
  robots allow all but /admin. Results: runfree.json on the history branch; refresh.yml downloads it to /tmp/runfree.json
  (`RUNFREE_FILE`) and each store comes in like a saved page (older than 36 h = failed, keeps its last offers). Names like
  "GT-2000 15 (W-D)" (Track Shack) -> gender + width (`name_tags`); parent companies -> brands (`CORP`). Idea pending: ask RunFree
  (hello@runfreeproject.com) for an official feed.
- Backcountry (Oct 6): reader built (`bc_product`, product pages' __NEXT_DATA__), but its bot protection answers GitHub's servers
  "HTTP 202, empty page": OFF (no circumventing). Revisit with an affiliate product feed.
- US shoe pages: shoe_pages.py `build_us()` from deals-us.json: /us/shoes/<slug>/, /us/running-shoes-sale/…, /us/brands/<b>/,
  /us/black-friday/ (US English `US` strings, US$, `L["abroad"]` labels); hreflang en-US + en-CA twin; registry us/shoes/pages.json
  (refresh.yml fetches it like shoes/pages.json); in the sitemap. The site links US cards/menu/footer there (`shoeDir()`).

## Fox Pro (decided Oct 4, 2026; table in the 6-month plan doc)

The ladder (Oct 4): Visitor (browse everything, always open for Google/Reddit) → Member (email: anything that saves or follows
something: sizes on all devices, watchlist ~10, drop news, Friday email) → Pro (faster/deeper). One sign-up card slot per page,
worded per page, never blocking, "No thanks" per device; later the same slot shows the Pro upsell to members. Hearts ask for the
email first. Release rhythm: ideas → backlog; site changes ship in batches every 2 weeks after checking the stats; bugs ship now.

Keep the hook free, charge for more, faster, deeper. Free: deals in your size, shoe price pages, watchlist (~10 items,
full price or sale), drop/back-in-size news in the Friday email, "lowest in N days" badge. Pro: same-morning alerts
(today's daily alerts; "free during launch" until Pro exists), unlimited watchlist, full price-history chart, family
profiles, pick stores/brands, Strava mileage + "Replace my shoe", later phone notifications. Target-price alerts dropped
(runners don't know a shoe's floor). Price to test ~$3–4/month or $29/year, founding $3.

## Supabase (project krwymmkauwqqxjxbvkyq)

- Publishable key is in `site/index.html` (public by design). Tables: `subscribers` (email, profile,
  pending_profile, token, confirmed_at, unsubscribed_at, last_mail_at, consent_via, weekly_sent_at),
  `watches`. Row security: nothing readable by visitors; the site talks only through functions
  (subscribe, confirm, get_profile, save_profile, unsubscribe, send_link, watch_*, google_*).
- Confirmation and sign-in emails are sent from inside Supabase (pg_net + Resend key in Vault as
  `resend_api_key`). Any SQL change = Bastien pastes it in the SQL Editor; test SQL first on the local
  Postgres copy (database `gf`) when available.
- Email: Resend, sender deals@thegearfox.com (domain verified; SPF, DKIM, DMARC p=none). Free tier:
  100/day, 3,000/month. Outlook tends to junk us; to confirm someone by hand, set confirmed_at and send them
  their `https://thegearfox.com/?k=<token>` link.

## The site (site/index.html)

- First visit: welcome screen → sizes → all deals (flow "D"; email/Google optional via the card or a heart). Welcome shows 3 tappable deals: one road, one trail,
  one race shoe (Canadian, 6+ sizes on sale, max 60% off, no spikes) and the real store count.
  Since Oct 4 there's no wall: after the sizes step every deal shows (see "No sign-up wall" below). The welcome line claims
  "More than half of gear deals aren't available in your size", recomputed daily (`missShare()`).
- Fit "Both" (Oct 4): the shoe grid becomes "Men's shoe size" and a line "Women's sizes: 10 (matched for you) · Change"
  follows it (men's + 1.5, `syncW()`, until changed; the grid opens on Change). Profile `sizes.shoes.women` (only with
  gender "any"); matching on the site, Friday email/alerts (`match()`) and shoe pages uses it for women's sizes ("W:" keys
  and women-only models), the men's list for the rest. Old "Both" profiles without it work as before. One runner = free;
  several runners = the Fox Pro family plan.
- Computers (Oct 4): from 900px the page is 1180px wide, 3 deals per row (4 from 1180px); new-deals row shows ~4; About page
  photo floats beside the text from 820px. Phones/tablets unchanged.
- Phones: compact cards (photo beside the text); categories start with 4 deals and skip ones already in Top deals.
  No automatic Google pop-up (the Google button is in sign-up step 2 and Sign in).
- Returning: calm top (sizes line + Edit, one count line with the 30-day "found this month" savings,
  watchlist strip, swipe row of new deals), categories, search + Filters (Ships from Canada, Include full
  price, Sort). Sale items only by default.
- EN headline "Your size. On sale. Every day."; FR « Des aubaines sur mesure. »
- ☰ menu (Oct 4, top right; `#menu`, `menuOpen()`): Today's deals · Shoe prices by model · My sizes · About · Instagram,
  then the Français/English button and "Prices in CAD" (the header no longer shows FR/CAD; the heart stays beside ☰). Line icons
  (`.mi`), no emojis. Shoe pages have the same menu as plain links (`menu_links()` in shoe_pages.py, + Your watchlist) using
  `/?show=watch` and `/?show=sizes`, which the homepage opens once data is loaded. Umami: menu {go}.
- Home screen app (Oct 4): manifest.webmanifest + apple-touch-icon/icon-192/512/maskable (Bastien's front-facing fox with the % tag
  on orange, Oct 4; maskable = same on orange with margin; favicon.svg stays the simple fox). Standalone.
  iPhones keep a home-screen app's storage apart from Safari: on iOS `appManifest()` points the manifest at a data: URL whose
  start_url carries the member's `?k=` or their sizes `#p=` (no email); `?src=app` + existing profile = the sizes are ignored
  (only seed the first launch; tested on Bastien's iPhone Oct 4: works). App visits: analytics `visit` detail "home-screen app". Deal links open outside (target _blank).
- No sign-up wall (Oct 4, a user said we forced sign-up): welcome -> sizes -> every deal; one card "Free with your email" (3 perks,
  Google, "No thanks" = gf-nosignup per device) after the first block; hearts open the email step (closable). Peek/blur view removed.
- Browse first + short sizes (Oct 6, from the funnel: 51% of homepage first visits picked sizes; 86 of 141 who didn't stayed 5-60 s):
  welcome footer = "Find my deals" + one quiet line "Just browse · Find a shoe" (FR "Tout voir · Chercher un modèle", one line
  down to 320px). Just browse (`BROWSE`, gf-browse) = every deal in every size (matchItems: a group with no size picked shows all
  sizes, `any` -> cards say "Sizes on sale"), a note on top "Showing every size. Pick your size…" (data-picksize). First sizes step
  is short (`shortSizes()`: fit + shoe size; clothing, road/trail, brands behind "+ Clothing size…"); no clothing size = clothing in
  every size with "Pick your clothing size" atop each clothing category. Analytics signup-step browse / more-sizes / pick-*.
  Funnel numbers: tools/funnel.py + funnel.yml (run by hand; Claude reads the result from the run's annotations).
- Come-back bar (Oct 5, Bastien): after a deal click, when the visitor returns to our tab (visibilitychange/focus, or 2.5 s later if
  the store opened without leaving), a dark bottom bar "Filling a cart at <store>? See their N deals in your size [Show] ×" (once per
  store per visit, 4+ deals, within 45 min; `offerStore()`). Show = one-store view (`view.store`, box "Shopping one store" + "× All
  stores"; matchItems keeps only sizes whose best price is at that store; ships-from filter ignored). `?store=<domain>` opens it.
  A deal counts for a store when that store has the best price in one of your sizes. Card link + Filters store list were tried in
  the preview and left out (clutter). Analytics: store-offer, store-view {store|from}.
- Sign-up spots (Oct 8, from the funnel: 3% of first visitors signed up; 209 Google visitors on shoe pages had no way to sign up):
  shoe pages' "Email me when the X drops in my size" box (`#alertBox`, shoe_pages.py; needs a size from rd-profile or the picker;
  posts `subscribe` itself, puts the shoe in gf-watch) and the homepage come-back bar's sign-up offer (`offerSignup()`: non-members,
  first return per visit; the store offer waits for the next return). Hearts picked before signing up ride in the profile as
  `watch_new` and come back with the confirm link on any device. Site tests "Sign-up bar after a deal click", "Shoe page: email me…".
- Analytics kinds (Oct 8): the database drops any event kind not in `ana_kinds()` (store bar/Canadian/country were lost Oct 5–8);
  `tools/check.py` "Analytics events are all recorded" fails if the site sends one it doesn't list. New kind = SQL for Bastien.
  `load` = ms until the deals show (+ connection, data size); the funnel report shows load bands vs sizes picked.
- Search help (Oct 8, Bastien: people searched "alphafly" and got nothing): `searchHelp()` in index.html. No deals in your sizes ->
  "Nothing in your size for X right now, but N in other sizes" + [Show all sizes] (`view.anySize`, reset on new text); a word that
  matches nothing -> "Did you mean …?" (`suggest()`: closest brand/model word in today's data, 1 typo under 7 letters, 2 above;
  "norda000" -> "norda 000"; "alphafly 4" -> the longest part that exists); a store's name -> [See every deal at Store]. Suggest,
  never auto-replace. Analytics: kind "search" with detail "any-size:"/"my-size:"/"did-you-mean:". Site test "Search: did you mean".
- Catalog file (Oct 8; stores that block us: Bastien has GPT make Running_Gear_Catalog.xlsx and uploads it to saved-pages/ every
  2-3 days): `catalog_rows()` reads the newest .xlsx ("Products" + "Sizes & availability" sheets), ignored 3 days after its own
  "Observed (UTC)" time (CATALOG_MAX_DAYS). Only "In stock" sizes, no kids, adidas size words ("L/G", "XSTP", 'S/P 5"') tidied.
  Known stores: Sport Chek (`sportchek`), adidas.ca (`adidasca`), REI (USA, replaces REI saved pages when present). Any other store
  in the file comes in by itself (`scrape_catalog_others`, STORES key "catalog"; offers st "cat-<site>"): CAD = Canada side only,
  USD = USA side only (we don't know it ships north), other currencies skipped; names in index.html STORES (the GPT list is there).
  Daily upload (Oct 8, Bastien: "have gpt do this daily"): thegearfox.com/catalog.html -> private Supabase bucket "catalog" (folder =
  dashboard_key, storage policy) -> catalog_uploaded() records it in catalog_files and starts a refresh (supabase/catalog.sql). scrape.py
  catalog_download() uses the newest upload first (newest 3 kept), then saved-pages/*.xlsx. Keep daily files OUT of git (20 MB each).
  **Before shipping ANY catalog file (Bastien, Oct 9: "Always test this before shipping it"): `python tools/catalog_test.py FILE`
  must say READY**, and its "Tap to check" list goes to Bastien with the reply.
  The file that ships must be the exact file that passed (Oct 10, Bastien: "Double check the catalog before shipping it"): any
  edit after the test (removing a wrong item by hand) = run the test again on the final file before tools/check.py and the push.
  One wrong live price: the test checks 10 more of that store; 9+ right = that item leaves the file, fewer = NOT READY.
  Links (Oct 10, Bastien: "every link brings to actual size and item linked"): `catalog_link()` adds the store's size code
  (Backcountry ?skid=SKU, REI ?sku=SKU); the test FAILs a store whose links are shared by several colours (opens on the wrong
  colour) until it gets a rule. Colour+size: Backcountry, REI, Brooks, New Balance, Sport Chek, Running Free. Colour only (size
  picked on the page; no size link, or the store blocks our check): ASICS, adidas, Zappos, Running Warehouse. It merges a partial batch (e.g. Backcountry only)
  into the newest full file in saved-pages/, then: file scan, store counts vs current (gone/halved = FAIL), Gender column vs name,
  sorting check on today's data + the file for every store in it, live links (4 random sale sizes per store opened on the
  store's page; blocked or script-only prices = tap-check), 5 deals to tap. Then tools/check.py, then push.
  Every file is checked before use (`catalog_validate`, Oct 8, Bastien: "scan the document before we publish"): refused when columns
  are missing, under 500 sizes in stock, <90% with a link, <80% with a photo, or >2% of prices wrong ($0 / above regular); then the
  next newest upload or saved-pages file is used. Warnings (still used): a store halved vs last file, 20%+ of a store's sale sizes
  70%+ off, links to several websites. Result in site/catalog-check.json -> morning email line + problems.
  One offer per colour (link + photo of a colour that has the size); no photo = not shown; under 25 products in stock = store left out
  (CATALOG_MIN); RW photos "&nw=400", Brooks dw/image sw/sh=400. Morning email: "Tap to check" 5 random catalog deals (catalog_spot).
  First file checked by hand on 9 random sale sizes: 9 right. SAVED_STORES expire (no keeping yesterday's deals). Health email:
  "Catalog file is N days old" the day before it runs out. No photos in the file (cards show text only).
- Shipping countries (Oct 8, Bastien spotted 2XU: 2xu.com is the Australian store): the Shopify reader reads each store's
  `ships_to_countries` (meta.json) every run; offers get `no_ca`/`no_us` and stay off that side ("*" = everywhere). Brands with
  separate Canadian stores are read twice (`2xu` ca.2xu.com + `2xuus` us.2xu.com; feeturesca, balegaca, stanceca, goodrca,
  nuunca, humaca). `tidy_brand` drops a regional suffix ("2XU Canada Outlet", "Balega Ca", "Stance US") after the alias lookup.
  2XU's FINAL_SALE rule removed (CA/US stores: only clearance is final). Details in STORES.md.
- Accuracy + retention batch (Oct 8, Bastien: "I want the most accurate information for our users. This is where the trust happens"):
  `scraper/featured_check.py` (refresh.yml, before the shoe pages): the top 60 Canadian / 30 USA sale items by score are opened on the
  store's page (`livecheck.still_on_sale`, `us=True` on the USA side: CAD copy -> USD, 2% leeway, Shopify only); a sale that ended is
  taken out of sale/deals(-us).json before publishing; /tmp/featured.json -> health email "Accuracy: X of Y featured deals confirmed".
  Every card: "Wrong price or size?" / « Prix ou taille erronés ? » (bottom-left; above "All sizes & stores" on shoe cards) -> 3 reasons
  -> analytics error "report|why|item|store|price"; the health email lists the last 24 h as "A visitor says: …". Top deals skip items
  left only in odd sizes until a size is picked (`commonFit`). Returning visitor (6 h+): "Since your last visit (Tuesday): N new · deals
  you opened that dropped" (`sinceBar`, from gf-base + gf-clicks `p`; the new count is left out when the new-deals row shows it).
  Hearts work without an email; a non-member's watchlist has "Email me when these drop" (`#emailNext`, signup-step drop-ask).
- Canadian brands (Oct 7, Bastien): Filters chip "🍁 Canadian brands" (Canada side only, `view.cdn`, `?canadian` link for posts),
  box "Canadian companies, not always made in Canada", 🍁 after the brand on cards. List `CDN_BRANDS` in index.html, checked by hand
  (stores' own lines only when really theirs). Not "made in Canada" (no data; most are made overseas). Analytics: canadian {on|off|from}.
  Site test "Canadian brands filter". Add brands only when confirmed Canadian.
- Final sale (Oct 4): FINAL_SALE store rules in scrape.py + tagged items -> "fs" per offer; label on cards, shoe pages, Friday email;
  About page "Returns and final sale". Recheck store policies every 3 months.
- Home screen tip (Oct 4): ☰ "Add to your home screen" on phones (iPhone steps / Android prompt) + one-time tip for members, 2nd visit+.
- Emails (Oct 6): `cleanMail()` strips "mailto:", "Name <…>", spaces and trailing dots; `okMail()` only lets through plain addresses
  Resend accepts (a "mailto:…" address got "Check your inbox" but Resend answered 422 Invalid `to`, and nothing arrived). The database
  sends with pg_net and never sees Resend's answer: Bastien reads `net._http_response` in the SQL Editor. tools/mail_check.py +
  mail-check.yml (run by hand, masked): Resend's latest emails + recent sign-up attempts. Site test: "Sign-up email check".
- CAD/USD switch, watchlist with alerts, Google sign-in, Umami analytics (no cookies; events welcome-view,
  signup-step, signup, signup-confirmed, signin, deal-click, watch-add, language, currency).

## Preview

`python tools/make_preview.py OUT.html` builds a self-contained copy with today's data, a pretend server,
and a test panel (new visitor, pretend confirmed, pretend a day passed, layout switches).
**Always mark what changed** (Oct 8, Bastien: "highlight a change so it sticks out"): pass one `--new "SELECTOR::What changed::How to
see it"` per visible change (e.g. `--new '.sincebar::"Since your last visit" line::Pick sizes, then Pretend a day has passed'`).
Matching parts get an orange dashed outline (toggle "Highlights on/off"), and the panel lists each change with "Show me". Publish it to the
"Gear Fox Preview" artifact: https://claude.ai/artifact/WqbJ6uZF8eM2NqFAuxoL6K
A ski/snowboard preview also exists (parked): https://claude.ai/artifact/QQeVvJDPSkD4dAomdeMpSo

## Where things stand (Oct 1, 2026)

Done: size-first site live, 56 stores (Capra; Oct 1: Le Coureur, BlackToe), Friday 7am-local email, alerts, daily health report, calm
layout, compact phone cards, sale-first loading, store names on cards, US nutrition by default, The Feed read
as a Canadian (only what ships to Canada), clothing moved out of gear, Share card + link previews + `?ref=`
links, Junk hint + resend, own click counts + monthly report. Email test complete (EN/FR sign-up, confirmation
in Primary from bastien@, Friday email, alert, unsubscribe). Resend open/click tracking OFF.
Soft launch: Instagram Reel + Story Thursday Oct 1 ~7am PT (`?ref=ig-story`, `?ref=ig-bio`). Bastien is not in a run club
(don't suggest club outreach as if he were; the old Sacred Strides idea is dropped). Growth ideas: Reddit/Facebook answers,
weekly Reel, a giveaway before Black Friday, Google pages per shoe. Watch the 100 emails/day Resend limit; upgrade if sign-ups spike.
Holidays: Black Friday (Nov 27) is the goal ("Is this deal real?" badges from the price history), Boxing Day, gift guide,
New Year; Thanksgiving/Halloween = themed posts only. Emails stay Friday-only (no extra BF emails).
Store candidates (Shopify, readable): Frontrunners Victoria (filter soccer cleats first), Aerobics First (Halifax), City Park
Runners (Winnipeg); Boutique Courir blocks bots. Postal-code stock: not possible (stores share online stock only); maybe a
province filter. Instagram @thegearfox live (footer + Friday email link).
Next ideas: "where each store ships to" list (REI US-only) + country setting; automated weekly top-deals post for @thegearfox; affiliate applications (AvantLink first).
