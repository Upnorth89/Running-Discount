-- The Gear Fox: subscriber database.
-- Paste this whole file into Supabase > SQL Editor > New query, then click Run.
-- Safe to run again: it only creates what's missing and replaces the functions.
--
-- How it works
--   * One table, subscribers: email, sizes profile, a private key (token), and consent dates.
--   * Nobody can read or write the table directly from the website (row level security, no policies).
--     The website can only call the small functions below, and every one of them needs either
--     an email address (which then gets a confirmation email) or the private key from an email.
--   * Confirmation emails go out through Resend. The Resend API key lives in Supabase Vault
--     (set it with the one-line command in the instructions, not in this file).

create extension if not exists pg_net;

create table if not exists public.subscribers (
  id              uuid primary key default gen_random_uuid(),
  email           text not null unique check (email = lower(email) and length(email) <= 254),
  profile         jsonb not null default '{}'::jsonb,
  pending_profile jsonb,                       -- changes waiting for the email to be confirmed
  token           uuid not null unique default gen_random_uuid(),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  confirmed_at    timestamptz,                 -- CASL: when they confirmed (express consent)
  unsubscribed_at timestamptz,
  last_mail_at    timestamptz
);
alter table public.subscribers enable row level security;
revoke all on public.subscribers from anon, authenticated;

-- ---------- internal helpers (not callable from the website) ----------

create or replace function public._gf_mail(p_to text, p_subject text, p_html text, p_text text)
returns void language plpgsql security definer set search_path = public as $$
declare k text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'resend_api_key';
  if k is null then raise exception 'resend_api_key is missing from Vault'; end if;
  perform net.http_post(
    url     := 'https://api.resend.com/emails',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Content-Type', 'application/json'),
    body    := jsonb_build_object('from', 'The Gear Fox <deals@thegearfox.com>', 'to', jsonb_build_array(p_to),
                                  'subject', p_subject, 'html', p_html, 'text', p_text));
end $$;

create or replace function public._gf_letter(p_title text, p_body text, p_button text, p_url text, p_lang text default 'en')
returns text language sql immutable as $$
  select '<!doctype html><html lang="' || case when p_lang = 'fr' then 'fr' else 'en' end || '"><body style="margin:0;background:#EEF1EC">'
      || '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF1EC"><tr><td align="center" style="padding:24px 12px">'
      || '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#FFFFFF;border:2px solid #17201C;border-radius:14px">'
      || '<tr><td style="padding:22px 24px 0;text-align:center"><img src="https://thegearfox.com/'
      || case when p_lang = 'fr' then 'logo-email-fr.png' else 'logo-email.png' end
      || '" width="220" alt="The Gear Fox" style="width:220px;max-width:80%;height:auto;border:0"></td></tr>'
      || '<tr><td style="padding:14px 24px 4px;text-align:center;font:800 24px Arial,Helvetica,sans-serif;color:#17201C">' || p_title || '</td></tr>'
      || '<tr><td style="padding:0 24px 18px;text-align:center;font:15px/1.5 Arial,Helvetica,sans-serif;color:#5C6660">' || p_body || '</td></tr>'
      || '<tr><td style="padding:0 24px 24px;text-align:center"><a href="' || p_url || '" style="display:inline-block;background:#F26A1B;color:#17201C;border:2px solid #17201C;border-radius:10px;padding:12px 22px;font:800 16px Arial,Helvetica,sans-serif;text-decoration:none">' || p_button || '</a></td></tr>'
      || '<tr><td style="padding:14px 24px 20px;text-align:center;border-top:2px dashed #CBD2CC;font:12px/1.5 Arial,Helvetica,sans-serif;color:#5C6660">'
      || case when p_lang = 'fr'
              then 'Si vous n''avez rien demandé, ignorez ce courriel et rien ne se passera.<br>The Gear Fox · Flairez les aubaines'
              else 'If you didn''t ask for this, ignore this email and nothing happens.<br>The Gear Fox · Outfox full price' end
      || '</td></tr></table></td></tr></table></body></html>'
$$;

revoke all on function public._gf_mail(text, text, text, text) from public, anon, authenticated;
drop function if exists public._gf_letter(text, text, text, text);   -- older version without a language
revoke all on function public._gf_letter(text, text, text, text, text) from public, anon, authenticated;

-- ---------- functions the website calls ----------

-- Sign up (or update from a new device). Always answers 'sent' so it never reveals who is subscribed.
-- The profile is held as pending until the owner of the email clicks the link.
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
    perform public._gf_mail(e, 'Confirmez vos aubaines du samedi de The Gear Fox',
      public._gf_letter('Un clic pour confirmer',
        'Confirmez votre courriel et chaque samedi matin, on vous envoie ce qui est en solde dans vos tailles. Désabonnement en un clic, en tout temps.',
        'Oui, envoyez-moi les aubaines', link, 'fr'),
      'Confirmez vos aubaines du samedi de The Gear Fox : ' || link);
  else
    perform public._gf_mail(e, 'Confirm your Saturday deals from The Gear Fox',
      public._gf_letter('One tap to confirm',
        'Confirm your email and every Saturday morning we''ll send you what''s on sale in your sizes. Unsubscribe anytime with one click.',
        'Yes, send me deals', link, 'en'),
      'Confirm your Saturday deals from The Gear Fox: ' || link);
  end if;
  update public.subscribers set last_mail_at = now() where id = r.id;
  return 'sent';
end $$;

-- The link in the confirmation email. Saves pending changes and (re)starts the Saturday email.
create or replace function public.confirm(p_token uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r public.subscribers;
begin
  update public.subscribers
     set profile = coalesce(pending_profile, profile), pending_profile = null,
         confirmed_at = case when confirmed_at is null or unsubscribed_at is not null then now() else confirmed_at end,
         unsubscribed_at = null, updated_at = now()
   where token = p_token returning * into r;
  if not found then return null; end if;
  return jsonb_build_object('email', r.email, 'profile', r.profile, 'subscribed', true);
end $$;

-- Links in the weekly email (?k=...): open your profile on any device.
create or replace function public.get_profile(p_token uuid)
returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object('email', email, 'profile', profile,
                            'subscribed', confirmed_at is not null and unsubscribed_at is null)
    from public.subscribers where token = p_token;
$$;

-- Saving the profile on a device that already has the key.
create or replace function public.save_profile(p_token uuid, p_profile jsonb)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  if p_profile is null or jsonb_typeof(p_profile) <> 'object' or octet_length(p_profile::text) > 20000 then
    raise exception 'invalid profile'; end if;
  update public.subscribers set profile = p_profile - 'email', updated_at = now() where token = p_token;
  return found;
end $$;

create or replace function public.unsubscribe(p_token uuid)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  update public.subscribers set unsubscribed_at = coalesce(unsubscribed_at, now()), updated_at = now()
   where token = p_token;
  return found;
end $$;

-- Called once a day by the deals refresh so the free project never pauses for inactivity.
create or replace function public.ping()
returns text language sql stable security definer set search_path = public as $$
  select 'ok ' || count(*) from public.subscribers;
$$;

revoke all on function public.subscribe(text, jsonb), public.confirm(uuid), public.get_profile(uuid),
                       public.save_profile(uuid, jsonb), public.unsubscribe(uuid), public.ping() from public;
grant execute on function public.subscribe(text, jsonb), public.confirm(uuid), public.get_profile(uuid),
                          public.save_profile(uuid, jsonb), public.unsubscribe(uuid), public.ping() to anon, authenticated;
