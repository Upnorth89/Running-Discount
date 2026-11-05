# Reddit rolling calendar (Oct 19, 2026; Bastien: "a rolling weekly calendar ... rotate 1 post per sub per week roughly")

Three posts a week (Mon / Wed / Fri, 7am Vancouver), on a 4-week loop. Each sub sees us every 4 weeks, except
r/RunningDeals (a deals sub: weekly is normal there, and our Oct 18 post stayed up). Weekly in every sub reads as
advertising: r/BuyCanadian removed a 3-item post (Oct 17) and Reddit's spam filter removed a 20-link post (Oct 12).

Claude sends the ready post at 6:30am (scheduled task "Reddit rotation"): `tools/reddit_post.py` with the line's options,
every link opened on the live site first, the copy page + the Markdown block. Bastien posts, then says "posted" (or "skipped").

| Week | Monday | Wednesday | Friday |
|------|--------|-----------|--------|
| A | r/RunningDeals (`--side both --direct`) | r/runTO (`--toronto`, mod-approved) | (open: r/trailrunning dropped Oct 29, pick a new sub) |
| B | r/RunningDeals | r/runninglifestyle | r/xxrunning (`--sex women`, check rules) |
| C | r/RunningDeals | r/RunVancouver (`--city vancouver`) | (r/ultrarunning dropped Nov 4: no traction; slot open) |
| D | r/RunningDeals | r/runningmontreal (`--city montreal`, FR + EN) | r/FrugalMaleFashionCDN (`--side ca --sex men`, check rules) |

Weeks: B = the week of Mon Oct 19, 2026, then C (Oct 26), D (Nov 2), A (Nov 9), B (Nov 16)… (week letter = A + ((Monday - Nov 9) / 7) mod 4). This week skips Monday (r/RunningDeals was posted Oct 18). Black Friday week (Nov 23-30): every post points to /black-friday/ (US /us/black-friday/).

**Common sizes only (Nov 5, Bastien: "dont give me shoes that would be on sale for sizes that arent common. this hurts the brand"; "i just dont want people to end up on a sold out shoe"):** a shoe line needs 3+ common sizes (men's 8-11.5, women's 6.5-9) at the shown price, each confirmed in stock on the store's page the day of the post, and 5+ live sizes in all. Spec sent to backend for reddit_post/post_check/social picks.

Never: r/BuyCanadian (removed us), r/trailrunning (Oct 23: 24 first visits, 0 sign-ups; Oct 29 skipped, only 1 US trail shoe passed the line check), r/RunningShoeGeeks (no self-promotion), the same items twice in a sub (`--exclude`).
Every 4 weeks: drop a sub that brought no visitors (funnel.yml first visits by ?ref=reddit-<sub>), try a new one in its slot.

Nov 4 r/ultrarunning: use the drafted gear-list post in docs/reddit-drafts/ultrarunning-nov4.md (Bastien, Oct 29: "not a shoe list").

## Log (newest first)
| Date | Sub | Posted? | Visits from it (7 days) |
|------|-----|---------|-------------------------|
| Nov 5 | r/RunningDeals weekly (10 CA + 9 US shoes, sorted by % off, shoe page links only, CAD/USD headers; social-producer + cmo reviewed; post_check all match; ?ref=reddit-runningdeals) | waiting | |
| Nov 4 | r/ultrarunning (5 CA + 5 US trail shoes, shoe page links only, + race gear lists line /races/?ref=reddit-ultra; Hoka Rocket X left out: failed post_check; ?ref=reddit-ultrarunning) | skipped (Bastien, Nov 4: "There's no traction there"). Dropped from the rotation | |
| Nov 2 | r/RunningDeals (week D Monday: 8 CA + 8 US shoes, shoe page links only; Hoka Rocket X left out: failed post_check; ?ref=reddit-runningdeals) | not posted (Bastien, Nov 5) | |
| Oct 30 | r/ultrarunning (week C Friday slot) | skipped: moved to Nov 4, the drafted gear-list post (Bastien, Oct 29: "not a shoe list") | |
| Oct 29 | r/trailrunning (9 CA + 1 US trail shoes) | skipped (Bastien: not with one US shoe; the sub "wasn't a big hit") | |
| Oct 28 | r/RunningDeals midweek (8 CA + 7 US shoes, none from Oct 26, shoe page links only; ?ref=reddit-runningdeals-wed) | yes (6 lines had wrong math; corrected body sent Oct 28) | 96 first visits on Oct 28 |
| Oct 26 | r/RunningDeals (10 CA + 10 US shoes, shoe page links only; ?ref=reddit-runningdeals) | yes | 527 first visits, 1 sign-up (funnel Oct 21-28) |
| Oct 23 | r/trailrunning (race gear lists hub, link /us/races/?ref=reddit-trailrunning) | yes | 24 first visits, 0 sign-ups |
| Oct 23 | r/xxrunning (6 shoes + 4 gear, women's, CA + US; ?ref=reddit-xxrunning) | yes | |
| Oct 21 | r/runninglifestyle (6 shoes + 4 gear, CA + US; ?ref=reddit-runninglifestyle) | waiting | |
| Oct 18 | r/RunningDeals (3 CA + 3 US) | yes, stayed up | |
| Oct 18 | r/RunVancouver + r/runningmontreal (fall/winter) | yes | |
| Oct 17 | r/BuyCanadian | removed by mods | |
| Oct 17 | r/runTO | yes | |
