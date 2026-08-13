#!/usr/bin/env python3
"""
Patch 9 - fix the goal-weight picker flashing open and vanishing.

Symptom
-------
Settings -> "Set goal weight" briefly shows a dialog, which then disappears.
The value can never be entered.

Cause
-----
The picker (`xz`) is rendered as a CHILD of the settings modal (`$U`), gated on
`isOpen: T` where `T = s === "goalWeightPicker"`.

The parent decides whether to mount the settings modal with:

    ee = u === "settings"

Clicking the button calls `onOpenModal("goalWeightPicker")`, which changes the
active modal away from "settings". So in the very same render that sets the
picker's isOpen true, `ee` becomes false and the settings modal unmounts -
taking the picker with it. The picker's own 200ms close animation is the flash.

Fix
---
1. Keep the settings modal mounted while the goal-weight picker is the active
   modal, so its child can actually render.
2. Return to settings on save/cancel rather than closing the whole settings
   modal. Upstream passed `N` (the settings modal's own onClose) for both,
   so a successful save dropped the user all the way back to the dashboard.
   `M("settings")` re-opens settings instead.

Usage:
  python glpal_patch9_goalweight.py titrate-index.js titrate-index-goal.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "4d5953e0277df472e98da30315afda51bee0bab43de9b2021844bf03a10e148a"
EXPECTED_OUTPUT_SHA256 = "cd67d85fc07934caf3c2e23395fc713660ddda0fe611cea244470029a3761aff"

REPLACEMENTS = [
    # 1. keep settings mounted while the picker is active
    ('ee=u==="settings"',
     'ee=u==="settings"||u==="goalWeightPicker"',
     "keep settings mounted for the picker"),
    # 2. save and cancel return to settings instead of closing everything
    ('S.jsx(xz,{isOpen:T,onSave:q=>{const X=parseFloat(q);'
     'if(X&&X>0){const V=gz(X,k);g(q),t({...d,goalWeight:V})}N()},onClose:N,',
     'S.jsx(xz,{isOpen:T,onSave:q=>{const X=parseFloat(q);'
     'if(X&&X>0){const V=gz(X,k);g(q),t({...d,goalWeight:V})}M("settings")},'
     'onClose:()=>M("settings"),',
     "return to settings on save/cancel"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch9_goalweight.py INPUT_JS OUTPUT_JS")

    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input is not the verified branded bundle.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")

    text = raw.decode("utf-8")
    for old, new, label in REPLACEMENTS:
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"{label}: expected 1 match, found {n}")
        text = text.replace(old, new, 1)

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")

    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print(f"applied {len(REPLACEMENTS)} replacements")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
