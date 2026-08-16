#!/usr/bin/env python3
"""
Patch 14 - show today's partial absorption instead of zero.

Background
----------
The level model in `v1` is deliberate and matches the drug: a dose contributes
nothing at the moment of injection, ramps linearly to full over 24 hours, then
decays by half-life. Tirzepatide's median Tmax is 24 hours, so the peak really
does land about a day after injection. That part is not a bug and is unchanged
here.

Symptom
-------
Log a dose and the chart shows no change at all until tomorrow.

Cause
-----
The chart samples the curve once per day, and each sample is taken at LOCAL
MIDNIGHT:

    const D = new Date(firstDate);
    for (; D <= lastDate; ) {
        T += v1(dosesByMed[R], halfLife[R], new Date(D));   // D is 00:00
        D.setDate(D.getDate() + 1);
    }

Midnight today is *before* a dose injected today, so `v1` sees a negative
elapsed time, returns early, and today's point is zero. The whole 24-hour ramp
falls between today's sample and tomorrow's, so it renders as a single step and
nothing appears to happen until the next day.

Fix
---
Evaluate the sample for today at the current time rather than at midnight. Past
and future days are untouched, so historical curve shapes do not change. A dose
injected at 08:00 and viewed at 14:00 now reads six hours of absorption instead
of zero, and the segment running up to tomorrow's peak is the ramp itself.

This changes only where the curve is *sampled*, not the model. `v1` is
untouched, and the patcher asserts as much.

Usage:
  python glpal_patch14_samplenow.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "0290848e7b5db004b190a76a8af3dc74b3b17ec093fa5ad6e544d7cef59d99c5"
EXPECTED_OUTPUT_SHA256 = "1b5d6f0bb61a7f9308085186783727d71f9ce4ae441f1ecf0b728e24155b6a35"

HELPER = (
    'function __glpalSampleAt(D){const n=new Date();'
    'return D.getFullYear()===n.getFullYear()&&D.getMonth()===n.getMonth()'
    '&&D.getDate()===n.getDate()?n:D}'
)

# tail of the patch-12 helper, a unique statement-level insertion point
ANCHOR = 'return{start:s/(n-1)*100,end:x/(n-1)*100}}'

REPLACEMENTS = [
    ('T+=v1(e[R],a[R],new Date(D))',
     'T+=v1(e[R],a[R],__glpalSampleAt(new Date(D)))',
     "combined level sample"),
    ('const R=v1(e[T],a[T],new Date(O))',
     'const R=v1(e[T],a[T],__glpalSampleAt(new Date(O)))',
     "per-medication level sample"),
]

# the decay model itself must not change
V1_MODEL = 'if(o<24){const l=o/24;s=i.dose*l}'


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch14_samplenow.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-13 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")

    if text.count(ANCHOR) != 1:
        raise RuntimeError(f"helper anchor found {text.count(ANCHOR)} times, expected 1")
    text = text.replace(ANCHOR, ANCHOR + HELPER, 1)

    for old, new, label in REPLACEMENTS:
        if text.count(old) != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {text.count(old)}")
        text = text.replace(old, new, 1)

    if text.count(V1_MODEL) != 1:
        raise RuntimeError("the absorption model in v1 was altered; it must not be")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("today's sample now taken at the current time; model unchanged")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
