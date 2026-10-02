-- The Gear Fox: start the morning refresh on time.
-- GitHub's own schedules often start hours late (Oct 1, 2026: 6 hours). This timer runs inside Supabase at
-- 11:17 UTC (4:17am Vancouver in summer, 3:17am in winter) and asks GitHub to start refresh.yml right away
-- with morning=true. GitHub's schedules stay as a backup; the workflow's "check" job skips any morning run
-- once today's report went out, so nobody gets two health emails.
--
-- Needs a GitHub key in Vault named github_dispatch_token (fine-grained token, only the Running-Discount repo,
-- permission Actions: Read and write). It expires 2027-09-29: make a new one before then and replace the Vault value.
-- Paste into Supabase > SQL Editor once.

create extension if not exists pg_cron;
create extension if not exists pg_net;

create or replace function public._gf_start_refresh()
returns void language plpgsql security definer set search_path = public as $$
declare k text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'github_dispatch_token';
  if k is null then raise exception 'github_dispatch_token is missing from Vault'; end if;
  perform net.http_post(
    url     := 'https://api.github.com/repos/Upnorth89/Running-Discount/actions/workflows/refresh.yml/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'thegearfox-supabase',
                                  'Content-Type', 'application/json'),
    body    := jsonb_build_object('ref', 'main', 'inputs', jsonb_build_object('morning', 'true')));
end $$;
revoke all on function public._gf_start_refresh() from public, anon, authenticated;

-- (re)create the daily timer
select cron.unschedule(jobid) from cron.job where jobname = 'gear-fox-morning-refresh';
select cron.schedule('gear-fox-morning-refresh', '17 11 * * *', 'select public._gf_start_refresh()');

-- Test (optional): start a run now, then look at GitHub's answer a few seconds later. 204 = accepted.
-- A test run after today's morning report stops at the "check" step, so it sends nothing.
--   select public._gf_start_refresh();
--   select status_code, content from net._http_response order by created desc limit 1;
