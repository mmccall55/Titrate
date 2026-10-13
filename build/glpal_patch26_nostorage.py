#!/usr/bin/env python3
"""
Patch 26 - hide medication storage.

Symptom
    Marc does not use medication storage (inventory of pens/vials, unit cost,
    units left). It takes a whole section of the Dashboard and feeds the
    Doses screen's Cost/Month card.

Cause
    Upstream feature, always rendered.

Fix
    Two render guards, the patch-15 technique: prefix each element with
    `!1&&` so React renders `false` (nothing) in its place.
    - Dashboard: `S.jsx(bye, ...)`, the Medication Storage section (summary
      cards, category filter, bar chart, "+ Add Storage Item", item list, and
      its add/edit/delete dialog, which `bye` renders itself)
    - Doses: the Cost/Month card, which is the only other place storage data
      is shown

What this deliberately does NOT change
    - the `medicationStorage` store and its records (schema rule)
    - the store actions, CSV export/import of storage rows
    - `Wye`, which still computes costPerMonth; nothing renders it
    - every other card and section

Usage
    python glpal_patch26_nostorage.py IN.js OUT.js
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "8334d584743780575f8f1ec04809f170feb4699f27a3df604c24a886809d22a7"
EXPECTED_OUTPUT_SHA256 = "055531610e1c54a3488a0bfb9b1a181072fdc6972b78357b38449bd126ce5eda"

GUARDS = [
    ("Dashboard Medication Storage section",
     '}),S.jsx(bye,{medicationStorage:u,'),
    ("Doses Cost/Month card",
     '}),S.jsxs("div",{className:Pe,children:[S.jsx("p",{className:Qe.label,children:"Cost/Month"})'),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch26_nostorage.py INPUT_JS OUTPUT_JS")
    src, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Input is not the verified patch-25 bundle.\n"
                           f"Expected: {EXPECTED_INPUT_SHA256}\n  Actual: {actual_in}")
    text = raw.decode("utf-8")
    guards_before = text.count("!1&&")
    for label, old in GUARDS:
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"{label}: anchor found {n} times, expected 1")
        text = text.replace(old, old[:3] + "!1&&" + old[3:], 1)
    if text.count("!1&&") != guards_before + len(GUARDS):
        raise RuntimeError("guard count did not rise by exactly the number of guards")
    for needle in ('"Medication Storage"', '"Cost/Month"', '"+ Add Storage Item"'):
        if text.count(needle) != 1:
            raise RuntimeError(f"{needle} occurrence count changed")

    data = text.encode("utf-8")
    actual_out = sha256_bytes(data)
    if EXPECTED_OUTPUT_SHA256 and actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"output sha mismatch\nExpected: {EXPECTED_OUTPUT_SHA256}\n  Actual: {actual_out}")
    out_path.write_bytes(data)
    print(f"Wrote {out_path}")
    print("medication storage section and Cost/Month card no longer render")
    print(f"SHA-256: {actual_out}")


if __name__ == "__main__":
    main()
