#!/usr/bin/env python3
"""
Patch 17 - dashboard layout and a Log tab rename.

Three changes:

1. Log tab: the "Daily Log" heading becomes "Weight Log", which is what the
   section actually contains.

2. The six Performance Overview cards move into the dashboard's top card grid.
   `Hge` (Performance Overview) stops rendering its own card wrapper, heading,
   divider and grid, and returns a fragment of bare cards instead. It is then
   rendered as the last child of the top grid, so all the cards flow in one
   `grid-cols-3 lg:grid-cols-6` layout.

3. The Performance Overview section disappears as a consequence - its heading
   and container are what step 2 removes, and its standalone render site is
   deleted.

Card count: the top grid had six (Current, BMI, Total Loss, Weekly Avg,
Monthly Avg, To Lose) and Performance Overview had six (Progress Rate, Best
Week, Time Active, Start Weight, Best Month, Total Loss). "Total Loss" appeared
in both, so the Performance Overview copy - which shows kg only, against the
top card's kg plus percentage - is dropped. Eleven cards result.

Order of operations matters: the standalone Hge render is removed BEFORE the
same call is inserted into the grid, otherwise the removal anchor would match
twice.

Colour note: anchors carry the ORIGINAL #B19CD9, not the shipped orange. This
patch runs before the recolour stage in build_fork.py, so anchors lifted from
docs/ (post-recolour) will not match here.

Usage:
  python glpal_patch17_layout.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "c12bae59191c5f5b86da0060a2719e890614b43bac5af918cdbcc4b7da5af780"
EXPECTED_OUTPUT_SHA256 = "c388a97543015b78bbb3de446fee4e40aea0ef7898332ed2a6f79826fcd37e5a"

RENDER = ('S.jsx(Hge,{weights:r,totalLoss:k.totalLoss,startWeight:k.startWeight,'
          'goalWeight:N,profile:e})')

# 1. rename
LOG_OLD = 'children:"Daily Log"'
LOG_NEW = 'children:"Weight Log"'

# 2. drop the standalone Performance Overview render
STANDALONE_OLD = ',' + RENDER
STANDALONE_NEW = ''

# 3. append the cards as the last child of the top grid, between the close of
#    the "To Lose" card and the close of the grid itself
GRID_OLD = ('children:Ci(k.currentWeight-N,P)})]})]}),'
            'S.jsx("div",{className:"border-t border-[#B19CD9]/20 my-3"})')
GRID_NEW = ('children:Ci(k.currentWeight-N,P)})]}),' + RENDER + ']}),'
            'S.jsx("div",{className:"border-t border-[#B19CD9]/20 my-3"})')

# 4. Hge returns bare cards instead of its own titled card container
HGE_HEAD_OLD = ('return S.jsxs("div",{className:i,children:['
                'S.jsx("h1",{className:o.title,children:"Performance Overview"}),'
                'S.jsx("div",{className:"border-t border-[#B19CD9]/20 mb-3"}),'
                'S.jsxs("div",{className:"grid grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3",children:[')
HGE_HEAD_NEW = 'return S.jsxs(Q.Fragment,{children:['

# 5. drop the duplicate Total Loss card and close the fragment
HGE_TAIL_OLD = (',S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,'
                'children:"Total Loss"}),S.jsx("div",{className:"text-left",'
                'children:S.jsx("p",{className:l.value,children:Ci(t,u)})})]})]})]})}')
HGE_TAIL_NEW = ']})}'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch17_layout.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-16 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    steps = [
        (LOG_OLD, LOG_NEW, "Daily Log -> Weight Log"),
        (STANDALONE_OLD, STANDALONE_NEW, "remove standalone Performance Overview"),
        (GRID_OLD, GRID_NEW, "append cards to the top grid"),
        (HGE_HEAD_OLD, HGE_HEAD_NEW, "Hge returns a fragment"),
        (HGE_TAIL_OLD, HGE_TAIL_NEW, "drop duplicate Total Loss"),
    ]
    for old, new, label in steps:
        if text.count(old) != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {text.count(old)}")
        text = text.replace(old, new, 1)

    if "Performance Overview" in text:
        raise RuntimeError("the Performance Overview heading survived")
    if text.count(RENDER) != 1:
        raise RuntimeError(f"expected exactly 1 Hge render, found {text.count(RENDER)}")
    if text.count('children:"Dose Log"') != 1:
        raise RuntimeError("the Dose Log heading was disturbed")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("cards merged into one grid; Performance Overview gone; Daily Log renamed")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
