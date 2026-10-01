-- The Gear Fox: our own visit and deal-click counts (for the monthly report and affiliate applications).
-- Nothing personal: no email, no IP address, no device id. Just what kind of event, which store and category,
-- which ?ref= link and language, and when. Paste into Supabase > SQL Editor once.

create table if not exists public.clicks (
  id     bigint generated always as identity primary key,
  at     timestamptz not null default now(),
  kind   text not null check (kind in ('visit', 'click')),
  store  text check (length(store) <= 80),      -- store web address, for clicks
  grp    text check (length(grp) <= 20),        -- category, for clicks
  ref    text check (length(ref) <= 40),        -- ?ref= link the visitor came from
  lang   text check (lang in ('en', 'fr'))
);
create index if not exists clicks_at on public.clicks (at);
alter table public.clicks enable row level security;
revoke all on public.clicks from anon, authenticated;

-- the site calls this (anyone can add a count, nobody can read them)
create or replace function public.log_event(p_kind text, p_store text default null, p_group text default null,
                                            p_ref text default null, p_lang text default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_kind not in ('visit', 'click') then return; end if;
  insert into public.clicks (kind, store, grp, ref, lang)
  values (p_kind,
          nullif(left(lower(regexp_replace(coalesce(p_store, ''), '[^a-zA-Z0-9.-]', '', 'g')), 80), ''),
          case when p_group in ('shoes','tops','bottoms','bras','socks','gloves','headwear','packs','gear','watches','nutrition')
               then p_group end,
          nullif(left(lower(regexp_replace(coalesce(p_ref, ''), '[^a-zA-Z0-9_-]', '', 'g')), 40), ''),
          case when p_lang in ('en', 'fr') then p_lang end);
end $$;
revoke all on function public.log_event(text, text, text, text, text) from public;
grant execute on function public.log_event(text, text, text, text, text) to anon, authenticated;

-- the monthly report calls this with the secret key: totals for a date range, already grouped
create or replace function public.click_report(p_from timestamptz, p_to timestamptz)
returns jsonb language sql stable security definer set search_path = public as $$
  with c as (select * from public.clicks where at >= p_from and at < p_to)
  select jsonb_build_object(
    'visits', (select count(*) from c where kind = 'visit'),
    'clicks', (select count(*) from c where kind = 'click'),
    'by_store', coalesce((select jsonb_object_agg(store, n) from
                 (select store, count(*) n from c where kind = 'click' and store is not null group by store) s), '{}'),
    'by_group', coalesce((select jsonb_object_agg(grp, n) from
                 (select grp, count(*) n from c where kind = 'click' and grp is not null group by grp) s), '{}'),
    'visits_by_ref', coalesce((select jsonb_object_agg(ref, n) from
                 (select ref, count(*) n from c where kind = 'visit' and ref is not null group by ref) s), '{}'),
    'visits_by_lang', coalesce((select jsonb_object_agg(lang, n) from
                 (select lang, count(*) n from c where kind = 'visit' and lang is not null group by lang) s), '{}'));
$$;
revoke all on function public.click_report(timestamptz, timestamptz) from public, anon, authenticated;
