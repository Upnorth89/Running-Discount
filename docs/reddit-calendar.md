# Reddit rolling calendar (Oct 19, 2026; Bastien: "a rolling weekly calendar ... rotate 1 post per sub per week roughly")

Three posts a week (Mon / Wed / Fri, 7am Vancouver), on a 4-week loop. Each sub sees us every 4 weeks, except
r/RunningDeals (a deals sub: weekly is normal there, and our Oct 18 post stayed up). Weekly in every sub reads as
advertising: r/BuyCanadian removed a 3-item post (Oct 17) and Reddit's spam filter removed a 20-link post (Oct 12).

Claude sends the ready post at 6:30am (scheduled task "Reddit rotation"): `tools/reddit_post.py` with the line's options,
every link opened on the live site first, the copy page + the Markdown block. Bastien posts, then says "posted" (or "skipped").

| Week | Monday | Wednesday | Friday |
|------|--------|-----------|--------|
| A | r/RunningDeals (`--side both --direct`) | r/runTO (`--toronto`, mod-approved) | r/trailrunning (`--kind trail`) |
| B | r/RunningDeals | r/runninglifestyle | r/xxrunning (`--sex women`, check rules) |
| C | r/RunningDeals | r/RunVancouver (`--city vancouver`) | r/ultrarunning (`--kind trail`, his own story first) |
| D | r/RunningDeals | r/runningmontreal (`--city montreal`, FR + EN) | r/FrugalMaleFashionCDN (`--side ca --sex men`, check rules) |

Weeks: B = the week of Mon Oct 19, 2026, then C (Oct 26), D (Nov 2), A (Nov 9), B (Nov 16)… (week letter = A + ((Monday - Nov 9) / 7) mod 4). This week skips Monday (r/RunningDeals was posted Oct 18). Black Friday week (Nov 23-30): every post points to /black-friday/ (US /us/black-friday/).

Never: r/BuyCanadian (removed us), r/RunningShoeGeeks (no self-promotion), the same items twice in a sub (`--exclude`).
Every 4 weeks: drop a sub that brought no visitors (funnel.yml first visits by ?ref=reddit-<sub>), try a new one in its slot.

## Log (newest first)
| Date | Sub | Posted? | Visits from it (7 days) |
|------|-----|---------|-------------------------|
| Oct 26 | r/RunningDeals (10 CA + 10 US shoes, shoe page links only; ?ref=reddit-runningdeals) | waiting | |
| Oct 23 | r/trailrunning (race gear lists hub, link /us/races/?ref=reddit-trailrunning) | yes | |
| Oct 23 | r/xxrunning (6 shoes + 4 gear, women's, CA + US; ?ref=reddit-xxrunning) | yes | |
| Oct 21 | r/runninglifestyle (6 shoes + 4 gear, CA + US; ?ref=reddit-runninglifestyle) | waiting | |
| Oct 18 | r/RunningDeals (3 CA + 3 US) | yes, stayed up | |
| Oct 18 | r/RunVancouver + r/runningmontreal (fall/winter) | yes | |
| Oct 17 | r/BuyCanadian | removed by mods | |
| Oct 17 | r/runTO | yes | |
