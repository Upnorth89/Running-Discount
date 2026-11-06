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
SANS = "Arial,Helvetica,sans-serif"

W = {
    "en": dict(pill="FIRST 100 MEMBERS", hl="Good gear.<br>Better timing.", sub="Get the Fox Pro launch link first.", amt="$36", per="CAD / YEAR",
               after="$45 / year after<br>the founding round", lock="Founding price locked while you stay.",
               ticks=["Morning price-drop alerts", "Unlimited watchlist", "Price-drop emails after you buy"],
               plan="Planned from Dec 2. 30-day full refund.", btn="Join the founding list →", free="Free to join. Nothing to pay now.",
               foot="100 numbered spots. Memberships go to the first 100 who pay.",
               on_hl="You're on<br>the list.", on_sub="Your founding link arrives Wednesday, Dec 2.",
               on_foot="$36 CAD / year, founding price locked while you stay.<br>100 numbered spots. Memberships go to the first 100 who pay.",
               jan="Fox Pro will open in January. We'll email the list first. Nothing to pay before then.",
               alert=("Get the Fox Pro launch link first: 100 numbered spots at $36/year, price locked while you stay ($45/year after). "
                      "Spots go to the first 100 who pay.\n"
                      "Planned from Dec 2: alerts like this one are part of Fox Pro; free members get watchlist news in the Friday email."),
               alert_btn="Join the founding list"),
    "fr": dict(pill="100 PREMIERS MEMBRES", hl="Le bon équipement.<br>Au bon moment.", sub="Recevez le lien de lancement Fox Pro en premier.",
               amt="36&nbsp;$", per="CAD / AN", after="45&nbsp;$ / an après<br>la ronde fondatrice", lock="Prix fondateur garanti tant que vous restez.",
               ticks=["Alertes de baisse chaque matin", "Favoris illimités", "Un courriel si le prix baisse après l'achat"],
               plan="Prévu dès le 2 décembre. Remboursement complet sous 30&nbsp;jours.", btn="M'inscrire à la liste →",
               free="Inscription gratuite. Rien à payer maintenant.", foot="100 places numérotées. Elles vont aux 100 premiers qui paient.",
               on_hl="Vous êtes<br>sur la liste.", on_sub="Votre lien fondateur arrive le mercredi 2 décembre.",
               on_foot="36&nbsp;$ CAD / an, prix fondateur garanti tant que vous restez.<br>100 places numérotées. Elles vont aux 100 premiers qui paient.",
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


def box(lang, url, listed=False, ready=True):
    """The Friday email box (HTML, text). listed = already on the list (Nov 27: "You're on the list", no button);
    ready=False (Nov 27 readiness check failed) = the January line, no button."""
    w = W["fr" if lang == "fr" else "en"]
    top = (f'<tr><td style="padding:0 0 12px;border-bottom:1px solid #C9CFC4"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
           f'<td style="font:bold 15px {SANS};letter-spacing:3px;color:#24492F">FOX PRO</td>'
           f'<td align="right"><span style="display:inline-block;font:bold 11px {SANS};letter-spacing:1px;color:#24492F;border:1.5px solid #24492F;border-radius:99px;padding:4px 10px;white-space:nowrap">{w["pill"]}</span></td>'
           f'</tr></table></td></tr>')
    wrap = lambda rows: (f'<tr><td style="padding:4px 20px 16px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#F8F5EF" '
                         f'style="background:#F8F5EF;border-radius:20px;max-width:420px;margin:0 auto"><tr><td style="padding:22px 22px 18px;color:#121A16">'
                         f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr></table></td></tr>')
    if not ready:
        rows = top + f'<tr><td style="padding:14px 0 0;font:18px/1.35 {SERIF};color:#121A16">{w["jan"]}</td></tr>'
        return wrap(rows), text(w["jan"]) + "\n\n"
    if listed:
        rows = (top + f'<tr><td style="padding:14px 0 0;font:bold 36px/1.05 {SERIF};color:#121A16">{w["on_hl"]}</td></tr>'
                f'<tr><td style="padding:10px 0 0;font:18px/1.3 {SERIF};color:#5C5A55">{w["on_sub"]}</td></tr>'
                f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-top:1px solid #C9CFC4;padding:10px 0 0;font:13px/1.4 {SERIF};color:#5C5A55;text-align:center">{w["on_foot"]}</td></tr></table></td></tr>')
        return wrap(rows), text(w["on_hl"]) + " " + text(w["on_sub"]) + "\n\n"
    ticks = "".join(f'<tr><td width="28" valign="top" style="font:bold 18px/1.3 {SANS};color:#24492F">&#10003;</td>'
                    f'<td style="font:bold 17px/1.3 {SERIF};color:#121A16;padding:0 0 8px">{t}</td></tr>' for t in w["ticks"])
    rows = (top
            + f'<tr><td style="padding:14px 0 0;font:bold 36px/1.05 {SERIF};color:#121A16">{w["hl"]}</td></tr>'
            + f'<tr><td style="padding:10px 0 0;font:18px/1.3 {SERIF};color:#5C5A55">{w["sub"]}</td></tr>'
            + f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#EFE7DC" style="background:#EFE7DC;border-radius:14px">'
              f'<tr><td style="padding:14px 16px 6px"><span style="font:bold 42px/1 {SERIF};color:#121A16">{w["amt"]}</span>'
              f'&nbsp;&nbsp;<span style="font:bold 12px {SANS};letter-spacing:1.5px;color:#121A16">{w["per"]}</span></td></tr>'
              f'<tr><td style="padding:0 16px 4px;font:14px/1.25 {SERIF};color:#5C5A55">{w["after"]}</td></tr>'
              f'<tr><td style="padding:2px 16px 14px;font:italic 16px {SERIF};color:#24492F">{w["lock"]}</td></tr></table></td></tr>'
            + f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{ticks}</table></td></tr>'
            + f'<tr><td style="padding:6px 0 0;font:14px {SERIF};color:#5C5A55;text-align:center">{w["plan"]}</td></tr>'
            + f'<tr><td style="padding:14px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td bgcolor="#C8581E" align="center" style="background:#C8581E;border-radius:10px">'
              f'<a href="{E(url)}" style="display:block;padding:14px 16px;font:bold 18px {SERIF};color:#FFFFFF;text-decoration:none">{w["btn"]}</a></td></tr></table></td></tr>'
            + f'<tr><td style="padding:8px 0 0;font:14px {SERIF};color:#5C5A55;text-align:center">{w["free"]}</td></tr>'
            + f'<tr><td style="padding:12px 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-top:1px solid #C9CFC4;padding:10px 0 0;font:13px/1.4 {SERIF};color:#5C5A55;text-align:center">{w["foot"]}</td></tr></table></td></tr>')
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
