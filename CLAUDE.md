# DreamFinder — notes for Claude

A single-page mattress recommendation quiz for an in-store tablet / web kiosk. Users answer a quiz, get recommended mattresses, and receive an email with a discount code.

## Stack

- Vanilla HTML/CSS/JS. No build step, no framework, no bundler, no tests.
- Entire app lives in one file: `index.html` (~318KB, ~5000+ lines).
- Data is externalized:
  - `data/mattresses.csv` — source of truth for mattress catalog (edit this).
  - `data/mattresses.json` — derived JSON the app loads at runtime.
  - `data/store-config.json` — store-level config.
- Backend: a single Google Apps Script endpoint handles email + discount-code logging. The URL is hardcoded as `GOOGLE_SCRIPT_URL` at `index.html:4868`.

## How to run / test

There is no dev server and no test suite. To verify a change:

1. Open `index.html` directly in a browser (file:// is fine for UI; email send needs the hosted version because Apps Script CORS).
2. Walk the full golden path: start → all quiz questions → results screen → email submit → discount reveal → restart.
3. Open the browser devtools console **before** reporting a task done. A clean console is a hard requirement — a missing semicolon has reached main before (`58e0aae`) because the change was never loaded in a browser.
4. Test on both desktop (mouse) and mobile viewport (touch). Click-handling bugs have repeatedly only shown up on desktop.

If you cannot actually open a browser from your environment, say so explicitly — do not claim a UI change is verified.

## Rules for Claude when working in this repo

### Debugging rule: no symptom-patching

If a fix on the same bug or same area fails twice, **stop patching**. Do not propose a third fix that adds another `pointer-events`, `z-index`, or `stopPropagation` tweak. Instead:

1. Read the full event path from the user's click target up through every ancestor.
2. Identify which element is actually intercepting the event and why.
3. Explain the root cause in plain English before touching code.

This repo has a history of this anti-pattern — see commits `19966ce`, `0d9cb8f`, `bdebe70`, `aa734da`, `9f7cecc`, which were five sequential patches on the same underlying click-blocking bug.

### Context rule: don't blindly Read all of index.html

`index.html` is huge. Reading the whole file burns context you'll need for the task. Prefer:

1. `Grep` for the relevant function, id, or class first.
2. `Read` with `offset` and `limit` around the matches.
3. Only read the full file if the task genuinely requires a whole-file rewrite.

### Deployment config lives in one place

When the Google Apps Script endpoint is redeployed (which happens), the only edit needed is `GOOGLE_SCRIPT_URL` at `index.html:4868`. Do not scatter URLs or discount prefixes elsewhere in the code.

### Commit style

Commit messages in this repo are short, lowercase, imperative, and scoped to one thing (e.g. `fix mattress card clicks on desktop`, `add DREAM discount code to email screen`). Match that style.

### Data edits

When adding or editing mattress entries, edit `data/mattresses.csv` as the source of truth, then regenerate/sync `data/mattresses.json` if the app reads the JSON form. Do not hand-edit the JSON without also updating the CSV.
