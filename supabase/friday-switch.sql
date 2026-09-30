-- Friday switch: the two email functions whose wording changed (safe to run; replaces them in place),
-- plus a column recording when each person last got the Friday email (so the hourly runs never send twice).

alter table public.subscribers add column if not exists weekly_sent_at timestamptz;

create or replace function public.subscribe(p_email text, p_profile jsonb)
returns text language plpgsql security definer set search_path = public as $$
declare
  e text := lower(trim(coalesce(p_email, '')));
  r public.subscribers;
  recent int;
  active boolean;
  link text;
  fr boolean := coalesce(p_profile->>'lang', '') = 'fr';
begin
  if length(e) > 254 or e !~ '^[^@\s<>"'']+@[^@\s<>"'']+\.[a-z]{2,}$' then raise exception 'invalid email'; end if;
  if p_profile is null or jsonb_typeof(p_profile) <> 'object' or octet_length(p_profile::text) > 20000 then
    raise exception 'invalid profile'; end if;

  select count(*) into recent from public.subscribers where last_mail_at > now() - interval '1 hour';
  if recent >= 40 then raise exception 'too many sign-ups right now, try again in a few minutes'; end if;

  insert into public.subscribers (email) values (e) on conflict (email) do nothing;
  update public.subscribers set pending_profile = p_profile - 'email', updated_at = now()
   where email = e returning * into r;

  if r.last_mail_at > now() - interval '2 minutes' then return 'sent'; end if;   -- don't flood an inbox

  active := r.confirmed_at is not null and r.unsubscribed_at is null;
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

create or replace function public.send_link(p_email text, p_lang text default 'en')
returns text language plpgsql security definer set search_path = public as $$
declare
  e text := lower(trim(coalesce(p_email, '')));
  r public.subscribers;
  recent int;
  fr boolean;
  link text;
begin
  if length(e) > 254 or e !~ '^[^@\s<>"'']+@[^@\s<>"'']+\.[a-z]{2,}$' then raise exception 'invalid email'; end if;
  select * into r from public.subscribers where email = e;
  if not found then return 'sent'; end if;
  if r.last_mail_at > now() - interval '2 minutes' then return 'sent'; end if;
  select count(*) into recent from public.subscribers where last_mail_at > now() - interval '1 hour';
  if recent >= 40 then raise exception 'too many requests right now, try again in a few minutes'; end if;
  fr := coalesce(r.profile->>'lang', r.pending_profile->>'lang', p_lang) = 'fr';
  if r.confirmed_at is not null and r.unsubscribed_at is null then
    link := 'https://thegearfox.com/?k=' || r.token;
    if fr then
      perform public._gf_mail(e, 'Votre lien The Gear Fox',
        public._gf_letter('Vos aubaines, sur cet appareil',
          'Cliquez ci-dessous pour ouvrir vos aubaines avec vos tailles sur cet appareil. Pas besoin de vous réabonner.',
          'Ouvrir mes aubaines', link, 'fr'),
        'Ouvrez vos aubaines The Gear Fox : ' || link);
    else
      perform public._gf_mail(e, 'Your Gear Fox link',
        public._gf_letter('Your deals, on this device',
          'Tap below to open your deals with your sizes on this device. No need to sign up again.',
          'Open my deals', link, 'en'),
        'Open your Gear Fox deals: ' || link);
    end if;
  else
    link := 'https://thegearfox.com/?confirm=' || r.token;
    if fr then
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
  end if;
  update public.subscribers set last_mail_at = now() where id = r.id;
  return 'sent';
end $$;
