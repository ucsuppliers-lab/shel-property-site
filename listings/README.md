# Listings from partner agents

1. Copy `agents-template.csv` to `agents.csv` and `listings-template.csv` to `listings.csv`.
2. One row per agent / per home. Agents fill the same columns (we can send them the template).
3. Rules checked on every build (a row that fails is skipped and listed, never published):
   - agent must have registration and licence numbers (Cyprus law: shown on every advert);
   - price, purpose (resale / new-build / land / to-rent), title deed status (sale), energy class A–G or "exempt" (not land);
   - `photo_rights_confirmed` must be "yes".
4. Photos go in `listings/photos/` named `<ref>-1.jpg`, `<ref>-2.jpg`…
5. Sample listings are switched off (SHOW_SAMPLES = False in data.py, 28 Oct 2026). Until `listings.csv` has rows, pages show a "first homes are being added" message.

The columns map one-to-one to the Kyero XML feed most Cyprus agent systems export, so feeds can replace the CSV later.

## Import from a link (website editor)
In the editor (app.pagescms.org → Properties) press **Import from a link**, paste the property page's address and the agent's short code.
A GitHub Action (`.github/workflows/import-url.yml`, script `listings/import_url.py`) reads the page, fills in what it can, downloads up to 15 photos
and saves a **hidden draft** (Show on website and photo rights unticked). A person checks every field against the page, gets the agent's permission,
ticks both boxes, saves, then presses **Publish website**. Some portals block automatic reading; the run then fails with a plain message.
