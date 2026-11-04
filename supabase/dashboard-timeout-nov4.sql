-- The Gear Fox (Nov 4, 2026): the stats dashboard key "works 1 try in 2-3".
-- A wrong key answers in 0.6 s ("wrong key", P0001). The right key runs ana_dashboard over the raw events + today live,
-- which seems to brush the 3-second limit Supabase gives the public (anon) role; the cancelled query then looked like a bad key.
-- Note: a timeout set ON the function doesn't help (Postgres arms the timer when the statement starts, before the function
-- runs), so the limit is raised for the role the site uses. stats.html now retries twice and only says "wrong key" for P0001.
-- Paste into Supabase > SQL Editor.

-- PART 1 (read only): how long does the dashboard take? Copy the result back to Claude.
select calls, round(mean_exec_time) as mean_ms, round(max_exec_time) as max_ms, left(query, 60) as q
from pg_stat_statements where query ilike '%ana_dashboard%' or query ilike '%ana_members%' order by max_exec_time desc limit 5;
select rolname, rolconfig from pg_roles where rolname in ('anon', 'authenticated');

-- PART 2: give the site's public calls 10 seconds instead of 3 (the dashboard, ana_members; sign-ups and watches are quick
-- and unaffected), and tell the API to pick it up.
alter role anon set statement_timeout = '10s';
alter role authenticated set statement_timeout = '10s';
notify pgrst, 'reload config';
