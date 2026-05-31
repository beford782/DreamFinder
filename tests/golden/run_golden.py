#!/usr/bin/env python3
"""Golden-bundle harness runner - phase-aware (S2 + S3 active).

Phase 0 plan: docs/phase0-onboarding-pipeline-spec-2026-05-31.md section4
("S1 harness structure" + staged activation).

End-to-end goal (built up phase by phase):

    build_bel_workbook -> Bel.xlsx (temp workspace)
        -> [converter]       -> mattresses.csv(+es)               [S2, ACTIVE]
                              -> store-config.json, accessories.json [S3, ACTIVE]
                              -> images (jpg) + mattresses.json      [S4]
                              -> manifest.json                       [S5]
                              -> allowed-hosts.js                    [S6]
        -> canonical compare generated outputs vs committed data/ + manifest.json

Currently wired: **S2 + S3** - generate the Bel workbook, run the converter into a
temp workspace, and canonically compare the generated mattresses.csv /
mattresses-es.csv (CSV) and store-config.json / accessories.json (JSON) against
the committed Bel files. These compares are REQUIRED in normal mode (a mismatch
fails the run). S4-S6 are still pending and reported as such.

--strict: runs S2+S3 too, but exits non-zero while S4-S6 remain unwired (so future
CI only goes green once the full flow lands), even when S2+S3 pass.

Never mutates repo data/ and never writes generated files inside the repo
(everything goes to a tempfile workspace). S2+S3 need no images or build-data.ps1
(CSV/JSON-only compares); that machinery arrives with S4. Stdlib only in this
file; openpyxl is pulled in transitively by build_bel_workbook.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.fixtures import build_bel_workbook  # noqa: E402
from tests.golden import canonical  # noqa: E402

CONVERTER = REPO_ROOT / "tools" / "convert_store_data.py"

# (label, generated filename, comparison kind) for the active compares.
CSV_COMPARES = ["mattresses.csv", "mattresses-es.csv"]
JSON_COMPARES = ["store-config.json", "accessories.json"]

# Phases not yet wired into the runner (reported as pending).
PENDING_PHASES = [
    ("S4", "data/mattresses.json (+ image normalization)", "json, needs build-data.ps1 + images"),
    ("S5", "manifest.json", "json"),
    ("S6", "data/allowed-hosts.js", "array vs store-config.allowedHosts"),
]


def generate_workbook(workspace: str) -> str | None:
    """Generate the Bel fixture workbook into the workspace. Returns its path,
    or None if generation/self-check failed."""
    wb_path = os.path.join(workspace, "bel_onboarding.xlsx")
    print(f"[prep] Generating Bel workbook fixture -> {wb_path}")
    rc = build_bel_workbook.main(["--output", wb_path])
    if rc != 0 or not os.path.exists(wb_path):
        print(f"[prep] FAIL: fixture generation rc={rc}, exists={os.path.exists(wb_path)}")
        return None
    print(f"[prep] OK: workbook present ({os.path.getsize(wb_path)} bytes)")
    print(f"[prep] OK: canonical helpers importable; "
          f"DEFAULT_ALLOWLIST empty: {canonical.DEFAULT_ALLOWLIST == []}")
    return wb_path


def run_converter(workspace: str, wb_path: str) -> bool:
    """Run the converter on the workbook into the workspace (CSV + JSON)."""
    print(f"[convert] Running converter -> {workspace} (--skip-build-json)")
    proc = subprocess.run(
        [sys.executable, str(CONVERTER), wb_path,
         "--output-dir", workspace, "--skip-build-json"],
        capture_output=True, text=True)
    if proc.stdout.strip():
        print("  " + proc.stdout.strip().replace("\n", "\n  "))
    if proc.returncode != 0:
        print(f"[convert] FAIL: converter exited {proc.returncode}")
        if proc.stderr.strip():
            print("  " + proc.stderr.strip().replace("\n", "\n  "))
        return False
    return True


def compare_outputs(workspace: str) -> canonical.CompareResult:
    """Canonically compare generated outputs vs committed Bel files:
    S2 CSVs (mattresses) + S3 JSON (store-config, accessories)."""
    result = canonical.CompareResult()
    data = Path(workspace) / "data"

    for phase, names, fn in (("S2", CSV_COMPARES, canonical.compare_csv_files),
                             ("S3", JSON_COMPARES, canonical.compare_json_files)):
        for name in names:
            committed = REPO_ROOT / "data" / name
            generated = data / name
            if not generated.exists():
                result.differences.append(f"{name} - generated file missing at {generated}")
                result.ok = False
                print(f"[{phase}] {name}: MISSING")
                continue
            r = fn(str(committed), str(generated), label=name,
                   allowlist=canonical.DEFAULT_ALLOWLIST)
            print(f"[{phase}] {name}: {r.summary().splitlines()[0]}")
            result.merge(r)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true",
                        help="Run S2+S3, but exit non-zero while S4-S6 remain "
                             "unwired (for future CI once the full flow lands).")
    args = parser.parse_args(argv)

    print("=" * 70)
    print("DreamFinder golden-bundle harness (S2 + S3 active)")
    print("=" * 70)

    with tempfile.TemporaryDirectory(prefix="dreamfinder_golden_") as workspace:
        print(f"Temp workspace: {workspace}")
        print("-" * 70)

        wb_path = generate_workbook(workspace)
        if wb_path is None:
            print("-" * 70)
            print("[FAIL] prep failed.")
            return 1

        print("-" * 70)
        # -- S2 + S3: converter -> CSV/JSON -> canonical compare (REQUIRED) -----
        ok = run_converter(workspace, wb_path)
        if ok:
            result = compare_outputs(workspace)
            print(result.summary())
            ok = result.ok
        print("-" * 70)
        print(f"[S2+S3] {'PASS' if ok else 'FAIL'}: mattresses CSV + "
              f"store-config/accessories JSON golden compare.")

        # -- S4-S6: still pending ----------------------------------------------
        print("-" * 70)
        print("Pending phases (not yet wired):")
        for sid, what, kind in PENDING_PHASES:
            print(f"  {sid} -> {what}   [{kind}]")
        print("-" * 70)

    if not ok:
        print("[FAIL] S2+S3 golden compare failed.")
        return 1

    if args.strict:
        print("[STRICT] S2+S3 passed, but S4-S6 are not wired yet - exiting "
              "non-zero (full golden flow incomplete).")
        return 1

    print("[PASS] S2+S3 golden compare passed. (S4-S6 pending; run without "
          "--strict treats those as not-yet-required.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
