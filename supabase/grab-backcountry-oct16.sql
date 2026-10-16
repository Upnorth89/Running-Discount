-- The Gear Fox: "Grab deals" also takes Backcountry (Oct 16, 2026; Bastien: "Are able to have a grab deal for backcountry").
-- Paste into Supabase > SQL Editor once (after grab.sql). It lets the store name 'backcountry' through; nothing else changes.

alter table public.grab_saves drop constraint if exists grab_saves_store_check;
alter table public.grab_saves add constraint grab_saves_store_check check (store in ('mec', 'rei', 'svp', 'backcountry'));

create or replace function public.grab_save(p_key text, p_store text, p_data jsonb)
returns json language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if p_key is null or p_key <> (select value from ana_settings where name = 'dashboard_key') then
    return json_build_object('ok', false, 'why', 'key');
  end if;
  if p_store not in ('mec', 'rei', 'svp', 'backcountry') then return json_build_object('ok', false, 'why', 'store'); end if;
  n := coalesce(jsonb_array_length(coalesce(p_data -> 'hits', p_data -> 'results', p_data -> 'products')), 0);
  if n = 0 then return json_build_object('ok', false, 'why', 'empty'); end if;
  insert into grab_saves (store, n, data) values (p_store, n, p_data);
  delete from grab_saves where at < now() - interval '30 days';
  perform public._gf_refresh_now();
  return json_build_object('ok', true, 'n', n);
end $$;
grant execute on function public.grab_save(text, text, jsonb) to anon, authenticated;
