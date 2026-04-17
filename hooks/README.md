# Git hooks

Versioned git hooks for this repo. Activate once per clone:

    git config core.hooksPath hooks

## What's here

- **pre-commit** — blocks commits where `data/mattresses.csv` or
  `data/mattresses-es.csv` change without a matching update to
  `data/mattresses.json`. Also JSON-lints `data/store-config.json`
  when staged. Bypass with `git commit --no-verify` when genuinely
  needed.

The CSV → JSON regeneration itself is done by `build-data.ps1` at the
repo root. The hook only enforces that it was run; it doesn't run it
for you (PowerShell availability varies across dev machines).
