-- The Gear Fox: watchlist (price-drop and back-in-your-size alerts).
-- Paste this whole file into Supabase > SQL Editor > New query, then click Run.
-- Needs setup.sql to have run first. Safe to run again.
--
-- Each row is one product a subscriber is watching. The website adds and removes rows through
-- the functions below (they need the subscriber's private key from their email link). The daily
-- alert job reads and updates rows with the secret key.

create table if not exists public.watches (
  id             bigint generated always as identity primary key,
  subscriber_id  uuid not null references public.subscribers(id) on delete cascade,
  item_key       text not null check (length(item_key) <= 300),   -- brand|name|group|wide, lower case
  meta           jsonb not null default '{}'::jsonb,               -- brand, name, link, price when saved
  created_at     timestamptz not null default now(),
  last_price     numeric,        -- best price in their size at the last daily check
  last_in_stock  boolean,        -- in stock in their size at the last daily check
  notified_price numeric,        -- price we last told them about (starts at the price when saved)
  notified_at    timestamptz,
  unique (subscriber_id, item_key)
);
alter table public.watches enable row level security;
revoke all on public.watches from anon, authenticated;

create or replace function public.watch_add(p_token uuid, p_key text, p_meta jsonb)
returns boolean language plpgsql security definer set search_path = public as $$
declare sid uuid; n int; price numeric;
begin
  if p_key is null or length(p_key) > 300 or p_meta is null or jsonb_typeof(p_meta) <> 'object'
     or octet_length(p_meta::text) > 4000 then raise exception 'invalid watch'; end if;
  select id into sid from public.subscribers where token = p_token;
  if sid is null then return false; end if;
  select count(*) into n from public.watches where subscriber_id = sid;
  if n >= 200 then raise exception 'watchlist is full (200 items)'; end if;
  price := nullif(p_meta->>'price', '')::numeric;
  insert into public.watches (subscriber_id, item_key, meta, last_price, last_in_stock, notified_price)
  values (sid, lower(p_key), p_meta, price, true, price)
  on conflict (subscriber_id, item_key) do update set meta = excluded.meta;
  return true;
end $$;

create or replace function public.watch_remove(p_token uuid, p_key text)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  delete from public.watches w using public.subscribers s
   where w.subscriber_id = s.id and s.token = p_token and w.item_key = lower(p_key);
  return found;
end $$;

create or replace function public.watch_list(p_token uuid)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('key', w.item_key, 'meta', w.meta, 'saved', w.created_at)
                            order by w.created_at desc), '[]'::jsonb)
    from public.watches w join public.subscribers s on s.id = w.subscriber_id
   where s.token = p_token;
$$;

revoke all on function public.watch_add(uuid, text, jsonb), public.watch_remove(uuid, text),
                       public.watch_list(uuid) from public;
grant execute on function public.watch_add(uuid, text, jsonb), public.watch_remove(uuid, text),
                          public.watch_list(uuid) to anon, authenticated;
