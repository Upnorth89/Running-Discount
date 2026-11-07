# Designer: Fox Pro checkout, founding card, welcome + social kit (Nov 7 night)

Checked live on thegearfox.com (test mode), 320 + 390 px, EN + FR, pretend member (gf-sub stub), Supabase/Umami blocked, no sign-up, no payment.
Screenshots: /tmp/claude-0/-home-user-Running-Discount/82d55ccc-8e40-5723-b11a-15fe426eb537/scratchpad/night7/ (v-*.png = in view, *-card.png = whole card, mock-compare.png = Bastien's A/B mockup).

## Verdict: FIX

## Built vs Bastien's mockup (B cream)
- Built: cream card, FOX PRO + pill, serif title + $36, lock line, 3 ticks (renew / refund / cancel), terms link before the button, auto-renew line, ONE rust button, Stripe line, test-mode line.
- Missing vs B: "Better timing." headline, green price panel, the 3 things you pay for (Bought it? We keep watching / Morning alerts / Unlimited watchlist), fox logo tile, key-value rows (Renews / Reminder / Refund / Cancel), "Retailers decide" line.
- One-rust-button rule: PASS on every screen (checkout + founding card: only .fpcta is rust).
- Overlaps / cut-offs / page wider than screen: none at 320 or 390, EN or FR.

## Fixes (worst first)
1. Checkout card sits ~1,440 px (390) / ~1,600-1,730 px (320) down, under the deals: ?pro=checkout must open with the card first under the header (or scroll to #coCard on load). Someone ready to pay lands on deals. (v-checkout-en-390-top.png)
2. Checkout doesn't show what they pay for: add mockup B's 3 feature rows (forest line icons, bold title + one grey line) between the lock line and the renewal rows. Bastien: "visuals must reflect what people are paying for".
3. Renewal said twice (tick "Renews on Nov 6, 2027 at the same price…" + bold "Renews automatically on…"): replace the 3 ticks with B's rows (Renews / Renewal reminder 45 days before / Refund 30 days / Cancel online, anytime) and keep the one auto-renew sentence above the button. Also removes the FR orphans "avant." and "questions.".
4. Non-member at ?pro=checkout sees nothing at all (no card, no coMember line): show the card with "Fox Pro is for members: sign up with your email first" + the email field. Dead end today.
5. Welcome after paying (?pro=welcome) = the generic orange notice: make it a Pro-world card (cream, forest pill "WELCOME", founding-badge-base.png at 120 px + live number "007" per badges README, receipt line). Name clash: badge says "Founding Fox", FR notice says "Renard fondateur n° 007": copywriter picks one for both. (v-welcome-fr-320-top.png)
6. Button wraps to 2 lines at 320 + 390, EN + FR ("Continue to secure / payment →"): use B's "Continue to payment →" / FR « Passer au paiement → » (one line at 320).
7. Pill text (.fppill CHECKOUT / MEMBRES FONDATEURS) is 10.5 px at 320, 11.5 px at 390: min 12 px (drop letter-spacing to .1em so FR still fits).
8. Add the fox tile (site/icon-512.png, 24 px, radius 6) left of "FOX PRO" on every Pro card, as in B.

## Social kit (docs/fox-pro/launch-social-kit.md): FIX on the spec
- Reel bands 218 top / 400 bottom + fixed line above y 1520: OK.
- Cover: "4:5" is right for the feed, but say it in pixels: key content inside y 285-1635 and x 35-1045 of the 1080x1920 (the profile grid crops to 3:4: y 240-1680; 4:5 feed is the tighter one).
- His inset "~1/3 height bottom-right" = ~640 px tall: above y 1520 it reaches up to y ~880, likely over the price/pill. Cap the inset at 480 px tall and check start/middle/end frames before Bastien sees it.
- Story frames: Stories need top ~250 px clear (not 218) and a reserved empty spot for the link sticker (frame 2: ~y 1250-1480, centred); the spec doesn't reserve one.
- Nothing rendered yet to judge pixels: send the frames when they exist.
