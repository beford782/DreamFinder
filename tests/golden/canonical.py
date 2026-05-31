#!/usr/bin/env python3
"""Canonical / semantic comparison helpers for the golden-bundle test (S1c).

Phase 0 plan: docs/phase0-onboarding-pipeline-spec-2026-05-31.md §4.

The golden-bundle test proves the converter can reproduce Bel's committed bundle
from a Bel workbook. Comparing the regenerated files byte-for-byte against the
committed ones is hopeless — ``data/mattresses.json`` is serialized by PowerShell
(`ConvertTo-Json`, idiosyncratic whitespace) while config/accessories are
hand-maintained 2-space JSON, and CSVs differ in quoting/line-endings. So we
compare *semantically*:

  * JSON — parse, then deep-compare: dicts key-order-insensitively, lists in
    order, strings verbatim, numbers numerically.
  * CSV  — parse with DictReader, compare rows in order and cells by column name,
    tolerating CRLF/LF, quoting, and missing-vs-empty optional cells.

A small **allow-list** lets a curated, *reasoned* set of cosmetic diffs pass.
Nothing is silently ignored: every waived diff carries a reason and is reported
in ``CompareResult.allowed``. The default allow-list is empty.

Dependency-free (stdlib only). No openpyxl, no app imports, no file writes (the
loaders read; nothing here writes). Usable as a library now; ``run_golden.py``
(S1c, next) will consume it. A ``--self-test`` mode gives local sanity coverage
without pytest/CI.

Out of scope here (later phases): image comparison (S4) and allowed-hosts.js
comparison (S6).
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Result + allow-list types ────────────────────────────────────────────────

@dataclass(frozen=True)
class AllowEntry:
    """One curated, reasoned waiver. A diff is waived when its ``label`` and
    ``path`` match exactly. ``reason`` is mandatory — no silent ignores."""
    file: str
    path: str
    reason: str


@dataclass
class CompareResult:
    """Outcome of one comparison.

    ok           True when there are no unwaived differences.
    differences  human-readable lines for unwaived diffs (these fail the test).
    allowed      human-readable lines for diffs waived by the allow-list.
    """
    ok: bool = True
    differences: List[str] = field(default_factory=list)
    allowed: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok

    def merge(self, other: "CompareResult") -> "CompareResult":
        self.differences.extend(other.differences)
        self.allowed.extend(other.allowed)
        self.ok = self.ok and other.ok
        return self

    def summary(self) -> str:
        lines = []
        status = "PASS" if self.ok else "FAIL"
        lines.append(f"[{status}] {len(self.differences)} difference(s), "
                     f"{len(self.allowed)} allowed")
        for d in self.differences:
            lines.append(f"  - {d}")
        for a in self.allowed:
            lines.append(f"  ~ {a}")
        return "\n".join(lines)


def _match_allow(allowlist: Optional[List[AllowEntry]], label: str,
                 path: str) -> Optional[AllowEntry]:
    for entry in (allowlist or []):
        if entry.file == label and entry.path == path:
            return entry
    return None


def _finalize(raw: List[Tuple[str, str]], label: str,
              allowlist: Optional[List[AllowEntry]]) -> CompareResult:
    """Turn (path, message) diff records into a CompareResult, applying waivers."""
    result = CompareResult()
    for path, msg in raw:
        entry = _match_allow(allowlist, label, path)
        if entry is not None:
            result.allowed.append(f"{label}:{path} — ALLOWED ({entry.reason}): {msg}")
        else:
            result.differences.append(f"{label}:{path} — {msg}")
    result.ok = not result.differences
    return result


# ── JSON canonical comparison ────────────────────────────────────────────────

def canonical_json_load(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _kind(v: Any) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "str"
    if v is None:
        return "null"
    if isinstance(v, dict):
        return "dict"
    if isinstance(v, list):
        return "list"
    return "other"


def _short(v: Any, n: int = 60) -> str:
    s = repr(v)
    return s if len(s) <= n else s[:n] + "…"


def _diff_json(expected: Any, actual: Any, path: str,
               raw: List[Tuple[str, str]]) -> None:
    ek, ak = _kind(expected), _kind(actual)
    if ek != ak:
        raw.append((path or "(root)",
                    f"type mismatch: expected {ek} {_short(expected)}, "
                    f"got {ak} {_short(actual)}"))
        return

    if ek == "dict":
        e_keys, a_keys = set(expected), set(actual)
        for k in sorted(e_keys - a_keys):
            raw.append((f"{path}.{k}".lstrip("."), f"missing key (expected {_short(expected[k])})"))
        for k in sorted(a_keys - e_keys):
            raw.append((f"{path}.{k}".lstrip("."), f"unexpected key (got {_short(actual[k])})"))
        for k in expected:  # preserve a stable, source-driven order
            if k in actual:
                _diff_json(expected[k], actual[k], f"{path}.{k}".lstrip("."), raw)
        return

    if ek == "list":
        if len(expected) != len(actual):
            raw.append((path or "(root)",
                        f"list length: expected {len(expected)}, got {len(actual)}"))
        for i in range(min(len(expected), len(actual))):
            _diff_json(expected[i], actual[i], f"{path}[{i}]", raw)
        return

    if ek == "number":
        if expected != actual:  # numeric: 1 == 1.0 is fine
            raw.append((path or "(root)", f"number: expected {expected!r}, got {actual!r}"))
        return

    # str / bool / null — exact
    if expected != actual:
        raw.append((path or "(root)", f"value: expected {_short(expected)}, got {_short(actual)}"))


def compare_json_data(expected: Any, actual: Any, label: str = "json",
                      allowlist: Optional[List[AllowEntry]] = None) -> CompareResult:
    raw: List[Tuple[str, str]] = []
    _diff_json(expected, actual, "", raw)
    return _finalize(raw, label, allowlist)


def compare_json_files(expected_path: str, actual_path: str,
                       label: Optional[str] = None,
                       allowlist: Optional[List[AllowEntry]] = None) -> CompareResult:
    label = label or os.path.basename(expected_path)
    return compare_json_data(canonical_json_load(expected_path),
                             canonical_json_load(actual_path), label, allowlist)


# ── CSV canonical comparison ─────────────────────────────────────────────────

def canonical_csv_load(path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Return (fieldnames, rows). utf-8-sig strips any BOM; newline='' lets the
    csv module own line-terminator handling (CRLF/LF tolerance)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def _cell_equal(a: Any, b: Any) -> bool:
    # Tolerate missing-vs-empty: DictReader yields None for absent cells.
    a = "" if a is None else a
    b = "" if b is None else b
    return a == b


def compare_csv_data(expected: Tuple[List[str], List[Dict[str, str]]],
                     actual: Tuple[List[str], List[Dict[str, str]]],
                     label: str = "csv",
                     allowlist: Optional[List[AllowEntry]] = None) -> CompareResult:
    e_hdr, e_rows = expected
    a_hdr, a_rows = actual
    raw: List[Tuple[str, str]] = []

    e_set, a_set = set(e_hdr), set(a_hdr)
    for c in e_hdr:
        if c not in a_set:
            raw.append(("header", f"missing column {c!r}"))
    for c in a_hdr:
        if c not in e_set:
            raw.append(("header", f"unexpected column {c!r}"))
    if e_set == a_set and e_hdr != a_hdr:
        # Same columns, different order — non-functional (DictReader reads by
        # name), but reported so it can be explicitly waived if desired.
        raw.append(("header_order", f"column order differs: expected {e_hdr}, got {a_hdr}"))

    if len(e_rows) != len(a_rows):
        raw.append(("row_count", f"expected {len(e_rows)} rows, got {len(a_rows)}"))

    common_cols = [c for c in e_hdr if c in a_set]
    for i in range(min(len(e_rows), len(a_rows))):
        er, ar = e_rows[i], a_rows[i]
        for c in common_cols:
            if not _cell_equal(er.get(c), ar.get(c)):
                raw.append((f"row[{i}].{c}",
                            f"cell: expected {_short(er.get(c))}, got {_short(ar.get(c))}"))

    return _finalize(raw, label, allowlist)


def compare_csv_files(expected_path: str, actual_path: str,
                      label: Optional[str] = None,
                      allowlist: Optional[List[AllowEntry]] = None) -> CompareResult:
    label = label or os.path.basename(expected_path)
    return compare_csv_data(canonical_csv_load(expected_path),
                            canonical_csv_load(actual_path), label, allowlist)


# Default curated allow-list. Empty by design — every waiver must be added here
# deliberately, with a reason, by a human (or a reviewed change).
DEFAULT_ALLOWLIST: List[AllowEntry] = []


# ── Local self-test (no pytest/CI) ───────────────────────────────────────────

def _self_test() -> int:
    import tempfile

    passed = 0
    failed = 0

    def check(name: str, cond: bool):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [ok]   {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")

    # ---- JSON ----
    # key order-insensitive + numeric 1 vs 1.0 equal
    check("json: reordered keys equal",
          compare_json_data({"a": 1, "b": 2}, {"b": 2, "a": 1}).ok)
    check("json: 1 == 1.0 numerically",
          compare_json_data({"n": 1}, {"n": 1.0}).ok)
    check("json: nested lists in order equal",
          compare_json_data({"x": [1, {"y": "z"}]}, {"x": [1, {"y": "z"}]}).ok)
    # changed string -> diff
    r = compare_json_data({"s": "hi"}, {"s": "bye"})
    check("json: changed string differs", (not r.ok) and len(r.differences) == 1)
    # missing key -> diff
    check("json: missing key differs",
          not compare_json_data({"a": 1, "b": 2}, {"a": 1}).ok)
    # list length -> diff
    check("json: list length differs",
          not compare_json_data({"x": [1, 2]}, {"x": [1]}).ok)
    # bool vs number not falsely equal (True == 1 in Python, but kinds differ)
    check("json: true != 1 (type)",
          not compare_json_data({"b": True}, {"b": 1}).ok)
    # allow-list waives a known diff (reported as allowed, ok stays True)
    al = [AllowEntry(file="cfg.json", path="s", reason="known cosmetic")]
    r = compare_json_data({"s": "a"}, {"s": "b"}, label="cfg.json", allowlist=al)
    check("json: allow-list waives diff", r.ok and len(r.allowed) == 1 and not r.differences)

    # ---- CSV (quoting + CRLF tolerance via real files) ----
    with tempfile.TemporaryDirectory() as d:
        exp = os.path.join(d, "exp.csv")
        act = os.path.join(d, "act.csv")
        rows = [{"id": "g1", "name": "A, B", "note": ""},
                {"id": "g2", "name": "C", "note": "x"}]
        # expected: minimal quoting, LF
        with open(exp, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "note"], lineterminator="\n")
            w.writeheader(); w.writerows(rows)
        # actual: QUOTE_ALL + CRLF, same data
        with open(act, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "note"],
                               quoting=csv.QUOTE_ALL, lineterminator="\r\n")
            w.writeheader(); w.writerows(rows)
        check("csv: quoting+CRLF differences tolerated",
              compare_csv_files(exp, act).ok)

        # changed cell -> diff
        act2 = os.path.join(d, "act2.csv")
        rows2 = [dict(rows[0]), dict(rows[1])]
        rows2[1]["note"] = "y"
        with open(act2, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "note"], lineterminator="\n")
            w.writeheader(); w.writerows(rows2)
        r = compare_csv_files(exp, act2)
        check("csv: changed cell differs", (not r.ok) and any("row[1].note" in d_ for d_ in r.differences))

        # row count -> diff
        act3 = os.path.join(d, "act3.csv")
        with open(act3, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "note"], lineterminator="\n")
            w.writeheader(); w.writerows(rows[:1])
        check("csv: row count differs",
              any("row_count" in d_ for d_ in compare_csv_files(exp, act3).differences))

    # ---- CSV missing-vs-empty + header order (in-memory) ----
    # None (absent) vs "" treated equal
    check("csv: None vs '' tolerated",
          compare_csv_data((["id", "x"], [{"id": "1", "x": None}]),
                           (["id", "x"], [{"id": "1", "x": ""}])).ok)
    # same columns, different order -> reported (header_order)
    r = compare_csv_data((["a", "b"], [{"a": "1", "b": "2"}]),
                         (["b", "a"], [{"a": "1", "b": "2"}]))
    check("csv: header order reported", (not r.ok) and any("header_order" in d_ for d_ in r.differences))
    # ...and waivable
    r = compare_csv_data((["a", "b"], [{"a": "1", "b": "2"}]),
                         (["b", "a"], [{"a": "1", "b": "2"}]),
                         label="x.csv",
                         allowlist=[AllowEntry("x.csv", "header_order", "order non-functional")])
    check("csv: header order waivable", r.ok and len(r.allowed) == 1)

    print(f"\nSelf-test: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true",
                        help="Run built-in sanity checks and exit.")
    args = parser.parse_args(argv)
    if args.self_test:
        print("canonical.py self-test:")
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
