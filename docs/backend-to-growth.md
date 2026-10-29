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
