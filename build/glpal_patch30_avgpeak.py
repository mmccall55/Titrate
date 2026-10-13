#!/usr/bin/env python3
"""
Patch 30 - "Avg Peak (14d)" card on the Doses tab.

What Marc asked for
    A fourth card next to Total Doses, Current Level and Logged Doses showing
    the highest levels attained over the last 14 days, averaged.

Definition (agreed)
    A peak is a point where the modelled total level stops rising and starts
    falling - the top of each bump on the dose chart, normally one per dose.
    The card averages every peak whose time falls in the last 336 hours and
    has already happened (a dose whose peak is still ahead is not counted
    yet). No peaks in the window shows "--". Same model and inputs as the
    Current Level card (__glpalLevels / __glpalTotalAt from patch 29), sampled
    at 15-minute steps; shown to 2 decimals in mg like Current Level.

Fix (how)
    - new module-level function __glpalAvgPeak(records, now), inserted before
      `function __glpalDoseAt(`
    - a fourth card appended after Logged Doses, same markup as its siblings
    - the Doses card grid becomes `grid-cols-2 lg:grid-cols-4` (2x2 on a
      phone, one row of 4 on a wide screen); both classes exist in the
      shipped CSS

What this deliberately does NOT change
    - the other cards, v1, the chart, stored data

Usage
    python glpal_patch30_avgpeak.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "a9ba5fcf6250d8fab2b230eadfd0c54aed4f5507dc955de7d0769f8494453a4e"
EXPECTED_OUTPUT_SHA256 = "49111672aaba7538524bff25b5fd9d243f2aa48f6895d2c94925c666228f69fd"

HELPER_ANCHOR = "function __glpalDoseAt("
HELPER = (
    'function __glpalAvgPeak(r,now){if(!r||!r.length)return"--";const L=__glpalLevels(r),e=now.getTime(),st=9e5,a=e-336*36e5,p=[];'
    'let pv=__glpalTotalAt(L,new Date(a-st)),cu=__glpalTotalAt(L,new Date(a));'
    'for(let t=a+st;t<=e;t+=st){const nx=__glpalTotalAt(L,new Date(t));cu>pv&&cu>=nx&&cu>0&&p.push(cu);pv=cu;cu=nx}'
    'return p.length?(p.reduce((x,y)=>x+y,0)/p.length).toFixed(2)+"mg":"--"}'
)

LOGGED = 'children:r.filter(Dt=>Dt.isManual).length})]})'
CARD = (',S.jsxs("div",{className:Pe,children:[S.jsx("p",{className:Qe.label,children:"Avg Peak (14d)"}),'
        'S.jsx("p",{className:Qe.value,children:__glpalAvgPeak(r,ie)})]})')
GRID_OLD = ('grid grid-cols-3 lg:grid-cols-3 gap-2 sm:gap-3 overflow-visible",children:[S.jsxs("div",'
            '{className:Pe,children:[S.jsx("p",{className:Qe.label,children:"Total Doses"')
GRID_NEW = GRID_OLD.replace("grid grid-cols-3 lg:grid-cols-3", "grid grid-cols-2 lg:grid-cols-4", 1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch30_avgpeak.py INPUT_JS OUTPUT_JS")
    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Input is not the verified patch-29 bundle.\n"
                           f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")
    text = raw.decode("utf-8")
    if "__glpalAvgPeak" in text:
        raise RuntimeError("__glpalAvgPeak already present")
    if "function __glpalLevels(" not in text:
        raise RuntimeError("patch 29 helpers missing")
    for anchor in (HELPER_ANCHOR, LOGGED, GRID_OLD):
        if text.count(anchor) != 1:
            raise RuntimeError(f"anchor {anchor[:40]!r} found {text.count(anchor)} times, expected 1")
    text = text.replace(HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1)
    text = text.replace(LOGGED, LOGGED + CARD, 1)
    text = text.replace(GRID_OLD, GRID_NEW, 1)
    if text.count('"Avg Peak (14d)"') != 1:
        raise RuntimeError("card label count wrong")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")
    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("Avg Peak (14d) card added; Doses grid is 2x2 / 4-across")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
