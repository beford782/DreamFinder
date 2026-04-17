# DreamFinder — Template

Store-agnostic kiosk app for mattress showroom floors. This repo is the
**template** used to spin up a new retailer deployment. It contains no
retailer-specific content — branding, product data, colors, and text all
load from `data/` at runtime.

## What DreamFinder Is

A single-page tablet app where a customer:

1. Takes a 12-question sleep quiz
2. Gets scored mattress recommendations across Gold / Silver / Bronze tiers
3. Browses recommended accessories (bases, pillows, protectors)
4. Receives a discount code + results email
5. Hands off to a salesperson who sees their saved picks on screen

Bilingual English + Spanish by default. Runs on iPads.

## Spin Up a New Retailer

1. Clone this repo into a new repo owned by (or for) the retailer.
2. Retailer fills in the onboarding spreadsheet (`tools/create_template.py` generates it).
3. Run the converter against their submitted xlsx + images:

       python tools/convert_store_data.py ./incoming/Retailer.xlsx \
           --image-base-url "https://<org>.github.io/DreamFinder" \
           --source-images ./incoming \
           --output-dir .

   This writes `data/store-config.json`, `data/mattresses.csv`, and
   `data/accessories.json`, patches `Code.gs` and `manifest.json`, and
   converts submitted images to WebP under `images/`.

4. Regenerate `data/mattresses.json`:

       .\build-data.ps1

5. Drop retailer logos / PWA icons into `images/` and the repo root.
6. Create a Google Apps Script deployment (see `onboarding/Build_Runbook.md`),
   paste the `/exec` URL into `index.html`'s `GOOGLE_SCRIPT_URL` constant.
7. Add the new GitHub Pages domain to the domain lock `allowed` array in
   `index.html`.
8. Enable GitHub Pages on the new repo (main / root). Push.

Full walkthrough: `onboarding/Build_Runbook.md`.

## Layout

    index.html                  — the whole app (single file, no bundler)
    Code.gs                     — Google Apps Script for email + lead logging
    manifest.json               — PWA manifest
    build-data.ps1              — CSV → JSON + validation
    hooks/pre-commit            — guards against CSV/JSON drift
    data/
      store-config.json         — retailer branding + bilingual text
      mattresses.csv            — source of truth for the lineup
      mattresses.json           — generated from the CSV, don't edit
      mattresses-es.csv         — optional Spanish mattress translations
      accessories.json          — retailer accessories, bilingual
      dict-en.json              — shared English UI strings
      dict-es.json              — shared Spanish UI strings
    images/                     — retailer-owned: mattresses/, accessories/, logos/
    onboarding/                 — retailer-facing onboarding materials
    tools/
      create_template.py        — generates the retailer onboarding .xlsx
      convert_store_data.py     — reads filled xlsx, writes data/ + patches Code.gs
      md_to_pdf.py              — regenerates onboarding PDFs

## One-time Setup After Cloning

Activate the versioned pre-commit hook:

    git config core.hooksPath hooks
