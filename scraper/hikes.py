#!/usr/bin/env python3
"""Hike gear lists (Oct 25, 2026; Bastien: "Build a database of 100 hikes in north america, from day hikes to multiday adventures ...
people tell us where they are going and for how long, then we show a list of the 10 essentials or more gear dependant on the area
(bears, wildlife, wet vs dry climate, time of year, etc)").

HIKES: 100 North American hikes, day hikes to thru-hikes. Each one: where, the managing park/agency's page (`src`), length (km, round
trip unless `oneway`), climb (m), usual days, best months, climate, bears, and flags for what changes the gear (permits, bear canisters,
river fords, tides, altitude, exposure, heat, bugs, snow early/late season). Figures are rounded from the park pages and common trail
references; `checked` is False until a figure is re-read on `src` (rule: no claims we can't back up; a trail page shows "approx.").

gear_for(hike, days, month) -> the list: the 10 essentials (always), then what this hike, this length and this month add. Each line
says why and which shop category/type it links to on the Hiking tab (scraper/hike.py groups/types), so every item can show deals in
the visitor's size, like the race gear lists.

  python scraper/hikes.py                  sanity check + counts
  python scraper/hikes.py garibaldi-lake 1 8   one list (slug, days, month)
"""
import re
import sys

# ---------------------------------------------------------------- the hikes
# kind: day | overnight (1 night) | multi (2+ nights) | thru (weeks)
# climate: coastal-wet | mountain | alpine | desert | forest-humid | boreal | canyon
# bears: grizzly (grizzly/brown + black) | black | none (rare or absent)
# flags: permit, canister (approved bear canister required overnight), ford (river crossings), tide (tide tables), altitude (3,000 m+),
#        exposure (drops, cables, ladders), heat, bugs, snow (snow on trail into early summer or from early fall), scramble, water-scarce,
#        navigation (unmarked or route-finding), lightning (afternoon storms above treeline), cold-water (big cold lake/sea), huts
H = [
    # ---- British Columbia
    ("garibaldi-lake", "Garibaldi Lake", "BC", "ca", "Garibaldi Provincial Park", "day", 18, 820, 1, "7-9", "mountain", "black", "permit snow",
     "https://bcparks.ca/garibaldi-park/"),
    ("panorama-ridge", "Panorama Ridge", "BC", "ca", "Garibaldi Provincial Park", "day", 30, 1520, 1, "7-9", "alpine", "black", "permit snow exposure",
     "https://bcparks.ca/garibaldi-park/"),
    ("black-tusk", "Black Tusk", "BC", "ca", "Garibaldi Provincial Park", "day", 27, 1740, 1, "7-9", "alpine", "black", "permit snow scramble",
     "https://bcparks.ca/garibaldi-park/"),
    ("elfin-lakes", "Elfin Lakes", "BC", "ca", "Garibaldi Provincial Park", "overnight", 22, 600, 2, "7-10", "mountain", "black", "permit snow huts",
     "https://bcparks.ca/garibaldi-park/"),
    ("wedgemount-lake", "Wedgemount Lake", "BC", "ca", "Garibaldi Provincial Park", "day", 14, 1160, 1, "7-9", "alpine", "black", "permit snow",
     "https://bcparks.ca/garibaldi-park/"),
    ("joffre-lakes", "Joffre Lakes", "BC", "ca", "Joffre Lakes Park (Pipi7íyekw)", "day", 10, 400, 1, "6-10", "mountain", "black", "permit",
     "https://bcparks.ca/joffre-lakes-park/"),
    ("grouse-grind", "Grouse Grind", "BC", "ca", "Metro Vancouver (Grouse Mountain)", "day", 2.9, 853, 1, "5-10", "coastal-wet", "black", "oneway",
     "https://www.metrovancouver.org/services/regional-parks/park/grouse-grind"),
    ("stawamus-chief", "Stawamus Chief (three peaks)", "BC", "ca", "Stawamus Chief Provincial Park", "day", 11, 700, 1, "4-10", "coastal-wet", "black",
     "exposure", "https://bcparks.ca/stawamus-chief-park/"),
    ("frosty-mountain", "Frosty Mountain", "BC", "ca", "E.C. Manning Provincial Park", "day", 22, 1150, 1, "7-9", "mountain", "black", "snow",
     "https://bcparks.ca/ec-manning-park/"),
    ("west-coast-trail", "West Coast Trail", "BC", "ca", "Pacific Rim National Park Reserve", "multi", 75, 2400, 7, "5-9", "coastal-wet", "black",
     "permit tide ford oneway", "https://parks.canada.ca/pn-np/bc/pacificrim"),
    ("juan-de-fuca", "Juan de Fuca Marine Trail", "BC", "ca", "Juan de Fuca Provincial Park", "multi", 47, 1800, 4, "5-9", "coastal-wet", "black",
     "tide oneway", "https://bcparks.ca/juan-de-fuca-park/"),
    ("cape-scott", "Cape Scott Trail (to Nels Bight)", "BC", "ca", "Cape Scott Provincial Park", "multi", 34, 300, 3, "5-9", "coastal-wet", "black",
     "tide", "https://bcparks.ca/cape-scott-park/"),
    ("sunshine-coast-trail", "Sunshine Coast Trail", "BC", "ca", "qathet region (Sunshine Coast Trail Society)", "thru", 180, 6000, 12, "5-10",
     "coastal-wet", "black", "huts oneway", "https://sunshinecoasttrail.com/"),
    ("lake-ohara-alpine-circuit", "Lake O'Hara Alpine Circuit", "BC", "ca", "Yoho National Park", "day", 12, 800, 1, "7-9", "alpine", "grizzly",
     "permit exposure snow", "https://parks.canada.ca/pn-np/bc/yoho"),
    ("iceline", "Iceline Trail", "BC", "ca", "Yoho National Park", "day", 20, 900, 1, "7-9", "alpine", "grizzly", "snow",
     "https://parks.canada.ca/pn-np/bc/yoho"),
    ("berg-lake", "Berg Lake Trail", "BC", "ca", "Mount Robson Provincial Park", "multi", 46, 800, 3, "7-9", "mountain", "grizzly", "permit",
     "https://bcparks.ca/mount-robson-park/"),
    ("rockwall", "Rockwall Trail", "BC", "ca", "Kootenay National Park", "multi", 55, 2700, 4, "7-9", "alpine", "grizzly", "permit snow oneway",
     "https://parks.canada.ca/pn-np/bc/kootenay"),
    ("mount-assiniboine", "Mount Assiniboine (via Sunshine)", "BC", "ca", "Mount Assiniboine Provincial Park", "multi", 55, 1100, 4, "7-9", "alpine",
     "grizzly", "permit snow", "https://bcparks.ca/mount-assiniboine-park/"),
    # ---- Alberta
    ("plain-of-six-glaciers", "Plain of Six Glaciers", "AB", "ca", "Banff National Park", "day", 14.6, 590, 1, "6-10", "mountain", "grizzly", "",
     "https://parks.canada.ca/pn-np/ab/banff"),
    ("larch-valley-sentinel", "Larch Valley and Sentinel Pass", "AB", "ca", "Banff National Park", "day", 11.6, 725, 1, "7-10", "alpine", "grizzly",
     "permit snow", "https://parks.canada.ca/pn-np/ab/banff"),
    ("cory-pass", "Cory Pass Loop", "AB", "ca", "Banff National Park", "day", 13, 1000, 1, "7-9", "alpine", "grizzly", "scramble exposure",
     "https://parks.canada.ca/pn-np/ab/banff"),
    ("skoki", "Skoki Valley", "AB", "ca", "Banff National Park", "multi", 22, 800, 2, "7-9", "alpine", "grizzly", "permit huts",
     "https://parks.canada.ca/pn-np/ab/banff"),
    ("sulphur-skyline", "Sulphur Skyline", "AB", "ca", "Jasper National Park", "day", 8, 700, 1, "6-10", "mountain", "grizzly", "",
     "https://parks.canada.ca/pn-np/ab/jasper"),
    ("jasper-skyline", "Skyline Trail (Jasper)", "AB", "ca", "Jasper National Park", "multi", 44, 1400, 3, "7-9", "alpine", "grizzly",
     "permit snow lightning oneway", "https://parks.canada.ca/pn-np/ab/jasper"),
    ("tonquin-valley", "Tonquin Valley", "AB", "ca", "Jasper National Park", "multi", 43, 900, 4, "7-9", "mountain", "grizzly", "permit bugs",
     "https://parks.canada.ca/pn-np/ab/jasper"),
    ("ha-ling", "Ha Ling Peak", "AB", "ca", "Kananaskis (Canmore Nordic area)", "day", 7.5, 750, 1, "6-10", "mountain", "grizzly", "permit",
     "https://www.albertaparks.ca/"),
    ("burstall-pass", "Burstall Pass", "AB", "ca", "Peter Lougheed Provincial Park (Kananaskis)", "day", 15, 470, 1, "7-9", "alpine", "grizzly",
     "permit snow", "https://www.albertaparks.ca/"),
    ("crypt-lake", "Crypt Lake", "AB", "ca", "Waterton Lakes National Park", "day", 17, 700, 1, "7-9", "mountain", "grizzly", "exposure",
     "https://parks.canada.ca/pn-np/ab/waterton"),
    ("carthew-alderson", "Carthew-Alderson Trail", "AB", "ca", "Waterton Lakes National Park", "day", 19, 640, 1, "7-9", "alpine", "grizzly",
     "oneway", "https://parks.canada.ca/pn-np/ab/waterton"),
    # ---- Yukon
    ("chilkoot", "Chilkoot Trail", "YT", "ca", "Chilkoot Trail National Historic Site / Klondike Gold Rush NHP", "multi", 53, 1100, 4, "7-8",
     "alpine", "grizzly", "permit snow oneway", "https://parks.canada.ca/lhn-nhs/yt/chilkoot"),
    ("tombstone-grizzly-lake", "Grizzly Lake (Tombstone)", "YT", "ca", "Tombstone Territorial Park", "multi", 23, 900, 2, "7-8", "alpine", "grizzly",
     "permit bugs", "https://yukon.ca/en/tombstone-territorial-park"),
    ("kings-throne", "King's Throne", "YT", "ca", "Kluane National Park and Reserve", "day", 10, 1100, 1, "6-9", "alpine", "grizzly", "scramble",
     "https://parks.canada.ca/pn-np/yt/kluane"),
    # ---- Ontario
    ("algonquin-highland", "Highland Backpacking Trail", "ON", "ca", "Algonquin Provincial Park", "multi", 35, 600, 3, "5-10", "forest-humid", "black",
     "permit bugs", "https://www.ontarioparks.ca/park/algonquin"),
    ("centennial-ridges", "Centennial Ridges Trail", "ON", "ca", "Algonquin Provincial Park", "day", 10, 300, 1, "5-10", "forest-humid", "black",
     "bugs", "https://www.ontarioparks.ca/park/algonquin"),
    ("la-cloche-silhouette", "La Cloche Silhouette Trail", "ON", "ca", "Killarney Provincial Park", "multi", 78, 2000, 7, "5-10", "forest-humid",
     "black", "permit bugs", "https://www.ontarioparks.ca/park/killarney"),
    ("lake-superior-coastal", "Lake Superior Coastal Trail", "ON", "ca", "Lake Superior Provincial Park", "multi", 65, 1500, 6, "6-9", "boreal",
     "black", "permit cold-water oneway", "https://www.ontarioparks.ca/park/lakesuperior"),
    ("pukaskwa-coastal", "Coastal Hiking Trail (Pukaskwa)", "ON", "ca", "Pukaskwa National Park", "multi", 60, 1500, 6, "6-9", "boreal", "black",
     "permit cold-water oneway", "https://parks.canada.ca/pn-np/on/pukaskwa"),
    ("top-of-the-giant", "Top of the Giant", "ON", "ca", "Sleeping Giant Provincial Park", "day", 22, 300, 1, "5-10", "boreal", "black", "",
     "https://www.ontarioparks.ca/park/sleepinggiant"),
    ("bruce-peninsula-grotto", "Georgian Bay Trail to the Grotto", "ON", "ca", "Bruce Peninsula National Park", "day", 6, 50, 1, "5-10",
     "forest-humid", "black", "permit", "https://parks.canada.ca/pn-np/on/bruce"),
    ("bruce-trail", "Bruce Trail", "ON", "ca", "Bruce Trail Conservancy", "thru", 900, 15000, 40, "5-10", "forest-humid", "black", "bugs oneway",
     "https://brucetrail.org/"),
    # ---- Québec
    ("mont-albert", "Mont Albert", "QC", "ca", "Parc national de la Gaspésie (Sépaq)", "day", 17.4, 870, 1, "6-10", "alpine", "black", "permit snow",
     "https://www.sepaq.com/pq/gas/"),
    ("mont-jacques-cartier", "Mont Jacques-Cartier", "QC", "ca", "Parc national de la Gaspésie (Sépaq)", "day", 8.4, 465, 1, "6-9", "alpine", "black",
     "permit", "https://www.sepaq.com/pq/gas/"),
    ("acropole-des-draveurs", "L'Acropole des Draveurs", "QC", "ca", "Parc national des Hautes-Gorges-de-la-Rivière-Malbaie (Sépaq)", "day", 10.4,
     800, 1, "6-10", "mountain", "black", "permit", "https://www.sepaq.com/pq/hgo/"),
    ("les-loups", "Les Loups", "QC", "ca", "Parc national de la Jacques-Cartier (Sépaq)", "day", 10, 520, 1, "5-10", "forest-humid", "black",
     "permit", "https://www.sepaq.com/pq/jac/"),
    ("sentier-des-caps", "Sentier des Caps de Charlevoix", "QC", "ca", "Sentier des Caps de Charlevoix", "multi", 51, 2500, 4, "6-10",
     "forest-humid", "black", "permit huts oneway", "https://www.sentierdescaps.com/"),
    ("traversee-de-charlevoix", "Traversée de Charlevoix", "QC", "ca", "La Traversée de Charlevoix", "multi", 105, 3500, 6, "6-10", "forest-humid",
     "black", "permit huts oneway", "https://www.traverseedecharlevoix.qc.ca/"),
    ("sia-gaspesie", "International Appalachian Trail (Gaspésie)", "QC", "ca", "Sentier international des Appalaches – Québec", "thru", 650, 15000,
     35, "6-9", "boreal", "black", "huts oneway", "https://www.sia-iat.com/"),
    ("mont-tremblant-geant", "Le Géant (Mont-Tremblant)", "QC", "ca", "Parc national du Mont-Tremblant (Sépaq)", "day", 10, 600, 1, "5-10",
     "forest-humid", "black", "permit", "https://www.sepaq.com/pq/mot/"),
    # ---- Atlantic Canada
    ("cape-breton-skyline", "Skyline Trail (Cape Breton)", "NS", "ca", "Cape Breton Highlands National Park", "day", 8, 100, 1, "5-10",
     "coastal-wet", "black", "", "https://parks.canada.ca/pn-np/ns/cbreton"),
    ("cape-chignecto", "Cape Chignecto Coastal Trail", "NS", "ca", "Cape Chignecto Provincial Park", "multi", 51, 2000, 4, "5-10", "coastal-wet",
     "black", "permit tide", "https://parks.novascotia.ca/park/cape-chignecto"),
    ("fundy-footpath", "Fundy Footpath", "NB", "ca", "Fundy Trail Parkway / Fundy National Park", "multi", 49, 3000, 4, "6-9", "coastal-wet", "black",
     "permit tide ford oneway", "https://fundyfootpath.com/"),
    ("gros-morne-mountain", "Gros Morne Mountain", "NL", "ca", "Gros Morne National Park", "day", 17, 800, 1, "7-10", "alpine", "black", "scramble",
     "https://parks.canada.ca/pn-np/nl/grosmorne"),
    ("long-range-traverse", "Long Range Traverse", "NL", "ca", "Gros Morne National Park", "multi", 35, 900, 4, "7-9", "alpine", "black",
     "permit navigation bugs oneway", "https://parks.canada.ca/pn-np/nl/grosmorne"),
    ("east-coast-trail", "East Coast Trail", "NL", "ca", "East Coast Trail Association", "thru", 336, 8000, 20, "6-10", "coastal-wet", "none",
     "oneway", "https://eastcoasttrail.com/"),
    # ---- Washington
    ("mount-si", "Mount Si", "WA", "us", "Mount Si Natural Resources Conservation Area (DNR)", "day", 13, 1000, 1, "4-11", "coastal-wet", "black",
     "permit", "https://www.dnr.wa.gov/MountSi"),
    ("rainier-skyline", "Skyline Trail (Paradise)", "WA", "us", "Mount Rainier National Park", "day", 9, 520, 1, "7-9", "alpine", "black",
     "permit snow", "https://www.nps.gov/mora/"),
    ("wonderland-trail", "Wonderland Trail", "WA", "us", "Mount Rainier National Park", "thru", 150, 6700, 11, "7-9", "alpine", "black",
     "permit ford snow", "https://www.nps.gov/mora/"),
    ("enchantments", "The Enchantments (through-hike)", "WA", "us", "Alpine Lakes Wilderness (Okanogan-Wenatchee NF)", "day", 29, 1400, 1, "7-9",
     "alpine", "black", "permit scramble snow oneway", "https://www.fs.usda.gov/okawen"),
    ("hoh-river", "Hoh River Trail to Glacier Meadows", "WA", "us", "Olympic National Park", "multi", 56, 1100, 3, "6-9", "coastal-wet", "black",
     "permit canister", "https://www.nps.gov/olym/"),
    # ---- Oregon
    ("timberline-trail", "Timberline Trail", "OR", "us", "Mount Hood National Forest", "multi", 66, 2700, 4, "7-9", "alpine", "black",
     "ford snow", "https://www.fs.usda.gov/mthood"),
    ("south-sister", "South Sister", "OR", "us", "Three Sisters Wilderness (Deschutes NF)", "day", 19, 1500, 1, "7-9", "alpine", "black",
     "permit altitude", "https://www.fs.usda.gov/deschutes"),
    ("multnomah-wahkeena", "Multnomah–Wahkeena Loop", "OR", "us", "Columbia River Gorge NSA", "day", 8, 500, 1, "3-11", "coastal-wet", "black",
     "permit", "https://www.fs.usda.gov/crgnsa"),
    # ---- California
    ("half-dome", "Half Dome", "CA", "us", "Yosemite National Park", "day", 26, 1460, 1, "6-10", "mountain", "black",
     "permit exposure altitude", "https://www.nps.gov/yose/"),
    ("mount-whitney", "Mount Whitney", "CA", "us", "Inyo National Forest", "day", 35, 1900, 1, "7-9", "alpine", "black",
     "permit canister altitude lightning", "https://www.fs.usda.gov/inyo"),
    ("john-muir-trail", "John Muir Trail", "CA", "us", "Yosemite, Sequoia & Kings Canyon NPs + Inyo/Sierra NFs", "thru", 340, 14000, 21, "7-9",
     "alpine", "black", "permit canister altitude ford lightning oneway", "https://www.nps.gov/yose/"),
    ("rae-lakes-loop", "Rae Lakes Loop", "CA", "us", "Kings Canyon National Park", "multi", 66, 2100, 5, "7-9", "alpine", "black",
     "permit canister altitude", "https://www.nps.gov/seki/"),
    ("lost-coast", "Lost Coast Trail (north)", "CA", "us", "King Range National Conservation Area (BLM)", "multi", 40, 300, 3, "5-10",
     "coastal-wet", "black", "permit canister tide oneway", "https://www.blm.gov/programs/national-conservation-lands/california/king-range"),
    ("tahoe-rim-trail", "Tahoe Rim Trail", "CA", "us", "Tahoe Rim Trail Association / Lake Tahoe Basin NF", "thru", 265, 7300, 14, "7-9",
     "alpine", "black", "permit water-scarce altitude", "https://tahoerimtrail.org/"),
    ("lassen-peak", "Lassen Peak", "CA", "us", "Lassen Volcanic National Park", "day", 8, 600, 1, "7-10", "alpine", "black", "altitude snow",
     "https://www.nps.gov/lavo/"),
    # ---- Colorado
    ("four-pass-loop", "Four Pass Loop", "CO", "us", "Maroon Bells-Snowmass Wilderness (White River NF)", "multi", 43, 2400, 3, "7-9", "alpine",
     "black", "permit canister altitude lightning", "https://www.fs.usda.gov/whiteriver"),
    ("quandary-peak", "Quandary Peak", "CO", "us", "Pike-San Isabel NF / White River NF", "day", 11, 1000, 1, "6-9", "alpine", "black",
     "altitude lightning", "https://www.fs.usda.gov/whiteriver"),
    ("sky-pond", "Sky Pond", "CO", "us", "Rocky Mountain National Park", "day", 14.5, 520, 1, "6-10", "alpine", "black",
     "permit altitude scramble", "https://www.nps.gov/romo/"),
    ("colorado-trail", "Colorado Trail", "CO", "us", "Colorado Trail Foundation", "thru", 780, 27000, 40, "7-9", "alpine", "black",
     "altitude lightning water-scarce oneway", "https://coloradotrail.org/"),
    # ---- Utah
    ("angels-landing", "Angels Landing", "UT", "us", "Zion National Park", "day", 8.7, 450, 1, "3-11", "canyon", "none",
     "permit exposure heat", "https://www.nps.gov/zion/"),
    ("zion-narrows", "The Narrows (bottom-up)", "UT", "us", "Zion National Park", "day", 15, 100, 1, "6-10", "canyon", "none",
     "ford cold-water", "https://www.nps.gov/zion/"),
    ("delicate-arch", "Delicate Arch", "UT", "us", "Arches National Park", "day", 5, 150, 1, "3-11", "desert", "none", "permit heat water-scarce",
     "https://www.nps.gov/arch/"),
    ("queens-garden-navajo", "Queen's Garden & Navajo Loop", "UT", "us", "Bryce Canyon National Park", "day", 5, 180, 1, "4-10", "desert", "none",
     "altitude heat", "https://www.nps.gov/brca/"),
    ("chesler-park", "Chesler Park Loop", "UT", "us", "Canyonlands National Park (Needles)", "day", 18, 400, 1, "3-5,9-11", "desert", "none",
     "heat water-scarce navigation", "https://www.nps.gov/cany/"),
    # ---- Arizona
    ("grand-canyon-r2r", "Grand Canyon Rim to Rim", "AZ", "us", "Grand Canyon National Park", "multi", 38, 1800, 3, "5-6,9-10", "canyon", "none",
     "permit heat water-scarce oneway", "https://www.nps.gov/grca/"),
    ("plateau-point", "Bright Angel Trail to Plateau Point", "AZ", "us", "Grand Canyon National Park", "day", 19, 940, 1, "3-5,10-11", "canyon",
     "none", "heat water-scarce", "https://www.nps.gov/grca/"),
    ("havasu-falls", "Havasu Falls", "AZ", "us", "Havasupai Tribe (Havasu Canyon)", "multi", 32, 750, 3, "2-6,9-11", "canyon", "none",
     "permit heat", "https://theofficialhavasupaitribe.com/"),
    ("humphreys-peak", "Humphreys Peak", "AZ", "us", "Kachina Peaks Wilderness (Coconino NF)", "day", 16, 1000, 1, "6-10", "alpine", "black",
     "altitude lightning", "https://www.fs.usda.gov/coconino"),
    # ---- Montana / Wyoming / Idaho
    ("grinnell-glacier", "Grinnell Glacier", "MT", "us", "Glacier National Park", "day", 17, 600, 1, "7-9", "alpine", "grizzly", "permit snow",
     "https://www.nps.gov/glac/"),
    ("highline-trail", "Highline Trail (Logan Pass to the Loop)", "MT", "us", "Glacier National Park", "day", 19, 520, 1, "7-9", "alpine", "grizzly",
     "permit exposure oneway", "https://www.nps.gov/glac/"),
    ("cascade-canyon", "Cascade Canyon", "WY", "us", "Grand Teton National Park", "day", 15, 330, 1, "6-9", "mountain", "grizzly", "",
     "https://www.nps.gov/grte/"),
    ("teton-crest", "Teton Crest Trail", "WY", "us", "Grand Teton National Park / Caribou-Targhee NF", "multi", 64, 2700, 4, "7-9", "alpine",
     "grizzly", "permit canister snow altitude oneway", "https://www.nps.gov/grte/"),
    ("mount-washburn", "Mount Washburn", "WY", "us", "Yellowstone National Park", "day", 10, 430, 1, "7-9", "alpine", "grizzly", "altitude lightning",
     "https://www.nps.gov/yell/"),
    ("alice-toxaway", "Alice–Toxaway Loop", "ID", "us", "Sawtooth Wilderness (Sawtooth NRA)", "multi", 30, 900, 2, "7-9", "alpine", "black",
     "permit", "https://www.fs.usda.gov/sawtooth"),
    # ---- Alaska
    ("harding-icefield", "Harding Icefield Trail", "AK", "us", "Kenai Fjords National Park", "day", 13, 1000, 1, "7-9", "alpine", "grizzly", "snow",
     "https://www.nps.gov/kefj/"),
    ("crow-pass", "Crow Pass Trail", "AK", "us", "Chugach State Park", "multi", 37, 1000, 2, "7-9", "alpine", "grizzly", "ford snow oneway",
     "https://dnr.alaska.gov/parks/units/chugach/"),
    # ---- the US Northeast and Appalachians
    ("presidential-traverse", "Presidential Traverse", "NH", "us", "White Mountain National Forest", "day", 32, 2700, 1, "6-9", "alpine", "black",
     "exposure lightning oneway", "https://www.fs.usda.gov/whitemountain"),
    ("franconia-ridge", "Franconia Ridge Loop", "NH", "us", "White Mountain National Forest", "day", 14, 1160, 1, "5-10", "alpine", "black",
     "exposure", "https://www.fs.usda.gov/whitemountain"),
    ("katahdin", "Mount Katahdin (Hunt Trail)", "ME", "us", "Baxter State Park", "day", 16, 1250, 1, "6-10", "alpine", "black",
     "permit scramble exposure", "https://baxterstatepark.org/"),
    ("long-trail", "Long Trail", "VT", "us", "Green Mountain Club", "thru", 438, 20000, 25, "6-9", "forest-humid", "black", "bugs oneway",
     "https://www.greenmountainclub.org/"),
    ("mount-marcy", "Mount Marcy", "NY", "us", "High Peaks Wilderness (Adirondack Park)", "day", 24, 1000, 1, "6-10", "alpine", "black",
     "permit canister", "https://dec.ny.gov/"),
    ("old-rag", "Old Rag", "VA", "us", "Shenandoah National Park", "day", 15, 800, 1, "4-11", "forest-humid", "black", "permit scramble",
     "https://www.nps.gov/shen/"),
    ("alum-cave-leconte", "Alum Cave Trail to Mount LeConte", "TN", "us", "Great Smoky Mountains National Park", "day", 18, 850, 1, "4-11",
     "forest-humid", "black", "permit", "https://www.nps.gov/grsm/"),
    ("superior-hiking-trail", "Superior Hiking Trail", "MN", "us", "Superior Hiking Trail Association", "thru", 500, 12000, 30, "6-9",
     "boreal", "black", "bugs oneway", "https://superiorhiking.org/"),
    # ---- the long trails
    ("appalachian-trail", "Appalachian Trail", "GA–ME", "us", "Appalachian Trail Conservancy / NPS", "thru", 3530, 140000, 170, "3-10",
     "forest-humid", "black", "permit canister bugs oneway", "https://appalachiantrail.org/"),
    ("pacific-crest-trail", "Pacific Crest Trail", "CA–WA", "us", "Pacific Crest Trail Association / USFS", "thru", 4270, 150000, 150, "4-9",
     "alpine", "black", "permit canister altitude heat water-scarce snow ford oneway", "https://www.pcta.org/"),
    ("continental-divide-trail", "Continental Divide Trail", "NM–MT", "us", "Continental Divide Trail Coalition / USFS", "thru", 5000, 140000, 160,
     "4-9", "alpine", "grizzly", "permit altitude water-scarce snow lightning navigation oneway", "https://continentaldividetrail.org/"),
]

KEYS = ("slug", "name", "region", "side", "park", "kind", "km", "gain_m", "days", "months", "climate", "bears", "flags", "src")


def _months(s):
    out = set()
    for part in s.split(","):
        a, _, b = part.partition("-")
        a, b = int(a), int(b or a)
        out |= set(range(a, b + 1)) if a <= b else set(range(a, 13)) | set(range(1, b + 1))
    return sorted(out)


HIKES = []
for row in H:
    h = dict(zip(KEYS, row))
    h["flags"] = h["flags"].split()
    h["months"] = _months(h["months"])
    h["checked"] = False
    HIKES.append(h)
BY = {h["slug"]: h for h in HIKES}

# Oct 25: figures re-read on the park's / trail's own page (slug -> km, climb in m or None when the page gives none, the page, extra).
# Only these show distance/climb on the live trail gear lists (hike_pages.py); the rest wait for their own check.
PC = "https://parks.canada.ca/pn-np"
VERIFIED = {
    "frosty-mountain": (20.8, 1150, "https://bcparks.ca/ec-manning-park/", {}),            # 10.4 km one way from Lightning Lakes, 1,150 m
    "juan-de-fuca": (47, None, "https://bcparks.ca/juan-de-fuca-park/", {}),
    "cape-scott": (47.2, None, "https://bcparks.ca/cape-scott-park/hiking/", {"name": "Cape Scott Trail (to the lighthouse)"}),   # 23.6 km one way
    "iceline": (20.3, 1090, f"{PC}/bc/yoho/activ/randonnee-hike/jour-day", {}),           # Iceline via Little Yoho, loop
    "rockwall": (54.1, 3405, f"{PC}/bc/kootenay/activ/arrierepays-backcountry", {"oneway": True}),
    "plain-of-six-glaciers": (11.8, 595, f"{PC}/ab/banff/activ/randonnee-hiking", {}),     # 5.9 km one way, 595 m
    "cory-pass": (13, None, f"{PC}/ab/banff/activ/randonnee-hiking", {}),
    "sulphur-skyline": (8.8, 700, f"{PC}/ab/jasper/activ/experience/sentiers-trails/miette", {}),
    "crypt-lake": (17.2, None, f"{PC}/ab/waterton/activ/experiences/randonee-hiking", {}),
    "carthew-alderson": (20.1, None, f"{PC}/ab/waterton/activ/experiences/randonee-hiking/journee-day", {"oneway": True}),
    "chilkoot": (53, None, "https://parks.canada.ca/lhn-nhs/yt/chilkoot/visit", {}),
    "kings-throne": (10, 548, f"{PC}/yt/kluane/activ/randonnee-hiking/kings-throne", {"name": "King's Throne (to the cirque)"}),
    "algonquin-highland": (35, None, "https://www.ontarioparks.ca/park/algonquin/backcountry/activities", {}),
    "centennial-ridges": (10, None, "https://www.ontarioparks.ca/park/algonquin/activities", {}),
    "la-cloche-silhouette": (80, None, "https://www.ontarioparks.ca/park/killarney/activities", {}),
    "top-of-the-giant": (21.8, None, "https://www.ontarioparks.ca/park/sleepinggiant/activities", {}),
    "cape-breton-skyline": (8, None, f"{PC}/ns/cbreton/activ/randonnee-hiking/skyline", {}),   # 8 km loop (6.5 km out and back)
    "gros-morne-mountain": (17, 1000, f"{PC}/nl/grosmorne/activ/experiences/randonnee-hiking", {}),
    "long-range-traverse": (35, None, f"{PC}/nl/grosmorne/activ/experiences/arriere-pays-backcountry", {}),
    "cape-chignecto": (52, None, "https://parks.novascotia.ca/park/cape-chignecto", {}),
    "rainier-skyline": (8, None, "https://www.nps.gov/mora/planyourvisit/trails-of-mount-rainier.htm", {}),   # 5 miles
    "wonderland-trail": (150, None, "https://www.nps.gov/mora/planyourvisit/trails-of-mount-rainier.htm", {}),   # 93 miles
    "john-muir-trail": (338, None, "https://www.nps.gov/yose/planyourvisit/brochures.htm", {}),   # 210 miles
    "angels-landing": (8.7, 454, "https://www.nps.gov/zion/planyourvisit/angels-landing-hiking-permits.htm", {}),
    "delicate-arch": (4.8, None, "https://www.nps.gov/arch/", {}),
    "queens-garden-navajo": (4.7, None, "https://www.nps.gov/brca/", {}),
    "superior-hiking-trail": (483, None, "https://superiorhiking.org/", {}),               # 300 miles
}
for s, (km, gain, url, extra) in VERIFIED.items():
    h = BY[s]
    h.update(km=km, src=url, checked=True, gain_ok=gain is not None, **{k: v for k, v in extra.items() if k != "oneway"})
    if gain is not None:
        h["gain_m"] = gain
    if extra.get("oneway") and "oneway" not in h["flags"]:
        h["flags"].append("oneway")

# ---------------------------------------------------------------- the gear rules
# (key, EN, FR, why EN, why FR, shop link: (group, type) on the Hiking tab or None)
ESSENTIALS = [
    ("nav", "Navigation: map, compass or GPS app with offline maps", "Navigation : carte, boussole ou appli GPS hors ligne",
     "The first of the 10 essentials: phones lose signal and batteries.", "Le premier des 10 essentiels : les téléphones perdent le signal.",
     ("gear", "nav")),
    ("light", "Headlamp + spare batteries", "Frontale + piles de rechange", "Hikes run late more often than planned.",
     "Les randonnées finissent souvent plus tard que prévu.", ("gear", "light")),
    ("sun", "Sun protection: sunglasses, sun hat, sunscreen", "Protection solaire : lunettes, chapeau, crème", "UV is stronger with altitude and on snow.",
     "Les UV sont plus forts en altitude et sur la neige.", ("headwear", None)),
    ("firstaid", "First-aid kit (with blister care)", "Trousse de premiers soins (ampoules incluses)", "Blisters and small cuts are the most common problems.",
     "Ampoules et petites coupures sont les problèmes les plus fréquents.", ("gear", "safety")),
    ("knife", "Knife or multi-tool + repair tape", "Couteau ou outil multifonction + ruban de réparation", "For gear repairs and first aid.",
     "Pour réparer l'équipement et les premiers soins.", None),
    ("fire", "Fire: lighter or waterproof matches", "Feu : briquet ou allumettes imperméables", "For warmth in an emergency.",
     "Pour se réchauffer en cas d'urgence.", None),
    ("shelter", "Emergency shelter: space blanket or bivvy", "Abri d'urgence : couverture de survie ou bivouac", "If you're stuck out overnight.",
     "Si vous devez passer la nuit dehors.", ("gear", "safety")),
    ("food", "Extra food (a day's worth more than you plan)", "Nourriture en plus (une journée de plus)", "Delays happen.",
     "Les retards arrivent.", None),
    ("water", "Extra water + a way to treat it", "Eau en plus + de quoi la traiter", "Streams can carry giardia; dry trails have none.",
     "Les ruisseaux peuvent contenir la giardia; les sentiers secs n'en ont pas.", ("gear", "water")),
    ("layers", "Extra layers: warm layer + rain shell", "Couches en plus : vêtement chaud + imperméable", "Mountain weather turns fast.",
     "La météo en montagne change vite.", ("tops", "shell")),
]


def gear_for(h, days=None, month=None):
    """The list for one hike: the 10 essentials, then what the hike, its length and the month add. Each line: dict(key, en, fr, why_en,
    why_fr, shop, level) with level "essential" | "recommended" | "required" (only what the park itself requires)."""
    days = days or h["days"]
    fl = set(h["flags"])
    out = [dict(zip(("key", "en", "fr", "why_en", "why_fr", "shop"), e), level="essential") for e in ESSENTIALS]

    def add(key, en, fr, why_en, why_fr, shop=None, level="recommended"):
        if not any(x["key"] == key for x in out):
            out.append(dict(key=key, en=en, fr=fr, why_en=why_en, why_fr=why_fr, shop=shop, level=level))
    # footwear and clothing for the terrain
    rough = h["gain_m"] >= 800 or h["climate"] in ("alpine", "mountain") or "scramble" in fl
    add("boots", "Hiking boots" if rough or days > 1 else "Hiking shoes", "Bottes de randonnée" if rough or days > 1 else "Chaussures de randonnée",
        "Rocky, steep ground and a heavier pack: ankle support and a stiffer sole." if rough or days > 1 else "Good grip on a moderate trail.",
        "Terrain rocailleux, pentes et sac plus lourd : soutien et semelle rigide." if rough or days > 1 else "Bonne adhérence sur un sentier modéré.",
        ("shoes", "boot" if rough or days > 1 else "hike"))
    add("socks", "Wool hiking socks (+ a dry pair)", "Bas de laine de randonnée (+ une paire sèche)", "Dry feet = no blisters.",
        "Pieds secs = pas d'ampoules.", ("socks", None))
    add("pack", "Overnight pack (35 L+)" if days > 1 else "Day pack (20–30 L)", "Sac de plusieurs jours (35 L+)" if days > 1 else "Sac de jour (20-30 L)",
        "Room for the essentials" + (" and a night's gear." if days > 1 else "."), "De la place pour les essentiels" + (" et le matériel de nuit." if days > 1 else "."),
        ("packs", "overnight" if days > 1 else "day"))
    if h["gain_m"] >= 700 or days > 1:
        add("poles", "Trekking poles", "Bâtons de randonnée",
            f"About {h['gain_m']:,} m of climbing: poles save your knees on the way down." if h.get("gain_ok") else "A long climb or a heavy pack: poles save your knees on the way down.",
            f"Environ {h['gain_m']:,} m de dénivelé : les bâtons ménagent vos genoux à la descente." if h.get("gain_ok") else "Longue montée ou sac lourd : les bâtons ménagent vos genoux à la descente.",
            ("gear", "pole"))
    wet = h["climate"] in ("coastal-wet", "forest-humid")
    if wet:
        add("rainpants", "Rain pants", "Pantalon imperméable", "A wet-climate trail: rain is likely in any season.",
            "Un sentier en climat humide : la pluie est probable en toute saison.", ("bottoms", "rain"))
    if h["climate"] in ("alpine", "mountain", "boreal") or (month in (5, 6, 9, 10) if month else False):
        add("insulated", "Insulated jacket (down or synthetic)", "Manteau isolé (duvet ou synthétique)",
            "Above treeline and in spring/fall it can be near freezing, even in summer at the summit.",
            "Au-dessus de la limite des arbres et au printemps/automne, il peut faire près de zéro, même l'été au sommet.", ("tops", "insulated"))
        add("toque", "Warm hat + gloves", "Tuque + gants", "Wind on ridges and summits.", "Le vent sur les crêtes et les sommets.", ("headwear", None))
    if h["climate"] in ("desert", "canyon") or "heat" in fl:
        add("sunshirt", "Light sun shirt + wide-brim hat", "Chandail solaire léger + chapeau à large bord", "Hot and exposed: cover up, don't just sunscreen.",
            "Chaud et à découvert : couvrez-vous plutôt que seulement la crème.", ("tops", "shirt"))
        add("water3", "3–4 L of water capacity", "Capacité de 3-4 L d'eau", "Little or no water on the trail; heat raises what you drink.",
            "Peu ou pas d'eau sur le sentier; la chaleur fait boire plus.", ("gear", "water"))
    if "water-scarce" in fl and not any(x["key"] == "water3" for x in out):
        add("water3", "Extra water capacity (3 L+)", "Plus de capacité d'eau (3 L+)", "Water sources are far apart or dry late in the season.",
            "Les sources d'eau sont espacées ou à sec en fin de saison.", ("gear", "water"))
    # wildlife
    if h["bears"] == "grizzly":
        add("bearspray", "Bear spray (in a holster you can reach)", "Chasse-ours en aérosol (dans un étui accessible)",
            "Grizzly country: carry it where you can reach it in seconds.", "Territoire du grizzli : à portée de main en quelques secondes.",
            None)   # the stores we read don't sell it online (it doesn't ship): a checklist line
    elif h["bears"] == "black":
        add("bearspray", "Bear spray", "Chasse-ours en aérosol", "Black bears live here; spray is the proven deterrent.",
            "Des ours noirs vivent ici; l'aérosol est le moyen de dissuasion éprouvé.", None)
    if "canister" in fl and days > 1:
        add("canister", "Approved bear canister", "Contenant anti-ours approuvé", "The park requires one for overnight trips.",
            "Le parc l'exige pour les nuits en camping.", None, level="required")
    elif h["bears"] != "none" and days > 1:
        add("foodbag", "Bear hang kit or food storage (use the food lockers where provided)", "Corde pour suspendre la nourriture ou casier",
            "Food stored away from your tent keeps bears wild.", "Ranger la nourriture loin de la tente garde les ours sauvages.", None)
    if "bugs" in fl and (not month or month in (5, 6, 7)):
        add("bugs", "Bug net + repellent", "Moustiquaire de tête + chasse-moustiques", "Black flies and mosquitoes peak in early summer.",
            "Mouches noires et moustiques au maximum au début de l'été.", None)
    # terrain and conditions
    if "snow" in fl and (not month or month in (5, 6, 7, 9, 10)):
        add("traction", "Microspikes (trail crampons)", "Crampons de sentier", "Snow and ice linger on this trail early and late in the season.",
            "Neige et glace restent sur ce sentier en début et en fin de saison.", ("gear", "traction"))
        add("gaiters", "Gaiters", "Guêtres", "Keep snow and mud out of your boots.", "Gardent la neige et la boue hors des bottes.", ("gear", "gaiter"))
    if "ford" in fl:
        add("fordshoes", "Camp shoes or sandals for river crossings", "Souliers de camp ou sandales pour traverser les rivières",
            "Unbridged crossings: keep your boots dry and your footing sure.", "Traversées sans pont : bottes au sec et pieds sûrs.", None)
    if "tide" in fl:
        add("tides", "Tide table for your dates", "Table des marées pour vos dates", "Some beach sections are only passable at low tide.",
            "Certains passages de plage ne se font qu'à marée basse.", None, level="required")
    if "altitude" in fl or "lightning" in fl:
        add("early", "Start early; turn around by noon if storms build", "Partir tôt; faire demi-tour vers midi si l'orage menace",
            "Afternoon thunderstorms are common above treeline.", "Les orages d'après-midi sont fréquents au-dessus de la limite des arbres.", None)
    if "navigation" in fl:
        add("gpsdevice", "GPS device or app with the route loaded + paper map", "GPS ou appli avec le tracé + carte papier",
            "Parts of the route are unmarked.", "Certaines parties du parcours ne sont pas balisées.", ("gear", "nav"))
    if days >= 3 or h["kind"] == "thru" or "navigation" in fl:
        add("messenger", "Satellite messenger (inReach or similar)", "Messager satellite (inReach ou autre)", "No cell signal for most of it.",
            "Pas de réseau cellulaire sur la majeure partie.", ("gear", "safety"))
    if "cold-water" in fl:
        add("drysack", "Dry bags for clothes and sleeping bag", "Sacs étanches pour vêtements et sac de couchage", "Cold, wet conditions: a wet sleeping bag is dangerous.",
            "Froid et humide : un sac de couchage mouillé est dangereux.", None)
    # overnight: camping (read, not published: links go to the camp catalogue later)
    if days > 1 and "huts" not in fl:
        add("tent", "Tent or shelter", "Tente ou abri", "Overnight on the trail.", "Nuit sur le sentier.", None)
        add("sleep", "Sleeping bag + pad rated for the season", "Sac de couchage + matelas pour la saison", "Nights are cold in the mountains.",
            "Les nuits sont froides en montagne.", None)
        add("stove", "Stove, fuel, pot", "Réchaud, combustible, chaudron", "Hot food and water.", "Repas chauds et eau.", None)
    elif days > 1:
        add("hutbag", "Sleeping bag (huts usually provide only a mattress)", "Sac de couchage (les refuges offrent souvent seulement le matelas)",
            "Check what your hut or refuge provides.", "Vérifiez ce que fournit votre refuge.", None)
    if "permit" in fl:
        add("permit", "Permit or reservation", "Permis ou réservation", "This park/trail requires one (dates, quotas or parking). Check its page.",
            "Ce parc ou sentier en exige un (dates, quotas ou stationnement). Vérifiez sa page.", None, level="required")
    return out


def check():
    slugs = [h["slug"] for h in HIKES]
    assert len(slugs) == len(set(slugs)), "duplicate slug"
    for h in HIKES:
        assert h["kind"] in ("day", "overnight", "multi", "thru"), h["slug"]
        assert h["bears"] in ("grizzly", "black", "none"), h["slug"]
        assert h["src"].startswith("https://"), h["slug"]
        assert h["months"], h["slug"]
    return len(HIKES)


if __name__ == "__main__":
    n = check()
    if len(sys.argv) > 1:
        h = BY[sys.argv[1]]
        for x in gear_for(h, int(sys.argv[2]) if len(sys.argv) > 2 else None, int(sys.argv[3]) if len(sys.argv) > 3 else None):
            print(f"[{x['level']}] {x['en']}  ({x['why_en']})  -> {x['shop']}")
    else:
        import collections
        print(n, "hikes;", dict(collections.Counter(h["side"] for h in HIKES)), dict(collections.Counter(h["kind"] for h in HIKES)),
              dict(collections.Counter(h["bears"] for h in HIKES)))
