#!/usr/bin/env python3
"""
Patch 10 - goal weight displayed with the height converter.

Symptom
-------
Set a goal weight of 195 lb; the settings button reads "35 in".

Cause
-----
The bundle has two unit converters:

    Oo = (r,t) => t==="imperial" ? Math.round(pz(r)*10)/10 : r     # kg  -> lb   (pz = r*2.20462)
    fw = (r,t) => { if(t==="imperial"){ const {feet,inches} = zU(r) ... } }   # cm -> ft/in

The goal-weight button label calls `fw`, the HEIGHT formatter, and prints its
`.unit` - hence inches:

    195 lb  ->  stored 88.45 kg   (correct, via gz)
    88.45 / 2.54 = 34.8           -> "35 in"

The stored value is correct. Only this one label is wrong; the picker itself
already seeds its wheel with `Oo`, the weight converter.

Fix
---
Use `Oo` for the value and an explicit lbs/kg suffix, matching both the picker
and the "Goal Weight (kg|lbs)" caption directly above the button.

Usage:
  python glpal_patch10_goalunit.py titrate-index-goal.js titrate-index-unit.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "cd67d85fc07934caf3c2e23395fc713660ddda0fe611cea244470029a3761aff"
EXPECTED_OUTPUT_SHA256 = "e1330709887aeb115ac65dc0023e9372e8c7056b1161d77a51a703d1773a66ab"

OLD = ('children:u.goalWeight?`${Math.round(fw(u.goalWeight,w).value)} '
       '${fw(u.goalWeight,w).unit}`:"Set goal weight"')
NEW = ('children:u.goalWeight?`${Math.round(Oo(u.goalWeight,w)*10)/10} '
       '${w==="imperial"?"lbs":"kg"}`:"Set goal weight"')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch10_goalunit.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified patch-9 bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    n = text.count(OLD)
    if n != 1:
        raise RuntimeError(f"goal-weight label: expected 1 match, found {n}")
    text = text.replace(OLD, NEW, 1)

    # the height field must keep using the height formatter
    if "fw(u.height,w)" not in text:
        raise RuntimeError("the height display was altered; it must still use fw()")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("goal-weight label now uses the weight converter")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
