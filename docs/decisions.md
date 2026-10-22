# Decisions log: what we tried, the numbers, what we decided

Bastien, Oct 22: "file these changes and attempts somewhere with the data to make sure we don't or do circle back to them."
One line per thing tried. Before building an idea, look here first: if it's listed as dropped, only bring it back with new data.
Newest first. "Revisit" says when (or what would make us) look again.

## Sign-up and come-back prompts

| Date | What | Data | Decision | Revisit |
|---|---|---|---|---|
| Oct 22 | "Didn't buy it? Watch price" card after a store visit (homepage, since Oct 11) | 382 shown, 0 sign-ups | **Removed** | Only with a new idea for the offer, as an A/B test |
| Oct 22 | Come-back sign-up bar ("Want the Friday email?") after a store visit (since Oct 8) | 612 shown, 264 closed (43%), 0 sign-ups traced to it | **Removed** | No |
| Oct 21 | Sign-up card on the homepage ("Free with your email") | 3,306 sessions saw it, 13 sign-ups, 4 "No thanks" | Kept (it's the main homepage ask) | Rework when the 'look' test ends |
| Oct 21 | "Email me when the X drops" box on shoe pages | 30 of 63 sign-ups came from it | **Kept, our best sign-up spot** | Copy it to more pages (list pages, race pages) |
| Oct 18 | Test 'runcard' ("What do you run in?" on the sign-up card) | 1 vs 0 sign-ups (Oct 21), far too few to tell | Running | Decide ~Nov 15 |

## A/B tests (metric, result, p-value)

| Date | Test | Result | Decision |
|---|---|---|---|
| Oct 21- | 'look' = the redesign (Bastien's rendering: charcoal header, hero search + dropdown filters, category tiles, new cards, phone bar + Filters panel) | Not live yet. Metric: homepage first visitors who tap a deal or pick sizes, baseline ~48%, ~1,100 a group, decide ~Nov 6 | Waiting for Bastien's yes after the preview |
| Oct 18- | 'r100' (card badge "−$66" from $100 regular price, "−30%" below) | Deal clicks B 40% vs A 34%, p=0.46 (65/70 devices, Oct 21) | Running, decide ~Nov 1 |
| Oct 20 | 'drops' ("Dropped today in your size" row) | Store clicks of size-pickers B 21% vs A 62%, p=0.019 | **Ended: A for everyone** |
| Oct 20 | 'welcome' (B skipped the welcome screen) | Picked sizes B 11% vs A 29%, p=0.011 | **Ended: A (welcome screen stays)** |
| Oct 19-20 | 'layout' (search + Filters under the sizes line, swipe tiles) | Bastien chose B after 1 day (not a test result); back to 50/50 Oct 20 | Running |
| Oct 17 | 'card' (cleaner cards, ⋯ menu) | Never ran | Parked (commit 629e4d1) |

## Redesign details (Oct 21-22)

| What | Decision | Why |
|---|---|---|
| Category tile pictures: AI-generated set from Bastien (12 images) | **Dropped** (Bastien, Oct 22: "Let's not use AI generated pics") | Real brands' logos (Hoka, Salomon, Maurten, The North Face…) on products those brands never made; garbled labels ("Solid C160"); looks AI-made, the problem the redesign fixes |
| Category tile pictures: free stock photos | Not used | Bastien's spec bans lifestyle photos; stock shots of branded products suggest deals we may not have |
| Category tile pictures: today's real deals | **Used** | A known brand's item of the kind the tile names (shoe, jacket, vest, cap/gloves, watch); changes with the deals, always real |
| Sticky search + Filters bar and a Filters panel on phones (from ChatGPT's review) | Built | Baymard: keep filtering within reach on long mobile lists |
| One deal per row on small phones (< 380px) | Built | Two columns were cramped at 320px (names cut, "In stock" squeezed) |
| Fixed bottom bar (Home, Deals, Categories, My Sizes) (ChatGPT) | Declined | We're one page: 3 of 4 buttons go where you already are; ~60px of every screen; clashes with Safari's bar and our bottom offers |
| "View deal" button on every card (ChatGPT) | Declined | The whole card is already the button; adds a row per card on a list we're trying to make lighter |
| Brand logos in "Shop by brand" / on cards | Not used | No logo files or permission; brand names in bold type instead |
| Green "In stock" on every card | **Removed** (Bastien, Oct 22) | Everything we show is in stock, so a label on every card says nothing; the size row and the headline ("best prices in stock, in your size") say it once |
| Dark mode for the redesign | **Light only** (Bastien, Oct 22) | His rendering is light; store photos are on white (bright boxes on a dark page); NN/g: dark text on light reads better in normal light |

## Where visitors come from (for growth calls)

| Date | Fact | So |
|---|---|---|
| Oct 12-19 | Reddit: 276 first visits, 1 sign-up, 3% came back. Google: 26 visits, 40% came back, median 76 s | Reddit = awareness; judge site changes on Google/returning visitors, not Reddit |
| Oct 17 | r/BuyCanadian removed our post (3 items) | Don't post there again without asking the mods |
| Oct 12 | A Reddit post with 20 thegearfox.com links was removed by the spam filter | Few links per post, check each sub's rules |
| Oct 19 | Push notifications | Parked: iPhones need the home-screen app first; visitors stay ~20 s |
