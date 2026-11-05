# Night shift, Nov 5: Black Friday market watch + 3 new growth ideas (CMO)
Draft for the growth chat. Nothing public, nothing sent, no code. Every public line goes through compliance (and every visual through the designer) first.

Our numbers used (re-read tonight):
- docs/signup-funnel-nov4.md: funnel run 41778856341, 14 days to Nov 4. 69 sign-ups. The Watch-tap email step is the best spot (23 sign-ups, about 1 in 5 Watch-tap sessions). Shoe pages give 17. The homepage card converts 0.23%. Reddit 0.6%.
- docs/members-plan-nov4.md: 155 real members, 41 of them watch something. Alerts bring about 1 visit per 2 emails, the weekly email about 1 per 10. Email asks for the founding list are estimated at 15-25 joins, against a target of 40 by Nov 30.
- docs/decisions.md through Nov 5.
- Live sale.json (Nov 5, 06:34 UTC): n_stores = 150. The content calendar wrote "170 stores" on Nov 4: re-read {N} before any Reel or caption. The drop is likely Sport Chek off (Nov 5) plus the RunFree catalog rows that expired Nov 4.
- History branch prices.jsonl (157,807 lines). The new computation is in idea 1.

---

## Part 1. Black Friday 2026 market watch (Canada first, US second)

Black Friday is Fri Nov 27 and Cyber Monday Mon Nov 30 (Altitude FAQ; Brooks' 2026 pages say its sale "returns on November 27th").

| Who | What they're doing this year (found Nov 5) | Source |
|---|---|---|
| Altitude Sports (one of our top stores) | Sales from **Nov 2**. "All orders placed from November 2 to 19, 2026 will be eligible for a price match until December 7, 2026. If a product's price on our website drops during Black Friday, we'll adjust the price for you." Same colour and size; no marketplace sellers; no clearance/final sale; Canadian competitors only. Returns: orders Nov 2 - Dec 7 returnable until **Jan 8, 2027**. Lifetime members get "early access" (no date given). | https://www.altitude-sports.com/faq , https://www.altitude-sports.com/c/black-friday-cyber-monday |
| BlackToe Running (Toronto) | 2025: price-matched eligible Black Friday deals **Nov 13 - Dec 12**, extended returns to Jan 15. No 2026 page found yet; the 2025 page now answers 404. | https://www.blacktoerunning.com/pages/black-friday-2025 (search snippet; page 404 Nov 5), https://www.blacktoerunning.com/pages/returns-exchanges |
| Sporting Life | Black Friday page: deals "launch in November 2026", "subscribe now to be the first to hear about our early Black Friday deals". The page answers 403 to our fetch, so this is from the search snippet. A coupon site lists "41% off sale items" dated Nov 1. | https://www.sportinglife.ca/en-CA/black-friday.html , https://www.bargainmoose.ca/coupons/sportinglife.ca |
| MEC | No official 2026 dates found. Its running deals page is a rolling list (e.g. Saucony Ride 18 $91.75, reg $179.95). Member perks in past years: extra 10% on select MEC Label (2024). | https://www.mec.ca/en/products/running/deals , https://mec.ca/en/p/member-rewards |
| Running Room | No 2026 event found. Last year: up to 40% off Brooks/adidas/Garmin, through Sun Nov 30 (Canadian Running). | https://runningmagazine.ca/?p=20886 |
| Canadian Running Magazine | No 2026 Black Friday piece yet. The 2025 rhythm: "Early Black Friday deals on running shoes" **Nov 24**, Black Friday Nov 28, Cyber Monday tech Dec 1, gift guides Dec 7 + 9, Boxing Day Dec 26. **So pitch our numbers before ~Nov 20** (the press wave of Nov 16 fits). | https://runningmagazine.ca/author/gus/ , https://runningmagazine.ca/buyers-guide/early-black-friday-deals-on-running-shoes/ |
| RedFlagDeals | Its forum now sends robots to a TollBit paywall (tollbit.redflagdeals.com). We don't get around it. Bastien can browse it himself. No 2026 running thread surfaced in search. | redirect seen Nov 5 |
| RunRepeat (US) | Evergreen deals pages with % off (e.g. Pegasus 41 $60 from $140). No Black Friday 2026 page and no price-history/alert feature found. | https://runrepeat.com/deals/running-shoes?page=2 |
| Running Warehouse / Believe in the Run (US) | No 2026 dates found. Past seasons: free shipping + returns, deal roundups on the day. | https://believeintherun.com/?p=25033 |
| Deal-checker angle | Which? (UK) tracked the 2024 sale: **83%** of Black Friday "deals" were cheaper or the same price at least once in the 6 months around it. Canada's Competition Bureau (Nov 25, 2025) reported a **surge in complaints about inflated regular prices** and says made-up "regular prices" are illegal. No 2026 Bureau notice yet. Our own number (content calendar, Nov 4): 78.5% of Canadian sale prices we track were already this low 2 weeks before. | https://www.which.co.uk/policy-and-insight/article/dont-believe-the-hype-most-black-friday-deals-the-same-price-or-cheaper-at-other-times-of-the-year-which-finds-a3TbD5x5KADs , https://www.canada.ca/en/competition-bureau/news/2025/11/businesses-make-sure-your-black-friday-deals-are-real.html |

**Copy this one thing: a dated protection window in plain words.**
- Altitude's line is the clearest Black Friday promise in our space: "buy Nov 2-19, we'll match a drop until Dec 7".
- It removes the reason people wait ("what if it drops after I buy?"). That is exactly Fox Pro's "You buy, we watch, you claim".
- Our version names real dates and the store's own window. We never promise the refund itself: "The store decides".
- Idea 1 below uses it.

**Avoid this one thing: "up to X% off" headlines and early-access hype with no dates.**
- Sporting Life's "subscribe to be the first to hear" and the aggregators' "save up to 60%" are what the Competition Bureau and Which? are warning about.
- Our pages already lead with "real drops this week" vs "not new". Keep every headline and post line on that (price, the date it changed, sizes).
- Never write "up to N% off" from stores' regular prices.

Contest note: none of the ideas below is a contest or giveaway (the giveaway was cut Nov 2). No contest-law check is needed tonight.

---

## Part 2. Three growth ideas we haven't tried (ranked; #1 is the pick)

### #1 (PICK): "Bought it this week? We'll watch it for you, free until Dec 7": Black Friday purchases watched for founding-list joiners
**The idea.**
- Nov 20-30, anyone who joins the founding list (one tap for members, email for others) can log what they bought ("I bought it", already in the Fox Pro build: store, item, size, price).
- We watch that exact item at that store until Dec 7 (Altitude's own match deadline; the Pro launch is Dec 2).
- If the store's price drops, they get one email: what dropped, the store's own published rule if it has one, "The store decides".
- On Dec 2 the founding link offers to keep watching it with Pro.
- Nothing to pay, no card. It's a preview of Fox Pro's main promise on the week people actually buy.

**Evidence.**
- *Drops after a sale really happen (history, new tonight).* Shoes on sale (10%+ off) on Oct 15: **17.8%** (520 of 2,919) got cheaper again by our alert rule (10% or $10, at least $5) somewhere we track within 3 weeks, median **$15 lower**. Over 2 weeks from Oct 22: 6.7% (224 of 3,364).
  - This is the best price across stores. Same-store drops will be fewer.
  - Read it as "about 1 in 6 to 1 in 15", not a promise.
- *Item-specific asks convert best on our site.* The Watch-tap email step brings about 1 in 5 Watch-tap sessions to sign up (23 of 69 sign-ups). Alerts about chosen items bring ~5x the visits per email of the weekly email (members plan).
- *Stores publish the windows.* Altitude (orders Nov 2-19, match until Dec 7). BlackToe in 2025 (Nov 13 - Dec 12).
- *The market.* Kiko+ charges $39/year in Canada for exactly this kind of money-back watching (pro-roadmap-nov4.md: "people pay for getting money back, not for seeing prices").
- *It fills a readiness gap.* Readiness item 4 ("I bought it" tested on real purchases with correct claim emails) needs real purchases before Nov 27. This gives them, from real members, during the one week they buy.
- *It fills the list gap.* The email asks alone are estimated at 15-25 of the 40 the list needs.

**Why it isn't a repeat.**
- The Oct 28 waitlist card only *promised* "Money back after you buy" to visitors (0 joins of 82 views, old $3/$5 test card).
- This *does* the watching for real, for a purchase the person just made, inside the existing founding-list ask.
- Not a giveaway (cut Nov 2), not queue positions or waves (declined Nov 2), not a price cut (referral codes add time only). Nothing in decisions.md tried it.

**1-week test (Nov 20-27).**
- It rides on the asks already planned:
  - the Nov 20 Friday email block (Nov 21 for the Saturday group);
  - the drop-alert line (Nov 17 - Dec 1);
  - the founding card for members and returning visitors.
- Each adds one line: "Bought something this week? Log it when you join: we'll watch its price free until Dec 7."
- No A/B: ~160 weekly emails is far too few (the members plan says so). It's a before/after against Nov 17-19, the same asks without the line.

**Metric.**
- Founding-list joins (pro_wait) per day, by em/ref tag. Purchases logged. Drop emails sent.
- Wrong-price drop emails: must be 0.
- Target: 40 on the list by Nov 30.

**Stop rule.**
- Any drop email with a wrong price or a wrong store window: switch it off the same day (trust bucket; the readiness bar's item 1).
- By Wed Nov 25 (the proposed readiness-decision day), if there are fewer than 5 purchases logged, or the joins per day are not above Nov 17-19's: remove the line from the Nov 27 email and go back to the plain ask.

**Cost.**
- Bastien: ~20 min (one yes + the preview, copy through compliance).
- Backend: "I bought it" is already being built. The extra is a free watch-until-Dec-7 mode for list members and the Dec 2 hand-off: ~0.5-1 day.

**Needs Bastien's yes on 2 things.**
1. Show each person the price-adjustment rule of the store they bought at before Dec 2. The full 192-store list stays private, as he decided.
2. Watch until Dec 7, even though the launch is Dec 2.

**Dependency.** "I bought it" must pass its own test before Nov 20. If it slips, run the plain ask and start this with the Dec 2 founders instead.

**Expected (estimate, low confidence).** +5-15 list joins Nov 20-30, plus 10+ real logged purchases. The purchases are the readiness proof and the first true "we caught a drop" stories for the Dec 2 Reel, if the person agrees.

### #2: "Tell a running partner": a personal share line inside drop alerts and the Friday email (free members)
**The idea.**
- Under the price line of a real drop alert (and once in the Friday email): "Know someone who runs in size X? Send them this: thegearfox.com/?ref=f-<code>".
- The code is a short random per-member id, never the email.
- The friend lands on the same shoe page, with "Email me when it drops" right there.
- No reward, so no contest or referral rules beyond CASL. We never email the friend: the member sends it themselves.

**Evidence.**
- New fact Nov 4: several buyers asked for "the word to spread" (decisions, Testimonials row).
- Alerts are our most-opened email (~1 visit per 2).
- Signed-up devices came back 53% vs 14%.
- Research: referred customers are more loyal and more valuable (Schmitt, Skiera & Van den Bulte, Journal of Marketing 2011). People share what makes them look smart (Berger, "Contagious", social currency).

**Why it isn't a repeat.**
- The site's share card (since Oct 1) is anonymous and generic.
- Fox Pro referral (Oct 31) pays only for paying friends.
- Nothing personal at the moment of a real drop has been tried.

**1-week test.**
- The Nov 13 Friday send plus every alert Nov 13-20. Emails aren't covered by the freeze (members plan); the backend change is small: an id per member + a line in two templates.

**Metric.** First visits and sign-ups with ref=f-*.

**Stop rule.**
- Under 5 friend first visits across 2 Friday sends plus a week of alerts: remove it.
- Any unsubscribe or complaint that mentions it: remove it.

**Honest limit.** The volume is small (~15 alerts a week, ~160 weekly emails). It's a cheap lottery ticket, not a list-filler.

### #3: "Is this price real?": paste a store link on the Black Friday deal check page
**The idea.**
- One box on /black-friday/live/ + /vendredi-fou/direct/: paste a product link from any store we track.
- We match it to our item (deals.json `of` links, store product URL without query).
- We show its price line from our history ("It was $X on <date>, $Y today" / "same price since <date>").
- Then [Email me when it drops], which watches that item.
- No match: "We don't track this one" + search.

**Evidence.**
- The deal-checker angle is where the press and consumer groups are this year (Which? 83%; the Competition Bureau's complaint surge).
- Keepa and CamelCamelCamel built their audience on "paste a link" (pro-roadmap-nov4.md).
- 12% of our searches find nothing (funnel Nov 4). Shoppers already have the store page open, not our model name.
- The ask is item-specific, our best-converting kind of ask.

**Why it isn't a repeat.** Search (Oct 8), "Did you mean" and closest match (Oct 26) and the BF deal check lists (Oct 27) all start from our catalogue. None takes a store URL.

**Test.** Nov 20-27 on the deal check pages.

**Metric.** Pastes, match rate, watches + sign-ups per paste.

**Stop rule.** Under 20 pastes in BF week, or a match rate under 50%: remove it.

**Cost.**
- Backend 1-1.5 days after the freeze.
- Bastien ~15 min (preview OK).

**Why it's #3.**
- On phones, copying a store link and switching apps is friction, and we have no data that people will do it.
- Lowest expected sign-ups per hour of the three.

### Not proposed (checked tonight)
- **Size-extreme community posts** (men's 14-15, women's 5 and 11-12). Our sale.json today: men's 11 has 454 Canadian sale shoe cards (10%+ off), men's 14 has 125, 15 has 51, women's 12 has 119. Big sizes do have fewer deals. But posting in niche communities is the Reddit pattern again (clicks, <1% sign-ups), and brand+size pages were declined Oct 24. Left out.
- **RedFlagDeals posting.** Same Reddit pattern, strict self-promotion rules, and the forum now walls robots. Bastien can read it; we don't build on it.

## Recommendation
Do #1. It is the only idea that moves both Black Friday numbers at once:
- founding-list joins toward 40 by Nov 30 (emails alone ~15-25);
- real "I bought it" purchases for readiness item 4.

It's built on a promise stores are already making publicly (Altitude's Dec 7 window). It costs Bastien ~20 minutes.

Measure joins per day vs Nov 17-19, purchases logged, and wrong drop emails (must stay 0). Stop on any wrong email, or on fewer than 5 purchases by Nov 25.

Sources: links in the table above, plus https://www.canada.ca/en/competition-bureau/news/2025/11/businesses-make-sure-your-black-friday-deals-are-real.html , https://www.which.co.uk/policy-and-insight/article/dont-believe-the-hype-most-black-friday-deals-the-same-price-or-cheaper-at-other-times-of-the-year-which-finds-a3TbD5x5KADs , https://ca.style.yahoo.com/when-is-black-friday-2026-36-best-early-black-friday-sales-in-canada-from-best-buy-to-walmart-183620947.html
