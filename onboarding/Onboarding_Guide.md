# DreamFinder Store Onboarding Guide

Welcome! DreamFinder is a personalized mattress recommendation app that helps your
floor sales team guide customers to their perfect mattress through a quick 12-question
sleep consultation quiz.

DreamFinder ships with **full English + Spanish bilingual support**. Customers can
toggle between languages on the welcome screen, and the entire experience — quiz,
results, email, and salesperson handoff — switches to their preferred language.

After the mattress results, customers enter the **Sleep System** flow where
foundations, pillows, and protectors are presented as part of a complete sleep
solution — not as optional add-ons. Customers with specific issues (snoring,
acid reflux, back pain) see a personalized **adjustable base hero** with
animated product demo and benefit cards explaining exactly how it helps them.

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
| Mattress product images | Any common format (JPG/PNG/WebP), one per mattress | `mattresses/` folder in Google Drive |
| Accessory product images | Any common format (JPG/PNG/WebP), one per accessory | `accessories/` folder in Google Drive |
| Spanish store text (optional) | Spreadsheet (Store Info tab) | Same spreadsheet, Spanish columns |
| Spanish mattress descriptions (optional) | Spreadsheet (Mattresses tab) | Same spreadsheet, Spanish columns |

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
- **Email Sender Name** — The "From" name on customer result emails
- **Email Subject Line** — The subject line on customer result emails
- **Contact Email** — Email shown on the privacy/terms screen
- **Store Phone** — Shown in the customer email and on the salesperson handoff screen
- **Store Address** — Shown in the customer email so they know where to come
- **Store Hours** — Shown in the customer email (e.g., "Mon–Sat 10am–8pm · Sun 12–6pm")
- **Footer Text** — The copyright/credit line at the bottom of the app (e.g., "Powered by DreamFinder · (c) 2026 Your Store Name")

**Spanish Translations (optional but recommended):**
DreamFinder includes a built-in EN/ES language toggle. The quiz, results, and
email are automatically translated, but your store-specific text needs Spanish
versions from you:
- **Trust Signal (Spanish)** — e.g., "Sirviendo con orgullo a las familias de Texas"
- **Footer Text (Spanish)** — e.g., "© 2026 Tu Tienda. Todos los derechos reservados."
- **Social Proof (Spanish)** — e.g., "Confiado por clientes de Tu Tienda"
- **Email Subject (Spanish)** — e.g., "Tus Resultados de DreamFinder de Tu Tienda"
- **Email Sender Name (Spanish)** — e.g., "Equipo de Descanso de Tu Tienda"

If you don't provide Spanish translations, we'll generate them for you. If you
don't want the Spanish toggle at all, just let us know and we'll disable it.

### Step 3: Fill Out the Mattresses Tab

Add one row for every mattress you want in the app. Key fields:

- **ID** — A short unique code (lowercase, no spaces). Example: `royal-cloud`
- **Tier** — `gold` (premium), `silver` (mid-range), or `bronze` (value). Controls display priority.
- **Firmness** — Rate 1 (ultra soft) to 10 (ultra firm)
- **Feature Keywords** — These drive the quiz matching algorithm. See the Feature Keywords tab for the full list with descriptions.
- **Image** — Name your mattress image file after the mattress **name**, lowercased (e.g. a mattress named `Royal Cloud` -> `royal-cloud.jpg`). Any common format; we convert to JPG. (Mattress images are matched by name — there's no image-filename column on this tab.)
- **"Why" columns** — Short selling points shown when a mattress matches. "Why: Default" is required.

**Spanish mattress text (optional):** If you'd like the mattress badge chips, highlight
lines, and "Why it matches you" reason text to appear in Spanish when customers toggle
to ES, provide Spanish translations for each mattress. We'll generate these for you if
not provided — they can always be refined later.

> **Tip:** This template is **blank** — just fill in your own rows. (If you'd like a
> fully worked example to copy from, ask us for the Bel Furniture sample workbook.)

### Step 4: Fill Out the Accessories Tab

Customers see your accessories as a "Sleep System" (foundation + pillow + protector) after choosing their mattress. Adjustable bases get special treatment — when a customer's quiz answers indicate snoring, acid reflux, or back pain, the #1 adjustable base is featured with a personalized benefit card. Pillows adapt to sleep position (side/back/stomach sleepers see different featured options).

Add bases/foundations, pillows, and protectors. Key fields:

- **Category** — Must be: `Foundations & Support`, `Pillows`, or `Protectors`
- **Sub-Type** (for Foundations only) — `adjustable` (gets the hero treatment), `foundation`, `low_profile`, or `bunkie`
- **Match Scores (0-5)** — Controls how strongly each accessory is recommended based on quiz answers. Leave blank if unsure — we can help fill these in.
- **Match Tags** — Used by the Sleep System hero logic. For adjustable bases, include relevant tags like `snoring`, `back_pain`, `reflux` so the customer sees a personalized benefit card when their quiz matches.

### Step 5: Fill Out the Brands Tab

Add one row for each mattress brand you carry. These appear in the "Our Brands" section at the bottom of the app.

- **Brand Name** — The display name (e.g., "Serta", "Sealy")
- **Logo File Name** — The exact file name of the brand's logo you provide in the `logos/` folder (e.g., `serta-logo.png` or `serta.jpg`). We copy it into the app automatically — transparent PNGs look best on the dark footer. Leave blank to show the brand name as text only.

### Step 6: Upload Images to the Shared Google Drive Folder

You'll receive a shared folder with this structure:

```
DreamFinder - [Your Store Name]/
  logos/
    [brand]-logo.png   (one per brand, e.g. serta-logo.png — shown in "Our Brands")
    app-icon.png       (optional — one square PNG ≥512px for the installable app icon)
  mattresses/
    [name].jpg         (one per mattress, named after the mattress NAME, lowercased)
  accessories/
    [image-file-name]  (one per accessory, matching its Image File Name)
```

> **Note:** Your store name currently appears as styled **text** in the app (set on
> the Store Info tab), so a `store-logo.png` image isn't used yet — you may send one
> for future use. The **app icon is optional**: drop one square PNG (≥512px) in
> `logos/` and enter its file name in the Store Info **App Icon File** column, and
> we generate the installable home-screen icons from it. Skip it and the app still
> works — it just has no custom install icon.

**Image requirements:**
- **Mattresses & accessories:** Up to **1000 px on the long edge**. Send the **highest-quality source you have** in any common format (JPG, PNG, WebP). We auto-convert everything to optimized JPG at build time, so don't waste time pre-shrinking.
- **Brand logos:** Min 400px wide, **PNG** with transparent background (kept as-is)
- **App icon (optional):** One **square PNG, ≥ 512×512** — we generate the 192 and 512 px app icons from it.

**Name mattress image files after the mattress name (lowercased); name accessory image files to match the Image File Name in the Accessories tab.**

> **About the auto-conversion:** during the build we resize images to a max of 1000 px on the long edge and re-encode as optimized JPG (quality 88). The result is dramatically smaller than the original with no visible loss, so customer-facing pages — and the result email — load fast even on slow showroom WiFi. (JPG specifically, because Outlook and iOS Mail render WebP unreliably in email.)

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
- [ ] Spanish store text provided (or noted as "generate for us")
- [ ] Spanish mattress text provided (or noted as "generate for us")

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
