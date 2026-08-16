#!/usr/bin/env python3
"""
Patch 15 - hide the Peptides and Calculator sections.

Deliberately a hiding patch, not a removal. The routes, components and data
stores stay in the bundle; they are simply unreachable. That keeps the change
to two anchors instead of unpicking a minified dependency graph, and it means
existing peptide records in IndexedDB are left intact rather than orphaned.

What changes:
  1. The Peptides and Calculator entries are filtered out of the bottom nav,
     so neither tab can be reached. Note the Calculator tab's id is
     "dosage", not "calculator".
  2. The "Peptide Log" card on the Log tab is short-circuited to false, so the
     Log tab shows only the Dose Log and Daily Log.

What deliberately does not change:
  - The peptides and peptideLogs object stores, and any data in them.
  - The Peptide filter chip in Medication Storage on the Doses tab, which is a
     category filter for medications rather than peptide functionality.

Usage:
  python glpal_patch15_trim.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "1b5d6f0bb61a7f9308085186783727d71f9ce4ae441f1ecf0b728e24155b6a35"
EXPECTED_OUTPUT_SHA256 = "14e161b18f1950a00b03de32ef3427bc1352a0b18caefddef01952766d815e1a"

NAV_OLD = '}],[]);return S.jsx("nav",'
NAV_NEW = ('}].filter(z=>z.id!=="peptides"&&z.id!=="dosage"),[]);'
           'return S.jsx("nav",')

PEPLOG_OLD = ('S.jsxs("div",{className:i,children:[S.jsxs("div",{className:"flex justify-between '
              'items-center mb-2 cursor-pointer",onClick:()=>$t(!Je),children:[S.jsx("h1",'
              '{className:g.title,children:"Peptide Log"})')
PEPLOG_NEW = '!1&&' + PEPLOG_OLD

# the remaining tabs must survive
KEEP = ('id:"dashboard"', 'id:"doses"', 'id:"log"')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch15_trim.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-14 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    for old, new, label in ((NAV_OLD, NAV_NEW, "nav filter"),
                            (PEPLOG_OLD, PEPLOG_NEW, "peptide log card")):
        if text.count(old) != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {text.count(old)}")
        text = text.replace(old, new, 1)

    for tab in KEEP:
        if text.count(tab) != 1:
            raise RuntimeError(f"{tab} should still be present exactly once")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("Peptides and Calculator hidden; Peptide Log card disabled")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
