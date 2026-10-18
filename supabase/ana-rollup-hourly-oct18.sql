-- Oct 18, 2026 (Bastien: "Stats from yesterday are gone?"): the dashboard shows yesterday from the nightly totals (ana_daily),
-- which were written once a day at 2:13am Vancouver. Between midnight and 2:13am Vancouver (3-5am in Montréal), yesterday looked
-- empty. Nothing was lost (every event is kept 45 days); this writes yesterday's totals every hour at :05 instead, so the gap
-- is 5 minutes. Rewriting a day is safe (delete + insert). Paste in Supabase > SQL Editor > Run. Safe to run again.
select cron.schedule('ana-rollup', '5 * * * *', 'select public.ana_rollup()');
