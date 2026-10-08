-- The Gear Fox: upload the daily GPT catalog file from thegearfox.com/catalog.html (Oct 9, 2026; Bastien: "have gpt do this
-- daily"). The file (Running_Gear_Catalog.xlsx, ~20 MB) goes to a private storage bucket instead of GitHub, so the code history
-- doesn't grow by 20 MB a day. Only someone with the data page's private key (ana_settings.dashboard_key) can upload: files must
-- go in a folder named after that key. Nobody can read or list the bucket from the site; the morning update reads it with the
-- secret server key, uses the newest file, and deletes older ones.
-- Paste into Supabase > SQL Editor once. Needs analytics.sql (ana_settings) and morning-timer.sql (Vault key) first.

insert into storage.buckets (id, name, public, file_size_limit)
values ('catalog', 'catalog', false, 52428800)                       -- 50 MB, the free plan's limit per file
on conflict (id) do update set public = false, file_size_limit = 52428800;

-- the folder the site may write to = the private key (a security-definer helper, so the policy can read ana_settings)
create or replace function public._gf_catalog_folder()
returns text language sql stable security definer set search_path = public as $$
  select value from ana_settings where name = 'dashboard_key'
$$;
revoke all on function public._gf_catalog_folder() from public;
grant execute on function public._gf_catalog_folder() to anon, authenticated;

drop policy if exists "gear fox catalog upload" on storage.objects;
create policy "gear fox catalog upload" on storage.objects for insert to anon, authenticated
  with check (bucket_id = 'catalog' and (storage.foldername(name))[1] = public._gf_catalog_folder());

-- which file is newest (the update reads this list with the server key)
create table if not exists public.catalog_files (
  id   bigint generated always as identity primary key,
  at   timestamptz not null default now(),
  path text not null
);
alter table public.catalog_files enable row level security;
revoke all on public.catalog_files from anon, authenticated;

-- start a normal site update (same as grab.sql; repeated here so this file works on its own)
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

-- the upload page calls this after the file is in the bucket: records it and starts the site update
create or replace function public.catalog_uploaded(p_key text, p_path text)
returns json language plpgsql security definer set search_path = public as $$
begin
  if p_key is null or p_key <> (select value from ana_settings where name = 'dashboard_key') then
    return json_build_object('ok', false, 'why', 'key');
  end if;
  if p_path is null or split_part(p_path, '/', 1) <> p_key or p_path !~ '\.xlsx$' then
    return json_build_object('ok', false, 'why', 'path');
  end if;
  insert into catalog_files (path) values (p_path);
  delete from catalog_files where at < now() - interval '30 days';
  perform public._gf_refresh_now();
  return json_build_object('ok', true);
end $$;
grant execute on function public.catalog_uploaded(text, text) to anon, authenticated;
