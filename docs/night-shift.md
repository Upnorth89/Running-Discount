# Night shift: 5-10 growth jobs a night (growth chat + backend)

Bastien, Nov 5: "Find you and the backend 5-10 jobs per night to grow the business. Either ideas out of the box or things
that we haven't thought about." Scheduled task "Night shift: 5-10 growth jobs" (growth chat, 0:23am Vancouver), before the
Nightly SEO push (1:07am, which keeps SEO). Results go into the 5:43am daily round message (no extra message to Bastien).

## Rules
- 5-10 jobs a night. Mix: at least 2 backend jobs (sent as specs with send_message), at least 3 growth jobs done that night,
  and at least 1 "out of the box" idea (researched, with evidence and a cheap test, never built without Bastien's OK).
- Freeze until Nov 15: backend gets only what the freeze allows (bug/trust fixes, automation that saves Bastien time,
  store readers, Fox Pro behind its switch). Anything visible = spec queued for the Nov 16 batch + preview + his OK.
- Check docs/decisions.md and this log first: nothing already tried or declined comes back unless a NEW fact says so (name it).
- No duplicate of other tasks: SEO = Nightly SEO push; site review = daily round; Reddit = rotation; outreach follow-ups =
  their reminders.
- Every job ends with a result: a file in docs/, a spec sent, a draft ready for Bastien, or "checked, nothing to do" + why.
- Never invent numbers. Cite our funnel/history data or named research.
- Write tonight's row in the log below and commit (docs only; never while a dispatched refresh is pending).

## Job menu (pick across lanes; rotate so every lane comes up each week)
1. Stores (backend, allowed now): 1-3 new readable stores toward 200+ (US first, then Canadian gaps), via the store checklist.
2. Black Friday readiness (both): load time of sale.json on a mid phone, Resend volume on Nov 27, BF pages' numbers, a
   "what if traffic x10" check.
3. Automation that cuts Bastien's time (backend): whatever in the morning email still "needs you" and could fix itself.
4. Fox Pro (backend + growth): checkout/webhook/"I bought it" progress vs the Nov 16 preview and the Nov 27 readiness bar;
   founding-list ask copy (from Nov 17).
5. Data trust (growth, data-auditor): sample live deals vs store pages; any wrong one = bug spec now.
6. Outreach targets (growth, partnerships): NOT race organizers/backlinks (SEO does those). Newsletters, podcasts, creators,
   run shops, Québec French media, gift-guide writers. Real contacts + draft, logged in the outreach tracker.
7. Content (growth, social-producer): next Super Shoe Sunday / one-item video picks from real drops (docs/social-formats.md),
   livechecked the day of.
8. Members (growth, members-lead): what would bring members back this week; Friday email lines; waitlist ask.
9. Out of the box (growth, cmo): one idea we haven't tried, with evidence, a 1-week test and a stop rule -> plan doc backlog.
10. Competitor / market watch (growth): what other deal sites, stores and brands are doing for BF in Canada; one thing to copy
    or avoid.

## Log (newest first)
| Night | Jobs (lane: result) | Sent to backend | For Bastien |
|---|---|---|---|
| Nov 7 (#3) | Team night (11 agents, docs/team-night-nov7/): Mystery shop 'why wouldn't I pay?' (4 store counts on one visit, About 'ultramarathon', boxers under Shorts, Pro card with no terms/what stays free) · Data trust: BF deal check vs 18 store pages, prices right, rule let 12 price rises + 90 young items through, 4 wrong list badges · Compliance: Pro terms 14 fixes, EN=FR, 19 lawyer questions · Designer: test-mode Pro screens · Growth-analyst: founding list ≈28 vs 40 · CMO plan Nov 9-Dec 4 · Social BF calendar · Members Friday emails Nov 13/20/27 · SEO BF/gift pages ready · Partnerships: 6 US press/podcast emails, compliance-checked, on the Outbox · Copywriter: Pro welcome + 3 emails · Out of the box: 'forward your order email' 1-week test (docs/ideas-night-nov7.md) | Trust fixes (1270d27), BF real-drop rule (0dcb8a9), Pro test-mode checkout (13f2c6e): all LIVE | Yes/no: gift links from Nov 8; founding box first in Nov 20/27 emails + stop rule <12; drop r/ultrarunning Nov 27; forward-your-order line in the Nov 13 email. Send the 6 US emails. Paste the founding-numbers SQL |
| Nov 6 (#2) | Data trust: 15 live deals checked, 15/15 prices right, 8 sorting/name bugs (Le Coureur women's B width hidden as narrow: 15 cards) (docs/data-audit-nov6.md) · Outreach FR: 5 Québec targets + FR pitches, compliance-checked, send first Tout.Trail then Noovo Moi (docs/outreach-fr-nov6.md) · BF readiness: Resend free plan 100/day vs ~240 on Nov 27, ~270 Dec 4; no send pacing in code (docs/bf-email-volume-nov6.md) · Out of the box: clinic handout test (10 physios/pedorthists, ?ref=clinic-*) (docs/ideas-night-nov6.md) · Fox Pro: one merged card, team pass (artifact WQRQg7UejGru3uJwWc9EKS) | Pro work order (7 pieces, preview Nov 13) + 10 maintenance jobs; Resend pacing + 429 retry; 8 data-audit bugs; FR BF title « fausses aubaines » trust fix | Yes/no: upgrade Resend to Pro ($20/mo) by Nov 19; ship the merged card + drop tick 1; keep 6-10 watched items on Dec 2; clinic test Nov 9-15; send Tout.Trail + Noovo Moi pitches |
| Nov 5 (#1) | Members: "watch one thing" box for the 116 zero-watch members + BF Friday email lines (docs/members-night-nov5.md) · Content: Super Shoe Sunday Nov 8, 6 rows + 3 backups, post_check + livecheck passed (docs/super-shoe-sunday-nov8.md) · Market watch + out-of-box: Altitude's dated price match (to Dec 7); pick = "Bought it this week? We'll watch it free until Dec 7" for the founding list (docs/ideas-night-nov5.md) · Outreach: 6 new targets + drafts, send first Community Trail Running, then CTV Shopping Trends (docs/outreach-night-nov5.md, compliance pending) | JOB 1 add 2-3 stores; JOB 2 BF load readiness (sale.json 7.66 MB / 9,451 items); JOB 3 PRIVACY: old public run logs print subscriber emails (verify + list, delete on Bastien's yes); JOB 4 Ghost Trail (women's, Boréal) on the road Ghost page | Yes/no: delete old run logs with emails; watch box in Nov 13 email; send pitches 3 + 5 |
