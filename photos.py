"""Free photos (Unsplash Licence) for the draft site. Downloaded once, resized locally, shipped with the site."""
import os, sys, subprocess
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "photos_raw")
IMG = os.path.join(HERE, "static", "img")

# key -> Unsplash image id. Listing keys: <ref>-<n>; hero: hero
PHOTOS = {
    "hero": "photo-1622626732857-2bf7e9fb9e37",      # aerial beach, Paphos coast
    "10241-1": "photo-1683882484967-25650288bf19",   # terrace with bougainvillea over the sea
    "10238-1": "photo-1613977257592-4871e5fcd7c4",   # white villa, pool, outdoor seating
    "10238-2": "photo-1613977257363-707ba9348227",   # same style villa, second view
    "10238-3": "photo-1600210492493-0946911123ea",   # living room, glass doors
    "10233-1": "photo-1580587771525-78b9dba3b914",   # white and brown modern house
    "10229-1": "photo-1600210491369-e753d80a41f3",   # bright living room
    "10227-1": "photo-1613490493576-7fde63acd811",   # modern villa, long pool
    "10226-1": "photo-1602343168117-bb8ffe3e2e9f",   # white house by a pool
    "10224-1": "photo-1512917774080-9991f1c4c750",   # white house, pool, clear sky
    "10222-1": "photo-1643843207456-5a60c3806b37",   # harbour, palms, boats (Paphos)
    "10215-1": "photo-1622615822298-eb693dc257ce",   # white house near trees (Paphos)
    "10210-1": "photo-1648032632586-41abd89148fc",   # whitewashed village lane
    "10205-1": "photo-1622632982282-268b1dcca46a",   # hills by the sea, aerial (Paphos)
}

def download():
    os.makedirs(RAW, exist_ok=True)
    for key, pid in PHOTOS.items():
        dst = os.path.join(RAW, key + ".jpg")
        if os.path.exists(dst) and os.path.getsize(dst) > 10000:
            continue
        url = f"https://images.unsplash.com/{pid}?w=1800&q=82&fm=jpg&fit=max"
        r = subprocess.run(["curl", "-sSfL", "--max-time", "60", "-o", dst, url], capture_output=True, text=True)
        print(key, "ok" if r.returncode == 0 else "FAILED " + r.stderr.strip()[:80])

def resize():
    os.makedirs(IMG, exist_ok=True)
    for key in PHOTOS:
        src = os.path.join(RAW, key + ".jpg")
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert("RGB")
        for w, suffix, q in ((1600, "l", 76), (720, "m", 74)):
            if key == "hero" and suffix == "m":
                w = 900
            r = im.copy()
            r.thumbnail((w, w * 2))
            r.save(os.path.join(IMG, f"{key}-{suffix}.jpg"), "JPEG", quality=q, optimize=True, progressive=True)

def available():
    have = {}
    for key in PHOTOS:
        if os.path.exists(os.path.join(IMG, f"{key}-m.jpg")):
            ref, _, n = key.partition("-")
            have.setdefault(ref, []).append(key)
    return have

if __name__ == "__main__":
    if "download" in sys.argv: download()
    resize()
    print(available())
