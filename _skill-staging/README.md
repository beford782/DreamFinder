# Skill staging

This directory holds skills staged for installation under `~/.claude/skills/`.
They live here in the Bel repo so you can review them on the PR branch;
they are not used from this location.

## Install

    cp -r _skill-staging/new-retailer ~/.claude/skills/

After that, invoking `/new-retailer` from any directory will load the
skill. Claude auto-invokes it when you describe a new-retailer onboarding
task.

## Contents

- **new-retailer/** — spins up a new retailer deployment from a completed
  onboarding spreadsheet and image folder. Walks through the full flow
  (clone template, run converter, regenerate data, GAS deploy, Pages
  enable, smoke tests).
