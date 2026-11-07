# "I bought it": final copy (EN / FR-QC, vous) — copywriter, Nov 7 night. Compliance (Nov 7): FIXED: money wording (claim -> ask), Sporting Life/JD exclusions in full, return-and-rebuy line cut, store's own deadline vs our watch window, "check today's price" step, unknown-policy email variant, "Some stores", nº. CASL: service email (s.6(6)), footer kept. Lawyer: "Fox Pro"/"The Gear Fox" names under Bill 96.

Placeholders: {braces} = filled from data. Unknown-policy watch length N = 14 days (growth's pick: the most common window among stores that publish one; Sporting Life, Decathlon, Foot Locker CA, BlackToe, Run Uphill, Fleet Feet = 14). Sporting Life is now CONFIRMED (14 days, excludes Black Friday/Cyber Monday/Boxing Day events). REI and MEC stay "policy unknown" until their own page text.
Angle: the store pays, not us. Every line: "you tell us, we watch, the store decides".

## A. Button + sheet
- Button: `✓ I bought it` / `✓ Je l'ai acheté`
- Sheet title: `Bought it? We'll watch the price.` / `Acheté? On surveille le prix pour vous.`
- Item line (prefilled): `{Brand Model} · {Colour} · Size {s} · {Store}` / `{Marque Modèle} · {Couleur} · Pointure {s} · {Boutique}` (Taille for clothing)
- Field: `Price you paid` / `Prix payé`; hint `Before tax, as on your receipt.` / `Avant taxes, comme sur votre reçu.`
- Field: `Date` / `Date d'achat`
- Store rule, one of:
  1. Store adjusts: `{Store} adjusts its own prices for {N} days after you buy. We'll watch until {date}.` / `{Boutique} ajuste ses propres prix pendant {N} jours après l'achat. On surveille jusqu'au {date}.` (e.g. Altitude Sports, 15 days)
     + always: ` Conditions apply: see its policy.` / ` Des conditions s'appliquent : voir sa politique.` ({N} and {date} = the store's real window, incl. special windows: Altitude Black Friday orders Nov 2-19 covered until Dec 7)
     + Sporting Life: ` Its policy excludes limited-time events (flash sales, Black Friday, Cyber Monday, Boxing Day, closeouts).` / ` Sa politique exclut les événements à durée limitée (ventes éclair, Vendredi fou, Cyberlundi, après-Noël, liquidations).`
     + JD Sports: ` Its policy excludes limited-time and special-event sales.` / ` Sa politique exclut les soldes à durée limitée et les événements spéciaux.`
  2. Store doesn't adjust sale prices (Running Room): `Running Room's price protection doesn't cover sale prices. We'll still tell you if it drops.` / `La protection de prix de Running Room exclut les prix soldés. On vous avertit quand même si le prix baisse.`
     Never adjusts (The Last Hunt, Arc'teryx, Sport Chek online): `{Store} doesn't adjust prices after you buy. We'll still tell you if it drops.` / `{Boutique} n'ajuste pas ses prix après l'achat. On vous avertit quand même si le prix baisse.`
  3. Policy unknown: `We couldn't find a written policy for {Store}. Ask them. We'll watch for 14 days.` / `Nous n'avons pas trouvé de politique écrite chez {Boutique}. Demandez-leur. On surveille pendant 14 jours.`
- Main button: `Watch it for me` / `Surveillez-le pour moi`
- Small line: `The store decides any adjustment (refund or store credit). We email you how to ask.` / `C'est la boutique qui décide d'un ajustement (remboursement ou crédit). On vous écrit comment le demander.`
- After saving: `Watching it. We'll email you if it drops by {date}.` / `C'est surveillé. On vous écrit si le prix baisse d'ici le {date}.`
- Errors: `Add the price you paid.` / `Indiquez le prix payé.` · `Pick the day you bought it.` / `Choisissez le jour de l'achat.`

## B. My account grid
- Header: `Watching after you buy · {n} items` / `Surveillé après l'achat · {n} articles`; when something dropped: `Dropped ${Z} since you bought` / `Baisse de {Z} $ depuis l'achat`
- Tile: `Paid ${p} · {Nov 15}` / `Payé {p} $ · {15 nov.}` · `Today ${t}` / `Aujourd'hui {t} $`
- Status pills: `Watching · {d} days left` / `Surveillé · {d} jours restants` (1: `1 day left` / `1 jour restant`) · `Dropped ${Z}: ask the store` / `Baisse de {Z} $ : demandez à la boutique` · `Window closed` / `Délai terminé` · `This store doesn't adjust prices` / `Cette boutique n'ajuste pas ses prix` · `No written policy: ask the store` / `Aucune politique écrite : demandez à la boutique`
- Empty: `Bought something at full price? Tap "I bought it" and we'll watch it for you.` / `Vous avez acheté quelque chose à plein prix? Touchez « Je l'ai acheté » et on le surveille pour vous.`

## C. Claim email
- Subject: `The {Altra Lone Peak 9} you bought dropped ${45}` / `Baisse de {45} $ sur votre {Altra Lone Peak 9}`; over 60 chars: `Your {Brand} dropped ${Z}: {d} days to ask`
- Preheader: `Paid $180 on Nov 15, $135 today at {Store}. {d} days left to ask.` / `Payé 180 $ le 15 nov., 135 $ aujourd'hui chez {Boutique}. Il reste {d} jours pour demander.`

EN body:
```
FOX PRO · PRICE DROP

Hi,

The {Altra Lone Peak 9} you bought is cheaper today.
Paid $180 on Nov 15 · Today $135 at {Store} ({colour}, size {s}).
{Store}'s policy gives you until {date} to ask ({d} days left).
[unknown policy instead: "We'll watch until {date}. {Store}'s own deadline isn't published: ask them."]

How to ask:
1. Check that today's price still shows on {Store}'s site.
2. Find your order number (in the store's confirmation email).
3. Contact {Store}: {contact}. You can copy this:
   "Hi, I bought the {item}, {colour}, size {s}, on {date} for ${p}. It's ${t} on your site today. Could you adjust the price? Order #____."
4. Add the link to today's price: {product link}

The store decides. Here's what its policy says:
"{store's own words}"
{policy link}
[unknown policy instead: "We couldn't find a written policy for {Store}, so ask them."]

[Contact {Store}]

Ask soon. Some stores only adjust while the lower price is still showing.
Anything look wrong? Just reply.

Bastien · The Gear Fox · thegearfox.com
```

FR body:
```
FOX PRO · BAISSE DE PRIX

Bonjour,

Votre {Altra Lone Peak 9} coûte moins cher aujourd'hui.
Payé 180 $ le 15 nov. · Aujourd'hui 135 $ chez {Boutique} ({couleur}, pointure {s}).
La politique de {Boutique} vous donne jusqu'au {date} pour demander ({d} jours restants).
[politique inconnue : « On surveille jusqu'au {date}. {Boutique} ne publie pas de délai : demandez-leur. »]

Comment demander :
1. Vérifiez que le prix d'aujourd'hui est encore affiché sur le site de {Boutique}.
2. Trouvez votre numéro de commande (dans le courriel de confirmation de la boutique).
3. Écrivez à {Boutique} : {contact}. Vous pouvez copier ceci :
   « Bonjour, j'ai acheté {article}, {couleur}, pointure {s}, le {date} à {p} $. Il est à {t} $ sur votre site aujourd'hui. Pourriez-vous ajuster le prix? Commande nº ____. »
4. Ajoutez le lien vers le prix d'aujourd'hui : {lien}

C'est la boutique qui décide. Voici ce que dit sa politique :
« {mots de la boutique} »
{lien politique}
[politique inconnue : « Nous n'avons pas trouvé de politique écrite chez {Boutique} : demandez-leur. »]

[Écrire à {Boutique}]

Faites vite : certaines boutiques n'ajustent que tant que le prix réduit est affiché.
Quelque chose cloche? Répondez simplement à ce courriel.

Bastien · The Gear Fox · thegearfox.com
```

Store that doesn't adjust (replaces "How to ask" + the copy message):
- EN: `{Store}'s policy says it doesn't adjust prices after you buy ("{its words}"). We'll still tell you if the price drops.`
- FR: `La politique de {Boutique} dit qu'elle n'ajuste pas les prix après l'achat (« {ses mots} »). On vous avertit quand même si le prix baisse.`
- Running Room: `excludes sale prices` / `exclut les prix soldés`

CASL footer:
- EN: `You're getting this because you asked Fox Pro to watch this purchase. The Gear Fox · {MAILING_ADDRESS} · hello@thegearfox.com · Stop watching this item · Unsubscribe`
- FR: `Vous recevez ce courriel parce que vous avez demandé à Fox Pro de surveiller cet achat. The Gear Fox · {MAILING_ADDRESS} · hello@thegearfox.com · Arrêter de surveiller cet article · Se désabonner`

No separate "window closed" email.
CASL: a service email Fox Pro members asked for (s.6(6) exempts it from consent, not from ID + unsubscribe): keep this footer and put NO promotion (Pro upsell, deals) in it, or it becomes a commercial message.
