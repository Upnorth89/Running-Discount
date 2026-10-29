-- Oct 29, 2026 (Bastien: "Yes on each"): SINGLE OPT-IN. About half of email sign-ups never tapped the confirmation link
-- (52% confirmed on Oct 11, even with the reminder). Now an email sign-up is a member right away (Friday email, alerts,
-- watchlist, profile on every device) and gets ONE welcome email from Bastien instead of a confirmation email.
--
-- What stays the same:
--   * Someone who is already a member and signs up again from another device still gets a "save your changes" link
--     (nobody can change a member's sizes or read their watchlist by typing their address).
--   * Someone who unsubscribed and signs up again gets the old confirmation link (their old watchlist stays theirs).
--   * CASL proof of consent: confirmed_at (date/time), consent_via (how: 'form' / 'google' / 'email'), consent_text (the
--     words the form showed, sent by the site).
--   * Bounces and complaints (read from Resend each morning by scraper/mail_health.py) stop all email to that address.
--
-- Paste the whole file in Supabase > SQL Editor > Run. Safe to run again. The last block activates the unconfirmed
-- sign-ups of the last 30 days (not unsubscribed) and sends each one the welcome email, ~1 per second.

alter table public.subscribers add column if not exists consent_text text;
alter table public.subscribers add column if not exists welcomed_at timestamptz;
alter table public.subscribers add column if not exists bounced_at timestamptz;
alter table public.subscribers add column if not exists complained_at timestamptz;

-- Their sizes in one short line for the welcome email ("Men's shoe 11 · clothing M")
create or replace function public._gf_sizes_line(p jsonb, fr boolean)
returns text language sql immutable as $$
  select nullif(concat_ws(' · ',
    case when jsonb_array_length(coalesce(p #> '{sizes,shoes,sizes}', '[]')) > 0 then
      case coalesce(p->>'gender', '')
        when 'men' then case when fr then 'Pointure homme ' else 'Men''s shoe ' end
        when 'women' then case when fr then 'Pointure femme ' else 'Women''s shoe ' end
        else case when fr then 'Pointure ' else 'Shoe ' end end
      || (select string_agg(x, ', ') from jsonb_array_elements_text(p #> '{sizes,shoes,sizes}') x) end,
    case when jsonb_array_length(coalesce(p #> '{sizes,tops,sizes}', '[]')) > 0 then
      case when fr then 'vêtements ' else 'clothing ' end
      || (select string_agg(x, ', ') from jsonb_array_elements_text(p #> '{sizes,tops,sizes}') x) end), '')
$$;

-- The welcome email: "You're in" + what they'll get + their sizes + links to their deals / sizes + one-tap unsubscribe
create or replace function public._gf_welcome(p_id uuid)
returns void language plpgsql security definer set search_path = public as $$
declare
  r public.subscribers;
  fr boolean;
  hike boolean;
  sz text;
  base text;
  body text;
  html text;
  addr text;
begin
  select * into r from public.subscribers where id = p_id;
  if not found or r.unsubscribed_at is not null or r.bounced_at is not null or r.complained_at is not null then return; end if;
  fr := coalesce(r.profile->>'lang', '') = 'fr';
  hike := coalesce(r.profile->>'sport', '') = 'hike';
  sz := public._gf_sizes_line(r.profile, fr);
  base := 'https://thegearfox.com/?k=' || r.token;
  if fr then
    body := 'Chaque semaine, on vous envoie ' || case when hike then 'l''équipement de randonnée' else 'l''équipement de course' end
         || ' en solde dans vos tailles. Et quand un article que vous suivez baisse de prix, on vous le dit.'
         || case when sz is not null then '<br><br><b style="color:#17201C">Vos tailles :</b> ' || sz
              || ' · <a href="' || base || '&show=sizes" style="color:#C2410C">Modifier</a>' else '' end;
  else
    body := 'Every week, we''ll send you the ' || case when hike then 'hiking' else 'running' end
         || ' gear on sale in your sizes. And when something you watch drops in price, we''ll tell you.'
         || case when sz is not null then '<br><br><b style="color:#17201C">Your sizes:</b> ' || sz
              || ' · <a href="' || base || '&show=sizes" style="color:#C2410C">Change</a>' else '' end;
  end if;
  html := public._gf_letter(case when fr then 'C''est fait!' else 'You''re in' end, body,
            case when fr then 'Voir mes aubaines' else 'See my deals' end, base, case when fr then 'fr' else 'en' end);
  -- the letter's footer is for links people didn't ask for; a welcome says "Not you? Unsubscribe" instead
  -- CASL: sender, contact and mailing address on every commercial email (the address lives in Vault as 'mailing_address',
  -- like the MAILING_ADDRESS secret the Friday email uses; without it the line just shows the contact email)
  select decrypted_secret into addr from vault.decrypted_secrets where name = 'mailing_address';
  html := replace(html, 'The Gear Fox · Outfox full price', 'The Gear Fox · Outfox full price · hello@thegearfox.com' || coalesce('<br>' || addr, ''));
  html := replace(html, 'The Gear Fox · Flairez les aubaines', 'The Gear Fox · Flairez les aubaines · hello@thegearfox.com' || coalesce('<br>' || addr, ''));
  html := regexp_replace(html,
            '(If you didn''t ask for this, ignore this email and nothing happens\.|Si vous n''avez rien demandé, ignorez ce courriel et rien ne se passera\.)',
            case when fr then 'Ce n''était pas vous? <a href="https://thegearfox.com/?unsub=' || r.token || '" style="color:#5C6660">Se désabonner</a> en un clic.'
                 else 'Not you? <a href="https://thegearfox.com/?unsub=' || r.token || '" style="color:#5C6660">Unsubscribe</a> in one tap.' end);
  perform public._gf_mail(r.email,
    case when fr then 'Bienvenue sur The Gear Fox' else 'Welcome to The Gear Fox' end, html,
    case when fr then 'C''est fait! Chaque semaine, vos aubaines dans vos tailles. Voir mes aubaines : ' || base
                      || E'\nSe désabonner : https://thegearfox.com/?unsub=' || r.token
         else 'You''re in. Every week, the gear on sale in your sizes. See my deals: ' || base
              || E'\nUnsubscribe: https://thegearfox.com/?unsub=' || r.token end);
  update public.subscribers set welcomed_at = now(), last_mail_at = now() where id = p_id;
end $$;
revoke all on function public._gf_welcome(uuid) from public, anon, authenticated;
revoke all on function public._gf_sizes_line(jsonb, boolean) from public, anon, authenticated;

-- Sign-up. Returns 'k:<key>' when the person is a member now (the site links this device), else 'sent'.
create or replace function public.subscribe(p_email text, p_profile jsonb)
returns text language plpgsql security definer set search_path = public as $$
declare
  e text := lower(trim(coalesce(p_email, '')));
  r public.subscribers;
  recent int;
  active boolean;
  link text;
  fr boolean := coalesce(p_profile->>'lang', '') = 'fr';
  prof jsonb;
  ctext text;
begin
  if length(e) > 254 or e !~ '^[^@\s<>"'']+@[^@\s<>"'']+\.[a-z]{2,}$' then raise exception 'invalid email'; end if;
  if p_profile is null or jsonb_typeof(p_profile) <> 'object' or octet_length(p_profile::text) > 20000 then
    raise exception 'invalid profile'; end if;

  select count(*) into recent from public.subscribers where last_mail_at > now() - interval '1 hour';
  if recent >= 40 then raise exception 'too many sign-ups right now, try again in a few minutes'; end if;

  prof := p_profile - 'email' - 'consent';
  ctext := left(coalesce(p_profile->>'consent', ''), 1000);
  insert into public.subscribers (email) values (e) on conflict (email) do nothing;
  select * into r from public.subscribers where email = e;
  active := r.confirmed_at is not null and r.unsubscribed_at is null;

  -- new, or signed up before and never confirmed: a member now, with a welcome email
  if r.confirmed_at is null and r.unsubscribed_at is null then
    update public.subscribers
       set profile = prof, pending_profile = null, confirmed_at = now(), consent_via = 'form',
           consent_text = nullif(ctext, ''), updated_at = now()
     where id = r.id;
    if r.welcomed_at is null and (r.last_mail_at is null or r.last_mail_at < now() - interval '2 minutes') then
      perform public._gf_welcome(r.id);
    end if;
    return 'k:' || r.token;
  end if;

  -- already a member (another device), or unsubscribed: as before, a link proves it's their inbox
  update public.subscribers set pending_profile = prof, updated_at = now() where id = r.id;
  if r.last_mail_at > now() - interval '2 minutes' or r.bounced_at is not null or r.complained_at is not null then return 'sent'; end if;
  link := 'https://thegearfox.com/?confirm=' || r.token;
  if active and fr then
    perform public._gf_mail(e, 'Enregistrez vos changements The Gear Fox',
      public._gf_letter('Enregistrez vos changements',
        'Quelqu''un (vous, on l''espère) a modifié votre profil The Gear Fox. Cliquez ci-dessous pour enregistrer les changements et voir vos aubaines sur cet appareil.',
        'Enregistrer mes changements', link, 'fr'),
      'Enregistrez vos changements The Gear Fox : ' || link);
  elsif active then
    perform public._gf_mail(e, 'Save your Gear Fox changes',
      public._gf_letter('Save your changes',
        'Someone (hopefully you) updated your Gear Fox profile. Tap below to save the changes and open your deals on this device.',
        'Save my changes', link, 'en'),
      'Save your Gear Fox profile changes: ' || link);
  elsif fr then
    perform public._gf_mail(e, 'Confirmez vos aubaines du vendredi de The Gear Fox',
      public._gf_letter('Un clic pour confirmer',
        'Confirmez votre courriel et chaque vendredi matin, on vous envoie ce qui est en solde dans vos tailles. Désabonnement en un clic, en tout temps.',
        'Oui, envoyez-moi les aubaines', link, 'fr'),
      'Confirmez vos aubaines du vendredi de The Gear Fox : ' || link);
  else
    perform public._gf_mail(e, 'Confirm your Friday deals from The Gear Fox',
      public._gf_letter('One tap to confirm',
        'Confirm your email and every Friday morning we''ll send you what''s on sale in your sizes. Unsubscribe anytime with one click.',
        'Yes, send me deals', link, 'en'),
      'Confirm your Friday deals from The Gear Fox: ' || link);
  end if;
  update public.subscribers set last_mail_at = now() where id = r.id;
  return 'sent';
end $$;

-- Google sign-up: as before (Google checked the address), plus the same welcome email for a new member
create or replace function public.google_subscribe(p_profile jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare e text := public._gf_google_email(); r public.subscribers; was boolean;
begin
  if e is null then raise exception 'not signed in with Google'; end if;
  if p_profile is null or jsonb_typeof(p_profile) <> 'object' or octet_length(p_profile::text) > 20000 then
    raise exception 'invalid profile'; end if;
  insert into public.subscribers (email) values (e) on conflict (email) do nothing;
  select confirmed_at is not null and unsubscribed_at is null into was from public.subscribers where email = e;
  update public.subscribers
     set profile = p_profile - 'email' - 'consent', pending_profile = null, updated_at = now(),
         confirmed_at = case when confirmed_at is null or unsubscribed_at is not null then now() else confirmed_at end,
         consent_via = case when confirmed_at is null or unsubscribed_at is not null then 'google' else consent_via end,
         consent_text = case when confirmed_at is null or unsubscribed_at is not null then nullif(left(coalesce(p_profile->>'consent', ''), 1000), '') else consent_text end,
         unsubscribed_at = null
   where email = e returning * into r;
  if not was and r.welcomed_at is null then perform public._gf_welcome(r.id); end if;
  return jsonb_build_object('email', r.email, 'found', true, 'key', r.token, 'profile', r.profile, 'subscribed', true);
end $$;

revoke all on function public.subscribe(text, jsonb) from public;
grant execute on function public.subscribe(text, jsonb) to anon, authenticated;
revoke all on function public.google_subscribe(jsonb) from public, anon;
grant execute on function public.google_subscribe(jsonb) to authenticated;

-- The unconfirmed sign-ups of the last 30 days (not unsubscribed): members now, one welcome email each (~1 a second:
-- Resend's free plan takes 2 a second). Older ones stay as they are.
do $$
declare s record;
begin
  for s in select id from public.subscribers
            where confirmed_at is null and unsubscribed_at is null and created_at > now() - interval '30 days'
              and bounced_at is null and complained_at is null
            order by created_at loop
    update public.subscribers
       set profile = coalesce(pending_profile, profile) - 'consent', pending_profile = null, confirmed_at = now(),
           consent_via = 'form-before-oct29', updated_at = now()
     where id = s.id;
    perform public._gf_welcome(s.id);
    perform pg_sleep(1);
  end loop;
end $$;
