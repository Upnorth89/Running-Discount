# Running Discount

Running gear and nutrition from stores across Canada (Altitude Sports, The Last Hunt, The Feed, Sea2Sky Nutrition) in one place, filtered to your sizes, with an On sale section. The weekly email (next step) will only push sales.

**How it works:** a GitHub Action scrapes each store's full running catalogue once a day (about 7,000 listings, ~4 min),
merges the same product sold by several stores, writes `deals.json` (~330 KB compressed), and
publishes `site/` to GitHub Pages. No server and no database. Profiles are saved in each
visitor's browser for now.

```
site/index.html        the page (loads deals.json)
scraper/scrape.py      the scrapers -> site/deals.json (+ offers.json, raw per-store data used as a fallback)
scraper/embed.py       bakes deals.json into one HTML file (for the claude.ai artifact)
.github/workflows/     daily refresh + deploy
```

## Put it online (about 10 minutes, $0)

1. Create a **public** repo on GitHub (e.g. `running-discount`) and push this folder to `main`.
2. In the repo, go to **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Go to **Actions → Refresh deals → Run workflow**. About 2 minutes later the site is live at
   `https://<your-username>.github.io/running-discount/`.
4. Optional: add a custom domain under Settings → Pages (about $15/yr for the domain).

After that it refreshes every day at about 4am Pacific. You can press **Run workflow** any time to refresh sooner.

## Run locally

```
pip install -r scraper/requirements.txt
python scraper/scrape.py            # ~4 min, writes site/deals.json
python -m http.server -d site 8000  # open http://localhost:8000
```

## Notes

- GitHub pauses scheduled workflows after 60 days with no commits. Any push turns them back on.
- The Feed is a US store; prices are converted to CAD with the Bank of Canada daily rate.
- If a store fails to scrape, its deals from the previous run are kept.
- Next step for real users: store profiles and emails (Supabase free tier) and send the weekly
  email (Resend free tier, 3,000 emails/month).
