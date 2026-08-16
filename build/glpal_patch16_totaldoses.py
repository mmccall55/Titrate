#!/usr/bin/env python3
"""
Patch 16 - the "Total Doses" card counts plan doses, not doses.

Symptom
-------
Doses tab with three logged doses and no dosing plan:

    Total Doses   0      <- wrong
    Planned Doses 0
    Logged Doses  3

Cause
-----
The stats object carries both values:

    K = { totalDoses: O,             // O = d.length, every dose record
          totalPlannedDoses: j,      // derived from dosing plans
          plannedDoses: j,           // the same value again
          allFuturePlannedDoses: q,  // plan-derived, future only
          ... }

The card labelled "Total Doses" renders `totalPlannedDoses`, and both plan
counters start with `if (!plans || plans.length === 0) return 0`. With no plan
they are structurally zero, so the card reads 0 no matter how many doses exist.
`totalDoses` is computed and never displayed.

Fix
---
Point the card at `totalDoses`.

Note this is not merely a duplicate of Logged Doses: `totalDoses` counts every
dose record, while Logged Doses filters on `isManual`. With no plan the two
agree; once a plan generates doses they diverge, which is the distinction the
card is presumably for.

Usage:
  python glpal_patch16_totaldoses.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "14e161b18f1950a00b03de32ef3427bc1352a0b18caefddef01952766d815e1a"
EXPECTED_OUTPUT_SHA256 = "c12bae59191c5f5b86da0060a2719e890614b43bac5af918cdbcc4b7da5af780"

OLD = ('S.jsx("p",{className:Qe.label,children:"Total Doses"}),'
       'S.jsx("p",{className:Qe.value,children:Ie.totalPlannedDoses})')
NEW = ('S.jsx("p",{className:Qe.label,children:"Total Doses"}),'
       'S.jsx("p",{className:Qe.value,children:Ie.totalDoses})')

# the Planned Doses card must keep reading the future-plan counter
PLANNED = ('S.jsx("p",{className:Qe.label,children:"Planned Doses"}),'
           'S.jsx("p",{className:Qe.value,children:Ie.allFuturePlannedDoses})')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch16_totaldoses.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-15 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    if text.count(OLD) != 1:
        raise RuntimeError(f"Total Doses card: expected 1 match, found {text.count(OLD)}")
    text = text.replace(OLD, NEW, 1)

    if text.count(PLANNED) != 1:
        raise RuntimeError("the Planned Doses card was altered; it must not be")
    if 'totalDoses:O' not in text:
        raise RuntimeError("stats no longer expose totalDoses")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("Total Doses card now reads stats.totalDoses")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
