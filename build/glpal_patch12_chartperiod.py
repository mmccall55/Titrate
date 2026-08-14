#!/usr/bin/env python3
"""
Patch 12 - the Week/Month/90 Days/All Time selector does nothing on the
weight chart.

Symptom
-------
The period buttons visibly retime the dose chart but leave the weight chart
unchanged. Measured with synthetic histories:

    10 days of weights   1 of 4 periods rendered differently  (selector dead)
    45 days of weights   3 of 4
    150 days of weights  4 of 4

Cause
-----
The weight chart gets its zoom window from `Oge`, which derives percentages
from `d` - the span of the WEIGHT DATA in days:

    const u = (last - first) / oneDay
    const d = Math.ceil(u)
    if (period !== "all" && d >= c) { ...percentages of d... }
    // else: no zoom at all, h=0 v=100

Two separate faults follow:

1. When the recorded history is shorter than the selected window (`d < c`),
   the branch is skipped entirely and the chart shows everything. A new user
   with two weeks of weigh-ins gets identical output from all four buttons.

2. Even when the branch runs, the percentages are computed against `d` but
   applied to the category axis `k`, which is longer because it carries the
   forward projection. A percentage of the wrong denominator lands the window
   in the wrong place.

The dose chart avoids this because its equivalent helper builds its axis and
its percentages from the same array.

Fix
---
Compute the window directly from the axis in view: anchor it on `O`, the index
of today already used for the "today" marker, and express it as a percentage of
`k.length`. The window is the selected number of days of history plus a half
window of lookahead, matching the lookahead the dose chart's helper already
uses. "All Time" stays 0-100.

Day counts are kept as the app defined them (week 14, month 30, 90days 90) so
this changes only whether the selector works, not what each option means.

Usage:
  python glpal_patch12_chartperiod.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "37638391810ef2babbee71c5482db5c6bc49fe8d3163b2a9a54d78326b4dfd69"
EXPECTED_OUTPUT_SHA256 = "5797758f0e14262c54051165c93129eb91d9c5e2905716a0b07a08f95d1c9a76"

HELPER = (
    'function __glpalWeightZoom(k,O,e){'
    'const n=k&&k.length?k.length:0;'
    'if(n<2)return{start:0,end:100};'
    'const D={week:14,month:30,"90days":90}[e];'
    'if(!D)return{start:0,end:100};'
    'const t=O>=0&&O<n?O:n-1,'
    's=Math.max(0,t-D+1),'
    'x=Math.min(n-1,t+Math.ceil(D*.5));'
    'return{start:s/(n-1)*100,end:x/(n-1)*100}}'
)

# insert the helper immediately after the patch-7 date helper (statement level)
ANCHOR = 'return new Date(v)}'

OLD = 'dataZoom:[{type:"inside",start:w,end:D,zoomOnMouseWheel:!0,moveOnMouseWheel:!0}]'
NEW = ('dataZoom:[{type:"inside",...__glpalWeightZoom(k,O,a),'
       'zoomOnMouseWheel:!0,moveOnMouseWheel:!0}]')

# The chart-option memo never listed `period` (a) as a dependency. It only
# recomputed because Oge's outputs happened to change - and when the recorded
# history is shorter than the window those outputs are identical for every
# period, so the memo never re-ran and the chart rendered a stale period.
DEPS_OLD = ",[r,d,h,v,g,t,e,w,D,n,X,u,O,P,k,N,G,q,j]);"
DEPS_NEW = ",[r,d,h,v,g,t,e,w,D,n,X,u,O,P,k,N,G,q,j,a]);"

# the dose chart's own zoom must not be touched
DOSE_ZOOM = 'dataZoom:[{type:"inside",start:x,end:b,zoomOnMouseWheel:!0,moveOnMouseWheel:!0}]'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch12_chartperiod.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-11 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    if text.count(ANCHOR) != 1:
        raise RuntimeError(f"helper anchor found {text.count(ANCHOR)} times, expected 1")
    text = text.replace(ANCHOR, ANCHOR + HELPER, 1)

    if text.count(OLD) != 1:
        raise RuntimeError(f"weight chart dataZoom found {text.count(OLD)} times, expected 1")
    text = text.replace(OLD, NEW, 1)

    if text.count(DEPS_OLD) != 1:
        raise RuntimeError(f"memo dependency array found {text.count(DEPS_OLD)} times, expected 1")
    text = text.replace(DEPS_OLD, DEPS_NEW, 1)

    if text.count(DOSE_ZOOM) != 1:
        raise RuntimeError("the dose chart dataZoom was altered; it must stay as it was")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("weight chart: zoom derived from the rendered axis; period added to memo deps")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
