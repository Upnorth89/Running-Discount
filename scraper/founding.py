"""Fox Pro founding list: the email pieces (Nov 6, 2026; Bastien picked card "A", growth's spec).

Words: docs/founding-ask-copy-nov5.md + artifact X4E2mvP2mdfsWod67evvUM. Email build (designer): tables, bgcolor cells (#F8F5EF card,
#EFE7DC price panel, rust #C8581E button cell), &#10003; in #24492F instead of SVG, fixed px (headline 36px, price 42px), Georgia.

  FOUND_LIVE   off until Bastien's OK after the Nov 16 preview (the site's FOUND_LIVE in index.html is the same switch)
  FOUND_READY  the Nov 27 readiness check: False = the Nov 27 box says "Fox Pro will open in January" instead
Links: ?k=<token>&pro=join&em=<friday|saturday|alert|welcome>-pro. Joining is one tap on the landing page, never on page load
(link scanners open email links).
"""
import html

FOUND_LIVE = False
FOUND_READY = True
BOX_DAYS = {"2026-11-20", "2026-11-21", "2026-11-27"}       # Friday email box: Nov 20 (Saturday group Nov 21) + Nov 27
ALERT_FROM, ALERT_TO = "2026-11-17", "2026-12-01"           # drop/back-in-size alert line

E = lambda s: html.escape(str(s), quote=True)
SERIF = "Georgia,'Times New Roman',serif"
SANS = "-apple-system,'Segoe UI',Roboto,Arial,Helvetica,sans-serif"

# Nov 6 FINAL (Bastien: "yes swap it for the final card"): card 1 = join, card 2 = on the list (after joining + the Nov 27 box)
W = {
    "en": dict(pill="FOUNDING MEMBERS", hl="Good gear.<br>Better timing.", sub="Get the Fox Pro launch link first.", amt="$36", per="CAD / year",
               after="$45/year after the founding round", lock="Founding price locked while you stay.",
               ticks=["It drops after you buy? We email you how to ask the store for the difference.", "Morning price-drop alerts",
                      "Unlimited watchlist (free: 5 from Dec 2)"],
               plan="Planned from Dec 2. 30-day full refund.", btn="Join the founding list&nbsp;→", free="Free to join. Nothing to pay now.",
               foot="100 numbered memberships. First 100 to pay.",
               stat="LIST CONFIRMED", on_hl="You’re on the list.", on_sub="Your founding link is coming by email.", inbox="WATCH YOUR INBOX",
               date="Planned for Wednesday, December&nbsp;2", keep="$36 CAD / year", next="Watch the gear you want now →",
               jan="Fox Pro will open in January. We'll email the list first. Nothing to pay before then.",
               alert=("Get the Fox Pro launch link first: 100 numbered spots at $36/year, price locked while you stay ($45/year after). "
                      "Spots go to the first 100 who pay.\n"
                      "Planned from Dec 2: alerts like this one are part of Fox Pro; free members get watchlist news in the Friday email."),
               alert_btn="Join the founding list"),
    "fr": dict(pill="MEMBRES FONDATEURS", hl="Le bon équipement.<br>Au bon moment.", sub="Recevez le lien de lancement Fox Pro en premier.",
               amt="36&nbsp;$", per="CAD / an", after="45&nbsp;$/an après l’offre fondatrice", lock="Prix fondateur garanti tant que vous restez membre.",
               ticks=["Le prix baisse après l’achat\u00a0? On vous écrit comment demander la différence au magasin.", "Alertes de baisse le matin même",
                      "Liste de suivi illimitée (5 sans Pro dès le 2 déc.)"],
               plan="Prévu dès le 2 décembre. Remboursement complet sous 30&nbsp;jours.", btn="M’inscrire à la liste&nbsp;→",
               free="Inscription gratuite. Rien à payer maintenant.", foot="100 abonnements numérotés. Les 100 premiers à payer.",
               stat="INSCRIPTION CONFIRMÉE", on_hl="Vous êtes sur la liste.", on_sub="Votre lien fondateur arrivera par courriel.",
               inbox="SURVEILLEZ VOS COURRIELS", date="Prévu le mercredi 2&nbsp;décembre", keep="36&nbsp;$ CAD / an",
               next="Suivez dès maintenant l’équipement que vous voulez →",
               jan="Fox Pro ouvrira en janvier. On écrira d'abord aux inscrits. Rien à payer d'ici là.",
               alert=("Recevez le lien Fox Pro en premier : 100 places numérotées à 36 $/an, prix garanti tant que vous restez (45 $/an ensuite). "
                      "Les places vont aux 100 premiers qui paient.\n"
                      "Prévu dès le 2 décembre : ces alertes feront partie de Fox Pro ; les membres gratuits recevront ces nouvelles dans le courriel du vendredi."),
               alert_btn="Je m'inscris"),
}


def text(h):
    """Plain-text version of a line (the email's text part)."""
    import re
    return html.unescape(re.sub(r"<br\s*/?>", " ", h)).replace(" ", " ")


def on_list(p):
    return bool((p or {}).get("pro_wait"))


def box(lang, url, listed=False, ready=True, watch_url=None):
    """The Friday email box (HTML, text). listed = already on the list (Nov 27: card 2, "You're on the list", no join button);
    ready=False (Nov 27 readiness check failed) = the January line."""
    w = W["fr" if lang == "fr" else "en"]
    rule = "border-bottom:1px solid #CFCBC2"
    right = (f'<span style="display:inline-block;font:bold 11px {SANS};letter-spacing:1.5px;color:#24492F;white-space:nowrap">'
             f'<span style="color:#2E7D3A">&#9679;</span>&nbsp;{w["stat"]}</span>' if listed and ready else
             f'<span style="display:inline-block;font:bold 11px {SANS};letter-spacing:1.5px;color:#24492F;border:1.5px solid #24492F;border-radius:99px;padding:4px 10px;white-space:nowrap">{w["pill"]}</span>')
    top = (f'<tr><td style="padding:0 0 12px;{rule}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
           f'<td style="font:bold 15px {SANS};letter-spacing:3px;color:#24492F;white-space:nowrap">FOX PRO</td><td align="right">{right}</td></tr></table></td></tr>')
    wrap = lambda rows: (f'<tr><td style="padding:4px 20px 16px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#F9F6F0" '
                         f'style="background:#F9F6F0;border:1px solid #CFCBC2;border-radius:18px;max-width:420px;margin:0 auto"><tr><td style="padding:22px 22px 18px;color:#121A16">'
                         f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr></table></td></tr>')
    foot = (f'<tr><td style="padding:12px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-top:1px solid #CFCBC2;'
            f'padding:12px 0 0;font:14px/1.4 {SANS};color:#55524C;text-align:center">{w["foot"]}</td></tr></table></td></tr>')
    if not ready:
        rows = top + f'<tr><td style="padding:14px 0 0;font:18px/1.35 {SANS};color:#121A16">{w["jan"]}</td></tr>'
        return wrap(rows), text(w["jan"]) + "\n\n"
    if listed:
        rows = (top + f'<tr><td style="padding:14px 0 0;font:bold 30px/1.05 {SERIF};color:#121A16">{w["on_hl"]}</td></tr>'
                f'<tr><td style="padding:10px 0 0;font:17px/1.35 {SANS};color:#55524C">{w["on_sub"]}</td></tr>'
                f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#E3E8DA" style="background:#E3E8DA;border-radius:12px">'
                f'<tr><td style="padding:14px 16px 4px;font:bold 12px {SANS};letter-spacing:2px;color:#24492F">{w["inbox"]}</td></tr>'
                f'<tr><td style="padding:4px 16px"><table role="presentation" cellpadding="0" cellspacing="0"><tr><td width="44" height="3" bgcolor="#D9480F" style="background:#D9480F;font-size:0;line-height:0">&nbsp;</td></tr></table></td></tr>'
                f'<tr><td style="padding:6px 16px 14px;font:bold 22px/1.15 {SANS};color:#24492F">{w["date"]}</td></tr></table></td></tr>'
                f'<tr><td style="padding:14px 0 0;font:bold 18px {SANS};color:#121A16">{w["keep"]}</td></tr>'
                f'<tr><td style="padding:2px 0 0;font:16px {SANS};color:#55524C">{w["lock"]}</td></tr>'
                + (f'<tr><td style="padding:14px 0 0"><a href="{E(watch_url)}" style="font:bold 16px {SANS};color:#24492F;text-decoration:underline">{w["next"]}</a></td></tr>' if watch_url else "")
                + foot)
        return wrap(rows), (f'{text(w["on_hl"])} {w["on_sub"]} {w["inbox"]}: {text(w["date"])}.\n'
                            + (f'{text(w["next"]).rstrip(" →")}: {watch_url}\n' if watch_url else "") + "\n")
    ticks = "".join(f'<tr><td width="28" valign="top" style="font:bold 18px/1.3 {SANS};color:#2E7D3A">&#10003;</td>'
                    f'<td style="font:500 17px/1.35 {SANS};color:#121A16;padding:0 0 9px">{t}</td></tr>' for t in w["ticks"])
    rows = (top
            + f'<tr><td style="padding:14px 0 0;font:bold 36px/1.04 {SERIF};color:#121A16">{w["hl"]}</td></tr>'
            + f'<tr><td style="padding:10px 0 0;font:17px/1.35 {SANS};color:#55524C">{w["sub"]}</td></tr>'
            + f'<tr><td style="padding:14px 0 0"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
              f'<td valign="middle" style="font:bold 42px/1 {SERIF};color:#121A16;padding:0 12px 0 0;white-space:nowrap">{w["amt"]}</td>'
              f'<td valign="middle"><div style="font:bold 18px {SANS};color:#121A16">{w["per"]}</div><div style="font:14px/1.25 {SANS};color:#55524C">{w["after"]}</div></td></tr></table></td></tr>'
            + f'<tr><td style="padding:12px 0 12px;{rule};font:bold 16px {SANS};color:#24492F">{w["lock"]}</td></tr>'
            + f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{ticks}</table></td></tr>'
            + f'<tr><td style="padding:6px 0 0;font:14px {SANS};color:#55524C;text-align:center">{w["plan"]}</td></tr>'
            + f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td bgcolor="#C8581E" align="center" style="background:#C8581E;border-radius:10px">'
              f'<a href="{E(url)}" style="display:block;padding:14px 16px;font:bold 18px {SANS};color:#FFFFFF;text-decoration:none">{w["btn"]}</a></td></tr></table></td></tr>'
            + f'<tr><td style="padding:8px 0 0;font:14px {SANS};color:#55524C;text-align:center">{w["free"]}</td></tr>'
            + foot)
    txt = (f'{text(w["hl"])} {w["sub"]}\n{text(w["amt"])} {w["per"]} ({text(w["after"])}). {w["lock"]}\n'
           + "".join(f"✓ {t}\n" for t in w["ticks"]) + f'{text(w["plan"])}\n{text(w["btn"]).rstrip(" →")}: {url}\n{w["free"]} {w["foot"]}\n\n')
    return wrap(rows), txt


def alert_lines(lang, url):
    """The drop/back-in-size alert line (plain text, under "Open your watchlist"). Returns (html, text)."""
    w = W["fr" if lang == "fr" else "en"]
    paras = w["alert"].split("\n")
    h = (f'<div style="margin:18px 0 0;padding:12px 14px;border-top:1px solid #E3E7E2;font:14px/1.5 {SANS};color:#17201C">'
         + "".join(f'<p style="margin:0 0 6px">{E(x)}</p>' for x in paras)
         + f'<p style="margin:0"><a href="{E(url)}" style="color:#C8581E;font-weight:bold">{E(w["alert_btn"])} →</a></p></div>')
    return h, "\n".join(paras) + f"\n{w['alert_btn']}: {url}\n"
