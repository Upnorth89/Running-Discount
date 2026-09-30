# The Gear Fox: handoff notes for Claude

The Gear Fox (thegearfox.com, tagline "Outfox full price"; French: « Flairez les aubaines ») is a free site
that shows running and outdoor gear **on sale in your size** from 50+ stores, mostly Canadian. Owner:
Bastien (Vancouver, ultrarunner). Visitors pick their sizes, add an email, and get a Friday deals email
plus price-drop alerts on items they heart. Goal: $500–1,000/month by March 2027 from affiliate links,
then a paid tier (Fox Pro). The 6-month plan with weekly tasks:
https://claude.ai/code/artifact/36e1d545-7390-44fe-b080-80f03465af61

## How to work with Bastien

- **Preview first, always.** Show every change to the site in the playable preview artifact before it goes
  live (see Preview below). He approves, then it ships.
- He is not a developer. Plain language, short steps, no jargon; explain the why in a sentence.
- **Everything is bilingual (EN/FR).** Any new text needs both. French is Québec French ("courriel",
  "aubaines", "bas" for socks).
- Be willing to push back; he asks for honest opinions.
- **Push straight to `main`.** No pull requests or side branches (the site deploys from `main`).
- **Never ask him to paste secret keys into chat.** Secrets live only in GitHub secrets, Supabase or Vault.
- After every change, verify it landed: the right file in the right folder, the site updated, nothing broken.
- Don't touch `email/profiles.json` (old sign-up list; kept out of commits). Subscribers live in Supabase.
- Don't circumvent bot protection. Stores that block automated access (Sport Chek, Running Room, Atmosphere,
  Sports Experts, MEC, REI…) are either skipped, read from pages Bastien saves himself, or wait for
  affiliate product feeds.

## Repo map (github.com/upnorth89/Running-Discount, branch main)

```
site/index.html          the whole site (one file: HTML, CSS, JS, EN/FR dictionary I18N)
site/privacy.html        bilingual privacy page
site/grab.html, grab.js  "Grab deals" bookmark for MEC/REI (Bastien saves their sale pages weekly)
site/deals.json          generated daily (merged items); offers.json = raw per-store data; health.json
scraper/scrape.py        all store readers + merge -> site/deals.json and site/offers.json
scraper/weekly_email.py  the Friday email (also the size-matching rules shared with alerts)
scraper/alerts.py        daily price-drop / back-in-your-size emails
scraper/health.py        daily health check + morning report email
supabase/setup.sql       database: tables, sign-up/confirm/profile/Google functions, email templates
supabase/watchlist.sql   watchlist table + functions
supabase/friday-switch.sql  latest change (Friday wording + weekly_sent_at column); already applied
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
  - The scrape log ends with product counts per category (and on sale) and nutrition by store.
- **Weekly deals email** (`weekly-email.yml`): every hour on Friday 9:07–18:07 UTC. Each run sends to
  subscribers for whom it is now Friday 7am or later in their own time zone (profile `tz` from the browser;
  default: French = Eastern, English = Pacific) and records `weekly_sent_at` so nobody gets two.
  Manual "Run workflow" requires a `send_to` address (or `everyone`) and sends immediately.
- **Alerts**: at most one email per person every 3 days, only real drops (10% or $10), none on Fridays
  (the Friday email carries watchlist news).
- **Health check**: emails a daily report (subject says "all good", "all running, N still to fix" or
  "N new problems") to the `HEALTH_EMAIL` secret, else hello@thegearfox.com. Flags stale or empty stores,
  halved product counts, price jumps (currency mix-ups), piles of 70%+ discounts, and subscriber counts
  near the free email limits. Only the scheduled run emails.

GitHub secrets (names only): `SUPABASE_SECRET_KEY`, `RESEND_API_KEY`, `MAILING_ADDRESS` (CASL footer),
`HEALTH_EMAIL`.

## Stores and data

- Shopify stores: listed in `SHOPIFY_STORES` in scrape.py (~44). Read via `/products.json`, prices checked
  in CAD with Canadian cookies (cart.js tells the served currency; USD is converted).
- Altitude Sports and The Last Hunt: commercetools readers (running category types in `CT_TYPES`).
- Sporting Life, Stampeak, Sea2Sky, The Feed: custom readers. Decathlon: running clearance pages
  (server-rendered JSON, robots allow). MEC/REI: from saved pages only.
- Known: Honey Stinger is blocked from GitHub's servers (works elsewhere); REI needs fresh saved pages.
- **Adding a store** (Bastien aims for steady growth, 1–3 a week): check readability, currency, size labels
  (share readable), categories, sale share; add to `SHOPIFY_STORES`; remerge locally
  (`python scraper/scrape.py site/deals.json --remerge` with a fresh `offers.json`) and preview.
- Item shape in deals.json: `b` brand, `n` name, `g` group, `sx` genders, `w` wide, `img`, `lp`, `of` store
  links, `ca` ships from Canada, `sz` = `[size, price, offerIndex, regular, variantId?]`.
- Groups: shoes, tops, bottoms, bras, socks, gloves, headwear, packs, gear, watches, nutrition.
- Shoe size keys: `"10"`, `"M:10"`/`"W:11"` (from unisex labels), suffix `~W` wide, `~N` narrow (hidden).
- Accessories (packs, gear) in letter sizes follow the clothing size; odd labels are hidden on cards.
- Merge tidies names (no repeated brand, French gender words to English; the FR site shows them in French),
  canonical brands (e.g. "Hoka One One" → "Hoka"), drops casual footwear, sorts non-food out of Nutrition.
- Ranking ("Best match"): favourites, then a deal score = % off + category bonus + dollars saved.

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

- First visit: welcome screen → sizes → email or Google sign-in (flow "D"). The welcome line claims
  "More than half of gear deals aren't available in your size", recomputed daily (`missShare()`).
- Returning: calm top (sizes line + Edit, one count line with the 30-day "found this month" savings,
  watchlist strip, swipe row of new deals), categories, search + Filters (Ships from Canada, Include full
  price, Sort). Sale items only by default.
- EN headline "Your size. On sale. Every day."; FR « Des aubaines sur mesure. »
- CAD/USD switch, watchlist with alerts, Google sign-in, Umami analytics (no cookies; events welcome-view,
  signup-step, signup, signup-confirmed, signin, deal-click, watch-add, language, currency).

## Preview

`python tools/make_preview.py OUT.html` builds a self-contained copy with today's data, a pretend server,
and a test panel (new visitor, pretend confirmed, pretend a day passed, layout switches). Publish it to the
"Gear Fox Preview" artifact: https://claude.ai/artifact/WqbJ6uZF8eM2NqFAuxoL6K
A ski/snowboard preview also exists (parked): https://claude.ai/artifact/QQeVvJDPSkD4dAomdeMpSo

## Where things stand (Sep 30, 2026)

Done: size-first site live, 50+ stores, Friday 7am-local email, alerts, daily health report, calm layout,
clean names and ranking. Next (Week 1–2 of the plan): finish the email test (sign-up EN/FR, sign-in link,
Friday email, alert, unsubscribe), link previews + share button, Outlook "check Junk" hint + resend button,
then soft launch to friends and Sacred Strides athletes with `?ref=` links per group.
