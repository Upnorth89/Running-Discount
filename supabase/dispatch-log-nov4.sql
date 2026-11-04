-- The Gear Fox (Nov 4, 2026): GitHub starts that get no answer.
-- This morning the 11:17 UTC timer ran (cron: succeeded) but pg_net got NO answer from GitHub (status_code and content empty,
-- so a timeout or network error, not a refused key). pg_net waits only 5 seconds by default. This file:
--   1. one helper, _gf_post_dispatch(), that every timer uses: waits up to 20 seconds and writes each start in gf_dispatch_log;
--   2. the morning, afternoon/night, Friday/Saturday and Grab-save starts redefined to use it (same jobs, same times);
--   3. a timer every 10 minutes that copies GitHub's answer (status, error, timed out) into the log; rows older than 30 days go.
-- The morning health email can then say "Supabase's 4:17 start got no answer from GitHub; the 4:47 backup started it".
-- Nothing secret in here (the key stays in Vault). Paste into Supabase > SQL Editor once.

create table if not exists public.gf_dispatch_log (
  id          bigserial primary key,
  at          timestamptz not null default now(),
  workflow    text not null,
  why         text,                 -- 'morning', 'morning-backup', 'afternoon', 'night', 'weekly', 'grab-save'
  request_id  bigint,               -- pg_net's id: net._http_response.id
  status_code int,                  -- GitHub's answer: 204 = started; null until copied, or no answer at all
  error_msg   text,
  timed_out   boolean,
  checked_at  timestamptz
);
alter table public.gf_dispatch_log enable row level security;   -- no policy: visitors read nothing; the service key does
revoke all on public.gf_dispatch_log from anon, authenticated;

create or replace function public._gf_post_dispatch(p_workflow text, p_inputs jsonb, p_why text)
returns bigint language plpgsql security definer set search_path = public as $$
declare k text; rid bigint;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'github_dispatch_token';
  if k is null then raise exception 'github_dispatch_token is missing from Vault'; end if;
  select net.http_post(
    url     := 'https://api.github.com/repos/Upnorth89/Running-Discount/actions/workflows/' || p_workflow || '/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'thegearfox-supabase',
                                  'Content-Type', 'application/json'),
    body    := case when p_inputs is null then jsonb_build_object('ref', 'main')
                    else jsonb_build_object('ref', 'main', 'inputs', p_inputs) end,
    timeout_milliseconds := 20000) into rid;
  insert into gf_dispatch_log (workflow, why, request_id) values (p_workflow, p_why, rid);
  return rid;
end $$;
revoke all on function public._gf_post_dispatch(text, jsonb, text) from public, anon, authenticated;

-- the morning start (11:17 UTC job 'gear-fox-morning-refresh' and the 12:47 backup both call this)
create or replace function public._gf_start_refresh()
returns void language plpgsql security definer set search_path = public as $$
begin
  perform public._gf_post_dispatch('refresh.yml', '{"morning": "true"}'::jsonb,
          case when extract(hour from now() at time zone 'utc') >= 12 then 'morning-backup' else 'morning' end);
end $$;
revoke all on function public._gf_start_refresh() from public, anon, authenticated;

-- afternoon refresh + night reads (timers.sql jobs keep calling this with the same arguments)
create or replace function public._gf_dispatch(p_workflow text, p_inputs jsonb)
returns void language plpgsql security definer set search_path = public as $$
begin
  perform public._gf_post_dispatch(p_workflow, p_inputs,
          case when p_inputs ? 'afternoon' then 'afternoon' when p_inputs ? 'night' then 'night' else 'other' end);
end $$;
revoke all on function public._gf_dispatch(text, jsonb) from public, anon, authenticated;

-- Friday + Saturday weekly email
create or replace function public._gf_start_weekly()
returns void language plpgsql security definer set search_path = public as $$
begin
  perform public._gf_post_dispatch('weekly-email.yml', '{"send_to": "due"}'::jsonb, 'weekly');
end $$;
revoke all on function public._gf_start_weekly() from public, anon, authenticated;

-- Grab deals saves + catalog uploads (one start after 90 s of quiet, as before)
create or replace function public._gf_refresh_flush()
returns void language plpgsql security definer set search_path = public as $$
declare w timestamptz;
begin
  select value::timestamptz into w from ana_settings where name = 'refresh_wanted';
  if w is null or w > now() - interval '90 seconds' then return; end if;
  delete from ana_settings where name = 'refresh_wanted';
  perform public._gf_post_dispatch('refresh.yml', null, 'grab-save');
end $$;
revoke all on function public._gf_refresh_flush() from public, anon, authenticated;

-- copy GitHub's answers into the log (pg_net keeps them only ~6 hours) and forget rows older than 30 days
create or replace function public._gf_dispatch_check()
returns void language plpgsql security definer set search_path = public as $$
begin
  update gf_dispatch_log l set status_code = r.status_code, error_msg = r.error_msg, timed_out = r.timed_out, checked_at = now()
  from net._http_response r
  where r.id = l.request_id and l.checked_at is null;
  -- pg_net forgot it without an answer (older than its 6 h): mark it so the email can say "no answer"
  update gf_dispatch_log set checked_at = now() where checked_at is null and at < now() - interval '5 hours';
  delete from gf_dispatch_log where at < now() - interval '30 days';
end $$;
revoke all on function public._gf_dispatch_check() from public, anon, authenticated;

select cron.unschedule(jobid) from cron.job where jobname = 'gf-dispatch-check';
select cron.schedule('gf-dispatch-check', '*/10 * * * *', 'select public._gf_dispatch_check()');

-- Check (after a start): select at, workflow, why, status_code, error_msg, timed_out from gf_dispatch_log order by at desc limit 10;
