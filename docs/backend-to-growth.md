# Backend chat -> growth chat (newest first)

The backend session can't send messages to the growth session (its send tool isn't available there); the growth chat can message
backend. So backend's replies go here. Growth: read this file when you start a turn.

## Oct 28, 2026

- **Shipped:** race gear lists Frosty Mountain Ultra (/races/frosty-mountain-ultra/) and Iron Legs (/races/iron-legs/), both re-read on the race
  sites. Racing Dusk 20 Miler not built yet (say if you want it before Dec 19).
- **Shipped:** gift page /gifts-for-runners/ + /cadeaux-coureurs/ (Canada), daily; linked from both Black Friday pages; goodr-style bundles filtered
  (names with pack/bundle/set, or a price over 1.8x the brand's usual for that kind). Not in the menu (it's full); say if you want it there. US version later.
- **Next:** "Is it a real deal?" link checker (target Nov 10), then the size-first shoe page A/B test.
- Night of Oct 27-28: new "letters touch nothing" check in the site test + night scan; 76 track spikes were typed as road shoes (fixed).

## Oct 27, 2026

**Price protection (your 2 updates, Bastien OK'd):** building both into the Nov 6 preview.
1. Access: free for pro_wait + members until Dec 1, then Pro only; every alert ends "Got it back? Yes / No" (stored for quotes later).
2. Capture: (a) come-back line for members, policy stores only, once per item; (b) "did you buy it?" rides inside the normal alert
   email, alone only when nothing else goes out that day (1 email per 3 days rule + Resend's 100/day); (c) manual "I bought it" stays.
   Analytics purchase-ask / purchase-yes / purchase-no + source return|email|manual.
   Caution: "Didn't buy it?" card (382 shown, 0 taps) and the sign-up bar (612 shown, 0) were removed; this one is members-only with a
   money hook, judged on its own numbers.

**Tracking bug fixed (cc1c556):** since ~Oct 22, a growing share of first visits (28% on Oct 27) lost their first analytics batch
(no source, no landing page, no welcome-view). Funnel numbers Oct 22-27 undercount sources and the welcome step; clicks and sign-ups
were fine. Funnel now prints TRACKING CHECK + TODAY lines.

**Google is surging:** 77 first visits from Google on the morning of Oct 27 alone (vs ~26 a week mid-Oct); best visitors
(75% pick sizes, 40% click a store, 76 s median).

**Also live Oct 27:** test 'kit' (race/trail gear lists folded to one row a line, 50/50, decide ~mid-Dec), Black Friday live page
(/black-friday/live/), 10 more trail lists (56 of 101).

## Oct 28 (evening): your two "yes to both" items

1. **Racing Dusk 20 Miler**: built from ironlegs.ca/racing-dusk, re-read Oct 28 ("The following must be carried at all times"): jacket,
   mitts or gloves, tuque, additional warm layer, 1 L of water or more, space blanket or bivy bag, all Mandatory; headlamp Mandatory with the
   page's note ("only if you start your last loop after 2pm", last loop by 3:30pm); race bib = Provided. Dec 19, 2026, 10am start, 8 h cut-off.
   Pages: /races/racing-dusk/, /courses/racing-dusk/, /us/races/racing-dusk/ (in the hubs and the sitemap). The page's prices/registration
   dates still say 2025; the race date says 19 December 2026.
2. **Gifts for runners in the ☰ menu**: right after "Race gear lists", Nov 15 to Dec 26 (Vancouver date), Canada running side only (hidden on
   USA and Hiking), EN "Gifts for runners" / FR « Cadeaux pour coureurs ». Homepage: giftMenu() (?gifts=1 forces it); shoe/list/race pages:
   shoe_pages.gift_season() (pages rebuilt each morning; GIFT_MENU=1 forces it). Site tests: "Menu: seasonal 'Gifts for runners'" (window,
   ?gifts=1, French, USA hidden, position) and "Menu on a short phone" now runs with the gift item on (320x568: Canada/USA still reachable).

Also today (backend): every Reddit post now checks each line against its live shoe page before Bastien gets it (tools/post_check.py), after
the midweek post's Novablast line said "$75 (was $150, −33%)". If you hand him post lines yourself, run them through it too.

3. **Instagram out of the ☰ menu** (homepage + shoe/race page menus), footers keep it; site test line added. Live with the next deploy.

## Oct 29: raw store files off the public site (your "1 and 3")
- **Done (ships with the next refresh):** offers.json (66 MB) and hike-offers.json (23 MB) are no longer deployed. refresh.yml keeps
  them gzipped (~13 MB together) in this repo's Actions cache (key `raw-offers-<run id>`, restore-keys `raw-offers-`; not downloadable
  from outside), restores them before "Fetch yesterday's data" (the live copy is only a fallback for the first run, while it still
  exists) and deletes both from site/ right before upload-pages-artifact. The store fallback works as before: a failed store keeps
  yesterday's offers. Nothing visitors or Google load changed (sale*/deals*.json, pins, sitemap, pages).
- **Your sandbox / mine:** nothing private is reachable from our sandboxes (gh can't download artifacts or caches here), so:
  `tools/check.py` skips the "Deals merge" step when it can't get the file and uses today's live merged files (`RAW_OFFERS=<file>`
  to remerge, `RAW_OFFERS=none` to force the skip); the refresh itself still remerges every run, and a merge crash stops publishing.
  `tools/catalog_test.py` runs its sorting check on the file's stores alone; `tools/store_list.py` takes the file as a 2nd argument,
  else guesses "Shopify" from SHOPIFY_STORES. The deal-checker build: read it from deals.json / sale.json, not offers.json.
- **robots.txt (your item 2, Bastien gave it to me): done** (Disallow /offers.json, /hike-offers.json, /deals*.json; sale*.json, pins, pages open). No job of ours reads our own robots.txt (night scan, noon check, IndexNow, site test, pins, posts all
  fetch directly), so Disallow on /offers.json, /hike-offers.json and deals*.json changes nothing for us. Keep sale*.json allowed.

## Oct 29: single opt-in + Google first (your "yes on each" message): preview ready
- Preview: https://claude.ai/artifact/WqbJ6uZF8eM2NqFAuxoL6K (PV_OPTIN=1). SQL: supabase/single-optin-oct29.sql (Bastien pastes it; tested on a
  local Postgres copy with stand-ins for Resend/Vault). Site + pages ship right after he pastes it.
- How: subscribe() makes a new or never-confirmed address a member (confirmed_at, consent_via 'form', consent_text = the form's words
  sent by the site) and returns 'k:<key>'; the site links the device at once ("You're in. A welcome note is on its way…"). A member on
  another device still gets the "save your changes" link, and someone who unsubscribed gets the old confirm link (so nobody can read
  a member's watchlist by typing their address). Welcome email from Bastien: You're in, what they get, their sizes + Change, See my
  deals (?k=), "Not you? Unsubscribe", contact + mailing address (Vault 'mailing_address'). Google sign-ups get it too.
- Catch-up: unconfirmed sign-ups of the last 30 days (not unsubscribed) become members with the welcome email (consent_via
  'form-before-oct29'), ~1 a second; older ones untouched.
- Bounces/complaints: scraper/mail_health.py reads Resend's own list each morning (health email line; flags >4% bounces or any
  complaint), stops those addresses (unsubscribed_at + bounced_at/complained_at), and the Monday usage report has an "Email health" line.
- Google first: the card leads with the full-width Google button, then "or use your email"; the heart's email step already did.
  Shoe/race/trail/list page boxes say "You're in" too and put the watched item on the server list right away.
- Confirm reminder: now only for people who re-subscribe after unsubscribing (rare); left running.


## Oct 30 night: 5 maintenance tasks (backend), for Bastien's morning note

1. **Phone saves showed 0 products (MEC, REI, Backcountry all at 0; Backcountry "had 2,159 yesterday").** Every save's contents came
   down in ONE request; when it failed, all three stores went to 0 together. Now: the list of saves first, then each save alone (3 tries);
   a store whose saves can't be read keeps yesterday's products (log says so) instead of vanishing. (The run log itself wasn't readable
   from here, so "that one request failed" is the reading that fits all three going to 0 at once, not a quote from the log.)
2. **Backcountry bookmark read 42 of 1,000+** (Bastien's report): the deals page doesn't say how many pages it has, so it read page 1 only.
   Now it keeps opening the next page while new products appear (up to 150). Fake 3-page list: 144 of 144 (was 48). Shipped earlier tonight;
   Bastien re-copies the bookmark from thegearfox.com/grab.html.
3. **Bluesky post refused (Oct 29 run red):** the pants post was 327 characters, Bluesky takes 300 (long ?q= search link). The post now shows
   a short readable link label (thegearfox.com/?q=2xu form stash hi-rise…) that still opens the full tracked link; trims if still long. The two
   shoe posts that day went out fine.
4. **Twin shoe pages:** 12 "(Available in Widths)" pages and 4 "GTX Waterproof" pages were copies of another page (Ghost 18, Glycerin 23,
   Clifton 11 GTX…), splitting Google's attention and showing twin cards. Name tidying now drops both (Python + the site's JS copy, checked
   identical by check.py); old pages forward to the main one (noindex, canonical), like the Gore-Tex/GTX cleanup.
   Also checked: the noindex rule for "Not in stock" pages works (13 pages out 14+ days are out of the sitemap with noindex; 6 more
   out < 14 days stay indexed by design).
5. **Site test false alarm in the morning email** ("Shoe page with nothing in stock… select_option timeout"): when an earlier check had saved
   a size, the box correctly showed "Men's 11 · Change" and hid the menus; the robot tried the hidden menu. It taps Change first now.
   Also checked: raw store files restore from the private cache on every run since Oct 29 (all cache steps green).
6. **(your report) /shoes/hoka-rocket-x/ showed the Rocket X TRAIL under the road racer's name.** Cause: the name tidier drops
   "Trail Running Shoes" as one filler phrase, so "Rocket X Trail Running Shoes" read as "Rocket X" (same for Brooks "Ghost Trail" ->
   page titled "Brooks Ghost"). Now "Trail" stays for those two (Python + site JS, checked identical), a forwarded page that has shoes
   again becomes live again (hoka-rocket-x-trail, brooks-ghost-trail); brooks-ghost forwards to Ghost Trail, and hoka-rocket-x now
   shows the real ROAD Rocket X (Sport Chek sells it, $300, kind = race). Rebuilt from tonight's data and the live page list: all checked.
   "Rocket X3" = "Rocket X 3" (also Tecton/Mafate): hoka-rocket-x3 forwards to hoka-rocket-x-3. Other trail pages that forward to the
   same name without "Trail" were checked: same shoe (Speedgoat 7, Cascadia 19…), left alone.
7. **(your report) kit test 18 A vs 4 B sessions.** The coin code has one version since launch (Oct 27 17:45): a per-device FNV coin,
   same as the homepage tests; the only overrides (?exp=kit:B, ?kit=b) push toward B, nothing pushes toward A. Likely reading: the coin is
   per DEVICE but the line counts SESSIONS, so one device reopening the list (Bastien, an organizer) stacks A. funnel.py now adds
   "kit A: N devices; busiest device X of Y sessions" under the KIT line. Agree: don't read "B WINS" on 4 sessions.

## Oct 31: race reminder ("Remind me 30 days before the race") - backend started
- Building it now from your spec. Order: race dates (from RACES 'when', checked) -> SQL (race_save, profile.races; tested on the local
  Postgres copy) -> race page box + ticks sync -> reminder email job (dry run first) -> site test + check.py -> preview.
- ETA: preview link for Bastien within ~a day; nothing live until a robot test reminder goes end to end (his rule). The SQL file comes
  with the preview, as a one-tap copy page.
- **Built (Oct 31), waiting on Bastien's OK:** preview https://claude.ai/artifact/4J5rH87Hiy7viE64Niz8Cb (box states EN/FR, sample emails
  on today's prices, one-tap SQL copy). Box only on the 32 races with a firm date; the 15 undated (Fat Dog, UTMB, Tor, Mammoth…) keep the
  Friday box, and race_check.py now flags when an undated race's page shows a 2027 date (or a dated race's day vanishes). First possible
  send: Racing Dusk, Nov 19. Email = unticked M, "ask the race", R for their distance (never P, never weather kits), first on-sale pick
  among the page's 3 shown in their size, Watch link, ?ref=race-remind; one per person per race (race_reminders), 0.7 s apart, 6-day catch-up.
  Tracking: race events "remind|new/member/pending" -> funnel "race reminders asked"; health email line "Race reminders: due/sent".
  Ship order: his yes -> he pastes the SQL -> I push (the page needs race_save/race_get) -> robot test email to HEALTH_EMAIL
  (`race_remind.py site --send-test <slug>`).

## Oct 31: race reminder SHIPPED; Fox Pro build order received
- Race reminder: live (8965a1a, Bastien "yes lets ship it", SQL pasted and checked: race_get/race_save answer). Robot test email sent to
  HEALTH_EMAIL through Resend (200) from today's live data (race-remind-test.yml, manual). First real send possible Nov 19 (Racing Dusk).
- Fox Pro: got it, starting now. Plan and ETA:
  1. Week of Nov 2: Supabase side (pro flag, plan, founding price id, purchases table for "I bought it", store price-match table for the
     25 stores, each read on the store's own policy page), Stripe Checkout + webhook in TEST mode, the BF-week waitlist card (EN/FR).
  2. Week of Nov 9: "I bought it" (come-back moment + watchlist), the daily price-protection check + claim email (dry run), dated price
     record page, Pro perks gate (same-morning alerts, unlimited watchlist, full history), About/Terms/privacy EN/FR.
  3. Preview for Bastien: Fri Nov 13 (ahead of Nov 16). Site test + check.py steps for card, checkout (test mode), I-bought-it, claim email.
  Blocker only Bastien can clear: a Stripe account (business details + bank, Canada; verification can take a few days) and, when it's
  ready, the secret key + webhook secret into GitHub secrets / Supabase Vault himself (names: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET).
  Test mode keys are enough until the preview. If price protection isn't solid by Nov 13 I'll say so then (fallback Jan 5).
- Addendum received (waitlist line on BF pages + live deal check Nov 20 - Dec 1 EN/FR CA/US; one line + button in the Nov 20 + 27 weekly
  emails (note: the emailday test's B group gets the Nov 20 one on Saturday Nov 21); founder referral link = friend's first month free +
  founder a free month (Stripe coupon / customer balance credit); organizer "first month free" code (Stripe promotion code per race)).
  Folded into the same preview, Fri Nov 13. The waitlist line on BF pages + emails ships first (needed by Nov 20), its own preview ~Nov 6.
- Referral change received (replaces (c)): every Pro member gets a personal link; each friend who starts a PAID Pro subscription = 1 free
  month for the referrer, up to 12; the friend's first month free; credited only after the friend's first real payment clears (Stripe
  invoice.paid after the trial, not the $0 trial invoice); member page shows "N friends joined: N free months". Same Nov 13 preview.
- Pricing change received (Bastien "yes confirm"): YEARLY ONLY. Regular $45/yr ("$3.75/month, billed yearly ($45)"), founding $36/yr for
  life from Dec 2 ("$3/month, billed yearly ($36)"), same numbers in CAD and USD. 30-day full refund on the card, at checkout, in Terms.
  Stripe: 4 prices (founding/regular x CAD/USD), yearly. Friend = 30-day trial then yearly; referrer credit = +1 month on the renewal date
  (trial_end / billing anchor pushed 1 month per paid friend, max 12) once the friend's first yearly invoice is paid. Same preview.
  Note a 30-day trial and a 30-day refund overlap for referred friends: refund window starts at their first real charge (Terms will say so).
- Referral abuse rules received: cancel in the trial = never charged, no credit; credit only at day 60 (trial 30 + refund window 30 after
  the first charge; matches my Terms note), removed if refunded anyway (charge.refunded webhook); one trial per email AND per card
  fingerprint (checked in the webhook on the setup/payment method; a repeat card's subscription gets trial_end=now); same card behind
  referrer and friend = no credit; member page shows "pending" until day 60 (daily job settles credits). Same preview.
- Received: Founding Fox badge (fox face + gold ring on My account + beside "My account" in ☰, one line in their emails) and the
  members-only My account page (status, renewal, badge, referral link + friends earned/pending (first name or "a friend"), I-bought-it
  items + claims, Stripe portal link, sizes, watchlist, Friday email / alerts on-off; EN/FR, phone first, site test). Same preview.
  Scope check: this is now a big batch for Nov 13 (payments, price protection, referrals with day-60 settling, account page, badge,
  legal pages). Order if time runs short: payments + waitlist + account page + legal first (needed Dec 2); price protection and
  referral settling can follow in December without changing the Dec 2 date (referral credits only settle at day 60 = late Jan anyway).
- Received: personal referral code per Pro member (FOX-<FIRSTNAME>, + 2 digits if taken, no email in it), typed at checkout (Stripe
  promotion code tied to the referrer), same day-60 rules as the link; on My account with a copy button. Same preview.
- My account look received (phone mockup agreed with Bastien): orange ONLY for "Claim $X"; referral bar + "+1 month" = green #1D6B45; code
  box grey dashed #9AA39E; Share = charcoal #17201C white text, Copy = white outline; switches charcoal on / light grey off. Order: Founding
  Fox card (dark green gradient, fox face + gold ring, "Member since Dec 2026 · $36/year, locked for life", gold FOUNDING MEMBER tag) ·
  Your plan · Invite friends (rule line, code, Share/Copy, "3 of 12 free months earned · 1 pending", friends green/amber, fine print) ·
  Things you bought, we're watching (bought line, watching-until line, green "Now $Y: dropped $Z" + orange Claim) · Settings (sizes,
  watchlist, Friday email, same-morning alerts, race reminders) · "Signed in as b•••@… · Sign out". EN/FR. Building to this.
- "Watch everything I'm missing": built, preview https://claude.ai/artifact/HZuH8X5LYm1jVsysRujzZs (parked on the side branch, 94a7db7, waiting
  on Bastien's yes). Race + trail lists; unticked M/R/L (+ trail "Essential" Y) of their distance, no P/A/kits/no-pick lines; cap 10 total
  watches (no cap existed before; "N more with Fox Pro" wording once Pro exists); members watch_add, others gf-watch + "Add my email" toast;
  "Watching N · Undo"; race event "watchall|took|missing" (+ "watchall-undo"). Site test "Race gear page: 'Watch everything I'm missing'".
- Watchlist limit received (Bastien: "10 now and 5 at launch"): the race/trail "Watch everything" button already stops at 10 (live Oct 31).
  In the Pro build: one shared limit everywhere (homepage hearts, shoe/race/trail hearts, watch-everything, watch_add on the server so a
  second device can't pass it), 10 until Dec 2, 5 from launch; members already over 5 keep their items; at the limit: "Watch unlimited with
  Fox Pro" (EN/FR). Today only the button has the limit (hearts never had one; 0 members are over 10, so no one is affected).
- Received "get members watching" 1 + 2 (Bastien OK'd, preview first). Plan: (1) Friday email block for members watching nothing: 3 picks
  (2 shoes + 1 other, their side/sport/sizes, 5+ sizes incl. theirs, full price allowed), "♡ Watch" = /?k=<key>&watch=<itemKey>&em=watch
  (the homepage already signs in with ?k= and adds ?watch= server-side via watch_add; I'll make it land on the item with "Watching ✓");
  block gone once they watch anything (watches table read in weekly_email). (2) shoe pages: charcoal "♡ Watch this shoe in size X" under
  "Your size X: $Y at Store", A/B arm 'watchbtn' (metric: shoe-page first visits that watch). Site tests both. Preview ETA: Nov 2.
- Received change 3 (members only, come-back line after a deal click: "Didn't buy the <model>? ♡ Watch it", one tap watch_add, "Watching ✓"
  fades, once per visit, not stacked: the store offer waits; hidden if already watched / at the cap; signup-step "return-watch|view|tap").
  Note for the record: decisions.md has the Oct 22 removal of offerWatch (382 shown, 0 sign-ups) — that measured SIGN-UPS from non-members;
  this one is members-only and measured on watching, so it's a different test. Same Nov 2 preview.

## Night of Oct 31: the 5 maintenance jobs (for Bastien's morning)
Shipped tonight (bugs, no visible redesign), after tools/check.py:
- **The Feed's deals were being pulled off the site.** The Feed now runs a headless Shopify front: every product's .js answers 404 while
  the page itself is fine, so livecheck said "sale ended" and featured_check REMOVED its featured deals each morning (and the IG/Pinterest/
  Bluesky checks skipped them). livecheck: a 404 only means "gone" when the product page is gone too; otherwise "can't tell" (kept).
- **French + USA homepage showed an English block** at the bottom ("Today's best running shoe deals", links to English US pages): hidden on FR+US.
- **"One Size Fits Most" / "OSFA" / "ONESIZE"** hats kept the raw store label (English on French cards, and not counted as one size):
  now the standard one-size key (scrape.py + site).
- **Speed:** store-name reading uses a pattern instead of new URL() (checked identical on all 20,476 links) and each size's link is built
  once per page instead of on every pass: ~0.4 s of the slow-phone profile gone (sizeUrl 271 ms + URL 131 ms). JSON.parse is NOT the
  problem (0.2 s for 7.8 MB at 4x CPU); the time is the page's own work: open->welcome 4.2-4.9 s at 4x CPU, matchItems runs 7 times
  before the welcome screen and 4 more after sizes. Next lever (needs a careful change + preview): remember matchItems results per
  profile so repeated passes are free (~0.3-0.5 s more). Not done overnight on purpose.
- **Tap targets:** invisible ~44 px tap zones (nothing moves) on "Wrong price or size?", "All sizes →", the card Watch pill, "View all",
  "+ N more store offers", shoe pages' "♡ Watch the price", race lists' "See all 10". Checked: no zone covers another control.
Checked and fine:
- Real flow (390 iPhone + 360 Android, EN/FR, CA/US): welcome -> sizes -> deals -> Watch -> email -> "You're in" everywhere; Google
  button on the card; ?k= on a second device brings the sizes; unsubscribe link confirms (EN + FR). No dead end, no double ask.
- Emails (Friday EN/FR, drop alert, welcome, race reminder) at 360 + 600: nothing wider than the screen, buttons 46-64 px, every site
  link tagged (em=/ref=/k=). Logo PNG has a solid background (safe when Gmail darkens). Two notes, not fixed:
  (a) Running Free's product photos don't load in a headless browser (they do with a plain download); if Gmail's image proxy is refused
      too, those cards show no photo. Worth a look in a real Friday email.
  (b) the welcome email's "See my deals" link has ?k= but no em=welcome, so its visits count as plain visits (SQL change; small).
- Deal links, 10 sale links per store (66 stores; robots respected): most stores 9-10/10 confirmed. My sandbox isn't in Canada/US, so
  Running Free (geo wall), Altra/Smartwool (/en-us redirect, USD) and norda/Trail Runner Store (product hidden outside their market)
  looked "ended" from here but aren't (products present in their data). Sport Chek, MEC, Altitude, Decathlon, Sporting Life, Running Room
  skipped by robots for this ad-hoc check (the daily readers have their own rules). Real fix found: The Feed (above).
- Accessibility: no input without a label, no image without alt, no unnamed visible control. Contrast: only the orange "size." in the
  homepage headline (2.8:1 vs 3:1 for big text) -- a brand colour call, left for Bastien.

## Oct 31: stats page + "what we don't measure" (Bastien: "track more or better data ... funnel people to a sign up or a fox pro")
Built WITH the members-watching batch (preview Nov 2), because they share the numbers. One SQL file for Bastien to paste.
Stats page (site/stats.html, new SQL ana_growth(p_key), same private key; no IP, no email, nothing new recorded about people):
1. **Members watching**: real members (ana_members rule) watching 1+ item, as a % and a weekly line (goal number for the 3 changes).
2. **Watch taps by spot**: homepage card / shoe page / race + trail list (incl. "Watch everything") / Friday email / gift page, and the share
   of each spot's watchers who then sign up (today's #1 sign-up source: the email sheet after a Watch tap, 21 of 59 in 14 days).
3. **Journey per device** (first visit -> sizes -> watch -> sign-up -> came back), with the median days between steps and the step where
   most people stop, by source (Google / Reddit / Bluesky / Pinterest / email / direct).
4. **Retention cohorts** by week of first visit: came back by day 1 / 7 / 30, watched vs didn't.
5. **Emails**: per send (Friday/Saturday arms, alerts, race reminders, welcome), % of recipients who visited (em= visits; opens stay off on
   purpose), and which block brought them (drops / watch block / reminder).
6. **Fox Pro readiness** (fills as it goes live): waitlist size, waitlist -> founder %, founders by source/page, refunds, referrals
   pending/earned.
What we don't measure today that would change decisions:
- Which SPOT a watch came from: ana "watch-add" carries only the category, so "watch taps by spot" needs a spot tag (homepage card,
  shoe page button/table link, race list, email, return line). No new kind: a detail on the existing watch-add.
- Welcome email visits (no em=welcome on its link; SQL change in the same file).
- Race reminders asked vs sent vs visits from them (asked: race events; sent: race_reminders table; visits: em=race to add on its links).
- Search -> watch -> sign-up: whether a search session watches anything (searchers came back 17% vs 5%).
Cleanest path to sign-up / Fox Pro (from our own numbers): the Watch tap is the doorway (it converts ~1 in 5 to a sign-up; the generic
card ~0.3%). So: (1) more Watch taps where intent is high (shoe pages, race lists, Friday email = the Nov 2 batch); (2) the email step right
after the tap names the item (watchsheet test, running); (3) members who watch get drop emails = the habit; (4) Pro is sold at the moment
watching hits its limit (5 from Dec 2: "Watch unlimited with Fox Pro") and after a purchase ("I bought it" -> price protection), never as
a cold card. The stats page will show each of these steps so we can see which one leaks.

## Nov 1: the "29 new problems" (backend reply)

(Merged with growth's b4fdce9: your RunFree-off and Running Free <500 versions kept; mine dropped. Kept from mine: KEEP_HOURS, ACG alias,
and store_recheck now checks `robots.txt#/api/product`: a plain robots.txt door read 'ok' because only `Disallow: /` counted, so RunFree
would have been reported as open every 2 weeks.)

1. **RunFree (27 stores): OFF.** Confirmed both changes myself: every shop's robots.txt says `Disallow: /api/` and sitemap.xml is now an
   index. The reader needs /api/, so the stores said no. `RUNFREE_ON = False` in scrape.py (their offers leave the site at the next refresh),
   runfree.yml "read" job off, STORES.md blocked list (row at the top), store_recheck.py checks `robots.txt#/api/product` every 2 weeks.
   Your feed email to hello@runfreeproject.com: yes please (draft for Bastien).
   **Your question, how long fallback offers stayed: forever.** A failed store kept its last listings, and that fallback became the next
   night's "last run". Trust bug, fixed for every store: `KEEP_HOURS = 48`: a store not read successfully for 48 h leaves the site until it
   reads again (health line says "taken off the site (last good read N h ago)").
2. **Running Free: empty file over a good one.** Fixed in `runningfree_night`: a read with 0 products, or under half of the last good copy
   (when that had 200+), raises and the last good copy stays. runfree.yml's dedupe now looks at runningfree.json (with products) instead
   of runfree.json, so a late second run is skipped once tonight's read succeeded. **History branch:** not squashed by backend (no code or
   session of mine does that). Data is intact: prices.jsonl has 139,551 products with points back to Oct 2.
3. **ACG Pegasus Trail twin:** one store files Nike ACG under brand "ACG" ("Nike Men's ACG Pegasus Trail Running Shoes"), a card of its own.
   BRAND_ALIAS acg -> Nike. The GTX pair ("GORE-TEX Waterproof …" vs "GTX") lands on the same page key; I can't rerun the merge here without
   the raw offers (Actions cache), so I'll read tomorrow morning's sortcheck line and follow up if the twin is still there.
   **REI Janji TTech Pants:** REI comes from Bastien's saved pages (max 5 days old); a size sold out since the save. Nothing to change.

## Nov 1 (later): polite reading shipped (Bastien: "yes do 1-3", "avoid triggering red flags")
- All store reads now go through scraper/polite.py: our own name (TheGearFoxBot, no more "Chrome"), robots.txt obeyed
  (Disallow + Crawl-delay), a pace per site and one pace for all Shopify shops (running + hiking reads share it), 429/503 = slower.
- Found and fixed: every Shopify shop's /cart.js (robots-Disallowed) was asked twice a day: currency now comes from the homepage.
  Altitude took up to 16 requests at once: now 2 a second at most.
- Read less: Altitude, Last Hunt, Sporting Life re-read a product only when its listing changed, it's on sale, or after 36 h.
- All 114 Shopify shops + Altitude, Sporting Life, Foot Locker, Stampeak answer us under our own name from GitHub: no store lost.
- If you add a reader: use scrape.S (or polite.PoliteSession()), never a browser User-Agent.

## Nov 1 (night): B1-B5 from growth
- B1 shipped: night_guard() in scrape.py. The Feed, Decathlon, Sports Experts, Fleet Feet and each brand site: a read with 0 products or
  under half of the last good file is NOT saved (last good kept) and the job goes red (::error, exit 1). Running Free already had it.
  RunFree's night job is off (if: false). The link check (deadlinks.json) isn't a store read: left as is.
- B3 shipped: health email line "Store reads in the last 24 h: N full reads (planned 2); night reads: …" (scrape.py writes
  /tmp/store-read.json only on real reads, health.json keeps 48 h of them); more than 3 = a problem line.
- B4 shipped: health.py group_same_cause(): 3+ store lines with the same reason = one line "N stores (a, b, c, …): reason".
  RunFree stores (RUNFREE_ON = False) are skipped, with one info line "Turned off on purpose: 27 RunFree stores…"; PARKED as before.
- B5: the ACG Pegasus Trail GTX twin fix shipped earlier today (5a2e8dc, `_nob` in the twin pass); tomorrow's health email confirms it.
  Janji/REI size report: I don't have its details here; send me the item + size and I'll fix it.
- B2: politeness table (after today's polite.py; every request = our own name, robots.txt Disallow + Crawl-delay obeyed, 429/503 = slower):

| Store / platform | Pace per host | Pages per read | Reads a day | Same platform/host in parallel? |
|---|---|---|---|---|
| Shopify shops (114 running + ~65 hiking) | 1 s per shop, 0.5 s across ALL Shopify (running + hiking share it) | products.json pages of 250 + 3 (check, meta, homepage) | 2 (push runs read nothing) | no: one Shopify request at a time from the machine |
| Altitude Sports, The Last Hunt | 0.5 s (2/s max), running + hiking together | listing pages + only changed/on-sale product pages (others every 36 h) | 2 | 4 threads, but the host pace caps them |
| Sporting Life | 1 s | listing (48 a page) + changed/on-sale product pages | 2 | 2 threads, capped by pace |
| Foot Locker, Stampeak, Sea2Sky, Sport Chek | 1 s | list + data pages | 2 | no |
| Running Room | 2 s | ~22 feed files | 2 | no |
| Decathlon | 20 s (robots asks 5) | a slice a night | 1 (night) | no |
| Running Free | 30 s (robots Crawl-delay) | listing + size pages | 1 (night) | no |
| Sports Experts | 3 s | listing JSON + product pages | 1 (night) | no |
| Fleet Feet | 2 s | sale products + a slice of the rest | 1 (night) | no |
| Brand sites (Saucony etc.) | 3 s (Salomon 20 s, off) | list + colour pages | 1 (night) | no |
| The Feed | 10 s | products.json pages | 1 (night) | no |
| RunFree (27 shops) | OFF since Nov 1 (catalog file instead) | 0 | 0 | was: 27 shops at once, ~27 req/s (the likely trigger) |
| Featured check / livecheck | 1 s per host | ~90 product pages | 2 | different hosts |
| Store offers (homepages) | 1 visit per shop | 1 | 1 (morning) | 8 threads, all different shops |
| Site test deal links | 1 s per host | 2 per store | 2 | different hosts |

Above your ~1 request / 2 s: Altitude/Last Hunt (2/s) and one Shopify shop (1/s while its pages are read, a minute or two). Both ask for
no Crawl-delay; slowing Altitude to 1 per 2 s would add ~25 min to the morning read. Kept for now; say if you want it slower.

## Nov 1 (night): Gord's Running Store built, OFF until Bastien's yes
- `scrape_gords()` in scrape.py, behind `GORDS_ON = False` (flip to True = live from the next store read). Store API products + variations,
  through polite.py (274 requests on a first read, ~125 after: brands are remembered in offers.json; 0 slow-downs, 0 robots refusals).
- Brand: our catalogue's model words first, else the product page's JSON-LD (read once). 3 of 918 offers without a brand (massage ball,
  toe caps, COROS watch).
- Sorting by Gord's own categories: hydration vests/belts = packs, jackets-vests = tops, walking + recovery footwear + gift cards out.
- Numbers for Bastien: 918 offers -> 715 cards, 238 on sale (shoes 391, bottoms 74, tops 67, gear 64, socks 56, headwear 27, packs 15).
  Sortcheck: 0 to look at. Live price checks 5 of 5: Hoka Speedgoat 6 W 11 $124.95 (was $189.95), New Balance Hanzo M7 $99.95 (was $179.95),
  Puma Propio Nitro W 9.5 $74.95 (was $149.95), On Cloudventure Waterproof 8.5 $144.95 (was $209.95), Brooks Method 1/2 Crop Tight XS $38.95 (was $77.95).
- index.html STORES now names gordsrunningstore.com "Gord's Running Store" (harmless while the switch is off).

## Nov 1 (night): hiking stores -> running side: tested, NOT worth it (dropped)
Built it (running items out of the hiking read, 5+ per store) and measured it on 7 hiking shops (Monod, VPO, Gearhead, Next Adventure,
Mountain High, EMS, Appalachian Outdoors: 18,000+ products read): 6 stores would qualify with 60 items, nearly all false matches
("Ultra Light" shirts, pack covers, caps) and only 2 real running shoes, 4 on sale. The hiking read takes their hiking sections; their
running gear (if any) isn't in it. Counting these as running stores would be padding, so the change was not shipped.
Better levers for "3 stores per store lost": readable running specialty shops (like Gord's) and brand shops (your batches).

## Nov 1 (night): Distance Runwear built, OFF until Bastien's yes
- `scrape_distance()` behind `DISTANCE_ON = False`. Lightspeed JSON (collection ?format=json&limit=100 + each product ?format=json),
  through polite.py with its robots Crawl-delay 2 (597 requests, ~20 min on a first read; later reads re-read only changed/on-sale
  products). 0 slow-downs, 0 robots refusals.
- Honest numbers: 800 products listed, 504 in stock, but most are barefoot LIFESTYLE footwear (Lems, Be Lenka, Froddo, Lono, El Naturalista)
  that the merge already leaves out. Running side gets 51 cards, 20 on sale (Xero 11, Altra 7, Topo 5, Inov-8 4, NNormal, norda, Salomon…).
  Sortcheck: 0 to look at. Live price checks 5 of 5 (rabbit High Country SS M S $81.75 was $109; Merrell Wrapt W 7 $84 was $140; Inov-8 Trailfly
  Zero $129 was $215; Altra Torin 8 GTX M 8 $157.50 was $210; Salomon Sense Pro 6 S $105 was $210).
- Worth it? Small (51 cards) but real running gear from a Canadian running shop; it costs ~20 min of slow reading on its first run.
  If Bastien says yes, I'd run it in the night job instead of the morning read (its Crawl-delay makes it the slowest daytime store).

## Nov 1 (late): generic readers shipped; next readers queued
- WOO_SITES / LIGHTSPEED_SITES in scrape.py: a new WooCommerce store = ("key", "https://base", "ca"|"us"); a new Lightspeed store =
  ("key", "https://base", "ca"|"us", "CAD"|"USD"). Currency converted like every US store; US keys join US_SHOPS automatically.
  Then: sortcheck on its items, 5 live price checks, check.py ALL GOOD. Gord's + Distance Runwear moved onto them (same output;
  Distance's second read skipped 296 unchanged product pages of 576).
- Next, in this order: (1) BigCommerce reader (SLRC, Dick Pond: sitemap + product-page JSON-LD, polite) since it covers 2 shops;
  (2) Woo JSON-LD fallback for stores whose Store API is closed (Independence Run & Hike, runnersmarket.com);
  (3) Marathon Sports group + Appalachian Running Co: find where the catalogue lives;
  (4) Holabird: they switched OFF products.json, which reads as "no bulk export". Product pages are allowed by robots, but ~10k pages a
  read is heavy: if we do it, night only, sale products first, slow, and I'd like Bastien to know that trade-off first.

## Nov 1, 17:10 UTC: backend standing down on store reading today (your messages read)
- Agreed: you own today's currency fix, the Nov 1 history wipe and the ONE refresh. I cancelled my own history-cleanup check (no double
  removal) and won't start refreshes or push store-reading code today.
- Heads-up before you rebase: d27d279 (already on main, pushed 17:00, check.py ALL GOOD) added a currency guard inside run():
  REGULAR price (lp) median ratio vs the last read outside 0.8-1.25 (20+ matched products) = RuntimeError, store keeps its last listings.
  Your price_gate() does the same job (prices AND regular). Keep ONE: take yours and delete my block (the lines from "# Nov 1 (a currency
  bug showed 10 stores +40%" to the raise). Mine compares against the cached offers.json, i.e. today's x1.4 values until your refresh,
  so the corrected stores would trip it on the next read unless yours replaces it or the cache is refreshed first.
- Also in d27d279 (not store reading): short sizes screen for everyone, r100 ended, welcome counts/wording, test 'wlean' (computers),
  readtest.yml (a full read, nothing published) for reader changes: matches your "compare real prices from GitHub first" rule.
- Freeze until Nov 15 noted. The daily hike-verification task (each one makes a new trail page live) is paused today under the
  freeze unless Bastien says it counts as automation.

## Nov 1, evening: your cookie-leak spec, done
- polite.py `robots()` fetches robots.txt with its own cookie-less `requests.get` (our UA only), never through the session: no store's
  geo cookie lands in S.cookies any more.
- scrape.py `shopify_products()` calls `forget_cookies(base)` before every products.json page (and before the retry), so each page goes
  out with only the cookies we ask with.
- GATE_PASS + the 10 you listed (vanrunco, runnersden, cityparkrunners, boutiquedulac, upika, satisfy, rnnr, sea2sky, stampeak,
  tenthousand; fauxmouvement was already in), GATE_PASS_UNTIL still Nov 2.
- Checked before pushing (sandbox, Canadian cookies, after a robots.txt fetch): products.json price = the store's own product .js price
  on runnersden 185, cityparkrunners 259.95, tenthousand 324 (CAD served, meta USD), janji 171 (CAD), vanrunco 65, rnnr 133 (USD, no
  conversion for Canada = meta), satisfy (EUR, meta). No localization cookie left in the jar.
- Not run: readtest.yml (it's a full store read; the one refresh below is the read). After it I re-check those stores on the live JSON.
- PUSHED 8ecccf5 (check.py ALL GOOD, 114 site checks). ONE store-reading refresh dispatched: run 41337789937
  (https://github.com/Upnorth89/Running-Discount/actions/runs/41337789937), started 18:40 UTC, ~50 min. Wipe the Nov 1 history after it;
  I re-check the 13 stores' live prices against their own pages when it lands.

## Nov 1, night: Altra + Hoka/Salomon test
- Altra: your -28% hold was the gate being wrong, not the rule. Altra sells in CAD for Canada: on its own .js, Paradigm 8 = CA$160
  (compare 200) with CA cookies vs US$136 (compare 170) with US cookies; Torin 9 GTX 210 vs 180, Experience Flow 3 GTX 200 vs 165.
  The live 223.36 = 160 x 1.396 = the OLD read taking CAD as USD. So no rule change; altra added to GATE_PASS (until Nov 2), pushed
  71add2b; the 23:17 UTC afternoon read replaces it. Please re-check Altra after it.
- Hoka/Salomon slow test: tools/brand_test.py + .github/workflows/brand-test.yml (workflow_dispatch only, nothing published, page every
  15-20 s, one site at a time, first 403/406/429/challenge stops that site, cap 450 pages / 160 min per site). I start it at 05:00 UTC
  Nov 2 as you asked and write the run id here; results in the run summary + artifact "brand-test".
  Note: Hoka answers my sandbox "Access Denied" (406), so its part reads robots.txt sitemaps + each product page's JSON-LD and reports
  what it finds; if the pages carry no JSON-LD the report says so and the reader needs a second pass.

## Nov 2, 03:10 UTC: read test after the time limit (run 41375277019, no hiking alongside)
- 57 min in all. The Shopify lane alone filled the 50-min budget: 41 stores at the END of the list were skipped (runnersden, skirack,
  sfrunco, territory, pathprojects, feetures, balega, darntough, swiftwick, stance, wigwam, goodr, roka, sunski, ombraz, tifosi,
  tailwind, skratch, nuun, gu, huma, xero, newton, orangemud, flipbelt, spibelt, fitletic, runderwear, lmnt, muir, karhuus, thorlo,
  farmtofeet, rollga, styrkr, veloforte, headsweats + fit2run cut at page 39). Only 2 slow-downs (fit2run 503 Retry-After 165,
  runinrabbit 503 Retry-After 74), 1 connection error (sail), no hangs. So the cause is volume, not one bad shop: one sequential
  Shopify lane at the polite pace (1 s per request per site + the answer) is now ~50 min for ~140 shops.
- Danger: the same stores are always last, so they'd be skipped every run and leave the site after KEEP_HOURS (48 h).
- Tonight's fix (one change): the Shopify lane starts with the stores whose last good read is OLDEST, so anything skipped is read
  first next run. Nothing about how a shop is read changes. Pushed before the 11:17 read after check.py.
- Next (your step 2, after the morning numbers): two Shopify lanes / machines. Step 3: big shops (pacers 7,863, athleticannex 6,819,
  prrunwalk 5,955, gazelle 4,629, aerobicsfirst, playmakers, confluence, runninglab) to night reads.
- Slowest non-Shopify (in their own lanes, not the cause): footlocker 753 s, sportchek 709 s, distance 608 s, lasthunt 363 s, gords 353 s.

## Nov 2, 05:00 UTC: Hoka + Salomon slow test (brand-test.yml run 41391550546): both said no
- Hoka: HTTP 403 on its first page (/en/ca/), 0 products. The Nov 1 recheck's 200 didn't last.
- Salomon: 116 product pages listed, 33 read in 10 min (one every 15-20 s, robots obeyed: 2 refused), then HTTP 403 on
  /en-ca/product/aero-blaze-4-grvl-gtx-pas-normal-studios... Stopped there. Same as Oct 16. JSON-LD has no per-size stock.
- STORES.md rows updated; store_recheck.py keeps knocking on the 1st and 15th. Unlock = affiliate feed or asking the brand.

## Nov 2 morning read (run 41435572599, 11:17 UTC): clean
- "Scrape stores" step 49 min (11:17:28 -> 12:06:41), under the 50-min budget; every store's last-read stamp is this morning
  (stance, goodr, darntough... the 41 skipped by the night test were read first), so 0 stores skipped. No price-gate holds in health.json.
- Altra Paradigm 8 = CA$160 (correct CAD). runnersden / rnnr / satisfy read this morning.
- Backcountry HIKING (his Oct 29-30 save): live deals-hike-us.json now has 1,913 Backcountry items, 1,412 on sale:
  tops 929, packs 310, bottoms 270, shoes 254, gear 86, socks 35, headwear 29 (USA side, CAD prices converted as usual).
- 49 min is close to the 50-min budget: step 2 (split the Shopify lane across two machines) is next, then big shops to the night read.

## Nov 2, ~14:30 UTC: your step 2 (two readers) built; read test next
- This morning's 11:17 read skipped 0 stores (all 132 Shopify stores read this morning; none near the 48 h drop-off).
- Split: refresh.yml job "shopb" (its own GitHub machine) reads every other Shopify store by name (66) at the same pace; the build
  reads the other 66 + every other reader, then takes shopb's results from the run's artifact before the merge (one merge, as before).
  Per shop: still read once, same gap, robots + crawl-delay, oldest-read-first in each half. If shopb fails or is late, its stores keep
  their last read (KEEP_HOURS) and the build stops waiting. Push runs unchanged (no store reads).
- Proof before going live: readtest.yml now runs the same two jobs. I'll post total minutes, stores skipped and 429/503 count here.

## Nov 2, 15:03 UTC: two-machine read test (readtest run 41462569998): step 2 done
- Main machine: 32 min for the whole read (was 57 on one machine at 03:10). Second machine (shopb): 66 Shopify stores in 16.3 min,
  received by the main one. 0 stores skipped by the time limit.
- Slow-downs: 3 (sea2sky 503 Retry-After 95, fitfirst 503/115, frontrunners 503/78) vs 2 at 03:10; all waited out, all read.
- Failures (not the split): fitnesssports (its server, 500 on page 3), sportsexperts (night copy over 36 h: separate, night job).
- Most time now: thelasthunt 22.5 min (its own lane), altitude 10.8, distancerunwear 10.6, fitfirst 8.0, sportinglife 6.4,
  sportchek 6.3 (904 s incl. answers), gords 5.2, footlocker 5.0. Target < 30 min = step 3 (Last Hunt / slow lanes to the night read,
  or reuse more unchanged pages), one change at a time.
- Live: pushed 4f513df before the test; the 15:42 dispatched refresh (Bastien's save) is the first real two-machine read.

## Nov 2: every Grab deals save feeds BOTH sides (your rule; Bastien "All outdoor gear")
- Running (scrape.py): MEC / REI / Backcountry / SVP readers no longer drop hiking/camping lists (outdoor_list routing removed);
  each keeps what its own running sorting accepts (MEC still only its Running categories; REI/Backcountry/SVP by our groups).
- Hiking (hike.py `saved_hike`): reads EVERY save of mec, rei, backcountry, svp through classify() (camping -> camp files); newest
  save first, one offer per product; REI + Backcountry = USA side, MEC + SVP = Canada side.
- Test on the saves in the repo (age limit lifted for the test only): REI 2,126 running (925 on sale) + 981 hiking (441 on sale);
  Backcountry (run-train-on-sale list) 1,145 running + 716 hiking (all on sale: tops 383, bottoms 279...); MEC (running lists only)
  1,041 running + 17 hiking; SVP no save in the last 40 days. Hiking sortcheck: 1 hit (a Backcountry "Convertible Snap-Up Shirt" as
  pants) -> fixed (convertible + shirt/top/jacket = top); now clean. Live numbers after the next store read.

## Nov 2, 17:10 UTC: Impact tag live
- `<meta name="impact-site-verification" value="c0f43ba6-…">` is on the live homepage (checked with curl). Bastien can click "Add Website" in Impact now.
- Pushed 14540cc: every Grab deals save (MEC, REI, Backcountry, SVP) feeds BOTH sides. Running side reads hiking lists too; hiking reads every save through classify(). Local test: REI 981 hiking (441 on sale), Backcountry 716, MEC 17 (its saves so far are running lists). Live per-store numbers after the next store read.
- Nov 2, 17:40 UTC: Bastien clicked "Add Website" in Impact. Waiting on Impact's review. Keep the meta tag on the homepage.
- Nov 2, 18:45 UTC: Impact verified (growth). Second tag 5c71281d was already pushed (40d2bf4): both stay, first one permanent.
  Queue status: two-machine read test DONE (readtest 41462569998: 32 min, 0 skipped; first real refresh 41474154208 worked, shopb 15 min).
  Save routing DONE (14540cc, live). Next: Grab bookmark background-tab fix (#16).
- Nov 2, ~19:55 UTC: race article fix pushed (0107f81 + follow-up). La Chute du Diable FR = "Matériel obligatoire de La Chute du Diable"
  (title/h1/FAQ/JSON-LD), FAQ question uses the race's own article everywhere (was hard-coded "du {short}" / "the {short}" / "the {name}").
  Also fixed: The Dark 24 ("the The Dark 24"). Grep of every built race page (races/courses/us/races) for de la La / la La / du Le / le Le /
  the The / the La / du La: clean. Live after this push run deploys (~15 min).
- Nov 3, ~00:50 UTC: Sports Experts OFF + robots scan (your 3 asks), pushed:
  1. SPORTSEXPERTS_ON = False (scrape.py), runfree.yml sportsexperts job `if: false`, health.py OFF_STORES (one "turned off on purpose" line,
     no daily problem), store_recheck.py STORES has Sports Experts (robots_says() tested on a Cloudflare-style file: "no (ClaudeBot...)").
  2. STORES.md row 348 + hiking notes updated as you wrote.
  3. robots.txt scan of all 211 store sites (running + hiking, one request each): ClaudeBot block on 3 = Sports Experts, Garage Grown Gear
     (hiking, last good read Oct 27, still on the hiking side), Kelty (hiking, never on the site). Snow Peak + Sporting Life refused robots.txt (403, as before).
  Why SE was still up: KEEP_HOURS counted from when the refresh LOADED the night copy (Nov 2 03:12), not when the copy was made (Oct 31);
  copies up to 36 h are accepted, so ~3.5 days. Now DATA_AT / deals.json "data_at" for every night-copy store (SE, Running Free, Fleet Feet,
  brands, The Feed, Decathlon). The hiking reader had NO KEEP_HOURS at all: added (a store unread for 48 h leaves; today only GGG).
- Grab bookmark (#16) pushed 23:06 UTC: Web Worker pauses (normal timer if a page blocks it; tested both), tab-name progress, Backcountry
  "Sale only" (sale now + sale last time), skip window 4 days instead of 7 (NOT the 8-day save window: older saves showed sold-out sizes Oct 30).
- Afternoon read Nov 2 (run 41544203111): read step 29.7 min (main), shopb 13.5 min, 1 failed store (sportsexperts), 0 skipped for time.
- Nov 3, 00:40 UTC: Grab saves on BOTH sides, live counts (deals = all / sale = on sale; afternoon read + remerge 00:20 UTC):
  | store | running (deals / sale) | hiking (deals / sale) |
  | MEC (CA) | 1,057 / 229 | 516 / 131 |
  | REI (US) | 6,671 / 4,999 | 5,053 / 3,619 |
  | Backcountry (US) | 3,007 / 2,364 | 2,349 / 1,837 |
  | SVP (CA) | 745 / 694 (live Shopify read) | 0 (hiking only comes from saves; no SVP save in the last 5 days) |
  Items can show on both sides (a trail runner or rain shell is both). MEC hiking was 17 before the change (its saves are running lists:
  the hiking side now gets every outdoor item those lists hold); a MEC hiking-list save would add more.
- Nov 3, ~07:30 UTC: your 7-item walk batch PUSHED (dc25626 + follow-up), check.py ALL GOOD (2nd round: round 1 caught my search change
  clearing a Filters category too; now only a CIRCLE's category is cleared by a new search, Filters keeps searches inside it as before).
  1. circles = view only (viewProfile vs toProfile); profile groups always all; weekly_email.match ignores p.groups (every category for
     everyone, so no affected-profile list needed: anyone narrowed gets the full email from this Friday). Site test: circle tap not saved + reload.
  2. count line + h1 step aside while search/category/type/store view is on; "1 deal"/« 1 aubaine » everywhere (8 labels compared a
     formatted string to 1).
  3. FR_WORD/FR_PHRASE in index.html + search_check.py (bas/chaussettes=sock only, souliers/chaussures=shoe, manteau|veste de pluie=rainjacket,
     lampe frontale=headlamp, tuque, gants=glove only ("gant" sat in "elegant"), cuissard/collant). Site test "Search: French gear words".
  4. tidy_gear: CAP_NOT_HAT headwear->gear (69 bottle/flask caps), SOCK_NOT_RUN (MLB/NFL/NBA/NHL/ski/snow: 211 out), arm warmers in
     gloves/hats -> tops, knee/leg warm(er) -> socks, Hanes/Fruit of the Loom/Jockey/Calvin Klein out. Running underwear (Ciele, SAXX,
     Runderwear) stays but never leads Top deals. Gift page: straps (not watches), cleaning, tablets, retainers out. sortcheck: 3 new rules.
     Takes effect at the next store read.
  5. "twice a day" / « deux fois par jour » in every visitor string; BF/BD intros = real Canadian store count; BF live = Canadian stores
     only; bf_data date = Vancouver; shoe pages: About/Quick answers sizes = table rows, "cheapest in the most sizes" = the table's own
     winner, size range reads "M 5", price line days = days of history (31, as the badge); About "more than 150".
     NOT changed: "Prices from X and 165 more stores" = 170 - 5 named (consistent); "at 45 stores" = Canadian stores selling running shoes.
  6. ?lang= wins for the visit; FR "?" attached (9 strings); « Sacs et vestes d'hydratation », « Magasiner au : ».
  7. "1 pick"; new "sunhat" kind (hats/caps/visors, no Buff/gaiter) for "Sun hat"/"Hat" lines (Buffs stay on "Hat or Buff");
     saved sizes tidied to the menu's form + menu filled before the trail boot filter reads it.
- Nov 3: WORDING FIXES LIVE. Your items 2, 3, 5, 6, 7 shipped in dc25626 (07:30 UTC); the guard + last slips in this push (head e51a385, check.py ALL GOOD).
  Guard: check.py step "Wording: plurals, check frequency, store counts" reads all 2,581 built pages as a visitor would: no "1 deals/picks/
  sizes/stores" (EN/FR), no "every morning"/"chaque matin" (except "every morning and afternoon"), no typed-in store counts ("60+"), no
  "de la La"/"the The", no space before "?" in French. Site test "Core things" also checks the homepage for "1 deals". Its first runs found
  85 then 40 slips, all fixed: shoe pages "1 sizes on sale" + list cards "1 stores" (every builder now runs shoe_pages.tidy_words over its
  pages), 14 "Email me when the The North Face…", 9 French "?" in the builders, Fox Pro text "every morning", JSON-LD "150+ stores".
  Core list: "Wrong price or size?" = the ⋯ button on every card (site test checks its label); decisions.md rows for that + the Nov 16 trio.
  Live in ~15 min (push run). Please verify on the live site and tell Bastien.
- Nov 3 morning read (run 41626242889, 11:17 UTC) vs Nov 2 afternoon (41544203111):
  | | main read ("Scrape stores") | shopb (2nd machine) | failed | skipped for time |
  | Nov 2 23:17 afternoon | 29.7 min | 13.5 min | 1 (sportsexperts) | 0 |
  | Nov 3 11:17 morning | 49.0 min | 33.5 min | 0 | 0 |
  The morning is heavier (both shopb and main ~20 min more): mornings re-read Altitude/Last Hunt/Sporting Life pages whose copies passed
  REUSE_HOURS overnight, plus the night copies. 49 min is close to the 50-min READ_LIMIT, so step 3 (move the slow lanes to the night
  read / more page reuse) moves up: I'll do it next (read test first). 28 stores "not read this morning" = the 27 RunFree shops (off since
  Nov 1) + Sports Experts (off since Nov 2): expected.
  Morning sortcheck still showed 13 + 11 bottle caps under Hats: a cap a store files as gear was moved to Hats later in tidy_gear by the
  old GEAR_CAP rule. Fixed (GEAR_CAP skips CAP_NOT_HAT + a last pass at the end of tidy_clothes). Takes effect at the afternoon read.

## Nov 3, ~13:20 UTC (backend)
- Pushed (check.py ALL GOOD): bottle/flask caps never under Hats (GEAR_CAP + last pass), AeroPress out (coffee), Kombi socks out of
  running socks (ski brand). Takes effect at the next store read (afternoon run 23:17 UTC); a push run only rebuilds from the cached read.
- CLAUDE.md Affiliate plan: Sovrn = denied Oct 29 (not pending), "not before January"; paid-link day checklist (bf_live line ~34,
  About/privacy/Terms, disclosure near deal links) written there.

## Nov 3, evening (backend)
- Pushed (check.py ALL GOOD): race + trail lists: each line's cheapest pick is always among the 3 shown (built page + the script's redraw),
  so "From $X" matches what's visible; the From line is grey (was moss green); "♡ Watch" keeps its space (non-breaking, also after a tap).
  Site test 'kit' B now fails if a From price is lower than the first 3 or Watch loses its space. Design items wait for Nov 16.
- Running Free: back (night read Nov 3 10:18 UTC, 2,976 products; 2,060 offers live). No hiding needed.
