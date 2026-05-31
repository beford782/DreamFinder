#!/usr/bin/env python3
"""Golden-bundle harness runner — S1 skeleton (expected-failing until S2).

Phase 0 plan: docs/phase0-onboarding-pipeline-spec-2026-05-31.md §4
("S1 harness structure" + staged activation).

End-to-end goal (once the converter rewrite exists):

    build_bel_workbook -> Bel.xlsx (temp workspace)
        -> [converter, S2+]  -> store-config.json, mattresses.csv(+es),
                                 accessories.json, manifest.json, allowed-hosts.js
        -> [build-data.ps1]  -> mattresses.json   (in the temp workspace)
        -> canonical compare generated outputs vs committed data/ + manifest.json

The converter rewrite (S2+) does NOT exist yet, and the *current* converter is
stale (it emits inline JS, not the bundle). So this runner deliberately does the
parts that are valid today — generate the Bel workbook fixture into a temp
workspace and verify the S1 building blocks — then **explicitly skips** the
end-to-end golden comparison rather than passing silently. Use --strict to make
the unavailable full flow a hard failure (for future CI once S2 lands).

It never mutates repo data/ and never writes a generated workbook inside the repo
(everything goes to a tempfile workspace). Stdlib only in this file; openpyxl is
pulled in transitively by build_bel_workbook.

Activation points (flip CONVERTER_AVAILABLE and wire golden_compare in S2+):
    S2 -> compare data/mattresses.csv (+ -es)            [canonical.compare_csv_files]
    S3 -> compare data/store-config.json, accessories    [canonical.compare_json_files]
    S4 -> compare data/mattresses.json (+ images)        [json; needs build-data.ps1 + images]
    S5 -> compare manifest.json                          [canonical.compare_json_files]
    S6 -> compare data/allowed-hosts.js                  [array vs store-config.allowedHosts]
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.fixtures import build_bel_workbook  # noqa: E402
from tests.golden import canonical  # noqa: E402


# Flipped to True in S2 when the converter rewrite can emit the bundle. Until
# then the end-to-end golden comparison cannot run and must not silently "pass".
CONVERTER_AVAILABLE = False


def prep_checks(workspace: str) -> bool:
    """Run the parts of the flow that are valid today: generate the Bel workbook
    fixture into the temp workspace (with its own round-trip self-check) and
    confirm the canonical helpers are importable."""
    ok = True

    wb_path = os.path.join(workspace, "bel_onboarding.xlsx")
    print(f"[S1] Generating Bel workbook fixture -> {wb_path}")
    rc = build_bel_workbook.main(["--output", wb_path])
    exists = os.path.exists(wb_path)
    if rc != 0:
        print(f"[S1] FAIL: fixture generator self-check returned {rc}")
        ok = False
    if not exists:
        print("[S1] FAIL: workbook was not created")
        ok = False
    else:
        print(f"[S1] OK: workbook present ({os.path.getsize(wb_path)} bytes)")

    # Canonical helpers sanity (the library self-tests separately; here we just
    # confirm it imported and the curated allow-list starts empty).
    print(f"[S1] OK: canonical helpers importable; "
          f"DEFAULT_ALLOWLIST empty: {canonical.DEFAULT_ALLOWLIST == []}")

    return ok


def golden_compare(workspace: str, strict: bool) -> int:
    """Run (or skip) the end-to-end converter-backed comparison."""
    if not CONVERTER_AVAILABLE:
        msg = ("converter rewrite (S2+) not available - no generated bundle to "
               "compare against committed data/ yet.")
        if strict:
            print(f"[STRICT] Golden compare unavailable: {msg}")
            print("[STRICT] Exiting non-zero: full golden flow cannot run until S2.")
            return 1
        print(f"[SKIP] Golden compare skipped until S2 converter rewrite: {msg}")
        print("       Activation points:")
        print("         S2 -> data/mattresses.csv (+ -es)         [csv]")
        print("         S3 -> data/store-config.json, accessories [json]")
        print("         S4 -> data/mattresses.json (+ images)     [json, needs build-data.ps1]")
        print("         S5 -> manifest.json                       [json]")
        print("         S6 -> data/allowed-hosts.js               [array]")
        return 0

    # ── FUTURE (S2+) wiring — intentionally not implemented in S1 ──────────────
    # The converter rewrite must NOT run the current stale converter. Once it
    # exists, the flow here is roughly:
    #
    #   1. Generate the workbook (done above, in `workspace`).
    #   2. Copy committed scripts + data/ + images/ into `workspace` (isolation;
    #      build-data.ps1 is $PSScriptRoot-bound — never target repo data/).
    #   3. Run the converter on the workbook -> bundle files in `workspace`.
    #   4. Shell out to pwsh/powershell to run build-data.ps1 -> mattresses.json
    #      (reuse the pwsh||powershell detection from tools/hooks/pre-commit).
    #   5. result = canonical.CompareResult()
    #      result.merge(canonical.compare_csv_files(<committed>, <generated>,   # S2
    #                                               allowlist=canonical.DEFAULT_ALLOWLIST))
    #      result.merge(canonical.compare_json_files(...))                       # S3/S4/S5
    #      ... S6 allowed-hosts.js (array compare helper, added later) ...
    #      print(result.summary())
    #      return 0 if result.ok else 1
    raise NotImplementedError("converter-backed golden compare wiring lands in S2+")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true",
                        help="Treat the (currently unavailable) full golden flow "
                             "as a hard failure. For future CI once S2 lands.")
    args = parser.parse_args(argv)

    print("=" * 70)
    print("DreamFinder golden-bundle harness (S1 skeleton)")
    print("=" * 70)

    with tempfile.TemporaryDirectory(prefix="dreamfinder_golden_") as workspace:
        print(f"Temp workspace: {workspace}")
        print("-" * 70)
        if not prep_checks(workspace):
            print("-" * 70)
            print("[FAIL] S1 prep checks failed.")
            return 1
        print("-" * 70)
        print("[PASS] S1 prep checks.")
        print("-" * 70)
        return golden_compare(workspace, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
