# The Gear Fox: handoff notes for Claude

The Gear Fox (thegearfox.com, tagline "Outfox full price"; French: « Flairez les aubaines ») is a free site
that shows running and outdoor gear **on sale in your size** from 50+ stores, mostly Canadian. Owner:
Bastien (Montréal / Vancouver, ultrarunner; "runner from Montréal and Vancouver" = coast to coast). Visitors pick their sizes, add an email, and get a Friday deals email
plus price-drop alerts on items they heart. Goal: $500–1,000/month by March 2027 from affiliate links,
then a paid tier (Fox Pro). The 6-month plan with weekly tasks:
https://claude.ai/code/artifact/36e1d545-7390-44fe-b080-80f03465af61
**Decisions log: `docs/decisions.md`** (Oct 22, Bastien: "file these changes and attempts somewhere with the data"): every
idea tried, its numbers and the decision (kept / removed / parked / declined). Read it before building an idea; add a row after
every decision or ended test.
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
- Don't touch `email/profiles.json` (old sign-up list; untracked since Oct 11, in .gitignore: the repo is public, no personal email in it). Subscribers live in Supabase. No personal address anywhere in the code (mail_check.py reads OWN_EMAIL = HEALTH_EMAIL secret).
- Don't circumvent bot protection. Stores that block automated access (Sports Experts,
  MEC, REI…) are either skipped, read from pages Bastien saves himself, or wait for
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
                         scrape.py grab_saves() reads the last 5 days like saved-pages files (SAVED_MAX_DAYS; 10 until Oct 30, Bastien: "down to 5"). After editing grab.js: python tools/make_grab.py
                         Oct 27: each part of a save used to start refresh.yml (one Backcountry save = ~15 runs in seconds, cancelling a push run);
                         supabase/refresh-debounce-oct27.sql: _gf_refresh_now() only flags 'refresh_wanted' (ana_settings), pg_cron 'gf-refresh-flush'
                         (every minute) starts ONE run after 90 s of quiet. Catalog uploads go through it too. Pasted Oct 27.
                         Oct 16: any MEC/REI list (sale or all running gear; MEC 80 pages, REI 150), only the fields the site reads;
                         grab-save.html sends big lists in parts of 200 (one 3,000-product save hit Supabase's statement timeout).
                         Backcountry (Oct 16): the bookmark reads a list + each product's page data: the WHOLE list (Bastien: "we want all
                         the catalog as always"), sale first, 4 at a time, "Send what's read so far" anytime, and it resumes: products
                         read in the last 7 days are skipped (gf-bc-read in backcountry.com's localStorage; sale items always reread).
                         -> scrape_backcountry_grab (bc_item, USD->CAD, USA side); needs supabase/grab-backcountry-oct16.sql pasted.
site/deals.json          generated daily (merged items); sale.json = only items on sale (the site loads it first;
                         deals.json only for "Include full price" or the watchlist); offers.json = raw per-store data;
                         health.json. Oct 29 (Bastien via growth: "stop other bots copying our data"): offers.json + hike-offers.json are
                         NOT published any more: refresh.yml keeps them gzipped in the Actions cache (raw-offers-<run>, restore-keys
                         raw-offers-; a store that fails still keeps yesterday's offers) and deletes them from site/ before the upload.
                         Locally: check.py skips the remerge without RAW_OFFERS=<file> (RAW_OFFERS=none forces the skip), catalog_test.py
                         sorts the file's stores alone, store_list.py takes a file as 2nd argument. site/robots.txt Disallows /offers.json, /hike-offers.json and deals*.json (not sale*.json: Google renders the homepage with it).
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
                         brand pages /brands/<b>/ + /marques/<b>/ (brands with 3+ models), /black-friday/ + /vendredi-fou/,
                         /boxing-day/ + /soldes-apres-noel/ (Oct 21, Canada only: "get ready" page + today's top 6, real deals Dec 19-Jan 3);
                         every list page's browse links also go to Boxing Day and the race gear lists;
                         it also fills the homepage block between <!--SEO-TODAY--> markers (keep them EMPTY in git: the
                         morning build writes today's top 12 + links there; one EN and one FR copy, CSS shows the one matching html[lang]).
                         Size pages (Oct 15): /running-shoes-sale/men/size-11/ … (FR /chaussures-course-solde/homme/pointure-10-5/, USA
                         /us/…): men 7-13 + 14, women 5-11, sale only, regular width; size menu on the men/women pages, qs_box after cards.
                         BF price-data section (Oct 27, growth chat, Bastien OK'd, bb170cb): /black-friday/ + /vendredi-fou/ (pre-BF version) show
                         "What our price data shows today" from bf_stats()/bf_data() (tools/report_page.py compute(), HISTORY_FILE, back = 14 days):
                         % shoe models on sale, women's 8 / men's 9 share, % unchanged in 2 weeks, brands most/fewest on sale; no history = no section.
                         Black Friday deal check, LIVE page (Oct 27, growth chat's spec, Bastien OK'd): scraper/bf_live.py (refresh step after the
                         race pages) -> /black-friday/live/ + /vendredi-fou/direct/ (Canada; in the sitemap; linked near the top of both BF pages,
                         `bf_live_line`, US has none yet): from hist/prices.jsonl (running keys), ca items with a photo, no spikes: real drops this
                         week (changed in 7 days, lower than every price in the 30 before, 10% or $10, >= $5, 3+ sizes), not new (30%+ off,
                         reg $60+, same price 21+ days), went up (+10% and +$10 vs 21 days ago; old < 60% of today = glitch, out); one per brand,
                         12/12/8 shown; stats (all real drops, % of sale prices already this low 2 weeks ago, sale items). Shoes link to their
                         page ?ref=bf-desk, others to the store. Ended sales are already out (featured_check runs before). Neutral wording.
                         check.py "Black Friday deal check (live page)" (reads the history branch), site test "Black Friday deal check page".
                         Black Friday labels (Oct 23, Bastien OK'd): `low_days()` = the homepage badge rule (30+ days of history, today <= lo,
                         hi 2%+ above) per model at its best price -> summary `lowd` -> green "✓ Lowest price we've seen in N days" on every
                         list card (`card_list`); BF week (Nov 20-Dec 1) lists real drops first (`real_first`) + count line `bfReal`. check.py
                         step "Black Friday real-drop labels: the rule". Shows from ~Nov 1.
                         SEO cleanup (Oct 24, Bastien OK'd "1-3"): a model page with nothing in stock for 14+ days (`seen` = last in-stock day
                         in pages.json, `stale()`, HIDE_DAYS) gets noindex,follow and leaves the sitemap (NOINDEX; page stays for visitors);
                         breadcrumb brand links to /brands/<b>/ when it has a page (+ BreadcrumbList); base_model/baseModel: "Gore-Tex" = "GTX",
                         New Balance "880 v15" = "880v15" (28 + 8 duplicate pages forwarded). check.py: no noindex page in the sitemap, every other shoe page in it.
                         Back in my size (Oct 27, Bastien OK'd idea 1): a page with nothing in stock (not boot pages) shows #backBox (fit + size +
                         email) that watches the PAGE: key "page|<slug>" (gf-watch + watch_new); alerts.py adds "page|"+slug for every
                         build_models() page (running items, both sides), so the first shoe on it in their size sends "Back in your size";
                         the homepage watchlist matches page keys the same way (watchStatus). Analytics signup "shoe-page-back".
                         No A/B test: these pages had no sign-up at all (A = nothing); judged on its sign-ups. Site test "Shoe page with nothing in stock…".
                         Page photo (Oct 26 bug): model_page reassigned `first` to a per-table dict, so no shoe/boot page had a hero photo
                         or a Product `image`; now `photo` = first item photo (hero + JSON-LD image, needed for product results).
                         Price line (Oct 15, Bastien dropped the chart: "not make people feel like they missed a sale"): `price_chart()` under
                         the size tables, per version, from hist/prices.jsonl: 5%+ cheaper in 60 days -> "It was $X on <date> ($Y today). Sales
                         come back: don't miss the next one." + [Email me when it drops] (#alertBox); today lowest -> green line only with 30+
                         days of history (badge rule); flat -> nothing. Site test "Shoe page price history line".
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
                         Its errors (Oct 12) come in 3 parts: "Visitors flagged a deal" (report|… taps), "Errors from our site", and one
                         line for the visitor's browser/app (`NOT_OURS`: crypto wallets, __firefox__, "Script error." = another site's script;
                         the site now adds the app: "Script error. (other site, Instagram)"). Umami's script loads crossorigin (shows details).
                         Dashboard: site/stats.html (noindex, robots-disallowed; Chart.js) reads ana_dashboard(p_key, p_days):
                         ana_daily = per-day totals (ana_rollup via pg_cron, hourly at :05 since Oct 18 (ana-rollup-hourly-oct18.sql; was once at 9:13 UTC, so yesterday looked empty until 2:13am Vancouver), kept forever) + today live; key
                         in ana_settings.dashboard_key (Bastien copies it from Supabase Table Editor; stored in his browser).
                         Region = the device's time zone (ana_events.tz, p_tz), mapped to provinces/US/Europe in stats.html (Québec
                         mostly reports America/Toronto: "Ontario & Québec"). No IP, so no country from the network.
supabase/personal-emails.sql  confirmation/sign-in emails from "Bastien from The Gear Fox" <bastien@>, branded design
                         (applied). Keep Resend open/click tracking OFF: with it on, Gmail files them in Promotions
tools/make_preview.py    builds the playable preview artifact from site/index.html
saved-pages/             MEC/REI files from the Grab deals bookmark (ignored after 5 days)
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
    US badges can start ~Nov 5. Hiking (Oct 27, `history.py ... --hike` in refresh.yml's hiking step, after the hiking files land): own keys "hike|" (CAD) and
    "hikeus|" (USD), annotates deals/sale-hike(-us).json the same way; first day Oct 27 (17,633 CA + 16,026 US products), so hiking badges/BF
    labels can show from ~Nov 26; hiking items join the rotating posts once they have a week of history (picks_cat still reads running only). Preview: FAKE_HISTORY=1 python tools/make_preview.py OUT gives ~1 deal in 6 pretend history.
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
  Letters touch nothing (Oct 28, Bastien: "I shouldn't have to see the y bleeding over. These details matter and should be caught in our scan"):
  tools/visual_check.py `collisions(page)` = every visible line of text (its letters' own height, descenders included) against form boxes,
  buttons, pictures and filled/bordered boxes that aren't its parent/child; words cut off by a clipping box (not "…" on purpose); page wider
  than the screen. Fixed/sticky/absolute things (bars, dialogs, hearts and badges on cards/photos) are skipped; a stylesheet that didn't load
  (or came back empty) answers "STYLES-MISSING" instead (retry). Site test "Letters touch nothing…": homepage at 320/390/768/1024/1366/1920
  with every live test off (A) and on (B), other page types (FR homepage, shoes, BF, sale list, race hub + page, About, hikes) at 390 + 1366.
  Night scan runs it on the hubs + 40 random pages on a phone AND a 1366 laptop. The first catch was the "y" itself (the computer headline
  sat on the search box once sizes were picked: theme.css `.rd.rdsized .rdhero h1{margin-bottom:16px}`). check.py gives the site test
  30 min locally (it takes ~5 min on GitHub, 15+ in Claude's sandbox).
- **Noon check** (`noon-check.yml`, `scraper/noon_check.py`, Oct 8; Bastien: "2 health runs a day and a midday lite check"): 18:53 UTC
  (11:53am Vancouver), no store re-read: tools/sitetest.py in live mode (`sitetest.py https://thegearfox.com/ OUT`; files fetched over
  the web; failures re-run once, only twice-failed checks count) + featured_check.py on the live JSON. Emails ONLY when something is
  wrong ("Gear Fox noon check: N things to look at"); an ended featured sale also starts refresh.yml. SITETEST_INSECURE=1 = Claude's sandbox only.
- **Night scan** (`night-scan.yml`, `scraper/night_scan.py`, Oct 23; Bastien: "scan website as a user to find any glitches: this should
  be done nightly"): 09:41 UTC (2:41am Vancouver), every sitemap page (200, a title, no "undefined"/"NaN"/"{name}"/"$0.00" a visitor
  would read, shoe/list/race pages show a price or the "Not in stock" line), every other link/picture they use (200), and a 390px
  phone opening the hubs + 40 random pages (our script errors, wider than the screen, leftovers after scripts). Emails only when
  something is wrong ("Gear Fox night scan: N pages to look at"). First run Oct 23 (live): 2,369 pages, nothing broken; 114 shoe pages
  say "Not in stock" (pages never disappear: by design, but thin for Google).
- **Weekly deals email** (`weekly-email.yml`): every hour on Friday 9:07–18:07 UTC. Each run sends to
  subscribers for whom it is now Friday 7am or later in their own time zone (profile `tz` from the browser;
  default: French = Eastern, English = Pacific) and records `weekly_sent_at` so nobody gets two.
  Manual "Run workflow" requires a `send_to` address (or `everyone`) and sends immediately; `due` = a normal Friday
  run (7am+ local, once each). GitHub skipped all scheduled Friday runs on Oct 2: Supabase timer (friday-timer.sql).
  Profile `terrain` (road/trail/both, sign-up "Where do you run?"): the email keeps only that kind of shoes
  (road = daily+race, trail = trail+hike); the site ranks them first (`terrainFit`), spikes excluded.
  No nutrition deals in the Friday email (Oct 9, Bastien); hearted nutrition still gets watchlist news.
  First Friday email (no `weekly_sent_at` yet) shows a note: Gmail → drag to Primary; others → add us to contacts.
  Oct 18 (it brought 16 visits in 16 days; Bastien OK'd the mock): it leads with "Dropped this week in your size" (`week_drop()`:
  the item's best price 7 days ago in the history file vs today's price in their sizes; a real drop = 10% or $10, at least $5;
  one per product across colours; shoe first, then alternating; 6 shown, "↓ $X since last Friday"); the subject names the
  biggest one ("Saucony Ride TR2 dropped $100 in your size, + 67 more this week"; watchlist news still wins the subject);
  then 4 per category, 20 in all; button "See all N deals in your size". Judged on email-friday visits (65 subscribers:
  too few for an A/B test).
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
- **Decide with data, not guesses (Bastien, Oct 17: "Use data driven and proven methods ... No guessing like we've been doing").**
  Every site change that aims at a goal (come back, sign up, click) ships as an A/B test: `TESTS` + `ANA.arm(name)` in index.html
  (a coin per device and test, same group every visit; "exp|<test>|A/B" logged once per session; ?exp=<test>:B forces a group for
  previews/checks). Before it ships, write in the plan doc: the one metric, the baseline, the sample needed (two-proportion power
  calc, 80% power, 5% level) and the stop date. funnel.yml's "EXPERIMENT" lines give A vs B with p-values: keep B only at p < 0.05,
  else remove it. Bugs/trust fixes don't need a test.
  ENDED Oct 20 (A won, Bastien OK'd): 'drops' (B's "Dropped today in your size" row: store clicks of size-pickers 21% vs 62%,
  p=0.019) and 'welcome' (B skipped the welcome screen: 11% picked sizes vs 29%, p=0.011); both A for everyone. 'layout' back to 50/50
  Oct 20 (search stays in the header for all; B = the swipe row under the categories, A = above; early data sizes 14% B vs 45% A, 33 devices).
  Live tests: 'r100' (Rule of 100, Berger: B's card badge = "−$66" when the regular price is $100+ in the shown
  currency, "−30%" below; homepage cards + welcome deals only, `offTag()`; metric = homepage visitors who click a deal, baseline 30%
  of first visits, ~1,000 per group, decide ~Nov 1). 'layout' ENDED Oct 19 (Bastien chose B for everyone after 1 day, not a test result: search + Filters under the sizes line, the
  swipe row as small tiles that keep loading as you swipe, no "See all"). Was (Oct 18, Bastien: the top row was "a big row of stuff":
  B = search + Filters right under the sizes line, categories under it, then the swipe rows as small tiles `tile()`: photo, discount,
  price, heart, one line of name (Baymard: names tell items apart); metric = homepage visitors who search or click a deal, decide
  ~Nov 1). 'runcard' (Oct 18; B = the sign-up card asks "What do you run in?": type, up to 6 suggestions under the box (`rcSuggest`, every
  typed word starts a word of the model; iPhones show a <datalist> as a menu to scroll), one entry per model; the pick is watched
  (watch_new rides with the sign-up); full catalogue loads 1.5 s after the card shows, typing survives the redraw; metric = sign-ups,
  ~1% of homepage first visits, ~2,300 a group, decide ~Nov 15; also read runcard-focus / runcard-pick to see if people use it).
  Oct 22 (Bastien): the REDESIGN ('look' B: light page, category circles, new cards, phone search in the header with the
  Filters button inside it, theme.css on every page) is the site for everyone, NO test (his call; I recommended 2 weeks 50/50
  because 'layout' B, picked by look, cut size-picking 38% -> 17%, p=0.034). Watch before/after for 2 weeks (Oct 22 - Nov 5):
  homepage first visits that pick sizes (30% the week before), click a store (35%), come back (5%); a clear drop = say so
  and offer to switch back (LOOK_B in index.html). 'runcard' ENDED Oct 22 (0 vs 2 sign-ups, too rare to ever decide).
  Test 'alts' (Oct 22, shoe pages, shoe_pages.py `alt_file()` -> /shoes/alts.json): B = one scrolling row "Other race/trail/road
  shoes on sale in your size" (up to 12, 2 per brand max, other brands first; arrows on computers) under the size tables;
  metric = shoe-page first visits that go on to another of our pages (funnel "went on to another of our pages"; baseline 5%
  reached the homepage), ~435 per group, decide ~Nov 8. Site test "Shoe page: other shoes on sale in your size".
  Test 'run1st' (Oct 22, Bastien OK'd): B = in rdKnownFirst, names matching GYM (training, HIIT, studio, yoga, lifestyle…; never shoes)
  go after running gear and one store fills at most 2 of the first 12 Top deals; metric = homepage first visits that click a deal
  (35%), ~580 per group, decide ~Nov 9. Every non-homepage page uses the homepage's light look (theme.css `html:root:not(.rd)`, light
  even in dark mode, charcoal header, logo-mark-dark.svg); the store bar stays dark on purpose (contrast, Bastien Oct 22).
  Oct 22 (Bastien: "The view all brands button doesn't lead anywhere. How did you miss this"): it opened the brand menu, which phones hide.
  Now "View all brands" opens an A-Z list with "Find a brand" under the 8 tiles. Site test "Homepage: every button does something" presses
  every homepage button and checks ITS result (proved: it fails on the old live page); add each new button to its list.
  Oct 23 (Bastien): tagline "Outfox full price" back under the logo on computers (only the phone line under the header was to go);
  computers' hero shorter (photo 230px, one-line headline, sub hidden once sized) so the category circles fit a 1366x650 browser;
  More filters scrolls its row into view; Brand menu + brand circles/A-Z count full-price items when Include full price is on ("only 1
  norda"), `.fullwait` line while deals.json (21 MB, 3.4 MB sent) loads, toast if it fails.
  Test 'cards2' (Oct 25, Bastien OK'd; daily review: direct homepage first visits clicking a store fell 33% -> 15% after the redesign):
  B on phones 380-699px (`C2P()`, html.cards2, theme.css) = slimmer cards: photo 4:3, last line = "✓ Size 11" (`yourSize` minus "in stock") or
  sizes as "XS/S/M" (`sizeRow` -> .sztxt, yours in orange) + "♡ Watch" (`watchS`; core "Watch price" shortened for B only, his OK),
  smaller CAD (kept: not in the phone header), 6 top deals (`rdLim`). Metric = homepage first visits that click a store, p<0.05.
  Site test "Compact phone cards (test cards2)". Same day: Top deals clothing needs 2+ of S/M/L until a clothing size is picked (`commonFit`).
  Test 'pro' (Oct 25, Bastien OK'd; Fox Pro step 1 of 2): `proOn()`/`proHTML()` in index.html, Nov 2-16 (PRO_FROM/PRO_TO), visits 2+
  (`ANA.nv()`), takes the sign-up card's slot (members: one tap, saves `pro_wait` in the profile; others: email = subscribe + Friday email),
  A $3/$29, B $5/$49; gf-pro / gf-nopro; analytics signup-step pro-view|pro-join|pro-no; funnel "FOX PRO PRICE TEST"; `?pro=1` shows it any
  day (previews). A tap overstates paying: <5% at both prices = stop; else step 2 in early Dec = real founding payment (Stripe, 30-day refund).
  Site test "Fox Pro waitlist card (price test)".
  Test 'emailday' (Oct 27, Bastien OK'd idea 5; weekend visits ~3x weekdays): weekly_email.py `day_arm()` (coin from the token, same every
  week) B = the weekly email Saturday 7am local instead of Friday, DAY_TEST Oct 30 - Nov 21 (`send_day()`); Black Friday week on: Friday for all.
  weekly-email.yml also runs Saturdays; supabase/saturday-timer-oct27.sql = the Saturday timer (pasted Oct 27). Links carry em=friday /
  em=saturday (`em_day()`); B gets no Saturday alert in the window. Copy says "this week" (not "since last Friday") for both. Funnel line
  "EMAIL DAY TEST". Honest limit: ~40 subscribers a group x 4 sends: only a big difference (e.g. 11% -> 22% of sends bringing a visit) shows.
  Test 'popq' (Oct 27, Bastien OK'd idea 4): B = tapping the EMPTY search box shows "Popular right now" chips (`popShow()`, #popq, fixed under
  the box; max 6) from site/popular.json (tools/popular_searches.py, refresh step "Popular searches": the last 7 days' searches, once per
  session, 2+ sessions, kept only if today's search finds 5+ sale deals on that side; casing from today's names). Tap = search + ana
  "search" "popular: <q>". Why: searchers came back 17% vs 5% (funnel Oct 13-27), only ~5% of first-visit devices searched; Baymard:
  show suggestions before typing. Metric: homepage first visits that search, baseline ~5% of devices; 5% -> 7.5% needs ~1,500 a group:
  decide ~Nov 24 (or earlier if p<0.05). Preview: PV_POPQ=1 PV_POPULAR='{...}'. Site test "Popular searches under the search box".
  Test 'namecard' (Oct 29, Bastien: "ship all 3"; daily review Oct 28: Watch-price taps convert ~1 in 5 to sign-ups, the generic card 5 of 1,776
  sessions): B = the sign-up card names the first shoe in the visitor's Top deals ("Watch the X in your size · Now $Y, was $Z" + "Email me if it
  drops"; `NC`, `.namecard`; the deal rides with the sign-up as a watch). A = "Free with your email" (core list: Bastien OK'd B replacing it for half).
  Metric: homepage first visits that sign up, baseline 1%; 1% -> 2% needs ~2,300 a group: decide ~Nov 20. Robots default to A (stub); ?exp=namecard:B,
  PV_NAMECARD=1. Site test "Sign-up card that names a deal (test namecard)".
  Test 'watchsheet' (Oct 29, Bastien: "ship both and test"; daily review): B = the email step after a Watch tap names the item ("Email me when the
  Hoka Cielo X1 2.0 drops" / « M'avertir quand … baisse de prix », button "Email me when it drops"; `wsItem` set in toggleWatch, cleared by other openers);
  A = "Where should we send your deals?" + "Subscribe & show my deals". Metric: sign-ups from the sheet among Watch-tap sessions (~1 in 5 now,
  ~46 Watch-tap sessions a week): 20% -> 35% needs ~140 a group = ~6 weeks, decide ~Dec 10, earlier if p<0.05. Same day, a fix for everyone
  (no test): the watchlist's line (#lede) was hidden by the redesign and said "Confirm your email" to people who never gave one; now
  members / pending / "Add your email…" + [Email me when these drop] (#watchEmail, signup-step watchlist-ask), theme.css `.rd.rdw #lede`.
  Site test "Email step after a Watch tap (test watchsheet) + watchlist email ask".
  Store offers ranked (Oct 29, same OK): `promoRanked()` = most deals in your size at that store first (storeCounts), then the checked median %;
  phones show 1 + "+ N more store offers today" (`view.promoAll`, analytics filter promo-more).
  Race list items link to their category (Oct 29, same OK): `CAT_LINK`/`cat_link()` in race_pages.py -> "See more jackets on sale →" under the
  picks, /?cat=<group>&t=<type>&ref=race-<slug>; homepage ?cat= opens that category like its circle (BROWSE when no sizes; analytics category
  "link|g:t", race event "catall"). Race lists only (trail lists have their own builder).
  Parked: test 'card' (cleaner deal cards, ⋯ menu; commit 629e4d1, backlog). Site tests check each one. Correlations from the "RETENTION DRIVERS" lines are leads, never proof
  (Oct 17: "watchers come back 33%" was 9 devices).
- **Own the design and product calls (Bastien, Oct 17: "You're supposed to optimize this to make it look the best and cleanest...
  We're supposed to be a team, not me just telling you what to do").** Decide clutter, wording, what stays on a card, what's
  in or out of a batch, and which idea the data really backs; show him one finished, clean version with the reasons in a few lines.
  Ask him only for real business choices (spend, rules he set, what ships). Don't send options to pick from when one is clearly best.
  **Talk first on anything visible (Oct 18, after I shipped a new top line unasked: "Remember we're a team. Don't just do things
  without talking to me first. I want us to have conversations around changes").** Bring the idea + my pick + why in a few lines,
  agree, then build it in the preview, then ship on his OK. Ship without asking only what's clearly broken (wrong price, duplicate
  cards, crashes, sorting bugs).
- **Keep things moving (Bastien, Oct 23: "if I forget to say okay you can prompt me so things keep moving. You're a teammate not a
  bot").** Anything waiting on his OK gets brought back up by me (at the end of my next reply, or on the next check-in), with a
  one-line yes/no ask. Never let a finished preview sit silently. Start the preview work for an idea he's warm on without waiting.
- **Design polish is mine, growth is the priority (Bastien, Oct 19: "I'm spending lots of time on design vs growth. I shouldn't have to
  ask will the filter button cover the other buttons").** Once a direction is agreed, I make it consistent and check it myself at
  320/390/768/1280px (site test "Top of the page: nothing overlaps"): one shape family, nothing overlapping, nothing cut off. Bring
  finished work, not pieces; time with him goes to growth (sign-ups, posts, stores).
- **Be blunt, with real evidence (Bastien, Oct 18: "Use accurate consumer trends and data. If I suggest something that doesn't work,
  tell me it's stupid and the reason why. I need to stop reminding you of this").** Every recommendation cites our own numbers
  (funnel.yml) and/or established UX/consumer research (Baymard, Nielsen Norman Group…), named, never made-up stats. When his idea
  won't work, say so plainly first, then why, then what would. Agreeing to be agreeable is the failure he keeps flagging.
- **Weekly data check-in (Oct 24, Bastien: "weekly checkins ... where people drop off")**: scheduled task Mondays 7:47am Vancouver
  (trigger "Weekly data check-in (Monday)"): funnel.yml -> ONE page: Path to $300K scorecard, drop-offs this week vs last, the 3
  search-quality numbers ("Google of the outdoor space", one sector at a time: % searches finding nothing, duplicate cards, readable
  shoe sizes), data gaps, live tests, ONE decision. tools/funnel.py prints a SCORECARD (top) + SEARCHES section for it, and a HIKING section (Oct 26: switched to Hiking, boot pages, trail gear lists: ticks, trip length, store clicks, sign-ups; tests 'short'/'cards2' show in EXPERIMENT lines by themselves).
  Oct 24 baseline: 10% of searches found nothing (80/798; most = not on sale in their size, which the site already explains);
  46 duplicate shoe-card groups in Canada (fix parked on the side branch a5424a7: it changes ~40 shoe page slugs per side,
  needs a slug-stable display name first); 97.3% of shoe listings with readable sizes (REI "5 Mens/6.5 Womens" fixed).
  Search forgives a trailing s/e (`qhas()` in index.html + search_check.py; site test "Search forgives a plural, an extra e or a filler word").
  Oct 27: filler words (`FILLER`: for/with/the/and/of/pour/avec/et/des/du; never "on"/"la"/"le": brands, stores) are dropped when other words remain
  ("running vest for women" found nothing). Load times: funnel had NONE since Oct 8 (ana-kinds-oct8.sql without 'load' pasted after
  ana-load-oct8.sql): supabase/ana-kinds-oct27.sql = the full list (pasted Oct 27: load events flow again). Lab (Oct 27): a mid-range phone (CPU x4) needs 2.6 s
  just to process sale.json (1.2 MB sent, 7.6 MB unpacked), before any download time.
  Store offers reader: tools/offer_scan.py DEALS OUT (homepage bars of SHOPIFY_STORES, offer lines, our own sale share/median/max per store);
  Oct 27 first read: 113 stores, 83 with a bar, real offers: 2XU "up to 50% off selected" (our prices: 50% of its items on sale, median 50%).
  Not wired to the site yet (waiting on Bastien's yes).
- **Answer, don't flip (Oct 24, Bastien: "You gave me advice, I then ask for clarification and then you just tell me the opposite").**
  I recommended brand+size pages, then reversed twice when he only asked questions. Before recommending: weigh costs/risks myself
  (near-copies, clutter, upkeep, real reach). A question from him = explain, not reverse. Change a recommendation only for a new
  fact, and name that fact.
- **Core things: never remove or hide one without telling Bastien first and getting a yes (Oct 22: "you shouldn't be touching
  things without telling me if they remove things we've agreed on previously"; "that then leaves me to have to continuously
  monitor you").** The list (site test "Core things are on the page" checks each, on the current and the new design):
  "♡ Watch price" in words on every card, your sizes shown (the "Top drop" link left the list Oct 23: Bastien OK'd removing it, <18 of 4,644 clicks) + a way
  to change them, the sign-up card ("Free with your email"), search, Ships from Canada / Canadian brands / Include full price /
  Sort, "Wrong price or size?" on every card, "All sizes & stores" on shoe cards, the "Lowest price in N days" badge, the store and
  where it ships from on each card, the currency after prices (CAD/USD), Canada/USA and EN/FR switches, the footer links
  (Instagram, Shoe prices, About, Privacy). Adding to it: when Bastien agrees a feature, it goes on this list.
- **Design work: phone first, one complete mockup before code (Oct 22).** The redesign built Bastien's computer rendering
  literally onto phones, then took ~2 days of rounds undoing it (hero search back to the header, 5 filter boxes -> 1 button,
  photo tiles -> circles; Bastien: "we're really working backwards ... this is brutal"). Next time: show ONE finished phone
  screen (and the computer one) for agreement first, push back on what doesn't fit a phone, then build. Log each call in docs/decisions.md.
- **Daily site review (Bastien, Oct 18: "Daily lets go through the website to make it the most user friendly and increase retention
  on all fronts").** Each day: one part of the site (welcome, sizes, top of deals, cards, search, shoe pages, sign-up, watchlist,
  Friday email), looked at on a phone with that day's numbers; bring the 1-2 biggest problems + my fix + the evidence; he decides;
  fixes go through preview, goal changes as A/B tests.
- **Nothing is a silo (Bastien, Oct 18: "This is a functioning website with many moving parts. The key to success is how everything
  flows together"; "I can't be scrolling the website daily to catch these hiccups").** Two tests ('drops' and the new-deals row)
  each added a swipe row and I checked them one at a time: half of returning visitors got two rows. Before showing or shipping any
  change: look at the WHOLE page on a phone with every live test on at once (all B) and all off (all A), as a new and a returning
  visitor. Site test "Whole page: every live test on at once stays tidy" (≤1 swipe row on top, first deal within ~2 screens, nothing
  wider than the phone) runs on every refresh; extend it whenever a change touches the top of the page.
- **Race gear lists** (Oct 20-21, Bastien's idea; live Oct 21): `scraper/race_pages.py` (refresh step after the shoe pages; adds itself to
  sitemap.xml; check.py builds it; site test "Race gear page…"). /races/<slug>/ + /courses/<slug>/, hub /races/ + /courses/, ☰ menu item
  "Race gear lists" (Canada side + shoe pages; Bastien: "even if it's one, we will add more soon"). Each race in `RACES`: the race's OWN
  mandatory list (dated, linked; "check the spec"; "not affiliated"), M/R/A per distance. Per item: 10 picks in the visitor's fit + clothing
  size (3 shown, "See all 10"; at least 3 on sale when there are; full price included so people watch it; one per brand first), only the
  brands in `BRANDS` (Bastien's list) + `MAYBE` brands (2XU, Balmoral, Nike, Under Armour, Bula, Camelbak, Osprey) only for running items;
  ♡ Watch hearts in place (gf-watch, watch_add for members, hearts ride the sign-up). First line "Trail running shoes" = "What do you race
  in?" + size (gf-shoe-size / profile, price in that size). "Only N in your size today" when the brands don't have 10. Races live
  (Oct 21): Harricana, Québec Mega Trail, Boréalys Tremblant (base + bad-weather + hot-weather kits), Bromont Ultra, Chic-Chocs (17 mandatory
  / 4 recommended, checked by rendering their Wix page), Fjord-du-Saguenay (2027 = 135/100/90/55). Each list read on the race's own site;
  a race without its own "last updated" date says "as published when we read it". Kits a race calls only in bad or hot weather (`kits` in RACES:
  Tremblant) fold under the list ("Only if the race calls it, usually a few days before the start"), out of the mandatory count. Missing: Gaspésia 100 (list only in a Canva guide: ask
  Bastien's contacts). Oct 21 night (Bastien OK'd, shipped): Ultra-Trail Whistler, Fat Dog 120, 7 US UTMB races, UTMB Mont-Blanc (7 races,
  list read from its 2026 image; PTL left out). **Every race on both sides** (Bastien: "people travel to races ... people need their gear
  locally even if the race is abroad"): /races/<slug>/ + /courses/<slug>/ (Canadian stores, CAD) AND /us/races/<slug>/ (US stores, US$,
  English), hreflang en-CA/fr-CA/en-US between them (`twins()`), a "Shopping in the US? This list with US stores" line (hidden when the
  wrong-side bar shows); hubs list every race grouped Canada / United States / France, the visitor's country first. `side` in RACES =
  the race's country. UTMB North America publishes ONE gear PDF for all its events (100M/100K/50K/20K categories + hot/cold kits;
  `utmb_race()`). Kinds can repeat with a number ("gloves3" = "gloves" rules, `kbase()`); identical pick lists are stored once per page.
  Checked and left out (no real mandatory list): Angeles Crest 100 (2026 race book: only "headlamps needed" at the start), Squamish 50
  (headlamp only), Lost Soul, Golden, Broken Goat, Knee Knacker, Hardrock (recommended
  only), Wasatch, Mammoth Trailfest 50K ("No gear requirements"); Kodiak + Pacific Trails (kit only as images). Picks: eyewear under $15 or a spare
  lens/cleaner never shows (`min` per kind). Metric: Search Console + ref race-<slug> sign-ups; check mid-Jan + end of March (plan doc row).
  Oct 27 (Bastien via the growth chat, for his Sinister Sports call Oct 28; "yes if that's what their website says"): races whose whole list
  is suggested get `"suggested": True` (SUG strings: title/h1 "suggested gear list", every R = "Suggested by the race" / « Suggéré par la course »,
  a line on top "none of it is required", FAQ "Is any gear mandatory…? No."; hub link "Suggested gear list →"): sinister-7, canadian-death-race,
  black-spur-ultra, castle-alpine, vertical-vendetta, the-dark-24 (each from its own rules_gear page, read Oct 27) + soo-200, divide-200 switched.
  `labels` in RACES = a distance's display name ("Half marathon", "24-hour", "Vertical K"). Advent (virtual) and Ultra Obscura (no list) left out.
  sinistersports.ca asks Crawl-delay 10 and answers 429 to quick reads: read slowly.
  Oct 22 (Bastien: "Sinister SOO 200 and divide 200"): soo-200 + divide-200. Sinister Sports' lists mix levels, so two more labels:
  P = "Provided" / « Fourni » (inReach, battery, bib + chip, bivvy, blaze orange: no tick box, no picks, not in the mandatory count) and
  L = "Ask the race" / « À confirmer » (Divide lists them unmarked under "a mix of mandatory and recommended gear"; a line on top says to ask
  the race). Never call an L item mandatory or optional. A list with no M items hides the "You have N of M" line.
  Oct 22 (Bastien: "Add cocodona races, and mammoth ultras"): `cocodona` (all 5 distances; its 2027 Runner Guide NOW has Required Gear +
  Cold Weather Gear carried on some sections; the hooded jacket only in rain/snow = kit) and `mammoth-200` (runners manual PDF, day + night
  gear; puffy only if the race activates cold gear = kit). Cocodona's guide is a Google Doc: `check` in RACES = the URL race_check.py reads
  (its text export) instead of `src`.
  Oct 22 (Bastien: "add other Quebec races and more like Tahoe 200 and destination races. Also look into races in salt lake area"):
  Destination Trail's 2027 Runner Manuals (Google Docs, `_gdoc()` = src + check) NOW have a mandatory table: tahoe-200, bigfoot-200, moab-240,
  arizona-monster-300, el-jefe-100 (`_dt()`; SPOT/bivy/1 wag bag = P), tahoe-100k; Québec: ultra-trail-sayam (guide PDF), la-chute-du-diable.
  Left out (no list): Bigfoot 20M, Wasatch 100, Bear 100 (403), Kat'cina Mosa, Goat Rattler, Salt and Sulfur 420, Ultra Obscura,
  Relentless Ark, Trail LCDC (EpiPen only); Gaspésia 100 still only a Canva guide.
  Oct 23 (Bastien sent its Google Doc): `twisted-fork` (Park City UT, Massif Running; 68K/30K/15K; the 68K's ice item = L: the guide's
  May 27 change log says it was removed from required gear, the list still names it).
  Oct 23 (Bastien uploaded ENG-REGULATIONS-TORX-2026.pdf; torxtrail.com puts a Cloudflare challenge in front of robots, so `nocheck`: race_check
  skips it, recheck by hand each spring): `tor-des-geants` (TOR330) + `tor-des-glaciers` (TOR450), side "it" (hub group Italy). Article 14
  MANDATORY EQUIPMENT 1 = M; MANDATORY EQUIPMENT 2 (may stay in the TORX bag, race can require it) = kit "bag" (`kitWhen_<kit>` text).
  Oct 23 night (Bastien: "expand to international races as well. all around the world"): UTMB World Series events abroad via `_intl()`,
  each from the event's own mandatory gear page (<event>.utmb.world, robots allow; the gear page slug is in the page's simpleMenu):
  lavaredo (it), zugspitz (de), eiger (ch), tarawera (nz), ultra-trail-australia (au), mozart-100 (at), julian-alps (si). Hub groups per country
  (HUB groups + `side()` order). Tarawera/UTA "weather dependent" items stay M with a note saying which distances the race confirms
  later (`_WX`); a whole-race weather kit (UTA pants + fleece, mozart cold/warm kit) uses `kits`. Fetched but not built yet (scratch
  notes): istria + eryri (lists behind per-race tabs/PDFs), kosciuszko (its table has 5 ticks for 4 races: recheck), chiangmai, restonica, nice, andorra,
  mallorca, tenerife.
  Oct 27 (Bastien): hubs (/races/, /courses/, /us/races/, /hikes/…) have a search box (`hub_find()`, #hubQ: name/place/country/distance,
  accents ignored, empty groups fold, "No race matches…" + our email; analytics filter "hubsearch|…"). Site test "Race and trail hubs: search".
  Oct 28 (growth chat, Bastien OK'd; both re-read on the race's own site): `frosty-mountain-ultra` (Trail Whisperer's 2026 "MANDATORY CHECKLIST
  for 50K and 27K" PDF; 13K has no gear check; cup-less) and `iron-legs` (ironlegs.ca per-distance "Mandatory Gear" + "Suggested Gear"; relay's bear
  spray = L: page says suggested, 2026 guide says mandatory). Not built (no readable list): Steep Ultra, Gaspésia 100 (Canva blocks ClaudeBot),
  Racing Dusk 20 Miler: built Oct 28 (`racing-dusk`, ironlegs.ca/racing-dusk: 7 mandatory, headlamp only if the last loop starts after 2pm, bib = P).
  Test 'kit' (Oct 27, Bastien: "Yes race kit"; LIVE 50/50 on race + trail gear lists): B = `KITB` compact top + every line folded to one row
  (tick, name, level, "From $X · N picks", tap = picks; class kopen, not "open" = See all). Sinister 7 4.6 -> 2.5 phone screens, UTMB 9.2 -> 4.0,
  Alum Cave 8.9 -> 4.1. Coin = homepage's (gf-did + "kit"), "exp|kit|A/B" once per session; ?exp=kit:B or ?kit=b forces B. Metric: list
  sessions that tick an item or click a store (~4% baseline, funnel "KIT LAYOUT TEST"); 4% -> 8% needs ~550 sessions a group (~75 a week
  each now): decide ~mid-Dec, earlier if p<0.05. Site test "Race kit layout test (kit)".
  Tracking (Oct 23, Bastien: "a tracker to see how and if people are using the gear checklist"): race pages send kind "filter" events
  "race|<race>|open|dist|have|unhave|complete|seeall|size|shoesize|<detail>" (`rt()` in race_pages.py; no new SQL kind) and deal clicks
  "store|<item kind>||race|<race>"; funnel.yml "RACE GEAR LISTS": sessions, first visits landing there, % that changed distance /
  ticked / ticked every mandatory item / See all / size / store click / watch / sign-up / another page, by race, by ?ref=, items ticked,
  store clicks by item. Site test "Race gear page: what visitors do is recorded".
  **Race list check** (race-check.yml, the 3rd of each month, scraper/race_check.py): rereads every race's `src`/`src_fr` (pages + PDFs),
  keeps the gear lines + linked PDFs/list pictures, compares with race-check.json on the history branch; emails ONLY when a list changed
  (+/- lines) or a page stopped answering. Then update that race in RACES from its own list.
- **Hiking (Oct 25; Bastien: "gathering as many hiking stores and hiking gear we can find", "make it look identical to the running page";
  launch on his OK after the preview)**: `scraper/hike.py OUTDIR [stores…] [--remerge]` reads 66 stores (Altitude/Last Hunt
  /c/camping-and-hiking via `ct_store`; Shopify `SHOPIFY` list by collection or whole store; robots.txt checked each run; honest UA;
  a CAD store that answers in USD is left out that night) -> hike-offers.json + deals-hike(-us).json / sale-hike(-us).json + camp(-us).json
  (camping: read, NOT published). `classify()` = hiking groups (the running groups) + types (`HTYPES`): shoes hike/boot/approach, tops
  shell/insulated/fleece/wind/base/shirt, bottoms pant/rain/short/base, packs day/overnight (35 L+), gear pole/light/water/traction/safety/
  nav/gaiter/sun; SKIP (ski, bike, paddling, hunting, climbing hardware, kids, casual), NOT_HIKE_BRANDS (fashion/ski; Oct 26 + casual/fishing labels: Duck Head, Z Supply, Johnnie-O, Southern Shirt, Howler Brothers, Goorin, Mono, Simms, Marker), CASUAL words, "Short Jacket"/"Pack Down Anorak" = tops; the
  running merge does sizes/brands/genders, then our sorting wins (`tidy`); trail runners the running site carries (RUNNING_DEALS) stay on the
  running side; shoe labels "8.5 US"/"7 UK" read (`shoe_label`), EU only from makers' own charts (`EU_CHART`: LOWA). `ul` = fastpack flag.
  Site: Running | Hiking pills beside the size (`sportSw()`, phones in .rdqf, computers after #ddSize), `SPORT`/`HIKE()`, gf-sport,
  `applySport()` swaps TYPES/RD_TILES/words (HIKE_TXT EN/FR), DFILE adds "-hike", circles img/cat/hike-*.webp (Altitude photos, SOURCES.json).
  LIVE since Oct 25 (Bastien: "I'd launch today"; `HIKE_LIVE=true`): refresh.yml starts hike.py in the background right after "Fetch
  yesterday's data" (yesterday's hike-offers.json = each store's fallback) and publishes deals/sale-hike(-us).json + hike-offers.json before
  the site test (yesterday's live files if today's read didn't finish in time); camp files are never published. A failed hiking load sends
  the visitor back to Running. Watch hearts remember their side (`s:"hike"`); the other side's file loads only for the watchlist
  (`loadOther`); alerts.py reads the hiking files too (the Friday email doesn't yet). Hiking wording: HIKE_TXT (headline, intro, kinds, why,
  title); html.hike hides race lists, shoe price links and "Where do you run?". check.py downloads the live hiking files (HIKE_DIR = a
  local read before they exist). Site tests "Hiking tab: …" and "Menu on a short phone: Canada/USA reachable" (the menu scrolls inside
  itself). Preview: make_preview.py embeds sale-hike.json as gfdata-hike when it's in the site folder (PV_HIKE_PHOTOS=N).
  `scraper/hikes.py`: 101 hikes (park page, km, climb, days, months, climate, bears, flags) + `gear_for(hike, days, month)` = 10 essentials
  + what the hike adds, each linked to a hiking group/type ("Trail gear lists", next to build). Figures rounded, `checked` False until
  re-read on the park page.
  Intake (Oct 25, Bastien OK'd): `#wSport` "Gear for" row on the welcome; hiking words via HIKE_TOP keys (shoeSizeH, clothMore, by_tops…) +
  rd.h1; `#euBox` EU boot line (EU_M/EU_W = LOWA chart, `syncEU()` until changed, `euSet`) -> "E:44.5" keys match EU-only boots (scrape.py
  `eu_keep`); `#hkind` day/overnight/both -> profile `hike_kind`, `hikeFit()` ranks packs/layers. Site test "Hiking intake".
  Hiking side bottom (Oct 25, Bastien: "shows running deal links at the bottom"): `hike_home()` in shoe_pages.py fills <!--SEO-HIKE--> (keep EMPTY
  in git) with today's best boot deals + links; CSS shows it instead of SEO-TODAY on html.hike; footer link = `shoeDir()` + mShoes ("Boot prices by model").
  Boot price pages (Oct 25, Bastien: "Everything should be doing the same as the shoe page"): shoe_pages.py `build_hike()` /
  `hike_main()` (`shoe_pages.py site --hike`, refresh.yml right after the hiking files land; adds to sitemap.xml): /hiking-boots/<slug>/
  + /bottes-randonnee/<slug>/ (Canada) and /us/hiking-boots/<slug>/, list pages at each dir, registry <dir>/pages.json (3+ stores on that
  side, pages never disappear), `_H` strings EN/FR/US, `hike_name()` tidies store wording ("Mid WP" = "Waterproof Mid"; JS copy
  `hikeName()` in index.html, check.py "Boot price pages + links match"). Hiking side: cards' "All sizes & stores", menu "Boot prices by
  model", welcome "Find a boot" go there (`shoeDir()`). First build: 64 Canadian + 44 US models. Site test "Boot price pages + hiking cards…".
  Friday email (Oct 25, Bastien: "unless someone subscribes on the hiking page then it should give them hiking items"): profile `sport`
  = the side they signed up on (`withSport()` at subscribe/Google, kept by toProfile); weekly_email.py sends hiking items to sport=hike
  (HIKE_LABEL headings, links add &sport=hike, EU sizes match). Everyone else: running, as before.
  Test 'short' (Oct 25, LIVE 50/50 same day, Bastien: "yes let's shorten the size selection to fast track sign ups"): B = first sizes screen asks fit + shoe size only (clothing, EU line,
  kind of hiking behind "+ Clothing size, …"; `.clb`, html.shortb; no "Gear for" row). Why: 124 of 125 first visitors who didn't pick sizes
  left at the sizes screen; size-picking 33% -> 22% since Oct 22 (p=0.002). Metric: homepage first visits that pick sizes, ~465/group,
  decide ~Nov 8. Preview: PV_SHORT=1. Site test "Short sizes screen (test short B)".
  Trail gear lists (Oct 25, Bastien: "Yes start", then "Yes" to ship: LIVE since Oct 25; switches `LIVE` in scraper/hike_pages.py + `TRAIL_LIVE` in
  index.html; ☰ "Trail gear lists" on the Hiking side via `raceDir()`): scraper/hike_pages.py (refresh step after the boot pages) -> /hikes/<slug>/ + /randonnees/<slug>/ + /us/hikes/<slug>/ and hubs,
  reusing race_pages.py (size box, ticks, ♡ Watch, sign-up box; sign-ups here get `sport:"hike"`). Lines = hikes.gear_for() per trip length
  (`trips()`: day / 1 night / usual nights) with levels Essential (Y, counted) / Required (M) / Recommended (R); picks from the hiking files
  by group/type + a name rule per line (`NEED`, `NOT`, `PACK_BITS`: no watches, books, bells under safety lines); bear spray = checklist
  line (no store ships it). Only `checked` hikes go live: hikes.VERIFIED (27 of 101 on Oct 25, 46 on Oct 26, 56 on Oct 27, 66 on Oct 28, 75 on Oct 29, 81 on Oct 30; 10 a day by the scheduled task "Daily: verify 10 more hikes" (9:37am Vancouver), trails in season first; each figure re-read on the park/trail page,
  url kept; climb shown only when the page gives one, `gain_ok`). The other 74 need their trail page read by hand (Sépaq, PCTA, Yukon
  block robots). Preview: `hike_pages.py DIR --all`. Food box (Oct 26, `fuel()`/FUEL_JS): LCDA (Looney 2022, the Army's successor to Pandolf; half up, half down the average grade; Cunningham resting) kcal/day from body + pack kg, hours, climb, or a GPX file read in the browser (gf-fuel). kg | lb switch (Oct 27, Bastien: "some people use both"; `.fuu`, gf-fuel.u, converts body + pack, climb stays m/ft by side). Trail list pages use the hiking menu (`HL()`: boot prices + trail lists, site test checks no /races/ link). check.py "Trail gear lists (checked hikes only)" (--force), site test "Trail gear list:
  sizes, deals, ticks". Preview artifact: https://claude.ai/artifact/KdkvAVSK2eH9ApAXvTz5Yq
- **Gift page** (Oct 28, growth chat's prototype, Bastien: "Ship it all except the fox pro"): `scraper/gift_pages.py site` (refresh step after the BF deal
  check; adds itself to sitemap.xml) -> /gifts-for-runners/ + /cadeaux-coureurs/ (Canada side): size-free gifts (one size, or S+M+L / M+L in stock; hats,
  gloves, socks, lights, bottles, sunglasses, hydration vests/belts, watches) under $25/$50/$100: 8 on sale (20%+ off) + 4 full price ("♡ Watch the
  price" -> /?watch=<itemKey>&ref=gifts), one brand once per budget, max 3 of a kind among sale picks, Canadian stores, photos only. Odd prices out:
  "pack/bundle/set/kit" names and a regular price over 1.8x the brand's median for that kind (a goodr at $100). Linked from both Canadian BF pages
  (`bfGift` in bf_live_line). check.py "Gift page (EN/FR + USA)", site test "Gift page: three budgets…".
  USA (Oct 30, Bastien: "Yes ship it"): /us/gifts-for-runners/ from deals-us.json (prices shown in US$ = CAD / fx, budgets in US$), US stores, no Boxing Day
  box (links /us/black-friday/), linked from the US BF page (`US["bfGift"]`; bf_live_line shows the gift line even without a live check), hreflang
  en-US <-> en-CA. Cards name the store (STORES map via SP.store_names) instead of its web address, both sides.
  ☰ menu item "Gifts for runners" / « Cadeaux pour coureurs » (Oct 28, growth chat, Bastien OK'd): after Race gear lists, Nov 15 - Dec 26 Vancouver date,
  Canada running side only; homepage `giftMenu()` (?gifts=1), shoe/race pages `gift_season()` (GIFT_MENU=1). Site test "Menu: seasonal 'Gifts for runners'".
- **Clothing sizes per category** (Oct 21, a visitor: "medium in shorts, L in socks, small in t-shirts"): sizes screen keeps one quick
  "Clothing size" row + "Different size in shorts, socks or gloves?" (`#clothMore`/`#clothBy`, `state.clothBy` = only the categories that
  differ, `clothFor(g)`; bras follow tops, hats the main size). Profiles already kept a size per group (Friday email/alerts use them);
  applyProfile takes the size most groups share as the main one. Race pages: same link in their size box (gf-race-size.by). Site test
  "Clothing: a different size per category".
- **Header + menu + language (Oct 23, Bastien OK'd; header "we don't need to test this. It helps the flow")**: shoe/list/race pages
  (shoe_pages.py page_head, class `hdrb` on every page): the charcoal header slides away while reading down on phones and comes back on
  scroll-up (NN/g partially persistent header), stays on computers; 🔍 `#hsb` opens `#hsf` (search box -> homepage `?q=`, `--hh` keeps
  the shoe list's sticky `.find` under it). Homepage ☰: computers hide what the header shows (My sizes 760px+, deals/races 900px+,
  shoe prices 1400px+, theme.css); language = a choice row `#langPick` (`renderLangs()`, one line per language in LANGS), header
  🇨🇦/EN buttons open the menu. Shoe/race pages' menu: a "Language: English | Français" row (`.lsw`). Site tests "Shoe page: header
  comes back on scroll-up + search", "Computer: the ☰ menu doesn't repeat the header".
- **Watchlist across devices (Oct 23 bug, Bastien: "I keep taking 2 items off the list and it inputs them back")**: syncWatches used to
  upload every local item missing on the server, so a second device (phone browser vs home-screen app vs computer) put removed items
  back. Now `sv` marks items seen on the server (gone from it = removed elsewhere, removed here too; lists from before: items saved 1+
  day ago), `gf-watch-gone` keeps unconfirmed removals and resends them. Site test "Watchlist: removed on one device stays removed on the other".
- **Mystery shop (Oct 18, Bastien: "act like a spy shopper paid to find issues ... keep the mystery shopper somewhere so we can work on
  this later").** Report: https://claude.ai/artifact/D9V9KYMpdD2TygXGYJTAUR (copy in docs/mystery-shop-2026-10-18.html), open items as
  rows in the plan doc backlog. Fixed the same night: no-result search message, sign-up card after the results, women's table first
  on shoe pages + each table's own price line, no toast over the email sheet. Redo the walk (phone, new + returning, EN/FR) before
  Black Friday and after any big batch.
- **Check my own work before sending anything (Bastien, Oct 17: "I shouldn't have to review everything. My time is adding up").**
  Videos/graphics: look at frames from start, middle, end (text centered in its box, nothing cut by the bands, no overlap), every
  number from today's data (store count = n_stores in sale.json, 143 on Oct 17, "140+"), no over-explaining (people know CA = CAD).
  Send only the finished version, once.
- **No claims we can't back up (Bastien, Oct 17: "Let's not make any claims like 1/2 the marathon is wearing this").** Reels, posts,
  captions and scripts state only facts from our data or the product itself (price, % off, sizes, store, "carbon plate"): no
  "half the start line wears it", "best shoe of the year", "most deals are fake" unless we have our own numbers for it.
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
- **IndexNow** (Oct 11): refresh.yml job `indexnow` (morning runs, after deploy) sends every sitemap URL to api.indexnow.org (Bing,
  DuckDuckGo, ChatGPT search, Yandex); key file site/d5b591bd5a0f92826eeb50008110fb99.txt (public by design). First submit Oct 11: 1,856 URLs, HTTP 200.
  Oct 23 (Bastien OK'd): only CHANGED pages are sent (it was all ~2,400 daily: 24,200 in 12 days; IndexNow asks for changed pages only).
  tools/indexnow.py reads each sitemap page live, fingerprints its visible text minus date stamps/countdowns, compares with yesterday's
  (actions/cache "indexnow-*", /tmp/indexnow-state.json); new + changed are sent, cache lost = all. INDEXNOW_DRY=1 = count only.
  Bing Webmaster Tools (Oct 23, Bastien signed in): sitemap OK (2.3K URLs discovered) but only 5 pages indexed, Backlinks "-":
  Bing waits for links from other sites (race organizer emails). He requested indexing for /, /shoes/, /running-shoes-sale/.
- **Daily drop posts** (Oct 26, Bastien: "make growth into an automatic feature"; LIVE on Bluesky Oct 26, @thegearfox.bsky.social; repo variable SOCIAL_LIVE=0 pauses; a failed login turns the run red with Bluesky's reason): `tools/social_post.py` + social.yml
  (8:21am Vancouver): today's biggest REAL drops on shoes with a shoe page (history: a week ago vs today, 10% or $10, >= $5, 5+ sizes at the
  price), each confirmed by livecheck, one per brand, 3 a day, each shoe once per 21 days (actions/cache social-state.json); text = facts only
  + shoe page `?ref=bluesky`. Posts only when repo variable SOCIAL_LIVE=1 AND secrets BLUESKY_HANDLE + BLUESKY_APP_PASSWORD exist (Bastien
  adds them himself); otherwise a dry run (artifact "posts": posts.html). Pinterest (app review + demo video) and Threads (Meta verification)
  next. Plan doc tab "Growth plan (Oct 27)" = the full night-of-Oct-26 growth/monetize/SEO answers.
- **Rotation on the automatic posts** (Oct 26, Bastien OK'd; stop rule Nov 17): shoes every day + ONE rotating category by date
  (`social_post.rotation()`: date.toordinal() % 4 = most popular / coats / pants / tops; `fits()`). Bluesky = 1 rotating + 2 shoes,
  Pinterest = 2 rotating + 3 shoes per board, Instagram kit = its 3 non-shoe picks from that Wednesday's category (topped up as before).
  Rotating items (`picks_cat()`): real drop this week (same rule), S, M AND L at the shown price (one-size gear: OS), store page
  confirmed, one per brand, once per 21 days, running side only (the history has no hiking items); link = homepage ?q= that the site's
  search (search_check.py hay/qhas) answers with only that model in the WHOLE catalogue (deals.json: ?q= landings show full price too),
  never ending on "with"/"and". "Most popular" = the non-shoe category with the most deal clicks in 7 days (clicks record the category,
  not the item; needs SUPABASE_SECRET_KEY, else any category). Refs: bluesky-shoes / bluesky-<cat>, pinterest-shoes / pinterest-<cat>.
  Nov 17: rotating posts bring clicks but no sign-ups vs shoe posts = back to shoes only.
- **Pinterest feeds** (Oct 26, growth chat + Bastien: 6-week test, stop if <30 first visits with ?ref=pinterest by mid-Dec): `tools/pin_feed.py`
  (refresh.yml step "Pinterest feeds" after the race pages): morning = today's real drops from social_post.picks (side ca/us; US prices in US$
  against the "us|" history), livecheck-confirmed, 5 per side, each shoe once per 21 days (the feed is the memory), last 50 kept ->
  site/pins/ca.xml + us.xml (RSS 2.0, enclosure + media:content + <img> in the description, link = shoe page ?ref=pinterest) + a 1000x1500
  JPG per pin in site/pins/img/ (Playwright; a pin whose text overflows or photo fails is left out; >45 days pruned). Every other run =
  `--carry` (yesterday's feeds + pictures from the live site, since a deploy replaces site/). Night scan checks both feeds + every link/picture.
- **Growth calendar** (Oct 11, Bastien: "post every 3 days on running gear"): plan doc section "Growth: a post every 3 days" + send_later
  reminders at 6:30am Vancouver (C25K Oct 14, RunningShoes 17, runninglifestyle 20, BuyCanadian 23, xxrunning 26, trailrunning 29,
  FrugalMaleFashionCDN Nov 1, ultrarunning 4, RunningShoeGeeks 7 + plan the rest to Cyber Monday). A different place each time.
- **Google first (Bastien, Oct 19: "let's focus on where we retain and Google seo").** Funnel Oct 12-19: Reddit 276 first visits,
  1 sign-up, 3% came back; Google 26 visits, 40% came back, median 76 s. Reddit = awareness only; never judge a site change on Reddit
  visitors. Search Console (Oct 19): ~98 clicks in 3 weeks, nearly all "the gear fox"; shoe searches sit at positions 30-70 (new site,
  few links in). 1,226 pages indexed, 411 waiting. Shipped: homepage canonical, brand titles with today's count ("Altra Sale Canada: 31
  running shoes on sale, up to 55% off"), On = "On Running". Next levers: links from real running sites (press pitch), pages already
  near page 1 (on-cloudboom-max pos 3, /shoes/ 4, running-shoes-sale/ 6.5, brands/asics 7), brand+gender+size long tail (no thin pages).
  Push notifications parked (iPhone needs the home-screen app first; visitors stay ~20 s).
- **Monthly report** (Oct 20; Bastien OK'd it "live with no one having access unless I give a link"): `tools/report_page.py DEALS PRICES site YYYY-MM
  COMPARE-DATE` writes site/report/YYYY-MM/ + site/rapport/YYYY-MM/ (frozen, committed): share on sale, sale shoes left per size,
  brands (25+ models), "already at that price 2 weeks ago", top 10 stores, method, "free to quote with a link". Hidden (Bastien, Oct 20: "keep the page hidden"): NO link on the
  site, NOT in the sitemap; indexable, so Google only finds it through the links others give it. Shared by link only: press pitches, podcast, Reddit. ?ref=report-YYYY-MM.
  Keep only if it earns links: none by Nov 30 -> stop making them.
- **Reddit results (keep current):** r/RunningDeals: Oct 18 post (3 CA + 3 US, item links to thegearfox.com) stayed up. r/BuyCanadian: removed
  by the mods Oct 17 even with only 3 items: don't post there again (ask the mods first if ever). Posting in the same sub again:
  `reddit_post.py --exclude "model,model"` skips items posted there recently (ask Bastien whether the last draft was actually posted).
- **Tracking links**: `?ref=name` (kept per device, sent with visits/sign-ups, saved in the profile), `?lang=fr`.
- **Post maker** (`tools/reddit_post.py --ref <place> [--side ca|us|both] [--direct] [--out FILE]`; use --direct for Reddit, Oct 11; Bastien: post every 3 days, format
  "6 shoes 4 gear Canada and 6 shoes 4 gear USA, that's it", names as links): famous models first, biggest discount, 7+ sizes, each
  deal confirmed on the store's page (else the next one), shoe page link or a ?q= search that finds only that item; writes the
  Markdown (paste at old.reddit.com) and a plain version (address under each line, for the phone app). One ?ref per place.
  `--canadian` (Oct 11): the site's CDN_BRANDS only, well-known ones first (FAMOUS_CDN: Arc'teryx, norda, Ciele, SAXX, MEC…),
  4 shoes + 6 others, max 2 per brand, one per kind of thing (`noun()`: vests, warmers). Retro lifestyle reissues skipped.
  Oct 12: a post with 20 thegearfox.com links was removed by Reddit's spam filter: link items straight to the store, one
  Gear Fox line at the bottom, check the sub's self-promo rules / ask mods (r/runTO: Toronto-store list, marathon week).
  Oct 13 (Bastien): he WANTS item links to thegearfox.com (shoe page or ?q= search, ?ref per post), every link opened on the live
  site first. **Give posts right in the chat as hyperlinked items only** ("easier for me to copy paste. Only put the items"): no title,
  no footer, no files. `--toronto` (Oct 17, r/runTO, mod approved): only deals whose best price is at a store with Toronto shops
  (TORONTO: Running Free, Running Room, BlackToe, Sporting Life, MEC, Sport Chek, Decathlon, Foot Locker, Arc'teryx), "at <store>"
  on each line; an item whose ?q= link would find other models too is skipped. Put the Markdown inside ONE code block (copying rendered chat links loses them; Oct 13: "It doesn't
  work"); he pastes it in Reddit's Markdown mode.
  **Reddit = shoes only with shoe page links (Oct 24, Bastien: "Reddit is great for clicks but no sign ups"; 705 Reddit first visits in
  14 days, <1% signed up, 8 of 361 homepage landings picked sizes; shoe pages bring 24 of 61 sign-ups via "Email me when it drops"):
  `reddit_post.py --pages-only` (no ?q= searches, no gear). Compare sign-ups per post by ?ref.**
  **Every post checks itself (Oct 28, Bastien: "I need you to double check your work before I push stuff"; a line said "$75 (was $150, −33%)"):
  reddit_post.py ends with tools/post_check.py: each line must match a row on its live shoe page (price, was, %, 5+ sizes) or it exits 1
  and says which; never send a post whose POST CHECK isn't "all lines match".**
  **Rule (Oct 17, Bastien: "the shoe name should be a clickable link. It makes it look cleaner"): item names are ALWAYS the
  link, never a bare address under the line.** His Markdown paste in Reddit's normal editor showed raw [..](..), so every post
  also gets `--html FILE` (a copy page: names as links + "Copy post" button that copies rich text, links survive a paste in
  Reddit's normal editor): publish it as an artifact and give him the link, plus the Markdown code block for Markdown mode.

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

- Foot Locker (own reader, running shoes only): product codes can start with letters ("KI424725"); FL_CARD reads them since
  Oct 13 (Bastien saw an Evo SL at $99.99 we missed: 3 colours, 5 shoes skipped).
  Its running tag ("performancerunning") misses real running shoes filed under "Casual Sneakers" (Evo SL, Bondi 9, Clifton 10,
  Winflo 12 $99.99: 29 dropped Oct 13): untagged items are kept unless FL_LIFESTYLE matches (Vomero 5, XT-6, Air Max, clothing).
  Coverage check (Oct 13, Bastien: "how do we make sure we don't skip this"): `save_coverage(st, listed, read, note)` writes
  site/coverage.json (Foot Locker: the store's own count per gender vs codes read + product cards our pattern couldn't read;
  Shopify: a store that hits the 24-page limit); health.py `coverage_check` adds "Store coverage" to the email and flags <97%.
  First morning (Oct 14) it caught 3 US stores stopped at 24 pages: SHOPIFY_MAX_PAGES = 80 now (Athletic Annex 7,312 products,
  Pacers 8,191: +3,500); only a FULL last page is flagged (PR Run & Walk ended at 5,795 = false alarm).
  Oct 26: Altitude/Last Hunt (facet count of the product types we read vs product pages read: 100% both), Sporting Life ("N Items"
  vs read) and Running Room (feed files read + `RR_SKIP_CODES`: an unknown tax-class code with 20+ in-stock sizes = "new product codes we
  don't read yet" in the email). The Running Room check found codes 900/901 (Walking Room trail/hiking shoes: Speedgoat 6 Mid GTX, Ultra
  Flow, Lone Peak 9+, Timp 6), 211 (Garmin/Wahoo watches), 151/152/261 (running tops) silently dropped: now read (+265 products, 55 on sale).
  Decathlon (Oct 26): each running list's own "N items" (`DEC_LIST_STATS`, saved as `lists` in decathlon.json when the list is
  refreshed weekly) vs colour pages collected (59 of 59 on running-shoes), plus listed products read in the last 14 days (261 of 262).
- Sport Chek (Oct 13; Bastien: "build the Sport Chek reader"): it stopped blocking (robots.txt allows products, llms.txt published),
  so `scrape_sportchek` reads it live with an honest bot name through the data its own pages use (public key in every page, no
  login): search of the Running section etc. (~1,090 products), price/stock per 500 colour+sizes, size details only for products in
  stock online. Only web-warehouse stock that ships home. Size links open that colour+size. livecheck `_sportchek` asks the same price
  service (its pages show prices only after a script, so the page-text check would have called every deal "ended"). The catalog file's
  Sport Chek rows are ignored (`CATALOG_LIVE`). If it ever answers 403/captcha: stop, don't work around it. Checked Oct 14: Atmosphere
  closed its online store (moved into Sport Chek); Sports Experts is behind an Incapsula 403 wall (no).
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
  SVP Sports (Ontario chain, 13 stores; Shopify): Cloudflare blocked it Oct 4 (saved pages, parked Oct 6); since Oct 12 read LIVE (the check is
  gone, robots allow): SHOPIFY_STORES "svp", only /collections/running-collection (US_COLLECTIONS), no cart.js (robots forbid it:
  `NO_CART`), `tidy_svp` ("adidas - Men's X Shoes (CODE)" -> "Men's X", sizes "M11" -> 11, "(Wide)", yoga/maternity/track suits out).
- Running Free (Oct 9; Ontario chain, own shop system, no feed): `runningfree_night` in scrape.py, runfree.yml job "runningfree"
  (~2 h, one page every 30 s = its robots.txt Crawl-delay). Listing pages (96 a page) of the men's/women's sections give name,
  "Mens Black" gender+colour, photo, regular + sale price; size filter pages ("10-Regular-66612", "Medium-45397") list only what's
  in stock in that size (checked against product pages). Saved to runningfree.json on the history branch; the refresh downloads it
  (`RUNNINGFREE_FILE`, fresh = under 36 h). While fresh, the catalog file's Running Free rows are skipped. Short brands `RF_SHORT`
  (NB, SW, TNF, PI). Waist sizes (Size-28…) and shoe-drop filters (4mm…) are not read.
- Sports Experts (Oct 15; Québec chain, Canadian Tire/FGL; Bastien: "GPT keeps running out of tokens"): its Cloudflare wall
  stops Claude's sandbox but NOT GitHub's servers (probe.yml showed 200s, robots.txt allows category + product pages; Disallow
  search/sort/account/GoogleProductFeed), so it's read at night: runfree.yml job "sportsexperts" (`scrape.py --sportsexperts-night
  hist/sportsexperts.json`, one page every 3 s, ~75 min): listing pages' SearchResults JSON (SE_LISTS: running road/trail shoes,
  clothing, accessories, vests, nutrition, winter, sunglasses, watches), then each product page's variants (Kvas ShoeSize "8_Half",
  MenSize/WomenSize/BraSize/EquipmentSize, IsAvailableToSell, price per variant). /p-<slug>/<id>/<variant> opens that colour+size.
  The refresh downloads it to SPORTSEXPERTS_FILE (fresh = under 36 h); while fresh, the catalog file's rows are skipped. Wide =
  "Wide"/"[Extra Wide]" in the name; "Performance (Running) Shoes/Footwear" -> "Running Shoes" so cards merge; footwear without
  shoe sizes (LED lights, ice grips) -> gear. A 403/"Just a moment" from GitHub = it said no: stop. probe.yml now has grep/save/honest.
- Brand stores (Oct 16; Bastien: "readers for the brand websites ... Return policy are always better directly with the brands"):
  `WW_SITES` in scrape.py (Wolverine's Salesforce shops; Saucony Canada; Merrell's robots.txt blocks AI robots, so not read), runfree.yml job
  "brands" (`scrape.py --brands-night hist/brands.json`, a page every 3 s): listing pages' JSON-LD ItemList (`<script ... id=
  "productitem-schema">`; clothing = AggregateOffer lowPrice), each colour's page (price-standard / price-sales "C$ 230.00", else
  itemprop price) and `Product-GetSelectableVariations?pid=<upc>` (the service its size buttons use; robots only forbid
  "Product-Variation"): inventory IN_STOCK + quantity per UPC. /<slug>/<upc>.html opens that colour+size. `scrape_brand_site(key)`
  reads BRANDS_FILE (fresh < 36 h). Saucony's robots.txt allows ClaudeBot by name. Checked Oct 16 from GitHub: Brooks, New Balance,
  ASICS 403 (no); Hoka 403 (STORES.md); Salomon readable (needs its own reader); On near-empty page; Arc'teryx __NEXT_DATA__ (to check).
  First read: 360 colours, 120 on sale, 156 cards (92 new). sortcheck OK: "Endorphin Pro N Speed-lace" is a shoe.
  Arc'teryx (Oct 16, live): `JL_SITES` / `scrape_jl_site`: running lines (ARC_RUN: Norvan, Sylan, Incendo, Motus, Cormac, Silene,
  Essent) from its sitemap (lists load by script), JSON-LD per colour+size (InStock/LimitedAvailability); one price (no sales seen),
  links open the product (no size link); "N Vest" = hydration vest -> packs. 32 cards. Salomon: reader built but it answered 403
  after ~1 h of pages, and again at a page every 20 s -> a firm no (STORES.md); left out. Hoka: 403 most visits (no). Merrell: robots.txt blocks ClaudeBot -> not read.
- Fleet Feet (Oct 20; US chain, ~280 stores incl. Boulder, Chicago, Austin, Houston, San Diego): `fleetfeet_night` / `scrape_fleetfeet`
  in scrape.py, runfree.yml job "fleetfeet" (`scrape.py --fleetfeet-night hist/fleetfeet.json`, a page every 2 s, ~100 min a night):
  robots.txt allows product pages; each page's window.productData has every colour (width, price, originalPrice, sizes with the
  stores holding them) + JSON-LD brand/name. ~8,000 products from its sitemap: sale products re-read first every night, then a
  cursor through the list (full round ~3 nights; a product not read for 14 days drops). Refresh downloads it to FLEETFEET_FILE
  (fresh < 36 h). USA side only, prices converted to CAD like every US store. NOT its search service: the page's Typesense key was
  refused by my own safety check (Oct 20) and isn't needed. A 403/429/challenge = stop.
- Running Room (Oct 10; Canada's biggest running chain, Magento at ca.shop.runningroom.com): `scrape_runningroom` reads its own public
  product feed (robots.txt sitemap media/sitemap/ai_feed_sitemap.xml -> media/ai/products_N.json, ~22 files, rebuilt ~5am daily, 2 s
  apart): one record per size with price/final_price, stock qty, photo, a link that opens that colour+size. Tax class code -> group
  (`RR_GROUP`; 9xx "WR" = Walking Room, sandals, kids, swim, books left out); width from the name ("D Width") into the size. Oct 10:
  2,974 products, 1,262 on sale; sorting check clean; 4 of 4 sale prices matched on the store's page.
  Oct 12: asked for gzip, its server sometimes sends a file cut short (19 KB, the store failed): files are read with
  Accept-Encoding: identity + one retry.
- Shoe sizes, Oct 26: a Shopify shoe whose size option has an unknown name gets it found by its values (`si0` in shopify_items: 80%+ read by canon_shoe; width = WIDTH_OPT or all-width values `WIDTH_VAL`); canon_shoe reads "M5W7", "6.0(W7.5)", unisex "6/7.5" (W 1-2 above M only), "Medium (D) / 9.0".
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
- **Store recheck** (Oct 16; Bastien: "Everyone that says no we should try every 2 weeks to make sure there's no other way in"):
  store-recheck.yml on the 1st and 15th runs scraper/store_recheck.py from GitHub's servers: one polite visit per door (robots.txt
  incl. ClaudeBot/AI rules, running list page, public products.json) for every store in its STORES list (keep it in step with
  STORES.md blocked rows); emails "Store recheck: N may let us in now" / "all still say no". Open = page 200 with product data and
  robots ok -> build the reader (sortcheck + preview rules). Never a workaround.
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
  EYEWEAR_BRANDS (goodr…) never food/clothing. Food never comes in S/M/L: an item filed as food with 2+ clothing sizes ignores STRONG_FOOD
  and takes its brand's usual category (Oct 14: Sky "Rush Waffle Quarter", a quarter-zip, was food). sortcheck has the same "odd one out for its brand" rule (it found these).
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
- Gender words without the apostrophe (Oct 27, growth chat: VPO's "Rab Neutrino Pro Hoody - Mens" vs Monod's "- Men's" = two cards):
  `tidy_name` turns "- Mens/Womens/Men/Women", "(Mens)", a bare trailing "Men's" and a season code after it ("Men's S26") into " - Men's" /
  " - Women's" before the merge. Hiking CA 18,023 -> 17,735 cards. Canadian vs cross-border offers still stay separate cards (by design).
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
- Colourway duplicates (Oct 23, Bastien: norda showed "001A Abyss / Almond / Astral" as separate shoes): `drop_colour(p)` in the Shopify
  reader takes the colour out of the title when the product has exactly ONE colour option value that sits at the end / before "- …",
  "(Men's)", "|" or "Shoes" (Run Uphill, Foveo, Brainsport, Soar…; values with digits ignored: Le Coureur codes). mkey: "001-A" = "001A",
  "Spikes" = "Spike". Tested on 31 stores' live products.json before shipping.
- Shoe twin cards (Oct 26): `_shoe_name` reads New Balance "880 v15" = "880v15", a lone trail/road word as filler unless it names another model
  (`_TRAIL_MODELS` only keeps it when it changes the kind: "Ghost Trail", "Rocket X Trail"), Nike "Air Zoom"/"ZoomX"/"Zoom" (not Zoom Fly) + "Next%",
  men's (D)/women's (B) = standard width. A merged card takes the store wording whose shoe page is registered (scrape.py reads shoes/pages.json
  + us/shoes/pages.json beside deals.json), so merging never moves a page; forward_old forwards a page whose shoes moved to the page with the
  same words minus trail/road. SECOND PASS (Oct 26, Bastien: "a filter that catches this everyday when we gather data"): after the
  name merge, shoe cards landing on the same shoe page (brand + base_model words minus trail/road, gender, width, ships-from, same kind `t`)
  are joined whatever the wording; a plain-name 'daily' card joins the trail card on the EXACT same page (Boreal's "Ghost" = Ghost Trail;
  Brooks' road Ghost stays apart). sortcheck "one shoe on two cards (same shoe page)" flags any twin left in the morning email
  (OK_TWINS: Hoka Rocket X vs Rocket X Trail, Topo Ultraventure hike vs trail). Oct 26: CA 79 -> 0, USA 62 -> 0. Measure: count of shoe cards sharing a shoe-page slug + gender + width + ships-from (Oct 26: CA 81 -> 18).
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
  Oct 10 (Bastien: "the Black Friday page only talks about Canadian stores"): both Black Friday pages link each other (`bf_other`:
  "In the US? / In Canada?", FR « Aux États-Unis ? »), Canadian BF + sale-list pages name their US twin in hreflang (en-US), and the
  US BF page has the price-tracking section (US history since Oct 6).
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
- Returning: calm top (sizes line + Edit, one short line "N deals in your size today" (Oct 18; Bastien: the "found this month"
  tally looked random, then "it feels like a lot of information"; "Updated N h ago" sits in #dealsFoot at the bottom),
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
  first return per visit; the store offer waits for the next return). REMOVED Oct 22 (612 shown, 264 closed, 0 sign-ups; docs/decisions.md). Hearts picked before signing up ride in the profile as
  `watch_new` and come back with the confirm link on any device. Site tests "Sign-up bar after a deal click", "Shoe page: email me…".
  Oct 11 (Bastien: "optimize to have retention, not just a pathway to another website"; 45% of first visits land on shoe pages, 8 of
  1,160 signed up): shoe pages show a bottom bar "Didn't buy it? We'll email you when the X drops in your size" when the visitor comes
  back from a store (once per visit, never members, × = 7 days, size picker in the bar when unknown; it sends #alertBox's form);
  Black Friday + sale-list pages have `qs_box` (fit + shoe size + email, subscribe right there; ref black-friday / sale-list).
  Site tests "Shoe page: 'Didn't buy it?' bar", "Black Friday page: sign up right here".
  Oct 11 batch 2 (retention numbers: 11% of new visitors came back, watchers/members ~2x; 52% of sign-ups confirmed; the
  Friday email brought 7 visits): cards' heart is a "♡ Watch price" / « Suivre le prix » pill ("Watching"/« Suivi »; `setHearts()`);
  back from a store, `offerWatch()` showed a light card "Didn't buy it?" (REMOVED Oct 22: 382 shown, 0 sign-ups) (photo, name, price, "♡ Watch price"; once per item per visit,
  before the sign-up/store offers; lastShop.k = the card's itemKey); tapping it watches quietly (`toggleWatch(k,true)`) and non-members
  get `offerSignup(true)` ("Want an email when it drops?", shown even after No thanks). Bars `.bwbar`/`.subar` are light cards (Bastien:
  the dark bar was "hard to read"). "Check your inbox" (card + bar) has `mailBtn()` "Open Gmail/Outlook/Yahoo Mail/iCloud Mail/Proton
  Mail" by email domain (analytics signup-step open-mail|App); "or continue with Google" always on the sign-up card. `?q=` landings
  (`QLAND`, post links) get one short sign-up line (`.qsline`) right after the first deal section instead of the big card. Analytics
  signup-step watch-offer / watch-offer-yes / watch-offer-close / watchbar-view. Preview panel: "Pretend I came from a Reddit link".
  Backend the same day: `scraper/confirm_reminder.py` (refresh.yml morning step "Confirm reminders"): ONE email 20-72 h after an
  unconfirmed sign-up, same ?confirm= link, column confirm_reminded_at (supabase/confirm-reminder-oct11.sql; does nothing until
  pasted); Friday email cards have "♡ Watch the price" -> shop link + &watch=<itemKey>. Site tests "Come-back bar after a deal click"
  (watch offer first), "Cards have a 'Watch price' button", "Fits a small phone (320px)", "Check your inbox: open my mail",
  "Post link (?q=): deal, then a sign-up line".
- Single opt-in (Oct 29, Bastien via growth: "Yes on each"; ~half of email sign-ups never confirmed): supabase/single-optin-oct29.sql
  (subscribe() returns 'k:<key>' = a member now; welcome email `_gf_welcome`; consent_text/welcomed_at/bounced_at/complained_at; a member on
  another device or someone who unsubscribed still gets a link to their inbox; 30-day catch-up). Site: `joinedAs()` (homepage), `gfIn()`
  (shoe/race/trail/list pages, data-in text, watch_add right away); "Continue with Google" first on the sign-up card (`gCard()`, gBtnCard).
  Bounces/complaints: scraper/mail_health.py (morning health email + Monday report; >4% bounces or any complaint = flag; those addresses
  get unsubscribed_at). Preview: PV_OPTIN=1.
  Pasted Oct 29. Lesson: pg_net sends a transaction's requests together and Resend's free plan takes 2/s: the catch-up's 54 welcomes
  got 41 x 429 (fixed by tools/welcome_resend.py + welcome-resend.yml, 41/41 sent) and stamped last_mail_at, which the 40/hour limit
  counted, blocking all sign-ups (supabase/optin-fix-oct29.sql, pasted: the limit counts created_at). Never send a batch from SQL again.
  Trail hub (Oct 29, Bastien OK'd): grouped by province/state, folded (`HUB_JS`, HOME_TZ opens the visitor's own). Site test "Sign-up = member at once (single opt-in) + Google first".
- Analytics kinds (Oct 8): the database drops any event kind not in `ana_kinds()` (store bar/Canadian/country were lost Oct 5–8);
  `tools/check.py` "Analytics events are all recorded" fails if the site sends one it doesn't list. New kind = SQL for Bastien.
  `load` = ms until the deals show (+ connection, data size); the funnel report shows load bands vs sizes picked.
  Oct 27 (Bastien: "Are we tracking numbers correctly?"): 28% of first visits had lost their first batch (visit + welcome-view: no source,
  no landing page; ~3% before Oct 22). Fix: the visit waits in sessionStorage `gf-vq` and rides again with the next send until a send of it is
  confirmed (`vBusy`, 8 s), homepage ANA + shoe_pages page_foot `ana`; `document.prerendering` = wait. funnel "TRACKING CHECK" + "TODAY" lines;
  site test "Analytics: a first visit lost in the first send is sent again".
  Oct 28: most of those were OUR ROBOTS: a keepalive send (the last one as a page closes) skips Playwright's routes, so site-test /
  night-scan contexts leaked 'leave' events and 260 fake Fox Pro card views into ana_events. Every robot context adds
  `NO_KEEPALIVE` (tools/visual_check.py; ig_reel.py has a copy): add it to any new Playwright context that opens our pages. Funnel numbers Oct 22-27 undercount sources/landings.
- Search help (Oct 8, Bastien: people searched "alphafly" and got nothing): `searchHelp()` in index.html. No deals in your sizes ->
  "Nothing in your size for X right now, but N in other sizes" + [Show all sizes] (`view.anySize`, reset on new text); a word that
  matches nothing -> "Did you mean …?" (`suggest()`: closest brand/model word in today's data, 1 typo under 7 letters, 2 above;
  "norda000" -> "norda 000"; "alphafly 4" -> the longest part that exists); a store's name -> [See every deal at Store]. Suggest,
  never auto-replace. Analytics: kind "search" with detail "any-size:"/"my-size:"/"did-you-mean:". Site test "Search: did you mean".
  Oct 10 (stats page: "arcteryx", "goretex", "a1080v15" found nothing): search ignores punctuation per word (`hayOf`: Arc'teryx,
  Gore-Tex = GTX), a number joins its neighbour word ("1080 V15" = "108015"), never across words ("odlo" != "Hood - Long"); site test
  "Search without punctuation". Morning email "Searches that found nothing (last 24 h)" (`scraper/search_check.py`, a Python copy of
  hayOf/suggest: keep them the same): our search missed it (a problem) / typo / store name / not in their size / other side only /
  we don't carry it (store and brand ideas). Side from the device time zone. Its loose match must start at a word
  (Oct 12: 'vest' isn't in 'Five Stripes').
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
  Gender (Oct 11, a visitor: Zappos Supernova Rise 3 at $77 was the women's shoe shown in men's sizes): a name without a gender
  takes the Gender column's (" - Women's"/" - Men's"), so the cuts never merge. Visitor reports log the price as shown ("USD $77.00").
  One offer per colour (link + photo of a colour that has the size); no photo = not shown; under 25 products in stock = store left out
  (CATALOG_MIN); RW photos "&nw=400", Brooks dw/image sw/sh=400. Morning email: "Tap to check" 5 random catalog deals (catalog_spot).
  Row age (Oct 12; a visitor found adidas sizes sold out): GPT fills the file store by store, so its newest rows were 1 day old while
  adidas/New Balance/Sport Chek rows were 3.5 days old. Every ROW older than CATALOG_MAX_DAYS now leaves (not just the whole file);
  the morning email says it in ONE line (Oct 14, it was 15): "Catalog: no deals from X, Y (last read Oct 9). Leaving today: …
  Leaving tomorrow: …" (catalog-check.json `out`/`leaving`; stores halved only because rows aged out aren't flagged again).
  PARKED Oct 30 (Bastien: "let adidas stay off. we'll try later"): no uploads since Oct 26; health.py `PARKED` keeps the email quiet while
  adidasca/catalog are empty; an upload brings both back with no code change.
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
  (Oct 12) A flag whose item has no sale size at that store on today's site moves to "Already handled" in the health email
  (`report_gone`), not counted as a problem. Every card: "Wrong price or size?" / « Prix ou taille erronés ? » (bottom-left; above "All sizes & stores" on shoe cards) -> 3 reasons
  -> analytics error "report|why|item|store|price"; the health email lists the last 24 h as "A visitor says: …". Top deals skip items
  left only in odd sizes until a size is picked (`commonFit`). Returning visitor (6 h+): "Since your last visit (Tuesday): N new · deals
  you opened that dropped" (`sinceBar`, from gf-base + gf-clicks `p`; the new count is left out when the new-deals row shows it).
  Hearts work without an email; a non-member's watchlist has "Email me when these drop" (`#emailNext`, signup-step drop-ask).
- Store offers (Oct 27, Bastien: "wouldn't that be an added bonus for people to know?"; shipped empty, "yes ship it"): site/promos.json =
  [{store (the offer host exactly as in STORES/offers, e.g. "ca.shop.runningroom.com"), side ca|us, en, fr, code (optional: many are taken off in
  the cart), until "YYYY-MM-DD" (gone the day after, Vancouver date), from?, url (the store's terms)}], added by hand from a screenshot of the
  store's banner. Shows a line on top of the deals (max 2, `promoBar()`: "See <store>'s full-price gear in your size" -> store view + full price)
  and "+ Store offer: code X" on that store's FULL-PRICE cards only (`promoCard`; sale prices already carry the store's discount; codes have
  exclusions, so never taken off our prices). Analytics filter "promo|<store>", "promo-terms|<store>". Site test "Store offer: …".
  Preview: PV_PROMOS='[...]' make_preview.py (embeds it; that store's full-price US items ride along).
  AUTOMATIC since Oct 27 (Bastien: "yes for the store offers"): refresh.yml step "Store offers" = tools/offer_scan.py site (morning: one visit
  per SHOPIFY_STORES homepage, robots checked, honest UA; announcement-bar lines with a % or a code; SKIP member/sign-up/subscription/free
  shipping; NOT_CODE "auto"; a sale banner our prices don't back (0 on sale there) stays off) or --carry (other runs: this morning's offers
  from the live promos.json). Auto entries: auto, until=today, sale (banner about sale items -> "Our check: N of the M items we follow there
  are on sale, most at X% off", button = that store's deals), cards (cart-wide offer/code -> "+ Store offer" on full-price cards, button =
  full-price gear). Quoted word for word ("<Store>'s homepage today: “…”"; never translated). Hand offers: site/promos-hand.json (until).
  Phones show 1 box, computers 2. Morning email: "Store offers on the site today: …" (Bastien replies "remove X"). First day: 2XU CA+US, Wigwam.
- Canadian brands (Oct 7, Bastien): Filters chip "🍁 Canadian brands" (Canada side only, `view.cdn`, `?canadian` link for posts),
  box "Canadian companies, not always made in Canada", 🍁 at the end of the card's grey kind line (Oct 30: was after the brand, split names; `.kind.kf`, leaf never cut off). List `CDN_BRANDS` in index.html, checked by hand
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
