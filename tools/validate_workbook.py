#!/usr/bin/env python3
"""Validate a DreamFinder onboarding workbook WITHOUT writing a bundle.

A thin convenience wrapper around `convert_store_data.py --validate-only`: it runs
the exact same validation (V1 structure + store-config, V2 catalog + source images)
the converter runs by default, but never emits any files. Use it as a quick check
before building, or as a final readiness gate with --warnings-as-errors /
--require-gas-url.

Usage:
    python tools/validate_workbook.py <workbook.xlsx> [--source-images DIR]
           [--skip-image-normalization] [--warnings-as-errors] [--require-gas-url]

Exit code: 0 if no blocking issues, non-zero otherwise. Output mirrors the
converter's --validate-only output (it IS the converter, run in validate-only
mode). Dependency-light: stdlib only; delegates to convert_store_data.py.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONVERTER = os.path.join(HERE, "convert_store_data.py")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an onboarding workbook (writes nothing).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("workbook", help="Path to the onboarding .xlsx")
    parser.add_argument("--source-images", default=None,
                        help="Folder with mattresses/, accessories/, and brands/ subdirs; "
                             "enables source-image (and brand-logo) existence checks.")
    parser.add_argument("--skip-image-normalization", action="store_true",
                        help="Skip source-image existence checks.")
    parser.add_argument("--warnings-as-errors", action="store_true",
                        help="Treat validation warnings as blocking (final-gate mode).")
    parser.add_argument("--require-gas-url", action="store_true",
                        help="Treat a blank/placeholder gasUrl as a blocking error.")
    args = parser.parse_args(argv)

    cmd = [sys.executable, CONVERTER, args.workbook, "--validate-only"]
    if args.source_images:
        cmd += ["--source-images", args.source_images]
    if args.skip_image_normalization:
        cmd += ["--skip-image-normalization"]
    if args.warnings_as_errors:
        cmd += ["--warnings-as-errors"]
    if args.require_gas_url:
        cmd += ["--require-gas-url"]

    # --validate-only never writes, but the converter takes an --output-dir; give it
    # a throwaway temp dir (cleaned up) so nothing can land in the cwd.
    with tempfile.TemporaryDirectory(prefix="df_validate_") as tmp:
        cmd += ["--output-dir", tmp]
        return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
