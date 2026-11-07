# Fox Pro: welcome screen + 3 emails, final copy (EN / FR-QC, vous) — copywriter, Nov 7 night
Status: DRAFT. Compliance + designer check before the Nov 16 preview. Fills `docs/fox-pro-look.md` screens 2, 6, 7 (build_brief.py).
Placeholders: {braces} = filled from data. [N] / [BASTIEN] = not decided yet. Never fill a number by hand.
Formats: EN "Dec 2, 2027", "$36 CAD"; FR « 2 décembre 2027 », « 36 $ CA ». USA side: "US$36" / « 36 $ US ». Same numbers on both sides (terms §3).
Names: EN "Founding Fox #007"; FR « Renard fondateur nº 007 » (terms §2; the lawyer still has to check the "Fox Pro" name under Bill 96). Badge number = live text, 3 digits (badges/README.md). Non-founding members (spot 101+): drop the founding lines and use the Pro badge, "$45 CAD a year".
Lock word: FR uses « garanti » here. The terms draft says « bloqué ». Pick one and use it everywhere: I recommend « garanti » because « prix bloqué » reads like a blocked price.
Sign-off on every email: Bastien · The Gear Fox · thegearfox.com

---

## 1. Welcome after paying (screen 2)

Pill: `WELCOME` / `BIENVENUE`
Badge: founding-badge-base.png + live number `{001}`
Hero: `Founding Fox #{001}` / `Renard fondateur nº {001}`
Welcome: `Welcome to Fox Pro. Glad you're in the den.` / `Bienvenue dans Fox Pro. Content de vous compter parmi nous.`
Price line (forest + lock): `$36 CAD a year, locked while you stay. Renews {Dec 2, 2027}.` / `36 $ CA par année, garanti tant que vous restez. Renouvellement le {2 décembre 2027}.`
  USA: `US$36 a year, locked while you stay. Renews {Dec 2, 2027}.` / `36 $ US par année, garanti tant que vous restez. Renouvellement le {2 décembre 2027}.`
Receipt: `Your receipt is on its way to your inbox.` / `Votre reçu s'en vient par courriel.`
Rust button: `Watch the gear you want` / `Suivre l'équipement que vous voulez`
"I bought it" line: `Already bought something? Tap ✓ I bought it on its card and we'll watch the price for you.` / `Vous avez déjà acheté quelque chose? Touchez ✓ Je l'ai acheté sur sa fiche et on surveille le prix pour vous.`
Small link: `Go to My account` / `Aller à Mon compte`
Refund (small, grey): `Changed your mind? Full refund until {Jan 1, 2027}, in My account.` / `Vous changez d'idée? Remboursement complet jusqu'au {1er janvier 2027}, dans Mon compte.`

---

## 2. Morning price-drop alert (Pro, screen 6)
CASL: a service email the member asked for. No promotion in it (no Pro upsell, no unwatched deals).

Subject (main): `Dropped this morning: {Hoka Mach 6}, ${50} off in your size` / `Ce matin : {Hoka Mach 6}, {50} $ de moins dans votre pointure`
Subject over 60 characters: `Your {Hoka Mach 6} dropped ${50} this morning` / `Votre {Hoka Mach 6} a baissé de {50} $ ce matin`
2+ items: add ` + {2} more` / ` + {2} autres` only if it still fits under 60.
Clothing: "size" / « taille » (not « pointure »).
Preheader: `Now ${119} at {Running Free}, size {11} in stock. Checked at {7:17am}.` / `Maintenant {119} $ chez {Running Free}, pointure {11} en stock. Vérifié à {7 h 17}.`

Time rule: {time} = when we checked (4:17am Vancouver), shown in the member's own time zone (profile tz): EN "4:17am", FR « 4 h 17 ». Never "4:17am" for someone in Montréal.

EN body:
```
FOX PRO · THIS MORNING

Hi,

Something you're watching dropped overnight.

{Hoka Mach 6} · {Men's}
Now ${119} · was ${169}
Size {11} in stock at {Running Free}

[See it at the store]

Also dropped on your watchlist:
{Saucony Endorphin Speed 4} · ${139} · {Sporting Life}
{Arc'teryx Norvan Shell} · ${210} · {Altitude Sports}
[no other drops: leave this block out]

Checked at {4:17am}. Prices change: check before you buy.

Bastien · The Gear Fox · thegearfox.com
```

FR body:
```
FOX PRO · CE MATIN

Bonjour,

Un article que vous suivez a baissé pendant la nuit.

{Hoka Mach 6} · {Homme}
Maintenant {119} $ · avant {169} $
Pointure {11} en stock chez {Running Free}

[Voir chez le marchand]

Aussi en baisse dans votre liste :
{Saucony Endorphin Speed 4} · {139} $ · {Sporting Life}
{Arc'teryx Norvan Shell} · {210} $ · {Altitude Sports}
[aucune autre baisse : retirer ce bloc]

Vérifié à {4 h 17}. Les prix changent : vérifiez avant d'acheter.

Bastien · The Gear Fox · thegearfox.com
```

Footer:
- EN: `You're getting this because you asked Fox Pro for morning alerts on your watchlist. The Gear Fox · {MAILING_ADDRESS} · hello@thegearfox.com · Stop morning alerts · Unsubscribe`
- FR: `Vous recevez ce courriel parce que vous avez demandé à Fox Pro des alertes du matin sur votre liste de suivi. The Gear Fox · {MAILING_ADDRESS} · hello@thegearfox.com · Arrêter les alertes du matin · Se désabonner`
("Stop morning alerts" only turns off this email. The Friday email keeps carrying watchlist news.)

---

## 3. Renewal reminder, 45 days before (screen 7)
Legal notice (terms §4). The date, the amount and the currency come first. "Keep Fox Pro" and "Manage or cancel" get the same size and the same style: two outlined forest buttons side by side, no rust, because neither action should be pushed. No guilt wording, no "you'll lose…".

Subject: `Fox Pro renews on {Dec 2} for ${36} CAD` / `Fox Pro se renouvelle le {2 déc.} pour {36} $ CA`
Preheader: `Nothing to do if you're staying. Cancel online anytime before then.` / `Rien à faire si vous restez. Annulez en ligne en tout temps d'ici là.`

EN body:
```
FOX PRO · RENEWAL

Hi,

Fox Pro renews on {December 2, 2027}.
Amount: ${36.00} CAD, for one year. No tax added.
Card: {Visa} ending in {4242}.

Founding price locked: you keep $36 while you stay. (Founding Fox #{007})

{WATCHED BLOCK, see rule}

Staying? Nothing to do.
Not sure? Cancel online in a few taps. You keep Pro until {December 2, 2027} and we won't charge you again.

[Keep Fox Pro]   [Manage or cancel]

{[BASTIEN] only if the 30 days also cover renewals: "Renewed and changed your mind? Full refund within 30 days of the charge."}
Questions? Just reply. I read every one.

Bastien · The Gear Fox · thegearfox.com
```

FR body:
```
FOX PRO · RENOUVELLEMENT

Bonjour,

Fox Pro se renouvelle le {2 décembre 2027}.
Montant : {36,00} $ CA, pour une année. Aucune taxe ajoutée.
Carte : {Visa} se terminant par {4242}.

Prix fondateur garanti : vous gardez 36 $ tant que vous restez. (Renard fondateur nº {007})

{BLOC SURVEILLANCE, voir la règle}

Vous restez? Rien à faire.
Vous hésitez? Annulez en ligne en quelques touches. Vous gardez Pro jusqu'au {2 décembre 2027} et on ne vous facture plus rien.

[Garder Fox Pro]   [Gérer ou annuler]

{[BASTIEN] seulement si les 30 jours couvrent aussi les renouvellements : « Renouvelé et vous changez d'idée? Remboursement complet dans les 30 jours suivant le paiement. »}
Des questions? Répondez simplement. Je lis tout.

Bastien · The Gear Fox · thegearfox.com
```

WATCHED BLOCK rule (real data only):
- Count each item from our own records for this member over their paid year: purchases watched (I bought it), drops found on those purchases, morning alerts sent.
- Only show lines with a count of 1 or more. All zero = leave the whole block out (no "we were ready for you" filler).
- Never show dollar totals as money earned. "Drops you could ask about" is fine; "you saved $X" is not, because the store decides.
- EN lines: `This year Fox Pro:` · `watched {4} purchases after you bought` · `found {2} drops you could ask the store about` · `sent {23} morning alerts`
- FR lines: `Cette année, Fox Pro a :` · `surveillé {4} achats après l'achat` · `trouvé {2} baisses à demander à la boutique` · `envoyé {23} alertes du matin`
- Use the singular for 1: "1 purchase", "1 drop", "1 morning alert" / « 1 achat », « 1 baisse », « 1 alerte du matin ».

USA: `US$36.00` / `36,00 $ US`. Non-founding members: no lock line, "$45".
Footer (account notice, no promotion):
- EN: `You're getting this because you're a Fox Pro member and we tell you 45 days before every renewal. The Gear Fox · {MAILING_ADDRESS} · hello@thegearfox.com · Fox Pro terms`
- FR: `Vous recevez ce courriel parce que vous êtes membre Fox Pro et qu'on vous avertit 45 jours avant chaque renouvellement. The Gear Fox · {MAILING_ADDRESS} · hello@thegearfox.com · Conditions de Fox Pro`
(No unsubscribe link: the notice is required while the membership is active. Compliance to confirm.)

---

## 4. Receipt (after any payment)
Transactional. It doubles as "your copy" of the terms (terms §16).

Subject: `Your Fox Pro receipt: ${36} CAD` / `Votre reçu Fox Pro : {36} $ CA`
Preheader: `Founding Fox #{007}. Paid {Dec 2, 2026}. Renews {Dec 2, 2027}.` / `Renard fondateur nº {007}. Payé le {2 déc. 2026}. Renouvellement le {2 déc. 2027}.`

EN body:
```
FOX PRO · RECEIPT

Hi,

Thanks for joining. Here's your receipt.

Fox Pro, 1 year · Founding Fox #{007}
Amount: ${36.00} CAD
No tax added. That's the total.
Paid: {December 2, 2026}
Card: {Visa} ending in {4242}
Receipt nº {GF-2026-0007}
Renews: {December 2, 2027} at ${36} CAD. We'll email you 45 days before.

Full refund of the Fox Pro fee until {January 1, 2027} (30 days). Tap "Refund me" in My account or reply to this email. No reason needed.
Cancel online anytime in My account.

[Read your Fox Pro terms]

Bastien · The Gear Fox · thegearfox.com
```

FR body:
```
FOX PRO · REÇU

Bonjour,

Merci de vous joindre à nous. Voici votre reçu.

Fox Pro, 1 an · Renard fondateur nº {007}
Montant : {36,00} $ CA
Aucune taxe ajoutée. C'est le total.
Payé le : {2 décembre 2026}
Carte : {Visa} se terminant par {4242}
Reçu nº {GF-2026-0007}
Renouvellement : {2 décembre 2027} à {36} $ CA. On vous écrit 45 jours avant.

Remboursement complet des frais Fox Pro jusqu'au {1er janvier 2027} (30 jours). Touchez « Me rembourser » dans Mon compte ou répondez à ce courriel. Pas besoin de raison.
Annulez en ligne en tout temps dans Mon compte.

[Lire vos conditions Fox Pro]

Bastien · The Gear Fox · thegearfox.com
```

Renewal receipt: same, with the subject `Your Fox Pro renewal receipt: ${36} CAD` / `Votre reçu de renouvellement Fox Pro : {36} $ CA`. The refund line shows only if [BASTIEN] says yes to refunds after renewals.
Refund date = payment date + 30 days, per member (compliance Nov 6).
Footer: `The Gear Fox · {legal name [LAWYER]} · {MAILING_ADDRESS} · hello@thegearfox.com` (same in FR). Terms link = [final terms URL].

Open: [BASTIEN] refunds after renewals; [LAWYER] legal name, phone line, whether the renewal notice can skip unsubscribe; « garanti » vs « bloqué ».
