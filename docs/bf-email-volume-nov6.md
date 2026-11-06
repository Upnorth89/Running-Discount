# Email volume vs Resend's limits, Nov 17 - Dec 4 (growth-analyst, night of Nov 6, 2026)

## Answer
1. The free plan's 100 emails a day breaks on **Fri Nov 27 (~240 emails, 2.4x the cap)** and **Fri Dec 4 (~270)**; Fri Nov 20 / Sat Nov 21 sit right at it (~105-125 each). Month totals stay under 3,000 (Nov ~1,250, Dec ~1,800).
2. We are still on the free plan as far as the repo shows: Bastien said "I will upgrade the email resend" (Oct 31) and a one-time task "Resend upgrade Nov 18" exists, but nothing records it done.
3. Fix: **upgrade to Resend Pro ($20/month: 50,000 a month, no daily cap) by Thu Nov 19**. Spreading sends can't work: Nov 27 would need 3 days, and the email promises Friday.

## What sends email (from the code)
| Sender | When | Pace |
|---|---|---|
| weekly_email.py | Friday 7am local, hourly runs 9:07-18:07 UTC; test 'emailday' group B on Saturday until Nov 21 (`DAY_TEST`), Friday for all from Nov 27 | no pause between sends |
| alerts.py | morning refresh, never Fridays (line 252), max 1 per person per 70 h; B gets none on Saturdays in the test window | no pause |
| Welcome + "Save your changes" sign-in (Supabase pg_net) | each sign-up / sign-in; founding P.S. rides INSIDE the welcome (no extra email) | pg_net batches per transaction |
| race_remind.py, confirm_reminder.py | morning; tiny volumes (0 reminders asked as of Nov 4; single opt-in since Oct 29) | 0.6-0.7 s pause |
| Health/ops to Bastien (morning, afternoon, noon/night scan when something's wrong, Mon usage, Wed IG brief) | ~3 a day | - |
| Dec 2 founding link; purchase email with the terms (backend-to-growth.md, Nov 6) | not built yet | must be paced |

## Real numbers used
- 164 real members on Nov 4 (docs/signup-ideas-nov4.md); 155 on Nov 2 (funnel run 41466393627).
- New subscriber rows per week (mail-check run 42102106230, Nov 5): Oct 19 week 14, Oct 26 week 39, Nov 2 week 12 by Thursday. I use ~5 a day, 7 a day as the high case.
- Oct 31 Saturday group: 72 sent, 17 "nothing on sale in their sizes", 0 failed (weekly-email.yml logs, Oct 31). So ~80% of a group gets an email; 47 went out in one run (11:07 UTC) with no 429.
- Alerts: 1, 7, 1, 1 sent Nov 1-3 (refresh logs, docs/members-plan-nov4.md).
- Sign-up/sign-in emails: 7 in 2 days (mail-check, Nov 5).
- Resend log on Oct 31: 637 emails (docs/decisions.md, Oct 31) = October's real volume, roughly.
- No past day went over 100: before single opt-in (Oct 29) only ~half of sign-ups were confirmed, and the test split the list from Oct 30.
- Not verified: the account's plan itself (needs Resend's billing page or Bastien's word).

## Worst days (members projected at ~5 sign-ups a day from 164 on Nov 4; high case 7 a day)
| Day | List | Weekly email | Alerts | Welcomes + sign-ins | Ops + other | Total (high) | vs 100 |
|---|---|---|---|---|---|---|---|
| Fri Nov 20 | ~245 (275) | group A ~100 (110) | 0 (Friday) | ~8 | ~3 | **~110 (125)** | over |
| Sat Nov 21 | ~250 | group B ~100 (110) | A only ~5 (15) | ~8 | ~3 | **~115 (135)** | over |
| Fri Nov 27 (BF) | ~280 (325) | everyone ~225 (260) | 0 | ~12 (BF traffic) | ~3 | **~240 (280)** | 2.4x over |
| Wed Dec 2 | ~305 | - | ~10 (25; Cyber Monday drops, 70 h cap) | ~8 | founding link to the list 40-80 + purchase emails up to ~20 + 3 | **~80 (135)** | at risk |
| Fri Dec 4 (launch) | ~315 (385) | everyone ~250 (310) | 0 | ~15 | purchase emails + 3 | **~270 (330)** | 2.7x over |
Even Fri Nov 13 (group A ~82 + ~10) is close.

## Month totals vs 3,000
- November: weekly ~720 (Nov 6/7 ~136, 13/14 ~160, 20/21 ~200, 27 ~225) + alerts ~150 + welcomes/sign-ins ~200 + ops ~100 = **~1,200 (high ~1,500)**. Under.
- December: 4 Fridays x ~250-300 + Dec 2 + alerts + launch sign-ups = **~1,600-2,000**. Under, but by January 3,000 is in reach.

## The fix and why
- **Upgrade to Resend Pro ($20 USD/month) before the first Friday send on Nov 20 (9:07 UTC)**; Nov 19 is the hard deadline, so move the Nov 18 task no later. Over the cap, Resend answers 429 and the rest of that Friday's list gets nothing until the next hourly run, which also fails: a silent half-sent Black Friday email.
- Spreading is not a fix: 240 emails at 100 a day = 3 days; Friday is the promise and BF week is "Friday for all" by our own rule.
- The 2-requests-a-second limit stays on every plan. Two cheap backend guards (spec, not built): a 0.6 s pause + one retry on 429 in weekly_email.py and alerts.py (as race_remind/confirm_reminder already do); the Dec 2 founding link sent by a paced script, never from SQL (Oct 29 lesson: 41 of 54 welcomes lost).
- health.py warns only at 500 subscribers (WEEKLY_SUBS_WARN) and 60 sign-ups a day: it will not flag the Nov 27 overrun. Fine once on Pro; if the upgrade slips, that warning is wrong today.

## Decision for Bastien
Upgrade Resend to Pro ($20/month) by Thu Nov 19? yes/no
