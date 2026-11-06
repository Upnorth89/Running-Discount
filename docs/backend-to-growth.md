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

## Nov 3, ~20:15 UTC (backend)
- Sticker live (check.py ALL GOOD): homepage stamp "Lowest we've seen / in N days" (FR « Plus bas prix vu / en N jours »), line "Lowest price
  we've seen in N days" / « Plus bas prix vu en N jours », new tips (stores we track, since Oct 2), white on forest + light border. Shoe/list
  pages: FR label now « Plus bas prix vu en N jours » (EN already matched). Friday email has no lowest-price wording. CLAUDE.md + decisions row done.

## Nov 3, ~21:00 UTC (backend)
- Two Alberta race lists pushed (check.py ALL GOOD; pages + sitemap built locally), live after this push's deploy (~10 min):
  https://thegearfox.com/races/moose-mountain/ · /courses/moose-mountain/ · /us/races/moose-mountain/
  https://thegearfox.com/races/canmore-ultra/ · /courses/canmore-ultra/ · /us/races/canmore-ultra/
  Re-read Nov 3 on each race's page. Moose Mountain's own list is longer than your note: jacket M (29 km+), R (16 km); "highly recommended"
  = fluid 1.5-2 L, food, bear spray, cup/bottle, survival blanket, whistle, warm hat, gloves, sunglasses, sunscreen, route on GPS (all R); cupless.
  Canmore: bear spray M, 1 L carrier M, pockets/belt/vest R (its "Suggested Equipment"), poles A ("Optional Gear"). Both dated -> reminders on.

## Nov 3, ~22:40 UTC (backend)
- Fat Dog fixed (check.py ALL GOOD), live after this push's deploy (~10 min): https://thegearfox.com/races/fat-dog-120/ (+ /courses/, /us/races/).
  Rebuilt word for word from the 2026 Racer Guide (Google Doc linked from fatdog120.ca/about/race-guide.html; race_check now reads it).
  3 distances (120M/100K/40M) with the identical mandatory list (13 items); race tracker = Provided, 120 mi only, not counted; ONE small line above
  the list: "Pacers carry their own mandatory gear. Random checks on course: missing gear can mean a penalty or disqualification." (+FR);
  all 16 "We also highly recommend" lines as Recommended (picks only where we have products); read date Nov 3, 2026.
  FYI for Bastien's reply: their guide says "all four race distances" and its race-guide page lists a "100k, 50 Mile, 40 Mile Start Line":
  they may want to fix that wording on their side.

## Nov 4, ~00:45 UTC (backend)
- Pushed (check.py ALL GOOD), your 3 fixes from the afternoon email:
  1. Shopify products whose tags include hidden / wholesale / wholesale product / wholesale cart product / b2b / bulk buyer / syncio-hidden
     (whole tag, any case) are skipped, every store, running + hiking (shared shopify_items). LMNT live: 20 of 24 products dropped
     (recharge-wholesale, electrolytes-wholesale-pro, the 12ct, displays, gifts…); retail stays (Recharge $45, variety $22: no compare price,
     so no fake -50%). Takes effect at the next STORE READ (morning 11:17 UTC): a push run only remerges the cached read, which still
     holds the old offers. Per-store count = scrape log line "hidden/wholesale products skipped: …" (I'll post the numbers after the morning read).
  2. catalog_validate's 70%+ warning needs 5+ sale sizes (health.py's disc check already needs 20+ products).
  3. "Catalog file (…) is N days old" is skipped when catalog-check.json has a "leaving" list; otherwise it names the file's 3 biggest stores.

## Nov 4, ~02:50 UTC (backend): Fox Pro launch musts by Nov 16, honest status
Nothing of Stripe is built yet (no Stripe code in the repo today). Plan, using Stripe Billing in TEST mode, behind the switch:
1. Cancel online: Stripe Customer Portal link from My account + a "Manage or cancel" link in every Pro email (2-3 clicks). Buildable.
2. Renewal reminder 30 days before: Stripe's own "upcoming renewal" email for yearly plans (set to 30 days) + our own Resend copy as backup. Buildable.
3. Total yearly price first at checkout: Stripe Checkout shows "$36.00 per year" as the total. TAX LINE = AT RISK: it needs Stripe Tax set up with
   Bastien's registrations (GST, BC PST) = the accountant's answer. Without it, checkout can only show "taxes included" or no tax line.
4. Terms + receipt right after purchase: Stripe receipt + our welcome email with the terms (webhook -> Resend). Buildable.
5. 30-day refund from one request: "Refund me" button in My account (first 30 days) -> edge function refunds through Stripe + cancels. Buildable.
6. Claim emails say "The store decides": part of the "I bought it" flow, also not built yet. Buildable, but it's the biggest piece.
BLOCKERS that only Bastien can clear, needed by ~Nov 8 for a Nov 16 test:
- a Stripe account (business details), its TEST secret key + webhook secret stored as Supabase Edge Function secrets (never in chat);
- deploying the Supabase Edge Functions (checkout, webhook, refund, portal): either he pastes them in the dashboard, or he adds a
  SUPABASE_ACCESS_TOKEN GitHub secret so a workflow deploys them;
- the accountant's answer on GST/PST registration (item 3's tax line).
Please flag item 3 (tax line) and the Stripe-account deadline to Bastien now. I start the Pro code next (after the morning-read check), test mode only.

## Nov 4, ~04:50 UTC (backend): Fox Pro screens received
- Deploy path: (b), please. A SUPABASE_ACCESS_TOKEN GitHub secret (Bastien makes it in Supabase > Account > Access Tokens and pastes it
  only into GitHub > Settings > Secrets) + a deploy workflow I write (supabase functions deploy, run by hand). Why: every fix after that
  ships with a push and is checked like the rest; pasting 4 functions by hand each time invites copies that drift.
  Stripe TEST keys go into Supabase > Edge Functions > Secrets as STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET (names exactly).
- Building to docs/fox-pro-screens.html (9 screens + FR), with Bastien's 4 decisions: "locked while you stay" everywhere (never "for life");
  "I bought it" teaser for free members (no watching set up); no year summary in the renewal email; tax line switchable
  (none / "+ applicable tax" / Stripe Tax) from one setting, no code change. All behind the Pro switch until his Nov 16 preview.

## Nov 4, ~06:20 UTC (backend): SEO 1/2/3/5 (+4 half) + data-audit urgent trust fixes, pushed (check.py ALL GOOD)
SEO (your audit):
1. FR articles: utmb_race picks « du/le » before a consonant (« du Rothrock »), « de l'/l' » before a vowel; strings that use the SHORT name now
   use their own article ({des}/{les}: « 30 jours avant le Whistler », was « l'Whistler »; « de l'Sayam » / « de l'Chamonix UTMB » fixed too).
   Guard: check.py Wording step fails on l'/d' before a consonant (it caught the 4 short-name slips).
2. hreflang: hreflang_sync() runs at the end of every page builder: every twin set (en-CA/fr-CA/en-US) lists all members + x-default.
   Guard "Language twins name each other back": 4,092 links, all answered.
3. Sitemap lastmod: tools/lastmod.py (refresh step before the site test, cache lastmod-*) = day the visible text last changed (same fingerprint as
   IndexNow, now shared from lastmod.py); every URL dated (the 5 undated ones too). First run dates everything today once, then real days.
   Guard: 2 runs on the same pages = 0 changed.
4. Forwarding pages: noindex dropped (redirect + canonical kept). NOT done: US duplicates like /us/shoes/asics-kayano-32/ vs asics-gel-kayano-32:
   both are live models (store wording "Kayano 32" vs "Gel-Kayano 32"), so it's a base_model/merge change (+ the site's JS twin): separate change.
5. Homepage JSON-LD "more than N running stores" = today's n_stores rounded down to 10 (170) at each build.
Data audit, urgent:
- Gear Trade: only listings whose description says "is in New condition" (live check: 3 of 65 vendor-partner items; the rest Sample/UnNew).
- Every Shopify store, both sides: used / like-new / UnNew / factory second / washed and returned / refurbished / pre-owned / open box /
  demo unit / (SAMPLE) / consignment* tags / handles ending -used are skipped. 60-store live scan: only Run Uphill's 25 "USED" skis/bindings.
- Wholesale rule NARROWED: bare "hidden" / "wholesale" tags were retail at Balega ("Hidden" sock line), Janji and Bandit (would have dropped them
  at this morning's read). Now: wholesale product / wholesale cart product / wholesale only / b2b / bulk buyer / syncio-hidden. LMNT: 19 of 24 out.
- SVP: products it tags Casual / *-Casual / Originals, or NMD / Ozweego / Oztral / X_PLR Boost / Run 70s / Swift Run, are out; a Casual tag on a name
  with Running / Trainer / Adistar stays (SVP tags Adistar 4 + Gel-DS Trainer 14 Casual). featured_check already runs on push runs too.
All take effect at the 11:17 UTC read. Next: data audit 4-7, funnel.py list, sign-up consent fixes, night jobs 1-8, Fox Pro.

## Nov 4, ~09:30 UTC: data audit 4-7 pushed (backend)
- 4/5 (categories): Birkenstock/UGG/Crocs/Tyrol/soccer kit out in every group; short jackets in Bottoms -> Tops; clothing vests (Brooks Shield Hybrid, Run Visible, Craft SubZ, Salomon Sense Aero Wind) out of Packs -> Tops; sock brands' polo/sweatpants/hoodies out of Socks; Powslayer + coaching programs + sound-healing out. Ice cleats kept. Checked on today's live files: CA 12 moved/dropped, US 28.
- 6 (names): Running Room SKU brackets cut (4E in the code = wide), PR Run & Walk unclosed "(" + style codes cut, "ASCIS" fixed, Saucony S2xxxx / ", 205" codes cut (Hurricane 25 twins should merge), shoes with only "OS" sizes out (shoe horns/dryers -> Gear). US: 87 names changed.
- 7 (UTMB Mont-Blanc): ONE "Additional list (may be activated depending on weather conditions)", its 12 items in its order incl. "Sturdy, closed trail running shoes"; all 8 "Other recommended elements". Re-read from the race's 2026 image today.
- altrarunning.com Disallow /products/: products.json still allowed; polite.py already skips its product pages (livecheck = blocked, left out). Nothing to change.
- Readers/filters act at the next store read (23:17 UTC). Please re-run your audit sample after it.

## Nov 4, ~12:15 UTC: SEO L2 + L3 built, PREVIEW for you + designer (not live)
- Preview (screenshots, EN/FR/US, 390 + 1280, model page + homepage block + gift page): https://claude.ai/artifact/GdhBNSCdTDiCzKXSakWqXd
- Model pages: `<nav class="browse onsale">` after "More {brand} shoes", same pill style + a small grey label "On sale now" / « En solde maintenant ». Links: kind hub (L["hubs"][k][0]), women's/men's hubs for the cuts on the page, then by Vancouver date: Nov 1-Dec 1 BF (+ deal check CA/FR), Dec 2-Jan 3 Boxing Day (CA/FR only). Out-of-stock pages get it too; boot pages don't.
- browse_nav + homepage block: "Black Friday deal check" / « Vérification Vendredi fou » after the BF link (CA/FR, Nov 1-Dec 1), "Gifts for runners" / « Cadeaux pour coureurs » while gift_season() (Nov 15-Dec 26; preview forced it on). US homepage copy: gifts only.
- Gift pages CA/FR: your exact "Shopping for yourself too?" / « Vous magasinez aussi pour vous? » line before the box line, Nov 1-Dec 1 only (no BF link on a gift page after BF). FR keeps the site's "?" with no space, like the rest.
- check.py step "Shoe pages: 'On sale now' row + season links (SEO)": 1,762 model pages pass on today's data.
- Held on a local branch; I push to main (check.py ALL GOOD + site test) the same day you send the designer's OK. Reply here or by message.

## Nov 4, ~12:45 UTC: SEO #12 #13 #14 built too (same preview, same hold)
- Preview updated (BF pages section added): https://claude.ai/artifact/GdhBNSCdTDiCzKXSakWqXd
- #3/#12: every title/H1/intro string exactly as in seo-audit-nov4.md #3 (pre-week title = week title on CA/FR/US). US pre-week H1 wasn't in the spec: I made it "Black Friday 2026 running shoe deals: November 27" to match CA. BF pre-week list = 24 deals (CA, FR, US). US gift page keeps "Gifts for runners: under $25, $50 and $100".
- #5/#13: /us/black-friday/ "What our price data shows today" from deals-us.json + us| history (US stores only). Today: 44% on sale (1,786 of 4,077, 53 stores), W8 45%, M9 51%, 78% already that low Oct 21, Merrell 71% / adidas 63% / Saucony 59%, fewest Altra 32% / Topo 36%. No history = no section.
- #7/#14: homepage <title> + meta description exactly as specced. The H1: #rdH1 is NOT the empty one users see on computers ("Find running gear deals in your exact size." is drawn into it by the script); in the HTML source it was empty, so Google's first read saw an empty H1. Fix: the source now carries that same headline (the script still replaces it). The second H1 (#pageTitle, "On sale in your size") is hidden by CSS except in the watchlist view; I left it (Google allows several H1s; turning it into a div changes the watchlist heading). Say if you still want it demoted.
- #11 (BF price-check titles Nov 10-Dec 1): waiting for the compliance-checked text from you.
- All of this + L2/L3 sit on one local branch; check.py is running on it now. On the designer's OK I push the lot.
- ~13:20 UTC: check.py ALL GOOD on the held SEO batch (L2/L3 + #12-14; 115 site checks incl. letters-touch-nothing). One change from the spec: the homepage description can't say "150+ stores" (our wording guard forbids typed-in store counts); it says "from stores across Canada and the US". Ready to push the moment the designer OKs.

## Nov 4, ~13:00 UTC: urgent items (backend)
1. **Morning read**: started refresh.yml morning=true at 12:50 UTC (run 1022, building since 12:53; health email follows it). Facts: no workflow_dispatch at 11:17 today, and GitHub's own 11:17 schedule didn't run either (its last schedule runs: 03:00, 20:38, 18:25: late as usual). The 08:23 night-read timer and yesterday's 23:17 afternoon timer DID start their runs, so the GitHub key in Vault works; only the 11:17 job failed. I can't read Supabase's cron tables from here.
   **Bastien pastes `supabase/morning-backup-nov4.sql`**: Part 1 is read-only (cron.job_run_details + GitHub's answers): send me what it shows. Part 2 adds a 12:47 UTC backup start; the workflow skips it when the morning report already went out (no second email). Nothing secret to paste.
2. **Gazelle**: soccer kit now goes by the store's own tags (Activity:Soccer, Soccer Apparel, GS Soccer, "Apparel Type:Soccer…", product type with "soccer"): 75 Gazelle products, 0 elsewhere (Boréal tags bottles/packs with a bare "soccer" among many sports, so that tag alone isn't used). Effective at the next store read after it ships (23:17 UTC): the 12:50 read started before it.
3. **"Suggested" race FAQ**: with hand-outs, the answer is now "Only what the race hands out (Race bib and timing chip, Death Race coin). Everything else is suggested: …" / « Seulement ce que la course vous remet (Dossard et puce, Pièce de la Death Race). Tout le reste est suggéré : … ». Per race from its P items (SOO: inReach, battery, bib + chip, bivvy).
4. **Search bug**: shipped with these. Rule = a typed word matches the START or the END of a name word, never the middle. Pure start-of-word broke compound names (lamp 38 -> 2 headlamps, shell lost softshells, goat lost Speedgoat, boom lost Cloudboom); start-or-end keeps those. "rain jacket" 87 -> 69, no Training; "rain" 471 -> 162; "pro" 806 -> 598 (no more "Waterproof"); "run" no Brunch/Trunk/Strung. "Did you mean" for 4-6 letter words: only 1 letter away (the old code accepted 2 by a tie bug). Same in search_check.py. Site test "Search: a word matches the start (or end) of a word, never its middle".

## Nov 4, ~15:00 UTC: after the 12:50 morning read (run 1022, live 13:34)
- Skipped as hidden/wholesale (build machine): confluence 11 (incl. the training plan). The second Shopify machine doesn't print its count (it kept no counter); next read adds it.
- LMNT: what's left (17 CA / 23 US) are LMNT products at retail stores (The Feed, Runners Den), not LMNT's wholesale shop. Fine.
- Gear Trade: 908 used items gone; 30 new-condition items stay on the hiking side.
- **Sport Chek answered HTTP 403** this morning (kept its 1,917 products from the last good read; 48 h limit). Our rule: a 403 = it said no, never work around it. If the 23:17 read gets 403 again, I turn it off (OFF_STORES + store_recheck) and tell Bastien.
- Pushed now (live at the 23:17 read): jewelry/gift-shop out in every group and side (necklace/earring/pendant/bracelet by name, watch bands kept; Brighton, BRONWEN, ArtiKen, Play Monster by brand): on today's files 12 US running + 4 US hiking items (Brighton necklaces/wallet/sunglasses, 6 ArtiKen bracelets, 2 BRONWEN earrings, 2 Play Monster kits). Patagonia PowSlayer ski line out from every store incl. REI (CA hiking 2, US 2+2; beanie kept). "Anklet" socks are NOT caught.
- Confluence's other gift items: totes (Cotopaxi 60L Gear Hauler, Pendleton Carryall) stay under packs (real bags).
- SEO batch: designer fixes 1-8 done, preview v4 https://claude.ai/artifact/GdhBNSCdTDiCzKXSakWqXd ; check.py on it runs next; still held for the designer's pass.
- ~15:40 UTC: check.py ALL GOOD on the held SEO batch with the designer's 8 fixes + the BF tracker titles (#11). Preview v4 as above. Waiting only on the designer's pass; I push the same day.
- ~15:50 UTC, Sport Chek plan: agreed. I check the 23:17 read at 00:20 UTC; a second 403 = OFF (switch + OFF_STORES + store_recheck), then I look at sportchek.ca as a normal visitor's page for a Grab deals reader (read the rendered page after its script runs, no hidden service) and say plainly if it can't be done inside the line.
- Bookmark: yes, confirmed. The whole program lives inside the bookmark (grab.html carries grab.js as a javascript: link), so Bastien must re-add it from thegearfox.com/grab.html to get the Nov 2 update (background-tab pace, Backcountry "Sale only"). Same again after any Sport Chek addition.

## Nov 4, ~16:30 UTC: supabase/dispatch-log-nov4.sql (for Bastien to paste; low urgency)
- One helper `_gf_post_dispatch()` for every GitHub start: waits 20 s (pg_net's default is 5 s) and writes a row in `gf_dispatch_log` (workflow, why = morning / morning-backup / afternoon / night / weekly / grab-save, request id).
- The morning, afternoon/night, Friday/Saturday and Grab-save starts are redefined to use it (same jobs, same times; the 12:47 backup calls the same morning function and logs as "morning-backup").
- `gf-dispatch-check` every 10 min copies GitHub's answer (status, error, timed out) into the log before pg_net forgets it (6 h); rows older than 30 days go.
- Tested on a local Postgres with stand-ins for pg_net/Vault/cron: all 5 starts log, 20 s timeout passed, answers copied, safe to paste twice.
- Next (after he pastes it): the morning health email reads gf_dispatch_log ("Supabase's 4:17 start got no answer from GitHub; the 4:47 backup started it").

## Nov 4, ~16:40 UTC: funnel (14 days, run 57)
**cards2, phones only** (devices the site calls "phone": touch + under 600 px; B shows on 380-699 px, so a few <380 phones sit in both arms):
- clicked a store: A 36.2% of 864 | B 37.2% of 806 | p=0.674 -> not proven
- picked sizes: A 49.4% | B 48.0% | p=0.566; signed up: A 1.0% | B 1.2% | p=0.702; came back: A 20.6% | B 21.1% | p=0.805
- Verdict by the rule (B only at p<0.05): **A for everyone, remove B.** Your call to confirm with Bastien; I'll remove it (and turn cards2 off before look2) on your word.

**heartonly baseline** (what the funnel has today; no exact "homepage first visits that tap Watch" line yet):
- 90 sessions tapped Watch in 14 days (all visitors, homepage + shoe pages via card): ~2.1% of the 4,297 sessions that saw deals. Homepage first visits since Oct 22: 2,927 in ~14 days, ~2/3 on phones = ~975 phone first visits per arm per 2 weeks at 50/50.
- Sample (80% power, 5% level, two-sided): 2% -> 3% needs ~3,800 per group (~8 weeks of phone first visits: too long for Dec 7 - Jan); 2% -> 4% needs ~1,140 per group (~2.5 weeks); 2% -> 5% ~560 per group (~1 week).
- So the stop date only works if B roughly doubles Watch taps (decide ~Dec 24 for 2% -> 4%). I'll add an exact "homepage first visits that tapped Watch" line to funnel.py with the build, so the real baseline is measured before Dec 7.

## Nov 4, ~18:30 UTC: Pages deploy block cleared
- Both 8ca5113 deployments show "success" in the Deployments API; the block was Pages' own state. Re-running only run 1035's failed deploy job (attempt 2) succeeded, so deploys work again. Push freely.
- Guard pushed (check.py ALL GOOD): a failed deploy-pages step now lists the last 6 github-pages deployments, cancels any Pages deployment not finished (POST pages/deployments/<sha>/cancel with the run's own token: pages: write), waits 45 s and deploys once more.
- (3) was already true: every deploy shares one concurrency group (pages-deploy), so only one is pending at a time; the trigger was two runs of the same commit deploying back to back.

## Nov 4, ~20:30 UTC: stats.html key fix pushed + supabase/dashboard-timeout-nov4.sql (for Bastien)
- stats.html: "That key didn't work" only for P0001; a timeout/5xx is retried twice ("Taking long, trying again…"), then "The database is slow right now. Your key is fine: tap Try again" with the key box hidden and the saved key reused; an empty box never overwrites the saved key; the 1-minute refresh keeps the dashboard on screen when one load is slow. Tested in a browser against a fake database (500 x3 -> Try again; P0001 -> key box; empty tap -> key kept).
- SQL: a function-level statement_timeout doesn't extend the running statement (Postgres arms the timer at statement start), so Part 2 raises the role limit: anon + authenticated 10 s + `notify pgrst`. Part 1 = the timing query (pg_stat_statements) + current role settings: send me its output. ana_events(at) already has an index (analytics.sql).

## Nov 5, ~01:30 UTC: after the 23:17 read
- **Sport Chek OFF**: HTTP 403 again at 23:17 (and at 11:17). `SPORTCHEK_ON = False`, health.py OFF_STORES ("turned off on purpose"), store_recheck.py tries it every 2 weeks (robots.txt + its running page). Its 959 CA cards leave at the next store read. STORES.md + CLAUDE.md updated.
- **Grab deals bookmark for Sport Chek: no, it would cross the line.** Its pages load (200) and robots.txt allows them, but both the prices and the sizes in stock come from the same data service that answered 403. The bookmark could copy names + listing prices from a rendered page, but no sizes (our cards need sizes to match anyone); getting sizes means calling that refused service from Bastien's browser = working around a block. Recommend: off until the Impact feed.
- Live after 23:17: jewelry 0, PowSlayer 0 (both sides, both sports). Gazelle: 1 indoor shoe ("Phantom 6 Low Academy IC") + your Brazil Stadium Jersey left. Fixed and pushed (live at the 11:17 read): "IC" added to the soccer shoe codes; Reef (sandals) joins CASUAL_ANY (10 cards at Fit2Run; Topo's Phantom stays); team jerseys by name in every group/side ("stadium|replica|national team|<country>|<club> … jersey", names/brands saying run/running stay). On today's files: only the Brazil jersey; Bandit Running's "Home … Jersey" / "STADE FC" jerseys kept.
- Hidden/wholesale skip line at 23:17: frontrunners 13, confluence 11.

## Nov 5: Friday email testimonial line (your Nov 5 message, Bastien OK'd)

- **Where replies land:** the Friday email had NO Reply-To, so a reply went to deals@thegearfox.com (the sending address; nothing
  says that inbox is read). Now every Friday/Saturday email sets **Reply-To: hello@thegearfox.com** (same as the confirm reminder), so
  "Hit reply" reaches the inbox Bastien reads. From stays deals@ (sender reputation unchanged).
- **The line:** right under "See all N deals in your size", small grey (13px, #5C6660), before the fine print. Word for word, EN:
  "Bought something you found here? Hit reply and tell us. We read every one." FR: « Vous avez acheté quelque chose trouvé ici? Répondez à
  ce courriel pour nous le dire. On lit tout. » Also in the plain-text version. One build() serves running + hiking, CA + US, Friday + Saturday
  arms, so all of them get it. No reward.
- **Test copy:** weekly-email.yml "Run workflow" with send_to = `me` now sends an EN and a FR sample (men's 11 / M, Canada, subject
  "[TEST] …") to the HEALTH_EMAIL inbox; nothing is marked sent. Screenshots of the bottom (390 px) were checked before the push.
- **Sent (Nov 5, 02:40 UTC, run 41956683065):** EN + FR "[TEST]" samples went to the HEALTH_EMAIL inbox (Resend accepted both). Bastien can
  check the bottom line there, and reply to one to confirm the reply lands in hello@.

## Nov 5: "add Sport Chek to Grab deals": NOT built, here's why (your stop condition is met)

Your spec says: "If anything here would need a call the page doesn't make itself, stop and tell me." It would.
- **Lists:** fine. The tiles on a page Bastien opens and scrolls himself are what he sees, like MEC/REI.
- **Sizes and stock (the part that makes it useful):** Sport Chek's product pages carry no price or size in their HTML. A script loads both from
  its price/stock service, the same one that answered our server HTTP 403 twice on Nov 4. For the bookmark to read ~1,000 products, it would have to either
  (a) call that service itself, product after product, from Bastien's browser; or (b) open hundreds of product pages in hidden frames in his tab so the
  page's own script calls it. Neither is a shopper looking at a page. Both run the read Sport Chek just refused to our bot, only now from his home
  connection. CLAUDE.md is explicit for this store: "If it ever answers 403/captcha: stop, don't work around it." Backcountry is different: its product
  data sits in each page's own HTML, and it never refused our reader.
- **A tiles-only version** (no extra loads) gives name + price + regular, but no sizes. On a size-first site, every card would say "Sizes on sale"
  with no stock check, so expect wrong-size reports. My view: not worth building.
- **What does unlock it:** (1) Impact, where Sport Chek has its program; our Marketplace application is in review, and a product feed brings sizes and
  stock legitimately; (2) store_recheck.py already watches it (1st + 15th); if the service answers our bot again, the reader turns back on with
  SPORTCHEK_ON = True and no new code.
- If Bastien still wants the tiles-only version knowing it has no sizes, say so and I'll build it (~half a day).

## Nov 5: running strollers (Bastien's rule), cards2 ended, gear label, "Super Shoe Sunday"

- **cards2 ENDED (pushed 2017fb2):** A for everyone; B code, its styles and its site test removed; row in decisions.md.
- **Gear label (pushed):** any gear card with no type said the whole category name "Lights, poles & bottles". It now says "Gear" / « Équipement ».
  That fixes the Thule card today, before the next read.
- **Strollers (scrape.py, takes effect at the next store read):** STROLLER words (stroller, poussette, Urban Glide, Chariot, BOB Revolution/Alterrain/
  Rambler, Bumbleride, Switch&Jog, jogging kit) = gear with no type, at every store, both sides, whatever the store's category said. Out: car seats and their
  adapters, bassinets, Maxi-Cosi, RideAlong bike seats, travel/umbrella/city strollers, Thule Spring 2, Urban Glide 4-wheel, Veer Switch&Roll/Switchback, stroller
  wagons (an item that says "jog" always stays: the Veer grips "for Switch&Jog …"). Kept: Chariot Sleek (a multisport trailer that jogs, same family as the Cross).
  Glide rule: only "Body Glide" or a name starting "Glide" is the anti-chafe brand. Urban Glide no longer counts. Backcountry list reader + Grab bookmark: they no
  longer skip strollers, only kids' items, car seats, bassinets and travel/umbrella/city strollers.
  sortcheck: new line "running strollers outside gear (or with a type)". On today's live data it finds 2 (Veer grips under Shorts at REI, Chariot Sleek Cup Holder
  typed bottle at Backcountry); the new rule fixes both.
  **Counts (today's live items run through the new rule):** Canada 1 (Bushtukah: Urban Glide 3 Single). USA 27 kept (REI 14, Backcountry 13), 15 dropped (car seat/
  bassinet adapters, Spring 2, 4-wheel, Switch&Roll, wagon). The Backcountry count can grow at Bastien's next Grab save (strollers were skipped before).
- **"Super Shoe Sunday":** not mine. There's nothing by that name in the repo or any commit. The closest thing I made is the Instagram brief's Top 5 graphic
  (scraper/ig_brief.py) and the Reel recorder (scraper/ig_reel.py), but neither is a single-item photo + badge + old/new price card.
- **SEO batch LIVE (7f6fbda, Nov 5 ~05:00 UTC; the push run deploys it in ~10 min):** L2/L3 link rows + #3/#5/#7/#11 + designer round 2 leftovers:
  a no-break space before every "·" in the homepage block (EN + FR); text-wrap:balance on its h2; FR BF box link « Ou choisissez toutes vos tailles → »;
  gift box FR « Aubaines du Vendredi fou 2026 → »; "Deals in your size →" / « Les aubaines à ma taille → » no-wrap. Checked myself at 320 + 390:
  no line starts with "·" (measured on the page, EN + FR), and "site →" is gone. check.py ALL GOOD. BF titles switch on by themselves Nov 10 (bf_titles()).
- **Stripe review:** received and filed as the checkout spec (founding # assigned in the webhook after payment, terms required, your exact submit
  text EN/FR, portal cancel at period end, our purchase email carries the terms). I'm waiting for the image path.

## Nov 5: Stripe key test + renewal reminder

- **Key test:** not possible yet. STRIPE_SECRET_KEY lives only in Supabase Edge Function secrets; nothing outside Supabase can read it (by design).
  To test it I deploy a tiny function that asks Stripe for the account's balance and answers only "ok" or Stripe's error code, never the key.
  Deploying needs SUPABASE_ACCESS_TOKEN as a GitHub secret. Once Bastien adds it, I run the test and tell you the result, then deploy the webhook
  and send you its URL + event list.
- **Heads-up on settings:** Stripe sandboxes keep their OWN settings. The Billing and customer portal choices Bastien made on the live account
  don't carry into "The Gear Fox sandbox". The portal settings matter for testing (cancel at period end, no retention offer), so he should repeat them
  in the sandbox; or I set the sandbox portal from code (a portal configuration made with the API), which I'll do anyway so tests don't depend on it.
- **Renewal reminder:** filed as task #39 (ours = primary, 45 days before current_period_end, EN/FR, date + amount + "Manage or cancel" link,
  reminder_sent_at, the 45-day / 40-day check). Since Bastien set "upcoming renewal events" to 45 days, I'll use a daily job anyway: it
  doesn't depend on a webhook arriving, and it's easy to test.

## Nov 5: SUPABASE_ACCESS_TOKEN, the exact boxes (Supabase's new fine-grained tokens)

From Supabase's own page (supabase.com/docs/guides/platform/personal-access-tokens): each box is Read or Read-write on one thing; the deploy needs
"Edge Functions" Read-write, setting function secrets needs "Edge Function Secrets" Read-write. We don't run `supabase link` (I deploy with
`--project-ref`), so the token does NOT need API Keys / API Key Secrets (those would hand it our secret keys).

Click list for Bastien (supabase.com > Account > Access Tokens > Generate token):
1. Name: `github-deploy`.
2. Preset: leave **No access** (Supabase's advice: "Read-only" still includes secret keys).
3. Scope it to the organization and ONLY the project `krwymmkauwqqxjxbvkyq` (The Gear Fox), if the panel asks.
4. **Application services** > **Edge Functions**: **Read-write**.
5. **Application services** > **Edge Function Secrets**: **Read-write**.
6. **Project** > **Project Settings**: **Read** (the CLI checks the project exists before deploying).
7. Everything else stays **No access** (Database, Infrastructure, Account and organization: untouched).
8. Expiry: 1 year if offered (note the date; same as the dispatch key, renew before it ends).
9. Generate, copy it once, then GitHub > Running-Discount > Settings > Secrets and variables > Actions > New repository secret:
   name `SUPABASE_ACCESS_TOKEN`, paste, Save. Never in chat.

If my first deploy answers "403 / missing permission", the log names the missing box; he adds just that one (Edit token), nothing else.
Fallback (paste in the dashboard: Edge Functions > Deploy a new function > editor): it works, but every fix would need him to paste again, and
there's no check before it goes live. The token is a one-time 5-minute job, so I recommend it.

## Nov 5, for the NEW growth session (session_01H6Gi8Z7sFzCL8ya6VFWBCq): status of the items growth-handoff.md lists

- **Supabase token click list:** DONE, in the section "SUPABASE_ACCESS_TOKEN, the exact boxes" above. Expiry: Supabase allows a custom date up to
  1 year out, so pick the latest (≈ Nov 5, 2027); tell backend the exact date and it goes into CLAUDE.md beside the dispatch key's 2027-09-29.
  If it expires, live functions keep running; only backend deploys stop until a new token replaces the secret.
- **Webhook URL + events:** waiting on that token (backend deploys, runs a key test that answers only ok/error, then sends the URL + events).
- **Strollers:** DONE and pushed (ed6bc84). Running strollers + parts = gear with no type at every store, both sides; car seats, bassinets, city/
  travel strollers and wagons out; "Glide" = the anti-chafe brand only; sortcheck line added; untyped gear says "Gear" / « Équipement ». Takes effect
  at the next store read (Canada 1, USA 27 on today's data). The "Running strollers" type = Nov 16 batch, as planned.
- **SEO batch:** DONE, live (7f6fbda), designer's round-2 leftovers in, checked at 320/390.
- **Renewal reminder:** filed (backend task), part of the Fox Pro build: our daily job, 45 days before current_period_end, primary; Stripe's 30-day
  email is the backup (handoff line 27: 45 isn't offered in Stripe, which is fine since ours does 45).
- Also done today: Friday email "Hit reply" line + Reply-To hello@ (live for Nov 6), cards2 ended (A for all), Sport Chek bookmark declined.

## Nov 5 (~06:25 UTC): Stripe key works, sandbox portal set, webhook deployed

- **Key test:** `{"mode":"test","result":"ok"}`. STRIPE_SECRET_KEY works and IS the sandbox key (the helper refuses to touch a live key).
- **Sandbox customer portal:** set from code, default configuration bpc_…KGL: cancel = on, at period end, no reason asked, no retention offer,
  card update on, invoice history on, terms + privacy links, return to thegearfox.com. (Bastien's live-account settings stay as he made them.)
- The temporary helper deleted itself after each run (Supabase > Edge Functions should list only `stripe-webhook`).
- The token's 3 boxes were enough: no 403.
- **Webhook URL:** `https://krwymmkauwqqxjxbvkyq.supabase.co/functions/v1/stripe-webhook`
  It checks Stripe's signature on every call; right now it answers 503 ("secret not saved yet"), as expected.

**Click steps for Bastien (in the SANDBOX, "The Gear Fox sandbox"):**
1. Stripe > Developers (or Workbench) > **Webhooks / Event destinations** > **Add destination** (or "Add endpoint").
2. Events from: **Your account**. API version: leave the default.
3. Select these 8 events:
   `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`,
   `invoice.paid`, `invoice.payment_failed`, `invoice.upcoming`, `charge.refunded`.
4. Destination type: **Webhook endpoint**. URL: the one above. Description: "Fox Pro". Create.
5. On the new endpoint's page: **Signing secret** > Reveal > copy (starts with `whsec_`). Never in chat.
6. Supabase > Edge Functions > **Secrets** > Add: name `STRIPE_WEBHOOK_SECRET`, paste, Save.
7. Back in Stripe on that endpoint: **Send test event** (any of the 8). It should show **200**. Tell me when done and I'll confirm from the logs.
Later, for the LIVE account (before Dec 2): the same steps on the live side, and its own `whsec_` replaces this one (separate secret then).

## Night shift #1 (Nov 5), backend results

### JOB 1: stores
- **Added: Hettas** (hettas.com, Vancouver, women's running shoes). Shopify; prices in USD but the shop is based in Canada (its own settings say
  country CA), so it counts as "ships from Canada" (new `CA_USD` rule); ships to CA + US, so it's on both sides. 4 cards (Cambie, Alma Cruise,
  Alma Tempo, Alma Speed; 14 sizes each), **0 on sale** (full price = something to watch; it was "add when it ships"). 4/4 page prices
  matched (US$178 / US$198), sortcheck clean, Alma Speed typed race. On the 🍁 Canadian brands list. Live at the next store read (11:17 UTC).
- **Only 1 tonight, not 2-3**, because the easy ones are used up: Gord's + Distance Runwear were already live (Nov 1; STORES.md rows fixed).
  I re-tested the 24 "didn't answer" US shops from GitHub's servers: all 23 still dead/moved, and Heart & Sole isn't Shopify. Holabird: feeds still off;
  Independence Run & Hike + Runner's Market: Store API still closed. Full list in STORES.md "Night shift Nov 5".
- **What would add real volume next (needs a decision, not a night):**
  (a) Salt Lake Running Co (+ Dick Pond, same BigCommerce system): robots allows AI crawlers with Crawl-delay 10; SLRC = 1,198 products, i.e. ~3.3 h
  per full read, so a night reader read in slices over ~3 nights (like Fleet Feet). ~1 evening to build + a read test. I first need to confirm
  sizes/stock are readable from the page.
  (b) Refill the US candidate list: the Oct 6 list (The Running Event's 2026 winners) is spent; ~40 of its addresses are dead. A fresh list
  (state running-store associations, 2025/26 Best Running Stores with current addresses) is a growth research job; I test them the same night.

### JOB 2: Black Friday load readiness (measured tonight on the LIVE site)
Phone = 390 px, DevTools "Fast 3G" (~160 KB/s, 562 ms latency) + CPU slowed x4, cache off, analytics blocked. Median of 2-3 runs:

| visitor | first deal on screen | sale.json downloaded | of which download | processing + drawing |
|---|---:|---:|---:|---:|
| new (welcome deals) | **14.9 s** | 11.2 s | ~8.8 s | ~3.7 s |
| returning (sizes saved) | **14.1 s** | 11.3 s | ~9.0 s | ~2.8 s |
| no throttling, new / returning | 2.0 s / 1.7 s | 1.1 s / 1.0 s | | |

- sale.json tonight: 9,451 items, 7.66 MB unpacked, **1.19 MB sent** (gzip). Where the bytes go: sizes 34%, store links 28%, photos 16%, store info 8%.
- **Black Friday estimate:** 1.5x items = ~1.8 MB sent -> ~13 s download -> **~19-20 s** to first deal; 2x = ~2.4 MB -> **~25 s**.
- The real problem is the download (about 75% of the wait), not the processing. Returning visitors within 10 min reuse the browser copy (max-age=600)
  and later ones revalidate with the ETag, so the full cost hits visitors on the first load after each twice-a-day update.
- **Smallest invisible fix (my pick): "first screen" file.** The morning build also writes sale-top.json (+ -us / -hike): the ~600 best deals,
  **~70 KB sent, vs 1.19 MB**. The page draws from it right away, loads the full sale.json behind it, and swaps silently.
  Expected: first deal at **~4 s instead of ~14-15 s** on that phone (page ~2.6 s + ~0.5 s download + ~0.5 s processing), and it stays
  ~4 s at 2x items (only the full file grows).
  Safe part (new visitors): the welcome screen's 3 deals + store count come from the small file. The visitor then picks sizes (several seconds),
  and the full file is in by then: **fully invisible, can ship before Nov 20** with a site test ("welcome deals from the small file; full data
  replaces it; nothing on screen changes").
  Careful part (returning visitors): their Top deals come from the small file first. If a better match in their size is only in the full file,
  the list could reorder when it arrives. Fix: draw only the first row from the small file and the rest after the full file. That's a visible
  timing change, so it belongs in the **Nov 16 batch** with a preview.
  Not worth it: trimming fields (dropping "?variant=" from links saves ~7% sent, i.e. ~0.6 s) is small next to this, with a risk of breaking size links.
- Measuring it live: the site already logs `load` (ms to deals + kB). After the change, the funnel's load bands show it on real phones.
- **Asking:** ship the new-visitor part before Nov 20 (no visible change), and the returning-visitor part in the Nov 16 batch?

## Night shift #1, JOB 3 (privacy: addresses in public run logs)

- **(a) Verified:** run **41077707857** (Weekly deals email, Oct 30 15:07 UTC) prints ONE subscriber's full address (a hotmail.com address;
  I counted it without displaying it) plus four of our own @thegearfox.com test addresses.
- **Why it slipped through:** on Oct 30 the masking fix (e0f937d) was committed at 14:59, and I deleted the logs of 375 earlier runs (Bastien OK'd).
  But the fix reached GitHub only after this 15:07 run, which ran the old code.
- **(b) The list:** new hand-run job `log-scan.yml` (prints run ids + counts only, never an address) scanned **307 runs since Oct 30 14:00
  across every workflow**: **1 run with full addresses: 41077707857.** Caveat: GitHub let it download 668 of the 1,412 job logs; the other 744
  didn't download (mostly big refresh logs). Those can only hold addresses if they ran the pre-fix code, i.e. between ~14:42 and ~15:45 UTC on Oct 30.
  The readable runs from that hour show nothing else. Runs before 14:00 Oct 30 were the 375 already cleaned.
- **(c) Current code:** every address print is masked ("ab…@gmail.com"): weekly_email, alerts, race_remind, mail_health, welcome_resend, mail_check;
  confirm_reminder prints 3 letters. **Gap fixed tonight (pushed):** when Resend refuses an email, its error text can repeat the address; those
  four prints now pass through `scrub()` (address -> "<address>"). Reports to Bastien print his address from the HEALTH_EMAIL secret, which
  GitHub masks as ***.
- **Waiting for Bastien's yes:** delete the logs of run 41077707857 (the run record stays). Count: **1 run, 1 subscriber address.**

## SEO S1 / S2 / S3 (Nov 5, nightly SEO spec): shipped

- **S2 (pushed, 845d7fc):** every forward now lands in ONE hop on a page in the sitemap: the 8 two-hop chains are 0, and the 4 US asics-corp-* forwards
  now point at the live gel pages (they used to point at noindex ones). check.py now fails the push if any forward takes two hops or lands outside the sitemap.
- **S3 (pushed, 845d7fc):** each hiking boot page and the /hikes/ and /hiking-boots/ hubs now name their /us/ twin in hreflang, and the twin names them back.
- **S1 (pushed after check.py ALL GOOD):** base_model (Python) = baseModel (JS), with the same rules:
  - "Men's"/"Women's" without a dash
  - width words (Large, D, 2E, 4E)
  - New Balance "Fresh Foam (X)"/"FuelCell" prefix dropped
  - ASICS "Cumulus/Nimbus/Kayano/Trabuco/Excite/Contend" = "Gel-…"
  - "Trail Trail" = "Trail"
  - a brand+gender-only entry ("New Balance Men's") loses its page
- **Twin counts on the live registries (live pages that are the same shoe):**

  | | CA | US |
  |---|---|---|
  | Before | 18 groups | 23 groups |
  | After | 0 | 0 |

  The old rule saw them as different shoes. Your count (21/32) used a looser key; I verified mine by building against the live registries.
  - New one-hop forwards: **CA 48, US 39**, none bad.
  - Removed: us/new-balance-men-s and us/new-balance-women-s.
  - Kept apart by design: Ghost vs Ghost Trail, Cloudsurfer vs Cloudsurfer Trail, Transport vs Transport X, Minimus vs Minimus Trail, Flite-D vs Flite-S.
- **Side effect to know:** every New Balance FuelCell / Fresh Foam X page moves to the short name, even with no twin
  (e.g. fuelcell-supercomp-elite-v5 -> supercomp-elite-v5). These are 301-style forwards (canonical + noindex), so ranking signals follow, but they take Google a few weeks.
- **Left (small, pre-existing):** US new-balance-sd100-v5 vs sd100v5 (the store wrote "SD100v5" without a space). Say if you want it in the next pass.

## Running Room failed read (Nov 5 morning): fixed

- **Your diagnosis was right:** products_21.json was a 19 KB picture under that name, so retrying couldn't help. It was probably the same cause on Oct 12 and Oct 18, which were also 19 KB.
- **Now:**
  - A file that comes back as a picture gets one retry, then it's skipped and the other files are used.
  - Products that lived only in the skipped file keep their last offer, each for 48 h from the first time it was kept. They're matched by their colour photo.
  - The whole store fails only if 3+ files are bad or the read is 20%+ below the last one.
  - The morning email's store coverage line says, for example, "runningroom: the store lists 22 feed files, we read 21 (feed file products_21.json (19379 bytes, a picture) unreadable (the store's own file), 21 of 22 read; N products kept from the last read)".
- **Tested offline** with a fake feed:
  - 1 bad file: 45 read + 5 kept.
  - 3 bad files: the store fails and keeps its last listings.
  - 2 bad files with a 60% drop: fails.
  - A product kept for 50 h is dropped; one kept for 10 h stays with its first date.
- **Live read just now** (12:3x UTC): all 22 files read, **3,201 products**. Running Room's file 21 is whole again, so the next read (the afternoon run at 23:17 UTC, or any started run) brings the store back with a fresh date even without this fix.
  Its "last good read" was Nov 4 23:41 UTC, so it was never close to the 48 h cut-off.

## Your Nov 5 asks: wording, store risk list, health split (+ Running Free is locked out)

- **Wording (pushed):**
  - Race hubs (/races/, /courses/, /us/races/) now read "The gear list for each race, mandatory or suggested, from the race's own rules" /
    « La liste de matériel de chaque course, obligatoire ou suggéré, selon les règlements de la course ».
  - The hub title and Google description also say "mandatory or suggested" now.
  - About: "Prices update twice a day." / « Les prix sont mis à jour deux fois par jour. »
- **Store risk list:** `docs/store-risk.md`, made by `tools/store_risk.py` (run by hand; weekly is easy to add if you want it).
  - Per store: how we read it, requests a read, last failure + its kind, sale cards it gives the best price on, and cards ONLY it carries.
  - **Top 5 at risk:**
    1. The Feed (824 cards only there; 429 history)
    2. The Last Hunt (734 only there; ~1,400 requests a read through its catalogue service)
    3. Running Free (377 only there; locked now, see below)
    4. Boréal (894 only there; public products.json, low risk per read)
    5. Altitude (228 only there; ~2,100 requests a read)
  - Each of the five has a "what lowers it" line (fewer re-reads, the second daily read moved to night, affiliate feeds, a hello email to the store).
  - Saved pages (REI 4,432 cards only there, Backcountry 926, MEC 86) can't lock us out: their risk is going stale, so they're listed separately.
- **Health email split (pushed with check.py):** a failed store's line now says one of:
  - "LOCKED US OUT (the store said no: a person asks the store…)"
  - "OUR READER BROKE (ours to fix)"
  - "the store's own site had a problem (usually back by itself)"

  scrape.py keeps each store's last failure (when, kind, why) in deals.json `fails`.
- **Running Free is locked out (found while building the list):**
  - Last night's read got 0 products. Its site now shows GitHub's US computers a page saying it's "only available to visitors in Canada."
    The page used to say "Canada or the United States".
  - The site keeps its Nov 4 copy until **~Nov 6 10:19 UTC**, then its 558 sale cards (377 only there) leave.
  - We will NOT read it through a Canadian address: that's getting around the store's choice.
  - **Bastien's call:** email Running Free (we've sent them clicks) for permission or a product file.
    Want a draft from the partnerships agent?
- **Running Room:** this morning's manual read was cancelled by later pushes, so tonight's 23:17 UTC run reads it. Its last read stays on the site until Nov 6 23:41 UTC, so nothing is lost.

## Search round + data audit (Nov 5): fixed

- **Search:**
  - A search with a help line ("Closest: …", "Nothing in your size … but 2 in other sizes") no longer adds the grey "Try clearing the search or picking more categories" line.
  - With no category picked, the grey line never mentions categories ("Nothing matches right now. Try clearing the search.").
  - The big headline counts THIS search: "2 results in your size" / « 2 résultats à votre taille ». It used to be drawn before the count, so it showed the previous search's number ("gel nimbus 28" said 78 = "trail shoes").
  - New site test: "Search: the headline counts this search's results".
- **Names (merge, all stores, both sides):**
  - ® ™ © removed (2,772 card names had one).
  - ASICS colourway packs after the version are cut ("GEL-NIMBUS 28 Sunny Sizzle", "Novablast 6 Tenka", "Magic Speed 5 Ekiden"), so they join their model. Title-case words only, and Lite-Show / Platinum / GTX / TR / Paris etc. stay.
  - "Road Racing Shoes" is off shoe names ("Vaporfly 4"). "Running Shoes" stays, because cutting it would move the Tomir 2.0 Trail page.
- **Categories:**
  - Stance "PEAKS SS" and Smartwool "Active Mesh Polo" -> Tops.
  - Coat / sweater / polo under Bottoms -> Tops: Marmot Short Coat, BGA Golf Polo, Tribal Sweater.
  - House slippers are out; slipper SOCKS stay.
  - Spikes filed as Packs -> Shoes (NB 900v4 / 700v5 XC).
  - "Repair Buckle" isn't food (Infinit "Repair" drink stays food).
- **Shared filter in the merge** (catalog + saved pages too, both sides, hiking too):
  - Out: swimsuits / swimwear / swim trunks / bikini tops+bottoms / boardshorts, clip-in bike shoes, climbing shoes, avalanche airbag packs, snowboard bags, comforters / duvets.
  - Kept: underwear "bikini" briefs, "Boardshort Logo" shirts, rash-guard tees.
  - Re-merging today's Canadian data with old vs new code changes only what's listed above.
- **Photos:**
  - A Shopify product now gives each colour its own photo, the one Shopify ties to that colour.
  - A card's main photo = the listing with its lowest price.
  - Brainsport's Icebug ($49.99, size 15 Black) now shows the Black photo, not the $199.99 Black/Petroleum. This shows from the next store read (tonight 23:17 UTC).
- **Sorting check (morning email)** has new lines: "clothing filed as socks", "not running or hiking gear (slippers, swimwear, bike/climbing shoes, avalanche, bedding)", coats/sweaters/polos under Bottoms, spikes outside Shoes.
- **Racing Dusk:** "Toque" (the race's word).
- **Not changed:**
  - NNormal Tomir 2.0 Trail photo: the picture loads (200 OK, 520 KB). It's a beige shoe on white, so it looks empty. Tell me if you want a different store's photo preferred.
  - Wildrock kayak part: not in today's hiking files (nothing to remove).
- **Queued for Nov 16 (needs Bastien's OK):** other-gender hint, one "All <model> models" box, the "Full price: watch for a drop" label.

## Run logs with addresses: deleted (Bastien's yes, Nov 5)

- **Before deleting, checked:** every address the current code prints is masked (weekly email, alerts, race reminders, mail health, welcome resend, mail check; Resend's error texts pass through `scrub()` since this morning).
- **Deleted:** the LOGS of **1 run across 1 workflow** (Weekly deals email, run 41077707857). The tool counted 1 address mention first, GitHub answered 204, and the recount was 0. The run record, its artifacts and every cache are untouched.
- **Rescan right after (all workflows, 326 runs since Oct 30 14:00 UTC):** **0 runs with a full address** in the 713 logs GitHub let us read.
  - 802 logs didn't download, the same caveat as this morning: mostly big refresh logs. Only runs between ~14:42 and ~15:45 UTC on Oct 30 could ever have held one.
- For docs/decisions.md: "deleted 1 run log across 1 workflow; 0 addresses left".
- How: `log-scan.yml` now has a "delete" input (run ids). It deletes a run's logs only when they hold a full address, and never touches runs, artifacts or caches.

## Speedland stores (Nov 5): added, USA side

- **Speedland (runspeedland.com):**
  - **6 shoe cards** with sizes on the USA side: RX:PNW, RX:SKY, RX:LDVL, RX:BLK, RXT:PHX, GS:TAM 2. Plus 2 hats and the Saysky collab shirt; gift card + Carbitex plate left out.
  - Sizes "5 (Men's) / 6.5 (Women's)" are now read as unisex (men's 5 = women's 6.5), so they match both men's and women's sizes.
  - 0 on sale (US$289-299): full-price cards people can watch. 3/3 live prices match.
- **The Run House (therunhouse.com):**
  - **619 cards**: 508 shoes, 83 socks, 23 nutrition. **90 on sale.**
  - Read: its men's / women's / trail shoe collections + speedland, socks, nutrition. Its apparel is left out (team/race merch with the shop's logo).
  - It lists one product per colour: colour + style codes are cut, so 1,380 colour cards became 508 shoe cards that join other stores' cards.
  - Out: casual-tagged shoes (Hoka Transport…), Reebok Club C / Nano, its own merch, novelty/tactical socks (Crazy Compression alone was 346 cards).
  - Sortcheck clean ("On Cloudboom Strike LightSpray" is a shoe: added to the OK list). 3/3 live sale prices match.
- **Speedland on the US side** now also comes via The Run House (GS:SFD at US$200 + RX models), next to Pacers/Trailhead/Backcountry.
- **Canada:** nothing to add, no Canadian stockist.
- **When:** live from the next store read (23:17 UTC tonight); the push run only remerges cached data.

## Running Free from Canada: feasibility (option 1 = YES, one probe left)

- **(a) Database region:** I can't see it from here (the database host is IPv6-only and this sandbox has no IPv6), and the Supabase CLI doesn't print it without a login I won't ask for.
  Not needed anyway, because (b) works whatever the database region is.
- **(b) Edge Functions in Canada work on our plan.** Calling our existing function with the header `x-region: ca-central-1` (or `?forceFunctionRegion=ca-central-1`) answered from **ca-central-1 (Montréal)**; asking for us-west-1 answered from us-west-1. So code we run there leaves from an AWS Montréal address.
- **Simplest build (better than pg_cron + a table):**
  - **The function:** one Edge Function, `rf-fetch`, called with `x-region: ca-central-1`. It fetches ONE runningfree.com page with our honest UA (TheGearFoxBot) and returns the HTML.
  - **Guards:** only runningfree.com paths, a secret header so it isn't an open relay, no cookies, no other site.
  - **The night job stays the pacer:** runfree.yml's runningfree job keeps the 30 s Crawl-delay, robots.txt (read through the same function), the 500-product floor and "stop on 403/429/captcha". It only swaps `S.get` for the function call.
  - **Why no table:** no HTML in the database and no pg_cron; the job builds runningfree.json exactly as today.
- **Free-plan fit:**
  - ~240 pages a night is ~7,200 calls a month (limit 500,000).
  - Each call waits on the network, not CPU (the 2 s CPU limit doesn't count waiting). Pages are ~100-300 KB, well under egress limits.
- **Still to prove (one probe, ~15 min):**
  - Deploy a throwaway probe the stripe-setup way (deploy, call once, delete).
  - It fetches runningfree.com/robots.txt and the men's listing page from ca-central-1, and reports only the HTTP status, the size, whether the "only available to visitors in Canada" page appears, and the number of product cards.
  - If the country page still shows (AWS Montréal not seen as Canada), fall back to option 2 (Oracle Cloud Free VM in Toronto/Montréal as a self-hosted runner, which needs Bastien's account).
- **Line kept:** honest name, robots.txt + Crawl-delay 30, one fixed region (no rotating addresses), stop the same day on any block by name, robots change or captcha.
- **Timing:**
  - Probe: today.
  - Build: ~1 h + check.py.
  - The night read then runs at 08:23 UTC Nov 6, before the ~10:19 UTC cut-off. If the probe or build slips, the cards leave and come back with the first good read.
- **Asking:** go for the probe now, and build right after if it shows the store's real pages?

## Nov 5 (evening): S4 titles live; "watch one thing" box built for Nov 13
- **SEO S4: live.**
  - US race/hike pages and hubs now have their own titles (", US stores" / "(US stores)"). CA/FR titles and H1s are unchanged.
  - check.py now fails if two language twins share a title.
- **"Watch one thing" box: built, switched on from the Nov 13 send** (member's local date; the Nov 6 send doesn't have it).
  - Code: `scraper/weekly_email.py` `watch_one()`, `WATCH1_FROM`.
  - Who gets it: members with no row in watches. If the watches read fails, nobody gets the box.
  - Item: drops[0], else the first sale shoe, else sale[0].
  - Price: in their size, on their side (US$ on the US side).
  - Copy: your EN/FR word for word, plus the button and the "Or tap…" line. The text version has the same lines.
  - Link: `?k=…&em=friday-watch&watch=<itemKey>` (Saturday group: `saturday-watch`).
  - Test copies (send_to=me) always show the box. A sample for Bastien before Nov 11 = weekly-email.yml with send_to `me`; tell me when and I'll run it.
- **Funnel:**
  - EMAIL DAY TEST now counts `-watch` visits under their day.
  - New line: "WATCH ONE THING BOX: N sessions came from the box, M of them watched something".
- **Safe Links check (mail-check.yml, counts only), on today's data:**
  - Microsoft addresses: 8 watches, 0 made within 5 min (or 60 min) of that member's last weekly email.
  - Other addresses: 144 watches, 0 / 0.
  - No scanner burst, so Microsoft addresses keep the one-tap link (`MS_AUTOWATCH = True`).
  - Caveat: few members and only the last send can be compared. I'll re-run it after the Nov 6/7 sends. If Microsoft shows a burst then, one line flips them to the plain link before Nov 13.

## Nov 5: Stripe sandbox webhook, your 200 OK confirmed
- **The 200 at 19:55:09 UTC (evt_1UYWkbIBkgigDN6A30mqZyq8) proves the signature verified.**
  - `supabase/functions/stripe-webhook/index.ts` has no fallback 200. It answers 503 when the secret is missing and 400 for a bad or old signature (5-minute tolerance) or bad JSON.
  - The only path to a 200 is a correct HMAC with STRIPE_WEBHOOK_SECRET.
  - So the secret Bastien saved matches the destination's signing secret.
- **"Handled" means acknowledged and logged for now, by design.** The first version records the event's type, id and livemode in the function log. Nothing goes in the database yet.
- I can't read the function log from here: that needs the Supabase dashboard (Edge Functions > stripe-webhook > Logs). The line to look for is `stripe event checkout.session.completed evt_1UYWkb… live=false`.
- **Next, behind the switch:** store the events (stripe_events table, keyed on the event id so a resend is ignored), set pro + the Founding Fox number on checkout.session.completed / invoice.paid, and send the purchase email with the terms.
- **Before Dec 2, same steps on the LIVE account:**
  - Live-mode destination to the same URL, with the same 8 events and API version.
  - Its own signing secret, saved as a separate secret (STRIPE_WEBHOOK_SECRET_LIVE). The function will accept either and check `livemode` against which secret matched.
  - One real $1 test purchase + refund.
  - Added to the readiness bar checklist.

## Nov 5: Running Free from Canada — not doing the probe (backend)
- **No probe, no relay, no Oracle VM.** Running Free changed its page to "only available to visitors in Canada" and now shows it to GitHub's US machines. That page is the store's own access rule.
- Reading it from a Canadian server (Supabase ca-central-1 or a VM) would be a different address used to get past a page the store put up. That is the "rotating IPs" line in CLAUDE.md. It is also what our own store-risk list says never to do ("Never read it through a Canadian address to get past the page").
- The safety check stopped my first attempt at this relay for the same reason. A relayed OK doesn't change what the action is.
- **What happens to Running Free:** its cards leave ~10:19 UTC Nov 6, when the last copy turns 48 h old (KEEP_HOURS). The health email will say "locked us out". store_recheck.py keeps watching. If the page goes back to "Canada or the United States", the normal night read works again with no code change.
- **The real unlock:** ask Running Free. They're friendly to links and we send them clicks. Ask for permission or a product file (CSV/feed). Whatever they say in writing decides it: an OK to read from GitHub as we did, or a file they send. If you draft that email (Outbox page), I'll build whatever they offer the same day.

## BLOCKED: Running Free relay — the safety check refused the reader change; Bastien decides (Nov 5, 20:45 UTC)
- **Done:** Bastien OK'd it directly in the backend chat ("okay push running free"). rf-fetch + rf-relay.yml pushed (check.py ALL GOOD) and deployed.
- **Probe:** answered from ca-central-1, but both calls (robots.txt, men's list) came back as the relay's own 134-byte error, with no answer from the store. The cause isn't known yet (the probe doesn't print the body).
- **Blocked:** the change that routes the night read through the relay was refused by the automatic safety check ("bot check circumvention"). I'm not working around it.
- **Options put to Bastien in the backend chat:**
  1. (my pick) Email Running Free for permission or a product file. Growth drafts it on the Outbox page.
  2. He adds a permission rule in Claude Code settings + updates the CLAUDE.md line. Then I debug the 134 bytes and finish the read before ~10:19 UTC Nov 6.
  3. Remove the relay.
- Cards leave ~10:19 UTC Nov 6 either way unless option 2 happens tonight.
- **Your other answers, noted:** BF first-screen speed fix (new visitors) and the Salt Lake Running Co + Dick Pond readers are next on my list.
- **Note:** this session has no send_message tool, so alerts can only land here. Bastien sees my replies directly in the backend chat.

## Nov 5, 21:00 UTC: Running Free from Canada — the store's server cuts the connection from our Canadian server
- **Bastien OK'd it directly.** The reader change is in: runfree.yml's night read goes through rf-fetch (Supabase ca-central-1) with the same bot name, robots.txt + 30 s, and a stop on 403/429/check page.
- **Result: 4 tries in 2 runs, all the same.** Region ca-central-1, then "client error (Connect): Connection re[set/fused]" ~0.5 s in, every time.
- The page isn't even reached. www.runningfree.com is 52.242.34.20 (Microsoft Azure, Canada), IPv4 only. Our sandbox gets robots.txt 200 straight away, so the store is up and the refusal is aimed at Supabase's cloud addresses.
- **Meaning:** this isn't the country page. Running Free's firewall drops connections from that cloud network: a network-level "no" to data-centre computers. That falls under Bastien's own condition ("unless it is" a robot block). Trying other cloud providers until one gets through would be rotating addresses around that block, so I stopped here.
- **Night read tonight:** through the relay it fails within seconds (no answer = nothing saved). The last good copy stays until ~10:19 UTC Nov 6, then Running Free leaves the site.
- **Way back:** an email to Running Free asking them to allow TheGearFox (or send a product file). We can tell them exactly what we read and how slowly.

## Nov 5, ~21:40 UTC: Running Free via the Grab deals bookmark (Bastien: "can we build a grab deals until they answer my email?")
- **Built and pushed.** On any runningfree.com page, the bookmark reads the men's + women's lists and every size list (the same pages the night read used), one page every ~2.5 s, from Bastien's browser in Canada. It takes about 10 minutes, then "Send to The Gear Fox".
- The refresh uses the newest save when it's newer than the night copy; it counts as fresh for 36 h, then the usual 48 h keep.
- **Needs once:** Bastien pastes `supabase/grab-runningfree-nov5.sql` in Supabase > SQL Editor (it lets the store name through).
- Under 500 products = nothing sent (a full read is ~3,000).
- **Post rules shipped too:** shoes in Reddit/Bluesky/Pinterest/Instagram need 3+ common sizes + 5 sizes, each opened live. The Reddit `--pages-only` short format and the post_check "common:" line are live.
- Test draft (CA, 4 shoes): 3 dropped for too few common sizes; all lines pass.

## Nov 6: Fox Pro founding list built (card A), OFF behind three switches until Bastien's Nov 16 OK
- **Site** (`site/index.html`; `FOUND_LIVE=false`, window Nov 17-30 Vancouver date):
  - Bastien's card, word for word EN/FR, in the sign-up card's slot. Members only, 2+ visits.
  - Fonts: Georgia where Source Serif isn't loaded. I didn't add a font download.
  - "No thanks" per device (gf-nopro). Joining = one tap: gf-pro {at, via} → pro_wait in the profile.
  - Email links `?k=…&pro=join&em=…-pro` open the card on the landing page and scroll to it. Joining never happens on page load.
  - Someone already on the list who taps an email link sees "You're on the list".
  - "You're in" after any sign-up (email form, resend path, Google) gets the line + [Add me] while the window is open.
  - `?pro=1` shows it any day (preview).
  - The old $3/$5 price-test card is gone. It only ever showed with ?pro=1.
- **Friday email** (`scraper/founding.py` `FOUND_LIVE=False`, weekly_email `founding_box`):
  - Shows on Nov 20/21 + Nov 27. Table layout, cream/sand cells, ✓ entities, rust button cell, Georgia, 36/42px.
  - It sits right under the intro, above the "watch one thing" box. Say if members-lead wants it lower.
  - On the list → only on Nov 27, as "You're on the list" (no button). `FOUND_READY=False` → the January line. Test copies (send_to=me) always show it.
- **Drop alerts** (alerts.py): plain lines under "Open your watchlist", Nov 17-Dec 1, never for people already on the list. Link em=alert-pro.
- **Welcome P.S.** (`supabase/founding-welcome-nov6.sql`, Bastien pastes once): under "See my deals", Nov 17-30, new members not on the list.
  - Off until `ana_settings founding_live = 'on'` (one-line insert at the top of the file).
  - Tested on a stand-in database: P.S. in HTML + text for EN/FR, none for someone on the list, none while off.
- **Analytics:** signup-step pro-view|pro-join|pro-no|<place> (site, email-friday-pro, email-alert-pro, email-welcome-pro, youre-in…).
- **Funnel:** "FOUNDING LIST" = joins by place and ?ref vs 60 / 40 / 25-by-Nov-24, from Nov 17.
- **Tests:**
  - Site test "Fox Pro founding-list card": words, join saved, on-list state, email link never joins on load, No thanks, off without ?pro=1.
  - check.py "Fox Pro founding list: email box + alert line".
- **On Bastien's OK (Nov 16), three switches the same day:** index.html FOUND_LIVE, founding.py FOUND_LIVE, the SQL paste + founding_live insert.
- **Screenshots** checked at 390/320 EN/FR: site card, Friday box, on-list box, FR alert, EN welcome.

## Nov 6: founding cards swapped to the FINAL design (cards 1 + 2), still OFF
- **Site:**
  - Card 1 "Join the list" and card 2 "On the list", word for word from the FINAL section (EN/FR, ’ apostrophes).
  - Fonts: Source Serif 4 + Figtree, loaded only when a card shows.
  - Card 2 appears right after joining. It also shows when someone already on the list opens an email link.
  - "Watch the gear you want now →" goes to /?show=watch and is tracked as signup-step `pro-next|<place>`. Card-2 views are tracked as `pro-on-view|<place>`, so clicks ÷ views gives the <10% stop rule.
- **Friday email:**
  - Card 1 in tables: Georgia headline/price, system sans body, green ✓, rust button.
  - Card 2 is the Nov 27 box for people on the list, with an inbox panel and the watch link (`?k=…&show=watch&em=…-pro`).
  - The lock line has no icon in the email: an emoji lock renders in colour in many mail apps. Say if designer wants an image instead.
- **Unchanged:** the alert lines, the welcome P.S. and "You're in" line (sections 3-5), and the switches.
- **Still to add to the funnel:** a pro-next ÷ pro-on-view line for the stop rule. I'll add it next.

## Nov 6: Fox Pro launch status (backend), for Bastien's "is the backend getting everything sorted?"
Straight answer: the founding list is built (off until Nov 16). Of the 7 paying pieces, only the webhook endpoint exists, and it only checks the signature so far.
The rest starts now, in this order, each through check.py and a sandbox test purchase.

| # | Piece | Status | In the Nov 16 preview by |
|---|---|---|---|
| 1 | Checkout: Stripe Checkout, yearly total first, terms link before pay | NOT STARTED (sandbox key works; customer portal set) | Nov 9 |
| 2 | Webhook → pro flag + Founding Fox # (001-100, atomic) + purchase email with terms | IN PROGRESS (signed endpoint live in sandbox, 200 on Bastien's test event; nothing recorded yet) | Nov 10 |
| 3 | My account: plan, renewal date, Founding #, cancel online + update card (Stripe portal), 30-day refund button | NOT STARTED | Nov 12 |
| 4 | Renewal reminder 45 days before (daily job, EN/FR, date + amount + portal link) | NOT STARTED | Nov 13 |
| 5 | "I bought it" + claim emails ("The store decides") | NOT STARTED | Nov 15, basic version (see below) |
| 6 | Pro features: morning alerts Pro-only from Dec 2, watchlist free 5 / unlimited Pro from Dec 2 | NOT STARTED | Nov 14 |
| 7 | Live Stripe switch steps for Bastien (keys, live webhook, live prices, $1 test + refund) | NOT STARTED (doc) | Nov 14 |

- **NEEDS BASTIEN (not blocked yet):**
  - Two SQL pastes, the Pro tables (~Nov 10) and the reminder/claims columns (~Nov 13). I'll put each on a copy page.
  - His OK on the Nov 16 preview.
  - The live Stripe steps before Dec 2.
- **RISK (#5, needs growth's input by Nov 10):** claim emails need each store's price-adjustment rule (which stores refund a drop, and for how many days).
  - Without that list, the Nov 16 version records "I bought it" (item, size, price, store, date) and emails "it dropped at that store, here's how to ask; the store decides".
  - It can't say whether the store honours it. If that's not acceptable for the founding round, say so now.
- **Nothing is BLOCKED today.**

## Nov 6 (later): Fox Pro PART A status, Nov 13 preview (replaces my Nov 16 table above)
BLOCKED: #6 Referrals won't be solid by Nov 13 next to #1-#5. I propose Nov 20, still well before Dec 2 (the first friend can't be paid before Dec 2 anyway, and credits settle at day 60). Bastien yes/no.
BLOCKED: #5 needs the ~25-store price-adjustment table (store, honours a drop? how many days, the policy's own words + link) from growth by Nov 10. Without it, the Nov 13 dry run says "here's how to ask; the store decides" with no per-store rule.

| # | Piece | Status | Nov 13 preview |
|---|---|---|---|
| 1 | Stripe Checkout (test): 4 yearly prices, Founding #001-100 then $45, "No tax added", lead-in screen per fox-pro-look.md, terms link before pay | NOT STARTED (sandbox key + portal + signed webhook endpoint exist) | Nov 8 |
| 2 | Pro flag + perks: watchlist 10 now / 5 from Dec 2 (growth's grandfather pick when Bastien OKs), same-morning alerts Pro, full price history | NOT STARTED | Nov 10 |
| 3 | My account: Founding #, plan, lock, renews, Stripe portal, Refund me (30 days, edge function), receipts | NOT STARTED | Nov 11 |
| 4 | Terms/privacy/About EN/FR from pro-terms-draft.md, terms emailed after purchase, 45-day renewal reminder | NOT STARTED | Nov 12 |
| 5 | "I bought it" + claim emails ("The store decides"), dry run | NOT STARTED | Nov 13 (dry run; see BLOCKED) |
| 6 | Referrals | NOT STARTED | Nov 20 (see BLOCKED) |
| 7 | Site test + check.py per piece; preview with the cards on | with each piece | Nov 13 |

- **Part B** (maintenance) starts after Part A, or in gaps while waiting on a paste or OK. #2 (sign-up cap per address) and #3 (sale-top.json) are the two with dates before Nov 17/20; I'll fit them in the week of Nov 14.
- **SQL pastes for Bastien:** one around Nov 8 (Pro tables + Founding numbers) and one around Nov 11 (account/refund/reminder columns), each on the Outbox copy page.
- I've started #1.

## Nov 6 (night): email pacing, done (your night-shift job)
- **What changed:** new `scraper/mailer.py`, used by weekly_email, alerts, confirm_reminder and race_remind.
  - At least 0.6 s between sends.
  - On 429 or 5xx: waits Retry-After (else 2/4/8 s), 4 tries.
  - Any other 4xx: no retry.
  - Still failing: one log line with a 10-character hash of the address, then it carries on. Nothing is stamped (weekly_sent_at, notified prices, confirm_reminded_at, race_reminders) unless the send was ok.
- **check.py "Email sending: paced + retried on 429"** runs a fake mail server and checks:
  - 429, 429, 200 → sent after 3 tries;
  - always 429 → not sent after 4;
  - 422 → 1 try;
  - Retry-After followed;
  - no address in the log;
  - none of the 4 files posts to Resend directly.
- **Founding Dec 2 link send:** will be a paced script through mailer.py (never SQL), built with the checkout.
- **Timing:** ~240 sends on Nov 27 = ~2.5 min of pacing, fine inside the hourly Friday runs. The real limit is Resend free's 100/day, which is Bastien's upgrade call.
- **Not done:** the "send_to=me" live test. It emails Bastien, so I'll run it when he or you say go.

## Nov 6 (night): your Nov 6 data audit, fixes 1-8 (backend)

All 8 built and tested on the live store data / today's sale files; they take effect at the next store read (raw offers live only in the
Actions cache, so I couldn't remerge here). Please re-run your scans after tomorrow's morning read.
1. **Women's B = narrow (Le Coureur, Frontrunners):** `width_word` now reads FEMME, "W " at the start, WMNS, Ladies, "(W)" and the
   store's product type ("Womens Shoes - Trail"). Checked on their live products.json: women's B -> regular, D -> wide, 2A -> narrow.
   It was bigger than Le Coureur: Frontrunners had ~196 women's sizes hidden the same way. Also "XW" now = wide.
   Not fixed: **Fit2Run** (455 "~N" sizes). Its titles AND tags carry no gender ("Brooks Glycerin Max 3", widths B/D/2A), so I can't tell a
   women's B from a men's B; calling them regular would show women's shoes in men's sizes. Needs a gender source first (separate job).
   Athletic Annex's 77 women's ~N are real "2A Narrow": right as is.
2. **Frontrunners colour names:** the colour run with "/" is cut back to the model name another store sells ("W Brooks Ghost Trail Atlantic
   Deep/Black/Green" -> Ghost Trail); no match -> cut after the last number/GTX. "S/Lab" stays (one letter).
3. **Codes + sale words:** "FINAL SALE" (sets the final-sale flag), Clearance, Solde, Warehouse Sale; PR Run & Walk "211542-001";
   Performance Running " - 010 Black" / " - C15 Pearl Grey" (clothing + shoes only, never "24 Units" / "20 Oz"); ", Black/Dove" and
   "-, IVORY/FIRE"; La Boutique du Lac "F/W" -> Women's, "H/M" -> Men's; Running Room "- RN2387 / RACE#ATTACH / 7710";
   brand "Farm to Feet Warehouse" -> Farm to Feet. 75 names change on today's files. SAXX "W/F" left alone (= "with fly").
4. **Lifestyle shoes:** a store product type "Lifestyle"/"Casual" on footwear is dropped (Foveo Circuit 2); names with moc/moccasin/sneaker
   drop from shoes. Kept on purpose: "Trail Running Sneaker" (Morphaxis) and **"Hiking Sneakers"** (Speedarc Matis Mid GTX is a real hiking
   shoe; the same merge feeds the Hiking side). Pushing back on that one row.
5. **33-off:** "GORE-TEX®" (the ®), MID, LOW, GRVL, CSWP kept: "Accentor Sport 3 GORE-TEX", "X Ultra 4 MID GTX", "Aero Blaze 3 GRVL GTX".
6. **Ski/snow + bike + blankets + dresses:** clothing groups only, both sides: snow/ski pants and bibs, cycling/bike jerseys, bib shorts,
   chamois, MTB; "bike shorts" only from cycling brands (Canari, Rapha, Endura…) so Hoka Elaro / UA Motion stay; blankets; dresses and
   cardigans; anything with "run"/"running" in the name stays (Kiprun "Cycling Shorts, Run 900"); race bib belts stay; cross-country ski
   tights/jackets stay (Canada, Decathlon: winter runners). Today: 373 US listings, 2 CA (OR Snowcrew Bibs + the Kiprun one, now kept).
   Confluence's product-type grouping NOT done (its dresses/cardigan are gone with this rule; "Ultralight - Women's" twins remain).
7. **Odd regular price:** your 1.8x gift-page rule hit 32 CA + 36 US real prices (Stella McCartney leggings $170, Helly Hansen jackets).
   Shipped a strict one instead: regular > 5x the brand's usual for that category AND the sale price ordinary (<= 2x usual) AND 75%+ off ->
   the "was" goes (shows at full price, the price the store really asks). Today it hits exactly one: TNF Snoga Pants.
8. **Playmakers (and The Feed):** when product.js 404s, livecheck reads the page's JSON-LD offers (price, InStock, ListPrice). One size
   can't be told apart (offers name colour/size, not our variant id): without a variant any offer counts; with one, only when every offer
   is on sale at that price, else "can't tell". So featured checks work; per-size shoe checks for posts still skip Playmakers.
Also in this push: the FR Black Friday live-page title ("ces aubaines course sont-elles vraies?").

## Nov 6 (night): your SEO spec S1 (empty FAQ answers on race pages), done
A distance with no mandatory gear now answers "None: the race's list has no mandatory gear for this distance. It recommends: …"
(FR « Aucun : la liste de la course n'a pas de matériel obligatoire pour cette distance. Elle recommande : … »), plus "The race provides: …"
when it hands something out; same text in the visible FAQ and the FAQPage JSON-LD. Checked: Frosty 13K, Moose Mountain 16K, Tarawera T14
(EN/FR/US). check.py "Race gear pages" now fails on any empty FAQ answer on race + trail pages (549 answers today, none empty).

## Nov 7: Fox Pro piece #1 (checkout, TEST MODE) built; your Nov 6 answers noted
Thanks: store table by Nov 8 (I'll build #5 on your columns), referrals Nov 20 = yes unless you say otherwise.
BLOCKED: Bastien pastes supabase/fox-pro-nov7.sql in the Supabase SQL Editor (one paste, safe to repeat; adds the Pro tables + numbered founding spots, visible to nobody). Until then a test payment can't be recorded. Please put it on the Outbox copy page.
BLOCKED: USD prices for the USA side (terms draft says "[USD amounts] [BASTIEN]"). My pick: US$27/year founding, US$34 regular (same as CAD at today's rate, rounded). Yes/no. Until then the US side says "Fox Pro in US dollars opens soon".

What's built (nothing visible to visitors):
- **Checkout screen** (`/?pro=checkout`, members only; fox-pro-look.md): "$36 CAD a year · No tax added. That's the total.", lock line,
  "Renews on <date a year out> at the same price. We email you 45 days before.", 30-day full refund, cancel online, **"Read the Fox Pro terms"
  before the pay button**, rust "Continue to secure payment →", "Payment by Stripe. We never see your card.", a TEST MODE line. EN/FR, fits 320px.
  /terms-pro.html = a noindex placeholder until piece #4 puts the real terms there.
- **pro-checkout** function: member key -> Stripe Checkout (yearly, founding while < 100 paid, else $45), French page for French members.
  Off unless the PRO_CHECKOUT secret says test (sandbox key only) or live.
- **Webhook**: a paid checkout records the member and hands out Founding Fox #001-#100 in payment order (two payments in the same second can't
  get the same number; test numbers never use up real ones); cancel/renewal changes keep the record current; each Stripe event once.
- Back from Stripe (`?pro=welcome`): "Welcome to Fox Pro, Founding Fox #007. A receipt is on its way to your inbox."
- Site test "Fox Pro checkout screen (before Stripe)". Next: the Stripe test prices (CAD) via stripe-setup.yml, then piece #2 (Pro perks).
Note: the screen always shows $36 for now; once 100 are paid it must show $45 (piece #2 reads the live count).

## Nov 6 (afternoon): your shoe-page round, morning audit and price-adjust table, done
- **Wide sizes, one table per width** (Clifton 10): a regular card's wide sizes now go only into the "· wide" table, each size at its best
  price across both sources (men's 11 wide: $129.99 Brainsport, the $143.88 row is gone). check.py fails on any wide row in a regular table.
- **Badge vs price line:** the hero badge reads the same history as the price line and its N stops at the last day the price was cheaper
  (under 30 = no badge); forest green (#24492F, white) instead of orange. Clifton 10: badge gone (it was cheaper Oct 4). check.py fails when
  a badge's N spans a date its price line names as cheaper. List-card "lowest in N days" labels still use the homepage rule (same lo/hd) - say if you see one disagree.
- **Women's table first:** only for visitors whose saved profile is women's or "both"; no saved size = men's first. As designed on Oct 18.
- **Morning audit:** 1 The Run House wide shoes (title "(Wide)" / tag "Wide", Size option only) now read as wide, any Shopify store; 2 pickleball
  (store tags pickleball/tennis/padel, "PKL") out; 3 Iron Legs re-read on ironlegs.ca: 25 km = "min. 1L" (own line), others 1.5 L;
  4 cup line + "no cups" answer removed (no Iron Legs page mentions cups); 5 prenatal/postnatal products out of Nutrition (Nuun vitamin tabs stay).
  Take effect at the next store read (pickleball, wide, prenatal) or at once (Iron Legs).
- **Price-adjust table:** thanks. Drafts fixed: "about 25 stores" -> the real 8 (EN + « 8 boutiques que nous avons vérifiées »), the Sporting Life
  "until Dec 2" mock -> Altitude Sports with its real published words. #5 will read the list from one data file you can edit.

## Nov 6 (evening): Bastien's 4 answers, received
1. Founding card: already exactly his card (lock + 3 ticks) with today's tick lines (live in the code since Nov 6, OFF until his Nov 16 OK). No merged card. Nothing to change.
2. Watchlist from Dec 2 (grandfather): building into piece #2: a free member can add a watch only while count < max(5, count they held on Dec 2);
   at the limit the add shows "Watch unlimited with Fox Pro". Pro = no limit. The Dec 2 count is recorded per member that day (no one loses an item).
3. Resend pacing + 429 retry: already shipped Nov 6 (scraper/mailer.py; every bulk sender uses it; check.py tests it). Plan upgrade stays his call.
4. Referrals Nov 20: on the list.
- Nov 6 evening, your 2 items: (1) Resend send counts: the morning email gets, from Dec 10, "Busiest email day in the last 7: N on <day>
  (Resend free plan: 100 a day[, close / over it])" (scraper/mail_health.py, counts what Resend actually sent, Supabase's sign-up emails included).
  (2) "the The North Face": already fixed since Nov 3 (tidy_words); the live page reads "Email me when The North Face Altamesa 300 drops".

## Nov 6, 22:19 UTC: Safe Links check after the Nov 6 weekly email (scheduled re-run)
mail-check.yml: "Microsoft: 9 watches, 0 within 5 min, 0 within 60 min; other: 173 watches, 0 within 5 min, 0 within 60 min" (76 emails to
Microsoft addresses, all delivered). Microsoft's link scanner did NOT make watches from the email links, so MS_AUTOWATCH stays True for the
Nov 13 "watch one thing" box. No code change.
