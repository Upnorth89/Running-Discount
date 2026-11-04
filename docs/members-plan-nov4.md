# Members plan: founding list asks, a note to watchers, one Friday change, reply drafts
Members lead, night of Nov 3-4, 2026. Drafts only: nothing sent, no code changed. Every public line goes through compliance before it ships.

## Numbers this rests on (funnel.yml run 41466393627, Nov 2, last 14 days = Oct 19 - Nov 2; GitHub run logs)
- 155 real members. Watchlist sizes: 0 items 114, 1 item 21, 2 items 6, 3 items 3, 4-5 items 4, 6-10 items 7, 11+ 0. **41 members watch something** (the brief said ~38).
- Visits from our emails: friday 16, alert 16, saturday 7.
  - Friday/Saturday sends: Oct 31 (Saturday group) = 72 emails sent (run logs). Oct 23 + Oct 30 Friday logs have expired; I estimate ~170 sends from the list size. So the weekly email brings **about 1 visit per 10 emails**.
  - Alerts: 0-7 sent a day (refresh logs Nov 1-3: 1, 7, 1, 1 sent). That's roughly 30 alerts in the window bringing 16 visits, so **about 1 visit per 2 emails**. These are estimates (counts are small), not proof. Still, the email about items people chose brings ~5x the visits of the generic one.
- Members come back: 66 of 127 who signed up (52%) vs 15% of everyone else. Watchers on the first visit: 41% (27 devices, a lead only).
- First visits from the Friday email: 7, of which 0 picked sizes and 2 clicked a store.
- Measurement gap: the deal cards in the Friday email link straight to the store with no tag. Store taps from the email are invisible to us. "Visits per email" counts only the few links that come to our site (logo, small "See all" links, "♡ Watch the price", the bottom button).

---

## 1. The founding-list ask inside existing emails (one line + one button each)

### How the button works (spec for the backend chat)
- Link: `https://thegearfox.com/?k=<token>&pro=join&em=<tag>`. Tags: `friday-pro` / `saturday-pro` (Nov 20-21), `friday-pro` (Nov 27), `alert-pro`, `welcome-pro`.
- The page opens the approved founding card (screen 1 in docs/fox-pro-screens.html) and the member taps "Join the founding list" once (saves `pro_wait`).
- **Never join on page load.** Outlook/Microsoft Safe Links and other security scanners open every link in an email. Joining on load would add fake names to the list and break the 40-person readiness count.
- Anyone already on the list (`pro_wait` set) gets no ask (Nov 20, alerts, welcome). On Nov 27 they get the "you're on the list" line instead.
- Funnel: count `pro-join` by `em` tag, so we know which email filled the list.
- Wording follows the approved card exactly: "$36/year for founding members (that's $3/month), price locked while you stay", 100 numbered spots, no payment now. $3/month never as the headline, no "for life", no countdown.

### a) Friday email, Nov 20
The emailday test runs until Nov 21, so group B gets this on Saturday Nov 21. That's still the agreed weekly email, not an extra one.

Where: right after the "Dropped this week in your size" block, before the category sections. Value first, then the ask. A bordered box like the first-email note (#FFF4EC, orange border), with a white button outlined in charcoal so it doesn't compete with the orange main button.

EN
> **Fox Pro opens Dec 2.** Same-morning drop alerts, no watchlist limit, and we keep watching the price after you buy. $36/year for the 100 founding members (that's $3/month), price locked while you stay. Nothing to pay now.
> [Join the founding list]

FR
> **Fox Pro ouvre le 2 décembre.** Alertes de baisse le matin même, favoris illimités, et on continue de surveiller le prix après votre achat. 36 $/an pour les 100 membres fondateurs (3 $/mois), prix garanti tant que vous restez membre. Rien à payer maintenant.
> [M'inscrire sur la liste]

### b) Friday email, Nov 27 (Black Friday; same Friday email, Friday for everyone)
Where: same spot.

Not on the list, EN
> **The founding list gets Fox Pro first, on Wednesday, Dec 2** (two days before everyone else). $36/year for the 100 founding members (that's $3/month), price locked while you stay. Joining costs nothing.
> [Join the founding list]

Not on the list, FR
> **Les inscrits sur la liste auront accès à Fox Pro en premier, le mercredi 2 décembre** (deux jours avant tout le monde). 36 $/an pour les 100 membres fondateurs (3 $/mois), prix garanti tant que vous restez membre. S'inscrire ne coûte rien.
> [M'inscrire sur la liste]

Already on the list (no button), EN
> You're on the founding list. Your link arrives Wednesday, Dec 2, at the same time as everyone else on it.

FR
> Vous êtes sur la liste des fondateurs. Votre lien arrive le mercredi 2 décembre, en même temps que tous les inscrits.

**Risk to fix in the plan: the readiness bar is checked Nov 27, the same morning this email goes out at 7am.** If the bar fails, "Dec 2" becomes false in an email we already sent. Ask: hold the readiness decision on **Wednesday Nov 25** (the readiness weeks are almost over by then). Or keep a ready swap line for Nov 27: "Fox Pro will open in January. We'll email the list first. Nothing to pay before then." / « Fox Pro ouvrira en janvier. On écrira d'abord aux inscrits. Rien à payer d'ici là. »

### c) Drop / back-in-size alerts, Nov 17 - Dec 1 (members not on the list)
Where: below the orange "Open your watchlist" button, above the fine print, separated by a thin line. The same small outlined button.

EN
> This alert came the morning the price changed. From Dec 2, same-morning alerts are part of Fox Pro; free members get watchlist news in the Friday email. Founding members: $36/year (that's $3/month), locked while you stay, 100 spots.
> [Join the founding list]

FR
> Cette alerte vous est arrivée le matin même du changement de prix. Dès le 2 décembre, les alertes du matin même feront partie de Fox Pro; les membres gratuits recevront les nouvelles de leurs favoris dans le courriel du vendredi. Membres fondateurs : 36 $/an (3 $/mois), prix garanti tant que vous restez membre, 100 places.
> [M'inscrire sur la liste]

Why it says what changes: the approved Pro table moves free drop alerts to the Friday email. The people reading an alert are exactly the ones who lose same-morning alerts. Telling them inside the alert is the honest version. Hiding it until Dec 2 would cost trust with our most engaged members.

### d) Welcome email (new members, Nov 17 - Dec 1)
Where: one line under the "See my deals" button (`_gf_welcome` in Supabase SQL, so Bastien pastes the change). The main ask stays "See my deals".

EN
> One more thing: Fox Pro opens Dec 2. Founding members pay $36/year (that's $3/month), price locked while you stay; 100 numbered spots. Want first access?
> [Join the founding list]

FR
> Autre chose : Fox Pro ouvre le 2 décembre. Les membres fondateurs paient 36 $/an (3 $/mois), prix garanti tant que vous restez membre; 100 places numérotées. Envie d'y avoir accès en premier?
> [M'inscrire sur la liste]

Same change: the welcome's "See my deals" link has no `em=` tag (the Oct 31 decisions row lists it as not done). Add `&em=welcome` so welcome visits count.

### CASL check on all four
Each spot rides inside an email that already has sender, contact, mailing address and one-tap unsubscribe (weekly_email.py footer, alerts.py footer, `_gf_welcome`). No new email, no new rhythm, and every recipient already gave consent.
**One thing to verify:** `_gf_welcome` only shows the postal address if Vault holds `mailing_address`. Without it, the line falls back to the contact email only, and CASL requires a mailing address. Bastien should check that the Vault secret exists (Supabase > Vault) before Nov 17.

### Will it reach 40? (blunt)
- About 400 weekly emails across Nov 20 + 27, at ~1 visit per 10 emails, means ~40 visits.
- Alerts reach ~41 watchers.
- My estimate: the email asks bring **15-25 joins, not 40**. The rest has to come from the site's founding card (members tap once, Nov 17-30), the watcher note below, and Black Friday traffic. The growth chat should know that.

---

## 2. Personal note from Bastien to the 41 members who watch something

**On its own around Nov 17, it is an extra email.** It's outside the Friday rhythm, so it breaks our rule (CASL would allow it: they consented and the footer is there). Compliant version: **the note opens their Nov 20 weekly email** (Nov 21 for the Saturday group), as a block above the drops, only for members with 1+ watched item. Same send, same subject rules.

Three things before it ships (backend + Bastien):
- **Reply-to:** set `reply_to` to bastien@thegearfox.com (or hello@) for this block's recipients. The email comes from deals@, and the note asks for replies.
- **Personalization:** fill {first} and {n} from their watches (alerts.py already reads them). No name: "Hi,".
- **Bastien decides first:** what happens on Dec 2 to free members who already watch more than 5 items (7 members watch 6-10). My recommendation: keep what they watch, and limit only new adds. Taking items away from our most active members is the fastest way to lose them. The line in brackets below depends on his answer.

EN (block title: "A note from Bastien")
> Hi {first},
> Quick one from me. You're watching {n} {item/items} on The Gear Fox, which is exactly how I hoped people would use it. Two things before December:
> **Fox Pro opens Dec 2.** It's built for people who watch prices: alerts the same morning a price drops, no limit on your list, and we keep watching after you buy, in case the store refunds a drop. Founding members pay $36/year (that's $3/month), locked while you stay. 100 numbered spots; the list gets the link first. [Join the founding list]
> **What changes for free members:** from Dec 2, your watchlist news comes in the Friday email instead of the same morning, and new watches stop at 5 items. [Everything you watch today stays on your list.]
> If you have a minute, hit reply and tell me what you'd want from it. I read every reply.
> Bastien

FR (titre : « Un mot de Bastien »)
> Bonjour {first},
> Un petit mot de ma part. Vous suivez {n} {article/articles} sur The Gear Fox, et c'est exactement comme ça que j'espérais qu'on l'utilise. Deux choses avant décembre :
> **Fox Pro ouvre le 2 décembre.** C'est fait pour ceux qui surveillent les prix : alertes le matin même d'une baisse, favoris illimités, et on continue de surveiller après votre achat, au cas où le magasin rembourserait la différence. Les membres fondateurs paient 36 $/an (3 $/mois), prix garanti tant que vous restez membre. 100 places numérotées; les inscrits reçoivent le lien en premier. [M'inscrire sur la liste]
> **Ce qui change pour les membres gratuits :** dès le 2 décembre, les nouvelles de vos favoris arrivent dans le courriel du vendredi plutôt que le matin même, et les nouveaux ajouts s'arrêtent à 5 articles. [Tout ce que vous suivez aujourd'hui reste dans votre liste.]
> Si vous avez une minute, répondez à ce courriel pour me dire ce que vous en attendez. Je lis toutes les réponses.
> Bastien

**Risk to raise with Bastien (a new fact, not a reversal):**
- Today the same-morning alert is our best come-back email: ~1 visit per 2 sends vs ~1 per 10 for the weekly email.
- From Dec 2, free watchers lose it. Their return rate may drop.
- Not a reason to change the Pro plan. It is a number to watch: watchers' 7-day return rate before vs after Dec 2. If it falls by half, look at it again in January.
- Measure the note: replies (count them by hand), founding-list joins tagged `friday-pro` from the 41, and unsubscribes among them (should stay 0-1).

---

## 3. The one Friday change: a "See my deals" button at the top

**Change:** put the "See all N deals in your size" button right under the intro (before "Dropped this week"), as well as at the bottom. The top copy carries its own tag, `em=friday-top` / `em=saturday-top`.

Copy (the same words as the existing bottom button, so no new translation risk):
- EN: [See all {n} deals in your size]
- FR: [Voir les {n} aubaines à votre taille]

**Why this one:**
- Today the only big link to our site is at the very bottom, after up to 26 cards. Every card above it goes straight to a store.
- Most readers never scroll that far. Nielsen Norman Group's newsletter studies found people skim and scan newsletters and act on what they see first. Litmus' attention data puts average email read time around 9-10 seconds.
- Our own hint: the alert email puts its site button within the first screen and brings ~5x the visits per email. Different intent, so a lead, not proof.
- It removes nothing (subject, drops and cards stay). It costs one block of HTML, and the freeze doesn't cover emails.

**Rejected:**
- Sending card taps to our site instead of the store. That adds a hop people didn't ask for and inflates our number instead of helping them.
- A preheader line. The intro already fills the inbox preview with "N things dropped in your sizes".

**How we measure (A/B not possible: say so):**
- ~160 emails a week, already split by the emailday test until Nov 21. Detecting 10 -> 20 visits per 100 emails needs ~200 emails per group per variant, which we don't have before Black Friday.
- So: before/after plus the button's own tag.
- **Metric:** email visits per email sent = visits tagged email-friday*/saturday* ÷ "sent" lines in the weekly-email run logs.
  - Baseline ~10 per 100 (Oct 31: 7 visits / 72 sent, counted by Nov 2; Oct 23 + 30 estimated).
  - Plus the share of email visits arriving via `-top`.
- **Ship:** for the Nov 13 send (both groups get it the same day, so the day test stays fair).
- **Check dates:**
  - Mon Nov 16: Nov 13-14 sends vs Oct 30 - Nov 7.
  - Mon Nov 30: Nov 20-21 + Nov 27, with the Black Friday caveat. BF will raise visits on its own, so judge Nov 27 mainly on the `-top` share.
- **Keep rule:** `-top` brings at least a third of email visits, or visits per email rise above 15 per 100. Under 2 `-top` visits across two sends = remove it.
- **Backend note:** funnel.py's EMAIL DAY TEST line counts the exact "email-friday"/"email-saturday" only. Make it count the prefix so the new tag doesn't vanish from the test.

---

## 4. Reply drafts for Bastien (his voice: warm, short)

"Wrong price or size?" reports from the site are anonymous (no email). These drafts are for people who write to hello@ or DM.

### a) Someone flagged a wrong price (filled with the real Nov 3 fix; swap the brackets for other cases)
EN
> Hi [name], thanks for flagging the LMNT electrolytes. You were right. That "50% off" was a wholesale-only product the store keeps hidden from shoppers, and we were reading it like a normal sale. We fixed it the same day: we now skip products a store marks wholesale or hidden, at every store, so it can't come back. Reports like yours are how we catch these. Thank you!
> Bastien, The Gear Fox

FR
> Bonjour [nom], merci d'avoir signalé les électrolytes LMNT. Vous aviez raison : ce « 50 % de rabais » était un produit réservé aux grossistes, caché aux clients, et on le lisait comme un solde normal. C'est corrigé depuis le jour même : on ignore maintenant les produits qu'un magasin marque « grossiste » ou « caché », dans toutes les boutiques, pour que ça ne revienne pas. Ce sont des signalements comme le vôtre qui nous permettent de les attraper. Merci!
> Bastien, The Gear Fox

Template when our data was right but the card misled (the Oct 29 Foot Locker case):
EN
> Hi [name], thanks for the heads-up on the [item]. I checked: [store]'s price was right, but only in [sizes]. Our card showed it next to every size, which was misleading. Cards now say "From $X" and show the price for your own size. Thanks for helping make it better.
> Bastien

FR
> Bonjour [nom], merci pour le signalement sur [article]. J'ai vérifié : le prix de [magasin] était bon, mais seulement en [tailles]. Notre fiche l'affichait à côté de toutes les tailles, ce qui portait à confusion. Les fiches indiquent maintenant « À partir de X $ » et le prix dans votre taille. Merci de nous aider à nous améliorer.
> Bastien

(Never write "fixed" until the fix is live, and say what was ours vs the store's.)

### b) A member asks how alerts work
EN
> Hi [name], good question! Tap "♡ Watch price" on any item and we check it every morning in your sizes. You get an email when the price drops at least 10% or $10 from the last price we told you, or when it's back in stock in your size. To keep your inbox calm, it's at most one alert every 3 days, and none on Fridays (your Friday email carries the news). You can watch up to 10 items for now. Remove an item and the alerts for it stop.
> Bastien

FR
> Bonjour [nom], bonne question! Touchez « Suivre le prix » sur n'importe quel article et on le vérifie chaque matin dans vos tailles. Vous recevez un courriel quand le prix baisse d'au moins 10 % ou 10 $ par rapport au dernier prix qu'on vous a donné, ou quand l'article revient en stock dans votre taille. Pour ne pas encombrer votre boîte, c'est au plus une alerte aux 3 jours, et aucune le vendredi (le courriel du vendredi vous donne les nouvelles). Vous pouvez suivre jusqu'à 10 articles pour l'instant. Retirez un article et ses alertes s'arrêtent.
> Bastien

From Nov 17, add: "Heads-up: from Dec 2, free members get these in the Friday email, and same-morning alerts become part of Fox Pro." / « À noter : dès le 2 décembre, les membres gratuits recevront ces nouvelles dans le courriel du vendredi, et les alertes du matin même feront partie de Fox Pro. »

### c) "Is Fox Pro worth it?"
EN
> Hi [name], honest answer: it depends how you shop. If you watch a couple of items and the Friday email is enough, stay free. The deals, sizes and shoe price pages aren't going anywhere. Pro is worth it if you watch a lot of gear or want to know the same morning a price drops. Also if you'd like us to keep watching after you buy: some stores refund the difference when their price drops, and we'll show you their rule and the message to send. The store decides, but one $20 refund covers the year. Founding price is $36/year (that's $3/month), locked while you stay, with a full refund within 30 days if it's not for you.
> Bastien

FR
> Bonjour [nom], réponse honnête : ça dépend de votre façon de magasiner. Si vous suivez quelques articles et que le courriel du vendredi vous suffit, restez gratuit. Les aubaines, les tailles et les pages de prix ne disparaissent pas. Pro vaut la peine si vous suivez beaucoup d'équipement ou voulez savoir le matin même qu'un prix baisse. Aussi si vous voulez qu'on continue de surveiller après votre achat : certains magasins remboursent la différence si leur prix baisse, et on vous montre leur politique et le message à envoyer. La décision revient au magasin, mais un seul remboursement de 20 $ paie l'année. Le prix fondateur est de 36 $/an (3 $/mois), garanti tant que vous restez membre, avec remboursement complet sous 30 jours si ça ne vous convient pas.
> Bastien

---

## Asks for Bastien (one line each)
1. Readiness decision by Wed Nov 25, so the Nov 27 email can't promise a Dec 2 that moves? yes/no
2. Free members with 6-10 watched items on Dec 2: keep what they have and limit only new adds (my pick)? yes/no
3. The watcher note as a block in the Nov 20 email (not a separate email), with replies going to bastien@? yes/no
4. Top "See my deals" button in the Friday email from the Nov 13 send? yes/no
5. Check that Vault has `mailing_address` (welcome email CASL line).

## For the backend chat once he says yes (specs, no code from me)
- `pro=join` landing (one tap, never on load), with `em` tags in pro-join analytics.
- The ask blocks in weekly_email.py (Nov 20-21 / Nov 27 variants, skipping `pro_wait`) and alerts.py (Nov 17 - Dec 1).
- `_gf_welcome` line + `&em=welcome` (SQL for Bastien to paste).
- Watcher note block + `reply_to` for its recipients.
- Top button with the `-top` tag.
- funnel.py email-day prefix count + pro-join by tag.
