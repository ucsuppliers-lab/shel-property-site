"""Load real listings and agents from CSV (listings/listings.csv, listings/agents.csv).

If listings.csv has rows, they replace the sample listings when the site is built.
Every row is checked; a row that fails a check is skipped and reported, never published.
Photos: put files in listings/photos/<ref>-1.jpg, <ref>-2.jpg ... (agent must confirm rights).
"""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import taxonomy as TX
HERE = os.path.dirname(os.path.abspath(__file__))
PURPOSES = {"resale", "new-build", "land"}  # rentals removed 29 Oct 2026
DEEDS = {"issued", "after-completion", "pending"}
ENERGY = set("A B C D E F G".split()) | {"exempt"}

def _num(v, kind=float):
    v = (v or "").replace(",", "").replace("€", "").strip()
    if not v: return None
    try: return kind(v)
    except ValueError: return kind(round(float(v)))

def _yes(v):
    return (v or "").strip().lower() in ("yes", "y", "true", "1")

CONTENT = os.path.join(os.path.dirname(HERE), "content")

def _json_rows(kind):
    """Entries saved by the website editor (Pages CMS) in content/<kind>/*.json."""
    import json
    d = os.path.join(CONTENT, kind)
    out = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                r = json.load(open(os.path.join(d, f), encoding="utf-8"))
                out.append({k: ("" if v is None else v if isinstance(v, list) else str(v)) for k, v in r.items()})
    return out

def _csv_rows(name):
    p = os.path.join(HERE, name)
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if os.path.exists(p) else []

def load_agents():
    out = {}
    for r in _csv_rows("agents.csv") + _json_rows("agents"):
        if not r.get("id"):
            continue
        out[r["id"].strip()] = {"name": r["name"], "office": r["office"], "since": _num(r.get("since"), int),
                                "reg": r["registration_no"], "licence": r["licence_no"], "phone": r["phone"],
                                "about": r.get("about", ""), "licence_checked": r.get("licence_checked_on", "")}
    return out

def load_listings(agents):
    rows, extra, problems = [], {}, []
    for i, r in enumerate(_csv_rows("listings.csv") + _json_rows("listings"), start=2):
        # Private sites only (deploy previews, and the password-protected staging project): show hidden drafts too.
        DRAFTS = os.environ.get("SHOW_DRAFTS") == "1" or os.environ.get("SITE_NAME") == "shel-property-staging"
        if str(r.get("published", "yes")).lower() in ("false", "no", "0") and not DRAFTS:
            continue
        if not (r.get("ref") or "").strip():
            continue
        ref = r["ref"].strip()
        errs = []
        if r.get("purpose") not in PURPOSES: errs.append("purpose must be one of " + ", ".join(sorted(PURPOSES)))
        if r.get("agent_id") not in agents: errs.append("agent_id not in agents.csv")
        elif not agents[r["agent_id"]]["reg"] or not agents[r["agent_id"]]["licence"]: errs.append("agent has no registration/licence numbers")
        if _num(r.get("price")) is None: errs.append("price missing")
        if r.get("purpose") != "land" and (r.get("energy_class") or "").strip() not in ENERGY: errs.append("energy_class missing (A-G or exempt)")
        if r.get("purpose") != "to-rent" and r.get("title_deed") not in DEEDS: errs.append("title_deed must be issued / after-completion / pending")
        if not _yes(r.get("photo_rights_confirmed")): errs.append("photo rights not confirmed by agent")
        if not (r.get("area") or "").strip() and TX.HUB_OF.get(r.get("locality") or ""):
            r = dict(r, area=TX.HUB_OF[r["locality"]])
        if not (r.get("area") or "").strip(): errs.append("area missing")
        if errs and DRAFTS:
            problems.append(f"row {i} ({ref}) DRAFT, would be held back: " + "; ".join(errs))
            errs = [e for e in errs if e.startswith("purpose") or e.startswith("price")]
            if not r.get("agent_id") or r.get("agent_id") not in agents:
                r = dict(r, agent_id="_draft")
        if errs:
            problems.append(f"row {i} ({ref}): " + "; ".join(errs))
            continue
        ptype, psub = TX.type_and_sub((r.get("type") or "").strip(), (r.get("subtype") or "").strip())
        rows.append({
            "ptype": ptype, "sub": psub, "locality": (r.get("locality") or "").strip() or None,
            "condition": (r.get("condition") or "").strip() or ("Resale" if r["purpose"] == "resale" else None),
            "furnished": (r.get("furnished") or "").strip() or None, "zoning": (r.get("zoning") or "").strip() or None,
            "floor": (str(r.get("floor") or "")).strip() or None, "parking": _num(r.get("parking_spaces"), int),
            "veranda": _num(r.get("veranda_m2"), int), "toilets": _num(r.get("toilets"), int),
            "airport_km": _num(r.get("distance_to_airport_km")), "school_km": _num(r.get("distance_to_schools_km")),
            "shops_km": _num(r.get("distance_to_amenities_km")), "featured": _yes(str(r.get("featured", ""))),
            "ref": ref, "purpose": r["purpose"], "area": (r.get("area") or "").strip(), "kind": (psub or ptype) if psub not in ("Plot", "Field", "Development land", "Whole floor", "Residential", "Commercial") else ptype,
            "title": (r.get("title") or "").strip(), "price": _num(r["price"], int),
            "period": "month" if r["purpose"] == "to-rent" else None, "vat": _yes(r.get("plus_vat")),
            "beds": _num(r.get("bedrooms"), int), "baths": _num(r.get("bathrooms"), int),
            "covered": _num(r.get("covered_m2"), int), "extra": None, "plot": _num(r.get("plot_m2"), int),
            "deed": r.get("title_deed") or None, "sea_km": _num(r.get("distance_to_sea_km")),
            "energy": (r.get("energy_class") or "").strip() or None, "agent": r["agent_id"],
            "added": r.get("date_listed") or "", "tags": [], "features": [f.strip() for f in (r.get("features") or "").split("|") if f.strip()],
            "photo": r.get("photo_caption") or r.get("title") or "", "tone": "sky", "desc": r.get("description", "").strip(),
            "lat": _num(r.get("latitude")), "lng": _num(r.get("longitude")),
            "draft": str(r.get("published", "yes")).lower() in ("false", "no", "0") or r.get("agent_id") == "_draft",
            "photo_files": [x for x in (r.get("photos") or []) if x] if isinstance(r.get("photos"), list) else [],
        })
        extra[ref] = {"year": _num(r.get("year_built"), int), "fees": _num(r.get("common_fees_month"), int),
                      "confirmed": r.get("last_confirmed") or r.get("date_listed") or ""}
    return rows, extra, problems
