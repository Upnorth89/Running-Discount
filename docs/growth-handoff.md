# Growth chat handoff (written Nov 5, 2026, before starting a fresh growth chat)

Read first: CLAUDE.md (rules + how to work with Bastien), docs/decisions.md (every decision with numbers), docs/team.md (agents),
docs/social-formats.md (video formats: STAY ON THEM), docs/backend-to-growth.md (backend's notes, newest at the bottom).
Backend chat = session_01RUChGi3w44GsN1T5Lpq1Zn (writes ALL code; growth sends specs with send_message).
Outreach tracker = artifact database https://claude.ai/artifact/4tD4v4AWgXWrW6zohytTuN (collection "outreach").
Plan doc (6-month plan, weekly goals, Ideas backlog) = https://claude.ai/code/artifact/36e1d545-7390-44fe-b080-80f03465af61

## Lessons from the old chat (why we restarted)
- Very long chats get compacted, and details not written in the repo are lost (it forgot Super Shoe Sunday and the Halloween
  video). Write every format, decision and open item into docs/ the same day.
- When you can't see a screen (new Supabase/Stripe UIs), say so and ask for ONE screenshot. Never guess the click steps.
  Bastien, Nov 5: "you used to be very clear with your instructions. feels like you're skipping steps."
- Give step-by-step lists that match his screen, one action per line.
- Use the team for creative calls (Bastien, Nov 5: "Use the team to decide … not by yourself").

## Freeze
Until Nov 15 (no new features). Exceptions: bug/trust fixes, store readers, Fox Pro (hidden). First batch Nov 16.

## Open items, newest first
- Nov 5 rule: Bastien reads only this chat. Backend sends "BLOCKED: ..." messages; relay them to him in the next reply. Answered tonight: Running Free probe GO, BF "first screen" file (new-visitor part YES, returning part -> Nov 16 preview), Salt Lake Running Co + Dick Pond readers YES.

### Stripe / Fox Pro (Bastien set up Stripe the night of Nov 4)
Done:
- The account was created and "Activate payments" submitted (sole proprietor, CAD bank; verification pending a few days).
- Category: SaaS - personal use. Stripe Tax OFF, free Radar only, no Climate.
- Billing settings (on the LIVE account):
  - Upcoming renewal events 30 days (45 not offered).
  - Renewal, expiring-card and failed-card emails on.
  - Card updates on the Stripe-hosted page; manage-subscription link on.
  - 3D Secure for Radar matches, plus confirmation emails at 3/5/7 days.
  - Incomplete 15 days = cancel. Smart Retries; all retries fail = cancel.
- Sandbox secret key saved in Supabase > Edge Functions > Secrets as STRIPE_SECRET_KEY.

To do:
1. DONE Nov 5: SUPABASE_ACCESS_TOKEN saved as a GitHub secret (Supabase token "github-deploy", project TheGearFox only:
   Project Settings Read, Edge Functions + Edge Function Secrets Read-write). EXPIRES 2027-10-24 (Bastien; the review screen said Nov 4): renew before. Backend told to run the key test.
2. Public details. Check they're filled:
   - statement descriptor THEGEARFOX.COM;
   - support hello@thegearfox.com;
   - terms https://thegearfox.com/terms.html, privacy https://thegearfox.com/privacy.html;
   - mailing address + phone (Québec requires them; a Google Voice/Fongo number is fine).
3. Customer portal: cancel at end of billing period, no retention offer, no required reason.
   He may not have saved this yet: ask him.
4. A USD payout account (Settings > Bank accounts and currencies) once verified.
5. DONE Nov 5 (SANDBOX): destination "fox-pro-webhook", 8 events, STRIPE_WEBHOOK_SECRET saved in Supabase; test checkout.session.completed = 200 OK. LIVE account: same steps before Dec 2 (its own whsec_).
6. Tax (answered by growth Nov 5, from CRA + BC rules; Bastien to confirm 2 facts: not already GST-registered, and his OTHER self-employed taxable revenue + Gear Fox stays under $30k/yr): GST small supplier (<= $30k worldwide taxable revenue, associates included, single quarter and last 4 quarters) = no GST registration, no GST charged. BC PST: Fox Pro likely counts as software (watchlist/alerts = functionality beyond viewing; PST 105 + telecom bulletin), but small seller (<= $10k gross retail sales in past AND next 12 months, PST 003) = no registration. QST specified registration only past $30k to Québec consumers; US states $100k+. Checkout = "$36/year. No tax added." Stripe Tax stays off. Watch: Pro revenue past/next 12 months vs $10k (BC, ~142 paying members at $45 after the 100 founders) and all revenue vs $30k. Accountant still at income-tax time.
7. Branding LATER (Bastien: "we can do the logo later"). Designer spec:
   - brand + accent #0C241D (forest, not charcoal/orange);
   - icon = docs/fox-pro/fox.png on a forest square;
   - logo = site/logo-mark-dark.svg as a PNG;
   - product image 1024x1024: forest, fox, "FOX PRO", a gold #D9B25C rule + "FOUNDING FOX", no price.
   It goes through the designer first.

Checkout spec, sent to backend Nov 5:
- Hosted full page, locale fr for FR.
- Product name "Fox Pro, Founding member" / « Fox Pro, membre fondateur ». The founding # is assigned after payment.
- Terms checkbox (consent_collection).
- The renewal + refund text above the button, EN/FR, from compliance.
- Never "$3/month" at checkout. automatic_tax off.
- Our own purchase email carries the terms.
- Our own renewal reminder 45 days before (Resend), since Stripe's can't be timed.
- Referral/race codes add TIME (13-month first year; +1 month to the referrer after the friend's first payment clears),
  never a price cut. Codes are created by backend, not by hand.
- Stripe description (CMO): "Same-morning drop alerts, unlimited watchlist, full price history, and we watch what you bought for a price drop."

### Stroller deal video (Nov 5)
- The deal: Thule Urban Glide 3 Single, Midnight Blue only, $449.98 CAD (was $899.95, −50%) at Bushtukah, which ships to Canada
  only. It was $899.95 every day Oct 2 - Nov 3 (our history).
- Final video: format 2 in docs/social-formats.md. Files were in the old chat's scratchpad (stroller-sss-en/fr.mp4); remake them from the template if needed.
- Livecheck the price before he posts. No USD version: the US has no comparable deal, and Bushtukah doesn't ship to the US.
- Running strollers STAY on the site as gear (Bastien's yes). Backend makes it consistent at every store and fixes the
  "Lights, poles & bottles" label + the \bglide\b rule. A "Running strollers" type goes in the Nov 16 batch.

### SEO batch (L2/L3 + #12-14, designer-passed)
Backend was applying 3 last wording fixes and pushing Nov 5. Spot-check the live pages after the deploy:
- shoe-page "On sale now" pills (FR 320px);
- BF page top pill row;
- gift page box;
- homepage block "Black Friday 2026 shoe deals" / « Aubaines du Vendredi fou 2026 ».

### Tests (decided Nov 4-5; all logged in docs/decisions.md)
- run1st ENDED (A). cards2 ENDED (A, phones-only p=0.674). alts runs to Dec 23, judged on sign-ups.
- 'look2' from Dec 7, phones 50/50: the GPT redesign's pieces on our cards. docs/look2-draft.css; metric store clicks 33% -> 38%.
- 'heartonly' from Dec 7, its own coin: a heart in the photo corner instead of "♡ Watch price" words (Bastien OK'd testing it).
  docs/heartonly-draft.css. It works only if B roughly doubles Watch taps (2% -> 4%, ~1,140/group); decide ~Dec 24.
- Preview of both: https://claude.ai/artifact/EoxH6wPt1SoFr6SVDbV8pa

### Nov 16 batch (needs a preview + his OK)
- "Add gear to watch" box in the watchlist: type gear, it's watched in your sizes everywhere; shoes watch the page key.
  Judged on members watching 1+ (38/150 on Oct 31). Preview before Nov 14.
- "Running strollers" type.
- The team's sign-up ideas (docs/signup-ideas-nov4.md).

### Testimonials
- Bastien asked the 2 buyers (compliance's ask: names every use, preview + takedown, nothing in return).
- When they reply:
  - check "saved $X" against our history, else write "paid $Y, regular $Z";
  - write the quote for their OK;
  - keep a PRIVATE consent record, never in the repo.
- First use: the founding-list ask (from Nov 17) + the Dec 2 founding email. Site quotes = an A/B test in January.
- Friday email line "Bought something you found here? Hit reply and tell us." went live Nov 6, with Reply-To hello@.
- Stop rule: fewer than 3 usable quotes by Nov 20 = founding emails go without quotes.

### People
- **Andrew Farny** (Rossmonster = Colorado campervan builder; a fan, not a partner): emailed unprompted asking for exactly Fox Pro.
  Bastien replied Nov 5 (teased 2 features + a version of his idea, asked how he found us + what he'd watch first, offered the early list).
  If he says yes: send the full-feature follow-up (in the old chat; rebuild it from the Fox Pro features + compliance-approved
  price wording). Never add him to a list without his yes.
- **Kirsti** (Sinister Sports): waiting. Nudge Nov 10, plus the Lewiston / 5 Peaks emails by Nov 10 (scheduled task).
- **UTFS** (Ultra-Trail du Fjord du Saguenay): Bastien drafted a FR call ask Nov 5; it's in the tracker. Mark sent when he says so; follow up ~Nov 19.
- **RunFree** follow-up Nov 11. **Fat Dog** (Erik Bird) Nov 18. Both are scheduled tasks.

### Stores / data
- **Sport Chek OFF** (403 twice Nov 4). A Grab-deals bookmark version would cross the line (sizes come from the refused
  service), so it's not built. It waits for the Impact feed or store_recheck.
- **Grab deals bookmark:** updated Nov 2. Bastien re-added it Nov 4. Different stores can run in parallel tabs; never two tabs on one store.
- **US junk cleared Nov 4:** PowSlayer, jewelry, Gazelle soccer (one Brazil jersey fixed by a name rule).
- **Morning timer:** Nov 4's 11:17 UTC start got no answer from GitHub (pg_net timeout). Bastien pasted the 12:47 backup
  (gear-fox-morning-backup). Backend's supabase/dispatch-log-nov4.sql (20 s timeout + log): pasted Nov 5.
- **Dashboard key:** stats.html fixed (only P0001 says "wrong key"). supabase/dashboard-timeout-nov4.sql: pasted Nov 5.

### Bastien's to-dos
- DONE Nov 5: pasted dispatch-log-nov4.sql + dashboard-timeout-nov4.sql (both Success). Part 1: dashboard call mean 788 ms, max 4,117 ms
  (over anon's old 3 s limit = the "wrong key" bug); anon/authenticated now 10 s. Check tomorrow's morning start in gf_dispatch_log.
- Check the "[TEST]" Friday email bottom line and reply once, to confirm replies land in hello@.
- Emails: the 8% emails to Le Coureur Nordique and Run Uphill; Heads or Trails; Iron Legs.
- Stripe items 1-6 above, then the accountant.
- Reddit: r/ultrarunning dropped Nov 4 (no traction). The Reddit rotation continues Mon/Wed/Fri.

## Scheduled tasks (moved to the new growth chat Nov 5)
- Night shift 0:23am (5-10 growth + backend jobs a night; docs/night-shift.md; Bastien Nov 5).
- Daily improvement round 5:43am.
- Nightly SEO push 1:07am.
- Reddit rotation Mon/Wed/Fri 6:15am.
- Monday check-in 7:47am.
- One-time:
  - Kirsti Nov 10;
  - RunFree Nov 11;
  - Fat Dog Nov 18;
  - Resend upgrade Nov 18;
  - Fox Pro readiness Nov 27.
- Backend-chat tasks (Fox Pro step 1 verdict Nov 17, the redesign before/after check, the FKT bounty prep Dec 1,
  the r/RunningShoeGeeks reminder Nov 7) stay where they are.
