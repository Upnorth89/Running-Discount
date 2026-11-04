# Sign-up funnel + live tests (night job, Nov 4, 2026)

Source for every number unless marked: funnel.yml run 41778856341 (triggered Nov 4 05:22 UTC, success), tools/funnel.py 14 days =
Oct 21 - Nov 4. Raw annotations: /tmp/claude-0/-home-user-Running-Discount/cb135926-fa1d-570a-9fca-b3ccd4d85f5b/scratchpad/night/funnel-nov04.txt
EXPERIMENT lines = devices first seen Oct 21 - Nov 2 (2+ days old), their FIRST session only. Estimates are labelled "est.".

## Answer in 3 lines
1. Sign-ups come from item-specific asks: Watch-tap email step 23 + shoe-page "Email me when it drops" 17 = 40 of 69 sign-up events (58%); the generic homepage card brings 10 (0.23% of the 4,288 sessions that saw deals) and the namecard version 0.
2. Three tests can be called now on their own rules: alts, run1st, cards2 all reached sample, none better -> A for everyone. namecard, watchsheet, popq, wlean, kit, emailday keep running (watchsheet + popq metrics are not even printed by funnel.py yet).
3. Biggest leak = shoe pages: 1,376 first visits (28% of all), 445 clicked a store, 4% ever came back, ~0.7% sign up in the first visit.

## (1) Sign-ups by entry point, last 14 days (69 sign-up events; 61 new subscriber rows, 61 confirmed)
| Entry point (event detail) | Sign-ups | Denominator | Rate |
|---|---|---|---|
| Watch-tap email step, A + B together (email|sheet) | 23 | 91 sessions tapped Watch | <= 25% (upper bound: the step also opens from the watchlist button; members tapping Watch never need it) |
| Shoe page "Email me when it drops" (shoe-page; the shoe-page "Didn't buy it?" bar submits the same form, so it is inside this 17) | 17 | 1,376 shoe-page first visits; 335 of them picked a size | est. 1.2% per first visit, ~5% per size-picker (sign-ups can be in later sessions) |
| Google button (google) | 12 | not tracked (no Google-button-tap count) | n/a |
| Homepage card A "Free with your email" (email|card) | 10 | 4,288 sessions that saw deals (card + namecard together) | 0.23% |
| Homepage namecard B (email|namecard) | 0 | since Oct 29 | 0 |
| Sale-list qs_box (sale-list) | 6 | page sessions not counted by funnel | n/a |
| Black Friday qs_box (black-friday) | 0 | not counted | 0 |
| Shoe page "Back in my size" (shoe-page-back) | 1 | not counted | n/a |
| Race gear list box (race-<slug>) | 0 | 200 race-list sessions (3 signed up elsewhere in the session) | 0% |
| Trail gear list box (hike-<slug>) | 0 | 19 sessions | 0% |
| Runcard / Fox Pro card | 0 / 0 | Fox Pro card: 82 sessions saw it (20 A, 62 B), 0 joined | 0% |
By first-visit source: google 16 of 850 (2%), no referrer 18 of 3,368 (1%), reddit 2 of 427, other sites 3 of 225, home-screen app 2 of 12.
Reddit ?ref links: 8 sign-ups from 1,336 first visits (0.6%). Signed-up devices came back 53% vs 14% for the rest (correlation, not proof).
Sign-up failures: 5 (all bad-email) in 4 sessions.

## (2) Live tests (two-proportion test, 80% power, 5% level; keep B only at p < 0.05)
Daily volumes from the EXPERIMENT counts divided by the days each test has in the cohort window (est.).
| Test | Registered metric | So far A / B | p | Needed per group | Call | Decide by |
|---|---|---|---|---|---|---|
| alts (shoe pages) | went on to another of our pages | 17.2% of 676 / 19.3% of 689 | 0.305 | 435 (planned for 5% -> 10%) | CALL: A (sample reached, not proven). Real baseline is 17%, not 5%; +2 pts would need 5,310/group | now (plan said Nov 8) |
| run1st | homepage first visits clicking a store | 32.9% of 1,373 / 32.1% of 1,320 | 0.658 | 583 | CALL: A. Lead: B picked sizes less, 42.7% vs 46.4%, p=0.056 | now (plan Nov 9) |
| cards2 | homepage first visits clicking a store | 33.4% of 1,308 / 32.9% of 1,242 | 0.797 | 1,444 for 33% -> 38% | CALL: A. Caveat: the coin is tossed for every device, B only shows on 380-699px phones, so computers dilute it; still no sign of lift | now |
| namecard | homepage first visits signing up | 1.1% of 436 / 1.0% of 389 | 0.870 | 2,319 (1% -> 2%) | KEEP. Card-only sign-ups since Oct 29: B 0 ("email|namecard"); A's "email|card" 10 covers the whole 14 days, so no clean split (lead only) | ~82/group/day -> sample ~Nov 26, read ~Nov 28 (plan said Nov 20) |
| watchsheet | sign-ups from the step among Watch-tap sessions | NOT PRINTED by funnel.py (only first-visit sign-up: 1.1% of 365 / 1.2% of 423, p=0.910) | - | 138 (20% -> 35%) | KEEP; can't be judged until funnel prints it | ~54 Watch-tap sessions a week = ~27/group -> ~Dec 3 |
| popq | homepage first visits that search | NOT PRINTED (proxies: sizes 48.2% / 51.9% p=0.106; another page 6.4% / 8.1% p=0.149) | - | 1,471 (5% -> 7.5%) | KEEP; sample reached ~Nov 6 but the metric needs a funnel line | Nov 8 if the line exists |
| wlean (computers) | computer homepage first visits picking sizes | 66.7% of 21 / 80.0% of 30 | 0.282 | 376 as planned (35% -> 45%); 173 if re-based on the 67% seen | KEEP. "store or sizes" B 90% vs 67% p=0.039 is a secondary metric among 12 looked at: not a win | ~10/group/day -> Nov 19 (173) or ~Dec 6 (376) |
| kit (race + trail lists) | sessions ticking or clicking a store | 29% of 24 / 50% of 12 | 0.220 | 553 as planned (4% -> 8%); 84 at the real 29% baseline | KEEP | B gets ~1.5 sessions/day -> ~Dec 22 for 84 |
| emailday | sends that bring a visit | Friday 16 sessions / Saturday 8 (Friday count mixes in the pre-test Oct 23 send) | - | 178 sends/group (11% -> 22%) | KEEP; needs per-send denominators from the email log | after the last B send Nov 21 -> read Nov 23 |
Ended tests still printed (short, r100, layout, runcard): ignore. Fox Pro price test: 0 of 82 joined (window started Nov 2; card is ?pro=1 only since Oct 31, so these 82 views come from ?pro=1 links (previews, checks), not a market read).

## (3) Three biggest sign-up leaks (intent, no sign-up)
1. Shoe pages: 1,376 first visits, 445 clicked a store (32%), 335 picked a size, 17 sign-ups in any session; 4% of shoe-page landers ever
   came back vs 16% of homepage landers. funnel.py cannot see the "Didn't buy it?" bar: the page sends "shoe-backbar-view", funnel counts
   "watchbar-view" (shows 0) and "backbar-view" (exact match). So its show rate is unknown (measurement bug).
2. Homepage after sizes: 1,328 first visits picked sizes, 960 clicked a store, 35 signed up (1% of 2,930). The card: 10 sign-ups from 4,288
   sessions that saw deals, and only 2 "No thanks" taps: people scroll past it rather than turn it down.
3. Watch taps: 91 sessions tapped Watch, 23 sign-ups from the step: up to ~68 sessions with item intent left without an email (upper bound:
   some are members). Separately 116 of 164 real members watch nothing. Race lists: 200 sessions, 9 watched an item, 0 box sign-ups, 0 reminders asked.

## (4) One recommendation for the Nov 16 batch
Shoe pages: per-table "♡ Watch the price" opens the named email step in place ("Email me when the <shoe> drops in size <n>") instead of
sending people to /?watch= on the homepage. A/B test 'shoewatch'.
Why: the two item-named asks bring 58% of sign-ups; shoe pages are 28% of first visits but only ~0.7% sign up in the first visit
(alts A 0.4% / B 1.0%); the current link takes them off the page (only 5% of shoe-page landers reach the homepage).
Expected lift (est.): 0.7% -> ~2.1% of shoe-page first visits signing up. Detecting that needs 1,105 per group; at ~49/group/day
(1,376 shoe-page first visits / 14 days / 2) = ~Dec 8 if it starts Nov 16. A smaller lift (0.7% -> 1.4%) needs 3,328/group: undecidable before January.
Measure: funnel EXPERIMENT 'shoewatch' "signed up (everyone)" on shoe-page first visits + a new count of shoe-page Watch taps.
Before it: funnel.py lines (spec for backend, not visible, freeze-safe): popq "searched" per arm; watchsheet "sheet sign-ups / Watch-tap
sessions" per arm; cards2 phones 380-699 only; shoe-page "Didn't buy it?" bar = "shoe-backbar-view"; sign-ups by entry point per arm.
