# Members lead, night of Nov 7: the Friday emails Nov 13, Nov 20 (+ Sat 21), Nov 27
Drafts and plan only. Nothing sent, no code changed, not committed. Builds on docs/members-night-nov5.md (watch-one box, BF-week copy) and docs/founding-ask-copy-nov5.md (founding box); doesn't repeat their copy.

## What the code already does (scraper/weekly_email.py, read Nov 7)
- Order today: intro, then `first_note` (first email only) + founding box + watch-one box stacked, then watchlist news, "Dropped this week in your size", 4 per category, "Hit reply", footer (unsubscribe, privacy, mailing address).
- Watch-one box: built, starts Nov 13 (`WATCH1_FROM`), members with no watch only, `em=friday-watch` / `saturday-watch`. No end date or off switch.
- Founding box: built, OFF (`founding.FOUND_LIVE = False` until Bastien's Nov 16 OK), `BOX_DAYS` Nov 20, 21, 27; Nov 27 shows "You're on the list" to people on it; `FOUND_READY = False` gives the January line.
- Funnel already counts `email-friday*` by prefix, so `-watch` / `-pro` visits stay in the emailday test.
- NOT built: Black Friday subject lines, BF first lines, the deal-check link. No gift link anywhere in the email.

## The one rule across all three: one new thing per email
The subject sells the deals (that's what people signed up for). Each week adds ONE new box, never two new asks at once. Why: the email brought 16 Friday + 11 Saturday visits in 14 days (funnel Nov 4) vs 18 from alerts that name the member's own items; the Friday email works when it is about their sizes, not about us. NN/g: newsletter readers scan the first screen and act on what comes first.

## Fri Nov 13 (B group Sat Nov 14)
- **Subject (no change):** watchlist news wins, else the drop pattern.
  EN: "{Brand Model} dropped ${m} in your size, + {k} more this week" · FR « {Modèle} : −{m} à votre taille, + {k} autres baisses cette semaine »
- **Order:** intro > watch-one box (0-watchers only) > watchlist news (watchers) > Dropped this week > categories > Hit reply > footer.
- **New:** the watch-one box (~116 members who watch nothing). Watchers see the usual email.
- **Don't add:** any Fox Pro teaser or "something's coming" line. The list opens Nov 17; a teaser now would be a second ask in the same email as watch-one, and would blur the watch-one read.
- **Metric + check:** WATCHLIST SIZE "0:" share (baseline Nov 4: 116 of 165 = 70%) and friday-watch/saturday-watch visits. Read Mon Nov 16. Safe Links count (mail_check) the same day: if Microsoft shows watches made within 5 min of the send, set `MS_AUTOWATCH = False` before Nov 20.

## Fri Nov 20 (B group Sat Nov 21, last test Saturday)
- **Subject (no change):** same drop pattern. No "Fox Pro" or "founding" in the subject: the drop is the reason to open, and a sales subject on a deals email reads as a bait-and-switch.
- **Order (my pick, needs a small code change):** intro > watch-one box (0-watchers) > watchlist news > Dropped this week > **founding box** > categories > Hit reply > footer.
  Why move it below the drops: today the founding card (the tall designed card) and the watch-one box stack above the first deal, so a 0-watcher scrolls past two asks before the drop the subject promised. Below the drops it is still in the top half, next to proof of what we do (Cialdini: the ask lands after the value is shown).
- **New:** the founding list box, first time (copy: docs/founding-ask-copy-nov5.md section 1, Bastien's card A). Only if Bastien OKs FOUND_LIVE on Nov 16.
- **Don't add:** a Black Friday preview, "get ready" or BF page link. That's next week's reason to open; using it now spends it and stacks a third link.
- **Metrics + checks:**
  - Founding joins from `email-friday-pro` / `email-saturday-pro` (my estimate 8-12); team stop rule: < 25 on the list in total by Tue Nov 24.
  - Watch-one stop rule, Mon Nov 23 (docs/members-night-nov5.md: keep if 8+ of the 116 watch via the box or 0-watch share -5 pts; remove if < 3 -watch visits, any complaint, 2+ unsubscribes in a send).
  - emailday test ends Nov 21: read Mon Nov 23 (Fri vs Sat visits per send; ~40 a group x 4 sends, so only a big gap counts; say "no difference" if p >= 0.05 and go Friday for all, as already planned).
  - Volume: Nov 20/21 sit at ~105-125 emails a day (docs/bf-email-volume-nov6.md): Resend Pro must be live by Thu Nov 19.

## Fri Nov 27, Black Friday (Friday for everyone, the only email that week)
- **Subject:** the BF-week variants in docs/members-night-nov5.md (compliance OK with its fix):
  - watchlist news: EN "Black Friday week: your watchlist moved, plus {n} deals in your size" / FR « Semaine du Vendredi fou : vos favoris ont bougé, et {n} aubaines à votre taille »
  - a drop: EN "Black Friday week: {name} dropped {m} in your size, + {k} more" / FR « Semaine du Vendredi fou : {name} −{m} à votre taille, + {k} autres baisses »
  - no drop: EN "Black Friday week: {n} deals in your size" / FR « Semaine du Vendredi fou : {n} aubaines à votre taille » ("up to {top}%" only if that item is in that email in their size)
- **Order:** intro (BF first line, states our own 10%/$10 rule, never "real drop") + one line to the deal check > watchlist news > Dropped this week > founding box (join; or the one-line "You're on the founding list. Your link arrives Wednesday, Dec 2.", no button) > categories > Hit reply > footer. Watch-one box only if it passed the Nov 23 stop rule.
- **Deal-check link:** Canada EN /black-friday/live/, FR /vendredi-fou/direct/; US /us/black-friday/ with the compliance-fixed line ("compares today's sale prices with the last two weeks"). Tag it `&em=friday-bf` (11 letters) so its clicks are counted apart from the deals.
- **New:** the deal check (the one thing no store email gives them: which BF prices actually moved this week). For people on the list: their Dec 2 date.
- **Don't add:** the gift page. A third link in the busiest email of the year; and no "ends soon", countdown, "lowest ever", second Saturday send or Cyber Monday email (one email a week rule). Gift page goes in the Dec 11 email instead (Dec 4 = the launch email), with the Boxing Day page.
- **Metrics + check Mon Nov 30:** email-friday sessions per email sent (vs Nov 20), friday-bf clicks, founding joins from friday-pro, unsubscribes (<= 1 is normal), complaints 0, bounces < 4% (mail_health). ~240 emails that day: Resend Pro needed.
- **Readiness:** the Nov 27 box reads `FOUND_READY`. First sends start ~10-12 UTC (Atlantic/Eastern 7am), so the readiness call must be made by the evening of Thu Nov 26, not the morning of.

## Needs backend code (send as specs after Bastien's yes)
1. **BF-week subjects + first line + deal-check line** (CA EN/FR, US line, `em=friday-bf`), only on Nov 27 (date-gated). Copy: docs/members-night-nov5.md "Black Friday week email". Bastien's yes is not on record in docs/decisions.md (Nov 5 ask 2): ask him.
2. **Move the founding box below "Dropped this week"** (today it's stacked with first_note + watch-one above the deals). Small: render it as a section after the drops instead of adding it to `first_note`. The Nov 27 "You're on the list" line can stay at the top (one short line).
3. **Watch-one off switch:** a `WATCH1_TO` date (or flag) so the Nov 23 stop rule can remove it before Nov 27 with a one-line change.
4. Optional BF fact line (Canada only, from the same morning's bf_stats the page shows): build only if it's the same number; else skip.

## Asks for Bastien (one line each)
1. BF-week subject + first lines + deal-check link for Nov 27 (copy in docs/members-night-nov5.md)? yes/no
2. Founding box below the week's drops instead of on top, Nov 20 + 27? yes/no
3. Gift page waits for the Dec 11 email (not Nov 27)? yes/no
