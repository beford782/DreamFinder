# DreamFinder — Build a New Retailer Runbook

> Internal guide. Walks through spinning up a new retailer deployment from
> a completed onboarding spreadsheet and image folder. Aim for ~30 minutes
> per retailer once you've done it twice.

---

## Phase 0 — Pre-flight check

Before you start, confirm the retailer has actually delivered:

- [ ] Completed onboarding spreadsheet (`.xlsx`) — every required field filled, yellow Bel example rows deleted
- [ ] Mattress images (one per `id` in the Mattresses tab) in any common format
- [ ] Accessory images (one per `id` in the Accessories tab)
- [ ] Logo PNG (transparent background, ≥400px wide)
- [ ] Two square PWA icons (192×192 and 512×512, PNG)
- [ ] Brand logos (one per row in the Brands tab)

If anything's missing, push back to the retailer before you start. Half-built deployments are a tar pit.

---

## Phase 1 — Repo setup

You have two patterns:

**Pattern A (recommended): new repo per retailer.**
The canonical Bel repo doubles as the template. For each new retailer:

1. Create a new GitHub repo under their preferred org name (or yours). Example: `acmemattress/DreamFinder`.
2. Clone the Bel repo locally:
   ```
   git clone https://github.com/beford782/DreamFinder.git acme-dreamfinder
   cd acme-dreamfinder
   ```
3. Repoint origin at the new repo:
   ```
   git remote set-url origin https://github.com/acmemattress/DreamFinder.git
   ```

**Pattern B: branch in a shared monorepo.**
Less recommended — the white-label strings are easier to mix up across branches.

---

## Phase 2 — Run the data converter (with image conversion)

Drop the retailer's spreadsheet and image folders into a working directory. Layout:

```
incoming/
  Acme_Store_Data.xlsx
  mattresses/
    *.png / *.jpg / *.webp     (any format, any size)
  accessories/
    *.png / *.jpg / *.webp
  logos/
    store-logo.png
    store-icon-192.png
    store-icon-512.png
    serta-logo.png
    sealy-logo.png
    ...
```

Then from the cloned repo's `tools/` directory:

```
python convert_store_data.py ../incoming/Acme_Store_Data.xlsx \
  --image-base-url "https://acmemattress.github.io/DreamFinder" \
  --source-images "../incoming" \
  --output-dir ".."
```

This will:

1. **Auto-convert** every mattress and accessory image to optimized WebP (1000px max edge, quality 82) and write them into `images/mattresses/` and `images/accessories/`.
2. Generate a CSS variable block, JS objects, and a branding-replacements list — all printed to stdout.

**Manually move the logo files** into `images/` (the converter doesn't touch logos; they need to stay PNG):

```
cp incoming/logos/* images/logos/
```

(Create `images/logos/` if it doesn't already exist.)

---

## Phase 3 — White-label string replacements

The app has 9–11 spots where "Bel Furniture" or related Bel-specific values are hardcoded. Replace each one with the new retailer's value. Keep this checklist open as you go:

### `index.html`

| Line (approx) | What to replace | Source |
|---|---|---|
| 7 | `<title>Bel Furniture × DreamFinder</title>` | Store Name |
| 13 | Meta description (mentions "Bel Furniture") | Store Name |
| 14 | Open Graph title | Store Name |
| 3468 | `Recommended by your Bel Furniture sleep team` | Store Name |
| 3477 | Footer copyright text | Footer Text |
| 3781 | Email opt-in privacy line | Store Name |
| 3837 | Domain lock `allowed = ['beford782.github.io', ...]` | New GitHub Pages domain |
| 5065 | `In Stock at Bel Furniture` (default fallback) | Store Name |
| 5342 | `GOOGLE_SCRIPT_URL` constant | New GAS deployment URL (Phase 5) |
| 5415 | `Bel Furniture × DreamFinder` (email header default) | Store Name |
| 5463 | `Bring this email to your Bel Furniture store` (email footer default) | Store Name |
| 6254 | Privacy policy text | Store Name |

Several of these have `STORE_CONFIG.text.{inStockText, emailHeader, emailSubtext}` overrides — populate the JSON instead of editing the fallbacks if you want to keep the template generic. Currently `data/store-config.json` only has a few fields; expand as needed.

CSS theme color is set near the top of `<style>` (`--store-primary` etc.). Change to the retailer's primary brand color.

### Language support (`data/store-config.json`)

The template ships bilingual (English + Spanish) by default. A language toggle appears on the welcome screen and customers can flip the whole app — quiz, profile, results, drawer, accessories, email capture, email body — into Spanish.

To configure per retailer, edit the `languages` array:

```json
"languages": ["en", "es"]   // default — toggle visible
"languages": ["en"]          // English-only — toggle hidden
```

If Spanish is enabled, also customize the `text_es` block alongside `text`:

```json
"text": {
  "socialProof": "Trusted by Acme customers across Arizona",
  "footer": "© 2026 Acme Mattress. All rights reserved.",
  ...
},
"text_es": {
  "socialProof": "Confiado por clientes de Acme en todo Arizona",
  "footer": "© 2026 Acme Mattress. Todos los derechos reservados.",
  ...
}
```

See `data/dict-en.json` / `data/dict-es.json` for the UI dictionary (all static strings, shared across retailers — rarely need retailer edits).

### Spanish mattress descriptions (optional)

To translate mattress-specific copy (badge chips, highlight lines, per-match reason text) into Spanish, create `data/mattresses-es.csv` alongside `data/mattresses.csv`. Columns:

- `id` (required, matches the English CSV)
- `displayBadges`, `highlight`, `reason_cooling`, `reason_pressureRelief`, `reason_motionIsolation`, `reason_support`, `reason_plush`, `reason_medium`, `reason_firm`, `reason_durability`, `reason_default`

Empty cells are allowed — the app falls back to the English value when a Spanish translation is missing. Run `.\build-data.ps1` after editing the CSV to regenerate `data/mattresses.json` with the Spanish fields merged in as `tags_es`, `highlight_es`, `reasons_es`.

If the retailer doesn't want Spanish, just skip creating this file. The app ignores it cleanly.

### `Code.gs`

Open in any text editor and replace:
- `'Your DreamFinder Results from Bel Furniture'` → retailer's email subject (Store Info → Email Subject Line)
- `'Bel Furniture Sleep Team'` (two places) → retailer's sender name (Store Info → Email Sender Name)
- `'Show this email at Bel Furniture to redeem.'` → retailer-specific phrasing
- `'Bel Furniture x DreamFinder'` (header) → retailer name
- `'Bring this email to your Bel Furniture store'` (footer) → retailer phrasing

### `manifest.json`

```json
{
  "name": "DreamFinder — Acme Mattress",
  "short_name": "DreamFinder",
  "description": "Personalized sleep consultation for Acme Mattress",
  ...
}
```

---

## Phase 4 — Generate / drop in icons + update favicon

The app's favicon is an inline SVG (line ~10 of `index.html`). It uses the gold moon — leave it as-is unless the retailer wants their own.

PWA icons (`icon-192.png` and `icon-512.png`) are referenced in `manifest.json` but live at the repo root. Drop the retailer's submitted icons there.

Confirm both files exist at the repo root:
```
ls icon-192.png icon-512.png
```

---

## Phase 5 — Set up Google Apps Script for the retailer

**Each retailer needs their own GAS web app**, sending email from their own Google account and writing to their own Sheet.

1. Create a new Google Sheet under their Google account. Name it `<Retailer> DreamFinder Leads`.
2. Tools → Apps Script. This opens a new project bound to the sheet.
3. Delete the placeholder code. Paste the contents of the repo's `Code.gs` (with the Phase 3 retailer-specific text edits already applied).
4. Save. Click **Deploy → New deployment**.
5. Gear icon → **Web app**.
6. Configure:
   - Description: `Initial`
   - Execute as: **Me** (the retailer's account)
   - Who has access: **Anyone**
7. Click **Deploy**. Authorize when prompted.
8. **Copy the Web app URL** that ends in `/exec`.
9. Paste it into `index.html` line 5342 (`GOOGLE_SCRIPT_URL`). Save.

**Note:** in the future when Code.gs is edited, you must do **Deploy → Manage deployments → pencil → Version: New version → Deploy** to actually promote changes. Just saving the editor isn't enough.

---

## Phase 6 — First push + GitHub Pages

```
git add .
git commit -m "Initial Acme deployment"
git push origin main
```

Then in the new repo on GitHub:
1. Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main** / folder: **/ (root)**
4. Save

Wait 1–3 minutes for the first deploy. Pages URL will be:
```
https://acmemattress.github.io/DreamFinder/
```

Confirm that domain matches what you put in the Phase 3 domain lock (line 3837) — if not, update and push again.

---

## Phase 7 — End-to-end verification

Open the Pages URL on a desktop browser AND on an iPad. Run the full flow:

- [ ] Welcome screen shows the retailer's name, colors, trust signal, badge
- [ ] Quiz runs all 12 questions; skip-logic works for solo sleepers; multi-select cap of 3 enforced
- [ ] Review screen shows current answers; Edit returns to that question
- [ ] Profile screen shows the personalized opener (uses `trigger`, `current_mattress_age`, `sleep_quality`)
- [ ] Confidence pill + social proof show
- [ ] Theme accent colors look right per profile archetype
- [ ] Results page: Gold/Silver/Bronze tabs work; tier explainer reads correctly; $/$$/$$$ price markers visible
- [ ] Mattress card opens drawer; drawer prev/next works; mattress images load
- [ ] Compare 2 button works; compare modal renders side-by-side
- [ ] Accessories flow works
- [ ] Email submit:
  - [ ] No DEBUG row in the sheet
  - [ ] Single clean row written: date, name, email, phone, DREAM code, matches, accessories
  - [ ] Customer email arrives with mattress images + DREAM code visible
  - [ ] Email reflects the customer's saved picks, not just algorithm picks
- [ ] Restart button works from header, accessories screen, and email screen
- [ ] Discount overlay doesn't block taps; full reveal completes before fade-out
- [ ] Idle timer (2 min) returns to welcome
- [ ] Console (DevTools) is clean — no red errors, no 404s

---

## Phase 8 — Hand-off

- [ ] Send the retailer their live Pages URL
- [ ] Walk a salesperson through the kiosk flow, including the handoff screen with the sales cheat sheet
- [ ] Confirm they can access the lead Sheet
- [ ] Schedule a 1-week check-in: was everything submitted as expected, any odd lead patterns, etc.
- [ ] Add the new retailer's repo to your bookmark list

---

## Per-retailer files to keep as artifacts

After delivering, archive a copy of:
- The completed `Acme_Store_Data.xlsx` (the source of truth)
- The retailer's `Code.gs` (in case you need to redeploy after future engine changes)
- The Pages URL + GAS Web app URL + Sheet URL in a shared "Retailers" doc

This makes future changes (engine version bumps, scoring tweaks) a re-run rather than a re-build.

---

## Common gotchas

- **GAS Web app URL changed silently after a redeploy.** If you create a *new* deployment instead of updating the existing one, the URL changes. Always use **Deploy → Manage deployments → pencil → New version**.
- **Mattress images broken in the customer email.** The client converts relative URLs to absolute using `PUBLIC_ASSET_ROOT` — make sure that constant points at the new retailer's Pages URL.
- **"Unauthorized domain" splash on first load.** Domain lock at index.html line ~3837 doesn't include the new retailer's Pages domain. Add it and push.
- **DEBUG rows reappear in the lead Sheet.** That's an old GAS deployment still serving traffic. Confirm `GOOGLE_SCRIPT_URL` matches the live deployment URL exactly.
- **Outlook desktop on Windows shows broken mattress images in email.** Outlook desktop doesn't render WebP. If a retailer's customer base skews Outlook-desktop, swap the email-only image references to JPG.
