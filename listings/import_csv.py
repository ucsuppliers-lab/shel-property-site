"""Load real listings and agents from CSV (listings/listings.csv, listings/agents.csv).

If listings.csv has rows, they replace the sample listings when the site is built.
Every row is checked; a row that fails a check is skipped and reported, never published.
Photos: put files in listings/photos/<ref>-1.jpg, <ref>-2.jpg ... (agent must confirm rights).
"""
import csv, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
PURPOSES = {"resale", "new-build", "land", "to-rent"}
DEEDS = {"issued", "after-completion", "pending"}
ENERGY = set("A B C D E F G".split()) | {"exempt"}

def _num(v, kind=float):
    v = (v or "").replace(",", "").replace("€", "").strip()
    return kind(v) if v else None

def _yes(v):
    return (v or "").strip().lower() in ("yes", "y", "true", "1")

def load_agents():
    p = os.path.join(HERE, "agents.csv")
    if not os.path.exists(p):
        return {}
    out = {}
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if not r.get("id"):
            continue
        out[r["id"].strip()] = {"name": r["name"], "office": r["office"], "since": _num(r.get("since"), int),
                                "reg": r["registration_no"], "licence": r["licence_no"], "phone": r["phone"],
                                "about": r.get("about", ""), "licence_checked": r.get("licence_checked_on", "")}
    return out

def load_listings(agents):
    p = os.path.join(HERE, "listings.csv")
    if not os.path.exists(p):
        return [], {}, []
    rows, extra, problems = [], {}, []
    for i, r in enumerate(csv.DictReader(open(p, encoding="utf-8-sig")), start=2):
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
        if errs:
            problems.append(f"row {i} ({ref}): " + "; ".join(errs))
            continue
        rows.append({
            "ref": ref, "purpose": r["purpose"], "area": r["area"].strip(), "kind": r["type"].strip(),
            "title": r["title"].strip(), "price": _num(r["price"], int),
            "period": "month" if r["purpose"] == "to-rent" else None, "vat": _yes(r.get("plus_vat")),
            "beds": _num(r.get("bedrooms"), int), "baths": _num(r.get("bathrooms"), int),
            "covered": _num(r.get("covered_m2"), int), "extra": None, "plot": _num(r.get("plot_m2"), int),
            "deed": r.get("title_deed") or None, "sea_km": _num(r.get("distance_to_sea_km")),
            "energy": (r.get("energy_class") or "").strip() or None, "agent": r["agent_id"],
            "added": r.get("date_listed") or "", "tags": [], "features": [f.strip() for f in (r.get("features") or "").split("|") if f.strip()],
            "photo": r.get("photo_caption") or r["title"], "tone": "sky", "desc": r.get("description", "").strip(),
            "lat": _num(r.get("latitude")), "lng": _num(r.get("longitude")),
        })
        extra[ref] = {"year": _num(r.get("year_built"), int), "fees": _num(r.get("common_fees_month"), int),
                      "confirmed": r.get("last_confirmed") or r.get("date_listed") or ""}
    return rows, extra, problems
