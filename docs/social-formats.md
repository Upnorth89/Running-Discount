# Social video formats (keep them the same every time)

Bastien, Nov 5: "We need to stay on the same style." Every deal video follows ONE of these formats. Never invent a new look
without asking him first. Every video passes the designer agent (frames at start/middle/end) and its words pass compliance.
Prices are re-checked on the store's own page (livecheck) the day it's posted. Make no claims we can't back up.

## 1. Super Shoe Sunday (Bastien's series, made by him; reference file he sent Nov 5: super-shoe-sunday-2-fox-en.MOV)
1080x1920, 30 fps, about 23 s.
- **Frame:** dark bands #141F1A, 218 px top and 400 px bottom (Instagram covers them). Cream panel #F9F4ED between them.
- **Title:** orange #E2652A rounded block (x 157-923, y 240-365), "SUPER SHOE SUNDAY" in Barlow Condensed 800, white.
  Under it, grey #6F7671 Inter 42 px: "Guess the price · Canada + USA".
- **Six rows, about 170 px each.**
  - Left: the product photo on a white rounded card.
  - Right: the name (Inter 800), a dark CA/US badge, the regular price (Barlow, grey #5E6762) and a black "???" box.
- **Reveal, row by row:**
  - the regular price struck through with a red line (#C8352A);
  - the sale price in big green #1F9256;
  - a green "−33%" pill at the right;
  - a small grey line: "Women's · 7 sizes · Store".
- **End:** the screen dims (rgba(20,31,26,.88)), with a white rounded card holding the main logo (site/logo.svg), then
  "LINK IN BIO" (Barlow 800, white), "Deals in your size, Canada & USA" and "thegearfox.com".
- He films himself with a green screen over it (see 3).

## 2. One-item "Guess the price" (same style, for a single standout deal; made Nov 5 for the Thule Urban Glide 3 stroller)
- **Template:** docs/formats/one-item-guess-the-price.html (?l=en|fr &s=a|b|c). Put the product photo next to it as
  product.png, and never commit store photos (the repo is public).
- **Title block:** "GUESS THE PRICE" / « DEVINEZ LE PRIX », or a series name if Bastien gives one.
- **Sub line:** "<kind> · Canada".
- **Layout:** one big photo card, then the name, the CA badge, the price and ???. Reveal (s=b) = struck price, green price, green
  −% pill on the name line, "Colour · Store" line. End (s=c) = the same dimmed logo card as Super Shoe Sunday.
- **Render:** Playwright 1080x1920 screenshots, then ffmpeg:
  - a = 5.4 s (he talks over the ???);
  - xfade wiperight 0.35 s at 5.0;
  - b = 5.5 s;
  - fade 0.5 s at 10.0;
  - c = 3 s.
  - Total about 13 s.
- **Rejected on Nov 5:** a screen recording of the website ("I don't want people to just see the website"); a white "showcase"
  with a slow zoom; a light green-screen layout ("doesn't even look like what we've done before"). Stay on format 1/2.

## 2b. One-item TALK card (Nov 5, Bastien: "simply have the card with the stroller, give me 10-15 seconds to talk about it and then we can show gearfox link in bio")
- Same template as format 2 (docs/formats/one-item-guess-the-price.html), price already shown (s=b), no ??? step.
- Title block states a fact instead of "Guess the price": e.g. "HALF PRICE" / « MOITIÉ PRIX » when the drop is exactly 50%. Only a fact the numbers prove.
- Timing: card 13 s (he talks), fade 0.5 s at 12.5 s, end card (logo + LINK IN BIO) 3.5 s. Total 16 s.
- First made for the Thule Urban Glide 3 Single (Bushtukah, $449.98, was $899.95; livechecked Nov 5 13:30 UTC). Files: out/stroller-en.mp4, out/stroller-fr.mp4 (not committed).

## 3. Green screen (how Bastien films)
- **Background:** Instagram Reels → Effects → Green Screen → pick the video. Or CapCut: video first, his clip on top
  → Remove background / Chroma key.
- **Where he sits:** small, bottom-right, about 1/3 of the height, under the price rows. He never covers the photo, price or ???.
- **What he says:**
  - Hook over the ???: "Guess what this … costs right now."
  - At the reveal: the price + store.
  - He stops talking before the logo.
- **Finish:** auto-captions on, quiet music under his voice. Caption = the facts + "Prices can change: check the store
  before you buy." + Link in bio. Use a ?ref= link per post (e.g. ?ref=ig-reel-stroller).

## 4. Automatic Reels / kits (code: scraper/ig_reel.py, scraper/ig_brief.py; Wednesdays)
Screen recordings of the site with safe bands, payoff first (CLAUDE.md "Instagram Reels"). These are the automatic weekly kit only.
The hand-made deal videos above are separate.

## Caption style (keep it; Bastien Nov 5: "We've had a style of posts. With the Fox emoji etc")
From scraper/ig_reel.py `script()`: one hook sentence with the facts + 👀; one line on how the site works ("Heart anything on The Gear Fox and we watch
the price for you, in your size, at 80+ Canadian stores. Free. Link in bio 🦊"); "Prices can change: check the store before you buy."; blank line;
5 lowercase hashtags (EN e.g. #runcanada #trailrunning #runningdeals + 2 for the item; FR #course #courseapied #coureur #quebecrunning #aubaines style).
FR = Québec, tutoiement, casual ("pis", "fait que"). Store count from today's data (Canadian stores ~83 on Nov 5).

## Things to remember
- Bastien is a new dad (Nov 2026). Compliance-approved hook: "New dad here." FR: « Je viens d'être papa. » Never imply he owns
  the product.
- The demo profile is his sizes: men's 11, clothing M.
- A Halloween video exists, made in another chat. Ask Bastien for it and add it here as a reference.
