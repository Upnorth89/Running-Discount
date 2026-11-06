-- The Gear Fox: Fox Pro founding list, the welcome email's P.S. (Nov 6, 2026; Bastien picked card "A", growth's spec).
-- Paste into Supabase > SQL Editor once. Nothing changes for anyone until the switch is on:
--   insert into public.ana_settings (name, value) values ('founding_live', 'on') on conflict (name) do update set value = 'on';
-- (after Bastien's OK on the Nov 16 preview; the site's FOUND_LIVE and scraper/founding.py FOUND_LIVE go on the same day).
-- The P.S. shows Nov 17-30 (Vancouver date) to new members who aren't already on the list. Otherwise this is the Oct 29 welcome, unchanged.

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
  fp boolean;
  ps text := '';
  ps_txt text := '';
begin
  select * into r from public.subscribers where id = p_id;
  if not found or r.unsubscribed_at is not null or r.bounced_at is not null or r.complained_at is not null then return; end if;
  fr := coalesce(r.profile->>'lang', '') = 'fr';
  hike := coalesce(r.profile->>'sport', '') = 'hike';
  sz := public._gf_sizes_line(r.profile, fr);
  base := 'https://thegearfox.com/?k=' || r.token;
  -- Nov 6 (Fox Pro founding list, Bastien picked card "A"): new members Nov 17-30 (Vancouver date) who aren't on the list get one P.S.
  -- under "See my deals". Off until ana_settings 'founding_live' = 'on' (set after Bastien's OK on the Nov 16 preview).
  fp := coalesce((select value from public.ana_settings where name = 'founding_live'), '') = 'on'
        and (now() at time zone 'America/Vancouver')::date between date '2026-11-17' and date '2026-11-30'
        and coalesce(r.profile->'pro_wait', 'null'::jsonb) = 'null'::jsonb;
  if fp then
    if fr then
      ps_txt := 'P.-S. Recevez le lien en premier : 100 places numérotées de membre fondateur à 36 $/an, prix garanti tant que vous restez membre (45 $/an ensuite). '
             || 'Les places vont aux 100 premiers qui paient. Fox Pro, prévu dès le 2 décembre : le prix baisse après l’achat ? On vous écrit comment demander la différence au magasin. Alertes de baisse le matin même, liste de suivi illimitée. '
             || 'S''inscrire à la liste est gratuit. Rien à payer maintenant.';
      ps := ps_txt || ' <a href="' || base || '&pro=join&em=welcome-pro" style="color:#C8581E;font-weight:bold">Je m''inscris</a>';
      ps_txt := ps_txt || ' Je m''inscris : ' || base || '&pro=join&em=welcome-pro';
    else
      ps_txt := 'P.S. Get the link first: 100 numbered Founding Fox spots at $36/year, price locked while you stay (everyone after pays $45/year). '
             || 'Spots go to the first 100 who pay. Fox Pro, planned from Dec 2: it drops after you buy? We email you how to ask the store for the difference. Morning price-drop alerts, unlimited watchlist. '
             || 'Joining the list is free. Nothing to pay now.';
      ps := ps_txt || ' <a href="' || base || '&pro=join&em=welcome-pro" style="color:#C8581E;font-weight:bold">Join the founding list</a>';
      ps_txt := ps_txt || ' Join the founding list: ' || base || '&pro=join&em=welcome-pro';
    end if;
  end if;
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
  if fp then      -- the P.S. row goes right under the "See my deals" button
    html := replace(html, '<tr><td style="padding:14px 24px 20px;text-align:center;border-top:2px dashed #CBD2CC;',
      '<tr><td style="padding:0 24px 20px;text-align:left;font:14px/1.5 Arial,Helvetica,sans-serif;color:#17201C">' || ps || '</td></tr>'
      || '<tr><td style="padding:14px 24px 20px;text-align:center;border-top:2px dashed #CBD2CC;');
  end if;
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
              || E'\nUnsubscribe: https://thegearfox.com/?unsub=' || r.token end
    || case when fp then E'\n\n' || ps_txt else '' end);
  update public.subscribers set welcomed_at = now(), last_mail_at = now() where id = p_id;
end $$;
revoke all on function public._gf_welcome(uuid) from public, anon, authenticated;
