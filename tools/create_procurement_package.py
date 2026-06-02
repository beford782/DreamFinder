#!/usr/bin/env python3
"""Create a local ZIP bundle of the procurement files.

The binary ZIP is intentionally generated locally rather than committed because
Codex's web PR/diff interface does not support binary file previews.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "continental_silverline_procurement_files.zip"
FILES = [
    ROOT / "procurement" / "continental_silverline_bid_setup_profile.md",
    ROOT / "procurement" / "mattress_bid_setup_questionnaire.csv",
    ROOT / "procurement" / "step_2_portal_and_commodity_checklist.md",
]

missing = [path for path in FILES if not path.exists()]
if missing:
    missing_list = "\n".join(f"- {path.relative_to(ROOT)}" for path in missing)
    raise SystemExit(f"Missing required files:\n{missing_list}")

with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
    for path in FILES:
        archive.write(path, arcname=path.name)

print(f"Created {OUTPUT.relative_to(ROOT)} with {len(FILES)} files")
