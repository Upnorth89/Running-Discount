#!/usr/bin/env python3
"""One page per popular shoe model, for Google: "Saucony Endorphin Speed 5 on sale in Canada".

Each page lists every size in stock with the best price, the store (linked straight to that size) and the % off,
in English (/shoes/<slug>/) and French (/chaussures/<slug>/). Rebuilt every morning from deals.json, after the
price history step (so "lowest price we've seen" can show; good news only, never "it was cheaper before").

A model gets a page once 3+ stores that ship from Canada carry it. Pages never disappear: a model that drops out
keeps its page (listed in shoes/pages.json, fetched from the live site each run) with "not in stock right now",
so Google never finds a dead link.

Also writes shoes/index.html + chaussures/index.html (all models by brand) and sitemap.xml.

Usage: python scraper/shoe_pages.py SITE_DIR
"""
import html
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse, quote

BASE = "https://thegearfox.com"
MIN_STORES = 3          # Canadian stores carrying the model before it gets a page
HISTORY_DAYS = 30       # days of price history before "lowest price we've seen" can show

T = {
    "en": {
        "dir": "shoes", "lang": "en-CA", "other": "fr",
        "title": "{name} price in Canada: every size, every store",
        "titleSale": "{name} Sale Canada: from {price} (−{p}%)",
        "aboutH": "About this shoe", "faqH": "Quick answers",
        "pwLow": "Today's price is the lowest we've seen in {n} days: {today}.", "pwWas": "It was {low} on {date} ({now} today). Sales come back: don't miss the next one.", "pwBtn": "Email me when it drops",
        "about": "The {name} is a {type}. Today {stores} stores in Canada carry it and we found {sizes} sizes in stock.",
        "aboutBest": " The lowest price is {price} at {store} ({bsizes}).", "aboutMost": " {store} is the cheapest in the most sizes ({n}).",
        "qSale": "Is the {name} on sale in Canada right now?",
        "aSaleYesG": "Yes. {lines} Prices are checked every morning.",
        "aSaleG": "{g}: from {price} ({p}% off) at {store}, in {bsizes}.", "aSaleGNo": "{g}: not on sale today, from {price}.",
        "aSaleYes": "Yes. Today it's up to {p}% off: {price} at {store} in {bsizes}, and {n} sizes on sale in all. Prices are checked every morning.",
        "aSaleNo": "Not today. It's in stock at full price from {price}. Tap \u201cWatch the price\u201d and we'll email you when it drops.",
        "qSizes": "Which sizes are in stock?", "qWhere": "Where is the {name} cheapest in Canada?",
        "aWhere": "{store}, at {price} today ({bsizes}). Each size can be cheapest at a different store: the tables above show the best one for every size.",
        "typeLower": {"daily": "road running shoe", "race": "racing shoe", "trail": "trail running shoe", "hike": "hiking shoe", "": "running shoe"},
        "hubs": {"all": ("Running shoes on sale in Canada", "Running shoes on sale in Canada today", "Every popular running shoe on sale today at Canadian stores, sorted by the biggest discount. Checked every morning."),
                 "road": ("Road running shoes on sale in Canada", "Road running shoes on sale", "Daily trainers and road shoes on sale today at Canadian stores, biggest discount first."),
                 "trail": ("Trail running shoes on sale in Canada", "Trail running shoes on sale", "Trail running shoes on sale today at Canadian stores, biggest discount first."),
                 "racing": ("Carbon racing shoes on sale in Canada", "Racing shoes on sale", "Carbon-plated and racing shoes on sale today at Canadian stores, biggest discount first."),
                 "women": ("Women's running shoes on sale in Canada", "Women's running shoes on sale", "Women's running shoes on sale today at Canadian stores, biggest discount first."),
                 "men": ("Men's running shoes on sale in Canada", "Men's running shoes on sale", "Men's running shoes on sale today at Canadian stores, biggest discount first.")},
        "hubDir": "running-shoes-sale", "hubSlugs": {"all": "", "road": "road", "trail": "trail", "racing": "racing", "women": "women", "men": "men"},
        "sizeDir": "size", "gWord": {"men": "Men's", "women": "Women's"}, "gLab": {"men": "Men's", "women": "Women's"},
        "sizeTitle": "{g} Size {s} Running Shoes on Sale in Canada: {n} deals today",
        "sizeH1": "{g} running shoes on sale in size {s}",
        "sizeIntro": "{n} running shoes on sale today in {g} size {s} at Canadian stores. Every price is the price in size {s}, biggest discount first. Checked every morning.",
        "sizeAt": "at {store}", "sizeNav": "Other sizes", "sizeOther": "{g} sizes",
        "brandDir": "brands", "brandTitle": "{brand} Sale Canada: {n} running shoes on sale, up to {p}% off", "brandH1": "{brand} on sale in Canada",
        "brandIntro": "Every {brand} running shoe we track at Canadian stores, with today's best price. Biggest discount first; checked every morning.",
        "browse": "Browse", "brandsH": "Brands", "bfLink": "Black Friday",
        "sizesStores": "{sizes} sizes · {stores} stores", "fullPrice": "full price",
        "bfDir": "black-friday", "bfTitle": "Black Friday 2026 running shoe deals in Canada",
        "bfH1": "Black Friday 2026: running deals in Canada",
        "bfIntro": "Black Friday is Friday, November 27. We check 60+ Canadian running and outdoor stores every morning and show only what's in stock. Here are today's biggest running shoe deals; on Black Friday this page fills with that week's best.",
        "bfTitlePre": "Black Friday 2026 running shoe deals in Canada: what to expect",
        "bfH1Pre": "Black Friday 2026 in Canada: November {date}",
        "bfIntroPre": "{days} days to go. Black Friday deals aren't out yet. During Black Friday week this page shows the real deals from 60+ Canadian running stores, checked every morning.",
        "bfOther": ("In the US?", "See Black Friday deals at US stores →", "/us/black-friday/"),   # Oct 10: both sides link each other
        # Boxing Day (Oct 21; asked by a Reddit user Oct 4, backlog: live by early November so search engines know it before Dec 26)
        "bdDir": "boxing-day", "bdLink": "Boxing Day",
        "bdTitle": "Boxing Day {y} running shoe deals in Canada", "bdH1": "Boxing Day {y}: running deals in Canada",
        "bdIntro": "Boxing Day is {day}, December 26. We check 60+ Canadian running and outdoor stores every morning and show only what's in stock. Here are today's biggest running shoe deals in sizes people wear.",
        "bdTitlePre": "Boxing Day {y} running shoe deals in Canada: what to expect", "bdH1Pre": "Boxing Day {y} in Canada: {day}, December 26",
        "bdIntroPre": "{days} days to go. From December 19, this page shows the real Boxing Day deals from 60+ Canadian running stores, checked every morning. Until then: how to get ready, and today's best deals.",
        "bdSpotH": "How to get the most out of Boxing Day",
        "bdSpot": ["Pick your sizes now, so on Boxing Day you only see what's left in your size.",
                   "Watch the shoes you want: we email you when one drops in your size, so you don't have to check every store.",
                   "Check the return policy: some sale items are final sale. We label them."],
        "bdTodayH": "Not Boxing Day yet: today's best running shoe deals ({date})", "bdCta": "Get the Boxing Day deals in your size",
        "bdOther": ("Before that:", "Black Friday running deals →", "/black-friday/"),
        "bfLive": ("Is it a real deal?", "Today's Black Friday deal check: real drops, old “sales”, recent price rises →", "/black-friday/live/"),
        "bfGift": ("Shopping for someone else?", "Gifts for runners under $25, $50 and $100, no size needed →", "/gifts-for-runners/"),
        "bfTrackH": "We're tracking real prices before Black Friday",
        "bfTrackTxt": "Since October 2 we record the price of every running product we follow, every day: {n} products so far. So on Black Friday we'll know which deals are real and which prices went up in November just to come back down.",
        "bfDataH": "What our price data shows today ({date})",
        "bfData": ["{pct}% of running shoe models at Canadian stores are on sale right now ({on} of {shoes}, at {shops} stores).",
                   "Your size is the catch: a women's size 8 can buy only {w8}% of those sale shoes, a men's size 9 only {m9}%.",
                   "{same}% of the shoes on sale today were already at that price or lower two weeks ago ({back}). A \"sale\" is often not new.",
                   "Brands with the most models on sale: {most}. The fewest: {least}."],
        "bfSpotH": "How to spot a real Black Friday deal",
        "bfSpot": ["Compare with the price of the last few weeks, not the \"was\" price on the tag.",
                   "Check your size: a big discount often only covers sizes nobody wears.",
                   "Look at the return policy: many sale items are final sale. We label them."],
        "bfTodayH": "Not Black Friday yet: today's best running shoe deals ({date})",
        "bfCta": "Get the Black Friday deals in your size", "bfCtaTxt": "Pick your sizes once. Our Friday email lands on Black Friday morning with the best deals in your sizes, and price-drop alerts for the shoes you watch.",
        "homeH": "Today's best running shoe deals in Canada", "homeMore": "All shoe prices by model",
        "h1sub": "On sale in Canada: every size, every store",
        "desc": "{name}: today's best price in every size at {n} Canadian running stores{off}. Checked every morning by The Gear Fox.",
        "descOff": ", up to {p}% off",
        "from": "From <b>{price}</b> <s>{reg}</s> ({p}% off)",
        "fromFull": "From <b>{price}</b>",
        "facts": "{sizes} sizes in stock · {stores} stores · checked {date}",
        "none": "Not in stock at the stores we check right now. Prices change every day: we'll show it here as soon as it's back.",
        "low": "Lowest price we've seen in {d} days",
        "bfReal": "{n} of these {t} deals are at their lowest price in 30+ days of our own price checks: real drops, not a price raised first. They're listed first.",
        "size": "Size", "price": "Price", "store": "Store", "was": "was",
        "men": "Men's", "women": "Women's", "unisex": "Unisex (men's sizes)", "unisexMW": "Unisex (men's and women's sizes)", "wide": "wide",
        "us": "ships from the US", "final": "Final sale",
        "cta": "Get it in your size", "ctaTxt": "Pick your sizes once. Every Friday we email the best deals in them, and you can get a price-drop alert on this shoe.",
        "ctaBtn": "See deals in my size",
        # Oct 11 (Bastien: "optimize to have retention, not just a pathway to another website"): sign up where people are
        "backH": "Didn't buy it?", "backTxt": "We'll email you when the {name} drops in your size. Free, unsubscribe in one tap.",
        "backBtn": "Email me", "backNo": "No thanks",
        "qsHub": "Get the best deals in your size, every Friday", "qsTxt": "Free. One email on Friday mornings with the deals in your size. Unsubscribe in one tap.",
        "qsMen": "Men's", "qsWomen": "Women's", "qsSize": "Shoe size", "qsBtn": "Send me the deals", "qsPick": "Pick your shoe size first.",
        "qsMore": "Or pick all your sizes on the site →",
        "more": "More {brand} shoes", "all": "All shoe models",
        "altH": {"daily": "Other road shoes on sale in your size", "race": "Other race shoes on sale in your size",
                 "trail": "Other trail shoes on sale in your size", "hike": "Other hiking & winter shoes on sale in your size"},
        "altH0": {"daily": "Other road shoes on sale today", "race": "Other race shoes on sale today",
                  "trail": "Other trail shoes on sale today", "hike": "Other hiking & winter shoes on sale today"},
        "altIn": "in size {s}", "altN": "{n} sizes on sale",
        "types": {"daily": "Road running shoe", "race": "Racing shoe (plated)", "trail": "Trail running shoe", "hike": "Hiking & winter shoe"},
        "idxTitle": "Running shoe prices by model in Canada",
        "idxH1": "Shoe prices by model",
        "idxIntro": "Every popular running shoe we track, with today's best price in each size at Canadian stores. Updated every morning.",
        "idxDesc": "Today's best price in every size for {n} running shoe models at Canadian stores. Updated every morning by The Gear Fox.",
        "onSale": "on sale", "home": "The Gear Fox", "switch": "Français", "menu": "Menu", "mDeals": "Today's deals", "mShoes": "Shoe prices by model", "mWatch": "Your watchlist", "mSizes": "My sizes", "mAbout": "About The Gear Fox", "mRaces": "Race gear lists", "tagline": "OUTFOX FULL PRICE",
        "hdrSearch": "Search deals", "hdrSearchPh": "Shoes, brands, gear", "hdrSearchGo": "Search",
        "yourSize": "Your size", "at": "at", "see": "See it", "watch": "Watch the price", "alertH": "Email me when the {name} drops in my size",
        "alertTxt": "Free. One email when the price falls in your size, plus the Friday deals. Unsubscribe in one tap.", "alertBtn": "Email me",
        "boH": "Email me when the {name} is back in my size", "boTxt": "Free. One email when a store we check has it in your size, plus the Friday deals. Unsubscribe in one tap.",
        "boFit": "Fit", "boMen": "Men's", "boWomen": "Women's", "boSize": "Size", "boPick": "Pick your fit and size first.",
        "alertPick": "Pick your size above first, so we watch the right one.", "alertBad": "That email doesn't look right.",
        "alertOk": "Almost done: check your inbox for {email} and tap the link to confirm (look in Junk too).", "alertFail": "Couldn't sign you up right now. Try again in a minute.",
        "alertDone": "You're watching this shoe. We'll email you when it drops in your size.", "emailPh": "you@example.com", "pick": "Your size:", "pickPh": "Pick your size", "change": "Change", "allInSize": "See every deal in your size →",
        "notInSize": "Not in stock in your size right now. Watch it and we'll email you when it's back or drops.",
        "find": "Search a model (e.g. Clifton)", "noMatch": "No model matches. Try the brand name, or a shorter word.",
        "foot": "The Gear Fox · Outfox full price · Prices change often: the store's price at checkout is the one that counts.",
        "privacy": "Privacy",
        "months": ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."],
        "date": lambda d, m: f"{m} {d}",
        "money": lambda v: f"${v:,.2f}",
    },
    "fr": {
        "dir": "chaussures", "lang": "fr-CA", "other": "en",
        "title": "{name} : prix au Canada, chaque pointure, chaque boutique",
        "titleSale": "{name} en solde au Canada : dès {price} (−{p} %)",
        "aboutH": "À propos de cette chaussure", "faqH": "Réponses rapides",
        "pwLow": "Le prix d'aujourd'hui est le plus bas des {n} derniers jours : {today}.", "pwWas": "Elle était à {low} le {date} ({now} aujourd'hui). Les soldes reviennent : ne manquez pas la prochaine.", "pwBtn": "M'avertir quand il baisse",
        "about": "La {name} est une {type}. Aujourd'hui, {stores} boutiques au Canada la vendent et nous avons trouvé {sizes} pointures en stock.",
        "aboutBest": " Le prix le plus bas est {price} chez {store} ({bsizes}).", "aboutMost": " {store} est la moins chère dans le plus de pointures ({n}).",
        "qSale": "La {name} est-elle en solde au Canada en ce moment?",
        "aSaleYesG": "Oui. {lines} Les prix sont vérifiés chaque matin.",
        "aSaleG": "{g} : à {price} ({p} % de rabais) chez {store}, en {bsizes}.", "aSaleGNo": "{g} : pas en solde aujourd'hui, à {price}.",
        "aSaleYes": "Oui. Aujourd'hui, jusqu'à {p} % de rabais : {price} chez {store} en {bsizes}, et {n} pointures en solde en tout. Les prix sont vérifiés chaque matin.",
        "aSaleNo": "Pas aujourd'hui. Elle est en stock au prix régulier dès {price}. Touchez « Suivre le prix » et on vous écrira dès qu'elle baisse.",
        "qSizes": "Quelles pointures sont en stock?", "qWhere": "Où la {name} est-elle la moins chère au Canada?",
        "aWhere": "Chez {store}, à {price} aujourd'hui ({bsizes}). Chaque pointure peut être moins chère ailleurs : les tableaux ci-dessus montrent la meilleure boutique pour chacune.",
        "typeLower": {"daily": "chaussure de course sur route", "race": "chaussure de compétition", "trail": "chaussure de course en sentier", "hike": "chaussure de randonnée", "": "chaussure de course"},
        "hubs": {"all": ("Chaussures de course en solde au Canada", "Chaussures de course en solde aujourd'hui", "Toutes les chaussures de course populaires en solde aujourd'hui dans les boutiques canadiennes, du plus gros rabais au plus petit. Vérifié chaque matin."),
                 "road": ("Chaussures de course sur route en solde au Canada", "Chaussures de route en solde", "Chaussures d'entraînement et de route en solde aujourd'hui au Canada, plus gros rabais en premier."),
                 "trail": ("Chaussures de course en sentier en solde au Canada", "Chaussures de sentier en solde", "Chaussures de course en sentier en solde aujourd'hui au Canada, plus gros rabais en premier."),
                 "racing": ("Chaussures de compétition en solde au Canada", "Chaussures de compétition en solde", "Chaussures à plaque de carbone et de compétition en solde aujourd'hui au Canada, plus gros rabais en premier."),
                 "women": ("Chaussures de course pour femme en solde au Canada", "Chaussures de course pour femme en solde", "Chaussures de course pour femme en solde aujourd'hui au Canada, plus gros rabais en premier."),
                 "men": ("Chaussures de course pour homme en solde au Canada", "Chaussures de course pour homme en solde", "Chaussures de course pour homme en solde aujourd'hui au Canada, plus gros rabais en premier.")},
        "hubDir": "chaussures-course-solde", "hubSlugs": {"all": "", "road": "route", "trail": "sentier", "racing": "competition", "women": "femme", "men": "homme"},
        "sizeDir": "pointure", "gWord": {"men": "pour hommes", "women": "pour femmes"}, "gLab": {"men": "Hommes", "women": "Femmes"},
        "sizeTitle": "Chaussures de course {g} pointure {s} en solde au Canada : {n} aubaines aujourd'hui",
        "sizeH1": "Chaussures de course {g} en solde, pointure {s}",
        "sizeIntro": "{n} chaussures de course {g} en solde aujourd'hui en pointure {s} dans les boutiques canadiennes. Chaque prix est celui de la pointure {s}, du plus gros rabais au plus petit. Vérifié chaque matin.",
        "sizeAt": "chez {store}", "sizeNav": "Autres pointures", "sizeOther": "Pointures {g}",
        "brandDir": "marques", "brandTitle": "{brand} en solde au Canada : {n} chaussures de course, jusqu'à {p} % de rabais", "brandH1": "{brand} en solde au Canada",
        "brandIntro": "Toutes les chaussures de course {brand} que nous suivons dans les boutiques canadiennes, avec le meilleur prix du jour. Plus gros rabais en premier; vérifié chaque matin.",
        "browse": "Parcourir", "brandsH": "Marques", "bfLink": "Vendredi fou",
        "sizesStores": "{sizes} pointures · {stores} boutiques", "fullPrice": "prix régulier",
        "bfDir": "vendredi-fou", "bfTitle": "Vendredi fou 2026 : aubaines de chaussures de course au Canada",
        "bfH1": "Vendredi fou 2026 : aubaines course au Canada",
        "bfIntro": "Le Vendredi fou (Black Friday) tombe le vendredi 27 novembre. Nous vérifions plus de 60 boutiques canadiennes de course et de plein air chaque matin et montrons seulement ce qui est en stock. Voici les plus gros rabais du jour; le Vendredi fou, cette page affichera les meilleures aubaines de la semaine.",
        "bfTitlePre": "Vendredi fou 2026 : aubaines de chaussures de course au Canada, à quoi s'attendre",
        "bfH1Pre": "Vendredi fou 2026 au Canada : le {date} novembre",
        "bfIntroPre": "Encore {days} jours. Les aubaines du Vendredi fou ne sont pas encore là. Pendant la semaine du Vendredi fou, cette page montre les vraies aubaines de plus de 60 boutiques de course canadiennes, vérifiées chaque matin.",
        "bfOther": ("Aux États-Unis ?", "Voir les aubaines du Black Friday dans les boutiques américaines →", "/us/black-friday/"),
        "bdDir": "soldes-apres-noel", "bdLink": "Boxing Day",
        "bdTitle": "Boxing Day {y} : soldes d'après-Noël en chaussures de course au Canada", "bdH1": "Boxing Day {y} : aubaines course au Canada",
        "bdIntro": "Le Boxing Day tombe le {day} 26 décembre. Nous vérifions plus de 60 boutiques canadiennes de course et de plein air chaque matin et montrons seulement ce qui est en stock. Voici les plus gros rabais du jour dans les pointures courantes.",
        "bdTitlePre": "Boxing Day {y} : soldes d'après-Noël en chaussures de course au Canada, à quoi s'attendre", "bdH1Pre": "Boxing Day {y} au Canada : le {day} 26 décembre",
        "bdIntroPre": "Encore {days} jours. À partir du 19 décembre, cette page montre les vraies aubaines du Boxing Day de plus de 60 boutiques de course canadiennes, vérifiées chaque matin. D'ici là : comment vous préparer, et les meilleures aubaines du jour.",
        "bdSpotH": "Comment profiter au maximum du Boxing Day",
        "bdSpot": ["Choisissez vos tailles dès maintenant : au Boxing Day, vous ne verrez que ce qui reste dans votre taille.",
                   "Suivez les chaussures que vous voulez : on vous écrit quand l'une baisse dans votre pointure, pas besoin de vérifier chaque boutique.",
                   "Vérifiez la politique de retour : certains articles en solde sont en vente finale. On les indique."],
        "bdTodayH": "Pas encore le Boxing Day : les meilleures aubaines du jour ({date})", "bdCta": "Recevez les aubaines du Boxing Day dans votre pointure",
        "bdOther": ("Avant ça :", "Les aubaines course du Vendredi fou →", "/vendredi-fou/"),
        "bfLive": ("Vraie aubaine ou pas ?", "La vérification du jour : vraies baisses, vieux « soldes », hausses récentes →", "/vendredi-fou/direct/"),
        "bfGift": ("Un cadeau à faire ?", "Cadeaux pour coureurs à moins de 25 $, 50 $ et 100 $, sans souci de taille →", "/cadeaux-coureurs/"),
        "bfTrackH": "On suit les vrais prix avant le Vendredi fou",
        "bfTrackTxt": "Depuis le 2 octobre, on note chaque jour le prix de chaque article de course qu'on suit : {n} articles jusqu'ici. Au Vendredi fou, on saura quelles aubaines sont vraies et quels prix ont monté en novembre pour mieux redescendre.",
        "bfDataH": "Ce que nos relevés de prix montrent aujourd'hui ({date})",
        "bfData": ["{pct} % des modèles de chaussures de course dans les boutiques canadiennes sont en solde en ce moment ({on} sur {shoes}, dans {shops} boutiques).",
                   "La pointure change tout : une femme qui chausse du 8 n'a accès qu'à {w8} % de ces soldes, un homme en 9, à {m9} %.",
                   "{same} % des chaussures en solde aujourd'hui étaient déjà à ce prix, ou moins, il y a deux semaines ({back}). Un « solde » n'est souvent pas nouveau.",
                   "Marques avec le plus de modèles en solde : {most}. Le moins : {least}."],
        "bfSpotH": "Comment reconnaître une vraie aubaine du Vendredi fou",
        "bfSpot": ["Comparez avec le prix des dernières semaines, pas avec le prix « avant » de l'étiquette.",
                   "Vérifiez votre pointure : un gros rabais ne couvre souvent que des tailles que personne ne porte.",
                   "Regardez la politique de retour : plusieurs articles en solde sont en vente finale. On les indique."],
        "bfTodayH": "Pas encore le Vendredi fou : les meilleures aubaines du jour ({date})",
        "bfCta": "Recevez les aubaines du Vendredi fou dans votre pointure", "bfCtaTxt": "Choisissez vos tailles une fois. Notre courriel du vendredi arrive le matin du Vendredi fou avec les meilleures aubaines dans vos tailles, et des alertes de baisse de prix pour les chaussures que vous suivez.",
        "homeH": "Meilleures aubaines de chaussures de course au Canada aujourd'hui", "homeMore": "Tous les prix par modèle",
        "h1sub": "En solde au Canada : chaque pointure, chaque boutique",
        "desc": "{name} : le meilleur prix du jour dans chaque pointure dans {n} boutiques de course canadiennes{off}. Vérifié chaque matin par The Gear Fox.",
        "descOff": ", jusqu'à {p} % de rabais",
        "from": "À partir de <b>{price}</b> <s>{reg}</s> ({p} % de rabais)",
        "fromFull": "À partir de <b>{price}</b>",
        "facts": "{sizes} pointures en stock · {stores} boutiques · vérifié le {date}",
        "none": "Pas en stock dans les boutiques que nous suivons en ce moment. Les prix changent chaque jour : on l'affichera ici dès son retour.",
        "low": "Le plus bas prix vu en {d} jours",
        "bfReal": "{n} de ces {t} aubaines sont à leur plus bas prix en 30 jours ou plus selon nos relevés quotidiens : de vraies baisses, pas un prix gonflé avant. Elles sont en premier.",
        "size": "Pointure", "price": "Prix", "store": "Boutique", "was": "avant",
        "men": "Homme", "women": "Femme", "unisex": "Unisexe (pointures homme)", "unisexMW": "Unisexe (pointures homme et femme)", "wide": "large",
        "us": "expédié des États-Unis", "final": "Vente finale",
        "cta": "Trouvez-la dans votre pointure", "ctaTxt": "Choisissez vos tailles une fois. Chaque vendredi, on vous envoie les meilleures aubaines dans vos tailles, et vous pouvez suivre le prix de cette chaussure.",
        "ctaBtn": "Voir les aubaines à ma taille",
        "backH": "Pas acheté ?", "backTxt": "On vous écrit quand {name} baisse dans votre pointure. Gratuit, désabonnement en un clic.",
        "backBtn": "M'avertir", "backNo": "Non merci",
        "qsHub": "Les meilleures aubaines dans votre pointure, chaque vendredi", "qsTxt": "Gratuit. Un courriel le vendredi matin avec les aubaines dans votre pointure. Désabonnement en un clic.",
        "qsMen": "Homme", "qsWomen": "Femme", "qsSize": "Pointure", "qsBtn": "Envoyez-moi les aubaines", "qsPick": "Choisissez d'abord votre pointure.",
        "qsMore": "Ou choisissez toutes vos tailles sur le site →",
        "more": "Autres chaussures {brand}", "all": "Tous les modèles",
        "altH": {"daily": "Autres chaussures de route en solde dans votre pointure", "race": "Autres chaussures de compétition en solde dans votre pointure",
                 "trail": "Autres chaussures de sentier en solde dans votre pointure", "hike": "Autres chaussures de randonnée et d'hiver en solde dans votre pointure"},
        "altH0": {"daily": "Autres chaussures de route en solde aujourd'hui", "race": "Autres chaussures de compétition en solde aujourd'hui",
                  "trail": "Autres chaussures de sentier en solde aujourd'hui", "hike": "Autres chaussures de randonnée et d'hiver en solde aujourd'hui"},
        "altIn": "en pointure {s}", "altN": "{n} pointures en solde",
        "types": {"daily": "Chaussure de course sur route", "race": "Chaussure de compétition (plaque)", "trail": "Chaussure de course en sentier", "hike": "Chaussure de randonnée et d'hiver"},
        "idxTitle": "Prix des chaussures de course par modèle au Canada",
        "idxH1": "Prix par modèle",
        "idxIntro": "Toutes les chaussures de course populaires que nous suivons, avec le meilleur prix du jour dans chaque pointure dans les boutiques canadiennes. Mis à jour chaque matin.",
        "idxDesc": "Le meilleur prix du jour dans chaque pointure pour {n} modèles de chaussures de course dans les boutiques canadiennes. Mis à jour chaque matin par The Gear Fox.",
        "onSale": "en solde", "home": "The Gear Fox", "switch": "English", "menu": "Menu", "mDeals": "Aubaines du jour", "mShoes": "Prix des chaussures par modèle", "mWatch": "Vos favoris", "mSizes": "Mes tailles", "mAbout": "À propos de The Gear Fox", "mRaces": "Listes de matériel de course", "tagline": "FLAIREZ LES AUBAINES",
        "hdrSearch": "Chercher des aubaines", "hdrSearchPh": "Chaussures, marques…", "hdrSearchGo": "Chercher",
        "yourSize": "Votre pointure", "at": "chez", "see": "Voir", "watch": "Suivre le prix", "alertH": "M'avertir quand {name} baisse dans ma pointure",
        "alertTxt": "Gratuit. Un courriel quand le prix baisse dans votre pointure, plus les aubaines du vendredi. Désabonnement en un clic.", "alertBtn": "M'avertir",
        "boH": "Écrivez-moi quand le {name} revient dans ma pointure", "boTxt": "Gratuit. Un courriel quand une boutique que nous suivons l'a dans votre pointure, plus les aubaines du vendredi. Désabonnement en un clic.",
        "boFit": "Coupe", "boMen": "Homme", "boWomen": "Femme", "boSize": "Pointure", "boPick": "Choisissez d'abord la coupe et la pointure.",
        "alertPick": "Choisissez d'abord votre pointure plus haut, pour qu'on suive la bonne.", "alertBad": "Ce courriel ne semble pas valide.",
        "alertOk": "Presque fini : ouvrez le courriel envoyé à {email} et touchez le lien pour confirmer (regardez aussi dans les indésirables).", "alertFail": "Inscription impossible pour le moment. Réessayez dans une minute.",
        "alertDone": "Vous suivez cette chaussure. On vous écrit quand elle baisse dans votre pointure.", "emailPh": "vous@exemple.com", "pick": "Votre pointure :", "pickPh": "Choisissez votre pointure", "change": "Modifier", "allInSize": "Voir toutes les aubaines dans votre pointure →",
        "notInSize": "Pas en stock dans votre pointure en ce moment. Suivez-la et on vous écrira dès qu'elle revient ou baisse.",
        "find": "Chercher un modèle (ex. Clifton)", "noMatch": "Aucun modèle trouvé. Essayez le nom de la marque ou un mot plus court.",
        "foot": "The Gear Fox · Flairez les aubaines · Les prix changent souvent : le prix de la boutique au paiement est celui qui compte.",
        "privacy": "Confidentialité",
        "months": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "date": lambda d, m: f"{d} {m}",
        "money": lambda v: f"{v:,.2f} $".replace(",", " ").replace(".", ","),
    },
}
# the USA side (Oct 6, 2026): same pages in US English under /us/, from deals-us.json (US stores, US dollars)
US = dict(T["en"])
US["bfLive"] = None   # the live deal check is Canada only for now (Oct 27)
US.update({
    "dir": "us/shoes", "lang": "en-US", "other": "en-CA", "q": "&c=us", "home": "/?c=us", "cur": "USD",
    "title": "{name} price: every size, every store",
    "titleSale": "{name} Sale: from {price} (−{p}%)",
    "about": "The {name} is a {type}. Today {stores} US stores carry it and we found {sizes} sizes in stock.",
    "qSale": "Is the {name} on sale right now?", "qWhere": "Where is the {name} cheapest?",
    "hubs": {"all": ("Running shoes on sale", "Running shoes on sale today", "Every popular running shoe on sale today at US running stores, sorted by the biggest discount. Checked every morning."),
             "road": ("Road running shoes on sale", "Road running shoes on sale", "Daily trainers and road shoes on sale today at US running stores, biggest discount first."),
             "trail": ("Trail running shoes on sale", "Trail running shoes on sale", "Trail running shoes on sale today at US running stores, biggest discount first."),
             "racing": ("Carbon racing shoes on sale", "Racing shoes on sale", "Carbon-plated and racing shoes on sale today at US running stores, biggest discount first."),
             "women": ("Women's running shoes on sale", "Women's running shoes on sale", "Women's running shoes on sale today at US running stores, biggest discount first."),
             "men": ("Men's running shoes on sale", "Men's running shoes on sale", "Men's running shoes on sale today at US running stores, biggest discount first.")},
    "hubDir": "us/running-shoes-sale", "brandDir": "us/brands", "bfDir": "us/black-friday", "bdDir": None,   # no Boxing Day in the US
    "sizeTitle": "{g} Size {s} Running Shoes on Sale: {n} deals today",
    "sizeIntro": "{n} running shoes on sale today in {g} size {s} at US running stores. Every price is the price in size {s}, biggest discount first. Checked every morning.",
    "brandTitle": "{brand} Sale: {n} running shoes on sale, up to {p}% off", "brandH1": "{brand} shoes on sale",
    "brandIntro": "Every {brand} running shoe we track at US running stores, with today's best price. Biggest discount first; checked every morning.",
    "bfTitle": "Black Friday 2026 running shoe deals", "bfH1": "Black Friday 2026: running shoe deals",
    "bfIntro": "Black Friday is Friday, November 27. We check local running stores across the US every morning and show only what's in stock. Here are today's biggest running shoe deals.",
    "bfTitlePre": "Black Friday 2026 running shoe deals: what to expect", "bfH1Pre": "Black Friday 2026: November {date}",
    "bfIntroPre": "{days} days to go. Black Friday deals aren't out yet. During Black Friday week this page shows the real deals from local running stores across the US, checked every morning.",
    "h1sub": "On sale at US running stores: every size, every store",
    "desc": "{name}: today's best price in every size at {n} US running stores{off}. Checked every morning by The Gear Fox.",
    "idxTitle": "Running shoe prices by model", "idxIntro": "Every popular running shoe we track, with today's best price in each size at US running stores. Updated every morning.",
    "idxDesc": "Today's best price in every size for {n} running shoe models at US running stores. Updated every morning by The Gear Fox.",
    "switch": "Canadian stores", "homeH": "Today's best running shoe deals",
    "bfOther": ("In Canada?", "See Black Friday deals at Canadian stores →", "/black-friday/"),
    "bfTrackTxt": "Since October 6 we record the price of every running product we follow at US stores, every day: {n} products so far. So on Black Friday we'll know which deals are real and which prices went up in November just to come back down.",
})
T["en"].update({"q": "", "home": "/", "cur": "CAD"})
T["fr"].update({"q": "&lang=fr", "home": "/?lang=fr", "cur": "CAD"})
# where a row's store ships from, said only when it's not the page's own country
T["en"]["abroad"] = lambda st: T["en"]["us"] if len(st) > 1 else ""
T["fr"]["abroad"] = lambda st: T["fr"]["us"] if len(st) > 1 else ""
US["abroad"] = lambda st: "ships from Canada" if len(st) < 2 else "" if st[1] == "US" else "ships from abroad"

UMAMI_ID = "d73c30be-171d-40d8-8101-278c2a536699"
SB_URL = "https://krwymmkauwqqxjxbvkyq.supabase.co"


def esc(s):
    return html.escape(str(s), quote=True)


def base_model(n):
    """"Triumph 23 Running Shoes [Wide] - Women's" -> "Triumph 23"."""
    n = re.sub(r"\s*(-\s*|\()(Men|Women)[’']s\)?$|\s*(-\s*|\()Unisex\)?$", "", n)
    n = re.split(r"\s+[—·]\s+", n)[0]                                    # "Clifton 10 — White/White"
    n = re.sub(r"\s*[\[(](x-?wide|extra wide|wide|2e|4e|d|ee|large)[\])]\s*|\s+\b(extra wide|x-?wide|wide)\b", " ", n, flags=re.I)
    n = re.sub(r"\b((trail|road) )?running shoes?\b|\bhiking shoes?\b|\bshoes?\b", "", n, flags=re.I)
    n = re.sub(r"^\s*(M|W|U|Unisex|All[- ]Gender|Men[’']?s|Women[’']?s)\s+", "", n, flags=re.I)        # "M Ghost 18" (Oct 7)
    n = re.sub(r"\s+(running road|road racing|road running|road)\s*$", "", n.strip(" -"), flags=re.I)   # "Ghost 17 Road"
    # Oct 8 (Search Console skipped near-copies): Nike's long names and athlete editions share one page
    n = re.sub(r"\b(ZoomX|Air Zoom|Zoom)\s+(?=(Vaporfly|Alphafly|Pegasus|Streakfly|Invincible)\b)", "", n, flags=re.I)
    n = re.sub(r"\b(Vaporfly|Alphafly)\s+Next\s*%?\s*", r"\1 ", n, flags=re.I)
    n = re.sub(r"\s+(Keely Hodgkinson|H\.?\s?Koumori)\b.*$", "", n, flags=re.I)
    # Oct 24 (28 shoes had a "Gore-Tex" page AND a "GTX" page competing on Google): one page each
    n = re.sub(r"\bGore[- ]?Tex\b", "GTX", n, flags=re.I)
    n = re.sub(r"^((?:Fresh\s?Foam(?:\s+X)?|FuelCell)\s+)?(\d{3,4})\s+v(\d+)\b", r"\1\2v\3", n.strip(), flags=re.I)   # New Balance "880 v15" = "880v15"
    return re.sub(r"\s+", " ", n).strip(" -")


def slugify(s):
    s = s.lower().replace("+", " plus").replace("&", " and ")
    s = re.sub(r"[àâä]", "a", re.sub(r"[éèêë]", "e", re.sub(r"[öô]", "o", re.sub(r"[üû]", "u", s))))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def store_names(index_html):
    """The STORES map in index.html: {"altitude-sports.com": ["Altitude Sports"], "thefeed.com": ["The Feed", "US"], ...}."""
    m = re.search(r"const STORES=(\{.*?\});", index_html, re.S)
    try:
        return json.loads(m.group(1)) if m else {}
    except Exception:
        return {}


def host(u):
    return urlparse(u).hostname.replace("www.", "") if u else ""


def size_url(item, e):
    """Same as the site's sizeUrl(): the store's own link for this size, else ?variant=."""
    u = item["of"][e[2]] if e[2] < len(item["of"]) else item["of"][0]
    if len(e) < 5 or not u:
        return u
    if isinstance(e[4], str) and e[4].startswith("https://"):
        return e[4]
    p = urlparse(u)
    q = dict(parse_qsl(p.query))
    q["variant"] = e[4]
    return urlunparse(p._replace(query=urlencode(q)))


def size_sort(s):
    # Oct 23 (Prime X3 Strung's unisex table read 6, 7.5 … 12, W 10, W 12, W 8.5): men's/plain sizes first, then women's ("W 8.5"
    # / "F 8,5"), each by number
    w = bool(re.match(r"[WF] ", s))
    m = re.search(r"(\d+(?:[.,]\d)?)", s)
    return (w, float(m.group(1).replace(",", ".")) if m else 99, s)


def build_models(items):
    models = defaultdict(list)
    for d in items:
        if d["g"] != "shoes" or d.get("t") == "spike":
            continue
        name = base_model(d["n"])
        if not name:
            continue
        models[slugify(f'{d["b"]} {name}')].append(d)
    return models


def canadian_stores(its, stores):
    return {host(u) for d in its for u in d["of"] if len(stores.get(host(u), [""])) < 2}


def variant_label(d, L):
    sx = d.get("sx") or []
    lab = L["men"] if sx == ["men"] else L["women"] if sx == ["women"] else L["unisex"]
    if any(str(e[0]).startswith(("M:", "W:")) for e in d["sz"]):
        lab = L["unisex"]
    if any(str(e[0]).startswith("W:") for e in d["sz"]):   # Oct 23: it lists women's sizes too, so not "(men's sizes)"
        lab = L["unisexMW"]
    return lab + (f" · {L['wide']}" if d.get("w") else "")


def rows_for(d, stores, L):
    out = {}
    for e in d["sz"]:
        s = str(e[0])
        if s.endswith("~N") or s == "OS":
            continue
        wide = s.endswith("~W")
        mw = any(str(x[0]).startswith("W:") for x in d["sz"])   # both cuts in one table: men's rows say "M 9" (as the summary does)
        s = s.replace("~W", "").replace("M:", "M " if mw else "").replace("W:", "W ").replace("E:", "EU ")   # EU-only boots (Oct 25)
        if mw and not s.startswith(("M ", "W ")):     # a store's plain "8" in that table is the men's 8: one row with "M 8"
            s = "M " + s
        key = s + (f" ({L['wide']})" if wide and not d.get("w") else "")
        if key not in out or e[1] < out[key][0]:
            u = size_url(d, e)
            out[key] = (e[1], e[3] if len(e) > 3 else e[1], host(u), u, final_sale(d, e))
    return sorted(out.items(), key=lambda kv: size_sort(kv[0]))


def final_sale(d, e):
    """Same as the site's finalSale(): the store's rule (scrape.py FINAL_SALE, per offer in "fs") for the price shown."""
    fs = d.get("fs") or []
    c = fs[e[2]] if e[2] < len(fs) else 0
    if not c:
        return False
    reg = e[3] if len(e) > 3 and e[3] else e[1]
    return True if c == 1 else e[1] < reg * 0.99 if c == 2 else reg > 0 and 100 * (1 - e[1] / reg) >= c - 0.5


HOME_TZ = ZoneInfo("America/Vancouver")   # Oct 8: the 4:17pm update is already "tomorrow" in UTC ("checked Oct 9" on Oct 8)


def fmt_date(iso, L):
    dt = (datetime.fromisoformat(iso.replace("Z", "+00:00")) if iso else datetime.now(timezone.utc)).astimezone(HOME_TZ)
    return L["date"](dt.day, L["months"][dt.month - 1])


HEAD_CSS = """
:root{--ink:#17201C;--muted:#5C6660;--mist:#EEF1EC;--card:#FFFFFF;--line:#CBD2CC;--moss:#B8470A;--hivis:#F26A1B;--hivis-ink:#17201C;
--band:#17201C;--band-ink:#FFFFFF;--body:"Barlow",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--display:"Barlow Condensed","Arial Narrow",Impact,system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#E7ECE8;--muted:#9BA6A0;--mist:#121815;--card:#1B2320;--line:#34403A;--moss:#FF9A5C;--hivis-ink:#121815;--band:#26312C;--band-ink:#E7ECE8}}
:root[data-theme="dark"]{--ink:#E7ECE8;--muted:#9BA6A0;--mist:#121815;--card:#1B2320;--line:#34403A;--moss:#FF9A5C;--hivis-ink:#121815;--band:#26312C;--band-ink:#E7ECE8}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--mist);color:var(--ink);font:400 17px/1.5 var(--body);-webkit-font-smoothing:antialiased}
a{color:var(--moss)}
.top{background:var(--card);border-bottom:1.5px solid var(--line)}
.top .in,.wrap{max-width:720px;margin:0 auto;padding:12px 16px}
.top .in{display:flex;align-items:center;justify-content:space-between;gap:12px}
.top .logo{display:flex;flex-direction:column;align-items:center;text-decoration:none;color:var(--ink)}
.top .logo img{height:40px;width:auto;display:block}
.top .tagline{display:flex;align-items:center;gap:5px;margin-top:3px;font:600 8.5px/1 var(--body);letter-spacing:.16em;white-space:nowrap}
.top .tagline::before,.top .tagline::after{content:"";width:10px;height:1.5px;background:var(--hivis);border-radius:1px}
.lang{font:600 14px var(--body);border:1.5px solid var(--line);border-radius:999px;padding:6px 12px;text-decoration:none;color:var(--ink)}
.top{position:relative}.menu{position:static}.menu summary{list-style:none;display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:50%;border:1.5px solid var(--line);cursor:pointer;color:var(--ink)}
.menu summary::-webkit-details-marker{display:none}.menu[open] summary{background:var(--ink);color:var(--card);border-color:var(--ink)}
.menu nav{position:absolute;right:max(16px,calc(50% - 344px));top:calc(100% + 6px);z-index:30;width:min(300px,calc(100vw - 32px));background:var(--card);border:1.5px solid var(--line);border-radius:18px;box-shadow:0 14px 40px rgba(0,0,0,.18);padding:8px}
.menu nav a{display:flex;align-items:center;gap:12px;min-height:48px;padding:0 12px;border-radius:12px;font:600 16px/1.2 var(--body);color:var(--ink);text-decoration:none}
.menu nav a:hover{background:var(--mist)}.menu nav .mi{flex:0 0 auto;color:var(--muted)}
.menu nav a.sw{border-top:1.5px solid var(--line);border-radius:0;margin-top:6px;font-size:15px;color:var(--moss)}
.menu nav .lsw{display:flex;align-items:center;gap:6px;flex-wrap:wrap;border-top:1.5px solid var(--line);margin-top:6px;padding:10px 8px 4px;font-size:14px;color:var(--muted)}
.menu nav .lsw .k{flex:1 1 auto}
.menu nav .lsw a,.menu nav .lsw .on{display:inline-flex;align-items:center;min-height:36px;padding:6px 12px;border:1.5px solid var(--line);border-radius:999px;font:600 14px var(--body);color:var(--ink);text-decoration:none}
.menu nav .lsw .on{background:var(--hivis,#C9F24D);border-color:var(--hivis,#C9F24D);color:#17201C}
.crumbs{font-size:14px;color:var(--muted);margin:14px 0 0}
h1{font:800 clamp(30px,7vw,44px)/1.05 var(--display);margin:6px 0 4px;letter-spacing:-.01em}
.sub{margin:0 0 14px;color:var(--muted);font-size:16px}
.hero{display:flex;gap:16px;align-items:center;background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:14px;margin:0 0 18px}
.hero img{width:120px;height:90px;object-fit:contain;background:#fff;border-radius:10px;flex:none}
.hero p{margin:2px 0}
.hero b{font:800 26px/1 var(--display)}
.hero s{color:var(--muted)}
.tag{display:inline-block;font:700 12px var(--body);letter-spacing:.04em;text-transform:uppercase;color:var(--moss)}
.badge{display:inline-block;background:var(--hivis);color:var(--hivis-ink);border:1.5px solid var(--ink);border-radius:6px;font:700 13px var(--body);padding:2px 8px;margin-top:6px}
.facts{font-size:14px;color:var(--muted)}
h2{font:700 24px/1.1 var(--display);margin:22px 0 8px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1.5px solid var(--line);border-radius:12px;overflow:hidden;font-size:15px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line)}
th{font:600 13px var(--body);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
td.p{white-space:nowrap}
td.p b{font:800 18px var(--display)}
td.p s{color:var(--muted);font-size:13px;margin-left:4px}
.off{display:inline-block;background:var(--hivis);color:var(--hivis-ink);border-radius:5px;font:700 12px var(--body);padding:1px 5px;margin-left:6px}
.us{display:block;font-size:12px;color:var(--muted)}
.fin{display:block;font-size:12px;font-weight:600;color:var(--ink)}
.gts{display:flex;flex-direction:column}
.th2{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.watch{font:600 14px var(--body);color:var(--moss);white-space:nowrap}
tr.yours td{background:rgba(242,106,27,.14)}
tr.yours td:first-child{font-weight:700;box-shadow:inset 4px 0 0 var(--hivis)}
.side{background:#17201C;color:#fff;border-radius:12px;padding:12px 14px;margin:0 0 14px;font-size:15px}
.side a{color:#FFB37A;font-weight:700}
.mine{background:var(--card);border:1.5px solid var(--hivis);border-radius:12px;padding:12px 14px;margin:0 0 6px;font-size:16px}
.mine b{font:800 20px var(--display)}
.mine .pickl{font-weight:600}.mine select.pick{font:600 16px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:10px;padding:8px 10px;min-height:44px;max-width:100%}
.mine .chg{font:600 15px var(--body);color:var(--moss);background:none;border:0;padding:0;text-decoration:underline;cursor:pointer}
.mine .all{display:block;margin-top:6px;font-size:15px}.mine .all a{color:var(--moss);font-weight:600}
.alert{background:var(--band);color:var(--band-ink);border-radius:14px;padding:14px 16px;margin:12px 0 4px}
.alert h2{margin:0 0 4px;font-size:19px;color:var(--band-ink)}.alert .fine{margin:0 0 10px;font-size:14px;opacity:.85}
.alert form{display:flex;gap:8px}.alert input{flex:1;min-width:0;font:16px var(--body);border:0;border-radius:999px;padding:11px 14px}
.alert button{flex:none;font:700 15px/1 var(--body);background:var(--hivis);color:var(--hivis-ink);border:0;border-radius:999px;padding:11px 16px;cursor:pointer}
.alert .msg{margin:8px 0 0;font-size:14px}.alert .msg:empty{display:none}
.boback form{flex-wrap:wrap}.boback .bok{flex:1 1 100%;margin:0;font-weight:700}.boback .bok button{background:none;border:0;color:inherit;text-decoration:underline;font:inherit;font-weight:400;padding:0 0 0 2px;cursor:pointer}.boback .bor[hidden]{display:none}.boback .bor{display:flex;gap:8px;flex:1 1 100%}.boback select{flex:1;min-width:0;font:16px var(--body);border:0;border-radius:999px;padding:10px 12px;background:#fff;color:#17201c}
.qs form{flex-direction:column}.qsrow{display:flex;gap:8px}.qs select{flex:1;min-width:0;font:16px var(--body);border:0;border-radius:999px;padding:11px 12px;background:#fff;color:#17201C}
.qs .qsrow+.qsrow{flex-wrap:wrap}.qs .qsrow+.qsrow input{flex:1 1 100%}.qs .qsrow+.qsrow button{flex:1 1 100%}
.qs .qsmore{margin:10px 0 0}.qs .qsmore a{color:var(--band-ink)}
.backbar{position:fixed;left:0;right:0;bottom:0;z-index:50;background:#17201C;color:#fff;padding:12px 14px calc(12px + env(safe-area-inset-bottom));box-shadow:0 -6px 24px rgba(0,0,0,.25)}
.backbar .in{max-width:640px;margin:0 auto}.backbar b{font-size:17px}.backbar p{margin:2px 0 8px;font-size:14px;opacity:.85}
.backbar form{display:flex;gap:8px}.backbar input{flex:1;min-width:0;font:16px var(--body);border:0;border-radius:999px;padding:10px 14px}
.backbar button{flex:none;font:700 15px/1 var(--body);border:0;border-radius:999px;padding:10px 14px;cursor:pointer;background:var(--hivis);color:var(--hivis-ink)}
.backbar form{flex-wrap:wrap}.backbar .bsel{flex:1 1 100%;font:16px var(--body);border:0;border-radius:999px;padding:10px 12px}
.backbar .x{position:absolute;top:6px;right:8px;background:none;color:#fff;font-size:22px;padding:4px 8px}
.faq h3{font:700 17px/1.3 var(--body);margin:14px 0 4px}
.faq p{margin:0 0 6px}
.cards{display:grid;gap:8px;padding:0;margin:0;list-style:none}
.cards a{display:flex;align-items:center;gap:12px;background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:8px 12px 8px 8px;color:var(--ink);text-decoration:none}
.cards img{width:72px;height:54px;object-fit:contain;background:#fff;border-radius:8px;flex:none}
.cards .nm{flex:1;min-width:0}.cards .nm b{display:block;font:700 17px/1.2 var(--display)}.cards .nm small{color:var(--muted);font-size:13px}
.cards .pr{text-align:right;white-space:nowrap}.cards .pr b{display:block;font:800 19px var(--display)}.cards .pr .off{margin:0}
.browse{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 14px}.browse a{font:600 14px var(--body);color:var(--ink);text-decoration:none;border:1.5px solid var(--line);border-radius:999px;padding:5px 11px;background:var(--card)}
.cta{background:var(--band);color:var(--band-ink);border-radius:14px;padding:18px;margin:26px 0}
.cta h2{margin:0 0 6px;color:var(--band-ink)}
.cta p{margin:0 0 12px;color:var(--band-ink);opacity:.85}
.btn{display:inline-block;background:var(--hivis);color:#17201C;border:2px solid #17201C;border-radius:10px;font:700 18px var(--display);padding:10px 18px;text-decoration:none}
.links{display:flex;flex-wrap:wrap;gap:8px;padding:0;list-style:none;margin:0}
.alts{margin:22px 0 6px}.alts h2{margin:0 0 10px}
.altrow{display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:6px;scrollbar-width:none}.altrow::-webkit-scrollbar{display:none}
.altrow a{flex:0 0 150px;scroll-snap-align:start;display:flex;flex-direction:column;background:var(--card,#fff);border:1px solid var(--line,#ddd);border-radius:10px;padding:8px;text-decoration:none;color:inherit}
.altrow img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:6px}
.altrow img.x,.altrow img:not([src]){visibility:hidden}   /* a photo that fails keeps its square, the card its shape */
.altrow .ab{display:block;margin-top:6px;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;opacity:.7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.altrow .an{font-size:14px;line-height:1.25;margin:1px 0 4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.altrow .ap{margin-top:auto;font-size:15px}.altrow .ap b{font-size:16px}.altrow .ao{display:inline-block;margin-left:4px;background:#F26A1B;color:#111;font-weight:700;font-size:12px;border-radius:4px;padding:1px 5px}
.altrow .az{font-size:12.5px;opacity:.75}
/* Oct 22 (Bastien: "one row that you can scroll left like on Amazon"): one row on every screen; computers get arrows when it overflows */
.altw{position:relative}
.altw .arr{display:none;position:absolute;top:38%;z-index:2;width:38px;height:38px;border-radius:50%;border:1px solid var(--line,#ddd);background:#fff;color:#17232B;font:700 22px/1 system-ui;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.altw .arr.l{left:-12px}.altw .arr.r{right:-12px}
@media(hover:hover) and (pointer:fine){.altw.of .arr{display:block}.altw .arr[disabled]{opacity:0;pointer-events:none}}
@media(min-width:760px){.altrow a{flex-basis:160px}}
.links a{display:inline-block;background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:6px 12px;text-decoration:none;color:var(--ink);font-size:15px}
.links small{color:var(--moss);font-weight:600}
.brand{margin:18px 0 6px;font:700 20px var(--display);scroll-margin-top:120px}
.find{position:sticky;top:0;z-index:5;background:var(--mist);padding:10px 0 8px;margin:0 -2px}
/* Oct 23: the header comes back on scroll-up (phones), stays on computers; search icon + box under it (class hdrb on every page) */
.cards a .nm small.lowl{display:block;color:#1f7a46;font-weight:700}
.realn{background:#e8f5ec;color:#1f5f38;border-radius:12px;padding:10px 14px;font-weight:600;margin:12px 0}
.hdrb header.top{position:sticky;top:0;z-index:30;transition:transform .22s ease}
.hdrb header.top.hide{transform:translateY(-100%)}
.hdrb .find{top:var(--hh,0px);transition:top .22s ease}
.hsb{display:inline-flex;align-items:center;justify-content:center;flex:none;width:44px;height:44px;margin-left:auto;margin-right:-4px;border-radius:50%;background:none;border:1px solid rgba(255,255,255,.3);color:#fff;cursor:pointer}
.hsb[aria-expanded="true"]{background:rgba(255,255,255,.16)}
.hsb[hidden],.hsf[hidden]{display:none}
.hsf{display:flex;gap:8px;max-width:720px;margin:0 auto;padding:0 16px 12px}
.hsf input{flex:1;min-width:0;min-height:44px;font:400 16px var(--body);color:#17201C;background:#fff;border:0;border-radius:999px;padding:0 16px}
.hsf button{flex:none;min-height:44px;font:700 15px var(--body);color:#17201C;background:var(--hivis,#FF5A1F);border:0;border-radius:999px;padding:0 16px;cursor:pointer}
.find input{width:100%;font:400 17px var(--body);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:12px;padding:12px 14px}
.find input:focus{outline:3px solid var(--moss);outline-offset:1px}
.jump{display:flex;gap:6px;overflow-x:auto;padding:2px 0 4px;scrollbar-width:none}
.jump a{flex:none;font:600 13px var(--body);color:var(--ink);text-decoration:none;border:1.5px solid var(--line);border-radius:999px;padding:4px 10px;background:var(--card)}
.nomatch{color:var(--muted);margin:16px 0}
.foot{font-size:13px;color:var(--muted);margin:30px 0 10px}
.pws{margin:14px 0}.pw{background:var(--card);border:1.5px solid var(--line);border-left:5px solid var(--hivis);border-radius:12px;padding:10px 14px;margin:0 0 8px;font-size:15px}
.pw.good{border-left-color:#1C6B37}.pw b{display:block;font-size:14px;color:var(--muted)}
.pwbtn{display:inline-block;margin-top:2px;background:var(--hivis);color:#17201C;font-weight:700;text-decoration:none;border-radius:999px;padding:8px 14px}
.browse.sizes a[aria-current]{background:var(--ink);color:var(--card)}
"""


MENU_SVG = ('<svg class="mi" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')
MENU_ICONS = {'🎁': '<path d="M20 12v9H4v-9"/><path d="M2 7h20v5H2z"/><path d="M12 21V7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>', '🔥': '<path d="M3 12V4.5A1.5 1.5 0 0 1 4.5 3H12l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.4"/>', '👟': '<path d="M2.5 17v-6l3.5-3 3 2.5 2.5-2.5 4.5 4.5h3a2.5 2.5 0 0 1 2.5 2.5V17z"/><path d="M2.5 20.5h19"/>', '♡': '<path d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 8 3.4 4.5 6.9 4.5c2.1 0 3.6 1.2 5.1 3 1.5-1.8 3-3 5.1-3 3.5 0 5.5 3.5 4.2 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/>', '✏️': '<path d="M4 20h4L19.5 8.5l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>', '🦊': '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/><path d="M12 7.6v.1"/>', '📸': '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.2 6.8v.1"/>', '🏁': '<path d="M5 21V3.5"/><path d="M5 4h12l-2.5 4L17 12H5"/>'}   # same line icons as the homepage menu


def gift_season(today=None):
    """Nov 15 - Dec 26 (Vancouver date): the gift page is in the ☰ menu. GIFT_MENU=1 forces it (previews, checks)."""
    import datetime
    from zoneinfo import ZoneInfo
    d = today or datetime.datetime.now(ZoneInfo("America/Vancouver")).date()
    return bool(os.environ.get("GIFT_MENU")) or (11, 15) <= (d.month, d.day) <= (12, 26)


def menu_links(L, other_path):
    """The site's ☰ menu, as plain links (same items as the homepage menu)."""
    fr = L["lang"] == "fr-CA"
    home = L["home"]
    items = [(home, "🔥", L["mDeals"]), (f"/{L['dir']}/", "👟", L["mShoes"]),
             (home + ("&" if "?" in home else "?") + "show=watch", "♡", L["mWatch"]), (home + ("&" if "?" in home else "?") + "show=sizes", "✏️", L["mSizes"]),
             ("/about.html" + ("?lang=fr" if fr else ""), "🦊", L["mAbout"]), ("https://www.instagram.com/thegearfox/", "📸", "Instagram")]
    if L.get("hike"):      # boot + trail list pages: menu goes to the hiking side, trail gear lists instead of race lists
        items[1] = (f"/{L['dir']}/", "👟", L["mShoes"])
        items.insert(2, ("/us/hikes/" if L["lang"] == "en-US" else "/randonnees/" if fr else "/hikes/", "🏁",
                         "Listes de matériel de randonnée" if fr else "Trail gear lists"))   # Oct 26 (Bastien: "the trail list still links to races")
    else:
        items.insert(2, ("/us/races/" if L["lang"] == "en-US" else "/courses/" if fr else "/races/", "🏁", L["mRaces"]))   # race gear lists (Oct 21; US races too)
        # Oct 28 (growth chat, Bastien OK'd): "Gifts for runners" right after the race lists, Nov 15 - Dec 26, Canada only (pages are rebuilt every morning)
        if L["lang"] != "en-US" and gift_season():
            items.insert(3, ("/cadeaux-coureurs/" if fr else "/gifts-for-runners/", "🎁", "Cadeaux pour coureurs" if fr else "Gifts for runners"))
    out = "".join(f'<a href="{u}">{MENU_SVG.format(MENU_ICONS[i])}{esc(t)}</a>' for u, i, t in items)
    if L["lang"] == "en-US":
        return out + f'<a class="sw" href="{other_path}" hreflang="{L["other"]}">{L["switch"]}</a>'
    # Oct 23 (Bastien: "French to english should give people the choice"): every language listed in its own name, this one marked
    here = '<span class="on" aria-current="true" lang="{0}">{1}</span>'
    there = f'<a href="{other_path}" hreflang="{L["other"]}" lang="{{0}}">{{1}}</a>'
    langs = [("en", "English", not fr), ("fr", "Français", fr)]
    return out + (f'<div class="lsw"><span class="k">{"Langue" if fr else "Language"}</span>'
                  + "".join((here if cur else there).format(c, n) for c, n, cur in langs) + "</div>")


def alternates(L, path_en, path_fr):
    """Canada: English + French. USA: its own page, plus the Canadian twin when there is one (path_fr holds it)."""
    if L["lang"] == "en-US":
        twin = (f'\n<link rel="alternate" hreflang="en-CA" href="{BASE}{path_fr}">\n<link rel="alternate" hreflang="x-default" href="{BASE}{path_fr}">'
                if path_fr else "")
        return f'<link rel="alternate" hreflang="en-US" href="{BASE}{path_en}">{twin}'
    us = "/us" + path_en if path_en == "/black-friday/" or path_en.startswith("/running-shoes-sale/") else ""   # pages that always have a US twin
    return (f'<link rel="alternate" hreflang="en-CA" href="{BASE}{path_en}">\n<link rel="alternate" hreflang="fr-CA" href="{BASE}{path_fr}">\n'
            + (f'<link rel="alternate" hreflang="en-US" href="{BASE}{us}">\n' if us else "")
            + f'<link rel="alternate" hreflang="x-default" href="{BASE}{path_en}">')


def page_head(L, title, desc, path_en, path_fr, extra=""):
    lang_path = path_en if L["lang"] != "fr-CA" else path_fr
    return f"""<!DOCTYPE html>
<html lang="{L['lang'][:2]}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | The Gear Fox</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}{lang_path}">
{alternates(L, path_en, path_fr)}
<meta name="theme-color" content="#F26A1B">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Gear Fox">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Gear Fox">
<meta property="og:url" content="{BASE}{lang_path}">
<meta property="og:image" content="{BASE}/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/shoe-pages.css">
{extra}
<link rel="stylesheet" href="/theme.css">
<script defer src="https://cloud.umami.is/script.js" data-website-id="{UMAMI_ID}" data-domains="thegearfox.com,www.thegearfox.com"></script>
</head>
<body>
<header class="top"><div class="in"><a class="logo" href="{L['home']}" aria-label="The Gear Fox">
<img src="/logo-mark-dark.svg" alt="The Gear Fox" width="1534" height="664">
<span class="tagline">{L['tagline']}</span></a>
<button type="button" class="hsb" id="hsb" aria-label="{L['hdrSearch']}" aria-expanded="false" hidden><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg></button>
<details class="menu"><summary aria-label="{L['menu']}"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></summary>
<nav>{menu_links(L, (path_fr or "/shoes/") if L['lang'] != 'fr-CA' else path_en)}</nav></details></div>
<form class="hsf" id="hsf" role="search" action="/" hidden data-home="{L['home']}"><input type="search" name="q" placeholder="{L['hdrSearchPh']}" aria-label="{L['hdrSearch']}" autocomplete="off" enterkeyhint="search"><button type="submit">{L['hdrSearchGo']}</button></form></header>
<script>document.documentElement.classList.add("hdrb")</script>
<main class="wrap">
"""


def page_foot(L):
    priv = "/privacy.html" + ("?lang=fr" if L["lang"] == "fr-CA" else "")
    # deal clicks count toward the monthly report (same anonymous counter as the site: store + category, nothing personal)
    return f"""<p class="foot">{esc(L['foot'])} · <a href="https://www.instagram.com/thegearfox/" rel="noopener">@thegearfox</a> · <a href="{priv}">{L['privacy']}</a></p>
</main>
<script>
/* our own analytics (same as the homepage, supabase/analytics.sql): what people do, never who they are */
var ana=(function(){{var ls=function(k){{try{{return localStorage.getItem(k)}}catch(e){{return null}}}},ss=function(k){{try{{return sessionStorage.getItem(k)}}catch(e){{return null}}}};
  var uid=function(){{try{{return crypto.randomUUID()}}catch(e){{return "10000000-1000-4000-8000-100000000000".replace(/[018]/g,function(c){{return (c^Math.random()*16>>c/4).toString(16)}})}}}};
  var did=ls("gf-did"),sid=ss("gf-sid"),nv=+(ls("gf-nv")||0),fresh=!sid,Q=[],t0=Date.now(),T=null;
  if(!did){{did=uid();try{{localStorage.setItem("gf-did",did)}}catch(e){{}}}}
  if(!sid){{sid=uid();nv+=1;try{{sessionStorage.setItem("gf-sid",sid);localStorage.setItem("gf-nv",String(nv))}}catch(e){{}}}}
  var touch=matchMedia("(pointer:coarse)").matches,w=Math.min(screen.width||innerWidth,innerWidth),dev=touch&&w<600?"phone":touch&&w<1100?"tablet":"computer";
  var tz=null;try{{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||null}}catch(e){{}}
  var ref=null;try{{var r0=(new URLSearchParams(location.search).get("ref")||"").toLowerCase().replace(/[^a-z0-9_-]/g,"").slice(0,40),
    old=JSON.parse(localStorage.getItem("gf-ref")||"null");ref=r0||old||null;
    if(r0&&!old)localStorage.setItem("gf-ref",JSON.stringify(r0))}}catch(e){{}}   /* kept like on the homepage (first link wins), so a
                                         sign-up after a Reddit -> shoe page -> homepage visit is credited to Reddit (Oct 6) */
  /* Oct 27: the first batch (the visit) was being lost for ~28% of first visits: it waits in sessionStorage (gf-vq) and rides again
     until a send of it is confirmed (same as the homepage); a prerendered page waits until it is opened */
  var vBusy=false;
  function flush(k){{if(!Q.length)return;if(document.prerendering){{if(!T)T=setTimeout(function(){{T=null;flush(false)}},3000);return}}
    var pv=null;if(!vBusy||Date.now()-vBusy>8000)try{{pv=JSON.parse(ss("gf-vq")||"null")}}catch(e){{}}
    var ev=Q.splice(0,pv?39:40),hasV;if(pv&&!ev.some(function(e){{return e.k==="visit"}}))ev.unshift(pv);hasV=ev.some(function(e){{return e.k==="visit"}});if(hasV)vBusy=Date.now();
    try{{fetch("{SB_URL}/rest/v1/rpc/ana_track",{{method:"POST",keepalive:!!k,headers:{{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"}},
    body:JSON.stringify({{p_did:did,p_sid:sid,p_events:ev,p_lang:"{L['lang'][:2]}",p_ref:ref,p_dev:dev,p_nv:nv,p_tz:tz}})}})
    .then(function(r){{if(hasV){{vBusy=false;if(r.ok)try{{sessionStorage.removeItem("gf-vq")}}catch(e){{}}}}}}).catch(function(){{if(hasV)vBusy=false}})}}catch(e){{if(hasV)vBusy=false}}}}
  function add(k,d,n,p){{var e={{k:k}};if(d)e.d=String(d).slice(0,120);if(n!=null)e.n=n;if(p)e.p=p;Q.push(e);if(!T)T=setTimeout(function(){{T=null;flush(false)}},6000)}}
  var away=false,bye=function(){{if(away)return;away=true;add("leave",null,Math.round((Date.now()-t0)/1000));clearTimeout(T);T=null;flush(true)}};
  document.addEventListener("visibilitychange",function(){{if(document.visibilityState==="hidden")bye();else{{away=false;t0=Date.now()}}}});
  addEventListener("pagehide",bye);
  var em="";try{{em=(new URLSearchParams(location.search).get("em")||"").replace(/[^a-z-]/g,"").slice(0,20)}}catch(e){{}}   /* ?em=friday: from our emails */
  if(fresh){{add("visit",em?"email-"+em:document.referrer?new URL(document.referrer).hostname:"",null,location.pathname);try{{sessionStorage.setItem("gf-vq",JSON.stringify(Q[Q.length-1]))}}catch(e){{}}}}
  var m=location.pathname.match(/^\/(?:us\/)?(?:shoes|chaussures)\/([^\/]+)\/$/);add("shoe-page-view",m?m[1]:location.pathname);
  return add}})();
/* Oct 23 (Bastien: "On some pages you get lost scrolling ... keep the header on all pages? So people can search and toggle menu or
   click the logo"; then "we don't need to test this. It helps the flow"): on phones the header slides away while you read down and
   comes back as soon as you scroll up (NN/g: partially persistent header); on computers it stays; the search icon opens a box that
   searches the homepage in your size */
(function(){{var top=document.querySelector("header.top"),b=document.getElementById("hsb"),f=document.getElementById("hsf");if(!top||!b||!f)return;
  b.hidden=false;var inp=f.querySelector("input"),root=document.documentElement;
  var open=function(on){{f.hidden=!on;b.setAttribute("aria-expanded",String(on));if(on){{show();inp.focus()}}}};
  b.addEventListener("click",function(){{open(f.hidden)}});
  f.addEventListener("submit",function(e){{e.preventDefault();var v=inp.value.trim();if(!v)return;try{{ana("signup-step","hdr-search")}}catch(x){{}}
    var h=f.dataset.home;location.href=h+(h.indexOf("?")>=0?"&":"?")+"q="+encodeURIComponent(v)}});
  /* phones: slides away while you read down, back as soon as you scroll up (NN/g: partially persistent header); computers: always there */
  var last=scrollY,hid=false,menu=top.querySelector("details.menu");
  var hh=function(){{root.style.setProperty("--hh",hid?"0px":top.offsetHeight+"px")}};
  var show=function(){{if(hid){{hid=false;top.classList.remove("hide");hh()}}}};
  var hide=function(){{if(!hid&&f.hidden&&!(menu&&menu.open)){{hid=true;top.classList.add("hide");hh()}}}};
  hh();addEventListener("resize",hh);
  addEventListener("scroll",function(){{var y=scrollY,d=y-last;if(Math.abs(d)<6)return;last=y;
    if(innerWidth>=900||y<top.offsetHeight*2){{show();return}}if(d>0)hide();else show()}},{{passive:true}})}})();
(function(){{var p,box=document.getElementById("mine");if(!box)return;
try{{p=JSON.parse(localStorage.getItem("rd-profile")||"null")}}catch(e){{}}
/* Oct 18 (spy-shopper pass): a women's visitor had to scroll past the whole Men's table; her cut goes first (CSS order only,
   so the tables keep their place in the page and their numbers for the size picker) */
var gq=(p&&p.gender)||"";if(!gq){{try{{gq=(JSON.parse(localStorage.getItem("gf-shoe-size")||"null")||{{}}).g||""}}catch(e){{}}}}
if(gq==="women")document.querySelectorAll('.gt[data-g="women"]').forEach(function(x){{x.style.order="-1"}});
var clean=function(s){{return s.replace(/\s*\(.*\)$/,"").replace(/^M /,"")}};   // "M 9" rows (unisex tables with women's sizes too) = men's 9
/* highlight the rows that fit and say where the size is cheapest; ok(table, row size) decides what fits */
function mark(ok){{var best=null;document.querySelectorAll("tr.yours").forEach(function(r){{r.classList.remove("yours");r.removeAttribute("id")}});
  document.querySelectorAll("table[data-g]").forEach(function(t,ti){{t.querySelectorAll("tr[data-s]").forEach(function(r){{
    if(!ok(t,ti,r.dataset.s))return;r.classList.add("yours");var pr=parseFloat(r.dataset.p);if(!best||pr<best.p)best={{p:pr,r:r}}}})}});
  return best}}
function say(best,extra){{box.hidden=false;if(!best){{box.innerHTML=box.dataset.none+(extra||"");return}}
  var c=best.r.children;best.r.id="your-size";
  box.innerHTML=box.dataset.your+" "+c[0].textContent+": <b>"+c[1].querySelector("b").textContent+"</b> "+box.dataset.at+" "+c[2].querySelector("a").textContent+' · <a href="#your-size">'+box.dataset.see+" ↓</a>"+(extra||"")}}
if(p&&p.sizes&&p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length){{   // sizes saved on the main site
  var mine=p.sizes.shoes.sizes.map(String),mineW=(p.sizes.shoes.women||[]).map(String),wid=p.sizes.shoes.width||[],g=p.gender||"any";
  var sizesFor=function(tg){{return g==="any"&&mineW.length&&tg==="women"?mineW:mine}};
  var wantW=wid.indexOf("Wide")>=0,wantR=!wid.length||wid.indexOf("Regular")>=0;
  say(mark(function(t,ti,s){{var tg=t.dataset.g,w=t.dataset.w==="1";if((w&&!wantW)||(!w&&!wantR))return false;if(tg!=="unisex"&&g!=="any"&&tg!==g)return false;
    var wide=/\(/.test(s),n=clean(s);if(wide&&!wantW)return false;
    if(tg==="unisex"){{if(/^W /.test(n))return g!=="men"&&sizesFor("women").indexOf(n.slice(2))>=0;return (g!=="women"&&mine.indexOf(n)>=0)||(g==="women"&&mine.indexOf(String(parseFloat(n)+1.5))>=0)}}
    return sizesFor(tg).indexOf(n)>=0}}));
  return}}
/* no sizes yet (a visitor from Google or Reddit): a size picker, remembered for this shoe page and the main site's sign-up */
var tables=[].slice.call(document.querySelectorAll("table[data-g]"));if(!tables.length)return;
var sel=document.createElement("select");sel.className="pick";sel.setAttribute("aria-label",box.dataset.pick);
sel.innerHTML='<option value="">'+box.dataset.pickph+"</option>"+tables.map(function(t,ti){{var h=t.previousElementSibling&&t.previousElementSibling.querySelector("h2");
  var seen={{}};return '<optgroup label="'+(h?h.textContent:"")+'">'+[].slice.call(t.querySelectorAll("tr[data-s]")).map(function(r){{var s=r.dataset.s;if(seen[s])return "";seen[s]=1;
    return '<option value="'+ti+"|"+s+'">'+(h?h.textContent+" ":"")+s+"</option>"}}).join("")+"</optgroup>"}}).join("");
var pickRow=function(){{box.hidden=false;box.innerHTML='<label class="pickl">'+box.dataset.pick+" </label>";box.appendChild(sel)}};
var choose=function(v,save){{if(!v){{pickRow();return}}var ti=+v.split("|")[0],s=v.slice(v.indexOf("|")+1),t=tables[ti];if(!t){{pickRow();return}}
  var best=mark(function(tt,tti,rs){{return tti===ti&&rs===s}});
  if(save){{var n=clean(s),gg=t.dataset.g;if(/^W /.test(n)){{gg="women";n=n.slice(2)}}else if(gg==="unisex")gg="men";
    try{{localStorage.setItem("gf-shoe-size",JSON.stringify({{g:gg,s:n,v:v}}))}}catch(e){{}}try{{ana("shoe-page-size",gg+"|"+n)}}catch(e){{}}try{{window.gfAlts&&gfAlts()}}catch(e){{}}try{{window.umami&&umami.track("shoe-page-size",{{}})}}catch(e){{}}}}
  say(best,' · <button type="button" class="chg">'+box.dataset.chg+"</button>"+'<span class="all"><a href="'+box.dataset.home+'">'+box.dataset.all+"</a></span>");
  box.querySelector(".chg").addEventListener("click",function(){{sel.value="";pickRow();sel.focus()}})}};
sel.addEventListener("change",function(){{choose(sel.value,true)}});
var prev;try{{prev=JSON.parse(localStorage.getItem("gf-shoe-size")||"null")}}catch(e){{}}
if(prev&&prev.v&&sel.querySelector('option[value="'+prev.v.replace(/"/g,"")+'"]')){{sel.value=prev.v;choose(prev.v,false)}}
else if(prev&&prev.s){{var o=[].slice.call(sel.options).filter(function(o){{var x=o.value.slice(o.value.indexOf("|")+1);return o.value&&clean(x).replace(/^W /,"")===prev.s&&(tables[+o.value.split("|")[0]].dataset.g===prev.g||(tables[+o.value.split("|")[0]].dataset.g==="unisex"&&(prev.g==="women")===/^W /.test(x)))}})[0];
  if(o){{sel.value=o.value;choose(o.value,false)}}else pickRow()}}
else pickRow()}})();
/* test 'alts' (Oct 22): B = other shoes of the same kind on sale in your size, under the size tables. Same coin as the homepage
   (device id + test name), so a device stays in its group; ?exp=alts:B forces it (previews, checks) */
(function(){{var box=document.getElementById("alts");if(!box)return;
var ls=function(k){{try{{return JSON.parse(localStorage.getItem(k)||"null")}}catch(e){{return null}}}};
var over=ls("gf-exp")||{{}};try{{var q=new URLSearchParams(location.search).get("exp");if(q){{q.split(",").forEach(function(x){{var a=x.split(":");if(a[0]&&/^[AB]$/.test(a[1]))over[a[0]]=a[1]}});localStorage.setItem("gf-exp",JSON.stringify(over))}}}}catch(e){{}}
var did="";try{{did=localStorage.getItem("gf-did")||""}}catch(e){{}}
var arm=over.alts||(function(){{var h=2166136261,s=did+"|alts";for(var i=0;i<s.length;i++){{h^=s.charCodeAt(i);h=Math.imul(h,16777619)}}return (h>>>0)%2?"B":"A"}})();
try{{if(!sessionStorage.getItem("gf-exp-alts")){{sessionStorage.setItem("gf-exp-alts","1");ana("signup-step","exp|alts|"+arm)}}}}catch(e){{}}
if(arm!=="B")return;
var fr=box.dataset.fr==="1",esc=function(s){{return String(s).replace(/[&<>"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}};
var money=function(v){{var s=v.toFixed(2);return fr?s.replace(".",",")+" $":"$"+s}};
var data=null,me=box.dataset.slug,myB=box.dataset.b.toLowerCase();
function size(){{var p=ls("rd-profile");if(p&&p.sizes&&p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length){{var g=p.gender||"any";
    return {{g:g,m:p.sizes.shoes.sizes.map(String),w:(p.sizes.shoes.women&&p.sizes.shoes.women.length?p.sizes.shoes.women:g==="women"?p.sizes.shoes.sizes:[]).map(String)}}}}
  var s=ls("gf-shoe-size");if(s&&s.s)return s.g==="women"?{{g:"women",m:[],w:[String(s.s)]}}:{{g:"men",m:[String(s.s)],w:[]}};return null}}
function draw(){{if(!data)return;var list=(data[box.dataset.t]||[]).filter(function(x){{return x.s!==me}}),z=size(),rows=[];
  list.forEach(function(x){{var best=null;
    if(z){{["m","w"].forEach(function(c){{if((c==="m"&&z.g==="women")||(c==="w"&&z.g==="men"))return;var sz=c==="m"?z.m:z.w;
      sz.forEach(function(s){{var v=(x[c]||{{}})[s];if(v&&(!best||v[0]<best[0]))best=[v[0],v[1],s]}})}});if(!best)return}}
    else{{["m","w"].forEach(function(c){{for(var s in (x[c]||{{}})){{var v=x[c][s];if(!best||v[1]>best[1])best=[v[0],v[1],null]}}}})}}
    var n=Object.keys(x.m||{{}}).length+Object.keys(x.w||{{}}).length;rows.push({{x:x,p:best,n:n}})}});
  rows.sort(function(a,b){{return z?b.p[1]-a.p[1]:((b.n>=6)-(a.n>=6))||b.p[1]-a.p[1]}});   // no size yet: shoes on sale in 6+ sizes first
  var out=[],per={{}};rows.forEach(function(r){{var b=r.x.b.toLowerCase();if(b===myB)return;per[b]=(per[b]||0)+1;if(per[b]<=2&&out.length<12)out.push(r)}});   // other brands, 2 at most each
  rows.forEach(function(r){{if(out.length<12&&out.indexOf(r)<0&&r.x.b.toLowerCase()===myB)out.push(r)}});
  if(out.length<3){{box.hidden=true;return}}
  box.querySelector("h2").textContent=z?box.dataset.h:box.dataset.h0;
  box.querySelector(".altrow").innerHTML=out.map(function(r){{var x=r.x,p=r.p;
    return '<a href="'+box.dataset.dir+x.s+'/" data-alt="'+esc(x.s)+'">'+'<img'+(x.i?' src="'+esc(x.i)+'"':"")+' alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.className=\\'x\\'">'+
      '<span class="ab">'+esc(x.b)+'</span><span class="an">'+esc(x.n)+'</span><span class="ap"><b>'+money(p[0])+'</b><span class="ao">−'+p[1]+'%</span></span>'+
      '<span class="az">'+esc(p[2]?box.dataset["in"].replace("{{s}}",p[2]):box.dataset.n.replace("{{n}}",r.n))+"</span></a>"}}).join("");
  box.hidden=false;arrows()}}
var row=box.querySelector(".altrow"),wrap=box.querySelector(".altw"),L=box.querySelector(".arr.l"),R=box.querySelector(".arr.r");
function arrows(){{var of=row.scrollWidth>row.clientWidth+4;wrap.classList.toggle("of",of);L.disabled=row.scrollLeft<4;R.disabled=row.scrollLeft+row.clientWidth>=row.scrollWidth-4}}
L.setAttribute("aria-label",fr?"Précédent":"Previous");R.setAttribute("aria-label",fr?"Suivant":"Next");row.addEventListener("scroll",arrows,{{passive:true}});addEventListener("resize",arrows);
L.addEventListener("click",function(){{row.scrollBy({{left:-row.clientWidth*0.9,behavior:"smooth"}})}});R.addEventListener("click",function(){{row.scrollBy({{left:row.clientWidth*0.9,behavior:"smooth"}})}});
box.addEventListener("click",function(e){{var a=e.target.closest("a[data-alt]");if(a){{try{{ana("shoe-page-link","alts|"+a.dataset.alt)}}catch(x){{}}}}}});
window.gfAlts=draw;
fetch(box.dataset.src).then(function(r){{return r.json()}}).then(function(d){{data=d;draw()}}).catch(function(){{}})}})();
/* "Email me when it drops in my size" (Oct 8): sign up right on the shoe page. The shoe goes on the watchlist (this phone and,
   through watch_new in the sign-up, any device that opens the confirm link); sizes come from the main site or the picker above */
(function(){{var box=document.getElementById("alertBox");if(!box)return;var f=box.querySelector("form"),msg=box.querySelector(".msg");
var get=function(k){{try{{return JSON.parse(localStorage.getItem(k)||"null")}}catch(e){{return null}}}},put=function(k,v){{try{{localStorage.setItem(k,JSON.stringify(v))}}catch(e){{}}}};
var subd=get("gf-sub");if(subd&&(subd.active||subd.key)){{var w0=get("gf-watch")||{{}};var t0=document.querySelector("table[data-key]");
  if(t0&&w0[t0.dataset.key]){{box.querySelector("form").remove();msg.textContent=box.dataset.done;return}}}}
f.addEventListener("submit",function(e){{e.preventDefault();
  var em=f.querySelector("input").value.trim().replace(/^mailto:/i,"").replace(/^.*<([^>]+)>.*$/,"$1").replace(/\s+/g,"").replace(/\.+$/,"");
  if(!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{{2,}}$/.test(em)||/\.\./.test(em)){{msg.textContent=box.dataset.bad;return}}
  var p=get("rd-profile"),ss=get("gf-shoe-size"),tables=[].slice.call(document.querySelectorAll("table[data-key]")),t=null,g=null,size=null;
  if(p&&p.sizes&&p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length){{g=p.gender||"any";
    t=tables.filter(function(x){{return x.dataset.g===g}})[0]||tables.filter(function(x){{return x.dataset.g==="unisex"}})[0]||tables[0]}}
  else if(ss&&ss.s){{g=ss.g;size=ss.s;var ti=ss.v?+ss.v.split("|")[0]:-1;t=tables[ti]||tables.filter(function(x){{return x.dataset.g===g}})[0]||tables[0]}}
  else{{msg.textContent=box.dataset.pick;var sel=document.querySelector("#mine select");if(sel){{sel.focus();sel.scrollIntoView({{block:"center"}})}}return}}
  var fr=document.documentElement.lang==="fr",us=/^\/us\//.test(location.pathname),tz=null;try{{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||null}}catch(x){{}}
  var ref=get("gf-ref");
  if(!(p&&p.sizes&&p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length)){{
    var G=["shoes","tops","bottoms","bras","socks","gloves","headwear","packs","gear","watches","nutrition"],sz={{shoes:{{sizes:[size],width:[]}}}};
    G.slice(1).forEach(function(k){{sz[k]={{sizes:[]}}}});
    p={{lang:fr?"fr":"en",country:us?"us":"ca",tz:tz,name:"",email:em,gender:g==="unisex"?"any":g,terrain:"both",ships:"ca",groups:G,sizes:sz,brands:[],activities:[]}};
    if(ref)p.ref=ref}}
  p.email=em;
  var mine=[].slice.call(t.querySelectorAll("tr.yours")).map(function(r){{return parseFloat(r.dataset.p)}}),
      all=[].slice.call(t.querySelectorAll("tr[data-p]")).map(function(r){{return parseFloat(r.dataset.p)}}),
      price=(mine.length?Math.min.apply(null,mine):Math.min.apply(null,all))||null,a=t.querySelector("a[data-store]");
  var meta={{b:t.dataset.b,n:t.dataset.n,g:"shoes",url:a?a.href:location.href,price:price,low:price,seen:price,gone:!mine.length&&!!size,saved:new Date().toISOString()}};
  var w=get("gf-watch")||{{}};w[t.dataset.key]=meta;
  var nw={{}};nw[t.dataset.key]=meta;var btn=f.querySelector("button");btn.disabled=true;
  fetch("{SB_URL}/rest/v1/rpc/subscribe",{{method:"POST",headers:{{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"}},
    body:JSON.stringify({{p_email:em,p_profile:Object.assign({{}},p,{{watch_new:nw}})}})}}).then(function(r){{if(!r.ok)throw 0;
    put("gf-watch",w);if(!get("rd-profile"))put("rd-profile",p);if(!(subd&&(subd.active||subd.key)))put("gf-sub",{{pending:em}});
    f.remove();msg.textContent=box.dataset.ok.replace("{{email}}",em);
    try{{ana("signup","shoe-page")}}catch(x){{}}try{{window.umami&&umami.track("signup",{{method:"email",where:"shoe-page",lang:fr?"fr":"en",ref:ref||"none"}})}}catch(x){{}}}})
  .catch(function(){{btn.disabled=false;msg.textContent=box.dataset.fail}})}})}})();
/* "Email me when it's back in my size" (Oct 27): pages with nothing in stock. The PAGE goes on the watchlist ("page|<slug>"); the
   morning alerts send "Back in your size" when any shoe on it is in their size again */
(function(){{var box=document.getElementById("backBox");if(!box)return;var f=box.querySelector("form"),msg=box.querySelector(".msg"),
  fit=box.querySelector("[data-fit]"),sz=box.querySelector("[data-size]"),K=box.dataset.key;
var get=function(k){{try{{return JSON.parse(localStorage.getItem(k)||"null")}}catch(e){{return null}}}},put=function(k,v){{try{{localStorage.setItem(k,JSON.stringify(v))}}catch(e){{}}}};
var subd=get("gf-sub"),w0=get("gf-watch")||{{}};if(subd&&(subd.active||subd.key)&&w0[K]){{f.remove();msg.textContent=box.dataset.done;return}}
var fill=function(){{var v=sz.value;sz.innerHTML=sz.options[0].outerHTML+(fit.value?(fit.value==="women"?sz.dataset.w:sz.dataset.m):"");sz.value=v}};
fit.addEventListener("change",fill);
var p0=get("rd-profile"),ss=get("gf-shoe-size"),g0=p0&&p0.gender==="women"?"women":p0&&p0.gender==="men"?"men":ss&&ss.g==="women"?"women":ss&&ss.g==="men"?"men":"",
  s0=(p0&&p0.sizes&&p0.sizes.shoes&&(p0.sizes.shoes.sizes||[])[0])||(ss&&ss.s)||"";
if(g0){{fit.value=g0;fill();if(s0)sz.value=String(parseFloat(String(s0).replace(/^[MW]:/,"")))}}
/* Oct 27 (Bastien: "wouldn't we know which size they clicked already"): sizes saved on this phone (main site or another shoe page)
   = one line "Men's 11 · Change" instead of the two boxes */
if(fit.value&&sz.value){{var bor=box.querySelector(".bor"),ln=document.createElement("p");ln.className="bok";
  ln.innerHTML=fit.options[fit.selectedIndex].text+" "+sz.value+' · <button type="button">'+box.dataset.chg+"</button>";bor.hidden=true;bor.parentNode.insertBefore(ln,bor);
  ln.querySelector("button").addEventListener("click",function(){{ln.remove();bor.hidden=false}})}}
f.addEventListener("submit",function(e){{e.preventDefault();
  var em=f.querySelector("input").value.trim().replace(/^mailto:/i,"").replace(/^.*<([^>]+)>.*$/,"$1").replace(/\s+/g,"").replace(/\.+$/,"");
  if(!fit.value||!sz.value){{msg.textContent=box.dataset.pick;return}}
  if(!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{{2,}}$/.test(em)||/\.\./.test(em)){{msg.textContent=box.dataset.bad;return}}
  var fr=document.documentElement.lang==="fr",us=/^\/us\//.test(location.pathname),tz=null,ref=get("gf-ref");try{{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||null}}catch(x){{}}
  var p=get("rd-profile");
  if(!(p&&p.sizes&&p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length)){{
    var G=["shoes","tops","bottoms","bras","socks","gloves","headwear","packs","gear","watches","nutrition"],S={{shoes:{{sizes:[sz.value],width:[]}}}};
    G.slice(1).forEach(function(k){{S[k]={{sizes:[]}}}});
    p={{lang:fr?"fr":"en",country:us?"us":"ca",tz:tz,name:"",email:em,gender:fit.value,terrain:"both",ships:"ca",groups:G,sizes:S,brands:[],activities:[]}};if(ref)p.ref=ref}}
  p.email=em;
  var meta={{b:box.dataset.b,n:box.dataset.n,g:"shoes",url:location.href,price:null,low:null,seen:null,gone:true,saved:new Date().toISOString()}},nw={{}};nw[K]=meta;
  var w=get("gf-watch")||{{}};w[K]=meta;var btn=f.querySelector("button");btn.disabled=true;
  fetch("{SB_URL}/rest/v1/rpc/subscribe",{{method:"POST",headers:{{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"}},
    body:JSON.stringify({{p_email:em,p_profile:Object.assign({{}},p,{{watch_new:nw}})}})}}).then(function(r){{if(!r.ok)throw 0;
    put("gf-watch",w);if(!get("rd-profile"))put("rd-profile",p);if(!(subd&&(subd.active||subd.key)))put("gf-sub",{{pending:em}});
    f.remove();msg.textContent=box.dataset.ok.replace("{{email}}",em);
    try{{ana("signup","shoe-page-back")}}catch(x){{}}try{{window.umami&&umami.track("signup",{{method:"email",where:"shoe-page-back",lang:fr?"fr":"en",ref:ref||"none"}})}}catch(x){{}}}})
  .catch(function(){{btn.disabled=false;msg.textContent=box.dataset.fail}})}})}})();
/* wrong side (Oct 6, 2026): a visitor who picked USA on a Canadian page (or Canada on a US page) gets a bar to the same page
   on their side, when it exists (Google, old links and the menu's country link can lead to the other side) */
(function(){{var c=null;try{{c=JSON.parse(localStorage.getItem("gf-country")||"null")||(JSON.parse(localStorage.getItem("rd-profile")||"null")||{{}}).country||null}}catch(e){{}}
  if(!c){{try{{c=document.documentElement.lang==="fr"?"ca":/^(America\/(New_York|Detroit|Kentucky|Indiana|Chicago|Menominee|North_Dakota|Denver|Boise|Phoenix|Los_Angeles|Anchorage|Juneau|Sitka|Metlakatla|Yakutat|Nome|Adak)|Pacific\/Honolulu)/.test(Intl.DateTimeFormat().resolvedOptions().timeZone||"")?"us":"ca"}}catch(e){{}}}}   /* first visit from Reddit/Google: the device's time zone, like the homepage (Oct 6) */
  var path=location.pathname,us=/^\/us\//.test(path);if(!c||(c==="us")===us)return;
  var to=us?path.replace(/^\/us\//,"/"):"/us"+path.replace(/^\/chaussures\//,"/shoes/").replace(/^\/chaussures-course-solde\/.*$/,"/running-shoes-sale/").replace(/^\/marques\//,"/brands/").replace(/^\/vendredi-fou\//,"/black-friday/").replace(/^\/courses\//,"/races/");   /* race lists (Oct 21) */
  var fr=document.documentElement.lang==="fr";
  var show=function(u){{var b=document.createElement("p");b.className="side";
    b.innerHTML=(us?"These prices are from US stores. ":fr?"Ces prix viennent de boutiques canadiennes. ":"These prices are from Canadian stores. ")+'<a href="'+u+'">'+(us?"See Canadian stores →":fr?"Voir les boutiques américaines →":"See US stores →")+"</a>";
    var m=document.querySelector("main.wrap");if(m)m.insertBefore(b,m.firstChild)}};
  fetch(to,{{method:"HEAD"}}).then(function(r){{show(r.ok?to:(us?"/shoes/":"/us/shoes/"))}}).catch(function(){{}})}})();
/* Oct 11 (Bastien: "optimize to have retention, not just a pathway to another website"). 1) Shoe pages: back from a store without
   buying = the moment to offer the price-drop email; a bottom bar sends the shoe page's own "Email me" form (once per visit, never to
   members, × = not again for 7 days). 2) Black Friday + sale-list pages: fit + shoe size + email, right on the page. */
(function(){{var box=document.getElementById("alertBox");if(!box||!box.dataset.backh)return;
var get=function(k){{try{{return JSON.parse(localStorage.getItem(k)||"null")}}catch(e){{return null}}}};
var sub=get("gf-sub");if(sub&&(sub.active||sub.key||sub.pending))return;
try{{var no=+localStorage.getItem("gf-backno")||0;if(no&&Date.now()-no<7*864e5)return;if(sessionStorage.getItem("gf-backshown"))return}}catch(e){{}}
var away=0,shown=false;
var show=function(){{var bf=box.querySelector("form");if(shown||!bf)return;shown=true;try{{sessionStorage.setItem("gf-backshown","1")}}catch(e){{}}
  var bar=document.createElement("div");bar.className="backbar";bar.setAttribute("role","dialog");
  bar.innerHTML='<div class="in"><b></b><p></p><form novalidate><input type="email" autocomplete="email" inputmode="email" aria-label="Email" required><button type="submit"></button></form></div><button type="button" class="x"></button>';
  bar.querySelector("b").textContent=box.dataset.backh;bar.querySelector("p").textContent=box.dataset.backtxt;
  bar.querySelector("form button").textContent=box.dataset.backbtn;var x=bar.querySelector(".x");x.textContent="×";x.setAttribute("aria-label",box.dataset.backno);
  bar.querySelector("input").placeholder=box.querySelector("input").placeholder;
  var pr=get("rd-profile"),ss0=get("gf-shoe-size"),ms=document.querySelector("#mine select"),bs=null;   // no size yet: pick it in the bar
  if(!(pr&&pr.sizes&&pr.sizes.shoes&&(pr.sizes.shoes.sizes||[]).length)&&!(ss0&&ss0.s)&&ms){{bs=ms.cloneNode(true);bs.value="";bs.className="bsel";
    bs.setAttribute("aria-label",(document.querySelector("#mine .pickl")||{{}}).textContent||"Size");bar.querySelector("form").insertBefore(bs,bar.querySelector("input"))}}
  document.body.appendChild(bar);
  try{{ana("signup-step","shoe-backbar-view")}}catch(e){{}}
  x.addEventListener("click",function(){{bar.remove();try{{localStorage.setItem("gf-backno",String(Date.now()))}}catch(e){{}}try{{ana("signup-step","shoe-backbar-close")}}catch(e){{}}}});
  var msg=box.querySelector(".msg");
  new MutationObserver(function(){{var t=msg.textContent;if(!t)return;
    if(!box.querySelector("form")){{bar.querySelector("p").textContent=t;var f2=bar.querySelector("form");if(f2)f2.remove();setTimeout(function(){{bar.remove()}},6000)}}
    else if(t===box.dataset.pick)bar.remove();else bar.querySelector("p").textContent=t}}).observe(msg,{{childList:true,characterData:true,subtree:true}});
  bar.querySelector("form").addEventListener("submit",function(e){{e.preventDefault();var bf2=box.querySelector("form");if(!bf2)return;
    if(bs){{if(!bs.value){{bar.querySelector("p").textContent=box.dataset.pick;bs.focus();return}}var ms2=document.querySelector("#mine select");
      if(ms2){{ms2.value=bs.value;ms2.dispatchEvent(new Event("change"))}}}}
    bf2.querySelector("input").value=bar.querySelector("input").value;try{{ana("signup-step","shoe-backbar-send")}}catch(x2){{}}
    if(bf2.requestSubmit)bf2.requestSubmit();else bf2.dispatchEvent(new Event("submit",{{cancelable:true}}))}})}};
document.addEventListener("click",function(e){{if(!e.target.closest("a[data-store]"))return;away=Date.now();
  setTimeout(function(){{if(document.visibilityState==="visible")show()}},4000)}});
document.addEventListener("visibilitychange",function(){{if(document.visibilityState==="visible"&&away&&Date.now()-away>1500)show()}})}})();
(function(){{var box=document.getElementById("qsBox");if(!box)return;var f=box.querySelector("form"),msg=box.querySelector(".msg"),g=f.querySelector(".qsg"),s=f.querySelector(".qss");
var get=function(k){{try{{return JSON.parse(localStorage.getItem(k)||"null")}}catch(e){{return null}}}},put=function(k,v){{try{{localStorage.setItem(k,JSON.stringify(v))}}catch(e){{}}}};
var sub=get("gf-sub");if(sub&&(sub.active||sub.key)){{box.remove();return}}
var showG=function(){{[].forEach.call(s.querySelectorAll("optgroup"),function(o){{var on=o.dataset.g===g.value;o.hidden=!on;o.disabled=!on}});
  var o=s.selectedOptions[0];if(o&&o.parentNode&&o.parentNode.disabled)s.value=""}};
var p0=get("rd-profile"),ss=get("gf-shoe-size");
if(ss&&ss.s){{g.value=ss.g==="women"?"women":"men";showG();s.value=String(ss.s)}}else if(p0&&p0.gender==="women"){{g.value="women";showG()}}
g.addEventListener("change",showG);
f.addEventListener("submit",function(e){{e.preventDefault();
  var em=f.querySelector("input").value.trim().replace(/^mailto:/i,"").replace(/^.*<([^>]+)>.*$/,"$1").replace(/\s+/g,"").replace(/\.+$/,"");
  if(!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{{2,}}$/.test(em)||/\.\./.test(em)){{msg.textContent=box.dataset.bad;return}}
  if(!s.value){{msg.textContent=box.dataset.pick;s.focus();return}}
  var fr=document.documentElement.lang==="fr",us=/^\/us\//.test(location.pathname),tz=null;try{{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||null}}catch(x){{}}
  var G=["shoes","tops","bottoms","bras","socks","gloves","headwear","packs","gear","watches","nutrition"],p;
  if(p0&&p0.sizes){{p=JSON.parse(JSON.stringify(p0));if(!(p.sizes.shoes&&(p.sizes.shoes.sizes||[]).length))p.sizes.shoes={{sizes:[s.value],width:[]}}}}
  else{{var sz={{shoes:{{sizes:[s.value],width:[]}}}};G.slice(1).forEach(function(k){{sz[k]={{sizes:[]}}}});
    p={{lang:fr?"fr":"en",country:us?"us":"ca",tz:tz,name:"",gender:g.value,terrain:"both",ships:"ca",groups:G,sizes:sz,brands:[],activities:[]}}}}
  p.email=em;if(!p.ref)p.ref=get("gf-ref")||box.dataset.ref;var btn=f.querySelector("button");btn.disabled=true;
  fetch("{SB_URL}/rest/v1/rpc/subscribe",{{method:"POST",headers:{{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"}},
    body:JSON.stringify({{p_email:em,p_profile:p}})}}).then(function(r){{if(!r.ok)throw 0;
    put("gf-sub",{{pending:em}});if(!p0)put("rd-profile",p);put("gf-shoe-size",{{g:g.value,s:s.value}});
    f.remove();msg.textContent=box.dataset.ok.replace("{{email}}",em);
    try{{ana("signup",box.dataset.ref)}}catch(x){{}}try{{window.umami&&umami.track("signup",{{method:"email",where:box.dataset.ref,lang:fr?"fr":"en"}})}}catch(x){{}}}})
  .catch(function(){{btn.disabled=false;msg.textContent=box.dataset.fail}})}})}})();
document.addEventListener("click",function(e){{var a=e.target.closest("a[data-store]");if(!a)return;
try{{fetch("{SB_URL}/rest/v1/rpc/log_event",{{method:"POST",keepalive:true,headers:{{apikey:"sb_publishable_zRrZ7lk8fCbjdTV3tgVD5g_PtxgHOD2","Content-Type":"application/json"}},
body:JSON.stringify({{p_kind:"click",p_store:a.dataset.store,p_group:"shoes",p_ref:"shoe-page",p_lang:"{L['lang'][:2]}"}})}})}}catch(x){{}}
try{{window.umami&&umami.track("deal-click",{{store:a.dataset.store,from:"shoe-page"}})}}catch(x){{}}
try{{var tr=a.closest("tr"),rp=location.pathname.match(/^\/(?:us\/)?(?:races|courses)\/([^\/]+)\//),gi=a.closest(".gi");   /* race lists: "race|<race>|<item>" */
  ana("deal-click",rp?a.dataset.store+"|"+(gi?gi.dataset.k:"")+"||race|"+rp[1]:a.dataset.store+"|shoes||shoe-page",tr?[].indexOf.call(tr.parentNode.children,tr)+1:null)}}catch(x){{}}}});
</script>
</body>
</html>
"""


def sizes_phrase(keys, L):
    """["4.5", "5"] -> "sizes 4.5 and 5" / « pointures 4,5 et 5 »; "M:9" -> "M 9", "W:10" -> "W 10" (as the tables say)."""
    fr = L["lang"] == "fr-CA"
    labs = []
    for k in keys:
        k = str(k)
        wide = k.endswith("~W")
        k = k.replace("~W", "")
        k = re.sub(r"^M:", "H " if fr else "M ", re.sub(r"^W:", "F " if fr else "W ", k))
        k = (k.replace(".", ",") if fr else k) + ((" large" if fr else " wide") if wide else "")
        labs.append(k)
    labs = list(dict.fromkeys(labs))
    def order(k):                              # "11" before "11 wide"; men's/women's letters kept together
        m = re.search(r"(\d+(?:[.,]\d)?)", k)
        return (k[:1] if k[:1].isalpha() else "", float(m.group(1).replace(",", ".")) if m else 99, k.endswith(("wide", "large")))
    labs.sort(key=order)
    if not labs:
        return ""
    if len(labs) > 4:
        nums = []
        for k in labs:
            try:
                nums.append(float(k.replace(",", ".")))
            except ValueError:
                break
        if len(nums) == len(labs):             # "sizes 7–10" / « pointures 7 à 10 »
            f = lambda x: (f"{x:g}".replace(".", ",") if fr else f"{x:g}")
            n = len(labs)
            return f"{n} pointures, de {f(min(nums))} à {f(max(nums))}" if fr else f"{n} sizes from {f(min(nums))} to {f(max(nums))}"
        return f"{len(labs)} pointures" if fr else f"{len(labs)} sizes"
    one, many, and_ = ("pointure", "pointures", " et ") if fr else ("size", "sizes", " and ")
    return f"{one} {labs[0]}" if len(labs) == 1 else f"{many} " + ", ".join(labs[:-1]) + and_ + labs[-1]


def low_days(its):
    """Oct 23 (Black Friday "is this deal real?"; Bastien OK'd): the homepage badge's rule for a list of versions: today's best
    price is the lowest in 30+ days of our own history AND the price was at least 2% higher in that window (a real drop, not a
    price that never moved). Returns the days (max 60) or 0. Good news only: nothing is ever labelled "fake"."""
    lows = [d for d in its if d.get("hd", 0) >= HISTORY_DAYS and d.get("lo") is not None and d.get("sz")
            and min(e[1] for e in d["sz"]) <= d["lo"] + 0.01 and (d.get("hi") or 0) > min(e[1] for e in d["sz"]) * 1.02]
    return min(60, max(d["hd"] for d in lows)) if lows else 0


def summary(its, stores, gender=None):
    """Today's numbers for one model (optionally one gender): best price, its discount, store, sizes, stores."""
    sizes, by_store, best = 0, defaultdict(set), None
    # Oct 23 (Evo SL ATR's women's line said "sizes M 7 and M 13"): a unisex shoe's men's sizes ("M:7") never count for women, nor "W:" for men
    cut = lambda e: not gender or not str(e[0]).startswith({"women": "M:", "men": "W:"}.get(gender, "\0"))
    for d in its:
        sx = d.get("sx") or []
        if gender and sx and gender not in sx:
            continue
        for e in d["sz"]:
            if str(e[0]).endswith("~N") or not cut(e):
                continue
            u = size_url(d, e)
            h = host(u)
            by_store[h].add((tuple(sx), str(e[0]), bool(d.get("w"))))
            reg = e[3] if len(e) > 3 else e[1]
            if best is None or e[1] < best[0]:
                best = (e[1], reg, h, u, tuple(sx))
    if not best:
        return None
    sizes = len({x for v in by_store.values() for x in v})
    carriers = {host(u) for d in its if not (gender and d.get("sx") and gender not in d["sx"]) for u in d["of"]}   # every store that carries it
    off = round(100 * (1 - best[0] / best[1])) if best[1] and best[0] < best[1] * 0.99 else 0
    top = max((round(100 * (1 - e[1] / e[3])) for d in its for e in d["sz"] if len(e) > 3 and e[1] < e[3] * 0.99 and cut(e)
               and (not gender or not d.get("sx") or gender in d["sx"])), default=0)
    most = max(by_store.items(), key=lambda kv: len(kv[1]))
    sale_sizes = len({(tuple(d.get("sx") or []), str(e[0]), bool(d.get("w"))) for d in its for e in d["sz"] if len(e) > 3 and e[1] < e[3] * 0.99
                      and cut(e) and (not gender or not d.get("sx") or gender in d["sx"])})
    # Oct 16 (Bastien couldn't find the $99 Kjerag: it was only in sizes 4.5 and 5): the sizes at that lowest price
    at_best = list(dict.fromkeys(str(e[0]) for d in its for e in d["sz"] if abs(e[1] - best[0]) < 0.005
                                 and not str(e[0]).endswith("~N") and cut(e) and host(size_url(d, e)) == best[2]
                                 and (not gender or not d.get("sx") or gender in d["sx"])
                                 and (len(best[4]) != 1 or (d.get("sx") or []) == list(best[4]))))   # that cut's sizes only
    return {"price": best[0], "reg": best[1], "off": off, "top": top, "store": stores.get(best[2], [best[2]])[0], "url": best[3],
            "sizes": sizes, "stores": len(carriers), "sale_sizes": sale_sizes, "best_sizes": at_best,
            "lowd": low_days([d for d in its if (not gender or not d.get("sx") or gender in d["sx"]) and d.get("sz")
                              and abs(min(e[1] for e in d["sz"]) - best[0]) < 0.01]) if off >= 10 else 0,   # the version at that price
            "best_sx": best[4][0] if len(best[4]) == 1 else None,
            "most": stores.get(most[0], [most[0]])[0], "most_n": len(most[1]),
            "img": next((d["img"] for d in its if d.get("img")), None), "t": its[0].get("t") or ""}


# Size pages (Oct 14, 2026; Bastien: "how do we dominate the SEO space"): "men's size 11 running shoes on sale" is what people
# type, and in-your-size is what only we can answer. One page per size, every price is the price in THAT size.
SIZES = {"men": [x / 2 for x in range(14, 27)] + [14.0], "women": [x / 2 for x in range(10, 23)]}


def size_slug(L, s):
    return f'{L["sizeDir"]}-{s:g}'.replace(".", "-")


def size_path(L, g, s):
    return f'/{L["hubDir"]}/{L["hubSlugs"][g]}/{size_slug(L, s)}/'


def size_summary(its, stores, gender, size):
    """Today's best sale price for one model in one size (regular width): (price, regular, store, %off) or None."""
    best = None
    for d in its:
        sx = d.get("sx") or []
        for e in d["sz"]:
            k = str(e[0])
            if k.endswith(("~N", "~W")):
                continue
            if k.startswith("M:"):
                if gender != "men":
                    continue
                k = k[2:]
            elif k.startswith("W:"):
                if gender != "women":
                    continue
                k = k[2:]
            elif gender == "women" and sx != ["women"]:
                continue                       # plain sizes on a unisex shoe are men's sizes
            elif gender == "men" and sx == ["women"]:
                continue
            try:
                if float(k) != size:
                    continue
            except ValueError:
                continue
            reg = e[3] if len(e) > 3 and e[3] else e[1]
            if e[1] >= reg * 0.99:
                continue
            if best is None or e[1] < best[0]:
                best = (e[1], reg, host(size_url(d, e)))
    if not best:
        return None
    return {"price": best[0], "reg": best[1], "top": round(100 * (1 - best[0] / best[1])), "sizes": 1, "stores": 1,
            "note": stores.get(best[2], [best[2]])[0], "img": next((d["img"] for d in its if d.get("img")), None)}


def size_nav(L, g, current=None):
    """Links to every size of one gender (and the other gender's sizes), so Google finds them all."""
    other = "women" if g == "men" else "men"
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{size_path(L, g, s)}"{cur if s == current else ""}>{s:g}</a>' for s in SIZES[g])
    return (f'<nav class="browse sizes" aria-label="{esc(L["sizeNav"])}"><strong>{esc(L["sizeOther"].format(g=L["gWord"][g]))}</strong> {links}</nav>'
            f'<p class="fine"><a href="{size_path(L, other, SIZES[other][len(SIZES[other]) // 2])}">{esc(L["sizeOther"].format(g=L["gWord"][other]))} →</a></p>')


def size_pages(site, L, models, live, stores, brands, twin=None):
    """Writes every size page for one language/side; twin(L2, g, s) gives the other-language address. Returns the URLs."""
    urls = []
    for g in ("men", "women"):
        for size in SIZES[g]:
            rows = []
            for sl in live:
                if models.get(sl):
                    sm = size_summary(models[sl], stores, g, size)
                    if sm and sm["top"] >= 10:
                        sm["note"] = L["sizeAt"].format(store=sm["note"])
                        rows.append((sl, live[sl]["n"], sm))
            rows.sort(key=lambda r: (-r[2]["top"], r[2]["price"]))
            own = size_path(L, g, size)
            en_p, fr_p = twin(g, size) if twin else (own, "")
            gw, sz = L["gWord"][g], f"{size:g}"
            p = site / own.strip("/") / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(list_page(L, en_p, fr_p, L["sizeTitle"].format(g=gw, s=sz, n=len(rows)), L["sizeH1"].format(g=gw, s=sz),
                                   L["sizeIntro"].format(g=gw.lower() if L.get("lang", "").startswith("en") else gw, s=sz, n=len(rows)),
                                   rows[:80], brands, size_nav(L, g, size), after=qs_box(L, L["qsHub"], "size-page")))
            urls.append(own)
    return urls


# Price history chart (Oct 14, 2026; Bastien: "how do we dominate the SEO space"): the lowest price per day for each version
# (men's / women's), from the price history on the history branch. Information other sites don't have, and the answer to
# "is this a real deal?" before Black Friday. Drawn as plain SVG on the server: readable without scripts, light in both themes.
HIST = {}
MONTHS = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
          "fr": "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()}


def load_history(path):
    try:
        for line in Path(path).read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                HIST[row["k"]] = row["h"]
    except Exception:
        pass
    return len(HIST)


def short_date(d, L):
    fr = L["lang"] == "fr-CA"
    return f"{d.day} {MONTHS['fr'][d.month - 1]}" if fr else f"{MONTHS['en'][d.month - 1]} {d.day}"


def price_chart(its, L, updated, prefix=""):
    """One small step chart per version (men's / women's / unisex), regular width only; "" until 7+ days of history."""
    today = (datetime.fromisoformat(updated.replace("Z", "+00:00")) if updated else datetime.now(timezone.utc)).astimezone(HOME_TZ).date()
    scale = L.get("fx", 1.0) if prefix else 1.0          # the USA side's history is in USD; L["money"] expects CAD
    money = L["money"]
    groups = defaultdict(list)
    for d in its:
        if d.get("w"):
            continue
        h = HIST.get(prefix + f"{d['b']}|{d['n']}|{d['g']}|0".lower())
        if h:
            groups[variant_label(d, L)].append(sorted(h))
    blocks = []
    for lab, hs in groups.items():
        start = max(min(date.fromisoformat(h[0][0]) for h in hs), today - timedelta(days=59))
        days = [start + timedelta(days=i) for i in range((today - start).days + 1)]
        if len(days) < 7:
            continue
        vals = []
        for day in days:
            best = None
            for h in hs:
                v = None
                for dd, p, _ in h:
                    if date.fromisoformat(dd) <= day:
                        v = p
                    else:
                        break
                if v is not None and (best is None or v < best):
                    best = v
            vals.append(None if best is None else best * scale)
        pts = [(i, v) for i, v in enumerate(vals) if v is not None]
        if len(pts) < 7:
            continue
        lo_i, lo = min(pts, key=lambda t: (t[1], -t[0]))         # the most recent day at the lowest price
        now = pts[-1][1]
        if now <= lo:                                              # good news only: today is the lowest, 30+ days (badge rule)
            if len(days) >= 30 and max(v for _, v in pts) > now * 1.02:
                blocks.append((lab, "good", "✓ " + L["pwLow"].format(n=min(len(days), 60), today=money(now))))
        elif lo < now * 0.95:                                      # it was cheaper: "don't miss the next one" + the email box
            blocks.append((lab, "was", L["pwWas"].format(low=money(lo), date=short_date(days[lo_i], L), now=money(now))))
    if not blocks:
        return {}, ""
    # Oct 18 (spy-shopper pass: a women's visitor read the men's price line under the women's table): each version's line goes
    # under its own table; when men's and women's say the same, one line after all the tables
    same = len(blocks) > 1 and len({(k, t) for _, k, t in blocks}) == 1
    btn = f'<a class="pwbtn" href="#alertBox">{esc(L["pwBtn"])}</a>' if any(k == "was" for _, k, _ in blocks) else ""
    if same:          # (one version only: its line goes under its own table, below)
        lab, k, t = blocks[0]
        return {}, f'<section class="pws"><p class="pw {k}">{esc(t)}</p>{btn}</section>'
    return {lab: f'<section class="pws"><p class="pw {k}">{esc(t)}</p>{btn}</section>' for lab, k, t in blocks}, ""


def model_page(slug, its, stores, L, updated, related, brand_models, paths=None, brand_pages=(), hide=False):
    first = its[0]
    brand = first["b"]
    name = f"{brand} {(hike_name if L.get('hike') else base_model)(first['n'])}"
    path_en, path_fr = paths or (f"/shoes/{slug}/", f"/chaussures/{slug}/")
    money = L["money"]
    # every variant (men's, women's, wide…) with its sizes
    groups = []
    for d in sorted(its, key=lambda d: ({"men": 0, "women": 1}.get((d.get("sx") or ["u"])[0], 2) if len(d.get("sx") or []) == 1 else 2, bool(d.get("w")))):
        rows = rows_for(d, stores, L)
        if rows:
            groups.append((variant_label(d, L), rows, d))
    merged, first = defaultdict(list), {}  # two items with the same label (e.g. GTX folded in elsewhere) share one table
    for lab, rows, d in groups:
        merged[lab].extend(rows)
        first.setdefault(lab, d)
    # Oct 26: the page's photo (hero + Google's product data); `first` above is per table, so the photo comes from the items
    # (it read first["img"] on that dict and never found one: no shoe page had a photo)
    photo = next((d["img"] for _, _, d in groups if d.get("img")), "") or next((d["img"] for d in its if d.get("img")), "")
    allrows = [r for _, rows in merged.items() for r in rows]
    sale = [r for _, r in allrows if r[0] < r[1] * 0.99]
    best = min(allrows, key=lambda kv: kv[1][0])[1] if allrows else None
    top = max((round(100 * (1 - p / r)) for p, r, *_ in sale), default=0)
    n_stores = len({host(u) for d in its for u in d["of"]})          # every store that carries it, not just the cheapest
    sm = summary(its, stores) if any(d["sz"] for d in its) else None
    title = (L["titleSale"].format(name=name, price=money(sm["price"]), p=sm["off"]) if sm and sm["off"] >= 10
             else L["title"].format(name=name))
    desc = L["desc"].format(name=name, n=n_stores, off=L["descOff"].format(p=top) if top >= 10 else "")
    ld = ""
    if best:
        lo_p, hi_p = min(r[0] for _, r in allrows), max(r[0] for _, r in allrows)
        ld = json.dumps({"@context": "https://schema.org", "@type": "Product", "name": name, "brand": {"@type": "Brand", "name": brand},
                         **({"image": photo} if photo else {}),
                         "offers": {"@type": "AggregateOffer", "priceCurrency": L["cur"], "lowPrice": f"{lo_p / L.get('fx', 1):.2f}", "highPrice": f"{hi_p / L.get('fx', 1):.2f}",
                                    "offerCount": len(allrows), "availability": "https://schema.org/InStock"}}, ensure_ascii=False)
        ld = f'<script type="application/ld+json">{ld}</script>'
    elif hide:   # Oct 24 (Bastien OK'd): nothing in stock for 14+ days = kept out of Google until it's back (the page stays for visitors)
        ld = '<meta name="robots" content="noindex,follow">'
        NOINDEX.add(path_fr if L["lang"] == "fr-CA" else path_en)    # this page only (a US page names its Canadian twin)
    out = [page_head(L, title, desc, path_en, path_fr, ld)]
    # the brand links to its brand page (when there is one): our own links tell Google which pages matter
    bl = f'<a href="/{L["brandDir"]}/{slugify(brand)}/">{esc(brand)}</a>' if brand in brand_pages else esc(brand)
    out.append(f'<p class="crumbs"><a href="/{L["dir"]}/">{L["all"]}</a> › {bl}</p>')
    out.append(f'<h1>{esc(name)}</h1><p class="sub">{L["h1sub"]}</p>')
    t = L["types"].get(first.get("t") or "", "")
    if best:
        p, reg = best[0], best[1]
        off = round(100 * (1 - p / reg)) if reg and p < reg * 0.99 else 0
        line = L["from"].format(price=money(p), reg=money(reg), p=off) if off else L["fromFull"].format(price=money(p))
        # "Is this deal real?": good news only (Bastien's call): the best price today is the lowest in 30+ days of history
        lows = [d for d in its if d.get("hd", 0) >= HISTORY_DAYS and d.get("lo") is not None and min(e[1] for e in d["sz"]) <= d["lo"] + 0.01 and (d.get("hi") or 0) > min(e[1] for e in d["sz"]) * 1.02]   # a real drop
        badge = f'<span class="badge">{L["low"].format(d=min(60, max(d["hd"] for d in lows)))}</span>' if lows and off else ""   # 60-day window
        img = f'<img src="{esc(photo)}" alt="{esc(name)}" loading="lazy" referrerpolicy="no-referrer">' if photo else ""
        out.append(f'<div class="hero">{img}<div>{f"<span class=tag>{esc(t)}</span>" if t else ""}<p>{line}</p>{badge}'
                   f'<p class="facts">{L["facts"].format(sizes=len(allrows), stores=n_stores, date=fmt_date(updated, L))}</p></div></div>')
    else:
        out.append(f'<div class="hero"><div>{f"<span class=tag>{esc(t)}</span>" if t else ""}<p>{L["none"]}</p></div></div>')
        # Oct 27 (Bastien OK'd idea 1: ~114 shoe pages say "Not in stock"; shoe pages bring most sign-ups): watch the PAGE ("page|<slug>",
        # alerts.py matches any shoe on it in their size) and get the "Back in your size" email when a store has it again
        if not L.get("hike"):
            zs = lambda a, b: "".join(f'<option value="{z:g}">{z:g}</option>' for z in [x / 2 for x in range(a * 2, b * 2 + 1)])
            out.append(f'<section class="alert boback" id="backBox" data-key="page|{esc(slug)}" data-b="{esc(brand)}" data-n="{esc(name)}" '
                       f'data-pick="{esc(L["boPick"])}" data-chg="{esc(L["change"])}" data-bad="{esc(L["alertBad"])}" data-ok="{esc(L["alertOk"])}" data-fail="{esc(L["alertFail"])}" data-done="{esc(L["alertDone"])}">'
                       f'<h2>{esc(L["boH"].format(name=name))}</h2><p class="fine">{L["boTxt"]}</p><form novalidate><div class="bor">'
                       f'<select data-fit aria-label="{esc(L["boFit"])}"><option value="">{esc(L["boFit"])}</option><option value="men">{esc(L["boMen"])}</option><option value="women">{esc(L["boWomen"])}</option></select>'
                       f'<select data-size aria-label="{esc(L["boSize"])}" data-m="{esc(zs(6, 15))}" data-w="{esc(zs(5, 12))}"><option value="">{esc(L["boSize"])}</option></select></div>'
                       f'<input type="email" autocomplete="email" inputmode="email" placeholder="{esc(L["emailPh"])}" aria-label="Email" required>'
                       f'<button type="submit">{L["alertBtn"]}</button></form><p class="msg" aria-live="polite"></p></section>')
    # "your size": the page reads the sizes saved on this phone (main site) and highlights them (script at the end)
    out.append(f'<div class="mine" id="mine" hidden data-your="{esc(L["yourSize"])}" data-at="{esc(L["at"])}" data-see="{esc(L["see"])}" '
               f'data-none="{esc(L["notInSize"])}" data-pick="{esc(L["pick"])}" data-pickph="{esc(L["pickPh"])}" data-chg="{esc(L["change"])}" '
               f'data-all="{esc(L["allInSize"])}" data-home="/?ref=shoe-size{L["q"]}"></div>')
    # Oct 8 (funnel: 209 first visits from Google in 14 days, 11% reached the homepage, no way to sign up here): sign up right here
    if any(first[lab].get("of") for lab in merged):
        out.append(f'<section class="alert" id="alertBox" data-pick="{esc(L["alertPick"])}" data-bad="{esc(L["alertBad"])}" data-ok="{esc(L["alertOk"])}" '
                   f'data-fail="{esc(L["alertFail"])}" data-done="{esc(L["alertDone"])}" data-backh="{esc(L["backH"])}" '
                   f'data-backtxt="{esc(L["backTxt"].format(name=name))}" data-backbtn="{esc(L["backBtn"])}" data-backno="{esc(L["backNo"])}">'
                   f'<h2>{esc(L["alertH"].format(name=name))}</h2><p class="fine">{L["alertTxt"]}</p>'
                   f'<form novalidate><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(L["emailPh"])}" aria-label="Email" required>'
                   f'<button type="submit">{L["alertBtn"]}</button></form><p class="msg" aria-live="polite"></p></section>')
    lang_q = L["q"]
    per_pw, all_pw = price_chart(its, L, updated, "us|" if L.get("dir", "").startswith("us/") else "")
    out.append('<div class="gts">')      # the visitor's own cut moves first (script below: CSS order, the tables keep their DOM order)
    for lab, rows in merged.items():
        d0 = first[lab]
        sx = d0.get("sx") or []
        tg = "men" if sx == ["men"] else "women" if sx == ["women"] else "unisex"
        key = f'{d0["b"]}|{d0["n"]}|{d0["g"]}|{1 if d0.get("w") else 0}'.lower()          # the site's itemKey()
        watch = f'<a class="watch" href="/?watch={quote(key)}{lang_q}" rel="nofollow">♡ {L["watch"]}</a>' if d0.get("of") else ""
        rows = sorted({k: v for k, v in rows}.items(), key=lambda kv: size_sort(kv[0]))
        out.append(f'<div class="gt" data-g="{tg}"><div class="th2"><h2>{esc(lab)}</h2>{watch}</div><table data-g="{tg}" data-w="{1 if d0.get("w") else 0}" data-key="{esc(key)}" data-b="{esc(d0["b"])}" data-n="{esc(d0["n"])}"><thead><tr><th>{L["size"]}</th><th>{L["price"]}</th><th>{L["store"]}</th></tr></thead><tbody>')
        for size, (p, reg, h, u, fin) in rows:
            off = round(100 * (1 - p / reg)) if reg and p < reg * 0.99 else 0
            st = stores.get(h, [h])
            ab = L["abroad"](st)
            us = f'<span class="us">{ab}</span>' if ab else ""
            fin = f'<span class="fin">{L["final"]}</span>' if fin else ""
            price = f'<b>{money(p)}</b>' + (f'<s>{money(reg)}</s><span class="off">−{off}%</span>' if off else "")
            out.append(f'<tr data-s="{esc(size)}" data-p="{p:.2f}"><td>{esc(size)}</td><td class="p">{price}</td><td><a href="{esc(u)}" rel="nofollow noopener" target="_blank" data-store="{esc(h)}">{esc(st[0])}</a>{us}{fin}</td></tr>')
        out.append("</tbody></table>" + per_pw.get(lab, "") + "</div>")
    out.append("</div>" + all_pw)
    # Oct 22 (daily review: 42% of first visits land here, 5% go on to another page, 3% come back): test 'alts' (B) shows other
    # shoes of the same kind on sale in the visitor's size, from the file alt_file() writes; the script below fills it
    kind = first_t if (first_t := (its[0].get("t") or "daily")) in L["altH"] else "daily"
    out.append(f'<section class="alts" id="alts" hidden data-t="{kind}" data-src="/{L["dir"]}/alts.json" data-slug="{slug}" data-b="{esc(brand)}" '
               f'data-dir="/{L["dir"]}/" data-h="{esc(L["altH"][kind])}" data-h0="{esc(L["altH0"][kind])}" data-in="{esc(L["altIn"])}" '
               f'data-n="{esc(L["altN"])}" data-fr="{1 if L["lang"] == "fr-CA" else 0}"><h2></h2><div class="altw"><button type="button" class="arr l" aria-label="‹" disabled>‹</button><div class="altrow"></div><button type="button" class="arr r" aria-label="›">›</button></div></section>')
    if sm:     # a few lines Google (and people) can read: what it is, where it's cheapest, sizes, today's answers
        about = L["about"].format(name=esc(name), type=L["typeLower"].get(sm["t"], L["typeLower"][""]), stores=sm["stores"], sizes=sm["sizes"])
        bsz = sizes_phrase(sm.get("best_sizes") or [], L)
        g1 = sm.get("best_sx")
        if bsz and g1 and any(d.get("sx") == [("women" if g1 == "men" else "men")] for d in its):   # both cuts exist: say whose sizes
            bsz = f"{bsz} {L['gWord'][g1]}" if L["lang"] == "fr-CA" else f"{L['gLab'][g1].lower()}: {bsz}"
        bsz = esc(bsz)
        about += L["aboutBest"].format(price=money(sm["price"]), store=esc(sm["store"]), bsizes=bsz).replace(" ()", "")
        if sm["most"] != sm["store"] and sm["stores"] > 1:
            about += L["aboutMost"].format(store=esc(sm["most"]), n=sm["most_n"])
        ranges = []
        for lab, rows in merged.items():
            nums = sorted({float(m.group(1)) for k, _ in rows for m in [re.match(r"(?:W )?(\d+(?:\.5)?)", k)] if m})
            if nums:
                fr = L["lang"] == "fr-CA"
                f = lambda x: f"{x:g}".replace(".", ",") if fr else f"{x:g}"
                c = " : " if fr else ": "
                ranges.append(f"{lab}{c}{f(nums[0])}–{f(nums[-1])}" if len(nums) > 1 else f"{lab}{c}{f(nums[0])}")
        ans_sale = (L["aSaleYes"].format(p=sm["top"], price=money(sm["price"]), store=esc(sm["store"]), n=sm["sale_sizes"], bsizes=bsz) if sm["top"] >= 5
                    else L["aSaleNo"].format(price=money(sm["price"])))
        # Oct 16 (Bastien, Agravic 3: "you say 17 sizes but only on sale in women's in a couple sizes"): a model with its own
        # men's and women's versions gets one line each, so the deepest discount never reads as both
        if sm["top"] >= 5 and any(d.get("sx") == ["men"] for d in its) and any(d.get("sx") == ["women"] for d in its):
            lines = []
            for g in ("women", "men"):
                sg = summary(its, stores, g)
                if not sg:
                    continue
                gs = esc(sizes_phrase(sg.get("best_sizes") or [], L))
                lines.append(L["aSaleG"].format(g=L["gLab"][g], price=money(sg["price"]), p=sg["off"], store=esc(sg["store"]), bsizes=gs)
                             if sg["off"] >= 5 else L["aSaleGNo"].format(g=L["gLab"][g], price=money(sg["price"])))
            if lines:
                ans_sale = L["aSaleYesG"].format(lines=" ".join(lines))
        out.append(f'<h2>{L["aboutH"]}</h2><p>{about}</p><h2>{L["faqH"]}</h2><div class="faq">'
                   f'<h3>{L["qSale"].format(name=esc(name))}</h3><p>{ans_sale}</p>'
                   f'<h3>{L["qSizes"]}</h3><p>{esc("; ".join(ranges))}.</p>'
                   f'<h3>{L["qWhere"].format(name=esc(name))}</h3><p>{L["aWhere"].format(store=esc(sm["store"]), price=money(sm["price"]), bsizes=bsz).replace(" ()", "")}</p></div>')
        # Oct 23 (Bastien: "become the best at seo and aeo so that we even show up on AI searches"): the same quick answers as
        # FAQPage data (Google and answer engines lift question/answer pairs), plus breadcrumbs; nothing visible changes
        plain = lambda x: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()
        qa = [(plain(L["qSale"].format(name=esc(name))), plain(ans_sale)), (plain(L["qSizes"]), plain("; ".join(ranges)) + "."),
              (plain(L["qWhere"].format(name=esc(name))), plain(L["aWhere"].format(store=esc(sm["store"]), price=money(sm["price"]), bsizes=bsz).replace(" ()", "")))]
        faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa if q and len(a) > 2]}
        crumbs_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "The Gear Fox", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": L["all"], "item": f"{BASE}/{L['dir']}/"},
            *([{"@type": "ListItem", "position": 3, "name": bname(brand), "item": f"{BASE}/{L['brandDir']}/{slugify(brand)}/"}] if brand in brand_pages else []),
            {"@type": "ListItem", "position": 4 if brand in brand_pages else 3, "name": name}]}
        # the date the prices were checked: answer engines favour pages they can see are fresh
        page_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": name, "dateModified": date.today().isoformat(),
                   "inLanguage": L["lang"], "publisher": {"@type": "Organization", "name": "The Gear Fox", "url": BASE + "/"}}
        out.append("".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (faq_ld, crumbs_ld, page_ld)))
    home = "/?ref=shoe-page" + L["q"]
    out.append(f'<section class="cta"><h2>{L["cta"]}</h2><p>{L["ctaTxt"]}</p><a class="btn" href="{home}">{L["ctaBtn"]}</a></section>')
    if related:
        out.append(f'<h2>{L["more"].format(brand=esc(brand))}</h2><ul class="links">' +
                   "".join(f'<li><a href="/{L["dir"]}/{s}/">{esc(brand_models[s])}</a></li>' for s in related) + "</ul>")
    out.append(page_foot(L))
    return "".join(out)


def alt_file(models, live, fx=1.0, namer=None):
    """Oct 22: /shoes/alts.json (and /us/shoes/alts.json): for each kind of shoe, the 40 models with the deepest sale, each with
    its sale sizes per cut ("m" men's / unisex, "w" women's): size -> [price, % off]. Shoe pages pick 6 in the visitor's size."""
    out = defaultdict(list)
    for slug in live:
        its = models.get(slug)
        if not its:
            continue
        cuts = {"m": {}, "w": {}}
        for d in its:
            if d.get("w"):
                continue
            sx = d.get("sx") or []
            for e in d["sz"]:
                sz = str(e[0])
                reg = e[3] if len(e) > 3 and e[3] else e[1]
                if sz.endswith(("~N", "~W")) or sz == "OS" or not e[1] < reg * 0.99:
                    continue
                g = "w" if sx == ["women"] or sz.startswith("W:") else "m"
                sz = sz.replace("M:", "").replace("W:", "")
                if not re.fullmatch(r"\d+(\.5)?", sz):
                    continue
                pct = round(100 * (1 - e[1] / reg))
                if sz not in cuts[g] or e[1] / fx < cuts[g][sz][0]:
                    cuts[g][sz] = [round(e[1] / fx, 2), pct]
        n = len(cuts["m"]) + len(cuts["w"])
        if not n:
            continue
        top = max(v[1] for c in cuts.values() for v in c.values())
        if top < 10:
            continue
        t = its[0].get("t") or "daily"
        img = next((d["img"] for d in its if d.get("img")), "")
        out[t].append((top, n, {"s": slug, "b": its[0]["b"], "n": (namer or base_model)(its[0]["n"]), "i": img,
                                **{g: c for g, c in cuts.items() if c}}))
    # shoes on sale in 4+ sizes first (a 71% deal left in one women's 5 helps almost nobody), then the deepest discount
    return {t: [x[2] for x in sorted(rows, key=lambda r: (r[1] < 4, -r[0], -r[1]))[:40]] for t, rows in out.items()}


def card_list(L, rows):
    """rows: [(slug, name, summary)] -> linked cards: photo, name, sizes/stores, price and % off."""
    money = L["money"]
    out = []
    for slug, name, sm in rows:
        img = f'<img src="{esc(sm["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if sm.get("img") else ""
        price = (f'<b>{money(sm["price"])}</b><span class="off">−{sm["top"]}%</span>' if sm["top"] >= 10
                 else f'<b>{money(sm["price"])}</b><small>{L["fullPrice"]}</small>')
        out.append(f'<li><a href="/{L["dir"]}/{slug}/">{img}<span class="nm"><b>{esc(name)}</b>'
                   f'<small>{esc(sm["note"]) if sm.get("note") else L["sizesStores"].format(sizes=sm["sizes"], stores=sm["stores"])}</small>'
                   + (f'<small class="lowl">✓ {esc(L["low"].format(d=sm["lowd"]))}</small>' if sm.get("lowd") else "")
                   + f'</span><span class="pr">{price}</span></a></li>')
    return '<ul class="cards">' + "".join(out) + "</ul>"


def browse_nav(L, brands):
    """Links between the pages: by kind, by brand, Black Friday (same order in both languages)."""
    if L.get("hike"):      # boot pages (Oct 25): hiking deals + every boot model; no running lists
        return f'<nav class="browse" aria-label="{L["browse"]}"><a href="{L["home"]}">{esc(L["mDeals"])}</a><a href="/{L["dir"]}/">{esc(L["all"])}</a></nav>'
    hub = lambda k: f'/{L["hubDir"]}/' + (f'{L["hubSlugs"][k]}/' if L["hubSlugs"][k] else "")
    links = [(hub(k), L["hubs"][k][1]) for k in ("all", "road", "trail", "racing", "women", "men")]
    links += [(f'/{L["bfDir"]}/', L["bfLink"])] + ([(f'/{L["bdDir"]}/', L["bdLink"])] if L.get("bdDir") else []) + [(f'/{L["dir"]}/', L["all"])]
    links.append(("/us/races/" if L["lang"] == "en-US" else "/courses/" if L["lang"] == "fr-CA" else "/races/", L["mRaces"]))   # Oct 21: race gear lists
    out = f'<nav class="browse" aria-label="{L["browse"]}">' + "".join(f'<a href="{u}">{esc(t)}</a>' for u, t in links) + "</nav>"
    if brands:
        out += f'<nav class="browse" aria-label="{L["brandsH"]}">' + "".join(
            f'<a href="/{L["brandDir"]}/{slugify(b)}/">{esc(b)}</a>' for b in brands) + "</nav>"
    return out


def real_first(rows):
    """Black Friday week: deals at their lowest price in 30+ days first (stable: biggest discount first within each group)."""
    return sorted(rows, key=lambda r: 0 if r[2].get("lowd") else 1)


def real_line(L, rows):
    n = sum(1 for r in rows if r[2].get("lowd"))
    return f'<p class="realn">✓ {esc(L["bfReal"].format(n=n, t=len(rows)))}</p>' if n else ""


def bf_stats(site, today):
    """Black Friday page, before the week (Oct 27, growth chat + Bastien): today's numbers from our own price history, the same
    method as the monthly report (tools/report_page.py compute: Canadian stores only, spikes out, 'on sale' = 1%+ under regular)."""
    import os
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        import report_page as RP
        hist = os.environ.get("HISTORY_FILE") or "hist/prices.jsonl"
        if not Path(hist).exists():
            return None
        return RP.compute(str(site / "deals.json"), hist, (today - timedelta(days=14)).isoformat())
    except Exception as e:
        print(f"  ! Black Friday stats left out ({e})", file=sys.stderr)
        return None


def bf_data(L, R):
    if not R or not R["shoes"] or not R["hist"]:
        return ""
    fr = L is T["fr"]
    num = (lambda n: f"{n:,}".replace(",", "\u202f")) if fr else (lambda n: f"{n:,}")
    sz = lambda g, s: next((v for k, v in R["sizes"][g][1] if k == s), 0)
    big = [b for b in R["brands"] if b[1] >= 100]
    most = ", ".join(f"{bname(b[0])} {b[2]}{' %' if fr else '%'}" for b in big[:3])
    least = ", ".join(f"{bname(b[0])} {b[2]}{' %' if fr else '%'}" for b in big[-2:][::-1])
    back = date.fromisoformat(R["back"])
    vals = dict(pct=round(100 * R["on"] / R["shoes"]), on=num(R["on"]), shoes=num(R["shoes"]), shops=R["shops"], w8=sz("women", "8"),
                m9=sz("men", "9"), same=round(100 * R["same"] / R["hist"]), back=fmt_date(back.isoformat() + "T18:00:00+00:00", L), most=most, least=least)
    lines = [x.format(**vals) for x in L["bfData"]] if big else [x.format(**vals) for x in L["bfData"][:3]]
    return (f'<h2>{esc(L["bfDataH"].format(date=fmt_date(R["day"] + "T18:00:00+00:00", L)))}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in lines) + "</ul>")


def black_friday(year):
    """The fourth Friday of November."""
    d = date(year, 11, 1)
    return d + timedelta(days=(4 - d.weekday()) % 7 + 21)


def qs_box(L, head, ref):
    """Quick sign-up on list pages (Black Friday, sale lists; Oct 11): fit + shoe size + email, right here. The script at the
    page's end sends it like the homepage's sign-up (a member with those sizes gets the Friday email)."""
    men = "".join(f'<option value="{v:g}">{v:g}</option>' for v in [x / 2 for x in range(12, 31)])
    women = "".join(f'<option value="{v:g}">{v:g}</option>' for v in [x / 2 for x in range(10, 25)])
    return (f'<section class="alert qs" id="qsBox" data-ref="{ref}" data-pick="{esc(L["qsPick"])}" data-bad="{esc(L["alertBad"])}" '
            f'data-ok="{esc(L["alertOk"])}" data-fail="{esc(L["alertFail"])}"><h2>{esc(head)}</h2><p class="fine">{esc(L["qsTxt"])}</p>'
            f'<form novalidate><div class="qsrow"><select class="qsg" aria-label="Fit"><option value="men">{esc(L["qsMen"])}</option>'
            f'<option value="women">{esc(L["qsWomen"])}</option></select><select class="qss" aria-label="{esc(L["qsSize"])}">'
            f'<option value="">{esc(L["qsSize"])}</option><optgroup data-g="men">{men}</optgroup><optgroup data-g="women" hidden disabled>{women}</optgroup></select></div>'
            f'<div class="qsrow"><input type="email" autocomplete="email" inputmode="email" placeholder="{esc(L["emailPh"])}" aria-label="Email" required>'
            f'<button type="submit">{esc(L["qsBtn"])}</button></div></form><p class="msg" aria-live="polite"></p>'
            f'<p class="fine qsmore"><a href="{L["home"]}{"&" if "?" in L["home"] else "?"}ref={ref}">{esc(L["qsMore"])}</a></p></section>')


def bf_live_line(L):
    """Oct 27: the live deal check (scraper/bf_live.py), linked near the top of the Canadian Black Friday pages."""
    if not L.get("bfLive"):
        return ""
    q, txt, href = L["bfLive"]
    gift = (f'<p class="bflive"><strong>{esc(L["bfGift"][0])}</strong> <a href="{L["bfGift"][2]}">{esc(L["bfGift"][1])}</a></p>'
            if L.get("bfGift") else "")   # Oct 28: the gift page (scraper/gift_pages.py)
    return f'<p class="bflive"><strong>{esc(q)}</strong> <a href="{href}">{esc(txt)}</a></p>' + gift


def bf_other(L):
    q, txt, href = L["bfOther"]
    return f'<p><strong>{esc(q)}</strong> <a href="{href}">{esc(txt)}</a></p>'


def bname(b):
    """Oct 19 (Search Console: people search "on cloud sale", "on running sale"; our title said "On Sale Canada" and the heading
    "On on sale in Canada"): the brand On is written "On Running" in titles and headings."""
    return "On Running" if b == "On" else b


def brand_title(L, b, rows):
    """Brand page title with today's numbers, like the shoe pages: "Altra Sale Canada: 23 running shoes on sale, up to 45% off"."""
    on = [r for r in rows if (r[2].get("top") or 0) > 0]
    if not on:
        return L["brandTitle"].split(":")[0].format(brand=bname(b))
    return L["brandTitle"].format(brand=bname(b), n=len(on), p=max(r[2]["top"] for r in on))


def list_page(L, path_en, path_fr, title, h1, intro, rows, brands, extra="", after=""):
    out = [page_head(L, title, intro, path_en, path_fr)]
    out.append(f'<h1>{esc(h1)}</h1><p class="sub">{esc(intro)}</p>{extra}')
    out.append(card_list(L, rows) if rows else f'<p>{esc(L["none"])}</p>')
    out.append(after)
    out.append(browse_nav(L, brands))
    out.append(page_foot(L))
    return "".join(out)


def home_section(L_en, L_fr, rows, brands, us=None):
    """A plain-HTML block for the homepage (between the SEO-TODAY markers): today's best shoe deals with links, readable
    by search engines even though the main deals are drawn by the page's script. One copy per language, plus one for the USA
    side (us = (rows, brands) from deals-us.json; Oct 6, 2026); the site shows the copy matching its language and country."""
    def one(L, code, rows, brands):
        money = L["money"]
        li = "".join(f'<li><a href="/{L["dir"]}/{s}/">{esc(n)}</a> · {money(sm["price"])}' + (f' (−{sm["top"]}%)' if sm["top"] >= 10 else "") + "</li>"
                     for s, n, sm in rows)
        nav = " · ".join(f'<a href="{u}">{esc(t)}</a>' for u, t in
                         [(f'/{L["hubDir"]}/', L["hubs"]["all"][1]), (f'/{L["bfDir"]}/', L["bfLink"]), (f'/{L["dir"]}/', L["homeMore"])])
        br = " · ".join(f'<a href="/{L["brandDir"]}/{slugify(b)}/">{esc(b)}</a>' for b in brands[:12])
        lang = "en" if code == "us" else code
        return (f'<div class="seo-{code}" lang="{lang}"><h2>{esc(L["homeH"])}</h2><ol>{li}</ol>'
                f'<p>{nav}</p><p>{br}</p></div>')
    us_html = one(US, "us", *us) if us else ""
    return f'<section class="seo-today">{one(L_en, "en", rows, brands)}{one(L_fr, "fr", rows, brands)}{us_html}</section>'


def index_page(L, entries, updated, paths=("/shoes/", "/chaussures/")):
    """entries: [(brand, slug, model name, best % off or 0)]"""
    path_en, path_fr = paths
    out = [page_head(L, L["idxTitle"], L["idxDesc"].format(n=len(entries)), path_en, path_fr)]
    out.append(f'<h1>{L["idxH1"]}</h1><p class="sub">{L["idxIntro"]}</p>')
    out.append(browse_nav(L, []))
    by = defaultdict(list)
    for b, s, n, off in entries:
        by[b].append((n, s, off))
    brands = sorted(by, key=str.lower)
    # search as you type + brand shortcuts (for people; Google reads the plain links below either way)
    out.append(f'<div class="find"><input id="find" type="search" placeholder="{esc(L["find"])}" aria-label="{esc(L["find"])}" autocomplete="off">'
               f'<nav class="jump">' + "".join(f'<a href="#b-{slugify(b)}">{esc(b)}</a>' for b in brands) + '</nav></div>')
    for b in brands:
        out.append(f'<section class="bgrp"><p class="brand" id="b-{slugify(b)}">{esc(b)}</p><ul class="links">' + "".join(
            f'<li data-n="{esc((b + " " + n).lower())}"><a href="/{L["dir"]}/{s}/">{esc(n[len(b):].strip() if n.lower().startswith(b.lower() + " ") else n)}{f" <small>−{off}%</small>" if off >= 10 else ""}</a></li>'
            for n, s, off in sorted(by[b], key=lambda x: x[0].lower())) + "</ul></section>")
    out.append(f'<p class="nomatch" id="nomatch" hidden>{esc(L["noMatch"])}</p>')
    out.append("""<script>(function(){var f=document.getElementById("find"),nm=document.getElementById("nomatch");
var norm=function(t){return t.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/[^a-z0-9+ ]/g," ")};
f.addEventListener("input",function(){var w=norm(f.value).split(/\\s+/).filter(Boolean),any=false;
document.querySelectorAll(".bgrp").forEach(function(g){var n=0;g.querySelectorAll("li").forEach(function(li){var t=norm(li.dataset.n).replace(/ /g,"")+" "+norm(li.dataset.n);
var ok=w.every(function(x){return t.indexOf(x)>=0});li.hidden=!ok;if(ok)n++});g.hidden=!n;if(n)any=true});
nm.hidden=any||!w.length;document.querySelector(".jump").hidden=!!w.length})})();</script>""")
    out.append(page_foot(L))
    return "".join(out)


def main():
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    import os
    n_hist = load_history(os.environ.get("HISTORY_FILE") or "hist/prices.jsonl")
    print(f"price history: {n_hist} products")
    data = json.loads((site / "deals.json").read_text())
    items, updated = data["items"], data.get("updated")
    stores = store_names((site / "index.html").read_text())
    models = build_models(items)
    reg_path = site / "shoes" / "pages.json"          # every model that ever had a page (fetched from the live site)
    try:
        known = json.loads(reg_path.read_text())
    except Exception:
        known = {}
    for slug, its in models.items():
        if slug not in known and len(canadian_stores(its, stores)) >= MIN_STORES:
            known[slug] = {"b": its[0]["b"], "n": f'{its[0]["b"]} {base_model(its[0]["n"])}', "t": its[0].get("t") or ""}
    forward_old(known, models, site, [L["dir"] for L in T.values()])
    known_live = {s: v for s, v in known.items() if not v.get("to")}
    names = {s: v["n"] for s, v in known_live.items()}
    by_brand = defaultdict(list)
    for s, v in known_live.items():
        by_brand[v["b"].lower()].append(s)
    # today's numbers per model (and per gender) for the list pages
    summ = {sl: summary(models[sl], stores) for sl in known_live if models.get(sl)}
    summ = {k: v for k, v in summ.items() if v}
    gsumm = {g: {sl: summary(models[sl], stores, g) for sl in summ} for g in ("women", "men")}
    on_sale = lambda d: sorted([(sl, known_live[sl]["n"], sm) for sl, sm in d.items() if sm and sm["top"] >= 10],
                               key=lambda r: (-r[2]["top"], -r[2]["sizes"]))
    kinds = {"all": on_sale(summ), "road": on_sale({k: v for k, v in summ.items() if v["t"] == "daily"}),
             "trail": on_sale({k: v for k, v in summ.items() if v["t"] == "trail"}),
             "racing": on_sale({k: v for k, v in summ.items() if v["t"] == "race"}),
             "women": on_sale(gsumm["women"]), "men": on_sale(gsumm["men"])}
    brand_models = defaultdict(list)
    for sl, sm in summ.items():
        brand_models[known_live[sl]["b"]].append(sl)
    brands = sorted([b for b, sls in brand_models.items() if len(sls) >= 3], key=lambda b: (-len(brand_models[b]), b.lower()))
    entries, n_live = [], 0
    for slug, meta in known_live.items():
        its = models.get(slug) or [{"b": meta["b"], "n": meta["n"][len(meta["b"]) + 1:], "g": "shoes", "t": meta.get("t"), "sz": [], "of": []}]
        n_live += bool(models.get(slug))
        same = [s for s in by_brand[meta["b"].lower()] if s != slug]
        related = sorted(same, key=lambda s: (known[s].get("t") != meta.get("t"), s))[:8]
        offs = [round(100 * (1 - e[1] / e[3])) for d in its for e in d["sz"] if len(e) > 3 and e[1] < e[3] * 0.99]
        entries.append((meta["b"], slug, meta["n"], max(offs, default=0)))
        hide = stale(meta, bool(models.get(slug)))
        for L in T.values():
            p = site / L["dir"] / slug / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(model_page(slug, its, stores, L, updated, related, names, brand_pages=set(brands), hide=hide))
    (site / "shoe-pages.css").write_text(HEAD_CSS.strip() + "\n")
    (site / "shoes" / "alts.json").write_text(json.dumps(alt_file(models, known_live), ensure_ascii=False, separators=(",", ":")))
    (site / "chaussures").mkdir(exist_ok=True)
    (site / "chaussures" / "alts.json").write_text((site / "shoes" / "alts.json").read_text())
    extra_urls = []
    for L in T.values():
        other = T["fr" if L is T["en"] else "en"]
        for k, rows in kinds.items():
            sub = lambda LL: f'/{LL["hubDir"]}/' + (f'{LL["hubSlugs"][k]}/' if LL["hubSlugs"][k] else "")
            en_p, fr_p = (sub(L), sub(other)) if L is T["en"] else (sub(other), sub(L))
            title, h1, intro = L["hubs"][k]
            p = site / sub(L).strip("/") / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(list_page(L, en_p, fr_p, title, h1, intro, rows[:80], brands,
                                   (size_nav(L, k) if k in ("men", "women") else "") + qs_box(L, L["qsHub"], "sale-list")))
            extra_urls.append(sub(L))
        en_L, fr_L = T["en"], T["fr"]
        extra_urls += size_pages(site, L, models, known_live, stores, brands,
                                 twin=lambda g, sz: (size_path(en_L, g, sz), size_path(fr_L, g, sz)))
        for b in brands:
            rows = sorted([(sl, known_live[sl]["n"], summ[sl]) for sl in brand_models[b]], key=lambda r: (-r[2]["top"], r[1].lower()))
            en_p, fr_p = f'/brands/{slugify(b)}/', f'/marques/{slugify(b)}/'
            p = site / L["brandDir"] / slugify(b) / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(list_page(L, en_p, fr_p, brand_title(L, b, rows), L["brandH1"].format(brand=bname(b)),
                                   L["brandIntro"].format(brand=bname(b)), rows, brands))
            extra_urls.append(f'/{L["brandDir"]}/{slugify(b)}/')
        # Black Friday: live from now on so it is known to search engines well before Nov 27
        bf_rows = [r for r in kinds["all"] if r[2]["sizes"] >= 6][:40]
        cta = qs_box(L, L["bfCta"], "black-friday")
        p = site / L["bfDir"] / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        today = (datetime.fromisoformat(updated.replace("Z", "+00:00")) if updated else datetime.now(timezone.utc)).astimezone(HOME_TZ).date()
        bf = black_friday(today.year if today <= black_friday(today.year) + timedelta(days=4) else today.year + 1)
        if bf - timedelta(days=7) <= today <= bf + timedelta(days=4):     # Black Friday week to Cyber Monday: the real deals
            p.write_text(list_page(L, "/black-friday/", "/vendredi-fou/", L["bfTitle"], L["bfH1"], L["bfIntro"], real_first(bf_rows), brands,
                                   bf_live_line(L) + bf_other(L) + real_line(L, bf_rows) + cta))
        else:   # before: honest page, the price tracking + tips, and today's deals clearly labelled as today's (Bastien, Oct 4)
            tracked = sum(1 for i in items if i.get("hd"))
            if "bf_R" not in globals():
                globals()["bf_R"] = bf_stats(site, today)
            extra = (bf_live_line(L) + bf_other(L) + cta + f'<h2>{esc(L["bfTrackH"])}</h2><p>{esc(L["bfTrackTxt"].format(n=f"{tracked:,}".replace(",", " " if L is T["fr"] else ",")))}</p>'
                     + bf_data(L, globals()["bf_R"])
                     + f'<h2>{esc(L["bfSpotH"])}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in L["bfSpot"]) + "</ul>"
                     + f'<h2>{esc(L["bfTodayH"].format(date=fmt_date(updated, L)))}</h2>')
            p.write_text(list_page(L, "/black-friday/", "/vendredi-fou/", L["bfTitlePre"], L["bfH1Pre"].format(date=bf.day),
                                   L["bfIntroPre"].format(days=(bf - today).days), bf_rows[:6], brands, extra))
        extra_urls.append(f'/{L["bfDir"]}/')
        # Boxing Day (Dec 26): same idea; the real deals from Dec 19 to Jan 3, an honest "get ready" page before that
        y = today.year if today <= date(today.year, 12, 26) + timedelta(days=8) else today.year + 1
        bd = date(y, 12, 26)
        dayname = (["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] if L is T["en"]
                   else ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"])[bd.weekday()]
        p = site / L["bdDir"] / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        bd_other = f'<p><strong>{esc(L["bdOther"][0])}</strong> <a href="{L["bdOther"][2]}">{esc(L["bdOther"][1])}</a></p>'
        cta = qs_box(L, L["bdCta"], "boxing-day")
        if bd - timedelta(days=7) <= today <= bd + timedelta(days=8):
            p.write_text(list_page(L, "/boxing-day/", "/soldes-apres-noel/", L["bdTitle"].format(y=y), L["bdH1"].format(y=y),
                                   L["bdIntro"].format(day=dayname), bf_rows, brands, cta))
        else:
            extra = (cta + f'<h2>{esc(L["bdSpotH"])}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in L["bdSpot"]) + "</ul>" + bd_other
                     + f'<h2>{esc(L["bdTodayH"].format(date=fmt_date(updated, L)))}</h2>')
            p.write_text(list_page(L, "/boxing-day/", "/soldes-apres-noel/", L["bdTitlePre"].format(y=y), L["bdH1Pre"].format(y=y, day=dayname),
                                   L["bdIntroPre"].format(days=(bd - today).days), bf_rows[:6], brands, extra))
        extra_urls.append(f'/{L["bdDir"]}/')
    for L in T.values():
        (site / L["dir"]).mkdir(parents=True, exist_ok=True)
        (site / L["dir"] / "index.html").write_text(index_page(L, entries, updated))
    reg_path.write_text(json.dumps(known, ensure_ascii=False, separators=(",", ":")))
    day = (updated or datetime.now(timezone.utc).isoformat())[:10]
    urls = ["/", "/shoes/", "/chaussures/", "/about.html", "/privacy.html"] + extra_urls
    urls += [f"/{d}/{s}/" for s in known_live for d in ("shoes", "chaussures")]
    us_urls, us_home = build_us(site, stores, set(known_live), {slugify(b) for b in brands})
    urls += us_urls
    # homepage: a plain block search engines can read (the deals themselves are drawn by the page's script)
    idx = site / "index.html"
    html_ = idx.read_text()
    if "<!--SEO-TODAY-->" in html_ and "<!--/SEO-TODAY-->" in html_:
        block = home_section(T["en"], T["fr"], [r for r in kinds["all"] if r[2]["sizes"] >= 6][:12], brands, us_home)
        html_ = re.sub(r"<!--SEO-TODAY-->.*?<!--/SEO-TODAY-->", lambda m: "<!--SEO-TODAY-->" + block + "<!--/SEO-TODAY-->", html_, flags=re.S)
        idx.write_text(html_)
    (site / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{day}</lastmod></url>\n" for u in urls if u not in NOINDEX) + "</urlset>\n")
    print(f"shoe pages: {len(known_live)} models ({n_live} in stock today), {2 * len(known_live)} pages EN/FR, "
          f"{sum(1 for v in known.values() if v.get('to'))} old addresses forwarded, {len(NOINDEX)} out-of-stock pages kept out of Google, {len(extra_urls)} list pages ({len(brands)} brands), sitemap {len(urls)} links")


NOINDEX = set()   # model pages with nothing in stock for 14+ days: noindex + out of the sitemap
HIDE_DAYS = 14    # a day or two out of stock doesn't flip a page in and out of Google


def stale(meta, live_today):
    """Registry entry `seen` = the last day the model was in stock (kept in pages.json). True = hide it from Google."""
    today = date.today().isoformat()
    if live_today:
        meta["seen"] = today
        return False
    return not meta.get("seen") or (date.today() - date.fromisoformat(meta["seen"])).days >= HIDE_DAYS
NOT_SHOE_PAGE = re.compile(r"clean|\bkit\b|\blaces?\b|insoles?|spray|wipes|shoe horn", re.I)   # moved out of shoes (Oct 7)


def forward_old(known, models, site, dirs):
    """An old page whose name now tidies into another model ("Neo Vista (Men's)" -> "Neo Vista", "M Ghost 18" -> "Ghost 18")
    forwards to it: noindex, canonical, out of the sitemap."""
    for slug in [s_ for s_, v in known.items() if NOT_SHOE_PAGE.search(v["n"]) and s_ not in models]:
        del known[slug]                # a cleaning kit that was filed as a shoe: no page (it never was one)
    for slug, meta in known.items():
        if meta.get("to") or slug in models:
            continue
        b = meta["b"]
        rest = base_model(meta["n"][len(b) + 1:] if meta["n"].lower().startswith(b.lower() + " ") else meta["n"])
        tries = [rest, re.sub(r"^" + re.escape(b) + r"\s+", "", rest, flags=re.I),        # "Unisex ASICS Megablast"
                 re.sub(r"\s+trail running$", "", rest, flags=re.I)]                     # "Speedgoat 7 GTX Trail Running"
        first = slugify(b).split("-")[0]
        brands = [b] + sorted({v["b"] for v in known.values() if v["b"] != b and slugify(v["b"]).split("-")[0] == first})   # "Asics Corp." -> "ASICS"
        for kb in brands:
            for x in tries + [re.sub(r"^" + re.escape(kb) + r"\s+", "", rest, flags=re.I)]:
                to = slugify(f"{kb} {x}")
                if to != slug and to in known and not known[to].get("to"):
                    meta["to"] = to
                    break
            if meta.get("to"):
                break
        if not meta.get("to"):   # Oct 26: "zegama-trail-2" = "zegama-2-trail", "stinson-7" -> "stinson-7-trail", "860v15-2e" -> "860v15-wide":
            # since the merge reads a lone trail/road word as filler, a page whose shoes moved forwards to the live page with the same words
            nk = lambda x: sorted(w for w in x.replace("-2e", "-wide").split("-") if w not in ("trail", "road"))
            hit = [k for k in models if k != slug and k in known and not known[k].get("to") and nk(k) == nk(slug)]
            if len(hit) == 1:
                meta["to"] = hit[0]
    for slug, to in {s: v["to"] for s, v in known.items() if v.get("to")}.items():
        for d in dirs:
            p = site / d / slug / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            u = f"/{d}/{to}/"
            p.write_text(f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{esc(known[to]["n"])}</title><link rel="canonical" href="{BASE}{u}">'
                         f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={u}"></head><body><a href="{u}">{esc(known[to]["n"])}</a></body></html>')


def build_us(site, stores, ca_models, ca_brands):
    """The USA side's pages (Oct 6, 2026): /us/shoes/<slug>/, list pages, brand pages, Black Friday, from deals-us.json.
    Same rules as Canada: a page once 3+ US stores carry the model; pages never disappear (us/shoes/pages.json).
    Returns the URLs for the sitemap."""
    f = site / "deals-us.json"
    if not f.exists():
        return [], None
    data = json.loads(f.read_text())
    items, updated = data["items"], data.get("updated")
    fx = float((data.get("fx") or {}).get("USD") or 1.37)
    L = US
    L["fx"] = fx
    L["money"] = lambda v: f"${v / fx:,.2f}"
    us_store = lambda h: stores.get(h, [""])[1:2] == ["US"]
    models = build_models(items)
    reg_path = site / "us" / "shoes" / "pages.json"
    try:
        known = json.loads(reg_path.read_text())
    except Exception:
        known = {}
    for slug, its in models.items():
        if slug not in known and len({host(u) for d in its for u in d["of"] if us_store(host(u))}) >= MIN_STORES:
            known[slug] = {"b": its[0]["b"], "n": f'{its[0]["b"]} {base_model(its[0]["n"])}', "t": its[0].get("t") or ""}
    forward_old(known, models, site, ["us/shoes"])
    live = {s: v for s, v in known.items() if not v.get("to")}
    names = {s: v["n"] for s, v in live.items()}
    by_brand = defaultdict(list)
    for s_, v in live.items():
        by_brand[v["b"].lower()].append(s_)
    summ = {sl: summary(models[sl], stores) for sl in live if models.get(sl)}
    summ = {k: v for k, v in summ.items() if v}
    gsumm = {g: {sl: summary(models[sl], stores, g) for sl in summ} for g in ("women", "men")}
    on_sale = lambda d: sorted([(sl, live[sl]["n"], sm) for sl, sm in d.items() if sm and sm["top"] >= 10],
                               key=lambda r: (-r[2]["top"], -r[2]["sizes"]))
    kinds = {"all": on_sale(summ), "road": on_sale({k: v for k, v in summ.items() if v["t"] == "daily"}),
             "trail": on_sale({k: v for k, v in summ.items() if v["t"] == "trail"}),
             "racing": on_sale({k: v for k, v in summ.items() if v["t"] == "race"}),
             "women": on_sale(gsumm["women"]), "men": on_sale(gsumm["men"])}
    brand_models = defaultdict(list)
    for sl in summ:
        brand_models[live[sl]["b"]].append(sl)
    brands = sorted([b for b, sls in brand_models.items() if len(sls) >= 3], key=lambda b: (-len(brand_models[b]), b.lower()))
    entries, urls = [], []
    for slug, meta in live.items():
        its = models.get(slug) or [{"b": meta["b"], "n": meta["n"][len(meta["b"]) + 1:], "g": "shoes", "t": meta.get("t"), "sz": [], "of": []}]
        same = [x for x in by_brand[meta["b"].lower()] if x != slug]
        related = sorted(same, key=lambda x: (known[x].get("t") != meta.get("t"), x))[:8]
        offs = [round(100 * (1 - e[1] / e[3])) for d in its for e in d["sz"] if len(e) > 3 and e[1] < e[3] * 0.99]
        entries.append((meta["b"], slug, meta["n"], max(offs, default=0)))
        p = site / L["dir"] / slug / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(model_page(slug, its, stores, L, updated, related, names,
                                paths=(f"/{L['dir']}/{slug}/", f"/shoes/{slug}/" if slug in ca_models else ""), brand_pages=set(brands),
                                hide=stale(meta, bool(models.get(slug)))))
        urls.append(f"/{L['dir']}/{slug}/")
    (site / L["dir"] / "alts.json").write_text(json.dumps(alt_file(models, live, fx), ensure_ascii=False, separators=(",", ":")))
    for k, rows in kinds.items():
        tail = f'{L["hubSlugs"][k]}/' if L["hubSlugs"][k] else ""
        own, twin = f'/{L["hubDir"]}/{tail}', f'/{T["en"]["hubDir"]}/{tail}'
        title, h1, intro = L["hubs"][k]
        p = site / own.strip("/") / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(list_page(L, own, twin, title, h1, intro, rows[:80], brands,
                               (size_nav(L, k) if k in ("men", "women") else "") + qs_box(L, L["qsHub"], "sale-list")))
        urls.append(own)
    urls += size_pages(site, L, models, live, stores, brands, twin=lambda g, sz: (size_path(L, g, sz), size_path(T["en"], g, sz)))
    for b in brands:
        rows = sorted([(sl, live[sl]["n"], summ[sl]) for sl in brand_models[b]], key=lambda r: (-r[2]["top"], r[1].lower()))
        own = f'/{L["brandDir"]}/{slugify(b)}/'
        p = site / own.strip("/") / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(list_page(L, own, f'/brands/{slugify(b)}/' if slugify(b) in ca_brands else "", brand_title(L, b, rows),
                               L["brandH1"].format(brand=bname(b)), L["brandIntro"].format(brand=bname(b)), rows, brands))
        urls.append(own)
    bf_rows = [r for r in kinds["all"] if r[2]["sizes"] >= 6][:40]
    cta = qs_box(L, L["bfCta"], "black-friday")
    today = (datetime.fromisoformat(updated.replace("Z", "+00:00")) if updated else datetime.now(timezone.utc)).astimezone(HOME_TZ).date()   # Oct 23: was UTC (US page said 35 days to go, Canada 36)
    bf = black_friday(today.year if today <= black_friday(today.year) + timedelta(days=4) else today.year + 1)
    own = f'/{L["bfDir"]}/'
    p = site / own.strip("/") / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    if bf - timedelta(days=7) <= today <= bf + timedelta(days=4):
        p.write_text(list_page(L, own, "/black-friday/", L["bfTitle"], L["bfH1"], L["bfIntro"], real_first(bf_rows), brands,
                               bf_other(L) + real_line(L, bf_rows) + cta))
    else:
        tracked = sum(1 for i in items if i.get("hd"))
        extra = (bf_other(L) + cta + f'<h2>{esc(L["bfTrackH"])}</h2><p>{esc(L["bfTrackTxt"].format(n=f"{tracked:,}"))}</p>'
                 + f'<h2>{esc(L["bfSpotH"])}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in L["bfSpot"]) + "</ul>"
                 + f'<h2>{esc(L["bfTodayH"].format(date=fmt_date(updated, L)))}</h2>')
        p.write_text(list_page(L, own, "/black-friday/", L["bfTitlePre"], L["bfH1Pre"].format(date=bf.day),
                               L["bfIntroPre"].format(days=(bf - today).days), bf_rows[:6], brands, extra))
    urls.append(own)
    (site / L["dir"]).mkdir(parents=True, exist_ok=True)
    (site / L["dir"] / "index.html").write_text(index_page(L, entries, updated, paths=(f"/{L['dir']}/", "/shoes/")))
    urls.append(f"/{L['dir']}/")
    reg_path.write_text(json.dumps(known, ensure_ascii=False, separators=(",", ":")))
    print(f"USA shoe pages: {len(live)} models, {len(urls)} pages ({len(brands)} brands)")
    return urls, ([r for r in kinds["all"] if r[2]["sizes"] >= 6][:12], brands)


# ---------- Boot & hiking shoe price pages (Oct 25, Bastien: "Everything should be doing the same as the shoe page") ----------
HIKE_WORDS = re.compile(r"\b(hiking|hike|backpacking|approach|trekking|walking|winter|trail)\s+(boots?|shoes?)\b|\bboots?\b", re.I)
_H = {
    "en": dict(dir="hiking-boots", q="&sport=hike", home="/?sport=hike",
               title="{name} price in Canada: every size, every store", titleSale="{name} Sale Canada: from {price} (−{p}%)",
               aboutH="About this boot",
               about="The {name} is a {type}. Today {stores} stores in Canada carry it and we found {sizes} sizes in stock.",
               typeLower={"hike": "hiking shoe", "boot": "hiking boot", "approach": "approach shoe", "": "hiking boot or shoe"},
               types={"hike": "Hiking shoe", "boot": "Hiking boot", "approach": "Approach shoe"},
               altH={k: "Other hiking boots & shoes on sale in your size" for k in ("hike", "boot", "approach", "daily")},
               altH0={k: "Other hiking boots & shoes on sale today" for k in ("hike", "boot", "approach", "daily")},
               h1sub="On sale in Canada: every size, every store",
               desc="{name}: today's best price in every size at {n} Canadian outdoor stores{off}. Checked every morning by The Gear Fox.",
               cta="Get it in your size", ctaTxt="Pick your sizes once. Every Friday we email the best hiking deals in them, and you can get a price-drop alert on this boot.",
               more="More {brand} boots & shoes", all="All boot & hiking shoe models", mShoes="Boot prices by model", mDeals="Today's hiking deals",
               idxTitle="Hiking boot & shoe prices by model in Canada", idxH1="Boot prices by model",
               idxIntro="Every hiking boot and shoe we track, with today's best price in each size at Canadian outdoor stores. Updated every morning.",
               idxDesc="Today's best price in every size for {n} hiking boot and shoe models at Canadian outdoor stores. Updated every morning by The Gear Fox.",
               find="Search a model (e.g. Moab)", alertDone="You're watching this boot. We'll email you when it drops in your size."),
    "fr": dict(dir="bottes-randonnee", q="&lang=fr&sport=hike", home="/?lang=fr&sport=hike",
               title="{name} : prix au Canada, chaque pointure, chaque boutique", titleSale="{name} en solde au Canada : dès {price} (−{p} %)",
               aboutH="À propos de ce modèle",
               about="{name} : {type}. Aujourd'hui, {stores} boutiques au Canada le vendent et nous avons trouvé {sizes} pointures en stock.",
               typeLower={"hike": "chaussure de randonnée", "boot": "botte de randonnée", "approach": "chaussure d'approche", "": "botte ou chaussure de randonnée"},
               types={"hike": "Chaussure de randonnée", "boot": "Botte de randonnée", "approach": "Chaussure d'approche"},
               altH={k: "Autres bottes et chaussures de randonnée en solde dans votre pointure" for k in ("hike", "boot", "approach", "daily")},
               altH0={k: "Autres bottes et chaussures de randonnée en solde aujourd'hui" for k in ("hike", "boot", "approach", "daily")},
               h1sub="En solde au Canada : chaque pointure, chaque boutique",
               desc="{name} : le meilleur prix du jour dans chaque pointure dans {n} boutiques de plein air canadiennes{off}. Vérifié chaque matin par The Gear Fox.",
               cta="Trouvez-la dans votre pointure", ctaTxt="Choisissez vos tailles une fois. Chaque vendredi, on vous envoie les meilleures aubaines de randonnée dans vos tailles, et vous pouvez suivre le prix de ce modèle.",
               more="Autres modèles {brand}", all="Toutes les bottes et chaussures de randonnée", mShoes="Prix des bottes par modèle", mDeals="Aubaines de randonnée du jour",
               idxTitle="Prix des bottes et chaussures de randonnée par modèle au Canada", idxH1="Prix des bottes par modèle",
               idxIntro="Toutes les bottes et chaussures de randonnée que nous suivons, avec le meilleur prix du jour dans chaque pointure dans les boutiques de plein air canadiennes. Mis à jour chaque matin.",
               idxDesc="Le meilleur prix du jour dans chaque pointure pour {n} modèles de bottes et chaussures de randonnée dans les boutiques canadiennes. Mis à jour chaque matin par The Gear Fox.",
               find="Chercher un modèle (ex. Moab)", alertDone="Vous suivez ce modèle. On vous écrit quand il baisse dans votre pointure."),
    "us": dict(dir="us/hiking-boots", q="&c=us&sport=hike", home="/?c=us&sport=hike",
               title="{name} price: every size, every store", titleSale="{name} Sale: from {price} (−{p}%)",
               about="The {name} is a {type}. Today {stores} US stores carry it and we found {sizes} sizes in stock.",
               h1sub="On sale at US outdoor stores: every size, every store",
               desc="{name}: today's best price in every size at {n} US outdoor stores{off}. Checked every morning by The Gear Fox.",
               idxTitle="Hiking boot & shoe prices by model", idxIntro="Every hiking boot and shoe we track, with today's best price in each size at US outdoor stores. Updated every morning.",
               idxDesc="Today's best price in every size for {n} hiking boot and shoe models at US outdoor stores. Updated every morning by The Gear Fox."),
}


HEIGHT = {"mid": "Mid", "middle": "Mid", "low": "Low", "high": "High"}
SHELL = {"wp": "Waterproof", "wtpf": "Waterproof", "waterproof": "Waterproof", "gtx": "GTX", "vent": "Vent", "vented": "Vent"}


def hike_name(n):
    """Stores word the same boot differently ("Targhee IV Mid WP", "Targhee IV Waterproof Mid", "... Mid Wtpf"): one name each,
    so one page. Core words keep their order; then height (Mid/Low/High), then the shell (Waterproof/GTX/Vent)."""
    n = HIKE_WORDS.sub(" ", n)
    n = re.sub(r"\(?\bavailable in (wide )?widths?\b\)?", " ", n, flags=re.I)
    n = base_model(n)
    n = re.sub(r"\b(men|women)[’']?s\b|\bunisex\b|\bfootwear\b|\b\d{6,}\b", " ", n, flags=re.I)   # style codes "1313731"
    n = re.sub(r"\b(\d+)\.0\b", r"\1", n)                                       # "Free Hiker 2.0" = "Free Hiker 2"
    n = re.sub(r"\b(\w+)\s+\1\b", r"\1", n, flags=re.I)                          # "Terrex Terrex"
    core, h, sh = [], [], []
    for w in n.replace("-", " - ").split():
        k = w.lower().strip(".,")
        if k in HEIGHT:
            h.append(HEIGHT[k])
        elif k in SHELL:
            sh.append(SHELL[k])
        elif w != "-":
            core.append(w)
    return " ".join(core + list(dict.fromkeys(h)) + list(dict.fromkeys(sh))).strip(" -")


def hike_models(items):
    models = defaultdict(list)
    for d in items:
        if d["g"] != "shoes":
            continue
        name = hike_name(d["n"])
        if name:
            models[slugify(f'{d["b"]} {name}')].append(d)
    return models


def build_hike(site, stores):
    """Boot & hiking shoe pages from the hiking files: /hiking-boots/<slug>/ + /bottes-randonnee/<slug>/ (Canada) and
    /us/hiking-boots/<slug>/. Same rules as the shoe pages: a page once 3+ stores on that side carry the model; pages never
    disappear (hiking-boots/pages.json). Returns the URLs for the sitemap."""
    urls = []
    for side, fname in (("ca", "deals-hike.json"), ("us", "deals-hike-us.json")):
        f = site / fname
        if not f.exists():
            continue
        data = json.loads(f.read_text())
        items, updated = data["items"], data.get("updated")
        fx = float((data.get("fx") or {}).get("USD") or 1.37)
        langs = []
        for code in (("en", "fr") if side == "ca" else ("us",)):
            L = dict(US if code == "us" else T[code])
            L.update(_H["en"] if code == "us" else {})
            L.update(_H[code])
            L["hike"] = True
            if code == "us":
                L["fx"], L["money"] = fx, (lambda v, fx=fx: f"${v / fx:,.2f}")
            langs.append(L)
        on_side = (lambda h: stores.get(h, [""])[1:2] == ["US"]) if side == "us" else (lambda h: len(stores.get(h, [""])) < 2)
        models = hike_models(items)
        reg_path = site / langs[0]["dir"] / "pages.json"
        try:
            known = json.loads(reg_path.read_text())
        except Exception:
            known = {}
        for slug, its in models.items():
            if slug not in known and len({host(u) for d in its for u in d["of"] if on_side(host(u))}) >= MIN_STORES:
                known[slug] = {"b": its[0]["b"], "n": f'{its[0]["b"]} {hike_name(its[0]["n"])}', "t": its[0].get("t") or ""}
        live = {s_: v for s_, v in known.items() if not v.get("to")}
        names = {s_: v["n"] for s_, v in live.items()}
        by_brand = defaultdict(list)
        for s_, v in live.items():
            by_brand[v["b"].lower()].append(s_)
        entries = []
        for slug, meta in live.items():
            its = models.get(slug) or [{"b": meta["b"], "n": meta["n"][len(meta["b"]) + 1:], "g": "shoes", "t": meta.get("t"), "sz": [], "of": []}]
            same = [x for x in by_brand[meta["b"].lower()] if x != slug]
            related = sorted(same, key=lambda x: (known[x].get("t") != meta.get("t"), x))[:8]
            offs = [round(100 * (1 - e[1] / e[3])) for d in its for e in d["sz"] if len(e) > 3 and e[1] < e[3] * 0.99]
            entries.append((meta["b"], slug, meta["n"], max(offs, default=0)))
            paths = (f"/{_H['en']['dir']}/{slug}/", f"/{_H['fr']['dir']}/{slug}/") if side == "ca" else (f"/{_H['us']['dir']}/{slug}/", "")
            for L in langs:
                p = site / L["dir"] / slug / "index.html"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(model_page(slug, its, stores, L, updated, related, names, paths=paths, hide=stale(meta, bool(models.get(slug)))))
                urls.append(f"/{L['dir']}/{slug}/")
        for L in langs:
            (site / L["dir"]).mkdir(parents=True, exist_ok=True)
            (site / L["dir"] / "alts.json").write_text(json.dumps(alt_file(models, live, fx if side == "us" else 1.0, hike_name), ensure_ascii=False, separators=(",", ":")))
            ip = (f"/{_H['en']['dir']}/", f"/{_H['fr']['dir']}/") if side == "ca" else (f"/{L['dir']}/", "")
            (site / L["dir"] / "index.html").write_text(index_page(L, entries, updated, paths=ip))
            urls.append(f"/{L['dir']}/")
        reg_path.write_text(json.dumps(known, ensure_ascii=False, separators=(",", ":")))
        print(f"boot pages ({side}): {len(live)} models, {len(entries) * len(langs)} pages")
    return urls


HIKE_HOME = {"en": ("Today's best hiking boot deals in Canada", "Hiking deals in your size", "All boot prices by model"),
             "fr": ("Les meilleures aubaines de bottes de randonnée au Canada aujourd'hui", "Aubaines de randonnée à votre taille", "Prix des bottes par modèle"),
             "us": ("Today's best hiking boot deals", "Hiking deals in your size", "All boot prices by model")}


def hike_home(site, stores):
    """Oct 25 (Bastien: the hiking tab showed "Today's best running shoe deals" at the bottom): the homepage's hiking twin of the
    SEO-TODAY block, between <!--SEO-HIKE--> markers (keep them EMPTY in git); html.hike shows it instead of the running one."""
    parts = []
    for side, fname, codes in (("ca", "deals-hike.json", ("en", "fr")), ("us", "deals-hike-us.json", ("us",))):
        f = site / fname
        if not f.exists():
            continue
        data = json.loads(f.read_text())
        models = hike_models(data["items"])
        try:
            known = json.loads((site / _H["en" if side == "ca" else "us"]["dir"] / "pages.json").read_text())
        except Exception:
            continue
        rows = []
        for sl, meta in known.items():
            if meta.get("to") or not models.get(sl):
                continue
            sm = summary(models[sl], stores)
            if sm and sm["top"] >= 10 and sm["sizes"] >= 6:
                rows.append((sl, meta["n"], sm))
        rows = sorted(rows, key=lambda r: (-r[2]["top"], -r[2]["sizes"]))[:12]
        fx = float((data.get("fx") or {}).get("USD") or 1.37)
        for code in codes:
            L = dict(US if code == "us" else T[code]); L.update(_H["en"] if code == "us" else {}); L.update(_H[code])
            money = (lambda v: f"${v / fx:,.2f}") if code == "us" else L["money"]
            h2, deals, more = HIKE_HOME[code]
            li = "".join(f'<li><a href="/{L["dir"]}/{sl}/">{esc(n)}</a> · {money(sm["price"])}' + (f' (−{sm["top"]}%)' if sm["top"] >= 10 else "") + "</li>"
                         for sl, n, sm in rows)
            trail = {"en": ("/hikes/", "Trail gear lists"), "fr": ("/randonnees/", "Listes de matériel de randonnée"), "us": ("/us/hikes/", "Trail gear lists")}[code]
            nav = f'<a href="{L["home"]}">{esc(deals)}</a> · <a href="/{L["dir"]}/">{esc(more)}</a> · <a href="{trail[0]}">{esc(trail[1])}</a>'
            parts.append(f'<div class="seo-{code}" lang="{"en" if code == "us" else code}"><h2>{esc(h2)}</h2><ol>{li}</ol><p>{nav}</p></div>')
    idx = site / "index.html"
    html_ = idx.read_text()
    if parts and "<!--SEO-HIKE-->" in html_:
        block = f'<section class="seo-today seo-hike">{"".join(parts)}</section>'
        idx.write_text(re.sub(r"<!--SEO-HIKE-->.*?<!--/SEO-HIKE-->", lambda m: "<!--SEO-HIKE-->" + block + "<!--/SEO-HIKE-->", html_, flags=re.S))


def hike_main(site):
    """`shoe_pages.py site --hike`: the boot pages, after the hiking read lands in site/ (it runs alongside the running read)."""
    import os
    load_history(os.environ.get("HISTORY_FILE") or "hist/prices.jsonl")
    stores = store_names((site / "index.html").read_text())
    urls = build_hike(site, stores)
    hike_home(site, stores)
    p = site / "sitemap.xml"
    if p.exists() and urls:
        x = p.read_text()
        day = date.today().isoformat()
        new = "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{day}</lastmod></url>\n" for u in urls
                      if u not in NOINDEX and f"{BASE}{u}<" not in x)
        p.write_text(x.replace("</urlset>", new + "</urlset>"))


if __name__ == "__main__":
    if "--hike" in sys.argv:
        hike_main(Path(sys.argv[1]))
    else:
        main()
