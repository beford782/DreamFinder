# DreamFinder — Claude Code Project Guide

## Working With Blake

If Blake asks you to do something and you know of a better approach —
whether it's a cleaner implementation, a simpler workflow, a tool that
would make the task easier, or a potential pitfall with the current
approach — **speak up before acting**. Briefly explain the alternative
and let him decide. Don't just silently execute what was asked if you
can see a better path.

---

## What DreamFinder Is
DreamFinder is a store-agnostic single-page tablet kiosk app for mattress showroom floors.
Customers take a 12-question sleep quiz, get personalized mattress recommendations across
Gold/Silver/Bronze tiers, browse accessories, and receive results + a discount code by email.
Salespeople get a handoff screen showing the customer's saved picks.

**DreamFinder is a white-label product.** The canonical app has no relationship to any
specific retailer. Each store gets its own fully customized deployment.

---

## This Repo — Bel Furniture Deployment
Deployed at: https://beford782.github.io/DreamFinder
Repo: https://github.com/beford782/DreamFinder
Local path: `C:\Users\BlakeFord\Documents\GitHub\DreamFinder`

This is Bel Furniture's instance. Everything in `data/` is Bel-specific.
Do not treat any Bel-specific content (mattress models, branding, discount codes,
GAS endpoint) as a default or starting point for other retailers.

---

## Working pattern: terminal + web review

Claude Code in terminal does the work. Web Claude (claude.ai) reviews
the work for non-mechanical changes. Sequential, not parallel.

- Terminal Claude Code is the primary surface for DreamFinder work —
  file edits, greps, commits, pushes, local dev server.
- Web Claude is the second pair of eyes for high-stakes changes:
  schema additions, white-label boundary changes, new public API
  fields, anything where "trust the wiring" feels tempting.
- Skip web review for genuinely mechanical work (typo fixes, dict
  string updates, single-property CSS tweaks).
- Handoff: paste terminal output (proposals, diffs, grep results,
  git status) into web chat verbatim. Do not summarize — the value
  is in raw output, including narration the terminal session might
  gloss over.
- Do not run both surfaces editing files in parallel on the same
  task. Sequential only.

Cadence that has shipped clean: discovery → proposal → web review →
approval → implement → verify → commit → push. Single commit at a
time, browser-verify between commits, no back-to-back-without-review.

Reference: 2026-04-30 / 2026-05-01 sessions shipping commits 72424d1
(handoff idle timeout), 9e2f256 (dream code wipe), 7f766fd (Nocturnal
dead code retire) all followed this pattern.

---

## White-Label Architecture — Critical Rules

### The store-agnostic boundary
`index.html` must contain zero store-specific content. No retailer names, logos,
colors, mattress models, or discount codes hardcoded in the HTML.

All store identity lives in two files only:
- `data/store-config.json` — branding, store name, colors, brands list, GAS URL,
  public asset root, and all retailer-specific copy (text / text_es blocks)
- `data/mattresses.csv` / `data/mattresses.json` — this store's mattress lineup

### Each retailer gets its own repo
Do not push Bel changes to another retailer's deployment.
Do not copy `data/mattresses.csv` between retailer repos — each store has a
completely different product lineup.

**Deployments (separate repos):**
- Bel Furniture — this repo (active)
- The Furniture Market — `beford782/TheFurnitureMarket` (active)
- Star Furniture — separate repo (planned)
- Lacks Furniture — separate repo (planned)

### New features must be config-driven
Any feature that could vary by store (colors, copy, quiz questions, tier names,
email templates) must be driven by `store-config.json`, not hardcoded.
If you find yourself writing a store name or brand color into the HTML, stop —
it belongs in config.

### Quiz questions are currently hardcoded — known limitation
The 12 quiz questions and their answer options live in the HTML, not in config.
This is a known gap. Do not add more hardcoded store-specific question logic.
Flag any question customization requests as requiring a config migration first.

---

## App Architecture — Read Before Touching Anything

### Single-file HTML
`index.html` is the entire app. No separate JS or CSS files. Do not split it.

### Domain Lock
A domain lock at the top of the `<script>` block restricts where the app runs.
Allowed hosts: `beford782.github.io`, `localhost`, `127.0.0.1`.
If deploying to a new domain, add it to the `allowed` array around line 3824.

Opening `index.html` via `file://` is **not supported** — the domain lock rejects
empty hostname, and even if it didn't, browser CORS blocks `fetch()` of
`data/*.json` on the file protocol. For local development, serve the repo root
over HTTP (e.g. `python -m http.server 8000`, `npx http-server`, or VS Code's
Live Server) and open `http://localhost:8000/`.

### Data files
- `data/mattresses.csv` — source of truth for mattress lineup, edit this
- `data/mattresses-es.csv` — Spanish translations for mattress display text (optional per retailer)
- `data/mattresses.json` — generated file, never edit directly
- `data/store-config.json` — all store-specific configuration
- `data/dict-en.json` — English UI dictionary (shared across all retailers)
- `data/dict-es.json` — Spanish UI dictionary (shared across all retailers)

The app fetches mattresses.json, store-config.json, and the active dictionary at load time.

### Build script
```
.\build-data.ps1
```
Run from repo root. Converts `data\mattresses.csv` → `data\mattresses.json`.
If `data\mattresses-es.csv` exists, merges Spanish translations as `tags_es`,
`highlight_es`, `reasons_es` fields into the JSON.
Always run this before committing if the CSV was changed.
Never commit CSV changes without also committing the regenerated JSON.

### Git hooks (one-time activation per clone)
This repo ships hooks in `tools/hooks/`, activated via `core.hooksPath`.
Git does **not** auto-enable hooks from a clone for security reasons, so on a
**fresh clone (new machine, or a new retailer repo forked from this one)** run
once:
```
git config core.hooksPath tools/hooks
```
Without this, the hook files exist but never fire. Current hooks:
- `pre-push` — refuses any non-fast-forward push to `main` (stale-local-main guard).
- `pre-commit` — when a mattress CSV is staged, re-runs `build-data.ps1` and
  refuses the commit if `data/mattresses.json` is out of sync. Enforces the
  "never commit CSV without regenerated JSON" rule above. Escape hatch:
  `GIT_SKIP_CSV_BUILD=1 git commit ...`. Requires `pwsh` or `powershell` on PATH.

---

## Bilingual / i18n Architecture — Critical Rules

DreamFinder ships with full English + Spanish support as a core feature of the
white-label template. Every new retailer deployment includes bilingual accessibility
by default. Do not treat this as optional or Bel-specific.

### How it works
- **Language toggle** (EN | ES) appears on the welcome screen. Controlled by
  `store-config.json` field `"languages": ["en", "es"]`. Toggle hides automatically
  if only one language is configured.
- **UI strings** live in `data/dict-en.json` and `data/dict-es.json`. These are
  generic (not retailer-specific) and shared across all deployments. Do not put
  store names, slogans, or brand copy in the dict files.
- **Retailer-specific text** lives in `store-config.json` under `text` (English)
  and `text_es` (Spanish) blocks. This includes trust signals, footer copy, email
  privacy text, social proof, and in-stock labels.
- **Quiz questions, profile names, and label constants** use inline bilingual
  objects `{en: "...", es: "..."}` directly in `index.html`. The `L(obj)` function
  reads the active language from these objects.
- **Mattress product text** (badges, highlights, match reasons) is translated via
  `data/mattresses-es.csv`. The build script merges these into `mattresses.json`.
  If a retailer hasn't provided Spanish product translations, the app falls back
  to English text gracefully.
- **Email** is sent in the customer's chosen language. The client builds the HTML
  email body in the active language and sends `lang: currentLang` in the GAS payload.
  `Code.gs` uses this for the subject line and server-side fallback.
- **Session reset** (`startOver()`) always resets language to English.

### Rules for new features
- Any new user-facing string must be bilingual. Use `t('key')` for dict lookups
  or `{en: "...", es: "..."}` with `L()` for inline data.
- Never hardcode English-only display text in JavaScript template literals.
- Retailer-specific copy (store name, taglines, footer) goes in `store-config.json`
  `text` and `text_es` blocks — never in the dict files.
- When adding new quiz questions or options, always include both `en` and `es` values.
- When adding new accessories, use `{en: "...", es: "..."}` for `name`, `category`,
  and `description` fields.

### Key functions
- `t(key, replacements)` — dictionary lookup with optional `{placeholder}` interpolation
- `L(obj)` — reads `currentLang` from a `{en: "...", es: "..."}` object; falls back
  to plain strings gracefully
- `mField(m, field)` — language-aware mattress field accessor (reads `field_es` when
  in Spanish mode)
- `applyTranslations()` — applies `data-i18n` attributes on all tagged HTML elements
- `switchLanguage(lang)` — reloads dictionary, updates toggle UI, re-applies text
- `applyLanguageConfig()` — shows/hides toggle based on `store-config.languages`

---

## Mattress Data — CSV Column Reference

| Column | Notes |
|---|---|
| `tier` | gold / silver / bronze |
| `id` | g1–g33, unique per deployment, never reuse |
| `name` | Model name |
| `brand` | Spring Air / Restonic / Bel-O-Pedic (Bel-specific) |
| `subBrand` | Sub-line (Copper, Last Mattress, etc.) |
| `firmnessScore` | 1–10 number used by scoring engine |
| `firmnessLabel` | Display text (Plush, Medium, Firm, etc.) |
| `price` | Leave blank — not displayed in app |
| `locally-made` | yes / no — affects scoring (see below) |
| `quizTags` | Pipe-delimited. Used by scoring engine as `features` in JSON |
| `displayBadges` | Pipe-delimited. 2–3 chips shown on card |
| `highlight` | One punchy line for the card hero (~10 words) |
| `features` | Long-form feature text for display |
| `reason_*` | Personalised match reason shown to customer per quiz answer |

---

## Scoring Engine — How Recommendations Work

Located in `index.html` around line 4040. Three scoring passes:

**1. Firmness (most important, max +50)**
Linear sliding scale: `firmScore = max(0, 50 - diff * 10)` where
`diff = |customerFirmness - mattressFirmness|`. So: diff 0 = +50,
diff 1 = +40, diff 2 = +30, diff 3 = +20, diff 4 = +10, diff 5+ = 0.
Additionally, if `diff ≥ 4` an extra **-20** penalty is applied,
so a diff of 4 nets -10 and a diff of 5+ nets -20.

**2. Feature matching**
Quiz answers map to feature tags via `opt.scores`. Each matching tag adds points.
Tags are stored in the JSON `features` array (mapped from `quizTags` in CSV).

**3. Locally made bonus (+25)**
If `m.locallyMade === true`, adds 25 points and appends a match reason.
In the Bel deployment: Spring Air and Restonic = locally made, Bel-O-Pedic = not.
This value and logic may differ per retailer deployment.

Qualified results = top 3 models scoring ≥ 60% of the top score.

IMPORTANT: Do not modify scoring weights or logic without confirming with Blake.
This area has had significant prior tuning.

---

## Backend — Google Apps Script

Email delivery and lead logging use a Google Apps Script (GAS) web app.
The GAS endpoint URL lives in `data/store-config.json` under `gasUrl`.
Each retailer deployment has its own GAS script and endpoint.

Absolute image URLs for the HTML email body are built from
`store-config.json`'s `publicAssetRoot` (each retailer's own public
hostname); emails fall back to relative URLs if that field is missing.

If GAS needs redeployment: Manage Deployments → pencil icon → New version.
The GAS script builds email HTML server-side to avoid payload size limits.

---

## iPad / Touch Event Rules

The app runs on iPads in showrooms. These rules must be preserved in all deployments:
- `touch-action: manipulation` on all interactive elements
- Dynamic elements (mattress cards, buttons) need both `touchend` and `pointerdown` listeners
- `event.preventDefault()` on touchend handlers to prevent ghost clicks
- `location.reload()` must never be used — always call `window.startOver()` to reset

IMPORTANT: Do not change touch handling without confirming with Blake — this required
significant debugging to get right.

---

## Key App Flows (Don't Break These)

- **Quiz → Results**: 9 questions → scoring engine → Gold/Silver/Bronze tier tabs → top pick badge
- **Mattress drawer**: Opens on card tap. Prev/next navigation between results. Firmness bar, match reasons, features.
- **Accessories / Sleep System**: Framed as "Build Your Sleep System" (not add-ons).
  Conditional adjustable base hero (shown when quiz flags snoring, reflux, or back pain)
  with animated SVG and personalized benefit cards. Featured top pillow with "Matched to
  Your Profile" badge. "Did You Know?" educational callout for protectors. Sticky cart bar.
  Cart persists to handoff screen.
- **Discount reveal**: Dramatic animation — DREAM + 3-digit code. 10rem gold glow font.
- **Handoff screen**: Customer marks "I'm Interested" on mattresses/accessories. Salesperson sees saved picks.
- **Idle timeout**: Inactivity triggers reset flow back to start screen. Uses `window.startOver()`.

---

## Image Format Convention

**MUST:** all mattress and accessory images are `.jpg`, lowercase
kebab-case, no spaces, no underscores.

- ✅ `copper-ice-regular.jpg`, `kimber-firm.jpg`, `adjustable-4150.jpg`
- ❌ `Copper Ice Regular.png`, `kimber_firm.webp`, `AdjustableBase.PNG`

**Why:** Outlook desktop's Word render engine doesn't support `.webp`
at all, handles `.png` unreliably (especially with URL-encoded spaces
in the filename), and iOS Mail's Mail Privacy Protection is stricter
still. Customer results emails routinely ship product images, so any
image outside the jpg-kebab-case convention shows as a broken link.

**When adding a new mattress or accessory image:**
1. Save as `.jpg` at quality 85–90.
2. Filename lowercase, kebab-case, no spaces. Must match the
   mattress `name` column in CSV (lowercased, spaces kept in CSV but
   use kebab-case in the filename if you're adding a new product —
   the build script tolerates spaces for legacy files, prefers
   kebab-case going forward).
3. Drop into `images/mattresses/` or `images/accessories/`.
4. For accessories, reference the filename in `index.html`'s
   `ACCESSORIES` array.

**Converting existing webp or png assets:**
```python
from PIL import Image
Image.open('source.webp').convert('RGB').save('target.jpg', 'JPEG', quality=88, optimize=True)
```

`build-data.ps1` resolves extensions in order `jpg, png, webp`, so a
leftover `.webp` won't break anything — but new images should be jpg
from the start to avoid the email rendering gap.

---

## Deployment

```
git add .
git commit -m "description"
git push origin main --force
```

Force push is intentional — always used for this repo.
GitHub Pages updates within 1–2 minutes after push.

### IMPORTANT: Claude Code on the Web creates feature branches automatically
If this session is running in Claude Code on the web (claude.ai/code),
pushes default to a `claude/<name>-<id>` branch — NOT to main.
GitHub Pages only deploys from main, so those pushes do not go live.

**At the start of every session and before any commit/push, Claude MUST:**
1. Check the current branch with `git branch --show-current`
2. If the branch is anything other than `main`, warn Blake clearly that
   pushes on this branch will NOT deploy, and offer to either:
   - Push to main directly: `git push origin HEAD:main --force`, or
   - Use the `git ship` alias (already configured locally) which does the same

Never assume a push to a `claude/*` branch is a successful deployment.
Always confirm main was updated before reporting that a change is live.

---

## Don't touch without checking with Blake first

- Modify scoring weights or logic in the quiz engine
- Change touch event handling
- Hardcode any store-specific content into `index.html`
- Copy mattress data or config between retailer repos
- Edit `data/mattresses.json` directly (always regenerate from CSV)
- Add store names, colors, or branding anywhere except
  `store-config.json`
