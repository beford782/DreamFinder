# DreamFinder Template — Claude Code Guide

## What This Repo Is

The store-agnostic template used to spin up new retailer deployments of
DreamFinder. It contains **no retailer-specific content** — no store name,
no brand colors, no product lineup, no GAS URL. All of that loads from
`data/` at runtime.

If you are reading this in a retailer's deployment (e.g. a clone named
`<retailer>/DreamFinder`), the retailer's CLAUDE.md in their repo overrides
this one.

## Hard Rules

### No retailer-specific content in `index.html`

No store names, logos, colors, mattress models, or discount codes hardcoded
in the HTML. All of that belongs in `data/store-config.json` and the CSV /
JSON data files. If you find yourself writing a store name into the HTML,
stop — the template is wrong, not the ask.

### Each retailer gets their own repo

This template is cloned into a per-retailer repo. Do not push template
changes to a retailer's repo, and do not copy retailer data back into the
template.

### Features must be config-driven

Any feature that could vary by store (colors, copy, quiz questions, tier
names, email templates) must read from `data/store-config.json`, not be
hardcoded. If a knob doesn't exist yet, add it to the config shape before
adding the feature.

### Quiz questions are currently hardcoded — known limitation

The 12 quiz questions live in the HTML. This is a known gap. Do not add
more hardcoded store-specific question logic. Flag quiz customization
requests as requiring a config migration first.

## Bilingual / i18n

The template ships EN + ES as a core feature. Every user-facing string must
be bilingual. Three mechanisms:

- **Shared UI strings**: `data/dict-en.json` / `data/dict-es.json`, read
  via `t('key')`. Generic, never retailer-specific.
- **Retailer text**: `store-config.json` → `text` + `text_es` blocks.
- **Inline bilingual objects**: `{en: "...", es: "..."}` in code, read via
  `L(obj)`. Used for quiz questions, profile names, mattress data.

Mattress text goes through `mField(m, field)` which reads `field_es` when
in Spanish mode and falls back to English gracefully.

`switchLanguage(lang)` reloads the dictionary and re-applies text.
`startOver()` resets language to English.

## Scoring Engine

`index.html` around line 4040. Three passes:

1. **Firmness** (max +50): `firmScore = max(0, 50 - diff * 10)`. Extra
   -20 penalty when `diff ≥ 4`.
2. **Feature matching**: quiz `opt.scores` map to `features` tags.
3. **Locally made bonus** (+25): `m.locallyMade === true` adds 25 and
   appends a match reason.

Qualified results = top 3 scoring ≥ 60% of the top score.

Do not change scoring weights without a human's OK — there has been
significant prior tuning.

## iPad / Touch Event Rules

These must survive every retailer deployment:

- `touch-action: manipulation` on all interactive elements
- Dynamic elements need both `touchend` and `pointerdown` listeners
- `event.preventDefault()` on touchend handlers to prevent ghost clicks
- Never use `location.reload()` — always `window.startOver()` to reset

Do not change touch handling without human review.

## Data Flow

- `data/mattresses.csv` (and optional `mattresses-es.csv`) → `build-data.ps1`
  → `data/mattresses.json`. Validates on build (hard-fail on duplicate ids,
  invalid tier, out-of-range firmness, missing required fields).
- `data/store-config.json` and `data/accessories.json` are edited directly
  and loaded at runtime.
- `hooks/pre-commit` blocks commits that stage CSV changes without the
  regenerated JSON. Enable with `git config core.hooksPath hooks`.

Never edit `data/mattresses.json` directly — always regenerate from the CSV.

## Setting Up a New Retailer

Use `tools/convert_store_data.py` with the retailer's filled onboarding
spreadsheet and image folder. It writes `data/store-config.json`,
`data/mattresses.csv`, `data/accessories.json`, and patches `Code.gs`
+ `manifest.json` in place.

Full walkthrough: `onboarding/Build_Runbook.md`.
