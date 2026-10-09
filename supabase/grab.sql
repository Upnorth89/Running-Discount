-- The Gear Fox: "Grab deals" from your phone (Oct 8, 2026; Bastien: "make me a grab deal for my phone").
-- The bookmark reads MEC's / REI's running deals in your own browser, then "Send to The Gear Fox" opens
-- thegearfox.com/grab-save.html, which hands the list to grab_save() here. It's kept 10 days (the scraper reads the
-- newest per store, like a file in saved-pages/) and a site update starts right away (about 20 minutes).
-- Only you can send: grab_save() wants the same private key as the data page (ana_settings.dashboard_key).
-- Paste into Supabase > SQL Editor once. Needs analytics.sql (ana_settings) and morning-timer.sql (Vault key) first.

create table if not exists public.grab_saves (
  id    bigint generated always as identity primary key,
  at    timestamptz not null default now(),
  store text not null check (store in ('mec', 'rei', 'svp')),
  n     int,
  data  jsonb not null
);
create index if not exists grab_saves_at on public.grab_saves (at);
alter table public.grab_saves enable row level security;
revoke all on public.grab_saves from anon, authenticated;

-- start a normal site update (not a "morning" one, so it never sends a second health email)
create or replace function public._gf_refresh_now()
returns void language plpgsql security definer set search_path = public as $$
declare k text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'github_dispatch_token';
  if k is null then return; end if;
  perform net.http_post(
    url     := 'https://api.github.com/repos/Upnorth89/Running-Discount/actions/workflows/refresh.yml/dispatches',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Accept', 'application/vnd.github+json',
                                  'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'thegearfox-supabase',
                                  'Content-Type', 'application/json'),
    body    := jsonb_build_object('ref', 'main'));
end $$;
revoke all on function public._gf_refresh_now() from public, anon, authenticated;

create or replace function public.grab_save(p_key text, p_store text, p_data jsonb)
returns json language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if p_key is null or p_key <> (select value from ana_settings where name = 'dashboard_key') then
    return json_build_object('ok', false, 'why', 'key');
  end if;
  if p_store not in ('mec', 'rei', 'svp') then return json_build_object('ok', false, 'why', 'store'); end if;
  n := coalesce(jsonb_array_length(coalesce(p_data -> 'hits', p_data -> 'results', p_data -> 'products')), 0);
  if n = 0 then return json_build_object('ok', false, 'why', 'empty'); end if;
  insert into grab_saves (store, n, data) values (p_store, n, p_data);
  delete from grab_saves where at < now() - interval '30 days';
  perform public._gf_refresh_now();
  return json_build_object('ok', true, 'n', n);
end $$;
grant execute on function public.grab_save(text, text, jsonb) to anon, authenticated;
