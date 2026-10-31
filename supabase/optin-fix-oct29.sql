-- Oct 29 fix for single-optin-oct29.sql (paste in Supabase > SQL Editor > Run; safe to run again).
-- The 30-day catch-up stamped last_mail_at on every welcome email it sent, and the sign-up limit counted those: 40+ emails in the
-- last hour = "too many sign-ups right now" for EVERY visitor until the hour passed. 1) un-stamp the catch-up, 2) the limit now counts
-- new sign-ups in the last hour, not emails.
update public.subscribers set last_mail_at = null where consent_via = 'form-before-oct29';

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

  -- Oct 29 fix: count new sign-ups in the last hour (not emails sent: the 30-day catch-up's welcome emails blocked every sign-up for an hour)
  select count(*) into recent from public.subscribers where created_at > now() - interval '1 hour';
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

revoke all on function public.subscribe(text, jsonb) from public;
grant execute on function public.subscribe(text, jsonb) to anon, authenticated;
