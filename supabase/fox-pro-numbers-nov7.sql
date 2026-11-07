-- Fox Pro founding numbers, the members-lead rules (Nov 7, 2026). Paste once in the Supabase SQL Editor after fox-pro-nov7.sql
-- (safe to paste again). Visitors see nothing; only the Stripe functions use these.
--  * Refunded within the 30 days: the spot never counted. Its number goes back; the next payer gets the LOWEST free number.
--  * Cancelled later: the number is retired forever. If they come back they pay the regular price and get the Pro badge.
--  * Test (sandbox) numbers never use real ones.

alter table public.pro_members add column if not exists retired_no int;   -- a founding number this member held, retired (never reused)

-- a refunded member's number is free again: only members not refunded hold their number
alter table public.pro_members drop constraint if exists pro_members_livemode_founding_no_key;
create unique index if not exists pro_members_live_no on public.pro_members (livemode, founding_no) where refunded_at is null;

-- numbers held or retired (refunded rows free theirs)
create or replace function public.pro_founding_taken(p_live boolean default true)
returns int language sql stable security definer set search_path = public as $$
  select count(*)::int from public.pro_members
   where livemode = p_live and refunded_at is null and (founding_no is not null or retired_no is not null);
$$;
revoke all on function public.pro_founding_taken(boolean) from public, anon, authenticated;

create or replace function public.pro_join(p_sub uuid, p_plan text, p_currency text, p_amount int, p_customer text, p_stripe_sub text,
                                           p_period_end timestamptz, p_live boolean)
returns int language plpgsql security definer set search_path = public as $$
declare n int; cur public.pro_members; had boolean;
begin
  perform pg_advisory_xact_lock(hashtext('gf-pro-founding'));
  select * into cur from public.pro_members where subscriber_id = p_sub;
  had := found;            -- FOUND changes with every later query
  if had and cur.refunded_at is null and cur.status in ('active', 'trialing', 'past_due') then
    -- the same membership again (a repeated event): keep everything
    update public.pro_members set stripe_customer = p_customer, stripe_sub = p_stripe_sub,
           current_period_end = coalesce(p_period_end, current_period_end), updated_at = now()
     where subscriber_id = p_sub;
    return coalesce(cur.founding_no, 0);
  end if;
  if had and cur.refunded_at is null then
    -- came back after cancelling: the old number is retired forever, regular plan and the Pro badge
    update public.pro_members set retired_no = coalesce(founding_no, retired_no), founding_no = null, plan = 'regular',
           currency = p_currency, amount_cents = p_amount, stripe_customer = p_customer, stripe_sub = p_stripe_sub,
           status = 'active', cancel_at_end = false, current_period_end = p_period_end, first_paid_at = now(), updated_at = now()
     where subscriber_id = p_sub;
    return 0;
  end if;
  -- new, or refunded before (the spot never counted): a founding payer gets the lowest number nobody holds or retired
  if p_plan = 'founding' then
    select min(g) into n from generate_series(1, 100) g
     where not exists (select 1 from public.pro_members m where m.livemode = p_live and m.refunded_at is null
                         and (m.founding_no = g or m.retired_no = g));
  end if;
  if had then
    update public.pro_members set founding_no = n, retired_no = null, plan = case when n is null then 'regular' else 'founding' end,
           currency = p_currency, amount_cents = p_amount, stripe_customer = p_customer, stripe_sub = p_stripe_sub, status = 'active',
           cancel_at_end = false, current_period_end = p_period_end, first_paid_at = now(), refunded_at = null, livemode = p_live, updated_at = now()
     where subscriber_id = p_sub;
  else
    insert into public.pro_members (subscriber_id, founding_no, plan, currency, amount_cents, stripe_customer, stripe_sub,
                                    current_period_end, livemode)
    values (p_sub, n, case when n is null then 'regular' else 'founding' end, p_currency, p_amount, p_customer, p_stripe_sub,
            p_period_end, p_live);
  end if;
  return coalesce(n, 0);
end $$;
revoke all on function public.pro_join(uuid, text, text, int, text, text, timestamptz, boolean) from public, anon, authenticated;

-- the checkout asks this before choosing the price: a member who held a founding number and cancelled pays the regular price
create or replace function public.pro_returning(p_sub uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.pro_members where subscriber_id = p_sub and refunded_at is null
                  and (founding_no is not null or retired_no is not null or plan = 'regular'));
$$;
revoke all on function public.pro_returning(uuid) from public, anon, authenticated;

-- pro_status also says which badge to show (founding number or Pro)
create or replace function public.pro_status(p_token uuid)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce((select jsonb_build_object('pro', m.status in ('active', 'trialing', 'past_due') and m.refunded_at is null,
                                             'founding_no', m.founding_no, 'plan', m.plan, 'renews', m.current_period_end,
                                             'cancel_at_end', m.cancel_at_end, 'test', not m.livemode,
                                             'badge', case when m.founding_no is not null then 'founding' else 'pro' end)
                   from public.subscribers s join public.pro_members m on m.subscriber_id = s.id
                   where s.token = p_token and s.unsubscribed_at is null), '{"pro": false}'::jsonb);
$$;
grant execute on function public.pro_status(uuid) to anon;
