#!/usr/bin/env python3
"""
Patch 19 - drop the Best Week and Best Month cards.

Final card set, left to right:

    Current Weight, Start Weight, Total Loss, To Lose, BMI, Time Active

Monthly Avg was already removed in patch 18, along with Weekly Avg and
Progress Rate, so only the two "Best" cards remain to go.

`Hge` is now down to a single card (Time Active). It is kept as a component
rather than inlined because Time Active is computed by a closure over its
`weights` prop, which the dashboard grid does not otherwise hold.

The literal below was generated from the patch-18 artifact rather than typed,
so the surviving card is preserved byte for byte.

Usage:
  python glpal_patch19_bestcards.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "46b1164aab5818c1f3dd8f7f8ba4db398205a1123429188f2eeceff14c7242e2"
EXPECTED_OUTPUT_SHA256 = "ff23c8f4593df5cefd946aba41b7f013de7274d8e3aad40326c0f87befe1d786"

HGE_OLD = 'return S.jsxs(Q.Fragment,{children:[S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Best Week"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:["-",Ci(SM.calculateBestWeek(r),u)]})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Best Month"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:["-",Ci(SM.calculateBestMonth(r),u)]})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Time Active"}),S.jsx("div",{className:"text-left",children:S.jsx("p",{className:l.value,children:c()})})]})]})}'

HGE_NEW = 'return S.jsxs(Q.Fragment,{children:[S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Time Active"}),S.jsx("div",{className:"text-left",children:S.jsx("p",{className:l.value,children:c()})})]})]})}'

GONE = ("Best Week", "Best Month", "Weekly Avg", "Monthly Avg", "Progress Rate")
KEPT = ("Current Weight", "Start Weight", "Total Loss", "To Lose", "BMI", "Time Active")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch19_bestcards.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-18 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    if text.count(HGE_OLD) != 1:
        raise RuntimeError(f"Hge fragment: expected 1 match, found {text.count(HGE_OLD)}")
    text = text.replace(HGE_OLD, HGE_NEW, 1)

    for label in GONE:
        if 'children:"' + label + '"' in text:
            raise RuntimeError(f"{label} card survived")
    for label in KEPT:
        n = text.count('children:"' + label + '"')
        if n != 1:
            raise RuntimeError(f"expected exactly one {label} card, found {n}")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("6 cards: Current Weight, Start Weight, Total Loss, To Lose, BMI, Time Active")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
