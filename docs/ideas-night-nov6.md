# Night shift, Nov 6: out-of-the-box ideas (CMO)

## Lane 9 (CMO): "Told to get new shoes? Find that model on sale in your size": a handout for sports physios and pedorthists in Montréal + Vancouver

**The idea (2 lines).** Physios and pedorthists tell patients which shoe model to buy, then the patient goes shopping alone. We give 10 clinics a free one-page EN/FR handout (and the same text for their patient email) that sends that runner to the model's shoe page, `?ref=clinic-<name>`, where "Email me when it drops" already works.

**Why it isn't a repeat.** docs/decisions.md, the Nov 4-5 idea files, creators-nov6.md and the outreach lists cover Reddit, Instagram, creators, podcasts, newsletters, race organizers, run shops and members. No row mentions clinics, physios or pedorthists. This isn't run-club outreach (Bastien isn't in a club; the Sacred Strides idea was dropped). It needs no new page or site feature, so the freeze doesn't block it.

**Evidence (our numbers, funnel Oct 21-Nov 4, docs/signup-funnel-nov4.md).**
- Sign-ups come from asks about one named item: the Watch step brought 23 and the shoe-page "Email me when it drops" box brought 17, so 40 of 69 sign-up events (58%). The generic homepage card converts 0.23%.
- On shoe pages, about 5% of visitors who pick a size sign up (17 sign-ups from 335 size-pickers). A patient with a model already named arrives as that visitor.
- Visitors who arrive looking for something specific stay longer and sign up more. Google first visits: 2% sign up (16 of 850) and 40% came back (Oct 12-19). Reddit browsing: 0.6%, 3% came back.
- No research gives a referral rate for clinics. This test measures it, so expect a small number.

**1-week test (Nov 9-15).**
1. Claude + partnerships (Mon, 0 min of Bastien's time): find 10 sports-physio or pedorthist clinics, 5 in Montréal (FR) and 5 in Vancouver (EN), each with a business email it publishes itself. Claude drafts a 5-line email, writes the handout text EN/FR, and builds a QR code per clinic that points to /shoes/ and /chaussures/ with `?ref=clinic-<slug>`. The handout says "Prices change daily, the store decides", names no clinic, and uses no testimonial. Designer checks the handout. Compliance checks the email (CASL: published business address, relevant to their role, unsubscribe line) and the handout. Everything goes on the Gear Fox Outbox.
2. Bastien (Tue, about 15 min): sends the 10 emails from the Outbox. Optional, about 15 min: on a run, drops printed handouts at the 2 clinics nearest him.
3. Claude (Fri Nov 13 and Mon Nov 16): reads the replies Bastien forwards, plus funnel.yml first visits and sign-ups by `ref=clinic-*`.

**The one metric + success bar.** The number of clinics that say yes (hand it out or send it to patients) by Nov 16. Success = 2 or more. After that, the real outcome is sign-ups from `ref=clinic-*`, and the bar is 3 or more by Dec 1.

**Stop rule.** If 0 of 10 clinics say yes by Nov 16, stop and make no second batch. Bastien sends no follow-up beyond one polite reminder. If clinics say yes but `ref=clinic-*` brings fewer than 20 first visits or 0 sign-ups by Dec 1, stop and log it in docs/decisions.md.

**Cost.** Bastien: 15-30 min in total. Backend: none.
