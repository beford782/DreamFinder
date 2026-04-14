# DreamFinder Store Onboarding Guide

Welcome! DreamFinder is a personalized mattress recommendation app that helps your
floor sales team guide customers to their perfect mattress through a quick 9-question
sleep consultation quiz.

To set up DreamFinder for your store, we need a few things from you.

---

## What You Need to Provide

| Item | Format | Where to Put It |
|------|--------|-----------------|
| Store branding info | Spreadsheet (Store Info tab) | Google Sheets or Excel file |
| Your mattress lineup | Spreadsheet (Mattresses tab) | Google Sheets or Excel file |
| Your accessories | Spreadsheet (Accessories tab) | Google Sheets or Excel file |
| Your mattress brands | Spreadsheet (Brands tab) | Google Sheets or Excel file |
| Store logo | PNG, transparent background | `logos/` folder in Google Drive |
| Brand logos | PNG, one per brand | `logos/` folder in Google Drive |
| Square app icons (192px + 512px) | PNG | `logos/` folder in Google Drive |
| Mattress product images | PNG or JPG, one per mattress | `mattresses/` folder in Google Drive |
| Accessory product images | PNG, JPG, or WebP | `accessories/` folder in Google Drive |

---

## Step-by-Step Instructions

### Step 1: Open the Spreadsheet Template

You'll receive either a **Google Sheets link** or a downloadable **Excel file (.xlsx)**.
Both have the same structure — use whichever you prefer.

The spreadsheet has 6 tabs:
- **Store Info** — Your store name, colors, branding, and footer text
- **Mattresses** — One row per mattress in your lineup
- **Accessories** — Bases, pillows, and protectors
- **Brands** — The mattress brands you carry (shown in the app footer)
- **Feature Keywords** — Reference list for the Mattresses tab
- **Instructions** — Detailed help for every field

### Step 2: Fill Out the Store Info Tab

This is just one row of basic info:
- **Store Name** — Your full name as shown to customers
- **Logo Lines** — How your name appears in the app's styled logo (Line 1 is big, Line 2 is smaller)
- **Brand Colors** — Your primary brand color as a hex code (use Google "hex color picker" if unsure)
- **Trust Signal** — A tagline like "Family-owned since 1995" shown on the welcome screen
- **Badge** — A short label like "Local Favorite" or "Est. 1990"
- **Location** — Your state or region (shown before GPS kicks in)
- **Discount %** — The completion reward discount (default 5%)
- **Footer Text** — The copyright/credit line at the bottom of the app (e.g., "Powered by DreamFinder · (c) 2026 Your Store Name")

### Step 3: Fill Out the Mattresses Tab

Add one row for every mattress you want in the app. Key fields:

- **ID** — A short unique code (lowercase, no spaces). Example: `royal-cloud`
- **Tier** — `gold` (premium), `silver` (mid-range), or `bronze` (value). Controls display priority.
- **Firmness** — Rate 1 (ultra soft) to 10 (ultra firm)
- **Feature Keywords** — These drive the quiz matching algorithm. See the Feature Keywords tab for the full list with descriptions.
- **Image File Name** — Must exactly match the file you upload (e.g., `royal-cloud.png`)
- **"Why" columns** — Short selling points shown when a mattress matches. "Why: Default" is required.

> **Tip:** The yellow example rows show Bel Furniture's real data. Use them as a guide,
> then delete them before submitting.

### Step 4: Fill Out the Accessories Tab

Add bases/foundations, pillows, and protectors. Key fields:

- **Category** — Must be: `Foundations & Support`, `Pillows`, or `Protectors`
- **Match Scores (0-5)** — Controls how strongly each accessory is recommended based on quiz answers. Leave blank if unsure — we can help fill these in.

### Step 5: Fill Out the Brands Tab

Add one row for each mattress brand you carry. These appear in the "Our Brands" section at the bottom of the app.

- **Brand Name** — The display name (e.g., "Serta", "Sealy")
- **Logo File Name** — Must match a file you upload to the `logos/` folder (e.g., `serta-logo.png`)

### Step 6: Upload Images to the Shared Google Drive Folder

You'll receive a shared folder with this structure:

```
DreamFinder - [Your Store Name]/
  logos/
    store-logo.png
    store-icon-192.png
    store-icon-512.png
    [brand]-logo.png  (one per brand, e.g. serta-logo.png)
  mattresses/
    [id].png  (one per mattress)
  accessories/
    [id].jpg  (one per accessory)
```

**Image requirements:**
- Mattresses: 600 x 400 px, PNG or JPG, transparent or white background
- Accessories: 400 x 300 px, PNG/JPG/WebP
- Logo: Min 400px wide, PNG with transparent background
- Icons: Exactly 192x192 and 512x512, square PNG

**File names must match the ID column in your spreadsheet.**

---

## Checklist Before Submitting

- [ ] Store Info tab filled out completely
- [ ] All mattresses entered with ID, Name, Brand, Tier, Firmness, Feature Keywords, and Why: Default
- [ ] All accessories entered with ID, Name, Category, Price, and Description
- [ ] Brands tab filled out with brand names and logo file names
- [ ] Store logo uploaded to `logos/`
- [ ] Brand logos uploaded to `logos/` (one per brand)
- [ ] Both PWA icons (192 + 512) uploaded to `logos/`
- [ ] One image per mattress in `mattresses/`, file names matching IDs
- [ ] One image per accessory in `accessories/`, file names matching IDs
- [ ] Yellow example rows deleted from spreadsheet

---

## What Happens Next

1. **You submit** — Complete the spreadsheet and upload images
2. **We build** — We generate your custom DreamFinder app (usually 1-2 business days)
3. **You review** — We send you a preview link to test on your tablets/devices
4. **We launch** — After your approval, we deploy the live version
5. **Training** — We provide a quick walkthrough for your sales team

---

## Questions?

Reach out to Blake anytime. We're here to help make this as smooth as possible.
