# Mystery shop: thegearfox.com, Nov 7, 2026 (night team)

I walked the live site as three people on a 390px phone, using Playwright with Chromium. Calls to Supabase, Umami and Google were blocked, so nothing was recorded, and I never signed up or paid. The walks:
1. A new visitor arriving from a Reddit link on a shoe page (`/shoes/hoka-clifton-10/?ref=test`).
2. A new visitor on the homepage who picks men's 11 / M.
3. A French visitor on `/vendredi-fou/`, `/vendredi-fou/direct/` and `/?lang=fr`.

I also looked at the Fox Pro founding card (`?pro=1`, with a pretend member, EN and FR) and read About, Privacy and Terms the way a skeptic would. Screenshots are in `/tmp/claude-0/-home-user-Running-Discount/82d55ccc-8e40-5723-b11a-15fe426eb537/scratchpad/ms-*.png`. Raw text is in `.../scratchpad/ms/out.json`.

## What held up (no action)
- **Speed (measured from the sandbox, on a fast network):** the shoe page was usable after 0.7 s. The homepage welcome showed after 1.3 s. The first deal appeared 0.2 s after picking sizes.
- **Errors:** no script errors on any page.
- **Prices:** I checked the top homepage deal on the store's own page. Hoka Cielo X1 2.0 at $130 (was $324.99) at Le Coureur Nordique, size 11 in stock: correct. The card link opens that size's variant.
- **Links:** a sample of 22 links (14 ours, 8 store pages) all answered 200.
- **Stores that are off are really gone:** Sport Chek, Sports Experts and the RunFree shops have no offers left in sale.json.
- **French:** the French pages have no English text apart from brand and store names.
- **Nothing to repeat from Oct 18:** none of the items fixed after the Oct 18 walk came back.

## Issues, by severity (1 = blocks paying, 2 = hurts trust, 3 = polish)

### 1. Nothing tells a payer the Fox Pro terms (severity 1)
**Where:**
- Terms (`ms-terms.png`): the only line about it is "free unless we clearly say otherwise".
- Privacy (`ms-privacy.png`): last updated Oct 4. It says "We don't use cookies" and has nothing about payments.
- Founding card (`ms-pro-card-en.png`): no link to any details.

**Why it hurts:** a runner who is about to give $36 looks for three things: renewal, cancelling, refund. None of them is written anywhere. Stripe checkout also sets cookies, which contradicts the Privacy page. The launch musts already require online cancel, a renewal reminder, terms emailed after purchase and "The store decides".

**Smallest fix:**
- Add a "Fox Pro" section to Terms: yearly price plus tax, auto-renewal with a reminder 30-60 days before, cancel online, 30-day full refund, and "the store decides" for price adjustments.
- Add a "Payments (Stripe)" section to Privacy.
- Add a "Details" link on the card, next to "Planned from Dec 2".

### 2. The Pro card reads as "we're taking things away" (severity 2)
**Where:** the founding card, EN and FR (`ms-pro-card-en.png`, `ms-pro-card-fr.png`).
- "Morning price-drop alerts" is listed as a Pro perk. Members get these alerts free today.
- "Unlimited watchlist (free: 5 from Dec 2)" tells current members their limit falls from 10 to 5.
- "We email you how to ask the store for the difference" has no "the store decides" next to it.

**Why it hurts:** a member's first look at Pro is a list of what they lose. That feels like bait-and-switch and is the opposite of the "keep the hook free" ladder. The price-difference promise also sounds guaranteed when it isn't.

**Smallest fix:**
- Add one line, "Always free: deals in your size, Friday email, 5 watched items, drop news".
- Reword the alerts line to "Same-morning alerts (free members: in the Friday email)", or whatever is actually decided.
- Add "The store decides" to the price-difference line.

**Note:** `?pro=1` shows nothing to a visitor who isn't a member, because the card only replaces a member's sign-up slot. That is by design, but previews need a member profile to see it.

### 3. About page breaks Bastien's Nov 5 wording rule (severity 2)
**Where:** About (`ms-about.png`).
- It says "I'm an ultramarathon runner". The Nov 5 rule is "a runner from Montréal and Vancouver", never "ultrarunner".
- It still says "Heart something" (it's "Watch price" now).
- It says "It's free" with no word about Fox Pro coming.

**Why it hurts:** this is the trust page a skeptic reads before paying, and it doesn't match the person or the product.

**Smallest fix:** change those three lines, in EN and FR.

### 4. Store counts don't agree from page to page (severity 2)
**Where:**
- Homepage "We check 153 stores" and "…and 148 more stores" (`ms-home-welcome.png`); About "more than 150".
- FR Black Friday page: "98 boutiques de course canadiennes", and its stats line "dans 45 boutiques".
- BF deal check page: "83 boutiques" (`ms-fr-bflive-top.png`).

**Why it hurts:** `n_stores` = 153 still counts about 31 stores that are switched off or haven't been read in days: Sport Chek (Nov 3), Sports Experts (Nov 2), and roughly 28 RunFree US shops (Oct 31). On the Canada side, only 83 stores have offers today. A journalist or skeptic who sees four numbers in one session stops believing all of them.

**Smallest fix:** count only stores read in the last 48 h, and say it per side ("83 stores in Canada, N in the USA").

### 5. Underwear shows up as running shorts, and a shoe sits in Gear (severity 3)
**Where:**
- About 40 boxer briefs (Stance, SAXX, New Balance) are filed as bottoms/short and shown as "Men's shorts" / « Short · Homme ».
- "New Balance Premium Boxer Brief" is in the first "Just browse" screen (`ms-home-welcome.png`, behind the sheet).
- "Salomon Glide Max TR Run The Alps" (a trail shoe) is listed under Lights, poles & bottles as "Gear".

**Why it hurts:** a runner who taps Shorts and sees boxers thinks the sorting is careless.

**Smallest fix:** in `tidy_clothes`, file "boxer"/"brief" under underwear or leave them out. In `tidy_gear`, move "Glide Max" to shoes. Add both to sortcheck.

### 6. A store's own banner sits above "Today's top deals" (severity 3)
**Where:** the homepage right after picking sizes (`ms-home-deals-top.png`). A dashed box quotes SAIL's homepage ("Crazy November Deals: up to 50% off!") above the top deals. Our own line under it says most of SAIL's sale items are at 30% off.

**Why it hurts:** it looks like a paid placement, while our BF pages say "no store pays to be listed". It also takes the first screen away from deals.

**Smallest fix:** move it below the first row of deals, or keep only offers where our check agrees with the banner.

### 7. A "real drop" measured from an above-list price (severity 3)
**Where:** the BF deal check page shows Hoka Clifton 10 (women's) as "↓ 79 $ … Était à 189 $".

**Why it hurts:**
- Every store lists it at $179.95-$180. The $189 is Capra's full price on wide sizes, so the drop is overstated by about $9.
- On the shoe page, Capra's $189 rows also appear inside "On sale in Canada" tables with no discount.

**Smallest fix:** cap the "was" price at the item's most common regular price.

### 8. About is missing from the footers where people land (severity 3)
**Where:** shoe, BF and list page footers show only "@thegearfox · Privacy · Terms". About is reachable only through the ☰ menu.

**Why it hurts:** about 45% of first visits land on shoe pages. "Who runs this and how do they make money" should be one tap from there.

**Smallest fix:** add About to `page_foot` in shoe_pages.py.

### 9. Wording polish (severity 3)
- Product names copied as the store writes them: "Ciele NSBTank - Equipment", "Ciele VLVMockneck Shirt", "Merrell Moab Speed 2 Gore-Tex (Available in Wide Widths)", "NNormal Running Socks | Mid-Length · Grey 003", "Saucony Mirage Flow Shoes".
- French dates: "avant le 1 nov." should be "1er nov.".
- The Pro card uses a serif typeface found nowhere else on the site, so it looks like a third-party widget. Leave this to the designer.

## Top 5 to fix before Dec 2
1. Fox Pro terms, privacy for payments, and a link from the card (severity 1).
2. A Pro card that says what stays free, plus "the store decides" (severity 2).
3. About page wording: "a runner from Montréal and Vancouver", Watch price, Pro mention (severity 2).
4. One honest store count per side (severity 2).
5. Boxer briefs out of Shorts, and the shoe out of Gear (severity 3).
