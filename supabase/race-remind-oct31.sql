-- Oct 31, 2026 (Bastien: "lets build it now"): race gear lists' "Remind me 30 days before the race".
-- A member's race lists live in their own table (race_lists: race, distance, items ticked), not in the profile: the homepage
-- saves the whole profile and the confirm step replaces it, which would wipe a race list.
-- Paste this whole file in Supabase > SQL Editor > Run. Safe to run twice.

-- 1. One row per member and race.
create table if not exists public.race_lists (
  subscriber_id uuid not null references public.subscribers(id) on delete cascade,
  slug       text not null check (slug ~ '^[a-z0-9-]{2,60}$'),
  dist       text,
  side       text,
  ticks      jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (subscriber_id, slug)
);
alter table public.race_lists enable row level security;   -- nothing readable by visitors; the job uses the secret key
revoke all on public.race_lists from anon, authenticated;

create or replace function public._gf_race_put(p_id uuid, p_race jsonb)
returns void language plpgsql security definer set search_path = public as $$
declare v_slug text := p_race ->> 'slug';
begin
  if p_race is null or jsonb_typeof(p_race) <> 'object' or v_slug is null or v_slug !~ '^[a-z0-9-]{2,60}$'
     or octet_length(p_race::text) > 4000 or (p_race ? 'ticks' and jsonb_typeof(p_race -> 'ticks') <> 'array') then
    raise exception 'invalid race'; end if;
  insert into public.race_lists (subscriber_id, slug, dist, side, ticks)
  values (p_id, v_slug, left(p_race ->> 'dist', 40), left(p_race ->> 'side', 4), coalesce(p_race -> 'ticks', '[]'::jsonb))
  on conflict (subscriber_id, slug) do update
     set dist = excluded.dist, side = excluded.side, ticks = excluded.ticks, updated_at = now();
end $$;
revoke all on function public._gf_race_put(uuid, jsonb) from public, anon, authenticated;

-- 2. A sign-up from a race page carries profile.races = [{slug, dist, side, ticks}]: whenever it lands in the profile
--    (sign-up, or the confirm link from another device), it moves into race_lists and leaves the profile.
create or replace function public._gf_race_move()
returns trigger language plpgsql security definer set search_path = public as $$
declare x jsonb;
begin
  if new.profile ? 'races' then
    if jsonb_typeof(new.profile -> 'races') = 'array' then
      for x in select * from jsonb_array_elements(new.profile -> 'races') limit 10 loop
        begin perform public._gf_race_put(new.id, x); exception when others then null; end;  -- a bad entry never blocks a sign-up
      end loop;
    end if;
    new.profile := new.profile - 'races';
  end if;
  return new;
end $$;
drop trigger if exists gf_race_move on public.subscribers;
create trigger gf_race_move before update of profile on public.subscribers
  for each row execute function public._gf_race_move();

-- 3. A race page saves the distance + ticks for a member (key from gf-sub), and reads them back on another device.
create or replace function public.race_save(p_token uuid, p_race jsonb)
returns boolean language plpgsql security definer set search_path = public as $$
declare sid uuid;
begin
  select id into sid from public.subscribers
   where token = p_token and confirmed_at is not null and unsubscribed_at is null;
  if sid is null then return false; end if;
  perform public._gf_race_put(sid, p_race);
  return true;
end $$;

create or replace function public.race_get(p_token uuid, p_slug text)
returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object('dist', l.dist, 'ticks', l.ticks, 'at', floor(extract(epoch from l.updated_at) * 1000))
    from public.race_lists l join public.subscribers s on s.id = l.subscriber_id
   where s.token = p_token and l.slug = p_slug;
$$;
revoke all on function public.race_save(uuid, jsonb), public.race_get(uuid, text) from public;
grant execute on function public.race_save(uuid, jsonb), public.race_get(uuid, text) to anon, authenticated;

-- 4. The reminder job records each send, so nobody gets the same race's reminder twice.
create table if not exists public.race_reminders (
  subscriber_id uuid not null references public.subscribers(id) on delete cascade,
  slug text not null,
  race_date date not null,
  sent_at timestamptz not null default now(),
  primary key (subscriber_id, slug, race_date)
);
alter table public.race_reminders enable row level security;
revoke all on public.race_reminders from anon, authenticated;
