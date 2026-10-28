# Growth -> backend handoff, Oct 28 (Bastien: "Ship it all except the fox pro")

Prototypes from the growth chat, built on Oct 28's live deals.json / sale.json / offers.json. Each needs to become a real
refresh step (daily data, EN/FR pages, sitemap, check.py step, site test). Previews Bastien saw:
night summary https://claude.ai/artifact/GrgkeZBe4ixQFb7gAG82XP, gift page https://claude.ai/artifact/8vHteAbJNpDLc9MKijp8tv

- gifts_prototype.py: `python gifts_prototype.py deals.json en|fr` -> gifts-<lang>.html. Size-free gifts (one size or S/M/L in
  stock), Canada side, under $25/$50/$100: 8 on sale (20%+ off) + 4 full price ("Full price · ♡ Watch the price"), one brand once
  per budget. Known miss: a goodr "Abominable Snow Icon" at $100 full price (likely a multi-pack): filter odd prices.
- deal_check_build.py + deal_check_page.html: "Is it a real deal?" paste a product link -> verdict (real drop by the lowLowest
  badge rule / cheaper at another store in your size / not special / too new) + price per store in your size + Watch.
  build: `python deal_check_build.py deals.json offers.json out/` -> one JSON per store host (52,515 links, ~250 KB gz each).
  Page fetches out/hosts.json then out/<host>.json. Watch/See buttons are placeholders (/?q=...&ref=deal-check).
- shoe_page_mock.html (+ needs pegdata.js shape {men:{img,rows:[[size,price,reg,store,url]]},women:...}): size-first shoe page.
