-- Oct 30, 2026 (Bastien: "add a real subscriber count on the stats page so I can see it easily").
-- The stats page (stats.html) asks for the number of REAL subscribers: confirmed, not unsubscribed, test addresses left out.
-- A test address = anything @thegearfox.com or @example.com, any address with a "+tag" (name+test1@...), and the plain address
-- those +tags belong to (the owner testing). No address is written here: the repo is public. tools/funnel.py uses the same rule.
-- Paste this whole file in Supabase > SQL Editor > Run. Safe to run twice.
create or replace function public.ana_members(p_key text)
returns jsonb language plpgsql stable security definer set search_path = public as $$
begin
  if p_key is null or p_key <> (select value from ana_settings where name = 'dashboard_key') then
    raise exception 'wrong key';
  end if;
  return (
    with act as (
      select lower(email) e, regexp_replace(lower(email), '\+[^@]*@', '@') base, created_at
      from subscribers where confirmed_at is not null and unsubscribed_at is null),
    t as (
      select created_at, (e like '%@thegearfox.com' or e like '%@example.com' or e like '%+%@%'
                          or e in (select base from act where e like '%+%@%')) test
      from act)
    select jsonb_build_object(
      'real',  count(*) filter (where not test),
      'tests', count(*) filter (where test),
      'list',  count(*),
      'week',  count(*) filter (where not test and created_at > now() - interval '7 days'))
    from t);
end $$;
revoke all on function public.ana_members(text) from public;
grant execute on function public.ana_members(text) to anon, authenticated;
