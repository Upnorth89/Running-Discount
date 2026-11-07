# Compliance: Fox Pro terms check (readiness bar #5, terms part), night of Nov 7

Verdict: **FIX** (done in docs/pro-terms-draft.md, change list at its top). Terms now carry every launch must, EN and FR saying the same thing. Not legal advice; the open legal points are listed for the lawyer.

## Launch musts vs the terms
| Must | Status |
|---|---|
| Québec CPA distance-contract info (who we are, price, currency, total, renewal, cancel/refund rules, copy within 15 days) | Present. GAP: legal name, mailing address, phone number still blank (§1) |
| Québec Law 10 (Bill 10, in force Sept 12, 2026): easy online cancel | Present (§5): Cancel button in My account, no call, no stay-offers, confirmation email |
| Renewal reminder | Present (§4): 45 days before, never <15 or >45 (California window for yearly plans; inside Canada's 30-60) |
| California auto-renewal (USA side) | Present: renewal terms above the pay button, UNTICKED consent box (§4), cancel online (§5), copy email with renewal terms + how to cancel (§17) |
| 30-day refund of the Fox Pro fee | Present (§6), now says "of your Fox Pro fee"; gear refunds come from the store |
| Founding numbers / refund rules | Present (§3): 100 numbered spots, $36 locked while renewing without a gap; refunded number goes back, cancelled number retired (Bastien to confirm) |
| USD same numbers (US$36/45) | Fixed in FR (was a blank) |
| No tax at launch | Present (§3), matches Nov 5 decision |
| "I bought it" = the store decides | Present (§7); "claim" -> "ask the store"; unknown-policy (14 days) + non-adjusting stores covered; no hard store count |
| CASL | New §9 Emails (ID + address + unsubscribe, no promotion in service emails); §8 referrals: no invite-by-email, disclose the free month when posting publicly |
| Privacy for purchase data | §10: what is kept, never shared/sold, Stripe in the US, delete anytime; retention days blank |
| Governing law | §15: British Columbia proposed; Québec/other consumer law wins; no arbitration, no class-action waiver |
| Changing the terms | §13 now shaped on Québec CPA s.11.2 (old vs new wording, date, right to refuse = end Pro + refund of unused part) |

## Needs Bastien
1. Phone number for §1 (Québec CPA s.54.4 lists one).
2. Legal name + mailing address (§1).
3. Confirm founding-number rule (refunded = back, cancelled later = retired).
4. 30-day refund after each renewal too? (recommend yes)
5. Referral cap: 12 total or per year.
6. Days to fix a failed renewal; refund timing in business days.
7. "I bought it" data kept how long after the window (pick: 90 days).
8. Governing law = BC (pick).
9. Terms URL + store-list page URL.

## Needs the lawyer (before spot 101 / by Jan 31; list of 19 at the bottom of the draft)
Top ones: phone/identity disclosures; pro-rated refund on mid-year cancel (Québec/Ontario); Bill 96 French-first at checkout for Québec members who use English; whether renewal notices/receipts still go to someone who unsubscribed from everything (CASL); Ontario CPA 2023 subscription rules; Law 25 transfer to Stripe (privacy impact assessment); liability cap limits in Québec.

## Still to do outside the terms (before checkout opens)
- Privacy page EN/FR: Stripe, purchase records, retention, Stripe cookies.
- Purchase email (piece #4) must include the renewal + cancel lines from §17; until it exists, live mode must not open.
- Renewal reminder job: send window 15-45 days, never earlier than 45.
