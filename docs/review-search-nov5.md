# Daily site review: SEARCH (Thu Nov 5, 2026), designer

Live site https://thegearfox.com/, 390px phone (Chromium, Python Playwright), first visit, men's 11 / M. Supabase/Umami/analytics blocked, NO_KEEPALIVE on, no sign-up.
Screenshots: /tmp/claude-0/-home-user-Running-Discount/82d55ccc-8e40-5723-b11a-15fe426eb537/scratchpad/search-nov5/ (NN-query.png = first screen, -full.png = whole page; results.json = counts).

| Query | Cards | What shows | Verdict |
|---|---|---|---|
| pegasus | 4 sale + 7 full price | 4 "Prices →" shoe-page boxes fill the whole first screen; "Results" (4) starts below the fold; then "Shoes 7" at full price, no label saying so; headline "4 deals in your size" | relevant; first deal below the fold |
| speedgoat 6 | 3 | GTX, base, Mid GTX | good |
| vaporfly | 1 | "Nike Vaporfly 4 Road Racing Shoes" (name not tidied) | ok |
| running jacket women | 0 | "No exact match… Closest: Nike Stride Repel…, 2XU Aero…, Running Room Balaclava Jacket…" + grey box "Nothing matches right now. Try clearing the search or picking more categories." Headline still "2,184 deals in your size." | BUG: sale.json has 33 women's running jackets on sale; the men's fit hides them and nothing says so |
| trail shoes | 78 + 188 | good results; headline still "2,184" | count line wrong |
| arcteryx | 16 + 93 | Arc'teryx only, spread by category | good |
| gel nimbus 28 | 2 (full price) | no sale, no "nothing on sale" line; second card "ASICS GEL-NIMBUS® 28 Sunny Sizzle" (® + colour = duplicate card); headline "2,184" | data tidy + count line |
| hoka bondi 9 wide | 0 | "Nothing in your size … but 2 in other sizes. Show all sizes" + the same grey "Nothing matches… picking more categories" box | two empty messages, second gives wrong advice |
| souliers trail | 78 | same as "trail shoes" | good |
| empty box tap | A: nothing; B (?exp=popq:B): "Popular right now" chips EVO SL / Alphafly / adidas / rabbit / norda / Hoka | B clean, no overlap |

No collisions (visual_check.collisions) on any screen, no script errors, nothing wider than 390px. NNormal Tomir 2.0 Trail card had a blank photo on the "trail shoes" first screen.

## Biggest problems
1. BUG, empty state (05-running-jacket-women.png, 09-hoka-bondi-9-wide.png): when a search finds no sale deal in your size the page shows two messages; the grey one ("Try clearing the search or picking more categories") is wrong advice (no category was picked) and the headline above still says "2,184 deals in your size." For "running jacket women" the real reason (the visitor's fit is Men's; 33 women's running jackets are on sale) is never said. Baymard (no-results pages): say why nothing matched and offer a way out; NN/g: error messages must say what happened and how to fix it. Smallest fix: hide `nothing` when searchHelp() already shows a line; when the query names the other gender, line: "You're seeing men's sizes. Women's running jackets on sale: 33 [Show women's]" / « Vous voyez les tailles hommes. Manteaux de course femmes en solde : 33 [Voir femmes] ». Headline = the search's count while a search is active ("0 deals for “…” in your size" / « 0 aubaine pour « … » à votre taille »).
2. IMPROVE, model search (02-pegasus.png): 4 full-width "Prices →" boxes take the first 390x300px; the first deal photo starts at y≈710. Smallest fix: one box only ("All Pegasus models: every size, every store →" / « Tous les modèles Pegasus : toutes les tailles, tous les magasins → ») or put the boxes after the Results row; and label the full-price block "Full price: watch for a drop" / « Prix régulier : surveillez une baisse ». Baymard: search results should put matching products first.
