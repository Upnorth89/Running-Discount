# Free sign-ups before Black Friday: 5 ideas for the Nov 16 batch (CMO, night of Nov 3-4)

Numbers: funnel.yml run 41778856341 (Nov 4, last 14 days, Oct 21 - Nov 3), cross-checked with run 41466393627 (Nov 2).
- 69 sign-ups in 14 days (~35 a week). Where they came from: email sheet after a Watch tap 23, shoe page 17, Google 12, homepage card 10, sale lists 6, "back in my size" 1. 164 real members.
- Homepage first visits: 2,930. 45% picked sizes, 33% clicked a store, 35 signed up (1.2%).
- Shoe page first visits: 1,376. 24% picked a size, 32% clicked a store, 5% went on to the homepage. Shoe-page landers come back 4% (everyone else 15%).
- Watch taps: 91 sessions in 14 days (about 3% of the 3,154 sessions with a deal click). About 1 in 5 turn into a sign-up, the best rate on the site.
- Search: 741 sessions, 1,222 searches, 12% found nothing. Top searches are shoe models: evo sl 20, alphafly 17, vomero 12, metaspeed 10, novablast 8, superblast 7 (superblast found nothing 3 times).
- By source: Google 850 first visits, 2% signed up, 27% came back. Reddit 427 first visits, 0.5% signed up.
- Live tests on sign-ups: namecard 1.1% vs 1.0%, p=0.87. watchsheet 1.1% vs 1.2%, p=0.91. alts B looked like a sign-up win on Nov 2 (p=0.034) but faded to p=0.215 by Nov 4. **Do not ship 'alts' on sign-ups.** Decide it Nov 8 on its own metric.
- Not proposed again (decisions.md): come-back sign-up bar, "Didn't buy it?" card, runcard, social-proof counts (164 is too small: a low number reads as "nobody uses this").

## Before the batch (no build, or minutes of build)

**A. Who sees the founding card, Nov 17-30. This is the biggest number in play.**
The approved screen 1 puts the founding card in the homepage sign-up slot and on the Black Friday pages, for everyone.
- That slot is our #2-4 sign-up source: card 10, Google 12 (mostly from the card), first visits 35 in 14 days.
- Showing a $36/year pitch to someone who has never used the site skips a rung of our own ladder (Visitor -> Member -> Pro, decided Oct 4). It also bets our steadiest free sign-up source on a card with zero data.
- NN/g: ask for commitment after people have seen the value, not before.
- **My pick:** members and returning visitors (visit 2+, as the original 'pro' card was set) see the founding card. First visits keep today's free card (namecard A/B continues).
- Cost: one condition, under 0.1 day. Bastien's call: yes/no.

**B. Fix two counters that hide sign-up spots (bug bucket, backend, ~30 min).**
1. The shoe page "Didn't buy it?" bar sends `shoe-backbar-view`, but funnel.py counts `watchbar-view`. The funnel says "shown 0" both weeks, so we can't judge a live sign-up spot.
2. The watchlist's "Email me when these drop" (#watchEmail) sends `watchlist-ask`, but the funnel counts only `drop-ask` ("asks 0").

Also add the spot to `watch-add` (backend already flagged this Oct 31). Without it, ideas 1 and 4 can't be measured by spot.

## The 5 ideas, ranked by expected sign-ups per hour of Bastien's time
Each costs Bastien about 10-15 minutes (one preview OK). So the ranking follows expected sign-ups, with backend days as the tie-break.

### #1 (MY PICK): Shoe pages: "♡ Watch this shoe in size X" right under the price line, watching in place
- **What, phone first:** a full-width charcoal button directly under "Your size 11: $X at Store" (or under the size picker when there's no size yet).
  - Tap = the shoe is watched right there (gf-watch; members watch_add). The page does not jump to /?watch= on the homepage, which is what the table's "♡ Watch the price" link does today.
  - Then a bottom sheet named for the shoe: "Email me when the Evo SL drops in size 11". It has the email field + "Continue with Google". If no size is known, the sheet shows fit + size chips first.
  - The existing #alertBox form stays as is lower on the page. One ask per page, as the ladder says.
  - This is the 'watchbtn' arm from the members-watching batch (Bastien OK'd it Nov 2, preview first). My additions: the sheet names the shoe and carries the size, and the test is judged on SIGN-UPS, not only watches.
- **Where:** every running model page: /shoes/, /chaussures/, /us/shoes/. Boot pages later.
- **Why:**
  - Our numbers: the Watch tap -> email sheet is our #1 source (23 of 69) at ~1 in 5. Shoe pages are our #2 source (17) and bring 1,376 first visits, but only 24% pick a size, and the box needs a size AND a typed email before it does anything.
  - Research: one small step first, then the ask. That's foot-in-the-door: Freedman & Fraser 1966, and Cialdini's commitment and consistency. Baymard: make the main action obvious on product pages.
- **Expected (estimate):** 5% of shoe-page first visits tap (vs ~3% on homepage cards; these visitors came for that shoe) x 1 in 5 give an email = ~14 more sign-ups per 14 days. That's about +7 a week, or +20% on today's total.
- **Cost:** ~1 backend day (partly built for the Nov 2 preview).
- **A/B:** arm 'watchbtn', 50/50 on shoe-page first visits.
  - Metric: shoe-page first visits that sign up. Baseline 1.24%. 1.24% -> 2.5% needs ~1,800 a group (80% power, 5% level).
  - At ~345 a group a week (more in BF week): **decide ~Dec 14, or earlier at p<0.05.**
  - Early read: first visits that watch OR sign up, 2% -> 4%, ~1,140 a group, ~Dec 7.
- **Conflicts:** none with the founding slot (it's not the homepage card). 'alts' runs on the same pages until Nov 8: start after it ends, or note the overlap (different metric, independent coins).
- **Stop rule:** by Nov 30 with 1,000+ per group, if B's sign-up rate is at or below A's, remove it.

### #2: The existing Black Friday sign-up box on the pages that have none, Nov 16-30
- **What:** reuse the qs_box with the bfCta copy that's already live on /black-friday/ ("Get the Black Friday deals in your size. ... Our Friday email lands on Black Friday morning..."). It's true: Nov 27 is a Friday and the emailday test ends Nov 21. Put it on:
  - /black-friday/live/ + /vendredi-fou/direct/, after the first list. Today there's no sign-up at all, and it's the page we pitch to press.
  - the 3 gift pages, after the $25 block.
  - brand pages: CA EN/FR + US, no box today; Google ~pos 7 for asics.
  - plus one link line on model pages (seo-lead's #2 line), with no second form on model pages.
  - Dec 1-31 (Canada): bdCta Boxing Day copy.
- **Why:** sale lists bring 6 sign-ups in 14 days with the same box. Seasonal intent peaks Nov 20-30. These pages are where Google and press traffic will land (seo-audit #1-#3 point links at them). Precedent: "Back in my size" (Oct 27) shipped with no A/B because A = no box at all.
- **Expected (estimate, low confidence):** +5-15 sign-ups Nov 16-30, mostly BF week. Depends on whether the SEO links and press land.
- **Cost:** ~0.5 day (function + date window exist). Copy already public; compliance re-check is light.
- **Measure:** sign-ups by ref (bf-live, gifts, brand). No A/B: A = nothing.
- **Conflict:** the founding card is planned for the BF pages. Same split as A: members/returning visitors see the founding card, first visits see this box.
- **Stop:** under 3 sign-ups across these pages by Dec 1 = don't carry it into Boxing Day.

### #3: Move the list-page box up: after the first 8 cards, not after 80
- **What:** on /running-shoes-sale/* and the size pages, qs_box today sits after the full list (`after=` 80 cards). Show it after card 8, as the homepage does after its first block. Same copy, same form.
- **Why:** NN/g scrolling research: most viewing time goes to the first screenfuls and drops steeply after. A box after 80 cards is seen by almost nobody, yet it still brings 6 sign-ups in 14 days.
- **Expected (estimate):** 1.5-2x on those pages = +3-6 per 14 days.
- **Cost:** ~0.25 day.
- **A/B:** arm 'qsup'. Metric: list-page sessions that sign up. Too few to prove before Jan (~6 a fortnight).
  - Decide Jan 11, or at p<0.05.
  - **Stop rule:** remove early if B's store clicks per session fall 5+ points with 300+ per group (the box must not push deals down).
- **Conflict:** none.

### #4: Search for a shoe -> "♡ Watch the [model] in your size"
- **What:** when a search matches one shoe page (same rule as search_check.py), one line on top of the results: "♡ Watch the Evo SL in size 11 · Email me when it drops". It watches the page key `page|<slug>` (alerts.py already sends for any shoe on that page in their size, both sides), then opens the email sheet (watchsheet arm as assigned).
  - The same line replaces the dead end in searchHelp's "Nothing in your size for X right now".
- **Why:**
  - 741 search sessions in 14 days; the top searches are models people want (alphafly 17, metaspeed 10, superblast with nothing in size).
  - Searchers came back 22% vs 11%.
  - Baymard: a no-results or not-in-stock page should offer the next step (a "notify me"), not a dead end.
- **Expected (estimate):** ~250 model-search sessions x 8% tap x 1 in 5 = +3-5 per 14 days, plus more members watching (the Pro audience).
- **Cost:** 1-1.5 days.
- **A/B:** arm 'swatch'. Metric: search sessions that sign up or watch. Baseline is unknown (no spot on watch-add yet, see B). 3% -> 5% needs ~1,500 a group = slow.
  - Directional read Dec 14, decision Jan 11.
- **Conflict:** popq (search box) has a different metric; independent coins. Not in the homepage card slot.
- **Stop:** under 2% of model-search sessions tap it by Dec 14 = remove.

### #5: "Continue with Google" on every static-page box (shoe pages, list/BF/brand boxes, race boxes)
- **What:** the Google button above the email field, as the homepage card has since Oct 29.
- **Why:** Google brings 12 of 69 sign-ups from the one place it exists. Typing an email on a phone is the step people drop (Baymard mobile form research).
- **Expected (estimate):** +15-30% on static-page box sign-ups = +3-5 per 14 days.
- **Cost:** ~1 day (the Google script + google_* calls on static pages).
- **Measure:** no separate A/B; it overlaps #1-#3 on the same pages and Google-first already shipped without one. Watch the share of static-page sign-ups via Google, and total static-page sign-ups per 100 sessions before/after.
- **Stop:** total sign-ups per 100 sessions on those pages lower 2 weeks after vs 2 weeks before = remove.
- If the batch must shrink, fold it into #1's sheet only.

## What to measure (Monday check-in)
- Sign-ups per week by `where`: email|sheet, shoe-page, watchbtn, bf-live, gifts, brand, size-page, search-watch, google-static. Baseline ~35 a week.
- Homepage first-visit sign-up rate during Nov 17-30. It must stay at ~1.2% if A (founding card only for members/returning visitors) is a yes.
- Founding-list joins by spot (separate from free sign-ups).

## Stop rule for the whole batch
If total weekly sign-ups for Nov 23-29 (BF week, the most traffic we'll see) are not above 45, the batch isn't working:
- remove the ideas with no sign-ups of their own;
- spend December's batch on SEO links only (seo-audit #1, #2, #4).
