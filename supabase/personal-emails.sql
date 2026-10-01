-- The Gear Fox: confirmation and sign-in emails as a short personal note from Bastien.
-- Gmail files emails with logos and big buttons under Promotions; a plain note with a text link usually lands in
-- Primary, and the confirmation is the one email people must not miss. Same functions and parameters as in
-- setup.sql (the sign-up and sign-in functions call them unchanged). Paste into Supabase > SQL Editor once.
-- The Friday email and alerts are sent from GitHub (scraper/), not from here, and keep "The Gear Fox".

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
  select '<!doctype html><html lang="' || case when p_lang = 'fr' then 'fr' else 'en' end || '"><body style="margin:0;background:#FFFFFF">'
      || '<div style="max-width:520px;padding:20px 16px;font:15px/1.6 Arial,Helvetica,sans-serif;color:#17201C">'
      || '<p style="margin:0 0 12px"><b>' || p_title || '</b></p>'
      || '<p style="margin:0 0 12px">' || p_body || '</p>'
      || '<p style="margin:0 0 16px"><a href="' || p_url || '" style="color:#B8470A;font-weight:bold">' || p_button || '</a></p>'
      || '<p style="margin:0 0 16px;color:#5C6660;font-size:13px">'
      || case when p_lang = 'fr'
              then 'Astuce : déplacez ce courriel dans l''onglet Principal (ou indiquez « Pas un courriel indésirable ») pour ne jamais manquer les aubaines du vendredi.'
              else 'Tip: move this email to your Primary tab (or mark it "Not junk") so you never miss Friday''s deals.' end
      || '</p><p style="margin:0">' || case when p_lang = 'fr' then 'Bastien<br>The Gear Fox · Flairez les aubaines'
                                             else 'Bastien<br>The Gear Fox · Outfox full price' end || '</p>'
      || '<p style="margin:16px 0 0;color:#5C6660;font-size:12px">'
      || case when p_lang = 'fr' then 'Si vous n''avez rien demandé, ignorez ce courriel et rien ne se passera.'
              else 'If you didn''t ask for this, ignore this email and nothing happens.' end
      || '</p></div></body></html>'
$$;

revoke all on function public._gf_mail(text, text, text, text) from public, anon, authenticated;
revoke all on function public._gf_letter(text, text, text, text, text) from public, anon, authenticated;
