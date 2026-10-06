-- The Gear Fox: start the afternoon refresh and the night reads on time (Oct 6, 2026).
-- GitHub's own schedules often start hours late (Oct 5: the 1:17pm refresh started at 6:18pm). Like the morning timer
-- (morning-timer.sql, already in place), these run inside Supabase and ask GitHub to start the job right away:
--   23:17 UTC  refresh.yml with afternoon=true   (4:17pm Vancouver in summer, 12 h after the morning run: fresh prices for
--              after-work browsing + the afternoon check email)
--   08:23 UTC  runfree.yml with night=true        (1:23am Vancouver: RunFree stores + Decathlon, read slowly)
-- GitHub's own schedules stay as a backup; each workflow skips a second start (no double emails, no double reads).
-- Uses the same Vault key as the morning timer (github_dispatch_token). Paste into Supabase > SQL Editor once.

create or replace function public._gf_dispatch(p_workflow text, p_inputs jsonb)
returns void language plpgsql security definer set search_path = public as $$
declare k text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'github_dispatch_token';
  if k is null then raise exception 'github_dispatch_token is missing from Vault'; end if;
  perform net.http_post(
    url     := 'https://api.github.com/repos/Upnorth89/Running-Discount/actions/workflows/' || p_workflow || '/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'thegearfox-supabase',
                                  'Content-Type', 'application/json'),
    body    := jsonb_build_object('ref', 'main', 'inputs', p_inputs));
end $$;
revoke all on function public._gf_dispatch(text, jsonb) from public, anon, authenticated;

select cron.unschedule(jobid) from cron.job where jobname in ('gear-fox-afternoon-refresh', 'gear-fox-night-reads');
select cron.schedule('gear-fox-afternoon-refresh', '17 23 * * *',
                     $$select public._gf_dispatch('refresh.yml', '{"afternoon": "true"}'::jsonb)$$);
select cron.schedule('gear-fox-night-reads', '23 8 * * *',
                     $$select public._gf_dispatch('runfree.yml', '{"night": "true"}'::jsonb)$$);

-- Check: the three timers (morning, afternoon, night) should be listed
--   select jobname, schedule from cron.job where jobname like 'gear-fox-%';
