"""Shared lists for search filters, the website editor and the importer (structure modelled on large Cyprus portals)."""
import re

TYPES = ["House", "Apartment", "Land", "Office", "Shop/Showroom", "Building", "Mixed use building",
         "Warehouse/Factory", "Project", "Restaurant"]
SUBTYPES = {
    "House": ["Detached", "Semi-detached", "Townhouse", "Maisonette", "Bungalow", "Villa"],
    "Apartment": ["Studio", "Ground floor", "Whole floor", "Top floor/penthouse", "Duplex"],
    "Land": ["Plot", "Field", "Development land"],
    "Office": ["Whole floor"],
    "Building": ["Residential", "Commercial"],
}
ALL_SUBTYPES = [s for t in TYPES for s in SUBTYPES.get(t, [])]
CONDITIONS = ["Resale", "Key ready", "Under construction", "Off plan", "Completed", "Incomplete"]
ZONING = ["Residential", "Commercial", "Touristic", "Agricultural", "Industrial"]
FURNISHED = ["Fully furnished", "Partially furnished", "Unfurnished", "Optional furnished"]
PRICES = [50000, 60000, 70000, 80000, 90000, 100000, 110000, 120000, 125000, 130000, 140000, 150000, 160000, 170000,
          175000, 180000, 190000, 200000, 210000, 220000, 230000, 240000, 250000, 260000, 270000, 280000, 290000, 300000,
          325000, 350000, 375000, 400000, 425000, 450000, 475000, 500000, 550000, 600000, 650000, 700000, 750000, 800000,
          850000, 900000, 950000, 1000000, 1250000, 1500000, 1750000, 2000000, 2500000, 3000000, 4000000, 5000000]
COVERED = [10, 15, 20, 30, 40, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]
PLOT = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1250, 1500, 1750, 2000, 2500, 3000,
        4000, 5000, 7500, 10000]
YEARS = list(range(2028, 1969, -1))

# Villages and neighbourhoods of the Paphos district (place names; spellings as used on Cyprus property portals)
LOCALITIES = sorted(set("""Acheleia|Agia Marina Chrysochous|Agia Marina Kelokedaron|Agia Marinouda|Agia Varvara|Agios Dimitrianos|
Agios Georgios|Agios Isidoros|Agios Theodoros|Akamas|Akourdaleia|Akoursos|Amargeti|Anarita|Anavargos|Androlikou|
Aphrodite Hills|Archimandrita|Argaka|Arminou|Armou|Arodes|Asprogia|Axylou|Chlorakas|Choletria|Choli|Choulou|Chrysochou|
Coral Bay|Drousia|Drymou|Emba|Episkopi|Evretou|Filousa|Fyti|Galataria|Geroskipou|Geroskipou Tourist Area|Gialia|Giolou|
Goudi|Ineia|Kallepia|Kamares|Kannaviou|Kathikas|Kato Paphos|Kedares|Kelokedara|Kidasi|Kili|Kissonerga|Koili|Koloni|Konia|
Kouklia|Kritou Marottou|Kritou Tera|Kynousa|Lasa|Latchi|Lemona|Lempa|Letymvou|Limni|Lysos|Makounta|Mamonia|Mandria|
Marathounta|Meladeia|Mesa Chorio|Mesana|Mesogi|Milia|Miliou|Moutallos|Nata|Neo Chorio|Nikokleia|Paphos town|Pano Panagia|
Peyia|Pelathousa|Pentalia|Peristerona|Polemi|Polis|Pomos|Praitori|Prastio|Prodromi|Psathi|Salamiou|Sea Caves|Secret Valley|
Simou|Skoulli|Souskiou|Statos-Agios Fotios|Steni|Stroumbi|Tala|Theletra|Thrinia|Timi|Tombs of the Kings|Trachypedoula|
Tremithousa|Tsada|Universal""".replace("\n", "").split("|")))
ALIASES = {"pegeia": "Peyia", "pegia": "Peyia", "empa": "Emba", "chloraka": "Chlorakas", "kato pafos": "Kato Paphos",
           "pafos (center)": "Paphos town", "pafos": "Paphos town", "paphos": "Paphos town", "yeroskipou": "Geroskipou",
           "polis chrysochous": "Polis", "latsi": "Latchi", "mouttalos": "Moutallos", "trimithousa": "Tremithousa",
           "episcopi paphou": "Episkopi", "mandria pafou": "Mandria", "kili": "Kili", "kilinia": "Kili"}
# our 11 town/area pages
HUB_OF = {"Kato Paphos": "kato-paphos", "Paphos town": "paphos-town", "Chlorakas": "chloraka", "Kissonerga": "kissonerga",
          "Coral Bay": "coral-bay", "Peyia": "peyia", "Tala": "tala", "Emba": "emba", "Geroskipou": "geroskipou",
          "Polis": "polis", "Latchi": "latchi", "Universal": "paphos-town", "Tombs of the Kings": "kato-paphos",
          "Moutallos": "paphos-town", "Anavargos": "paphos-town", "Konia": "paphos-town", "Geroskipou Tourist Area": "geroskipou",
          "Mesogi": "emba", "Tremithousa": "tala", "Sea Caves": "peyia", "Akamas": "peyia", "Argaka": "polis", "Prodromi": "polis"}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

GENERIC = {"pafos", "paphos", "paphos town"}

def find_locality(text):
    t = (text or "").lower()
    best = None
    for name in LOCALITIES + list(ALIASES):
        if name.lower() in GENERIC: continue
        i = t.find(name.lower())
        if i >= 0 and (best is None or i < best[0] or (i == best[0] and len(name) > len(best[1]))):
            best = (i, name)
    if not best:
        return "Paphos town" if re.search(r"\b(pafos|paphos)\s*(town|centre|center|\(cent)", t) else None
    return ALIASES.get(best[1].lower(), best[1]) if best[1] not in LOCALITIES else best[1]

OLD_KIND = {"Apartment": ("Apartment", None), "Penthouse": ("Apartment", "Top floor/penthouse"), "Studio": ("Apartment", "Studio"),
            "Townhouse": ("House", "Townhouse"), "Semi-detached house": ("House", "Semi-detached"),
            "Detached house": ("House", "Detached"), "Villa": ("House", "Villa"), "Bungalow": ("House", "Bungalow"),
            "Maisonette": ("House", "Maisonette"), "Building plot": ("Land", "Plot"), "Land": ("Land", None), "Plot": ("Land", "Plot"),
            "House": ("House", None), "Shop": ("Shop/Showroom", None)}

def type_and_sub(kind, sub=None):
    if kind in TYPES: return kind, (sub or None)
    t, s = OLD_KIND.get(kind or "", ("House", None))
    return t, (sub or s)
