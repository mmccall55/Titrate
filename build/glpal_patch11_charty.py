#!/usr/bin/env python3
"""
Patch 11 - weight chart y-axis bounds.

Symptom
-------
On the dashboard the weight trend is squashed into a thin band at the top of
the plot. With weights of 84.5-88.5 kg the axis ran 65-90 kg, so the actual
data used about a sixth of the vertical space.

Cause
-----
The weight y-axis is configured with `scale:!0` and no explicit bounds, so
ECharts fits the extent to EVERYTHING drawn - including the goal-weight
markLine and the dashed forward projection, which can sit far below the
recorded data. The further away the goal, the flatter the real trend looks.

The helper `kge` already computes precisely the right numbers:

    minWeight     = Math.min(...weights)
    maxWeight     = Math.max(...weights)
    weightPadding = (max - min) * 0.1 || 5

and returns them destructured as h, v and g. They are listed in the chart
memo's dependency array but never actually used - the bounds were evidently
intended and never wired in.

Fix
---
Bound the axis to the recorded weights UNION the goal, plus that padding,
rounded outward to whole units for clean labels:

    min: Math.floor(Math.min(h, t) - g)
    max: Math.ceil(Math.max(v, t) + g)

Taking the union in both directions means the goal line is always on screen:
below the data while you are working down toward it, and above the data if you
drop past it. The projection is deliberately NOT included - it is extrapolated
rather than recorded, and it was the largest contributor to the original
squashing. It still draws, and is clipped where it leaves the range.

Bounds are in kg (the stored unit); the existing label formatter handles
imperial conversion, so this is correct in both unit systems.

Usage:
  python glpal_patch11_charty.py titrate-index-unit.js titrate-index-chart.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "e1330709887aeb115ac65dc0023e9372e8c7056b1161d77a51a703d1773a66ab"
EXPECTED_OUTPUT_SHA256 = "37638391810ef2babbee71c5482db5c6bc49fe8d3163b2a9a54d78326b4dfd69"

# t is the goalWeight prop. Including it in BOTH directions keeps the goal line
# on screen whether you are above it or have dropped below it, while the
# speculative projection is excluded so it cannot drag the extent.
OLD = 'yAxis:{type:"value",position:"right",scale:!0,axisLine:{show:!1}'
NEW = ('yAxis:{type:"value",position:"right",scale:!0,'
       'min:Math.floor(Math.min(h,t||h)-g),max:Math.ceil(Math.max(v,t||v)+g),'
       'axisLine:{show:!1}')

# the dose chart keeps its zero baseline
DOSE_AXIS = 'yAxis:{type:"value",position:"right",min:0,axisLine:{show:!1}'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch11_charty.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-10 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    n = text.count(OLD)
    if n != 1:
        raise RuntimeError(f"weight y-axis: expected 1 match, found {n}")
    text = text.replace(OLD, NEW, 1)

    if text.count(DOSE_AXIS) != 1:
        raise RuntimeError("the dose chart y-axis was altered; it must keep min:0")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("weight y-axis now bounded to the recorded data plus padding")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
