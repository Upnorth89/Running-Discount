-- The Gear Fox: "money back after you buy" (price protection), step 1: the tables and the site's functions.
-- Growth chat spec (Oct 27, Bastien OK'd): a member says they bought something (one tap after a store click, the next-morning email,
-- or "I bought it" on the watchlist); while the store's price-adjustment window is open, the daily alert job watches that item in
-- their size and emails them when the price drops: "Ask <store> for $X back". Every such email ends with "Got it back? Yes / No".
-- NOT LIVE YET: preview first. Paste in Supabase > SQL Editor when Bastien says go. Needs setup.sql. Safe to run again.
--
-- store_policies has NO rows here on purpose (Bastien: the policy list stays private): the growth chat gives him its own SQL for them.

create table if not exists public.store_policies (
  store       text primary key,                          -- offer host exactly as in the site's STORES map ("ca.shop.runningroom.com")
  kind        text not null check (kind in ('adjust', 'match', 'both')),   -- price adjustment on its own price / price match / both
  days        int  not null check (days between 1 and 120),               -- window after the purchase
  side        text not null default 'ca' check (side in ('ca', 'us')),
  rules       text,                                       -- the store's own words, short (what's excluded, how to ask)
  url         text,                                       -- the store's policy page
  checked_on  date not null default current_date          -- re-read the store's page every 3 months
);
alter table public.store_policies enable row level security;
revoke all on public.store_policies from anon, authenticated;

create table if not exists public.purchases (
  id             bigint generated always as identity primary key,
  subscriber_id  uuid not null references public.subscribers(id) on delete cascade,
  item_key       text not null check (length(item_key) <= 300),   -- same key as the watchlist (brand|name|group|wide, lower case)
  store          text not null check (length(store) <= 120),
  price          numeric not null check (price > 0 and price < 100000),
  currency       text not null default 'CAD' check (currency in ('CAD', 'USD')),
  size           text check (length(size) <= 40),
  bought_on      date not null default current_date,
  src            text not null default 'manual' check (src in ('return', 'email', 'manual')),   -- which way of asking worked
  meta           jsonb not null default '{}'::jsonb,         -- brand, name, link, photo when saved
  created_at     timestamptz not null default now(),
  lowest_seen    numeric,          -- lowest price in their size at that store since the purchase (daily job)
  notified_price numeric,          -- the drop we last emailed them about
  notified_at    timestamptz,
  got_back       boolean,          -- their answer to "Got it back?" (null = no answer)
  answered_at    timestamptz,
  unique (subscriber_id, item_key, store, bought_on)
);
alter table public.purchases enable row level security;
revoke all on public.purchases from anon, authenticated;

-- one tap on the site or in the email: everything we already know (item, store, price shown, size) comes prefilled
create or replace function public.purchase_add(p_token uuid, p_key text, p_store text, p_price numeric, p_size text,
                                               p_bought date default null, p_src text default 'manual', p_meta jsonb default '{}'::jsonb,
                                               p_currency text default 'CAD')
returns bigint language plpgsql security definer set search_path = public as $$
declare sid uuid; n int; pid bigint;
begin
  if p_key is null or length(p_key) > 300 or p_store is null or length(p_store) > 120 or p_price is null or p_price <= 0
     or p_meta is null or jsonb_typeof(p_meta) <> 'object' or octet_length(p_meta::text) > 4000
     or coalesce(p_bought, current_date) not between current_date - 120 and current_date then raise exception 'invalid purchase'; end if;
  select id into sid from public.subscribers where token = p_token and unsubscribed_at is null;
  if sid is null then return null; end if;
  select count(*) into n from public.purchases where subscriber_id = sid and created_at > now() - interval '1 day';
  if n >= 20 then raise exception 'too many purchases today'; end if;
  insert into public.purchases (subscriber_id, item_key, store, price, currency, size, bought_on, src, meta, lowest_seen)
  values (sid, lower(p_key), lower(p_store), p_price, coalesce(nullif(upper(p_currency), ''), 'CAD'), nullif(p_size, ''),
          coalesce(p_bought, current_date), coalesce(nullif(p_src, ''), 'manual'), p_meta, p_price)
  on conflict (subscriber_id, item_key, store, bought_on) do update
     set price = excluded.price, size = excluded.size, meta = excluded.meta
  returning id into pid;
  return pid;
end $$;

-- the member's own list (watchlist page): what we're watching for them and until when
create or replace function public.purchase_list(p_token uuid)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', p.id, 'key', p.item_key, 'store', p.store, 'price', p.price, 'currency', p.currency,
                                               'size', p.size, 'bought', p.bought_on, 'meta', p.meta, 'got_back', p.got_back,
                                               'until', p.bought_on + coalesce(sp.days, 0), 'kind', sp.kind)
                            order by p.bought_on desc, p.id desc), '[]'::jsonb)
    from public.purchases p join public.subscribers s on s.id = p.subscriber_id
    left join public.store_policies sp on sp.store = p.store
   where s.token = p_token;
$$;

create or replace function public.purchase_remove(p_token uuid, p_id bigint)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  delete from public.purchases p using public.subscribers s
   where p.subscriber_id = s.id and s.token = p_token and p.id = p_id;
  return found;
end $$;

-- "Got it back? Yes / No" from the alert email (one tap, the email's own token: no sign-in)
create or replace function public.purchase_claimed(p_token uuid, p_id bigint, p_yes boolean)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  update public.purchases p set got_back = p_yes, answered_at = now()
    from public.subscribers s
   where p.subscriber_id = s.id and s.token = p_token and p.id = p_id;
  return found;
end $$;

-- which stores have a policy (names only, so the site knows when to ask "Bought it?"; the rules stay private)
create or replace function public.policy_stores()
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('store', store, 'days', days, 'side', side) order by store), '[]'::jsonb)
    from public.store_policies;
$$;

revoke all on function public.purchase_add(uuid, text, text, numeric, text, date, text, jsonb, text), public.purchase_list(uuid),
                       public.purchase_remove(uuid, bigint), public.purchase_claimed(uuid, bigint, boolean), public.policy_stores() from public;
grant execute on function public.purchase_add(uuid, text, text, numeric, text, date, text, jsonb, text), public.purchase_list(uuid),
                          public.purchase_remove(uuid, bigint), public.purchase_claimed(uuid, bigint, boolean), public.policy_stores()
   to anon, authenticated;
