---
name: new-retailer
description: Spin up a new DreamFinder retailer deployment from a completed onboarding spreadsheet and image folder. Use when Blake says "onboard [retailer]", "new retailer for DreamFinder", or "set up [store name] deployment". Handles cloning the template, running the converter, regenerating data, patching Code.gs + manifest, and walking through the manual GAS / Pages steps.
---

# New DreamFinder Retailer

## When to use

Invoke when Blake asks to set up a new store on DreamFinder — typical
phrasings: "onboard Acme Mattress", "spin up a new retailer for
DreamFinder", "set up the Star Furniture deployment".

Do **not** invoke for:

- Tweaking an existing retailer's config (edit `data/store-config.json` directly)
- Adding a mattress to an existing lineup (edit `data/mattresses.csv`, run `build-data.ps1`)
- Rebranding/refreshing an existing retailer (same repo, config edits only)

## Prerequisites to confirm with Blake before starting

1. **Template repo location** — by default clone from
   `https://github.com/beford782/DreamFinder-template.git`. If Blake has
   a different template source, ask.
2. **New retailer's org/name** — what GitHub org will host the new repo?
   (e.g. `acmemattress`, `beford782`, etc.)
3. **Completed onboarding spreadsheet** — confirm path to the `.xlsx`.
   The retailer should have deleted the yellow Bel example rows.
4. **Image folder** — confirm path to the `incoming/` folder with
   `mattresses/`, `accessories/`, and `logos/` subdirectories.
5. **Pages URL** — what will the GitHub Pages URL be?
   (derives from org + repo name, e.g. `https://acmemattress.github.io/DreamFinder`)

If any are missing, ask before proceeding.

## Procedure

### 1. Clone the template

```
git clone https://github.com/beford782/DreamFinder-template.git <local-dir>
cd <local-dir>
git remote set-url origin https://github.com/<retailer-org>/<repo-name>.git
git config core.hooksPath hooks
```

### 2. Run the converter

From the clone's root:

```
python tools/convert_store_data.py ../incoming/<Retailer>.xlsx \
    --image-base-url "https://<retailer-org>.github.io/<repo-name>" \
    --source-images ../incoming \
    --output-dir .
```

This writes:
- `data/store-config.json`
- `data/mattresses.csv`
- `data/accessories.json`
- patches `Code.gs` in place (Bel strings → retailer strings)
- patches `manifest.json` in place

…and converts images to WebP under `images/mattresses/` and `images/accessories/`.

### 3. Regenerate mattresses.json

```
.\build-data.ps1
```

This runs the validator. If it fails on duplicate ids, invalid tiers, or
missing required fields, surface the errors to Blake and stop — don't
try to work around them.

### 4. Logo + PWA icons

The converter doesn't touch logos. Ask Blake to drop:

- Store logo → `images/logos/store-logo.png` (PNG, transparent bg, ≥400px wide)
- Brand logos → `images/logos/<brand>-logo.png` (one per brand)
- PWA icons → `icon-192.png` and `icon-512.png` at the repo root
  (both must be exact PNG dimensions)

### 5. Wire the domain lock

Open `index.html`, find the `allowed` array around the domain lock block
(search for `allowed = [`). Add the new Pages host:

```
var allowed = ['<retailer-org>.github.io', 'localhost', '127.0.0.1'];
```

### 6. Wire PUBLIC_ASSET_ROOT

In `index.html`, find the `PUBLIC_ASSET_ROOT` constant (search for it).
Set it to the retailer's Pages URL with a trailing slash:

```
const PUBLIC_ASSET_ROOT = 'https://<retailer-org>.github.io/<repo-name>/';
```

This is required for mattress and accessory images to render in emails.

### 7. Google Apps Script deployment

**Blake has to do this interactively** — you can't automate the GAS UI.
Walk him through:

1. Create a new Google Sheet under the retailer's Google account,
   named `<Retailer> DreamFinder Leads`.
2. Tools → Apps Script. Delete the placeholder `myFunction()`.
3. Paste the contents of `Code.gs` (already patched with retailer strings).
4. Save. Deploy → New deployment → Web app.
   - Execute as: the retailer's account
   - Who has access: Anyone
5. Authorize. Copy the `/exec` URL.
6. Paste it into `index.html`'s `GOOGLE_SCRIPT_URL` constant
   (search for `GOOGLE_SCRIPT_URL`).

If GAS code ever changes after initial deploy: Deploy → Manage deployments
→ pencil → New version → Deploy. Creating a *new* deployment changes the
URL, which silently breaks things.

### 8. First push + Pages setup

```
git add .
git commit -m "Initial <Retailer> deployment"
git push -u origin main
```

Then in the new repo on GitHub:

- Settings → Pages → Source: Deploy from branch → main / root → Save.

Wait 1–3 minutes for first deploy.

### 9. Smoke-test checklist

Ask Blake to open the Pages URL on desktop and on an iPad. Confirm:

- Welcome screen shows retailer colors, trust signal, badge
- Quiz runs all 12 questions
- Profile + results render; Gold/Silver/Bronze tabs work; tier explainer correct
- Mattress cards open the drawer; drawer prev/next works
- Accessories flow works; cart persists to handoff screen
- Email submit writes a single clean row to the Sheet (no DEBUG row)
- Customer email arrives with mattress images + DREAM code visible
- **EN/ES toggle works** — quiz, profile, results, accessories, email all switch
- Console is clean (no red errors, no 404s)
- Idle reset returns to welcome

### 10. Hand-off

Confirm Blake has archived:

- The retailer's filled `.xlsx` (source of truth)
- The retailer's patched `Code.gs` (for future GAS redeploys)
- Pages URL, GAS Web app URL, Sheet URL

## Tripwires

- **Converter flags missing required fields** — don't silently fill in
  defaults. Surface the errors and ask Blake or the retailer to fix.
- **Spanish columns are blank** — the converter falls back to English
  copy. That's fine unless Blake said the retailer wants Spanish-only
  or declined the EN/ES toggle (in which case set `"languages": ["en"]`
  in `store-config.json`).
- **Logo files not provided** — don't proceed to push. Brand logos
  missing from the footer look bad; PWA icons missing break "Add to
  Home Screen."
- **Domain lock not updated** — first page load on the new Pages URL
  shows an "Unauthorized domain" splash. Always double-check before
  handing off.
- **Pushed to the wrong branch** — if this session is on Claude Code on
  the web, pushes default to a `claude/*-<id>` branch, NOT main. Pages
  only deploys from main. Check `git branch --show-current` before
  every push.

## After a deployment is live

Keep the retailer's repo in Blake's bookmark list. When DreamFinder's
template gets upgraded (new features, scoring tweaks, bilingual improvements),
deploy upstream changes to each retailer repo by re-running the template
parts plus whatever data migration is needed.
