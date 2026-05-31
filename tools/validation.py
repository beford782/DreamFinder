#!/usr/bin/env python3
"""DreamFinder onboarding validation (V1) - structure + Store Info / store-config.

Hard validation so a bad workbook cannot silently produce a broken DreamFinder
deployment. V1 covers the highest-value gates:

  * workbook structure: required tabs, required headers, duplicate headers,
    Store Info exactly one data row, schema-required cells non-empty.
  * store-config values: storeName, slug-safe storeKey, languages, hex colors,
    HTTPS publicAssetRoot with trailing slash, allowedHosts hygiene, discount
    digits, manifest.start_url, gasUrl placeholder policy.

Deep per-row mattress/accessory/SalesNotes checks, image-existence checks, and
post-emit output validation are LATER phases (V2/V3) - not implemented here.

"Required" is derived from `tools/workbook_schema.py` `required` flags (the curated
source of truth), NOT a broad wishlist - fields like price / quizTags / pitchKey /
subBrand / topPickReason are legitimately blank in real data and are not required.

Dependency-light: stdlib + workbook_schema only. No openpyxl, no app imports. It
validates already-parsed structures (the converter's read rows + assembled config),
so it is unit-testable with plain dicts. ASCII console output. Run `--self-test`.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Shared schema lives alongside this file in tools/.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workbook_schema as schema  # noqa: E402


SUPPORTED_LANGUAGES = (["en"], ["en", "es"])
CODE_DIGITS_MIN, CODE_DIGITS_MAX = 3, 10
_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# -- Report -------------------------------------------------------------------

@dataclass
class ValidationReport:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors

    def __bool__(self) -> bool:
        return self.ok

    def merge(self, other: "ValidationReport") -> "ValidationReport":
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def blocking(self, warnings_as_errors: bool = False) -> bool:
        """True if the converter should abort: any error, or (under
        --warnings-as-errors) any warning."""
        return bool(self.errors) or (warnings_as_errors and bool(self.warnings))

    def summary(self) -> str:
        if not self.errors and not self.warnings:
            return "[validate] OK - no issues."
        lines = []
        if self.errors:
            lines.append(f"[validate] {len(self.errors)} error(s):")
            lines += [f"  ERROR: {e}" for e in self.errors]
        if self.warnings:
            lines.append(f"[validate] {len(self.warnings)} warning(s):")
            lines += [f"  WARN:  {w}" for w in self.warnings]
        return "\n".join(lines)


# -- Helpers ------------------------------------------------------------------

def _blank(v) -> bool:
    return v is None or str(v).strip() == ""


def _is_hex(v) -> bool:
    return isinstance(v, str) and bool(_HEX_RE.match(v.strip()))


def _is_slug(v) -> bool:
    return isinstance(v, str) and bool(_SLUG_RE.match(v.strip()))


def _host_from_url(url: str) -> str:
    """Extract the host from an https URL (no scheme, no path). '' if unparseable."""
    s = str(url).strip()
    if "://" in s:
        s = s.split("://", 1)[1]
    return s.split("/", 1)[0]


# -- Structure validation (raw tabs) ------------------------------------------
# raw_tabs maps PRESENT tab name -> (headers: list[str], rows: list[dict]).
# A required tab absent from raw_tabs is reported as missing.

def validate_structure(raw_tabs: Dict[str, Tuple[List[str], List[dict]]]) -> ValidationReport:
    r = ValidationReport()
    for tab in schema.get_tab_names():
        if tab not in raw_tabs:
            r.add_error(f"missing required tab: {tab!r}")
            continue
        headers, rows = raw_tabs[tab]

        # duplicate headers
        seen = set()
        for h in headers:
            if h in seen:
                r.add_error(f"{tab}: duplicate header {h!r}")
            seen.add(h)

        # required headers present
        required = schema.required_columns(tab)
        for col in required:
            if col.name not in headers:
                r.add_error(f"{tab}: missing required header {col.name!r}")

        # Store Info: exactly one data row
        if tab == "Store Info" and len(rows) != 1:
            r.add_error(f"Store Info: expected exactly 1 data row, found {len(rows)}")

        # schema-required cells non-empty (only for headers that are present)
        for col in required:
            if col.name not in headers:
                continue
            for i, row in enumerate(rows, start=1):
                if _blank(row.get(col.name)):
                    r.add_error(f"{tab} row {i}: required {col.name!r} is empty")
    return r


# -- Store-config value validation (assembled config dict) --------------------

def validate_store_config(config: dict, manifest: Optional[dict] = None, *,
                          require_gas_url: bool = False) -> ValidationReport:
    r = ValidationReport()

    if _blank(config.get("storeName")):
        r.add_error("storeName is empty")

    sk = config.get("storeKey")
    if _blank(sk):
        r.add_error("storeKey is empty")
    elif not _is_slug(sk):
        r.add_error(f"storeKey {sk!r} is not slug-safe (lowercase letters/digits/hyphens)")

    langs = config.get("languages")
    if langs not in SUPPORTED_LANGUAGES:
        r.add_error(f"languages must be ['en'] or ['en','es'], got {langs!r}")

    colors = config.get("colors") or {}
    if not _is_hex(colors.get("storePrimary")):
        r.add_error(f"colors.storePrimary missing or not a #hex color: {colors.get('storePrimary')!r}")
    for k in ("storePrimaryLight", "accent"):
        v = colors.get(k)
        if not _blank(v) and not _is_hex(v):
            r.add_error(f"colors.{k} is not a valid #hex color: {v!r}")

    par = config.get("publicAssetRoot")
    if _blank(par):
        r.add_error("publicAssetRoot is empty")
    else:
        par = str(par).strip()
        if not par.startswith("https://"):
            r.add_error(f"publicAssetRoot must be an HTTPS URL: {par!r}")
        if not par.endswith("/"):
            r.add_error(f"publicAssetRoot must end with a trailing slash: {par!r}")

    ah = config.get("allowedHosts")
    if not isinstance(ah, list) or not ah:
        r.add_error("allowedHosts is empty (the M1 domain lock requires at least the Pages host)")
    else:
        for h in ah:
            hs = str(h)
            if "://" in hs:
                r.add_error(f"allowedHosts entry {hs!r} must not include a protocol")
            if "/" in hs:
                r.add_error(f"allowedHosts entry {hs!r} must not include a path/slash")
            if hs in ("localhost", "127.0.0.1"):
                r.add_error(f"allowedHosts must not include {hs!r} (localhost/127.0.0.1 are a built-in fallback)")
        host = _host_from_url(par) if not _blank(par) else ""
        if host and host not in ah:
            r.add_warning(f"allowedHosts {ah} does not include the publicAssetRoot host {host!r} - "
                          f"the live site will blank on that host")

    disc = config.get("discount") or {}
    cd = disc.get("codeDigits")
    if isinstance(cd, bool) or not isinstance(cd, int) or not (CODE_DIGITS_MIN <= cd <= CODE_DIGITS_MAX):
        r.add_error(f"discount.codeDigits must be an integer {CODE_DIGITS_MIN}-{CODE_DIGITS_MAX}, got {cd!r}")

    gas = str(config.get("gasUrl") or "").strip()
    is_placeholder = _blank(gas) or "example" in gas.lower() or gas.upper() in ("TODO", "PLACEHOLDER")
    if is_placeholder:
        msg = "gasUrl is blank/placeholder (set it after the Google Apps Script deploy)"
        if require_gas_url:
            r.add_error(msg)
        else:
            r.add_warning(msg)

    if manifest is not None and _blank(manifest.get("start_url")):
        r.add_error("manifest.start_url is empty")

    return r


# -- V1 entrypoint ------------------------------------------------------------

def validate_bundle_inputs(raw_tabs, store_config, manifest=None, *,
                           require_gas_url: bool = False) -> ValidationReport:
    """V1 validation: workbook structure + store-config values. Caller passes the
    converter's parsed tabs and the assembled config/manifest (assembled only when
    structure is sound enough to do so)."""
    r = ValidationReport()
    r.merge(validate_structure(raw_tabs))
    r.merge(validate_store_config(store_config, manifest, require_gas_url=require_gas_url))
    return r


# -- Self-test (no pytest; stdlib only) ---------------------------------------

def _good_tabs():
    """A minimal structurally-valid raw_tabs (required headers + non-empty
    required cells) for every schema tab."""
    tabs = {}
    for tab in schema.get_tab_names():
        headers = schema.get_column_headers(tab)
        req = [c.name for c in schema.required_columns(tab)]
        row = {h: ("x" if h in req else "") for h in headers}
        # tier must be a valid value for structural row (not enum-checked in V1,
        # but keep it sensible); firmnessScore numeric-ish.
        if tab == "Mattresses":
            row["tier"] = "gold"
            row["firmnessScore"] = "5"
        tabs[tab] = (headers, [row])
    return tabs


def _good_config():
    return {
        "storeName": "Acme Mattress",
        "storeKey": "acme",
        "languages": ["en", "es"],
        "logo": {"main": "acme", "sub": "mattress"},
        "colors": {"storePrimary": "#123abc", "storePrimaryLight": "#2244cc",
                   "storePrimaryGlow": "rgba(1,2,3,0.15)", "accent": "#b8935d"},
        "gasUrl": "https://script.google.com/macros/s/AKxyz/exec",
        "publicAssetRoot": "https://acme.github.io/DreamFinder/",
        "allowedHosts": ["acme.github.io"],
        "discount": {"codePrefix": "DREAM", "codeDigits": 3},
    }


def _good_manifest():
    return {"name": "DreamFinder - Acme", "start_url": "/DreamFinder/"}


def _self_test() -> int:
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [ok]   {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")

    # minimal valid sample passes
    r = validate_bundle_inputs(_good_tabs(), _good_config(), _good_manifest())
    check("valid sample passes", r.ok and not r.warnings)

    # missing required tab
    t = _good_tabs(); del t["SalesNotes"]
    check("missing required tab -> error",
          any("missing required tab" in e for e in validate_structure(t).errors))

    # duplicate header
    t = _good_tabs()
    h, rows = t["Brands"]; t["Brands"] = (h + [h[0]], rows)
    check("duplicate header -> error",
          any("duplicate header" in e for e in validate_structure(t).errors))

    # Store Info multiple rows
    t = _good_tabs(); h, rows = t["Store Info"]; t["Store Info"] = (h, rows + [dict(rows[0])])
    check("Store Info multiple rows -> error",
          any("expected exactly 1 data row" in e for e in validate_structure(t).errors))

    # missing schema-required value
    t = _good_tabs(); h, rows = t["Mattresses"]; rows[0]["reason_default"] = ""
    check("missing required cell -> error",
          any("reason_default" in e for e in validate_structure(t).errors))

    # invalid hex color
    c = _good_config(); c["colors"]["storePrimary"] = "8B1A1A"
    check("invalid hex color -> error",
          any("storePrimary" in e for e in validate_store_config(c).errors))

    # missing allowedHosts
    c = _good_config(); c["allowedHosts"] = []
    check("missing allowedHosts -> error",
          any("allowedHosts is empty" in e for e in validate_store_config(c).errors))

    # allowedHosts with protocol
    c = _good_config(); c["allowedHosts"] = ["https://acme.github.io"]
    check("allowedHosts with protocol -> error",
          any("must not include a protocol" in e for e in validate_store_config(c).errors))

    # allowedHosts with localhost
    c = _good_config(); c["allowedHosts"] = ["acme.github.io", "localhost"]
    check("allowedHosts with localhost -> error",
          any("localhost" in e for e in validate_store_config(c).errors))

    # publicAssetRoot missing trailing slash
    c = _good_config(); c["publicAssetRoot"] = "https://acme.github.io/DreamFinder"
    check("publicAssetRoot no trailing slash -> error",
          any("trailing slash" in e for e in validate_store_config(c).errors))

    # blank gasUrl -> warning (not error) by default
    c = _good_config(); c["gasUrl"] = ""
    r = validate_store_config(c)
    check("blank gasUrl -> warning only", r.ok and any("gasUrl" in w for w in r.warnings))

    # --require-gas-url promotes gasUrl to error
    c = _good_config(); c["gasUrl"] = ""
    r = validate_store_config(c, require_gas_url=True)
    check("require_gas_url promotes gasUrl to error",
          any("gasUrl" in e for e in r.errors))

    # warnings_as_errors promotes allowedHosts-missing-Pages-host warning to blocking
    c = _good_config(); c["allowedHosts"] = ["someoneelse.github.io"]
    r = validate_store_config(c)
    check("allowedHosts missing Pages host -> warning",
          r.ok and any("does not include the publicAssetRoot host" in w for w in r.warnings))
    check("warnings_as_errors makes that warning blocking",
          r.blocking(warnings_as_errors=True) and not r.blocking(warnings_as_errors=False))

    # discount.codeDigits out of range
    c = _good_config(); c["discount"]["codeDigits"] = 2
    check("codeDigits out of range -> error",
          any("codeDigits" in e for e in validate_store_config(c).errors))

    # manifest.start_url empty
    m = dict(_good_manifest()); m["start_url"] = ""
    check("manifest.start_url empty -> error",
          any("manifest.start_url" in e for e in validate_store_config(_good_config(), m).errors))

    print(f"\nSelf-test: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true",
                        help="Run built-in validation checks and exit.")
    args = parser.parse_args(argv)
    if args.self_test:
        print("validation.py self-test:")
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
