#!/usr/bin/env python3
"""
Patch 31 - dosage calculator: results above the input, always shown.

What Marc asked for
    Put the calculator output above the "Target medication level (mg)" box,
    and always show it, even before anything is typed - zeros are fine.

Behaviour after this patch
    - four result rows (Dose, 10 mg/ml vial, 15 mg/ml vial, Peak) are always
      rendered, above the label and input
    - empty or invalid input: Dose 0.00 mg, 0.00 ml (0 units) on both vial
      rows, Peak "≈ 0.0 mg in ~0 h"
    - target already reached by current doses: zeros on the dose rows and
      the Peak row reads "No dose needed" (same four rows, so the layout
      never changes height)
    - otherwise the values from patch 29, still recalculated as the target
      changes; the calculation itself is untouched

Fix (how)
    Replace the body of __glpalDoseCalc (the component inserted by patch 29)
    with one that renders the rows first and falls back to zeros. The old
    function text is taken from patch 29's own HELPERS string, so the anchor
    is exactly what patch 29 inserted.

What this deliberately does NOT change
    - __glpalCalc, __glpalLevels, __glpalTotalAt, the Avg Peak card

Usage
    python glpal_patch31_calclayout.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glpal_patch29_dosecalc import HELPERS as P29_HELPERS  # noqa: E402

EXPECTED_INPUT_SHA256 = "49111672aaba7538524bff25b5fd9d243f2aa48f6895d2c94925c666228f69fd"
EXPECTED_OUTPUT_SHA256 = "d24fc503a1d812934b081709608d56d30bbbb5e89d9ddf017910afeed2857c43"

OLD = P29_HELPERS[P29_HELPERS.index("function __glpalDoseCalc("):]
NEW = (
    'function __glpalDoseCalc(p){const[t,sT]=Q.useState(""),{isDarkMode:dk}=jr(),r=p.entries||[],mk=Math.floor(p.now.getTime()/6e4),'
    'T=Math.round(parseFloat(t)*10)/10,R=Q.useMemo(()=>__glpalCalc(r,T,mk*6e4),[r,T,mk]),'
    'nd=!!(R&&R.none),Z=R&&!R.none?R:{dose:0,peak:0,hours:0},'
    'tx=`text-sm ${dk?"text-white":"text-gray-700"}`,'
    'ln=(a,b)=>S.jsxs("div",{className:"flex justify-between "+tx,children:[S.jsx("span",{children:a}),S.jsx("span",{className:"font-semibold",children:b})]}),'
    'ml=c=>{const v=Z.dose/c;return v.toFixed(2)+" ml ("+Math.round(v*100)+" units)"};'
    'return S.jsxs("div",{className:"mt-3","data-glpal":"dose-calc",children:['
    'S.jsxs("div",{className:"mb-2","data-glpal":"dose-calc-results",children:['
    'ln("Dose",Z.dose.toFixed(2)+" mg"),ln("10 mg/ml vial",ml(10)),ln("15 mg/ml vial",ml(15)),'
    'ln("Peak",nd?"No dose needed":"\\u2248 "+Z.peak.toFixed(1)+" mg in ~"+Math.round(Z.hours)+" h")]}),'
    'S.jsx("label",{htmlFor:"glpalTarget",className:p.labelClass,children:"Target medication level (mg)"}),'
    'S.jsx("input",{id:"glpalTarget",type:"number",step:"0.1",min:"0",inputMode:"decimal",value:t,onChange:e=>sT(e.target.value),placeholder:"e.g. 10.1",'
    'className:`w-full px-3 py-2 mt-1 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#B19CD9]/50 ${dk?"border-[#B19CD9]/30 bg-black/20 text-white placeholder-gray-400":"border-gray-300 bg-white text-gray-700 placeholder-gray-400"}`})'
    ']})}'
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch31_calclayout.py INPUT_JS OUTPUT_JS")
    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Input is not the verified patch-30 bundle.\n"
                           f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")
    text = raw.decode("utf-8")
    if text.count(OLD) != 1:
        raise RuntimeError(f"patch-29 component found {text.count(OLD)} times, expected 1")
    text = text.replace(OLD, NEW, 1)
    if text.count("function __glpalDoseCalc(") != 1 or text.count('"data-glpal":"dose-calc-results"') != 1:
        raise RuntimeError("component replacement did not apply cleanly")
    if text.count("function __glpalCalc(") != 1:
        raise RuntimeError("__glpalCalc changed")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")
    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("calculator results now always shown, above the input")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
