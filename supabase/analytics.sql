-- The Gear Fox: our own product analytics (Oct 2026). What people DO on the site, so we can see where they
-- drop off and what brings them back. Never who they are: no email, no name, no IP address, no cookies.
-- Each browser gets a random number (made on the device, stored in its localStorage) so we can tell a
-- returning visitor from a new one; it is never linked to an email or account.
-- Raw events are kept 45 days, then deleted; the per-device table keeps only dates and counts (for retention).
-- Paste into Supabase > SQL Editor once.

create table if not exists public.ana_events (
  id      bigint generated always as identity primary key,
  at      timestamptz not null default now(),
  did     uuid not null,                                   -- random device number (localStorage gf-did)
  sid     uuid not null,                                   -- random session number (sessionStorage)
  kind    text not null check (length(kind) <= 32),
  detail  text check (length(detail) <= 120),              -- e.g. store, category, search words, menu item
  num     real,                                            -- e.g. card position, seconds, scroll %, result count
  page    text check (length(page) <= 80),                 -- /, /shoes/<slug>/, /about.html …
  lang    text check (lang in ('en', 'fr')),
  ref     text check (length(ref) <= 40),
  dev     text check (dev in ('phone', 'tablet', 'computer')),
  nv      int                                              -- this device's visit number (1 = first visit)
);
create index if not exists ana_events_at on public.ana_events (at);
create index if not exists ana_events_kind_at on public.ana_events (kind, at);
alter table public.ana_events enable row level security;
revoke all on public.ana_events from anon, authenticated;

-- one small row per device: first and last day seen, how many visits and days. For "do people come back?"
create table if not exists public.ana_devices (
  did        uuid primary key,
  first_day  date not null,
  last_day   date not null,
  visits     int not null default 1,
  days       int not null default 1,
  signed_up  boolean not null default false,               -- signed up for the Friday email on this device (no email kept here)
  ref        text check (length(ref) <= 40),               -- the link that first brought them
  dev        text
);
create index if not exists ana_devices_first on public.ana_devices (first_day);
alter table public.ana_devices enable row level security;
revoke all on public.ana_devices from anon, authenticated;

-- what the site may send: anything else is ignored
create or replace function public.ana_kinds() returns text[] language sql immutable as $$
  select array['visit','leave','scroll','welcome-view','signup-step','sizes-saved','peek-view','signup','signup-confirmed',
               'signin','resend','deal-click','watch-add','watch-remove','watchlist-open','watch-from-page','search',
               'search-none','category','type','filter','sort','menu','language','currency','share','shoe-page-link',
               'shoe-page-view','shoe-page-size','more','ref-visit','error']
$$;

-- the site calls this with a small batch of events (anyone can add, nobody can read)
create or replace function public.ana_track(p_did uuid, p_sid uuid, p_events jsonb, p_lang text default null,
                                            p_ref text default null, p_dev text default null, p_nv int default null)
returns void language plpgsql security definer set search_path = public as $$
declare
  e jsonb; n int := 0; d text; today date := (now() at time zone 'America/Toronto')::date;
  ref text := nullif(left(lower(regexp_replace(coalesce(p_ref, ''), '[^a-zA-Z0-9_-]', '', 'g')), 40), '');
  lang text := case when p_lang in ('en','fr') then p_lang end;
  dev text := case when p_dev in ('phone','tablet','computer') then p_dev end;
begin
  if p_did is null or p_sid is null or jsonb_typeof(p_events) <> 'array' then return; end if;
  -- a session sends at most ~400 events (stops runaway loops or abuse from filling the database)
  if (select count(*) from ana_events where sid = p_sid) > 400 then return; end if;
  insert into ana_devices as a (did, first_day, last_day, ref, dev) values (p_did, today, today, ref, dev)
  on conflict (did) do update set
    days = a.days + case when a.last_day < today then 1 else 0 end,
    visits = a.visits + case when exists (select 1 from jsonb_array_elements(p_events) x where x->>'k' = 'visit') then 1 else 0 end,
    last_day = greatest(a.last_day, today);
  for e in select * from jsonb_array_elements(p_events) loop
    n := n + 1; exit when n > 40;
    if not (e->>'k' = any(ana_kinds())) then continue; end if;
    d := left(regexp_replace(coalesce(e->>'d', ''), '[\r\n\t]', ' ', 'g'), 120);
    if e->>'k' in ('search', 'search-none') and (d ~ '@' or d ~ '\d{7,}') then d := '(hidden)'; end if;   -- never keep an email or phone number someone typed
    insert into ana_events (did, sid, kind, detail, num, page, lang, ref, dev, nv)
    values (p_did, p_sid, e->>'k', nullif(d, ''),
            case when (e->>'n') ~ '^-?\d+(\.\d+)?$' then (e->>'n')::real end,
            nullif(left(coalesce(e->>'p', ''), 80), ''), lang, ref, dev, p_nv);
    if e->>'k' in ('signup', 'signup-confirmed', 'signin') then
      update ana_devices set signed_up = true where did = p_did;
    end if;
  end loop;
end $$;
revoke all on function public.ana_track(uuid, uuid, jsonb, text, text, text, int) from public;
grant execute on function public.ana_track(uuid, uuid, jsonb, text, text, text, int) to anon, authenticated;

-- the weekly report calls this with the secret key: everything already counted and grouped
create or replace function public.ana_report(p_from timestamptz, p_to timestamptz)
returns jsonb language sql stable security definer set search_path = public as $$
  with e as (select * from ana_events where at >= p_from and at < p_to),
  s as (   -- one row per session: what happened in it
    select sid, min(did::text) did, min(nv) nv, min(dev) dev, min(lang) lang, min(ref) ref,
           min(page) filter (where kind = 'visit') entry,
           bool_or(kind = 'welcome-view') welcome, bool_or(kind = 'sizes-saved') sizes,
           bool_or(kind = 'peek-view') peek, bool_or(kind = 'signup') signup,
           bool_or(kind = 'deal-click') clicked, bool_or(kind = 'watch-add') hearted,
           bool_or(kind = 'search') searched, max(num) filter (where kind = 'leave') secs,
           max(num) filter (where kind = 'scroll') scrolled, count(*) filter (where kind = 'deal-click') clicks
    from e group by sid),
  top as (select kind, detail, count(*) n, count(distinct did) devices from e
          where kind in ('search','search-none','category','type','filter','sort','menu','shoe-page-view','shoe-page-size',
                         'deal-click','watch-add','share','language','currency','error')
          group by kind, detail)
  select jsonb_build_object(
    'devices', (select count(distinct did) from s),
    'new_devices', (select count(distinct did) from s where nv = 1),
    'sessions', (select count(*) from s),
    'by_dev', coalesce((select jsonb_object_agg(coalesce(dev, '?'), n) from (select dev, count(*) n from s group by dev) x), '{}'),
    'by_lang', coalesce((select jsonb_object_agg(coalesce(lang, '?'), n) from (select lang, count(*) n from s group by lang) x), '{}'),
    'by_ref', coalesce((select jsonb_agg(x order by sessions desc) from (
                select coalesce(ref, '(direct)') ref, count(*) sessions, count(*) filter (where sizes) sizes,
                       count(*) filter (where signup) signups, count(*) filter (where clicked) clicked
                from s group by ref) x), '[]'),
    'entry', coalesce((select jsonb_agg(x order by sessions desc) from (
                select coalesce(entry, '?') page, count(*) sessions, count(*) filter (where clicked) clicked
                from s group by entry order by count(*) desc limit 15) x), '[]'),
    'funnel_new', (select jsonb_build_object(
                'sessions', count(*), 'welcome', count(*) filter (where welcome), 'sizes', count(*) filter (where sizes),
                'peek', count(*) filter (where peek), 'signup', count(*) filter (where signup),
                'clicked', count(*) filter (where clicked)) from s where nv = 1),
    'returning', (select jsonb_build_object(
                'sessions', count(*), 'clicked', count(*) filter (where clicked), 'hearted', count(*) filter (where hearted),
                'searched', count(*) filter (where searched)) from s where nv > 1),
    'median_secs', (select percentile_cont(0.5) within group (order by secs) from s where secs is not null),
    'scroll', coalesce((select jsonb_object_agg(b, n) from (select (case when scrolled >= 100 then 100 when scrolled >= 75 then 75
                when scrolled >= 50 then 50 when scrolled >= 25 then 25 else 0 end)::text b, count(*) n
                from s where scrolled is not null group by 1) x), '{}'),
    'click_positions', coalesce((select jsonb_object_agg(b, n) from (select case when num <= 6 then '1-6' when num <= 12 then '7-12'
                when num <= 24 then '13-24' else '25+' end b, count(*) n from e where kind = 'deal-click' and num is not null group by 1) x), '{}'),
    'top', coalesce((select jsonb_object_agg(kind, items) from (
                select kind, jsonb_agg(jsonb_build_object('d', detail, 'n', n, 'devices', devices) order by n desc) items
                from (select *, row_number() over (partition by kind order by n desc) r from top) t where r <= 15 group by kind) x), '{}'),
    'cohorts', coalesce((select jsonb_agg(x order by week) from (    -- of devices first seen each week: how many came back
                select date_trunc('week', first_day)::date week, count(*) devices,
                       count(*) filter (where last_day > first_day) came_back,
                       count(*) filter (where last_day >= first_day + 7) back_after_7d,
                       count(*) filter (where days >= 3) active_3_days,
                       count(*) filter (where signed_up) signed_up
                from ana_devices where first_day >= (p_to - interval '70 days')::date group by 1) x), '[]'));
$$;
revoke all on function public.ana_report(timestamptz, timestamptz) from public, anon, authenticated;

-- housekeeping every night: raw events older than 45 days are deleted (the per-device dates and counts stay)
do $$ begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    perform cron.schedule('ana-cleanup', '23 9 * * *', 'delete from public.ana_events where at < now() - interval ''45 days''');
  end if;
end $$;
