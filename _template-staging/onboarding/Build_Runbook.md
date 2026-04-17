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

New repo per retailer. Clone the store-agnostic template:

1. Create a new GitHub repo under the retailer's preferred org name (or yours). Example: `acmemattress/DreamFinder`.
2. Clone the template locally:
   ```
   git clone https://github.com/beford782/DreamFinder-template.git acme-dreamfinder
   cd acme-dreamfinder
   ```
3. Repoint origin at the new repo:
   ```
   git remote set-url origin https://github.com/acmemattress/DreamFinder.git
   ```
4. Activate the versioned pre-commit hook:
   ```
   git config core.hooksPath hooks
   ```

The template contains no retailer-specific content. The converter in
Phase 2 fills in branding, product data, and email strings; a short
list of manual `index.html` edits covers what the converter can't touch.

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

From the cloned repo's root:

```
python tools/convert_store_data.py ../incoming/Acme_Store_Data.xlsx \
  --image-base-url "https://acmemattress.github.io/DreamFinder" \
  --source-images "../incoming" \
  --output-dir "."
```

This will:

1. **Auto-convert** every mattress and accessory image to optimized WebP (1000px max edge, quality 82) and write them into `images/mattresses/` and `images/accessories/`.
2. Write `data/store-config.json` with retailer branding, colors, and bilingual text blocks.
3. Write `data/mattresses.csv` with the retailer's lineup.
4. Write `data/accessories.json` with bilingual `{en, es}` shape.
5. Patch `Code.gs` in place (Bel template strings → retailer strings).
6. Patch `manifest.json` in place.
7. Print a checklist of remaining manual steps.

Then regenerate `data/mattresses.json` from the new CSV (this also runs the CSV validator):

```
.\build-data.ps1
```

If validation fails (duplicate ids, invalid tier, out-of-range firmness,
missing required fields), fix the CSV and re-run. Don't proceed until
validation passes.

**Manually copy logos** into `images/logos/` (the converter doesn't touch logos — they stay PNG):

```
cp incoming/logos/* images/logos/
```

(Create `images/logos/` if it doesn't already exist.)

---

## Phase 3 — Manual `index.html` edits

The converter writes config + data + Code.gs + manifest, but it does not
edit `index.html`. Two small edits are still needed:

### Domain lock

Search for `var allowed = [` in `index.html`. Add the new Pages host:

```javascript
var allowed = ['acmemattress.github.io', 'localhost', '127.0.0.1'];
```

Without this, first page load on the new Pages URL shows an
"Unauthorized domain" splash.

### Public asset root (for email images)

Search for `const PUBLIC_ASSET_ROOT`. Set it to the retailer's Pages URL
with a trailing slash:

```javascript
const PUBLIC_ASSET_ROOT = 'https://acmemattress.github.io/DreamFinder/';
```

This prefix is used when building mattress and accessory image URLs for
outbound email. Without it, email images don't render.

### GOOGLE_SCRIPT_URL (filled in after Phase 5)

Leave this for now — you'll paste the `/exec` URL in after the GAS deploy.

### Spanish mattress descriptions (optional)

If the retailer wants mattress badge chips, highlight lines, and per-match
reason text to appear in Spanish, drop a `data/mattresses-es.csv` next to
`data/mattresses.csv`. Columns:

- `id` (required, matches the English CSV)
- `displayBadges`, `highlight`, `reason_cooling`, `reason_pressureRelief`, `reason_motionIsolation`, `reason_support`, `reason_plush`, `reason_medium`, `reason_firm`, `reason_durability`, `reason_default`

Empty cells are allowed — the app falls back to English. After dropping
the file, re-run `.\build-data.ps1` to regenerate `mattresses.json` with
`tags_es`, `highlight_es`, `reasons_es` fields merged in.

If the retailer doesn't want Spanish at all, set
`"languages": ["en"]` in `data/store-config.json` to hide the toggle.

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
3. Delete the placeholder code. Paste the contents of the repo's `Code.gs` (already patched by the Phase 2 converter).
4. Save. Click **Deploy → New deployment**.
5. Gear icon → **Web app**.
6. Configure:
   - Description: `Initial`
   - Execute as: **Me** (the retailer's account)
   - Who has access: **Anyone**
7. Click **Deploy**. Authorize when prompted.
8. **Copy the Web app URL** that ends in `/exec`.
9. Paste it into `index.html`'s `GOOGLE_SCRIPT_URL` constant. Save.

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

Confirm that domain matches what you put in the Phase 3 domain lock — if not, update and push again.

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
- [ ] **Spanish toggle (EN/ES) visible on welcome screen**
- [ ] **Tap ES — entire welcome screen switches to Spanish**
- [ ] **Complete quiz in Spanish — all 12 questions, labels, sublabels in Spanish**
- [ ] **Profile, results, drawer, accessories all render in Spanish**
- [ ] **Submit email in Spanish mode — email arrives with Spanish subject, body, labels**
- [ ] **Tap EN — reverts to English cleanly**
- [ ] **Idle reset returns language to English**
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
- **"Unauthorized domain" splash on first load.** The domain lock `allowed` array in `index.html` doesn't include the new retailer's Pages domain. Add it and push.
- **DEBUG rows reappear in the lead Sheet.** That's an old GAS deployment still serving traffic. Confirm `GOOGLE_SCRIPT_URL` matches the live deployment URL exactly.
- **Outlook desktop on Windows shows broken mattress images in email.** Outlook desktop doesn't render WebP. If a retailer's customer base skews Outlook-desktop, swap the email-only image references to JPG.
