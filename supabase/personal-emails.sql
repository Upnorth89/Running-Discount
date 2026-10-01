-- The Gear Fox: confirmation and sign-in emails come from "Bastien from The Gear Fox" <bastien@thegearfox.com>
-- (a different address from the Friday deals) in the branded design from setup.sql.
-- Oct 1, 2026 test: with Resend open/click tracking ON they landed in Gmail Promotions; with tracking OFF
-- (Resend > Domains > thegearfox.com > Configuration) the plain version landed in Primary. Keep tracking off.
-- Paste into Supabase > SQL Editor once.
create or replace function public._gf_mail(p_to text, p_subject text, p_html text, p_text text)
returns void language plpgsql security definer set search_path = public as $$
declare k text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'resend_api_key';
  if k is null then raise exception 'resend_api_key is missing from Vault'; end if;
  perform net.http_post(
    url     := 'https://api.resend.com/emails',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Content-Type', 'application/json'),
    body    := jsonb_build_object('from', 'Bastien from The Gear Fox <bastien@thegearfox.com>', 'to', jsonb_build_array(p_to),
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
revoke all on function public._gf_letter(text, text, text, text, text) from public, anon, authenticated;
