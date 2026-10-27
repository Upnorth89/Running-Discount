-- Oct 27: one site refresh per Grab deals save, not one per part.
-- The bookmark sends a big list in parts of 200 (grab-save.html) and every grab_save() call started refresh.yml, so one
-- Backcountry save started ~15 runs in a few seconds (runs 740-779, Oct 27), and the burst cancelled a waiting push run (764).
-- Now _gf_refresh_now() only notes that a refresh is wanted; a 1-minute timer starts ONE run once nothing new came in for 90 s.
-- Same for catalog uploads (catalog.sql), which also call _gf_refresh_now(). Paste in the Supabase SQL Editor once.

create or replace function public._gf_refresh_now()
returns void language plpgsql security definer set search_path = public as $$
begin
  insert into ana_settings (name, value) values ('refresh_wanted', now()::text)
  on conflict (name) do update set value = excluded.value;
end $$;
revoke all on function public._gf_refresh_now() from public, anon, authenticated;

-- the timer: starts refresh.yml when a refresh is wanted and the saves have been quiet for 90 seconds
create or replace function public._gf_refresh_flush()
returns void language plpgsql security definer set search_path = public as $$
declare w timestamptz; k text;
begin
  select value::timestamptz into w from ana_settings where name = 'refresh_wanted';
  if w is null or w > now() - interval '90 seconds' then return; end if;
  delete from ana_settings where name = 'refresh_wanted';
  select decrypted_secret into k from vault.decrypted_secrets where name = 'github_dispatch_token';
  if k is null then return; end if;
  perform net.http_post(
    url     := 'https://api.github.com/repos/Upnorth89/Running-Discount/actions/workflows/refresh.yml/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'thegearfox-supabase',
                                  'Content-Type', 'application/json'),
    body    := jsonb_build_object('ref', 'main'));
end $$;
revoke all on function public._gf_refresh_flush() from public, anon, authenticated;

select cron.schedule('gf-refresh-flush', '* * * * *', 'select public._gf_refresh_flush()');
