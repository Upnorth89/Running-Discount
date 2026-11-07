# Content calendar, Nov 10 - Dec 6, 2026: sign-ups + the Fox Pro founding list
Social producer, night of Nov 4. Draft for the growth chat. Nothing posted or sent. Every public piece goes through compliance
(and every visual through the designer) before Bastien posts it.

## The frame (what this rests on)
- Timeline: freeze ends Nov 15 / Fox Pro preview Nov 16 / **Sinister Sports collab post Tue Nov 17** / **founding list Nov 17-30** /
  BF pages switch to deal mode Nov 20 / **Black Friday Fri Nov 27**, Cyber Monday Nov 30 / readiness decision (ask: Wed Nov 25, see members plan) /
  **founding round Wed Dec 2** (the list gets the link) / **public launch Fri Dec 4**.
- Already automatic (0 min of Bastien's time): Bluesky drop posts (8:21am Vancouver: 2 shoes + 1 rotating, ?ref=bluesky-shoes /
  bluesky-<cat>), Pinterest feeds ca + us (5 a day each, ?ref=pinterest), Wednesday Instagram kit (ig_brief.py at ~13:03 UTC: 3 picks,
  Top-5 graphic, reel-en.mp4 + reel-fr.mp4 of this week's real drops in men's 11 / M, already livechecked), Reddit draft at 6:30am
  Mon/Wed/Fri (reddit_post.py + post_check.py), Friday email (Saturday for the 'emailday' B group until Nov 21; Friday for all from Nov 27).
- Channel roles (from our numbers): Reddit = clicks, not sign-ups (705 first visits in 14 days, <1% signed up, Oct 24) -> shoe page
  links only, **never a Fox Pro pitch**. Shoe pages bring sign-ups via "Email me when it drops" (24 of 61 sign-ups, Oct 24) -> every
  social link goes to a shoe page or a BF/race page, never the bare homepage. Emails about chosen items bring ~5x the visits per send
  of the weekly email (members plan Nov 4) -> the founding list is filled mostly by email asks + the on-site card, not social.
  Instagram = Bastien's face + Québec audience (EN + FR every time).
- Rules carried into every piece: facts only (price, % off, sizes, store, dates from our own history); safe bands on every Reel
  (#17201C 218 px top, 400 px bottom of 1080x1920), payoff in the first second, captions on the site part only; demo = men's 11 / M
  ("my size"); every price re-checked on the store's page **the morning it's posted** (scraper/livecheck.py, CAD on Canada pieces,
  USD on US ones); Fox Pro wording exactly as approved: "$36/year for founding members (that's $3/month), price locked while you stay",
  100 numbered spots, 30-day full refund, "The store decides" on anything about price protection. Never $3/month as the headline,
  never "for life", no countdowns, no "spots left" unless it's the real live count.
- Bastien's time budget: <= 20 min a day. Totals below: ~155 min over 27 days (~6 min/day), max 20 (Nov 25, Dec 2).

## Real drops verified tonight (Nov 4) in hist/prices.jsonl + the live sale.json + the store's page
Read with `git show origin/history:prices.jsonl` (156,572 lines). Store page checked with livecheck.still_on_sale from the sandbox.
They are **examples for hooks and for the BF "is it real?" story; each must be re-checked the day it's used, or swapped for that
week's ig_reel / social_post picks**.

| Shoe (CA side) | History (best price, date it changed) | Today | Sizes at that price (live site) | Store page Nov 4 | Shoe page |
|---|---|---|---|---|---|
| Nike Vomero Plus RR - Men's | $225.00 from Oct 13 -> $159.99 on Oct 29 | $159.99, reg $225 (−29%) | 8, 9, 10.5, **11**, 11.5, 12, 13 (Foot Locker) | True | /shoes/nike-vomero-plus/ |
| On Cloudeclipse - Men's | $210.00 from Oct 10 -> $115.00 on Nov 3 | $115.00, reg $229.99 (−50%) | 7, 7.5, 11.5, 12, 13 (La Boutique du Lac) | True | /shoes/on-cloudeclipse/ |
| Salomon Aero Glide 3 - Men's | $157.50 Oct 2 -> $126.00 Oct 3 -> $84.00 Oct 31 | $84.00, reg $209.99 (−60%) | 10.5, 11.5, 12, 13 (La Boutique du Lac) | True | /shoes/salomon-aero-glide-3/ |
| On Cloudultra Pro - Women's | $329.99 from Oct 2 -> $229.95 on Nov 1 | $229.95, reg $329.99 (−30%) | 7, 7.5, 8, 8.5, 9 (Gord's Running Store) | True | /shoes/on-cloudultra-pro/ |
| Saucony Endorphin Speed 5 - Men's (the "not new" example) | $137.99 Oct 2 ... $119.99 since **Oct 12** | $119.99, reg $229.99 (−48%) | 13 sizes incl. 11 (SVP Sports) | True | /shoes/saucony-endorphin-speed-5/ |
| Hoka Zinal 3 - Men's | $174.95 from Oct 2 -> $109.94 on Nov 1 | $109.94 (−37%) | 9.5, 11, 11.5 (MEC) | **can't check (MEC blocks robots): don't feature** | /shoes/hoka-zinal-3/ |

The number for Black Friday posts (computed tonight, same method as the BF page's "already this low 2 weeks ago"):
of 9,061 Canadian sale items with 14+ days of history, **7,117 (78.5%) were already at today's price or lower 2 weeks ago**
(shoes: 1,770 of 2,123 = 83.4%). Recompute the morning it's used (it moves daily); quote it as "of the sale prices we track in
Canada, X% were already this low 2 weeks ago", never "most Black Friday deals are fake".
Store count on Nov 4: n_stores = 170 in sale.json ("170 stores"; re-read the day of).

## Links and refs (all checked 200 tonight unless marked)
| Piece | Link |
|---|---|
| IG bio Nov 10-16 | https://thegearfox.com/black-friday/?ref=ig-bio |
| IG bio Nov 17-Dec 1 | founding-list landing, **not built yet** (/pro/ = 404; the ?pro=1 card still shows the old $3/$29 vs $5/$49 test). Backend must point it at the approved screen 1 ($36/year) by Nov 16: `?pro=join&ref=ig-bio-founding`. Until then the bio stays on /black-friday/. |
| IG bio Dec 2-6 | the live /pro/ page (or checkout landing) ?ref=ig-bio-launch |
| Sinister collab | https://thegearfox.com/races/sinister-7/?ref=ig-sinister (FR /courses/sinister-7/?ref=ig-sinister) + hub /races/?ref=ig-sinister |
| BF pages | /black-friday/, /vendredi-fou/, /us/black-friday/, live check /black-friday/live/ + /vendredi-fou/direct/ |
| Gifts | /gifts-for-runners/, /cadeaux-coureurs/, /us/gifts-for-runners/ |
| Reddit | shoe pages only, ?ref=reddit-<sub> (+ -bf in BF week) |
| Story stickers | ?ref=ig-story-<topic> (one per Story, listed per day) |

## Day by day
Format: **Channel** · piece (hook EN / FR) · data · link + ref · who makes it · Bastien minutes.
"Auto" days for Bluesky + Pinterest run every day and aren't repeated below (0 min).

### Week A (Reddit week A started Mon Nov 9: r/RunningDeals that day is outside this window, drafted as usual)
**Tue Nov 10** · nothing new (Bluesky + Pinterest auto) · 0 min

**Wed Nov 11 (Remembrance Day)** · Reddit r/runTO (week A Wednesday, `--toronto`, `store_band`, mod-approved) · shoe pages
?ref=reddit-runto · Claude drafts 6:30am, Bastien pastes after 11:00 local (not during the silence) · **5 min**
· The Wednesday kit email arrives today; the Reel waits until tomorrow (no deal Reel on Nov 11).

**Thu Nov 12** · Instagram Reel + Story, this week's kit · hook (first second, on the payoff frame): EN "My size 11. Dropped $X." /
FR « Ma pointure 11. −X $. » (X = the kit's real drop; tonight's equivalent: Vomero Plus RR men's 11, $225 -> $159.99) · ig_reel picks
(history: a week ago vs today, $20+ and 15%+, livechecked before the email) · **re-run livecheck on the 2 featured items Thursday
morning (the kit was checked Wednesday)** · Story link sticker = that shoe's page ?ref=ig-story-drop · auto (ig_brief.py + ig_reel.py)
+ Claude's Thursday recheck, Bastien posts the ready Reel EN (FR Reel as a second post or FR caption) + Top-5 Story · **8 min**

**Fri Nov 13** · Friday email (both groups; the top "See all N deals in your size" button, em=friday-top, if Bastien says yes) · auto · 0 min
· Reddit week A Friday = open slot: leave it EMPTY (no tested sub; a removal before Black Friday would cost more than one post brings) · 0 min

**Sat Nov 14** · nothing new · 0 min

**Sun Nov 15** · Instagram Story: gift page opens in the menu today · EN "Gifts for runners, no size needed: under $25, $50, $100." /
FR « Cadeaux pour coureurs, sans pointure : moins de 25 $, 50 $, 100 $. » · gift page's own picks (8 on sale + 4 full price per budget;
one example price livechecked that morning) · /gifts-for-runners/?ref=ig-story-gifts (FR sticker /cadeaux-coureurs/?ref=ig-story-gifts) ·
Claude makes the Story frame (screenshot of the page at 390 px, designer check), Bastien posts · **3 min**

### Week B - founding list opens
**Mon Nov 16** · Reddit r/RunningDeals (week B) · as Nov 10, `--exclude` Nov 10 models · ?ref=reddit-runningdeals · **5 min**
· Bastien reviews the Fox Pro preview (not content; counted in the build) · Claude: swap the IG bio link to the founding landing ONLY
once backend confirms it shows the approved card.

**Tue Nov 17** · **Instagram collab post with Sinister Sports** (Collab invite to their account; Kirsti agreed Oct 25 to "collab on a post";
confirm the handle and the date with her by Nov 12) · format: 20-25 s screen Reel of /races/sinister-7/ (men's 11 / M picked), 3 frames:
(1) payoff first: the list with ticks and "From $X" lines, caption "Sinister 7 suggested gear, in your size, on sale"; (2) the "Suggested by
the race" labels, caption "None of it is required (bib + chip from the race)"; (3) "Remind me 30 days before" box ·
hook EN "Racing Sinister 7? Here's their suggested gear, in your size." / FR « Sinister 7 ? Leur liste d'équipement suggéré, dans votre taille. » ·
data: the page's own lines (re-read from sinistersports.ca rules_gear on Oct 27) + 2 picks' prices livechecked that morning · link in bio +
caption "Link in bio: thegearfox.com/races" · ?ref=ig-sinister · Claude records the screen part (tools/reels/rec.js, safe bands, payoff
zoom), Bastien posts + sends the collab invite · **10 min**
Caption EN: "Sinister Sports' races don't make you carry a mandatory list, but they do suggest one. We put each race's suggested gear
in one place: tick what you have, see what's on sale in your size today, get a reminder 30 days before race day. Sinister 7, Canadian
Death Race, SOO 200, Divide 200, Black Spur, Castle Alpine, Vertical Vendetta, The Dark 24. Not affiliated: lists as published by the race."
FR : « Les courses de Sinister Sports n'imposent pas de liste obligatoire, mais elles en suggèrent une. On a réuni l'équipement suggéré
de chaque course : cochez ce que vous avez, voyez ce qui est en solde dans votre taille aujourd'hui, recevez un rappel 30 jours avant. »
· also **founding list opens on the site** (card, members one tap): no social push today; the collab owns the day.
· Bluesky rotation stop rule (Nov 17): growth-analyst reads rotating vs shoe refs; rotating posts with 0 sign-ups -> shoes only.

**Wed Nov 18** · Instagram Wednesday kit (as Nov 12, posted the same day) · **8 min** · PLUS one Story: "You buy, we watch" explainer, founding list ·
EN "Bought it and the price drops after? Fox Pro keeps watching, and shows you the store's own rule. The store decides." / FR « Le prix
baisse après votre achat ? Fox Pro continue de surveiller et vous montre la politique du magasin. La décision revient au magasin. » +
"$36/year for founding members (that's $3/month), price locked while you stay. 100 numbered spots. Nothing to pay now." · data: none
(product facts) · sticker = founding landing ?ref=ig-story-founding · Claude drafts the frame from the approved screens (docs/fox-pro-screens.html),
compliance + designer check, Bastien posts · **3 min**
· Reddit r/runninglifestyle (week B Wednesday) · shoe pages ?ref=reddit-runninglifestyle · **5 min**

**Thu Nov 19** · nothing new (BF pages switch to deal mode tomorrow) · 0 min

**Fri Nov 20** · Friday email with the founding-list ask + the watcher note (members plan sections 1a + 2; Saturday Nov 21 for group B) · auto ·
0 min (Bastien answers replies: counted Sat)
· Reddit r/xxrunning (week B Friday, `--sex women`, rules re-read) · women's shoe pages ?ref=reddit-xxrunning · **5 min**
· Instagram Story: BF live page is up · EN "Black Friday deal check: real drops this week, and prices that went UP." / FR « Vérification du
Vendredi fou : les vraies baisses de la semaine, et les prix qui ont monté. » · bf_live.py's own lists · /black-friday/live/?ref=ig-story-bflive
(FR /vendredi-fou/direct/?ref=ig-story-bflive) · Claude screenshots (designer check), Bastien posts · **3 min**

**Sat Nov 21** · Bastien replies to watcher-note replies (members plan: "I read every reply") · **10 min max**

**Sun Nov 22** · nothing new · 0 min

### Week C - Black Friday week (every Reddit post points to /black-friday/ in its one bottom line)
**Mon Nov 23** · Reddit r/RunningDeals BF edition · first line = the data point (recomputed that morning: "Of the N sale prices we track in
Canada, X% were already this low 2 weeks ago. These 8 dropped this week:") then shoe lines whose history shows a drop in the last 7 days
(only real drops, the bf_live rule) · shoe pages ?ref=reddit-runningdeals-bf, bottom line /black-friday/live/?ref=reddit-runningdeals-bf ·
Claude drafts (post_check all lines match + the stat recomputed from prices.jsonl), Bastien pastes · **5 min**

**Tue Nov 24** · Press: BF early cut report (partnerships' job, report_page.py) · Instagram Story sharing the report link only if published ·
?ref=ig-story-report · **2 min**

**Wed Nov 25** · **Instagram Reel (Bastien films 1 line) "Is this Black Friday price new?"** · 20 s: (0-1 s, payoff first) frame of a real
drop on a shoe page price line "It was $A on <date> ($B today)", caption "Real drop: $A -> $B"; (1-8 s) Bastien to camera: "Before you buy
on Friday: we've tracked these prices since October." / FR « Avant d'acheter vendredi : on suit ces prix depuis octobre. »; (8-16 s) screen of
/black-friday/live/ "Real drops this week" vs "Not new: same price 21+ days"; (16-20 s) caption "Check yours: link in bio" · data: one drop
(tonight's equivalent: On Cloudeclipse men's $210 since Oct 10 -> $115 on Nov 3) + one "not new" (tonight's equivalent: Saucony Endorphin
Speed 5 men's $119.99 every day since Oct 12) + the % stat, all re-checked the morning of · bio + Story sticker /black-friday/live/?ref=ig-reel-bf
(FR /vendredi-fou/direct/?ref=ig-reel-bf) · Claude records + edits (safe bands, captions in the site part), Bastien films the 7-second line ·
**15 min** (replaces the Wednesday kit Reel this week; the kit's Top-5 Story still goes up)
· Reddit r/RunVancouver (`--city vancouver`) · ?ref=reddit-runvancouver-bf · **5 min**  -> day total 20 min
· Readiness decision for Dec 2 (Bastien + growth chat): decides which version of the Nov 27 email line and the Dec 2 Reel ship.

**Thu Nov 26** · nothing new (US Thanksgiving) · 0 min

**Fri Nov 27 (Black Friday)** · Friday email for everyone (BF + founding line "the list gets Fox Pro first, Wed Dec 2", or the January swap
line) · auto · 0 min
· ~~Reddit r/ultrarunning~~ REMOVED Nov 7 (Bastien: "Yes to all 3"; dropped Nov 4, no traction). Slot left empty.
· Instagram Story x2: morning "BF live check updated this morning" (?ref=ig-story-bf) + evening founding reminder ("The founding list closes
Nov 30. Nothing to pay now." Real date, no timer graphic) (?ref=ig-story-founding) · Bastien posts Claude's frames · **4 min**

**Sat Nov 28** · nothing new · 0 min

**Sun Nov 29** · Instagram Story: last day before the list closes tomorrow (EN/FR, same approved wording) · ?ref=ig-story-founding · **2 min**

### Week D - founding round + public launch
**Mon Nov 30 (Cyber Monday)** · Reddit r/RunningDeals Cyber Monday (real drops since Friday only) · ?ref=reddit-runningdeals-cm · **5 min**
· founding list closes tonight: growth-analyst counts pro_wait (target 40+)

**Tue Dec 1** · Claude: picks the Reel's real drop for Dec 2 from that morning's history, livechecks it, sends Bastien the script with the
numbers filled in + the shot list · 0 min (he reads it Dec 2)

**Wed Dec 2 (founding round)** · **Founder Reel (script below), only if the readiness bar holds** · Bastien films ~3 takes to camera
(phone, vertical) · Claude edits (safe bands, captions in the middle band, payoff first) · link in bio = founding checkout landing
?ref=ig-reel-founder · **15 min** (film + post)
· Reddit r/runningmontreal (week D Wednesday, FR + EN, `--city montreal`): **shoe deals only, no Fox Pro** · ?ref=reddit-runningmontreal · **5 min**
-> day total 20 min
· The list's checkout email goes out from the system (backend; not social).

**Thu Dec 3** · nothing new · Bastien answers DMs/replies about Pro · **10 min max**

**Fri Dec 4 (public launch)** · Friday email: the launch block (members-lead drafts; "Fox Pro is open to everyone; founding spots left: N"
only with the real live count) · auto · 0 min
· Instagram: repost the founder Reel to Story with the Dec 4 last line + link sticker ?ref=ig-story-launch; pinned feed post = the
founder Reel · **5 min**
· Reddit r/FrugalMaleFashionCDN (week D Friday, `--side ca --sex men`, rules re-read): **shoe deals only, no Fox Pro** ·
?ref=reddit-frugalmalefashioncdn · **5 min**
· Bluesky: one hand-written launch post by Bastien? NO: keep Bluesky automatic drops (no Pro pitch inside an automated drop feed) · 0 min

**Sat Dec 5** · Instagram Story: Boxing Day page "get ready" (Canada; real deals Dec 19-Jan 3) · /boxing-day/?ref=ig-story-boxing
(FR /soldes-apres-noel/) · **2 min**

**Sun Dec 6** · Claude: results page for the growth chat (see "What to measure") · 0 min

Bastien total Nov 10 - Dec 6: ~155 min over 27 days (~6 min/day; max 20 on Nov 25 and Dec 2; 16 on Nov 18).

## Founder Reel, Wed Dec 2 (30 s, his voice, facts only)
Shot: Bastien to camera, vertical, outdoors in running gear (his own; no brand claims). Captions burned in the middle band only
(y 218 to 1520), never in the bottom 400 px. Hook + payoff in the first second.

| Time | Picture | Caption on screen (EN / FR) | Bastien says |
|---|---|---|---|
| 0-1.5 s | Payoff first: his phone, a real alert email in his size (slow zoom on the price line), filled Dec 1 from the history + livecheck | "Dropped $X in my size, the same morning" / « −X $ dans ma pointure, le matin même » | (silence, then) |
| 1.5-6 s | Bastien to camera | "Bastien · Montréal / Vancouver" | EN: "I'm Bastien, a runner from Montréal and Vancouver." |
| 6-11 s | Screen: homepage in men's 11 / M | "{N} stores, checked every day. Free." / « {N} boutiques vérifiées chaque jour. Gratuit. » | "The Gear Fox checks {N} stores every day for gear on sale in your size. That stays free." |
| 11-20 s | Screen: watchlist, then the "I bought it" screen | "Same-morning alerts · No watchlist limit · We keep watching after you buy. The store decides." | "Today Fox Pro opens: an email the morning a price drops, no limit on your watchlist, and after you buy, we keep watching, in case the store refunds the difference." |
| 20-27 s | Bastien to camera | "$36/year for founding members (that's $3/month), locked while you stay · 100 numbered spots · 30-day full refund" | "Founding members pay thirty-six dollars a year, price locked while you stay. A hundred numbered spots, and thirty days to change your mind." |
| 27-30 s | End card (logo on #17201C, inside the safe area) | "Founding list: today. Everyone: Friday, Dec 4. Link in bio." | "The founding list gets it today. Everyone else, Friday. Link in bio." |

FR voice (same shots; Québec French):
« Moi, c'est Bastien, coureur, de Montréal à Vancouver. The Gear Fox vérifie {N} boutiques chaque jour pour trouver l'équipement en solde
dans votre taille. Ça, ça reste gratuit. Aujourd'hui, Fox Pro ouvre : un courriel le matin même d'une baisse de prix, des favoris illimités,
et après votre achat, on continue de surveiller, au cas où le magasin rembourserait la différence. Les membres fondateurs paient 36 $ par
année, prix garanti tant que vous restez membre. Cent places numérotées, et 30 jours pour changer d'idée. La liste y a accès aujourd'hui;
tout le monde, vendredi. Lien dans la bio. »
FR captions: « Alertes le matin même · Favoris illimités · On surveille après l'achat. La décision revient au magasin. » / « 36 $/an pour
les membres fondateurs (3 $/mois), prix garanti tant que vous restez · 100 places numérotées · Remboursement complet 30 jours »

Dec 4 variant (Story repost): last line "Fox Pro is open to everyone today. Link in bio." / « Fox Pro est ouvert à tous aujourd'hui. Lien
dans la bio. » + "Founding spots left: N" ONLY if N is the real live count at posting time; otherwise no number.
If the readiness bar fails (Nov 25): no Dec 2 Reel. Story only: "Fox Pro opens in January. The list hears first. Nothing to pay before
then." / « Fox Pro ouvrira en janvier. On écrira d'abord aux inscrits. Rien à payer d'ici là. » (members plan swap line).
Facts check on this script: {N} = n_stores in sale.json on Dec 1 (170 on Nov 4); $X = a real alert/drop from that morning, livechecked;
"twice a day" is also true but "every day" is shorter; no claim of savings, no member counts, no "best", no "for life".

## What to measure (funnel.yml + monthly report; growth-analyst reads it Mon Nov 16, Mon Nov 30, Sun Dec 6)
| Goal | Metric | Source | Target / stop rule |
|---|---|---|---|
| Founding list | pro-join count by ref / em tag (ig-story-founding, ig-bio-founding, friday-pro, alert-pro, welcome-pro, site card) | funnel "FOX PRO", analytics signup-step pro-join | 40+ by Nov 30 (else January); members plan says email gives 15-25 of it |
| Founding round | paid founders by ref (ig-reel-founder, ig-story-launch, email) | Stripe + profile ref | 8-20 by Jan 31 |
| Sign-ups from social | sign-ups and first visits per ?ref above | funnel by ref | IG pieces: >= 1 sign-up per 50 first visits to keep the format |
| Sinister collab | first visits + race-list ticks + reminder sign-ups ?ref=ig-sinister | funnel "RACE GEAR LISTS" by ref | the first backlink: does sinistersports.ca link a page? (Search Console Links) |
| BF Reel | first visits ?ref=ig-reel-bf, % that go on to a shoe page, sign-ups | funnel | compare with the Nov 12/18 kit Reels |
| Reddit | first visits + sign-ups per ?ref=reddit-<sub>(-bf/-cm) | funnel | drop a sub with 0 visitors (calendar rule) |
| Bluesky rotation | rotating vs shoe refs | funnel | Nov 17 stop rule |
| Pinterest | first visits ?ref=pinterest | funnel | < 30 by mid-Dec = stop |
| Bastien's time | minutes he reports per day | him | <= 20 every day |

## Dependencies + risks (for the growth chat)
1. **Founding-list landing for public links**: /pro/ is 404 and ?pro=1 still shows the old price-test card ($3/$29 vs $5/$49). Backend needs a
   public `?pro=join` (or /pro/) with the approved screen 1 by Nov 16, one tap, never join on page load. Without it, no IG founding sticker/bio.
2. Sinister collab: confirm with Kirsti (handle, Nov 17 date, collab invite vs her own repost) by Nov 12 (partnerships). Compliance: no
   payment either way; the page already says "not affiliated", the caption says it too.
3. Readiness decision Nov 25 drives the Nov 27 email line and the Dec 2 Reel (members plan ask 1).
4. Reddit stays Pro-free, including Dec 2-4 (team rule). Nov 13 Friday slot left empty on purpose.
5. Every hook number above is tonight's; the 6:30am drafts and the Wednesday kit fill in that day's numbers. Nothing posts with a price that
   wasn't livechecked that morning (MEC/Decathlon/Sporting Life items can't be checked: leave them out of hooks).
