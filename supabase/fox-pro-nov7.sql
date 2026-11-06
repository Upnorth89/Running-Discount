-- Fox Pro, piece 1 (Nov 7, 2026): who pays, and the numbered founding spots. Nothing here is visible to visitors.
-- Paste once in the Supabase SQL Editor (safe to paste again).
-- Only the Stripe edge functions (service role) read/write these tables; visitors and the site never see them.

create table if not exists public.pro_members (
  subscriber_id     uuid primary key references public.subscribers(id) on delete cascade,
  founding_no       int check (founding_no between 1 and 100),   -- Founding Fox #001-#100; null = regular price
  plan              text not null check (plan in ('founding', 'regular')),
  currency          text not null check (currency in ('cad', 'usd')),
  amount_cents      int not null,                                        -- the yearly price they pay (locked while they stay)
  stripe_customer   text,
  stripe_sub        text unique,
  status            text not null default 'active',                      -- Stripe's subscription status (active, past_due, canceled...)
  cancel_at_end     boolean not null default false,
  current_period_end timestamptz,                                        -- renews on (or ends on, when cancel_at_end)
  first_paid_at     timestamptz not null default now(),
  refunded_at       timestamptz,
  livemode          boolean not null default false,                      -- test (sandbox) rows stay apart from real ones
  updated_at        timestamptz not null default now(),
  unique (livemode, founding_no)                                         -- sandbox numbers never use up real ones
);
alter table public.pro_members enable row level security;
revoke all on public.pro_members from anon, authenticated;

-- every Stripe event once (Stripe can send the same event twice)
create table if not exists public.pro_events (
  id          text primary key,
  type        text not null,
  received_at timestamptz not null default now()
);
alter table public.pro_events enable row level security;
revoke all on public.pro_events from anon, authenticated;

-- Founding spots taken (live payments only, unless p_live is false = the sandbox count)
create or replace function public.pro_founding_taken(p_live boolean default true)
returns int language sql stable security definer set search_path = public as $$
  select count(*)::int from public.pro_members where founding_no is not null and livemode = p_live and refunded_at is null;
$$;
revoke all on function public.pro_founding_taken(boolean) from public, anon, authenticated;

-- After a paid checkout: record the member and hand out the next founding number (one at a time: the advisory lock makes two payments
-- in the same second get #007 and #008, never both #007). A founding checkout that lands after #100 is gone becomes 'regular' in the
-- table; the webhook then tells us (health email) so the price can be fixed by hand. Returns the founding number, or 0.
create or replace function public.pro_join(p_sub uuid, p_plan text, p_currency text, p_amount int, p_customer text, p_stripe_sub text,
                                           p_period_end timestamptz, p_live boolean)
returns int language plpgsql security definer set search_path = public as $$
declare n int; cur public.pro_members;
begin
  perform pg_advisory_xact_lock(hashtext('gf-pro-founding'));
  select * into cur from public.pro_members where subscriber_id = p_sub;
  if found then
    update public.pro_members set stripe_customer = p_customer, stripe_sub = p_stripe_sub, status = 'active',
           current_period_end = coalesce(p_period_end, current_period_end), refunded_at = null, updated_at = now()
     where subscriber_id = p_sub;
    return coalesce(cur.founding_no, 0);
  end if;
  if p_plan = 'founding' then
    select coalesce(max(founding_no), 0) + 1 into n from public.pro_members where livemode = p_live;
    if n > 100 then n := null; end if;
  end if;
  insert into public.pro_members (subscriber_id, founding_no, plan, currency, amount_cents, stripe_customer, stripe_sub,
                                  current_period_end, livemode)
  values (p_sub, n, case when n is null then 'regular' else 'founding' end, p_currency, p_amount, p_customer, p_stripe_sub,
          p_period_end, p_live);
  return coalesce(n, 0);
end $$;
revoke all on function public.pro_join(uuid, text, text, int, text, text, timestamptz, boolean) from public, anon, authenticated;

-- Is this member Pro right now? (the site asks with the member's own key; Pro perks come in piece 2)
create or replace function public.pro_status(p_token uuid)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce((select jsonb_build_object('pro', m.status in ('active', 'trialing', 'past_due') and m.refunded_at is null,
                                             'founding_no', m.founding_no, 'plan', m.plan, 'renews', m.current_period_end,
                                             'cancel_at_end', m.cancel_at_end, 'test', not m.livemode)
                   from public.subscribers s join public.pro_members m on m.subscriber_id = s.id
                   where s.token = p_token and s.unsubscribed_at is null), '{"pro": false}'::jsonb);
$$;
grant execute on function public.pro_status(uuid) to anon;
