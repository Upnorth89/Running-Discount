-- Oct 11, 2026 (Bastien: "seems like a big drop from people who showed up"): the dashboard's new-visitor funnel, split by where
-- people landed. Half of first visits land on a shoe price page (Reddit, Google) and never see the welcome screen, so one funnel
-- for everyone looked like a big drop. Adds 'funnel_land' to ana_report: per landing (homepage / shoe pages / other) the first
-- visits, saw the welcome, picked a size (sizes step or a shoe page's size), signed up, clicked a deal, went on to the homepage.
-- Paste the whole file in Supabase > SQL Editor > Run. Safe to run again.
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
           max(num) filter (where kind = 'scroll') scrolled, count(*) filter (where kind = 'deal-click') clicks,
           bool_or(kind = 'shoe-page-size') shoe_size
    from e group by sid),
  -- where each session landed (Oct 11, Bastien: half of first visits land on a shoe page and never see the welcome)
  sl as (select *, case when coalesce(entry, '') in ('/', '/index.html') then 'homepage'
                        when entry ~ '^/(us/)?(shoes|chaussures|running-shoes-sale|chaussures-course-solde|brands|marques|black-friday|vendredi-fou)/'
                             then 'shoe pages' else 'other' end land from s),
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
    'funnel_land', coalesce((select jsonb_object_agg(land, x) from (
                select land, jsonb_build_object('sessions', count(*), 'welcome', count(*) filter (where welcome),
                       'sizes', count(*) filter (where sizes or shoe_size), 'signup', count(*) filter (where signup),
                       'clicked', count(*) filter (where clicked), 'home', count(*) filter (where welcome or sizes)) x
                from sl where nv = 1 group by land) y), '{}'),
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
