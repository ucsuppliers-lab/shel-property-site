# Listings from partner agents

1. Copy `agents-template.csv` to `agents.csv` and `listings-template.csv` to `listings.csv`.
2. One row per agent / per home. Agents fill the same columns (we can send them the template).
3. Rules checked on every build (a row that fails is skipped and listed, never published):
   - agent must have registration and licence numbers (Cyprus law: shown on every advert);
   - price, purpose (resale / new-build / land / to-rent), title deed status (sale), energy class A–G or "exempt" (not land);
   - `photo_rights_confirmed` must be "yes".
4. Photos go in `listings/photos/` named `<ref>-1.jpg`, `<ref>-2.jpg`…
5. While `listings.csv` doesn't exist, the site shows the sample listings.

The columns map one-to-one to the Kyero XML feed most Cyprus agent systems export, so feeds can replace the CSV later.
