"""Build a draft property from a web page link.

Used by the website editor's "Import from a link" button (.github/workflows/import-url.yml).
Reads what the page publishes about itself (schema.org data, Open Graph tags, the visible text),
fills in as many fields as it can, downloads the photos, and saves the result to
content/listings/<ref>.json as a DRAFT: "Show on website" and "photo rights" are left unticked,
so a person checks every field and confirms permission before it can go live.

Usage: python3 listings/import_url.py URL [agent_id] [ref]
"""
import json, os, re, sys, hashlib, datetime, urllib.request, urllib.parse
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import data as D  # site areas

UA = {"User-Agent": "Mozilla/5.0 (compatible; ShelPropertyImporter/1.0; +https://shelproperty.com)",
      "Accept-Language": "en-GB,en;q=0.8"}
TYPES = ["Penthouse", "Studio", "Townhouse", "Semi-detached house", "Detached house", "Villa", "Bungalow",
         "Maisonette", "Apartment", "Building plot", "Land"]
TYPE_WORDS = [("penthouse", "Penthouse"), ("studio", "Studio"), ("town house", "Townhouse"), ("townhouse", "Townhouse"),
              ("semi-detached", "Semi-detached house"), ("semi detached", "Semi-detached house"), ("bungalow", "Bungalow"),
              ("maisonette", "Maisonette"), ("villa", "Villa"), ("detached house", "Detached house"), ("detached", "Detached house"),
              ("apartment", "Apartment"), ("flat", "Apartment"), ("building plot", "Building plot"), ("plot", "Building plot"),
              ("land", "Land")]

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        b = r.read()
        return b if binary else b.decode(r.headers.get_content_charset() or "utf-8", "replace")

def walk_ld(obj):
    if isinstance(obj, list):
        for o in obj: yield from walk_ld(o)
    elif isinstance(obj, dict):
        yield obj
        for k in ("@graph", "mainEntity", "itemOffered", "offers", "about"):
            if k in obj: yield from walk_ld(obj[k])

def num(s):
    if s is None: return None
    s = re.sub(r"[^\d.,]", "", str(s))
    if not s: return None
    if re.search(r"[.,]\d{3}($|[.,])", s): s = s.replace(",", "").replace(".", "")
    else: s = s.replace(",", ".")
    try:
        v = float(s); return int(v) if v.is_integer() else v
    except ValueError:
        return None

def first(*vals):
    for v in vals:
        if v not in (None, "", []): return v
    return None

def extract(url, html):
    soup = BeautifulSoup(html, "html.parser")
    meta = lambda *names: first(*[(soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n}) or {}).get("content") for n in names])
    ld = []
    for s in soup.find_all("script", type="application/ld+json"):
        try: ld += list(walk_ld(json.loads(s.string or "")))
        except Exception: pass
    for t in soup(["script", "style", "noscript", "svg"]): t.decompose()
    h1 = soup.find("h1")
    h1 = re.sub(r"\s+", " ", h1.get_text(" ")).strip() if h1 else None
    paras = [re.sub(r"\s+", " ", p.get_text(" ")).strip() for p in soup.find_all(["p", "div"]) if not p.find(["p", "div"])]
    def prose(x):  # real sentences, not a menu of links
        return 120 < len(x) < 3000 and "cookie" not in x.lower() and len(re.findall(r"[a-z][.!?](?:\s|$)", x)) >= 2 \
            and len(re.findall(r"\b[A-Z][a-z]+", x)) < len(x.split()) * 0.5
    long_para = max((x for x in paras if prose(x)), key=len, default=None)
    gone = " ".join(filter(None, [h1, soup.title.string if soup.title else ""])).lower()
    if re.search(r"not found|404|no longer available|has been sold|page cannot be found|doesn.t exist", gone):
        raise ValueError("this page says the property isn't there any more (sold, removed or a wrong link)")
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    low = text.lower()

    def ldv(*keys):
        for o in ld:
            for k in keys:
                v = o.get(k)
                if isinstance(v, dict): v = v.get("value") or v.get("name")
                if v not in (None, "", []): return v
        return None

    site = (meta("og:site_name") or "").lower()
    cands = [h1, ldv("name"), meta("og:title", "twitter:title"), soup.title.string if soup.title else None]
    cands = [re.split(r"\s+[|–]\s+", c.strip())[0] for c in cands if isinstance(c, str) and c.strip()]
    title = next((c for c in cands if c.lower() != site and len(c) > 8 and not re.search(r"group|ltd|limited|estates?$|realty$", c, re.I)), cands[0] if cands else None)
    desc = first(ldv("description"), meta("og:description", "description"))
    if desc: desc = re.sub(r"\s+", " ", BeautifulSoup(str(desc), "html.parser").get_text(" ")).strip()
    if long_para and (not desc or len(desc) < 160 or re.search(r"we've got information|for sale at", desc, re.I)): desc = long_para
    if desc and re.search(r"we've got information|for sale at [A-Z ]+\.?$", desc, re.I): desc = None  # site boilerplate: leave for a person
    head = " ".join(filter(None, [title, urllib.parse.unquote(url).replace("-", " ").lower()])).lower()
    price = num(first(ldv("price"), meta("product:price:amount", "og:price:amount")))
    if not price:
        m = re.search(r"(?:€|eur\s?)\s?(\d{1,3}(?:[.,\s]\d{3})+|\d{4,})", text, re.I) or re.search(r"(\d{1,3}(?:[.,]\d{3})+)\s?(?:€|eur)", text, re.I)
        price = num(m.group(1)) if m else None
    beds = num(ldv("numberOfBedrooms", "numberOfRooms"))
    if not beds:
        m = re.search(r"(\d{1,2})\s*(?:-|\s)?(?:bed(?:room)?s?|br)\b", head) or re.search(r"(\d{1,2})\s*(?:-|\s)?(?:bed(?:room)?s?|br)\b", low)
        beds = num(m.group(1)) if m else None
    baths = num(ldv("numberOfBathroomsTotal", "numberOfFullBathrooms"))
    if not baths:
        m = re.search(r"(\d{1,2})\s*(?:bath(?:room)?s?)\b", low); baths = num(m.group(1)) if m else None
    m2 = r"(\d{2,5}(?:[.,]\d+)?)\s*(?:m2|m²|sq\.?\s?m|sqm|square met)"
    cov = re.search(r"(?:covered|internal|living|built|indoor)[^0-9]{0,25}" + m2, low)
    plot = re.search(r"(?:plot|land|lot)[^0-9]{0,25}" + m2, low)
    any_m2 = re.search(m2, low)
    covered = num(first(ldv("floorSize"), cov.group(1) if cov else None, any_m2.group(1) if any_m2 and not plot else None))
    plot_m2 = num(plot.group(1)) if plot else None
    m = re.search(r"energy\s*(?:efficiency\s*)?(?:class|rating|certificate)?\s*[:\-]?\s*\b([a-g])\b(?![a-z])", low)
    energy = m.group(1).upper() if m else None
    deed = "issued" if re.search(r"title deeds?\s*(?:[:\-]\s*)?(?:are\s+|is\s+)?(?:issued|available|yes|in place|ready)", low) else \
           "pending" if re.search(r"title deeds?\s*(?:[:\-]\s*)?(?:pending|not yet|awaiting|no\b)", low) else \
           "after-completion" if re.search(r"title deeds?\s+(?:after|upon|on)\s+completion", low) else None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(km|m)\s+(?:from|to)\s+(?:the\s+)?(?:sea|beach|coast)", low)
    sea = (num(m.group(1)) / (1000 if m.group(2) == "m" else 1)) if m else None
    m = re.search(r"(?:built|construction|completed|year built)\D{0,15}((?:19|20)\d{2})", low); year = num(m.group(1)) if m else None
    hay = " ".join(filter(None, [title, url.lower(), low[:4000]])).lower()
    alias = {"pegeia": "peyia", "pegia": "peyia", "kato pafos": "kato-paphos", "chlorakas": "chloraka", "yeroskipou": "geroskipou",
             "polis chrysochous": "polis", "latsi": "latchi", "paphos town": "paphos-town", "paphos centre": "paphos-town",
             "pafos (center)": "paphos-town", "pafos center": "paphos-town", "pafos centre": "paphos-town", "paphos center": "paphos-town",
             "kato pafos": "kato-paphos", "pafos town": "paphos-town", "universal": "paphos-town"}
    def find_area(t):
        hits = []
        for k, v in D.AREAS.items():
            for w in {v["name"].lower(), k.replace("-", " ")} | {a for a, kk in alias.items() if kk == k}:
                if w in ("paphos",): continue
                i = t.find(w)
                if i >= 0: hits.append((i, k))
        return min(hits)[1] if hits else None
    area = find_area(head) or find_area(low[:4000])
    kind = next((t for w, t in TYPE_WORDS if re.search(r"\b" + re.escape(w) + r"\b", head)), None) or \
           next((t for w, t in TYPE_WORDS if w not in ("land", "plot") and re.search(r"\b" + re.escape(w) + r"\b", low[:3000])), None)
    if re.search(r"\bfor sale\b", head): rent = False
    elif re.search(r"\b(for rent|to rent|to let)\b", head): rent = True
    else: rent = bool(re.search(r"\b(per month|/month|monthly rent)\b", low[:3000]))
    newb = bool(re.search(r"\b(new build|new-build|off[- ]plan|under construction|\+ ?vat|plus vat)\b", hay))
    purpose = "to-rent" if rent else "land" if kind in ("Land", "Building plot") else "new-build" if newb else "resale"
    geo = next((o.get("geo") for o in ld if isinstance(o.get("geo"), dict)), {}) or {}
    lat, lng = num(geo.get("latitude")), num(geo.get("longitude"))
    feats = [f for f in ["Private pool", "Communal pool", "Sea view", "Mountain view", "Garden", "Roof garden", "Solar panels",
                         "Air conditioning", "Underfloor heating", "Covered parking", "Garage", "Lift", "Fireplace", "Furnished", "Storage"]
             if f.lower() in low]
    # photos: schema.org, Open Graph, then large images in the page
    imgs = []
    for v in [ldv("image", "photo")] + [t.get("content") for t in soup.find_all("meta", attrs={"property": "og:image"})]:
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, dict): x = x.get("url") or x.get("contentUrl")
            if isinstance(x, str): imgs.append(x)
    for t in BeautifulSoup(html, "html.parser").find_all(["img", "a", "source"]):
        for attr in ("data-src", "data-lazy", "data-original", "src", "href", "srcset", "data-srcset"):
            v = t.get(attr)
            if not v: continue
            v = v.split(",")[-1].strip().split(" ")[0]
            if re.search(r"\.(jpe?g|webp|png)(\?|$)", v, re.I) and not re.search(r"logo|icon|sprite|avatar|flag|placeholder|banner", v, re.I):
                imgs.append(v)
    seen, photos = set(), []
    for u in imgs:
        u = urllib.parse.urljoin(url, u)
        key = re.sub(r"[-_]?\d{2,4}x\d{2,4}", "", u.split("?")[0])
        if key not in seen: seen.add(key); photos.append(u)
    return dict(title=title, description=desc, price=price, bedrooms=beds, bathrooms=baths, covered_m2=covered, plot_m2=plot_m2,
                energy_class=energy, title_deed=deed, distance_to_sea_km=sea, year_built=year, area=area, type=kind,
                purpose=purpose, plus_vat=bool(re.search(r"(?:€\s?[\d.,]{4,}|[\d.,]{4,}\s?€)\s*(?:\+|plus)\s?vat", low) or re.search(r"\+ ?vat|plus vat", head)), latitude=lat, longitude=lng,
                features="|".join(feats)), photos

def main(url, agent_id="", ref=""):
    html = get(url)
    f, photo_urls = extract(url, html)
    ref = re.sub(r"[^A-Za-z0-9-]", "", ref) or "web-" + hashlib.sha1(url.encode()).hexdigest()[:8]
    pdir = os.path.join(ROOT, "content", "photos"); os.makedirs(pdir, exist_ok=True)
    saved = []
    for u in photo_urls:
        if len(saved) >= 15: break
        try:
            b = get(u, binary=True)
        except Exception:
            continue
        if len(b) < 25000: continue  # thumbnails, icons
        name = f"{ref}-{len(saved) + 1}.jpg"
        try:
            from PIL import Image; import io
            im = Image.open(io.BytesIO(b)).convert("RGB")
            if im.width < 500: continue
            im.save(os.path.join(pdir, name), "JPEG", quality=88)
        except Exception:
            continue
        saved.append("/content/photos/" + name)
    today = datetime.date.today().isoformat()
    entry = {"published": False, "ref": ref, "agent_id": agent_id, **f, "photos": saved,
             "photo_caption": "", "photo_rights_confirmed": False, "date_listed": today, "last_confirmed": today,
             "source_url": url, "imported_on": today}
    entry = {k: v for k, v in entry.items() if v is not None}
    print("::notice::Draft " + ref + ": " + str(len(saved)) + " photos; found " + ", ".join(k for k in ("title","price","area","type","bedrooms","bathrooms","covered_m2","title_deed","energy_class") if entry.get(k)))
    out = os.path.join(ROOT, "content", "listings", ref + ".json")
    json.dump(entry, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    missing = [k for k in ("title", "price", "area", "type", "bedrooms", "title_deed", "energy_class", "description") if not entry.get(k)]
    print(f"Saved draft {out} with {len(saved)} photos.")
    print("Check and fill in: " + (", ".join(missing) if missing else "nothing obvious missing"))
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        p = json.loads(os.environ.get("PAYLOAD") or "{}").get("inputs", {})
        a = [p.get("url", ""), p.get("agent_id", ""), p.get("ref", "")]
    try:
        main(*a)
    except Exception as e:
        msg = f"Couldn't import {a[0]}: {type(e).__name__}: {e}"
        if "403" in str(e) or "401" in str(e):
            msg += ". The site blocks automatic reading; ask the agent for their property feed or the details in the onboarding sheet."
        print("::error::" + msg)
        sys.exit(1)
