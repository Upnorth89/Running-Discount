-- The Gear Fox: start the Friday deals email on time.
-- GitHub skipped every scheduled Friday run on Oct 2, 2026 (9:07-13:07 UTC). This timer runs inside Supabase every
-- hour on Friday at :07 from 9:07 to 18:07 UTC and asks GitHub to start weekly-email.yml with send_to=due, which
-- sends to the people for whom it's now 7am or later and marks them sent (nobody gets two). GitHub's own
-- schedule stays as a backup.
--
-- Uses the same GitHub key as the morning timer (Vault: github_dispatch_token, expires 2027-09-29).
-- Paste into Supabase > SQL Editor once (after morning-timer.sql).

create or replace function public._gf_start_weekly()
returns void language plpgsql security definer set search_path = public as $$
declare k text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'github_dispatch_token';
  if k is null then raise exception 'github_dispatch_token is missing from Vault'; end if;
  perform net.http_post(
    url     := 'https://api.github.com/repos/Upnorth89/Running-Discount/actions/workflows/weekly-email.yml/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'thegearfox-supabase',
                                  'Content-Type', 'application/json'),
    body    := jsonb_build_object('ref', 'main', 'inputs', jsonb_build_object('send_to', 'due')));
end $$;
revoke all on function public._gf_start_weekly() from public, anon, authenticated;

select cron.unschedule(jobid) from cron.job where jobname = 'gear-fox-friday-email';
select cron.schedule('gear-fox-friday-email', '7 9-18 * * 5', 'select public._gf_start_weekly()');
