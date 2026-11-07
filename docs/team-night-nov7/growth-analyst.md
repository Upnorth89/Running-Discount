# Founding-list pipeline math (growth-analyst, night of Nov 7, 2026)

Sources (each number below names one):
- F = funnel.yml run 42062595471 (Nov 5 16:16 UTC; window = the last 14 days, Oct 22 - Nov 5)
- M = mail-check.yml run 42315357980 (Nov 6 23:58 UTC)
- B = docs/bf-email-volume-nov6.md (weekly-email + refresh run logs)
- S = docs/signup-funnel-nov4.md (funnel run 41778856341, Nov 4)
- C = docs/founding-ask-copy-nov5.md (the places and the members-lead/CMO estimates)

## Answer in 3 lines
1. At today's pace we reach about **250-300 members by Nov 30** (on track for 250), but the founding asks as planned give an expected **~15-45 joins, middle ~28**. That is under the 40 floor in the middle case and well under the 60 goal.
2. The Friday emails (~380 sends over 3 sends) and the "You're in" step (every new sign-up sees it) are the two places that carry the number. The site card, alert line and welcome P.S. add ~5-15 between them.
3. Biggest levers: **(a) put the founding box at the TOP of the Nov 20/21 + Nov 27 emails** (about +5-10 joins), and **(b) ship the "You're in" step on Nov 16 for every sign-up spot, incl. shoe pages** (about +3-10). More members helps, but only ~1 join per 10 extra members. A Reel is the weakest lever on our numbers.

## 1. Members now and sign-ups per day
| Number | Value | Source |
|---|---|---|
| Real members (subscribers minus 9 test addresses) | 165 on Nov 5 | F "EMAIL: … REAL SUBSCRIBERS NOW 165" |
| Sign-ups in 14 days | 60, all confirmed (single opt-in) = **4.3 a day** | F |
| Sign-ups in the week of Oct 29 - Nov 4 | 37 = 5.3 a day (high case) | F "WEEK VS WEEK" |
| New rows in the week of Nov 2 (Mon-Fri) | 17 = ~3.4 a day (low case) | M "new rows week of Nov 02" |
| Unsubscribes, ever | 1 | F |
| Watchers (members watching 1+ item) | 50 of 165 (30%) | F "WATCHLIST SIZE" |
| Members who come back on another day | 86 of 161 (53%), ever, not per window | F "COMING BACK" |

Projection (straight line from 165 on Nov 5, no Black Friday boost):
| Date | Low 3.4/day | Mid 4.3/day | High 5.3/day |
|---|---|---|---|
| Nov 17 | 206 | 217 | 229 |
| Nov 20 (Friday send) | 216 | 230 | 245 |
| Nov 27 (BF Friday) | 240 | 260 | 282 |
| Nov 30 | 250 | 273 | 298 |
Read: 250 members by Nov 30 holds even at the low pace. New members Nov 17-30 (14 days): ~48 / ~60 / ~74.

## 2. Who sees each founding ask, Nov 17-30
| Place | Who sees it | Count | Basis |
|---|---|---|---|
| Friday email box, Nov 20 (A) / Nov 21 (B, emailday test) | members not on the list who get an email | ~185 sends (230 x ~80%) | ~80% of a group gets an email: Oct 31 Saturday group 72 sent, 17 skipped "nothing on sale in their sizes" (B) |
| Friday email box, Nov 27 (BF, Friday for all) | same, minus those already on the list | ~195 sends (260 x ~80%, minus joiners) | B |
| Site card (members, 2+ visits, card slot) | members who visit in the window AND scroll to the card slot | **unknown**; ceiling ~120 (53% of ~230) | F gives "came back ever", not "visited Nov 17-30". The card sits after the first block: scroll depth for members isn't printed |
| Drop/back-in-size alert line | watchers who get an alert | ~30-60 alerts to ~20-40 people | alerts: 1, 7, 1, 1 sent Nov 1-3 (B); ~30 in 14 days; BF should bring more drops (assumption); only 30% of members watch (F) |
| Welcome email P.S. | new members | ~48-74 | projection above |
| "You're in" step (CMO, Nov 16 batch) | every new sign-up, at the moment of joining | ~48-74 (100% see it) | projection above |

How many open/read the emails: **unknown** (Resend open tracking is off on purpose). What we have: our emails bring **~1 site visit per 10 weekly emails** and **~1 per 2 alert emails** (docs/members-plan-nov4.md; F: visits from emails alert 18, friday 17, saturday 11 in 14 days). The weekly count misses store taps (cards link straight to stores), so 10% is a floor for "clicked something".

## 3. Join rates: what evidence we have
- **Our Oct 28-Nov 4 Fox Pro card: 0 joins of 82 views (S).** Not comparable: since Oct 31 the card shows only on ?pro=1 links, so those 82 views are previews and checks, not visitors; it was also the $3/$5 price-test card. It tells us nothing about real join rates. Treat as "no data".
- **Our closest real analog: item-named asks.** Email step after a Watch tap: 21-23 sign-ups from ~91 Watch-tap sessions, up to ~25% (S, F). Generic homepage card: 10 sign-ups from 4,395 sessions that saw deals = 0.23% (F). A one-tap ask to someone already acting converts ~100x better than a generic box on our own site.
- **Named outside benchmark (for paying, the harder step):** self-serve freemium products convert ~3-5% of free users to paid ("good"), 6-8% "great" (Lenny Rachitsky's freemium benchmarks). A free, one-tap list join should be at or above that, so I use 3% as the floor for members who see the ask.
- **Email clicks:** our own ~10% visit-per-weekly-email (above) is the ceiling for any one box; a box after the "Dropped this week" block gets less than the whole email.

Rates used (assumptions, labelled):
| Place | Low | High | Why |
|---|---|---|---|
| Friday box, per send | 1.5% (3% click x half tap Join) | 5% (10% click x half) | our 1-in-10 email visits; Join needs one tap on the card |
| Site card, per member who sees it | 3% | 10% | freemium floor; one tap, members only |
| Alert line, per person | 3% | 10% | alerts pull 1 visit per 2 emails, but the line sits under "Open your watchlist" |
| Welcome P.S. | 2% | 5% | a P.S. under the main button, read once |
| "You're in" step | 5% | 25% | same moment as the Watch-tap step (up to 25%) |

## 4. Expected list size by Nov 30 (members, before overlap)
| Place | Low | Mid | High |
|---|---|---|---|
| Friday Nov 20/21 | 3 | 6 | 9 |
| Friday Nov 27 | 3 | 6 | 10 |
| Site card (ceiling 120 seers; unknown) | 2 | 6 | 12 |
| Alert line | 1 | 2 | 4 |
| Welcome P.S. | 1 | 2 | 4 |
| "You're in" step | 2 | 6 | 15 |
| **Total** | **~12** | **~28** | **~54** |
Overlap (the same member reached twice) lowers each total a little. So: floor 40 = high-ish case; goal 60 = not reached as planned. The members-lead/CMO estimate in C (35-70) sits above my range because its rates are not tied to our data.

Stop-rule check: C says "< 25 by Nov 24 = BF traffic not converting". By Nov 24 only the site card (7 days), one Friday send, alerts and ~30 welcomes/You're-in steps have run: mid case ~14. **That rule will fire even if things go to plan.** Re-base it to "< 12 by Nov 24" (mid case minus noise), or judge on Nov 28 after the BF send.

## 5. The 2 levers that move the number most
Every place scales with how many people see it x the share that taps. Ranked by joins added per unit of work:

**Lever 1: founding box at the top of the Nov 20/21 + Nov 27 emails (right after the intro, before "Dropped this week")** instead of after the drops block (C / members-plan placement).
- Math: ~380 sends. NN/g's scrolling research (2018): ~57% of viewing time goes above the fold, ~74% to the first two screenfuls. Moving the box from mid-email to the top plausibly doubles its clicks: 3-10% -> 6-15% click, half tap Join = 1.5-5% -> 3-7.5% join = **+6 to +10 joins** over the two sends (low to high).
- Cost: one ordering change in weekly_email.py; it shares the top with the "Watch one thing" box (zero-watchers only, Nov 13+). Order: founding box first on Nov 20/21 + 27 only, watch box second.
- Measure: pro-join by em=friday-pro vs saturday-pro (both groups get the same placement, so the emailday test stays clean).

**Lever 2: the "You're in" step on Nov 16, at EVERY sign-up spot (homepage, Watch-tap step, shoe pages, sale lists, BF pages, race/trail lists)**, not only the homepage.
- Math: it's the only place every new member sees, at a moment of action. Shoe pages + the Watch-tap step are 43 of 71 sign-up events (F "Sign-ups by where": shoe-page 22, email|sheet 21). Leaving them out drops ~60% of the audience. At 60 new members x 5-25% = **3-15 joins**; homepage-only would be ~1-6.
- Also feeds lever "more members": BF traffic (Nov 20-30) lifts sign-ups, and each one meets the ask at once.

**Why not the others first:**
- More members: each extra member is worth ~0.1 join over this window (28 joins / ~270 members, mid case). +50 members (doubling the pace for 10 days) = ~+5. Real, but slower than levers 1-2; the shoe-page in-place watch test ('shoewatch', S) is the way, and it can't decide before Dec 8.
- A Reel: Instagram brought 16 first visits in 14 days (F scorecard), tagged ig links 9 first visits and 1 sign-up (F). A Reel reaching members who join = a handful at best. Do it for awareness, not for the list.
- Reddit: 1,322 first visits, 7 sign-ups (0.5%, F). Not a list builder.

## Data gaps (what would answer them)
- Members who visited Nov 17-30 and saw the card: funnel.py needs "members active in window" + "pro-view by place" (the analytics event signup-step pro-view|<place> exists per backend-to-growth Nov 6; the funnel line doesn't yet).
- Email box clicks: em=friday-pro / saturday-pro / alert-pro / welcome-pro tags exist; funnel must print pro-join by em tag (spec'd in docs/members-plan-nov4.md).
- No A/B test is possible here: 5% -> 10% join needs ~435 per group (80% power, 5% level); one send is ~190. Judge each place by its own joins.

## One decision for Bastien
Put the founding box FIRST in the Nov 20/21 and Nov 27 emails (above "Dropped this week")? yes/no. (Plus a housekeeping one for growth to just do: re-base the Nov 24 stop line to < 12.)
