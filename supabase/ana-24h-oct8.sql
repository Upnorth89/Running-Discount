-- Oct 8, 2026: the data page (stats.html) gets a "last 24 hours" view, hour by hour.
-- Paste this whole file in Supabase > SQL Editor > Run. Safe to run twice.
create or replace function public.ana_dashboard(p_key text, p_days int default 30)
returns jsonb language plpgsql stable security definer set search_path = public as $$
declare today date := (now() at time zone 'America/Vancouver')::date; d int := least(greatest(coalesce(p_days, 30), 1), 400);
begin
  if p_key is null or p_key <> (select value from ana_settings where name = 'dashboard_key') then
    raise exception 'wrong key';
  end if;
  return jsonb_build_object(
    'today', today,
    'live', (select count(distinct did) from ana_events where at > now() - interval '30 minutes'),
    'days', (select coalesce(jsonb_agg(x order by x.day), '[]') from (            -- one row per day: the headline numbers
              select day, jsonb_object_agg(metric, n) m from (
                select day, metric, n from ana_daily where key = '' and day >= today - d and day < today
                union all select today, metric, n from ana_metrics(today) where key = '') q group by day) x),
    'prev', (select coalesce(jsonb_object_agg(metric, n), '{}') from (           -- the period before, for the % change
              select metric, sum(n) n from ana_daily where key = '' and day >= today - 2 * d and day < today - d group by metric) x),
    'breakdown', (select coalesce(jsonb_object_agg(metric, items), '{}') from (    -- sources, devices, languages, pages, stores
              select metric, jsonb_agg(jsonb_build_object('k', key, 'n', n) order by n desc) items from (
                select metric, key, sum(n) n from (
                  select metric, key, n from ana_daily where key <> '' and day >= today - d and day < today
                  union all select metric, key, n from ana_metrics(today) where key <> '') q
                group by metric, key) r group by metric) x),
    'report', ana_report(greatest(now() - make_interval(days => d), now() - interval '45 days'), now()),   -- funnel, searches, cohorts
    -- Oct 8 (Bastien: post and notify when shoppers are around): visits, deal clicks and sign-ups by the visitor's own local
    -- hour and weekday (each event carries the device's time zone; Vancouver when unknown or not a real zone name)
    'hours', (select coalesce(jsonb_agg(jsonb_build_object('h', h, 'v', v, 'c', c, 's', s) order by h), '[]') from (
              select extract(hour from at at time zone z)::int h, count(*) filter (where kind = 'visit') v,
                     count(*) filter (where kind = 'deal-click') c, count(*) filter (where kind = 'signup') s
              from (select e.at, e.kind, coalesce(t.name, 'America/Vancouver') z from ana_events e
                    left join pg_timezone_names t on t.name = e.tz
                    where e.at > greatest(now() - make_interval(days => d), now() - interval '45 days')
                      and e.kind in ('visit', 'deal-click', 'signup')) q group by 1) x),
    'weekdays', (select coalesce(jsonb_agg(jsonb_build_object('d', dw, 'v', v, 'c', c) order by dw), '[]') from (
              select extract(isodow from at at time zone z)::int dw, count(*) filter (where kind = 'visit') v,
                     count(*) filter (where kind = 'deal-click') c
              from (select e.at, e.kind, coalesce(t.name, 'America/Vancouver') z from ana_events e
                    left join pg_timezone_names t on t.name = e.tz
                    where e.at > greatest(now() - make_interval(days => d), now() - interval '45 days')
                      and e.kind in ('visit', 'deal-click')) q group by 1) x),
    -- Oct 8 (Bastien: "24h, 7 days, 30 and 60"): the last 24 hours, hour by hour (UTC hour starts; the page shows local time)
    'h24', (select coalesce(jsonb_agg(jsonb_build_object('t', t, 'v', v, 'nv', nv, 'c', c, 's', s) order by t), '[]') from (
              select date_trunc('hour', at) t, count(distinct did) v, count(distinct did) filter (where nv = 1) nv,
                     count(*) filter (where kind = 'deal-click') c, count(distinct sid) filter (where kind = 'signup') s
              from ana_events where at > now() - interval '24 hours' group by 1) x),
    'h24_total', (select jsonb_build_object('v', count(distinct did), 'nv', count(distinct did) filter (where nv = 1),
                         'c', count(*) filter (where kind = 'deal-click'), 's', count(distinct sid) filter (where kind = 'signup'))
              from ana_events where at > now() - interval '24 hours'),
    'h24_prev', (select jsonb_build_object('v', count(distinct did), 'nv', count(distinct did) filter (where nv = 1),
                         'c', count(*) filter (where kind = 'deal-click'), 's', count(distinct sid) filter (where kind = 'signup'))
              from ana_events where at > now() - interval '48 hours' and at <= now() - interval '24 hours'));
end $$;
revoke all on function public.ana_dashboard(text, int) from public;
grant execute on function public.ana_dashboard(text, int) to anon, authenticated;
