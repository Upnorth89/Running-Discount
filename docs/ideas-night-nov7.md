# Out-of-the-box idea, night of Nov 7 (growth). Not built: needs Bastien's OK.

## "Forward your order email": I bought it, with one tap
**Idea:** a member forwards the store's order-confirmation email to hello@thegearfox.com and we start the "I bought it" watch for them
(item, size, price paid, date, store all sit in that email). No form to fill.

**Why (evidence, our own numbers):**
- Manual steps after a store visit don't get done: the "Didn't buy it?" card got 382 views and 0 taps; the come-back sign-up bar got 612 views and 0 sign-ups (both removed Oct 22, docs/decisions.md).
- "I bought it" needs 4 facts (item, size, price, date) typed on a phone; the store's own email already holds all of them.
- Price protection is free for members until Dec 1 (Oct 27 decision), so it can be tested before Pro exists.

**1-week test (Nov 13-20), no code:** one line in the Nov 13 Friday email (EN/FR, compliance first): "Bought running gear at full price this week?
Forward the order email to hello@thegearfox.com and we'll watch its price for 14 days." Bastien/growth handle forwards by hand
(look up the item on the site, add the watch, reply "Watching it until {date}").
**Metric:** forwards received from ~165 members. **Stop rule:** fewer than 3 forwards by Nov 20 = drop it (manual entry stays).
3 or more = spec an inbound parser for the Pro build (Dec+), and use the replies as "I bought it" testimonials.
**Cost:** ~10 min of Bastien's time per forward; privacy page must say what we keep from a forwarded email (compliance).
**Overlap check:** not in docs/decisions.md; members-lead's Nov 13 email adds only the "watch one thing" box, so this would be a second line: needs his yes.
