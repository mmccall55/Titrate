#!/usr/bin/env python3
"""
Patch 18 - dashboard card set and order.

Final set, left to right:

    Current Weight, Start Weight, Total Loss, To Lose, BMI,
    Best Week, Best Month, Time Active

Removed: Weekly Avg, Monthly Avg, Progress Rate.
Renamed: "Current" -> "Current Weight".

The cards come from two components - the dashboard grid (classes w / D) and
`Hge` (classes s / l) - and cannot be freely interleaved, because each card
reads variables scoped to its own component. The requested order happens to
split cleanly: the first five all come from the dashboard grid and the last
three all come from Hge, which renders immediately after them.

The one exception is Start Weight, which lived in Hge. It is rebuilt in the
dashboard grid's own style using `k.startWeight`, the same value Hge was
already being passed. Hge's copy is dropped.

After this Hge no longer reads its totalLoss, startWeight or goalWeight props.
They are left in place rather than unpicking the call site.

The literals below were generated from the patch-17 artifact rather than typed,
so the untouched cards are preserved byte for byte.

Usage:
  python glpal_patch18_cards.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "c388a97543015b78bbb3de446fee4e40aea0ef7898332ed2a6f79826fcd37e5a"
EXPECTED_OUTPUT_SHA256 = "46b1164aab5818c1f3dd8f7f8ba4db398205a1123429188f2eeceff14c7242e2"

TOP_OLD = 'S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Current"}),S.jsx("p",{className:D.value,children:Ci(k.currentWeight,P)})]}),S.jsxs("div",{className:w,children:[S.jsxs("div",{className:"flex justify-between items-center mb-1",children:[S.jsx("p",{className:D.label,children:"BMI"}),S.jsx(_ye,{})]}),S.jsxs("p",{className:D.totalLossValue,style:{display:"flex",justifyContent:"space-between",alignItems:"flex-end"},children:[S.jsx("span",{style:{display:"inline-block",whiteSpace:"nowrap"},children:k.bmi.toFixed(1)}),S.jsxs("span",{className:`${D.bmiCategory} ${k.bmiCategory.color}`,children:["(",k.bmiCategory.category,")"]})]})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Total Loss"}),S.jsxs("p",{className:D.totalLossValue,style:{display:"flex",justifyContent:"space-between",alignItems:"flex-end"},children:[S.jsx("span",{style:{display:"inline-block",whiteSpace:"nowrap"},children:Ci(k.totalLoss,P)}),S.jsxs("span",{className:D.percentage,children:["(",k.totalLossPercentage.toFixed(1),"%)"]})]})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Weekly Avg"}),S.jsxs("p",{className:D.value,children:[k.weeklyAverageLoss>0?"-":"",Ci(Math.abs(k.weeklyAverageLoss),P)]})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Monthly Avg"}),S.jsxs("p",{className:D.value,children:[k.monthlyAverageLoss>0?"-":"",Ci(Math.abs(k.monthlyAverageLoss),P)]})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"To Lose"}),S.jsx("p",{className:D.value,children:Ci(k.currentWeight-N,P)})]})'

TOP_NEW = 'S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Current Weight"}),S.jsx("p",{className:D.value,children:Ci(k.currentWeight,P)})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Start Weight"}),S.jsx("p",{className:D.value,children:Ci(k.startWeight,P)})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"Total Loss"}),S.jsxs("p",{className:D.totalLossValue,style:{display:"flex",justifyContent:"space-between",alignItems:"flex-end"},children:[S.jsx("span",{style:{display:"inline-block",whiteSpace:"nowrap"},children:Ci(k.totalLoss,P)}),S.jsxs("span",{className:D.percentage,children:["(",k.totalLossPercentage.toFixed(1),"%)"]})]})]}),S.jsxs("div",{className:w,children:[S.jsx("p",{className:D.label,children:"To Lose"}),S.jsx("p",{className:D.value,children:Ci(k.currentWeight-N,P)})]}),S.jsxs("div",{className:w,children:[S.jsxs("div",{className:"flex justify-between items-center mb-1",children:[S.jsx("p",{className:D.label,children:"BMI"}),S.jsx(_ye,{})]}),S.jsxs("p",{className:D.totalLossValue,style:{display:"flex",justifyContent:"space-between",alignItems:"flex-end"},children:[S.jsx("span",{style:{display:"inline-block",whiteSpace:"nowrap"},children:k.bmi.toFixed(1)}),S.jsxs("span",{className:`${D.bmiCategory} ${k.bmiCategory.color}`,children:["(",k.bmiCategory.category,")"]})]})]})'

HGE_OLD = 'return S.jsxs(Q.Fragment,{children:[S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Progress Rate"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:[(t/(e-a)*100).toFixed(1),"%"]})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Best Week"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:["-",Ci(SM.calculateBestWeek(r),u)]})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Time Active"}),S.jsx("div",{className:"text-left",children:S.jsx("p",{className:l.value,children:c()})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Start Weight"}),S.jsx("div",{className:"text-left",children:S.jsx("p",{className:l.value,children:Ci(e,u)})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Best Month"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:["-",Ci(SM.calculateBestMonth(r),u)]})})]})]})}'

HGE_NEW = 'return S.jsxs(Q.Fragment,{children:[S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Best Week"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:["-",Ci(SM.calculateBestWeek(r),u)]})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Best Month"}),S.jsx("div",{className:"text-left",children:S.jsxs("p",{className:l.value,children:["-",Ci(SM.calculateBestMonth(r),u)]})})]}),S.jsxs("div",{className:s,children:[S.jsx("p",{className:l.label,children:"Time Active"}),S.jsx("div",{className:"text-left",children:S.jsx("p",{className:l.value,children:c()})})]})]})}'

GONE = ("Weekly Avg", "Monthly Avg", "Progress Rate")
KEPT = ("Current Weight", "Start Weight", "Total Loss", "To Lose", "BMI",
        "Best Week", "Best Month", "Time Active")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch18_cards.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-17 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    for old, new, label in ((TOP_OLD, TOP_NEW, "dashboard grid cards"),
                            (HGE_OLD, HGE_NEW, "Hge cards")):
        if text.count(old) != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {text.count(old)}")
        text = text.replace(old, new, 1)

    for label in GONE:
        if f'children:"{label}"' in text:
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
    print("8 cards: Current Weight, Start Weight, Total Loss, To Lose, BMI, "
          "Best Week, Best Month, Time Active")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
