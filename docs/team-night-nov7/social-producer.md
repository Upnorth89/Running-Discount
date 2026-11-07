# Social calendar, Nov 9 - Dec 1, 2026 (social-producer, team night Nov 7)
Draft for the growth chat. Nothing posted. Every piece still goes social-producer + cmo, designer (visuals), compliance (words) before Bastien.
This is the one-line-per-day view. It does NOT re-draft the founding-list pieces: those stay as written in docs/fox-pro/launch-social-kit.md
(Nov 17 Reel + 2 Stories, Nov 24 repost) and docs/content-calendar-nov4.md (founding Stories, Dec 2 Founder Reel). Here they are only placed.

## What changed since the Nov 4 calendar (newer rules win)
1. **Instagram is English only** (Bastien, Nov 5): no FR Reels/captions on Instagram. FR stays on the site/emails.
2. **No website screen recordings in hand-made videos** (Bastien, Nov 5: "I don't want people to just see the website"). The Nov 4 calendar's
   Sinister collab Reel and Nov 25 BF Reel were site recordings: both move to format 2b/2c cards (docs/social-formats.md). The automatic
   Wednesday kit Reel (format 4) is the only site recording left; team pick: post its **Top-5 Story only**, not the screen Reel (2 hand-made
   Reels a week is already his budget).
3. **Super Shoe Sunday is weekly** (Bastien's series): Nov 15, 22, 29 added (Nov 8 = docs/super-shoe-sunday-nov8.md).
4. **Nov 17 clash**: launch kit puts the Fox Pro "I bought it" Reel on Tue Nov 17; the Nov 4 calendar put the Sinister collab there. Kirsti
   hasn't confirmed (growth-handoff: nudge Nov 10). Team pick: **Fox Pro Reel keeps Nov 17; Sinister collab Thu Nov 19** (or the date she gives).
5. Reddit: r/ultrarunning (Nov 4) and r/trailrunning (Oct 29) dropped; week A + C Friday slots open. Nov 5 format rule (title + Canada (CAD) /
   USA (USD), name = only link, no footer) is newer than the calendar's "every BF-week post points to /black-friday/": BF-week posts stay shoe
   lines only, refs get `-bf`; the BF page is NOT added as a footer (ask below).
6. Ref fix: founding Stories use `ig-story-pro` (launch kit, newer) not `ig-story-founding`.
7. Bluesky/Pinterest refs are per rotation: `bluesky-shoes` / `bluesky-<cat>`, `pinterest-shoes` / `pinterest-<cat>` (not bare `pinterest`).

## Numbers we can use (read Nov 7 night; recompute the morning of, never reuse)
- sale.json updated 2026-11-07 01:10 UTC: n_stores = 153 ("150+ stores").
- /black-friday/live/ (updated Nov 6): 379 real drops this week, 80% of sale prices already this low 2 weeks ago, 8,083 sale items checked,
  "83 stores" (Canada). Quote only as "of the sale prices we track in Canada, X% were already this low 2 weeks ago".
- **Nov 8 Super Shoe Sunday, row 2 (NB FuelCell Rebel v5, JD Sports, $70)**: livecheck False tonight (also False at $90; BF live page shows
  $90 since Nov 5). Expect to swap in the backup (Nike Structure 26, BlackToe) Sunday morning after the normal check.
- Pages checked 200 tonight: /black-friday/live/, /black-friday/, /us/black-friday/, /gifts-for-runners/, /us/gifts-for-runners/,
  /boxing-day/, /races/sinister-7/, /pins/ca.xml, /pins/us.xml.

## Every day, automatic (0 min, not repeated below)
- **Bluesky** 8:21am Vancouver (social.yml): 2 shoes + 1 rotating category (real drops, livechecked by the job, shoe page or ?q= link).
  Refs bluesky-shoes / bluesky-<cat>. **Nov 17 stop rule**: rotating refs with 0 sign-ups vs shoe refs -> shoes only.
- **Pinterest** ca.xml + us.xml (refresh.yml, morning): 5 real drops per side, livechecked, shoe page links. Refs pinterest-shoes / pinterest-<cat>.
  Stop rule: < 30 first visits with ?ref=pinterest* by mid-Dec = off.
- Data sources these use: hist/prices.jsonl real drops (a week ago vs today, 10% or $10, >= $5, 5+ sizes) + livecheck.

## Day by day (LC = livecheck on the store's own page THAT MORNING, right country/currency; min = Bastien's minutes)
| Date | Channel · piece · format | Data source | Link + ?ref | LC same morning | Min |
|---|---|---|---|---|---|
| Mon Nov 9 | Reddit r/RunningDeals (week A, `--side both --direct --pages-only`, `--exclude` the Nov 5 models) · IG bio still ig-sss-nov8 until tonight | real drops + live shoe pages; post_check "all lines match" | shoe pages ?ref=reddit-runningdeals | YES (every line, every common size) | 5 |
| Tue Nov 10 | IG bio -> /black-friday/ · Bluesky/Pinterest auto | - | https://thegearfox.com/black-friday/?ref=ig-bio | no | 1 |
| Wed Nov 11 | Reddit r/runTO (week A, `--toronto`, `store_band`), post after 11:00 local (Remembrance Day) · Wednesday kit email arrives (auto) | real drops at Toronto stores | shoe pages ?ref=reddit-runto | YES | 5 |
| Thu Nov 12 | IG Story: Wednesday kit's Top-5 graphic (no screen Reel, see change 2) | ig_brief picks (livechecked Wed) | sticker = top shoe's page ?ref=ig-story-top5 | YES (re-check the 5 Thursday; drop any False) | 3 |
| Fri Nov 13 | Reddit week A Friday slot: EMPTY on purpose (no tested sub) · Friday email (auto) | - | - | no | 0 |
| Sat Nov 14 | nothing | - | - | no | 0 |
| Sun Nov 15 | **IG Reel: Super Shoe Sunday #N** (format 1 + green screen; 6 rows, 3 CA + 3 US, one per brand) + **IG Story: gift page** (menu item opens today) | SSS: hist real drops + post_check (Nov 8 method). Gift: gift_pages.py picks (8 sale + 4 full price per budget) | Reel: bio -> https://thegearfox.com/?ref=ig-sss-nov15 (Nov 15-16). Gift Story: /gifts-for-runners/?ref=ig-story-gifts | YES (6 rows + backups; 1 gift price if shown) | 20 |
| Mon Nov 16 | Reddit r/RunningDeals (week B, `--exclude` Nov 9) · Fox Pro preview (not content) · bio swap to founding landing ONLY when backend confirms it shows the approved card | real drops | ?ref=reddit-runningdeals | YES | 5 |
| Tue Nov 17 | **IG Reel "I bought it" + 2 Stories** = launch kit section 1-2, as written (gates: Nov 16 OK, a qualifying example) · Bluesky rotation decision | launch kit procedure (price-adjust table, history D0, livecheck) | bio ?ref=ig-reel-ibought; Story frame 2 ?ref=ig-story-pro | YES (the example item, men's 11 in stock, CAD) | 20 |
| Wed Nov 18 | Reddit r/runninglifestyle (week B; its Oct 21 draft is still "waiting": ask if it went up, else first post there) · Wednesday kit email (auto) | real drops | ?ref=reddit-runninglifestyle | YES | 5 |
| Thu Nov 19 | **IG Collab post with Sinister Sports** IF Kirsti confirms (else her date): still card in the 2c sticker style, no site footage; facts = the race's own suggested list (no prices on the card) · Top-5 Story from the kit | race page lines (re-read on sinistersports.ca rules_gear that week) | bio /races/sinister-7/?ref=ig-sinister | only if a price appears (team pick: none) | 10 (+3 Story) |
| Fri Nov 20 | Reddit r/xxrunning (week B, `--sex women`, rules re-read) · IG Story: BF deal-check page (deal mode from today) · Friday email (auto; Sat for 'emailday' B) | bf_live.py lists (real drops / not new / went up) | Reddit women's shoe pages ?ref=reddit-xxrunning · Story /black-friday/live/?ref=ig-story-bflive | YES (Reddit lines; any price visible in the Story screenshot) | 8 |
| Sat Nov 21 | nothing (Bastien answers Friday-email replies: members' time, not social) | - | - | no | 0 |
| Sun Nov 22 | **IG Reel: Super Shoe Sunday, Black Friday week** (format 1; only rows that are bf_live "real drops this week") | hist real drops + bf_live rule | Story stickers per country: /running-shoes-sale/?ref=ig-sss-nov22 + /us/running-shoes-sale/?ref=ig-sss-nov22 (bio stays on the founding landing) | YES | 20 |
| Mon Nov 23 | Reddit r/RunningDeals BF edition (week C; title may carry the % stat recomputed that morning; lines = real drops in the last 7 days) | prices.jsonl + bf_live rule + post_check | ?ref=reddit-runningdeals-bf | YES | 5 |
| Tue Nov 24 | IG Story: repost of the Nov 17 Story frames with a fresh example ONLY if one qualifies (launch kit 2) · press BF report Story only if partnerships published it | launch kit procedure / report_page.py | ?ref=ig-story-pro / ?ref=ig-story-report | YES (new example) | 3 |
| Wed Nov 25 | **IG Reel "Is this Black Friday price new?"** (format 2b TALK card, title "LOWEST WE'VE SEEN IN N DAYS" = the site's stamp rule, a fact) + Reddit r/RunVancouver (week C, `--city vancouver`) · readiness decision (not content) | one bf_live real drop (history line: "$A until <date>, $B today") + the % stat recomputed | Reel bio/Story /black-friday/live/?ref=ig-reel-bf · Reddit ?ref=reddit-runvancouver-bf | YES (Reel item + every Reddit line) | 20 (15 + 5) |
| Thu Nov 26 | nothing (US Thanksgiving) · Top-5 kit Story optional | - | - | if posted | 0-3 |
| Fri Nov 27 BF | Friday email (auto, all) · IG Story x2: morning "BF deal check updated" + evening founding Story (Nov 4 calendar wording, compliance-approved; no timer) · Reddit week C Friday slot: team pick EMPTY (see ask 2) | bf_live page | ?ref=ig-story-bf · ?ref=ig-story-pro | YES if a price is shown | 4 |
| Sat Nov 28 | nothing | - | - | no | 0 |
| Sun Nov 29 | **IG Reel: Super Shoe Sunday, Cyber Monday eve** (format 1, drops since Nov 23 only) + founding Story (Nov 4 calendar wording; the list's last day is Nov 30) | hist real drops + post_check | Story stickers ?ref=ig-sss-nov29 (per country) · ?ref=ig-story-pro | YES | 20 |
| Mon Nov 30 CM | Reddit r/RunningDeals Cyber Monday (week D; real drops since Fri only; skip if under 5 lines pass) · founding list count (growth-analyst) | prices.jsonl + post_check | ?ref=reddit-runningdeals-cm | YES | 5 |
| Tue Dec 1 | Claude: picks + livechecks the Dec 2 Founder Reel's drop, sends the filled script (content-calendar-nov4); no post | that morning's history | ?ref=ig-reel-founder (Dec 2) | YES (Dec 1, again Dec 2) | 0 |

Bastien's total Nov 9 - Dec 1: ~162 min over 23 days (~7/day); Reel days at 20 max (Nov 15, 17, 22, 25, 29). SSS days assume Claude hands him
the 6 rows, photos, captions and the rendered base video, and he only records the green screen + posts. If he still builds the base video himself,
SSS days go over 20: then a format-1 HTML template (like docs/formats/one-item-guess-the-price.html) is the fix (team job, docs only).

## Livecheck rule for every "YES" above
`scraper/livecheck.py still_on_sale(url, price, variant, us=<US side>)` the same morning; only True ships (None/blocked = left out: MEC, REI,
Decathlon, Sporting Life, Backcountry rows never in hand-made pieces). Reddit: reddit_post.py + tools/post_check.py "all lines match", 3+ common
sizes (men's 8-11.5 / women's 6.5-9) each confirmed. Demo = men's 11 / M only when the piece says "my size".
Caption footer on every price piece: "Prices can change: check the store before you buy."

## What to measure (funnel.yml by ref; Monday check-ins Nov 16, 23, 30)
| Ref | Measure | Keep / stop |
|---|---|---|
| ig-sss-nov15 / -nov22 / -nov29 | first visits, % pick sizes, store clicks, sign-ups; IG views, 3-s hold, saves, shares, guess comments | IG piece needs >= 1 sign-up per 50 first visits (calendar rule) |
| ig-reel-ibought, ig-story-pro | pro-join, first visits | launch kit: < 3 list joins by Nov 30 = don't remake for Dec 4 |
| ig-reel-bf, ig-story-bflive, ig-story-bf | first visits, % going on to a shoe page, sign-ups | compare with SSS refs |
| ig-story-gifts, ig-story-top5 | link taps, first visits, sign-ups | 0 sign-ups by Nov 30 = drop that Story type |
| ig-sinister | first visits, list ticks, reminder sign-ups; does sinistersports.ca link us (Search Console) | the backlink is the real goal |
| reddit-<sub>(-bf/-cm) | first visits + sign-ups per post | 0 visitors = drop the sub (calendar rule) |
| bluesky-shoes vs bluesky-<cat> | first visits, sign-ups | Nov 17 decision |
| pinterest-shoes / pinterest-<cat> | first visits | < 30 by mid-Dec = off |

## Asks for the growth chat / Bastien (yes/no)
1. Wednesday kit: Top-5 Story only, no screen-recording Reel (his Nov 5 "no website" rule)? Team pick: yes.
2. BF day Fri Nov 27: leave the Reddit slot empty (team pick; r/RunningDeals already gets Nov 23 + Nov 30), or a 3rd RunningDeals post that week?
3. BF-week Reddit: keep the Nov 5 no-footer format (team pick) vs the calendar's "point to /black-friday/" line?
4. Super Shoe Sunday: who builds the base video, and how many minutes does it take him today?
