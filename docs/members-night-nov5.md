# Members night shift, Nov 5: getting the 116 who watch nothing to watch one thing
Members lead, night of Nov 5, 2026. This builds on docs/members-plan-nov4.md and doesn't repeat it. Drafts only: nothing was sent and no code was changed. Every public line goes to compliance before it ships. The backend chat writes the code once Bastien says yes.

## Numbers (funnel.yml run 41863479941, Nov 4, last 14 days)
- WATCHLIST SIZE: 165 real members. Watched items: 0 = 116, 1 = 26, 2 = 7, 3 = 2, 4-5 = 7, 6-10 = 7. So **49 of 165 (30%) watch something**. On Oct 31 it was 38 of 150 (25%).
- COMING BACK: members 53% vs non-members 14%. RETENTION DRIVERS: devices that hearted a deal came back 34% (32 devices) vs 12% for the rest. That's a lead, not proof.
- Visits from our emails (14 days): alert 18, friday 16, saturday 11. The Oct 31 Saturday group got 48 sends in its biggest hourly run (weekly-email run 41195506700).
- Watch taps on the site: 90 visits tapped Watch in 14 days, 65 of them only once.

## Which email can reach the 116? (sorted before picking)
- **Alerts:** reach watchers only (alerts.py works from rows in `watches`). That's 0 of the 116.
- **Race reminders:** go only to people who saved a race list, at race date minus 30 days. A handful.
- **Welcome email:** new members only (~5-10 a week). It's SQL, so Bastien has to paste the change.
- **Friday/Saturday email:** reaches nearly all of the 116 every week. **This is the only lever before Black Friday.**

Today the Friday email asks people to watch in one way only: a small 12px "♡ Watch the price" link under each card (`card()`, `wl + "&watch=" + key`). Nothing tells someone who watches nothing what watching does.

## (1) The one change: a "watch one thing" box in the weekly email, only for members who watch nothing
**Where:** `scraper/weekly_email.py`, `build()`.
- Put a box right after the intro (after `first_note` when that shows), before the sections. Same style as `first_note` (#FFF4EC, 1.5px orange border).
- **Who gets it:** subscribers with no row at all in `watches` (page| keys count as watching). `main()` already fetches the rows for `watch_news` (`A.fetch_rows()`), so pass in a set of tokens that have rows.
- **Which item:** `drops[0]` (the week's biggest drop in their size, shoe first). If there are no drops, use the first shoe in `sale` after its sort. If there are no shoes, use `sale[0]`.
- **Link:** `shop_link(p) + "&em=" + em_day() + "-watch" + "&watch=" + quote(itemKey)`. That gives the tags `friday-watch` / `saturday-watch`, both under the site's 20-letter cap. The site already handles `?watch=`: `watchFromLink()` -> `toggleWatch` -> `watch_add` for members, and records "watch-from-page" + "watch-add".
- **The text version** gets the same lines plus the link.
- **Ship for the Nov 13 send** (both day-test groups get it, so the emailday test stays fair). Nov 6 is too close: Bastien needs to see the copy first.
- **Precedence:** this supersedes my Nov 4 "top button" idea for these 116 people. New fact: the goal is now watching, and this box is already a top link to the site.

### Copy
EN
> **You're not watching anything yet.** Tap below and we'll email you if the {Brand} {Name} drops 10% or $10 from today's price in your size ({price} today), or comes back in your size after selling out. One tap on the site removes it.
> [♡ Watch this price]
> Or tap "♡ Watch the price" under anything below.

FR
> **Vous ne suivez encore aucun article.** Touchez ci-dessous et on vous écrira si le prix du {Brand} {Name} baisse de 10 % ou 10 $ par rapport au prix d'aujourd'hui dans votre taille ({price} aujourd'hui), ou s'il revient en stock dans votre taille. Un seul geste sur le site suffit pour le retirer.
> [♡ Suivre ce prix]
> Ou touchez « ♡ Suivre le prix » sous n'importe quel article plus bas.

**Compliance: OK Nov 5** (EN + FR as written). The promise matches alerts.py `is_drop()` (10% or $10) + back-in-size and names no timing, so it stays true after Dec 2 (free = Friday email). Members already consented to these emails; the box adds no new consent. Conditions: {price} must be the price in THAT member's size on their side (US$ on the US side, where "$10" = US$10); and run the Safe Links check below BEFORE Nov 13: if Microsoft scanners add watches nobody tapped, those people would get alerts they never asked for (a trust problem, not CASL): then send Microsoft addresses the box without the auto-watch link (link to the shoe page instead) until the one-tap confirm ships.

Why each piece is safe:
- **"we'll email you if…"** is the alert rule in alerts.py `is_drop()` (10% or $10 vs the notified price), plus back-in-size. It stays true after Dec 2: free members get the news in the Friday email, and Pro gets it the same morning. So it promises no timing.
- **No mention of Black Friday urgency** and no countdown.
- **Nothing pre-ticked:** the member taps.

Evidence:
- Watchers came back 34% vs 12% (a lead).
- The email that names the items people chose (the alert) brings ~5x the visits per send of the generic one (docs/members-plan-nov4.md).
- Nielsen Norman Group: newsletter readers scan and act on what comes first. Today the only "watch" ask is a small link inside the cards.
- Zero risk to anyone already watching: they don't get the box.

**One risk, already in the live links:** `?watch=` watches the item as the page loads. Microsoft Safe Links and other scanners open email links in a real browser. On Outlook/Hotmail addresses, that could add watches nobody asked for. That fakes our metric and later sends unwanted alerts.
- Check (backend, read-only): for watches created within 5 minutes of that member's send time, compare Microsoft vs other domains (tools/mail_check.py already splits by provider).
- If Microsoft shows a burst, the proper fix (a one-tap confirm instead of watching on load) waits for the Nov 16 batch, because it's a site change.
- Until then, count Microsoft watches only if the member also has a deal click or a later visit.

## (2) How we measure it (existing funnel lines)
**Main:** WATCHLIST SIZE, the `0:` count over real members.
- Baseline Nov 4: 116 of 165 = 70% watch nothing.
- Read it before the Nov 13 send, then on Mon Nov 16 and Mon Nov 23.

**Per send:**
- "Visits from our emails": the `friday-watch` and `saturday-watch` counts. Their share of all email visits shows the box gets taps.
- "Watch taps per visit": adds.

**Guards:**
- The unsubscribe count (funnel `unsub`).
- mail_health complaints and bounces in the morning email.
- COMING BACK, "signed up: came back" (53% now).

**No A/B test:**
- 116 people are already split by the emailday test until Nov 21.
- Detecting 5% -> 20% of recipients watching needs ~75 per group at 80% power, and we'd have ~58.
- So we judge before vs after. That's honest only because the 0-watch share barely moved on its own (75% Oct 31 -> 70% Nov 4, mostly new members).

**Small backend ask (tools only, not visible):**
- funnel.py's EMAIL DAY TEST counts exact "email-friday"/"email-saturday". Make it count the prefix so `-watch` visits stay in the test.
- Add one line: "members who signed up before <date> whose first watch was created this week". This separates our effect from new sign-ups who arrive already watching.

## (3) Stop rule
Check Mon Nov 23, after the Nov 13/14 and Nov 20/21 sends.
- **Keep it for Nov 27, and through Dec 2 as is**, if:
  - 8+ of the 116 (7%) watch something through a `-watch` link, or
  - the "watch nothing" share falls by 5+ points among members who signed up before Nov 13.
- **Remove it before Nov 27** if:
  - fewer than 3 `-watch` visits across the two sends, or
  - the main metric doesn't move (keeps the Black Friday email clean).
- **Remove it at once** if:
  - any spam complaint, or
  - 2+ unsubscribes in a send from box recipients (vs ~0-1 a week now), or
  - the Safe Links check shows fake watches we can't filter.
- Log the result as a row in docs/decisions.md either way.

## Black Friday week email (Fri Nov 27; the regular weekly email: Friday for everyone, no extra send)
Facts-only. One trap: the email's "dropped" rule (`week_drop`: 10% or $10 below the best price 7 days ago) is NOT the deal-check page's "real drop" (lower than every price in the 30 days before). So the email never says "real drop". It states its own rule.

**Subject**, BF-week variants of the three existing lambdas in STR. Same logic: watchlist news first, then the biggest drop, then the count.
| case | EN | FR |
|---|---|---|
| watchlist news | Black Friday week: your watchlist moved, plus {n} deals in your size | Semaine du Vendredi fou : vos favoris ont bougé, et {n} aubaines à votre taille |
| a drop | Black Friday week: {name} dropped {m} in your size, + {k} more | Semaine du Vendredi fou : {name} −{m} à votre taille, + {k} autres baisses |
| no drop | Black Friday week: {n} deals in your size, up to {top}% off | Semaine du Vendredi fou : {n} aubaines à votre taille, jusqu'à {top} % de rabais |

**Compliance (subjects): watchlist news OK, a drop OK. No drop: FIX.** "Up to {top}% off" (Competition Bureau: an "up to" claim misleads when only one item reaches it) is OK only if the {top}% item is shown in that same email in that member's size; otherwise use: EN "Black Friday week: {n} deals in your size" / FR « Semaine du Vendredi fou : {n} aubaines à votre taille ». The % off is against the store's own regular price (stores' compare-at): never against our history.

**First lines** (`intro_drop` variant, then one line linking the deal check):

EN
> {first}, {k} things dropped in your sizes this week: each one is at least 10% or $10 below its price a week ago in our price history. Here they are, then the week's best deals.
> Not sure a Black Friday price is new? Our deal check, updated twice a day, shows this week's real drops and the "sales" that have been the same for weeks: thegearfox.com/black-friday/live/

FR
> {first}, {k} articles ont baissé dans vos tailles cette semaine : chacun coûte au moins 10 % ou 10 $ de moins qu'il y a une semaine, selon notre historique de prix. Les voici, puis les meilleures aubaines de la semaine.
> Un prix du Vendredi fou vous semble familier? Notre vérificateur, mis à jour deux fois par jour, montre les vraies baisses de la semaine et les « soldes » au même prix depuis des semaines : thegearfox.com/vendredi-fou/direct/

**US side** (SIDE["us"]): there's no live check page, so the second line links /us/black-friday/:
> "Our Black Friday page shows how this year's prices compare with the last two weeks: thegearfox.com/us/black-friday/"

Check the US page text before the send to make sure it still matches.

**Compliance (first lines): OK Nov 5 for EN/FR Canada** (the email states its own rule, never "real drop"; "the 'sales' that have been the same for weeks" mirrors the page's own heading « Not new: same "sale" price for weeks »). **US line: FIX**: "this year's prices" is not what the page says. Use: "Our Black Friday page compares today's sale prices with the last two weeks: thegearfox.com/us/black-friday/" (the page today: "81% of the shoes on sale today were already at that price or lower two weeks ago").

**Optional fact line** (use only if the backend fills it from the same morning's bf_stats the page shows; otherwise leave it out):
- EN: "This morning, {p}% of the sale prices we track were already this low 2 weeks ago."
- FR: « Ce matin, {p} % des prix en solde qu'on suit étaient déjà aussi bas il y a 2 semaines. »

**Compliance (fact line): OK, CANADA SIDE ONLY**, filled from the same morning's number the Canadian page shows (its wording: "of sale prices were already this low 2 weeks ago", Canadian stores). Never on the US email: the US page's stat is a different one (shoes only, "at that price or lower"). FR side = the /vendredi-fou/direct/ number.

**Stays as is:**
- the founding-list block (docs/members-plan-nov4.md 1b, incl. the Nov 25 readiness swap line);
- the "Hit reply" line;
- the fine print ("Prices and stock change daily; the product page has the final price");
- unsubscribe, privacy and the mailing address.

**Compliance notes:**
- no "ends soon", "last chance", "best price of the year" or "lowest price ever";
- "up to {top}%" comes from today's matched data (the 7x-regular typo guard is already in the merge);
- the deal-check links state the page's own method.

## Trust item found tonight (for Bastien / backend, not members-facing)
- Weekly-email run logs from before the Nov 3 masking fix show whole subscriber addresses. One example: run 41077707857, Oct 30, a "nothing on sale" line. This repo's Actions logs are public.
- Ask: delete the logs of weekly-email (and alerts/refresh) runs dated before Nov 3 (each run's "…" menu > Delete all logs, or the backend via the API).
- The code is already fixed (`mask()`).
- Compliance: agree, delete them (personal info in public logs; PIPEDA safeguards). Also check alerts/refresh/confirm-reminder/race-remind logs for the same before Nov 3.

## Asks (one line each)
1. The "watch one thing" box in the Nov 13 weekly email for members who watch nothing (copy above)? yes/no
2. The Black Friday week subject + first lines for Nov 27 (copy above)? yes/no
3. Delete the pre-Nov 3 Actions logs that show subscriber addresses? yes/no
