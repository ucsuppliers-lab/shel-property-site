"""Builds the Shel Property draft site into ./out from data.py and templates/."""
import json, os, re, shutil, sys, hashlib
from datetime import date
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "lib"))
import data as D
import i18n as I18N
from seal import wave_seal_g, icon_g
import photos as PH
from PIL import Image as _Im

OUT = os.path.join(HERE, "out")
OCEAN, GOLD_LOGO, GOLD = "#0E4470", "#A88245", "#D9BC8C"

def seal_svg(size, dark=False):
    w = 0.9 if size >= 120 else (1.4 if size >= 60 else (1.8 if size >= 40 else 2.2))
    line, ring = ("#FFFFFF", GOLD) if dark else (OCEAN, GOLD_LOGO)
    return Markup(f'<svg viewBox="0 0 64 64" width="{size}" height="{size}" aria-hidden="true" focusable="false">{wave_seal_g(line, w, ring_color=ring)}</svg>')

FAVICON = "data:image/svg+xml," + re.sub(r"\s+", " ", (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{OCEAN}"/>{icon_g("#FFFFFF", 3.4)}</svg>'
)).replace("#", "%23").replace('"', "'")

ICONS = {
    "bed": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18v-7h18v7M3 14h18M7 11V8h5v3"/></svg>',
    "bath": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h16v3a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4v-3zM6 12V6a2 2 0 0 1 4 0"/></svg>',
    "area": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="1"/><path d="M4 9h3M9 4v3"/></svg>',
    "plot": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 20l4-14h10l4 14z"/><path d="M8 13h8"/></svg>',
    "sea": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M2 15c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2M2 19c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2"/></svg>',
    "heart": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>',
    "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>',
    "chev": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
}

TONES = {"sky": ("#DDEFF8", "#BFE0F2", "#8FC6E6"), "sea": ("#E6F3FA", "#9ED3EC", "#3E8FC4"), "sand": ("#F6EADF", "#DDEFF8", "#9ED3EC")}

def scene(ref, tone):
    """Placeholder 'photo': sky, sea and sand in brand colours, varied by ref. Stands in for real agent photos."""
    h = int(hashlib.md5(ref.encode()).hexdigest()[:6], 16)
    top, mid, sea = TONES[tone]
    horizon = 52 + (h % 14)
    hill = 30 + (h >> 4) % 40
    gid = f"g{ref}{h % 97}"
    return Markup(
        f'<svg class="scene" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{mid}"/></linearGradient></defs>'
        f'<rect width="400" height="300" fill="url(#{gid})"/>'
        f'<path d="M{hill*3} {horizon*3-10} q60 -38 130 -10 t140 4 L400 {horizon*3} L0 {horizon*3} z" fill="#F4EEE2" opacity=".75"/>'
        f'<rect y="{horizon*3}" width="400" height="{300-horizon*3}" fill="{sea}" opacity=".55"/>'
        f'<path d="M0 {horizon*3+18} q25 -6 50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="2"/>'
        f'<path d="M0 {horizon*3+34} q25 -6 50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="2"/>'
        f'<path d="M0 300 L0 {275 - h % 20} Q200 {255 - h % 30} 400 {270 - (h >> 3) % 25} L400 300 z" fill="#E8CBB2"/>'
        f'</svg>')

def photo_img(key, root, alt, eager=False, sizes="(max-width: 700px) 100vw, 400px"):
    m = os.path.join(PH.IMG, f"{key}-m.jpg"); l = os.path.join(PH.IMG, f"{key}-l.jpg")
    w, h = _Im.open(m).size; wl = _Im.open(l).size[0]
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return Markup(f'<img src="{root}img/{key}-m.jpg" srcset="{root}img/{key}-m.jpg {w}w, {root}img/{key}-l.jpg {wl}w" sizes="{sizes}" width="{w}" height="{h}" alt="{alt}" {load}>')

def money(n, lang="en"):
    if lang == "de":
        return "{:,.0f} €".format(n).replace(",", ".")
    return "€{:,.0f}".format(n)

def price_html(l, lang="en"):
    if l["period"] == "night":
        return Markup(f'<small>from</small> {money(l["price"])} <small>a night</small>')
    if l["period"] == "month":
        return Markup(f'{money(l["price"])} <small>a month</small>')
    vat = {"en": "+ VAT", "de": "+ MwSt.", "he": '+ מע"מ'}[lang]
    return Markup(money(l["price"], lang) + (f' <small>{vat}</small>' if l["vat"] else ''))

DEED_T = {"de": {"issued": "Title Deed ausgestellt", "after-completion": "Title Deed nach Fertigstellung", "pending": "Title Deed ausstehend", "n/a": "Pachtobjekt"},
          "he": {"issued": "טאבו הונפק", "after-completion": "טאבו לאחר סיום הבנייה", "pending": "טאבו בהמתנה", "n/a": "נכס בחכירה"}}
def deed_text(k, lang="en"):
    return DEED_T[lang][k] if lang in DEED_T else D.DEED[k]

MONTHS = {"en": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
          "de": ["Jan.","Feb.","März","Apr.","Mai","Juni","Juli","Aug.","Sept.","Okt.","Nov.","Dez."],
          "he": ["בינואר","בפברואר","במרץ","באפריל","במאי","ביוני","ביולי","באוגוסט","בספטמבר","באוקטובר","בנובמבר","בדצמבר"]}
def nice_date(s, lang="en"):
    y, m, d = s.split("-")
    sep = ". " if lang == "de" else " "
    return f"{int(d)}{sep}{MONTHS[lang][int(m)-1]} {y}"

def deed_chip(l, lang="en"):
    cls = {"issued": "chip", "after-completion": "chip", "pending": "chip chip-warn", "n/a": "chip chip-quiet"}[l["deed"]]
    label = deed_text(l["deed"], lang)
    if l["purpose"] == "to-rent":
        cls, label = "chip chip-quiet", "Long let"
    return Markup(f'<span class="{cls}">{label}</span>')

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

HAVE = PH.available()
for l in D.LISTINGS:
    l["photos"] = HAVE.get(l["ref"], [])
    l["area_name"] = D.AREAS[l["area"]]["name"]
    l["agent_obj"] = D.AGENTS[l["agent"]]
    l["path"] = f'property/{l["ref"]}-{slug(l["title"])}-{l["area"]}.html'
    l["features_lc"] = " ".join(f.lower() for f in l["features"])
    x = D.EXTRA.get(l["ref"], {})
    l["year"] = x.get("year"); l["fees"] = x.get("fees"); l["confirmed"] = x.get("confirmed", l["added"])
    for k in ("zone", "density", "access", "utilities", "seller"): l[k] = x.get(k)
    l["project"] = next((d for d in D.DEVELOPMENTS if l["ref"] in d["refs"]), None)
    if x.get("energy"): l["energy"] = x["energy"]
    l["sponsored"] = l["ref"] in D.SPONSORED
    l["tr"] = {}
    if x.get("desc_de"):
        l["tr"]["de"] = dict(desc=x["desc_de"], title="Villa mit 3 Schlafzimmern und eigenem Pool", kind="Villa", area="Peyia",
                             features=["Eigener Pool", "Meerblick", "Fußbodenheizung", "Solar-Warmwasser", "Garten"])
        l["tr"]["he"] = dict(desc=x["desc_he"], title="וילה עם 3 חדרי שינה ובריכה פרטית", kind="וילה", area="פגיה",
                             features=["בריכה פרטית", "נוף לים", "חימום תת-רצפתי", "דוד שמש", "גינה"])
LIST_BY_DATE = sorted(D.LISTINGS, key=lambda l: l["added"], reverse=True)

SALE = ("resale", "new-build", "land")
def in_cat(l, pur):
    return l["purpose"] in SALE if pur == "for-sale" else l["purpose"] == pur

def pages_index():
    p = {pur: f"{pur}/index.html" for pur in D.PURPOSES}
    for pur in D.PURPOSES:
        for a in D.AREAS:
            if any(in_cat(l, pur) and l["area"] == a for l in D.LISTINGS):
                p[f"{pur}/{a}"] = f"{pur}/{a}.html"
    p["developments"] = "developments/index.html"
    return p
PAGES = pages_index()

env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")), autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
env.globals.update(T=I18N.T, L=I18N.L, deed_text=deed_text, nice_date=nice_date, photo_img=photo_img, HERO=('hero' in HAVE), seal=seal_svg, icons={k: Markup(v) for k, v in ICONS.items()}, scene=scene, price=price_html, deed_chip=deed_chip,
                   money=money, D=D, PAGES=PAGES, FAVICON=FAVICON, today=date(2026, 10, 23))

def write(rel, tpl, **ctx):
    depth = rel.count("/")
    root = "../" * depth
    html = env.get_template(tpl).render(root=root, rel=rel, **ctx)
    html = re.sub(r"\n\s*\n+", "\n", html)
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return rel

def project(lat, lng):
    # simple equirectangular box over the Paphos district, 1 unit = 100 m
    x = (lng - 32.25) * 912
    y = (35.12 - lat) * 1110
    return round(x, 1), round(y, 1)

COAST = [(35.10, 32.28), (35.03, 32.28), (34.96, 32.30), (34.91, 32.33), (34.856, 32.362), (34.83, 32.385), (34.80, 32.398),
         (34.77, 32.405), (34.752, 32.403), (34.745, 32.43), (34.735, 32.46), (34.715, 32.49), (34.70, 32.53), (34.675, 32.58),
         (34.66, 32.62), (34.655, 32.65), (35.0, 32.65), (35.02, 32.60), (35.05, 32.52), (35.04, 32.45), (35.035, 32.41),
         (35.045, 32.38), (35.07, 32.33)]
def map_svg(listings, root, aspect=0.75):
    """Drawn coastline (SVG, stretched to the box) with pins and labels as HTML on top, so they stay a fixed size."""
    pts = [project(D.AREAS[l["area"]]["lat"], D.AREAS[l["area"]]["lng"]) for l in listings] or [(150, 300)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    pad = 45 if len(listings) > 1 else 70
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad - 12, max(ys) + pad
    w, h = x1 - x0, y1 - y0
    if w / h < aspect:   # too tall: widen
        nw = h * aspect; x0 -= (nw - w) / 2; w = nw
    else:                # too wide: heighten
        nh = w / aspect; y0 -= (nh - h) / 2; h = nh
    pct = lambda x, y: (f"{(x - x0) / w * 100:.2f}%", f"{(y - y0) / h * 100:.2f}%")
    land = " ".join("%s,%s" % project(la, lo) for la, lo in COAST)
    out = [f'<div class="map" style="aspect-ratio: {aspect:.3f}">',
           f'<svg viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
           f'<rect x="-400" y="-400" width="1200" height="1300" fill="#CFE6F5"/>'
           f'<polygon points="{land}" fill="#F6EADF" stroke="#E6D5C3" stroke-width="1.2" vector-effect="non-scaling-stroke"/></svg>']
    for k, ar in D.AREAS.items():
        x, y = project(ar["lat"], ar["lng"])
        if x0 < x < x0 + w and y0 < y < y0 + h:
            L, T = pct(x, y)
            out.append(f'<span class="map-label" style="left:{L};top:{T}">{ar["name"]}</span>')
    seen = {}
    for l in listings:
        k = seen.get(l["area"], 0); seen[l["area"]] = k + 1
        x, y = project(D.AREAS[l["area"]]["lat"], D.AREAS[l["area"]]["lng"])
        L, T = pct(x, y)
        lab = price_short(l)
        out.append(f'<a class="pin" data-ref="{l["ref"]}" href="{root}{l["path"]}" style="left:{L};top:{T};--stack:{k}" aria-label="{l["title"]}, {l["area_name"]}, {lab}">{lab}</a>')
    out.append('</div>')
    return Markup("".join(out))

def leaflet_map(listings, root, aspect=0.75, area_circle=False):
    """Interactive OpenStreetMap map (Leaflet). The drawn SVG map stays inside as the fallback if the map can't load."""
    import json as _j, math as _m
    seen, pins = {}, []
    for l in listings:
        a = D.AREAS[l["area"]]; k = seen.get(l["area"], 0); seen[l["area"]] = k + 1
        lat = l.get("lat") or a["lat"]; lng = l.get("lng") or a["lng"]
        if not l.get("lat") and k:  # spread homes in the same area so markers don't sit on top of each other
            lat += 0.004 * _m.sin(k * 2.1); lng += 0.005 * _m.cos(k * 2.1)
        pins.append({"lat": round(lat, 5), "lng": round(lng, 5), "label": price_short(l), "title": l["title"],
                     "area": l["area_name"], "href": root + l["path"]})
    import html as _h
    data = _h.escape(_j.dumps({"pins": pins, "circle": area_circle}), quote=True)
    return Markup(f'<div class="lmap" style="aspect-ratio:{aspect:.3f}" data-map="{data}">'
                  f'<div class="lmap-fallback">{map_svg(listings, root, aspect)}</div></div>')

def price_short(l):
    p = l["price"]
    if l["period"] == "night": return f"€{p}/night"
    if l["period"] == "month": return f"€{p:,}/mo"
    return f"€{p/1000:.0f}k" if p < 1_000_000 else f"€{p/1_000_000:.1f}m"

env.globals.update(map_svg=map_svg, leaflet_map=leaflet_map, SAMPLE=D.SAMPLE)

def card_html(l, root):
    return env.get_template("_card.html").render(l=l, root=root)

def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(HERE, "static", "style.css"), os.path.join(OUT, "style.css"))
    shutil.copy(os.path.join(HERE, "static", "app.js"), os.path.join(OUT, "app.js"))
    if os.path.isdir(PH.IMG): shutil.copytree(PH.IMG, os.path.join(OUT, "img"))
    made = []
    area_counts = {k: sum(1 for l in D.LISTINGS if l["area"] == k) for k in D.AREAS}
    made.append(write("index.html", "home.html", latest=LIST_BY_DATE[:8], area_counts=area_counts, page_title=None, nav=None, alt={"en": "index.html", "de": "de/index.html", "he": "he/index.html"}))
    for pur, P in D.PURPOSES.items():
        ls = [l for l in LIST_BY_DATE if in_cat(l, pur)]
        areas_here = [(a, D.AREAS[a]["name"], sum(1 for l in ls if l["area"] == a)) for a in D.AREAS if any(l["area"] == a for l in ls)]
        made.append(write(f"{pur}/index.html", "results.html", listings=ls, pur=pur, P=P, area=None, areas_here=areas_here, nav=pur))
        for a, name, n in areas_here:
            made.append(write(f"{pur}/{a}.html", "results.html", listings=[l for l in ls if l["area"] == a], pur=pur, P=P,
                              area=dict(D.AREAS[a], slug=a), areas_here=areas_here, nav=pur))
    DE_L, HE_L = "de/immobilie/10238-villa-peyia.html", "he/nehes/10238-villa-peyia.html"
    for l in D.LISTINGS:
        similar = [s for s in LIST_BY_DATE if s["purpose"] == l["purpose"] and s["ref"] != l["ref"]][:3]
        alt = {"en": l["path"], "de": DE_L, "he": HE_L} if (l["ref"] == "10238" and D.SAMPLE) else {"en": l["path"]}
        made.append(write(l["path"], "listing.html", l=l, similar=similar, nav=l["purpose"], alt=alt))
        if l["ref"] == "10238" and D.SAMPLE:
            made.append(write(DE_L, "listing.html", l=l, similar=[], nav="resale", lang="de", alt=alt))
            made.append(write(HE_L, "listing.html", l=l, similar=[], nav="resale", lang="he", alt=alt))
    HOME_ALT = {"en": "index.html", "de": "de/index.html", "he": "he/index.html"}
    GUIDE_ALT = {"en": "buying-from-abroad/index.html", "de": "de/ratgeber-kauf-aus-deutschland.html", "he": "he/madrich-kniya-mi-israel.html"}
    made.append(write("de/index.html", "home_de.html", lang="de", alt=HOME_ALT, nav=None))
    made.append(write("he/index.html", "home_he.html", lang="he", alt=HOME_ALT, nav=None))
    made.append(write("de/ratgeber-kauf-aus-deutschland.html", "guide_de.html", lang="de", alt=GUIDE_ALT, nav="abroad"))
    made.append(write("he/madrich-kniya-mi-israel.html", "guide_he.html", lang="he", alt=GUIDE_ALT, nav="abroad"))
    made.append(write("buying-from-abroad/index.html", "abroad_hub.html", nav="abroad", alt=GUIDE_ALT))
    made.append(write("buying-from-abroad/from-the-uk.html", "abroad_uk.html", nav="abroad",
                      g={"title": "Buying in Paphos from the UK", "lead": D.MARKETS["uk"]["lead"]}))
    made.append(write("buying-from-abroad/permit.html", "permit.html", nav="abroad"))
    made.append(write("buying-from-abroad/costs.html", "costs.html", nav="abroad"))
    made.append(write("developments/index.html", "developments.html", nav="developments"))
    for d in D.DEVELOPMENTS:
        units = [l for l in D.LISTINGS if l["ref"] in d["refs"]]
        made.append(write(f"developments/{d['slug']}.html", "development.html", d=d, units=units, nav="developments"))
    made.append(write("buyer-desk.html", "desk.html", nav="desk"))
    made.append(write("trust.html", "trust.html", nav=None))
    for f,t in (("index","svc_index"),("legal","svc_legal"),("finance","svc_finance"),("residency","svc_residency")):
        made.append(write(f"services/{f}.html", t+".html", nav="services"))
        made.append(write(f"he/services/{f}.html", t+"_he.html", nav="services", lang="he", alt={"en": f"services/{f}.html", "he": f"he/services/{f}.html"}))
    made.append(write("agents/dashboard.html", "dashboard.html", nav=None))
    made.append(write("accessibility.html", "info_accessibility.html", nav=None))
    made.append(write("agents/index.html", "agents.html", nav="agents"))
    for k, a in D.AGENTS.items():
        made.append(write(f"agents/{k}.html", "agent.html", a=a, key=k, listings=[l for l in LIST_BY_DATE if l["agent"] == k], nav="agents"))
    made.append(write("for-agents.html", "for_agents.html", nav=None))
    made.append(write("guides/index.html", "guides.html", nav=None))
    for g in D.GUIDES:
        made.append(write(f"guides/{g['slug']}.html", f"guide_{g['slug'].replace('-', '_')}.html", g=g, nav=None))
    saved_data = [{"ref": l["ref"], "card": card_html(l, "")} for l in LIST_BY_DATE]
    made.append(write("saved.html", "saved.html", saved_json=Markup(json.dumps(saved_data).replace("</", "<\\/")), nav=None))
    for page in ["about", "contact", "report", "privacy", "cookies", "terms"]:
        made.append(write(f"{page}.html", f"info_{page}.html", nav=None))
    return made

if __name__ == "__main__":
    made = build()
    print(len(made), "pages")
