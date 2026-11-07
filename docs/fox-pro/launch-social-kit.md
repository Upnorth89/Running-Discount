# Fox Pro launch: social kit, Nov 17 - Dec 4 (draft, Nov 7 night; social-producer + CMO judgement; compliance + CMO passed with fixes Nov 7; designer still to pass)

Compliance + CMO (Nov 7): store list updated to the 10 confirmed stores (Sporting Life out for Nov 17-Dec 1: its rule excludes Black Friday; REI out: US + saved pages only; Running Room = no); pitch moved into the first 3 s ("Tell Fox Pro what you bought. We watch the price for you.") in the hook text and the first spoken line; hook no longer reads as "you get $Z back"; "From Dec 2" now carries "the list hears first if that date moves" (readiness bar can push it to January); "$45/year after" -> "from spot 101"; store conditions quoted in full; music from Instagram's licensed library only; no Paid Partnership label needed (no store pays us) but required the day one does. Not a legal opinion: the example's "full price" (D0) logic is sound but a lawyer should see the Pro terms before Dec 2 as planned.

Existing formats only (docs/social-formats.md): 2b one-item TALK card + 3 green screen for the Reel; Story = a still of that card + the
agreed founding-card Story version. Nothing here is posted or built. Bastien posts; Instagram is ENGLISH ONLY (his Nov 5 rule), so the FR
caption below is for the record (Facebook/site), not for Instagram.

## Gates (nothing goes out unless all hold)
- **Nov 16:** Bastien OKs the Fox Pro preview. No OK = no Nov 17 Reel/Stories (nothing changes publicly).
- **"I bought it" must exist in the preview** (backend piece #5, dry run due Nov 13-15). If it isn't built, the Reel still works (it only
  says "from Dec 2"), but don't show any Pro screen that doesn't exist.
- **Real example only** (procedure below). No qualifying item that morning = no example Reel that day; post Story frame 2 only.
- **Nov 27 readiness bar fails** = Dec 2 pieces cancelled; Story line instead: "Fox Pro will open in January. We'll email the list first.
  Nothing to pay before then." (agreed copy, founding-ask doc).

## 1. Reel, Tue Nov 17: "I bought it" (format 2b TALK card + green screen)
Why this one (CMO): the pitch is concrete money ("you paid full price, it dropped, the store's own rule lets you ask"), the CTA is free
(join the list, nothing to pay), and it's the feature Bastien called the best one (decisions Nov 6). Honest size: Instagram brought ~70
visits in October; expect a handful of list joins, not dozens. Email does the heavy lifting (members plan). Keep his time <= 20 min.

### Fill the real example that morning (data-auditor checks before Bastien films)
1. **Store:** only one of the 10 stores confirmed to adjust their own price drop (docs/price-adjust-table-nov6.md, incl. Bastien's Nov 6 screenshots). Prefer
   Altitude Sports (15 days; Black Friday: orders Nov 2-19 covered until Dec 7), BlackToe (14 days, store credit, claim while the sale is
   still on) or Foot Locker CA (14 days). Avoid JD Sports in Nov (its rule excludes "limited-time or special-event sales"), Sporting Life from Nov 17 to Dec 1 (14 days, but its rule
   excludes "Black Friday, Cyber Monday… limited-time savings events"; fine outside those events), REI (US, read only from Bastien's saved pages),
   Running Room (excludes sale prices: a NO), Decathlon (our
   check can't read its page reliably), US stores (audience is Canadian). Re-read that store's policy page the same morning; quote its words.
2. **Item:** in men's 11 or M (demo profile), on sale today at that store, `scraper/livecheck.py still_on_sale` = True on the store's own
   page in CAD, with that size in stock.
3. **The full-price day (D0):** from `prices.jsonl` (history branch): the last day the item's best price across our stores was >= that
   store's regular price today. History is best-across-stores, not per store: if the best anywhere was the regular price, that store was at
   full price too. Data-auditor confirms the store's regular price didn't change since D0 (else don't use it).
4. **N = days from D0 to today**, and N must be <= the store's window. Z = regular - today's price. Real drop rule: 10% or $10, >= $5.
5. Fill: {Brand Model}, {D0}, {N}, {X} regular, {Y} today, {Z} difference, {Store}, {W} window, {store condition} = ALL its conditions from its own page (e.g. Altitude: "same colour and size, as gift card balance";
   BlackToe: "as store credit, while the sale is on"; Foot Locker: "certain exclusions apply"). Every number from steps 1-4; nothing rounded up.

It is a "say you bought it" example. Never say Bastien or anyone bought it, got money back, or "saved $Z" (rules: never imply he owns the
product; no claims we can't back).

### The card (template docs/formats/one-item-guess-the-price.html, s=b, as in 2b)
- Title block (orange): "{N} DAYS LATER" (a fact the numbers prove, like "HALF PRICE"). Sub line: "{kind} · Canada".
- Photo card, name, CA badge, regular {X} struck, green {Y}, pill "−${Z}" (dollars, not %: the difference is what you'd ask for;
  designer to OK the pill text change).
- Grey line: "Full price {D0} · {Store}".
- Fixed small line under the card (inside the cream panel, above y 1520): "Price adjustment: {Store}'s own rule, {W} days. The store decides."
- Burned hook, top of the panel (never in the 218 px top / 400 px bottom bands), two lines: "Paid full price?" / "Tell Fox Pro. We watch the
  price for you." (CMO: the pitch must be readable in the first 3 s; the number lands on the card itself.) Never "−$Z back" or "you save".
- End card: same dimmed logo card + "LINK IN BIO".

### Timing (2b: card while he talks, fade, end card)
| Time | Picture | He says (EN) |
|---|---|---|
| 0-1 s | Reaction open: his "wait, what?" face full screen, hook text already on screen | (nothing) |
| 1-14 s | He shrinks bottom-right (~1/3 height, never over photo/price/pill, above the bottom band) over the card | "Bought it at full price? Tell Fox Pro, we watch the price for you. This one: {N} days later, same store, {Z} dollars cheaper, and {Store}'s own policy lets you ask for the difference. We email you how to ask. The store decides. Opens December 2nd; the founding list is open now, link in bio." |
| 14-14.5 s | fade | stops talking |
| 14.5-18 s | End card, logo + LINK IN BIO | (nothing) |
About 50 words = ~16 s; the card runs as long as he talks (2b is 13 s; up to ~17 s is fine). Auto-captions on, quiet music from Instagram's own licensed library only (business account).
Cover: the card (not his face), moved down so the 4:5 grid crop shows it whole (as 2c).

### Caption (EN, the one posted)
Paid full price for {Brand Model} on {D0}? {N} days later it's ${Y} at {Store}, ${Z} less (men's 11 in stock this morning). {Store}'s own
policy: price adjustment within {W} days{, store condition}. Tell Fox Pro what you bought: from Dec 2 it checks the price every morning and emails you how to
ask the store for the difference. The store decides. 👀 (Dec 2 is the plan; if it moves, the list hears first.)
The founding list is open: 100 numbered Founding Fox spots at $36/year, price locked while you stay ($45/year from spot 101). Free to join, nothing
to pay now. Link in bio 🦊
Prices can change: check the store before you buy.

#runcanada #runningdeals #trailrunning #runninggear #pricedrop

### FR (record only; not for Instagram)
Payé {Brand Model} plein prix le {D0} ? {N} jours plus tard, il est à {Y} $ chez {Store}, {Z} $ de moins (pointure 11 en stock ce matin).
La politique de {Store} : ajustement de prix dans les {W} jours{, condition}. Dis à Fox Pro ce que t'as acheté : dès le 2 décembre, il vérifie le prix chaque
matin et t'écrit comment demander la différence au magasin. La décision revient au magasin. 👀 (Le 2 décembre est prévu ; si la date change, la liste le sait en premier.)
La liste fondatrice est ouverte : 100 places numérotées de Founding Fox à 36 $/an, prix garanti tant que tu restes membre (45 $/an
à partir de la 101e place). Gratuit, rien à payer maintenant. Lien dans la bio 🦊
Les prix peuvent changer : vérifie chez le magasin avant d'acheter.
#course #courseapied #coureur #quebecrunning #aubaines

## 2. Two Story frames (Nov 17, after the Reel; repost Nov 24 with a fresh example only if one qualifies)
- **Frame 1:** a still of the Reel card (s=b) + an Instagram text sticker in the cream panel: "Bought it at full price? Tell Fox Pro, we watch
  the price for you. Opens Dec 2. The store decides." No link (the link lives on frame 2).
- **Frame 2:** the agreed founding card, Story version (card 1 without button / free line / No thanks; founding-ask doc), link sticker
  "Nothing to pay now" -> founding-list landing with ?ref=ig-story-pro. Never "spots left" on Nov 17 (nobody can pay yet). From Dec 4 a
  "Founding spots left: N" line only with the real live count at posting time (content calendar rule).

## 3. Dec 2 "Founding Fox #001" Reel: idea only, and only if it's literally true
- Use it ONLY if Bastien's own payment is the first LIVE payment and My account really shows Founding Fox #001. The Nov 6 test payment
  (#1, test mode) does not count; backend must make sure live numbering starts at 001 with no test row in it (badges README: test numbers
  never use real ones). If anyone else pays first, he isn't #001: no #001 Reel (his real number only).
- He must keep it: a refund within 30 days puts the number back, which would make the Reel false.
- Say who he is: "I'm the founder, and I paid like everyone else." Not social proof (it's his own business), so CMO's call: weak alone.
  Best use = the 1.5 s payoff-first opener of the already-planned Dec 2 Founder Reel (content-calendar-nov4.md), showing the real badge
  (founding-badge-base.png + live number), then that script as written. Badge shown as an EXAMPLE of what founders get, not a count.

## Compliance must check (before Bastien sees the final)
1. Hypothetical example: "say you bought" framing, no "you get $Z back", no "saved"; "The store decides" on screen AND in the caption.
2. The store's rule quoted from its own page the same day, with its conditions (gift card / store credit / same colour and size /
   no final sale); naming the store = factual reference, no endorsement implied.
3. "Full price" = the store's own regular price, shown that day on its page (Competition Bureau ordinary-price rules); D0 backed by history.
4. Future tense for Pro ("from Dec 2", "planned"): nothing paid or working before then.
5. Price lines: "$36/year ... locked while you stay", "$45/year after", "100 numbered spots", never "$3/month" as headline, "for life",
   countdowns or "spots left" without a live count. "30-day full refund" only once the terms are final.
6. Dec 2 #001: true, disclosed as the founder, not refunded.
7. Instagram branded content: no store pays us, so no Paid Partnership label; the day any store/affiliate link pays, add the label + disclosure.
8. "Opens Dec 2" is a plan, not a promise: caption says the list hears first if it moves (Nov 27 readiness bar).
Designer: frames at start/middle/end (hook line, pill text, the fixed "store decides" line, his inset never over price/pill).

## Links + what to measure
| Piece | Link | Measure (funnel FOX PRO + by ref; Instagram insights) |
|---|---|---|
| Reel Nov 17 | bio link https://thegearfox.com/?ref=ig-reel-ibought (backend: confirm which URL opens the founding card for a NON-member; `?pro=1` was the old test card) | first visits, pro-join, sign-ups by ref; Reel views, 3-s hold, shares, saves, bio taps |
| Story frame 2 | https://thegearfox.com/?ref=ig-story-pro (same landing check) | link taps, first visits, pro-join |
| Dec 2 Founder Reel | ?ref=ig-reel-founder (content calendar) | paid founders by ref (Stripe + profile ref) |
Keep/stop: an IG piece needs >= 1 sign-up or list join per 50 first visits (content-calendar rule). Reel + Stories < 3 list joins by Nov 30
= don't remake the example Reel for Dec 4; reuse the Founder Reel only. Note the ref mismatch: content-calendar-nov4.md says
ig-story-founding, the final founding-ask doc says ig-story-pro; this kit uses ig-story-pro (the newer doc).

## Open for Bastien (yes/no, after the marketing pass)
1. Reel title "{N} DAYS LATER" + "−$Z" pill on the 2b card? (team pick)
2. If no store/item qualifies on Nov 17: Story frame 2 only, Reel moves to the first day one qualifies (by Nov 24)? (team pick: yes)
3. Dec 2: pay first in live mode to be Founding Fox #001 (only if you're happy keeping it)?
